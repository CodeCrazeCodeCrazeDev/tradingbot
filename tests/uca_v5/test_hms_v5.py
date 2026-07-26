import pytest
import os
import shutil
import json
from trading_bot.core.hms.memory import HierarchicalMemorySystem, calculate_integrity_hash
from trading_bot.core.hms.models import ResearchLedgerEntry, Hypothesis, EvidenceGraph

@pytest.fixture
def hms():
    base_path = "alphaalgo_data/test_hms"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)
    # Ensure fresh singleton instance or clear initial state
    HierarchicalMemorySystem._instance = None
    h = HierarchicalMemorySystem(base_path=base_path)
    yield h
    shutil.rmtree(base_path)
    HierarchicalMemorySystem._instance = None

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

def test_hms_deterministic_rollback_and_migration(hms):
    """Verify forward migration to 1.1 and automatic rollback on failure."""
    assert hms.memory_schema["version"] == "1.0"

    # 1. Forward migration
    success = hms.migrate_schema("1.1")
    assert success is True
    assert hms.memory_schema["version"] == "1.1"
    assert "SAGE_NODE" in hms.memory_schema["entities"]

    # 2. Re-migrate to same version
    assert hms.migrate_schema("1.1") is True

    # 3. Rollback (Backward migration)
    success_back = hms.migrate_schema("1.0")
    assert success_back is True
    assert hms.memory_schema["version"] == "1.0"
    assert "SAGE_NODE" not in hms.memory_schema["entities"]

    # 4. Fail and trigger rollback
    # We pass an invalid target format (e.g. non-float representation) which will raise ValueError
    failed_migration = hms.migrate_schema("INVALID_VERSION")
    assert failed_migration is False
    assert hms.memory_schema["version"] == "1.0" # Cleanly rolled back to original

def test_hms_integrity_mismatch_fallback(hms):
    """Verify that corrupt schema triggers integrity checks and fallback to defaults."""
    # Corrupt the on-disk file
    schema_file = hms.schema_path
    corrupt_data = {
        "version": "1.5",
        "entities": ["CORRUPT"],
        "relations": ["CORRUPT"],
        "integrity_hash": "incorrect_hash"
    }
    with open(schema_file, "w") as f:
        json.dump(corrupt_data, f)

    # Force re-initialization of memory system instance
    HierarchicalMemorySystem._instance = None
    hms_new = HierarchicalMemorySystem(base_path=hms.base_path)

    # Check that it fell back to default 1.0 schema with verified hash
    assert hms_new.memory_schema["version"] == "1.0"
    assert "CORRUPT" not in hms_new.memory_schema["entities"]
    assert hms_new.memory_schema["integrity_hash"] == calculate_integrity_hash(hms_new.memory_schema)
