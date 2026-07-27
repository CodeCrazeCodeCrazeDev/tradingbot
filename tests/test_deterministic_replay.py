import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import ActionStatus

@pytest.mark.asyncio
async def test_deterministic_decision_replay():
    """
    Verifies that given identical market observation inputs, the Cognitive System Controller
    inference pipeline produces fully deterministic outputs, with no strategic drift or non-reproducibility.
    """
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    # Force reset singleton for run 1
    CognitiveSystemController._instance = None
    csc_run_1 = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    obs = {
        "price_action": "BULLISH",
        "volatility": 0.1,
        "market": {"volatility": 0.1}
    }

    # Execute Run 1
    decision_1 = await csc_run_1.process_market_observation(obs)

    # Force reset singleton for run 2 to ensure independent initialization
    CognitiveSystemController._instance = None
    csc_run_2 = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    # Execute Run 2 with identical inputs
    decision_2 = await csc_run_2.process_market_observation(obs)

    # Assert exact deterministic match of decisions
    assert decision_1.outcome == decision_2.outcome
    assert decision_1.dominant_rejection_reason == decision_2.dominant_rejection_reason


@pytest.mark.asyncio
async def test_hasp_guardrail_failure_recovery():
    """
    Verifies that the HASP program functions cleanly intercept critical volatility states
    and gracefully recover via a non-bypassable rejection/remedial action.
    """
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    # Force reset singleton
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    # Critical volatility (>0.3) triggering HASP override
    high_vol_obs = {
        "price_action": "BULLISH",
        "volatility": 0.45,
        "market": {"volatility": 0.45}
    }

    decision = await csc.process_market_observation(high_vol_obs)

    # Verify fail-safe rejection
    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Volatility exceeded HASP safety threshold (0.3)" in decision.dominant_rejection_reason
