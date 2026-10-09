"""
Time-Scale Fusion Module
========================
Multi-timeframe signal integration with conflict resolution.

Combines:
- Microstructure (ms-seconds)
- Intraday momentum (minutes)
- Medium-term (hours)
- Macro flow (days-weeks)

Conflict Resolution:
- Confidence evaluation
- Cross-correlation analysis
- Regime evaluation
- Risk exposure assessment

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.signal import correlate
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TimeScale(Enum):
    """Time scale classifications"""
    MICRO = auto()      # ms to seconds
    INTRADAY = auto()   # minutes
    MEDIUM = auto()     # hours
    MACRO = auto()      # days to weeks


class SignalAlignment(Enum):
    """Signal alignment status"""
    ALIGNED = auto()
    PARTIAL = auto()
    CONFLICTING = auto()
    NEUTRAL = auto()


@dataclass
class TimeScaleSignal:
    """Signal from a specific time scale"""
    scale: TimeScale
    timestamp: datetime
    
    # Signal
    direction: float  # -1 to 1
    strength: float   # 0 to 1
    confidence: float # 0 to 1
    
    # Context
    regime: str = ""
    volatility: float = 0.0
    
    # Metadata
    indicators_used: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class FusedSignal:
    """Fused multi-timeframe signal"""
    timestamp: datetime
    
    # Fused output
    direction: float
    strength: float
    confidence: float
    
    # Component signals
    micro_signal: Optional[TimeScaleSignal] = None
    intraday_signal: Optional[TimeScaleSignal] = None
    medium_signal: Optional[TimeScaleSignal] = None
    macro_signal: Optional[TimeScaleSignal] = None
    
    # Alignment
    alignment: SignalAlignment = SignalAlignment.NEUTRAL
    conflict_score: float = 0.0
    
    # Risk adjustment
    risk_multiplier: float = 1.0
    
    # Reasoning
    fusion_reasoning: str = ""


@dataclass
class ConflictResolution:
    """Conflict resolution result"""
    has_conflict: bool
    conflict_type: str = ""
    resolution: str = ""
    
    # Winning signal
    dominant_scale: Optional[TimeScale] = None
    
    # Adjustments
    confidence_adjustment: float = 1.0
    position_adjustment: float = 1.0


class MicrostructureAnalyzer:
    """Analyze microstructure (ms-seconds)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tick_history: deque = deque(maxlen=10000)
        self.quote_history: deque = deque(maxlen=10000)
        
    def add_tick(self, price: float, size: float, side: str, timestamp: datetime):
        """Add tick data"""
        self.tick_history.append({
            'price': price,
            'size': size,
            'side': side,
            'timestamp': timestamp
        })
    
    def add_quote(self, bid: float, ask: float, timestamp: datetime):
        """Add quote data"""
        self.quote_history.append({
            'bid': bid,
            'ask': ask,
            'mid': (bid + ask) / 2,
            'spread': ask - bid,
            'timestamp': timestamp
        })
    
    def generate_signal(self) -> TimeScaleSignal:
        """Generate microstructure signal"""
        
        if len(self.tick_history) < 100:
            return TimeScaleSignal(
                scale=TimeScale.MICRO,
                timestamp=datetime.now(),
                direction=0,
                strength=0,
                confidence=0.3
            )
        
        ticks = list(self.tick_history)[-100:]
        
        # Order flow imbalance
        buy_volume = sum(t['size'] for t in ticks if t['side'] == 'buy')
        sell_volume = sum(t['size'] for t in ticks if t['side'] == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            imbalance = (buy_volume - sell_volume) / total_volume
        else:
            imbalance = 0
        
        # Price momentum
        prices = [t['price'] for t in ticks]
        momentum = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        
        # Spread analysis
        if self.quote_history:
            quotes = list(self.quote_history)[-50:]
            avg_spread = np.mean([q['spread'] for q in quotes])
            spread_trend = quotes[-1]['spread'] - quotes[0]['spread']
        else:
            avg_spread = 0
            spread_trend = 0
        
        # Combined signal
        direction = 0.6 * imbalance + 0.4 * np.sign(momentum)
        strength = abs(imbalance) * 0.7 + abs(momentum) * 1000 * 0.3
        
        # Confidence based on spread
        confidence = 0.7 if avg_spread < 0.0001 else 0.5
        
        return TimeScaleSignal(
            scale=TimeScale.MICRO,
            timestamp=datetime.now(),
            direction=np.clip(direction, -1, 1),
            strength=min(strength, 1.0),
            confidence=confidence,
            indicators_used=['order_flow', 'tick_momentum', 'spread'],
            reasoning=f"OFI: {imbalance:.2f}, Momentum: {momentum:.4f}"
        )


class IntradayAnalyzer:
    """Analyze intraday patterns (minutes)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.bar_history: deque = deque(maxlen=500)
        
    def add_bar(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timestamp: datetime
    ):
        """Add minute bar"""
        self.bar_history.append({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'timestamp': timestamp
        })
    
    def generate_signal(self) -> TimeScaleSignal:
        """Generate intraday signal"""
        
        if len(self.bar_history) < 50:
            return TimeScaleSignal(
                scale=TimeScale.INTRADAY,
                timestamp=datetime.now(),
                direction=0,
                strength=0,
                confidence=0.3
            )
        
        bars = list(self.bar_history)
        closes = [b['close'] for b in bars]
        volumes = [b['volume'] for b in bars]
        
        # EMA crossover
        ema_fast = self._ema(closes, 12)
        ema_slow = self._ema(closes, 26)
        ema_signal = (ema_fast - ema_slow) / ema_slow if ema_slow > 0 else 0
        
        # RSI
        rsi = self._rsi(closes, 14)
        rsi_signal = (rsi - 50) / 50
        
        # VWAP deviation
        vwap = self._vwap(bars)
        vwap_signal = (closes[-1] - vwap) / vwap if vwap > 0 else 0
        
        # Volume trend
        vol_sma = np.mean(volumes[-20:])
        vol_signal = volumes[-1] / vol_sma - 1 if vol_sma > 0 else 0
        
        # Combined
        direction = 0.4 * ema_signal * 10 + 0.3 * rsi_signal + 0.2 * vwap_signal * 10 + 0.1 * np.sign(vol_signal)
        strength = abs(ema_signal) * 10 * 0.5 + abs(rsi_signal) * 0.3 + abs(vwap_signal) * 10 * 0.2
        
        # Confidence
        confidence = 0.6 + 0.2 * (1 if vol_signal > 0.5 else 0)
        
        return TimeScaleSignal(
            scale=TimeScale.INTRADAY,
            timestamp=datetime.now(),
            direction=np.clip(direction, -1, 1),
            strength=min(strength, 1.0),
            confidence=confidence,
            indicators_used=['ema_cross', 'rsi', 'vwap', 'volume'],
            reasoning=f"EMA: {ema_signal:.4f}, RSI: {rsi:.1f}, VWAP dev: {vwap_signal:.4f}"
        )
    
    def _ema(self, data: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(data) < period:
            return data[-1] if data else 0
        
        multiplier = 2 / (period + 1)
        ema = data[0]
        for price in data[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _rsi(self, data: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(data) < period + 1:
            return 50
        
        deltas = np.diff(data[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _vwap(self, bars: List[Dict]) -> float:
        """Calculate VWAP"""
        total_pv = sum(
            (b['high'] + b['low'] + b['close']) / 3 * b['volume']
            for b in bars
        )
        total_vol = sum(b['volume'] for b in bars)
        return total_pv / total_vol if total_vol > 0 else 0


class MediumTermAnalyzer:
    """Analyze medium-term patterns (hours)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.hourly_history: deque = deque(maxlen=200)
        
    def add_hourly(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timestamp: datetime
    ):
        """Add hourly bar"""
        self.hourly_history.append({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'timestamp': timestamp
        })
    
    def generate_signal(self) -> TimeScaleSignal:
        """Generate medium-term signal"""
        
        if len(self.hourly_history) < 24:
            return TimeScaleSignal(
                scale=TimeScale.MEDIUM,
                timestamp=datetime.now(),
                direction=0,
                strength=0,
                confidence=0.3
            )
        
        bars = list(self.hourly_history)
        closes = [b['close'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        
        # Trend analysis
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
        
        trend_signal = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
        
        # Volatility regime
        atr = self._atr(highs, lows, closes, 14)
        volatility = atr / closes[-1] if closes[-1] > 0 else 0
        
        # Support/Resistance
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        current = closes[-1]
        
        sr_position = (current - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
        sr_signal = sr_position - 0.5  # -0.5 to 0.5
        
        # Combined
        direction = 0.6 * trend_signal * 10 + 0.4 * sr_signal
        strength = abs(trend_signal) * 10 * 0.7 + abs(sr_signal) * 0.3
        
        return TimeScaleSignal(
            scale=TimeScale.MEDIUM,
            timestamp=datetime.now(),
            direction=np.clip(direction, -1, 1),
            strength=min(strength, 1.0),
            confidence=0.7,
            volatility=volatility,
            indicators_used=['sma_trend', 'atr', 'sr_levels'],
            reasoning=f"Trend: {trend_signal:.4f}, S/R pos: {sr_position:.2f}"
        )
    
    def _atr(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int
    ) -> float:
        """Calculate ATR"""
        if len(highs) < period + 1:
            return 0
        
        trs = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            trs.append(tr)
        
        return np.mean(trs[-period:])


class MacroFlowAnalyzer:
    """Analyze macro flow (days-weeks)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.daily_history: deque = deque(maxlen=100)
        self.macro_indicators: Dict[str, float] = {}
        
    def add_daily(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timestamp: datetime
    ):
        """Add daily bar"""
        self.daily_history.append({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'timestamp': timestamp
        })
    
    def update_macro(self, indicators: Dict[str, float]):
        """Update macro indicators"""
        self.macro_indicators.update(indicators)
    
    def generate_signal(self) -> TimeScaleSignal:
        """Generate macro signal"""
        
        if len(self.daily_history) < 20:
            return TimeScaleSignal(
                scale=TimeScale.MACRO,
                timestamp=datetime.now(),
                direction=0,
                strength=0,
                confidence=0.3
            )
        
        bars = list(self.daily_history)
        closes = [b['close'] for b in bars]
        volumes = [b['volume'] for b in bars]
        
        # Long-term trend
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
        
        trend = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
        
        # Volume trend
        vol_20 = np.mean(volumes[-20:])
        vol_50 = np.mean(volumes[-50:]) if len(volumes) >= 50 else vol_20
        vol_trend = (vol_20 - vol_50) / vol_50 if vol_50 > 0 else 0
        
        # Macro indicators
        vix = self.macro_indicators.get('vix', 20)
        vix_signal = (20 - vix) / 20  # Negative when VIX high
        
        yield_curve = self.macro_indicators.get('yield_curve', 0)
        yc_signal = yield_curve  # Positive slope = bullish
        
        # Combined
        direction = 0.4 * trend * 10 + 0.2 * vol_trend + 0.2 * vix_signal + 0.2 * yc_signal
        strength = abs(trend) * 10 * 0.5 + abs(vix_signal) * 0.3 + abs(yc_signal) * 0.2
        
        return TimeScaleSignal(
            scale=TimeScale.MACRO,
            timestamp=datetime.now(),
            direction=np.clip(direction, -1, 1),
            strength=min(strength, 1.0),
            confidence=0.8,
            regime='risk_on' if vix < 20 else 'risk_off',
            indicators_used=['sma_trend', 'volume_trend', 'vix', 'yield_curve'],
            reasoning=f"Trend: {trend:.4f}, VIX: {vix:.1f}, YC: {yield_curve:.2f}"
        )


class ConflictResolver:
    """Resolve conflicts between time scales"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Scale weights (higher = more important)
        self.scale_weights = {
            TimeScale.MICRO: 0.15,
            TimeScale.INTRADAY: 0.25,
            TimeScale.MEDIUM: 0.30,
            TimeScale.MACRO: 0.30
        }
        
    def resolve(
        self,
        signals: Dict[TimeScale, TimeScaleSignal]
    ) -> ConflictResolution:
        """Resolve conflicts between signals"""
        
        if len(signals) < 2:
            return ConflictResolution(has_conflict=False)
        
        # Check for directional conflict
        directions = {scale: sig.direction for scale, sig in signals.items()}
        
        positive = sum(1 for d in directions.values() if d > 0.2)
        negative = sum(1 for d in directions.values() if d < -0.2)
        
        has_conflict = positive > 0 and negative > 0
        
        if not has_conflict:
            return ConflictResolution(has_conflict=False)
        
        # Determine conflict type
        if TimeScale.MACRO in signals and TimeScale.MICRO in signals:
            macro_dir = signals[TimeScale.MACRO].direction
            micro_dir = signals[TimeScale.MICRO].direction
            
            if np.sign(macro_dir) != np.sign(micro_dir):
                conflict_type = "macro_micro_divergence"
            else:
                conflict_type = "general_conflict"
        else:
            conflict_type = "general_conflict"
        
        # Find dominant signal
        weighted_scores = {}
        for scale, signal in signals.items():
            score = signal.direction * signal.confidence * self.scale_weights[scale]
            weighted_scores[scale] = score
        
        dominant_scale = max(weighted_scores.items(), key=lambda x: abs(x[1]))[0]
        
        # Calculate adjustments
        max_confidence = max(s.confidence for s in signals.values())
        min_confidence = min(s.confidence for s in signals.values())
        
        confidence_adjustment = 0.5 + 0.5 * (1 - (max_confidence - min_confidence))
        position_adjustment = 0.5 if conflict_type == "macro_micro_divergence" else 0.7
        
        return ConflictResolution(
            has_conflict=True,
            conflict_type=conflict_type,
            resolution=f"Following {dominant_scale.name} signal with reduced size",
            dominant_scale=dominant_scale,
            confidence_adjustment=confidence_adjustment,
            position_adjustment=position_adjustment
        )
    
    def calculate_cross_correlation(
        self,
        signals: Dict[TimeScale, TimeScaleSignal]
    ) -> float:
        """Calculate cross-correlation between scales"""
        
        if len(signals) < 2:
            return 1.0
        
        directions = [s.direction for s in signals.values()]
        
        # Pairwise correlation
        correlations = []
        for i in range(len(directions)):
            for j in range(i + 1, len(directions)):
                corr = 1 if np.sign(directions[i]) == np.sign(directions[j]) else -1
                correlations.append(corr)
        
        return np.mean(correlations) if correlations else 0


class TimeScaleFusion:
    """
    Complete Time-Scale Fusion Module.
    
    Combines:
    - Microstructure (ms-seconds)
    - Intraday momentum (minutes)
    - Medium-term (hours)
    - Macro flow (days-weeks)
    
    With conflict resolution based on:
    - Confidence evaluation
    - Cross-correlation
    - Regime evaluation
    - Risk exposure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analyzers
        self.micro_analyzer = MicrostructureAnalyzer(config)
        self.intraday_analyzer = IntradayAnalyzer(config)
        self.medium_analyzer = MediumTermAnalyzer(config)
        self.macro_analyzer = MacroFlowAnalyzer(config)
        
        # Conflict resolver
        self.conflict_resolver = ConflictResolver(config)
        
        # History
        self.fusion_history: List[FusedSignal] = []
        
        logger.info("TimeScaleFusion initialized")
    
    def update_micro(self, price: float, size: float, side: str, bid: float, ask: float):
        """Update microstructure data"""
        now = datetime.now()
        self.micro_analyzer.add_tick(price, size, side, now)
        self.micro_analyzer.add_quote(bid, ask, now)
    
    def update_intraday(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float
    ):
        """Update intraday data"""
        self.intraday_analyzer.add_bar(open_, high, low, close, volume, datetime.now())
    
    def update_medium(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float
    ):
        """Update medium-term data"""
        self.medium_analyzer.add_hourly(open_, high, low, close, volume, datetime.now())
    
    def update_macro(
        self,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        indicators: Dict[str, float] = None
    ):
        """Update macro data"""
        self.macro_analyzer.add_daily(open_, high, low, close, volume, datetime.now())
        if indicators:
            self.macro_analyzer.update_macro(indicators)
    
    def fuse(self) -> FusedSignal:
        """Fuse all time scale signals"""
        
        # Generate signals from each scale
        micro_signal = self.micro_analyzer.generate_signal()
        intraday_signal = self.intraday_analyzer.generate_signal()
        medium_signal = self.medium_analyzer.generate_signal()
        macro_signal = self.macro_analyzer.generate_signal()
        
        signals = {
            TimeScale.MICRO: micro_signal,
            TimeScale.INTRADAY: intraday_signal,
            TimeScale.MEDIUM: medium_signal,
            TimeScale.MACRO: macro_signal
        }
        
        # Resolve conflicts
        resolution = self.conflict_resolver.resolve(signals)
        cross_corr = self.conflict_resolver.calculate_cross_correlation(signals)
        
        # Calculate fused signal
        weights = self.conflict_resolver.scale_weights
        
        weighted_direction = sum(
            signals[scale].direction * signals[scale].confidence * weights[scale]
            for scale in signals
        )
        total_weight = sum(
            signals[scale].confidence * weights[scale]
            for scale in signals
        )
        
        if total_weight > 0:
            fused_direction = weighted_direction / total_weight
        else:
            fused_direction = 0
        
        # Calculate strength and confidence
        fused_strength = np.mean([s.strength for s in signals.values()])
        fused_confidence = np.mean([s.confidence for s in signals.values()])
        
        # Apply conflict adjustments
        if resolution.has_conflict:
            fused_confidence *= resolution.confidence_adjustment
            fused_strength *= resolution.position_adjustment
        
        # Determine alignment
        if cross_corr > 0.5:
            alignment = SignalAlignment.ALIGNED
        elif cross_corr > 0:
            alignment = SignalAlignment.PARTIAL
        elif cross_corr < -0.3:
            alignment = SignalAlignment.CONFLICTING
        else:
            alignment = SignalAlignment.NEUTRAL
        
        # Risk multiplier based on alignment
        risk_multiplier = 1.0
        if alignment == SignalAlignment.CONFLICTING:
            risk_multiplier = 0.5
        elif alignment == SignalAlignment.PARTIAL:
            risk_multiplier = 0.75
        elif alignment == SignalAlignment.ALIGNED:
            risk_multiplier = 1.2
        
        fused = FusedSignal(
            timestamp=datetime.now(),
            direction=np.clip(fused_direction, -1, 1),
            strength=min(fused_strength, 1.0),
            confidence=fused_confidence,
            micro_signal=micro_signal,
            intraday_signal=intraday_signal,
            medium_signal=medium_signal,
            macro_signal=macro_signal,
            alignment=alignment,
            conflict_score=1 - cross_corr,
            risk_multiplier=risk_multiplier,
            fusion_reasoning=self._generate_reasoning(signals, resolution, alignment)
        )
        
        self.fusion_history.append(fused)
        
        return fused
    
    def _generate_reasoning(
        self,
        signals: Dict[TimeScale, TimeScaleSignal],
        resolution: ConflictResolution,
        alignment: SignalAlignment
    ) -> str:
        """Generate reasoning for fused signal"""
        
        parts = []
        
        for scale, signal in signals.items():
            dir_str = "bullish" if signal.direction > 0.2 else "bearish" if signal.direction < -0.2 else "neutral"
            parts.append(f"{scale.name}: {dir_str} ({signal.confidence:.0%})")
        
        parts.append(f"Alignment: {alignment.name}")
        
        if resolution.has_conflict:
            parts.append(f"Conflict: {resolution.conflict_type}")
            parts.append(f"Following: {resolution.dominant_scale.name if resolution.dominant_scale else 'N/A'}")
        
        return " | ".join(parts)
    
    def get_scale_breakdown(self) -> Dict[str, Any]:
        """Get breakdown by time scale"""
        
        if not self.fusion_history:
            return {}
        
        latest = self.fusion_history[-1]
        
        return {
            'micro': {
                'direction': latest.micro_signal.direction if latest.micro_signal else 0,
                'confidence': latest.micro_signal.confidence if latest.micro_signal else 0,
                'reasoning': latest.micro_signal.reasoning if latest.micro_signal else ""
            },
            'intraday': {
                'direction': latest.intraday_signal.direction if latest.intraday_signal else 0,
                'confidence': latest.intraday_signal.confidence if latest.intraday_signal else 0,
                'reasoning': latest.intraday_signal.reasoning if latest.intraday_signal else ""
            },
            'medium': {
                'direction': latest.medium_signal.direction if latest.medium_signal else 0,
                'confidence': latest.medium_signal.confidence if latest.medium_signal else 0,
                'reasoning': latest.medium_signal.reasoning if latest.medium_signal else ""
            },
            'macro': {
                'direction': latest.macro_signal.direction if latest.macro_signal else 0,
                'confidence': latest.macro_signal.confidence if latest.macro_signal else 0,
                'reasoning': latest.macro_signal.reasoning if latest.macro_signal else ""
            },
            'fused': {
                'direction': latest.direction,
                'confidence': latest.confidence,
                'alignment': latest.alignment.name,
                'risk_multiplier': latest.risk_multiplier
            }
        }


# Factory function
def create_time_scale_fusion(config: Optional[Dict] = None) -> TimeScaleFusion:
    """Create and return a TimeScaleFusion instance"""
    return TimeScaleFusion(config)
