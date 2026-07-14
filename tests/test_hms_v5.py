
import os
import shutil
import json
import logging
from datetime import datetime
from trading_bot.core.hms.memory import HierarchicalMemorySystem, SAGEGraphMemory
from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_sage_graph_memory_evolution():
    print("Running test_sage_graph_memory_evolution...")
    storage_path = "test_sage_graph.graphml"
    if os.path.exists(storage_path):
        os.remove(storage_path)

    sage = SAGEGraphMemory(storage_path=storage_path)

    # Add some evidence
    triplet = ("Market", "CORRELATES", "Oil")
    context = {"regime": "High Vol"}
    evidence = {"source": "Bloomberg", "value": 0.85}
    sage.add_evidence(triplet, context, evidence)

    assert sage.graph.has_edge("Market", "Oil")

    # Evolve the graph
    feedback = [
        {"action": "PRUNE", "edge_id": ("Market", "Oil", list(sage.graph["Market"]["Oil"].keys())[0])}
    ]
    sage.evolve(feedback)

    assert not sage.graph.has_edge("Market", "Oil")

    if os.path.exists(storage_path):
        os.remove(storage_path)
    print("test_sage_graph_memory_evolution PASSED")

def test_hms_store_ledger_entry():
    print("Running test_hms_store_ledger_entry...")
    base_path = "test_hms_data"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    hms = HierarchicalMemorySystem(base_path=base_path)

    # Create a mock ResearchLedgerEntry
    nodes = {
        "n1": EvidenceNode(node_id="n1", content="Bullish Sentiment", node_type="CLAIM"),
        "n2": EvidenceNode(node_id="n2", content="Buy Recommendation", node_type="HYPOTHESIS")
    }
    edges = [
        EvidenceEdge(source_id="n1", target_id="n2", relation=RelationType.SUPPORTS, weight=0.9)
    ]
    graph = EvidenceGraph(nodes=nodes, edges=edges)
    entry = ResearchLedgerEntry(entry_id="test_entry_1", evidence_graph_snapshot=graph)

    hms.store_ledger_entry(entry)

    # Verify file persistence
    ledger_file = os.path.join(base_path, "research_ledger", "test_entry_1.json")
    assert os.path.exists(ledger_file)
    with open(ledger_file, 'r') as f:
        data = json.load(f)
        assert data["entry_id"] == "test_entry_1"

    # Verify SAGE sync
    assert hms.sage.graph.has_node("n1")
    assert hms.sage.graph.has_node("n2")
    assert hms.sage.graph.has_edge("n1", "n2")

    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    print("test_hms_store_ledger_entry PASSED")

def test_hms_automem_optimization():
    print("Running test_hms_automem_optimization...")
    base_path = "test_hms_automem"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    hms = HierarchicalMemorySystem(base_path=base_path)

    hms.optimize_metamemory(success_trajectories=[{"id": "traj1"}])

    assert "last_optimized" in hms.memory_schema

    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    print("test_hms_automem_optimization PASSED")

if __name__ == "__main__":
    test_sage_graph_memory_evolution()
    test_hms_store_ledger_entry()
    test_hms_automem_optimization()
    print("All tests PASSED")
