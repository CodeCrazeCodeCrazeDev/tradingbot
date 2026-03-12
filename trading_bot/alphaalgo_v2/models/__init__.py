"""
Models Module
============================================================

Auto-generated integration file.
"""

# brain
try:
    from .brain import (
        IntelligenceBrain,
    )
except ImportError as e:
    # brain not available
    pass

__all__ = [
    'IntelligenceBrain',
]
