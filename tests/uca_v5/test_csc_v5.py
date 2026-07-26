import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus

@pytest.fixture(autouse=True)
def reset_csc_singleton():
    """Reset the CognitiveSystemController singleton before/after each test."""
    CognitiveSystemController._instance = None
    yield
    CognitiveSystemController._instance = None

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
    # Setup mocks
    world_model = MagicMock()

    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])

    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"market": {"volatility": 0.5}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Volatility exceeded HASP safety threshold" in decision.dominant_rejection_reason

@pytest.mark.asyncio
async def test_csc_pivot_loop():
    # Ensure bus is started
    await decision_bus.start()

    # Setup mocks
    world_model = MagicMock()

    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])

    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock verifier reports failing first attempt
    report_fail = MagicMock(is_valid=False, confidence=0.95, critique="STRATEGIC_FLAW detected")
    report_pass = MagicMock(is_valid=True, confidence=0.9, critique="Looks good")

    csc.verifier_swarm.run_swarm = AsyncMock(side_effect=[[report_fail], [report_pass]])

    obs = {"market": {"volatility": 0.1}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    await decision_bus.stop()

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert csc.verifier_swarm.run_swarm.call_count == 2
