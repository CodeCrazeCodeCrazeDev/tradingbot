"""
data_feeds package
"""

try:
    from .historical_feeds import (
        AlphaVantageFeed,
        DataSource,
        FREDFeed,
        HistoricalBar,
        HistoricalDataFeed,
        YahooFinanceFeed,
        create_historical_feed
    )
    from .multi_source_feed import (
        CoinGeckoAdapter,
        DataFeedAdapter,
        DataFeedSource,
        DataPoint,
        DataQuality,
        FeedConfig,
        FeedHealth,
        MultiSourceDataFeed,
        YahooFinanceAdapter,
        create_multi_source_feed
    )
    from .websocket_feeds import (
        BinanceWebSocketFeed,
        CoinbaseWebSocketFeed,
        ConnectionState,
        KrakenWebSocketFeed,
        OrderBookUpdate,
        TickData,
        WebSocketFeed,
        WebSocketFeedManager,
        create_websocket_feed
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in data_feeds: {e}')

__all__ = [
    'AlphaVantageFeed',
    'BinanceWebSocketFeed',
    'CoinGeckoAdapter',
    'CoinbaseWebSocketFeed',
    'ConnectionState',
    'DataFeedAdapter',
    'DataFeedSource',
    'DataPoint',
    'DataQuality',
    'DataSource',
    'FREDFeed',
    'FeedConfig',
    'FeedHealth',
    'HistoricalBar',
    'HistoricalDataFeed',
    'KrakenWebSocketFeed',
    'MultiSourceDataFeed',
    'OrderBookUpdate',
    'TickData',
    'WebSocketFeed',
    'WebSocketFeedManager',
    'YahooFinanceAdapter',
    'YahooFinanceFeed',
    'create_historical_feed',
    'create_multi_source_feed',
    'create_websocket_feed',
]