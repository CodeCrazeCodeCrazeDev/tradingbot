"""
Time Series Database - Optimized storage for time series data
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


class TimeSeriesDB:
    """Time series database for market data"""
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.data: Dict[str, pd.DataFrame] = {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
            logger.info("TimeSeriesDB initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("TimeSeriesDB started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            logger.info("TimeSeriesDB stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def store(self, symbol: str, data: pd.DataFrame):
        try:
            if symbol in self.data:
                self.data[symbol] = pd.concat([self.data[symbol], data]).drop_duplicates()
            else:
                self.data[symbol] = data
        except Exception as e:
            logger.error(f"Error in store: {e}")
            raise
    
    def query(self, symbol: str, start: datetime = None, end: datetime = None) -> Optional[pd.DataFrame]:
        try:
            if symbol not in self.data:
                return None
            df = self.data[symbol]
            if start:
                df = df[df.index >= start]
            if end:
                df = df[df.index <= end]
            return df
        except Exception as e:
            logger.error(f"Error in query: {e}")
            raise
    
    def get_latest(self, symbol: str, n: int = 1) -> Optional[pd.DataFrame]:
        try:
            if symbol not in self.data:
                return None
            return self.data[symbol].tail(n)
        except Exception as e:
            logger.error(f"Error in get_latest: {e}")
            raise


_db: Optional[TimeSeriesDB] = None

def get_db() -> TimeSeriesDB:
    try:
        global _db
        if _db is None:
            _db = TimeSeriesDB()
        return _db
    except Exception as e:
        logger.error(f"Error in get_db: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_db().initialize(config)

async def start() -> bool:
    return await get_db().start()

async def stop() -> bool:
    return await get_db().stop()
