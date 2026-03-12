"""
Global + Micro Analyzer - Multi-Scale Market Intelligence
==========================================================

Combines global forces with microscopic patterns:
1. Macro-economic analysis (global forces)
2. Microstructure analysis (price patterns)
3. Cross-asset correlations
4. Sentiment aggregation
5. Event-driven analysis
6. Multi-timeframe synthesis
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
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


class MarketForce(Enum):
    """Types of market forces"""
    # Global/Macro
    MONETARY_POLICY = "monetary_policy"
    FISCAL_POLICY = "fiscal_policy"
    GEOPOLITICAL = "geopolitical"
    ECONOMIC_CYCLE = "economic_cycle"
    INFLATION = "inflation"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    
    # Micro/Technical
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    ORDERFLOW = "orderflow"
    LIQUIDITY = "liquidity"
    
    # Sentiment
    NEWS = "news"
    SOCIAL = "social"
    INSTITUTIONAL = "institutional"
    RETAIL = "retail"


class PatternType(Enum):
    """Types of patterns"""
    # Price patterns
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_SHOULDERS = "head_shoulders"
    TRIANGLE = "triangle"
    WEDGE = "wedge"
    FLAG = "flag"
    CHANNEL = "channel"
    
    # Candlestick patterns
    DOJI = "doji"
    HAMMER = "hammer"
    ENGULFING = "engulfing"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    
    # Microstructure patterns
    ABSORPTION = "absorption"
    EXHAUSTION = "exhaustion"
    BREAKOUT = "breakout"
    FAKEOUT = "fakeout"
    SWEEP = "sweep"


class TimeFrame(Enum):
    """Analysis timeframes"""
    TICK = "tick"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


@dataclass
class GlobalForceAnalysis:
    """Analysis of global/macro forces"""
    force_type: MarketForce
    direction: str  # bullish, bearish, neutral
    strength: float  # 0-1
    confidence: float  # 0-1
    description: str
    data_sources: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MicroPatternAnalysis:
    """Analysis of micro patterns"""
    pattern_type: PatternType
    timeframe: TimeFrame
    direction: str  # bullish, bearish
    strength: float  # 0-1
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketIntelligence:
    """Combined market intelligence"""
    symbol: str
    timestamp: datetime
    
    # Global analysis
    global_bias: str  # bullish, bearish, neutral
    global_strength: float
    global_forces: List[GlobalForceAnalysis]
    
    # Micro analysis
    micro_bias: str
    micro_strength: float
    patterns: List[MicroPatternAnalysis]
    
    # Combined
    overall_bias: str
    overall_confidence: float
    alignment_score: float  # How aligned global and micro are
    
    # Trading recommendation
    recommended_action: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float
    
    # Risk assessment
    risk_level: str  # low, medium, high, extreme
    key_risks: List[str]


class GlobalMicroAnalyzer:
    """
    Global + Micro Analyzer
    
    Combines macro-economic forces with microscopic price patterns
    for comprehensive market intelligence.
    
    Capabilities:
    - Macro-economic analysis
    - Microstructure pattern detection
    - Cross-asset correlation
    - Multi-timeframe synthesis
    - Sentiment aggregation
    - Risk assessment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analysis weights
        self.global_weight = self.config.get('global_weight', 0.4)
        self.micro_weight = self.config.get('micro_weight', 0.4)
        self.sentiment_weight = self.config.get('sentiment_weight', 0.2)
        
        # Timeframes to analyze
        self.timeframes = [
            TimeFrame.M5, TimeFrame.M15, TimeFrame.H1,
            TimeFrame.H4, TimeFrame.D1
        ]
        
        # Pattern detection thresholds
        self.pattern_confidence_threshold = 0.6
        
        # Cache for analysis
        self.analysis_cache: Dict[str, MarketIntelligence] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # Statistics
        self.stats = {
            'analyses_performed': 0,
            'patterns_detected': 0,
            'global_forces_analyzed': 0,
            'correct_predictions': 0
        }
        
        logger.info("Global-Micro Analyzer initialized")
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        macro_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None
    ) -> MarketIntelligence:
        """
        Perform comprehensive analysis
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV data
            macro_data: Macro-economic data
            sentiment_data: Sentiment data
            
        Returns:
            Complete market intelligence
        """
        logger.info(f"Analyzing {symbol}...")
        self.stats['analyses_performed'] += 1
        
        # Check cache
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            if datetime.now() - cached.timestamp < self.cache_ttl:
                return cached
        
        # Analyze global forces
        global_forces = await self._analyze_global_forces(macro_data or {})
        global_bias, global_strength = self._aggregate_global(global_forces)
        
        # Analyze micro patterns
        patterns = await self._analyze_micro_patterns(market_data)
        micro_bias, micro_strength = self._aggregate_micro(patterns)
        
        # Analyze sentiment
        sentiment_bias, sentiment_strength = self._analyze_sentiment(sentiment_data or {})
        
        # Combine analyses
        overall_bias, overall_confidence = self._combine_analyses(
            global_bias, global_strength,
            micro_bias, micro_strength,
            sentiment_bias, sentiment_strength
        )
        
        # Calculate alignment
        alignment_score = self._calculate_alignment(
            global_bias, micro_bias, sentiment_bias
        )
        
        # Generate trading recommendation
        recommendation = self._generate_recommendation(
            overall_bias, overall_confidence, alignment_score,
            market_data, patterns
        )
        
        # Assess risk
        risk_level, key_risks = self._assess_risk(
            global_forces, patterns, alignment_score
        )
        
        # Create intelligence report
        intelligence = MarketIntelligence(
            symbol=symbol,
            timestamp=datetime.now(),
            global_bias=global_bias,
            global_strength=global_strength,
            global_forces=global_forces,
            micro_bias=micro_bias,
            micro_strength=micro_strength,
            patterns=patterns,
            overall_bias=overall_bias,
            overall_confidence=overall_confidence,
            alignment_score=alignment_score,
            recommended_action=recommendation['action'],
            entry_price=recommendation['entry'],
            stop_loss=recommendation['stop_loss'],
            take_profit=recommendation['take_profit'],
            position_size_pct=recommendation['size'],
            risk_level=risk_level,
            key_risks=key_risks
        )
        
        # Cache result
        self.analysis_cache[cache_key] = intelligence
        
        logger.info(f"Analysis complete: {overall_bias} ({overall_confidence:.2%})")
        
        return intelligence
    
    async def _analyze_global_forces(
        self,
        macro_data: Dict
    ) -> List[GlobalForceAnalysis]:
        """Analyze global/macro forces"""
        forces = []
        
        # Monetary policy analysis
        if 'interest_rates' in macro_data or True:  # Always analyze
            rate_trend = macro_data.get('rate_trend', 'stable')
            
            if rate_trend == 'rising':
                direction = 'bearish'
                strength = 0.7
            elif rate_trend == 'falling':
                direction = 'bullish'
                strength = 0.7
            else:
                direction = 'neutral'
                strength = 0.3
            
            forces.append(GlobalForceAnalysis(
                force_type=MarketForce.MONETARY_POLICY,
                direction=direction,
                strength=strength,
                confidence=0.8,
                description=f"Interest rate trend: {rate_trend}",
                data_sources=['central_bank', 'fed']
            ))
        
        # Inflation analysis
        inflation = macro_data.get('inflation', 2.0)
        if inflation > 4:
            direction = 'bearish'
            strength = min(1.0, inflation / 10)
        elif inflation < 1:
            direction = 'bearish'  # Deflation risk
            strength = 0.5
        else:
            direction = 'neutral'
            strength = 0.3
        
        forces.append(GlobalForceAnalysis(
            force_type=MarketForce.INFLATION,
            direction=direction,
            strength=strength,
            confidence=0.85,
            description=f"Inflation at {inflation}%",
            data_sources=['cpi', 'pce']
        ))
        
        # Economic cycle
        gdp_growth = macro_data.get('gdp_growth', 2.0)
        if gdp_growth > 3:
            direction = 'bullish'
            strength = min(1.0, gdp_growth / 5)
        elif gdp_growth < 0:
            direction = 'bearish'
            strength = min(1.0, abs(gdp_growth) / 3)
        else:
            direction = 'neutral'
            strength = 0.4
        
        forces.append(GlobalForceAnalysis(
            force_type=MarketForce.ECONOMIC_CYCLE,
            direction=direction,
            strength=strength,
            confidence=0.75,
            description=f"GDP growth: {gdp_growth}%",
            data_sources=['gdp', 'economic_indicators']
        ))
        
        # Geopolitical
        geo_risk = macro_data.get('geopolitical_risk', 'low')
        if geo_risk == 'high':
            direction = 'bearish'
            strength = 0.8
        elif geo_risk == 'medium':
            direction = 'neutral'
            strength = 0.5
        else:
            direction = 'neutral'
            strength = 0.2
        
        forces.append(GlobalForceAnalysis(
            force_type=MarketForce.GEOPOLITICAL,
            direction=direction,
            strength=strength,
            confidence=0.6,
            description=f"Geopolitical risk: {geo_risk}",
            data_sources=['news', 'geopolitical_index']
        ))
        
        self.stats['global_forces_analyzed'] += len(forces)
        
        return forces
    
    async def _analyze_micro_patterns(
        self,
        market_data: Dict
    ) -> List[MicroPatternAnalysis]:
        """Analyze microscopic price patterns"""
        patterns = []
        
        prices = market_data.get('close', [])
        highs = market_data.get('high', prices)
        lows = market_data.get('low', prices)
        volumes = market_data.get('volume', [1] * len(prices))
        
        if len(prices) < 20:
            return patterns
        
        prices = np.array(prices)
        highs = np.array(highs)
        lows = np.array(lows)
        
        # Trend analysis
        trend_pattern = self._detect_trend(prices)
        if trend_pattern:
            patterns.append(trend_pattern)
        
        # Support/Resistance
        sr_patterns = self._detect_support_resistance(prices, highs, lows)
        patterns.extend(sr_patterns)
        
        # Candlestick patterns
        candle_patterns = self._detect_candlestick_patterns(
            prices, highs, lows
        )
        patterns.extend(candle_patterns)
        
        # Volume patterns
        volume_patterns = self._detect_volume_patterns(prices, volumes)
        patterns.extend(volume_patterns)
        
        # Breakout detection
        breakout = self._detect_breakout(prices, highs, lows, volumes)
        if breakout:
            patterns.append(breakout)
        
        self.stats['patterns_detected'] += len(patterns)
        
        return patterns
    
    def _detect_trend(self, prices: np.ndarray) -> Optional[MicroPatternAnalysis]:
        """Detect trend pattern"""
        if len(prices) < 20:
            return None
        
        # Calculate trend using linear regression
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        # Normalize slope
        avg_price = np.mean(prices)
        normalized_slope = slope / avg_price * 100
        
        if normalized_slope > 0.1:
            direction = 'bullish'
            strength = min(1.0, normalized_slope / 0.5)
        elif normalized_slope < -0.1:
            direction = 'bearish'
            strength = min(1.0, abs(normalized_slope) / 0.5)
        else:
            return None
        
        current_price = prices[-1]
        atr = np.mean(np.abs(np.diff(prices[-14:])))
        
        return MicroPatternAnalysis(
            pattern_type=PatternType.CHANNEL,
            timeframe=TimeFrame.H1,
            direction=direction,
            strength=strength,
            confidence=0.7,
            entry_price=current_price,
            stop_loss=current_price - atr * 2 if direction == 'bullish' else current_price + atr * 2,
            take_profit=current_price + atr * 3 if direction == 'bullish' else current_price - atr * 3,
            description=f"Trend: {direction}, slope: {normalized_slope:.4f}"
        )
    
    def _detect_support_resistance(
        self,
        prices: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> List[MicroPatternAnalysis]:
        """Detect support and resistance levels"""
        patterns = []
        
        if len(prices) < 50:
            return patterns
        
        current_price = prices[-1]
        
        # Find local maxima (resistance)
        for i in range(10, len(highs) - 10):
            if highs[i] == max(highs[i-10:i+10]):
                # Check if price is near this level
                if abs(current_price - highs[i]) / current_price < 0.02:
                    patterns.append(MicroPatternAnalysis(
                        pattern_type=PatternType.DOUBLE_TOP,
                        timeframe=TimeFrame.H4,
                        direction='bearish',
                        strength=0.6,
                        confidence=0.65,
                        entry_price=current_price,
                        stop_loss=highs[i] * 1.01,
                        take_profit=current_price * 0.95,
                        description=f"Resistance at {highs[i]:.2f}"
                    ))
                    break
        
        # Find local minima (support)
        for i in range(10, len(lows) - 10):
            if lows[i] == min(lows[i-10:i+10]):
                if abs(current_price - lows[i]) / current_price < 0.02:
                    patterns.append(MicroPatternAnalysis(
                        pattern_type=PatternType.DOUBLE_BOTTOM,
                        timeframe=TimeFrame.H4,
                        direction='bullish',
                        strength=0.6,
                        confidence=0.65,
                        entry_price=current_price,
                        stop_loss=lows[i] * 0.99,
                        take_profit=current_price * 1.05,
                        description=f"Support at {lows[i]:.2f}"
                    ))
                    break
        
        return patterns
    
    def _detect_candlestick_patterns(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray
    ) -> List[MicroPatternAnalysis]:
        """Detect candlestick patterns"""
        patterns = []
        
        if len(closes) < 3:
            return patterns
        
        # Get last few candles
        opens = np.roll(closes, 1)  # Approximate opens
        opens[0] = closes[0]
        
        # Doji detection
        body = abs(closes[-1] - opens[-1])
        range_size = highs[-1] - lows[-1]
        
        if range_size > 0 and body / range_size < 0.1:
            patterns.append(MicroPatternAnalysis(
                pattern_type=PatternType.DOJI,
                timeframe=TimeFrame.H1,
                direction='neutral',
                strength=0.5,
                confidence=0.7,
                entry_price=closes[-1],
                stop_loss=lows[-1],
                take_profit=highs[-1],
                description="Doji - indecision"
            ))
        
        # Hammer detection
        lower_wick = min(opens[-1], closes[-1]) - lows[-1]
        upper_wick = highs[-1] - max(opens[-1], closes[-1])
        
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            patterns.append(MicroPatternAnalysis(
                pattern_type=PatternType.HAMMER,
                timeframe=TimeFrame.H1,
                direction='bullish',
                strength=0.7,
                confidence=0.65,
                entry_price=closes[-1],
                stop_loss=lows[-1] * 0.99,
                take_profit=closes[-1] * 1.03,
                description="Hammer - potential reversal"
            ))
        
        # Engulfing detection
        if len(closes) >= 2:
            prev_body = closes[-2] - opens[-2]
            curr_body = closes[-1] - opens[-1]
            
            # Bullish engulfing
            if prev_body < 0 and curr_body > 0 and abs(curr_body) > abs(prev_body):
                patterns.append(MicroPatternAnalysis(
                    pattern_type=PatternType.ENGULFING,
                    timeframe=TimeFrame.H1,
                    direction='bullish',
                    strength=0.75,
                    confidence=0.7,
                    entry_price=closes[-1],
                    stop_loss=lows[-1] * 0.99,
                    take_profit=closes[-1] * 1.04,
                    description="Bullish engulfing"
                ))
            
            # Bearish engulfing
            elif prev_body > 0 and curr_body < 0 and abs(curr_body) > abs(prev_body):
                patterns.append(MicroPatternAnalysis(
                    pattern_type=PatternType.ENGULFING,
                    timeframe=TimeFrame.H1,
                    direction='bearish',
                    strength=0.75,
                    confidence=0.7,
                    entry_price=closes[-1],
                    stop_loss=highs[-1] * 1.01,
                    take_profit=closes[-1] * 0.96,
                    description="Bearish engulfing"
                ))
        
        return patterns
    
    def _detect_volume_patterns(
        self,
        prices: np.ndarray,
        volumes: List
    ) -> List[MicroPatternAnalysis]:
        """Detect volume-based patterns"""
        patterns = []
        
        if len(volumes) < 20:
            return patterns
        
        volumes = np.array(volumes)
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        
        # Volume spike
        if current_volume > avg_volume * 2:
            price_change = (prices[-1] - prices[-2]) / prices[-2]
            
            if price_change > 0:
                direction = 'bullish'
            else:
                direction = 'bearish'
            
            patterns.append(MicroPatternAnalysis(
                pattern_type=PatternType.BREAKOUT,
                timeframe=TimeFrame.H1,
                direction=direction,
                strength=min(1.0, current_volume / avg_volume / 3),
                confidence=0.6,
                entry_price=prices[-1],
                stop_loss=prices[-1] * (0.98 if direction == 'bullish' else 1.02),
                take_profit=prices[-1] * (1.04 if direction == 'bullish' else 0.96),
                description=f"Volume spike: {current_volume/avg_volume:.1f}x average"
            ))
        
        return patterns
    
    def _detect_breakout(
        self,
        prices: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: List
    ) -> Optional[MicroPatternAnalysis]:
        """Detect breakout patterns"""
        if len(prices) < 20:
            return None
        
        # Recent range
        recent_high = np.max(highs[-20:-1])
        recent_low = np.min(lows[-20:-1])
        current_price = prices[-1]
        
        # Breakout above resistance
        if current_price > recent_high:
            return MicroPatternAnalysis(
                pattern_type=PatternType.BREAKOUT,
                timeframe=TimeFrame.H1,
                direction='bullish',
                strength=0.8,
                confidence=0.7,
                entry_price=current_price,
                stop_loss=recent_high * 0.99,
                take_profit=current_price + (recent_high - recent_low),
                description=f"Breakout above {recent_high:.2f}"
            )
        
        # Breakdown below support
        if current_price < recent_low:
            return MicroPatternAnalysis(
                pattern_type=PatternType.BREAKOUT,
                timeframe=TimeFrame.H1,
                direction='bearish',
                strength=0.8,
                confidence=0.7,
                entry_price=current_price,
                stop_loss=recent_low * 1.01,
                take_profit=current_price - (recent_high - recent_low),
                description=f"Breakdown below {recent_low:.2f}"
            )
        
        return None
    
    def _aggregate_global(
        self,
        forces: List[GlobalForceAnalysis]
    ) -> Tuple[str, float]:
        """Aggregate global forces into overall bias"""
        if not forces:
            return 'neutral', 0.0
        
        bullish_score = 0.0
        bearish_score = 0.0
        
        for force in forces:
            weight = force.strength * force.confidence
            if force.direction == 'bullish':
                bullish_score += weight
            elif force.direction == 'bearish':
                bearish_score += weight
        
        total = bullish_score + bearish_score
        if total == 0:
            return 'neutral', 0.0
        
        if bullish_score > bearish_score * 1.2:
            return 'bullish', bullish_score / total
        elif bearish_score > bullish_score * 1.2:
            return 'bearish', bearish_score / total
        else:
            return 'neutral', 0.5
    
    def _aggregate_micro(
        self,
        patterns: List[MicroPatternAnalysis]
    ) -> Tuple[str, float]:
        """Aggregate micro patterns into overall bias"""
        if not patterns:
            return 'neutral', 0.0
        
        bullish_score = 0.0
        bearish_score = 0.0
        
        for pattern in patterns:
            weight = pattern.strength * pattern.confidence
            if pattern.direction == 'bullish':
                bullish_score += weight
            elif pattern.direction == 'bearish':
                bearish_score += weight
        
        total = bullish_score + bearish_score
        if total == 0:
            return 'neutral', 0.0
        
        if bullish_score > bearish_score * 1.2:
            return 'bullish', bullish_score / total
        elif bearish_score > bullish_score * 1.2:
            return 'bearish', bearish_score / total
        else:
            return 'neutral', 0.5
    
    def _analyze_sentiment(
        self,
        sentiment_data: Dict
    ) -> Tuple[str, float]:
        """Analyze sentiment data"""
        if not sentiment_data:
            return 'neutral', 0.5
        
        # Aggregate sentiment scores
        news_sentiment = sentiment_data.get('news', 0)
        social_sentiment = sentiment_data.get('social', 0)
        institutional = sentiment_data.get('institutional', 0)
        
        avg_sentiment = (news_sentiment + social_sentiment + institutional) / 3
        
        if avg_sentiment > 0.2:
            return 'bullish', min(1.0, avg_sentiment)
        elif avg_sentiment < -0.2:
            return 'bearish', min(1.0, abs(avg_sentiment))
        else:
            return 'neutral', 0.5
    
    def _combine_analyses(
        self,
        global_bias: str, global_strength: float,
        micro_bias: str, micro_strength: float,
        sentiment_bias: str, sentiment_strength: float
    ) -> Tuple[str, float]:
        """Combine all analyses into overall view"""
        # Weighted scoring
        scores = {'bullish': 0.0, 'bearish': 0.0, 'neutral': 0.0}
        
        # Global contribution
        scores[global_bias] += global_strength * self.global_weight
        
        # Micro contribution
        scores[micro_bias] += micro_strength * self.micro_weight
        
        # Sentiment contribution
        scores[sentiment_bias] += sentiment_strength * self.sentiment_weight
        
        # Determine overall bias
        best_bias = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best_bias] / total if total > 0 else 0
        
        return best_bias, confidence
    
    def _calculate_alignment(
        self,
        global_bias: str,
        micro_bias: str,
        sentiment_bias: str
    ) -> float:
        """Calculate alignment between different analyses"""
        biases = [global_bias, micro_bias, sentiment_bias]
        
        # Count agreements
        bullish_count = biases.count('bullish')
        bearish_count = biases.count('bearish')
        
        max_agreement = max(bullish_count, bearish_count)
        
        return max_agreement / 3.0
    
    def _generate_recommendation(
        self,
        overall_bias: str,
        overall_confidence: float,
        alignment_score: float,
        market_data: Dict,
        patterns: List[MicroPatternAnalysis]
    ) -> Dict[str, Any]:
        """Generate trading recommendation"""
        prices = market_data.get('close', [0])
        current_price = prices[-1] if prices else 0
        
        # Calculate ATR for stops
        if len(prices) > 14:
            atr = np.mean(np.abs(np.diff(prices[-14:])))
        else:
            atr = current_price * 0.02
        
        # Determine action
        if overall_confidence < 0.5 or alignment_score < 0.5:
            action = 'HOLD'
            size = 0
        elif overall_bias == 'bullish':
            action = 'BUY'
            size = min(0.1, overall_confidence * alignment_score * 0.15)
        elif overall_bias == 'bearish':
            action = 'SELL'
            size = min(0.1, overall_confidence * alignment_score * 0.15)
        else:
            action = 'HOLD'
            size = 0
        
        # Calculate levels
        if action == 'BUY':
            entry = current_price
            stop_loss = current_price - atr * 2
            take_profit = current_price + atr * 3
        elif action == 'SELL':
            entry = current_price
            stop_loss = current_price + atr * 2
            take_profit = current_price - atr * 3
        else:
            entry = current_price
            stop_loss = 0
            take_profit = 0
        
        return {
            'action': action,
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'size': size
        }
    
    def _assess_risk(
        self,
        global_forces: List[GlobalForceAnalysis],
        patterns: List[MicroPatternAnalysis],
        alignment_score: float
    ) -> Tuple[str, List[str]]:
        """Assess overall risk level"""
        risks = []
        risk_score = 0
        
        # Check for conflicting signals
        if alignment_score < 0.5:
            risks.append("Conflicting signals between global and micro analysis")
            risk_score += 2
        
        # Check for high-impact global forces
        for force in global_forces:
            if force.force_type == MarketForce.GEOPOLITICAL and force.strength > 0.7:
                risks.append("High geopolitical risk")
                risk_score += 2
            if force.force_type == MarketForce.MONETARY_POLICY and force.strength > 0.8:
                risks.append("Significant monetary policy impact")
                risk_score += 1
        
        # Check pattern confidence
        if patterns:
            avg_confidence = np.mean([p.confidence for p in patterns])
            if avg_confidence < 0.6:
                risks.append("Low pattern confidence")
                risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            risk_level = 'extreme'
        elif risk_score >= 3:
            risk_level = 'high'
        elif risk_score >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return risk_level, risks
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            **self.stats,
            'cache_size': len(self.analysis_cache),
            'weights': {
                'global': self.global_weight,
                'micro': self.micro_weight,
                'sentiment': self.sentiment_weight
            }
        }
