"""
event_monitoring package
"""

try:
    from .economic_calendar import (
        EconomicCalendar,
        EconomicEventImpact,
        EconomicEventResult,
        EconomicIndicator,
        ForecastAnalyzer,
        retry
    )
    from .event_monitor import (
        EconomicEvent,
        Event,
        EventMonitor,
        EventPriority,
        EventSource,
        EventType,
        MarketEvent,
        NewsEvent,
        SocialMediaEvent
    )
    from .event_processor import (
        EventFilter,
        EventHandler,
        EventPrioritizer,
        EventProcessor,
        EventResponseStrategy
    )
    from .market_condition_monitor import (
        CorrelationTracker,
        LiquidityState,
        MarketCondition,
        MarketConditionMonitor,
        MarketRegime,
        RegimeDetector,
        VolatilityState,
        retry
    )
    from .news_analyzer import (
        EntityExtractor,
        KeywordDetector,
        NewsAnalyzer,
        NewsSource,
        SentimentAnalysisResult,
        retry
    )
    from .real_time_data import (
        DataFeedStatus,
        DataPoint,
        DataSource,
        DataStreamConfig,
        DataStreamManager,
        DataValidationRule,
        DataValidator,
        RealTimeDataFeed
    )
    from .social_media_monitor import (
        MentionTracker,
        SentimentAnalyzer,
        SocialMediaAnalysisResult,
        SocialMediaMonitor,
        SocialMediaSource,
        SocialMediaTrend,
        TrendDetector,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in event_monitoring: {e}')

__all__ = [
    'CorrelationTracker',
    'DataFeedStatus',
    'DataPoint',
    'DataSource',
    'DataStreamConfig',
    'DataStreamManager',
    'DataValidationRule',
    'DataValidator',
    'EconomicCalendar',
    'EconomicEvent',
    'EconomicEventImpact',
    'EconomicEventResult',
    'EconomicIndicator',
    'EntityExtractor',
    'Event',
    'EventFilter',
    'EventHandler',
    'EventMonitor',
    'EventPrioritizer',
    'EventPriority',
    'EventProcessor',
    'EventResponseStrategy',
    'EventSource',
    'EventType',
    'ForecastAnalyzer',
    'KeywordDetector',
    'LiquidityState',
    'MarketCondition',
    'MarketConditionMonitor',
    'MarketEvent',
    'MarketRegime',
    'MentionTracker',
    'NewsAnalyzer',
    'NewsEvent',
    'NewsSource',
    'RealTimeDataFeed',
    'RegimeDetector',
    'SentimentAnalysisResult',
    'SentimentAnalyzer',
    'SocialMediaAnalysisResult',
    'SocialMediaEvent',
    'SocialMediaMonitor',
    'SocialMediaSource',
    'SocialMediaTrend',
    'TrendDetector',
    'VolatilityState',
    'retry',
]