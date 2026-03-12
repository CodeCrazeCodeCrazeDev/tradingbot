"""
sentiment package
"""

try:
    from .realtime_sentiment_engine import (
        NewsAggregator,
        NewsEvent,
        RealtimeSentimentEngine,
        SentimentAnalyzer,
        SentimentSignal,
        SocialMediaMonitor
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in sentiment: {e}')

__all__ = [
    'NewsAggregator',
    'NewsEvent',
    'RealtimeSentimentEngine',
    'SentimentAnalyzer',
    'SentimentSignal',
    'SocialMediaMonitor',
]