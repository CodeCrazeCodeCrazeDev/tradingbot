"""
Phase 2: Multi-Agent Trading System
"""

from .base_agent import (
    BaseAgent,
    AgentType,
    AgentProposal,
    AgentState,
    AgentCommunication
)

from .specialized_agents import (
    TrendFollowingAgent,
    MeanReversionAgent,
    VolatilityAgent,
    RiskManagerAgent,
    MarketMakerAgent
)

from .coordinator import MultiAgentCoordinator

__all__ = [
    'BaseAgent',
    'AgentType',
    'AgentProposal',
    'AgentState',
    'AgentCommunication',
    'TrendFollowingAgent',
    'MeanReversionAgent',
    'VolatilityAgent',
    'RiskManagerAgent',
    'MarketMakerAgent',
    'MultiAgentCoordinator'
]
