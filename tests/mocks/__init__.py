"""
Mock infrastructure for testing trading bot components.
Provides mock implementations for external dependencies.
"""

from .mock_broker import MockMT5Broker, MockBrokerConnection
from .mock_database import MockDatabase, MockTimeSeriesDB
from .mock_market_data import MockMarketDataFeed, generate_ohlcv_data, generate_order_book
from .mock_external_apis import MockNewsAPI, MockCoinGeckoAPI, MockYahooFinanceAPI

__all__ = [
    'MockMT5Broker',
    'MockBrokerConnection',
    'MockDatabase',
    'MockTimeSeriesDB',
    'MockMarketDataFeed',
    'generate_ohlcv_data',
    'generate_order_book',
    'MockNewsAPI',
    'MockCoinGeckoAPI',
    'MockYahooFinanceAPI',
]
