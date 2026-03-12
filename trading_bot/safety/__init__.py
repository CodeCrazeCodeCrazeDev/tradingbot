"""
Safety Module
============================================================

Auto-generated integration file.
"""

# auto_pause
try:
    from .auto_pause import (
        AutoPauseManager,
    )
except ImportError as e:
    # auto_pause not available
    AutoPauseManager = None

# safety_orchestrator
try:
    from .safety_orchestrator import (
        SafetyOrchestrator,
        SafetyStatus,
    )
except ImportError as e:
    # safety_orchestrator not available
    SafetyOrchestrator = None
    SafetyStatus = None

__all__ = [
    'AutoPauseManager',
    'SafetyOrchestrator',
    'SafetyStatus',
]
