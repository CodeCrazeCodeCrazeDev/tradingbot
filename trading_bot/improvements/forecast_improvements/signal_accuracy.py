"""
Signal Accuracy Enhancement - Improvement #3 (CRITICAL)
========================================================

Target 65%+ win rate through multi-factor confirmation.

Features:
- Multi-timeframe confirmation (M5, M15, H1, H4)
- Volume confirmation for all signals
- Market structure validation
- Trend strength filtering
- News event avoidance
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics
from typing import Set

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


class SignalDirection(Enum):
    """Signal direction"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = "very_strong"  # 90%+ confidence
    STRONG = "strong"            # 75-90% confidence
    MODERATE = "moderate"        # 60-75% confidence
    WEAK = "weak"               # 45-60% confidence
    VERY_WEAK = "very_weak"     # <45% confidence


class TrendDirection(Enum):
    """Trend direction"""
    STRONG_UP = "strong_up"
    UP = "up"
    NEUTRAL = "neutral"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class MarketStructure(Enum):
    """Market structure types"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGE = "range"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CONSOLIDATION = "consolidation"


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    direction: SignalDirection
    strength: SignalStrength
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str
    timestamp: datetime = field(default_factory=datetime.now)
    reasons: List[str] = field(default_factory=list)
    confirmations: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def risk_reward(self) -> float:
        """Calculate risk/reward ratio"""
        if self.direction == SignalDirection.BUY:
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        
        if risk > 0:
            return reward / risk
        return 0.0
    
    @property
    def confirmation_score(self) -> float:
        """Calculate confirmation score"""
        if not self.confirmations:
            return 0.0
        return sum(1 for v in self.confirmations.values() if v) / len(self.confirmations)


@dataclass
class TimeframeAnalysis:
    """Analysis for a single timeframe"""
    timeframe: str
    trend: TrendDirection
    trend_strength: float  # 0-1
    momentum: float  # -1 to 1
    volatility: float
    support: float
    resistance: float
    volume_trend: str  # "increasing", "decreasing", "stable"
    timestamp: datetime = field(default_factory=datetime.now)


class MultiTimeframeConfirmation:
    """Multi-timeframe trend confirmation"""
    
    TIMEFRAMES = ['M5', 'M15', 'H1', 'H4', 'D1']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.required_alignment = self.config.get('required_alignment', 0.6)  # 60% of timeframes must align
        self.analysis_cache: Dict[str, Dict[str, TimeframeAnalysis]] = {}
    
    async def analyze_timeframe(self, symbol: str, timeframe: str, bars: List[Dict]) -> TimeframeAnalysis:
        """Analyze a single timeframe"""
        if len(bars) < 20:
            return TimeframeAnalysis(
                timeframe=timeframe,
                trend=TrendDirection.NEUTRAL,
                trend_strength=0.0,
                momentum=0.0,
                volatility=0.0,
                support=0.0,
                resistance=0.0,
                volume_trend="stable"
            )
        
        closes = [b['close'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        volumes = [b.get('volume', 0) for b in bars]
        
        # Calculate trend using multiple methods
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
        
        # EMA calculation
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        
        # Trend direction
        current_price = closes[-1]
        trend_score = 0
        
        if current_price > sma_20:
            trend_score += 1
        else:
            trend_score -= 1
        
        if sma_20 > sma_50:
            trend_score += 1
        else:
            trend_score -= 1
        
        if ema_12 > ema_26:
            trend_score += 1
        else:
            trend_score -= 1
        
        # Higher highs / higher lows check
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]
        
        if recent_highs[-1] > max(recent_highs[:-1]) and recent_lows[-1] > min(recent_lows[:-1]):
            trend_score += 1
        elif recent_highs[-1] < min(recent_highs[:-1]) and recent_lows[-1] < max(recent_lows[:-1]):
            trend_score -= 1
        
        # Determine trend
        if trend_score >= 3:
            trend = TrendDirection.STRONG_UP
        elif trend_score >= 1:
            trend = TrendDirection.UP
        elif trend_score <= -3:
            trend = TrendDirection.STRONG_DOWN
        elif trend_score <= -1:
            trend = TrendDirection.DOWN
        else:
            trend = TrendDirection.NEUTRAL
        
        # Trend strength (0-1)
        trend_strength = min(abs(trend_score) / 4, 1.0)
        
        # Momentum (RSI-based)
        rsi = self._calculate_rsi(closes, 14)
        momentum = (rsi - 50) / 50  # -1 to 1
        
        # Volatility (ATR-based)
        atr = self._calculate_atr(highs, lows, closes, 14)
        volatility = atr / current_price if current_price > 0 else 0
        
        # Support/Resistance
        support = min(lows[-20:])
        resistance = max(highs[-20:])
        
        # Volume trend
        recent_vol = sum(volumes[-5:]) / 5 if volumes[-5:] else 0
        older_vol = sum(volumes[-20:-5]) / 15 if len(volumes) >= 20 else recent_vol
        
        if recent_vol > older_vol * 1.2:
            volume_trend = "increasing"
        elif recent_vol < older_vol * 0.8:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
        
        analysis = TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_strength=trend_strength,
            momentum=momentum,
            volatility=volatility,
            support=support,
            resistance=resistance,
            volume_trend=volume_trend
        )
        
        # Cache analysis
        if symbol not in self.analysis_cache:
            self.analysis_cache[symbol] = {}
        self.analysis_cache[symbol][timeframe] = analysis
        
        return analysis
    
    def _calculate_ema(self, data: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate ATR"""
        if len(highs) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
        
        return sum(tr_values[-period:]) / period
    
    def check_alignment(self, symbol: str, direction: SignalDirection) -> Tuple[bool, float, Dict[str, bool]]:
        """Check if timeframes are aligned with signal direction"""
        if symbol not in self.analysis_cache:
            return False, 0.0, {}
        
        analyses = self.analysis_cache[symbol]
        alignments = {}
        
        for tf, analysis in analyses.items():
            if direction == SignalDirection.BUY:
                aligned = analysis.trend in [TrendDirection.UP, TrendDirection.STRONG_UP]
            elif direction == SignalDirection.SELL:
                aligned = analysis.trend in [TrendDirection.DOWN, TrendDirection.STRONG_DOWN]
            else:
                aligned = analysis.trend == TrendDirection.NEUTRAL
            
            alignments[tf] = aligned
        
        alignment_score = sum(1 for v in alignments.values() if v) / len(alignments) if alignments else 0
        is_aligned = alignment_score >= self.required_alignment
        
        return is_aligned, alignment_score, alignments
    
    def get_dominant_trend(self, symbol: str) -> Tuple[TrendDirection, float]:
        """Get dominant trend across timeframes"""
        if symbol not in self.analysis_cache:
            return TrendDirection.NEUTRAL, 0.0
        
        analyses = self.analysis_cache[symbol]
        
        # Weight higher timeframes more
        weights = {'M5': 1, 'M15': 2, 'H1': 3, 'H4': 4, 'D1': 5}
        
        trend_score = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            weight = weights.get(tf, 1)
            total_weight += weight
            
            if analysis.trend == TrendDirection.STRONG_UP:
                trend_score += 2 * weight
            elif analysis.trend == TrendDirection.UP:
                trend_score += 1 * weight
            elif analysis.trend == TrendDirection.STRONG_DOWN:
                trend_score -= 2 * weight
            elif analysis.trend == TrendDirection.DOWN:
                trend_score -= 1 * weight
        
        if total_weight > 0:
            normalized_score = trend_score / (2 * total_weight)  # -1 to 1
        else:
            normalized_score = 0
        
        if normalized_score > 0.5:
            return TrendDirection.STRONG_UP, abs(normalized_score)
        elif normalized_score > 0.2:
            return TrendDirection.UP, abs(normalized_score)
        elif normalized_score < -0.5:
            return TrendDirection.STRONG_DOWN, abs(normalized_score)
        elif normalized_score < -0.2:
            return TrendDirection.DOWN, abs(normalized_score)
        else:
            return TrendDirection.NEUTRAL, abs(normalized_score)


