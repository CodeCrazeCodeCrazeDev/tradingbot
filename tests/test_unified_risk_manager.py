"""
Unit tests for Unified Risk Manager
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.risk.unified_risk_manager import UnifiedRiskManager, MockRiskManager


class TestUnifiedRiskManager:
    """Test suite for UnifiedRiskManager."""
    
    def test_initialization_with_config(self):
        """Test initialization with config dict."""
        config = {
            'max_drawdown_pct': 20.0,
            'risk_per_trade_pct': 1.0,
            'max_lots': 1.0
        }
        
        rm = UnifiedRiskManager(config=config)
        
        assert rm is not None
        assert rm.config == config
        assert rm._implementation_type in ['MT5-based', 'Config-based', 'Mock']
    
    def test_initialization_without_params(self):
        """Test initialization without parameters."""
        rm = UnifiedRiskManager()
        
        assert rm is not None
        assert rm._implementation_type in ['MT5-based', 'Config-based', 'Mock']
    
    def test_compute_approved_lots(self):
        """Test lot size calculation and capping."""
        rm = UnifiedRiskManager(config={'max_lots': 1.0})
        
        # Test normal calculation
        lots = rm.compute_approved_lots(
            symbol='EURUSD',
            entry_price=1.1000,
            stop_loss=1.0980
        )
        
        assert lots > 0
        assert lots <= 1.0
    
    def test_compute_approved_lots_capping(self):
        """Test that lots are capped at maximum."""
        rm = UnifiedRiskManager(config={'max_lots': 0.5})
        
        # Request large position
        lots = rm.compute_approved_lots(
            symbol='EURUSD',
            entry_price=1.1000,
            stop_loss=1.0999  # Tight stop
        )
        
        # Should be capped at max_lots
        assert lots <= 0.5
    
    def test_compute_approved_lots_minimum(self):
        """Test that lots have minimum value."""
        rm = UnifiedRiskManager(config={'max_lots': 1.0, 'risk_per_trade_pct': 0.01})
        
        # Request tiny position
        lots = rm.compute_approved_lots(
            symbol='EURUSD',
            entry_price=1.1000,
            stop_loss=1.0000  # Wide stop
        )
        
        # Should have minimum value
        assert lots >= 0.01
    
    def test_check_drawdown(self):
        """Test drawdown check."""
        rm = UnifiedRiskManager(config={})
        
        # Should return True for mock implementation
        result = rm.check_drawdown()
        assert result is True
    
    def test_get_account_status(self):
        """Test account status retrieval."""
        rm = UnifiedRiskManager(config={})
        
        status = rm.get_account_status()
        
        assert isinstance(status, dict)
        assert 'max_drawdown_pct' in status
        assert 'max_lots' in status


class TestMockRiskManager:
    """Test suite for MockRiskManager."""
    
    def test_initialization(self):
        """Test mock risk manager initialization."""
        config = {
            'max_drawdown_pct': 20.0,
            'risk_per_trade_pct': 1.0,
            'max_lots': 1.0
        }
        
        mock_rm = MockRiskManager(config)
        
        assert mock_rm.max_drawdown_pct == 20.0
        assert mock_rm.risk_per_trade_pct == 1.0
        assert mock_rm.max_lots == 1.0
    
    def test_calc_position_size(self):
        """Test position size calculation."""
        mock_rm = MockRiskManager({'risk_per_trade_pct': 1.0, 'max_lots': 1.0})
        
        result = mock_rm.calc_position_size(
            symbol='EURUSD',
            stop_loss_pips=20.0
        )
        
        # Result is a float
        assert isinstance(result, float)
        assert result > 0
        assert result <= 1.0
    
    def test_calc_position_size_respects_max_lots(self):
        """Test that position size respects max lots."""
        mock_rm = MockRiskManager({'risk_per_trade_pct': 10.0, 'max_lots': 0.5})
        
        result = mock_rm.calc_position_size(
            symbol='EURUSD',
            stop_loss_pips=10.0  # Tight stop with high risk
        )
        
        # Should be capped at max_lots
        assert result <= 0.5
    
    def test_check_drawdown_always_true(self):
        """Test that mock always allows trading."""
        mock_rm = MockRiskManager({})
        
        assert mock_rm.check_drawdown() is True
    
    def test_get_account_status(self):
        """Test mock account status."""
        mock_rm = MockRiskManager({})
        
        status = mock_rm.get_account_status()
        
        assert isinstance(status, dict)
        assert 'max_drawdown_pct' in status
        assert 'max_lots' in status


class TestIntegration:
    """Integration tests for UnifiedRiskManager."""
    
    def test_calculate_position_size_alias(self):
        """Test that calculate_position_size works as alias."""
        rm = UnifiedRiskManager(config={'max_lots': 1.0})
        
        # Both methods should work
        result1 = rm.calculate_max_position_size(
            symbol='EURUSD',
            account_balance=10000.0,
            risk_per_trade=1.0
        )
        
        # Should return valid result
        assert result1 > 0
    
    def test_error_handling(self):
        """Test error handling in compute_approved_lots."""
        rm = UnifiedRiskManager(config={})
        
        # Should not crash with invalid inputs
        try:
            lots = rm.compute_approved_lots(
                symbol='INVALID',
                entry_price=1.0,
                stop_loss=1.0  # Same as entry - edge case
            )
            # Should return safe minimum
            assert lots >= 0.01
        except Exception as e:
            pytest.fail(f"Should handle errors gracefully: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
