"""Performance Optimization Module for the Market Intelligence System."""

import logging
import numpy as np
import pandas as pd
import psutil
import gc
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import lru_cache
import cProfile
import pstats
try:
    from memory_profiler import profile
except ImportError:
    profile = None


class PerformanceMonitor:
    """Monitor and track performance metrics of the trading system."""
    
    def __init__(self):
        self.performance_metrics = {}
        self.execution_times = {}
        self.memory_usage = {}
        self.cpu_usage = {}
        logger.info("Initialized PerformanceMonitor")
    
    def track_execution_time(self, function_name: str, execution_time: float):
        """Track execution time for functions."""
        if function_name not in self.execution_times:
            self.execution_times[function_name] = []
        
        self.execution_times[function_name].append({
            'timestamp': datetime.now(),
            'execution_time': execution_time
        })
        
        # Keep only last 1000 measurements
        if len(self.execution_times[function_name]) > 1000:
            self.execution_times[function_name] = self.execution_times[function_name][-1000:]
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        summary = {
            'execution_times': {},
            'memory_metrics': self._get_memory_metrics(),
            'cpu_metrics': self._get_cpu_metrics(),
            'bottlenecks': self._identify_bottlenecks()
        }
        
        # Summarize execution times
        for func_name, times in self.execution_times.items():
            if times:
                execution_values = [t['execution_time'] for t in times]
                summary['execution_times'][func_name] = {
                    'avg_time': np.mean(execution_values),
                    'max_time': np.max(execution_values),
                    'min_time': np.min(execution_values),
                    'std_time': np.std(execution_values),
                    'call_count': len(execution_values)
                }
        
        return summary
    
    def _get_memory_metrics(self) -> Dict:
        """Get current memory usage metrics."""
        process = psutil.Process()
        
        return {
            'memory_percent': process.memory_percent(),
            'memory_info': process.memory_info()._asdict(),
            'memory_full_info': process.memory_full_info()._asdict()
        }
    
    def _get_cpu_metrics(self) -> Dict:
        """Get current CPU usage metrics."""
        process = psutil.Process()
        
        return {
            'cpu_percent': process.cpu_percent(),
            'cpu_times': process.cpu_times()._asdict(),
            'num_threads': process.num_threads()
        }
    
    def _identify_bottlenecks(self) -> List[Dict]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for func_name, times in self.execution_times.items():
            if times:
                execution_values = [t['execution_time'] for t in times]
                avg_time = np.mean(execution_values)
                
                # Flag functions taking more than 1 second on average
                if avg_time > 1.0:
                    bottlenecks.append({
                        'function': func_name,
                        'avg_execution_time': avg_time,
                        'severity': 'high' if avg_time > 5.0 else 'medium'
                    })
        
        return sorted(bottlenecks, key=lambda x: x['avg_execution_time'], reverse=True)


