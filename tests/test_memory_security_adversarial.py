import pytest
from trading_bot.core.hms.memory import (
    ProvenanceAwareMemoryRecord,
    MemoryValidationStatus,
    HierarchicalMemorySystem
)

def test_provenance_aware_memory_record_creation():
    record = ProvenanceAwareMemoryRecord(
        source="agent_alpha",
        creator="llm_v1",
        content="Market liquidity is decreasing on pair EUR/USD",
        evidence_refs=["obs_101", "obs_102"],
        confidence=0.85
    )
    assert record.memory_id is not None
    assert record.integrity_hash != ""
    assert record.is_valid() is True
    assert record.validation_status == MemoryValidationStatus.UNVERIFIED

def test_tampered_memory_integrity_failure():
    record = ProvenanceAwareMemoryRecord(
        source="agent_alpha",
        creator="llm_v1",
        content="Authentic initial content",
        evidence_refs=["obs_101"]
    )
    assert record.is_valid() is True

    # Tamper with content without updating hash
    record.content = "Adversarial content injected!"
    assert record.is_valid() is False

def test_quarantined_memory_invalidation():
    record = ProvenanceAwareMemoryRecord(
        source="agent_rogue",
        creator="llm_v1",
        content="Malicious payload",
        validation_status=MemoryValidationStatus.QUARANTINED
    )
    assert record.is_valid() is False

def test_echo_amplification_prevention():
    # Agent A creates memory
    rec_a = ProvenanceAwareMemoryRecord(
        source="agent_a",
        creator="llm_v1",
        content="Claim X",
        evidence_refs=["obs_001"]
    )

    # Agent B retrieves rec_a and creates rec_b derived from same evidence
    rec_b = ProvenanceAwareMemoryRecord(
        source="agent_b",
        creator="llm_v2",
        content="Claim X confirmed",
        evidence_refs=["obs_001"], # Same primary evidence lineage
        parent_memory=rec_a.memory_id
    )

    # Check evidence refs line up
    assert rec_a.evidence_refs == rec_b.evidence_refs
    # B's retrieval does NOT automatically upgrade rec_a or rec_b to TRUSTED
    assert rec_a.validation_status != MemoryValidationStatus.TRUSTED
    assert rec_b.validation_status != MemoryValidationStatus.TRUSTED
