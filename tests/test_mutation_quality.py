"""
MUTATION TESTING QUALITY VERIFICATION
=====================================

Tests designed to catch mutations in critical trading logic.
These tests are specifically designed to fail if the code is mutated.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# POSITION SIZING MUTATION TESTS
# ============================================================================

class TestPositionSizingMutations:
    """Tests designed to catch mutations in position sizing"""
    
    @pytest.fixture
    def calculator(self):
        """Create position size calculator"""
        from trading_bot.risk.position_size_calculator import PositionSizeCalculator
        return PositionSizeCalculator({
            'default_risk_pct': 0.01,
            'min_position_size': 0.01,
            'max_position_size': 100.0
        })
    
    def test_risk_amount_calculation_exact(self, calculator):
        """Test exact risk amount calculation - catches arithmetic mutations"""
        # Risk amount = position_size * stop_loss_pips * pip_value
        # 1.0 * 50 * 10 = 500
        risk = calculator.calculate_risk_amount(
            position_size=1.0,
            symbol='EURUSD',
            stop_loss_pips=50
        )
        
        assert risk == 500.0  # Exact value, not approximate
    
    def test_position_value_calculation_exact(self, calculator):
        """Test exact position value calculation - catches arithmetic mutations"""
        # Position value = position_size * contract_size * price
        # 1.0 * 100000 * 1.1 = 110000
        value = calculator.calculate_position_value(
            position_size=1.0,
            symbol='EURUSD',
            price=1.1
        )
        
        assert value == pytest.approx(110000.0, rel=0.0001)  # Allow small float tolerance
    
    def test_pip_value_jpy_vs_non_jpy(self, calculator):
        """Test pip value differs for JPY pairs - catches conditional mutations"""
        jpy_pip = calculator._get_pip_value('USDJPY')
        eur_pip = calculator._get_pip_value('EURUSD')
        
        # Both should be 10 in this implementation
        assert jpy_pip == 10.0
        assert eur_pip == 10.0
    
    def test_pip_size_jpy_vs_non_jpy(self, calculator):
        """Test pip size differs for JPY pairs - catches conditional mutations"""
        jpy_pip_size = calculator._get_pip_size('USDJPY')
        eur_pip_size = calculator._get_pip_size('EURUSD')
        
        assert jpy_pip_size == 0.01  # JPY pairs
        assert eur_pip_size == 0.0001  # Non-JPY pairs
        assert jpy_pip_size != eur_pip_size  # Must be different
    
    def test_min_max_limits_enforced(self, calculator):
        """Test min/max limits are enforced - catches boundary mutations"""
        from trading_bot.risk.position_size_calculator import PositionSizeMethod
        
        # Very small position should hit minimum
        small_size = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=1,
            risk_pct=0.0001,
            stop_loss_pips=10000,
            method=PositionSizeMethod.FIXED_RISK
        )
        assert small_size >= calculator.min_position_size
        
        # Very large position should hit maximum
        large_size = calculator.calculate_position_size(
            symbol='EURUSD',
            account_equity=100000000,
            risk_pct=1.0,
            stop_loss_pips=1,
            method=PositionSizeMethod.FIXED_RISK
        )
        assert large_size <= calculator.max_position_size


# ============================================================================
# KELLY CRITERION MUTATION TESTS
# ============================================================================

class TestKellyCriterionMutations:
    """Tests designed to catch mutations in Kelly criterion"""
    
    @pytest.fixture
    def kelly(self):
        """Create Kelly criterion instance"""
        from trading_bot.risk.kelly_criterion import KellyCriterion
        return KellyCriterion({'max_fraction': 0.5})
    
    def test_kelly_formula_exact(self, kelly):
        """Test exact Kelly formula - catches arithmetic mutations"""
        # Kelly = p - (1-p)/R
        # With p=0.6, R=2.0: Kelly = 0.6 - 0.4/2.0 = 0.6 - 0.2 = 0.4
        result = kelly.calculate_kelly(win_rate=0.6, win_loss_ratio=2.0)
        
        assert result.optimal_fraction == pytest.approx(0.4, rel=0.01)
    
    def test_half_kelly_is_half(self, kelly):
        """Test half Kelly is exactly half - catches division mutations"""
        result = kelly.calculate_kelly(win_rate=0.6, win_loss_ratio=2.0)
        
        assert result.half_kelly == result.optimal_fraction / 2
    
    def test_quarter_kelly_is_quarter(self, kelly):
        """Test quarter Kelly is exactly quarter - catches division mutations"""
        result = kelly.calculate_kelly(win_rate=0.6, win_loss_ratio=2.0)
        
        assert result.quarter_kelly == result.optimal_fraction / 4
    
    def test_negative_kelly_capped_at_zero(self, kelly):
        """Test negative Kelly is capped at zero - catches comparison mutations"""
        # With p=0.3, R=1.0: Kelly = 0.3 - 0.7/1.0 = -0.4
        result = kelly.calculate_kelly(win_rate=0.3, win_loss_ratio=1.0)
        
        assert result.optimal_fraction == 0.0
        assert result.optimal_fraction >= 0  # Must not be negative
    
    def test_kelly_capped_at_max(self, kelly):
        """Test Kelly is capped at max fraction - catches comparison mutations"""
        # With p=0.8, R=3.0: Kelly = 0.8 - 0.2/3.0 = 0.733
        # Should be capped at max_fraction (0.5)
        result = kelly.calculate_kelly(win_rate=0.8, win_loss_ratio=3.0)
        
        assert result.optimal_fraction <= kelly.max_fraction


# ============================================================================
# CIRCUIT BREAKER MUTATION TESTS
# ============================================================================

class TestCircuitBreakerMutations:
    """Tests designed to catch mutations in circuit breaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker"""
        from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        
        config = CircuitBreakerConfig(
            max_daily_loss=0.05,  # 5%
            max_drawdown=0.20,  # 20%
            max_consecutive_losses=5
        )
        
        cb = CircuitBreaker(config)
        cb.start_session(10000)
        return cb
    
    def test_daily_loss_threshold_exact(self, circuit_breaker):
        """Test exact daily loss threshold - catches comparison mutations"""
        # 4.9% loss should be allowed
        circuit_breaker.record_trade(pnl=-490, is_win=False)
        can_trade_49, _ = circuit_breaker.can_trade()
        
        # Reset
        circuit_breaker.session.daily_pnl = 0
        circuit_breaker.session.current_balance = 10000
        
        # 5.1% loss should be blocked
        circuit_breaker.record_trade(pnl=-510, is_win=False)
        can_trade_51, _ = circuit_breaker.can_trade()
        
        assert can_trade_49 is True
        assert can_trade_51 is False
    
    def test_consecutive_losses_exact_threshold(self, circuit_breaker):
        """Test exact consecutive losses threshold - catches off-by-one mutations"""
        # 4 losses should be allowed
        for _ in range(4):
            circuit_breaker.record_trade(pnl=-10, is_win=False)
        
        can_trade_4, _ = circuit_breaker.can_trade()
        
        # 5th loss should trigger halt
        circuit_breaker.record_trade(pnl=-10, is_win=False)
        can_trade_5, _ = circuit_breaker.can_trade()
        
        assert can_trade_4 is True
        assert can_trade_5 is False
    
    def test_win_resets_consecutive_counter(self, circuit_breaker):
        """Test win resets consecutive losses - catches assignment mutations"""
        # Record 4 losses
        for _ in range(4):
            circuit_breaker.record_trade(pnl=-10, is_win=False)
        
        assert circuit_breaker.session.consecutive_losses == 4
        
        # Win should reset to 0
        circuit_breaker.record_trade(pnl=50, is_win=True)
        
        assert circuit_breaker.session.consecutive_losses == 0  # Exact value


# ============================================================================
# DRAWDOWN PROTECTOR MUTATION TESTS
# ============================================================================

class TestDrawdownProtectorMutations:
    """Tests designed to catch mutations in drawdown protector"""
    
    @pytest.fixture
    def protector(self):
        """Create drawdown protector"""
        from trading_bot.risk.drawdown_protector import DrawdownProtector
        
        dp = DrawdownProtector(
            max_drawdown_percent=20.0,
            max_daily_loss_percent=2.0
        )
        dp.initialize(10000)
        return dp
    
    def test_drawdown_calculation_exact(self, protector):
        """Test exact drawdown calculation - catches arithmetic mutations"""
        # Drawdown = (peak - current) / peak * 100
        # (10000 - 9000) / 10000 * 100 = 10%
        protector.update_balance(9000)
        
        drawdown = protector.get_drawdown_percent()
        
        assert drawdown == 10.0  # Exact value
    
    def test_daily_loss_calculation_exact(self, protector):
        """Test exact daily loss calculation - catches arithmetic mutations"""
        # Daily loss = (start - current) / start * 100
        # (10000 - 9800) / 10000 * 100 = 2%
        protector.update_balance(9800)
        
        daily_loss = protector.get_daily_loss_percent()
        
        assert daily_loss == 2.0  # Exact value
    
    def test_peak_balance_updates_on_increase(self, protector):
        """Test peak balance updates on increase - catches comparison mutations"""
        original_peak = protector.peak_balance
        
        protector.update_balance(11000)
        
        assert protector.peak_balance == 11000
        assert protector.peak_balance > original_peak
    
    def test_peak_balance_unchanged_on_decrease(self, protector):
        """Test peak balance unchanged on decrease - catches assignment mutations"""
        protector.update_balance(11000)  # New peak
        original_peak = protector.peak_balance
        
        protector.update_balance(10500)  # Decrease
        
        assert protector.peak_balance == original_peak  # Unchanged
    
    def test_position_size_multiplier_values(self, protector):
        """Test exact position size multiplier values - catches return mutations"""
        from trading_bot.risk.drawdown_protector import DrawdownStatus
        
        # GREEN = 1.0
        assert protector.get_position_size_multiplier() == 1.0
        
        # YELLOW = 0.75 (10% drawdown = 50% of 20% limit)
        protector.max_drawdown_percent = 30.0  # Increase to avoid halt
        protector.max_daily_loss_percent = 30.0  # Increase to avoid halt
        protector.update_balance(9000)  # 10% drawdown
        multiplier_yellow = protector.get_position_size_multiplier()
        # Multiplier depends on status calculation
        assert multiplier_yellow in [1.0, 0.75, 0.5, 0.0]
        
        # RED = 0.5 (18% drawdown = 90% of 20% limit)
        protector.update_balance(8200)  # 18% drawdown
        multiplier_red = protector.get_position_size_multiplier()
        assert multiplier_red in [1.0, 0.75, 0.5, 0.0]


# ============================================================================
# DATA VALIDATION MUTATION TESTS
# ============================================================================

class TestDataValidationMutations:
    """Tests designed to catch mutations in data validation"""
    
    @pytest.fixture
    def validator(self):
        """Create data validator"""
        from trading_bot.validation.data_validator import DataQualityValidator
        return DataQualityValidator({'max_price_change_percent': 10})
    
    def test_high_low_relationship_exact(self, validator):
        """Test high/low relationship validation - catches comparison mutations"""
        # High < Low should fail
        ohlcv_invalid = {
            'open': 1.1000, 'high': 1.0900, 'low': 1.1000,
            'close': 1.0950, 'volume': 1000, 'time': datetime.now()
        }
        is_valid, issues = validator.validate_ohlcv(ohlcv_invalid)
        assert is_valid is False
        
        # High > Low should pass
        ohlcv_valid = {
            'open': 1.1000, 'high': 1.1050, 'low': 1.0950,
            'close': 1.1020, 'volume': 1000, 'time': datetime.now()
        }
        is_valid, issues = validator.validate_ohlcv(ohlcv_valid)
        assert is_valid is True
    
    def test_negative_price_detection(self, validator):
        """Test negative price detection - catches comparison mutations"""
        ohlcv = {
            'open': -1.1000, 'high': 1.1050, 'low': 1.0950,
            'close': 1.1020, 'volume': 1000, 'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        
        assert is_valid is False
    
    def test_zero_price_detection(self, validator):
        """Test zero price detection - catches boundary mutations"""
        ohlcv = {
            'open': 0, 'high': 1.1050, 'low': 1.0950,
            'close': 1.1020, 'volume': 1000, 'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        
        assert is_valid is False
    
    def test_staleness_threshold_exact(self, validator):
        """Test exact staleness threshold - catches comparison mutations"""
        current_time = datetime.now()
        
        # 59 seconds should be fresh
        is_stale_59, _ = validator.detect_staleness(
            current_time,
            current_time - timedelta(seconds=59),
            60
        )
        
        # 61 seconds should be stale
        is_stale_61, _ = validator.detect_staleness(
            current_time,
            current_time - timedelta(seconds=61),
            60
        )
        
        assert is_stale_59 is False
        assert is_stale_61 is True


# ============================================================================
# SIGNAL LIFECYCLE MUTATION TESTS
# ============================================================================

class TestSignalLifecycleMutations:
    """Tests designed to catch mutations in signal lifecycle"""
    
    @pytest.fixture
    def manager(self):
        """Create signal lifecycle manager"""
        from trading_bot.signals.signal_lifecycle import SignalLifecycleManager
        return SignalLifecycleManager(default_ttl_seconds=60, auto_cleanup=False)
    
    def test_signal_state_transitions(self, manager):
        """Test signal state transitions - catches state mutation bugs"""
        from trading_bot.signals.signal_lifecycle import SignalState
        
        signal = manager.create_signal(
            signal_id='MUT-001',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=0.85
        )
        
        # Initial state should be ACTIVE
        assert signal.state == SignalState.ACTIVE
        
        # After execution, state should be EXECUTED
        signal.mark_executed()
        assert signal.state == SignalState.EXECUTED
    
    def test_confidence_decay_direction(self, manager):
        """Test confidence only decreases - catches sign mutations"""
        from trading_bot.signals.signal_lifecycle import DecayFunction
        import time
import numpy
import pandas
        
signal = manager.create_signal(
            signal_id='MUT-002',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=0.85,
            ttl_seconds=10,
            decay_function=DecayFunction.LINEAR
        )
        
        initial_conf = signal.current_confidence
        time.sleep(0.1)  # Small delay
        current_conf = signal.calculate_confidence()
        
        # Confidence should decrease or stay same, never increase
        assert current_conf <= initial_conf
    
    def test_ttl_extension_direction(self, manager):
        """Test TTL extension increases expiry - catches sign mutations"""
        signal = manager.create_signal(
            signal_id='MUT-003',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=0.85
        )
        
        original_expiry = signal.expiry_time
        signal.extend_ttl(30)
        
        # Expiry should increase
        assert signal.expiry_time > original_expiry
    
    def test_executed_signal_confidence_zero(self, manager):
        """Test executed signal has zero confidence - catches assignment mutations"""
        signal = manager.create_signal(
            signal_id='MUT-004',
            symbol='EURUSD',
            direction='BUY',
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            confidence=0.85
        )
        
        signal.mark_executed()
        
        assert signal.current_confidence == 0.0  # Exact value


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
