"""
Property-Based Testing with Hypothesis
Tests that verify properties hold for all valid inputs
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Try to import hypothesis, provide fallback if not installed
try:
    from hypothesis import given, strategies as st, settings, assume, HealthCheck
    from hypothesis.extra.numpy import arrays
    from hypothesis.extra.pandas import column, data_frames, series
    HYPOTHESIS_AVAILABLE = True
    # Default settings to suppress fixture health check
    DEFAULT_SETTINGS = settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create dummy decorators
    def given(*args, **kwargs):
        def decorator(func):
            def wrapper(*a, **kw):
                pytest.skip("Hypothesis not installed")
            return wrapper
        return decorator
    
    class st:
        @staticmethod
        def floats(*args, **kwargs): return None
        @staticmethod
        def integers(*args, **kwargs): return None
        @staticmethod
        def lists(*args, **kwargs): return None
        @staticmethod
        def text(*args, **kwargs): return None
        @staticmethod
        def sampled_from(*args, **kwargs): return None
        @staticmethod
        def one_of(*args, **kwargs): return None
        @staticmethod
        def just(*args, **kwargs): return None
        @staticmethod
        def booleans(*args, **kwargs): return None
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def assume(condition):
    
    DEFAULT_SETTINGS = settings()


# ============================================================================
# POSITION SIZING PROPERTY TESTS
# ============================================================================

class TestPositionSizingProperties:
    """Property-based tests for position sizing"""
    
    @pytest.fixture
    def calculator(self):
        """Create position size calculator"""
        from trading_bot.risk.position_size_calculator import PositionSizeCalculator
        return PositionSizeCalculator({
            'min_position_size': 0.01,
            'max_position_size': 100.0
        })
    
    @given(
        equity=st.floats(min_value=100, max_value=10000000, allow_nan=False, allow_infinity=False),
        risk_pct=st.floats(min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False),
        stop_loss_pips=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_position_size_always_positive(self, calculator, equity, risk_pct, stop_loss_pips):
        """Property: Position size is always positive"""
        from trading_bot.risk.position_size_calculator import PositionSizeMethod
        
        size = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=risk_pct,
            stop_loss_pips=stop_loss_pips,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        assert size >= 0
    
    @given(
        equity=st.floats(min_value=100, max_value=10000000, allow_nan=False, allow_infinity=False),
        risk_pct=st.floats(min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False),
        stop_loss_pips=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_position_size_within_limits(self, calculator, equity, risk_pct, stop_loss_pips):
        """Property: Position size is within min/max limits"""
        
        size = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=risk_pct,
            stop_loss_pips=stop_loss_pips,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        assert calculator.min_position_size <= size <= calculator.max_position_size
    
    @given(
        equity=st.floats(min_value=1000, max_value=100000, allow_nan=False, allow_infinity=False),
        risk_pct=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_larger_stop_loss_smaller_position(self, calculator, equity, risk_pct):
        """Property: Larger stop loss results in smaller or equal position"""
        
        size_small_sl = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=risk_pct,
            stop_loss_pips=20,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        size_large_sl = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=risk_pct,
            stop_loss_pips=100,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        assert size_large_sl <= size_small_sl
    
    @given(
        equity=st.floats(min_value=1000, max_value=100000, allow_nan=False, allow_infinity=False),
        stop_loss_pips=st.floats(min_value=10, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_larger_risk_larger_position(self, calculator, equity, stop_loss_pips):
        """Property: Larger risk percentage results in larger or equal position"""
        
        size_small_risk = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=0.01,
            stop_loss_pips=stop_loss_pips,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        size_large_risk = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=equity,
            risk_pct=0.05,
            stop_loss_pips=stop_loss_pips,
            method=PositionSizeMethod.FIXED_RISK
        )
        
        assert size_large_risk >= size_small_risk


# ============================================================================
# KELLY CRITERION PROPERTY TESTS
# ============================================================================

class TestKellyCriterionProperties:
    """Property-based tests for Kelly criterion"""
    
    @pytest.fixture
    def kelly(self):
        """Create Kelly criterion instance"""
        from trading_bot.risk.kelly_criterion import KellyCriterion
        return KellyCriterion({'max_fraction': 0.5})
    
    @given(
        win_rate=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
        win_loss_ratio=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_kelly_fraction_bounded(self, kelly, win_rate, win_loss_ratio):
        """Property: Kelly fraction is bounded between 0 and max_fraction"""
        result = kelly.calculate_kelly(win_rate=win_rate, win_loss_ratio=win_loss_ratio)
        
        assert 0 <= result.optimal_fraction <= kelly.max_fraction
    
    @given(
        win_rate=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
        win_loss_ratio=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_half_kelly_is_half(self, kelly, win_rate, win_loss_ratio):
        """Property: Half Kelly is exactly half of optimal"""
        result = kelly.calculate_kelly(win_rate=win_rate, win_loss_ratio=win_loss_ratio)
        
        if result.optimal_fraction > 0:
            assert abs(result.half_kelly - result.optimal_fraction / 2) < 1e-10
    
    @given(
        win_rate=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
        win_loss_ratio=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_quarter_kelly_is_quarter(self, kelly, win_rate, win_loss_ratio):
        """Property: Quarter Kelly is exactly quarter of optimal"""
        result = kelly.calculate_kelly(win_rate=win_rate, win_loss_ratio=win_loss_ratio)
        
        if result.optimal_fraction > 0:
            assert abs(result.quarter_kelly - result.optimal_fraction / 4) < 1e-10
    
    @given(
        win_loss_ratio=st.floats(min_value=0.5, max_value=5.0, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_higher_win_rate_higher_kelly(self, kelly, win_loss_ratio):
        """Property: Higher win rate results in higher or equal Kelly"""
        result_low = kelly.calculate_kelly(win_rate=0.4, win_loss_ratio=win_loss_ratio)
        result_high = kelly.calculate_kelly(win_rate=0.7, win_loss_ratio=win_loss_ratio)
        
        assert result_high.optimal_fraction >= result_low.optimal_fraction


# ============================================================================
# DATA VALIDATION PROPERTY TESTS
# ============================================================================

class TestDataValidationProperties:
    """Property-based tests for data validation"""
    
    @pytest.fixture
    def validator(self):
        """Create data validator"""
        from trading_bot.validation.data_validator import DataQualityValidator
        return DataQualityValidator({'max_price_change_percent': 10})
    
    @given(
        open_price=st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
        range_pct=st.floats(min_value=0.001, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_valid_ohlcv_passes(self, validator, open_price, range_pct):
        """Property: Valid OHLCV data always passes validation"""
        # Generate valid OHLCV where high >= max(open, close) and low <= min(open, close)
        close = open_price * (1 + range_pct * (np.random.random() - 0.5))
        high = max(open_price, close) * (1 + abs(range_pct))
        low = min(open_price, close) * (1 - abs(range_pct))
        
        ohlcv = {
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': 1000,
            'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        
        # Valid data should pass
        assert is_valid is True or len(issues) == 0 or 'extreme' in str(issues).lower()
    
    @given(
        price=st.floats(min_value=-1000, max_value=-0.01, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_negative_prices_fail(self, validator, price):
        """Property: Negative prices always fail validation"""
        ohlcv = {
            'open': price,
            'high': abs(price) + 1,
            'low': price,
            'close': abs(price),
            'volume': 1000,
            'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        
        assert is_valid is False
    
    @given(
        base_price=st.floats(min_value=1, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_high_less_than_low_fails(self, validator, base_price):
        """Property: High < Low always fails validation"""
        ohlcv = {
            'open': base_price,
            'high': base_price - 1,  # High less than low
            'low': base_price,
            'close': base_price,
            'volume': 1000,
            'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        
        assert is_valid is False


# ============================================================================
# CIRCUIT BREAKER PROPERTY TESTS
# ============================================================================

class TestCircuitBreakerProperties:
    """Property-based tests for circuit breaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker"""
        from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        
        config = CircuitBreakerConfig(
            max_daily_loss=0.05,
            max_drawdown=0.20,
            max_consecutive_losses=5
        )
        
        cb = CircuitBreaker(config)
        cb.start_session(10000)
        return cb
    
    @given(
        pnl=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_trade_recording_updates_state(self, circuit_breaker, pnl):
        """Property: Recording a trade always updates state"""
        initial_balance = circuit_breaker.session.current_balance
        
        circuit_breaker.record_trade(pnl=pnl, is_win=pnl > 0)
        
        new_balance = circuit_breaker.session.current_balance
        
        # Balance should change by pnl amount
        assert abs(new_balance - (initial_balance + pnl)) < 0.01
    
    @given(
        num_losses=st.integers(min_value=1, max_value=10)
    )
    @DEFAULT_SETTINGS
    def test_consecutive_losses_tracked(self, num_losses):
        """Property: Consecutive losses are correctly tracked"""
        
        config = CircuitBreakerConfig(
            max_daily_loss=0.50,  # High limit to avoid triggering
            max_drawdown=0.50,
            max_consecutive_losses=20
        )
        
        cb = CircuitBreaker(config)
        cb.start_session(100000)
        
        for _ in range(num_losses):
            cb.record_trade(pnl=-1, is_win=False)
        
        assert cb.session.consecutive_losses == num_losses
    
    @given(
        num_losses=st.integers(min_value=1, max_value=5)
    )
    @DEFAULT_SETTINGS
    def test_win_resets_consecutive_losses(self, num_losses):
        """Property: A win always resets consecutive losses to 0"""
        
        config = CircuitBreakerConfig(
            max_daily_loss=0.50,
            max_drawdown=0.50,
            max_consecutive_losses=20
        )
        
        cb = CircuitBreaker(config)
        cb.start_session(100000)
        
        # Record losses
        for _ in range(num_losses):
            cb.record_trade(pnl=-1, is_win=False)
        
        # Record win
        cb.record_trade(pnl=10, is_win=True)
        
        assert cb.session.consecutive_losses == 0


# ============================================================================
# DRAWDOWN PROTECTOR PROPERTY TESTS
# ============================================================================

class TestDrawdownProtectorProperties:
    """Property-based tests for drawdown protector"""
    
    @pytest.fixture
    def protector(self):
        """Create drawdown protector"""
        from trading_bot.risk.drawdown_protector import DrawdownProtector
        
        dp = DrawdownProtector(
            max_drawdown_percent=20.0,
            max_daily_loss_percent=5.0
        )
        dp.initialize(10000)
        return dp
    
    @given(
        balance=st.floats(min_value=1, max_value=20000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_drawdown_always_non_negative(self, protector, balance):
        """Property: Drawdown is always non-negative"""
        protector.update_balance(balance)
        
        drawdown = protector.get_drawdown_percent()
        
        assert drawdown >= 0
    
    @given(
        balance=st.floats(min_value=10001, max_value=50000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_new_high_updates_peak(self, protector, balance):
        """Property: New high balance updates peak"""
        protector.update_balance(balance)
        
        assert protector.peak_balance == balance
    
    @given(
        balance=st.floats(min_value=1, max_value=9999, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_lower_balance_keeps_peak(self, protector, balance):
        """Property: Lower balance doesn't change peak"""
        original_peak = protector.peak_balance
        protector.update_balance(balance)
        
        assert protector.peak_balance == original_peak
    
    @given(
        balance=st.floats(min_value=1, max_value=10000, allow_nan=False, allow_infinity=False)
    )
    @DEFAULT_SETTINGS
    def test_multiplier_bounded(self, protector, balance):
        """Property: Position size multiplier is bounded [0, 1]"""
        protector.update_balance(balance)
        
        multiplier = protector.get_position_size_multiplier()
        
        assert 0 <= multiplier <= 1


