import pytest
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, SignedInterAgentMessage
from trading_bot.core.hms.memory import HierarchicalMemorySystem, ProvenanceAwareMemoryRecord, MemoryValidationStatus
from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
from trading_bot.core.immutable_shield import ImmutableShield

def test_single_memory_authority_enforces_provenance():
    hms = HierarchicalMemorySystem.get_instance() if hasattr(HierarchicalMemorySystem, 'get_instance') else HierarchicalMemorySystem("temp_hms")

    # Valid record
    valid_rec = ProvenanceAwareMemoryRecord(source="agent_1", content="Valid market note", validation_status=MemoryValidationStatus.VALIDATED)
    assert valid_rec.is_valid() is True

    # Tampered record rejected
    tampered_rec = ProvenanceAwareMemoryRecord(source="agent_1", content="Clean content", integrity_hash="FAKE_HASH")
    assert tampered_rec.is_valid() is False

def test_single_message_authority_enforces_signatures():
    bus = UnifiedDecisionBus.get_instance() if hasattr(UnifiedDecisionBus, 'get_instance') else UnifiedDecisionBus()

    msg = SignedInterAgentMessage(sender_id="ag1", sender_version="1.0", task_id="t1", payload={"data": "test"})
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is True

    msg.payload["data"] = "TAMPERED"
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is False
