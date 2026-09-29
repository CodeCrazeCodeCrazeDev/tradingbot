"""
Autonomous Learner Module
============================================================

Auto-generated integration file.
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.autonomous_learner is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)

# learning_orchestrator
try:
    from .learning_orchestrator import (
        LearningOrchestrator,
    )
except ImportError as e:
    # learning_orchestrator not available
    pass

__all__ = [
    'LearningOrchestrator',
]
