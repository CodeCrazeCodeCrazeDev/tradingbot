"""
UCA V5 End-to-End Decision Pipeline Validation
==============================================

Validates the full authoritative orchestration path:
Market Data -> CSC -> World Model -> Consensus -> Execution Plan
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.router import SkillRouter
from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.verification.swarm import VerificationSwarm
from trading_bot.core.immutable_shield import ImmutableShield
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, ActionStatus, LogAction
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

# Mock dependencies for E2E testing
class MockWorldModel:
    async def simulate(self, *args, **kwargs): return []
    def predict(self, *args, **kwargs): return {"price": 100.0}

class MockRiskEngine:
    def check_risk(self, *args, **kwargs): return True

class MockExecutionPlanner:
    def plan_execution(self, *args, **kwargs): return {"plan": "execute_now"}

class MockEvolutionGate:
    def validate_evolution(self, *args, **kwargs): return True

@pytest.fixture(scope="function")
def full_system(event_loop):
    # 1. Initialize core infrastructure
    hms = HierarchicalMemorySystem(base_path="tests/temp_hms_e2e")
    bus = UnifiedDecisionBus()
    shield = ImmutableShield()
    router = SkillRouter()
    swarm = VerificationSwarm()

    # Wrapper for shield to match LogAct voter interface
    async def shield_voter(action):
        report = await shield.validate_action(action.action_type, action.payload, action.payload.get("context", {}))
        return {"decision": report.decision.value, "reason": report.reason}

    # 2. Register mandatory voters
    bus.register_voter("ImmutableShield", shield_voter)
    event_loop.run_until_complete(bus.start())

    # 3. Initialize One Brain (CSC)
    csc = CognitiveSystemController(
        world_model=MockWorldModel(),
        hms=hms,
        skill_router=router,
        verifier_swarm=swarm,
        risk_engine=MockRiskEngine(),
        consensus_engine=bus,
        execution_planner=MockExecutionPlanner(),
        evolution_gate=MockEvolutionGate(),
        shield=shield
    )

    yield csc
    event_loop.run_until_complete(bus.stop())

@pytest.mark.asyncio
async def test_e2e_successful_trade_pipeline(full_system):
    """
    Validates that a normal market observation correctly propagates
    through the entire 12-step pipeline to execution.
    """
    csc = full_system

    # Simulate market observation
    observation = {
        "symbol": "BTC/USDT",
        "price": 50000.0,
        "volatility": 0.1,
        "regime": "bull"
    }

    # Process through One Brain
    decision = await csc.process_market_observation(observation)

    # Assertions for successful propagation
    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert decision.trade_id is not None
    assert decision.confidence_vector.statistical > 0

    # Verify audit trail in LogAct
    assert len(csc.consensus_engine._log) > 0
    last_log = csc.consensus_engine._log[-1]
    assert last_log.status == ActionStatus.EXECUTED
    assert "ImmutableShield" in last_log.voter_reports

@pytest.mark.asyncio
async def test_e2e_risk_veto_pipeline(full_system):
    """
    Validates that a high-volatility observation triggers HASP intervention
    and correctly halts/rejects the trade.
    """
    csc = full_system

    # Simulate high volatility (Triggers HASP Guardrail)
    observation = {
        "symbol": "BTC/USDT",
        "price": 50000.0,
        "volatility": 0.6,
        "regime": "unstable"
    }

    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
