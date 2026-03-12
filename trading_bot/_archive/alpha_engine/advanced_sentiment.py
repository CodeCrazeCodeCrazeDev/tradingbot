"""
Advanced Sentiment Analysis Module
===================================

Comprehensive multi-source sentiment aggregation:
- Financial News (Reuters, Bloomberg, WSJ)
- Social Media (Twitter, Reddit, StockTwits)
- SEC Filings & Earnings Transcripts
- Macroeconomic Data & Central Bank Statements
- FinBERT & LLM-based Analysis
- Loughran-McDonald Financial Lexicon
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

logger = logging.getLogger(__name__)

# Try importing NLP libraries
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Using fallback sentiment analysis.")


class SentimentSource(Enum):
    """Sources of sentiment data"""
    NEWS_REUTERS = "news_reuters"
    NEWS_BLOOMBERG = "news_bloomberg"
    NEWS_WSJ = "news_wsj"
    NEWS_FT = "news_ft"
    SOCIAL_TWITTER = "social_twitter"
    SOCIAL_REDDIT = "social_reddit"
    SOCIAL_STOCKTWITS = "social_stocktwits"
    SEC_FILINGS = "sec_filings"
    EARNINGS_CALLS = "earnings_calls"
    CENTRAL_BANK = "central_bank"
    ECONOMIC_DATA = "economic_data"


class SentimentLevel(Enum):
    """Sentiment levels"""
    EXTREME_BEARISH = "extreme_bearish"  # < -70
    BEARISH = "bearish"  # -70 to -30
    SLIGHTLY_BEARISH = "slightly_bearish"  # -30 to -10
    NEUTRAL = "neutral"  # -10 to +10
    SLIGHTLY_BULLISH = "slightly_bullish"  # +10 to +30
    BULLISH = "bullish"  # +30 to +70
    EXTREME_BULLISH = "extreme_bullish"  # > +70


@dataclass
class SentimentDataPoint:
    """Single sentiment data point"""
    timestamp: datetime
    source: SentimentSource
    text: str
    score: float  # -100 to +100
    confidence: float  # 0 to 1
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across sources"""
    timestamp: datetime
    symbol: str
    
    # Overall scores
    composite_score: float  # -100 to +100
    level: SentimentLevel
    confidence: float
    
    # Source breakdown
    news_score: float
    social_score: float
    institutional_score: float  # SEC filings, earnings
    macro_score: float  # Central bank, economic
    
    # Momentum
    sentiment_momentum: float  # Rate of change
    sentiment_acceleration: float
    
    # Divergence
    price_sentiment_divergence: float
    cross_source_divergence: float
    
    # Signals
    is_extreme: bool
    contrarian_signal: Optional[str]  # 'buy' or 'sell' if extreme


@dataclass
class TradingSignalFromSentiment:
    """Trading signal derived from sentiment"""
    timestamp: datetime
    symbol: str
    signal_type: str  # 'confirmation', 'divergence', 'extreme', 'event'
    direction: str  # 'long', 'short', 'neutral'
    strength: float  # 0 to 1
    position_adjustment: float  # Multiplier (e.g., 1.2 = increase 20%)
    reasoning: str


# Loughran-McDonald Financial Sentiment Lexicon
LOUGHRAN_MCDONALD_POSITIVE = [
    'accomplish', 'accomplishment', 'achieve', 'achievement', 'advance', 'advantage',
    'beneficial', 'benefit', 'best', 'better', 'boost', 'breakthrough', 'brilliant',
    'creative', 'delight', 'deliver', 'desirable', 'despite', 'diligent', 'distinction',
    'efficient', 'empower', 'enable', 'enhance', 'enjoy', 'enthusiasm', 'excellent',
    'exceptional', 'exciting', 'exclusive', 'favorable', 'gain', 'good', 'great',
    'greatest', 'growth', 'highest', 'honor', 'ideal', 'improve', 'improvement',
    'incredible', 'innovation', 'innovative', 'integrity', 'leader', 'leadership',
    'lucrative', 'opportunities', 'opportunity', 'optimal', 'optimism', 'optimistic',
    'outperform', 'outstanding', 'perfect', 'pleased', 'pleasure', 'positive',
    'premier', 'premium', 'proactive', 'proficiency', 'proficient', 'profit',
    'profitable', 'progress', 'prosper', 'prosperity', 'rebound', 'record',
    'recover', 'recovery', 'reward', 'rewarding', 'robust', 'solid', 'stability',
    'stable', 'strength', 'strengthen', 'strong', 'succeed', 'success', 'successful',
    'superior', 'surpass', 'tremendous', 'upturn', 'valuable', 'win', 'winner',
]

