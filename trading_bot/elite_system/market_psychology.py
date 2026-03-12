"""
Elite Market Psychology Module - Advanced market psychology integration
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import logging
from datetime import datetime
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import numpy
import pandas

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentSource(Enum):
    """Sentiment data source enumeration"""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    ANALYST_RATINGS = "analyst_ratings"
    ECONOMIC_REPORTS = "economic_reports"
    TECHNICAL_INDICATORS = "technical_indicators"
    OPTIONS_FLOW = "options_flow"


class MarketSentiment(Enum):
    """Market sentiment enumeration"""
    EXTREME_FEAR = -3
    FEAR = -2
    CAUTION = -1
    NEUTRAL = 0
    OPTIMISM = 1
    GREED = 2
    EXTREME_GREED = 3


class EliteMarketPsychology:
    """
    Advanced market psychology integration system implementing elite professional trading concepts
    """
    
    def __init__(self, symbol: str = None, lookback_periods: int = 100):
        """
        Initialize the Elite Market Psychology analyzer
        
        Args:
            symbol: Trading instrument symbol
            lookback_periods: Number of periods to analyze for sentiment trends
        """
        self.symbol = symbol
        self.lookback_periods = lookback_periods
        self.sentiment_history = pd.DataFrame(columns=['timestamp', 'sentiment_score', 'source'])
        self.behavioral_metrics = {}
        self.smart_money_indicators = {}
        self.crowd_behavior_metrics = {}
        
        try:
            # Initialize sentiment analyzer
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        logger.info(f"Initialized Elite Market Psychology analyzer for {symbol}")
    
    def analyze_news_sentiment(self, news_items: List[Dict]) -> Dict:
        """
        Analyze sentiment from news articles
        
        Args:
            news_items: List of news items with 'title', 'content', and 'timestamp'
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not news_items:
            return {'sentiment_score': 0, 'sentiment_label': MarketSentiment.NEUTRAL.name}
        
        sentiment_scores = []
        
        for item in news_items:
            title = item.get('title', '')
            content = item.get('content', '')
            timestamp = item.get('timestamp', datetime.now())
            
            # Analyze title (higher weight) and content
            title_sentiment = self.sentiment_analyzer.polarity_scores(title)
            content_sentiment = self.sentiment_analyzer.polarity_scores(content)
            
            # Weighted average (title has more impact)
            compound_score = (title_sentiment['compound'] * 0.6) + (content_sentiment['compound'] * 0.4)
            
            sentiment_scores.append({
                'timestamp': timestamp,
                'sentiment_score': compound_score,
                'source': SentimentSource.NEWS.value
            })
        
        # Store sentiment history
        self._update_sentiment_history(sentiment_scores)
        
        # Calculate aggregate sentiment
        avg_sentiment = np.mean([s['sentiment_score'] for s in sentiment_scores])
        sentiment_label = self._score_to_sentiment_label(avg_sentiment)
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label.name,
            'item_count': len(news_items),
            'positive_count': sum(1 for s in sentiment_scores if s['sentiment_score'] > 0.2),
            'negative_count': sum(1 for s in sentiment_scores if s['sentiment_score'] < -0.2),
            'neutral_count': sum(1 for s in sentiment_scores if -0.2 <= s['sentiment_score'] <= 0.2)
        }
    
    def analyze_social_sentiment(self, social_posts: List[Dict]) -> Dict:
        """
        Analyze sentiment from social media posts
        
        Args:
            social_posts: List of social media posts with 'text' and 'timestamp'
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not social_posts:
            return {'sentiment_score': 0, 'sentiment_label': MarketSentiment.NEUTRAL.name}
        
        sentiment_scores = []
        
        for post in social_posts:
            text = post.get('text', '')
            timestamp = post.get('timestamp', datetime.now())
            
            # Analyze post text
            sentiment = self.sentiment_analyzer.polarity_scores(text)
            compound_score = sentiment['compound']
            
            sentiment_scores.append({
                'timestamp': timestamp,
                'sentiment_score': compound_score,
                'source': SentimentSource.SOCIAL_MEDIA.value
            })
        
        # Store sentiment history
        self._update_sentiment_history(sentiment_scores)
        
        # Calculate aggregate sentiment
        avg_sentiment = np.mean([s['sentiment_score'] for s in sentiment_scores])
        sentiment_label = self._score_to_sentiment_label(avg_sentiment)
        
        # Calculate volume and momentum metrics
        volume = len(social_posts)
        recent_posts = [p for p in social_posts if (datetime.now() - p.get('timestamp', datetime.now())).total_seconds() < 3600]
        momentum = len(recent_posts) / max(1, volume)
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label.name,
            'post_volume': volume,
            'momentum': momentum,
            'positive_count': sum(1 for s in sentiment_scores if s['sentiment_score'] > 0.2),
            'negative_count': sum(1 for s in sentiment_scores if s['sentiment_score'] < -0.2),
            'neutral_count': sum(1 for s in sentiment_scores if -0.2 <= s['sentiment_score'] <= 0.2)
        }
    
    def analyze_market_data_sentiment(self, market_data: pd.DataFrame) -> Dict:
        """
        Analyze sentiment from market data (price action, volume, etc.)
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if market_data.empty:
            return {'sentiment_score': 0, 'sentiment_label': MarketSentiment.NEUTRAL.name}
        
        # Calculate technical indicators for sentiment
        market_data = market_data.copy()
        
        # Calculate price momentum
        market_data['returns'] = market_data['close'].pct_change()
        market_data['momentum_5'] = market_data['returns'].rolling(window=5).mean()
        market_data['momentum_20'] = market_data['returns'].rolling(window=20).mean()
        
        # Calculate volume indicators
        market_data['volume_sma'] = market_data['volume'].rolling(window=20).mean()
        market_data['volume_ratio'] = market_data['volume'] / market_data['volume_sma']
        
        # Calculate volatility
        market_data['volatility'] = market_data['returns'].rolling(window=20).std()
        
        # Get latest values
        latest = market_data.iloc[-1]
        
        # Calculate sentiment score based on technical indicators
        price_momentum_score = np.tanh(latest['momentum_5'] * 100)  # Scale and bound momentum
        volume_score = np.tanh((latest['volume_ratio'] - 1) * 2)  # Volume above/below average
        
        # Combine scores (weighted)
        sentiment_score = (price_momentum_score * 0.7) + (volume_score * 0.3)
        sentiment_label = self._score_to_sentiment_label(sentiment_score)
        
        # Store in sentiment history
        self._update_sentiment_history([{
            'timestamp': market_data.index[-1] if hasattr(market_data, 'index') else datetime.now(),
            'sentiment_score': sentiment_score,
            'source': SentimentSource.TECHNICAL_INDICATORS.value
        }])
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label.name,
            'price_momentum': latest['momentum_5'],
            'volume_ratio': latest['volume_ratio'],
            'volatility': latest['volatility']
        }
    
    def detect_smart_money_activity(self, market_data: pd.DataFrame, volume_data: pd.DataFrame = None) -> Dict:
        """
        Detect institutional (smart money) activity in the market
        
        Args:
            market_data: DataFrame with OHLCV data
            volume_data: Optional DataFrame with detailed volume data (buy/sell volume)
            
        Returns:
            Dictionary with smart money activity indicators
        """
        if market_data.empty:
            return {'smart_money_active': False}
        
        results = {}
        
        # Detect large block trades
        results['block_trades'] = self._detect_block_trades(market_data)
        
        # Detect accumulation/distribution
        results['accumulation_distribution'] = self._detect_accumulation_distribution(market_data)
        
        # Detect divergences between price and volume
        results['price_volume_divergence'] = self._detect_price_volume_divergence(market_data)
        
        # Detect stop hunts
        results['stop_hunts'] = self._detect_stop_hunts(market_data)
        
        # Overall smart money activity score
        activity_score = 0
        if results['block_trades']['detected']:
            activity_score += 0.3
        if results['accumulation_distribution']['score'] > 0.7:
            activity_score += 0.3
        if results['price_volume_divergence']['detected']:
            activity_score += 0.2
        if results['stop_hunts']['detected']:
            activity_score += 0.2
        
        results['smart_money_active'] = activity_score > 0.5
        results['activity_score'] = activity_score
        
        # Store smart money indicators
        self.smart_money_indicators = results
        
        return results
    
    def analyze_crowd_behavior(self, market_data: pd.DataFrame, sentiment_data: List[Dict] = None) -> Dict:
        """
        Analyze crowd behavior patterns
        
        Args:
            market_data: DataFrame with OHLCV data
            sentiment_data: Optional list of sentiment data points
            
        Returns:
            Dictionary with crowd behavior analysis
        """
        if market_data.empty:
            return {'crowd_phase': 'unknown'}
        
        results = {}
        
        # Detect market phase
        results['market_phase'] = self._detect_market_phase(market_data)
        
        # Detect herd behavior
        results['herd_behavior'] = self._detect_herd_behavior(market_data, sentiment_data)
        
        # Detect FOMO (Fear of Missing Out)
        results['fomo'] = self._detect_fomo(market_data)
        
        # Detect capitulation
        results['capitulation'] = self._detect_capitulation(market_data)
        
        # Store crowd behavior metrics
        self.crowd_behavior_metrics = results
        
        return results
    
    def get_contrarian_signals(self) -> Dict:
        """
        Generate contrarian trading signals based on market psychology
        
        Returns:
            Dictionary with contrarian signals
        """
        signals = {}
        
        # Check for extreme sentiment
        recent_sentiment = self.get_recent_sentiment()
        if recent_sentiment['sentiment_label'] in [MarketSentiment.EXTREME_FEAR.name, MarketSentiment.EXTREME_GREED.name]:
            signals['extreme_sentiment'] = {
                'signal': 'buy' if recent_sentiment['sentiment_label'] == MarketSentiment.EXTREME_FEAR.name else 'sell',
                'strength': 0.8,
                'reason': f"Extreme {recent_sentiment['sentiment_label'].lower().replace('extreme_', '')} detected"
            }
        
        # Check for capitulation
        if self.crowd_behavior_metrics.get('capitulation', {}).get('detected', False):
            signals['capitulation'] = {
                'signal': 'buy',
                'strength': 0.9,
                'reason': "Capitulation detected"
            }
        
        # Check for FOMO
        if self.crowd_behavior_metrics.get('fomo', {}).get('detected', False):
            signals['fomo'] = {
                'signal': 'sell',
                'strength': 0.7,
                'reason': "FOMO behavior detected"
            }
        
        # Check for smart money activity against crowd
        if (self.smart_money_indicators.get('smart_money_active', False) and 
            self.crowd_behavior_metrics.get('herd_behavior', {}).get('detected', False)):
            
            # If smart money is accumulating while crowd is bearish
            if (self.smart_money_indicators.get('accumulation_distribution', {}).get('type') == 'accumulation' and
                recent_sentiment['sentiment_score'] < -0.3):
                signals['smart_money_vs_crowd'] = {
                    'signal': 'buy',
                    'strength': 0.85,
                    'reason': "Smart money accumulating while crowd is bearish"
                }
            
            # If smart money is distributing while crowd is bullish
            elif (self.smart_money_indicators.get('accumulation_distribution', {}).get('type') == 'distribution' and
                  recent_sentiment['sentiment_score'] > 0.3):
                signals['smart_money_vs_crowd'] = {
                    'signal': 'sell',
                    'strength': 0.85,
                    'reason': "Smart money distributing while crowd is bullish"
                }
        
        return signals
    
    def get_recent_sentiment(self) -> Dict:
        """
        Get recent aggregate sentiment across all sources
        
        Returns:
            Dictionary with recent sentiment metrics
        """
        if self.sentiment_history.empty:
            return {'sentiment_score': 0, 'sentiment_label': MarketSentiment.NEUTRAL.name}
        
        # Get recent sentiment (last lookback_periods)
        recent = self.sentiment_history.tail(self.lookback_periods)
        
        # Calculate aggregate sentiment
        avg_sentiment = recent['sentiment_score'].mean()
        sentiment_label = self._score_to_sentiment_label(avg_sentiment)
        
        # Calculate sentiment trend
        if len(recent) > 10:
            first_half = recent['sentiment_score'].iloc[:len(recent)//2].mean()
            second_half = recent['sentiment_score'].iloc[len(recent)//2:].mean()
            trend = second_half - first_half
        else:
            trend = 0
        
        # Calculate sentiment volatility
        volatility = recent['sentiment_score'].std()
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label.name,
            'sentiment_trend': trend,
            'sentiment_volatility': volatility,
            'data_points': len(recent)
        }
    
    def get_behavioral_bias_metrics(self) -> Dict:
        """
        Get metrics on current behavioral biases in the market
        
        Returns:
            Dictionary with behavioral bias metrics
        """
        biases = {}
        
        # Recency bias
        recent_sentiment = self.get_recent_sentiment()
        if abs(recent_sentiment['sentiment_trend']) > 0.3:
            biases['recency_bias'] = {
                'detected': True,
                'strength': min(1.0, abs(recent_sentiment['sentiment_trend']) * 2),
                'direction': 'bullish' if recent_sentiment['sentiment_trend'] > 0 else 'bearish'
            }
        else:
            biases['recency_bias'] = {'detected': False}
        
        # Confirmation bias
        if self.crowd_behavior_metrics.get('market_phase') in ['uptrend', 'downtrend']:
            direction = self.crowd_behavior_metrics.get('market_phase')
            sentiment_aligned = (direction == 'uptrend' and recent_sentiment['sentiment_score'] > 0.3) or \
                               (direction == 'downtrend' and recent_sentiment['sentiment_score'] < -0.3)
            
            if sentiment_aligned:
                biases['confirmation_bias'] = {
                    'detected': True,
                    'strength': 0.7,
                    'direction': 'bullish' if direction == 'uptrend' else 'bearish'
                }
            else:
                biases['confirmation_bias'] = {'detected': False}
        else:
            biases['confirmation_bias'] = {'detected': False}
        
        # Loss aversion
        if self.crowd_behavior_metrics.get('capitulation', {}).get('detected', False):
            biases['loss_aversion'] = {
                'detected': True,
                'strength': self.crowd_behavior_metrics['capitulation'].get('strength', 0.5),
                'direction': 'bearish'
            }
        else:
            biases['loss_aversion'] = {'detected': False}
        
        # Overconfidence
        if self.crowd_behavior_metrics.get('fomo', {}).get('detected', False):
            biases['overconfidence'] = {
                'detected': True,
                'strength': self.crowd_behavior_metrics['fomo'].get('strength', 0.5),
                'direction': 'bullish'
            }
        else:
            biases['overconfidence'] = {'detected': False}
        
        return biases
    
    # Private helper methods
    
    def _update_sentiment_history(self, sentiment_items: List[Dict]) -> None:
        """Update sentiment history with new items"""
        if not sentiment_items:
            return
            
        # Convert to DataFrame
        new_data = pd.DataFrame(sentiment_items)
        
        # Append to history
        self.sentiment_history = pd.concat([self.sentiment_history, new_data], ignore_index=True)
        
        # Keep only the most recent lookback_periods
        if len(self.sentiment_history) > self.lookback_periods * 2:
            self.sentiment_history = self.sentiment_history.tail(self.lookback_periods)
    
    def _score_to_sentiment_label(self, score: float) -> MarketSentiment:
        """Convert numerical sentiment score to sentiment label"""
        if score < -0.6:
            return MarketSentiment.EXTREME_FEAR
        elif score < -0.3:
            return MarketSentiment.FEAR
        elif score < -0.1:
            return MarketSentiment.CAUTION
        elif score <= 0.1:
            return MarketSentiment.NEUTRAL
        elif score <= 0.3:
            return MarketSentiment.OPTIMISM
        elif score <= 0.6:
            return MarketSentiment.GREED
        else:
            return MarketSentiment.EXTREME_GREED
    
    def _detect_block_trades(self, market_data: pd.DataFrame) -> Dict:
        """Detect large block trades"""
        # Calculate average volume
        avg_volume = market_data['volume'].rolling(window=20).mean()
        
        # Look for volume spikes
        volume_spikes = []
        for i in range(20, len(market_data)):
            if market_data['volume'].iloc[i] > avg_volume.iloc[i] * 3:  # Volume 3x above average
                volume_spikes.append(i)
        
        return {
            'detected': len(volume_spikes) > 0,
            'count': len(volume_spikes),
            'indices': volume_spikes
        }
    
    def _detect_accumulation_distribution(self, market_data: pd.DataFrame) -> Dict:
        """Detect accumulation/distribution patterns"""
        # Calculate Accumulation/Distribution Line
        market_data = market_data.copy()
        high = market_data['high']
        low = market_data['low']
        close = market_data['close']
        volume = market_data['volume']
        
        # Money Flow Multiplier
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.replace([np.inf, -np.inf], 0)
        
        # Money Flow Volume
        mfv = mfm * volume
        
        # Accumulation/Distribution Line
        market_data['adl'] = mfv.cumsum()
        
        # Detect divergence between price and ADL
        price_trend = close.iloc[-5:].mean() > close.iloc[-10:-5].mean()
        adl_trend = market_data['adl'].iloc[-5:].mean() > market_data['adl'].iloc[-10:-5].mean()
        
        # Determine accumulation or distribution
        if adl_trend and not price_trend:
            ad_type = 'accumulation'
            score = 0.8
        elif not adl_trend and price_trend:
            ad_type = 'distribution'
            score = 0.8
        elif adl_trend and price_trend:
            ad_type = 'aligned_bullish'
            score = 0.5
        else:
            ad_type = 'aligned_bearish'
            score = 0.5
        
        return {
            'type': ad_type,
            'score': score,
            'price_trend': 'up' if price_trend else 'down',
            'adl_trend': 'up' if adl_trend else 'down'
        }
    
    def _detect_price_volume_divergence(self, market_data: pd.DataFrame) -> Dict:
        """Detect divergences between price and volume"""
        # Calculate price and volume trends
        price_change = market_data['close'].pct_change(5)
        volume_change = market_data['volume'].pct_change(5)
        
        # Check for divergence in recent data
        recent_price_trend = np.sign(price_change.iloc[-5:].mean())
        recent_volume_trend = np.sign(volume_change.iloc[-5:].mean())
        
        # Divergence is when price and volume trends move in opposite directions
        divergence = recent_price_trend * recent_volume_trend < 0
        
        # Determine divergence type
        if divergence:
            if recent_price_trend > 0 and recent_volume_trend < 0:
                div_type = 'price_up_volume_down'
                interpretation = 'bearish'
            else:
                div_type = 'price_down_volume_up'
                interpretation = 'bullish'
        else:
            div_type = 'none'
            interpretation = 'neutral'
        
        return {
            'detected': divergence,
            'type': div_type,
            'interpretation': interpretation,
            'price_trend': 'up' if recent_price_trend > 0 else 'down',
            'volume_trend': 'up' if recent_volume_trend > 0 else 'down'
        }
    
    def _detect_stop_hunts(self, market_data: pd.DataFrame) -> Dict:
        """Detect stop hunt patterns"""
        # Look for price spikes beyond support/resistance followed by reversal
        stop_hunts = []
        
        for i in range(5, len(market_data) - 1):
            # Calculate recent high and low
            recent_high = market_data['high'].iloc[i-5:i].max()
            recent_low = market_data['low'].iloc[i-5:i].min()
            
            # Check for upward stop hunt
            if (market_data['high'].iloc[i] > recent_high * 1.005 and  # Spike above recent high
                market_data['close'].iloc[i] < recent_high and  # Close below recent high
                market_data['close'].iloc[i] < market_data['open'].iloc[i]):  # Bearish candle
                
                stop_hunts.append({
                    'index': i,
                    'type': 'upward',
                    'interpretation': 'bearish'
                })
            
            # Check for downward stop hunt
            if (market_data['low'].iloc[i] < recent_low * 0.995 and  # Spike below recent low
                market_data['close'].iloc[i] > recent_low and  # Close above recent low
                market_data['close'].iloc[i] > market_data['open'].iloc[i]):  # Bullish candle
                
                stop_hunts.append({
                    'index': i,
                    'type': 'downward',
                    'interpretation': 'bullish'
                })
        
        return {
            'detected': len(stop_hunts) > 0,
            'count': len(stop_hunts),
            'hunts': stop_hunts
        }
    
    def _detect_market_phase(self, market_data: pd.DataFrame) -> str:
        """Detect current market phase"""
        # Calculate short and long-term moving averages
        market_data = market_data.copy()
        market_data['sma20'] = market_data['close'].rolling(window=20).mean()
        market_data['sma50'] = market_data['close'].rolling(window=50).mean()
        
        # Get latest values
        latest = market_data.iloc[-1]
        
        # Determine trend
        if latest['close'] > latest['sma20'] > latest['sma50']:
            return 'uptrend'
        elif latest['close'] < latest['sma20'] < latest['sma50']:
            return 'downtrend'
        elif latest['close'] > latest['sma20'] and latest['sma20'] < latest['sma50']:
            return 'recovery'
        elif latest['close'] < latest['sma20'] and latest['sma20'] > latest['sma50']:
            return 'correction'
        else:
            return 'sideways'
    
    def _detect_herd_behavior(self, market_data: pd.DataFrame, sentiment_data: List[Dict] = None) -> Dict:
        """Detect herd behavior"""
        # Calculate price momentum
        returns = market_data['close'].pct_change()
        momentum = returns.rolling(window=5).mean()
        
        # Check for accelerating momentum
        recent_momentum = momentum.iloc[-5:]
        acceleration = recent_momentum.diff().mean()
        
        # Check sentiment alignment if available
        sentiment_aligned = False
        if sentiment_data:
            recent_sentiment = [s['sentiment_score'] for s in sentiment_data[-10:]]
            avg_sentiment = np.mean(recent_sentiment) if recent_sentiment else 0
            sentiment_aligned = (acceleration > 0 and avg_sentiment > 0.3) or (acceleration < 0 and avg_sentiment < -0.3)
        
        # Herd behavior is detected when momentum is accelerating and sentiment is aligned
        herd_detected = abs(acceleration) > 0.001 and (not sentiment_data or sentiment_aligned)
        
        return {
            'detected': herd_detected,
            'acceleration': acceleration,
            'direction': 'bullish' if acceleration > 0 else 'bearish',
            'strength': min(1.0, abs(acceleration) * 1000),
            'sentiment_aligned': sentiment_aligned if sentiment_data else None
        }
    
    def _detect_fomo(self, market_data: pd.DataFrame) -> Dict:
        """Detect Fear of Missing Out (FOMO)"""
        # Calculate returns and volume
        returns = market_data['close'].pct_change()
        volume_change = market_data['volume'].pct_change()
        
        # FOMO conditions:
        # 1. Strong positive returns
        # 2. Increasing volume
        # 3. Accelerating price movement
        
        recent_returns = returns.iloc[-5:]
        recent_volume_change = volume_change.iloc[-5:]
        
        avg_return = recent_returns.mean()
        avg_volume_change = recent_volume_change.mean()
        return_acceleration = recent_returns.diff().mean()
        
        # FOMO is detected when returns are strongly positive, volume is increasing, and price is accelerating
        fomo_detected = avg_return > 0.01 and avg_volume_change > 0.1 and return_acceleration > 0
        
        return {
            'detected': fomo_detected,
            'avg_return': avg_return,
            'avg_volume_change': avg_volume_change,
            'return_acceleration': return_acceleration,
            'strength': min(1.0, avg_return * 50) if fomo_detected else 0
        }
    
    def _detect_capitulation(self, market_data: pd.DataFrame) -> Dict:
        """Detect capitulation (panic selling)"""
        # Calculate returns and volume
        returns = market_data['close'].pct_change()
        volume_change = market_data['volume'].pct_change()
        
        # Capitulation conditions:
        # 1. Strong negative returns
        # 2. Extremely high volume
        # 3. Climactic price movement
        
        recent_returns = returns.iloc[-5:]
        recent_volume = market_data['volume'].iloc[-5:]
        avg_volume = market_data['volume'].iloc[-20:-5].mean()
        
        avg_return = recent_returns.mean()
        max_volume_ratio = recent_volume.max() / avg_volume
        
        # Capitulation is detected when returns are strongly negative and volume spikes dramatically
        capitulation_detected = avg_return < -0.02 and max_volume_ratio > 2.5
        
        return {
            'detected': capitulation_detected,
            'avg_return': avg_return,
            'max_volume_ratio': max_volume_ratio,
            'strength': min(1.0, abs(avg_return) * 25) if capitulation_detected else 0
        }
