import unittest
import asyncio
from trading_bot.core.unified_registry import registry
from trading_bot.core_agent_system.agent_registry import AgentRegistry, PlannerAgent
from trading_bot.core_agent_system.tool_registry import ToolRegistry, MarketDataTool
from trading_bot.core.service_registry import ServiceRegistry, BaseService, ServiceHealth

class MockService(BaseService):
    async def start(self): pass
    async def stop(self): pass
    async def health_check(self): return ServiceHealth(True, None)

class TestRegistryConsolidation(unittest.TestCase):
    def test_agent_registry_bridge(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        ar = AgentRegistry()
        agent = PlannerAgent({"name": "TestAgent"})
        agent_id = loop.run_until_complete(ar.register_agent(agent))

        # Verify it's in the Unified Registry
        comp = registry.get(agent_id)
        self.assertEqual(comp, agent)

        loop.close()

    def test_tool_registry_bridge(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tr = ToolRegistry()
        tool = MarketDataTool()
        tool_id = loop.run_until_complete(tr.register_tool(tool))

        # Verify it's in the Unified Registry
        comp = registry.get("market_data")
        self.assertEqual(comp, tool)

        loop.close()

    def test_service_registry_bridge(self):
        sr = ServiceRegistry()
        service = MockService()
        service.SERVICE_NAME = "mock_service"
        sr.register(service)

        # Verify it's in the Unified Registry
        comp = registry.get("mock_service")
        self.assertEqual(comp, service)

if __name__ == "__main__":
    unittest.main()
