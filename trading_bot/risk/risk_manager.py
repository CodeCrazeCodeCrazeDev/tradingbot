"""
Dummy risk_manager.py for backward compatibility.

This file exists to satisfy imports from other modules.
All functionality has been consolidated into MASTER_risk_manager.py
"""

# Re-export from MASTER risk manager
from trading_bot.risk.MASTER_risk_manager import (
    MasterRiskManager as RiskManager,
    TradeDirection,
    TradeQuality,
    RiskMode,
    MarketRegime,
    TradingStats,
    PositionSize,
    RiskAssessment,
    RiskLimits,
    create_risk_manager
)

__all__ = [
    'RiskManager',
    'TradeDirection',
    'TradeQuality',
    'RiskMode',
    'MarketRegime',
    'TradingStats',
    'PositionSize',
    'RiskAssessment',
    'RiskLimits',
    'create_risk_manager'
]
