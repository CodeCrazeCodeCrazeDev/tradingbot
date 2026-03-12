"""
awareness package
"""

try:
    from .edge_analytics_dashboard import (
        EdgeAnalysis,
        EdgeAnalyticsDashboard,
        EdgeAnalyzer,
        MetricType,
        MetricsCalculator,
        PerformanceMetrics,
        StrategyPerformance,
        TimeFrame
    )
    from .self_awareness import (
        AdvancedSelfAwarenessSystem,
        EdgeAnalyticsDashboard,
        EdgeMetric,
        EmotionalState,
        IdentityPersonalityModel,
        JournalEntry,
        MetaCognitionEngine,
        PersonalityTrait,
        SelfCriticismEngine,
        SelfCritique,
        SyntheticEmotionEngine,
        ThinkingMode,
        ThoughtProcess,
        TradingJournal
    )
    from .trading_journal import (
        AITradingJournal,
        MarketCondition,
        NarrativeGenerator,
        TradeAnalyzer,
        TradeEmotion,
        TradeEntry,
        TradeOutcome,
        TradingSession
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in awareness: {e}')

__all__ = [
    'AITradingJournal',
    'AdvancedSelfAwarenessSystem',
    'EdgeAnalysis',
    'EdgeAnalyticsDashboard',
    'EdgeAnalyzer',
    'EdgeMetric',
    'EmotionalState',
    'IdentityPersonalityModel',
    'JournalEntry',
    'MarketCondition',
    'MetaCognitionEngine',
    'MetricType',
    'MetricsCalculator',
    'NarrativeGenerator',
    'PerformanceMetrics',
    'PersonalityTrait',
    'SelfCriticismEngine',
    'SelfCritique',
    'StrategyPerformance',
    'SyntheticEmotionEngine',
    'ThinkingMode',
    'ThoughtProcess',
    'TimeFrame',
    'TradeAnalyzer',
    'TradeEmotion',
    'TradeEntry',
    'TradeOutcome',
    'TradingJournal',
    'TradingSession',
]