import pytest
from trading_bot.core.hms.memory import ProvenanceAwareMemoryRecord, MemoryValidationStatus
from trading_bot.core.unified_event_bus import CapabilityDomain
from trading_bot.core.security.defense import ExecutableSecurityInvariants

def test_invariant_1_intelligence_direct_execution_blocked():
    capabilities = [CapabilityDomain.INTELLIGENCE.value, CapabilityDomain.RESEARCH.value]
    assert ExecutableSecurityInvariants.check_invariant_1_intelligence_direct_execution(capabilities) is False

def test_invariant_4_unverified_memory_blocked():
    record = ProvenanceAwareMemoryRecord(
        source="agent_research",
        content="Market going up",
        validation_status=MemoryValidationStatus.UNVERIFIED
    )
    assert ExecutableSecurityInvariants.check_invariant_4_unverified_memory_decision(record) is False

def test_invariant_14_emergency_veto_dominates_swarm_consensus():
    proposal = "BUY_NOW"
    assert ExecutableSecurityInvariants.check_invariant_14_emergency_veto_dominates(proposal, veto_triggered=True) == "NO_ACTION"

def test_failure_scenario_corrupted_memory_fail_closed():
    record = ProvenanceAwareMemoryRecord(
        source="agent_research",
        content="Authentic data",
        validation_status=MemoryValidationStatus.TRUSTED
    )
    assert record.is_valid() is True

    record.content = "CORRUPTED_DATA"
    assert record.is_valid() is False
    assert ExecutableSecurityInvariants.check_invariant_4_unverified_memory_decision(record) is False
