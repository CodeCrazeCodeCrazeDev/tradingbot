"""
improvements package
"""

try:
    from .drawdown_recovery import (
        DrawdownRecoveryManager,
        PerformanceSnapshot,
        PerformanceTracker,
        RecoveryMode,
        RecoveryPlan,
        TradingState
    )
    from .entry_optimizer import (
        EntryOpportunity,
        EntryOptimizer,
        EntryQuality,
        LiquidityZoneFinder,
        PriceZone,
        PullbackDetector,
        ZoneType
    )
    from .exit_strategies import (
        AdvancedExitManager,
        ExitLevel,
        ExitReason,
        PartialProfitTaker,
        PositionExitPlan,
        TimeBasedExitManager,
        TrailingStopManager,
        TrailingStopType
    )
    from .improvement_orchestrator import ImprovementOrchestrator, TradeValidationResult, create_improvement_system
    from .market_regime import (
        MarketRegime,
        MarketRegimeDetector,
        MomentumRegime,
        RegimeType,
        VolatilityRegime
    )
    from .news_filter import (
        EconomicCalendar,
        EconomicEvent,
        EventType,
        NewsEventFilter,
        NewsFilterResult,
        NewsImpact
    )
    from .position_sizing import (
        DynamicPositionSizer,
        KellyCriterion,
        PositionSizeResult,
        SizingMode,
        VolatilityAdjustedSizer
    )
    from .session_spread_filter import (
        SessionFilter,
        SessionInfo,
        SpreadFilter,
        SpreadInfo,
        TradingSession,
        TradingTimeFilter
    )
    from .signal_enhancement import (
        MarketStructureValidator,
        MultiTimeframeAnalyzer,
        SignalEnhancementResult,
        SignalEnhancer,
        SignalStrength,
        TimeframeAnalysis,
        TrendDirection,
        VolumeConfirmation
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in improvements: {e}')

__all__ = [
    'AdvancedExitManager',
    'DrawdownRecoveryManager',
    'DynamicPositionSizer',
    'EconomicCalendar',
    'EconomicEvent',
    'EntryOpportunity',
    'EntryOptimizer',
    'EntryQuality',
    'EventType',
    'ExitLevel',
    'ExitReason',
    'ImprovementOrchestrator',
    'KellyCriterion',
    'LiquidityZoneFinder',
    'MarketRegime',
    'MarketRegimeDetector',
    'MarketStructureValidator',
    'MomentumRegime',
    'MultiTimeframeAnalyzer',
    'NewsEventFilter',
    'NewsFilterResult',
    'NewsImpact',
    'PartialProfitTaker',
    'PerformanceSnapshot',
    'PerformanceTracker',
    'PositionExitPlan',
    'PositionSizeResult',
    'PriceZone',
    'PullbackDetector',
    'RecoveryMode',
    'RecoveryPlan',
    'RegimeType',
    'SessionFilter',
    'SessionInfo',
    'SignalEnhancementResult',
    'SignalEnhancer',
    'SignalStrength',
    'SizingMode',
    'SpreadFilter',
    'SpreadInfo',
    'TimeBasedExitManager',
    'TimeframeAnalysis',
    'TradeValidationResult',
    'TradingSession',
    'TradingState',
    'TradingTimeFilter',
    'TrailingStopManager',
    'TrailingStopType',
    'TrendDirection',
    'VolatilityAdjustedSizer',
    'VolatilityRegime',
    'VolumeConfirmation',
    'ZoneType',
    'create_improvement_system',
]