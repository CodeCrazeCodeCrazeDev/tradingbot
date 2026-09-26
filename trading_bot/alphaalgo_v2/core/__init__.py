"""
Core Module
============================================================

Auto-generated integration file.
"""

# exceptions
try:
    from .exceptions import (
        SystemError,
    )
except ImportError as e:
    # exceptions not available
    pass

# interfaces
try:
    from .interfaces import (
        IEvolutionEngine,
        ILearningEngine,
        IRiskManager,
    )
except ImportError as e:
    # interfaces not available
    pass

__all__ = [
    'IEvolutionEngine',
    'ILearningEngine',
    'IRiskManager',
    'SystemError',
]
