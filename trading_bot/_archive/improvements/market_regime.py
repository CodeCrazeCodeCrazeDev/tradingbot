"""
Market Regime Detection
=======================

Detects and classifies market conditions:
1. Trending vs Ranging
2. Volatility regime (low/normal/high/extreme)
3. Momentum regime
4. Liquidity regime

Target: Adapt strategy to current market conditions
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Types of market regimes"""
    STRONG_TREND_UP = "strong_trend_up"
    TREND_UP = "trend_up"
    RANGING = "ranging"
    TREND_DOWN = "trend_down"
    STRONG_TREND_DOWN = "strong_trend_down"
    CHOPPY = "choppy"
    BREAKOUT = "breakout"


class VolatilityRegime(Enum):
    """Volatility regime classification"""
    VERY_LOW = "very_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class MomentumRegime(Enum):
    """Momentum regime classification"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class MarketRegime:
    """Complete market regime analysis"""
    symbol: str
    timestamp: datetime
    
    # Primary regime
    regime_type: RegimeType
    regime_confidence: float
    
    # Volatility
    volatility_regime: VolatilityRegime
    current_volatility: float
    volatility_percentile: float
    
    # Momentum
    momentum_regime: MomentumRegime
    momentum_score: float
    
    # Trend
    trend_strength: float  # 0-1
    trend_direction: int   # 1 = up, -1 = down, 0 = neutral
    
    # Trading recommendations
    recommended_strategy: str
    position_size_multiplier: float
    avoid_trading: bool
    reasons: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'regime_type': self.regime_type.value,
            'regime_confidence': self.regime_confidence,
            'volatility_regime': self.volatility_regime.value,
            'momentum_regime': self.momentum_regime.value,
            'trend_strength': self.trend_strength,
            'recommended_strategy': self.recommended_strategy,
            'position_size_multiplier': self.position_size_multiplier,
            'avoid_trading': self.avoid_trading,
            'reasons': self.reasons,
        }


class MarketRegimeDetector:
    """
    Detects current market regime for strategy adaptation.
    
    PRINCIPLE: Different market conditions require different strategies.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # ADX threshold for trending
        self.adx_trend_threshold = self.config.get('adx_trend_threshold', 25)
        self.adx_strong_trend = self.config.get('adx_strong_trend', 40)
        
        # ATR lookback for volatility
        self.atr_period = self.config.get('atr_period', 14)
        self.volatility_lookback = self.config.get('volatility_lookback', 100)
        
        # Momentum settings
        self.momentum_period = self.config.get('momentum_period', 14)
        
        # Range detection
        self.range_atr_multiplier = self.config.get('range_atr_multiplier', 2.0)
        
        logger.info("MarketRegimeDetector initialized")
    
    def detect(
        self,
        symbol: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: Optional[np.ndarray] = None
    ) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            symbol: Trading symbol
            highs: High prices
            lows: Low prices
            closes: Close prices
            volumes: Volume data (optional)
        
        Returns:
            MarketRegime with complete analysis
        """
        reasons = []
        
        # Calculate indicators
        atr = self._calculate_atr(highs, lows, closes)
        adx, plus_di, minus_di = self._calculate_adx(highs, lows, closes)
        rsi = self._calculate_rsi(closes)
        
        # 1. Detect volatility regime
        volatility_regime, vol_percentile = self._detect_volatility_regime(
            atr, highs, lows, closes
        )
        reasons.append(f"Volatility: {volatility_regime.value} ({vol_percentile:.0f}th percentile)")
        
        # 2. Detect trend/range
        regime_type, trend_strength, trend_direction = self._detect_trend_regime(
            adx, plus_di, minus_di, closes
        )
        reasons.append(f"Regime: {regime_type.value} (strength: {trend_strength:.2f})")
        
        # 3. Detect momentum
        momentum_regime, momentum_score = self._detect_momentum_regime(rsi, closes)
        reasons.append(f"Momentum: {momentum_regime.value} (score: {momentum_score:.2f})")
        
        # 4. Determine trading recommendations
        recommended_strategy, size_multiplier, avoid = self._get_recommendations(
            regime_type, volatility_regime, momentum_regime, trend_strength
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            adx, trend_strength, vol_percentile
        )
        
        return MarketRegime(
            symbol=symbol,
            timestamp=datetime.now(),
            regime_type=regime_type,
            regime_confidence=confidence,
            volatility_regime=volatility_regime,
            current_volatility=atr,
            volatility_percentile=vol_percentile,
            momentum_regime=momentum_regime,
            momentum_score=momentum_score,
            trend_strength=trend_strength,
            trend_direction=trend_direction,
            recommended_strategy=recommended_strategy,
            position_size_multiplier=size_multiplier,
            avoid_trading=avoid,
            reasons=reasons
        )
    
    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> float:
        """Calculate Average True Range"""
        if len(highs) < self.atr_period + 1:
            return 0.0
        
        tr = np.zeros(len(highs))
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
        
        return np.mean(tr[-self.atr_period:])
    
    def _calculate_adx(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> Tuple[float, float, float]:
        """Calculate ADX, +DI, -DI"""
        if len(highs) < period * 2:
            return 0.0, 0.0, 0.0
        
        # Calculate +DM and -DM
        plus_dm = np.zeros(len(highs))
        minus_dm = np.zeros(len(highs))
        tr = np.zeros(len(highs))
        
        for i in range(1, len(highs)):
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
            
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
        
        # Smooth with EMA
        smoothed_tr = self._ema(tr, period)
        smoothed_plus_dm = self._ema(plus_dm, period)
        smoothed_minus_dm = self._ema(minus_dm, period)
        
        # Calculate +DI and -DI
        plus_di = 100 * smoothed_plus_dm[-1] / smoothed_tr[-1] if smoothed_tr[-1] > 0 else 0
        minus_di = 100 * smoothed_minus_dm[-1] / smoothed_tr[-1] if smoothed_tr[-1] > 0 else 0
        
        # Calculate DX and ADX
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum if di_sum > 0 else 0
        
        # ADX is smoothed DX (simplified)
        adx = dx  # In practice, this should be smoothed over period
        
        return adx, plus_di, minus_di
    
    def _calculate_rsi(self, closes: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50.0
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def _detect_volatility_regime(
        self,
        current_atr: float,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Tuple[VolatilityRegime, float]:
        """Detect volatility regime"""
        if len(closes) < self.volatility_lookback:
            return VolatilityRegime.NORMAL, 50.0
        
        # Calculate historical ATR values
        atr_history = []
        for i in range(self.atr_period, len(closes)):
            h = highs[i-self.atr_period:i]
            l = lows[i-self.atr_period:i]
            c = closes[i-self.atr_period:i]
            atr_history.append(self._calculate_atr(h, l, c))
        
        if not atr_history:
            return VolatilityRegime.NORMAL, 50.0
        
        # Calculate percentile
        percentile = (np.sum(np.array(atr_history) < current_atr) / len(atr_history)) * 100
        
        # Classify
        if percentile < 10:
            regime = VolatilityRegime.VERY_LOW
        elif percentile < 30:
            regime = VolatilityRegime.LOW
        elif percentile < 70:
            regime = VolatilityRegime.NORMAL
        elif percentile < 90:
            regime = VolatilityRegime.HIGH
        else:
            regime = VolatilityRegime.EXTREME
        
        return regime, percentile
    
    def _detect_trend_regime(
        self,
        adx: float,
        plus_di: float,
        minus_di: float,
        closes: np.ndarray
    ) -> Tuple[RegimeType, float, int]:
        """Detect trend/range regime"""
        # Determine trend direction
        if plus_di > minus_di:
            direction = 1
        elif minus_di > plus_di:
            direction = -1
        else:
            direction = 0
        
        # Calculate trend strength (normalized ADX)
        trend_strength = min(1.0, adx / 50)
        
        # Classify regime
        if adx >= self.adx_strong_trend:
            if direction == 1:
                regime = RegimeType.STRONG_TREND_UP
            else:
                regime = RegimeType.STRONG_TREND_DOWN
        elif adx >= self.adx_trend_threshold:
            if direction == 1:
                regime = RegimeType.TREND_UP
            else:
                regime = RegimeType.TREND_DOWN
        elif adx < 20:
            # Check if ranging or choppy
            if len(closes) >= 20:
                recent_range = max(closes[-20:]) - min(closes[-20:])
                avg_range = np.mean(np.abs(np.diff(closes[-20:])))
                
                if recent_range < avg_range * 10:
                    regime = RegimeType.RANGING
                else:
                    regime = RegimeType.CHOPPY
            else:
                regime = RegimeType.RANGING
        else:
            regime = RegimeType.RANGING
        
        return regime, trend_strength, direction
    
    def _detect_momentum_regime(
        self,
        rsi: float,
        closes: np.ndarray
    ) -> Tuple[MomentumRegime, float]:
        """Detect momentum regime"""
        # Calculate momentum score (-1 to 1)
        momentum_score = (rsi - 50) / 50
        
        # Also check price momentum
        if len(closes) >= 20:
            price_momentum = (closes[-1] - closes[-20]) / closes[-20]
            momentum_score = (momentum_score + price_momentum * 10) / 2
        
        momentum_score = max(-1, min(1, momentum_score))
        
        # Classify
        if momentum_score > 0.6:
            regime = MomentumRegime.STRONG_BULLISH
        elif momentum_score > 0.2:
            regime = MomentumRegime.BULLISH
        elif momentum_score > -0.2:
            regime = MomentumRegime.NEUTRAL
        elif momentum_score > -0.6:
            regime = MomentumRegime.BEARISH
        else:
            regime = MomentumRegime.STRONG_BEARISH
        
        return regime, momentum_score
    
    def _get_recommendations(
        self,
        regime_type: RegimeType,
        volatility_regime: VolatilityRegime,
        momentum_regime: MomentumRegime,
        trend_strength: float
    ) -> Tuple[str, float, bool]:
        """Get trading recommendations based on regime"""
        # Strategy recommendations
        strategy_map = {
            RegimeType.STRONG_TREND_UP: ("trend_following", 1.2, False),
            RegimeType.TREND_UP: ("trend_following", 1.0, False),
            RegimeType.RANGING: ("mean_reversion", 0.8, False),
            RegimeType.TREND_DOWN: ("trend_following", 1.0, False),
            RegimeType.STRONG_TREND_DOWN: ("trend_following", 1.2, False),
            RegimeType.CHOPPY: ("avoid", 0.5, True),
            RegimeType.BREAKOUT: ("breakout", 1.0, False),
        }
        
        strategy, size_mult, avoid = strategy_map.get(
            regime_type, ("conservative", 0.5, False)
        )
        
        # Adjust for volatility
        if volatility_regime == VolatilityRegime.EXTREME:
            size_mult *= 0.5
            avoid = True
        elif volatility_regime == VolatilityRegime.HIGH:
            size_mult *= 0.7
        elif volatility_regime == VolatilityRegime.VERY_LOW:
            size_mult *= 0.8  # Low vol = small moves
        
        return strategy, size_mult, avoid
    
    def _calculate_confidence(
        self,
        adx: float,
        trend_strength: float,
        vol_percentile: float
    ) -> float:
        """Calculate regime detection confidence"""
        # Higher ADX = more confident in trend detection
        adx_confidence = min(1.0, adx / 40)
        
        # Extreme volatility = less confident
        if vol_percentile > 90 or vol_percentile < 10:
            vol_confidence = 0.6
        else:
            vol_confidence = 0.9
        
        return (adx_confidence + vol_confidence + trend_strength) / 3
    
    def get_strategy_for_regime(self, regime: MarketRegime) -> Dict[str, Any]:
        """Get detailed strategy parameters for the detected regime"""
        strategies = {
            RegimeType.STRONG_TREND_UP: {
                'entry': 'pullback_to_ema',
                'exit': 'trailing_stop',
                'stop_loss': 'atr_based',
                'take_profit': 'extended',
                'position_size': 'normal_to_large',
            },
            RegimeType.TREND_UP: {
                'entry': 'pullback_to_support',
                'exit': 'fixed_target',
                'stop_loss': 'swing_low',
                'take_profit': 'resistance',
                'position_size': 'normal',
            },
            RegimeType.RANGING: {
                'entry': 'support_resistance',
                'exit': 'opposite_boundary',
                'stop_loss': 'outside_range',
                'take_profit': 'range_target',
                'position_size': 'reduced',
            },
            RegimeType.CHOPPY: {
                'entry': 'avoid',
                'exit': 'quick',
                'stop_loss': 'tight',
                'take_profit': 'small',
                'position_size': 'minimal',
            },
        }
        
        return strategies.get(regime.regime_type, strategies[RegimeType.RANGING])