LOUGHRAN_MCDONALD_NEGATIVE = [
    'abandon', 'adverse', 'against', 'allegation', 'annul', 'bad', 'bankrupt',
    'bankruptcy', 'blame', 'breach', 'burden', 'catastrophe', 'caution', 'cease',
    'challenge', 'claim', 'closure', 'collapse', 'concern', 'conflict', 'constraint',
    'contamination', 'contingency', 'crisis', 'critical', 'criticism', 'damage',
    'danger', 'decline', 'decrease', 'default', 'defect', 'deficiency', 'deficit',
    'delay', 'delisting', 'denial', 'deplete', 'depreciation', 'deteriorate',
    'difficult', 'difficulty', 'diminish', 'disadvantage', 'disappoint', 'disaster',
    'disclose', 'discontinue', 'dispute', 'disruption', 'distress', 'doubt',
    'downgrade', 'downturn', 'drop', 'failure', 'fall', 'fear', 'fine', 'fraud',
    'harm', 'hazard', 'impair', 'impairment', 'inability', 'inadequate', 'incident',
    'ineffective', 'inferior', 'instability', 'investigation', 'lawsuit', 'layoff',
    'liability', 'liquidation', 'litigation', 'loss', 'losses', 'negative',
    'negligence', 'obstacle', 'penalty', 'plunge', 'poor', 'problem', 'recall',
    'recession', 'restructuring', 'risk', 'sanction', 'scandal', 'shortage',
    'shrink', 'slump', 'slowdown', 'struggle', 'sue', 'suffer', 'suspend',
    'terminate', 'threat', 'trouble', 'uncertain', 'uncertainty', 'unfavorable',
    'violation', 'volatile', 'volatility', 'warn', 'warning', 'weak', 'weakness',
    'worse', 'worsen', 'worst', 'writedown', 'writeoff',
]

LOUGHRAN_MCDONALD_UNCERTAINTY = [
    'almost', 'anticipate', 'appear', 'approximate', 'assume', 'believe',
    'conceivable', 'conditional', 'contingent', 'depend', 'doubt', 'estimate',
    'expect', 'fluctuate', 'forecast', 'hope', 'indefinite', 'indicate',
    'likelihood', 'may', 'maybe', 'might', 'nearly', 'pending', 'perhaps',
    'possibility', 'possible', 'possibly', 'potential', 'predict', 'preliminary',
    'presume', 'probable', 'probably', 'project', 'random', 'risk', 'roughly',
    'seem', 'sometime', 'somewhat', 'speculate', 'suggest', 'suppose', 'tentative',
    'uncertain', 'uncertainty', 'unclear', 'unknown', 'unlikely', 'unpredictable',
    'unproven', 'unsettled', 'variable', 'vary',
]