class VolumeConfirmation:
    """Volume-based signal confirmation"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_volume_ratio = self.config.get('min_volume_ratio', 1.2)  # 20% above average
        self.volume_history: Dict[str, deque] = {}
        self.history_size = self.config.get('history_size', 100)
    
    def update_volume(self, symbol: str, volume: float, timestamp: Optional[datetime] = None):
        """Update volume history"""
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=self.history_size)
        
        self.volume_history[symbol].append({
            'volume': volume,
            'timestamp': timestamp or datetime.now()
        })
    
    def check_volume_confirmation(self, symbol: str, current_volume: float) -> Tuple[bool, float, str]:
        """Check if volume confirms the signal"""
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
            return True, 1.0, "Insufficient volume history"
        
        volumes = [v['volume'] for v in self.volume_history[symbol]]
        avg_volume = statistics.mean(volumes)
        
        if avg_volume == 0:
            return True, 1.0, "Zero average volume"
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= self.min_volume_ratio * 1.5:
            return True, volume_ratio, "Very high volume - strong confirmation"
        elif volume_ratio >= self.min_volume_ratio:
            return True, volume_ratio, "Above average volume - confirmed"
        elif volume_ratio >= 0.8:
            return False, volume_ratio, "Average volume - weak confirmation"
        else:
            return False, volume_ratio, "Below average volume - not confirmed"
    
    def detect_volume_spike(self, symbol: str, threshold: float = 2.0) -> bool:
        """Detect volume spike"""
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
            return False
        
        volumes = [v['volume'] for v in self.volume_history[symbol]]
        avg_volume = statistics.mean(volumes[:-1])  # Exclude current
        current_volume = volumes[-1]
        
        return current_volume > avg_volume * threshold
    
    def get_volume_trend(self, symbol: str, periods: int = 10) -> str:
        """Get volume trend"""
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < periods * 2:
            return "unknown"
        
        volumes = [v['volume'] for v in self.volume_history[symbol]]
        recent = sum(volumes[-periods:]) / periods
        older = sum(volumes[-periods*2:-periods]) / periods
        
        if recent > older * 1.2:
            return "increasing"
        elif recent < older * 0.8:
            return "decreasing"
        else:
            return "stable"


class MarketStructureValidator:
    """Validates market structure for signal quality"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.swing_lookback = self.config.get('swing_lookback', 5)
    
    def identify_structure(self, highs: List[float], lows: List[float], closes: List[float]) -> MarketStructure:
        """Identify current market structure"""
        if len(highs) < 20:
            return MarketStructure.CONSOLIDATION
        
        # Find swing highs and lows
        swing_highs = self._find_swing_highs(highs)
        swing_lows = self._find_swing_lows(lows)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return MarketStructure.CONSOLIDATION
        
        # Check for higher highs and higher lows (uptrend)
        hh = swing_highs[-1] > swing_highs[-2]
        hl = swing_lows[-1] > swing_lows[-2]
        
        # Check for lower highs and lower lows (downtrend)
        lh = swing_highs[-1] < swing_highs[-2]
        ll = swing_lows[-1] < swing_lows[-2]
        
        # Determine structure
        if hh and hl:
            return MarketStructure.UPTREND
        elif lh and ll:
            return MarketStructure.DOWNTREND
        elif hh and ll:
            return MarketStructure.BREAKOUT
        elif lh and hl:
            return MarketStructure.RANGE
        else:
            # Check for reversal patterns
            if self._check_reversal(swing_highs, swing_lows, closes):
                return MarketStructure.REVERSAL
            return MarketStructure.CONSOLIDATION
    
    def _find_swing_highs(self, highs: List[float]) -> List[float]:
        """Find swing high points"""
        swing_highs = []
        lookback = self.swing_lookback
        
        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i-lookback:i+lookback+1]):
                swing_highs.append(highs[i])
        
        return swing_highs
    
    def _find_swing_lows(self, lows: List[float]) -> List[float]:
        """Find swing low points"""
        swing_lows = []
        lookback = self.swing_lookback
        
        for i in range(lookback, len(lows) - lookback):
            if lows[i] == min(lows[i-lookback:i+lookback+1]):
                swing_lows.append(lows[i])
        
        return swing_lows
    
    def _check_reversal(self, swing_highs: List[float], swing_lows: List[float], closes: List[float]) -> bool:
        """Check for reversal pattern"""
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return False
        
        # Double top
        if abs(swing_highs[-1] - swing_highs[-2]) / swing_highs[-2] < 0.01:
            if closes[-1] < swing_lows[-1]:
                return True
        
        # Double bottom
        if abs(swing_lows[-1] - swing_lows[-2]) / swing_lows[-2] < 0.01:
            if closes[-1] > swing_highs[-1]:
                return True
        
        return False
    
    def validate_signal_structure(self, structure: MarketStructure, direction: SignalDirection) -> Tuple[bool, str]:
        """Validate if signal aligns with market structure"""
        if direction == SignalDirection.BUY:
            if structure == MarketStructure.UPTREND:
                return True, "Buy signal aligned with uptrend"
            elif structure == MarketStructure.REVERSAL:
                return True, "Potential bullish reversal"
            elif structure == MarketStructure.BREAKOUT:
                return True, "Bullish breakout"
            elif structure == MarketStructure.RANGE:
                return False, "Range-bound market - risky buy"
            elif structure == MarketStructure.DOWNTREND:
                return False, "Buy against downtrend - counter-trend"
            else:
                return False, "Consolidation - wait for clarity"
        
        elif direction == SignalDirection.SELL:
            if structure == MarketStructure.DOWNTREND:
                return True, "Sell signal aligned with downtrend"
            elif structure == MarketStructure.REVERSAL:
                return True, "Potential bearish reversal"
            elif structure == MarketStructure.BREAKOUT:
                return True, "Bearish breakout"
            elif structure == MarketStructure.RANGE:
                return False, "Range-bound market - risky sell"
            elif structure == MarketStructure.UPTREND:
                return False, "Sell against uptrend - counter-trend"
            else:
                return False, "Consolidation - wait for clarity"
        
        return False, "Neutral signal"


