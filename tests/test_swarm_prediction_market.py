import pytest
import asyncio
from unittest.mock import MagicMock, patch
from trading_bot.core_agent_system.swarm.controller import SwarmController
from trading_bot.core_agent_system.swarm.models import SwarmSignal, SwarmConsensus, SwarmLayer

@pytest.mark.asyncio
async def test_swarm_controller_prediction_market_loop():
    # Mock registry
    registry = MagicMock()
    registry.get_agents_by_role.return_value = []

    # Setup controller
    controller = SwarmController(agent_registry=registry)

    # Task and context
    context = {'market_state': {'price': 100}}

    # Create mock signals
    sig1 = SwarmSignal(
        source_id="Agent1",
        direction=1.0,
        confidence=0.9,
        layer=SwarmLayer.EXPERT,
        timestamp=0,
        metadata={}
    )

    # 1. Test Consensus (Should place bets)
    # We'll mock the layers to return our test signal
    controller.micro_layer.get_signals = MagicMock(return_value=[])
    controller.expert_layer.get_expert_analysis = MagicMock(return_value=asyncio.Future())
    controller.expert_layer.get_expert_analysis.return_value.set_result([sig1])

    with patch.object(controller.prediction_market, 'place_bet') as mock_place_bet:
        consensus = await controller.get_consensus("trading", context)

        assert consensus.direction == 1.0
        # Should have called place_bet
        mock_place_bet.assert_called()

    # 2. Test Record Outcome (Should resolve market)
    outcome = 1.0 # Positive outcome

    with patch.object(controller.prediction_market, 'resolve_market') as mock_resolve:
        await controller.record_outcome(consensus, outcome, context)

        # Verify resolution call
        mock_resolve.assert_called_once_with(outcome)

if __name__ == "__main__":
    pytest.main([__file__])
