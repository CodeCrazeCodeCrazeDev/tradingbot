"""One-wave compatibility facade for the legacy risk manager API.

New runtime code must use ``CanonicalRiskService``. The legacy surface remains
available for callers during convergence and emits a deprecation warning when
instantiated.
"""

import warnings

from trading_bot.risk.service import CanonicalRiskService
from trading_bot.risk.MASTER_risk_manager import (
    MasterRiskManager,
    TradeDirection,
    TradeQuality,
    RiskMode,
    MarketRegime,
    TradingStats,
    PositionSize,
    RiskAssessment,
    RiskLimits,
    create_risk_manager as _legacy_create_risk_manager
)


class RiskManager(MasterRiskManager):
    """Deprecated legacy API; use ``CanonicalRiskService`` for new code."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "RiskManager is a one-wave compatibility facade; use CanonicalRiskService.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


def create_risk_manager(*args, **kwargs):
    """Create the legacy manager for compatibility with a deprecation warning."""
    warnings.warn(
        "create_risk_manager is deprecated; inject CanonicalRiskService instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return RiskManager(*args, **kwargs)


__all__ = [
    'CanonicalRiskService',
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
