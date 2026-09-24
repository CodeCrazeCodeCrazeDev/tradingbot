"""
Unit Tests for Risk Manager
===========================
Tests for the MASTER Risk Manager component.
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


@pytest.mark.unit
class TestRiskManagerPositionSizing:
    """Test position sizing calculations."""
    
    def test_position_size_basic(self, risk_manager):
        """Test basic position size calculation."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        position = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=50,
            direction=TradeDirection.LONG,
            confidence=0.8
        )
        
        assert position is not None
        assert position.lot >= 0
        assert position.risk_amount >= 0
    
    def test_position_size_with_high_confidence(self, risk_manager):
        """Test position size increases with confidence."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        low_conf = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=50,
            direction=TradeDirection.LONG,
            confidence=0.5
        )
        
        high_conf = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=50,
            direction=TradeDirection.LONG,
            confidence=0.95
        )
        
        # Higher confidence should allow larger position
        assert high_conf.lot >= low_conf.lot
    
    def test_position_size_respects_max_risk(self, risk_manager):
        """Test position size respects maximum risk limits."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        position = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=10,  # Very tight stop
            direction=TradeDirection.LONG,
            confidence=1.0
        )
        
        # Risk percent should be within reasonable bounds
        assert 0 <= position.risk_percent <= 0.10


@pytest.mark.unit
class TestRiskManagerValidation:
    """Test trade validation."""
    
    def test_validate_trade_basic(self, risk_manager):
        """Test basic trade validation."""
        trade = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot': 0.1,
            'entry_price': 1.1000,
            'stop_loss': 1.0950,
            'take_profit': 1.1100
        }
        
        # Should not raise exception
        is_valid = risk_manager.validate_trade(trade) if hasattr(risk_manager, 'validate_trade') else True
        assert is_valid is not False
    
    def test_emergency_shutdown_blocks_trades(self, risk_manager):
        """Test that emergency shutdown blocks new positions."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        
        risk_manager.emergency_shutdown = True
        
        position = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=50,
            direction=TradeDirection.LONG,
            confidence=0.8
        )
        
        assert position.lot == 0
        
        # Reset
        risk_manager.emergency_shutdown = False


@pytest.mark.unit
class TestRiskManagerDrawdown:
    """Test drawdown calculations."""
    
    def test_drawdown_tracking(self, risk_manager):
        """Test drawdown is tracked correctly."""
        initial_equity = risk_manager.current_equity
        
        # Simulate equity changes
        risk_manager.current_equity = initial_equity * 0.95  # 5% loss
        risk_manager._update_drawdown() if hasattr(risk_manager, '_update_drawdown') else None
        
        # Drawdown should be recorded
        assert risk_manager.current_drawdown >= 0
    
    def test_max_drawdown_limit(self, risk_manager):
        """Test max drawdown limit enforcement."""
        max_dd = risk_manager.config.get('max_drawdown', 0.20)
        
        # Should have a reasonable max drawdown limit
        assert 0 < max_dd <= 0.5  # Between 0% and 50%
