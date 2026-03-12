"""
Sentiment Analysis Engine
==========================

Multi-source sentiment aggregation for trading signals.

Data Sources:
- Financial News (Reuters, Bloomberg, WSJ)
- Social Media (Twitter/X, Reddit, StockTwits)
- SEC Filings & Transcripts
- Macroeconomic Data

Processing:
- FinBERT for financial text
- LLM-based sentiment analysis
- Domain-specific lexicons (Loughran-McDonald)
- Aspect-based sentiment
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import re
import json
import asyncio
import hashlib

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Using rule-based sentiment.")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class SentimentSource(Enum):
    """Sources of sentiment data"""
    NEWS = "news"
    TWITTER = "twitter"
    REDDIT = "reddit"
    STOCKTWITS = "stocktwits"
    SEC_FILINGS = "sec_filings"
    EARNINGS_CALLS = "earnings_calls"
    ANALYST_REPORTS = "analyst_reports"
    ECONOMIC_DATA = "economic_data"


class SentimentType(Enum):
    """Types of sentiment analysis"""
    OVERALL = "overall"
    ASPECT = "aspect"
    ENTITY = "entity"
    EVENT = "event"


@dataclass
class SentimentSignal:
    """Individual sentiment signal"""
    source: SentimentSource
    timestamp: datetime
    symbol: str
    score: float  # -100 to +100
    confidence: float  # 0 to 1
    magnitude: float  # Strength of sentiment
    text: str = ""
    entities: List[str] = field(default_factory=list)
    aspects: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'score': self.score,
            'confidence': self.confidence,
            'magnitude': self.magnitude,
            'entities': self.entities,
            'aspects': self.aspects,
        }


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across sources"""
    symbol: str
    timestamp: datetime
    overall_score: float  # -100 to +100
    confidence: float
    source_scores: Dict[str, float]
    momentum: float  # Rate of change
    divergence: float  # Sentiment vs price divergence
    extreme_level: str  # 'extreme_bullish', 'bullish', 'neutral', 'bearish', 'extreme_bearish'
    signal_count: int
    
    @property
    def is_extreme(self) -> bool:
        return abs(self.overall_score) > 70
    
    @property
    def direction(self) -> str:
        if self.overall_score > 30:
            return 'bullish'
        elif self.overall_score < -30:
            return 'bearish'
        return 'neutral'


