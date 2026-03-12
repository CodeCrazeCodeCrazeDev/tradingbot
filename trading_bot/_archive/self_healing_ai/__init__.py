"""
self_healing_ai package
"""

try:
    from .core import (
        BaseValidator,
        IMMUTABLE_LIMITS,
        RemediationAction,
        RemediationStatus,
        StateManager,
        SystemHealth,
        SystemState,
        ValidationCategory,
        ValidationIssue,
        ValidationReport,
        ValidationSeverity
    )
    from .orchestrator import SelfHealingOrchestrator, quick_start
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in self_healing_ai: {e}')

__all__ = [
    'BaseValidator',
    'IMMUTABLE_LIMITS',
    'RemediationAction',
    'RemediationStatus',
    'SelfHealingOrchestrator',
    'StateManager',
    'SystemHealth',
    'SystemState',
    'ValidationCategory',
    'ValidationIssue',
    'ValidationReport',
    'ValidationSeverity',
    'quick_start',
]