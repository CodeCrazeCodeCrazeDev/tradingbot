"""
social package
"""

try:
    from .copy_trading import (
        CopyMode,
        CopySettings,
        CopyTrade,
        SocialTradingPlatform,
        StrategyPerformance,
        StrategyStatus,
        TradingStrategy
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in social: {e}')

try:
    from .intelligent_learning import (
        IntelligentSocialLearning,
        TraderAnalyzer,
        HedgeFundAnalyzer,
        TraderType,
        LearningDimension,
        InsightQuality,
        TradingInsight,
        PerformanceGap,
        AdaptedStrategy,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in social.intelligent_learning: {e}')

__all__ = [
    'CopyMode',
    'CopySettings',
    'CopyTrade',
    'SocialTradingPlatform',
    'StrategyPerformance',
    'StrategyStatus',
    'TradingStrategy',
    'IntelligentSocialLearning',
    'TraderAnalyzer',
    'HedgeFundAnalyzer',
    'TraderType',
    'LearningDimension',
    'InsightQuality',
    'TradingInsight',
    'PerformanceGap',
    'AdaptedStrategy',
]