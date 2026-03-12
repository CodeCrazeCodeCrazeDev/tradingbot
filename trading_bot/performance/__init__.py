"""
Performance Module
============================================================

Auto-generated integration file.
"""

# complete_performance_system
try:
    from .complete_performance_system import (
        CompletePerformanceSystem,
    )
except ImportError as e:
    # complete_performance_system not available
    pass

# memory_manager
try:
    from .memory_manager import (
        MemoryManager,
    )
except ImportError as e:
    # memory_manager not available
    pass

__all__ = [
    'CompletePerformanceSystem',
    'MemoryManager',
]
