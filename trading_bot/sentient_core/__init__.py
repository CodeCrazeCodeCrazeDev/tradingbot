"""
Sentient Core Module
============================================================

Auto-generated integration file.
"""

# ai_learner
try:
    from .ai_learner import (
        AISystemAnalysis,
    )
except ImportError as e:
    # ai_learner not available
    pass

# sentient_orchestrator
try:
    from .sentient_orchestrator import (
        SentientOrchestrator,
        SystemState,
        SystemStatus,
    )
except ImportError as e:
    # sentient_orchestrator not available
    pass

__all__ = [
    'AISystemAnalysis',
    'SentientOrchestrator',
    'SystemState',
    'SystemStatus',
]
