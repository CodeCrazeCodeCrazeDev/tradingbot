"""
Risk Management Module
============================================================

Auto-generated integration file.
"""

# dynamic_hedging
try:
    from .dynamic_hedging import (
        DynamicHedgingEngine,
    )
except ImportError as e:
    # dynamic_hedging not available
    pass

__all__ = [
    'DynamicHedgingEngine',
]
