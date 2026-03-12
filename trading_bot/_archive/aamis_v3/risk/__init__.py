"""
risk package
"""

try:
    from .advanced_risk_management import (
        AdaptiveLeverageManager,
        AdvancedRiskManagementSystem,
        AllocationMethod,
        KellyCalculator,
        MarketRegime,
        PositionPyramider,
        PositionSizing,
        RegimeVaRCalculator,
        RiskLevel,
        RiskMetrics,
        SlippageModeler,
        SmartCapitalAllocator,
        SpreadModeler,
        StopLossOptimization,
        StopLossOptimizer,
        TailRiskHedger,
        TradeSequencer,
        VolatilityTargeter
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in risk: {e}')

__all__ = [
    'AdaptiveLeverageManager',
    'AdvancedRiskManagementSystem',
    'AllocationMethod',
    'KellyCalculator',
    'MarketRegime',
    'PositionPyramider',
    'PositionSizing',
    'RegimeVaRCalculator',
    'RiskLevel',
    'RiskMetrics',
    'SlippageModeler',
    'SmartCapitalAllocator',
    'SpreadModeler',
    'StopLossOptimization',
    'StopLossOptimizer',
    'TailRiskHedger',
    'TradeSequencer',
    'VolatilityTargeter',
]