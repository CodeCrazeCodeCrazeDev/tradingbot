"""
Enhanced Data Fetcher
============================================================

OHLCV fetcher used by the ultimate_bot scripts. Delegates to the
canonical MultiSourceDataFeed when available; falls back to an
empty frame rather than fabricating data.
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class EnhancedDataFetcher:
    """Fetches market data for the ultimate_bot strategies."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def fetch(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> pd.DataFrame:
        try:
            from trading_bot.data_feed.multi_source_feed import MultiSourceDataFeed
            feed = MultiSourceDataFeed()
            dp = feed.fetch_realtime(symbol)
            if dp is not None:
                return pd.DataFrame([{
                    "timestamp": getattr(dp, "timestamp", None),
                    "open": getattr(dp, "price", None),
                    "high": getattr(dp, "price", None),
                    "low": getattr(dp, "price", None),
                    "close": getattr(dp, "price", None),
                    "volume": getattr(dp, "volume", 0.0),
                }])
        except Exception as e:
            logger.warning(f"EnhancedDataFetcher: live fetch failed for {symbol}: {e}")
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
