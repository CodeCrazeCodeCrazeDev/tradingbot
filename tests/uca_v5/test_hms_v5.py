import pytest
import os
import shutil
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.hms.models import ResearchLedgerEntry, Hypothesis, EvidenceGraph

@pytest.fixture
def hms():
    base_path = "alphaalgo_data/test_hms"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)
    yield HierarchicalMemorySystem(base_path=base_path)
    shutil.rmtree(base_path)

def test_hms_sage_graph_evolution(hms):
    # Setup entry
    hyp = Hypothesis(description="Bullish move on EURUSD", predicted_outcome="BULL")
    entry = ResearchLedgerEntry(
        hypothesis=hyp,
        reasoning_steps=["Step 1", "Step 2"],
        evidence_graph_snapshot=EvidenceGraph()
    )

    # Store entry (triggers SAGE add_evidence)
    hms.store_ledger_entry(entry)

    # Check graph persistence
    assert os.path.exists(os.path.join(hms.base_path, "sage_graph.graphml"))
    assert len(hms.sage.graph.nodes) > 0
    # In V6, add_evidence creates unique edge keys
    assert any(d.get("relation") == "HYPOTHESIZED" for u, v, d in hms.sage.graph.edges(data=True))

def test_hms_automem_optimization(hms):
    initial_count = hms.memory_schema.get("optimized_count", 0)

    # Run optimization
    hms.optimize_metamemory([{"id": "success_1"}])

    new_count = hms.memory_schema.get("optimized_count")
    assert new_count > initial_count

def test_hms_sage_multihop_retrieval(hms):
    # Setup graph
    hms.sage.add_evidence(("A", "CAUSES", "B"), {}, {"confidence": 0.9})
    hms.sage.add_evidence(("B", "CAUSES", "C"), {}, {"confidence": 0.8})

    # Retrieve
    results = hms.sage.retrieve_subgraph("A", hops=2)
    assert len(results) >= 2
    print("Multi-hop retrieval verified.")
