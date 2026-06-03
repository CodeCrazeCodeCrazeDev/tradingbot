import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from trading_bot.core_agent_system.agent_registry import (
    AgentRegistry, AgentRole, AgentStatus, PlannerAgent, BaseAgent
)
from trading_bot.core_agent_system.tool_registry import (
    ToolRegistry, BaseTool, ToolSchema, ToolCategory
)
from trading_bot.core_agent_system.master_orchestrator import (
    MasterOrchestrator, SystemContext, DecisionPriority
)

@pytest.mark.asyncio
async def test_agent_registry_lifecycle():
    registry = AgentRegistry()
    await registry.initialize()

    agent = PlannerAgent({'name': 'TestPlanner'})
    agent_id = await registry.register_agent(agent)

    assert agent_id in registry.agents
    assert len(registry.get_agents_by_role(AgentRole.PLANNER)) == 1

    status = registry.get_status()
    assert status['total_agents'] == 1
    assert status['role_distribution']['planner'] == 1

    await registry.unregister_agent(agent_id)
    assert agent_id not in registry.agents
    assert agent.status == AgentStatus.TERMINATED

    await registry.shutdown()

@pytest.mark.asyncio
async def test_tool_registry_validation():
    registry = ToolRegistry()
    # Mock default tools for this test
    registry._register_default_tools = AsyncMock()
    await registry.initialize()

    class TestTool(BaseTool):
        def _define_schema(self):
            return ToolSchema(
                name="test_tool",
                description="A test tool",
                parameters={"param1": {"type": "string"}},
                required=["param1"]
            )
        async def _execute(self, params):
            return {"success": True, "result": params["param1"]}

    tool = TestTool("test_tool", "A test tool")
    await registry.register_tool(tool)

    # Valid call
    result = await registry.execute_tool("test_tool", {"param1": "hello"})
    assert result["success"] is True
    assert result["result"] == "hello"

    # Invalid call (missing param)
    result = await registry.execute_tool("test_tool", {})
    assert result["success"] is False
    assert "Missing required parameter" in result["error"]

    await registry.shutdown()

@pytest.mark.asyncio
async def test_master_orchestrator_decision_fusion():
    orchestrator = MasterOrchestrator()

    # Mock dependencies
    orchestrator.policy_network = AsyncMock()
    orchestrator.policy_network.predict.return_value = {
        'actions': [{'type': 'hold', 'action': {}, 'probability': 0.9}]
    }

    orchestrator.value_network = AsyncMock()
    orchestrator.value_network.evaluate.return_value = 0.8

    orchestrator.agent_registry = AsyncMock()
    orchestrator.agent_registry.get_all_proposals.return_value = [
        {'type': 'buy', 'action': {'operation': 'open_long'}, 'confidence': 0.7, 'source_agent': 'agent1'}
    ]

    orchestrator.memory_system = AsyncMock()
    orchestrator.memory_system.retrieve_similar.return_value = []

    context = SystemContext(
        timestamp=datetime.now(),
        market_state={'trend': 'bullish', 'volatility': 0.01},
        portfolio_state={'exposure': 0},
        agent_states={},
        pending_decisions=[],
        recent_outcomes=[],
        risk_metrics={'var': 0.01}
    )

    # Test candidate generation
    candidates = await orchestrator._generate_candidate_actions(context)
    # 1 from policy (hold), 1 from agent (buy), 1 default hold
    assert len(candidates) >= 2

    # Test evaluation
    evaluated = await orchestrator._evaluate_candidates(context, candidates)
    assert len(evaluated) == len(candidates)
    assert 'value' in evaluated[0]

    # Test MCTS search with our prioritization fix
    best = await orchestrator._mcts_search(context, evaluated)
    assert best is not None
