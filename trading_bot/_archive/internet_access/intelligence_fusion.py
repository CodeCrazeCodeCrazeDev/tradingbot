"""
Phase 3: Online Intelligence Integration
Merges internet data with internal models using weighted decision fusion.
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy
import pandas

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    NEWS = "news"
    MACRO = "macro"
    VOLATILITY = "volatility"


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG_BUY = 2.0
    STRONG_BUY = 1.5
    BUY = 1.0
    WEAK_BUY = 0.5
    NEUTRAL = 0.0
    WEAK_SELL = -0.5
    SELL = -1.0
    STRONG_SELL = -1.5
    VERY_STRONG_SELL = -2.0


@dataclass
class TradingSignal:
    """Individual trading signal with metadata"""
    signal_type: SignalType
    strength: float  # -2.0 to +2.0
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    symbol: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_weighted_signal(self, weight: float) -> float:
        """Get signal strength adjusted by weight and confidence"""
        return self.strength * self.confidence * weight


@dataclass
class FusedDecision:
    """Final trading decision after fusion"""
    symbol: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    strength: float
    component_signals: Dict[str, TradingSignal]
    reasoning: str
    risk_score: float = 0.5
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'confidence': round(self.confidence, 4),
            'strength': round(self.strength, 4),
            'risk_score': round(self.risk_score, 4),
            'reasoning': self.reasoning,
            'signals': {
                k: {'strength': v.strength, 'confidence': v.confidence}
                for k, v in self.component_signals.items()
            }
        }


class IntelligenceFusionEngine:
    """
    Fuses multiple intelligence sources using weighted decision fusion.
    Default weights: 60% Technical, 25% Sentiment, 15% News/Volatility
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Fusion weights (must sum to 1.0)
        self.weights = config.get('fusion_weights', {
            'technical': 0.60,
            'sentiment': 0.25,
            'news': 0.10,
            'volatility': 0.05
        })
        
        # Validate weights
        total_weight = sum(self.weights.values())
        if not (0.99 <= total_weight <= 1.01):
            logger.warning(f"Weights sum to {total_weight}, normalizing...")
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        # Confidence thresholds
        self.min_confidence = config.get('min_confidence', 0.6)
        self.strong_confidence = config.get('strong_confidence', 0.8)
        
        # Signal history
        self.signal_history: List[FusedDecision] = []
        
        logger.info(f"Intelligence Fusion initialized with weights: {self.weights}")
    
    def analyze_technical(self, market_data: Dict) -> TradingSignal:
        """
        Analyze technical indicators from market data.
        Returns technical signal with confidence.
        """
        try:
            # Extract latest data
            if not market_data:
                return TradingSignal(
                    signal_type=SignalType.TECHNICAL,
                    strength=0.0,
                    confidence=0.0,
                    timestamp=datetime.now(),
                    symbol='UNKNOWN',
                    metadata={'error': 'No market data'}
                )
            
            # Get primary timeframe (1h or first available)
            df = market_data.get('1h') or market_data.get(list(market_data.keys())[0])
            
            if df is None or df.empty:
                return TradingSignal(
                    signal_type=SignalType.TECHNICAL,
                    strength=0.0,
                    confidence=0.0,
                    timestamp=datetime.now(),
                    symbol='UNKNOWN'
                )
            
            # Calculate technical indicators
            signals = []
            
            # 1. Moving Average Crossover
            if len(df) >= 50:
                df['sma_20'] = df['close'].rolling(20).mean()
                df['sma_50'] = df['close'].rolling(50).mean()
                
                if df['sma_20'].iloc[-1] > df['sma_50'].iloc[-1]:
                    signals.append(1.0)  # Bullish
                else:
                    signals.append(-1.0)  # Bearish
            
            # 2. RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                latest_rsi = rsi.iloc[-1]
                if latest_rsi < 30:
                    signals.append(1.5)  # Oversold - strong buy
                elif latest_rsi > 70:
                    signals.append(-1.5)  # Overbought - strong sell
                else:
                    signals.append(0.0)  # Neutral
            
            # 3. MACD
            if len(df) >= 26:
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal_line = macd.ewm(span=9, adjust=False).mean()
                
                if macd.iloc[-1] > signal_line.iloc[-1]:
                    signals.append(1.0)  # Bullish
                else:
                    signals.append(-1.0)  # Bearish
            
            # 4. Bollinger Bands
            if len(df) >= 20:
                sma = df['close'].rolling(20).mean()
                std = df['close'].rolling(20).std()
                upper = sma + (2 * std)
                lower = sma - (2 * std)
                
                current_price = df['close'].iloc[-1]
                if current_price < lower.iloc[-1]:
                    signals.append(1.0)  # Price below lower band - buy
                elif current_price > upper.iloc[-1]:
                    signals.append(-1.0)  # Price above upper band - sell
                else:
                    signals.append(0.0)
            
            # Aggregate signals
            if signals:
                avg_signal = np.mean(signals)
                signal_std = np.std(signals)
                confidence = 1.0 - min(signal_std / 2.0, 0.9)  # Lower std = higher confidence
            else:
                avg_signal = 0.0
                confidence = 0.0
            
            return TradingSignal(
                signal_type=SignalType.TECHNICAL,
                strength=np.clip(avg_signal, -2.0, 2.0),
                confidence=confidence,
                timestamp=datetime.now(),
                symbol='SYMBOL',
                metadata={
                    'indicators_used': len(signals),
                    'signal_std': signal_std if signals else 0
                }
            )
        
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return TradingSignal(
                signal_type=SignalType.TECHNICAL,
                strength=0.0,
                confidence=0.0,
                timestamp=datetime.now(),
                symbol='UNKNOWN',
                metadata={'error': str(e)}
            )
    
    def analyze_sentiment(self, sentiment_data: Dict) -> TradingSignal:
        """
        Analyze sentiment data from social media and news.
        Returns sentiment signal with confidence.
        """
        try:
            if not sentiment_data:
                return TradingSignal(
                    signal_type=SignalType.SENTIMENT,
                    strength=0.0,
                    confidence=0.0,
                    timestamp=datetime.now(),
                    symbol='UNKNOWN'
                )
            
            # Aggregate sentiment across all symbols
            sentiment_scores = []
            volumes = []
            
            for symbol, data in sentiment_data.items():
                score = data.get('score', 0)
                volume = data.get('volume', 0)
                
                sentiment_scores.append(score)
                volumes.append(volume)
            
            if sentiment_scores:
                # Weight by volume
                total_volume = sum(volumes)
                if total_volume > 0:
                    weighted_sentiment = sum(
                        s * v / total_volume
                        for s, v in zip(sentiment_scores, volumes)
                    )
                else:
                    weighted_sentiment = np.mean(sentiment_scores)
                
                # Confidence based on volume and consistency
                avg_volume = np.mean(volumes)
                sentiment_std = np.std(sentiment_scores)
                
                # Higher volume and lower variance = higher confidence
                volume_factor = min(avg_volume / 10000, 1.0)
                consistency_factor = 1.0 - min(sentiment_std, 0.9)
                confidence = (volume_factor + consistency_factor) / 2
            else:
                weighted_sentiment = 0.0
                confidence = 0.0
            
            # Convert sentiment score (-1 to +1) to signal strength (-2 to +2)
            strength = weighted_sentiment * 2.0
            
            return TradingSignal(
                signal_type=SignalType.SENTIMENT,
                strength=np.clip(strength, -2.0, 2.0),
                confidence=confidence,
                timestamp=datetime.now(),
                symbol='AGGREGATE',
                metadata={
                    'symbols_analyzed': len(sentiment_scores),
                    'avg_volume': avg_volume if sentiment_scores else 0
                }
            )
        
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return TradingSignal(
                signal_type=SignalType.SENTIMENT,
                strength=0.0,
                confidence=0.0,
                timestamp=datetime.now(),
                symbol='UNKNOWN',
                metadata={'error': str(e)}
            )
    
    def analyze_news(self, news_data: List[Dict]) -> TradingSignal:
        """
        Analyze news headlines for trading signals.
        Returns news-based signal with confidence.
        """
        try:
            if not news_data:
                return TradingSignal(
                    signal_type=SignalType.NEWS,
                    strength=0.0,
                    confidence=0.0,
                    timestamp=datetime.now(),
                    symbol='UNKNOWN'
                )
            
            # Simple sentiment analysis on headlines
            positive_keywords = ['surge', 'rally', 'gain', 'rise', 'bullish', 'growth', 'strong']
            negative_keywords = ['fall', 'drop', 'decline', 'bearish', 'weak', 'crash', 'plunge']
            
            sentiment_scores = []
            
            for article in news_data[:20]:  # Analyze top 20
                title = article.get('title', '').lower()
                description = article.get('description', '').lower()
                text = title + ' ' + description
                
                positive_count = sum(1 for kw in positive_keywords if kw in text)
                negative_count = sum(1 for kw in negative_keywords if kw in text)
                
                if positive_count > negative_count:
                    sentiment_scores.append(1.0)
                elif negative_count > positive_count:
                    sentiment_scores.append(-1.0)
                else:
                    sentiment_scores.append(0.0)
            
            if sentiment_scores:
                avg_sentiment = np.mean(sentiment_scores)
                sentiment_std = np.std(sentiment_scores)
                
                # Confidence based on consistency and recency
                consistency = 1.0 - min(sentiment_std, 0.9)
                recency = min(len(news_data) / 50, 1.0)  # More news = higher confidence
                confidence = (consistency + recency) / 2
                
                strength = avg_sentiment * 1.5  # News has moderate impact
            else:
                strength = 0.0
                confidence = 0.0
            
            return TradingSignal(
                signal_type=SignalType.NEWS,
                strength=np.clip(strength, -2.0, 2.0),
                confidence=confidence,
                timestamp=datetime.now(),
                symbol='AGGREGATE',
                metadata={
                    'articles_analyzed': len(sentiment_scores),
                    'avg_sentiment': avg_sentiment if sentiment_scores else 0
                }
            )
        
        except Exception as e:
            logger.error(f"Error in news analysis: {e}")
            return TradingSignal(
                signal_type=SignalType.NEWS,
                strength=0.0,
                confidence=0.0,
                timestamp=datetime.now(),
                symbol='UNKNOWN',
                metadata={'error': str(e)}
            )
    
    def analyze_volatility(self, market_data: Dict, macro_data: Dict) -> TradingSignal:
        """
        Analyze volatility and macro conditions as a filter.
        High volatility or adverse macro = reduce position sizing.
        """
        try:
            volatility_score = 0.0
            confidence = 0.5
            
            # Check market volatility
            if market_data:
                df = market_data.get('1h') or market_data.get(list(market_data.keys())[0])
                
                if df is not None and len(df) >= 20:
                    returns = df['close'].pct_change()
                    volatility = returns.std() * np.sqrt(252)  # Annualized
                    
                    # High volatility = caution (negative signal)
                    if volatility > 0.3:
                        volatility_score = -1.0
                    elif volatility < 0.1:
                        volatility_score = 0.5  # Low vol = favorable
                    
                    confidence = 0.7
            
            # Check macro conditions
            if macro_data:
                # Adverse macro conditions = caution
                unemployment = macro_data.get('unemployment_rate', {}).get('value', 5.0)
                inflation = macro_data.get('inflation_rate', {}).get('value', 2.0)
                
                if unemployment > 7.0 or inflation > 5.0:
                    volatility_score -= 0.5
                
                confidence = 0.8
            
            return TradingSignal(
                signal_type=SignalType.VOLATILITY,
                strength=np.clip(volatility_score, -2.0, 2.0),
                confidence=confidence,
                timestamp=datetime.now(),
                symbol='MARKET',
                metadata={'volatility_filter': True}
            )
        
        except Exception as e:
            logger.error(f"Error in volatility analysis: {e}")
            return TradingSignal(
                signal_type=SignalType.VOLATILITY,
                strength=0.0,
                confidence=0.5,
                timestamp=datetime.now(),
                symbol='UNKNOWN',
                metadata={'error': str(e)}
            )
    
    def fuse_signals(
        self,
        technical: TradingSignal,
        sentiment: TradingSignal,
        news: TradingSignal,
        volatility: TradingSignal,
        symbol: str
    ) -> FusedDecision:
        """
        Fuse all signals using weighted decision fusion.
        Returns final trading decision.
        """
        # Calculate weighted signal
        weighted_sum = (
            technical.get_weighted_signal(self.weights['technical']) +
            sentiment.get_weighted_signal(self.weights['sentiment']) +
            news.get_weighted_signal(self.weights['news']) +
            volatility.get_weighted_signal(self.weights['volatility'])
        )
        
        # Calculate overall confidence
        weighted_confidence = (
            technical.confidence * self.weights['technical'] +
            sentiment.confidence * self.weights['sentiment'] +
            news.confidence * self.weights['news'] +
            volatility.confidence * self.weights['volatility']
        )
        
        # Determine action
        if weighted_sum > 0.5 and weighted_confidence >= self.min_confidence:
            action = 'BUY'
        elif weighted_sum < -0.5 and weighted_confidence >= self.min_confidence:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Build reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Technical: {technical.strength:.2f} (conf: {technical.confidence:.2f})")
        reasoning_parts.append(f"Sentiment: {sentiment.strength:.2f} (conf: {sentiment.confidence:.2f})")
        reasoning_parts.append(f"News: {news.strength:.2f} (conf: {news.confidence:.2f})")
        reasoning_parts.append(f"Volatility: {volatility.strength:.2f} (conf: {volatility.confidence:.2f})")
        reasoning_parts.append(f"Weighted signal: {weighted_sum:.2f}")
        
        reasoning = " | ".join(reasoning_parts)
        
        # Calculate risk score (inverse of confidence)
        risk_score = 1.0 - weighted_confidence
        
        decision = FusedDecision(
            symbol=symbol,
            timestamp=datetime.now(),
            action=action,
            confidence=weighted_confidence,
            strength=weighted_sum,
            component_signals={
                'technical': technical,
                'sentiment': sentiment,
                'news': news,
                'volatility': volatility
            },
            reasoning=reasoning,
            risk_score=risk_score
        )
        
        # Store in history
        self.signal_history.append(decision)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]
        
        logger.info(f"🧠 Decision: {action} {symbol} | Confidence: {weighted_confidence:.2%} | Strength: {weighted_sum:.2f}")
        logger.debug(f"   {reasoning}")
        
        return decision
    
    def process_data_package(self, data_package: Dict, symbol: str) -> FusedDecision:
        """
        Process a complete data package and return fused decision.
        """
        logger.info(f"🔄 Processing data package for {symbol}")
        
        # Analyze each component
        technical_signal = self.analyze_technical(data_package.get('market_data', {}))
        sentiment_signal = self.analyze_sentiment(data_package.get('sentiment', {}))
        news_signal = self.analyze_news(data_package.get('news', []))
        volatility_signal = self.analyze_volatility(
            data_package.get('market_data', {}),
            data_package.get('macro', {})
        )
        
        # Fuse signals
        decision = self.fuse_signals(
            technical_signal,
            sentiment_signal,
            news_signal,
            volatility_signal,
            symbol
        )
        
        return decision
    
    def get_performance_stats(self) -> Dict:
        """Get statistics on fusion performance"""
        if not self.signal_history:
            return {}
        
        actions = [d.action for d in self.signal_history]
        confidences = [d.confidence for d in self.signal_history]
        
        return {
            'total_decisions': len(self.signal_history),
            'buy_signals': actions.count('BUY'),
            'sell_signals': actions.count('SELL'),
            'hold_signals': actions.count('HOLD'),
            'avg_confidence': np.mean(confidences),
            'high_confidence_pct': sum(1 for c in confidences if c >= self.strong_confidence) / len(confidences) * 100
        }
