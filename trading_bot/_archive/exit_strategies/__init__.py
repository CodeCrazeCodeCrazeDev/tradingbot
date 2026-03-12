"""
exit_strategies package
"""

try:
    from .adaptive_exits import (
        AdaptiveExitStrategy,
        FibonacciExitLevels,
        TimeBasedExit,
        VolatilityBasedExit
    )
    from .dynamic_management import (
        DynamicTradeManager,
        PartialExitRule,
        PartialExitStrategy,
        ScaleLevel,
        ScaledExitStrategy,
        TradeHealth
    )
    from .exit_signal_generator import (
        ExitConfirmation,
        ExitSignalGenerator,
        ExitStrength,
        MultiTimeframeExitAnalyzer
    )
    from .exit_strategy import (
        BreakEven,
        ExitReason,
        ExitSignal,
        ExitStrategy,
        ExitType,
        TakeProfit,
        TrailingStop
    )
    from .profit_maximizer import (
        MarketCondition,
        MarketConditionExit,
        MaximizationStrategy,
        ProfitMaximizer,
        RiskRewardOptimizer
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in exit_strategies: {e}')

__all__ = [
    'AdaptiveExitStrategy',
    'BreakEven',
    'DynamicTradeManager',
    'ExitConfirmation',
    'ExitReason',
    'ExitSignal',
    'ExitSignalGenerator',
    'ExitStrategy',
    'ExitStrength',
    'ExitType',
    'FibonacciExitLevels',
    'MarketCondition',
    'MarketConditionExit',
    'MaximizationStrategy',
    'MultiTimeframeExitAnalyzer',
    'PartialExitRule',
    'PartialExitStrategy',
    'ProfitMaximizer',
    'RiskRewardOptimizer',
    'ScaleLevel',
    'ScaledExitStrategy',
    'TakeProfit',
    'TimeBasedExit',
    'TradeHealth',
    'TrailingStop',
    'VolatilityBasedExit',
]