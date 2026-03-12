"""
alternative_data package
"""

try:
    from .satellite_imagery import (
        AnalysisResult,
        CreditCardFlowAnalyzer,
        GeopoliticalEventForecaster,
        SatelliteImage,
        SatelliteImageryAnalyzer
    )
    from .sentiment_engine import (
        FreeNewsScraper,
        FreeRedditScraper,
        FreeSentimentAnalyzer,
        FreeTwitterScraper,
        RealTimeSentimentEngine,
        SentimentScore
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in alternative_data: {e}')

__all__ = [
    'AnalysisResult',
    'CreditCardFlowAnalyzer',
    'FreeNewsScraper',
    'FreeRedditScraper',
    'FreeSentimentAnalyzer',
    'FreeTwitterScraper',
    'GeopoliticalEventForecaster',
    'RealTimeSentimentEngine',
    'SatelliteImage',
    'SatelliteImageryAnalyzer',
    'SentimentScore',
]