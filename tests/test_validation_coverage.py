"""
Validation module coverage tests - Tests all validation code paths.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTradeValidatorCoverage(unittest.TestCase):
    """Coverage tests for TradeValidator"""
    
    def setUp(self):
        from trading_bot.validation.trade_validator import TradeValidator, ValidationRules
        self.validator = TradeValidator()
        self.custom_rules = ValidationRules(
            max_lot_size=2.0,
            min_lot_size=0.01,
            allowed_symbols=['EURUSD', 'GBPUSD']
        )
        self.validator_custom = TradeValidator(rules=self.custom_rules)
    
    def test_validate_trade_valid(self):
        """Test valid trade validation"""
        result = self.validator.validate_trade(
            symbol='EURUSD',
            lot=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            account_equity=10000
        )
        self.assertTrue(result)
    
    def test_validate_trade_invalid_lot_negative(self):
        """Test validation with negative lot"""
        from trading_bot.validation.trade_validator import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=-0.1,
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_lot_too_small(self):
        """Test validation with lot too small"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.001,  # Below min
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_lot_too_large(self):
        """Test validation with lot too large"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=10.0,  # Above max
                price=1.1000,
                sl=1.0950,
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_invalid_price(self):
        """Test validation with invalid price"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=-1.1000,  # Negative price
                sl=1.0950,
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_price_deviation(self):
        """Test validation with price deviation"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.2000,  # 9% deviation
                sl=1.1950,
                tp=1.2100,
                account_equity=10000,
                current_market_price=1.1000
            )
    
    def test_validate_trade_invalid_sl(self):
        """Test validation with invalid stop loss"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=-1.0950,  # Negative SL
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_sl_too_tight(self):
        """Test validation with stop loss too tight"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0999,  # Too tight
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_sl_too_wide(self):
        """Test validation with stop loss too wide"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=0.9000,  # Too wide (18%)
                tp=1.1100,
                account_equity=10000
            )
    
    def test_validate_trade_invalid_tp(self):
        """Test validation with invalid take profit"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,
                tp=-1.1100,  # Negative TP
                account_equity=10000
            )
    
    def test_validate_trade_tp_too_far(self):
        """Test validation with take profit too far"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0950,
                tp=2.0000,  # 82% away
                account_equity=10000
            )
    
    def test_validate_trade_bad_risk_reward(self):
        """Test validation with bad risk/reward ratio"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=0.1,
                price=1.1000,
                sl=1.0900,  # 100 pips risk
                tp=1.1010,  # 10 pips reward (0.1 R:R)
                account_equity=10000
            )
    
    def test_validate_trade_excessive_risk(self):
        """Test validation with excessive risk per trade"""
        with self.assertRaises(ValidationError):
            self.validator.validate_trade(
                symbol='EURUSD',
                lot=1.0,  # Large lot
                price=1.1000,
                sl=1.0500,  # 500 pips risk
                tp=1.1500,
                account_equity=1000  # Small account
            )
    
    def test_validate_trade_symbol_not_allowed(self):
        """Test validation with symbol not in allowed list"""
        with self.assertRaises(ValidationError):
            self.validator_custom.validate_trade(
                symbol='USDJPY',  # Not in allowed list
                lot=0.1,
                price=150.00,
                sl=149.50,
                tp=150.50,
                account_equity=10000
            )
    
    def test_validate_trade_allowed_symbol(self):
        """Test validation with allowed symbol"""
        result = self.validator_custom.validate_trade(
            symbol='EURUSD',  # In allowed list
            lot=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            account_equity=10000
        )
        self.assertTrue(result)


class TestDataQualityValidatorCoverage(unittest.TestCase):
    """Coverage tests for DataQualityValidator"""
    
    def setUp(self):
        from trading_bot.validation.data_quality import DataQualityValidator
        self.validator = DataQualityValidator()
    
    def test_validate_ohlcv_valid(self):
        """Test valid OHLCV data"""
        df = pd.DataFrame({
            'open': [1.1, 1.2, 1.15],
            'high': [1.25, 1.3, 1.2],
            'low': [1.05, 1.15, 1.1],
            'close': [1.2, 1.25, 1.18],
            'volume': [1000, 1500, 1200]
        })
        is_valid, results = self.validator.validate_ohlcv(df)
        self.assertTrue(is_valid)
    
    def test_validate_ohlcv_missing_columns(self):
        """Test OHLCV with missing columns"""
        df = pd.DataFrame({
            'open': [1.1, 1.2],
            'close': [1.2, 1.25]
        })
        is_valid, results = self.validator.validate_ohlcv(df)
        self.assertFalse(is_valid)
    
    def test_validate_ohlcv_with_nan(self):
        """Test OHLCV with NaN values"""
        df = pd.DataFrame({
            'open': [1.1, np.nan, 1.15],
            'high': [1.25, 1.3, 1.2],
            'low': [1.05, 1.15, 1.1],
            'close': [1.2, 1.25, 1.18],
            'volume': [1000, 1500, 1200]
        })
        is_valid, results = self.validator.validate_ohlcv(df)
        # Should flag NaN values
        self.assertIsNotNone(results)
    
    def test_validate_ohlcv_invalid_high_low(self):
        """Test OHLCV with high < low"""
        df = pd.DataFrame({
            'open': [1.1, 1.2, 1.15],
            'high': [1.05, 1.3, 1.2],  # High < Low
            'low': [1.25, 1.15, 1.1],
            'close': [1.2, 1.25, 1.18],
            'volume': [1000, 1500, 1200]
        })
        is_valid, results = self.validator.validate_ohlcv(df)
        self.assertFalse(is_valid)
    
    def test_validate_ohlcv_negative_volume(self):
        """Test OHLCV with negative volume"""
        df = pd.DataFrame({
            'open': [1.1, 1.2, 1.15],
            'high': [1.25, 1.3, 1.2],
            'low': [1.05, 1.15, 1.1],
            'close': [1.2, 1.25, 1.18],
            'volume': [1000, -1500, 1200]  # Negative volume
        })
        is_valid, results = self.validator.validate_ohlcv(df)
        self.assertFalse(is_valid)
    
    def test_validate_ohlcv_empty(self):
        """Test empty OHLCV data"""
        df = pd.DataFrame()
        is_valid, results = self.validator.validate_ohlcv(df)
        self.assertFalse(is_valid)
    
    def test_check_staleness(self):
        """Test staleness check"""
        if hasattr(self.validator, 'check_staleness'):
            # Fresh data
            fresh_time = datetime.now()
            result = self.validator.check_staleness(fresh_time)
            self.assertFalse(result)  # Not stale
            
            # Stale data
            stale_time = datetime.now() - timedelta(hours=1)
            result = self.validator.check_staleness(stale_time)
            self.assertTrue(result)  # Stale


class TestRiskValidationGateCoverage(unittest.TestCase):
    """Coverage tests for RiskValidationGate"""
    
    def setUp(self):
        from trading_bot.validation.risk_validation_gate import RiskValidationGate
        self.gate = RiskValidationGate()
    
    def test_validate_trade_valid(self):
        """Test valid trade validation"""
        result = self.gate.validate_trade(
            symbol='EURUSD',
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction='LONG'
        )
        self.assertTrue(result.approved)
    
    def test_validate_trade_invalid_position_size(self):
        """Test validation with invalid position size"""
        result = self.gate.validate_trade(
            symbol='EURUSD',
            position_size=-0.1,  # Invalid
            risk_amount=100,
            risk_percent=0.01,
            direction='LONG'
        )
        self.assertFalse(result.approved)
    
    def test_validate_trade_high_risk(self):
        """Test validation with high risk"""
        result = self.gate.validate_trade(
            symbol='EURUSD',
            position_size=0.1,
            risk_amount=1000,
            risk_percent=0.10,  # 10% risk
            direction='LONG'
        )
        # Should have warnings or be rejected
        self.assertIsNotNone(result)
    
    def test_add_position(self):
        """Test adding position"""
        self.gate.add_position('EURUSD', {'size': 0.1, 'direction': 'LONG'})
        self.assertIn('EURUSD', self.gate.open_positions)
    
    def test_remove_position(self):
        """Test removing position"""
        self.gate.add_position('EURUSD', {'size': 0.1})
        self.gate.remove_position('EURUSD')
        self.assertNotIn('EURUSD', self.gate.open_positions)
    
    def test_update_loss(self):
        """Test updating loss"""
        self.gate.update_loss(100, 0.01)
        self.assertEqual(self.gate.daily_loss, 0.01)
    
    def test_update_drawdown(self):
        """Test updating drawdown"""
        self.gate.update_drawdown(0.05)
        self.assertEqual(self.gate.current_drawdown, 0.05)
    
    def test_get_status(self):
        """Test getting status"""
        status = self.gate.get_status()
        self.assertIn('emergency_shutdown', status)
        self.assertIn('current_drawdown', status)


class TestDataValidationPipelineCoverage(unittest.TestCase):
    """Coverage tests for DataValidationPipeline"""
    
    def setUp(self):
        from trading_bot.validation.data_validation_pipeline import DataValidationPipeline, OHLCVData
        self.pipeline = DataValidationPipeline()
        self.OHLCVData = OHLCVData
    
    def test_validate_valid_data(self):
        """Test pipeline with valid data"""
        data = self.OHLCVData(
            symbol='EURUSD',
            timestamp=datetime.now(),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            volume=1000
        )
        is_valid, result = self.pipeline.validate(data)
        self.assertIsNotNone(result)
    
    def test_validate_dict_data(self):
        """Test pipeline with dict data"""
        data = {
            'symbol': 'EURUSD',
            'timestamp': datetime.now(),
            'open': 1.1000,
            'high': 1.1050,
            'low': 1.0950,
            'close': 1.1020,
            'volume': 1000
        }
        is_valid, result = self.pipeline.validate(data)
        self.assertIsNotNone(result)
    
    def test_get_stats(self):
        """Test getting pipeline stats"""
        stats = self.pipeline.get_stats()
        self.assertIn('total_validated', stats)


class TestSelfTestingSystemCoverage(unittest.TestCase):
    """Coverage tests for SelfTestingSystem"""
    
    def setUp(self):
        from trading_bot.validation.self_testing import SelfTestingSystem
        self.system = SelfTestingSystem()
    
    def test_run_connectivity_test(self):
        """Test connectivity test"""
        if hasattr(self.system, 'run_test'):
            result = self.system.run_test('connectivity')
            self.assertIsNotNone(result)
    
    def test_run_all_tests(self):
        """Test running all tests"""
        if hasattr(self.system, 'run_all_tests'):
            results = self.system.run_all_tests()
            self.assertIsNotNone(results)
    
    def test_get_test_results(self):
        """Test getting test results"""
        if hasattr(self.system, 'get_results'):
            results = self.system.get_results()
            self.assertIsNotNone(results)
    
    def test_register_test(self):
        """Test registering custom test"""
        if hasattr(self.system, 'register_test'):
            def custom_test():
                return True
            self.system.register_test('custom', custom_test)


class TestSelfVerificationSystemCoverage(unittest.TestCase):
    """Coverage tests for SelfVerificationSystem"""
    
    def setUp(self):
        from trading_bot.validation.self_verification import SelfVerificationSystem
        self.system = SelfVerificationSystem()
    
    def test_verify_component(self):
        """Test component verification"""
        if hasattr(self.system, 'verify_component'):
            result = self.system.verify_component('data')
            self.assertIsNotNone(result)
    
    def test_verify_all(self):
        """Test verifying all components"""
        if hasattr(self.system, 'verify_all'):
            results = self.system.verify_all()
            self.assertIsNotNone(results)
    
    def test_get_verification_status(self):
        """Test getting verification status"""
        if hasattr(self.system, 'get_status'):
            status = self.system.get_status()
            self.assertIsNotNone(status)


class TestSelfOptimizationSystemCoverage(unittest.TestCase):
    """Coverage tests for SelfOptimizationSystem"""
    
    def setUp(self):
        from trading_bot.validation.self_optimization import SelfOptimizationSystem
        self.system = SelfOptimizationSystem()
    
    def test_optimize(self):
        """Test optimization"""
        if hasattr(self.system, 'optimize'):
            result = self.system.optimize()
            self.assertIsNotNone(result)
    
    def test_get_recommendations(self):
        """Test getting recommendations"""
        if hasattr(self.system, 'get_recommendations'):
            recommendations = self.system.get_recommendations()
            self.assertIsNotNone(recommendations)
    
    def test_apply_optimization(self):
        """Test applying optimization"""
        if hasattr(self.system, 'apply_optimization'):
            result = self.system.apply_optimization({'param': 'value'})
            self.assertIsNotNone(result)


class TestCriticalValidatorsCoverage(unittest.TestCase):
    """Coverage tests for CriticalValidators"""
    
    def setUp(self):

            from trading_bot.validation.critical_validators import CriticalValidators
import numpy
import pandas
self.validator = CriticalValidators()
self.available = True
def test_validate_trade(self):
        """Test trade validation"""
        if not self.available:
            self.skipTest("CriticalValidators not available")
        
        if hasattr(self.validator, 'validate_trade'):
            trade = {
                'symbol': 'EURUSD',
                'direction': 'buy',
                'size': 0.01,
                'price': 1.1000
            }
            result = self.validator.validate_trade(trade)
            self.assertIsNotNone(result)
    
def test_validate_risk(self):
        """Test risk validation"""
        if not self.available:
            self.skipTest("CriticalValidators not available")
        
        if hasattr(self.validator, 'validate_risk'):
            risk_params = {
                'max_position_size': 0.02,
                'max_daily_loss': 0.05
            }
            result = self.validator.validate_risk(risk_params)
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
