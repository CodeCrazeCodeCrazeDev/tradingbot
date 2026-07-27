import pytest
import time
from trading_bot.core.hms.ontology import CMOSNode, CMOSProvenance, CMOSNodeTier, CMOSEdge, CMOSEdgeRelation
from trading_bot.core.hms.cmos import CognitiveMemoryOS
from trading_bot.core.hms.contracts import CMOSContractVerifier, CMOSContractValidationError


@pytest.fixture
def clean_cmos():
    cmos = CognitiveMemoryOS()
    # Reset internal graph state for clean tests
    cmos.repository.graph.clear()
    cmos.reproduction_ledger.clear()
    cmos.observability.latencies.clear()
    cmos.observability.read_requests = 0
    cmos.observability.cache_hits = 0
    cmos.observability.mutations = 0
    return cmos


def test_referential_integrity_gate(clean_cmos):
    # Test valid link: both exist
    p = CMOSProvenance(source_agent="Test", source_input_hash="hash1")
    n1 = CMOSNode(node_id="node_a", tier=CMOSNodeTier.T1_EPISODIC, content={"desc": "A"}, provenance=p)
    n2 = CMOSNode(node_id="node_b", tier=CMOSNodeTier.T2_SEMANTIC, content={"desc": "B"}, provenance=p)

    clean_cmos.write_node(n1)
    clean_cmos.write_node(n2)

    edge = CMOSEdge(source_id="node_a", target_id="node_b", relation=CMOSEdgeRelation.SEMANTIC)
    clean_cmos.link_nodes(edge)

    # Referential integrity check passes
    nodes = clean_cmos.repository.list_nodes()
    edges = clean_cmos.repository.list_edges()
    is_valid, dangling = CMOSContractVerifier.verify_referential_integrity(nodes, edges)
    assert is_valid
    assert dangling == 0

    # Test invalid link: target doesn't exist
    edge_invalid = CMOSEdge(source_id="node_a", target_id="non_existent", relation=CMOSEdgeRelation.SEMANTIC)
    with pytest.raises(CMOSContractValidationError) as excinfo:
        clean_cmos.link_nodes(edge_invalid)
    assert "Referential Integrity violated" in str(excinfo.value)


def test_provenance_completeness_gate(clean_cmos):
    p = CMOSProvenance(source_agent="Agent_1", source_input_hash="hash_abc")
    n = CMOSNode(node_id="node_x", tier=CMOSNodeTier.T1_EPISODIC, content={"x": 1}, provenance=p)
    clean_cmos.write_node(n)

    is_valid, coverage = CMOSContractVerifier.verify_provenance_completeness(clean_cmos.repository.list_nodes())
    assert is_valid
    assert coverage == 1.0


def test_graph_consistency_and_contradictions(clean_cmos):
    p = CMOSProvenance(source_agent="Validator", source_input_hash="hash_v")
    n1 = CMOSNode(node_id="node_yes", tier=CMOSNodeTier.T2_SEMANTIC, content={"claim": "Market is BULLISH"}, provenance=p)
    n2 = CMOSNode(node_id="node_no", tier=CMOSNodeTier.T2_SEMANTIC, content={"claim": "Market is BEARISH"}, provenance=p)

    clean_cmos.write_node(n1)
    clean_cmos.write_node(n2)

    # Link with CONTRADICTS relationship
    edge = CMOSEdge(source_id="node_yes", target_id="node_no", relation=CMOSEdgeRelation.CONTRADICTS)
    clean_cmos.link_nodes(edge)

    is_consistent, contradictions = CMOSContractVerifier.verify_graph_consistency(
        clean_cmos.repository.list_nodes(),
        clean_cmos.repository.list_edges()
    )
    assert not is_consistent
    assert "node_yes contradicts node_no" in contradictions


def test_deterministic_replay_audit(clean_cmos):
    # Perform series of operations
    p = CMOSProvenance(source_agent="ReplayAgent", source_input_hash="hash_r")
    n = CMOSNode(node_id="node_r", tier=CMOSNodeTier.T1_EPISODIC, content={"value": 42}, provenance=p)

    clean_cmos.write_node(n)
    clean_cmos.read_node("node_r")

    # Fetch audit ledger
    ledger = clean_cmos.replay_audit_trail()
    assert len(ledger) >= 2
    assert ledger[-2]["action"] == "WRITE"
    assert ledger[-2]["node_id"] == "node_r"
    assert ledger[-1]["action"] == "READ"
    assert ledger[-1]["node_id"] == "node_r"


def test_observability_telemetry(clean_cmos):
    p = CMOSProvenance(source_agent="ObsAgent", source_input_hash="hash_o")
    n = CMOSNode(node_id="node_o", tier=CMOSNodeTier.T0_WORKSPACE, content={"temp": True}, provenance=p)

    clean_cmos.write_node(n)
    clean_cmos.read_node("node_o")

    metrics = clean_cmos.observability.get_metrics_snapshot()
    assert "p50_latency_ms" in metrics
    assert "cache_hit_ratio" in metrics
    assert metrics["cache_hit_ratio"] == 1.0


def test_simulated_corruption_and_recovery(clean_cmos):
    p = CMOSProvenance(source_agent="RecoveryAgent", source_input_hash="hash_rec")
    n = CMOSNode(node_id="node_rec", tier=CMOSNodeTier.T1_EPISODIC, content={"state": "critical"}, provenance=p)
    clean_cmos.write_node(n)

    # Simulate corruption: delete the node
    clean_cmos.repository.delete_node("node_rec")
    assert clean_cmos.repository.get_node("node_rec") is None

    # Recover using the deterministic transaction log
    for tx in clean_cmos.replay_audit_trail():
        if tx["action"] == "WRITE" and tx["node_id"] == "node_rec":
            rec_node = CMOSNode(
                node_id=tx["node_id"],
                tier=CMOSNodeTier(tx["tier"]),
                content=tx["content"],
                provenance=CMOSProvenance(
                    source_agent=tx["provenance"]["source_agent"],
                    source_input_hash=tx["provenance"]["source_input_hash"],
                    source_quality=tx["provenance"]["source_quality"],
                    confidence=tx["provenance"]["confidence"],
                    evidence_uris=tx["provenance"]["evidence_uris"],
                    creation_time=tx["provenance"]["creation_time"]
                )
            )
            clean_cmos.repository.store_node(rec_node)

    # Verification: node successfully recovered
    recovered = clean_cmos.repository.get_node("node_rec")
    assert recovered is not None
    assert recovered.content["state"] == "critical"
