"""
Market Psychology Engine - Advanced Sentiment and Psychology Analysis

Implements institutional-grade market psychology analysis:
- Mass psychology quantification
- Smart money tracking
- Behavioral pattern recognition
- Sentiment analysis
- Fear/Greed measurement
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque
import asyncio
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class PsychologyPhase(Enum):
    EUPHORIA = "euphoria"
    GREED = "greed"
    OPTIMISM = "optimism"
    NEUTRAL = "neutral"
    ANXIETY = "anxiety"
    FEAR = "fear"
    CAPITULATION = "capitulation"
    DEPRESSION = "depression"


class InstitutionalBias(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results"""
    overall_sentiment: float  # -1 to 1
    retail_sentiment: float
    institutional_sentiment: float
    social_sentiment: float
    news_sentiment: float
    fear_greed_index: float  # 0-100
    psychology_phase: PsychologyPhase
    contrarian_signal: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SmartMoneyTracking:
    """Smart money tracking results"""
    institutional_bias: InstitutionalBias
    accumulation_score: float  # 0-1
    distribution_score: float  # 0-1
    order_block_activity: float
    dark_pool_indicator: float
    whale_activity: float
    cot_positioning: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PsychologyState:
    """Complete market psychology state"""
    sentiment: SentimentAnalysis
    smart_money: SmartMoneyTracking
    behavioral_patterns: List[str]
    manipulation_indicators: List[str]
    trading_recommendation: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_sentiment': self.sentiment.overall_sentiment,
            'fear_greed_index': self.sentiment.fear_greed_index,
            'psychology_phase': self.sentiment.psychology_phase.value,
            'institutional_bias': self.smart_money.institutional_bias.value,
            'accumulation_score': self.smart_money.accumulation_score,
            'distribution_score': self.smart_money.distribution_score,
            'behavioral_patterns': self.behavioral_patterns,
            'manipulation_indicators': self.manipulation_indicators,
            'recommendation': self.trading_recommendation,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


