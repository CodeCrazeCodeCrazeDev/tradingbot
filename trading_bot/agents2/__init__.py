"""
Agents2 Module - Under Hivemind Control
============================================================

All agents in this module are controlled by the Hivemind.
"""

# coordinator
try:
    from .coordinator import (
        MultiAgentCoordinator,
    )
except ImportError as e:
    pass

# specialized_agents
try:
    from .specialized_agents import (
        RiskManagerAgent,
        PortfolioManagerAgent,
        StrategyOptimizerAgent,
    )
except ImportError as e:
    pass

# base_agent
try:
    from .base_agent import (
        BaseAgent,
        AgentProposal,
        AgentState,
    )
except ImportError:
    pass


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
    
    async def initialize(self):
        """Initialize all Agents2 systems under hivemind control."""
        # Create specialized agents
        try:
            self.agents['risk_manager'] = RiskManagerAgent()
        except Exception:
            pass
        
        try:
            self.agents['portfolio_manager'] = PortfolioManagerAgent()
        except Exception:
            pass
        
        try:
            self.agents['strategy_optimizer'] = StrategyOptimizerAgent()
        except Exception:
            pass
        
        # Create coordinator with all agents
        try:
            self.coordinator = MultiAgentCoordinator(self.agents)
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
        return {
            'initialized': self._initialized,
            'running': self._running,
            'agent_count': len(self.agents),
            'coordinator_active': self.coordinator is not None,
            'under_hivemind_control': self.hivemind is not None,
            'agents': list(self.agents.keys()),
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
    'HivemindAgents2Manager',
    'Agent2Manager',
    'AgentOrchestrator2',
    'MultiAgentCoordinator',
    'RiskManagerAgent',
    'PortfolioManagerAgent',
    'StrategyOptimizerAgent',
    'BaseAgent',
    'AgentProposal',
    'AgentState',
]
