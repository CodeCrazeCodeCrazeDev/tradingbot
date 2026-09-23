"""
Unit Tests for Risk Validation Gate
====================================

Comprehensive test suite for the centralized risk validation system.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.validation import (
    RiskValidationGate,
    ValidationResponse,
    get_validation_gate
)


class TestRiskValidationGate:
    """Test suite for Risk Validation Gate."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'max_risk_per_trade': 0.02,
            'max_portfolio_risk': 0.05,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.25,
            'emergency_drawdown': 0.30,
            'max_open_positions': 10
        }
        self.gate = RiskValidationGate(config=self.config)
    
    def test_initialization(self):
        """Test validation gate initialization."""
        assert self.gate is not None
        assert self.gate.emergency_shutdown == False
        assert self.gate.daily_loss == 0.0
        assert len(self.gate.open_positions) == 0
    
    def test_valid_trade_approval(self):
        """Test approval of valid trade."""
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert isinstance(result, ValidationResponse)
        assert result.approved == True
        assert len(result.reasons) == 0
    
    def test_excessive_risk_rejection(self):
        """Test rejection of excessive risk."""
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=1.0,
            risk_amount=500,
            risk_percent=0.05,  # 5% - exceeds 2% limit
            direction="LONG"
        )
        
        assert result.approved == False
        assert len(result.reasons) > 0
        assert any("Risk per trade too high" in r for r in result.reasons)
    
    def test_emergency_shutdown_rejection(self):
        """Test rejection during emergency shutdown."""
        self.gate.emergency_shutdown = True
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert result.risk_score == 100.0
        assert any("EMERGENCY SHUTDOWN" in r for r in result.reasons)
    
    def test_drawdown_limit_rejection(self):
        """Test rejection when drawdown limit exceeded."""
        self.gate.current_drawdown = 0.26  # 26% - exceeds 25% limit
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Drawdown limit exceeded" in r for r in result.reasons)
    
    def test_emergency_drawdown_triggers_shutdown(self):
        """Test emergency shutdown trigger at 30% drawdown."""
        self.gate.current_drawdown = 0.31  # 31% - exceeds emergency 30%
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert self.gate.emergency_shutdown == True
        assert result.approved == False
    
    def test_daily_loss_limit(self):
        """Test daily loss limit enforcement."""
        self.gate.daily_loss = 0.06  # 6% - exceeds 5% limit
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Daily loss limit" in r for r in result.reasons)
    
    def test_weekly_loss_limit(self):
        """Test weekly loss limit enforcement."""
        self.gate.weekly_loss = 0.11  # 11% - exceeds 10% limit
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Weekly loss limit" in r for r in result.reasons)
    
    def test_monthly_loss_limit(self):
        """Test monthly loss limit enforcement."""
        self.gate.monthly_loss = 0.21  # 21% - exceeds 20% limit
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Monthly loss limit" in r for r in result.reasons)
    
    def test_portfolio_risk_limit(self):
        """Test portfolio risk limit enforcement."""
        # Add existing positions
        for i in range(3):
            self.gate.open_positions[f"PAIR{i}"] = {'risk_pct': 0.015}
        
        # Total existing risk: 4.5%, new trade: 1.5%, total: 6% > 5% limit
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.015,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Portfolio risk limit" in r for r in result.reasons)
    
    def test_max_open_positions(self):
        """Test max open positions limit."""
        # Fill up to max positions
        for i in range(10):
            self.gate.open_positions[f"PAIR{i}"] = {'risk_pct': 0.005}
        
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Max open positions" in r for r in result.reasons)
    
    def test_invalid_position_size(self):
        """Test rejection of invalid position size."""
        result = self.gate.validate_trade(
            symbol="EURUSD",
            position_size=0,  # Invalid
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        assert result.approved == False
        assert any("Invalid position size" in r for r in result.reasons)
    
    def test_position_tracking(self):
        """Test position add/remove tracking."""
        # Add position
        self.gate.add_position("EURUSD", {'risk_pct': 0.01, 'size': 0.1})
        assert len(self.gate.open_positions) == 1
        assert "EURUSD" in self.gate.open_positions
        
        # Remove position
        self.gate.remove_position("EURUSD")
        assert len(self.gate.open_positions) == 0
    
    def test_loss_tracking(self):
        """Test loss update tracking."""
        initial_daily = self.gate.daily_loss
        
        self.gate.update_loss(loss_amount=100, loss_percent=0.01)
        
        assert self.gate.daily_loss == initial_daily + 0.01
        assert self.gate.weekly_loss == 0.01
        assert self.gate.monthly_loss == 0.01
    
    def test_drawdown_update(self):
        """Test drawdown update."""
        self.gate.update_drawdown(0.15)
        assert self.gate.current_drawdown == 0.15
    
    def test_status_reporting(self):
        """Test status reporting."""
        status = self.gate.get_status()
        
        assert 'emergency_shutdown' in status
        assert 'current_drawdown' in status
        assert 'daily_loss' in status
        assert 'open_positions' in status
        assert 'limits' in status
    
    def test_warning_approval(self):
        """Test approval with warnings."""
        # Add existing position for same symbol
        self.gate.add_position("EURUSD", {'risk_pct': 0.01})
        
        result = self.gate.validate_trade(
            symbol="EURUSD",  # Same symbol - warning
            position_size=0.1,
            risk_amount=100,
            risk_percent=0.01,
            direction="LONG"
        )
        
        # Should have warnings (approval depends on implementation)
        assert len(result.warnings) > 0
    
    def test_global_instance(self):
        """Test global validation gate instance."""
        gate1 = get_validation_gate()
        gate2 = get_validation_gate()
        
        # Should be same instance
        assert gate1 is gate2


class TestValidationResponse:
    """Test suite for ValidationResponse."""
    
    def test_response_creation(self):
        """Test validation response creation."""
        from trading_bot.validation.risk_validation_gate import ValidationResult
from typing import Set
        
response = ValidationResponse(
            result=ValidationResult.APPROVED,
            approved=True,
            reasons=[],
            warnings=[],
            risk_score=10.0,
            timestamp=datetime.now()
        )
        
        assert response.approved == True
        assert response.risk_score == 10.0
        assert len(response.reasons) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
