import logging
logger = logging.getLogger(__name__)
"""
Liquidity Analysis Performance Optimization Integration

This module provides performance-optimized versions of liquidity analysis functions
with memory management, parallel processing, and caching capabilities.
"""

import asyncio
import concurrent.futures
import functools
import threading
import time
from collections import defaultdict, OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import weakref
import pickle
import hashlib

import numpy as np
import pandas as pd
from loguru import logger

from .liquidity import LiquidityAnalyzer, LiquidityPool, OrderBlock, FairValueGap
from .realtime_liquidity import RealTimeLiquidityAnalyzer, StreamingConfig, StreamingMode
from .market_structure import TimeFrame
from ..performance.memory_optimization import (
    MemoryOptimizer, MemoryEfficientCache, RingBuffer, DataStructureType
)


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    enable_caching: bool = True
    cache_size: int = 1000
    enable_parallel: bool = True
    max_workers: int = 4
    enable_memory_optimization: bool = True
    batch_size: int = 100
    compression_enabled: bool = True
    async_processing: bool = False


class LiquidityCache:
    """High-performance cache for liquidity analysis results."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
    
    def _generate_key(self, symbol: str, timeframe: TimeFrame, data_hash: str) -> str:
        """Generate cache key from parameters."""
        return f"{symbol}_{timeframe.name}_{data_hash}"
    
    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """Generate hash for DataFrame to use as cache key."""
        # Use last 10 rows and basic stats for hashing
        if len(df) > 10:
            sample_data = df.tail(10)
        else:
            sample_data = df
        
        # Create hash from shape, columns, and sample values
        hash_input = f"{df.shape}_{list(df.columns)}_{sample_data.values.tobytes()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def get(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Get cached result if available."""
        with self.lock:
            data_hash = self._hash_dataframe(df)
            key = self._generate_key(symbol, timeframe, data_hash)
            
            if key in self.cache:
                # Move to end (most recently used)
                result = self.cache.pop(key)
                self.cache[key] = result
                self.hit_count += 1
                return result
            
            self.miss_count += 1
            return None
    
    def put(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame, result: Dict[str, Any]):
        """Cache analysis result."""
        with self.lock:
            data_hash = self._hash_dataframe(df)
            key = self._generate_key(symbol, timeframe, data_hash)
            
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self.cache.popitem(last=False)
            
            self.cache[key] = result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size
        }
    
    def clear(self):
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0


