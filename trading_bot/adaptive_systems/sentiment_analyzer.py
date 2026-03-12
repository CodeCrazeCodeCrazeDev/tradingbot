"""
Market Sentiment Analysis System
Analyzes sentiment from multiple sources including news, social media, and order flow
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import json
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class SentimentSignal:
    """Market sentiment signal"""
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    sentiment: float  # -1 to 1
    source: str
    impact: float
    supporting_data: Dict
    metadata: Dict

class SentimentSource:
    """Sentiment data sources"""
    NEWS = "news"
    SOCIAL = "social"
    ORDER_FLOW = "order_flow"
    TECHNICAL = "technical"
    OPTION_FLOW = "option_flow"
    INSTITUTIONAL = "institutional"

class SentimentAnalyzer:
    """
    Advanced market sentiment analysis system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Analysis parameters
            self.sentiment_window = self.config.get('sentiment_window', 24)  # hours
            self.impact_threshold = self.config.get('impact_threshold', 0.5)
            self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        
            # Sentiment analyzers
            self.vader = SentimentIntensityAnalyzer()
            self.sentiment_history = {}
            self.source_weights = {
                SentimentSource.NEWS: 0.3,
                SentimentSource.SOCIAL: 0.2,
                SentimentSource.ORDER_FLOW: 0.2,
                SentimentSource.TECHNICAL: 0.1,
                SentimentSource.OPTION_FLOW: 0.1,
                SentimentSource.INSTITUTIONAL: 0.1
            }
        
            # State tracking
            self.current_sentiment = {}
            self.sentiment_trends = {}
            self.source_reliability = {}
        
            logger.info("Sentiment Analyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_sentiment(self, data: Dict) -> List[SentimentSignal]:
        """
        Analyze sentiment from multiple sources
        """
        try:
            signals = []
        
            # Analyze different sentiment sources
            if 'news' in data:
                signals.extend(self._analyze_news_sentiment(data['news']))
        
            if 'social' in data:
                signals.extend(self._analyze_social_sentiment(data['social']))
        
            if 'order_flow' in data:
                signals.extend(self._analyze_order_flow_sentiment(data['order_flow']))
        
            if 'technical' in data:
                signals.extend(self._analyze_technical_sentiment(data['technical']))
        
            if 'option_flow' in data:
                signals.extend(self._analyze_option_flow_sentiment(data['option_flow']))
        
            if 'institutional' in data:
                signals.extend(self._analyze_institutional_sentiment(data['institutional']))
        
            # Combine sentiment signals
            combined_signal = self._combine_sentiment_signals(signals)
            if combined_signal:
                signals.append(combined_signal)
        
            # Update state
            self._update_sentiment_state(signals)
        
            return signals
        except Exception as e:
            logger.error(f"Error in analyze_sentiment: {e}")
            raise
    
    def _analyze_news_sentiment(self, news_data: List[Dict]) -> List[SentimentSignal]:
        """
        Analyze sentiment from news articles
        """
        try:
            signals = []
        
            for article in news_data:
                # Extract text content
                title = article.get('title', '')
                content = article.get('content', '')
            
                # Analyze sentiment using both VADER and TextBlob
                vader_scores = self.vader.polarity_scores(title + " " + content)
                textblob_sentiment = TextBlob(title + " " + content).sentiment
            
                # Combine sentiment scores
                compound_sentiment = vader_scores['compound']
                textblob_polarity = textblob_sentiment.polarity
            
                # Weight the scores (VADER more heavily as it's finance-tuned)
                sentiment_score = 0.7 * compound_sentiment + 0.3 * textblob_polarity
            
                # Calculate confidence based on subjectivity and agreement
                confidence = (1 - textblob_sentiment.subjectivity) * \
                            (1 - abs(compound_sentiment - textblob_polarity))
            
                if abs(sentiment_score) > 0.2 and confidence > self.confidence_threshold:
                    signals.append(SentimentSignal(
                        signal_type="news_sentiment",
                        strength=abs(sentiment_score),
                        confidence=confidence,
                        timestamp=article.get('timestamp', datetime.now()),
                        sentiment=sentiment_score,
                        source=SentimentSource.NEWS,
                        impact=self._calculate_news_impact(article),
                        supporting_data={
                            'title': title,
                            'url': article.get('url'),
                            'vader_scores': vader_scores,
                            'textblob_scores': {
                                'polarity': textblob_polarity,
                                'subjectivity': textblob_sentiment.subjectivity
                            }
                        },
                        metadata={
                            'source_name': article.get('source'),
                            'category': article.get('category', 'general')
                        }
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_news_sentiment: {e}")
            raise
    
    def _analyze_social_sentiment(self, social_data: List[Dict]) -> List[SentimentSignal]:
        """
        Analyze sentiment from social media
        """
        try:
            signals = []
        
            # Group by platform
            platform_data = {}
            for post in social_data:
                platform = post.get('platform', 'unknown')
                if platform not in platform_data:
                    platform_data[platform] = []
                platform_data[platform].append(post)
        
            # Analyze each platform
            for platform, posts in platform_data.items():
                # Calculate aggregate sentiment
                sentiments = []
                for post in posts:
                    content = post.get('content', '')
                
                    # Get VADER sentiment
                    vader_scores = self.vader.polarity_scores(content)
                    sentiments.append(vader_scores['compound'])
            
                if sentiments:
                    avg_sentiment = np.mean(sentiments)
                    sentiment_std = np.std(sentiments)
                
                    # Generate signal if sentiment is significant
                    if abs(avg_sentiment) > 0.3:
                        signals.append(SentimentSignal(
                            signal_type="social_sentiment",
                            strength=abs(avg_sentiment),
                            confidence=1 - sentiment_std,  # Lower std = higher confidence
                            timestamp=datetime.now(),
                            sentiment=avg_sentiment,
                            source=SentimentSource.SOCIAL,
                            impact=self._calculate_social_impact(platform, len(posts)),
                            supporting_data={
                                'platform': platform,
                                'post_count': len(posts),
                                'sentiment_std': sentiment_std,
                                'sentiment_distribution': {
                                    'positive': len([s for s in sentiments if s > 0.2]),
                                    'negative': len([s for s in sentiments if s < -0.2]),
                                    'neutral': len([s for s in sentiments if abs(s) <= 0.2])
                                }
                            },
                            metadata={
                                'platform': platform,
                                'timeframe': f"{self.sentiment_window}h"
                            }
                        ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_social_sentiment: {e}")
            raise
    
    def _analyze_order_flow_sentiment(self, flow_data: Dict) -> List[SentimentSignal]:
        """
        Analyze sentiment from order flow data
        """
        try:
            signals = []
        
            if 'trades' not in flow_data:
                return signals
        
            trades = flow_data['trades']
        
            # Calculate buy/sell imbalance
            buy_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'buy')
            sell_volume = sum(t.get('volume', 0) for t in trades if t.get('side') == 'sell')
            total_volume = buy_volume + sell_volume
        
            if total_volume > 0:
                # Calculate flow sentiment
                flow_imbalance = (buy_volume - sell_volume) / total_volume
            
                # Calculate aggressiveness
                aggressive_buys = sum(1 for t in trades 
                                    if t.get('side') == 'buy' and t.get('aggressive', False))
                aggressive_sells = sum(1 for t in trades 
                                    if t.get('side') == 'sell' and t.get('aggressive', False))
            
                total_trades = len(trades)
                aggression_ratio = (aggressive_buys + aggressive_sells) / total_trades if total_trades > 0 else 0
            
                signals.append(SentimentSignal(
                    signal_type="order_flow_sentiment",
                    strength=abs(flow_imbalance),
                    confidence=min(total_volume / 100000, 1.0),  # Scale with volume
                    timestamp=datetime.now(),
                    sentiment=flow_imbalance,
                    source=SentimentSource.ORDER_FLOW,
                    impact=self._calculate_flow_impact(total_volume, aggression_ratio),
                    supporting_data={
                        'buy_volume': buy_volume,
                        'sell_volume': sell_volume,
                        'aggressive_ratio': aggression_ratio,
                        'trade_count': total_trades
                    },
                    metadata={
                        'analysis_type': 'flow_imbalance',
                        'timeframe': f"{self.sentiment_window}h"
                    }
                ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_order_flow_sentiment: {e}")
            raise
    
    def _analyze_technical_sentiment(self, technical_data: Dict) -> List[SentimentSignal]:
        """
        Analyze sentiment from technical indicators
        """
        try:
            signals = []
        
            if not technical_data:
                return signals
        
            # Analyze trend indicators
            trend_score = self._calculate_trend_score(technical_data)
            momentum_score = self._calculate_momentum_score(technical_data)
        
            # Combine technical factors
            technical_sentiment = 0.6 * trend_score + 0.4 * momentum_score
        
            if abs(technical_sentiment) > 0.2:
                signals.append(SentimentSignal(
                    signal_type="technical_sentiment",
                    strength=abs(technical_sentiment),
                    confidence=0.6,  # Technical analysis generally lower confidence
                    timestamp=datetime.now(),
                    sentiment=technical_sentiment,
                    source=SentimentSource.TECHNICAL,
                    impact=abs(technical_sentiment) * 0.5,
                    supporting_data={
                        'trend_score': trend_score,
                        'momentum_score': momentum_score,
                        'indicators': technical_data
                    },
                    metadata={
                        'analysis_type': 'technical',
                        'timeframe': f"{self.sentiment_window}h"
                    }
                ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_technical_sentiment: {e}")
            raise
    
    def _analyze_option_flow_sentiment(self, option_data: Dict) -> List[SentimentSignal]:
        """
        Analyze sentiment from options flow
        """
        try:
            signals = []
        
            if 'trades' not in option_data:
                return signals
        
            option_trades = option_data['trades']
        
            # Calculate put/call ratio
            call_volume = sum(t.get('volume', 0) for t in option_trades if t.get('type') == 'call')
            put_volume = sum(t.get('volume', 0) for t in option_trades if t.get('type') == 'put')
            total_volume = call_volume + put_volume
        
            if total_volume > 0:
                # Calculate sentiment from put/call ratio
                put_call_ratio = put_volume / call_volume if call_volume > 0 else float('inf')
            
                # Normalize to -1 to 1 scale (1.5 ratio is neutral)
                sentiment_score = -np.tanh((put_call_ratio - 1.5) / 2)
            
                signals.append(SentimentSignal(
                    signal_type="option_sentiment",
                    strength=abs(sentiment_score),
                    confidence=min(total_volume / 10000, 1.0),
                    timestamp=datetime.now(),
                    sentiment=sentiment_score,
                    source=SentimentSource.OPTION_FLOW,
                    impact=self._calculate_option_impact(option_data),
                    supporting_data={
                        'put_call_ratio': put_call_ratio,
                        'call_volume': call_volume,
                        'put_volume': put_volume,
                        'total_volume': total_volume
                    },
                    metadata={
                        'analysis_type': 'option_flow',
                        'timeframe': f"{self.sentiment_window}h"
                    }
                ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_option_flow_sentiment: {e}")
            raise
    
    def _analyze_institutional_sentiment(self, institutional_data: Dict) -> List[SentimentSignal]:
        """
        Analyze sentiment from institutional activity
        """
        try:
            signals = []
        
            if 'flows' not in institutional_data:
                return signals
        
            flows = institutional_data['flows']
        
            # Calculate institutional flow sentiment
            inflow = sum(f.get('volume', 0) for f in flows if f.get('direction') == 'buy')
            outflow = sum(f.get('volume', 0) for f in flows if f.get('direction') == 'sell')
            total_flow = inflow + outflow
        
            if total_flow > 0:
                flow_sentiment = (inflow - outflow) / total_flow
            
                signals.append(SentimentSignal(
                    signal_type="institutional_sentiment",
                    strength=abs(flow_sentiment),
                    confidence=0.8,  # High confidence in institutional data
                    timestamp=datetime.now(),
                    sentiment=flow_sentiment,
                    source=SentimentSource.INSTITUTIONAL,
                    impact=self._calculate_institutional_impact(total_flow),
                    supporting_data={
                        'inflow': inflow,
                        'outflow': outflow,
                        'total_flow': total_flow,
                        'institution_count': len(set(f.get('institution') for f in flows))
                    },
                    metadata={
                        'analysis_type': 'institutional_flow',
                        'timeframe': f"{self.sentiment_window}h"
                    }
                ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_institutional_sentiment: {e}")
            raise
    
    def _combine_sentiment_signals(self, signals: List[SentimentSignal]) -> Optional[SentimentSignal]:
        """
        Combine multiple sentiment signals into overall sentiment
        """
        try:
            if not signals:
                return None
        
            # Group signals by source
            source_signals = {}
            for signal in signals:
                if signal.source not in source_signals:
                    source_signals[signal.source] = []
                source_signals[signal.source].append(signal)
        
            # Calculate weighted sentiment for each source
            weighted_sentiments = []
            for source, source_sigs in source_signals.items():
                # Average sentiment for source
                avg_sentiment = np.mean([s.sentiment for s in source_sigs])
                avg_confidence = np.mean([s.confidence for s in source_sigs])
            
                weighted_sentiments.append({
                    'sentiment': avg_sentiment,
                    'weight': self.source_weights.get(source, 0.1),
                    'confidence': avg_confidence
                })
        
            # Calculate overall sentiment
            total_weight = sum(s['weight'] for s in weighted_sentiments)
            if total_weight == 0:
                return None
        
            overall_sentiment = sum(s['sentiment'] * s['weight'] for s in weighted_sentiments) / total_weight
            overall_confidence = sum(s['confidence'] * s['weight'] for s in weighted_sentiments) / total_weight
        
            return SentimentSignal(
                signal_type="combined_sentiment",
                strength=abs(overall_sentiment),
                confidence=overall_confidence,
                timestamp=datetime.now(),
                sentiment=overall_sentiment,
                source="combined",
                impact=abs(overall_sentiment) * overall_confidence,
                supporting_data={
                    'source_sentiments': {
                        source: {
                            'sentiment': np.mean([s.sentiment for s in sigs]),
                            'confidence': np.mean([s.confidence for s in sigs])
                        }
                        for source, sigs in source_signals.items()
                    },
                    'source_weights': self.source_weights
                },
                metadata={
                    'analysis_type': 'combined',
                    'timeframe': f"{self.sentiment_window}h"
                }
            )
        except Exception as e:
            logger.error(f"Error in _combine_sentiment_signals: {e}")
            raise
    
    def _calculate_news_impact(self, article: Dict) -> float:
        """
        Calculate potential market impact of news
        """
        try:
            impact_score = 0.5  # Base impact
        
            # Adjust for source reliability
            source = article.get('source', '')
            impact_score *= self.source_reliability.get(source, 0.5)
        
            # Adjust for recency
            if 'timestamp' in article:
                hours_old = (datetime.now() - article['timestamp']).total_seconds() / 3600
                impact_score *= np.exp(-hours_old / 24)  # Decay over 24 hours
        
            # Adjust for relevance
            if 'relevance_score' in article:
                impact_score *= article['relevance_score']
        
            return min(impact_score, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_news_impact: {e}")
            raise
    
    def _calculate_social_impact(self, platform: str, post_count: int) -> float:
        """
        Calculate potential market impact of social sentiment
        """
        # Base impact by platform
        try:
            platform_impact = {
                'twitter': 0.7,
                'reddit': 0.5,
                'stocktwits': 0.6,
                'telegram': 0.4
            }
        
            impact = platform_impact.get(platform.lower(), 0.3)
        
            # Scale with post volume (log scale)
            if post_count > 0:
                impact *= min(1.0, np.log10(post_count) / 4)
        
            return impact
        except Exception as e:
            logger.error(f"Error in _calculate_social_impact: {e}")
            raise
    
    def _calculate_flow_impact(self, volume: float, aggression_ratio: float) -> float:
        """
        Calculate potential market impact of order flow
        """
        # Scale with volume
        try:
            volume_impact = min(1.0, volume / 1000000)  # Scale to $1M
        
            # Adjust for aggressiveness
            impact = volume_impact * (1 + aggression_ratio)
        
            return min(impact, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_flow_impact: {e}")
            raise
    
    def _calculate_trend_score(self, technical_data: Dict) -> float:
        """
        Calculate technical trend score
        """
        try:
            trend_indicators = {
                'sma': technical_data.get('sma', 0),
                'ema': technical_data.get('ema', 0),
                'macd': technical_data.get('macd', 0)
            }
        
            # Combine trend indicators
            trend_score = sum(trend_indicators.values()) / len(trend_indicators)
        
            return np.clip(trend_score, -1, 1)
        except Exception as e:
            logger.error(f"Error in _calculate_trend_score: {e}")
            raise
    
    def _calculate_momentum_score(self, technical_data: Dict) -> float:
        """
        Calculate technical momentum score
        """
        try:
            momentum_indicators = {
                'rsi': (technical_data.get('rsi', 50) - 50) / 50,
                'stoch': (technical_data.get('stoch', 50) - 50) / 50,
                'cci': technical_data.get('cci', 0) / 100
            }
        
            # Combine momentum indicators
            momentum_score = sum(momentum_indicators.values()) / len(momentum_indicators)
        
            return np.clip(momentum_score, -1, 1)
        except Exception as e:
            logger.error(f"Error in _calculate_momentum_score: {e}")
            raise
    
    def _calculate_option_impact(self, option_data: Dict) -> float:
        """
        Calculate potential market impact of options activity
        """
        try:
            if 'total_premium' not in option_data:
                return 0.5
        
            # Scale with premium value
            premium_impact = min(1.0, option_data['total_premium'] / 1000000)  # Scale to $1M
        
            # Adjust for open interest changes
            if 'open_interest_change' in option_data:
                oi_change = abs(option_data['open_interest_change'])
                oi_impact = min(1.0, oi_change / 10000)  # Scale to 10K contracts
            
                return (premium_impact + oi_impact) / 2
        
            return premium_impact
        except Exception as e:
            logger.error(f"Error in _calculate_option_impact: {e}")
            raise
    
    def _calculate_institutional_impact(self, flow_volume: float) -> float:
        """
        Calculate potential market impact of institutional flows
        """
        # Scale with flow volume
        return min(1.0, flow_volume / 10000000)  # Scale to $10M
    
    def _update_sentiment_state(self, signals: List[SentimentSignal]):
        """
        Update internal sentiment state
        """
        try:
            timestamp = datetime.now()
        
            # Update current sentiment
            if signals:
                combined = self._combine_sentiment_signals(signals)
                if combined:
                    self.current_sentiment[timestamp] = combined.sentiment
        
            # Update sentiment trends
            self._update_sentiment_trends()
        
            # Clean old history
            self._clean_old_sentiment_history()
        except Exception as e:
            logger.error(f"Error in _update_sentiment_state: {e}")
            raise
    
    def _update_sentiment_trends(self):
        """
        Update sentiment trend analysis
        """
        try:
            if len(self.current_sentiment) < 2:
                return
        
            timestamps = sorted(self.current_sentiment.keys())
            sentiments = [self.current_sentiment[t] for t in timestamps]
        
            # Calculate trend metrics
            self.sentiment_trends = {
                'direction': np.sign(sentiments[-1] - sentiments[0]),
                'strength': abs(sentiments[-1] - sentiments[0]),
                'volatility': np.std(sentiments),
                'momentum': self._calculate_sentiment_momentum(sentiments)
            }
        except Exception as e:
            logger.error(f"Error in _update_sentiment_trends: {e}")
            raise
    
    def _calculate_sentiment_momentum(self, sentiments: List[float]) -> float:
        """
        Calculate sentiment momentum
        """
        try:
            if len(sentiments) < 2:
                return 0
        
            # Use exponential weights for recent sentiment changes
            weights = np.exp(np.linspace(-1, 0, len(sentiments)))
            weighted_changes = np.diff(sentiments) * weights[1:]
        
            return np.sum(weighted_changes)
        except Exception as e:
            logger.error(f"Error in _calculate_sentiment_momentum: {e}")
            raise
    
    def _clean_old_sentiment_history(self):
        """
        Clean old sentiment history
        """
        try:
            cutoff = datetime.now().timestamp() - (self.sentiment_window * 3600)
            self.current_sentiment = {
                t: s for t, s in self.current_sentiment.items()
                if t.timestamp() > cutoff
            }
        except Exception as e:
            logger.error(f"Error in _clean_old_sentiment_history: {e}")
            raise
    
    def get_sentiment_summary(self) -> Dict:
        """
        Get current sentiment summary
        """
        return {
            'current_sentiment': self.current_sentiment[max(self.current_sentiment.keys())]
            if self.current_sentiment else 0,
            'sentiment_trends': self.sentiment_trends,
            'source_reliability': self.source_reliability,
            'timeframe': f"{self.sentiment_window}h"
        }