class LoughranMcDonaldLexicon:
    """
    Loughran-McDonald Financial Sentiment Lexicon
    Domain-specific word lists for financial text
    """
    
    def __init__(self):
        # Positive words in financial context
        self.positive_words = {
            'achieve', 'achieved', 'achieving', 'advancement', 'advantage',
            'beneficial', 'benefit', 'benefits', 'best', 'better', 'boost',
            'breakthrough', 'creative', 'deliver', 'delivered', 'delivering',
            'efficient', 'enhance', 'enhanced', 'excellent', 'exceptional',
            'favorable', 'gain', 'gained', 'gains', 'good', 'great', 'greater',
            'growth', 'highest', 'improve', 'improved', 'improvement', 'improving',
            'increase', 'increased', 'increases', 'increasing', 'innovative',
            'leading', 'opportunities', 'opportunity', 'optimistic', 'outperform',
            'positive', 'profit', 'profitable', 'profitability', 'progress',
            'prosper', 'record', 'recover', 'recovery', 'revenue', 'rise',
            'rising', 'solid', 'strength', 'strong', 'stronger', 'succeed',
            'success', 'successful', 'superior', 'surpass', 'upturn', 'upward',
        }
        
        # Negative words in financial context
        self.negative_words = {
            'abandon', 'adverse', 'against', 'bankruptcy', 'burden', 'catastrophe',
            'challenge', 'challenges', 'closure', 'concern', 'concerns', 'crisis',
            'critical', 'damage', 'damages', 'decline', 'declined', 'declining',
            'decrease', 'decreased', 'decreases', 'decreasing', 'default',
            'deficit', 'delay', 'delayed', 'deteriorate', 'deteriorating',
            'difficult', 'difficulties', 'difficulty', 'disappoint', 'disappointed',
            'disappointing', 'disappointment', 'downturn', 'drop', 'dropped',
            'failure', 'fall', 'fallen', 'falling', 'fear', 'fears', 'fraud',
            'impair', 'impaired', 'impairment', 'inability', 'inadequate',
            'investigation', 'lawsuit', 'layoff', 'layoffs', 'litigation',
            'loss', 'losses', 'lower', 'lowest', 'negative', 'negligence',
            'penalty', 'problem', 'problems', 'recession', 'restructuring',
            'risk', 'risks', 'risky', 'shortage', 'shortfall', 'slump',
            'slowdown', 'struggle', 'struggling', 'terminate', 'terminated',
            'threat', 'threats', 'trouble', 'troubled', 'uncertain', 'uncertainty',
            'unfavorable', 'unprofitable', 'volatile', 'volatility', 'weak',
            'weaken', 'weakened', 'weakness', 'worse', 'worsen', 'worsening', 'worst',
        }
        
        # Uncertainty words
        self.uncertainty_words = {
            'almost', 'anticipate', 'anticipated', 'apparent', 'appear',
            'appeared', 'appearing', 'appears', 'approximate', 'approximately',
            'assume', 'assumed', 'assuming', 'assumption', 'assumptions',
            'believe', 'believed', 'believes', 'conceivable', 'conditional',
            'depend', 'depended', 'depending', 'depends', 'doubt', 'doubtful',
            'estimate', 'estimated', 'estimates', 'expect', 'expected',
            'expecting', 'forecast', 'forecasted', 'forecasting', 'forecasts',
            'hope', 'hoped', 'hopeful', 'hopefully', 'hoping', 'if', 'indicate',
            'indicated', 'indicates', 'indicating', 'indication', 'likelihood',
            'likely', 'may', 'maybe', 'might', 'nearly', 'pending', 'perhaps',
            'possible', 'possibly', 'potential', 'potentially', 'predict',
            'predicted', 'predicting', 'prediction', 'predictions', 'predicts',
            'preliminary', 'presume', 'presumed', 'presumes', 'presuming',
            'probable', 'probably', 'project', 'projected', 'projecting',
            'projection', 'projections', 'projects', 'risk', 'risky', 'roughly',
            'seem', 'seemed', 'seeming', 'seemingly', 'seems', 'should',
            'sometime', 'sometimes', 'somewhat', 'somewhere', 'speculate',
            'speculated', 'speculates', 'speculating', 'speculation', 'suggest',
            'suggested', 'suggesting', 'suggestion', 'suggestions', 'suggests',
            'suppose', 'supposed', 'supposedly', 'supposes', 'supposing',
            'tentative', 'tentatively', 'uncertain', 'uncertainty', 'unclear',
            'unknown', 'unlikely', 'unpredictable', 'unsure', 'vary', 'varied',
        }
        
        # Litigious words
        self.litigious_words = {
            'adjudicate', 'adjudicated', 'adjudicates', 'adjudicating',
            'allegation', 'allegations', 'allege', 'alleged', 'allegedly',
            'alleges', 'alleging', 'appeal', 'appealed', 'appealing', 'appeals',
            'arbitrate', 'arbitrated', 'arbitrates', 'arbitrating', 'arbitration',
            'claim', 'claimed', 'claiming', 'claims', 'claimant', 'claimants',
            'complaint', 'complaints', 'court', 'courts', 'defendant',
            'defendants', 'deposition', 'depositions', 'discovery', 'dismiss',
            'dismissed', 'dismisses', 'dismissing', 'dismissal', 'dismissals',
            'dispute', 'disputed', 'disputes', 'disputing', 'hearing', 'hearings',
            'injunction', 'injunctions', 'infringe', 'infringed', 'infringement',
            'infringements', 'infringes', 'infringing', 'judge', 'judges',
            'judgment', 'judgments', 'judicial', 'jurisdiction', 'jurisdictions',
            'jury', 'law', 'laws', 'lawsuit', 'lawsuits', 'lawyer', 'lawyers',
            'legal', 'legally', 'legislate', 'legislated', 'legislates',
            'legislating', 'legislation', 'legislative', 'liabilities',
            'liability', 'liable', 'litigate', 'litigated', 'litigates',
            'litigating', 'litigation', 'plaintiff', 'plaintiffs', 'plea',
            'plead', 'pleaded', 'pleading', 'pleadings', 'pleads', 'pleas',
            'prosecute', 'prosecuted', 'prosecutes', 'prosecuting', 'prosecution',
            'prosecutor', 'prosecutors', 'regulatory', 'ruling', 'rulings',
            'settle', 'settled', 'settlement', 'settlements', 'settles',
            'settling', 'subpoena', 'subpoenaed', 'subpoenas', 'sue', 'sued',
            'sues', 'suing', 'suit', 'suits', 'summon', 'summoned', 'summoning',
            'summons', 'testify', 'testified', 'testifies', 'testifying',
            'testimony', 'trial', 'trials', 'tribunal', 'tribunals', 'verdict',
            'verdicts', 'violate', 'violated', 'violates', 'violating',
            'violation', 'violations',
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text using Loughran-McDonald lexicon"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {'score': 0, 'positive': 0, 'negative': 0, 'uncertainty': 0, 'litigious': 0}
        
        positive_count = sum(1 for w in words if w in self.positive_words)
        negative_count = sum(1 for w in words if w in self.negative_words)
        uncertainty_count = sum(1 for w in words if w in self.uncertainty_words)
        litigious_count = sum(1 for w in words if w in self.litigious_words)
        
        # Calculate sentiment score
        net_sentiment = (positive_count - negative_count) / total_words * 100
        
        return {
            'score': net_sentiment,
            'positive': positive_count / total_words,
            'negative': negative_count / total_words,
            'uncertainty': uncertainty_count / total_words,
            'litigious': litigious_count / total_words,
            'word_count': total_words,
        }


class FinBERTAnalyzer:
    """
    FinBERT-based sentiment analysis for financial text
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = 'cpu'
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"FinBERT loaded on {self.device}")
            except Exception as e:
                logger.warning(f"Failed to load FinBERT: {e}")
                self.model = None
        
        # Fallback lexicon
        self.lexicon = LoughranMcDonaldLexicon()
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of financial text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if not text or len(text.strip()) == 0:
            return {'score': 0, 'confidence': 0, 'label': 'neutral'}
        
        if self.model is not None and TRANSFORMERS_AVAILABLE:
            return self._analyze_with_model(text)
        else:
            return self._analyze_with_lexicon(text)
    
    def _analyze_with_model(self, text: str) -> Dict[str, Any]:
        """Analyze using FinBERT model"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)[0]
            
            # FinBERT labels: positive, negative, neutral
            labels = ['positive', 'negative', 'neutral']
            probs = probs.cpu().numpy()
            
            # Calculate score (-100 to +100)
            score = (probs[0] - probs[1]) * 100
            
            # Get predicted label
            pred_idx = np.argmax(probs)
            label = labels[pred_idx]
            confidence = float(probs[pred_idx])
            
            return {
                'score': float(score),
                'confidence': confidence,
                'label': label,
                'probabilities': {
                    'positive': float(probs[0]),
                    'negative': float(probs[1]),
                    'neutral': float(probs[2]),
                }
            }
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return self._analyze_with_lexicon(text)
    
    def _analyze_with_lexicon(self, text: str) -> Dict[str, Any]:
        """Fallback lexicon-based analysis"""
        result = self.lexicon.analyze(text)
        
        score = result['score']
        if score > 10:
            label = 'positive'
        elif score < -10:
            label = 'negative'
        else:
            label = 'neutral'
        
        confidence = min(abs(score) / 50, 1.0)
        
        return {
            'score': score,
            'confidence': confidence,
            'label': label,
            'lexicon_details': result,
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]


class NewsProcessor:
    """
    Process financial news for sentiment signals
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # News source credibility weights
        self.source_weights = {
            'reuters': 1.0,
            'bloomberg': 1.0,
            'wsj': 0.95,
            'ft': 0.95,
            'cnbc': 0.8,
            'yahoo': 0.7,
            'seekingalpha': 0.6,
            'default': 0.5,
        }
        
        # Cache for deduplication
        self.seen_hashes: set = set()
        self.news_buffer: deque = deque(maxlen=1000)
        
    def process_article(self, article: Dict[str, Any]) -> Optional[SentimentSignal]:
        """
        Process a news article
        
        Args:
            article: Dictionary with 'title', 'content', 'source', 'timestamp', 'symbols'
            
        Returns:
            SentimentSignal or None if duplicate
        """
        # Deduplication
        content_hash = hashlib.md5(
            (article.get('title', '') + article.get('content', '')[:500]).encode()
        ).hexdigest()
        
        if content_hash in self.seen_hashes:
            return None
        self.seen_hashes.add(content_hash)
        
        # Combine title and content for analysis
        text = article.get('title', '') + '. ' + article.get('content', '')[:1000]
        
        # Analyze sentiment
        result = self.analyzer.analyze(text)
        
        # Get source weight
        source = article.get('source', 'default').lower()
        source_weight = self.source_weights.get(source, self.source_weights['default'])
        
        # Extract symbols mentioned
        symbols = article.get('symbols', [])
        if not symbols:
            symbols = self._extract_symbols(text)
        
        # Create signal for each symbol
        signals = []
        for symbol in symbols:
            signal = SentimentSignal(
                source=SentimentSource.NEWS,
                timestamp=article.get('timestamp', datetime.now()),
                symbol=symbol,
                score=result['score'] * source_weight,
                confidence=result['confidence'] * source_weight,
                magnitude=abs(result['score']) / 100,
                text=article.get('title', ''),
                metadata={
                    'source': source,
                    'url': article.get('url', ''),
                    'label': result.get('label', 'neutral'),
                }
            )
            signals.append(signal)
            self.news_buffer.append(signal)
        
        return signals[0] if signals else None
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        # Simple pattern matching for stock symbols
        # In production, use a proper NER model
        pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(pattern, text)
        
        # Filter common words
        common_words = {'A', 'I', 'THE', 'AND', 'OR', 'FOR', 'TO', 'IN', 'ON', 'AT', 'BY', 'CEO', 'CFO', 'IPO', 'ETF', 'NYSE', 'NASDAQ'}
        symbols = [s for s in potential_symbols if s not in common_words and len(s) >= 2]
        
        return symbols[:5]  # Limit to 5 symbols
    
    def get_recent_sentiment(self, symbol: str, hours: int = 24) -> Dict[str, Any]:
        """Get recent sentiment for a symbol"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        relevant = [s for s in self.news_buffer 
                   if s.symbol == symbol and s.timestamp > cutoff]
        
        if not relevant:
            return {'score': 0, 'count': 0, 'confidence': 0}
        
        # Time-weighted average
        total_weight = 0
        weighted_score = 0
        
        for signal in relevant:
            age_hours = (datetime.now() - signal.timestamp).total_seconds() / 3600
            weight = np.exp(-age_hours / 12)  # Decay with 12-hour half-life
            weighted_score += signal.score * weight * signal.confidence
            total_weight += weight * signal.confidence
        
        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        
        return {
            'score': avg_score,
            'count': len(relevant),
            'confidence': min(len(relevant) / 10, 1.0),  # More articles = more confidence
        }


