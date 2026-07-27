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
    assert hms.sage.graph.has_edge(str(entry.entry_id), "Bullish move on EURUSD")

def test_hms_automem_optimization(hms):
    initial_version = hms.memory_schema.get("version", "1.0")

    # Run optimization
    hms.optimize_metamemory([{"id": "success_1"}])

    new_version = hms.memory_schema.get("version")
    assert float(new_version) > float(initial_version)
