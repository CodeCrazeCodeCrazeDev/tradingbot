"""
execution package
"""

try:
    from .advanced_execution import (
        AdvancedExecutionSystem,
        AdverseSelectionModeler,
        ExecutionMetrics,
        ExecutionStrategy,
        HFTExecutionEngine,
        LiquiditySnapshot,
        NewsEventThrottler,
        SpreadAwareExecutor,
        VenueQuality,
        VenueType
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in execution: {e}')

__all__ = [
    'AdvancedExecutionSystem',
    'AdverseSelectionModeler',
    'ExecutionMetrics',
    'ExecutionStrategy',
    'HFTExecutionEngine',
    'LiquiditySnapshot',
    'NewsEventThrottler',
    'SpreadAwareExecutor',
    'VenueQuality',
    'VenueType',
]