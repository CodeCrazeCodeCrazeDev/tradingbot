import pytest
import asyncio
import torch
from unittest.mock import MagicMock, AsyncMock, patch
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.immutable_shield import ImmutableShield, GovernanceDecision

@pytest.mark.asyncio
async def test_e2e_pipeline_full_path():
    """
    Verifies the end-to-end decision path:
    Observation -> CSC -> Hypothesis -> Simulation -> Swarm -> Shield -> Approved
    """
    # 1. Setup mocks for each stage
    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock(spec=ImmutableShield)

    # Mock Shield to APPROVE
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.APPROVED
    shield.validate_action.return_value = shield_report

    # Mock Hypothesis Generation
    mock_branch = MagicMock()
    mock_branch.branch_id = "test_branch"
    mock_branch.hypotheses = [MagicMock(description="Test Hypothesis")]

    hypothesis_gen = MagicMock()
    hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[mock_branch])
    hypothesis_gen.simulate_branches = AsyncMock(return_value={"test_branch": [MagicMock(name="Scenario_A")]})

    # Mock Verification Swarm
    verifier_swarm = MagicMock()
    mock_report = MagicMock()
    mock_report.is_valid = True
    mock_report.confidence = 0.9
    verifier_swarm.run_swarm = AsyncMock(return_value=[mock_report])

    # 2. Initialize CSC with mocks
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)
    csc.hypothesis_gen = hypothesis_gen
    csc.verifier_swarm = verifier_swarm

    # 3. Trigger observation
    observation = {"symbol": "EURUSD", "price": 1.1000, "volatility": 0.1}
    decision = await csc.process_market_observation(observation)

    # 4. Assertions
    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert hypothesis_gen.generate_competing_branches.called
    assert hypothesis_gen.simulate_branches.called
    assert verifier_swarm.run_swarm.called
    assert shield.validate_action.called
    assert hms.store_ledger_entry.called

@pytest.mark.asyncio
async def test_pipeline_rejection_by_swarm():
    """Verifies that the Swarm can block flawed trades."""
    shield = MagicMock(spec=ImmutableShield)

    # Mock Swarm to REJECT (Veto)
    verifier_swarm = MagicMock()
    veto_report = MagicMock()
    veto_report.is_valid = False
    veto_report.confidence = 0.95
    verifier_swarm.run_swarm = AsyncMock(return_value=[veto_report])

    # Mock Hypothesis
    mock_branch = MagicMock()
    mock_branch.branch_id = "b1"
    hypothesis_gen = MagicMock()
    hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[mock_branch])
    hypothesis_gen.simulate_branches = AsyncMock(return_value={"b1": []})

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(shield=shield)
    csc.hypothesis_gen = hypothesis_gen
    csc.verifier_swarm = verifier_swarm

    observation = {"price": 1.0}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Failed Pivot/Refine loop" in decision.dominant_rejection_reason

@pytest.mark.asyncio
async def test_pipeline_rejection_by_shield():
    """Verifies that the Immutable Shield is a non-bypassable gate."""
    shield = MagicMock(spec=ImmutableShield)

    # Mock Shield to BLOCK
    shield_report = MagicMock()
    shield_report.decision = GovernanceDecision.BLOCKED
    shield_report.reason = "Risk Limit Exceeded"
    shield.validate_action.return_value = shield_report

    # Mock Swarm to APPROVE
    verifier_swarm = MagicMock()
    ok_report = MagicMock()
    ok_report.is_valid = True
    ok_report.confidence = 1.0
    verifier_swarm.run_swarm = AsyncMock(return_value=[ok_report])

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(shield=shield)

    # Patch internals
    csc.hypothesis_gen.generate_competing_branches = AsyncMock(return_value=[MagicMock(branch_id="b1")])
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={"b1": []})
    csc.verifier_swarm = verifier_swarm

    observation = {"price": 1.0}
    decision = await csc.process_market_observation(observation)

    assert decision.outcome == DecisionOutcome.TRADE_REJECTED
    assert "Shield: Risk Limit Exceeded" in decision.dominant_rejection_reason
