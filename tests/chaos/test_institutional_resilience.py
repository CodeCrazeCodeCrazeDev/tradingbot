"""
UCA V5 Institutional Chaos Engineering
======================================

Injects deterministic faults into core subsystems to verify
graceful degradation and safety invariant preservation.
"""

import pytest
import asyncio
from typing import Dict, Any

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.verification.swarm import VerificationSwarm
from trading_bot.core.immutable_shield import ImmutableShield
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, LogAction, ActionStatus
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

# Faulty Mocks
class TimeoutWorldModel:
    async def simulate(self, *args, **kwargs):
        await asyncio.sleep(10.0) # Triggers timeout
        return []
    def predict(self, *args, **kwargs): return {"price": 100.0}

class DisagreeingSwarm(VerificationSwarm):
    async def run_swarm(self, *args, **kwargs):
        from trading_bot.core.hms.models import VerifierReport
        return [
            VerifierReport(agent_name="V1", is_valid=True, confidence=0.9, critique=""),
            VerifierReport(agent_name="V2", is_valid=False, confidence=0.9, critique="Veto")
        ]

@pytest.fixture
def base_system(event_loop):
    bus = UnifiedDecisionBus()
    event_loop.run_until_complete(bus.start())
    hms = HierarchicalMemorySystem(base_path="tests/temp_hms_chaos")
    shield = ImmutableShield()

    # Voter registration
    async def shield_voter(action):
        return {"decision": "APPROVED"}
    bus.register_voter("ImmutableShield", shield_voter)

    yield {
        "bus": bus,
        "hms": hms,
        "shield": shield,
        "router": SkillRouter()
    }
    event_loop.run_until_complete(bus.stop())

@pytest.mark.asyncio
async def test_chaos_hms_unavailable(base_system):
    """
    Fault: HMS retrieve_evidence_chain raises Exception.
    Expect: System continues using working memory; trade not necessarily rejected if logic allows.
    """
    sys = base_system

    class BrokenHMS:
        async def retrieve_evidence_chain(self, *args, **kwargs):
            raise ConnectionError("HMS DB Down")
        def store_ledger_entry(self, *args, **kwargs): pass

    csc = CognitiveSystemController(
        world_model={"simulate": lambda: []},
        hms=BrokenHMS(),
        skill_router=sys["router"],
        verifier_swarm=VerificationSwarm(),
        risk_engine={"check": True},
        consensus_engine=sys["bus"],
        execution_planner={"plan": True},
        evolution_gate={"val": True},
        shield=sys["shield"]
    )

    # This should not crash the process loop
    observation = {"price": 100.0, "volatility": 0.1}
    try:
        decision = await csc.process_market_observation(observation)
        assert decision is not None
    except ConnectionError:
        pytest.fail("CSC crashed on HMS failure instead of degrading gracefully")

@pytest.mark.asyncio
async def test_chaos_swarm_disagreement(base_system):
    """
    Fault: Swarm cannot reach consensus.
    Expect: Fail closed (TRADE_REJECTED).
    """
    sys = base_system
    csc = CognitiveSystemController(
        world_model={"simulate": lambda: []},
        hms=sys["hms"],
        skill_router=sys["router"],
        verifier_swarm=DisagreeingSwarm(),
        risk_engine={"check": True},
        consensus_engine=sys["bus"],
        execution_planner={"plan": True},
        evolution_gate={"val": True},
        shield=sys["shield"]
    )

    observation = {"price": 100.0, "volatility": 0.1}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Pivot/Refine" in decision.dominant_rejection_reason or "Verification" in decision.dominant_rejection_reason or "Failed" in decision.dominant_rejection_reason

@pytest.mark.asyncio
async def test_chaos_consensus_voter_missing(base_system):
    """
    Fault: Mandatory Shield voter is missing from bus.
    Expect: LogAct vetoes all actions.
    """
    sys = base_system
    # Create a clean bus without the shield registered
    empty_bus = UnifiedDecisionBus(config={"max_log_size": 10})
    await empty_bus.start()

    csc = CognitiveSystemController(
        world_model={"simulate": lambda: []},
        hms=sys["hms"],
        skill_router=sys["router"],
        verifier_swarm=VerificationSwarm(),
        risk_engine={"check": True},
        consensus_engine=empty_bus,
        execution_planner={"plan": True},
        evolution_gate={"val": True},
        shield=sys["shield"]
    )

    observation = {"price": 100.0, "volatility": 0.1}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Mandatory" in decision.dominant_rejection_reason
    await empty_bus.stop()
