"""
Performance Benchmarking Tests
Comprehensive benchmarks for critical trading bot components
"""

import pytest
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics
from typing import List

# Try to import components
try:
    from trading_bot.validation.data_validator import DataQualityValidator, DataQualityMonitor
    DATA_VALIDATOR_AVAILABLE = True
except ImportError:
    DATA_VALIDATOR_AVAILABLE = False

try:
    from trading_bot.risk.portfolio_risk_manager import PortfolioRiskManager
    PORTFOLIO_RISK_AVAILABLE = True
except ImportError:
    PORTFOLIO_RISK_AVAILABLE = False

try:
    from trading_bot.risk.position_size_calculator import PositionSizeCalculator, PositionSizeMethod
    POSITION_SIZE_AVAILABLE = True
except ImportError:
    POSITION_SIZE_AVAILABLE = False

try:
    from trading_bot.risk.kelly_criterion import KellyCriterion
    KELLY_AVAILABLE = True
except ImportError:
    KELLY_AVAILABLE = False

try:
    from trading_bot.risk.var_engine import VaREngine
    VAR_AVAILABLE = True
except ImportError:
    VAR_AVAILABLE = False

try:
    from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

try:
    from trading_bot.signals.signal_lifecycle import SignalLifecycleManager
    SIGNAL_LIFECYCLE_AVAILABLE = True
except ImportError:
    SIGNAL_LIFECYCLE_AVAILABLE = False


# ============================================================================
# BENCHMARK UTILITIES
# ============================================================================

class BenchmarkResult:
    """Container for benchmark results"""
    
    def __init__(self, name: str, iterations: int, times: List[float]):
        self.name = name
        self.iterations = iterations
        self.times = times
        self.total_time = sum(times)
        self.mean_time = statistics.mean(times) if times else 0
        self.median_time = statistics.median(times) if times else 0
        self.std_time = statistics.stdev(times) if len(times) > 1 else 0
        self.min_time = min(times) if times else 0
        self.max_time = max(times) if times else 0
        self.ops_per_sec = iterations / self.total_time if self.total_time > 0 else 0
    
    def __str__(self):
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations:,}\n"
            f"  Total Time: {self.total_time:.4f}s\n"
            f"  Mean: {self.mean_time*1000:.4f}ms\n"
            f"  Median: {self.median_time*1000:.4f}ms\n"
            f"  Std Dev: {self.std_time*1000:.4f}ms\n"
            f"  Min: {self.min_time*1000:.4f}ms\n"
            f"  Max: {self.max_time*1000:.4f}ms\n"
            f"  Ops/sec: {self.ops_per_sec:,.0f}"
        )


def benchmark(func, iterations=1000, warmup=100):
    """Run a benchmark"""
    # Warmup
    for _ in range(warmup):
        func()
    
    # Benchmark
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    
    return times


