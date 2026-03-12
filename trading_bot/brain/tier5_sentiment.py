"""
Tier 5: Sentiment & Psychological Intelligence
Analyzes market sentiment and psychological factors
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector, SentimentVector
)

from trading_bot.ml.sentiment import (
    SentimentAnalyzer, NewsScraper, SocialMediaMonitor,
    SentimentResult, SentimentSource
)

logger = logging.getLogger(__name__)


# Stub classes for sentiment analysis components
class FearGreedIndex:
    """Fear & Greed Index calculator"""
    def calculate(self, market_data: pd.DataFrame) -> float:
        """Calculate fear & greed index (0-100)"""
        return 50.0  # Neutral default


class AIEmotionMapper:
    """AI-based emotion mapper"""
    def analyze_emotions(self, news_data: List[Dict]) -> Dict[str, float]:
        """Analyze emotions from news data"""
        return {'neutral': 1.0}


class TopicClusterer:
    """Topic clustering for social media"""
    def cluster_topics(self, social_data: List[Dict]) -> Dict[str, int]:
        """Cluster topics from social data"""
        return {}


class NewsShockDetector:
    """News shock detection"""
    def detect_shocks(self, news_data: List[Dict], market_data: pd.DataFrame) -> List[Dict]:
        """Detect news shocks"""
        return []


class OrderBookSentiment:
    """Simple order book sentiment analyzer"""
    
    def __init__(self):
        self.bid_volume = 0.0
        self.ask_volume = 0.0
    
    def analyze(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze order book for sentiment"""
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        
        bid_volume = sum(b.get('volume', 0) for b in bids) if bids else 0
        ask_volume = sum(a.get('volume', 0) for a in asks) if asks else 0
        
        total_volume = bid_volume + ask_volume
        if total_volume > 0:
            imbalance = (bid_volume - ask_volume) / total_volume
        else:
            imbalance = 0.0
        
        return {
            'imbalance': imbalance,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'bias': 'bullish' if imbalance > 0.1 else 'bearish' if imbalance < -0.1 else 'neutral'
        }


@dataclass
class SentimentScore:
    """Sentiment score with confidence"""
    value: float  # -1.0 to 1.0
    confidence: float
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]


class OrderBookSentimentAnalysis:
    """Order book sentiment analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sentiment_analyzer = OrderBookSentiment()
    
    def analyze(self, order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze order book sentiment"""
        if not order_book_data:
            try:
                return {
                    'bias': 0.0,
                    'strength': 0.0,
                    'imbalance': 0.0,
                    'pressure': 'neutral'
                }

                # Calculate order book imbalance
                result = self.sentiment_analyzer.calculate_imbalance(
                    order_book_data.get('bids', []),
                    order_book_data.get('asks', [])
                )

                return {
                    'bias': result['imbalance_ratio'],
                    'strength': abs(result['imbalance_ratio']),
                    'imbalance': result['weighted_imbalance'],
                    'pressure': result['sentiment'],
                    'metrics': {
                        'bid_volume': result['bid_volume'],
                        'ask_volume': result['ask_volume'],
                        'spread': order_book_data.get('spread', 0.0)
                    }
                }

            except Exception as e:
                logger.error(f"Error analyzing order book sentiment: {str(e)}")
                return {
                    'bias': 0.0,
                    'strength': 0.0,
                    'imbalance': 0.0,
                    'pressure': 'neutral'
                }


class MarketEmotionAnalysis:
    """Market emotion analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fear_greed = FearGreedIndex()
        self.emotion_mapper = AIEmotionMapper()
    
    def analyze(self, market_data: pd.DataFrame, 
               news_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Analyze market emotions"""
        # Calculate Fear & Greed Index
        fear_greed = self.fear_greed.calculate(market_data)
        
        # Map emotions from news
        emotions = {}
        if news_data:
            emotions = self.emotion_mapper.analyze_emotions(news_data)
        
        # Determine dominant emotion
        if emotions:
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            emotion_strength = max(emotions.values())
        else:
            dominant_emotion = 'neutral'
            emotion_strength = 0.0
        
        # Convert fear & greed to sentiment (-1 to 1)
        sentiment = (fear_greed - 50) / 50
        
        return {
            'fear_greed_index': fear_greed,
            'sentiment': sentiment,
            'dominant_emotion': dominant_emotion,
            'emotion_strength': emotion_strength,
            'emotions': emotions
        }