class LoughranMcDonaldAnalyzer:
    """
    Sentiment analysis using Loughran-McDonald financial lexicon
    """
    
    def __init__(self):
        self.positive_words = set(LOUGHRAN_MCDONALD_POSITIVE)
        self.negative_words = set(LOUGHRAN_MCDONALD_NEGATIVE)
        self.uncertainty_words = set(LOUGHRAN_MCDONALD_UNCERTAINTY)
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text using L-M lexicon"""
        # Tokenize
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        if not words:
            return {
                'score': 0,
                'positive_count': 0,
                'negative_count': 0,
                'uncertainty_count': 0,
                'confidence': 0,
            }
        
        # Count sentiment words
        positive_count = sum(1 for w in words if w in self.positive_words)
        negative_count = sum(1 for w in words if w in self.negative_words)
        uncertainty_count = sum(1 for w in words if w in self.uncertainty_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            score = 0
            confidence = 0
        else:
            # Calculate score (-100 to +100)
            score = (positive_count - negative_count) / total_sentiment_words * 100
            
            # Confidence based on coverage
            confidence = min(total_sentiment_words / len(words) * 10, 1.0)
        
        # Adjust for uncertainty
        if uncertainty_count > total_sentiment_words * 0.3:
            confidence *= 0.7  # Reduce confidence if high uncertainty
        
        return {
            'score': score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'uncertainty_count': uncertainty_count,
            'confidence': confidence,
            'word_count': len(words),
        }


class FinBERTAnalyzer:
    """
    FinBERT-based sentiment analysis for financial text
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"FinBERT loaded successfully on {self.device}")
            except Exception as e:
                logger.warning(f"Failed to load FinBERT: {e}")
                self.model = None
        
        # Fallback lexicon analyzer
        self.lexicon_analyzer = LoughranMcDonaldAnalyzer()
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment"""
        if self.model is None:
            try:
                # Use fallback
                result = self.lexicon_analyzer.analyze(text)
                return {
                    'score': result['score'],
                    'label': 'positive' if result['score'] > 10 else ('negative' if result['score'] < -10 else 'neutral'),
                    'confidence': result['confidence'],
                    'method': 'lexicon',
                }

                # Tokenize
                inputs = self.tokenizer(
                    text,
                    return_tensors='pt',
                    truncation=True,
                    max_length=512,
                    padding=True,
                ).to(self.device)

                # Predict
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.softmax(outputs.logits, dim=-1)[0]

                # FinBERT outputs: [positive, negative, neutral]
                positive_prob = probs[0].item()
                negative_prob = probs[1].item()
                neutral_prob = probs[2].item()

                # Calculate score (-100 to +100)
                score = (positive_prob - negative_prob) * 100

                # Determine label
                max_prob = max(positive_prob, negative_prob, neutral_prob)
                if max_prob == positive_prob:
                    label = 'positive'
                elif max_prob == negative_prob:
                    label = 'negative'
                else:
                    label = 'neutral'

                return {
                    'score': score,
                    'label': label,
                    'confidence': max_prob,
                    'positive_prob': positive_prob,
                    'negative_prob': negative_prob,
                    'neutral_prob': neutral_prob,
                    'method': 'finbert',
                }

            except Exception as e:
                logger.error(f"FinBERT analysis failed: {e}")
                result = self.lexicon_analyzer.analyze(text)
                return {
                    'score': result['score'],
                    'label': 'positive' if result['score'] > 10 else ('negative' if result['score'] < -10 else 'neutral'),
                    'confidence': result['confidence'],
                    'method': 'lexicon_fallback',
                }

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]


class NewsProcessor:
    """
    Processes financial news for sentiment
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # News history
        self.news_history: Dict[str, deque] = {}  # symbol -> news items
        
        # Source credibility weights
        self.source_weights = {
            SentimentSource.NEWS_REUTERS: 1.0,
            SentimentSource.NEWS_BLOOMBERG: 1.0,
            SentimentSource.NEWS_WSJ: 0.9,
            SentimentSource.NEWS_FT: 0.9,
        }
    
    def process_article(self, headline: str, body: str, source: SentimentSource,
                       symbol: str = None, timestamp: datetime = None) -> SentimentDataPoint:
        """Process a news article"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Analyze headline (more weight)
        headline_result = self.analyzer.analyze(headline)
        
        # Analyze body (if provided)
        if body:
            body_result = self.analyzer.analyze(body[:1000])  # First 1000 chars
            # Weighted average (headline 60%, body 40%)
            score = headline_result['score'] * 0.6 + body_result['score'] * 0.4
            confidence = (headline_result['confidence'] * 0.6 + body_result['confidence'] * 0.4)
        else:
            score = headline_result['score']
            confidence = headline_result['confidence']
        
        # Apply source weight
        source_weight = self.source_weights.get(source, 0.8)
        confidence *= source_weight
        
        data_point = SentimentDataPoint(
            timestamp=timestamp,
            source=source,
            text=headline,
            score=score,
            confidence=confidence,
            symbol=symbol,
            metadata={
                'headline_score': headline_result['score'],
                'source_weight': source_weight,
            },
        )
        
        # Store in history
        if symbol:
            if symbol not in self.news_history:
                self.news_history[symbol] = deque(maxlen=1000)
            self.news_history[symbol].append(data_point)
        
        return data_point
    
    def get_news_sentiment(self, symbol: str, lookback_hours: int = 24) -> Dict[str, Any]:
        """Get aggregated news sentiment for symbol"""
        if symbol not in self.news_history:
            return {'score': 0, 'confidence': 0, 'count': 0}
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent = [n for n in self.news_history[symbol] if n.timestamp > cutoff]
        
        if not recent:
            return {'score': 0, 'confidence': 0, 'count': 0}
        
        # Time-weighted average (more recent = more weight)
        total_weight = 0
        weighted_score = 0
        
        for news in recent:
            # Exponential decay based on age
            age_hours = (datetime.now() - news.timestamp).total_seconds() / 3600
            time_weight = np.exp(-age_hours / 12)  # Half-life of 12 hours
            
            weight = time_weight * news.confidence
            weighted_score += news.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return {'score': 0, 'confidence': 0, 'count': len(recent)}
        
        return {
            'score': weighted_score / total_weight,
            'confidence': total_weight / len(recent),
            'count': len(recent),
        }


class SocialMediaAnalyzer:
    """
    Analyzes social media sentiment (Twitter, Reddit, StockTwits)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # Social history
        self.social_history: Dict[str, deque] = {}
        
        # Platform weights
        self.platform_weights = {
            SentimentSource.SOCIAL_TWITTER: 0.7,
            SentimentSource.SOCIAL_REDDIT: 0.8,
            SentimentSource.SOCIAL_STOCKTWITS: 0.9,
        }
        
        # Influencer tracking
        self.influencer_weights: Dict[str, float] = {}
    
    def process_post(self, text: str, source: SentimentSource, symbol: str = None,
                    author: str = None, engagement: int = 0,
                    timestamp: datetime = None) -> SentimentDataPoint:
        """Process a social media post"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Analyze sentiment
        result = self.analyzer.analyze(text)
        
        # Apply platform weight
        platform_weight = self.platform_weights.get(source, 0.5)
        
        # Apply engagement weight (log scale)
        engagement_weight = 1 + np.log1p(engagement) / 10
        
        # Apply influencer weight
        influencer_weight = self.influencer_weights.get(author, 1.0)
        
        # Combined confidence
        confidence = result['confidence'] * platform_weight * min(engagement_weight, 2.0) * influencer_weight
        confidence = min(confidence, 1.0)
        
        data_point = SentimentDataPoint(
            timestamp=timestamp,
            source=source,
            text=text[:500],  # Truncate
            score=result['score'],
            confidence=confidence,
            symbol=symbol,
            metadata={
                'author': author,
                'engagement': engagement,
                'platform_weight': platform_weight,
            },
        )
        
        # Store
        if symbol:
            if symbol not in self.social_history:
                self.social_history[symbol] = deque(maxlen=5000)
            self.social_history[symbol].append(data_point)
        
        return data_point
    
    def get_social_sentiment(self, symbol: str, lookback_hours: int = 6) -> Dict[str, Any]:
        """Get aggregated social sentiment"""
        if symbol not in self.social_history:
            return {'score': 0, 'confidence': 0, 'count': 0, 'velocity': 0}
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent = [s for s in self.social_history[symbol] if s.timestamp > cutoff]
        
        if not recent:
            return {'score': 0, 'confidence': 0, 'count': 0, 'velocity': 0}
        
        # Weighted average
        total_weight = 0
        weighted_score = 0
        
        for post in recent:
            age_hours = (datetime.now() - post.timestamp).total_seconds() / 3600
            time_weight = np.exp(-age_hours / 3)  # Half-life of 3 hours
            
            weight = time_weight * post.confidence
            weighted_score += post.score * weight
            total_weight += weight
        
        # Calculate velocity (posts per hour)
        velocity = len(recent) / lookback_hours
        
        return {
            'score': weighted_score / total_weight if total_weight > 0 else 0,
            'confidence': total_weight / len(recent) if recent else 0,
            'count': len(recent),
            'velocity': velocity,
        }
    
    def detect_unusual_activity(self, symbol: str) -> Dict[str, Any]:
        """Detect unusual social media activity"""
        if symbol not in self.social_history:
            return {'unusual': False}
        
        # Compare recent hour to baseline
        now = datetime.now()
        recent_hour = [s for s in self.social_history[symbol] 
                      if s.timestamp > now - timedelta(hours=1)]
        baseline = [s for s in self.social_history[symbol]
                   if now - timedelta(hours=24) < s.timestamp < now - timedelta(hours=1)]
        
        if len(baseline) < 10:
            return {'unusual': False, 'reason': 'insufficient_baseline'}
        
        baseline_rate = len(baseline) / 23  # Posts per hour
        recent_rate = len(recent_hour)
        
        if baseline_rate > 0 and recent_rate > baseline_rate * 3:
            return {
                'unusual': True,
                'reason': 'volume_spike',
                'recent_rate': recent_rate,
                'baseline_rate': baseline_rate,
                'multiplier': recent_rate / baseline_rate,
            }
        
        return {'unusual': False}


class InstitutionalSentimentAnalyzer:
    """
    Analyzes institutional sentiment from SEC filings and earnings calls
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # Filing history
        self.filing_history: Dict[str, deque] = {}
    
    def analyze_10k(self, text: str, symbol: str, filing_date: datetime) -> SentimentDataPoint:
        """Analyze 10-K filing"""
        # Focus on key sections
        sections_to_analyze = [
            'risk factors',
            'management discussion',
            'business overview',
        ]
        
        # Simple extraction (in production, use proper SEC parser)
        result = self.analyzer.analyze(text[:5000])
        
        return SentimentDataPoint(
            timestamp=filing_date,
            source=SentimentSource.SEC_FILINGS,
            text=f"10-K Filing for {symbol}",
            score=result['score'],
            confidence=result['confidence'] * 0.9,  # High confidence for official filings
            symbol=symbol,
            metadata={'filing_type': '10-K'},
        )
    
    def analyze_earnings_call(self, transcript: str, symbol: str,
                             call_date: datetime) -> Dict[str, Any]:
        """Analyze earnings call transcript"""
        # Analyze overall sentiment
        overall = self.analyzer.analyze(transcript[:5000])
        
        # Look for specific patterns
        confidence_phrases = [
            'confident', 'optimistic', 'strong', 'growth', 'exceed',
            'outperform', 'momentum', 'accelerate',
        ]
        concern_phrases = [
            'challenge', 'headwind', 'uncertain', 'cautious', 'decline',
            'pressure', 'difficult', 'concern',
        ]
        
        text_lower = transcript.lower()
        confidence_count = sum(1 for p in confidence_phrases if p in text_lower)
        concern_count = sum(1 for p in concern_phrases if p in text_lower)
        
        # Management tone adjustment
        tone_adjustment = (confidence_count - concern_count) * 5
        adjusted_score = overall['score'] + tone_adjustment
        adjusted_score = np.clip(adjusted_score, -100, 100)
        
        return {
            'score': adjusted_score,
            'confidence': overall['confidence'],
            'management_confidence': confidence_count,
            'management_concerns': concern_count,
            'tone_adjustment': tone_adjustment,
        }


