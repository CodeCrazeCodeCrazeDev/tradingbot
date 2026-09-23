"""
Comprehensive functional tests for trade_validator module.
These tests exercise all code paths to achieve high coverage.
"""
import pytest
import numpy as np
from trading_bot.validation.trade_validator import (
    TradeValidator, ValidationRules, ValidationError, OrderSafetyCheck
)


class TestValidationRules:
    """Tests for ValidationRules dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        rules = ValidationRules()
        assert rules.max_lot_size == 1.0
        assert rules.min_lot_size == 0.01
        assert rules.max_stop_loss_pct == 0.10
        assert rules.min_stop_loss_pct == 0.001
        assert rules.max_take_profit_pct == 0.50
        assert rules.min_risk_reward == 1.0
        assert rules.max_risk_per_trade_pct == 0.02
        assert rules.max_total_exposure_pct == 0.15
        assert rules.allowed_symbols is None
        assert rules.max_price_deviation_pct == 0.05
        assert rules.min_margin_level == 200.0
    
    def test_custom_values(self):
        """Test custom values can be set."""
        rules = ValidationRules(
            max_lot_size=2.0,
            min_lot_size=0.05,
            allowed_symbols=['EURUSD', 'GBPUSD']
        )
        assert rules.max_lot_size == 2.0
        assert rules.min_lot_size == 0.05
        assert rules.allowed_symbols == ['EURUSD', 'GBPUSD']


class TestTradeValidator:
    """Tests for TradeValidator class."""
    
    def test_initialization_default(self):
        """Test initialization with default rules."""
        validator = TradeValidator()
        assert validator.rules is not None
        assert validator.validation_history == []
    
    def test_initialization_custom_rules(self):
        """Test initialization with custom rules."""
        rules = ValidationRules(max_lot_size=5.0)
        validator = TradeValidator(rules=rules)
        assert validator.rules.max_lot_size == 5.0
    
    def test_validate_trade_success(self):
        """Test successful trade validation."""
        validator = TradeValidator()
        result = validator.validate_trade(
            symbol='EURUSD',
            lot=0.1,
            price=1.1000,
            sl=1.0950,  # 50 pips SL
            tp=1.1100,  # 100 pips TP
            account_equity=10000.0
        )
        assert result is True
        assert len(validator.validation_history) == 1
        assert validator.validation_history[0]['passed'] is True
    
    def test_validate_trade_lot_too_small(self):
        """Test validation fails for lot size too small."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.001,  # Below minimum
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        assert "below minimum" in str(exc_info.value)
    
    def test_validate_trade_lot_too_large(self):
        """Test validation fails for lot size too large."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=10.0,  # Above maximum
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        assert "exceeds maximum" in str(exc_info.value)
    
    def test_validate_trade_negative_lot(self):
        """Test validation fails for negative lot size."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=-0.1,
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        assert "positive" in str(exc_info.value)
    
    def test_validate_trade_negative_price(self):
        """Test validation fails for negative price."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=-1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        assert "positive" in str(exc_info.value)
    
    def test_validate_trade_price_deviation(self):
        """Test validation fails for price deviation from market."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.2000,  # 9% deviation
                sl=1.1950,
                tp=1.2100,
                account_equity=10000.0,
                current_market_price=1.1000
            )
        assert "deviates" in str(exc_info.value)
    
    def test_validate_trade_sl_too_tight(self):
        """Test validation fails for stop loss too tight."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0999,  # Only 1 pip
                tp=1.1100,
                account_equity=10000.0
            )
        assert "too tight" in str(exc_info.value)
    
    def test_validate_trade_sl_too_wide(self):
        """Test validation fails for stop loss too wide."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=0.9000,  # 18% SL
                tp=1.1100,
                account_equity=10000.0
            )
        assert "too wide" in str(exc_info.value)
    
    def test_validate_trade_negative_sl(self):
        """Test validation fails for negative stop loss."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=-1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        assert "positive" in str(exc_info.value)
    
    def test_validate_trade_sl_wrong_direction_long(self):
        """Test validation fails for SL above entry on long trade."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.1050,  # SL above entry for long
                tp=1.1100,
                account_equity=10000.0
            )
        assert "must be below" in str(exc_info.value)
    
    def test_validate_trade_sl_wrong_direction_short(self):
        """Test validation fails for SL below entry on short trade."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,  # SL below entry for short
                tp=1.0900,  # TP below entry = short
                account_equity=10000.0
            )
        assert "must be above" in str(exc_info.value)
    
    def test_validate_trade_tp_too_far(self):
        """Test validation fails for take profit too far."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,
                tp=2.0000,  # 82% TP
                account_equity=10000.0
            )
        assert "too far" in str(exc_info.value)
    
    def test_validate_trade_negative_tp(self):
        """Test validation fails for negative take profit."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,
                tp=-1.1100,
                account_equity=10000.0
            )
        assert "positive" in str(exc_info.value)
    
    def test_validate_trade_tp_wrong_direction_long(self):
        """Test validation fails for TP below entry on long trade."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,
                tp=1.0900,  # TP below entry but SL also below = confusing
                account_equity=10000.0
            )
        # This should trigger the short trade SL check
        assert "must be above" in str(exc_info.value)
    
    def test_validate_trade_poor_risk_reward(self):
        """Test validation fails for poor risk-reward ratio."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0900,  # 100 pips risk
                tp=1.1050,  # 50 pips reward = 0.5 RR
                account_equity=10000.0
            )
        assert "risk-reward" in str(exc_info.value).lower()
    
    def test_validate_trade_symbol_not_allowed(self):
        """Test validation fails for symbol not in allowed list."""
        rules = ValidationRules(allowed_symbols=['EURUSD', 'GBPUSD'])
        validator = TradeValidator(rules=rules)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_trade(
                symbol='USDJPY',
                lot=0.1,
                price=110.00,
                sl=109.50,
                tp=110.50,
                account_equity=10000.0
            )
        assert "not in allowed" in str(exc_info.value)
    
    def test_validate_portfolio_exposure_success(self):
        """Test successful portfolio exposure validation."""
        validator = TradeValidator()
        result = validator.validate_portfolio_exposure(
            new_trade_value=1000.0,
            current_exposure=500.0,
            account_equity=10000.0
        )
        assert result is True
    
    def test_validate_portfolio_exposure_exceeded(self):
        """Test portfolio exposure validation fails when exceeded."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_portfolio_exposure(
                new_trade_value=1000.0,
                current_exposure=1000.0,
                account_equity=10000.0
            )
        assert "exceed" in str(exc_info.value)
    
    def test_validate_margin_level_success(self):
        """Test successful margin level validation."""
        validator = TradeValidator()
        result = validator.validate_margin_level(margin_level=500.0)
        assert result is True
    
    def test_validate_margin_level_failed(self):
        """Test margin level validation fails when below minimum."""
        validator = TradeValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_margin_level(margin_level=100.0)
        assert "below minimum" in str(exc_info.value)
    
    def test_get_validation_stats_empty(self):
        """Test validation stats when no validations done."""
        validator = TradeValidator()
        stats = validator.get_validation_stats()
        assert stats['total'] == 0
        assert stats['passed'] == 0
        assert stats['failed'] == 0
        assert stats['pass_rate'] == 0
    
    def test_get_validation_stats_with_history(self):
        """Test validation stats with validation history."""
        validator = TradeValidator()
        
        # Successful validation
        validator.validate_trade(
            symbol='EURUSD',
            lot=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            account_equity=10000.0
        )
        
        # Failed validation
        try:
            validator.validate_trade(
                symbol='EURUSD',
                lot=10.0,  # Too large
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000.0
            )
        except ValidationError:
        
        stats = validator.get_validation_stats()
        assert stats['total'] == 2
        assert stats['passed'] == 1
        assert stats['failed'] == 1
        assert stats['pass_rate'] == 50.0
    
    def test_reset_history(self):
        """Test resetting validation history."""
        validator = TradeValidator()
        validator.validate_trade(
            symbol='EURUSD',
            lot=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            account_equity=10000.0
        )
        assert len(validator.validation_history) == 1
        
        validator.reset_history()
        assert len(validator.validation_history) == 0


