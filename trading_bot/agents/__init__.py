"""
Agents Module - Under Hivemind Control
============================================================

All agents in this module are controlled by the Hivemind.
"""

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge

# multi_agent_debate
try:
    from .multi_agent_debate import (
        MultiAgentDebateSystem,
        DebateTopic,
        DebateResult,
        DebateAgent,
    )
except ImportError as e:
    # multi_agent_debate not available
    pass

# Executor agent
try:
    from .executor_agent import ExecutorAgent
except ImportError:
    pass

# Planner agent
try:
    from .planner_agent import PlannerAgent
except ImportError:
    pass

# Verifier agent
try:
    from .verifier_agent import VerifierAgent
except ImportError:
    pass


class HivemindAgentManager:
    """
    Agent Manager under Hivemind Control.
    
    This manager ensures all agents in the agents module are
    controlled by the central hivemind intelligence.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.debate_system = None
        self.executor = None
        self.planner = None
        self.verifier = None
        self._initialized = False
        self._running = False
        self.a2a_bus = self.config.get("a2a_bus") or A2AMessageBus()
        self.world_bridge = self.config.get("world_bridge") or World2AgentBridge(self.a2a_bus)
        self.a2a_bus.register_agent(
            "agents.manager",
            capabilities=["planner_executor_verifier", "interop"],
        )
    
    async def initialize(self):
        """Initialize all agents under hivemind control."""
        # Initialize debate system
        try:
            self.debate_system = MultiAgentDebateSystem(config=self.config)
        except Exception as e:
            pass
        
        # Initialize specialized agents
        try:
            self.executor = ExecutorAgent(config=self.config)
            self.a2a_bus.register_agent("ExecutorAgent", capabilities=["execution"])
        except Exception:
            pass
        
        try:
            self.planner = PlannerAgent(config=self.config)
            self.a2a_bus.register_agent("PlannerAgent", capabilities=["planning"])
        except Exception:
            pass
        
        try:
            self.verifier = VerifierAgent(config=self.config)
            self.a2a_bus.register_agent("VerifierAgent", capabilities=["verification"])
        except Exception:
            pass
        
        self._initialized = True
    
    async def run_debate(self, topic, context=None):
        """Run a multi-agent debate under hivemind supervision."""
        if self.debate_system:
            return await self.debate_system.debate(topic, context)
        return None
    
    def get_status(self):
        """Get status of all managed agents."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'debate_system_active': self.debate_system is not None,
            'executor_active': self.executor is not None,
            'planner_active': self.planner is not None,
            'verifier_active': self.verifier is not None,
            'under_hivemind_control': self.hivemind is not None,
            'a2a_registered_agents': self.a2a_bus.list_agents(),
            'a2a_message_count': self.a2a_bus.message_count(),
        }
    
    async def start(self):
        """Start all agents."""
        self._running = True
    
    async def stop(self):
        """Stop all agents."""
        self._running = False


# Backward compatibility
AgentManager = HivemindAgentManager
AgentOrchestrator = HivemindAgentManager

__all__ = [
    'HivemindAgentManager',
    'AgentManager',
    'AgentOrchestrator',
    'MultiAgentDebateSystem',
    'DebateTopic',
    'DebateResult',
    'DebateAgent',
    'ExecutorAgent',
    'PlannerAgent',
    'VerifierAgent',
]
