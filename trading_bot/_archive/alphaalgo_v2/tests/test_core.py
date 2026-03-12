"""
Tests for core module
"""

import pytest
from datetime import datetime, timedelta
import uuid

from ..core.types import (
    Signal, SignalType, Order, OrderType, OrderStatus,
    Position, Trade, RiskDecision, RiskLevel, MarketData,
    ExecutionResult, EvolutionProposal, ProposalStatus,
)
from ..core.constants import (
    MAX_RISK_PER_TRADE, MAX_DAILY_LOSS, MAX_DRAWDOWN,
    TradingMode, SafetyLevel, MarketRegime,
)
from ..core.exceptions import (
    AlphaAlgoError, DataError, ExecutionError, RiskError,
    RiskLimitExceededError, ValidationError,
)


class TestSignal:
    """Tests for Signal type"""
    
    def test_signal_creation(self):
        """Test signal creation"""
        signal = Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            stop_loss=1.0800,
            take_profit=1.0950,
            timeframe="M15",
            source="test",
        )
        
        assert signal.symbol == "EURUSD"
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence == 0.75
    
    def test_signal_risk_reward(self):
        """Test risk/reward calculation"""
        signal = Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            stop_loss=1.0800,
            take_profit=1.0950,
            timeframe="M15",
            source="test",
        )
        
        rr = signal.risk_reward_ratio
        assert rr is not None
        assert rr == 2.0  # 100 pips TP / 50 pips SL
    
    def test_signal_expiry(self):
        """Test signal expiry"""
        # Expired signal
        expired_signal = Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            timeframe="M15",
            source="test",
            expires_at=datetime.now() - timedelta(minutes=5),
        )
        
        assert expired_signal.is_expired
        
        # Valid signal
        valid_signal = Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            timeframe="M15",
            source="test",
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        
        assert not valid_signal.is_expired


class TestOrder:
    """Tests for Order type"""
    
    def test_order_creation(self):
        """Test order creation"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0850,
        )
        
        assert order.symbol == "EURUSD"
        assert order.order_type == OrderType.MARKET
        assert order.volume == 0.1
        assert order.status == OrderStatus.PENDING


class TestPosition:
    """Tests for Position type"""
    
    def test_position_creation(self):
        """Test position creation"""
        position = Position(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            side=SignalType.BUY,
            volume=0.1,
            entry_price=1.0850,
            current_price=1.0860,
        )
        
        assert position.symbol == "EURUSD"
        assert position.volume == 0.1
    
    def test_position_profit(self):
        """Test position profit calculation"""
        position = Position(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            side=SignalType.BUY,
            volume=1.0,
            entry_price=1.0850,
            current_price=1.0860,
            profit=10.0,
        )
        
        assert position.profit == 10.0


class TestRiskDecision:
    """Tests for RiskDecision type"""
    
    def test_risk_decision_allowed(self):
        """Test allowed risk decision"""
        decision = RiskDecision(
            allowed=True,
            reason="Risk within limits",
            risk_level=RiskLevel.LOW,
        )
        
        assert decision.allowed
        assert decision.risk_level == RiskLevel.LOW
    
    def test_risk_decision_rejected(self):
        """Test rejected risk decision"""
        decision = RiskDecision(
            allowed=False,
            reason="Drawdown limit exceeded",
            risk_level=RiskLevel.CRITICAL,
        )
        
        assert not decision.allowed
        assert decision.risk_level == RiskLevel.CRITICAL


class TestConstants:
    """Tests for constants"""
    
    def test_immutable_limits(self):
        """Test immutable risk limits"""
        assert MAX_RISK_PER_TRADE == 0.02
        assert MAX_DAILY_LOSS == 0.05
        assert MAX_DRAWDOWN == 0.20
    
    def test_trading_modes(self):
        """Test trading modes"""
        assert TradingMode.LIVE.value == "live"
        assert TradingMode.PAPER.value == "paper"
        assert TradingMode.BACKTEST.value == "backtest"
    
    def test_safety_levels(self):
        """Test safety levels"""
        assert SafetyLevel.GREEN.value == "green"
        assert SafetyLevel.BLACK.value == "black"


class TestExceptions:
    """Tests for exceptions"""
    
    def test_base_exception(self):
        """Test base exception"""
        error = AlphaAlgoError("Test error", code="TEST_ERROR")
        
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.code == "TEST_ERROR"
    
    def test_data_error(self):
        """Test data error"""
        error = DataError("Data fetch failed", symbol="EURUSD", source="yahoo")
        
        assert error.symbol == "EURUSD"
        assert error.source == "yahoo"
    
    def test_risk_error(self):
        """Test risk error"""
        error = RiskLimitExceededError(
            "Risk limit exceeded",
            risk_type="daily_loss",
            current_value=0.06,
            limit_value=0.05,
        )
        
        assert error.risk_type == "daily_loss"
        assert error.current_value == 0.06


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
