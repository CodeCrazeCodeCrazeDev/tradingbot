"""
Portfolio Module
============================================================

Auto-generated integration file.
"""

# manager
try:
    from .manager import (
        PortfolioRiskManager,
    )
except ImportError as e:
    # manager not available
    pass

__all__ = [
    'PortfolioRiskManager',
]
