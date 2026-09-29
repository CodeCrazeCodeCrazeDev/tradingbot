import pytest
import pandas as pd
from trading_bot.risk.MASTER_risk_manager import MasterRiskManager, TradeQuality, RiskMode, MarketRegime

def test_risk_manager_drawdown_protection():
    """Verifies that the Risk Manager scales down or stops during high drawdown."""
    config = {"max_drawdown_limit": 0.2, "emergency_shutdown_drawdown": 0.3}
    risk_manager = MasterRiskManager(config=config)
    risk_manager.peak_equity = 10000

    # Normal state
    risk_manager.update_drawdown(10000)
    pos_normal = risk_manager.calculate_position_size("EURUSD", 20)
    assert pos_normal.lot > 0

    # Severe Drawdown (20%) - Should enter RECOVERY mode and reduce size
    risk_manager.update_drawdown(7500) # 25% DD
    pos_recovery = risk_manager.calculate_position_size("EURUSD", 20)
    assert risk_manager.risk_mode == RiskMode.RECOVERY
    assert pos_recovery.lot < pos_normal.lot

    # Emergency State (30%) - Should stop trading
    risk_manager.update_drawdown(6500) # 35% DD
    pos_emergency = risk_manager.calculate_position_size("EURUSD", 20)
    assert risk_manager.emergency_shutdown == True
    assert pos_emergency.lot == 0

def test_risk_manager_regime_awareness():
    """Verifies that risk is adjusted based on market regimes."""
    risk_manager = MasterRiskManager()

    # Bull market
    risk_manager.set_market_regime(MarketRegime.TRENDING_BULL)
    pos_bull = risk_manager.calculate_position_size("EURUSD", 20)

    # Volatile/Crisis market
    risk_manager.set_market_regime(MarketRegime.CRISIS)
    pos_crisis = risk_manager.calculate_position_size("EURUSD", 20)

    assert pos_crisis.lot < pos_bull.lot

def test_risk_manager_portfolio_limits():
    """Verifies that max portfolio risk limits are enforced."""
    config = {"max_portfolio_risk": 0.05}
    risk_manager = MasterRiskManager(config=config)

    # Simulate existing large positions
    risk_manager.open_positions = {
        "pos1": {"symbol": "GBPUSD", "risk_pct": 0.045}
    }

    # New trade that would exceed 5% total risk
    pos = risk_manager.calculate_position_size("EURUSD", 20, quality=TradeQuality.OPTIMAL)
    assert pos.lot == 0
    assert "Portfolio risk limit exceeded" in pos.reason
