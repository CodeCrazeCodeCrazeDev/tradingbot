"""
hedging package
"""

try:
    from .correlation_hedge import (
        CorrelationHedgeEngine,
        HedgePosition,
        HedgeRecommendation,
        HedgeStrategy,
        HedgeType,
        PortfolioExposure,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in hedging: {e}')

__all__ = [
    'CorrelationHedgeEngine',
    'HedgePosition',
    'HedgeRecommendation',
    'HedgeStrategy',
    'HedgeType',
    'PortfolioExposure',
    'retry',
]