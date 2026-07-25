import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # We want shield validation to succeed, or return a mock decision
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
async def test_csc_pivot_loop(monkeypatch):
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # We want shield validation to succeed, or return a mock decision
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock hypothesis generator to return deterministic branches with high confidence
    from trading_bot.core.csc.hypothesis import ReasoningBranch, Hypothesis
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)
    branch.hypotheses.append(Hypothesis(description="Test Hypothesis"))

    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_b": []})

    # Mock verifier reports failing first attempt
    report_fail = MagicMock(is_valid=False, confidence=0.95, critique="STRATEGIC_FLAW detected")
    report_pass = MagicMock(is_valid=True, confidence=0.9, critique="Looks good")

    csc.verifier_swarm.run_swarm = AsyncMock(side_effect=[[report_fail], [report_pass]])

    # Mock proposal execution to prevent timeouts
    from trading_bot.core.unified_event_bus import decision_bus, ActionStatus
    await decision_bus.start()

    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)

    obs = {"market": {"volatility": 0.1}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert csc.verifier_swarm.run_swarm.call_count == 2

    await decision_bus.stop()
