"""
Self Healing Ai Module
============================================================

Auto-generated integration file.
"""

# core
try:
    from .core import (
        StateManager,
        SystemHealth,
        SystemState,
    )
except ImportError as e:
    # core not available
    pass

# orchestrator
try:
    from .orchestrator import (
        SelfHealingOrchestrator,
    )
except ImportError as e:
    # orchestrator not available
    pass

__all__ = [
    'SelfHealingOrchestrator',
    'StateManager',
    'SystemHealth',
    'SystemState',
]
