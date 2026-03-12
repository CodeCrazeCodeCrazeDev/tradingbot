"""
arbitrage package
"""

try:
    from .arbitrage_network import (
        ArbitrageNetwork,
        ArbitrageOpportunity,
        ArbitrageType,
        CrossExchangeArbitrage,
        ETFArbitrage,
        TriangularArbitrage,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in arbitrage: {e}')

__all__ = [
    'ArbitrageNetwork',
    'ArbitrageOpportunity',
    'ArbitrageType',
    'CrossExchangeArbitrage',
    'ETFArbitrage',
    'TriangularArbitrage',
    'retry',
]