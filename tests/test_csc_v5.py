import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome

@pytest.mark.asyncio
async def test_csc_12_step_pipeline(monkeypatch):
    # Mock dependencies
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # Mock Shield to approve (awaited)
    shield_report = MagicMock()
    from trading_bot.core.immutable_shield import GovernanceDecision
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    controller = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    # Mock Hypothesis Gen using AsyncMock
    from trading_bot.core.csc.hypothesis import ReasoningBranch, Hypothesis
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)
    branch.hypotheses.append(Hypothesis(description="Test Hypothesis"))

    controller.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    controller.hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_b": []})

    # Mock Verifier Swarm
    from trading_bot.core.hms.models import VerifierReport
    report = VerifierReport(agent_name="V1", is_valid=True, confidence=0.9, critique="Looks good")
    controller.verifier_swarm.run_swarm = AsyncMock(return_value=[report])

    # Ensure bus is started and patch propose_action cleanly in the test to avoid timeouts
    from trading_bot.core.unified_event_bus import decision_bus, ActionStatus
    await decision_bus.start()

    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)

    observation = {"price_action": "BULLISH", "volatility": 0.01}
    decision = await controller.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert controller.hms.store_ledger_entry.called

    await decision_bus.stop()

@pytest.mark.asyncio
async def test_csc_hasp_guardrail():
    controller = CognitiveSystemController()

    # Observation that triggers volatility guardrail
    observation = {"price_action": "BULLISH", "volatility": 0.1}

    # Normalize state first
    from trading_bot.core.csc.models import MarketContextAdapter
    context = MarketContextAdapter.normalize(observation)

    intervention = controller._apply_hasp_guardrails(context)
    assert intervention.get("max_leverage") == 1.0
    assert intervention.get("reasoning_context") == "CRITICAL_VOLATILITY"

@pytest.mark.asyncio
async def test_csc_pivot_refine():
    controller = CognitiveSystemController()

    from trading_bot.core.csc.hypothesis import ReasoningBranch
    branch = ReasoningBranch(branch_id="test_b", name="Test Branch", confidence=0.9)

    from trading_bot.core.hms.models import VerifierReport
    reports = [VerifierReport(agent_name="V1", is_valid=False, confidence=0.9, critique="Too high risk")]

    refined = await controller._refine_strategy(branch, reports)
    assert refined.confidence < branch.confidence
    assert "Correction: Too high risk" in refined.reasoning_trace
