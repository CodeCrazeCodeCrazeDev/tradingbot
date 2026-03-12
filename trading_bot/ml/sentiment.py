"""Advanced Sentiment Analysis AI for market data and news.

This module implements comprehensive sentiment analysis capabilities for news articles,
social media, financial reports, and economic data to enhance trading decisions.

Features:
- Real-time news and social media sentiment analysis
- NLP-based financial report analysis
- Adaptive learning from past sentiment predictions
- Cross-source sentiment correlation
- Market regime-specific sentiment weighting
- Institutional sentiment detection
- Fraud and manipulation detection in sentiment data
"""

import logging
logger = logging.getLogger(__name__)
import random
import time
import json
import hashlib
try:
    import requests
except ImportError:
    requests = None
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from enum import Enum, auto
from collections import deque, Counter
from dataclasses import dataclass
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from loguru import logger
from trading_bot.adaptive_systems.market_regime import MarketRegime
from trading_bot.adaptive_systems.adaptive_learning import AdaptiveLearningEngine, ModelType
import numpy
import pandas

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('sentiment/vader_lexicon')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('stopwords', quiet=True)

# Define specific exceptions
class SentimentAnalysisError(Exception):
    """Base exception for sentiment analysis errors."""
    pass

class NewsScrapingError(SentimentAnalysisError):
    """Exception raised for errors during news scraping."""
    pass

class SocialMediaError(SentimentAnalysisError):
    """Exception raised for errors during social media analysis."""
    pass

class DataValidationError(SentimentAnalysisError):
    """Exception raised for data validation errors."""
    pass

class ProcessingError(SentimentAnalysisError):
    """Exception raised for data processing errors."""
    pass

class FraudDetectionError(SentimentAnalysisError):
    """Exception raised for fraud detection errors."""
    pass

class ModelTrainingError(SentimentAnalysisError):
    """Exception raised for model training errors."""
    pass

class APIRateLimitError(SentimentAnalysisError):
    """Exception raised when API rate limits are exceeded."""
    pass


class SentimentSource(Enum):
    """Enumeration of sentiment data sources."""
    NEWS = auto()
    SOCIAL_MEDIA = auto()
    FINANCIAL_REPORT = auto()
    ECONOMIC_DATA = auto()
    TECHNICAL_ANALYSIS = auto()
    INSTITUTIONAL_FLOW = auto()
    CENTRAL_BANK = auto()
    ANALYST_RATING = auto()
    INSIDER_TRADING = auto()
    OPTIONS_FLOW = auto()
    DARK_POOL = auto()
    REGULATORY_FILING = auto()
    EARNINGS_CALL = auto()
    CONFERENCE = auto()
    GEOPOLITICAL = auto()


@dataclass
class SentimentResult:
    """Structured result from sentiment analysis."""
    score: float  # Sentiment score (-1.0 to 1.0)
    confidence: float  # Confidence level (0.0 to 1.0)
    source: SentimentSource  # Source of the sentiment data
    symbol: str  # Trading symbol
    timestamp: datetime  # When the sentiment was analyzed
    text: Optional[str] = None  # Original text that was analyzed
    metadata: Dict[str, Any] = None  # Additional metadata
    fraud_probability: float = 0.0  # Probability this is manipulated data
    regime_adjusted_score: Optional[float] = None  # Score adjusted for market regime
    
    def __post_init__(self):
        """Validate the sentiment result after initialization."""
        if self.metadata is None:
            self.metadata = {}
        
        # Ensure score is within valid range
        self.score = max(-1.0, min(1.0, self.score))
        
        # Ensure confidence is within valid range
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Ensure fraud probability is within valid range
        self.fraud_probability = max(0.0, min(1.0, self.fraud_probability))
    
    @property
    def is_bullish(self) -> bool:
        """Check if sentiment is bullish."""
        return self.score > 0.1
    
    @property
    def is_bearish(self) -> bool:
        """Check if sentiment is bearish."""
        return self.score < -0.1
    
    @property
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return -0.1 <= self.score <= 0.1
    
    @property
    def is_reliable(self) -> bool:
        """Check if sentiment is reliable based on confidence and fraud probability."""
        return self.confidence > 0.6 and self.fraud_probability < 0.2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'score': self.score,
            'confidence': self.confidence,
            'source': self.source.name,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'is_bullish': self.is_bullish,
            'is_bearish': self.is_bearish,
            'is_neutral': self.is_neutral,
            'is_reliable': self.is_reliable,
            'fraud_probability': self.fraud_probability
        }
        
        if self.text:
            result['text'] = self.text
            
        if self.metadata:
            result['metadata'] = self.metadata
            
        if self.regime_adjusted_score is not None:
            result['regime_adjusted_score'] = self.regime_adjusted_score
            
        return result

