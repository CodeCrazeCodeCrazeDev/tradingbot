"""
agents package
"""

try:
    from .executor_agent import ExecutorAgent, create_executor_agent
    from .multi_agent_debate import (
        AgentArgument,
        AgentRole,
        Conviction,
        DebateRound,
        FinalDecision,
        HeadAI,
        MacroStrategist,
        MarketContext,
        MultiAgentDebateSystem,
        RiskSentinel,
        TacticalExecutioner,
        TradeAction,
        TradingAgent,
        create_debate_system
    )
    from .planner_agent import PlannerAgent, TradeProposal
    from .verifier_agent import VerificationResult, VerifierAgent
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in agents: {e}')

__all__ = [
    'AgentArgument',
    'AgentRole',
    'Conviction',
    'DebateRound',
    'ExecutorAgent',
    'FinalDecision',
    'HeadAI',
    'MacroStrategist',
    'MarketContext',
    'MultiAgentDebateSystem',
    'PlannerAgent',
    'RiskSentinel',
    'TacticalExecutioner',
    'TradeAction',
    'TradeProposal',
    'TradingAgent',
    'VerificationResult',
    'VerifierAgent',
    'create_debate_system',
    'create_executor_agent',
]