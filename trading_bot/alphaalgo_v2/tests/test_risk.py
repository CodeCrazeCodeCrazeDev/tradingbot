"""
Tests for risk engine
"""

import pytest
import uuid
from datetime import datetime

from ..core.types import Signal, SignalType, Position, Trade, RiskLevel
from ..core.constants import MAX_RISK_PER_TRADE, MAX_DAILY_LOSS, MAX_DRAWDOWN
from ..risk_engine.engine import RiskEngine
from ..risk_engine.position.sizer import PositionSizer, SizingMethod
from ..risk_engine.portfolio.manager import PortfolioRiskManager


import logging

logger = logging.getLogger(__name__)

class TestPositionSizer:
    """Tests for PositionSizer"""
    
    @pytest.fixture
    def sizer(self):
        return PositionSizer({
            "risk_per_trade": 0.02,
            "max_position_size": 0.10,
        })
    
    @pytest.fixture
    def signal(self):
        return Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            stop_loss=1.0800,  # 50 pips
            take_profit=1.0950,  # 100 pips
            timeframe="M15",
            source="test",
        )
    
    def test_fixed_sizing(self, sizer, signal):
        """Test fixed sizing"""
        try:
            result = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.FIXED,
            )
        
            assert result.size > 0
            assert result.method == SizingMethod.FIXED
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_fixed_sizing: {e}")
            raise
    
    def test_fixed_fractional_sizing(self, sizer, signal):
        """Test fixed fractional sizing"""
        try:
            result = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.FIXED_FRACTIONAL,
            )
        
            assert result.size > 0
            assert result.method == SizingMethod.FIXED_FRACTIONAL
            assert result.risk_percent <= 0.02  # Max 2% risk
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_fixed_fractional_sizing: {e}")
            raise
    
    def test_kelly_sizing(self, sizer, signal):
        """Test Kelly criterion sizing"""
        try:
            result = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.KELLY,
                win_rate=0.55,
                avg_win=100,
                avg_loss=50,
            )
        
            assert result.size >= 0
            assert result.method == SizingMethod.KELLY
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_kelly_sizing: {e}")
            raise
    
    def test_volatility_sizing(self, sizer, signal):
        """Test volatility-adjusted sizing"""
        # Low volatility
        try:
            result_low = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.VOLATILITY,
                volatility=0.5,
            )
        
            # High volatility
            result_high = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.VOLATILITY,
                volatility=2.0,
            )
        
            # Size should be larger in low volatility
            assert result_low.size > result_high.size
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_volatility_sizing: {e}")
            raise
    
    def test_max_position_size(self, sizer, signal):
        """Test max position size limit"""
        try:
            result = sizer.calculate(
                signal=signal,
                account_balance=10000,
                method=SizingMethod.FIXED_FRACTIONAL,
            )
        
            # Should not exceed 10% of account
            max_size = 10000 * 0.10
            assert result.size <= max_size
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_max_position_size: {e}")
            raise


class TestPortfolioRiskManager:
    """Tests for PortfolioRiskManager"""
    
    @pytest.fixture
    def manager(self):
        return PortfolioRiskManager({
            "initial_balance": 10000,
            "max_daily_loss": 0.05,
            "max_drawdown": 0.20,
            "max_positions": 5,
        })
    
    def test_update_balance(self, manager):
        """Test balance update"""
        try:
            manager.update_balance(10500)
        
            metrics = manager.get_metrics()
            assert metrics.daily_pnl == 500
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_update_balance: {e}")
            raise
    
    def test_validate_new_position_allowed(self, manager):
        """Test position validation - allowed"""
        try:
            decision = manager.validate_new_position(
                symbol="EURUSD",
                size=0.1,
                price=1.0850,
            )
        
            assert decision.allowed
            assert decision.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_new_position_allowed: {e}")
            raise
    
    def test_validate_new_position_max_positions(self, manager):
        """Test position validation - max positions"""
        # Add 5 positions
        try:
            for i in range(5):
                position = Position(
                    id=str(uuid.uuid4()),
                    symbol=f"PAIR{i}",
                    side=SignalType.BUY,
                    volume=0.1,
                    entry_price=1.0,
                    current_price=1.0,
                )
                manager.update_position(position)
        
            # Try to add 6th
            decision = manager.validate_new_position(
                symbol="PAIR5",
                size=0.1,
                price=1.0,
            )
        
            assert not decision.allowed
            assert "Maximum positions" in decision.reason
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_new_position_max_positions: {e}")
            raise
    
    def test_validate_new_position_daily_loss(self, manager):
        """Test position validation - daily loss limit"""
        # Simulate large loss
        try:
            manager.update_balance(9400)  # 6% loss
        
            decision = manager.validate_new_position(
                symbol="EURUSD",
                size=0.1,
                price=1.0850,
            )
        
            assert not decision.allowed
            assert "Daily loss" in decision.reason
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_new_position_daily_loss: {e}")
            raise
    
    def test_check_limits(self, manager):
        """Test limit checking"""
        try:
            limits = manager.check_limits()
        
            assert "max_daily_loss" in limits
            assert "max_drawdown" in limits
            assert "max_positions" in limits
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_check_limits: {e}")
            raise
    
    def test_get_metrics(self, manager):
        """Test metrics calculation"""
        try:
            metrics = manager.get_metrics()
        
            assert metrics.total_exposure >= 0
            assert metrics.position_count >= 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_get_metrics: {e}")
            raise


