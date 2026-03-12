"""
Unit Tests for MASTER Risk Manager
===================================

Comprehensive test suite for the consolidated MASTER risk management system.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.risk import (
    MasterRiskManager,
    TradeDirection,
    TradeQuality,
    RiskMode,
    MarketRegime,
    TradingStats,
    PositionSize,
    RiskLimits
)


class TestMasterRiskManager:
    """Test suite for MASTER Risk Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'max_risk_per_trade': 0.02,
            'max_portfolio_risk': 0.05,
            'max_drawdown_limit': 0.25,
            'equity': 10000,
            'balance': 10000
        }
        self.rm = MasterRiskManager(config=self.config)
    
    def test_initialization(self):
        """Test risk manager initialization."""
        assert self.rm is not None
        assert self.rm.risk_mode == RiskMode.STANDARD
        assert self.rm.market_regime == MarketRegime.NORMAL
        assert self.rm.emergency_shutdown == False
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        position = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            direction=TradeDirection.LONG,
            quality=TradeQuality.OPTIMAL,
            confidence=0.85
        )
        
        assert isinstance(position, PositionSize)
        assert position.lot >= 0
        assert position.risk_percent <= self.config['max_risk_per_trade']
        assert position.stop_loss_pips == 20
    
    def test_risk_mode_adjustment(self):
        """Test risk mode changes."""
        # Test conservative mode
        self.rm.set_risk_mode(RiskMode.CONSERVATIVE)
        assert self.rm.risk_mode == RiskMode.CONSERVATIVE
        
        position_conservative = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            direction=TradeDirection.LONG,
            quality=TradeQuality.STANDARD
        )
        
        # Test aggressive mode
        self.rm.set_risk_mode(RiskMode.AGGRESSIVE)
        position_aggressive = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            direction=TradeDirection.LONG,
            quality=TradeQuality.STANDARD
        )
        
        # Aggressive should have larger position (if not at limits)
        assert position_aggressive.risk_percent >= position_conservative.risk_percent
    
    def test_market_regime_adjustment(self):
        """Test market regime adjustments."""
        # Bull market - should increase risk
        self.rm.set_market_regime(MarketRegime.TRENDING_BULL)
        assert self.rm.market_regime == MarketRegime.TRENDING_BULL
        
        # Crisis - should decrease risk
        self.rm.set_market_regime(MarketRegime.CRISIS)
        assert self.rm.market_regime == MarketRegime.CRISIS
    
    def test_drawdown_protection(self):
        """Test drawdown protection."""
        # Simulate moderate drawdown
        self.rm.update_drawdown(10000)
        self.rm.peak_equity = 12000
        self.rm.update_drawdown(10000)
        
        assert self.rm.current_drawdown > 0
        
        # Simulate severe drawdown
        self.rm.update_drawdown(7500)  # 37.5% drawdown from peak
        
        # Should trigger emergency shutdown - position should be minimal
        position = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            direction=TradeDirection.LONG
        )
        
        # During emergency, position should be very small (minimum lot) or zero
        assert position.lot <= 0.01  # Minimal position in emergency
    
    def test_trade_quality_impact(self):
        """Test trade quality impact on position sizing."""
        optimal = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            quality=TradeQuality.OPTIMAL
        )
        
        speculative = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            quality=TradeQuality.SPECULATIVE
        )
        
        # Optimal should have larger position
        assert optimal.risk_percent >= speculative.risk_percent
    
    def test_confidence_adjustment(self):
        """Test confidence-based position sizing."""
        high_confidence = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            confidence=0.95
        )
        
        low_confidence = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            confidence=0.50
        )
        
        # High confidence should have larger position
        assert high_confidence.risk_percent >= low_confidence.risk_percent
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Zero stop loss
        position = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=0
        )
        assert position.lot == 0
        assert "Invalid" in position.reason or "error" in position.reason.lower()
        
        # Negative confidence
        position = self.rm.calculate_position_size(
            symbol="EURUSD",
            stop_loss_pips=20,
            confidence=-0.5
        )
        # Should handle gracefully (clamp to 0)
        assert position.lot >= 0
    
    def test_risk_assessment(self):
        """Test risk assessment generation."""
        assessment = self.rm.get_risk_assessment()
        
        assert assessment is not None
        assert hasattr(assessment, 'risk_score')
        assert hasattr(assessment, 'kelly_fraction')
        assert hasattr(assessment, 'regime_adjustment')
        assert 0 <= assessment.risk_score <= 100
    
    def test_emergency_shutdown_reset(self):
        """Test emergency shutdown reset."""
        # Trigger emergency
        self.rm.emergency_shutdown = True
        
        # Reset
        self.rm.reset_emergency_shutdown()
        
        assert self.rm.emergency_shutdown == False
        assert self.rm.risk_mode == RiskMode.RECOVERY
    
    def test_trade_history_tracking(self):
        """Test trade history and statistics."""
        # Add some trades
        self.rm.add_trade({
            'profit': 100,
            'pips': 20,
            'symbol': 'EURUSD'
        })
        
        self.rm.add_trade({
            'profit': -50,
            'pips': -10,
            'symbol': 'GBPUSD'
        })
        
        assert len(self.rm.trade_history) == 2


class TestTradingStats:
    """Test suite for TradingStats."""
    
    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = TradingStats()
        
        assert stats.total_trades == 0
        assert stats.winning_trades == 0
        assert stats.losing_trades == 0
        assert stats.win_rate == 0.0
        assert stats.profit_factor == 0.0


class TestRiskLimits:
    """Test suite for RiskLimits."""
    
    def test_limits_initialization(self):
        """Test limits initialization with defaults."""
        limits = RiskLimits()
        
        assert limits.max_risk_per_trade == 0.02
        assert limits.max_portfolio_risk == 0.05
        assert limits.max_drawdown_limit == 0.25
        assert limits.max_daily_loss == 0.05
        assert limits.max_open_positions == 10
    
    def test_custom_limits(self):
        """Test custom limit values."""
        limits = RiskLimits(
            max_risk_per_trade=0.01,
            max_drawdown_limit=0.15
        )
        
        assert limits.max_risk_per_trade == 0.01
        assert limits.max_drawdown_limit == 0.15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
