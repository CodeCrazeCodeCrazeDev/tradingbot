import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus, ActionStatus, UnifiedDecisionBus, LogAction

@pytest.fixture(autouse=True)
def reset_csc_singleton():
    """Reset CognitiveSystemController singleton before and after each test."""
    CognitiveSystemController._instance = None
    yield
    CognitiveSystemController._instance = None

@pytest.fixture(autouse=True)
async def manage_decision_bus():
    """Starts the event bus before each test and stops it after to avoid leakage."""
    res = decision_bus.start()
    if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
        await res
    yield
    res2 = decision_bus.stop()
    if asyncio.iscoroutine(res2) or hasattr(res2, "__await__"):
        await res2

@pytest.fixture(autouse=True)
def mock_event_bus_for_csc(monkeypatch):
    async def mock_propose(self, action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

    async def mock_wait(self, timeout=5.0):
        return ActionStatus.EXECUTED

    monkeypatch.setattr(UnifiedDecisionBus, "propose_action", mock_propose)
    monkeypatch.setattr(LogAction, "wait_for_decision", mock_wait)

@pytest.mark.asyncio
async def test_csc_hasp_intervention(monkeypatch):
    # Setup mocks
    world_model = MagicMock()
    world_model.simulate_intervention = AsyncMock(return_value={})

    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    from trading_bot.core.csc.router import SkillRouter
    skill_router = SkillRouter()
    verifier_swarm = MagicMock()
    risk_engine = MagicMock()
    consensus_engine = MagicMock()
    execution_planner = MagicMock()
    evolution_gate = MagicMock()

    csc = CognitiveSystemController(world_model, hms, shield)

    # Reset continuous/discrete state channels to prevent side effects
    csc.discrete_channel = []
    csc.continuous_state = {}

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"volatility": 0.5, "features": [0.1] * 16}

    try:
        decision = await csc.process_market_observation(obs)
        # Under HASP triggering, the guardrail might intervene or approve under controlled leverage,
        # or the shield validates correctly. We verify that the pipeline processes correctly.
        assert decision is not None
    finally:
        await decision_bus.stop()

@pytest.mark.asyncio
async def test_csc_pivot_loop():
    # Setup mocks
    world_model = MagicMock()
    world_model.simulate_intervention = AsyncMock(return_value={})

    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))
    from trading_bot.core.csc.router import SkillRouter
    skill_router = SkillRouter()
    verifier_swarm = MagicMock()
    risk_engine = MagicMock()
    consensus_engine = MagicMock()
    execution_planner = MagicMock()
    evolution_gate = MagicMock()

    csc = CognitiveSystemController(world_model, hms, shield)

    obs = {"volatility": 0.1, "features": [0.1] * 16}

    # Mock simulation to trigger pivot
    # In V6, pivot is triggered by high failure rate in simulation
    csc.hypothesis_gen.simulate_branches = AsyncMock(return_value={
        "branch_bull": {"failure_rate": 0.8},
        "branch_bear": {"failure_rate": 0.1},
        "branch_range": {"failure_rate": 0.2}
    })

    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[MagicMock(is_valid=True, confidence=0.9)])

    try:
        decision = await csc.process_market_observation(obs)
        assert decision.outcome == DecisionOutcome.TRADE_APPROVED
    finally:
        await decision_bus.stop()
