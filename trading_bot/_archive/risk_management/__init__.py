"""
risk_management package
"""

try:
    from .black_swan_protection import (
        BlackSwanAlert,
        BlackSwanEventType,
        BlackSwanProtector,
        EmergencyProtocol,
        HedgingStrategy,
        ProtectionLevel,
        TailRiskAnalyzer,
        TailRiskMetrics
    )
    from .drawdown_ladder import DrawdownLadder, DrawdownLevel
    from .portfolio_manager import (
        Allocation,
        CorrelationMatrix,
        Exposure,
        Portfolio,
        PortfolioManager,
        PortfolioMetrics,
        Position
    )
    from .position_sizing import (
        FixedFractionalSizer,
        KellyCalculator,
        OptimalFSizer,
        PositionSize,
        PositionSizer,
        RiskParitySizer,
        SizingMethod,
        VolatilityBasedSizer
    )
    from .risk_engine import (
        PortfolioRisk,
        RiskAlert,
        RiskEngine,
        RiskLevel,
        RiskLimits,
        RiskMetrics,
        TradeRisk
    )
    from .risk_monitor import (
        DrawdownMonitor,
        RiskEvent,
        RiskEventType,
        RiskMonitor,
        RiskThreshold,
        StressTest,
        VaRCalculator
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in risk_management: {e}')

__all__ = [
    'Allocation',
    'BlackSwanAlert',
    'BlackSwanEventType',
    'BlackSwanProtector',
    'CorrelationMatrix',
    'DrawdownLadder',
    'DrawdownLevel',
    'DrawdownMonitor',
    'EmergencyProtocol',
    'Exposure',
    'FixedFractionalSizer',
    'HedgingStrategy',
    'KellyCalculator',
    'OptimalFSizer',
    'Portfolio',
    'PortfolioManager',
    'PortfolioMetrics',
    'PortfolioRisk',
    'Position',
    'PositionSize',
    'PositionSizer',
    'ProtectionLevel',
    'RiskAlert',
    'RiskEngine',
    'RiskEvent',
    'RiskEventType',
    'RiskLevel',
    'RiskLimits',
    'RiskMetrics',
    'RiskMonitor',
    'RiskParitySizer',
    'RiskThreshold',
    'SizingMethod',
    'StressTest',
    'TailRiskAnalyzer',
    'TailRiskMetrics',
    'TradeRisk',
    'VaRCalculator',
    'VolatilityBasedSizer',
]