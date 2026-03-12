"""
Comprehensive functional tests for risk_validation_gate module.
"""
import pytest
from datetime import datetime
from trading_bot.validation.risk_validation_gate import (
    RiskValidationGate, ValidationResult, ValidationResponse
)


class TestValidationResult:
    """Tests for ValidationResult enum."""
    
    def test_enum_values(self):
        """Test enum has expected values."""
        assert ValidationResult.APPROVED is not None
        assert ValidationResult.REJECTED is not None
        assert ValidationResult.WARNING is not None
    
    def test_enum_count(self):
        """Test enum has correct number of values."""
        assert len(list(ValidationResult)) == 3


class TestValidationResponse:
    """Tests for ValidationResponse dataclass."""
    
    def test_approved_response(self):
        """Test approved validation response."""
        response = ValidationResponse(
            result=ValidationResult.APPROVED,
            approved=True,
            reasons=[],
            warnings=[],
            risk_score=25.0,
            timestamp=datetime.now()
        )
        assert response.approved is True
        assert response.result == ValidationResult.APPROVED
        assert response.risk_score == 25.0
    
    def test_rejected_response(self):
        """Test rejected validation response."""
        response = ValidationResponse(
            result=ValidationResult.REJECTED,
            approved=False,
            reasons=["Risk too high"],
            warnings=[],
            risk_score=85.0,
            timestamp=datetime.now()
        )
        assert response.approved is False
        assert response.result == ValidationResult.REJECTED
        assert "Risk too high" in response.reasons
    
    def test_warning_response(self):
        """Test warning validation response."""
        response = ValidationResponse(
            result=ValidationResult.WARNING,
            approved=True,
            reasons=[],
            warnings=["High volatility"],
            risk_score=50.0,
            timestamp=datetime.now()
        )
        assert response.result == ValidationResult.WARNING
        assert "High volatility" in response.warnings
    
    def test_post_init_sets_approved(self):
        """Test __post_init__ sets approved based on result."""
        response = ValidationResponse(
            result=ValidationResult.APPROVED,
            approved=False,  # Will be overwritten
            reasons=[],
            warnings=[],
            risk_score=25.0,
            timestamp=datetime.now()
        )
        assert response.approved is True  # Should be True because result is APPROVED


class TestRiskValidationGate:
    """Tests for RiskValidationGate class."""
    
    def test_initialization_default(self):
        """Test initialization with default config."""
        gate = RiskValidationGate()
        assert gate is not None
        assert gate.max_risk_per_trade == 0.02
        assert gate.max_portfolio_risk == 0.05
        assert gate.max_daily_loss == 0.05
        assert gate.max_drawdown == 0.25
        assert gate.emergency_shutdown is False
    
    def test_initialization_custom_config(self):
        """Test initialization with custom config."""
        config = {
            'max_risk_per_trade': 0.01,
            'max_portfolio_risk': 0.03,
            'max_daily_loss': 0.03,
            'max_open_positions': 5
        }
        gate = RiskValidationGate(config=config)
        assert gate.max_risk_per_trade == 0.01
        assert gate.max_portfolio_risk == 0.03
        assert gate.max_daily_loss == 0.03
        assert gate.max_open_positions == 5
    
    def test_validate_trade_success(self):
        """Test successful trade validation."""
        gate = RiskValidationGate()
        
        response = gate.validate_trade(
            symbol='EURUSD',
            position_size=0.1,
            risk_amount=100.0,
            risk_percent=0.01,  # 1% risk
            direction='BUY'
        )
        
        assert response is not None
        assert isinstance(response, ValidationResponse)
    
    def test_state_tracking(self):
        """Test state tracking initialization."""
        gate = RiskValidationGate()
        
        assert gate.daily_loss == 0.0
        assert gate.weekly_loss == 0.0
        assert gate.monthly_loss == 0.0
        assert gate.current_drawdown == 0.0
        assert gate.open_positions == {}
    
    def test_time_tracking(self):
        """Test time tracking initialization."""
        gate = RiskValidationGate()
        
        assert gate.last_daily_reset is not None
        assert gate.last_weekly_reset is not None
        assert gate.last_monthly_reset is not None
        assert isinstance(gate.last_daily_reset, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