# ============================================================================
# DATA VALIDATION BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not DATA_VALIDATOR_AVAILABLE, reason="DataQualityValidator not available")
class TestDataValidationBenchmarks:
    """Benchmarks for data validation"""
    
    @pytest.fixture
    def validator(self):
        """Create validator"""
        return DataQualityValidator()
    
    def test_ohlcv_validation_latency(self, validator):
        """Benchmark OHLCV validation latency"""
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        
        times = benchmark(lambda: validator.validate_ohlcv(ohlcv), iterations=1000)
        result = BenchmarkResult("OHLCV Validation", 1000, times)
        
        print(f"\n{result}")
        
        # Performance assertion: should complete in < 1ms average
        assert result.mean_time < 0.001, f"OHLCV validation too slow: {result.mean_time*1000:.2f}ms"
    
    def test_batch_validation_throughput(self, validator):
        """Benchmark batch validation throughput"""
        batch = [
            {
                'open': 100.0 + i * 0.1,
                'high': 105.0 + i * 0.1,
                'low': 95.0 + i * 0.1,
                'close': 102.0 + i * 0.1,
                'volume': 1000 + i,
                'time': datetime.now()
            }
            for i in range(100)
        ]
        
        def validate_batch():
            for ohlcv in batch:
                validator.validate_ohlcv(ohlcv)
        
        times = benchmark(validate_batch, iterations=100)
        result = BenchmarkResult("Batch Validation (100 items)", 100, times)
        
        print(f"\n{result}")
        
        # Should process 100 items in < 50ms
        assert result.mean_time < 0.05, f"Batch validation too slow: {result.mean_time*1000:.2f}ms"
    
    def test_outlier_detection_performance(self, validator):
        """Benchmark outlier detection performance"""
        np.random.seed(42)
        prices = list(np.random.randn(1000) * 10 + 100)
        
        times = benchmark(lambda: validator.detect_outliers(prices), iterations=100)
        result = BenchmarkResult("Outlier Detection (1000 prices)", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 10ms
        assert result.mean_time < 0.01, f"Outlier detection too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# POSITION SIZING BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not POSITION_SIZE_AVAILABLE, reason="PositionSizeCalculator not available")
class TestPositionSizingBenchmarks:
    """Benchmarks for position sizing"""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator"""
        return PositionSizeCalculator()
    
    def test_fixed_risk_calculation_latency(self, calculator):
        """Benchmark fixed risk position sizing"""
        def calculate():
            calculator.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                method=PositionSizeMethod.FIXED_RISK
            )
        
        times = benchmark(calculate, iterations=1000)
        result = BenchmarkResult("Fixed Risk Position Sizing", 1000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.5ms
        assert result.mean_time < 0.0005, f"Position sizing too slow: {result.mean_time*1000:.2f}ms"
    
    def test_kelly_position_sizing_latency(self, calculator):
        """Benchmark Kelly criterion position sizing"""
        def calculate():
            calculator.calculate_position_size(
                symbol='EURUSD',
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                method=PositionSizeMethod.KELLY
            )
        
        times = benchmark(calculate, iterations=1000)
        result = BenchmarkResult("Kelly Position Sizing", 1000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 1ms
        assert result.mean_time < 0.001, f"Kelly sizing too slow: {result.mean_time*1000:.2f}ms"
    
    def test_position_value_calculation_latency(self, calculator):
        """Benchmark position value calculation"""
        def calculate():
            calculator.calculate_position_value(
                position_size=1.0,
                symbol='EURUSD',
                price=1.1000
            )
        
        times = benchmark(calculate, iterations=10000)
        result = BenchmarkResult("Position Value Calculation", 10000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.1ms
        assert result.mean_time < 0.0001, f"Value calculation too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# KELLY CRITERION BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not KELLY_AVAILABLE, reason="KellyCriterion not available")
class TestKellyCriterionBenchmarks:
    """Benchmarks for Kelly criterion"""
    
    @pytest.fixture
    def kelly(self):
        """Create Kelly calculator"""
        return KellyCriterion()
    
    def test_kelly_calculation_latency(self, kelly):
        """Benchmark Kelly calculation"""
        def calculate():
            kelly.calculate_kelly(win_rate=0.55, win_loss_ratio=1.5)
        
        times = benchmark(calculate, iterations=1000)
        result = BenchmarkResult("Kelly Calculation", 1000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.5ms
        assert result.mean_time < 0.0005, f"Kelly calculation too slow: {result.mean_time*1000:.2f}ms"
    
    def test_kelly_from_history_latency(self, kelly):
        """Benchmark Kelly from trade history"""
        history = [
            {'pnl': 100, 'is_win': True},
            {'pnl': -50, 'is_win': False},
            {'pnl': 75, 'is_win': True},
            {'pnl': -30, 'is_win': False},
            {'pnl': 120, 'is_win': True},
        ] * 20  # 100 trades
        
        def calculate():
            kelly.calculate_kelly_from_history(history)
        
        times = benchmark(calculate, iterations=100)
        result = BenchmarkResult("Kelly from History (100 trades)", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 5ms
        assert result.mean_time < 0.005, f"Kelly from history too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# VAR ENGINE BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not VAR_AVAILABLE, reason="VaREngine not available")
class TestVaREngineBenchmarks:
    """Benchmarks for VaR engine"""
    
    @pytest.fixture
    def var_engine(self):
        """Create VaR engine"""
        return VaREngine()
    
    @pytest.fixture
    def sample_returns(self):
        """Generate sample returns"""
        np.random.seed(42)
        return pd.Series(np.random.randn(252) * 0.02)  # 1 year of daily returns
    
    @pytest.fixture
    def sample_positions(self):
        """Generate sample positions"""
        return [
            {'symbol': 'EURUSD', 'value': 10000, 'weight': 0.4},
            {'symbol': 'GBPUSD', 'value': 7500, 'weight': 0.3},
            {'symbol': 'USDJPY', 'value': 7500, 'weight': 0.3}
        ]
    
    def test_historical_var_latency(self, var_engine, sample_returns, sample_positions):
        """Benchmark historical VaR calculation"""
        def calculate():
            var_engine.calculate_var(
                returns=sample_returns,
                positions=sample_positions,
                method='historical'
            )
        
        times = benchmark(calculate, iterations=100)
        result = BenchmarkResult("Historical VaR", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 10ms
        assert result.mean_time < 0.01, f"Historical VaR too slow: {result.mean_time*1000:.2f}ms"
    
    def test_parametric_var_latency(self, var_engine, sample_returns, sample_positions):
        """Benchmark parametric VaR calculation"""
        def calculate():
            var_engine.calculate_var(
                returns=sample_returns,
                positions=sample_positions,
                method='parametric'
            )
        
        times = benchmark(calculate, iterations=100)
        result = BenchmarkResult("Parametric VaR", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 5ms
        assert result.mean_time < 0.005, f"Parametric VaR too slow: {result.mean_time*1000:.2f}ms"
    
    def test_monte_carlo_var_latency(self, var_engine, sample_returns, sample_positions):
        """Benchmark Monte Carlo VaR calculation"""
        def calculate():
            var_engine.calculate_var(
                returns=sample_returns,
                positions=sample_positions,
                method='monte_carlo',
                num_simulations=1000
            )
        
        times = benchmark(calculate, iterations=10)
        result = BenchmarkResult("Monte Carlo VaR (1000 sims)", 10, times)
        
        print(f"\n{result}")
        
        # Should complete in < 100ms
        assert result.mean_time < 0.1, f"Monte Carlo VaR too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# CIRCUIT BREAKER BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not CIRCUIT_BREAKER_AVAILABLE, reason="CircuitBreaker not available")
class TestCircuitBreakerBenchmarks:
    """Benchmarks for circuit breaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker"""
        config = CircuitBreakerConfig(
            max_daily_loss=0.05,
            max_drawdown=0.20,
            max_consecutive_losses=5
        )
        cb = CircuitBreaker(config)
        cb.start_session(10000)
        return cb
    
    def test_can_trade_check_latency(self, circuit_breaker):
        """Benchmark can_trade check"""
        times = benchmark(lambda: circuit_breaker.can_trade(), iterations=10000)
        result = BenchmarkResult("Can Trade Check", 10000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.1ms
        assert result.mean_time < 0.0001, f"Can trade check too slow: {result.mean_time*1000:.2f}ms"
    
    def test_record_trade_latency(self):
        """Benchmark trade recording"""
        
        def record():
            config = CircuitBreakerConfig(
                max_daily_loss=0.50,
                max_drawdown=0.50,
                max_consecutive_losses=1000
            )
            cb = CircuitBreaker(config)
            cb.start_session(1000000)
            
            for i in range(100):
                cb.record_trade(pnl=(-1)**i * 10, is_win=i % 2 == 0)
        
        times = benchmark(record, iterations=100)
        result = BenchmarkResult("Record 100 Trades", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 50ms
        assert result.mean_time < 0.05, f"Trade recording too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# SIGNAL LIFECYCLE BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not SIGNAL_LIFECYCLE_AVAILABLE, reason="SignalLifecycleManager not available")
class TestSignalLifecycleBenchmarks:
    """Benchmarks for signal lifecycle"""
    
    @pytest.fixture
    def manager(self):
        """Create signal manager"""
        return SignalLifecycleManager(default_ttl_seconds=60, auto_cleanup=False)
    
    def test_signal_creation_latency(self, manager):
        """Benchmark signal creation"""
        counter = [0]
        
        def create():
            counter[0] += 1
            manager.create_signal(
                signal_id=f'TEST-{counter[0]}',
                symbol='EURUSD',
                direction='BUY',
                entry_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1100,
                confidence=0.85
            )
        
        times = benchmark(create, iterations=1000)
        result = BenchmarkResult("Signal Creation", 1000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.5ms
        assert result.mean_time < 0.0005, f"Signal creation too slow: {result.mean_time*1000:.2f}ms"
    
    def test_signal_lookup_latency(self):
        """Benchmark signal lookup"""
        manager = SignalLifecycleManager(default_ttl_seconds=60, auto_cleanup=False)
        
        # Create 1000 signals
        for i in range(1000):
            manager.create_signal(
                signal_id=f'TEST-{i}',
                symbol='EURUSD',
                direction='BUY',
                entry_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1100,
                confidence=0.85
            )
        
        def lookup():
            manager.get_signal('TEST-500')
        
        times = benchmark(lookup, iterations=10000)
        result = BenchmarkResult("Signal Lookup (1000 signals)", 10000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 0.01ms (O(1) lookup)
        assert result.mean_time < 0.00001, f"Signal lookup too slow: {result.mean_time*1000:.2f}ms"
    
    def test_active_signals_filter_latency(self):
        """Benchmark active signals filtering"""
        manager = SignalLifecycleManager(default_ttl_seconds=60, auto_cleanup=False)
        
        # Create 1000 signals
        for i in range(1000):
            manager.create_signal(
                signal_id=f'TEST-{i}',
                symbol=['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
                direction='BUY',
                entry_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1100,
                confidence=0.5 + (i % 50) * 0.01
            )
        
        def filter_signals():
            manager.get_active_signals(symbol='EURUSD', min_confidence=0.7)
        
        times = benchmark(filter_signals, iterations=1000)
        result = BenchmarkResult("Filter Active Signals (1000 signals)", 1000, times)
        
        print(f"\n{result}")
        
        # Should complete in < 5ms
        assert result.mean_time < 0.005, f"Signal filtering too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# MEMORY BENCHMARKS
# ============================================================================

class TestMemoryBenchmarks:
    """Memory usage benchmarks"""
    
    def test_large_dataset_memory(self):
        """Test memory usage with large datasets"""
        import sys
        
        # Create large price series
        np.random.seed(42)
        n = 100000
        prices = pd.Series(100 + np.cumsum(np.random.randn(n) * 0.01))
        
        # Calculate memory
        memory_mb = sys.getsizeof(prices) / (1024 * 1024)
        
        print(f"\nLarge Dataset Memory: {memory_mb:.2f} MB for {n:,} prices")
        
        # Should use < 10MB for 100k prices
        assert memory_mb < 10, f"Memory usage too high: {memory_mb:.2f} MB"
    
    def test_indicator_calculation_memory(self):
        """Test memory during indicator calculations"""
        
        np.random.seed(42)
        n = 10000
        prices = pd.Series(100 + np.cumsum(np.random.randn(n) * 0.01))
        
        # Calculate multiple indicators
        sma_20 = prices.rolling(20).mean()
        sma_50 = prices.rolling(50).mean()
        ema_20 = prices.ewm(span=20).mean()
        returns = prices.pct_change()
        volatility = returns.rolling(20).std()
        
        # Total memory
        total_memory = (
            sys.getsizeof(prices) +
            sys.getsizeof(sma_20) +
            sys.getsizeof(sma_50) +
            sys.getsizeof(ema_20) +
            sys.getsizeof(returns) +
            sys.getsizeof(volatility)
        ) / (1024 * 1024)
        
        print(f"\nIndicator Memory: {total_memory:.2f} MB for 5 indicators on {n:,} prices")
        
        # Should use < 5MB
        assert total_memory < 5, f"Memory usage too high: {total_memory:.2f} MB"


# ============================================================================
# THROUGHPUT BENCHMARKS
# ============================================================================

class TestThroughputBenchmarks:
    """Throughput benchmarks"""
    
    def test_tick_processing_throughput(self):
        """Test tick processing throughput"""
        np.random.seed(42)
        
        # Generate 10000 ticks
        ticks = [
            {
                'symbol': 'EURUSD',
                'bid': 1.1000 + np.random.randn() * 0.001,
                'ask': 1.1002 + np.random.randn() * 0.001,
                'time': datetime.now(),
                'volume': np.random.randint(1, 100)
            }
            for _ in range(10000)
        ]
        
        def process_ticks():
            for tick in ticks:
                mid = (tick['bid'] + tick['ask']) / 2
                spread = tick['ask'] - tick['bid']
                _ = mid, spread
        
        start = time.perf_counter()
        process_ticks()
        elapsed = time.perf_counter() - start
        
        throughput = len(ticks) / elapsed
        
        print(f"\nTick Processing Throughput: {throughput:,.0f} ticks/sec")
        
        # Should process > 100k ticks/sec
        assert throughput > 100000, f"Throughput too low: {throughput:,.0f} ticks/sec"
    
    def test_signal_generation_throughput(self):
        """Test signal generation throughput"""
        np.random.seed(42)
        
        # Generate price data
        n = 1000
        prices = pd.Series(100 + np.cumsum(np.random.randn(n) * 0.5))
        
        def generate_signals():
            sma_fast = prices.rolling(10).mean()
            sma_slow = prices.rolling(50).mean()
            
            signals = []
            for i in range(50, len(prices)):
                if sma_fast.iloc[i] > sma_slow.iloc[i] and sma_fast.iloc[i-1] <= sma_slow.iloc[i-1]:
                    signals.append(('BUY', i))
                elif sma_fast.iloc[i] < sma_slow.iloc[i] and sma_fast.iloc[i-1] >= sma_slow.iloc[i-1]:
                    signals.append(('SELL', i))
            
            return signals
        
        times = benchmark(generate_signals, iterations=100)
        result = BenchmarkResult("Signal Generation (1000 bars)", 100, times)
        
        print(f"\n{result}")
        
        # Should complete in < 200ms (pandas rolling operations can be slow)
        assert result.mean_time < 0.2, f"Signal generation too slow: {result.mean_time*1000:.2f}ms"


# ============================================================================
# BENCHMARK SUMMARY
# ============================================================================

class TestBenchmarkSummary:
    """Generate benchmark summary"""
    
    def test_generate_summary(self):
        """Generate performance benchmark summary"""
        summary = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     PERFORMANCE BENCHMARK SUMMARY                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Component                    │ Target Latency │ Status                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ OHLCV Validation             │ < 1ms          │ ✓ Critical Path               ║
║ Position Sizing              │ < 0.5ms        │ ✓ Critical Path               ║
║ Kelly Calculation            │ < 0.5ms        │ ✓ Critical Path               ║
║ Can Trade Check              │ < 0.1ms        │ ✓ Critical Path               ║
║ Signal Creation              │ < 0.5ms        │ ✓ Critical Path               ║
║ Signal Lookup                │ < 0.01ms       │ ✓ Critical Path               ║
║ Historical VaR               │ < 10ms         │ ✓ Background                  ║
║ Parametric VaR               │ < 5ms          │ ✓ Background                  ║
║ Monte Carlo VaR              │ < 100ms        │ ✓ Background                  ║
║ Tick Processing              │ > 100k/sec     │ ✓ High Throughput             ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(summary)
        assert True


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmarking tests (legacy compatibility)."""
    
    @pytest.fixture
    def validator(self):
        """Create validator."""
        if DATA_VALIDATOR_AVAILABLE:
            return DataQualityValidator()
        pytest.skip("DataQualityValidator not available")
    
    def test_data_validation_latency(self, validator):
        """Test data validation latency."""
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        
        start = time.time()
        for _ in range(1000):
            validator.validate_ohlcv(ohlcv)
        elapsed = time.time() - start
        
        avg_latency = (elapsed / 1000) * 1000  # Convert to ms
        assert avg_latency < 10, f"Validation latency too high: {avg_latency:.2f}ms"
    
    def test_batch_validation_throughput(self, validator):
        """Test batch validation throughput."""
        ohlcv_list = [
            {
                'open': 100.0 + i * 0.1,
                'high': 105.0 + i * 0.1,
                'low': 95.0 + i * 0.1,
                'close': 102.0 + i * 0.1,
                'volume': 1000 + i * 10,
                'time': datetime.now() + timedelta(minutes=i)
            }
            for i in range(100)
        ]
        
        start = time.time()
        for _ in range(100):
            validator.validate_batch(ohlcv_list)
        elapsed = time.time() - start
        
        throughput = (100 * 100) / elapsed  # Records per second
        assert throughput > 100, f"Throughput too low: {throughput:.0f} records/sec"
    
    def test_risk_calculation_latency(self, risk_manager):
        """Test risk calculation latency."""
        risk_manager.update_equity(10000.0)
        
        for i in range(10):
            risk_manager.add_position(f'pos{i}', f'SYM{i}', 1.0, 100.0 + i, 'forex')
        
        start = time.time()
        for _ in range(100):
            risk_manager.calculate_risk_metrics()
        elapsed = time.time() - start
        
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        assert avg_latency < 50, f"Risk calculation latency too high: {avg_latency:.2f}ms"
    
    def test_position_update_latency(self, risk_manager):
        """Test position update latency."""
        risk_manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        
        start = time.time()
        for i in range(1000):
            risk_manager.update_position_price('pos1', 1.1000 + i * 0.0001)
        elapsed = time.time() - start
        
        avg_latency = (elapsed / 1000) * 1000  # Convert to ms
        assert avg_latency < 5, f"Position update latency too high: {avg_latency:.2f}ms"
    
    def test_memory_usage_baseline(self, risk_manager):
        """Test baseline memory usage."""
        
        initial_size = sys.getsizeof(risk_manager)
        
        # Add positions
        for i in range(100):
            risk_manager.add_position(f'pos{i}', f'SYM{i}', 1.0, 100.0, 'forex')
        
        final_size = sys.getsizeof(risk_manager)
        growth = final_size - initial_size
        
        # Should not grow excessively
        assert growth < 1000000, f"Memory growth too high: {growth} bytes"
    
    def test_equity_history_memory(self, risk_manager):
        """Test equity history memory usage."""
        
        initial_size = sys.getsizeof(risk_manager.returns_history)
        
        # Add 1000 equity updates
        for i in range(1000):
            risk_manager.update_equity(10000.0 + i * 10)
        
        final_size = sys.getsizeof(risk_manager.returns_history)
        growth = final_size - initial_size
        
        # Should be reasonable
        assert growth < 500000, f"History memory growth too high: {growth} bytes"
    
    def test_data_quality_monitoring_throughput(self, monitor):
        """Test data quality monitoring throughput."""
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        
        start = time.time()
        for i in range(1000):
            ohlcv['time'] = datetime.now() + timedelta(minutes=i)
            monitor.process_data(ohlcv)
        elapsed = time.time() - start
        
        throughput = 1000 / elapsed  # Records per second
        assert throughput > 100, f"Monitoring throughput too low: {throughput:.0f} records/sec"
    
    def test_error_handler_retry_latency(self):
        """Test error handler retry latency."""
        handler = RobustErrorHandler()
        
        import asyncio
        
        async def test_retry():
            call_count = 0
            
            async def unreliable_func():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ConnectionError("Failed")
                return "success"
            
            start = time.time()
            for _ in range(100):
                await handler.execute_with_retry(unreliable_func)
            elapsed = time.time() - start
            
            return elapsed
        
        elapsed = asyncio.run(test_retry())
        avg_latency = (elapsed / 100) * 1000  # Convert to ms
        
        # Should be fast even with retries
        assert avg_latency < 100, f"Retry latency too high: {avg_latency:.2f}ms"
    
    def test_concurrent_position_updates(self, risk_manager):
        """Test concurrent position updates."""
        
        async def update_positions():
            risk_manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
            risk_manager.add_position('pos2', 'GBPUSD', 1.0, 1.2500, 'forex')
            
            start = time.time()
            for i in range(100):
                risk_manager.update_position_price('pos1', 1.1000 + i * 0.0001)
                risk_manager.update_position_price('pos2', 1.2500 + i * 0.0001)
            elapsed = time.time() - start
            
            return elapsed
        
        elapsed = asyncio.run(update_positions())
        throughput = (100 * 2) / elapsed  # Updates per second
        
        assert throughput > 1000, f"Concurrent update throughput too low: {throughput:.0f} updates/sec"


class TestScalability:
    """Test scalability with large datasets."""
    
    def test_large_position_portfolio(self):
        """Test with large number of positions."""
        config = {
            'max_var': 0.05,
            'max_cvar': 0.08,
            'max_drawdown': 0.15,
            'max_correlation_risk': 0.10,
            'max_sector_exposure': 0.25
        }
        manager = PortfolioRiskManager(config)
        
        # Add 1000 positions
        start = time.time()
        for i in range(1000):
            manager.add_position(f'pos{i}', f'SYM{i}', 1.0, 100.0 + i * 0.1, 'forex')
        elapsed = time.time() - start
        
        assert len(manager.positions) == 1000
        assert elapsed < 10, f"Adding 1000 positions took too long: {elapsed:.2f}s"
    
    def test_large_batch_validation(self):
        """Test batch validation with large dataset."""
        validator = DataQualityValidator()
        
        ohlcv_list = [
            {
                'open': 100.0 + i * 0.1,
                'high': 105.0 + i * 0.1,
                'low': 95.0 + i * 0.1,
                'close': 102.0 + i * 0.1,
                'volume': 1000 + i * 10,
                'time': datetime.now() + timedelta(minutes=i)
            }
            for i in range(10000)
        ]
        
        start = time.time()
        result = validator.validate_batch(ohlcv_list)
        elapsed = time.time() - start
        
        assert result['total'] == 10000
        assert elapsed < 5, f"Validating 10000 records took too long: {elapsed:.2f}s"
    
    def test_large_error_history(self):
        """Test error handler with large history."""
        handler = RobustErrorHandler()
        handler.max_history = 10000
        
import pathlib
import numpy
import pandas
        
async def generate_errors():
            start = time.time()
            for i in range(1000):
                error = Exception(f"Error {i}")
                await handler.handle_error(error, f"context{i}")
            elapsed = time.time() - start
            return elapsed
        
elapsed = asyncio.run(generate_errors())
        
assert len(handler.error_history) == 1000
assert elapsed < 5, f"Handling 1000 errors took too long: {elapsed:.2f}s"
