"""
agents package
"""

try:
    from .executor_agent import ExecutorAgent, create_executor_agent
    from .orchestrator import (
        AgentOrchestrator,
        AgentRole,
        BaseAgent,
        DecisionStatus,
        ExecutorAgent,
        PlannerAgent,
        SafetyValidatorAgent,
        TradingContext,
        TradingDecision,
        TradingProposal,
        ValidationResult,
        VerifierAgent
    )
    from .planner_agent import PlannerAgent, create_planner_agent
    from .safety_validator import SafetyValidator, create_safety_validator
    from .verifier_agent import VerifierAgent, create_verifier_agent
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in agents: {e}')

__all__ = [
    'AgentOrchestrator',
    'AgentRole',
    'BaseAgent',
    'DecisionStatus',
    'ExecutorAgent',
    'PlannerAgent',
    'SafetyValidator',
    'SafetyValidatorAgent',
    'TradingContext',
    'TradingDecision',
    'TradingProposal',
    'ValidationResult',
    'VerifierAgent',
    'create_executor_agent',
    'create_planner_agent',
    'create_safety_validator',
    'create_verifier_agent',
]