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

class CTraderOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "CTraderOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}