class TestRiskEngine:
    """Tests for RiskEngine"""
    
    @pytest.fixture
    def engine(self):
        return RiskEngine({
            "initial_balance": 10000,
        })
    
    @pytest.fixture
    def signal(self):
        return Signal(
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
    
    def test_validate_trade_allowed(self, engine, signal):
        """Test trade validation - allowed"""
        try:
            decision = engine.validate_trade(signal, position_size=0.1)
        
            assert decision.allowed
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_trade_allowed: {e}")
            raise
    
    def test_validate_trade_expired_signal(self, engine):
        """Test trade validation - expired signal"""
        try:
            from datetime import timedelta
        
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
        
            decision = engine.validate_trade(expired_signal, position_size=0.1)
        
            assert not decision.allowed
            assert "expired" in decision.reason.lower()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_trade_expired_signal: {e}")
            raise
    
    def test_validate_trade_trading_disabled(self, engine, signal):
        """Test trade validation - trading disabled"""
        try:
            engine.disable_trading()
        
            decision = engine.validate_trade(signal, position_size=0.1)
        
            assert not decision.allowed
            assert "disabled" in decision.reason.lower()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_validate_trade_trading_disabled: {e}")
            raise
    
    def test_get_position_size(self, engine, signal):
        """Test position size calculation"""
        try:
            size = engine.get_position_size(signal, account_balance=10000)
        
            assert size > 0
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_get_position_size: {e}")
            raise
    
    def test_update_trade(self, engine):
        """Test trade update"""
        try:
            trade = Trade(
                id=str(uuid.uuid4()),
                symbol="EURUSD",
                side=SignalType.BUY,
                volume=0.1,
                entry_price=1.0850,
                exit_price=1.0900,
                profit=50.0,
                opened_at=datetime.now(),
                closed_at=datetime.now(),
            )
        
            engine.update_trade(trade)
        
            summary = engine.get_risk_summary()
            assert summary["statistics"]["trades_today"] == 1
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_update_trade: {e}")
            raise
    
    def test_emergency_close(self, engine):
        """Test emergency close"""
        try:
            result = engine.emergency_close_all()
        
            assert result is True
            assert engine._emergency_mode is True
            assert engine._trading_enabled is False
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_emergency_close: {e}")
            raise
    
    def test_enable_disable_trading(self, engine):
        """Test enable/disable trading"""
        try:
            engine.disable_trading()
            assert engine._trading_enabled is False
        
            engine.enable_trading()
            assert engine._trading_enabled is True
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_enable_disable_trading: {e}")
            raise
    
    def test_check_limits(self, engine):
        """Test limit checking"""
        try:
            limits = engine.check_limits()
        
            assert "max_daily_loss" in limits
            assert "max_drawdown" in limits
            assert "trading_disabled" in limits
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_check_limits: {e}")
            raise
    
    def test_risk_summary(self, engine):
        """Test risk summary"""
        try:
            summary = engine.get_risk_summary()
        
            assert "risk_level" in summary
            assert "trading_enabled" in summary
            assert "account" in summary
            assert "statistics" in summary
            assert "portfolio" in summary
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in test_risk_summary: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