class SentimentAnalyzer:
    """Advanced AI-powered sentiment analysis for market-related content.
    
    Analyzes sentiment from news articles, social media, financial reports, and economic data
    to provide comprehensive market intelligence for trading decisions.
    
    Features:
    - Real-time sentiment analysis with NLP
    - Adaptive learning from past predictions
    - Cross-source sentiment correlation
    - Fraud and manipulation detection
    - Market regime-specific adjustments
    - Institutional sentiment detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the advanced sentiment analyzer.
        
        Args:
            config: Configuration dictionary with analyzer parameters.
                   If None, default parameters will be used.
        """
        self.config = config or {}
        self.sentiment_cache = {}
        self.history = deque(maxlen=1000)  # Store sentiment history for learning
        self.models = {}  # ML models for sentiment prediction
        self.fraud_detector = None  # Model for detecting manipulated sentiment
        self.lock = Lock()  # Thread safety for model updates
        self.news_scraper = NewsScraper()
        self.social_media_monitor = SocialMediaMonitor()
        self.nlp_analyzer = self._initialize_nlp()
        self.adaptive_learner = self._initialize_adaptive_learner()
        self.real_time_processor = self._initialize_real_time_processor()
        
        # Initialize fraud detection model
        self._initialize_fraud_detector()
        
        logger.info("Advanced SentimentAnalyzer initialized with AI capabilities")
    
    def _initialize_nlp(self) -> SentimentIntensityAnalyzer:
        """Initialize NLP components for sentiment analysis."""
        return SentimentIntensityAnalyzer()
    
    def _initialize_adaptive_learner(self) -> Optional[AdaptiveLearningEngine]:
        """Initialize adaptive learning component if enabled."""
        if self.config.get('use_adaptive_learning', True):
            try:
                return AdaptiveLearningEngine({})
            except ImportError:
                logger.warning("AdaptiveLearningEngine not available, using static models")
                return None
        return None
    
    def _initialize_real_time_processor(self) -> Optional[Thread]:
        """Initialize real-time sentiment processing thread if enabled."""
        if self.config.get('real_time_processing', True):
            processor = Thread(
                target=self._real_time_processing_loop,
                daemon=True,
                name="SentimentRealTimeProcessor"
            )
            processor.start()
            return processor
        return None
    
    def _initialize_fraud_detector(self) -> None:
        """Initialize the fraud detection model for sentiment manipulation detection."""
        try:
            # Create synthetic training data first
            X_train = self._generate_synthetic_fraud_training_data()
            
            # Initialize and immediately fit the model
            self.fraud_detector = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42
            ).fit(X_train)
            
            logger.info("Fraud detection model initialized and trained")
        except Exception as e:
            logger.error(f"Failed to initialize fraud detection model: {e}")
            self.fraud_detector = None
            
    def _generate_synthetic_fraud_training_data(self) -> np.ndarray:
        """Generate synthetic training data for the fraud detector.
        
        Returns:
            np.ndarray: Training data array
        """
        try:
            # Create synthetic training data for the fraud detector
            # Format: [score, confidence, is_news, is_social, text_length]
            normal_samples = [
                # Normal news samples (higher confidence, balanced sentiment)
                [0.8, 0.85, 1, 0, 500],  # Positive news with high confidence
                [0.6, 0.75, 1, 0, 450],  # Positive news
                [0.3, 0.65, 1, 0, 400],  # Slightly positive news
                [0.0, 0.60, 1, 0, 350],  # Neutral news
                [-0.3, 0.65, 1, 0, 400],  # Slightly negative news
                [-0.6, 0.75, 1, 0, 450],  # Negative news
                [-0.8, 0.85, 1, 0, 500],  # Negative news with high confidence
                
                # Normal social media samples (lower confidence, more extreme sentiment)
                [0.9, 0.60, 0, 1, 100],  # Positive social with medium confidence
                [0.5, 0.55, 0, 1, 80],   # Positive social
                [0.2, 0.52, 0, 1, 60],   # Slightly positive social
                [0.0, 0.50, 0, 1, 50],   # Neutral social
                [-0.2, 0.52, 0, 1, 60],  # Slightly negative social
                [-0.5, 0.55, 0, 1, 80],  # Negative social
                [-0.9, 0.60, 0, 1, 100]  # Negative social with medium confidence
            ]
            
            # Add some anomalous samples (potential manipulation patterns)
            anomalous_samples = [
                # Extremely positive with very high confidence
                [1.0, 0.99, 1, 0, 50],    # Suspiciously short but extremely positive news
                [1.0, 0.99, 0, 1, 20],    # Suspiciously short but extremely positive social
                
                # Extremely negative with very high confidence
                [-1.0, 0.99, 1, 0, 50],   # Suspiciously short but extremely negative news
                [-1.0, 0.99, 0, 1, 20],   # Suspiciously short but extremely negative social
                
                # Unusual combinations
                [0.95, 0.40, 1, 0, 1000], # Very positive but low confidence (unusual)
                [-0.95, 0.40, 1, 0, 1000] # Very negative but low confidence (unusual)
            ]
            
            # Combine samples (mostly normal with some anomalies)
            training_data = normal_samples + anomalous_samples
            
            # Convert to numpy array
            X_train = np.array(training_data)
            
            logger.info(f"Generated {len(training_data)} synthetic samples for fraud detection training")
            return X_train
            
        except Exception as e:
            logger.error(f"Error generating fraud detection training data: {e}")
            # Return a minimal valid dataset to avoid errors
            return np.array([[0.0, 0.5, 0, 0, 100], [0.5, 0.5, 1, 0, 200]])
    
    def _real_time_processing_loop(self) -> None:
        """Background thread for real-time sentiment processing."""
        logger.info("Starting real-time sentiment processing loop")
        
        # Watchlist of symbols to monitor
        watchlist = self.config.get('watchlist', [])
        if not watchlist:
            logger.warning("No symbols in watchlist for real-time sentiment monitoring")
            return
        try:
            
            while True:
                try:
                    # Process each symbol in the watchlist
                    for symbol in watchlist:
                        # Get latest news and social media data
                        news_data = self.news_scraper.get_news(symbol, days=1)
                        social_data = self.social_media_monitor.get_posts(symbol, hours=6)
                        
                        # Process in separate thread to avoid blocking
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            news_future = executor.submit(self._process_news_batch, symbol, news_data)
                            social_future = executor.submit(self._process_social_batch, symbol, social_data)
                            
                            # Wait for completion
                            news_results = news_future.result()
                            social_results = social_future.result()
                        
                        # Update models with new data
                        self._update_models_with_new_data(symbol, news_results, social_results)
                        
                    # Sleep between processing cycles
                    time.sleep(self.config.get('real_time_interval_seconds', 300))
                    
                except Exception as e:
                    logger.error(f"Error in real-time sentiment processing: {e}")
                    time.sleep(60)  # Sleep and retry on error
                    
        except Exception as e:
            logger.error(f"Real-time sentiment processing thread terminated: {e}")
    
    def _process_news_batch(self, symbol: str, news_data: List[Dict]) -> List[SentimentResult]:
        """Process a batch of news articles for sentiment."""
        results = []
        
        for article in news_data:
            try:
                # Extract text for analysis
                text = f"{article.get('title', '')} {article.get('content', '')}"
                
                # Skip if no meaningful text
                if not text.strip():
                    continue
                    
                # Get NLP sentiment score
                vader_result = self.nlp_analyzer.polarity_scores(text)
                
                # Create sentiment result
                result = SentimentResult(
                    score=vader_result['compound'],
                    confidence=0.7 + (abs(vader_result['compound']) * 0.2),  # Higher confidence for stronger sentiment
                    source=SentimentSource.NEWS,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    text=article.get('title', ''),
                    metadata={
                        'source': article.get('source'),
                        'date': article.get('date'),
                        'vader_scores': vader_result
                    }
                )
                
                # Check for fraud/manipulation
                if self.fraud_detector:
                    result.fraud_probability = self._detect_manipulation(result)
                
                results.append(result)
                
                # Add to history for learning
                self.history.append(result)
                
            except Exception as e:
                logger.error(f"Error processing news article: {e}")
        
        return results
    
    def _process_social_batch(self, symbol: str, social_data: List[Dict]) -> List[SentimentResult]:
        """Process a batch of social media posts for sentiment."""
        results = []
        
        for post in social_data:
            try:
                # Extract text for analysis
                text = post.get('text', '')
                
                # Skip if no meaningful text
                if not text.strip():
                    continue
                    
                # Get NLP sentiment score
                vader_result = self.nlp_analyzer.polarity_scores(text)
                
                # Create sentiment result
                result = SentimentResult(
                    score=vader_result['compound'],
                    confidence=0.5 + (abs(vader_result['compound']) * 0.2),  # Lower base confidence for social media
                    source=SentimentSource.SOCIAL_MEDIA,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    text=text,
                    metadata={
                        'platform': post.get('platform'),
                        'timestamp': post.get('timestamp'),
                        'likes': post.get('likes', 0),
                        'replies': post.get('replies', 0),
                        'vader_scores': vader_result
                    }
                )
                
                # Check for fraud/manipulation
                if self.fraud_detector:
                    result.fraud_probability = self._detect_manipulation(result)
                
                results.append(result)
                
                # Add to history for learning
                self.history.append(result)
                
            except Exception as e:
                logger.error(f"Error processing social media post: {e}")
        
        return results
    
    def _update_models_with_new_data(self, symbol: str, news_results: List[SentimentResult], 
                                    social_results: List[SentimentResult]) -> None:
        """Update ML models with new sentiment data."""
        if not self.adaptive_learner:
            return
        try:
            
            with self.lock:
                # Combine results
                all_results = news_results + social_results
                
                if not all_results:
                    return
                    
                # Extract features and labels for model updating
                features = []
                labels = []
                
                for result in all_results:
                    # Skip unreliable results
                    if not result.is_reliable:
                        continue
                        
                    # Extract features (simplified for example)
                    feature_vector = [
                        result.score,
                        result.confidence,
                        1 if result.source == SentimentSource.NEWS else 0,
                        1 if result.source == SentimentSource.SOCIAL_MEDIA else 0,
                        result.fraud_probability
                    ]
                    
                    # Use sentiment score as label (simplified)
                    label = 1 if result.is_bullish else (0 if result.is_neutral else -1)
                    
                    features.append(feature_vector)
                    labels.append(label)
                
                if features and labels:
                    # Update the adaptive learner with new data
                    if hasattr(self.adaptive_learner, 'update'):
                        # Compatibility branch for older learners
                        self.adaptive_learner.update(np.array(features), np.array(labels))
                    elif hasattr(self.adaptive_learner, 'add_training_sample'):
                        for feat, lab in zip(features, labels):
                            self.adaptive_learner.add_training_sample(
                                ModelType.SENTIMENT_ANALYZER,
                                feat,
                                lab,
                                metadata={'source': 'sentiment_realtime'}
                            )
                    logger.debug(f"Updated adaptive learner with {len(features)} new samples")
        except Exception as e:
            logger.error(f"Error updating models with new data: {e}")
    
    def _detect_manipulation(self, result: SentimentResult) -> float:
        """Detect potential manipulation or fraud in sentiment data.
        
        Returns probability of manipulation (0.0 to 1.0).
        """
        if not self.fraud_detector:
            return 0.0
        try:
            
            # Extract features for fraud detection
            features = [
                result.score,
                result.confidence,
                1 if result.source == SentimentSource.NEWS else 0,
                1 if result.source == SentimentSource.SOCIAL_MEDIA else 0,
                len(result.text) if result.text else 0,
                # Add more features as needed
            ]
            
            # Reshape for sklearn
            features = np.array(features).reshape(1, -1)
            
            # Get anomaly score (-1 for anomalies, 1 for normal)
            anomaly_score = self.fraud_detector.decision_function(features)[0]
            
            # Convert to probability (0 = likely fraud, 1 = likely legitimate)
            # Normalize from [-1, 1] to [0, 1] where 0 is fraudulent
            fraud_prob = 1 - ((anomaly_score + 1) / 2)
            
            return fraud_prob
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {e}")
            return 0.0  # Default to no fraud on error
    
    def analyze_news(self, symbol: str, days: int = 1) -> Dict[str, Any]:
        """Analyze news sentiment for a symbol using advanced NLP.
        
        Args:
            symbol: Trading symbol
            days: Number of days to look back for news
            
        Returns:
            Dictionary with comprehensive sentiment analysis
        """
        # Validate input
        if not isinstance(symbol, str) or not symbol:
            raise DataValidationError(f"Invalid symbol: {symbol}")
        try:
            
            logger.info(f"Analyzing sentiment for news on {symbol} over past {days} days")
            
            # Get news data
            news_data = self.news_scraper.get_news(symbol, days=days)
            
            if not news_data:
                logger.warning(f"No news found for {symbol} in the past {days} days")
                return {
                    'score': 0.0,
                    'confidence': 50.0,
                    'source': 'news',
                    'articles_analyzed': 0,
                    'sentiment': 'neutral',
                    'fraud_probability': 0.0
                }
            
            # Process news batch
            sentiment_results = self._process_news_batch(symbol, news_data)
            
            if not sentiment_results:
                logger.warning(f"No valid sentiment results for {symbol} news")
                return {
                    'score': 0.0,
                    'confidence': 50.0,
                    'source': 'news',
                    'articles_analyzed': 0,
                    'sentiment': 'neutral',
                    'fraud_probability': 0.0
                }
            
            # Calculate aggregate sentiment
            total_score = 0.0
            total_confidence = 0.0
            total_fraud_prob = 0.0
            reliable_count = 0
            
            for result in sentiment_results:
                if result.is_reliable:
                    # Weight by confidence
                    weight = result.confidence
                    total_score += result.score * weight
                    total_confidence += weight
                    total_fraud_prob += result.fraud_probability
                    reliable_count += 1
            
            # Calculate weighted averages
            if reliable_count > 0:
                avg_score = total_score / total_confidence if total_confidence > 0 else 0.0
                avg_confidence = total_confidence / reliable_count
                avg_fraud_prob = total_fraud_prob / reliable_count
            else:
                avg_score = 0.0
                avg_confidence = 0.5
                avg_fraud_prob = 0.0
            
            # Determine sentiment label
            if avg_score > 0.1:
                sentiment = 'bullish'
            elif avg_score < -0.1:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Prepare detailed result
            result = {
                'score': avg_score,
                'confidence': avg_confidence * 100,  # Convert to percentage
                'source': 'news',
                'articles_analyzed': len(news_data),
                'valid_articles': reliable_count,
                'sentiment': sentiment,
                'fraud_probability': avg_fraud_prob,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sources': list(set(article.get('source', 'unknown') for article in news_data)),
                'headlines': [result.text for result in sentiment_results[:5] if result.text]  # Top 5 headlines
            }
            
            logger.info(f"News sentiment for {symbol}: {sentiment} (score: {avg_score:.2f}, confidence: {avg_confidence*100:.1f}%)")
            return result
            
        except (requests.RequestException, ConnectionError) as e:
            logger.error(f"Network error in news sentiment analysis: {e}")
            raise NewsScrapingError(f"Network error: {e}") from e
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Data processing error in news sentiment analysis: {e}")
            raise ProcessingError(f"Error processing news data: {e}") from e
    
    def analyze_social_media(self, symbol: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze social media sentiment for a symbol using advanced NLP.
        
        Args:
            symbol: Trading symbol
            hours: Number of hours to look back for social media posts
            
        Returns:
            Dictionary with comprehensive sentiment analysis
        """
        try:
            logger.info(f"Analyzing social media sentiment for {symbol} over past {hours} hours")
            
            # Get social media data
            social_data = self.social_media_monitor.get_posts(symbol, hours=hours)
            
            if not social_data:
                logger.warning(f"No social media posts found for {symbol} in the past {hours} hours")
                return {
                    'score': 0.0,
                    'confidence': 40.0,  # Lower base confidence for social media
                    'source': 'social_media',
                    'posts_analyzed': 0,
                    'sentiment': 'neutral',
                    'fraud_probability': 0.0
                }
            
            # Process social media batch
            sentiment_results = self._process_social_batch(symbol, social_data)
            
            if not sentiment_results:
                logger.warning(f"No valid sentiment results for {symbol} social media")
                return {
                    'score': 0.0,
                    'confidence': 40.0,
                    'source': 'social_media',
                    'posts_analyzed': 0,
                    'sentiment': 'neutral',
                    'fraud_probability': 0.0
                }
            
            # Calculate aggregate sentiment with engagement weighting
            total_score = 0.0
            total_weight = 0.0
            total_fraud_prob = 0.0
            reliable_count = 0
            platforms_count = Counter()
            
            for result in sentiment_results:
                if result.is_reliable:
                    # Weight by confidence and engagement metrics
                    likes = result.metadata.get('likes', 0)
                    replies = result.metadata.get('replies', 0)
                    engagement = 1.0 + (0.01 * likes) + (0.05 * replies)  # Engagement factor
                    
                    # Combined weight
                    weight = result.confidence * engagement
                    
                    total_score += result.score * weight
                    total_weight += weight
                    total_fraud_prob += result.fraud_probability
                    reliable_count += 1
                    
                    # Track platform distribution
                    platform = result.metadata.get('platform', 'unknown')
                    platforms_count[platform] += 1
            
            # Calculate weighted averages
            if reliable_count > 0 and total_weight > 0:
                avg_score = total_score / total_weight
                avg_confidence = 0.5  # Base confidence for social media
                avg_fraud_prob = total_fraud_prob / reliable_count
                
                # Adjust confidence based on sample size and diversity
                platform_diversity = len(platforms_count) / max(1, len(self.social_media_monitor.platforms))
                sample_size_factor = min(1.0, reliable_count / 20)  # Caps at 20 posts
                
                avg_confidence = 0.5 + (0.1 * platform_diversity) + (0.2 * sample_size_factor)
            else:
                avg_score = 0.0
                avg_confidence = 0.4
                avg_fraud_prob = 0.0
            
            # Determine sentiment label
            if avg_score > 0.15:  # Higher threshold for social media bullishness
                sentiment = 'bullish'
            elif avg_score < -0.1:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Prepare detailed result
            result = {
                'score': avg_score,
                'confidence': avg_confidence * 100,  # Convert to percentage
                'source': 'social_media',
                'posts_analyzed': len(social_data),
                'valid_posts': reliable_count,
                'sentiment': sentiment,
                'fraud_probability': avg_fraud_prob,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platforms': dict(platforms_count),
                'sample_posts': [result.text for result in sentiment_results[:5] if result.text]  # Top 5 posts
            }
            
            logger.info(f"Social media sentiment for {symbol}: {sentiment} (score: {avg_score:.2f}, confidence: {avg_confidence*100:.1f}%)")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Network error in social media analysis: {e}")
            raise SocialMediaError(f"Network error: {e}") from e
        except ValueError as e:
            logger.error(f"Validation error in social media analysis: {e}")
            raise SocialMediaError(f"Validation error: {e}") from e
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Data processing error in social media analysis: {e}")
            raise SocialMediaError(f"Processing error: {e}") from e
    
    def analyze_economic_data(self, data: Dict[str, Any], 
                             expectations: Dict[str, float]) -> Dict[str, Any]:
        """Analyze sentiment from economic data releases.
        
        Args:
            data: Dictionary with economic indicators and their values
            expectations: Dictionary with expected values for comparison
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not data:
            logger.warning("No economic data provided for sentiment analysis")
            return {'sentiment': 'neutral', 'score': 0.0, 'impact': 'low'}
        
        logger.info(f"Analyzing sentiment for economic data: {list(data.keys())}")
        
        # This is a placeholder for actual economic data analysis
        # In a real implementation, this would use more sophisticated models
        
        # Define indicator importance (impact on markets)
        indicator_importance = {
            'gdp': 0.9,
            'unemployment': 0.8,
            'cpi': 0.85,
            'ppi': 0.7,
            'retail_sales': 0.75,
            'interest_rate': 0.95,
            'nfp': 0.9,
            'ism_manufacturing': 0.7,
            'ism_services': 0.65,
            'housing_starts': 0.6,
            'consumer_confidence': 0.75,
            'default': 0.5
        }
        
        # Initialize variables
        sentiment_scores = []
        total_importance = 0
        
        # Process each economic indicator
        for indicator, value in data.items():
            # Skip if not numeric
            if not isinstance(value, (int, float)):
                continue
                
            # Get expected value
            expected = expectations.get(indicator)
            if expected is None:
                continue
                
            # Get indicator importance
            importance = indicator_importance.get(indicator.lower(), indicator_importance['default'])
            total_importance += importance
            
            # Calculate surprise factor
            if expected != 0:
                surprise = (value - expected) / abs(expected)
            else:
                surprise = 0 if value == 0 else (1 if value > 0 else -1)
                
            # Determine if surprise is positive or negative for markets
            # For some indicators like unemployment, lower is better
            if indicator.lower() in ['unemployment', 'cpi', 'ppi', 'interest_rate']:
                surprise = -surprise
                
            # Cap surprise factor
            surprise = max(-1.0, min(1.0, surprise))
            
            # Add weighted score
            sentiment_scores.append(surprise * importance)
        
        # Calculate overall sentiment score
        if sentiment_scores and total_importance > 0:
            overall_score = sum(sentiment_scores) / total_importance
        else:
            overall_score = 0
            
        # Determine sentiment label
        if overall_score > 0.1:
            sentiment = 'bullish'
        elif overall_score < -0.1:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
            
        # Determine impact level
        if total_importance > 2.0:
            impact = 'high'
        elif total_importance > 1.0:
            impact = 'medium'
        else:
            impact = 'low'
            
        # Prepare result
        result = {
            'sentiment': sentiment,
            'score': overall_score,
            'impact': impact,
            'indicators_analyzed': len(sentiment_scores),
            'total_importance': total_importance
        }
        
        logger.info(f"Economic data sentiment analysis complete: {sentiment} ({overall_score:.2f})")
        return result
    
    def analyze_financial_reports(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Analyze financial reports and filings for a symbol.
        
        Args:
            symbol: Trading symbol
            days: Number of days to look back for reports
            
        Returns:
            Dictionary with sentiment analysis of financial reports
        """
        logger.info(f"Analyzing financial reports for {symbol} over past {days} days")
        
        # This would connect to SEC EDGAR or similar in a real implementation
        # For now, we'll generate mock data
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate mock sentiment
        sentiment_score = random.uniform(-0.3, 0.3)
        confidence = 0.7 + random.uniform(0, 0.2)  # Higher confidence for official reports
        
        # Determine sentiment label
        if sentiment_score > 0.1:
            sentiment = 'bullish'
        elif sentiment_score < -0.1:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'score': sentiment_score,
            'confidence': confidence * 100,
            'source': 'financial_reports',
            'sentiment': sentiment,
            'reports_analyzed': random.randint(1, 3),
            'filing_types': ['10-K', '10-Q', '8-K'][:random.randint(1, 3)],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def analyze_institutional_flow(self, symbol: str) -> Dict[str, Any]:
        """Analyze institutional order flow for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with institutional flow analysis
        """
        logger.info(f"Analyzing institutional order flow for {symbol}")
        
        # This would connect to order flow data providers in a real implementation
        # For now, we'll generate mock data
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate mock sentiment
        flow_score = random.uniform(-0.5, 0.5)
        confidence = 0.6 + random.uniform(0, 0.3)
        
        # Determine flow direction
        if flow_score > 0.2:
            flow = 'accumulation'
        elif flow_score < -0.2:
            flow = 'distribution'
        else:
            flow = 'neutral'
        
        return {
            'score': flow_score,
            'confidence': confidence * 100,
            'source': 'institutional_flow',
            'flow_type': flow,
            'dark_pool_activity': random.choice(['high', 'medium', 'low']),
            'block_trades': random.randint(0, 10),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_market_mood(self, symbol: str, regime: Optional[MarketRegime] = None) -> Dict[str, Any]:
        """Get comprehensive market mood by combining multiple sentiment sources with adaptive weighting.
        
        Uses AI-powered sentiment analysis with adaptive learning and market regime detection
        to provide a holistic view of market sentiment.
        
        Args:
            symbol: Trading symbol to analyze
            regime: Current market regime for adaptive weighting
            
        Returns:
            Dictionary with comprehensive market mood assessment
        """
        logger.info(f"Analyzing market mood for {symbol} (regime: {regime.value if regime else 'unknown'})")
        
        # Check if we have cached results that are still valid (less than 1 hour old)
        cache_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d_%H')}_{regime.value if regime else 'default'}"
        if cache_key in self.sentiment_cache:
            logger.info(f"Using cached market mood for {symbol}")
            return self.sentiment_cache[cache_key]
        
        # Get sentiment from different sources
        news_sentiment = self.analyze_news(symbol, days=2)
        social_sentiment = self.analyze_social_media(symbol, hours=12)
        financial_sentiment = self.analyze_financial_reports(symbol)
        institutional_sentiment = self.analyze_institutional_flow(symbol)
        
        # Generate technical sentiment (in real implementation, this would come from technical analysis)
        technical_sentiment = {
            'sentiment': random.choice(['bullish', 'bearish', 'neutral']),
            'score': random.uniform(-0.3, 0.3),
            'timeframe': 'short_term',
            'confidence': random.uniform(60, 80)
        }
        
        # Get adaptive weights based on market regime and learning
        weights = self._get_adaptive_weights(regime)
        
        # Apply adaptive learning if available
        if self.adaptive_learner:
            weights = self._apply_adaptive_learning(weights, regime, symbol)
        
        # Combine sentiments with adaptive weights
        components = {
            'news': news_sentiment['score'],
            'social': social_sentiment['score'],
            'financial': financial_sentiment['score'],
            'institutional': institutional_sentiment['score'],
            'technical': technical_sentiment['score']
        }
        
        # Calculate weighted score
        weighted_score = sum(score * weights.get(source, 0.1) for source, score in components.items())
        
        # Apply regime-specific adjustments
        weighted_score = self._apply_regime_adjustments(weighted_score, regime)
        
        # Check for manipulation
        manipulation_detected = self._detect_market_manipulation(components, regime)
        
        # Determine overall mood with regime-specific thresholds
        thresholds = self._get_mood_thresholds(regime)
        if manipulation_detected:
            # Be more conservative when manipulation is detected
            if weighted_score > thresholds['bullish'] * 1.5:
                mood = 'bullish'
            elif weighted_score < thresholds['bearish'] * 1.5:
                mood = 'bearish'
            else:
                mood = 'neutral'
        else:
            if weighted_score > thresholds['bullish']:
                mood = 'bullish'
            elif weighted_score < thresholds['bearish']:
                mood = 'bearish'
            else:
                mood = 'neutral'
        
        # Calculate adaptive confidence
        confidence = self._calculate_adaptive_confidence(
            news_sentiment, social_sentiment, financial_sentiment, 
            institutional_sentiment, technical_sentiment, weights, regime
        )
        
        # Prepare comprehensive result
        result = {
            'symbol': symbol,
            'mood': mood,
            'score': weighted_score,
            'confidence': confidence,
            'regime': regime.value if regime else 'unknown',
            'adaptive_weights': weights,
            'manipulation_probability': manipulation_detected,
            'components': {
                'news': news_sentiment,
                'social': social_sentiment,
                'financial': financial_sentiment,
                'institutional': institutional_sentiment,
                'technical': technical_sentiment
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_id': hashlib.md5(f"{symbol}_{datetime.now().isoformat()}".encode()).hexdigest()
        }
        
        # Cache the result
        self.sentiment_cache[cache_key] = result
        
        # Store for adaptive learning
        self._store_for_learning(result)
        
        logger.info(f"Advanced market mood analysis complete for {symbol}: {mood} (score: {weighted_score:.2f}, confidence: {confidence:.1f}%)")
        return result
        
    def _apply_adaptive_learning(self, weights: Dict[str, float], regime: Optional[MarketRegime], symbol: str) -> Dict[str, float]:
        """Apply adaptive learning to adjust weights based on past performance."""
        try:
            # This would use the adaptive learner to optimize weights based on past performance
            # For now, we'll make small random adjustments to simulate learning
            
            adjusted_weights = weights.copy()
            
            # Make small adjustments (±10%)
            for key in adjusted_weights:
                adjustment = random.uniform(-0.1, 0.1) * adjusted_weights[key]
                adjusted_weights[key] = max(0.05, min(0.5, adjusted_weights[key] + adjustment))
            
            # Normalize to ensure weights sum to 1
            total = sum(adjusted_weights.values())
            for key in adjusted_weights:
                adjusted_weights[key] /= total
                
            return adjusted_weights
            
        except Exception as e:
            logger.error(f"Error in adaptive learning: {e}")
            return weights
    
    def _detect_market_manipulation(self, components: Dict[str, float], regime: Optional[MarketRegime]) -> float:
        """Detect potential market manipulation by analyzing divergences between sentiment sources.
        
        Returns probability of manipulation (0.0 to 1.0).
        """
        try:
            # Look for unusual divergences between sentiment sources
            # For example, if social media is extremely bullish but institutional flow is bearish
            
            # Calculate divergence scores
            news_social_divergence = abs(components.get('news', 0) - components.get('social', 0))
            news_institutional_divergence = abs(components.get('news', 0) - components.get('institutional', 0))
            social_institutional_divergence = abs(components.get('social', 0) - components.get('institutional', 0))
            
            # Higher weights for more reliable divergences
            weighted_divergence = (
                news_social_divergence * 0.3 +
                news_institutional_divergence * 0.5 +
                social_institutional_divergence * 0.7
            )
            
            # Scale to 0-1 range (values above 1.0 are highly suspicious)
            manipulation_prob = min(1.0, weighted_divergence / 1.5)
            
            # Adjust based on regime (manipulation more common in certain regimes)
            if regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.CRISIS]:
                manipulation_prob *= 1.2
            
            return manipulation_prob
            
        except Exception as e:
            logger.error(f"Error in manipulation detection: {e}")
            return 0.0
    
    def _store_for_learning(self, result: Dict[str, Any]) -> None:
        """Store sentiment analysis result for future learning."""
        try:
            # In a real implementation, this would store the result in a database
            # For now, we'll just add it to the history deque
            
            # Create simplified record for learning
            learning_record = {
                'symbol': result['symbol'],
                'mood': result['mood'],
                'score': result['score'],
                'confidence': result['confidence'],
                'regime': result['regime'],
                'weights': result['adaptive_weights'],
                'timestamp': result['timestamp'],
                'components': {k: v['score'] for k, v in result['components'].items()}
            }
            
            # Add to history
            self.history.append(learning_record)
            
        except Exception as e:
            logger.error(f"Error storing sentiment for learning: {e}")
    
    def _calculate_adaptive_confidence(self, news_sent: Dict, social_sent: Dict, 
                                     financial_sent: Dict, inst_sent: Dict, tech_sent: Dict,
                                     weights: Dict, regime: Optional[MarketRegime]) -> float:
        """Calculate adaptive confidence based on regime and source reliability."""
        # Calculate weighted confidence from each source
        weighted_confidence = (
            (news_sent.get('confidence', 50) / 100) * weights.get('news', 0.2) +
            (social_sent.get('confidence', 40) / 100) * weights.get('social', 0.15) +
            (financial_sent.get('confidence', 70) / 100) * weights.get('financial', 0.25) +
            (inst_sent.get('confidence', 60) / 100) * weights.get('institutional', 0.25) +
            (tech_sent.get('confidence', 60) / 100) * weights.get('technical', 0.15)
        )
        
        # Apply regime-specific confidence adjustments
        if regime:
            confidence_multipliers = {
                MarketRegime.TRENDING_BULL: 1.1,
                MarketRegime.TRENDING_BEAR: 1.1,
                MarketRegime.RANGING: 0.9,
                MarketRegime.HIGH_VOLATILITY: 0.7,
                MarketRegime.LOW_VOLATILITY: 1.2,
                MarketRegime.BREAKOUT: 0.8,
                MarketRegime.CRISIS: 0.6
            }
            weighted_confidence *= confidence_multipliers.get(regime, 1.0)
        
        # Convert to percentage and ensure within range
        confidence_pct = min(100.0, max(0.0, weighted_confidence * 100))
        
        return confidence_pct
    
    def _get_adaptive_weights(self, regime: Optional[MarketRegime]) -> Dict[str, float]:
        """Get adaptive weights based on market regime."""
        if regime is None:
            return {
                'news': 0.20, 
                'social': 0.15, 
                'financial': 0.20, 
                'institutional': 0.25, 
                'technical': 0.20
            }
        
        # Regime-specific weight adjustments
        weight_adjustments = {
            MarketRegime.TRENDING_BULL: {
                'news': 0.15, 
                'social': 0.20, 
                'financial': 0.15, 
                'institutional': 0.25, 
                'technical': 0.25
            },
            MarketRegime.TRENDING_BEAR: {
                'news': 0.30, 
                'social': 0.10, 
                'financial': 0.25, 
                'institutional': 0.25, 
                'technical': 0.10
            },
            MarketRegime.RANGING: {
                'news': 0.15, 
                'social': 0.15, 
                'financial': 0.20, 
                'institutional': 0.20, 
                'technical': 0.30
            },
            MarketRegime.HIGH_VOLATILITY: {
                'news': 0.35, 
                'social': 0.05, 
                'financial': 0.25, 
                'institutional': 0.30, 
                'technical': 0.05
            },
            MarketRegime.LOW_VOLATILITY: {
                'news': 0.15, 
                'social': 0.15, 
                'financial': 0.20, 
                'institutional': 0.15, 
                'technical': 0.35
            },
            MarketRegime.BREAKOUT: {
                'news': 0.10, 
                'social': 0.20, 
                'financial': 0.15, 
                'institutional': 0.20, 
                'technical': 0.35
            },
            MarketRegime.CRISIS: {
                'news': 0.40, 
                'social': 0.05, 
                'financial': 0.30, 
                'institutional': 0.20, 
                'technical': 0.05
            }
        }
        
        return weight_adjustments.get(regime, {
            'news': 0.20, 
            'social': 0.15, 
            'financial': 0.20, 
            'institutional': 0.25, 
            'technical': 0.20
        })
    
    def _apply_regime_adjustments(self, score: float, regime: Optional[MarketRegime]) -> float:
        """Apply regime-specific adjustments to sentiment score."""
        if regime is None:
            return score
        
        # Regime-specific multipliers
        multipliers = {
            MarketRegime.TRENDING_BULL: 1.1,  # Amplify positive sentiment
            MarketRegime.TRENDING_BEAR: 0.9,  # Dampen sentiment in bear markets
            MarketRegime.RANGING: 1.0,
            MarketRegime.HIGH_VOLATILITY: 0.8,  # Reduce sentiment impact in volatile markets
            MarketRegime.LOW_VOLATILITY: 1.2,  # Amplify sentiment in stable markets
            MarketRegime.BREAKOUT: 1.3,  # Amplify sentiment during breakouts
            MarketRegime.CRISIS: 0.5  # Heavily dampen sentiment during crisis
        }
        
        return score * multipliers.get(regime, 1.0)
    
    def _get_mood_thresholds(self, regime: Optional[MarketRegime]) -> Dict[str, float]:
        """Get mood classification thresholds based on regime."""
        if regime is None:
            return {'bullish': 0.15, 'bearish': -0.15}
        
        # Regime-specific thresholds
        thresholds = {
            MarketRegime.TRENDING_BULL: {'bullish': 0.1, 'bearish': -0.2},
            MarketRegime.TRENDING_BEAR: {'bullish': 0.2, 'bearish': -0.1},
            MarketRegime.RANGING: {'bullish': 0.15, 'bearish': -0.15},
            MarketRegime.HIGH_VOLATILITY: {'bullish': 0.25, 'bearish': -0.25},
            MarketRegime.LOW_VOLATILITY: {'bullish': 0.1, 'bearish': -0.1},
            MarketRegime.BREAKOUT: {'bullish': 0.05, 'bearish': -0.05},
            MarketRegime.CRISIS: {'bullish': 0.4, 'bearish': -0.4}
        }
        
        return thresholds.get(regime, {'bullish': 0.15, 'bearish': -0.15})


class NewsScraper:
    """Scraper for financial news articles.
    
    Collects news articles from various financial news sources
    for sentiment analysis.
    """
    
    def __init__(self):
        """Initialize the news scraper."""
        self.sources = [
            'bloomberg',
            'reuters',
            'cnbc',
            'wsj',
            'ft',
            'marketwatch',
            'investing.com',
            'seekingalpha'
        ]
        logger.info("NewsScraper initialized")
    
    def get_news(self, symbol: str, days: int = 1) -> List[Dict]:
        """Get news articles for a specific symbol.
        
        Args:
            symbol: Trading symbol to get news for
            days: Number of days to look back
            
        Returns:
            List of dictionaries with news data
        """
        # Validate input parameters
        if not isinstance(symbol, str) or not symbol:
            raise DataValidationError(f"Invalid symbol: {symbol}")
        if not isinstance(days, int) or days < 1:
            raise DataValidationError(f"Invalid days parameter: {days}")
        try:
            
            logger.info(f"Getting news for {symbol} from past {days} days")
            
            # This is a placeholder for actual news scraping
            # In a real implementation, this would use APIs or web scraping
            
            # Generate mock news data for demonstration
            news_items = []
            
            # Current date for reference
            now = datetime.now()
            
            # Generate random news items
            
            # Sample headlines and content snippets
            bullish_headlines = [
                f"{symbol} Surges on Strong Earnings",
                f"Analysts Upgrade {symbol} to Buy",
                f"{symbol} Announces New Product Line",
                f"Market Rally Boosts {symbol}",
                f"{symbol} Exceeds Expectations"
            ]
            
            bearish_headlines = [
                f"{symbol} Falls After Earnings Miss",
                f"Analysts Downgrade {symbol}",
                f"{symbol} Faces Regulatory Challenges",
                f"Market Selloff Hits {symbol}",
                f"{symbol} Cuts Guidance"
            ]
            
            neutral_headlines = [
                f"{symbol} Announces Management Changes",
                f"{symbol} to Present at Industry Conference",
                f"{symbol} Trading Sideways After News",
                f"Any news on {symbol}?",
                f"Holding {symbol} for now"
            ]
            
            # Simulate processing time
            for _ in range(5):
                time.sleep(0.05)
            
            # Generate news items
            for _ in range(5):  # Generate 5 mock news items
                # Randomly select sentiment
                sentiment_type = random.choice(['bullish', 'bearish', 'neutral'])
                
                # Select headline based on sentiment
                if sentiment_type == 'bullish':
                    headline = random.choice(bullish_headlines)
                elif sentiment_type == 'bearish':
                    headline = random.choice(bearish_headlines)
                else:
                    headline = random.choice(neutral_headlines)
                    
                # Generate random date within the specified days
                random_days = random.uniform(0, days)
                news_date = now - timedelta(days=random_days)
                
                # Generate mock content
                content = f"This is a mock news article about {symbol}. " * 3
                
                # Add to news items
                news_items.append({
                    'title': headline,
                    'content': content,
                    'date': news_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': random.choice(self.sources)
                })
            
            logger.info(f"Retrieved {len(news_items)} news items for {symbol}")
            return news_items
        except (requests.RequestException, ConnectionError) as e:
            logger.error(f"Network error fetching news for {symbol}: {e}")
            raise NewsScrapingError(f"Network error: {e}") from e
        except DataValidationError as e:
            logger.error(f"Validation error in news data for {symbol}: {e}")
            raise e
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Data processing error for {symbol}: {e}")
            raise ProcessingError(f"Error processing news data: {e}") from e


class SocialMediaMonitor:
    """Monitor for social media sentiment about financial markets.
    
    Tracks social media mentions and sentiment about specific
    trading symbols and the overall market.
    """
    
    def __init__(self):
        """Initialize the social media monitor."""
        self.platforms = [
            'twitter',
            'reddit',
            'stocktwits',
            'telegram',
            'discord'
        ]
        logger.info("SocialMediaMonitor initialized")
    
    def get_posts(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get social media posts about a specific symbol.
        
        Args:
            symbol: Trading symbol to get posts for
            hours: Number of hours to look back
            
        Returns:
            List of dictionaries with social media post data
        """
        # Validate input parameters
        if not isinstance(symbol, str) or not symbol:
            raise DataValidationError(f"Invalid symbol: {symbol}")
        if not isinstance(hours, int) or hours < 1:
            raise DataValidationError(f"Invalid hours parameter: {hours}")
        try:
            
            logger.info(f"Getting social media posts for {symbol} from past {hours} hours")
            
            # This is a placeholder for actual social media monitoring
            # In a real implementation, this would use APIs
            
            # Generate mock social media data for demonstration
            posts = []
            
            # Current date for reference
            now = datetime.now()
            
            # Generate random posts
            
            # Sample post templates
            bullish_posts = [
                f"Just bought more ${symbol}! Looking strong!",
                f"${symbol} is breaking out! Target price +20%",
                f"Earnings for ${symbol} will crush expectations",
                f"${symbol} chart looks bullish, ready to moon",
                f"Accumulating ${symbol} at these levels, great opportunity"
            ]
            
            bearish_posts = [
                f"Sold all my ${symbol}, looking weak",
                f"${symbol} breaking down, target -15%",
                f"Earnings will disappoint for ${symbol}",
                f"${symbol} chart looks terrible, avoid",
                f"Shorting ${symbol} at these levels, overvalued"
            ]
            
            neutral_posts = [
                f"Watching ${symbol} closely",
                f"What's everyone thinking about ${symbol}?",
                f"${symbol} trading sideways, waiting for a move",
                f"Any news on ${symbol}?",
                f"Holding ${symbol} for now"
            ]
            
            # Generate posts
            for _ in range(10):  # Generate 10 mock posts
                # Randomly select sentiment
                sentiment_type = random.choice(['bullish', 'bearish', 'neutral'])
                
                # Select post based on sentiment
                if sentiment_type == 'bullish':
                    text = random.choice(bullish_posts)
                elif sentiment_type == 'bearish':
                    text = random.choice(bearish_posts)
                else:
                    text = random.choice(neutral_posts)
                    
                # Generate random timestamp within the specified hours
                random_hours = random.uniform(0, hours)
                post_time = now - timedelta(hours=random_hours)
                
                # Add to posts
                posts.append({
                    'text': text,
                    'platform': random.choice(self.platforms),
                    'timestamp': post_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'likes': random.randint(0, 100),
                    'replies': random.randint(0, 20)
                })
            
            logger.info(f"Retrieved {len(posts)} social media posts for {symbol}")
            return posts
        except (requests.RequestException, ConnectionError) as e:
            logger.error(f"Network error fetching social media for {symbol}: {e}")
            raise SocialMediaError(f"Network error: {e}") from e
        except DataValidationError as e:
            logger.error(f"Validation error in social media data for {symbol}: {e}")
            raise e
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Data processing error for {symbol}: {e}")
            raise ProcessingError(f"Error processing social media data: {e}") from e
