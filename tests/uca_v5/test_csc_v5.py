import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import decision_bus

@pytest.mark.asyncio
async def test_csc_hasp_intervention():
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

    # Observation triggering volatility guardrail (volatility > 0.3)
    obs = {"volatility": 0.5, "features": [0.1] * 16}

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

    from trading_bot.core.unified_event_bus import decision_bus
    await decision_bus.start()

    csc.verifier_swarm.run_swarm = AsyncMock(return_value=[MagicMock(is_valid=True, confidence=0.9)])

    decision = await csc.process_market_observation(obs)
    await decision_bus.stop()

    assert decision.outcome == DecisionOutcome.TRADE_APPROVED