class CacheManager:
    """Intelligent caching system for market data and analysis results."""
    
    def __init__(self, max_cache_size: int = 1000):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_access_count = {}
        self.max_cache_size = max_cache_size
        logger.info(f"Initialized CacheManager with max size: {max_cache_size}")
    
    @lru_cache(maxsize=128)
    def get_cached_analysis(self, symbol: str, timeframe: str, 
                          analysis_type: str, data_hash: str) -> Optional[Dict]:
        """Get cached analysis results."""
        cache_key = f"{symbol}_{timeframe}_{analysis_type}_{data_hash}"
        
        if cache_key in self.cache:
            # Update access count and timestamp
            self.cache_access_count[cache_key] = self.cache_access_count.get(cache_key, 0) + 1
            self.cache_timestamps[cache_key] = datetime.now()
            
            # Check if cache is still valid (5 minutes for most analysis)
            cache_age = datetime.now() - self.cache_timestamps[cache_key]
            if cache_age < timedelta(minutes=5):
                return self.cache[cache_key]
            else:
                # Remove expired cache
                self._remove_cache_entry(cache_key)
        
        return None
    
    def set_cached_analysis(self, symbol: str, timeframe: str, 
                          analysis_type: str, data_hash: str, result: Dict):
        """Cache analysis results."""
        cache_key = f"{symbol}_{timeframe}_{analysis_type}_{data_hash}"
        
        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_cache_size:
            self._evict_least_used()
        
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now()
        self.cache_access_count[cache_key] = 1
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove a cache entry."""
        self.cache.pop(cache_key, None)
        self.cache_timestamps.pop(cache_key, None)
        self.cache_access_count.pop(cache_key, None)
    
    def _evict_least_used(self):
        """Evict least recently used cache entries."""
        if not self.cache:
            return
        
        # Sort by access count and timestamp
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: (self.cache_access_count.get(k, 0), 
                          self.cache_timestamps.get(k, datetime.min))
        )
        
        # Remove 10% of cache entries
        evict_count = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:evict_count]:
            self._remove_cache_entry(key)
    
    def clear_expired_cache(self, max_age_minutes: int = 30):
        """Clear expired cache entries."""
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > timedelta(minutes=max_age_minutes):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")


class ParallelProcessor:
    """Parallel processing for computationally intensive tasks."""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(8, mp.cpu_count())
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Initialized ParallelProcessor with {self.max_workers} workers")
    
    async def process_multiple_symbols(self, symbols: List[str], 
                                     analysis_function, *args, **kwargs) -> Dict:
        """Process multiple symbols in parallel."""
        loop = asyncio.get_event_loop()
        
        # Create tasks for each symbol
        tasks = []
        for symbol in symbols:
            task = loop.run_in_executor(
                self.thread_executor,
                analysis_function,
                symbol,
                *args,
                **kwargs
            )
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        results = {}
        for symbol, task in tasks:
            try:
                result = await task
                results[symbol] = result
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
                results[symbol] = None
        
        return results
    
    async def process_multiple_timeframes(self, symbol: str, timeframes: List[str],
                                        analysis_function, *args, **kwargs) -> Dict:
        """Process multiple timeframes in parallel."""
        loop = asyncio.get_event_loop()
        
        # Create tasks for each timeframe
        tasks = []
        for timeframe in timeframes:
            task = loop.run_in_executor(
                self.thread_executor,
                analysis_function,
                symbol,
                timeframe,
                *args,
                **kwargs
            )
            tasks.append((timeframe, task))
        
        # Wait for all tasks to complete
        results = {}
        for timeframe, task in tasks:
            try:
                result = await task
                results[timeframe] = result
            except Exception as e:
                logger.error(f"Error processing timeframe {timeframe}: {e}")
                results[timeframe] = None
        
        return results
    
    def process_dataframe_chunks(self, df: pd.DataFrame, 
                               processing_function, chunk_size: int = 1000) -> pd.DataFrame:
        """Process large DataFrames in parallel chunks."""
        if len(df) <= chunk_size:
            return processing_function(df)
        
        # Split DataFrame into chunks
        chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(processing_function, chunk) for chunk in chunks]
            processed_chunks = [future.result() for future in futures]
        
        # Combine results
        return pd.concat(processed_chunks, ignore_index=True)
    
    def shutdown(self):
        """Shutdown executors."""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)


class MemoryOptimizer:
    """Optimize memory usage for large datasets."""
    
    def __init__(self):
        self.memory_threshold = 0.8  # 80% memory usage threshold
        logger.info("Initialized MemoryOptimizer")
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        original_memory = df.memory_usage(deep=True).sum()
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize object columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        optimized_memory = df.memory_usage(deep=True).sum()
        memory_saved = original_memory - optimized_memory
        
        logger.info(f"Memory optimization: {memory_saved / 1024**2:.2f} MB saved "
                   f"({memory_saved / original_memory * 100:.1f}% reduction)")
        
        return df
    
    def check_memory_usage(self) -> Dict:
        """Check current memory usage."""
        
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free,
            'threshold_exceeded': memory.percent > self.memory_threshold * 100
        }
    
    def cleanup_memory(self):
        """Force garbage collection and memory cleanup."""
        gc.collect()
        logger.info("Memory cleanup performed")
    
    def get_object_sizes(self, obj_dict: Dict) -> Dict:
        """Get memory sizes of objects."""
        import sys
        
        sizes = {}
        for name, obj in obj_dict.items():
            sizes[name] = sys.getsizeof(obj)
        
        return sorted(sizes.items(), key=lambda x: x[1], reverse=True)


class DatabaseOptimizer:
    """Optimize database operations for market data."""
    
    def __init__(self):
        self.connection_pool = None
        self.query_cache = {}
        logger.info("Initialized DatabaseOptimizer")
    
    def optimize_query(self, query: str, params: Dict = None) -> str:
        """Optimize SQL queries for better performance."""
        # Basic query optimization rules
        optimized_query = query
        
        # Add LIMIT if not present in SELECT queries
        if 'SELECT' in query.upper() and 'LIMIT' not in query.upper():
            optimized_query += ' LIMIT 10000'
        
        # Add indexes hints for common patterns
        if 'WHERE timestamp' in query:
            optimized_query = optimized_query.replace(
                'WHERE timestamp',
                'WHERE timestamp /* INDEX(timestamp_idx) */'
            )
        
        return optimized_query
    
    def batch_insert(self, table_name: str, data: List[Dict], 
                    batch_size: int = 1000) -> int:
        """Perform batch inserts for better performance."""
        total_inserted = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            # Simulate batch insert
            total_inserted += len(batch)
            logger.debug(f"Inserted batch of {len(batch)} records")
        
        return total_inserted
    
    def create_indexes(self, table_name: str, columns: List[str]):
        """Create database indexes for performance."""
        for column in columns:
            index_name = f"idx_{table_name}_{column}"
            logger.info(f"Creating index {index_name} on {table_name}.{column}")
            # Simulate index creation
    
    def analyze_query_performance(self, query: str) -> Dict:
        """Analyze query performance and suggest optimizations."""
        # Simulate query analysis
        analysis = {
            'estimated_cost': np.random.uniform(10, 1000),
            'estimated_rows': np.random.randint(100, 10000),
            'suggested_indexes': [],
            'optimization_suggestions': []
        }
        
        # Add suggestions based on query patterns
        if 'ORDER BY' in query.upper():
            analysis['suggested_indexes'].append('Consider index on ORDER BY columns')
        
        if 'WHERE' in query.upper():
            analysis['suggested_indexes'].append('Consider index on WHERE columns')
        
        return analysis


class RealTimeOptimizer:
    """Optimize real-time data processing and analysis."""
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.batch_processor = None
        self.batch_size = 100
        self.batch_timeout = 1.0  # seconds
        logger.info("Initialized RealTimeOptimizer")
    
    async def start_batch_processor(self):
        """Start the batch processor for real-time data."""
        self.batch_processor = asyncio.create_task(self._process_batches())
    
    async def add_data_point(self, data_point: Dict):
        """Add a data point to the processing queue."""
        await self.processing_queue.put(data_point)
    
    async def _process_batches(self):
        """Process data in batches for efficiency."""
        batch = []
        last_process_time = datetime.now()
        
        while True:
            try:
                # Wait for data with timeout
                data_point = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=self.batch_timeout
                )
                batch.append(data_point)
                
                # Process batch if size reached or timeout exceeded
                current_time = datetime.now()
                time_elapsed = (current_time - last_process_time).total_seconds()
                
                if len(batch) >= self.batch_size or time_elapsed >= self.batch_timeout:
                    await self._process_data_batch(batch)
                    batch = []
                    last_process_time = current_time
                    
            except asyncio.TimeoutError:
                # Process any remaining data in batch
                if batch:
                    await self._process_data_batch(batch)
                    batch = []
                    last_process_time = datetime.now()
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
    
    async def _process_data_batch(self, batch: List[Dict]):
        """Process a batch of data points."""
        if not batch:
            return
        try:
        
            # Convert to DataFrame for efficient processing
            df = pd.DataFrame(batch)
            
            # Perform batch analysis
            analysis_results = self._analyze_batch(df)
            
            logger.debug(f"Processed batch of {len(batch)} data points")
            
        except Exception as e:
            logger.error(f"Error processing data batch: {e}")
    
    def _analyze_batch(self, df: pd.DataFrame) -> Dict:
        """Analyze a batch of data efficiently."""
        # Simulate batch analysis
        return {
            'batch_size': len(df),
            'processing_time': datetime.now(),
            'summary_stats': df.describe().to_dict() if not df.empty else {}
        }
    
    def optimize_update_frequency(self, analysis_type: str, 
                                current_frequency: float) -> float:
        """Optimize update frequency based on market conditions."""
        # Dynamic frequency adjustment based on volatility
        volatility_factor = np.random.uniform(0.5, 2.0)  # Simulate volatility
        
        if volatility_factor > 1.5:
            # High volatility - increase frequency
            return min(current_frequency * 1.5, 10.0)
        elif volatility_factor < 0.8:
            # Low volatility - decrease frequency
            return max(current_frequency * 0.7, 0.1)
        else:
            return current_frequency
    
    def stop_batch_processor(self):
        """Stop the batch processor."""
        if self.batch_processor:
            self.batch_processor.cancel()


def performance_timer(func):
    """Decorator to time function execution."""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
        
        # Track in global performance monitor if available
        if hasattr(func, '_performance_monitor'):
            func._performance_monitor.track_execution_time(func.__name__, execution_time)
        
        return result
    return wrapper


def memory_monitor(func):
    """Decorator to monitor memory usage."""
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        
        memory_before = process.memory_info().rss
        result = func(*args, **kwargs)
        memory_after = process.memory_info().rss
        
        memory_diff = memory_after - memory_before
        if memory_diff > 0:
            logger.debug(f"{func.__name__} used {memory_diff / 1024**2:.2f} MB memory")
        
        return result
    return wrapper
