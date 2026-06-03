import pytest
from trading_bot.core_agent_system.agent_registry import AgentRegistry, PlannerAgent

@pytest.mark.asyncio
async def test_agent_registry_discovery():
    registry = AgentRegistry()
    await registry.initialize()

    planner = PlannerAgent({'name': 'TestPlanner'})
    await registry.register_agent(planner)

    agents = registry.get_agents_by_role('planner')
    assert len(agents) == 1
    assert agents[0].name == 'TestPlanner'

    await registry.shutdown()
