import pytest
import time
import networkx as nx
from trading_bot.core.hms.memory_os import (
    MemoryOS,
    MemoryNode,
    MemoryEdge,
    MemoryTier,
    EdgeRelation,
    MemoryProvenance,
    MetaMemoryLog
)

@pytest.fixture
def memory_os():
    return MemoryOS(base_storage_path="alphaalgo_data/test_memory_os_suite")

def test_memory_os_eight_tier_hierarchy(memory_os):
    # Verify we can write to different tiers (T0 to T7)
    node_t0 = MemoryNode(
        tier=MemoryTier.T0_WORKSPACE,
        content={"attention_topic": "volatile_breakout"}
    )
    node_t2 = MemoryNode(
        tier=MemoryTier.T2_SEMANTIC,
        content={"fact": "EURUSD pip value is 10 USD per lot"}
    )
    node_t4 = MemoryNode(
        tier=MemoryTier.T4_RESEARCH,
        content={"hypothesis": "DiscoLoop increases reasoning depth by 3x"}
    )
    node_t6 = MemoryNode(
        tier=MemoryTier.T6_INSTITUTIONAL,
        content={"study": "Ablation study on Volatility triggers"}
    )

    id_t0 = memory_os.write_memory(node_t0)
    id_t2 = memory_os.write_memory(node_t2)
    id_t4 = memory_os.write_memory(node_t4)
    id_t6 = memory_os.write_memory(node_t6)

    assert id_t0 == node_t0.node_id
    assert id_t2 == node_t2.node_id
    assert id_t4 == node_t4.node_id
    assert id_t6 == node_t6.node_id

    # Read back and confirm tiers
    read_t0 = memory_os.read_memory(id_t0)
    read_t4 = memory_os.read_memory(id_t4)

    assert read_t0.tier == MemoryTier.T0_WORKSPACE
    assert read_t4.tier == MemoryTier.T4_RESEARCH
    assert read_t4.content["hypothesis"] == "DiscoLoop increases reasoning depth by 3x"

def test_memory_os_graph_native_linking_and_navigation(memory_os):
    # Create a small causal trace: Hypothesis -> Experiment -> Result -> Lesson
    node_hyp = MemoryNode(
        tier=MemoryTier.T4_RESEARCH,
        content={"type": "hypothesis", "claim": "Aggressive scaling degrades expectancies"}
    )
    node_exp = MemoryNode(
        tier=MemoryTier.T4_RESEARCH,
        content={"type": "experiment", "runs": 100}
    )
    node_lesson = MemoryNode(
        tier=MemoryTier.T6_INSTITUTIONAL,
        content={"lesson": "Keep scaling under 2.0x"}
    )

    h_id = memory_os.write_memory(node_hyp)
    e_id = memory_os.write_memory(node_exp)
    l_id = memory_os.write_memory(node_lesson)

    # Link Hypothesis -> Experiment (Causal)
    memory_os.link_memories(MemoryEdge(source_id=h_id, target_id=e_id, relation=EdgeRelation.CAUSAL))
    # Link Experiment -> Lesson (Evidential)
    memory_os.link_memories(MemoryEdge(source_id=e_id, target_id=l_id, relation=EdgeRelation.EVIDENTIAL))

    # Navigate starting from Hypothesis
    traversed_ids = memory_os.navigator.navigate_multi_hop(h_id, EdgeRelation.CAUSAL, depth=1)
    assert e_id in traversed_ids
    assert l_id not in traversed_ids  # depth is 1, so lesson is not reached

    # Traverse with depth=2
    traversed_ids_all = memory_os.navigator.search_by_query("Runs", tier=MemoryTier.T4_RESEARCH)
    assert e_id in traversed_ids_all

def test_proactive_memory_manager_selective_reminders(memory_os):
    # Scenario A: Low risk, silent preference lesson -> Selective Silence
    context_low = {"market": {"volatility": 0.15}}
    memory_low = MemoryNode(
        tier=MemoryTier.T2_SEMANTIC,
        content={"lesson": "Use default sizer in normal volatility"}
    )

    should_inject, text = memory_os.proactive_manager.should_inject_reminder(context_low, [memory_low])
    assert not should_inject
    assert text is None

    # Scenario B: High risk, critical failure/warning lesson -> Proactive Intervention
    context_high = {"market": {"volatility": 0.45}}
    memory_high = MemoryNode(
        tier=MemoryTier.T6_INSTITUTIONAL,
        content={"lesson": "failed in high volatility: stay in HOLD state to prevent loss"}
    )

    should_inject_high, text_high = memory_os.proactive_manager.should_inject_reminder(context_high, [memory_high])
    assert should_inject_high
    assert "[CRITICAL PROACTIVE MEMORY]" in text_high
    assert "stay in HOLD state" in text_high

def test_meta_memory_logging_t7(memory_os):
    # Perform a read to trigger a T7 Meta-Memory log creation
    node = MemoryNode(
        tier=MemoryTier.T2_SEMANTIC,
        content={"fact": "Consolidation limit is 5 lot"}
    )
    node_id = memory_os.write_memory(node)

    # Read back memory
    memory_os.read_memory(node_id)

    # Find meta-memory nodes in T7
    t7_nodes = [
        data["node"] for nid, data in memory_os.graph.nodes(data=True)
        if data.get("tier") == MemoryTier.T7_META_MEMORY.value
    ]

    assert len(t7_nodes) > 0
    # Confirm stats are populated
    latest_meta = t7_nodes[-1]
    assert "latency_ms" in latest_meta.content
    assert "retrieval_success" in latest_meta.content
    assert latest_meta.content["retrieval_success"] is True

def test_memory_reproduction_replay(memory_os):
    node = MemoryNode(tier=MemoryTier.T1_EPISODIC, content={"session_id": "sess_1"})
    memory_os.write_memory(node)

    replay_log = memory_os.replay_transactions()
    assert len(replay_log) > 0
    assert replay_log[-1]["action"] == "WRITE"
    assert replay_log[-1]["node_id"] == node.node_id
