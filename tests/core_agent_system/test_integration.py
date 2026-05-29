import asyncio
import pytest
from trading_bot.core_agent_system import IntegratedAgentSystem

@pytest.mark.asyncio
async def test_integrated_system_flow():
    """
    Test the full end-to-end flow of the IntegratedAgentSystem.
    """
    system = IntegratedAgentSystem({
        'storage_path': 'test_integration_data',
        'safety_threshold': 0.7,
        'num_simulations': 10
    })

    await system.initialize()

    task = "Analyze market and provide a clear buy/sell/hold signal with reasoning"
    result = await system.execute_task(task)

    # Assertions
    assert result['success'] is True
    assert result['answer'] is not None
    assert "Task" in result['answer']
    assert "completed" in result['answer']
    assert result['iterations'] > 0

    await system.shutdown()
