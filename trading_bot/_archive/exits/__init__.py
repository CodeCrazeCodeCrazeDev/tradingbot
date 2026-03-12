"""Exits Module - Advanced Exit Strategies."""

try:
    from .advanced_exit_strategies import (
        AdvancedExitManager,
        TrailingStop,
        ChandelierExit,
        ParabolicSAR,
        TimeBasedExit,
        BreakevenManager,
        FixedStopLoss,
        ExitType,
        TrailingMethod,
        ExitReason,
        ExitLevel,
        ExitSignal,
        ExitPlan,
        TrailingStopState,
        calculate_trailing_stop,
        calculate_chandelier_exit,
        get_exit_recommendation
    )
except ImportError:
    AdvancedExitManager = None

__all__ = [
    'AdvancedExitManager',
    'TrailingStop',
    'ChandelierExit',
    'ParabolicSAR',
    'TimeBasedExit',
    'BreakevenManager',
    'FixedStopLoss',
    'ExitType',
    'TrailingMethod',
    'ExitReason',
    'ExitLevel',
    'ExitSignal',
    'ExitPlan',
    'TrailingStopState',
    'calculate_trailing_stop',
    'calculate_chandelier_exit',
    'get_exit_recommendation',
]
