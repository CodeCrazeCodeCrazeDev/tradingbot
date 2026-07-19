import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import LogAction, ActionStatus, decision_bus

@pytest.fixture(autouse=True)
def mock_event_bus(monkeypatch):
    # Mock LogAction.wait_for_decision to return ActionStatus.APPROVED immediately
    async def mock_wait(*args, **kwargs):
        return ActionStatus.APPROVED
    monkeypatch.setattr(LogAction, "wait_for_decision", mock_wait)

    # Mock decision_bus.propose_action to do nothing
    async def mock_propose(*args, **kwargs):
        pass
    monkeypatch.setattr(decision_bus, "propose_action", mock_propose)

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock()
    shield.validate_action = MagicMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"market": {"volatility": 0.5}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Volatility exceeded HASP safety threshold" in decision.dominant_rejection_reason

@pytest.mark.asyncio
async def test_csc_pivot_loop():
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock()
    shield.validate_action = MagicMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock verifier reports failing first attempt
    report_fail = MagicMock(is_valid=False, confidence=0.95, critique="STRATEGIC_FLAW detected")
    report_pass = MagicMock(is_valid=True, confidence=0.9, critique="Looks good")

    csc.verifier_swarm.run_swarm = AsyncMock(side_effect=[[report_fail], [report_pass]])

    obs = {"market": {"volatility": 0.1}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert csc.verifier_swarm.run_swarm.call_count == 2
