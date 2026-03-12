"""
portfolio package
"""

try:
    from .manager import PortfolioMetrics, PortfolioRiskManager
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in portfolio: {e}')

__all__ = [
    'PortfolioMetrics',
    'PortfolioRiskManager',
]