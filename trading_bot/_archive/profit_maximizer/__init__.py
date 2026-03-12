"""
profit_maximizer package
"""

try:
    from .brain_integration import ProfitMaximizerBrainWrapper, integrate_with_brain
    from .market_regime_adapter import MarketRegime, MarketRegimeAdapter, RegimeAnalysis
    from .profit_maximizer_core import (
        ConfluenceLevel,
        ConfluenceSignal,
        DynamicProfitTargets,
        EntryQuality,
        EntryTiming,
        LossRecoveryMode,
        ProfitMaximizerSystem,
        ProfitTarget,
        RecoveryMode,
        RecoveryState,
        SessionFilter,
        SessionQuality,
        SessionQualityResult,
        SignalConfluenceScorer,
        SmartEntryTimer,
        StreakMode,
        StreakState,
        TradeDecision,
        WinStreakOptimizer,
        quick_start
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in profit_maximizer: {e}')

__all__ = [
    'ConfluenceLevel',
    'ConfluenceSignal',
    'DynamicProfitTargets',
    'EntryQuality',
    'EntryTiming',
    'LossRecoveryMode',
    'MarketRegime',
    'MarketRegimeAdapter',
    'ProfitMaximizerBrainWrapper',
    'ProfitMaximizerSystem',
    'ProfitTarget',
    'RecoveryMode',
    'RecoveryState',
    'RegimeAnalysis',
    'SessionFilter',
    'SessionQuality',
    'SessionQualityResult',
    'SignalConfluenceScorer',
    'SmartEntryTimer',
    'StreakMode',
    'StreakState',
    'TradeDecision',
    'WinStreakOptimizer',
    'integrate_with_brain',
    'quick_start',
]