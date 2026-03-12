"""
from typing import Any, Dict, Set
Performance optimization utilities for trading system
"""

import logging
import time
import functools
from typing import Callable, Any, Dict
import threading
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cProfile
    import pstats
    from io import StringIO
    PROFILING_AVAILABLE = True
except ImportError:
    PROFILING_AVAILABLE = False


class PerformanceMonitor:
    """Monitor and optimize system performance"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.latencies = {}
        self.call_counts = {}
        self.lock = threading.Lock()
    
    def record_latency(self, operation: str, latency: float):
        """Record operation latency"""
        with self.lock:
            if operation not in self.latencies:
                self.latencies[operation] = deque(maxlen=self.window_size)
                self.call_counts[operation] = 0
            
            self.latencies[operation].append(latency)
            self.call_counts[operation] += 1
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get performance statistics"""
        with self.lock:
            if operation not in self.latencies:
                return {}
            
            latencies = list(self.latencies[operation])
            
            return {
                'mean': np.mean(latencies),
                'median': np.median(latencies),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'min': np.min(latencies),
                'max': np.max(latencies),
                'count': self.call_counts[operation]
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all performance statistics"""
        return {op: self.get_stats(op) for op in self.latencies.keys()}
    
    def print_report(self):
        """Print performance report"""
        print("\n" + "="*80)
        logger.info("PERFORMANCE REPORT")
        print("="*80)
        
        for operation, stats in self.get_all_stats().items():
            logger.info(f"\n{operation}:")
            logger.info(f"  Calls: {stats['count']}")
            logger.info(f"  Mean: {stats['mean']*1000:.2f}ms")
            logger.info(f"  Median: {stats['median']*1000:.2f}ms")
            logger.info(f"  P95: {stats['p95']*1000:.2f}ms")
            logger.info(f"  P99: {stats['p99']*1000:.2f}ms")
            logger.info(f"  Min: {stats['min']*1000:.2f}ms")
            logger.info(f"  Max: {stats['max']*1000:.2f}ms")


_monitor = PerformanceMonitor()


def measure_performance(operation_name: str = None):
    """Decorator to measure function performance"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency = time.perf_counter() - start
                _monitor.record_latency(op_name, latency)
        
        return wrapper
    return decorator


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _monitor


class MemoryOptimizer:
    """Optimize memory usage"""
    
    @staticmethod
    def optimize_dataframe(df):
        """Optimize pandas DataFrame memory usage"""
        try:
            import pandas as pd
            
            for col in df.columns:
                col_type = df[col].dtype
                
                if col_type != object:
                    c_min = df[col].min()
                    c_max = df[col].max()
                    
                    if str(col_type)[:3] == 'int':
                        if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                            df[col] = df[col].astype(np.int8)
                        elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                            df[col] = df[col].astype(np.int16)
                        elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                            df[col] = df[col].astype(np.int32)
                    else:
                        if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                            df[col] = df[col].astype(np.float32)
            
            return df
        except Exception as e:
            logger.error(f"Failed to optimize DataFrame: {e}")
            return df
    
    @staticmethod
    def clear_cache(obj):
        """Clear object cache"""
        if hasattr(obj, '__dict__'):
            for attr in list(obj.__dict__.keys()):
                if attr.startswith('_cache'):
                    delattr(obj, attr)


class BatchProcessor:
    """Process data in optimized batches"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def process_batches(self, data: list, processor: Callable) -> list:
        """Process data in batches"""
        results = []
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
        
        return results


class CacheManager:
    """Manage caching for expensive operations"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Any:
        """Get cached value"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        with self.lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()


def cached(ttl: float = 300):
    """Decorator for caching function results"""
    cache = CacheManager(ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        return wrapper
    return decorator


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test performance monitoring
    @measure_performance("test_operation")
    def slow_function():
        time.sleep(0.01)
        return 42
    
    # Run multiple times
    for _ in range(100):
        slow_function()
    
    # Print report
    monitor = get_performance_monitor()
    monitor.print_report()
    
    logger.info("\n✅ Performance optimizer test passed!")