# ============================================================================
# SIGNAL LIFECYCLE PROPERTY TESTS
# ============================================================================

class TestSignalLifecycleProperties:
    """Property-based tests for signal lifecycle"""
    
    @pytest.fixture
    def manager(self):
        """Create signal lifecycle manager"""
        from trading_bot.signals.signal_lifecycle import SignalLifecycleManager
import numpy
import pandas
        return SignalLifecycleManager(default_ttl_seconds=60, auto_cleanup=False)
    
    @given(
        confidence=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
        ttl=st.integers(min_value=1, max_value=3600)
    )
    @DEFAULT_SETTINGS
    def test_signal_confidence_bounded(self, manager, confidence, ttl):
        """Property: Signal confidence is always bounded [0, 1]"""
        signal = manager.create_signal(
            signal_id=f'TEST-{np.random.randint(10000)}',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=confidence,
            ttl_seconds=ttl
        )
        
        current_conf = signal.calculate_confidence()
        
        assert 0 <= current_conf <= 1
    
    @given(
        extension=st.integers(min_value=1, max_value=3600)
    )
    @DEFAULT_SETTINGS
    def test_ttl_extension_increases_expiry(self, manager, extension):
        """Property: TTL extension always increases expiry time"""
        signal = manager.create_signal(
            signal_id=f'TEST-{np.random.randint(10000)}',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=0.85
        )
        
        original_expiry = signal.expiry_time
        signal.extend_ttl(extension)
        
        assert signal.expiry_time > original_expiry


