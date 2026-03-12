import logging
logger = logging.getLogger(__name__)
"""
Comprehensive Performance Benchmarking Suite for Liquidity Analysis

This module provides extensive benchmarking and performance testing capabilities
for all liquidity analysis components.
"""

import time
import threading
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import concurrent.futures

import numpy as np
import pandas as pd
from loguru import logger

from .liquidity import LiquidityAnalyzer
from .realtime_liquidity import RealTimeLiquidityAnalyzer, StreamingConfig
from .liquidity_performance import OptimizedLiquidityAnalyzer
from .order_block_tracker import OrderBlockTracker
from .liquidity_heatmap import LiquidityHeatmapVisualizer
from .liquidity_ml_predictor import LiquidityMLPredictor
from .market_structure import TimeFrame


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    test_name: str
    execution_time: float
    memory_usage: float
    throughput: float
    accuracy: Optional[float] = None
    error_rate: float = 0.0
    metadata: Dict[str, Any] = None


class LiquidityBenchmarkSuite:
    """
    Comprehensive benchmarking suite for liquidity analysis components.
    
    Tests performance, accuracy, memory usage, and scalability of:
    - Core liquidity analysis
    - Real-time streaming
    - Performance optimizations
    - Order block tracking
    - Visualization systems
    - ML predictions
    """
    
    def __init__(self):
        """Initialize the benchmark suite."""
        self.results: List[BenchmarkResult] = []
        self.test_data = self._generate_test_data()
        
    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmark tests."""
        logger.info("Starting comprehensive liquidity analysis benchmarks")
        
        benchmarks = {
            'core_analysis': self.benchmark_core_analysis,
            'streaming_performance': self.benchmark_streaming,
            'optimization_efficiency': self.benchmark_optimization,
            'tracking_accuracy': self.benchmark_tracking,
            'visualization_speed': self.benchmark_visualization,
            'ml_prediction': self.benchmark_ml_prediction,
            'memory_usage': self.benchmark_memory,
            'scalability': self.benchmark_scalability
        }
        
        results = {}
        for name, benchmark_func in benchmarks.items():
            try:
                logger.info(f"Running {name} benchmark...")
                result = benchmark_func()
                results[name] = result
                self.results.append(result)
                logger.info(f"Completed {name}: {result.execution_time:.3f}s")
            except Exception as e:
                logger.error(f"Benchmark {name} failed: {e}")
        
        return results
    
    def benchmark_core_analysis(self) -> BenchmarkResult:
        """Benchmark core liquidity analysis performance."""
        analyzer = LiquidityAnalyzer()
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Test with multiple datasets
        total_operations = 0
        errors = 0
        
        for df in self.test_data['ohlcv_datasets']:
            try:
                # Test all core functions
                buy_pools, sell_pools = analyzer.find_equal_highs_lows(df)
                order_blocks = analyzer.detect_order_blocks(df)
                fvgs = analyzer.detect_fair_value_gaps(df)
                
                if 'volume' in df.columns:
                    volume_profile = analyzer.create_volume_profile(df)
                
                total_operations += 4
            except Exception as e:
                errors += 1
                logger.error(f"Core analysis error: {e}")
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        throughput = total_operations / execution_time if execution_time > 0 else 0
        error_rate = errors / total_operations if total_operations > 0 else 0
        
        return BenchmarkResult(
            test_name="Core Analysis",
            execution_time=execution_time,
            memory_usage=memory_usage,
            throughput=throughput,
            error_rate=error_rate,
            metadata={'operations': total_operations, 'datasets': len(self.test_data['ohlcv_datasets'])}
        )
    
    def benchmark_streaming(self) -> BenchmarkResult:
        """Benchmark real-time streaming performance."""
        config = StreamingConfig(
            update_interval=0.1,
            buffer_size=1000,
            enable_alerts=True
        )
        
        analyzer = RealTimeLiquidityAnalyzer(config)
        analyzer.start_streaming(['EURUSD'], [TimeFrame.M15])
        
        start_time = time.time()
        updates_sent = 0
        errors = 0
        
        # Send rapid updates
        for i in range(1000):
            try:
                price = 1.1000 + np.random.normal(0, 0.0001)
                volume = np.random.uniform(100, 1000)
                analyzer.update_tick('EURUSD', TimeFrame.M15, price, volume)
                updates_sent += 1
            except Exception as e:
                errors += 1
        
        end_time = time.time()
        analyzer.stop_streaming()
        
        execution_time = end_time - start_time
        throughput = updates_sent / execution_time if execution_time > 0 else 0
        error_rate = errors / updates_sent if updates_sent > 0 else 0
        
        return BenchmarkResult(
            test_name="Streaming Performance",
            execution_time=execution_time,
            memory_usage=0,  # Would need process monitoring
            throughput=throughput,
            error_rate=error_rate,
            metadata={'updates_sent': updates_sent}
        )
    
    def benchmark_optimization(self) -> BenchmarkResult:
        """Benchmark performance optimization efficiency."""
        optimizer = OptimizedLiquidityAnalyzer()
        
        # Test data
        symbol_data = {
            'EURUSD': {TimeFrame.M15: self.test_data['ohlcv_datasets'][0]},
            'GBPUSD': {TimeFrame.M15: self.test_data['ohlcv_datasets'][1]},
            'USDJPY': {TimeFrame.M15: self.test_data['ohlcv_datasets'][2]}
        }
        
        start_time = time.time()
        
        # Test parallel processing
        results = optimizer.analyze_multiple_symbols(symbol_data)
        
        end_time = time.time()
        
        execution_time = end_time - start_time
        cache_stats = optimizer.cache.get_stats() if optimizer.cache else {}
        
        return BenchmarkResult(
            test_name="Optimization Efficiency",
            execution_time=execution_time,
            memory_usage=0,
            throughput=len(symbol_data) / execution_time,
            metadata={
                'cache_hit_rate': cache_stats.get('hit_rate_percent', 0),
                'symbols_processed': len(symbol_data)
            }
        )
    
    def benchmark_tracking(self) -> BenchmarkResult:
        """Benchmark order block tracking accuracy."""
        tracker = OrderBlockTracker()
        
        start_time = time.time()
        events_processed = 0
        
        # Simulate order block lifecycle
        from .liquidity import OrderBlock, OrderBlockType
        
        ob = OrderBlock(
            type=OrderBlockType.BULLISH,
            start_idx=100,
            end_idx=100,
            high=1.1050,
            low=1.1030,
            open=1.1035,
            close=1.1045,
            strength=1.5,
            timeframe=TimeFrame.M15
        )
        
        tracker.register_order_block('EURUSD', TimeFrame.M15, ob)
        
        # Simulate price updates
        prices = np.linspace(1.1020, 1.1060, 100)
        for price in prices:
            tracker.update_price('EURUSD', TimeFrame.M15, price, volume=500)
            events_processed += 1
        
        end_time = time.time()
        
        stats = tracker.get_block_statistics('EURUSD', TimeFrame.M15)
        
        return BenchmarkResult(
            test_name="Order Block Tracking",
            execution_time=end_time - start_time,
            memory_usage=0,
            throughput=events_processed / (end_time - start_time),
            metadata=stats
        )
    
    def benchmark_visualization(self) -> BenchmarkResult:
        """Benchmark visualization rendering performance."""
        visualizer = LiquidityHeatmapVisualizer()
        
        # Sample liquidity data
        sample_data = {
            'buy_pools': [{'price': 1.1050, 'strength': 1.5}] * 10,
            'sell_pools': [{'price': 1.1040, 'strength': 1.3}] * 10,
            'order_blocks': [{'high': 1.1055, 'low': 1.1050, 'strength': 1.4, 'type': 'bullish'}] * 5
        }
        
        visualizer.update_liquidity_data('EURUSD', TimeFrame.M15, sample_data)
        
        start_time = time.time()
        
        # Test different visualization types
        fig1 = visualizer.create_liquidity_pools_heatmap('EURUSD', TimeFrame.M15)
        fig2 = visualizer.create_order_blocks_heatmap('EURUSD', TimeFrame.M15)
        fig3 = visualizer.create_combined_heatmap('EURUSD', TimeFrame.M15)
        
        end_time = time.time()
        
        perf_stats = visualizer.get_performance_stats()
        
        return BenchmarkResult(
            test_name="Visualization Performance",
            execution_time=end_time - start_time,
            memory_usage=0,
            throughput=3 / (end_time - start_time),  # 3 visualizations
            metadata=perf_stats
        )
    
    def benchmark_ml_prediction(self) -> BenchmarkResult:
        """Benchmark ML prediction performance."""
        predictor = LiquidityMLPredictor(enable_training=False)
        
        start_time = time.time()
        predictions_made = 0
        
        # Test predictions with sample data
        market_data = self.test_data['ohlcv_datasets'][0]
        context_data = {'market_regime': 1, 'session_time': 1}
        
        for _ in range(100):
            pred = predictor.predict_pool_formation(market_data, context_data)
            predictions_made += 1
        
        end_time = time.time()
        
        return BenchmarkResult(
            test_name="ML Prediction",
            execution_time=end_time - start_time,
            memory_usage=0,
            throughput=predictions_made / (end_time - start_time),
            metadata={'predictions_made': predictions_made}
        )
    
    def benchmark_memory(self) -> BenchmarkResult:
        """Benchmark memory usage across components."""
        from ..performance.memory_optimization import MemoryOptimizer, DataStructureType
        
        optimizer = MemoryOptimizer()
        
        start_time = time.time()
        total_reduction = 0
        optimizations = 0
        
        for df in self.test_data['ohlcv_datasets']:
            optimized_df, result = optimizer.optimize_dataframe(df, DataStructureType.OHLCV)
            total_reduction += result.reduction_percent
            optimizations += 1
        
        end_time = time.time()
        
        avg_reduction = total_reduction / optimizations if optimizations > 0 else 0
        
        return BenchmarkResult(
            test_name="Memory Optimization",
            execution_time=end_time - start_time,
            memory_usage=avg_reduction,  # Using reduction as memory metric
            throughput=optimizations / (end_time - start_time),
            metadata={'avg_memory_reduction': avg_reduction}
        )
    
    def benchmark_scalability(self) -> BenchmarkResult:
        """Benchmark system scalability with increasing load."""
        analyzer = LiquidityAnalyzer()
        
        # Test with increasing dataset sizes
        execution_times = []
        dataset_sizes = [100, 500, 1000, 2000, 5000]
        
        for size in dataset_sizes:
            # Generate dataset of specific size
            df = self._generate_ohlcv_data(size)
            
            start_time = time.time()
            
            # Run analysis
            analyzer.find_equal_highs_lows(df)
            analyzer.detect_order_blocks(df)
            analyzer.detect_fair_value_gaps(df)
            
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculate scalability metrics
        avg_time_per_size = sum(execution_times) / len(execution_times)
        
        return BenchmarkResult(
            test_name="Scalability Test",
            execution_time=avg_time_per_size,
            memory_usage=0,
            throughput=sum(dataset_sizes) / sum(execution_times),
            metadata={
                'dataset_sizes': dataset_sizes,
                'execution_times': execution_times,
                'scalability_factor': execution_times[-1] / execution_times[0]
            }
        )
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test datasets for benchmarking."""
        datasets = []
        
        # Generate multiple OHLCV datasets
        for i in range(5):
            df = self._generate_ohlcv_data(1000 + i * 500)
            datasets.append(df)
        
        return {
            'ohlcv_datasets': datasets
        }
    
    def _generate_ohlcv_data(self, size: int) -> pd.DataFrame:
        """Generate synthetic OHLCV data."""
        np.random.seed(42)
        
        dates = pd.date_range('2023-01-01', periods=size, freq='15min')
        
        # Create realistic price movement
        returns = np.random.normal(0, 0.0001, size)
        prices = 1.1000 * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        close = prices
        high = close + np.random.uniform(0, 0.0005, size)
        low = close - np.random.uniform(0, 0.0005, size)
        open_price = np.roll(close, 1)
        open_price[0] = close[0]
        volume = np.random.uniform(100, 1000, size)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (placeholder)."""
        # In real implementation, would use psutil or similar
        return 0.0
    
    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return "No benchmark results available."
        
        report = "# Liquidity Analysis Performance Benchmark Report\n\n"
        
        # Summary table
        report += "## Summary\n\n"
        report += "| Test | Execution Time (s) | Throughput | Error Rate |\n"
        report += "|------|-------------------|------------|------------|\n"
        
        for result in self.results:
            report += f"| {result.test_name} | {result.execution_time:.3f} | {result.throughput:.2f} | {result.error_rate:.2%} |\n"
        
        # Detailed results
        report += "\n## Detailed Results\n\n"
        
        for result in self.results:
            report += f"### {result.test_name}\n"
            report += f"- **Execution Time:** {result.execution_time:.3f} seconds\n"
            report += f"- **Throughput:** {result.throughput:.2f} operations/second\n"
            report += f"- **Error Rate:** {result.error_rate:.2%}\n"
            
            if result.metadata:
                report += "- **Additional Metrics:**\n"
                for key, value in result.metadata.items():
                    report += f"  - {key}: {value}\n"
            
            report += "\n"
        
        # Performance recommendations
        report += "## Performance Recommendations\n\n"
        
        # Find slowest components
        slowest = max(self.results, key=lambda r: r.execution_time)
        fastest = min(self.results, key=lambda r: r.execution_time)
        
        report += f"- **Slowest Component:** {slowest.test_name} ({slowest.execution_time:.3f}s)\n"
        report += f"- **Fastest Component:** {fastest.test_name} ({fastest.execution_time:.3f}s)\n"
        
        # Error rate analysis
        high_error_tests = [r for r in self.results if r.error_rate > 0.01]
        if high_error_tests:
            report += f"- **High Error Rate Components:** {', '.join(r.test_name for r in high_error_tests)}\n"
        
        return report


def run_comprehensive_benchmark() -> str:
    """Run comprehensive benchmark and return report."""
    suite = LiquidityBenchmarkSuite()
    results = suite.run_all_benchmarks()
    return suite.generate_report()


if __name__ == "__main__":
    # Run benchmarks
    report = run_comprehensive_benchmark()
    print(report)
    
    # Save report to file
    with open('liquidity_benchmark_report.md', 'w') as f:
        f.write(report)
    
    logger.info("Benchmark report saved to liquidity_benchmark_report.md")
