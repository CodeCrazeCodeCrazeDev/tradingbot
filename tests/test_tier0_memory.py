
import asyncio
import os
import shutil
import json
import networkx as nx
from trading_bot.core.hms.memory import HierarchicalMemorySystem, SAGEGraphMemory
from trading_bot.core.hms.models import ResearchLedgerEntry, EvidenceGraph, EvidenceNode, EvidenceEdge, RelationType

def test_sage_qkg_memory():
    print("Starting Tier 0 Memory Verification (SAGE/QKG)")

    test_path = "tests/temp_hms"
    if os.path.exists(test_path):
        shutil.rmtree(test_path)
    os.makedirs(test_path)

    hms = HierarchicalMemorySystem(base_path=test_path)

    # 1. Test QKG Context-Dependent Validity
    print("Case 1: QKG Context-Dependent Validity")
    edge = EvidenceEdge(
        source_id="liquidity",
        target_id="high_slippage",
        relation=RelationType.CAUSES,
        context_validity_mask={"regime": "high_vol"}
    )

    # Valid context
    assert edge.is_valid_in_context({"regime": "high_vol"}) == True
    # Invalid context
    assert edge.is_valid_in_context({"regime": "low_vol"}) == False
    print("PASS: QKG context validation works")

    # 2. Test SAGE Evolution
    print("\nCase 2: SAGE Graph Evolution")
    sage = SAGEGraphMemory()
    sage.add_evidence(
        triplet=("Fed", "RAISES", "Rates"),
        context={"market": "US"},
        evidence={"source": "Reuters"}
    )

    # Check if edge exists
    assert len(sage.graph.edges) == 1
    edge_data = list(sage.graph.edges(data=True))[0][2]
    u, v, key = list(sage.graph.edges(keys=True))[0]

    # Prune it via feedback
    sage.evolve([{"edge_id": (u, v, key), "action": "PRUNE"}])
    assert len(sage.graph.edges) == 0
    print("PASS: SAGE pruning evolution works")

    shutil.rmtree(test_path)
    print("\nTier 0 Memory Verification COMPLETE")

if __name__ == "__main__":
    test_sage_qkg_memory()