class TrendStrengthFilter:
    """Filters signals based on trend strength"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_adx = self.config.get('min_adx', 25)  # Minimum ADX for trend
        self.strong_adx = self.config.get('strong_adx', 40)  # Strong trend ADX
    
    def calculate_adx(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate ADX (Average Directional Index)"""
        if len(highs) < period * 2:
            return 0.0
        
        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        tr_values = []
        
        for i in range(1, len(highs)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            if high_diff > low_diff and high_diff > 0:
                plus_dm.append(high_diff)
            else:
                plus_dm.append(0)
            
            if low_diff > high_diff and low_diff > 0:
                minus_dm.append(low_diff)
            else:
                minus_dm.append(0)
            
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
        
        # Smooth values
        smoothed_plus_dm = self._smooth(plus_dm, period)
        smoothed_minus_dm = self._smooth(minus_dm, period)
        smoothed_tr = self._smooth(tr_values, period)
        
        if smoothed_tr == 0:
            return 0.0
        
        # Calculate +DI and -DI
        plus_di = 100 * smoothed_plus_dm / smoothed_tr
        minus_di = 100 * smoothed_minus_dm / smoothed_tr
        
        # Calculate DX
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 0.0
        
        dx = 100 * abs(plus_di - minus_di) / di_sum
        
        return dx
    
    def _smooth(self, values: List[float], period: int) -> float:
        """Wilder's smoothing"""
        if len(values) < period:
            return sum(values) / len(values) if values else 0
        
        first_sum = sum(values[:period])
        smoothed = first_sum
        
        for i in range(period, len(values)):
            smoothed = smoothed - (smoothed / period) + values[i]
        
        return smoothed / period
    
    def filter_by_trend_strength(self, adx: float, direction: SignalDirection) -> Tuple[bool, str, float]:
        """Filter signal based on trend strength"""
        if adx >= self.strong_adx:
            return True, f"Strong trend (ADX: {adx:.1f})", 1.0
        elif adx >= self.min_adx:
            confidence = (adx - self.min_adx) / (self.strong_adx - self.min_adx)
            return True, f"Moderate trend (ADX: {adx:.1f})", 0.5 + confidence * 0.5
        else:
            return False, f"Weak/No trend (ADX: {adx:.1f})", adx / self.min_adx


class NewsEventAvoidance:
    """Avoids trading during high-impact news events"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pre_news_minutes = self.config.get('pre_news_minutes', 30)
        self.post_news_minutes = self.config.get('post_news_minutes', 15)
        self.scheduled_events: List[Dict] = []
    
    def add_event(self, event: Dict):
        """Add scheduled news event"""
        self.scheduled_events.append(event)
    
    def set_events(self, events: List[Dict]):
        """Set all scheduled events"""
        self.scheduled_events = events
    
    def is_safe_to_trade(self, symbol: str, timestamp: Optional[datetime] = None) -> Tuple[bool, str]:
        """Check if it's safe to trade (no nearby news events)"""
        now = timestamp or datetime.now()
        
        # Extract currencies from symbol
        currencies = self._extract_currencies(symbol)
        
        for event in self.scheduled_events:
            event_time = event.get('time')
            if not event_time:
                continue
            
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time)
                except ValueError:
                    continue
            
            # Check if event affects this symbol
            event_currency = event.get('currency', '')
            if event_currency and event_currency not in currencies:
                continue
            
            # Check impact level
            impact = event.get('impact', 'low').lower()
            if impact not in ['high', 'medium']:
                continue
            
            # Check time proximity
            time_diff = (event_time - now).total_seconds() / 60  # minutes
            
            if -self.post_news_minutes <= time_diff <= self.pre_news_minutes:
                event_name = event.get('name', 'Unknown event')
                if time_diff > 0:
                    return False, f"Upcoming {impact} impact event in {time_diff:.0f} min: {event_name}"
                else:
                    return False, f"Recent {impact} impact event {abs(time_diff):.0f} min ago: {event_name}"
        
        return True, "No nearby high-impact events"
    
    def _extract_currencies(self, symbol: str) -> List[str]:
        """Extract currencies from symbol"""
        # Handle common formats: EURUSD, EUR/USD, EUR_USD
        symbol = symbol.replace('/', '').replace('_', '').upper()
        
        if len(symbol) >= 6:
            return [symbol[:3], symbol[3:6]]
        return [symbol]
    
    def get_upcoming_events(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get upcoming events for a symbol"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        currencies = self._extract_currencies(symbol)
        
        upcoming = []
        for event in self.scheduled_events:
            event_time = event.get('time')
            if not event_time:
                continue
            
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time)
                except ValueError:
                    continue
            
            if now <= event_time <= end_time:
                event_currency = event.get('currency', '')
                if not event_currency or event_currency in currencies:
                    upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.get('time', datetime.max))


