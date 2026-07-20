import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus, LogAction, ActionStatus

@pytest.fixture(autouse=True)
def mock_decision_bus(monkeypatch):
    """Fixture to mock LogAct decision bus to prevent hangs and timeouts."""
    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        return

    async def mock_wait_for_decision(self, timeout=5.0):
        self.status = ActionStatus.EXECUTED
        return ActionStatus.EXECUTED

    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)
    monkeypatch.setattr(LogAction, "wait_for_decision", mock_wait_for_decision)

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
async def test_csc_pivot_loop(monkeypatch):
    # Setup mocks
    world_model = MagicMock()
    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    hms.store_ledger_entry = MagicMock()

    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc = CognitiveSystemController(world_model, hms, shield)

    # Monkeypatch select_optimal_branch to return a high-confidence branch
    orig_select = csc._select_optimal_branch
    def mock_select_optimal_branch(branches, sims):
        branch = orig_select(branches, sims)
        if branch:
            branch.confidence = 1.0
        return branch
    monkeypatch.setattr(csc, "_select_optimal_branch", mock_select_optimal_branch)

    # Mock verifier reports failing first attempt
    report_fail = MagicMock(is_valid=False, confidence=0.95, critique="STRATEGIC_FLAW detected")
    report_pass = MagicMock(is_valid=True, confidence=0.9, critique="Looks good")

    csc.verifier_swarm.run_swarm = AsyncMock(side_effect=[[report_fail], [report_pass]])

    obs = {"market": {"volatility": 0.1}, "features": [0.1, 0.2]}

    decision = await csc.process_market_observation(obs)

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    assert csc.verifier_swarm.run_swarm.call_count == 2
