import pytest
import asyncio
from trading_bot.core_agent_system.integrated_system import IntegratedAgentSystem

@pytest.mark.asyncio
async def test_usis_integration():
    config = {
        'storage_path': 'test_core_agent_data',
        'swarm': {
            'exploration_rate': 0.1
        }
    }

    system = IntegratedAgentSystem(config)
    await system.initialize()

    # Test task routing to USIS
    task = "Run swarm analysis on market sentiment"
    context = {'market_state': {'prices': [1.1, 1.2, 1.15, 1.25, 1.3], 'sentiment_score': 0.5}}

    result = await system.execute_task(task, context)

    assert result['success'] is True
    assert 'direction' in result
    assert 'confidence' in result
    assert 'consensus' in result
    assert 'dominant_factors' in result

    print(f"USIS Result: {result['reasoning']}")

    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(test_usis_integration())
