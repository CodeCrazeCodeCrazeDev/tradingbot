"""
Agents2 Module - Under Hivemind Control.

All agents in this module are controlled by the Hivemind.
"""

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge

try:
    from .coordinator import MultiAgentCoordinator
except ImportError:
    MultiAgentCoordinator = None

try:
    from .specialized_agents import (
        MeanReversionAgent,
        RiskManagerAgent,
        TrendFollowingAgent,
        VolatilityAgent,
    )
except ImportError:
    MeanReversionAgent = None
    RiskManagerAgent = None
    TrendFollowingAgent = None
    VolatilityAgent = None

try:
    from .base_agent import AgentProposal, AgentState, BaseAgent
except ImportError:
    AgentProposal = None
    AgentState = None
    BaseAgent = None


class HivemindAgents2Manager:
    """
    Agents2 Manager under Hivemind Control.

    This manager ensures all Agents2 systems are controlled by
    the central hivemind intelligence.
    """

    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.coordinator = None
        self.agents = {}
        self._initialized = False
        self._running = False
        self.a2a_bus = self.config.get("a2a_bus") or A2AMessageBus()
        self.world_bridge = self.config.get("world_bridge") or World2AgentBridge(self.a2a_bus)
        self.a2a_bus.register_agent(
            "agents2.manager",
            capabilities=["management", "market_analysis", "interop"],
        )

    async def initialize(self):
        """Initialize all Agents2 systems under hivemind control."""
        agent_factories = {
            "trend": TrendFollowingAgent,
            "mean_reversion": MeanReversionAgent,
            "volatility": VolatilityAgent,
            "risk_manager": RiskManagerAgent,
        }

        for agent_name, factory in agent_factories.items():
            if factory is None:
                continue
            try:
                self.agents[agent_name] = factory()
            except Exception:
                pass

        try:
            if MultiAgentCoordinator is not None:
                self.coordinator = MultiAgentCoordinator(
                    self.agents,
                    a2a_bus=self.a2a_bus,
                    world_bridge=self.world_bridge,
                )
        except Exception:
            pass

        self._initialized = True

    def analyze_market(self, market_data: dict):
        """Run market analysis through coordinated agents."""
        if self.coordinator:
            proposals = self.coordinator.get_proposals(market_data)
            return self.coordinator.aggregate_decisions(proposals)
        return None

    def get_agent_rankings(self):
        """Get agent performance rankings."""
        if self.coordinator:
            return self.coordinator.get_agent_rankings()
        return []

    def get_status(self):
        """Get status of all managed agents."""
        interop_status = (
            self.coordinator.get_interoperability_status()
            if self.coordinator and hasattr(self.coordinator, "get_interoperability_status")
            else None
        )
        return {
            "initialized": self._initialized,
            "running": self._running,
            "agent_count": len(self.agents),
            "coordinator_active": self.coordinator is not None,
            "under_hivemind_control": self.hivemind is not None,
            "agents": list(self.agents.keys()),
            "interop": interop_status,
        }

    async def start(self):
        """Start all Agents2 systems."""
        self._running = True

    async def stop(self):
        """Stop all Agents2 systems."""
        self._running = False


# Backward compatibility
Agent2Manager = HivemindAgents2Manager
AgentOrchestrator2 = HivemindAgents2Manager

__all__ = [
    "HivemindAgents2Manager",
    "Agent2Manager",
    "AgentOrchestrator2",
    "MultiAgentCoordinator",
    "TrendFollowingAgent",
    "MeanReversionAgent",
    "VolatilityAgent",
    "RiskManagerAgent",
    "BaseAgent",
    "AgentProposal",
    "AgentState",
]
