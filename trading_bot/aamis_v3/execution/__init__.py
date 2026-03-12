"""
Execution Module
============================================================

Auto-generated integration file.
"""

# advanced_execution
try:
    from .advanced_execution import (
        AdvancedExecutionSystem,
        HFTExecutionEngine,
    )
except ImportError as e:
    # advanced_execution not available
    pass

__all__ = [
    'AdvancedExecutionSystem',
    'HFTExecutionEngine',
]