class SignalAccuracyEnhancer:
    """
    Master signal accuracy enhancement system.
    Combines all confirmation methods.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.mtf_confirmation = MultiTimeframeConfirmation(self.config)
        self.volume_confirmation = VolumeConfirmation(self.config)
        self.structure_validator = MarketStructureValidator(self.config)
        self.trend_filter = TrendStrengthFilter(self.config)
        self.news_avoidance = NewsEventAvoidance(self.config)
        
        # Configuration
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.required_confirmations = self.config.get('required_confirmations', 3)
        
        # Statistics
        self.signal_history: deque = deque(maxlen=1000)
    
    async def enhance_signal(
        self,
        symbol: str,
        direction: SignalDirection,
        entry_price: float,
        bars_data: Dict[str, List[Dict]],  # timeframe -> bars
        current_volume: float
    ) -> Optional[Signal]:
        """Enhance and validate a trading signal"""
        confirmations = {}
        reasons = []
        confidence_factors = []
        
        # 1. Multi-timeframe confirmation
        for tf, bars in bars_data.items():
            if bars:
                await self.mtf_confirmation.analyze_timeframe(symbol, tf, bars)
        
        mtf_aligned, mtf_score, mtf_details = self.mtf_confirmation.check_alignment(symbol, direction)
        confirmations['multi_timeframe'] = mtf_aligned
        confidence_factors.append(mtf_score)
        
        if mtf_aligned:
            reasons.append(f"MTF aligned ({mtf_score:.0%})")
        else:
            reasons.append(f"MTF not aligned ({mtf_score:.0%})")
        
        # 2. Volume confirmation
        self.volume_confirmation.update_volume(symbol, current_volume)
        vol_confirmed, vol_ratio, vol_reason = self.volume_confirmation.check_volume_confirmation(symbol, current_volume)
        confirmations['volume'] = vol_confirmed
        confidence_factors.append(min(vol_ratio / 1.5, 1.0))
        reasons.append(vol_reason)
        
        # 3. Market structure validation
        primary_tf = 'H1'
        if primary_tf in bars_data and len(bars_data[primary_tf]) >= 20:
            bars = bars_data[primary_tf]
            highs = [b['high'] for b in bars]
            lows = [b['low'] for b in bars]
            closes = [b['close'] for b in bars]
            
            structure = self.structure_validator.identify_structure(highs, lows, closes)
            struct_valid, struct_reason = self.structure_validator.validate_signal_structure(structure, direction)
            confirmations['market_structure'] = struct_valid
            confidence_factors.append(1.0 if struct_valid else 0.3)
            reasons.append(struct_reason)
            
            # 4. Trend strength filter
            adx = self.trend_filter.calculate_adx(highs, lows, closes)
            trend_valid, trend_reason, trend_conf = self.trend_filter.filter_by_trend_strength(adx, direction)
            confirmations['trend_strength'] = trend_valid
            confidence_factors.append(trend_conf)
            reasons.append(trend_reason)
        
        # 5. News event check
        news_safe, news_reason = self.news_avoidance.is_safe_to_trade(symbol)
        confirmations['news_safe'] = news_safe
        if not news_safe:
            confidence_factors.append(0.0)
        reasons.append(news_reason)
        
        # Calculate overall confidence
        if confidence_factors:
            confidence = statistics.mean(confidence_factors)
        else:
            confidence = 0.0
        
        # Count confirmations
        num_confirmations = sum(1 for v in confirmations.values() if v)
        
        # Determine signal strength
        if confidence >= 0.8 and num_confirmations >= 4:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 0.65 and num_confirmations >= 3:
            strength = SignalStrength.STRONG
        elif confidence >= 0.5 and num_confirmations >= 2:
            strength = SignalStrength.MODERATE
        elif confidence >= 0.35:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK
        
        # Check minimum requirements
        if confidence < self.min_confidence or num_confirmations < self.required_confirmations:
            logger.info(f"Signal rejected: confidence={confidence:.2f}, confirmations={num_confirmations}")
            return None
        
        # Calculate stop loss and take profit
        if primary_tf in bars_data and bars_data[primary_tf]:
            bars = bars_data[primary_tf]
            atr = self._calculate_atr(bars)
        else:
            atr = entry_price * 0.001  # Default 0.1%
        
        if direction == SignalDirection.BUY:
            stop_loss = entry_price - (atr * 2)
            take_profit = entry_price + (atr * 3)
        else:
            stop_loss = entry_price + (atr * 2)
            take_profit = entry_price - (atr * 3)
        
        # Create enhanced signal
        signal = Signal(
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=primary_tf,
            reasons=reasons,
            confirmations=confirmations,
            metadata={
                'mtf_score': mtf_score,
                'volume_ratio': vol_ratio,
                'num_confirmations': num_confirmations
            }
        )
        
        # Record signal
        self.signal_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction.value,
            'confidence': confidence,
            'strength': strength.value,
            'confirmations': num_confirmations
        })
        
        logger.info(f"Enhanced signal: {symbol} {direction.value} - {strength.value} ({confidence:.0%})")
        return signal
    
    def _calculate_atr(self, bars: List[Dict], period: int = 14) -> float:
        """Calculate ATR from bars"""
        if len(bars) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i]['high'] - bars[i]['low'],
                abs(bars[i]['high'] - bars[i-1]['close']),
                abs(bars[i]['low'] - bars[i-1]['close'])
            )
            tr_values.append(tr)
        
        return sum(tr_values[-period:]) / period
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get signal enhancement statistics"""
        if not self.signal_history:
            return {'total_signals': 0}
        
        signals = list(self.signal_history)
        
        strength_dist = {}
        for s in signals:
            strength = s['strength']
            strength_dist[strength] = strength_dist.get(strength, 0) + 1
        
        return {
            'total_signals': len(signals),
            'avg_confidence': statistics.mean(s['confidence'] for s in signals),
            'avg_confirmations': statistics.mean(s['confirmations'] for s in signals),
            'strength_distribution': strength_dist,
            'buy_signals': sum(1 for s in signals if s['direction'] == 'buy'),
            'sell_signals': sum(1 for s in signals if s['direction'] == 'sell')
        }
    
    def set_news_events(self, events: List[Dict]):
        """Set news events for avoidance"""
        self.news_avoidance.set_events(events)
