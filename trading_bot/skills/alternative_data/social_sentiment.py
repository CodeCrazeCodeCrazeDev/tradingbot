"""
Skill #85: Social Sentiment Velocity
====================================

Tracks social media sentiment velocity and momentum.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class SocialSentimentResult:
    """Social sentiment result."""
    sentiment_score: float
    sentiment_velocity: float
    mention_count: int
    trending_topics: List[str]
    trading_signal: str


class SocialSentimentVelocity:
    """Tracks social sentiment velocity."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.sentiment_history: List[float] = []
            logger.info("SocialSentimentVelocity initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, social_data: Dict) -> SocialSentimentResult:
        """Analyze social sentiment."""
        try:
            if not social_data:
                return SocialSentimentResult(0, 0, 0, [], "No social data")
        
            sentiment = social_data.get('sentiment', 0)
            mentions = social_data.get('mentions', 0)
            topics = social_data.get('topics', [])
        
            # Track history
            self.sentiment_history.append(sentiment)
            if len(self.sentiment_history) > 100:
                self.sentiment_history = self.sentiment_history[-100:]
        
            # Calculate velocity
            if len(self.sentiment_history) >= 2:
                velocity = self.sentiment_history[-1] - self.sentiment_history[-2]
            else:
                velocity = 0
        
            signal = "BULLISH" if sentiment > 0.3 and velocity > 0 else "BEARISH" if sentiment < -0.3 else "NEUTRAL"
        
            return SocialSentimentResult(
                sentiment_score=sentiment, sentiment_velocity=velocity,
                mention_count=mentions, trending_topics=topics[:5],
                trading_signal=f"SOCIAL {signal}: Sentiment {sentiment:.2f}, velocity {velocity:+.2f}"
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
