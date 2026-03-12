"""
Mock database implementations for testing.
Simulates database operations without requiring actual database connections.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from collections import defaultdict
import json
from typing import Set
from enum import auto
import numpy
import pandas


class MockDatabase:
    """
    Mock database for testing.
    Stores data in memory and simulates database operations.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        
        # In-memory storage
        self.tables: Dict[str, List[Dict]] = defaultdict(list)
        self.indexes: Dict[str, Dict] = defaultdict(dict)
        
        # Transaction state
        self.in_transaction = False
        self.transaction_buffer: List[tuple] = []
    
    def connect(self) -> bool:
        """Connect to database."""
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from database."""
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query (simulated)."""
        self._check_connection()
        # Simple query parsing for testing
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            return self._handle_select(query, params)
        elif query_lower.startswith('insert'):
            return self._handle_insert(query, params)
        elif query_lower.startswith('update'):
            return self._handle_update(query, params)
        elif query_lower.startswith('delete'):
            return self._handle_delete(query, params)
        
        return None
    
    def insert(self, table: str, data: Dict) -> int:
        """Insert a record."""
        self._check_connection()
        
        # Add auto-generated fields
        data['id'] = len(self.tables[table]) + 1
        data['created_at'] = datetime.now()
        
        if self.in_transaction:
            self.transaction_buffer.append(('insert', table, data))
        else:
            self.tables[table].append(data)
        
        return data['id']
    
    def insert_many(self, table: str, records: List[Dict]) -> List[int]:
        """Insert multiple records."""
        ids = []
        for record in records:
            ids.append(self.insert(table, record))
        return ids
    
    def find(self, table: str, query: Optional[Dict] = None) -> List[Dict]:
        """Find records matching query."""
        self._check_connection()
        
        if query is None:
            return self.tables[table].copy()
        
        results = []
        for record in self.tables[table]:
            if self._matches_query(record, query):
                results.append(record.copy())
        
        return results
    
    def find_one(self, table: str, query: Dict) -> Optional[Dict]:
        """Find a single record."""
        results = self.find(table, query)
        return results[0] if results else None
    
    def update(self, table: str, query: Dict, update: Dict) -> int:
        """Update records matching query."""
        self._check_connection()
        
        count = 0
        for record in self.tables[table]:
            if self._matches_query(record, query):
                record.update(update)
                record['updated_at'] = datetime.now()
                count += 1
        
        return count
    
    def delete(self, table: str, query: Dict) -> int:
        """Delete records matching query."""
        self._check_connection()
        
        original_count = len(self.tables[table])
        self.tables[table] = [
            r for r in self.tables[table]
            if not self._matches_query(r, query)
        ]
        
        return original_count - len(self.tables[table])
    
    def begin_transaction(self):
        """Begin a transaction."""
        self.in_transaction = True
        self.transaction_buffer = []
    
    def commit(self):
        """Commit transaction."""
        if self.in_transaction:
            for op, table, data in self.transaction_buffer:
                if op == 'insert':
                    self.tables[table].append(data)
            self.in_transaction = False
            self.transaction_buffer = []
    
    def rollback(self):
        """Rollback transaction."""
        self.in_transaction = False
        self.transaction_buffer = []
    
    def create_table(self, table: str, schema: Optional[Dict] = None):
        """Create a table."""
        if table not in self.tables:
            self.tables[table] = []
    
    def drop_table(self, table: str):
        """Drop a table."""
        if table in self.tables:
            del self.tables[table]
    
    def clear_table(self, table: str):
        """Clear all records from a table."""
        self.tables[table] = []
    
    def count(self, table: str, query: Optional[Dict] = None) -> int:
        """Count records."""
        return len(self.find(table, query))
    
    def _matches_query(self, record: Dict, query: Dict) -> bool:
        """Check if record matches query."""
        for key, value in query.items():
            if key not in record:
                return False
            
            if isinstance(value, dict):
                # Handle operators
                for op, op_value in value.items():
                    if op == '$gt' and not record[key] > op_value:
                        return False
                    elif op == '$gte' and not record[key] >= op_value:
                        return False
                    elif op == '$lt' and not record[key] < op_value:
                        return False
                    elif op == '$lte' and not record[key] <= op_value:
                        return False
                    elif op == '$ne' and not record[key] != op_value:
                        return False
                    elif op == '$in' and record[key] not in op_value:
                        return False
            elif record[key] != value:
                return False
        
        return True
    
    def _handle_select(self, query: str, params: Optional[tuple]) -> List[Dict]:
        """Handle SELECT query."""
        # Simple implementation for testing
        return []
    
    def _handle_insert(self, query: str, params: Optional[tuple]) -> int:
        """Handle INSERT query."""
        return 1
    
    def _handle_update(self, query: str, params: Optional[tuple]) -> int:
        """Handle UPDATE query."""
        return 1
    
    def _handle_delete(self, query: str, params: Optional[tuple]) -> int:
        """Handle DELETE query."""
        return 1
    
    def _check_connection(self):
        """Check if connected."""
        if not self.connected:
            raise ConnectionError("Database not connected")