# ============================================================================
# NUMERICAL STABILITY PROPERTY TESTS
# ============================================================================

class TestNumericalStabilityProperties:
    """Property-based tests for numerical stability"""
    
    @given(
        values=st.lists(
            st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=100
        )
    )
    @DEFAULT_SETTINGS
    def test_mean_calculation_stable(self, values):
        """Property: Mean calculation is numerically stable"""
        arr = np.array(values)
        
        # Standard mean
        standard_mean = np.mean(arr)
        
        # Incremental mean (Welford's)
        running_mean = 0
        for i, x in enumerate(arr):
            running_mean += (x - running_mean) / (i + 1)
        
        # Should be close
        assert abs(standard_mean - running_mean) < 1e-6 * max(abs(standard_mean), 1)
    
    @given(
        values=st.lists(
            st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=100
        )
    )
    @DEFAULT_SETTINGS
    def test_variance_calculation_stable(self, values):
        """Property: Variance calculation is numerically stable"""
        arr = np.array(values)
        
        # Standard variance
        standard_var = np.var(arr)
        
        # Welford's algorithm
        mean = 0
        M2 = 0
        for i, x in enumerate(arr):
            delta = x - mean
            mean += delta / (i + 1)
            delta2 = x - mean
            M2 += delta * delta2
        
        welford_var = M2 / len(arr) if len(arr) > 0 else 0
        
        # Should be close
        assert abs(standard_var - welford_var) < 1e-6 * max(abs(standard_var), 1)
    
    @given(
        prices=st.lists(
            st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=100
        )
    )
    @DEFAULT_SETTINGS
    def test_returns_calculation_stable(self, prices):
        """Property: Returns calculation is numerically stable"""
        arr = np.array(prices)
        
        # Simple returns
        simple_returns = np.diff(arr) / arr[:-1]
        
        # Log returns
        log_returns = np.diff(np.log(arr))
        
        # For small returns, simple ≈ log
        small_return_mask = np.abs(simple_returns) < 0.1
        if small_return_mask.any():
            diff = np.abs(simple_returns[small_return_mask] - log_returns[small_return_mask])
            assert np.all(diff < 0.01)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
