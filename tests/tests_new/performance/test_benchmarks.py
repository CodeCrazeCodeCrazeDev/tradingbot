"""
Performance Benchmarks
======================
Performance tests and benchmarks for critical system components.
"""

import pytest
import time
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import statistics


def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start
    return wrapper


@pytest.mark.performance
class TestRiskManagerPerformance:
    """Performance benchmarks for risk manager."""
    
    def test_position_sizing_speed(self, risk_manager):
        """Benchmark position sizing calculation speed."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        iterations = 1000
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            risk_manager.calculate_position_size(
                symbol='EURUSD',
                stop_loss_pips=50,
                direction=TradeDirection.LONG,
                confidence=0.8
            )
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000  # Convert to ms
        p95_time = np.percentile(times, 95) * 1000
        
        print(f"\nPosition Sizing Performance:")
        print(f"  Average: {avg_time:.3f} ms")
        print(f"  P95: {p95_time:.3f} ms")
        print(f"  Throughput: {1000/avg_time:.0f} calculations/sec")
        
        # Performance assertion: should be under 10ms average
        assert avg_time < 10, f"Position sizing too slow: {avg_time:.3f}ms"
    
    def test_risk_validation_speed(self, risk_manager):
        """Benchmark risk validation speed."""
        iterations = 1000
        times = []
        
        trade = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot_size': 0.1,
            'entry_price': 1.1000,
            'stop_loss': 1.0950
        }
        
        for _ in range(iterations):
            start = time.perf_counter()
            if hasattr(risk_manager, 'validate_trade'):
                risk_manager.validate_trade(trade)
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000
        
        print(f"\nRisk Validation Performance:")
        print(f"  Average: {avg_time:.3f} ms")
        
        # Should be very fast
        assert avg_time < 5, f"Risk validation too slow: {avg_time:.3f}ms"


@pytest.mark.performance
class TestExecutionEnginePerformance:
    """Performance benchmarks for execution engine."""
    
    def test_plan_creation_speed(self, execution_engine):
        """Benchmark execution plan creation speed."""
        from trading_bot.execution.advanced_algorithms import ExecutionAlgorithm, OrderSide
        
        iterations = 500
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            execution_engine.create_plan(
                algorithm=ExecutionAlgorithm.TWAP,
                symbol='EURUSD',
                side=OrderSide.BUY,
                quantity=1000,
                duration_seconds=60
            )
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000
        p95_time = np.percentile(times, 95) * 1000
        
        print(f"\nExecution Plan Creation Performance:")
        print(f"  Average: {avg_time:.3f} ms")
        print(f"  P95: {p95_time:.3f} ms")
        
        # Should be under 20ms
        assert avg_time < 20, f"Plan creation too slow: {avg_time:.3f}ms"


@pytest.mark.performance
class TestDataProcessingPerformance:
    """Performance benchmarks for data processing."""
    
    def test_ohlcv_processing_speed(self, sample_ohlcv_data):
        """Benchmark OHLCV data processing speed."""
        iterations = 100
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            
            # Simulate typical data processing
            df = sample_ohlcv_data.copy()
            df['returns'] = df['close'].pct_change()
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['volatility'] = df['returns'].rolling(20).std()
            df['rsi'] = 100 - (100 / (1 + df['returns'].rolling(14).apply(
                lambda x: (x[x > 0].sum() / abs(x[x < 0].sum())) if x[x < 0].sum() != 0 else 1
            )))
            
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000
        
        print(f"\nOHLCV Processing Performance (1000 bars):")
        print(f"  Average: {avg_time:.3f} ms")
        print(f"  Bars/sec: {1000 * 1000 / avg_time:.0f}")
        
        # Should process 1000 bars in under 100ms
        assert avg_time < 100, f"OHLCV processing too slow: {avg_time:.3f}ms"
    
    def test_tick_data_processing_speed(self, sample_tick_data):
        """Benchmark tick data processing speed."""
        iterations = 50
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            
            df = sample_tick_data.copy()
            df['mid'] = (df['bid'] + df['ask']) / 2
            df['spread'] = df['ask'] - df['bid']
            df['imbalance'] = (df['bid_size'] - df['ask_size']) / (df['bid_size'] + df['ask_size'])
            
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000
        
        print(f"\nTick Processing Performance (10000 ticks):")
        print(f"  Average: {avg_time:.3f} ms")
        print(f"  Ticks/sec: {10000 * 1000 / avg_time:.0f}")
        
        # Should process 10000 ticks in under 50ms
        assert avg_time < 50, f"Tick processing too slow: {avg_time:.3f}ms"


@pytest.mark.performance
class TestSignalGenerationPerformance:
    """Performance benchmarks for signal generation."""
    
    def test_signal_system_initialization_speed(self):
        """Benchmark signal system initialization speed."""
        from trading_bot.signals import CompleteSignalSystem
        
        iterations = 10
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            system = CompleteSignalSystem()
            times.append(time.perf_counter() - start)
        
        avg_time = statistics.mean(times) * 1000
        
        print(f"\nSignal System Init Performance:")
        print(f"  Average: {avg_time:.3f} ms")
        
        # Should initialize in under 500ms
        assert avg_time < 500, f"Signal system init too slow: {avg_time:.3f}ms"


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage benchmarks."""
    
    def test_risk_manager_memory(self, risk_manager):
        """Check risk manager memory footprint."""
        import sys
        
        size = sys.getsizeof(risk_manager)
        
        print(f"\nRisk Manager Memory:")
        print(f"  Base size: {size} bytes")
        
        # Should be reasonable
        assert size < 10_000_000, f"Risk manager too large: {size} bytes"
    
    def test_large_dataframe_memory(self):
        """Check memory usage with large DataFrames."""
        import sys
        
        # Create large DataFrame (100k rows)
        np.random.seed(42)
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2020-01-01', periods=100000, freq='min'),
            'open': np.random.randn(100000) * 100 + 1000,
            'high': np.random.randn(100000) * 100 + 1000,
            'low': np.random.randn(100000) * 100 + 1000,
            'close': np.random.randn(100000) * 100 + 1000,
            'volume': np.random.randint(1000, 100000, 100000)
        })
        
        memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"\nLarge DataFrame Memory (100k rows):")
        print(f"  Size: {memory_mb:.2f} MB")
        
        # Should be under 50MB for 100k rows
        assert memory_mb < 50, f"DataFrame too large: {memory_mb:.2f} MB"


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Concurrency and async performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_concurrent_position_calculations(self, risk_manager):
        """Benchmark concurrent position calculations."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        async def calculate_position():
            return risk_manager.calculate_position_size(
                symbol='EURUSD',
                stop_loss_pips=50,
                direction=TradeDirection.LONG,
                confidence=0.8
            )
        
        # Run 100 concurrent calculations
        start = time.perf_counter()
        tasks = [calculate_position() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        
        print(f"\nConcurrent Position Calculations (100):")
        print(f"  Total time: {elapsed*1000:.3f} ms")
        print(f"  Per calculation: {elapsed*10:.3f} ms")
        
        assert len(results) == 100
        assert elapsed < 5, f"Concurrent calculations too slow: {elapsed:.3f}s"
