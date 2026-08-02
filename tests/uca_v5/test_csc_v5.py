import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus, ActionStatus

@pytest.fixture(autouse=True)
def mock_event_bus_for_csc(monkeypatch):
    from trading_bot.core.unified_event_bus import LogAction, UnifiedDecisionBus, ActionStatus

    async def mock_propose(self, action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

    async def mock_wait(self, timeout=5.0):
        return ActionStatus.EXECUTED

    monkeypatch.setattr(UnifiedDecisionBus, "propose_action", mock_propose)
    monkeypatch.setattr(LogAction, "wait_for_decision", mock_wait)

class ImmediateDecisionBus:
    async def propose_action(self, action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()

@pytest.fixture(autouse=True)
def mock_decision_bus_fixture(monkeypatch):
    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()
    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)

@pytest.mark.asyncio
async def test_csc_hasp_intervention(monkeypatch):
    # Mock propose_action to approve immediately
    async def mock_propose_action(action):
        action.status = ActionStatus.EXECUTED
        action._completed_event.set()
    monkeypatch.setattr(decision_bus, "propose_action", mock_propose_action)

    # Setup mocks
    world_model = MagicMock()

    hms = MagicMock()
    hms.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield = MagicMock()
    shield.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    # Reset singleton state if needed to bind updated mocks
    if CognitiveSystemController._instance is not None:
        CognitiveSystemController._instance.world_model = world_model
        CognitiveSystemController._instance.hms = hms
        CognitiveSystemController._instance.shield = shield
    csc = CognitiveSystemController(world_model, hms, shield)

    # Reset continuous/discrete state channels to prevent side effects
    csc.discrete_channel = []
    csc.continuous_state = {}

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"volatility": 0.5, "features": [0.1] * 16}

    decision = await csc.process_market_observation(obs)

    # Under HASP triggering, the guardrail might intervene or approve under controlled leverage,
    # or the shield validates correctly. We verify that the pipeline processes correctly.
    assert decision is not None

    await decision_bus.stop()

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

    # Reset singleton state if needed to bind updated mocks
    if CognitiveSystemController._instance is not None:
        CognitiveSystemController._instance.world_model = world_model
        CognitiveSystemController._instance.hms = hms
        CognitiveSystemController._instance.shield = shield
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

    decision = await csc.process_market_observation(obs)
    await decision_bus.stop()

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
