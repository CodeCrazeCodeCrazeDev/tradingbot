"""
Yahoo Finance Feed - Data feed from Yahoo Finance
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class YahooFeed:
    """Yahoo Finance data feed"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        logger.info("YahooFeed initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        return True
    
    async def stop(self) -> bool:
        self._running = False
        return True
    
    def get_data(self, symbol: str, period: str = "1d", interval: str = "1m") -> Optional[pd.DataFrame]:
        if not HAS_YFINANCE:
            logger.warning("yfinance not installed")
            return None
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period, interval=interval)
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None


_feed: Optional[YahooFeed] = None
def get_feed() -> YahooFeed:
    global _feed
    if _feed is None:
        _feed = YahooFeed()
    return _feed

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_feed().initialize(config)
async def start() -> bool:
    return await get_feed().start()
async def stop() -> bool:
    return await get_feed().stop()
