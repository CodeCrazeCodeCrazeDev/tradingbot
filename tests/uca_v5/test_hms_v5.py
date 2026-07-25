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

def test_hms_deterministic_migrations_and_replay(hms):
    # Reset version for test isolation since hms is a singleton
    hms.memory_schema["schema_version"] = "1.0"
    hms.memory_schema["version"] = "1.0"
    hms.memory_schema["entities"] = []
    hms.memory_schema["relations"] = []
    hms.memory_schema["migration_history"] = []
    hms._save_schema()

    # Verify initial state
    assert hms.memory_schema["schema_version"] == "1.0"
    assert hms.validate_replay(hms.memory_schema) is True

    # 1. Migrate up to 1.1
    success = hms.migrate_to_version("1.1")
    assert success is True
    assert hms.memory_schema["schema_version"] == "1.1"
    assert any(e["type"] == "RESEARCH_METADATA" for e in hms.memory_schema["entities"])

    # Replay validation should hold
    assert hms.validate_replay(hms.memory_schema) is True

    # 2. Migrate up to 1.2
    success = hms.migrate_to_version("1.2")
    assert success is True
    assert hms.memory_schema["schema_version"] == "1.2"
    assert any(r["type"] == "CONTRADICTS" for r in hms.memory_schema["relations"])

    # Replay validation
    assert hms.validate_replay(hms.memory_schema) is True

    # 3. Rollback (down-migrate) back to 1.0
    success = hms.migrate_to_version("1.0")
    assert success is True
    assert hms.memory_schema["schema_version"] == "1.0"

    # Check that added entities and relations were removed
    assert not any(e["type"] == "RESEARCH_METADATA" for e in hms.memory_schema["entities"])
    assert not any(r["type"] == "CONTRADICTS" for r in hms.memory_schema["relations"])

    # Track history holds
    assert len(hms.memory_schema["migration_history"]) >= 4
    assert hms.validate_replay(hms.memory_schema) is True
