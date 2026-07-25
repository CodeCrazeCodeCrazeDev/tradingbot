import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import ActionStatus

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

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
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # Mock shield.validate_action to return approved governance decision
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock verifier reports failing first attempt
    report_fail = MagicMock(is_valid=False, confidence=0.95, critique="STRATEGIC_FLAW detected")
    report_pass = MagicMock(is_valid=True, confidence=0.9, critique="Looks good")

    csc.verifier_swarm.run_swarm = AsyncMock(side_effect=[[report_fail], [report_pass]])

    obs = {"market": {"volatility": 0.1}, "features": [0.1, 0.2]}

    with patch("trading_bot.core.unified_event_bus.decision_bus.propose_action", new_callable=AsyncMock) as mock_propose:
        async def side_effect(act):
            act.status = ActionStatus.EXECUTED
        mock_propose.side_effect = side_effect

        decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert csc.verifier_swarm.run_swarm.call_count == 2