class SocialMediaAnalyzer:
    """
    Analyze social media sentiment (Twitter, Reddit, StockTwits)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # Platform-specific settings
        self.platform_weights = {
            'twitter': 0.7,
            'reddit': 0.6,
            'stocktwits': 0.8,
        }
        
        # Influencer detection
        self.influencer_multiplier = 1.5
        self.influencer_threshold = 10000  # Followers
        
        # Buffers
        self.social_buffer: Dict[str, deque] = {
            'twitter': deque(maxlen=5000),
            'reddit': deque(maxlen=5000),
            'stocktwits': deque(maxlen=5000),
        }
        
        # Spam detection
        self.spam_patterns = [
            r'buy now', r'guaranteed', r'moon', r'rocket',
            r'100x', r'1000x', r'free money', r'get rich',
        ]
        
    def process_post(self, post: Dict[str, Any], platform: str) -> Optional[SentimentSignal]:
        """
        Process a social media post
        
        Args:
            post: Dictionary with 'text', 'timestamp', 'user', 'followers', 'likes', 'symbols'
            platform: 'twitter', 'reddit', or 'stocktwits'
            
        Returns:
            SentimentSignal or None if spam
        """
        text = post.get('text', '')
        
        # Spam detection
        if self._is_spam(text):
            return None
        
        # Analyze sentiment
        result = self.analyzer.analyze(text)
        
        # Calculate weight based on engagement and followers
        followers = post.get('followers', 0)
        likes = post.get('likes', 0)
        
        engagement_weight = min(1 + np.log1p(likes) / 10, 2.0)
        influencer_weight = self.influencer_multiplier if followers > self.influencer_threshold else 1.0
        platform_weight = self.platform_weights.get(platform, 0.5)
        
        total_weight = engagement_weight * influencer_weight * platform_weight
        
        # Extract symbols
        symbols = post.get('symbols', [])
        if not symbols:
            symbols = self._extract_cashtags(text)
        
        signals = []
        for symbol in symbols:
            source_map = {
                'twitter': SentimentSource.TWITTER,
                'reddit': SentimentSource.REDDIT,
                'stocktwits': SentimentSource.STOCKTWITS,
            }
            
            signal = SentimentSignal(
                source=source_map.get(platform, SentimentSource.TWITTER),
                timestamp=post.get('timestamp', datetime.now()),
                symbol=symbol,
                score=result['score'] * total_weight,
                confidence=result['confidence'] * min(total_weight, 1.0),
                magnitude=abs(result['score']) / 100,
                text=text[:200],
                metadata={
                    'platform': platform,
                    'user': post.get('user', ''),
                    'followers': followers,
                    'likes': likes,
                    'is_influencer': followers > self.influencer_threshold,
                }
            )
            signals.append(signal)
            
            if platform in self.social_buffer:
                self.social_buffer[platform].append(signal)
        
        return signals[0] if signals else None
    
    def _is_spam(self, text: str) -> bool:
        """Detect spam posts"""
        text_lower = text.lower()
        
        for pattern in self.spam_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for excessive caps or emojis
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.7:
            return True
        
        return False
    
    def _extract_cashtags(self, text: str) -> List[str]:
        """Extract $SYMBOL cashtags from text"""
        pattern = r'\$([A-Z]{1,5})\b'
        symbols = re.findall(pattern, text.upper())
        return list(set(symbols))[:5]
    
    def get_social_sentiment(self, symbol: str, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated social sentiment for a symbol"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        platform_scores = {}
        total_signals = 0
        
        for platform, buffer in self.social_buffer.items():
            relevant = [s for s in buffer 
                       if s.symbol == symbol and s.timestamp > cutoff]
            
            if relevant:
                # Volume-weighted sentiment
                scores = [s.score for s in relevant]
                confidences = [s.confidence for s in relevant]
                
                weighted_score = np.average(scores, weights=confidences) if confidences else 0
                platform_scores[platform] = {
                    'score': weighted_score,
                    'count': len(relevant),
                }
                total_signals += len(relevant)
        
        # Aggregate across platforms
        if platform_scores:
            overall_score = np.mean([p['score'] for p in platform_scores.values()])
        else:
            overall_score = 0
        
        return {
            'overall_score': overall_score,
            'platform_scores': platform_scores,
            'total_signals': total_signals,
            'confidence': min(total_signals / 50, 1.0),
        }


class SentimentAggregator:
    """
    Aggregates sentiment from all sources into unified signals
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize analyzers
        self.news_processor = NewsProcessor(config.get('news', {}))
        self.social_analyzer = SocialMediaAnalyzer(config.get('social', {}))
        self.finbert = FinBERTAnalyzer()
        
        # Source weights for aggregation
        self.source_weights = {
            SentimentSource.NEWS: self.config.get('news_weight', 0.35),
            SentimentSource.TWITTER: self.config.get('twitter_weight', 0.15),
            SentimentSource.REDDIT: self.config.get('reddit_weight', 0.15),
            SentimentSource.STOCKTWITS: self.config.get('stocktwits_weight', 0.15),
            SentimentSource.SEC_FILINGS: self.config.get('sec_weight', 0.10),
            SentimentSource.EARNINGS_CALLS: self.config.get('earnings_weight', 0.10),
        }
        
        # Sentiment history for momentum calculation
        self.sentiment_history: Dict[str, deque] = {}
        
        # Price data for divergence calculation
        self.price_history: Dict[str, deque] = {}
        
    def add_signal(self, signal: SentimentSignal):
        """Add a sentiment signal to history"""
        symbol = signal.symbol
        
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = deque(maxlen=1000)
        
        self.sentiment_history[symbol].append(signal)
    
    def update_price(self, symbol: str, price: float, timestamp: datetime = None):
        """Update price for divergence calculation"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=1000)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp or datetime.now(),
        })
    
    def get_aggregated_sentiment(self, symbol: str, 
                                 lookback_hours: int = 24) -> AggregatedSentiment:
        """
        Get aggregated sentiment for a symbol
        
        Args:
            symbol: Stock symbol
            lookback_hours: Hours to look back
            
        Returns:
            AggregatedSentiment object
        """
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        
        # Collect signals by source
        source_signals: Dict[SentimentSource, List[SentimentSignal]] = {}
        
        if symbol in self.sentiment_history:
            for signal in self.sentiment_history[symbol]:
                if signal.timestamp > cutoff:
                    if signal.source not in source_signals:
                        source_signals[signal.source] = []
                    source_signals[signal.source].append(signal)
        
        # Calculate source scores
        source_scores = {}
        weighted_sum = 0
        total_weight = 0
        
        for source, signals in source_signals.items():
            if signals:
                # Time-weighted average
                scores = []
                weights = []
                for s in signals:
                    age_hours = (datetime.now() - s.timestamp).total_seconds() / 3600
                    time_weight = np.exp(-age_hours / 12)
                    scores.append(s.score)
                    weights.append(time_weight * s.confidence)
                
                source_score = np.average(scores, weights=weights) if weights else 0
                source_scores[source.value] = source_score
                
                source_weight = self.source_weights.get(source, 0.1)
                weighted_sum += source_score * source_weight * sum(weights)
                total_weight += source_weight * sum(weights)
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Calculate momentum (rate of change)
        momentum = self._calculate_momentum(symbol, lookback_hours)
        
        # Calculate divergence (sentiment vs price)
        divergence = self._calculate_divergence(symbol, lookback_hours)
        
        # Determine extreme level
        if overall_score > 70:
            extreme_level = 'extreme_bullish'
        elif overall_score > 30:
            extreme_level = 'bullish'
        elif overall_score > -30:
            extreme_level = 'neutral'
        elif overall_score > -70:
            extreme_level = 'bearish'
        else:
            extreme_level = 'extreme_bearish'
        
        # Count total signals
        signal_count = sum(len(signals) for signals in source_signals.values())
        
        # Calculate confidence
        confidence = min(signal_count / 20, 1.0) * (1 - abs(divergence) / 2)
        
        return AggregatedSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_score=overall_score,
            confidence=confidence,
            source_scores=source_scores,
            momentum=momentum,
            divergence=divergence,
            extreme_level=extreme_level,
            signal_count=signal_count,
        )
    
    def _calculate_momentum(self, symbol: str, lookback_hours: int) -> float:
        """Calculate sentiment momentum (rate of change)"""
        if symbol not in self.sentiment_history:
            return 0
        
        signals = list(self.sentiment_history[symbol])
        if len(signals) < 2:
            return 0
        
        # Compare recent vs older sentiment
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        mid_point = datetime.now() - timedelta(hours=lookback_hours / 2)
        
        recent = [s.score for s in signals if s.timestamp > mid_point]
        older = [s.score for s in signals if cutoff < s.timestamp <= mid_point]
        
        if not recent or not older:
            return 0
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        return (recent_avg - older_avg) / max(abs(older_avg), 1)
    
    def _calculate_divergence(self, symbol: str, lookback_hours: int) -> float:
        """Calculate sentiment-price divergence"""
        if symbol not in self.sentiment_history or symbol not in self.price_history:
            return 0
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        
        # Get sentiment change
        signals = [s for s in self.sentiment_history[symbol] if s.timestamp > cutoff]
        if len(signals) < 2:
            return 0
        
        sentiment_change = signals[-1].score - signals[0].score
        
        # Get price change
        prices = [p for p in self.price_history[symbol] if p['timestamp'] > cutoff]
        if len(prices) < 2:
            return 0
        
        price_change = (prices[-1]['price'] - prices[0]['price']) / prices[0]['price'] * 100
        
        # Divergence: sentiment and price moving in opposite directions
        if sentiment_change * price_change < 0:
            divergence = abs(sentiment_change - price_change) / 100
        else:
            divergence = 0
        
        return min(divergence, 1.0)
    
    def get_trading_signal(self, symbol: str, dc_signal: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate trading signal based on sentiment
        
        Implements the trading rules from the spec:
        1. Sentiment Confirmation
        2. Sentiment Divergence
        3. Sentiment Regime Filter
        4. Event-Driven Override
        """
        sentiment = self.get_aggregated_sentiment(symbol)
        
        signal = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sentiment_score': sentiment.overall_score,
            'sentiment_direction': sentiment.direction,
            'confidence': sentiment.confidence,
            'action': 'hold',
            'position_adjustment': 1.0,
            'reason': '',
        }
        
        # Rule 1: Sentiment Confirmation
        if dc_signal:
            if dc_signal == 'long' and sentiment.overall_score > 30:
                signal['position_adjustment'] = 1.2  # Increase by 20%
                signal['reason'] = 'Sentiment confirms long signal'
            elif dc_signal == 'short' and sentiment.overall_score < -30:
                signal['position_adjustment'] = 1.2
                signal['reason'] = 'Sentiment confirms short signal'
        
        # Rule 2: Sentiment Divergence
        if sentiment.divergence > 0.3:
            if sentiment.overall_score > 0 and dc_signal == 'short':
                signal['position_adjustment'] *= 0.7  # Reduce exposure
                signal['reason'] += ' | Divergence warning'
            elif sentiment.overall_score < 0 and dc_signal == 'long':
                signal['position_adjustment'] *= 0.7
                signal['reason'] += ' | Divergence warning'
        
        # Rule 3: Sentiment Regime Filter
        if sentiment.is_extreme:
            signal['position_adjustment'] *= 0.5  # Risk-off at extremes
            signal['reason'] += f' | Extreme sentiment ({sentiment.extreme_level})'
        
        # Rule 4: Event-Driven Override
        if sentiment.momentum > 0.5:  # Rapid sentiment change
            signal['action'] = 'pause'
            signal['reason'] += ' | High sentiment volatility - pause trading'
        
        # Determine action
        if signal['action'] != 'pause':
            if sentiment.overall_score > 50 and sentiment.confidence > 0.6:
                signal['action'] = 'bullish_bias'
            elif sentiment.overall_score < -50 and sentiment.confidence > 0.6:
                signal['action'] = 'bearish_bias'
            else:
                signal['action'] = 'neutral'
        
        signal['aggregated_sentiment'] = sentiment.__dict__
        
        return signal
