"""
cTrader Integration Package

Provides connectivity to cTrader for:
- Real-time market data (ticks, OHLCV)
- Level 2 / Depth of Market data
- News feed
- Account management
"""

try:
    from .ctrader_integration import (
        CTraderIntegration,
        CTraderConnection,
        CTraderMarketData,
        CTraderNewsFeed,
        TickData,
        OHLCVBar,
        DepthOfMarket,
        Level2Entry,
        NewsItem,
        AccountInfo,
        Timeframe,
        ConnectionState,
        DataType,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in ctrader: {e}')

__all__ = [
    'CTraderIntegration',
    'CTraderConnection',
    'CTraderMarketData',
    'CTraderNewsFeed',
    'TickData',
    'OHLCVBar',
    'DepthOfMarket',
    'Level2Entry',
    'NewsItem',
    'AccountInfo',
    'Timeframe',
    'ConnectionState',
    'DataType',
]