class MarketPsychologyEngine:
    """
    Advanced Market Psychology Analysis Engine
    
    Analyzes market psychology through:
    - Sentiment analysis (retail, institutional, social, news)
    - Smart money tracking (accumulation, distribution, order blocks)
    - Behavioral pattern recognition
    - Fear/Greed measurement
    - Contrarian signal detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # History tracking
        self.psychology_history: deque = deque(maxlen=500)
        self.sentiment_history: deque = deque(maxlen=1000)
        
        # Thresholds
        self.extreme_fear_threshold = 20
        self.extreme_greed_threshold = 80
        self.contrarian_threshold = 0.15
        
        # State
        self.current_state: Optional[PsychologyState] = None
        
        logger.info("MarketPsychologyEngine initialized")
    
    async def analyze_psychology(
        self,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PsychologyState:
        """
        Analyze complete market psychology
        
        Args:
            market_data: Market data including prices, volumes
            context: Additional context (news, social, COT data)
            
        Returns:
            PsychologyState with complete analysis
        """
        context = context or {}
        
        # Analyze sentiment
        sentiment = await self._analyze_sentiment(market_data, context)
        
        # Track smart money
        smart_money = await self._track_smart_money(market_data, context)
        
        # Detect behavioral patterns
        behavioral_patterns = await self._detect_behavioral_patterns(market_data, sentiment)
        
        # Detect manipulation indicators
        manipulation_indicators = await self._detect_manipulation_indicators(market_data)
        
        # Generate trading recommendation
        recommendation, confidence = self._generate_recommendation(
            sentiment, smart_money, behavioral_patterns, manipulation_indicators
        )
        
        state = PsychologyState(
            sentiment=sentiment,
            smart_money=smart_money,
            behavioral_patterns=behavioral_patterns,
            manipulation_indicators=manipulation_indicators,
            trading_recommendation=recommendation,
            confidence=confidence
        )
        
        self.current_state = state
        self.psychology_history.append(state)
        
        logger.info(f"Psychology analysis: {sentiment.psychology_phase.value}, "
                   f"Institutional: {smart_money.institutional_bias.value}")
        
        return state
    
    async def _analyze_sentiment(
        self,
        market_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> SentimentAnalysis:
        """Analyze market sentiment from multiple sources"""
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        # Retail sentiment (from price action and volume)
        retail_sentiment = self._calculate_retail_sentiment(prices, volumes)
        
        # Institutional sentiment (from order flow patterns)
        institutional_sentiment = self._calculate_institutional_sentiment(prices, volumes)
        
        # Social sentiment (from context)
        social_sentiment = context.get('social_sentiment', 0.0)
        
        # News sentiment (from context)
        news_sentiment = context.get('news_sentiment', 0.0)
        
        # Calculate overall sentiment
        overall_sentiment = (
            retail_sentiment * 0.2 +
            institutional_sentiment * 0.4 +
            social_sentiment * 0.2 +
            news_sentiment * 0.2
        )
        
        # Calculate Fear/Greed Index
        fear_greed = self._calculate_fear_greed_index(
            prices, volumes, overall_sentiment
        )
        
        # Determine psychology phase
        psychology_phase = self._determine_psychology_phase(fear_greed, overall_sentiment)
        
        # Check for contrarian signal
        contrarian_signal = self._check_contrarian_signal(fear_greed, overall_sentiment)
        
        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            retail_sentiment=retail_sentiment,
            institutional_sentiment=institutional_sentiment,
            social_sentiment=social_sentiment,
            news_sentiment=news_sentiment,
            fear_greed_index=fear_greed,
            psychology_phase=psychology_phase,
            contrarian_signal=contrarian_signal
        )
    
    async def _track_smart_money(
        self,
        market_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> SmartMoneyTracking:
        """Track smart money activity"""
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        # Calculate accumulation/distribution
        accumulation_score = self._calculate_accumulation_score(prices, volumes)
        distribution_score = self._calculate_distribution_score(prices, volumes)
        
        # Order block activity
        order_block_activity = self._analyze_order_block_activity(prices, volumes)
        
        # Dark pool indicator (simulated)
        dark_pool_indicator = self._estimate_dark_pool_activity(prices, volumes)
        
        # Whale activity
        whale_activity = self._detect_whale_activity(volumes)
        
        # COT positioning (from context)
        cot_positioning = context.get('cot_data', {
            'commercial': 0.0,
            'non_commercial': 0.0,
            'retail': 0.0
        })
        
        # Determine institutional bias
        institutional_bias = self._determine_institutional_bias(
            accumulation_score, distribution_score, order_block_activity
        )
        
        return SmartMoneyTracking(
            institutional_bias=institutional_bias,
            accumulation_score=accumulation_score,
            distribution_score=distribution_score,
            order_block_activity=order_block_activity,
            dark_pool_indicator=dark_pool_indicator,
            whale_activity=whale_activity,
            cot_positioning=cot_positioning
        )
    
    async def _detect_behavioral_patterns(
        self,
        market_data: Dict[str, Any],
        sentiment: SentimentAnalysis
    ) -> List[str]:
        """Detect behavioral patterns in market"""
        patterns = []
        prices = market_data.get('prices', [])
        
        if len(prices) < 20:
            return patterns
        
        price_array = np.array(prices)
        
        # FOMO detection
        if sentiment.fear_greed_index > 75:
            recent_return = (price_array[-1] - price_array[-10]) / price_array[-10]
            if recent_return > 0.05:
                patterns.append("FOMO_BUYING")
        
        # Capitulation detection
        if sentiment.fear_greed_index < 25:
            recent_return = (price_array[-1] - price_array[-10]) / price_array[-10]
            if recent_return < -0.05:
                patterns.append("CAPITULATION_SELLING")
        
        # Retail trap detection
        volatility = np.std(np.diff(price_array) / price_array[:-1])
        if volatility > 0.03 and sentiment.retail_sentiment > 0.5:
            patterns.append("POTENTIAL_RETAIL_TRAP")
        
        # Euphoria detection
        if sentiment.psychology_phase == PsychologyPhase.EUPHORIA:
            patterns.append("EUPHORIA_PHASE")
        
        # Depression detection
        if sentiment.psychology_phase == PsychologyPhase.DEPRESSION:
            patterns.append("DEPRESSION_PHASE")
        
        # Herd behavior
        if abs(sentiment.retail_sentiment) > 0.7:
            patterns.append("HERD_BEHAVIOR")
        
        return patterns
    
    async def _detect_manipulation_indicators(
        self,
        market_data: Dict[str, Any]
    ) -> List[str]:
        """Detect potential market manipulation"""
        indicators = []
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        if len(prices) < 10:
            return indicators
        
        price_array = np.array(prices)
        volume_array = np.array(volumes) if volumes else np.ones(len(prices))
        
        # Stop hunt detection
        for i in range(-5, -1):
            if i >= -len(price_array) + 1:
                spike = abs(price_array[i] - price_array[i-1]) / price_array[i-1]
                reversal = abs(price_array[i+1] - price_array[i]) / price_array[i]
                if spike > 0.01 and reversal > 0.008:
                    indicators.append("STOP_HUNT_DETECTED")
                    break
        
        # Spoofing detection
        avg_volume = np.mean(volume_array)
        for i in range(-5, 0):
            if volume_array[i] > avg_volume * 3:
                price_change = abs(price_array[i] - price_array[i-1]) / price_array[i-1]
                if price_change < 0.002:
                    indicators.append("POTENTIAL_SPOOFING")
                    break
        
        # Wash trading detection
        volume_std = np.std(volume_array)
        unusual_volume_count = sum(1 for v in volume_array[-10:] if v > avg_volume + 2 * volume_std)
        if unusual_volume_count >= 3:
            indicators.append("UNUSUAL_VOLUME_PATTERN")
        
        # Layering detection
        if len(volume_array) >= 20:
            volume_pattern = volume_array[-20:]
            if np.corrcoef(volume_pattern[:2], volume_pattern[1:2])[0, 1] > 0.8:
                indicators.append("POTENTIAL_LAYERING")
        
        return indicators
    
    def _calculate_retail_sentiment(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate retail sentiment from price action"""
        if len(prices) < 10:
            return 0.0
        
        price_array = np.array(prices)
        
        # Recent momentum
        short_return = (price_array[-1] - price_array[-5]) / price_array[-5]
        long_return = (price_array[-1] - price_array[-20]) / price_array[-20] if len(prices) >= 20 else short_return
        
        # Retail tends to follow momentum
        sentiment = (short_return * 10 + long_return * 5) / 2
        
        return max(-1, min(1, sentiment))
    
    def _calculate_institutional_sentiment(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate institutional sentiment from order flow"""
        if len(prices) < 20 or not volumes:
            return 0.0
        
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        
        # Volume-weighted price movement
        price_changes = np.diff(price_array)
        weighted_changes = price_changes * volume_array[1:]
        
        # Institutional sentiment based on volume-weighted direction
        total_volume = np.sum(volume_array[1:])
        if total_volume > 0:
            sentiment = np.sum(weighted_changes) / (total_volume * np.mean(price_array))
        else:
            sentiment = 0.0
        
        return max(-1, min(1, sentiment * 100))
    
    def _calculate_fear_greed_index(
        self,
        prices: List[float],
        volumes: List[float],
        sentiment: float
    ) -> float:
        """Calculate Fear/Greed Index (0-100)"""
        if len(prices) < 20:
            return 50.0
        
        price_array = np.array(prices)
        
        # Components
        momentum = (price_array[-1] - price_array[-20]) / price_array[-20]
        volatility = np.std(np.diff(price_array) / price_array[:-1])
        
        # Momentum component (0-100)
        momentum_score = 50 + momentum * 500
        momentum_score = max(0, min(100, momentum_score))
        
        # Volatility component (high vol = fear)
        vol_score = 100 - min(100, volatility * 2000)
        
        # Sentiment component
        sentiment_score = (sentiment + 1) * 50
        
        # Combined index
        fear_greed = (
            momentum_score * 0.4 +
            vol_score * 0.3 +
            sentiment_score * 0.3
        )
        
        return max(0, min(100, fear_greed))
    
    def _determine_psychology_phase(self, fear_greed: float, sentiment: float) -> PsychologyPhase:
        """Determine current market psychology phase"""
        if fear_greed >= 90:
            return PsychologyPhase.EUPHORIA
        elif fear_greed >= 75:
            return PsychologyPhase.GREED
        elif fear_greed >= 55:
            return PsychologyPhase.OPTIMISM
        elif fear_greed >= 45:
            return PsychologyPhase.NEUTRAL
        elif fear_greed >= 30:
            return PsychologyPhase.ANXIETY
        elif fear_greed >= 15:
            return PsychologyPhase.FEAR
        elif fear_greed >= 5:
            return PsychologyPhase.CAPITULATION
        else:
            return PsychologyPhase.DEPRESSION
    
    def _check_contrarian_signal(self, fear_greed: float, sentiment: float) -> bool:
        """Check for contrarian trading signal"""
        # Extreme fear = potential buy
        if fear_greed < self.extreme_fear_threshold:
            return True
        # Extreme greed = potential sell
        if fear_greed > self.extreme_greed_threshold:
            return True
        return False
    
    def _calculate_accumulation_score(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate accumulation score"""
        if len(prices) < 20 or not volumes:
            return 0.5
        
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        
        # Accumulation: price stable/down with increasing volume
        price_change = (price_array[-1] - price_array[-20]) / price_array[-20]
        volume_change = np.mean(volume_array[-10:]) / np.mean(volume_array[-20:-10])
        
        if price_change < 0.02 and volume_change > 1.2:
            return min(1.0, 0.5 + volume_change * 0.3)
        elif price_change < 0 and volume_change > 1.5:
            return min(1.0, 0.6 + volume_change * 0.2)
        else:
            return 0.3
    
    def _calculate_distribution_score(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate distribution score"""
        if len(prices) < 20 or not volumes:
            return 0.5
        
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        
        # Distribution: price stable/up with increasing volume
        price_change = (price_array[-1] - price_array[-20]) / price_array[-20]
        volume_change = np.mean(volume_array[-10:]) / np.mean(volume_array[-20:-10])
        
        if price_change > -0.02 and price_change < 0.05 and volume_change > 1.2:
            return min(1.0, 0.5 + volume_change * 0.3)
        elif price_change > 0 and volume_change > 1.5:
            return min(1.0, 0.6 + volume_change * 0.2)
        else:
            return 0.3
    
    def _analyze_order_block_activity(self, prices: List[float], volumes: List[float]) -> float:
        """Analyze order block activity"""
        if len(prices) < 10 or not volumes:
            return 0.5
        
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        avg_volume = np.mean(volume_array)
        
        # Count significant order blocks
        order_blocks = 0
        for i in range(3, len(price_array) - 1):
            move = abs(price_array[i] - price_array[i-1]) / price_array[i-1]
            if move > 0.005 and volume_array[i] > avg_volume * 1.5:
                order_blocks += 1
        
        return min(1.0, order_blocks / 5)
    
    def _estimate_dark_pool_activity(self, prices: List[float], volumes: List[float]) -> float:
        """Estimate dark pool activity (simulated)"""
        if len(prices) < 10 or not volumes:
            return 0.3
        
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        
        # Large volume with minimal price impact suggests dark pool
        activity = 0.0
        for i in range(1, min(10, len(prices))):
            price_change = abs(price_array[-i] - price_array[-i-1]) / price_array[-i-1]
            volume_ratio = volume_array[-i] / np.mean(volume_array)
            
            if volume_ratio > 2 and price_change < 0.002:
                activity += 0.1
        
        return min(1.0, activity)
    
    def _detect_whale_activity(self, volumes: List[float]) -> float:
        """Detect whale activity from volume"""
        if not volumes or len(volumes) < 10:
            return 0.3
        
        volume_array = np.array(volumes)
        avg_volume = np.mean(volume_array)
        std_volume = np.std(volume_array)
        
        # Count whale-sized trades
        whale_count = sum(1 for v in volume_array[-10:] if v > avg_volume + 2 * std_volume)
        
        return min(1.0, whale_count / 5)
    
    def _determine_institutional_bias(
        self,
        accumulation: float,
        distribution: float,
        order_block: float
    ) -> InstitutionalBias:
        """Determine institutional bias"""
        net_score = accumulation - distribution + (order_block - 0.5) * 0.5
        
        if net_score > 0.4:
            return InstitutionalBias.STRONG_BULLISH
        elif net_score > 0.15:
            return InstitutionalBias.BULLISH
        elif net_score > -0.15:
            return InstitutionalBias.NEUTRAL
        elif net_score > -0.4:
            return InstitutionalBias.BEARISH
        else:
            return InstitutionalBias.STRONG_BEARISH
    
    def _generate_recommendation(
        self,
        sentiment: SentimentAnalysis,
        smart_money: SmartMoneyTracking,
        behavioral_patterns: List[str],
        manipulation_indicators: List[str]
    ) -> tuple:
        """Generate trading recommendation"""
        # Base recommendation on institutional bias
        bias = smart_money.institutional_bias
        
        if manipulation_indicators:
            return "CAUTION - Manipulation detected, avoid trading", 0.3
        
        if "CAPITULATION_SELLING" in behavioral_patterns:
            return "CONSIDER BUY - Capitulation detected", 0.7
        
        if "EUPHORIA_PHASE" in behavioral_patterns:
            return "CONSIDER SELL - Euphoria detected", 0.7
        
        if sentiment.contrarian_signal:
            if sentiment.fear_greed_index < 20:
                return "CONTRARIAN BUY - Extreme fear", 0.65
            elif sentiment.fear_greed_index > 80:
                return "CONTRARIAN SELL - Extreme greed", 0.65
        
        if bias == InstitutionalBias.STRONG_BULLISH:
            return "BULLISH - Follow smart money", 0.75
        elif bias == InstitutionalBias.BULLISH:
            return "LEAN BULLISH - Institutional accumulation", 0.6
        elif bias == InstitutionalBias.STRONG_BEARISH:
            return "BEARISH - Follow smart money", 0.75
        elif bias == InstitutionalBias.BEARISH:
            return "LEAN BEARISH - Institutional distribution", 0.6
        else:
            return "NEUTRAL - Wait for clearer signals", 0.5
    
    def get_current_state(self) -> Optional[PsychologyState]:
        """Get current psychology state"""
        return self.current_state
    
    def get_fear_greed_history(self, periods: int = 50) -> List[float]:
        """Get fear/greed index history"""
        history = list(self.psychology_history)[-periods:]
        return [s.sentiment.fear_greed_index for s in history]