class MockTimeSeriesDB:
    """
    Mock time series database for testing.
    Optimized for OHLCV and tick data storage.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        
        # In-memory storage organized by symbol and timeframe
        self.ohlcv_data: Dict[str, Dict[str, pd.DataFrame]] = defaultdict(dict)
        self.tick_data: Dict[str, List[Dict]] = defaultdict(list)
        self.metadata: Dict[str, Dict] = {}
    
    def connect(self) -> bool:
        """Connect to database."""
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from database."""
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected
    
    def store_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame
    ) -> bool:
        """Store OHLCV data."""
        self._check_connection()
        
        if symbol not in self.ohlcv_data:
            self.ohlcv_data[symbol] = {}
        
        if timeframe in self.ohlcv_data[symbol]:
            # Append to existing data
            existing = self.ohlcv_data[symbol][timeframe]
            self.ohlcv_data[symbol][timeframe] = pd.concat([existing, data]).drop_duplicates()
        else:
            self.ohlcv_data[symbol][timeframe] = data.copy()
        
        return True
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get OHLCV data."""
        self._check_connection()
        
        if symbol not in self.ohlcv_data or timeframe not in self.ohlcv_data[symbol]:
            return pd.DataFrame()
        
        data = self.ohlcv_data[symbol][timeframe].copy()
        
        if start is not None and 'timestamp' in data.columns:
            data = data[data['timestamp'] >= start]
        
        if end is not None and 'timestamp' in data.columns:
            data = data[data['timestamp'] <= end]
        
        if limit is not None:
            data = data.tail(limit)
        
        return data
    
    def store_tick(self, symbol: str, tick: Dict) -> bool:
        """Store tick data."""
        self._check_connection()
        
        tick['timestamp'] = tick.get('timestamp', datetime.now())
        self.tick_data[symbol].append(tick)
        
        # Keep only recent ticks (memory management)
        max_ticks = self.config.get('max_ticks_per_symbol', 10000)
        if len(self.tick_data[symbol]) > max_ticks:
            self.tick_data[symbol] = self.tick_data[symbol][-max_ticks:]
        
        return True
    
    def get_ticks(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get tick data."""
        self._check_connection()
        
        ticks = self.tick_data.get(symbol, [])
        
        if start is not None:
            ticks = [t for t in ticks if t['timestamp'] >= start]
        
        if end is not None:
            ticks = [t for t in ticks if t['timestamp'] <= end]
        
        if limit is not None:
            ticks = ticks[-limit:]
        
        return ticks
    
    def get_latest_ohlcv(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get latest OHLCV bar."""
        data = self.get_ohlcv(symbol, timeframe, limit=1)
        if data.empty:
            return None
        return data.iloc[-1].to_dict()
    
    def get_symbols(self) -> List[str]:
        """Get all symbols with data."""
        return list(set(list(self.ohlcv_data.keys()) + list(self.tick_data.keys())))
    
    def get_timeframes(self, symbol: str) -> List[str]:
        """Get available timeframes for a symbol."""
        if symbol in self.ohlcv_data:
            return list(self.ohlcv_data[symbol].keys())
        return []
    
    def delete_symbol_data(self, symbol: str) -> bool:
        """Delete all data for a symbol."""
        self._check_connection()
        
        if symbol in self.ohlcv_data:
            del self.ohlcv_data[symbol]
        if symbol in self.tick_data:
            del self.tick_data[symbol]
        
        return True
    
    def get_data_range(self, symbol: str, timeframe: str) -> Optional[tuple]:
        """Get date range of available data."""
        data = self.get_ohlcv(symbol, timeframe)
        if data.empty or 'timestamp' not in data.columns:
            return None
        return (data['timestamp'].min(), data['timestamp'].max())
    
    def _check_connection(self):
        """Check if connected."""
        if not self.connected:
            raise ConnectionError("Database not connected")


class MockRedisCache:
    """
    Mock Redis cache for testing.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        self.connected = False
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.expiry and datetime.now() > self.expiry[key]:
            del self.data[key]
            del self.expiry[key]
            return None
        return self.data.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        self.data[key] = value
        if ttl:
            self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.data:
            del self.data[key]
            if key in self.expiry:
                del self.expiry[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.get(key) is not None
    
    def clear(self):
        """Clear all cache."""
        self.data = {}
        self.expiry = {}
