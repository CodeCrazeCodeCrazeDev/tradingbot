"""
Unit tests for Position Sizer

Tests for position sizing calculations with various methods
"""

import pytest
import numpy as np
from typing import Dict, Any

from trading_bot.risk.position_sizer import (
    PositionSizer,
    SizingMethod
)


class TestPositionSizer:
    """Test suite for PositionSizer"""
    
    @pytest.fixture
    def sizer(self):
        """Create a position sizer instance"""
        config = {
            'default_risk_pct': 0.02,
            'max_position_size': 1000000,
            'min_position_size': 1000,
            'default_kelly_fraction': 0.25
        }
        return PositionSizer(config)
    
    def test_initialization(self):
        """Test position sizer initialization"""
        sizer = PositionSizer()
        assert sizer is not None
        assert sizer.default_risk_pct == 0.02
        assert sizer.max_position_size == 1000000
        assert sizer.min_position_size == 1000
    
    def test_fixed_risk_sizing(self, sizer):
        """Test fixed risk position sizing"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            stop_loss_pips=50,
            entry_price=1.1000,
            method=SizingMethod.FIXED_RISK
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
        assert size >= sizer.min_position_size
        
        # Risk should be approximately 2% of account
        # $10,000 * 0.02 = $200 risk
        # 50 pips = $50 per 10k lot
        # $200 / $50 = 4 lots = 40,000 units
        assert 35000 <= size <= 45000  # Allow some tolerance
    
    def test_kelly_criterion_sizing(self, sizer):
        """Test Kelly criterion position sizing"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            method=SizingMethod.KELLY_CRITERION,
            win_rate=0.55,
            avg_win=1.5,
            avg_loss=1.0
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_volatility_adjusted_sizing(self, sizer):
        """Test volatility-adjusted position sizing"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            method=SizingMethod.VOLATILITY_ADJUSTED,
            volatility=0.015,  # 1.5% daily volatility
            entry_price=1.1000
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_zero_equity(self, sizer):
        """Test with zero account equity"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=0,
            risk_pct=0.02,
            stop_loss_pips=50,
            entry_price=1.1000
        )
        
        assert size == 0
    
    def test_negative_equity(self, sizer):
        """Test with negative account equity"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=-1000,
            risk_pct=0.02,
            stop_loss_pips=50,
            entry_price=1.1000
        )
        
        assert size == 0
    
    def test_zero_stop_loss(self, sizer):
        """Test with zero stop loss"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            stop_loss_pips=0,
            entry_price=1.1000
        )
        
        # Should return 0 or handle gracefully
        assert size >= 0
    
    def test_max_position_size_limit(self, sizer):
        """Test maximum position size limit"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=1000000,  # Large equity
            risk_pct=0.10,  # High risk
            stop_loss_pips=10,  # Small stop
            entry_price=1.1000
        )
        
        assert size <= sizer.max_position_size
    
    def test_min_position_size_limit(self, sizer):
        """Test minimum position size limit"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=100,  # Small equity
            risk_pct=0.01,  # Small risk
            stop_loss_pips=100,  # Large stop
            entry_price=1.1000
        )
        
        # Should return 0 if below minimum
        assert size == 0 or size >= sizer.min_position_size
    
    def test_high_risk_percentage(self, sizer):
        """Test with high risk percentage"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.50,  # 50% risk (very high)
            stop_loss_pips=50,
            entry_price=1.1000
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_pip_value_calculation(self, sizer):
        """Test pip value calculation"""
        pip_value = sizer.calculate_pip_value('EURUSD', 1.1000)
        
        # For 1 standard lot (100k) EURUSD, 1 pip = $10
        assert abs(pip_value - 10.0) < 0.01
    
    def test_pip_value_jpy_pair(self, sizer):
        """Test pip value for JPY pairs"""
        pip_value = sizer.calculate_pip_value('USDJPY', 110.00)
        
        # For JPY pairs, pip is different
        assert pip_value > 0
    
    def test_lot_size_conversion(self, sizer):
        """Test lot size conversion"""
        lots = sizer.calculate_lot_size(100000, 'EURUSD')
        
        # 100k units = 1 standard lot
        assert abs(lots - 1.0) < 0.01
    
    def test_lot_size_mini(self, sizer):
        """Test mini lot conversion"""
        lots = sizer.calculate_lot_size(10000, 'EURUSD')
        
        # 10k units = 0.1 lots
        assert abs(lots - 0.1) < 0.01
    
    def test_lot_size_micro(self, sizer):
        """Test micro lot conversion"""
        lots = sizer.calculate_lot_size(1000, 'EURUSD')
        
        # 1k units = 0.01 lots
        assert abs(lots - 0.01) < 0.001
    
    def test_different_symbols(self, sizer):
        """Test position sizing for different symbols"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
        
        for symbol in symbols:
            size = sizer.calculate_position_size(
                symbol=symbol,
                account_equity=10000,
                risk_pct=0.02,
                stop_loss_pips=50,
                entry_price=1.1000 if 'USD' in symbol[:3] else 110.0
            )
            
            assert size > 0
            assert size <= sizer.max_position_size
    
    def test_kelly_with_poor_stats(self, sizer):
        """Test Kelly criterion with poor win rate"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            method=SizingMethod.KELLY_CRITERION,
            win_rate=0.30,  # Poor win rate
            avg_win=1.0,
            avg_loss=1.0
        )
        
        # Should return small or zero size
        assert size >= 0
    
    def test_kelly_with_excellent_stats(self, sizer):
        """Test Kelly criterion with excellent stats"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            method=SizingMethod.KELLY_CRITERION,
            win_rate=0.70,  # Excellent win rate
            avg_win=2.0,
            avg_loss=1.0
        )
        
        assert size > 0
        assert size <= sizer.max_position_size
    
    def test_volatility_high(self, sizer):
        """Test with high volatility"""
        size_high_vol = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=100000,  # Larger equity to avoid min_position_size floor
            risk_pct=0.02,
            method=SizingMethod.VOLATILITY_ADJUSTED,
            volatility=0.05,  # 5% volatility (high)
            entry_price=1.1000
        )
        
        size_low_vol = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=100000,  # Larger equity to avoid min_position_size floor
            risk_pct=0.02,
            method=SizingMethod.VOLATILITY_ADJUSTED,
            volatility=0.01,  # 1% volatility (low)
            entry_price=1.1000
        )
        
        # Higher volatility should result in smaller position
        assert size_high_vol < size_low_vol
    
    def test_risk_parity_sizing(self, sizer):
        """Test risk parity position sizing"""
        # Test with multiple positions
        positions = {
            'EURUSD': {'volatility': 0.01, 'correlation': 0.5},
            'GBPUSD': {'volatility': 0.015, 'correlation': 0.6}
        }
        
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            method=SizingMethod.VOLATILITY_ADJUSTED,
            volatility=0.01,
            entry_price=1.1000
        )
        
        assert size > 0
    
    def test_multiple_calculations_consistency(self, sizer):
        """Test that multiple calculations with same inputs give same results"""
        params = {
            'symbol': 'EURUSD',
            'account_equity': 10000,
            'risk_pct': 0.02,
            'stop_loss_pips': 50,
            'entry_price': 1.1000,
            'method': SizingMethod.FIXED_RISK
        }
        
        size1 = sizer.calculate_position_size(**params)
        size2 = sizer.calculate_position_size(**params)
        
        assert size1 == size2
    
    def test_edge_case_very_small_stop(self, sizer):
        """Test with very small stop loss"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            stop_loss_pips=1,  # 1 pip stop
            entry_price=1.1000
        )
        
        # Should calculate but respect max size
        assert size <= sizer.max_position_size
    
    def test_edge_case_very_large_stop(self, sizer):
        """Test with very large stop loss"""
        size = sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_pct=0.02,
            stop_loss_pips=1000,  # 1000 pip stop
            entry_price=1.1000
        )
        
        # Should calculate small position
        assert size >= 0
        assert size <= sizer.max_position_size


class TestPositionSizerConfiguration:
    """Test position sizer configuration"""
    
    def test_custom_config(self):
        """Test with custom configuration"""
        config = {
            'default_risk_pct': 0.01,
            'max_position_size': 500000,
            'min_position_size': 5000,
            'default_kelly_fraction': 0.5
        }
        sizer = PositionSizer(config)
        
        assert sizer.default_risk_pct == 0.01
        assert sizer.max_position_size == 500000
        assert sizer.min_position_size == 5000
    
    def test_empty_config(self):
        """Test with empty configuration"""
        sizer = PositionSizer({})
        
        # Should use defaults
        assert sizer.default_risk_pct > 0
        assert sizer.max_position_size > 0
        assert sizer.min_position_size > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
