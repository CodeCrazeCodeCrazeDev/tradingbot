"""
Tests validating Deterministic Replay and Causal Correctness.
Ensures that identical random seed, configuration, and market inputs produce identical decisions.
"""

import pytest
import numpy as np
import random
from unittest.mock import MagicMock, AsyncMock

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome, CoreDecision
from trading_bot.core.immutable_shield import GovernanceDecision
from trading_bot.core.unified_event_bus import ActionStatus, LogAction, decision_bus

def set_all_seeds(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

@pytest.fixture(autouse=True)
def mock_event_bus():
    async def mock_propose(action, *args, **kwargs):
        action.status = ActionStatus.EXECUTED
    LogAction.wait_for_decision = AsyncMock(return_value=ActionStatus.APPROVED)
    decision_bus.propose_action = mock_propose

@pytest.mark.asyncio
async def test_deterministic_decision_replay():
    """Verifies that identical seed and observation inputs yield identical decisions."""
    # Run 1
    set_all_seeds(42)
    world_model_1 = MagicMock()
    hms_1 = MagicMock()
    hms_1.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield_1 = MagicMock()
    shield_1.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc_1 = CognitiveSystemController(world_model_1, hms_1, shield_1)

    obs = {"market": {"volatility": 0.15}, "features": [0.5, -0.2, 0.1]}

    # We clear discrete channel to ensure a clean start
    csc_1.discrete_channel.clear()
    decision_1 = await csc_1.process_market_observation(obs)

    # Run 2
    set_all_seeds(42)
    world_model_2 = MagicMock()
    hms_2 = MagicMock()
    hms_2.retrieve_evidence_chain = AsyncMock(return_value=[])
    shield_2 = MagicMock()
    shield_2.validate_action = AsyncMock(return_value=MagicMock(decision=GovernanceDecision.APPROVED))

    csc_2 = CognitiveSystemController(world_model_2, hms_2, shield_2)
    csc_2.discrete_channel.clear()
    decision_2 = await csc_2.process_market_observation(obs)

    # Assert identical outcomes
    assert decision_1.outcome == decision_2.outcome
    assert decision_1.dominant_rejection_reason == decision_2.dominant_rejection_reason
    assert csc_1.discrete_channel == csc_2.discrete_channel
