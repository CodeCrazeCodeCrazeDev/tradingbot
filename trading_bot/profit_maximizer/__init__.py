"""
Profit Maximizer Module
============================================================

Auto-generated integration file.
"""

# brain_integration
try:
    from .brain_integration import (
        ProfitMaximizerBrainWrapper,
    )
except ImportError as e:
    # brain_integration not available
    pass

# profit_maximizer_core
try:
    from .profit_maximizer_core import (
        ProfitMaximizerSystem,
    )
    # Alias for backward compatibility
    ProfitMaximizer = ProfitMaximizerSystem
except ImportError as e:
    # profit_maximizer_core not available
    ProfitMaximizer = None
    pass

__all__ = [
    'ProfitMaximizer',
    'ProfitMaximizerBrainWrapper',
    'ProfitMaximizerSystem',
]
