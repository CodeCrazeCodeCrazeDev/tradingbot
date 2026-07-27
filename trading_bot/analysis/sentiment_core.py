"""
Core Sentiment Analysis Module for Financial Markets
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import re
import json
import os
import pickle
from collections import defaultdict, Counter

# NLP libraries
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from scipy.special import softmax

# Lazy imports for heavy dependencies
_spacy = None
_transformers_pipeline = None
_transformers_model = None
_transformers_tokenizer = None
TRANSFORMERS_AVAILABLE = False
SPACY_AVAILABLE = False

def _lazy_import_spacy():
    """Lazy import spacy"""
    global _spacy, SPACY_AVAILABLE
    if _spacy is not None:
        return SPACY_AVAILABLE
    try:
        import spacy as sp
        _spacy = sp
        SPACY_AVAILABLE = True
    except ImportError:
        SPACY_AVAILABLE = False
    return SPACY_AVAILABLE

def _lazy_import_transformers():
    """Lazy import transformers to avoid import-time errors"""
    global _transformers_pipeline, _transformers_model, _transformers_tokenizer, TRANSFORMERS_AVAILABLE
    if _transformers_pipeline is not None or TRANSFORMERS_AVAILABLE is False:
        return TRANSFORMERS_AVAILABLE
    try:
        from transformers import pipeline as tfp
        from transformers import AutoModelForSequenceClassification as tfm
        from transformers import AutoTokenizer as tft
        _transformers_pipeline = tfp
        _transformers_model = tfm
        _transformers_tokenizer = tft
        TRANSFORMERS_AVAILABLE = True
    except (ImportError, Exception) as e:
        logging.getLogger(__name__).debug(f"Transformers not available: {e}")
        TRANSFORMERS_AVAILABLE = False
    return TRANSFORMERS_AVAILABLE
import numpy
import pandas

logger = logging.getLogger(__name__)

# Download NLTK resources if not already present
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    text: str
    score: float  # -1.0 to 1.0, negative to positive
    magnitude: float  # 0.0 to 1.0, strength of sentiment
    compound: float  # VADER compound score
    polarity: str  # 'positive', 'negative', 'neutral'
    subjectivity: float  # 0.0 to 1.0, factual to subjective
    entities: List[Dict[str, Any]]  # Named entities
    topics: List[str]  # Main topics
    timestamp: datetime
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'score': self.score,
            'magnitude': self.magnitude,
            'compound': self.compound,
            'polarity': self.polarity,
            'subjectivity': self.subjectivity,
            'entities': self.entities,
            'topics': self.topics,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


@dataclass
class AssetSentiment:
    """Aggregated sentiment for an asset"""
    ticker: str
    score: float  # -1.0 to 1.0, negative to positive
    magnitude: float  # 0.0 to 1.0, strength of sentiment
    volume: int  # Number of mentions
    sources: Dict[str, float]  # Source to sentiment score
    recent_change: float  # Change in sentiment over recent period
    trending_topics: List[str]  # Trending topics related to asset
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'score': self.score,
            'magnitude': self.magnitude,
            'volume': self.volume,
            'sources': self.sources,
            'recent_change': self.recent_change,
            'trending_topics': self.trending_topics,
            'timestamp': self.timestamp.isoformat()
        }


class SentimentAnalyzer:
    """
    Core sentiment analysis for financial markets
    
    Features:
    - Multiple sentiment analysis models
    - Entity recognition
    - Topic extraction
    - Sentiment aggregation
    - Trend detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize models
        self.models = {}
        self.initialize_models()
        
        # Financial lexicon
        self.financial_lexicon = self._load_financial_lexicon()
        
        # Entity mapping
        self.entity_ticker_map = self._load_entity_ticker_map()
        
        # Sentiment history
        self.sentiment_history = defaultdict(list)
        
        # Maximum history to keep
        self.max_history = self.config.get('max_history', 1000)
        
        # Sentiment cache path
        self.cache_path = self.config.get('cache_path', 'sentiment_history.db')
        
        # Load cached history if available
        self._load_cache()
        
        logger.info("Sentiment Analyzer initialized")
    
    def initialize_models(self):
        """Initialize NLP models"""
        # Initialize VADER
        self.models['vader'] = SentimentIntensityAnalyzer()
        
        try:
            # Initialize spaCy
            if _lazy_import_spacy():
                self.models['spacy'] = _spacy.load('en_core_web_sm')
            else:
                raise ImportError("spaCy not available")
            logger.info("Loaded spaCy model")
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {e}")
            self.models['spacy'] = None
        
        # Initialize FinBERT if requested
        if self.config.get('use_finbert', False):
            try:
                model_name = "ProsusAI/finbert"
                if _lazy_import_transformers():
                    self.models['finbert'] = _transformers_pipeline("sentiment-analysis", model=model_name)
                else:
                    raise ImportError("Transformers not available")
                logger.info("Loaded FinBERT model")
            except Exception as e:
                logger.warning(f"Could not load FinBERT model: {e}")
                self.models['finbert'] = None
        
        # Initialize RoBERTa if requested
        if self.config.get('use_roberta', False):
            try:
                model_name = "cardiffnlp/twitter-roberta-base-sentiment"
                if _lazy_import_transformers():
                    model = _transformers_model.from_pretrained(model_name)
                    tokenizer = _transformers_tokenizer.from_pretrained(model_name)
                else:
                    raise ImportError("Transformers not available")
                self.models['roberta'] = {'model': model, 'tokenizer': tokenizer}
                logger.info("Loaded RoBERTa model")
            except Exception as e:
                logger.warning(f"Could not load RoBERTa model: {e}")
                self.models['roberta'] = None
    
    def _load_financial_lexicon(self) -> Dict[str, float]:
        """Load financial sentiment lexicon"""
        # Default financial lexicon
        lexicon = {
            # Positive financial terms
            'bullish': 0.8,
            'outperform': 0.7,
            'upgrade': 0.6,
            'beat': 0.5,
            'growth': 0.5,
            'profit': 0.5,
            'gain': 0.4,
            'positive': 0.4,
            'up': 0.3,
            'high': 0.3,
            'rise': 0.3,
            'improve': 0.3,
            'recovery': 0.3,
            'opportunity': 0.3,
            'strong': 0.3,
            'success': 0.3,
            'momentum': 0.2,
            'advantage': 0.2,
            
            # Negative financial terms
            'bearish': -0.8,
            'underperform': -0.7,
            'downgrade': -0.6,
            'miss': -0.5,
            'loss': -0.5,
            'decline': -0.5,
            'negative': -0.4,
            'down': -0.3,
            'low': -0.3,
            'fall': -0.3,
            'drop': -0.3,
            'weak': -0.3,
            'risk': -0.3,
            'concern': -0.3,
            'volatile': -0.2,
            'caution': -0.2,
            'uncertainty': -0.2,
            'pressure': -0.2
        }
        
        # Load custom lexicon if provided
        custom_lexicon_path = self.config.get('financial_lexicon_path')
        if custom_lexicon_path and os.path.exists(custom_lexicon_path):
            try:
                with open(custom_lexicon_path, 'r') as f:
                    custom_lexicon = json.load(f)
                lexicon.update(custom_lexicon)
                logger.info(f"Loaded custom financial lexicon from {custom_lexicon_path}")
            except Exception as e:
                logger.warning(f"Error loading custom lexicon: {e}")
        
        return lexicon
    
    def _load_entity_ticker_map(self) -> Dict[str, str]:
        """Load entity to ticker mapping"""
        # Default entity-ticker map
        entity_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'amazon': 'AMZN',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'facebook': 'META',
            'meta': 'META',
            'tesla': 'TSLA',
            'netflix': 'NFLX',
            'nvidia': 'NVDA',
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'goldman sachs': 'GS',
            'bank of america': 'BAC',
            'exxon': 'XOM',
            'exxonmobil': 'XOM',
            'chevron': 'CVX',
            'walmart': 'WMT',
            'disney': 'DIS',
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'mcdonalds': 'MCD',
            'mcdonald\'s': 'MCD',
            'bitcoin': 'BTC',
            'ethereum': 'ETH'
        }
        
        # Load custom mapping if provided
        custom_map_path = self.config.get('entity_ticker_map_path')
        if custom_map_path and os.path.exists(custom_map_path):
            try:
                with open(custom_map_path, 'r') as f:
                    custom_map = json.load(f)
                entity_map.update(custom_map)
                logger.info(f"Loaded custom entity-ticker map from {custom_map_path}")
            except Exception as e:
                logger.warning(f"Error loading custom entity-ticker map: {e}")
        
        return entity_map
    
    def analyze_text(self, text: str, source: str = 'unknown',
                   timestamp: Optional[datetime] = None) -> SentimentResult:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            source: Source of the text
            timestamp: Timestamp of the text (default: now)
            
        Returns:
            SentimentResult with analysis
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # VADER sentiment
        vader_scores = self.models['vader'].polarity_scores(cleaned_text)
        compound = vader_scores['compound']
        
        # Adjust with financial lexicon
        adjusted_score = self._apply_financial_lexicon(cleaned_text, compound)
        
        # Determine polarity
        if adjusted_score > 0.05:
            polarity = 'positive'
        elif adjusted_score < -0.05:
            polarity = 'negative'
        else:
            polarity = 'neutral'
        
        # Calculate magnitude (strength of sentiment)
        magnitude = min(1.0, abs(adjusted_score) * 2)
        
        # Extract entities
        entities = self._extract_entities(cleaned_text)
        
        # Extract topics
        topics = self._extract_topics(cleaned_text)
        
        # Calculate subjectivity
        subjectivity = self._calculate_subjectivity(cleaned_text)
        
        # Create result
        result = SentimentResult(
            text=cleaned_text,
            score=adjusted_score,
            magnitude=magnitude,
            compound=compound,
            polarity=polarity,
            subjectivity=subjectivity,
            entities=entities,
            topics=topics,
            timestamp=timestamp,
            source=source
        )
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _apply_financial_lexicon(self, text: str, base_score: float) -> float:
        """Apply financial lexicon to adjust sentiment score"""
        words = word_tokenize(text.lower())
        
        # Filter out stopwords
        stop_words = set(stopwords.words('english'))
        words = [w for w in words if w not in stop_words]
        
        # Calculate lexicon adjustment
        adjustment = 0.0
        word_count = 0
        
        for word in words:
            if word in self.financial_lexicon:
                adjustment += self.financial_lexicon[word]
                word_count += 1
        
        # Apply adjustment
        if word_count > 0:
            # Weight of lexicon vs. base score
            lexicon_weight = min(0.7, 0.1 * word_count)
            base_weight = 1.0 - lexicon_weight
            
            # Combine scores
            adjusted_score = base_weight * base_score + lexicon_weight * (adjustment / word_count)
        else:
            adjusted_score = base_score
        
        # Ensure score is in range [-1, 1]
        return max(-1.0, min(1.0, adjusted_score))
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        # Use spaCy if available
        if self.models.get('spacy'):
            doc = self.models['spacy'](text)
            
            for ent in doc.ents:
                # Map entity to ticker if possible
                ticker = self._map_entity_to_ticker(ent.text.lower())
                
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'ticker': ticker
                })
        else:
            # Simple entity extraction based on entity-ticker map
            for entity, ticker in self.entity_ticker_map.items():
                if entity in text.lower():
                    entities.append({
                        'text': entity,
                        'label': 'ORG',
                        'ticker': ticker
                    })
        
        return entities
    
    def _map_entity_to_ticker(self, entity: str) -> Optional[str]:
        """Map entity to ticker symbol"""
        return self.entity_ticker_map.get(entity.lower())
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Simple topic extraction based on noun phrases
        topics = []
        
        if self.models.get('spacy'):
            doc = self.models['spacy'](text)
            
            # Extract noun chunks
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit to 3 words
                    topics.append(chunk.text.lower())
        
        # Limit to top 5 topics
        return list(set(topics))[:5]
    
    def _calculate_subjectivity(self, text: str) -> float:
        """Calculate subjectivity score (0.0 to 1.0)"""
        # Simple subjectivity based on presence of subjective words
        subjective_words = {
            'think', 'believe', 'feel', 'opinion', 'seems', 'appears',
            'possibly', 'probably', 'maybe', 'perhaps', 'likely', 'unlikely',
            'suggest', 'estimate', 'expect', 'anticipate', 'forecast',
            'hope', 'fear', 'worry', 'concern', 'confident', 'optimistic',
            'pessimistic', 'bullish', 'bearish'
        }
        
        words = word_tokenize(text.lower())
        subjective_count = sum(1 for word in words if word in subjective_words)
        
        # Calculate subjectivity score
        if len(words) > 0:
            return min(1.0, subjective_count / len(words) * 5)  # Scale up for better distribution
        else:
            return 0.0
    
    def analyze_texts(self, texts: List[Dict[str, Any]]) -> List[SentimentResult]:
        """
        Analyze sentiment of multiple texts
        
        Args:
            texts: List of dictionaries with 'text', 'source', and optional 'timestamp'
            
        Returns:
            List of SentimentResult objects
        """
        results = []
        
        for text_item in texts:
            text = text_item.get('text', '')
            source = text_item.get('source', 'unknown')
            timestamp = text_item.get('timestamp')
            
            if not timestamp:
                timestamp = datetime.now()
            elif isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now()
            
            result = self.analyze_text(text, source, timestamp)
            results.append(result)
        
        return results
    
    def get_asset_sentiment(self, ticker: str, lookback_hours: int = 24) -> Optional[AssetSentiment]:
        """
        Get aggregated sentiment for an asset
        
        Args:
            ticker: Asset ticker symbol
            lookback_hours: Hours to look back
            
        Returns:
            AssetSentiment object or None if no data
        """
        # Get sentiment history for ticker
        history = self.sentiment_history.get(ticker, [])
        
        if not history:
            return None
        
        # Filter by lookback period
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent = [h for h in history if h.timestamp >= cutoff]
        
        if not recent:
            return None
        
        # Calculate aggregated sentiment
        scores = [h.score for h in recent]
        magnitudes = [h.magnitude for h in recent]
        
        avg_score = sum(scores) / len(scores)
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        
        # Calculate source breakdown
        sources = defaultdict(list)
        for h in recent:
            sources[h.source].append(h.score)
        
        source_scores = {
            source: sum(scores) / len(scores)
            for source, scores in sources.items()
        }
        
        # Calculate recent change
        if len(recent) >= 2:
            # Split into two periods
            mid_point = len(recent) // 2
            first_half = recent[:mid_point]
            second_half = recent[mid_point:]
            
            first_avg = sum(h.score for h in first_half) / len(first_half)
            second_avg = sum(h.score for h in second_half) / len(second_half)
            
            recent_change = second_avg - first_avg
        else:
            recent_change = 0.0
        
        # Extract trending topics
        topics = []
        for h in recent:
            topics.extend(h.topics)
        
        # Count topic frequency
        topic_counts = Counter(topics)
        trending_topics = [topic for topic, count in topic_counts.most_common(5)]
        
        # Create result
        result = AssetSentiment(
            ticker=ticker,
            score=avg_score,
            magnitude=avg_magnitude,
            volume=len(recent),
            sources=source_scores,
            recent_change=recent_change,
            trending_topics=trending_topics,
            timestamp=datetime.now()
        )
        
        return result
    
    def update_sentiment_history(self, results: List[SentimentResult]):
        """
        Update sentiment history with new results
        
        Args:
            results: List of SentimentResult objects
        """
        for result in results:
            # Extract tickers from entities
            tickers = set()
            for entity in result.entities:
                if entity.get('ticker'):
                    tickers.add(entity.get('ticker'))
            
            # Add result to history for each ticker
            for ticker in tickers:
                if ticker not in self.sentiment_history:
                    self.sentiment_history[ticker] = []
                
                self.sentiment_history[ticker].append(result)
                
                # Limit history size
                if len(self.sentiment_history[ticker]) > self.max_history:
                    self.sentiment_history[ticker] = self.sentiment_history[ticker][-self.max_history:]
        
        # Save cache periodically
        self._save_cache()
    
    def _save_cache(self):
        """Save sentiment history to cache"""
        try:
            with open(self.cache_path, 'wb') as f:
                pickle.dump(self.sentiment_history, f)
            logger.debug(f"Saved sentiment history to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Error saving sentiment cache: {e}")
    
    def _load_cache(self):
        """Load sentiment history from cache"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'rb') as f:
                    self.sentiment_history = pickle.load(f)
                logger.info(f"Loaded sentiment history from {self.cache_path}")
            except Exception as e:
                logger.warning(f"Error loading sentiment cache: {e}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = SentimentAnalyzer()
    
    # Example texts
    texts = [
        {
            'text': "Apple's new iPhone sales are exceeding expectations, analysts are bullish on the stock.",
            'source': 'news',
            'timestamp': datetime.now()
        },
        {
            'text': "Tesla faces production challenges as demand weakens in China market.",
            'source': 'twitter',
            'timestamp': datetime.now()
        },
        {
            'text': "Microsoft reported strong cloud revenue growth, beating analyst estimates.",
            'source': 'news',
            'timestamp': datetime.now()
        }
    ]
    
    # Analyze texts
    results = analyzer.analyze_texts(texts)
    
    # Print results
    for result in results:
        logger.info(f"Text: {result.text}")
        logger.info(f"Score: {result.score:.2f}, Magnitude: {result.magnitude:.2f}")
        logger.info(f"Polarity: {result.polarity}")
        logger.info(f"Entities: {result.entities}")
        logger.info(f"Topics: {result.topics}")
        print()
    
    # Update history
    analyzer.update_sentiment_history(results)
    
    # Get asset sentiment
    apple_sentiment = analyzer.get_asset_sentiment('AAPL')
    if apple_sentiment:
        logger.info(f"AAPL Sentiment: {apple_sentiment.score:.2f}")
        logger.info(f"Volume: {apple_sentiment.volume} mentions")
        logger.info(f"Trending topics: {apple_sentiment.trending_topics}")
