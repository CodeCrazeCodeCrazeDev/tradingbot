"""
data_sources package
"""

try:
    from .free_data_providers import (
        CoinGeckoProvider,
        FREDProvider,
        ForexDataProvider,
        FreeDataAggregator,
        NewsAPIProvider,
        RedditSentimentProvider,
        YahooFinanceProvider
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in data_sources: {e}')

__all__ = [
    'CoinGeckoProvider',
    'FREDProvider',
    'ForexDataProvider',
    'FreeDataAggregator',
    'NewsAPIProvider',
    'RedditSentimentProvider',
    'YahooFinanceProvider',
]