import asyncio

from trading_bot.a2a import A2AMessageBus
from trading_bot.agents2.base_agent import AgentProposal, AgentType, BaseAgent
from trading_bot.agents2.coordinator import MultiAgentCoordinator
from trading_bot.radar_ai.agents.meta_orchestrator import MetaOrchestrator
from trading_bot.world2agent import World2AgentBridge


class StubAgent(BaseAgent):
    def analyze_market(self, market_data):
        return AgentProposal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action="BUY",
            confidence=0.75,
            reasoning="stub signal",
            expected_return=0.01,
            risk_score=0.2,
            priority=2,
        )

    def get_strategy_name(self) -> str:
        return "Stub Strategy"


def test_a2a_bus_routes_direct_messages():
    bus = A2AMessageBus()
    bus.register_agent("planner", capabilities=["planning"])
    bus.register_agent("executor", capabilities=["execution"])

    bus.send(
        sender="planner",
        recipients=["executor"],
        intent="trade_plan",
        payload={"symbol": "EURUSD"},
        channel="test",
    )

    messages = bus.get_messages("executor", intent="trade_plan")
    assert len(messages) == 1
    assert messages[0].payload["symbol"] == "EURUSD"
    assert bus.message_count() == 1


def test_world2agent_bridge_enriches_agent_payload():
    bus = A2AMessageBus()
    bus.register_agent("agent-1")
    bus.register_agent("agent-2")
    bridge = World2AgentBridge(bus)

    snapshot = bridge.publish_world_state(
        source="world-model",
        world_state={"regime": "risk_on", "volatility": 1.2},
        audience=["agent-1", "agent-2"],
        tags=["market"],
    )
    payload = bridge.build_agent_context("agent-1", {"task": "analyze"})

    assert payload["world_context_id"] == snapshot.context_id
    assert payload["world_context"]["world_state"]["regime"] == "risk_on"
    assert len(bus.get_messages("agent-1", intent="world_state")) == 1


def test_agents2_coordinator_publishes_world_context_and_decision():
    bus = A2AMessageBus()
    bridge = World2AgentBridge(bus)
    agents = {
        "agent_a": StubAgent("agent_a", AgentType.TREND_FOLLOWER),
        "agent_b": StubAgent("agent_b", AgentType.MEAN_REVERTER),
    }
    coordinator = MultiAgentCoordinator(agents, a2a_bus=bus, world_bridge=bridge)

    proposals = coordinator.get_proposals({"price": 100, "volatility": 1.0})
    decision = coordinator.aggregate_decisions(proposals, method="weighted_vote")
    interop_status = coordinator.get_interoperability_status()

    assert decision["action"] == "BUY"
    assert bridge.snapshot_count() >= 1
    assert interop_status["message_count"] >= 3
    assert len(bus.get_messages("agent_a", intent="collective_decision")) == 1


def test_meta_orchestrator_uses_world_context_in_a2a_requests():
    bus = A2AMessageBus()
    bridge = World2AgentBridge(bus)
    orchestrator = MetaOrchestrator(
        auto_approve_simulations=True,
        a2a_bus=bus,
        world_bridge=bridge,
    )
    orchestrator.register_agent("SimulationAgent", object())

    bridge.publish_world_state(
        source="world-model",
        world_state={"symbol": "EURUSD", "simulation_bias": "bullish"},
        audience=["SimulationAgent", orchestrator.orchestrator_id],
        context_type="simulation",
    )

    request = asyncio.run(
        orchestrator.submit_request(
            agent_name="SimulationAgent",
            request_type="run_simulation",
            payload={"experiment_id": "EXP-1"},
            requires_approval=False,
        )
    )

    orchestrator_messages = bus.get_messages(orchestrator.orchestrator_id, intent="agent_request")
    assert request.status.value == "approved"
    assert len(orchestrator_messages) == 1
    assert "world_context_id" in orchestrator_messages[0].payload
    assert orchestrator.get_status()["latest_world_context_id"] is not None
