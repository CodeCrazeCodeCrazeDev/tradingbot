"""
Elite Trading Bot - Memory Optimization Module

This module provides memory-efficient data structures and optimization techniques
for handling large datasets and reducing memory footprint during trading operations.
"""

import sys
import logging
import gc
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from dataclasses import dataclass
import weakref
from collections import deque, defaultdict
import array

import numpy as np
import pandas as pd
import numpy
import pandas
import time

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic types
T = TypeVar('T')


class DataStructureType(Enum):
    """Types of optimized data structures."""
    PRICE_SERIES = "price_series"
    OHLCV = "ohlcv"
    ORDER_BOOK = "order_book"
    TRADE_DATA = "trade_data"
    TIME_SERIES = "time_series"
    MARKET_DEPTH = "market_depth"
    INDICATORS = "indicators"
    SIGNALS = "signals"
    CUSTOM = "custom"


@dataclass
class OptimizationResult:
    """Result of a memory optimization operation."""
    original_size: int
    optimized_size: int
    reduction_percent: float
    structure_type: DataStructureType
    description: str


class MemoryOptimizer:
    """
    Provides memory optimization techniques for the Elite Trading Bot.
    
    This class implements various memory-efficient data structures and optimization
    techniques to reduce memory usage while maintaining performance.
    """
    
    def __init__(self):
        """Initialize the memory optimizer."""
        try:
            self.optimization_stats: Dict[str, List[OptimizationResult]] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def optimize_dataframe(self, df: pd.DataFrame, structure_type: DataStructureType) -> Tuple[pd.DataFrame, OptimizationResult]:
        """
        Optimize a pandas DataFrame to reduce memory usage.
        
        Args:
            df: DataFrame to optimize
            structure_type: Type of data structure for specialized optimizations
            
        Returns:
            Tuple of (optimized_dataframe, optimization_result)
        """
        try:
            if df is None or df.empty:
                return df, OptimizationResult(0, 0, 0, structure_type, "Empty DataFrame")
        
            # Calculate original memory usage
            original_memory = df.memory_usage(deep=True).sum()
        
            # Make a copy to avoid modifying the original
            result = df.copy()
        
            # Apply general optimizations
            result = self._optimize_dtypes(result)
        
            # Apply specialized optimizations based on structure type
            if structure_type == DataStructureType.PRICE_SERIES:
                result = self._optimize_price_series(result)
            elif structure_type == DataStructureType.OHLCV:
                result = self._optimize_ohlcv(result)
            elif structure_type == DataStructureType.ORDER_BOOK:
                result = self._optimize_order_book(result)
            elif structure_type == DataStructureType.INDICATORS:
                result = self._optimize_indicators(result)
        
            # Calculate optimized memory usage
            optimized_memory = result.memory_usage(deep=True).sum()
            reduction = (original_memory - optimized_memory) / original_memory * 100 if original_memory > 0 else 0
        
            # Create optimization result
            opt_result = OptimizationResult(
                original_size=original_memory,
                optimized_size=optimized_memory,
                reduction_percent=reduction,
                structure_type=structure_type,
                description=f"Optimized {structure_type.value} DataFrame: {reduction:.2f}% reduction"
            )
        
            # Store optimization stats
            if structure_type.value not in self.optimization_stats:
                self.optimization_stats[structure_type.value] = []
            self.optimization_stats[structure_type.value].append(opt_result)
        
            logger.info(f"DataFrame optimization: {opt_result.description}")
            return result, opt_result
        except Exception as e:
            logger.error(f"Error in optimize_dataframe: {e}")
            raise
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize data types in a DataFrame to reduce memory usage.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            Optimized DataFrame
        """
        try:
            result = df.copy()
        
            # Optimize integers
            int_columns = result.select_dtypes(include=['int']).columns
            for col in int_columns:
                col_min = result[col].min()
                col_max = result[col].max()
            
                # Convert to smallest possible integer type
                if col_min >= 0:
                    if col_max < 2**8:
                        result[col] = result[col].astype(np.uint8)
                    elif col_max < 2**16:
                        result[col] = result[col].astype(np.uint16)
                    elif col_max < 2**32:
                        result[col] = result[col].astype(np.uint32)
                else:
                    if col_min > -2**7 and col_max < 2**7:
                        result[col] = result[col].astype(np.int8)
                    elif col_min > -2**15 and col_max < 2**15:
                        result[col] = result[col].astype(np.int16)
                    elif col_min > -2**31 and col_max < 2**31:
                        result[col] = result[col].astype(np.int32)
        
            # Optimize floats
            float_columns = result.select_dtypes(include=['float']).columns
            for col in float_columns:
                # Check if column can be represented as float32 without significant loss
                if result[col].min() > np.finfo(np.float32).min and result[col].max() < np.finfo(np.float32).max:
                    # Check precision requirements
                    if (result[col].round(6) == result[col]).all():
                        result[col] = result[col].astype(np.float32)
        
            # Optimize objects (strings)
            obj_columns = result.select_dtypes(include=['object']).columns
            for col in obj_columns:
                # Check if column contains only a few unique values
                if result[col].nunique() / len(result) < 0.5:  # Less than 50% unique values
                    result[col] = result[col].astype('category')
        
            return result
        except Exception as e:
            logger.error(f"Error in _optimize_dtypes: {e}")
            raise
    
    def _optimize_price_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply specialized optimizations for price series data.
        
        Args:
            df: DataFrame with price series data
            
        Returns:
            Optimized DataFrame
        """
        try:
            result = df.copy()
        
            # Price data typically doesn't need high precision
            # Convert to float32 if appropriate
            price_columns = [col for col in result.columns if any(
                price_term in col.lower() for price_term in ['price', 'open', 'high', 'low', 'close']
            )]
        
            for col in price_columns:
                if result[col].dtype.kind == 'f':  # If it's a float
                    result[col] = result[col].astype(np.float32)
        
            return result
        except Exception as e:
            logger.error(f"Error in _optimize_price_series: {e}")
            raise
    
    def _optimize_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply specialized optimizations for OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Optimized DataFrame
        """
        try:
            result = df.copy()
        
            # OHLC price columns to float32
            ohlc_columns = [col for col in result.columns if col.lower() in ['open', 'high', 'low', 'close']]
            for col in ohlc_columns:
                if result[col].dtype.kind == 'f':  # If it's a float
                    result[col] = result[col].astype(np.float32)
        
            # Volume often has large integers, but rarely needs full int64
            volume_columns = [col for col in result.columns if 'volume' in col.lower()]
            for col in volume_columns:
                if result[col].dtype.kind == 'i':  # If it's an integer
                    col_max = result[col].max()
                    if col_max < 2**32:
                        result[col] = result[col].astype(np.uint32)
        
            return result
        except Exception as e:
            logger.error(f"Error in _optimize_ohlcv: {e}")
            raise
    
    def _optimize_order_book(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply specialized optimizations for order book data.
        
        Args:
            df: DataFrame with order book data
            
        Returns:
            Optimized DataFrame
        """
        try:
            result = df.copy()
        
            # Price levels to float32
            price_columns = [col for col in result.columns if 'price' in col.lower()]
            for col in price_columns:
                if result[col].dtype.kind == 'f':  # If it's a float
                    result[col] = result[col].astype(np.float32)
        
            # Size/quantity columns often don't need full int64
            size_columns = [col for col in result.columns if any(
                size_term in col.lower() for size_term in ['size', 'quantity', 'volume', 'amount']
            )]
        
            for col in size_columns:
                if result[col].dtype.kind == 'i':  # If it's an integer
                    col_max = result[col].max()
                    if col_max < 2**32:
                        result[col] = result[col].astype(np.uint32)
        
            return result
        except Exception as e:
            logger.error(f"Error in _optimize_order_book: {e}")
            raise
    
    def _optimize_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply specialized optimizations for technical indicator data.
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            Optimized DataFrame
        """
        try:
            result = df.copy()
        
            # Most indicators don't need high precision
            float_columns = result.select_dtypes(include=['float']).columns
            for col in float_columns:
                result[col] = result[col].astype(np.float32)
        
            return result
        except Exception as e:
            logger.error(f"Error in _optimize_indicators: {e}")
            raise
    
    def create_efficient_time_series(self, data: Union[List[float], np.ndarray], 
                                    timestamps: Optional[Union[List, np.ndarray]] = None) -> Dict[str, Any]:
        """
        Create a memory-efficient time series data structure.
        
        Args:
            data: Time series data values
            timestamps: Optional timestamps for the data
            
        Returns:
            Dictionary with optimized time series data
        """
        # Calculate original memory usage
        try:
            original_size = sys.getsizeof(data)
            if timestamps is not None:
                original_size += sys.getsizeof(timestamps)
        
            # Convert data to efficient numpy array with appropriate dtype
            if isinstance(data, list):
                # Determine appropriate dtype
                min_val = min(data) if data else 0
                max_val = max(data) if data else 0
            
                if all(isinstance(x, int) for x in data):
                    # Integer data
                    if min_val >= 0:
                        if max_val < 2**8:
                            dtype = np.uint8
                        elif max_val < 2**16:
                            dtype = np.uint16
                        elif max_val < 2**32:
                            dtype = np.uint32
                        else:
                            dtype = np.uint64
                    else:
                        if min_val > -2**7 and max_val < 2**7:
                            dtype = np.int8
                        elif min_val > -2**15 and max_val < 2**15:
                            dtype = np.int16
                        elif min_val > -2**31 and max_val < 2**31:
                            dtype = np.int32
                        else:
                            dtype = np.int64
                else:
                    # Float data - use float32 for most financial data
                    dtype = np.float32
                
                optimized_data = np.array(data, dtype=dtype)
            else:
                # Already numpy array, just ensure efficient dtype
                if data.dtype == np.float64:
                    optimized_data = data.astype(np.float32)
                elif data.dtype == np.int64:
                    # Check range to see if we can use a smaller int type
                    min_val = data.min() if data.size > 0 else 0
                    max_val = data.max() if data.size > 0 else 0
                
                    if min_val >= 0:
                        if max_val < 2**8:
                            optimized_data = data.astype(np.uint8)
                        elif max_val < 2**16:
                            optimized_data = data.astype(np.uint16)
                        elif max_val < 2**32:
                            optimized_data = data.astype(np.uint32)
                        else:
                            optimized_data = data
                    else:
                        if min_val > -2**7 and max_val < 2**7:
                            optimized_data = data.astype(np.int8)
                        elif min_val > -2**15 and max_val < 2**15:
                            optimized_data = data.astype(np.int16)
                        elif min_val > -2**31 and max_val < 2**31:
                            optimized_data = data.astype(np.int32)
                        else:
                            optimized_data = data
                else:
                    optimized_data = data
        
            # Optimize timestamps if provided
            optimized_timestamps = None
            if timestamps is not None:
                if isinstance(timestamps, list):
                    optimized_timestamps = np.array(timestamps)
                else:
                    optimized_timestamps = timestamps
        
            # Calculate optimized size
            optimized_size = optimized_data.nbytes
            if optimized_timestamps is not None:
                optimized_size += optimized_timestamps.nbytes
        
            # Calculate reduction percentage
            reduction = (original_size - optimized_size) / original_size * 100 if original_size > 0 else 0
        
            # Create optimization result
            opt_result = OptimizationResult(
                original_size=original_size,
                optimized_size=optimized_size,
                reduction_percent=reduction,
                structure_type=DataStructureType.TIME_SERIES,
                description=f"Optimized time series: {reduction:.2f}% reduction"
            )
        
            # Store optimization stats
            if DataStructureType.TIME_SERIES.value not in self.optimization_stats:
                self.optimization_stats[DataStructureType.TIME_SERIES.value] = []
            self.optimization_stats[DataStructureType.TIME_SERIES.value].append(opt_result)
        
            logger.info(f"Time series optimization: {opt_result.description}")
        
            return {
                'data': optimized_data,
                'timestamps': optimized_timestamps,
                'optimization_result': opt_result
            }
        except Exception as e:
            logger.error(f"Error in create_efficient_time_series: {e}")
            raise
    
    def create_efficient_ohlcv(self, ohlcv_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Create a memory-efficient OHLCV data structure.
        
        Args:
            ohlcv_data: Dictionary with OHLCV data (open, high, low, close, volume)
            
        Returns:
            Dictionary with optimized OHLCV data
        """
        # Calculate original memory usage
        try:
            original_size = sum(sys.getsizeof(arr) for arr in ohlcv_data.values())
        
            # Create optimized structure
            optimized_data = {}
        
            # Optimize price data (OHLC) to float32
            for key in ['open', 'high', 'low', 'close']:
                if key in ohlcv_data:
                    optimized_data[key] = np.array(ohlcv_data[key], dtype=np.float32)
        
            # Optimize volume data based on range
            if 'volume' in ohlcv_data:
                volume = ohlcv_data['volume']
                max_vol = max(volume) if volume else 0
            
                if max_vol < 2**32:
                    optimized_data['volume'] = np.array(volume, dtype=np.uint32)
                else:
                    optimized_data['volume'] = np.array(volume, dtype=np.uint64)
        
            # Optimize timestamp data if present
            if 'timestamp' in ohlcv_data:
                optimized_data['timestamp'] = np.array(ohlcv_data['timestamp'])
        
            # Calculate optimized size
            optimized_size = sum(arr.nbytes for arr in optimized_data.values())
        
            # Calculate reduction percentage
            reduction = (original_size - optimized_size) / original_size * 100 if original_size > 0 else 0
        
            # Create optimization result
            opt_result = OptimizationResult(
                original_size=original_size,
                optimized_size=optimized_size,
                reduction_percent=reduction,
                structure_type=DataStructureType.OHLCV,
                description=f"Optimized OHLCV data: {reduction:.2f}% reduction"
            )
        
            # Store optimization stats
            if DataStructureType.OHLCV.value not in self.optimization_stats:
                self.optimization_stats[DataStructureType.OHLCV.value] = []
            self.optimization_stats[DataStructureType.OHLCV.value].append(opt_result)
        
            logger.info(f"OHLCV optimization: {opt_result.description}")
        
            return {
                'data': optimized_data,
                'optimization_result': opt_result
            }
        except Exception as e:
            logger.error(f"Error in create_efficient_ohlcv: {e}")
            raise
    
    def create_efficient_market_depth(self, bids: List[Tuple[float, float]], 
                                     asks: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Create a memory-efficient market depth data structure.
        
        Args:
            bids: List of (price, size) tuples for bids
            asks: List of (price, size) tuples for asks
            
        Returns:
            Dictionary with optimized market depth data
        """
        # Calculate original memory usage
        try:
            original_size = sys.getsizeof(bids) + sys.getsizeof(asks)
        
            # Create structured arrays for efficient storage
            bid_dtype = np.dtype([('price', np.float32), ('size', np.float32)])
            ask_dtype = np.dtype([('price', np.float32), ('size', np.float32)])
        
            optimized_bids = np.array(bids, dtype=bid_dtype)
            optimized_asks = np.array(asks, dtype=ask_dtype)
        
            # Calculate optimized size
            optimized_size = optimized_bids.nbytes + optimized_asks.nbytes
        
            # Calculate reduction percentage
            reduction = (original_size - optimized_size) / original_size * 100 if original_size > 0 else 0
        
            # Create optimization result
            opt_result = OptimizationResult(
                original_size=original_size,
                optimized_size=optimized_size,
                reduction_percent=reduction,
                structure_type=DataStructureType.MARKET_DEPTH,
                description=f"Optimized market depth: {reduction:.2f}% reduction"
            )
        
            # Store optimization stats
            if DataStructureType.MARKET_DEPTH.value not in self.optimization_stats:
                self.optimization_stats[DataStructureType.MARKET_DEPTH.value] = []
            self.optimization_stats[DataStructureType.MARKET_DEPTH.value].append(opt_result)
        
            logger.info(f"Market depth optimization: {opt_result.description}")
        
            return {
                'bids': optimized_bids,
                'asks': optimized_asks,
                'optimization_result': opt_result
            }
        except Exception as e:
            logger.error(f"Error in create_efficient_market_depth: {e}")
            raise
    
    def optimize_memory_usage(self):
        """
        Optimize overall memory usage by cleaning up unused objects and running garbage collection.
        
        Returns:
            Dictionary with memory usage statistics
        """
        # Get initial memory usage
        try:
            initial_usage = self._get_memory_usage()
        
            # Run garbage collection
            gc.collect()
        
            # Get final memory usage
            final_usage = self._get_memory_usage()
        
            # Calculate reduction
            reduction = initial_usage - final_usage
            reduction_percent = (reduction / initial_usage * 100) if initial_usage > 0 else 0
        
            logger.info(f"Memory optimization: {reduction_percent:.2f}% reduction "
                       f"({reduction / (1024*1024):.2f} MB freed)")
        
            return {
                'initial_usage_mb': initial_usage / (1024*1024),
                'final_usage_mb': final_usage / (1024*1024),
                'reduction_mb': reduction / (1024*1024),
                'reduction_percent': reduction_percent
            }
        except Exception as e:
            logger.error(f"Error in optimize_memory_usage: {e}")
            raise
    
    def _get_memory_usage(self) -> int:
        """
        Get current memory usage.
        
        Returns:
            Memory usage in bytes
        """
        # This is a simplified implementation
        # In a real system, you would use psutil or memory_profiler
        return 0  # Placeholder
    
    def get_optimization_stats(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get statistics on all optimizations performed.
        
        Returns:
            Dictionary with optimization statistics by data structure type
        """
        try:
            stats = {}
        
            for structure_type, results in self.optimization_stats.items():
                stats[structure_type] = []
                for result in results:
                    stats[structure_type].append({
                        'original_size': result.original_size,
                        'optimized_size': result.optimized_size,
                        'reduction_percent': result.reduction_percent,
                        'description': result.description
                    })
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_optimization_stats: {e}")
            raise


class MemoryEfficientCache(Generic[T]):
    """
    Memory-efficient cache implementation using weak references.
    
    This cache automatically removes entries when they are no longer referenced
    elsewhere in the code, helping to prevent memory leaks.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items to store in the cache
        """
        try:
            self.max_size = max_size
            self.cache = {}
            self.access_count = defaultdict(int)
            self.access_order = deque()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get(self, key: str) -> Optional[T]:
        """
        Get an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached item or None if not found or expired
        """
        try:
            if key in self.cache:
                item_ref = self.cache[key]
                item = item_ref()
            
                if item is not None:
                    # Update access statistics
                    self.access_count[key] += 1
                    self.access_order.append(key)
                
                    # Trim access order if it gets too large
                    if len(self.access_order) > self.max_size * 2:
                        self.access_order = deque(list(self.access_order)[-self.max_size:])
                
                    return item
                else:
                    # Reference has been garbage collected
                    del self.cache[key]
                    if key in self.access_count:
                        del self.access_count[key]
        
            return None
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise
    
    def put(self, key: str, value: T) -> None:
        """
        Add an item to the cache.
        
        Args:
            key: Cache key
            value: Item to cache
        """
        # Ensure we don't exceed max size
        try:
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
        
            # Store weak reference
            self.cache[key] = weakref.ref(value)
            self.access_count[key] = 1
            self.access_order.append(key)
        except Exception as e:
            logger.error(f"Error in put: {e}")
            raise
    
    def _evict(self) -> None:
        """Evict least recently used items from the cache."""
        try:
            if not self.cache:
                return
        
            # Count access frequency
            counter = defaultdict(int)
            for k in self.access_order:
                counter[k] += 1
        
            # Find least accessed items
            items_to_remove = []
            for k, count in sorted(counter.items(), key=lambda x: x[1]):
                if k in self.cache:
                    items_to_remove.append(k)
                    if len(items_to_remove) >= len(self.cache) // 4:  # Remove 25% of items
                        break
        
            # Remove items
            for k in items_to_remove:
                if k in self.cache:
                    del self.cache[k]
                if k in self.access_count:
                    del self.access_count[k]
        except Exception as e:
            logger.error(f"Error in _evict: {e}")
            raise
    
    def clear(self) -> None:
        """Clear the cache."""
        try:
            self.cache.clear()
            self.access_count.clear()
            self.access_order.clear()
        except Exception as e:
            logger.error(f"Error in clear: {e}")
            raise
    
    def size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            Number of items in the cache
        """
        return len(self.cache)


class RingBuffer:
    """
    Memory-efficient ring buffer for time series data.
    
    This data structure maintains a fixed-size buffer of the most recent values,
    automatically discarding old values when new ones are added.
    """
    
    def __init__(self, capacity: int, dtype=np.float32):
        """
        Initialize the ring buffer.
        
        Args:
            capacity: Maximum number of items in the buffer
            dtype: Data type for the buffer
        """
        try:
            self.capacity = capacity
            self.buffer = np.zeros(capacity, dtype=dtype)
            self.timestamps = np.zeros(capacity, dtype=np.int64)
            self.size = 0
            self.index = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def append(self, value: float, timestamp: Optional[int] = None) -> None:
        """
        Add a value to the buffer.
        
        Args:
            value: Value to add
            timestamp: Optional timestamp for the value
        """
        try:
            self.buffer[self.index] = value
        
            if timestamp is not None:
                self.timestamps[self.index] = timestamp
            else:
                self.timestamps[self.index] = int(time.time() * 1000)  # Default to current time in ms
        
            self.index = (self.index + 1) % self.capacity
            self.size = min(self.size + 1, self.capacity)
        except Exception as e:
            logger.error(f"Error in append: {e}")
            raise
    
    def get_values(self) -> np.ndarray:
        """
        Get all values in the buffer in chronological order.
        
        Returns:
            Array of values
        """
        try:
            if self.size < self.capacity:
                return self.buffer[:self.size].copy()
            else:
                return np.concatenate([self.buffer[self.index:], self.buffer[:self.index]])
        except Exception as e:
            logger.error(f"Error in get_values: {e}")
            raise
    
    def get_timestamps(self) -> np.ndarray:
        """
        Get all timestamps in the buffer in chronological order.
        
        Returns:
            Array of timestamps
        """
        try:
            if self.size < self.capacity:
                return self.timestamps[:self.size].copy()
            else:
                return np.concatenate([self.timestamps[self.index:], self.timestamps[:self.index]])
        except Exception as e:
            logger.error(f"Error in get_timestamps: {e}")
            raise
    
    def get_latest(self, n: int = 1) -> np.ndarray:
        """
        Get the n most recent values.
        
        Args:
            n: Number of values to return
            
        Returns:
            Array of the n most recent values
        """
        try:
            if n <= 0:
                return np.array([], dtype=self.buffer.dtype)
        
            n = min(n, self.size)
        
            if self.size < self.capacity:
                return self.buffer[max(0, self.size - n):self.size].copy()
            else:
                idx = (self.index - n) % self.capacity
                if idx < self.index:
                    return self.buffer[idx:self.index].copy()
                else:
                    return np.concatenate([self.buffer[idx:], self.buffer[:self.index]])
        except Exception as e:
            logger.error(f"Error in get_latest: {e}")
            raise
    
    def clear(self) -> None:
        """Clear the buffer."""
        try:
            self.size = 0
            self.index = 0
        except Exception as e:
            logger.error(f"Error in clear: {e}")
            raise


# Singleton instance for easy access
_default_optimizer = None

def get_default_optimizer() -> MemoryOptimizer:
    """Get or create the default memory optimizer instance."""
    try:
        global _default_optimizer
        if _default_optimizer is None:
            _default_optimizer = MemoryOptimizer()
        return _default_optimizer
    except Exception as e:
        logger.error(f"Error in get_default_optimizer: {e}")
        raise


# Example usage functions
def optimize_market_data(market_data: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize market data DataFrame for memory efficiency.
    
    Args:
        market_data: DataFrame with market data
        
    Returns:
        Optimized DataFrame
    """
    try:
        optimizer = get_default_optimizer()
    
        # Determine the type of data
        if all(col in market_data.columns for col in ['open', 'high', 'low', 'close']):
            data_type = DataStructureType.OHLCV
        elif 'price' in market_data.columns:
            data_type = DataStructureType.PRICE_SERIES
        else:
            data_type = DataStructureType.CUSTOM
    
        # Optimize the DataFrame
        optimized_data, result = optimizer.optimize_dataframe(market_data, data_type)
    
        logger.info(f"Market data optimization: {result.description}")
        return optimized_data
    except Exception as e:
        logger.error(f"Error in optimize_market_data: {e}")
        raise
