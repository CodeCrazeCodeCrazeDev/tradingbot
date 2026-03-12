"""
Database Initialization with Fallback

Initializes TimeSeriesDB with graceful fallback to in-memory storage if database unavailable.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque
import pandas as pd

logger = logging.getLogger(__name__)


class InMemoryTimeSeriesDB:
    """In-memory fallback for TimeSeriesDB"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data = defaultdict(lambda: deque(maxlen=10000))
        self.metadata = {}
        logger.warning("Using in-memory TimeSeriesDB (data will not persist)")
    
    def write(self, symbol: str, timestamp: datetime, data: Dict[str, Any]):
        """Write data point"""
        self.data[symbol].append({
            'timestamp': timestamp,
            **data
        })
    
    def read(self, symbol: str, start_time: Optional[datetime] = None, 
             end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read data points"""
        data = list(self.data[symbol])
        
        if start_time:
            data = [d for d in data if d['timestamp'] >= start_time]
        if end_time:
            data = [d for d in data if d['timestamp'] <= end_time]
        
        return data
    
    def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest data point"""
        if symbol in self.data and self.data[symbol]:
            return self.data[symbol][-1]
        return None
    
    def close(self):
        """Close database (no-op for in-memory)"""
        pass


class DatabaseInitializer:
    """Initialize database with fallback handling"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.db = None
        self.using_fallback = False
        
    def initialize(self):
        """
        Initialize database with fallback
        
        Returns:
            Database instance (TimeSeriesDB or InMemoryTimeSeriesDB)
        """
        try:
            # Try to initialize TimeSeriesDB
            from trading_bot.data.time_series_db import TimeSeriesDB
            
            db_config = self.config.get('database', {})
            self.db = TimeSeriesDB(db_config)
            
            # Test connection
            if hasattr(self.db, 'test_connection'):
                if not self.db.test_connection():
                    raise Exception("Database connection test failed")
            
            logger.info("TimeSeriesDB initialized successfully")
            self.using_fallback = False
            return self.db
            
        except ImportError as e:
            logger.warning(f"TimeSeriesDB not available: {e}")
            return self._initialize_fallback()
        except Exception as e:
            logger.error(f"TimeSeriesDB initialization failed: {e}")
            return self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Initialize fallback in-memory database"""
        logger.warning("Falling back to in-memory database")
        self.db = InMemoryTimeSeriesDB(self.config)
        self.using_fallback = True
        return self.db
    
    def get_database(self):
        """Get database instance"""
        if self.db is None:
            return self.initialize()
        return self.db
    
    def is_using_fallback(self) -> bool:
        """Check if using fallback database"""
        return self.using_fallback


def initialize_database_with_fallback(config: Optional[Dict[str, Any]] = None):
    """
    Convenience function to initialize database with fallback
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Database instance
    """
    initializer = DatabaseInitializer(config)
    return initializer.initialize()
