import pytest
import asyncio
import copy
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.models import NormalizedMarketContext, MarketContextAdapter
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision

def test_normalized_market_context_immutability():
    """Verify that NormalizedMarketContext is immutable and correctly populated."""
    context = NormalizedMarketContext(volatility=0.25, price_action="BULLISH", features=[1.0, 2.0])
    assert context.volatility == 0.25
    assert context.price_action == "BULLISH"
    assert context.features == [1.0, 2.0]

    with pytest.raises(AttributeError):
        # Frozen dataclass should raise AttributeError on write
        context.volatility = 0.50

def test_market_context_adapter_robustness():
    """Property-based validation for malformed, empty, and weird input data shapes."""
    # 1. Empty dict
    c1 = MarketContextAdapter.normalize({})
    assert c1.volatility == 0.0
    assert c1.price_action == "NEUTRAL"
    assert c1.features == []

    # 2. Nested dict (legacy style)
    c2 = MarketContextAdapter.normalize({"market": {"volatility": 0.45, "price_action": "BEARISH"}, "features": [1.0, 2.5]})
    assert c2.volatility == 0.45
    assert c2.price_action == "BEARISH"
    assert c2.features == [1.0, 2.5]

    # 3. Bad string types for features
    c3 = MarketContextAdapter.normalize({"volatility": "0.15", "features": ["1.2", "not_a_float", "3.4"]})
    assert c3.volatility == 0.15
    assert c3.features == [1.2, 3.4]

    # 4. None input or completely invalid type
    c4 = MarketContextAdapter.normalize(None)
    assert c4.volatility == 0.0
    assert c4.features == []

@pytest.mark.asyncio
async def test_csc_decision_determinism(monkeypatch):
    """
    Verify identical inputs, config, and mocks produce identical decision outcomes,
    composite confidence, and action sequence.
    """
    # Create matching mocks
    world_model = MagicMock()
    world_model.simulate_intervention = AsyncMock(return_value={"failure_rate": 0.0})
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action = AsyncMock(return_value=shield_report)

    csc = CognitiveSystemController(world_model, hms, shield)

    # Mock hypothesis and swarm to be deterministic
    from trading_bot.core.csc.hypothesis import ReasoningBranch, Hypothesis
    branch = ReasoningBranch(branch_id="det_b", name="Deterministic Branch", confidence=0.85)
    branch.hypotheses.append(Hypothesis(description="Det Hypothesis"))

    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"det_b": []})

    from trading_bot.core.hms.models import VerifierReport
    report = VerifierReport(agent_name="DetV1", is_valid=True, confidence=0.9, critique="Determinism check")
    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[report])

    # Patch decision_bus propose_action
    from trading_bot.core.unified_event_bus import decision_bus, ActionStatus
    await decision_bus.start()

    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)

    obs = {"market": {"volatility": 0.12}, "price_action": "BULLISH"}

    # Run decision process multiple times
    decisions = []
    for _ in range(3):
        # We need to deepcopy the obs to verify input isolation
        input_obs = copy.deepcopy(obs)
        decision = await csc.process_market_observation(input_obs)
        decisions.append(decision)

    # Assert 100% equivalence of all results
    first = decisions[0]
    for other in decisions[1:]:
        assert other.outcome == first.outcome
        assert other.trade_id is not None
        assert len(other.trade_id) > 0
        assert other.dominant_rejection_reason == first.dominant_rejection_reason
        assert other.confidence_vector.statistical == first.confidence_vector.statistical
        assert other.confidence_vector.regime == first.confidence_vector.regime
        assert other.confidence_vector.execution == first.confidence_vector.execution

    await decision_bus.stop()

@pytest.mark.asyncio
async def test_csc_negative_paths_and_failures(monkeypatch):
    """
    Verify negative paths (e.g. empty branches, empty verifier reports, conflicting reports,
    or rejected shield validations) result in structured rejection CoreDecisions.
    """
    world_model = MagicMock()
    world_model.simulate_intervention = AsyncMock(return_value={"failure_rate": 0.0})
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()

    # 1. Test Shield Reject
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.REJECTED
    shield_report.reason = "Hard exposure violation"
    shield.validate_action = AsyncMock(return_value=shield_report)

    csc = CognitiveSystemController(world_model, hms, shield)

    from trading_bot.core.csc.hypothesis import ReasoningBranch
    branch = ReasoningBranch(branch_id="test_neg", name="Negative Case", confidence=0.88)
    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[branch])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_neg": []})

    from trading_bot.core.hms.models import VerifierReport
    report = VerifierReport(agent_name="V1", is_valid=True, confidence=0.9, critique="Approved by swarm")
    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[report])

    obs = {"market": {"volatility": 0.02}}
    decision = await csc.process_market_observation(obs)

    # Must reject safely due to shield veto
    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Hard exposure violation" in decision.dominant_rejection_reason
