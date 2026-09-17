
import pytest
import os
import shutil
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.hms.models import ResearchLedgerEntry, Hypothesis, EvidenceGraph, EvidenceNode
from uuid import uuid4

@pytest.fixture
def hms():
    path = "test_hms_data"
    if os.path.exists(path):
        shutil.rmtree(path)
    # Reset singleton
    HierarchicalMemorySystem._instance = None
    hms_instance = HierarchicalMemorySystem(base_path=path)
    yield hms_instance
    if os.path.exists(path):
        shutil.rmtree(path)

def test_hms_initialization(hms):
    assert os.path.exists(hms.base_path)
    assert os.path.exists(hms.ledger_path)
    assert hms.sage is not None

def test_hms_store_ledger(hms):
    entry_id = str(uuid4())
    graph = EvidenceGraph()
    graph.add_node(EvidenceNode(node_id="n1", content="Evidence 1", node_type="FACT"))

    entry = ResearchLedgerEntry(
        entry_id=entry_id,
        hypothesis=Hypothesis(description="Test Hypothesis"),
        reasoning_steps=["Step 1"],
        evidence_graph_snapshot=graph,
        composite_confidence=0.9
    )

    hms.store_ledger_entry(entry)

    # Check file persistence
    assert os.path.exists(os.path.join(hms.ledger_path, f"{entry_id}.json"))

    # Check SAGE integration
    assert hms.sage.graph.has_node("n1")
    # Verify HYPOTHESIZED relation exists in edges
    hyp_found = False
    for u, v, d in hms.sage.graph.edges(data=True):
        if d.get("relation") == "HYPOTHESIZED" and v == "Test Hypothesis":
            hyp_found = True
            break
    assert hyp_found

@pytest.mark.asyncio
async def test_hms_retrieval(hms):
    hms.sage.add_evidence(("AssetA", "CORRELATED_WITH", "AssetB"), {"ctx": 1}, {"ev": 1})
    results = await hms.retrieve_evidence_chain("AssetA")
    assert len(results) > 0
    assert results[0]["source"] == "AssetA"
    assert results[0]["target"] == "AssetB"

def test_hms_automem_optimization(hms):
    hms.optimize_metamemory([])
    assert "last_optimized" in hms.memory_schema
