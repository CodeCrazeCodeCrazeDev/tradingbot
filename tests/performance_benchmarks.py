"""
Performance Benchmarks for Trading Bot
Tests performance of critical components and identifies bottlenecks
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Callable
import statistics
import psutil
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bot.utils.debug_tools import performance_profile, get_system_stats


class PerformanceBenchmark:
    """Performance benchmark runner"""
    
    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results = {}
        
    def benchmark(self, name: str, func: Callable, *args, **kwargs):
        """Run benchmark for a function"""
        print(f"\nBenchmarking: {name}")
        print(f"Iterations: {self.iterations}")
        
        durations = []
        memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        for i in range(self.iterations):
            start_time = time.perf_counter()
            func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            durations.append(duration)
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{self.iterations}")
        
        memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        memory_delta = memory_after - memory_before
        
        self.results[name] = {
            'iterations': self.iterations,
            'total_time': sum(durations),
            'avg_time': statistics.mean(durations),
            'median_time': statistics.median(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0,
            'memory_delta_mb': memory_delta,
            'throughput': self.iterations / sum(durations)
        }
        
        self._print_result(name)
        
    def _print_result(self, name: str):
        """Print benchmark result"""
        result = self.results[name]
        
        print(f"\nResults for {name}:")
        print(f"  Average: {result['avg_time']*1000:.3f}ms")
        print(f"  Median: {result['median_time']*1000:.3f}ms")
        print(f"  Min: {result['min_time']*1000:.3f}ms")
        print(f"  Max: {result['max_time']*1000:.3f}ms")
        print(f"  Std Dev: {result['std_dev']*1000:.3f}ms")
        print(f"  Throughput: {result['throughput']:.1f} ops/sec")
        print(f"  Memory Delta: {result['memory_delta_mb']:+.2f}MB")
        
    def print_summary(self):
        """Print summary of all benchmarks"""
        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*70)
        
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )
        
        print(f"\n{'Benchmark':<40} {'Avg Time':<15} {'Throughput':<15}")
        print("-"*70)
        
        for name, result in sorted_results:
            print(f"{name:<40} {result['avg_time']*1000:>10.3f}ms {result['throughput']:>10.1f} ops/s")
        
        print("\n" + "="*70)


def benchmark_data_processing():
    """Benchmark data processing operations"""
    import numpy as np
    import pandas as pd
    
    benchmark = PerformanceBenchmark(iterations=100)
    
    # Test 1: DataFrame creation
    def create_dataframe():
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1min'),
            'open': np.random.randn(1000) * 100 + 1000,
            'high': np.random.randn(1000) * 100 + 1000,
            'low': np.random.randn(1000) * 100 + 1000,
            'close': np.random.randn(1000) * 100 + 1000,
            'volume': np.random.randint(1000, 10000, 1000)
        }
        df = pd.DataFrame(data)
        return df
    
    benchmark.benchmark("DataFrame Creation (1000 rows)", create_dataframe)
    
    # Test 2: Technical indicator calculation
    df = create_dataframe()
    
    def calculate_sma():
        return df['close'].rolling(window=20).mean()
    
    benchmark.benchmark("SMA Calculation (20 period)", calculate_sma)
    
    # Test 3: Multiple indicators
    def calculate_multiple_indicators():
        sma = df['close'].rolling(window=20).mean()
        ema = df['close'].ewm(span=20).mean()
        std = df['close'].rolling(window=20).std()
        return sma, ema, std
    
    benchmark.benchmark("Multiple Indicators (SMA, EMA, STD)", calculate_multiple_indicators)
    
    benchmark.print_summary()
    return benchmark.results


def benchmark_risk_calculations():
    """Benchmark risk management calculations"""
    import numpy as np
    
    benchmark = PerformanceBenchmark(iterations=1000)
    
    # Test 1: Position size calculation
    def calculate_position_size():
        account_balance = 10000
        risk_per_trade = 0.02
        entry_price = 1.1000
        stop_loss = 1.0950
        
        risk_amount = account_balance * risk_per_trade
        pip_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / pip_risk
        return position_size
    
    benchmark.benchmark("Position Size Calculation", calculate_position_size)
    
    # Test 2: Portfolio risk calculation
    def calculate_portfolio_risk():
        positions = np.random.randn(10) * 1000
        weights = np.random.rand(10)
        weights = weights / weights.sum()
        correlation_matrix = np.random.rand(10, 10)
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
        np.fill_diagonal(correlation_matrix, 1)
        
        portfolio_variance = weights @ correlation_matrix @ weights
        portfolio_risk = np.sqrt(portfolio_variance)
        return portfolio_risk
    
    benchmark.benchmark("Portfolio Risk Calculation", calculate_portfolio_risk)
    
    # Test 3: VaR calculation
    def calculate_var():
        returns = np.random.randn(1000) * 0.02
        confidence_level = 0.95
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return var
    
    benchmark.benchmark("VaR Calculation (1000 samples)", calculate_var)
    
    benchmark.print_summary()
    return benchmark.results


def benchmark_ml_inference():
    """Benchmark ML model inference"""
    import numpy as np
    
    benchmark = PerformanceBenchmark(iterations=100)
    
    # Test 1: Simple neural network forward pass (simulated)
    def nn_forward_pass():
        input_data = np.random.randn(1, 100)
        weights1 = np.random.randn(100, 50)
        weights2 = np.random.randn(50, 10)
        weights3 = np.random.randn(10, 1)
        
        hidden1 = np.maximum(0, input_data @ weights1)  # ReLU
        hidden2 = np.maximum(0, hidden1 @ weights2)
        output = hidden2 @ weights3
        return output
    
    benchmark.benchmark("Neural Network Forward Pass", nn_forward_pass)
    
    # Test 2: Feature engineering
    def feature_engineering():
        data = np.random.randn(1000, 10)
        
        # Calculate various features
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        min_val = np.min(data, axis=0)
        max_val = np.max(data, axis=0)
        
        # Normalize
        normalized = (data - mean) / (std + 1e-8)
        
        return normalized
    
    benchmark.benchmark("Feature Engineering (1000 samples)", feature_engineering)
    
    benchmark.print_summary()
    return benchmark.results


def benchmark_database_operations():
    """Benchmark database operations"""
    import sqlite3
    from pathlib import Path
    
    benchmark = PerformanceBenchmark(iterations=10)
    
    # Create temporary database
    db_path = Path('temp_benchmark.db')
    
    # Test 1: Insert operations
    def insert_operations():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                price REAL,
                volume INTEGER
            )
        ''')
        
        for i in range(100):
            cursor.execute(
                'INSERT INTO trades (timestamp, symbol, price, volume) VALUES (?, ?, ?, ?)',
                (f'2024-01-01 00:{i:02d}:00', 'EURUSD', 1.1000 + i * 0.0001, 1000)
            )
        
        conn.commit()
        conn.close()
    
    benchmark.benchmark("Database Insert (100 records)", insert_operations)
    
    # Test 2: Query operations
    def query_operations():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trades WHERE price > 1.1050')
        results = cursor.fetchall()
        
        conn.close()
        return results
    
    benchmark.benchmark("Database Query", query_operations)
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    
    benchmark.print_summary()
    return benchmark.results


def run_all_benchmarks():
    """Run all performance benchmarks"""
    print("\n" + "="*70)
    print("RUNNING ALL PERFORMANCE BENCHMARKS")
    print("="*70)
    
    print("\n[1/4] Data Processing Benchmarks")
    print("-"*70)
    data_results = benchmark_data_processing()
    
    print("\n[2/4] Risk Calculation Benchmarks")
    print("-"*70)
    risk_results = benchmark_risk_calculations()
    
    print("\n[3/4] ML Inference Benchmarks")
    print("-"*70)
    ml_results = benchmark_ml_inference()
    
    print("\n[4/4] Database Operation Benchmarks")
    print("-"*70)
    db_results = benchmark_database_operations()
    
    # Overall summary
    print("\n" + "="*70)
    print("OVERALL PERFORMANCE SUMMARY")
    print("="*70)
    
    all_results = {
        **data_results,
        **risk_results,
        **ml_results,
        **db_results
    }
    
    # Find slowest operations
    slowest = sorted(all_results.items(), key=lambda x: x[1]['avg_time'], reverse=True)[:5]
    
    print("\nTop 5 Slowest Operations:")
    for i, (name, result) in enumerate(slowest, 1):
        print(f"{i}. {name}: {result['avg_time']*1000:.3f}ms")
    
    # Find fastest operations
    fastest = sorted(all_results.items(), key=lambda x: x[1]['avg_time'])[:5]
    
    print("\nTop 5 Fastest Operations:")
    for i, (name, result) in enumerate(fastest, 1):
        print(f"{i}. {name}: {result['avg_time']*1000:.3f}ms")
    
    # System stats
    print("\nSystem Statistics:")
    stats = get_system_stats()
    print(f"  CPU Usage: {stats['cpu']['percent']}%")
    print(f"  Memory Usage: {stats['memory']['percent']}%")
    print(f"  Process Memory: {stats['process']['memory_mb']:.1f}MB")
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)


if __name__ == '__main__':
    run_all_benchmarks()