class MacroSentimentAnalyzer:
    """
    Analyzes macroeconomic sentiment from central bank statements and economic data
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = FinBERTAnalyzer()
        
        # Macro history
        self.macro_history: deque = deque(maxlen=1000)
        
        # Hawkish/Dovish keywords
        self.hawkish_words = [
            'inflation', 'tighten', 'hike', 'restrictive', 'overheating',
            'vigilant', 'normalize', 'reduce', 'unwind', 'tapering',
        ]
        self.dovish_words = [
            'accommodate', 'support', 'stimulus', 'ease', 'patient',
            'gradual', 'flexible', 'data-dependent', 'transitory', 'moderate',
        ]
    
    def analyze_central_bank_statement(self, text: str, bank: str,
                                       statement_date: datetime) -> Dict[str, Any]:
        """Analyze central bank statement"""
        # General sentiment
        general = self.analyzer.analyze(text)
        
        # Hawkish/Dovish analysis
        text_lower = text.lower()
        hawkish_count = sum(1 for w in self.hawkish_words if w in text_lower)
        dovish_count = sum(1 for w in self.dovish_words if w in text_lower)
        
        # Policy stance score (-100 = very dovish, +100 = very hawkish)
        if hawkish_count + dovish_count > 0:
            policy_score = (hawkish_count - dovish_count) / (hawkish_count + dovish_count) * 100
        else:
            policy_score = 0
        
        # Market impact (hawkish = bearish for risk assets)
        market_sentiment = -policy_score * 0.5  # Invert and scale
        
        data_point = SentimentDataPoint(
            timestamp=statement_date,
            source=SentimentSource.CENTRAL_BANK,
            text=f"{bank} Statement",
            score=market_sentiment,
            confidence=0.9,
            metadata={
                'bank': bank,
                'policy_score': policy_score,
                'hawkish_count': hawkish_count,
                'dovish_count': dovish_count,
            },
        )
        
        self.macro_history.append(data_point)
        
        return {
            'market_sentiment': market_sentiment,
            'policy_score': policy_score,
            'hawkish_count': hawkish_count,
            'dovish_count': dovish_count,
            'confidence': 0.9,
        }
    
    def analyze_economic_surprise(self, indicator: str, actual: float,
                                  expected: float, prior: float) -> Dict[str, Any]:
        """Analyze economic data surprise"""
        # Calculate surprise
        if expected != 0:
            surprise_pct = (actual - expected) / abs(expected) * 100
        else:
            surprise_pct = 0
        
        # Determine sentiment impact
        positive_indicators = ['gdp', 'employment', 'retail', 'manufacturing']
        negative_indicators = ['unemployment', 'inflation', 'claims']
        
        indicator_lower = indicator.lower()
        
        if any(p in indicator_lower for p in positive_indicators):
            # Positive surprise = bullish
            sentiment = surprise_pct * 2
        elif any(n in indicator_lower for n in negative_indicators):
            # Positive surprise = bearish (e.g., higher inflation)
            sentiment = -surprise_pct * 2
        else:
            sentiment = surprise_pct
        
        sentiment = np.clip(sentiment, -100, 100)
        
        return {
            'indicator': indicator,
            'actual': actual,
            'expected': expected,
            'surprise_pct': surprise_pct,
            'sentiment': sentiment,
            'confidence': 0.8,
        }


class ComprehensiveSentimentAggregator:
    """
    Aggregates sentiment from all sources with trading signal generation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize analyzers
        self.news_processor = NewsProcessor(config.get('news', {}))
        self.social_analyzer = SocialMediaAnalyzer(config.get('social', {}))
        self.institutional_analyzer = InstitutionalSentimentAnalyzer(config.get('institutional', {}))
        self.macro_analyzer = MacroSentimentAnalyzer(config.get('macro', {}))
        
        # Source weights for aggregation
        self.source_weights = {
            'news': self.config.get('news_weight', 0.30),
            'social': self.config.get('social_weight', 0.20),
            'institutional': self.config.get('institutional_weight', 0.25),
            'macro': self.config.get('macro_weight', 0.25),
        }
        
        # Sentiment history
        self.sentiment_history: Dict[str, deque] = {}
        
        # Price history for divergence
        self.price_history: Dict[str, deque] = {}
    
    def update_price(self, symbol: str, price: float, timestamp: datetime = None):
        """Update price for divergence calculation"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=1000)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp,
        })
    
    def get_aggregated_sentiment(self, symbol: str) -> AggregatedSentiment:
        """Get comprehensive aggregated sentiment"""
        # Get sentiment from each source
        news = self.news_processor.get_news_sentiment(symbol)
        social = self.social_analyzer.get_social_sentiment(symbol)
        
        # Institutional and macro are more general
        institutional_score = 0  # Would need actual data
        macro_score = 0  # Would need actual data
        
        # Weighted aggregation
        total_weight = 0
        weighted_score = 0
        
        if news['count'] > 0:
            weighted_score += news['score'] * self.source_weights['news'] * news['confidence']
            total_weight += self.source_weights['news'] * news['confidence']
        
        if social['count'] > 0:
            weighted_score += social['score'] * self.source_weights['social'] * social['confidence']
            total_weight += self.source_weights['social'] * social['confidence']
        
        if total_weight > 0:
            composite_score = weighted_score / total_weight
        else:
            composite_score = 0
        
        # Determine level
        level = self._score_to_level(composite_score)
        
        # Calculate momentum
        momentum = self._calculate_momentum(symbol)
        
        # Calculate divergence
        price_divergence = self._calculate_price_divergence(symbol, composite_score)
        
        # Cross-source divergence
        cross_divergence = abs(news['score'] - social['score']) if news['count'] > 0 and social['count'] > 0 else 0
        
        # Check for extremes
        is_extreme = abs(composite_score) > 70
        contrarian_signal = None
        if composite_score < -70:
            contrarian_signal = 'buy'  # Extreme bearish = contrarian buy
        elif composite_score > 70:
            contrarian_signal = 'sell'  # Extreme bullish = contrarian sell
        
        aggregated = AggregatedSentiment(
            timestamp=datetime.now(),
            symbol=symbol,
            composite_score=composite_score,
            level=level,
            confidence=total_weight / sum(self.source_weights.values()) if total_weight > 0 else 0,
            news_score=news['score'],
            social_score=social['score'],
            institutional_score=institutional_score,
            macro_score=macro_score,
            sentiment_momentum=momentum,
            sentiment_acceleration=0,  # Would need more history
            price_sentiment_divergence=price_divergence,
            cross_source_divergence=cross_divergence,
            is_extreme=is_extreme,
            contrarian_signal=contrarian_signal,
        )
        
        # Store
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = deque(maxlen=1000)
        self.sentiment_history[symbol].append(aggregated)
        
        return aggregated
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """Convert score to sentiment level"""
        if score < -70:
            return SentimentLevel.EXTREME_BEARISH
        elif score < -30:
            return SentimentLevel.BEARISH
        elif score < -10:
            return SentimentLevel.SLIGHTLY_BEARISH
        elif score < 10:
            return SentimentLevel.NEUTRAL
        elif score < 30:
            return SentimentLevel.SLIGHTLY_BULLISH
        elif score < 70:
            return SentimentLevel.BULLISH
        else:
            return SentimentLevel.EXTREME_BULLISH
    
    def _calculate_momentum(self, symbol: str) -> float:
        """Calculate sentiment momentum (rate of change)"""
        if symbol not in self.sentiment_history:
            return 0
        
        history = list(self.sentiment_history[symbol])
        if len(history) < 2:
            return 0
        
        # Compare recent to older
        recent = [h.composite_score for h in history[-5:]]
        older = [h.composite_score for h in history[-10:-5]]
        
        if not older:
            return 0
        
        return np.mean(recent) - np.mean(older)
    
    def _calculate_price_divergence(self, symbol: str, sentiment_score: float) -> float:
        """Calculate divergence between price and sentiment"""
        if symbol not in self.price_history:
            return 0
        
        prices = [p['price'] for p in self.price_history[symbol]]
        if len(prices) < 20:
            return 0
        
        # Price momentum
        price_change = (prices[-1] - prices[-20]) / prices[-20] * 100
        
        # Divergence: price up but sentiment down, or vice versa
        divergence = price_change - sentiment_score
        
        return divergence
    
    def generate_trading_signal(self, symbol: str, dc_signal: str = None) -> TradingSignalFromSentiment:
        """
        Generate trading signal from sentiment
        
        Args:
            symbol: Trading symbol
            dc_signal: DC signal if available ('long', 'short', None)
            
        Returns:
            TradingSignalFromSentiment
        """
        sentiment = self.get_aggregated_sentiment(symbol)
        
        # Rule 1: Sentiment Confirmation
        if dc_signal and sentiment.confidence > 0.5:
            if dc_signal == 'long' and sentiment.composite_score > 30:
                return TradingSignalFromSentiment(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type='confirmation',
                    direction='long',
                    strength=min(sentiment.composite_score / 100, 1.0),
                    position_adjustment=1.2,  # Increase by 20%
                    reasoning=f"DC long confirmed by bullish sentiment ({sentiment.composite_score:.1f})",
                )
            elif dc_signal == 'short' and sentiment.composite_score < -30:
                return TradingSignalFromSentiment(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type='confirmation',
                    direction='short',
                    strength=min(abs(sentiment.composite_score) / 100, 1.0),
                    position_adjustment=1.2,
                    reasoning=f"DC short confirmed by bearish sentiment ({sentiment.composite_score:.1f})",
                )
        
        # Rule 2: Sentiment Divergence
        if abs(sentiment.price_sentiment_divergence) > 50:
            if sentiment.price_sentiment_divergence > 50:
                # Price up, sentiment down -> reduce long
                return TradingSignalFromSentiment(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type='divergence',
                    direction='reduce_long',
                    strength=0.5,
                    position_adjustment=0.7,  # Reduce by 30%
                    reasoning=f"Price-sentiment divergence: price up but sentiment declining",
                )
            else:
                # Price down, sentiment up -> reduce short
                return TradingSignalFromSentiment(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type='divergence',
                    direction='reduce_short',
                    strength=0.5,
                    position_adjustment=0.7,
                    reasoning=f"Price-sentiment divergence: price down but sentiment improving",
                )
        
        # Rule 3: Extreme Sentiment (Contrarian)
        if sentiment.is_extreme:
            return TradingSignalFromSentiment(
                timestamp=datetime.now(),
                symbol=symbol,
                signal_type='extreme',
                direction=sentiment.contrarian_signal or 'neutral',
                strength=0.3,  # Lower strength for contrarian
                position_adjustment=0.5,  # Reduce overall exposure
                reasoning=f"Extreme sentiment ({sentiment.composite_score:.1f}) - risk-off mode",
            )
        
        # Rule 4: Event-Driven (unusual activity)
        unusual = self.social_analyzer.detect_unusual_activity(symbol)
        if unusual.get('unusual'):
            return TradingSignalFromSentiment(
                timestamp=datetime.now(),
                symbol=symbol,
                signal_type='event',
                direction='neutral',
                strength=0.0,
                position_adjustment=0.0,  # Pause trading
                reasoning=f"Unusual social activity detected ({unusual.get('multiplier', 0):.1f}x normal) - pausing",
            )
        
        # Default: no signal
        return TradingSignalFromSentiment(
            timestamp=datetime.now(),
            symbol=symbol,
            signal_type='none',
            direction='neutral',
            strength=0.0,
            position_adjustment=1.0,
            reasoning="No significant sentiment signal",
        )