class SocialMediaAnalysis:
    """Social media sentiment analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.topic_clusterer = TopicClusterer()
    
    def analyze(self, social_data: List[Dict]) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        if not social_data:
            try:
                return {
                    'sentiment': 0.0,
                    'topics': {},
                    'strength': 0.0
                }

                # Cluster topics
                topics = self.topic_clusterer.cluster_topics(social_data)

                # Calculate overall sentiment
                sentiments = [post.get('sentiment', 0) for post in social_data]
                avg_sentiment = np.mean(sentiments) if sentiments else 0.0

                # Calculate topic strength
                topic_strength = {
                    topic: count/len(social_data)
                    for topic, count in topics.items()
                }

                # Get dominant topic
                dominant_topic = max(topic_strength.items(), key=lambda x: x[1])[0] if topic_strength else None

                return {
                    'sentiment': avg_sentiment,
                    'topics': topics,
                    'topic_strength': topic_strength,
                    'dominant_topic': dominant_topic,
                    'strength': max(topic_strength.values()) if topic_strength else 0.0
                }

            except Exception as e:
                logger.error(f"Error analyzing social media: {str(e)}")
                return {
                    'sentiment': 0.0,
                    'topics': {},
                    'strength': 0.0
                }


class NewsAnalysis:
    """News impact analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.shock_detector = NewsShockDetector()
    
    def analyze(self, news_data: List[Dict], 
               market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze news impact"""
        if not news_data:
            try:
                return {
                    'shock_detected': False,
                    'impact': 0.0,
                    'sentiment': 0.0
                }

                # Detect news shocks
                shock = self.shock_detector.detect(news_data, market_data)

                # Calculate average sentiment
                sentiments = [news.get('sentiment', 0) for news in news_data]
                avg_sentiment = np.mean(sentiments) if sentiments else 0.0

                # Calculate impact score
                if shock['detected']:
                    impact = shock['magnitude'] * shock['confidence']
                else:
                    impact = 0.0

                return {
                    'shock_detected': shock['detected'],
                    'shock_magnitude': shock.get('magnitude', 0.0),
                    'shock_confidence': shock.get('confidence', 0.0),
                    'impact': impact,
                    'sentiment': avg_sentiment,
                    'categories': shock.get('categories', [])
                }

            except Exception as e:
                logger.error(f"Error analyzing news: {str(e)}")
                return {
                    'shock_detected': False,
                    'impact': 0.0,
                    'sentiment': 0.0
                }


class Tier5SentimentAnalysis(TierBase):
    """
    Tier 5: Sentiment & Psychological Intelligence
    
    Analyzes market sentiment and psychology:
    - Order book sentiment
    - Fear & Greed Index
    - Social media analysis
    - News shock detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 5: Sentiment Analysis", config)
        self.orderbook_analysis = None
        self.emotion_analysis = None
        self.social_analysis = None
        self.news_analysis = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.orderbook_analysis = OrderBookSentimentAnalysis(self.config.get('orderbook', {}))
        self.emotion_analysis = MarketEmotionAnalysis(self.config.get('emotion', {}))
        self.social_analysis = SocialMediaAnalysis(self.config.get('social', {}))
        self.news_analysis = NewsAnalysis(self.config.get('news', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[RegimeContextVector] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> SentimentVector:
        """
        Process market data and analyze sentiment
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 4 (RegimeContextVector)
            additional_inputs: Dictionary with order book, news, and social data
            
        Returns:
            SentimentVector with sentiment analysis
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 5")
            return None
        try:
        
            # Get additional data
            order_book = additional_inputs.get('order_book', {})
            news_data = additional_inputs.get('news_data', [])
            social_data = additional_inputs.get('social_data', [])
            
            # Analyze order book sentiment
            ob_sentiment = self.orderbook_analysis.analyze(order_book)
            
            # Analyze market emotions
            emotions = self.emotion_analysis.analyze(market_data, news_data)
            
            # Analyze social media
            social = self.social_analysis.analyze(social_data)
            
            # Analyze news
            news = self.news_analysis.analyze(news_data, market_data)
            
            # Calculate market sentiment (-1 to 1)
            # Negative means bearish, positive means bullish
            ob_bias = ob_sentiment['bias']
            fear_greed_bias = emotions['sentiment']
            social_bias = social['sentiment']
            news_bias = news['sentiment']
            
            # Weight the components
            market_sentiment = (
                0.3 * ob_bias +
                0.3 * fear_greed_bias +
                0.2 * social_bias +
                0.2 * news_bias
            )
            
            # Calculate Fear-Greed Index (0-100)
            fear_greed_index = emotions['fear_greed_index']
            
            # Calculate order book bias (-1 to 1)
            order_book_bias = ob_sentiment['bias']
            
            # Calculate news impact (0 to 1)
            news_impact = news['impact']
            
            # Calculate social sentiment (-1 to 1)
            social_sentiment = social['sentiment']
            
            # Calculate narrative strength (0 to 1)
            narrative_strength = max(
                social['strength'],
                news['shock_confidence'] if news['shock_detected'] else 0.0,
                abs(ob_sentiment['imbalance'])
            )
            
            # Calculate signal value (-1 to 1)
            signal_value = market_sentiment
            
            # Calculate confidence (0 to 1)
            # Higher when multiple sources agree
            sentiments = [
                np.sign(ob_bias),
                np.sign(fear_greed_bias),
                np.sign(social_bias),
                np.sign(news_bias)
            ]
            
            agreement = sum(1 for s in sentiments if s == np.sign(market_sentiment))
            confidence = agreement / len(sentiments)
            
            # Boost confidence if narrative is strong
            if narrative_strength > 0.7:
                confidence = min(confidence * 1.2, 1.0)
            
            # Create metadata
            metadata = {
                'order_book': ob_sentiment,
                'emotions': emotions,
                'social': social,
                'news': news
            }
            
            # Create sentiment vector
            sentiment = SentimentVector(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                market_sentiment=market_sentiment,
                fear_greed_index=fear_greed_index,
                order_book_bias=order_book_bias,
                news_impact=news_impact,
                social_sentiment=social_sentiment,
                narrative_strength=narrative_strength,
                metadata=metadata
            )
            
            self.last_output = sentiment
            return sentiment
            
        except Exception as e:
            logger.error(f"Error processing Tier 5: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample additional inputs
    additional_inputs = {
        'order_book': {
            'bids': [(99.5, 1000), (99.0, 2000), (98.5, 1500)],
            'asks': [(100.5, 800), (101.0, 1500), (101.5, 2000)],
            'spread': 1.0
        },
        'news_data': [
            {'title': 'Market Rally', 'sentiment': 0.8, 'importance': 0.7},
            {'title': 'Economic Data', 'sentiment': 0.2, 'importance': 0.5}
        ],
        'social_data': [
            {'text': 'Bullish momentum', 'sentiment': 0.9},
            {'text': 'Support level holds', 'sentiment': 0.6}
        ]
    }
    
    # Initialize and process
    tier5 = Tier5SentimentAnalysis()
    tier5.initialize()
    result = tier5.process(df, additional_inputs=additional_inputs)
    
    # Print results
    logger.info("\n=== Tier 5: Sentiment Analysis Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Market Sentiment: {result.market_sentiment:.2f}")
    logger.info(f"Fear-Greed Index: {result.fear_greed_index:.1f}")
    logger.info(f"Order Book Bias: {result.order_book_bias:.2f}")
    logger.info(f"News Impact: {result.news_impact:.2f}")
    logger.info(f"Social Sentiment: {result.social_sentiment:.2f}")
    logger.info(f"Narrative Strength: {result.narrative_strength:.2%}")
