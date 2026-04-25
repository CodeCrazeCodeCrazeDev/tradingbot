"""
Meta-Governance Module

Comprehensive governance systems for controlling and optimizing
trading bot behavior with strict safety constraints.
"""

from .meta_agent_governance import (
    MetaAgentGovernanceLayer,
    AgentType,
    ChangeCategory,
    ChangeType,
    UnderperformanceType,
    AgentPerformance,
    ForbiddenChangeAttempt,
    CandidateUpgrade,
    ValidationCriteria,
    ValidationResult,
    create_meta_agent_governance_layer,
)

__all__ = [
    'MetaAgentGovernanceLayer',
    'AgentType',
    'ChangeCategory',
    'ChangeType',
    'UnderperformanceType',
    'AgentPerformance',
    'ForbiddenChangeAttempt',
    'CandidateUpgrade',
    'ValidationCriteria',
    'ValidationResult',
    'create_meta_agent_governance_layer',
]