class OptimizedLiquidityAnalyzer:
    """
    Performance-optimized liquidity analyzer with caching, parallel processing,
    and memory management capabilities.
    """
    
    def __init__(self, config: PerformanceConfig = None):
        """Initialize the optimized analyzer."""
        self.config = config or PerformanceConfig()
        
        # Core components
        self.analyzer = LiquidityAnalyzer(multi_timeframe=True)
        self.memory_optimizer = MemoryOptimizer()
        
        # Caching
        if self.config.enable_caching:
            self.cache = LiquidityCache(self.config.cache_size)
        else:
            self.cache = None
        
        # Parallel processing
        if self.config.enable_parallel:
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
            )
        else:
            self.executor = None
        
        # Performance tracking
        self.performance_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_analysis_time': 0.0,
            'memory_optimizations': 0,
            'parallel_executions': 0
        }
        
        self.analysis_times = []
        self.lock = threading.RLock()
    
    def analyze_symbol_optimized(self, symbol: str, timeframe: TimeFrame, 
                               df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform optimized liquidity analysis for a single symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: Analysis timeframe
            df: OHLCV DataFrame
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get(symbol, timeframe, df)
                if cached_result:
                    self.performance_stats['cache_hits'] += 1
                    return cached_result
                else:
                    self.performance_stats['cache_misses'] += 1
            
            # Optimize DataFrame memory usage
            if self.config.enable_memory_optimization:
                df, opt_result = self.memory_optimizer.optimize_dataframe(
                    df, DataStructureType.OHLCV
                )
                self.performance_stats['memory_optimizations'] += 1
            
            # Perform analysis
            result = self._perform_analysis(symbol, timeframe, df)
            
            # Cache result
            if self.cache:
                self.cache.put(symbol, timeframe, df, result)
            
            # Update performance stats
            analysis_time = time.time() - start_time
            self.analysis_times.append(analysis_time)
            if len(self.analysis_times) > 100:
                self.analysis_times.pop(0)
            
            self.performance_stats['total_analyses'] += 1
            self.performance_stats['avg_analysis_time'] = np.mean(self.analysis_times)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in optimized analysis for {symbol} {timeframe}: {e}")
            return {}
    
    def analyze_multiple_symbols(self, symbol_data: Dict[str, Dict[TimeFrame, pd.DataFrame]]) -> Dict[str, Dict[TimeFrame, Dict[str, Any]]]:
        """
        Analyze multiple symbols in parallel for maximum performance.
        
        Args:
            symbol_data: Dictionary of symbol -> timeframe -> DataFrame
            
        Returns:
            Dictionary of analysis results by symbol and timeframe
        """
        if not self.config.enable_parallel or not self.executor:
            # Sequential processing
            results = {}
            for symbol, tf_data in symbol_data.items():
                results[symbol] = {}
                for timeframe, df in tf_data.items():
                    results[symbol][timeframe] = self.analyze_symbol_optimized(symbol, timeframe, df)
            return results
        
        # Parallel processing
        start_time = time.time()
        futures = {}
        results = defaultdict(dict)
        
        # Submit all analysis tasks
        for symbol, tf_data in symbol_data.items():
            for timeframe, df in tf_data.items():
                future = self.executor.submit(
                    self.analyze_symbol_optimized, symbol, timeframe, df
                )
                futures[(symbol, timeframe)] = future
        
        # Collect results
        for (symbol, timeframe), future in futures.items():
            try:
                result = future.result(timeout=30)  # 30 second timeout
                results[symbol][timeframe] = result
            except Exception as e:
                logger.error(f"Error in parallel analysis for {symbol} {timeframe}: {e}")
                results[symbol][timeframe] = {}
        
        self.performance_stats['parallel_executions'] += 1
        logger.info(f"Parallel analysis of {len(futures)} tasks completed in {time.time() - start_time:.2f}s")
        
        return dict(results)
    
    async def analyze_symbol_async(self, symbol: str, timeframe: TimeFrame, 
                                 df: pd.DataFrame) -> Dict[str, Any]:
        """
        Async version of symbol analysis.
        
        Args:
            symbol: Trading symbol
            timeframe: Analysis timeframe
            df: OHLCV DataFrame
            
        Returns:
            Dictionary with analysis results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.analyze_symbol_optimized, symbol, timeframe, df
        )
    
    async def analyze_multiple_symbols_async(self, symbol_data: Dict[str, Dict[TimeFrame, pd.DataFrame]]) -> Dict[str, Dict[TimeFrame, Dict[str, Any]]]:
        """
        Async version of multiple symbol analysis.
        
        Args:
            symbol_data: Dictionary of symbol -> timeframe -> DataFrame
            
        Returns:
            Dictionary of analysis results by symbol and timeframe
        """
        tasks = []
        symbol_tf_pairs = []
        
        # Create async tasks
        for symbol, tf_data in symbol_data.items():
            for timeframe, df in tf_data.items():
                task = self.analyze_symbol_async(symbol, timeframe, df)
                tasks.append(task)
                symbol_tf_pairs.append((symbol, timeframe))
        
        # Execute all tasks concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results
        results = defaultdict(dict)
        for (symbol, timeframe), result in zip(symbol_tf_pairs, results_list):
            if isinstance(result, Exception):
                logger.error(f"Async analysis error for {symbol} {timeframe}: {result}")
                results[symbol][timeframe] = {}
            else:
                results[symbol][timeframe] = result
        
        return dict(results)
    
    def _perform_analysis(self, symbol: str, timeframe: TimeFrame, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform the actual liquidity analysis."""
        result = {}
        
        try:
            # Liquidity pools
            buy_pools, sell_pools = self.analyzer.find_equal_highs_lows(df, timeframe)
            result['buy_pools'] = [self._serialize_pool(pool) for pool in buy_pools]
            result['sell_pools'] = [self._serialize_pool(pool) for pool in sell_pools]
            
            # Order blocks
            order_blocks = self.analyzer.detect_order_blocks(df, timeframe)
            result['order_blocks'] = [self._serialize_order_block(ob) for ob in order_blocks]
            
            # Fair value gaps
            fvgs = self.analyzer.detect_fair_value_gaps(df, timeframe)
            result['fvgs'] = [self._serialize_fvg(fvg) for fvg in fvgs]
            
            # Premium/discount zones
            premium_zones, discount_zones = self.analyzer.identify_premium_discount_zones(df, timeframe)
            result['premium_zones'] = premium_zones
            result['discount_zones'] = discount_zones
            
            # Volume profile if available
            if 'volume' in df.columns and len(df) > 20:
                try:
                    volume_profile = self.analyzer.create_volume_profile(df, timeframe=timeframe)
                    result['volume_profile'] = self._serialize_volume_profile(volume_profile)
                except Exception as e:
                    logger.warning(f"Volume profile creation failed: {e}")
            
            # Liquidity grabs
            all_pools = buy_pools + sell_pools
            if all_pools:
                grabs = self.analyzer.detect_grabs(df, all_pools, timeframe)
                result['grabs'] = [self._serialize_grab(grab) for grab in grabs]
            
            result['analysis_timestamp'] = time.time()
            result['symbol'] = symbol
            result['timeframe'] = timeframe.name
            
        except Exception as e:
            logger.error(f"Error in analysis execution: {e}")
            result['error'] = str(e)
        
        return result
    
    def _serialize_pool(self, pool: LiquidityPool) -> Dict[str, Any]:
        """Serialize liquidity pool for caching."""
        return {
            'kind': pool.kind.value,
            'price': pool.price,
            'swing_idxs': pool.swing_idxs,
            'timeframe': pool.timeframe.name,
            'strength': pool.strength,
            'volume': pool.volume,
            'touched': pool.touched,
            'mitigated': pool.mitigated,
            'created_at': pool.created_at.isoformat() if pool.created_at else None
        }
    
    def _serialize_order_block(self, ob: OrderBlock) -> Dict[str, Any]:
        """Serialize order block for caching."""
        return {
            'type': ob.type.value,
            'start_idx': ob.start_idx,
            'end_idx': ob.end_idx,
            'high': ob.high,
            'low': ob.low,
            'open': ob.open,
            'close': ob.close,
            'volume': ob.volume,
            'strength': ob.strength,
            'timeframe': ob.timeframe.name,
            'mitigated': ob.mitigated,
            'mitigation_idx': ob.mitigation_idx,
            'created_at': ob.created_at.isoformat() if ob.created_at else None
        }
    
    def _serialize_fvg(self, fvg: FairValueGap) -> Dict[str, Any]:
        """Serialize fair value gap for caching."""
        return {
            'type': fvg.type.value,
            'idx': fvg.idx,
            'high': fvg.high,
            'low': fvg.low,
            'size': fvg.size,
            'size_pct': fvg.size_pct,
            'timeframe': fvg.timeframe.name,
            'filled': fvg.filled,
            'fill_idx': fvg.fill_idx,
            'strength': fvg.strength,
            'created_at': fvg.created_at.isoformat() if fvg.created_at else None
        }
    
    def _serialize_grab(self, grab) -> Dict[str, Any]:
        """Serialize liquidity grab for caching."""
        return {
            'idx': grab.idx,
            'pool': self._serialize_pool(grab.pool),
            'close_price': grab.close_price,
            'strength': grab.strength,
            'volume_delta': grab.volume_delta,
            'confirmed': grab.confirmed,
            'timeframe': grab.timeframe.name
        }
    
    def _serialize_volume_profile(self, vp) -> Dict[str, Any]:
        """Serialize volume profile for caching."""
        return {
            'price_levels': vp.price_levels.tolist(),
            'volumes': vp.volumes.tolist(),
            'poc': vp.poc,
            'value_area_high': vp.value_area_high,
            'value_area_low': vp.value_area_low,
            'value_area_pct': vp.value_area_pct,
            'timeframe': vp.timeframe.name
        }
    
    def batch_process_data(self, data_batches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process data in batches for improved performance.
        
        Args:
            data_batches: List of data batches to process
            
        Returns:
            List of processed results
        """
        results = []
        
        for i, batch in enumerate(data_batches):
            logger.info(f"Processing batch {i+1}/{len(data_batches)}")
            
            if self.config.enable_parallel and self.executor:
                # Process batch in parallel
                futures = []
                for item in batch.get('items', []):
                    future = self.executor.submit(
                        self.analyze_symbol_optimized,
                        item['symbol'],
                        item['timeframe'],
                        item['data']
                    )
                    futures.append(future)
                
                batch_results = []
                for future in concurrent.futures.as_completed(futures, timeout=60):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        logger.error(f"Batch processing error: {e}")
                        batch_results.append({})
                
                results.extend(batch_results)
            else:
                # Sequential processing
                for item in batch.get('items', []):
                    result = self.analyze_symbol_optimized(
                        item['symbol'],
                        item['timeframe'],
                        item['data']
                    )
                    results.append(result)
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = self.performance_stats.copy()
        
        # Add cache stats if available
        if self.cache:
            stats.update(self.cache.get_stats())
        
        # Add memory optimizer stats
        memory_stats = self.memory_optimizer.get_optimization_stats()
        stats['memory_optimizations_detail'] = memory_stats
        
        return stats
    
    def optimize_memory_usage(self):
        """Optimize memory usage across all components."""
        # Clear caches
        if self.cache:
            self.cache.clear()
        
        # Run memory optimizer
        memory_stats = self.memory_optimizer.optimize_memory_usage()
        
        # Clear old analysis times
        if len(self.analysis_times) > 50:
            self.analysis_times = self.analysis_times[-50:]
        
        logger.info(f"Memory optimization completed: {memory_stats}")
        return memory_stats
    
    def shutdown(self):
        """Shutdown the optimizer and clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        if self.cache:
            self.cache.clear()
        
        logger.info("Optimized liquidity analyzer shutdown completed")


class HighPerformanceRealTimeAnalyzer(RealTimeLiquidityAnalyzer):
    """
    High-performance version of the real-time liquidity analyzer with
    advanced optimization features.
    """
    
    def __init__(self, config: StreamingConfig = None, perf_config: PerformanceConfig = None):
        """Initialize the high-performance analyzer."""
        super().__init__(config)
        
        self.perf_config = perf_config or PerformanceConfig()
        self.optimized_analyzer = OptimizedLiquidityAnalyzer(self.perf_config)
        
        # Replace the standard analyzer with the optimized version
        self.analyzer = self.optimized_analyzer.analyzer
    
    def _process_symbol_timeframe(self, symbol: str, timeframe: TimeFrame, 
                                ohlcv: Optional[Dict[str, float]] = None):
        """Optimized version of symbol-timeframe processing."""
        try:
            # Get recent data from buffers
            prices = self.price_buffers[symbol][timeframe].get_values()
            volumes = self.volume_buffers[symbol][timeframe].get_values()
            timestamps = self.price_buffers[symbol][timeframe].get_timestamps()
            
            if len(prices) < 10:
                return
            
            # Create DataFrame for analysis
            df = self._create_analysis_dataframe(prices, volumes, timestamps, ohlcv)
            
            # Use optimized analysis
            result = self.optimized_analyzer.analyze_symbol_optimized(symbol, timeframe, df)
            
            # Process results and emit alerts
            self._process_analysis_result(symbol, timeframe, result)
            
        except Exception as e:
            logger.error(f"Error in optimized processing {symbol} {timeframe}: {e}")
    
    def _process_analysis_result(self, symbol: str, timeframe: TimeFrame, result: Dict[str, Any]):
        """Process analysis result and emit appropriate alerts."""
        try:
            # Process liquidity pools
            if 'buy_pools' in result and 'sell_pools' in result:
                self._process_pool_results(symbol, timeframe, result['buy_pools'], result['sell_pools'])
            
            # Process order blocks
            if 'order_blocks' in result:
                self._process_order_block_results(symbol, timeframe, result['order_blocks'])
            
            # Process FVGs
            if 'fvgs' in result:
                self._process_fvg_results(symbol, timeframe, result['fvgs'])
            
            # Process grabs
            if 'grabs' in result:
                self._process_grab_results(symbol, timeframe, result['grabs'])
            
        except Exception as e:
            logger.error(f"Error processing analysis result: {e}")
    
    def _process_pool_results(self, symbol: str, timeframe: TimeFrame, 
                            buy_pools: List[Dict], sell_pools: List[Dict]):
        """Process liquidity pool results."""
        # Implementation would convert serialized pools back to objects
        # and check for new formations to emit alerts
        pass
    
    def _process_order_block_results(self, symbol: str, timeframe: TimeFrame, 
                                   order_blocks: List[Dict]):
        """Process order block results."""
        # Implementation would handle order block alerts
        pass
    
    def _process_fvg_results(self, symbol: str, timeframe: TimeFrame, fvgs: List[Dict]):
        """Process FVG results."""
        # Implementation would handle FVG alerts
        pass
    
    def _process_grab_results(self, symbol: str, timeframe: TimeFrame, grabs: List[Dict]):
        """Process liquidity grab results."""
        # Implementation would handle grab alerts
        pass
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        base_stats = self.get_performance_stats()
        opt_stats = self.optimized_analyzer.get_performance_stats()
        
        return {
            'streaming_stats': base_stats,
            'optimization_stats': opt_stats,
            'combined_performance': {
                'total_processing_time': base_stats.get('avg_update_time', 0),
                'optimization_efficiency': opt_stats.get('cache_hits', 0) / max(1, opt_stats.get('total_analyses', 1)),
                'memory_efficiency': opt_stats.get('memory_optimizations', 0)
            }
        }


# Factory functions for easy creation
def create_optimized_analyzer(enable_caching: bool = True, enable_parallel: bool = True) -> OptimizedLiquidityAnalyzer:
    """Create an optimized liquidity analyzer with specified features."""
    config = PerformanceConfig(
        enable_caching=enable_caching,
        enable_parallel=enable_parallel,
        enable_memory_optimization=True,
        max_workers=4,
        cache_size=1000
    )
    
    return OptimizedLiquidityAnalyzer(config)


def create_high_performance_streaming_analyzer(symbols: List[str], 
                                             timeframes: List[TimeFrame]) -> HighPerformanceRealTimeAnalyzer:
    """Create a high-performance streaming analyzer."""
    streaming_config = StreamingConfig(
        mode=StreamingMode.CANDLE_CLOSE,
        update_interval=0.5,
        buffer_size=2000,
        enable_alerts=True,
        memory_optimization=True
    )
    
    perf_config = PerformanceConfig(
        enable_caching=True,
        enable_parallel=True,
        enable_memory_optimization=True,
        max_workers=6,
        cache_size=2000
    )
    
    analyzer = HighPerformanceRealTimeAnalyzer(streaming_config, perf_config)
    analyzer.start_streaming(symbols, timeframes)
    
    return analyzer


if __name__ == "__main__":
    # Performance testing
    
    # Create test data
    np.random.seed(42)
    n = 1000
    dates = pd.date_range('2023-01-01', periods=n, freq='15min')
    
    close = np.cumsum(np.random.normal(0, 1, n)) + 100
    high = close + np.random.uniform(0, 2, n)
    low = close - np.random.uniform(0, 2, n)
    open_price = low + np.random.uniform(0, high - low, n)
    volume = np.random.uniform(100, 1000, n)
    
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    # Test optimized analyzer
    analyzer = create_optimized_analyzer()
    
    # Single symbol analysis
    start_time = time.time()
    result = analyzer.analyze_symbol_optimized('EURUSD', TimeFrame.M15, df)
    single_time = time.time() - start_time
    
    logger.info(f"Single analysis time: {single_time:.4f}s")
    logger.info(f"Cache stats: {analyzer.cache.get_stats()}")
    
    # Multiple symbol analysis
    symbol_data = {
        'EURUSD': {TimeFrame.M15: df, TimeFrame.H1: df.iloc[:4]},
        'GBPUSD': {TimeFrame.M15: df, TimeFrame.H1: df.iloc[:4]},
        'USDJPY': {TimeFrame.M15: df, TimeFrame.H1: df.iloc[:4]}
    }
    
    start_time = time.time()
    results = analyzer.analyze_multiple_symbols(symbol_data)
    multi_time = time.time() - start_time
    
    logger.info(f"Multiple analysis time: {multi_time:.4f}s")
    logger.info(f"Performance stats: {analyzer.get_performance_stats()}")
    
    analyzer.shutdown()
