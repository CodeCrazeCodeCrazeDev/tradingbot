"""Unit tests for RiskManager position sizing and drawdown guard."""
from __future__ import annotations

import pytest
from types import SimpleNamespace

from trading_bot.risk.risk_manager import (
    RiskManager, 
    PositionSize, 
    RiskMode,
    TradeDirection,
    TradeQuality,
    MarketRegime,
    TradingStats,
    RiskAssessment,
    RiskLimits
)


def test_risk_manager_initialization() -> None:
    """Test RiskManager can be initialized."""
    rm = RiskManager()
    assert rm is not None


def test_position_size_dataclass() -> None:
    """Test PositionSize dataclass."""
    size = PositionSize(
        lot=0.1,
        risk_amount=100.0,
        risk_percent=0.02,
        stop_loss_pips=50.0,
        take_profit_pips=100.0
    )
    assert size.lot == 0.1
    assert size.risk_amount == 100.0
    assert size.risk_percent == 0.02


def test_risk_mode_enum() -> None:
    """Test RiskMode enum values."""
    assert RiskMode.CONSERVATIVE is not None
    assert RiskMode.STANDARD is not None
    assert RiskMode.AGGRESSIVE is not None
    assert RiskMode.RECOVERY is not None
    assert RiskMode.EMERGENCY is not None


def test_trade_direction_enum() -> None:
    """Test TradeDirection enum values."""
    assert TradeDirection.LONG is not None
    assert TradeDirection.SHORT is not None


def test_trade_quality_enum() -> None:
    """Test TradeQuality enum values."""
    assert TradeQuality.OPTIMAL is not None
    assert TradeQuality.STRONG is not None
    assert TradeQuality.STANDARD is not None
    assert TradeQuality.SPECULATIVE is not None


def test_market_regime_enum() -> None:
    """Test MarketRegime enum values."""
    assert MarketRegime.TRENDING_BULL is not None
    assert MarketRegime.TRENDING_BEAR is not None
    assert MarketRegime.RANGE_BOUND is not None
    assert MarketRegime.VOLATILE is not None
    assert MarketRegime.CRISIS is not None
    assert MarketRegime.NORMAL is not None


def test_trading_stats_dataclass() -> None:
    """Test TradingStats dataclass."""
    stats = TradingStats()
    assert stats.total_trades == 0
    assert stats.winning_trades == 0
    assert stats.win_rate == 0.0


def test_risk_limits_dataclass() -> None:
    """Test RiskLimits dataclass."""
    limits = RiskLimits()
    assert limits.max_risk_per_trade == 0.02
    assert limits.max_portfolio_risk == 0.05
    assert limits.max_open_positions == 10


def test_risk_assessment_dataclass() -> None:
    """Test RiskAssessment dataclass."""
    assessment = RiskAssessment(
        position_size=0.1,
        max_risk_per_trade=0.02,
        stop_loss=50.0,
        max_drawdown_expected=0.1,
        var_95=0.05,
        cvar_95=0.07,
        risk_of_ruin=0.01,
        risk_score=30.0,
        kelly_fraction=0.15,
        regime_adjustment=1.0
    )
    assert assessment.position_size == 0.1
    assert assessment.risk_score == 30.0