class TestOrderSafetyCheck:
    """Tests for OrderSafetyCheck class."""
    
    def test_check_duplicate_order_no_duplicates(self):
        """Test no duplicate orders detected."""
        import time
        new_order = {'symbol': 'EURUSD', 'lot': 0.1, 'timestamp': time.time()}
        recent_orders = [
            {'symbol': 'GBPUSD', 'lot': 0.1, 'timestamp': time.time() - 0.5}
        ]
        result = OrderSafetyCheck.check_duplicate_order(new_order, recent_orders)
        assert result is True
    
    def test_check_duplicate_order_duplicate_detected(self):
        """Test duplicate order detected."""
from dataclasses import dataclass
import numpy
        current_time = time.time()
        new_order = {'symbol': 'EURUSD', 'lot': 0.1, 'timestamp': current_time}
        recent_orders = [
            {'symbol': 'EURUSD', 'lot': 0.1, 'timestamp': current_time - 0.5}
        ]
        with pytest.raises(ValidationError) as exc_info:
            OrderSafetyCheck.check_duplicate_order(new_order, recent_orders)
        assert "Duplicate" in str(exc_info.value)
    
    def test_check_flash_crash_protection_normal(self):
        """Test flash crash protection with normal prices."""
        historical_prices = [1.1000, 1.1010, 1.0990, 1.1005, 1.0995,
                           1.1002, 1.0998, 1.1001, 1.0999, 1.1003]
        result = OrderSafetyCheck.check_flash_crash_protection(
            current_price=1.1000,
            historical_prices=historical_prices
        )
        assert result is True
    
    def test_check_flash_crash_protection_triggered(self):
        """Test flash crash protection triggered."""
        historical_prices = [1.1000, 1.1010, 1.0990, 1.1005, 1.0995,
                           1.1002, 1.0998, 1.1001, 1.0999, 1.1003]
        with pytest.raises(ValidationError) as exc_info:
            OrderSafetyCheck.check_flash_crash_protection(
                current_price=1.0000,  # 9% deviation
                historical_prices=historical_prices
            )
        assert "Flash crash" in str(exc_info.value)
    
    def test_check_flash_crash_protection_insufficient_data(self):
        """Test flash crash protection with insufficient data."""
        historical_prices = [1.1000, 1.1010, 1.0990]  # Less than 10
        result = OrderSafetyCheck.check_flash_crash_protection(
            current_price=1.0000,
            historical_prices=historical_prices
        )
        assert result is True
    
    def test_check_circuit_breaker_normal(self):
        """Test circuit breaker with normal volatility."""
        result = OrderSafetyCheck.check_circuit_breaker(volatility=0.05)
        assert result is True
    
    def test_check_circuit_breaker_triggered(self):
        """Test circuit breaker triggered."""
        with pytest.raises(ValidationError) as exc_info:
            OrderSafetyCheck.check_circuit_breaker(volatility=0.15)
        assert "Circuit breaker" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
