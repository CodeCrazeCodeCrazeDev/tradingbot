"""
Point-in-Time Data Access Layer
Prevents data leakage by ensuring strict temporal data access
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from threading import Lock
import bisect

logger = logging.getLogger(__name__)


@dataclass
class DataSnapshot:
    """Immutable data snapshot for a specific point in time"""
    timestamp: datetime
    data: Dict[str, Any]
    is_valid: bool = True


class PointInTimeDataAccess:
    """
    Strict point-in-time data access layer that prevents lookahead bias.
    
    Features:
    - Temporal data isolation
    - Future data protection
    - Immutable snapshots
    - Efficient range queries
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Data storage with temporal indexing
        self._data_snapshots: Dict[str, List[DataSnapshot]] = {}
        self._timestamp_index: Dict[str, List[datetime]] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # Configuration
        self.max_history_days = config.get('max_history_days', 365)
        self.cache_size = config.get('cache_size', 10000)
        
        logger.info("Point-in-time data access layer initialized")
    
    def add_snapshot(self, symbol: str, timestamp: datetime, data: Dict[str, Any]) -> None:
        """
        Add a new data snapshot with strict temporal ordering.
        
        Args:
            symbol: Trading symbol
            timestamp: Exact timestamp of the data
            data: Market data dictionary
        """
        with self._lock:
            if symbol not in self._data_snapshots:
                self._data_snapshots[symbol] = []
                self._timestamp_index[symbol] = []
            
            # Create immutable snapshot
            snapshot = DataSnapshot(timestamp=timestamp, data=data.copy())
            
            # Maintain sorted order by timestamp
            idx = bisect.bisect_left(self._timestamp_index[symbol], timestamp)
            
            # Check for duplicate timestamp
            if idx < len(self._timestamp_index[symbol]) and self._timestamp_index[symbol][idx] == timestamp:
                # Update existing snapshot
                self._data_snapshots[symbol][idx] = snapshot
            else:
                # Insert new snapshot
                self._data_snapshots[symbol].insert(idx, snapshot)
                self._timestamp_index[symbol].insert(idx, timestamp)
            
            # Trim old data
            self._trim_old_data(symbol)
    
    def get_data_at_time(self, symbol: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Get data available at exactly the specified timestamp.
        
        Args:
            symbol: Trading symbol
            timestamp: Query timestamp
            
        Returns:
            Data available at the timestamp or None if no data
        """
        with self._lock:
            if symbol not in self._data_snapshots:
                return None
            
            # Find exact timestamp or latest before it
            idx = bisect.bisect_right(self._timestamp_index[symbol], timestamp) - 1
            
            if idx >= 0 and self._data_snapshots[symbol][idx].timestamp <= timestamp:
                return self._data_snapshots[symbol][idx].data.copy()
            
            return None
    
    def get_data_range(self, 
                      symbol: str, 
                      start_time: datetime, 
                      end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get all data within a time range (exclusive of end_time).
        
        Args:
            symbol: Trading symbol
            start_time: Start of range (inclusive)
            end_time: End of range (exclusive)
            
        Returns:
            List of data snapshots in chronological order
        """
        with self._lock:
            if symbol not in self._data_snapshots:
                return []
            
            # Find range boundaries
            start_idx = bisect.bisect_left(self._timestamp_index[symbol], start_time)
            end_idx = bisect.bisect_left(self._timestamp_index[symbol], end_time)
            
            # Extract snapshots
            snapshots = self._data_snapshots[symbol][start_idx:end_idx]
            
            # Return copies to ensure immutability
            return [snapshot.data.copy() for snapshot in snapshots]
    
    def get_latest_before(self, symbol: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Get the latest data available before the specified timestamp.
        
        Args:
            symbol: Trading symbol
            timestamp: Query timestamp
            
        Returns:
            Latest data before timestamp or None
        """
        with self._lock:
            if symbol not in self._data_snapshots:
                return None
            
            idx = bisect.bisect_left(self._timestamp_index[symbol], timestamp) - 1
            
            if idx >= 0:
                return self._data_snapshots[symbol][idx].data.copy()
            
            return None
    
    def validate_no_leakage(self, 
                           symbol: str, 
                           query_time: datetime, 
                           data_access_time: datetime) -> bool:
        """
        Validate that data access doesn't introduce leakage.
        
        Args:
            symbol: Trading symbol
            query_time: Time being queried
            data_access_time: Actual time of data access
            
        Returns:
            True if no leakage detected
        """
        # Ensure data access is not before query time
        if data_access_time < query_time:
            logger.warning(f"Potential data leakage detected for {symbol}: "
                          f"accessing future data from {query_time} at {data_access_time}")
            return False
        
        return True
    
    def _trim_old_data(self, symbol: str) -> None:
        """Remove data older than max_history_days"""
        if symbol not in self._data_snapshots:
            return
        
        cutoff_time = datetime.now() - timedelta(days=self.max_history_days)
        
        # Find cutoff index
        cutoff_idx = bisect.bisect_left(self._timestamp_index[symbol], cutoff_time)
        
        if cutoff_idx > 0:
            # Remove old data
            self._data_snapshots[symbol] = self._data_snapshots[symbol][cutoff_idx:]
            self._timestamp_index[symbol] = self._timestamp_index[symbol][cutoff_idx:]
    
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics about stored data for a symbol"""
        with self._lock:
            if symbol not in self._data_snapshots:
                return {}
            
            snapshots = self._data_snapshots[symbol]
            
            if not snapshots:
                return {}
            
            timestamps = [s.timestamp for s in snapshots]
            
            return {
                'total_snapshots': len(snapshots),
                'earliest_timestamp': min(timestamps),
                'latest_timestamp': max(timestamps),
                'time_span_days': (max(timestamps) - min(timestamps)).days,
                'avg_snapshots_per_day': len(snapshots) / max(1, (max(timestamps) - min(timestamps)).days)
            }
    
    def clear_symbol(self, symbol: str) -> None:
        """Clear all data for a symbol"""
        with self._lock:
            if symbol in self._data_snapshots:
                del self._data_snapshots[symbol]
            if symbol in self._timestamp_index:
                del self._timestamp_index[symbol]
    
    def clear_all(self) -> None:
        """Clear all stored data"""
        with self._lock:
            self._data_snapshots.clear()
            self._timestamp_index.clear()


class TemporalDataValidator:
    """
    Validates temporal integrity of data access patterns.
    """
    
    def __init__(self):
        self.access_log: List[Tuple[str, datetime, datetime]] = []
        self.violations: List[Dict[str, Any]] = []
    
    def log_access(self, symbol: str, query_time: datetime, access_time: datetime) -> None:
        """Log a data access for validation"""
        self.access_log.append((symbol, query_time, access_time))
        
        # Check for violations
        if access_time < query_time:
            self.violations.append({
                'symbol': symbol,
                'query_time': query_time,
                'access_time': access_time,
                'violation_type': 'future_data_access'
            })
    
    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all detected violations"""
        return self.violations.copy()
    
    def clear_violations(self) -> None:
        """Clear violation log"""
        self.violations.clear()
