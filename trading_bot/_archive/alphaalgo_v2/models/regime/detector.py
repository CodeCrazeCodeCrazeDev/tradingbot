"""
AlphaAlgo V2 Regime Detector

Detects market regime for adaptive trading.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum
import pandas as pd
import numpy as np

from ...core.constants import MarketRegime
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class RegimeAnalysis:
    """Regime analysis result"""
    regime: MarketRegime
    confidence: float
    volatility: float
    trend_strength: float
    metrics: Dict[str, float]


class RegimeDetector:
    """
    Market regime detector
    
    Detects:
    - Trending (up/down)
    - Ranging
    - Volatile
    - Quiet
    - Transitioning
    
    Uses:
    - ADX for trend strength
    - ATR for volatility
    - Hurst exponent for mean reversion
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self._adx_trend_threshold = self.config.get("adx_trend", 25)
        self._volatility_high = self.config.get("volatility_high", 1.5)
        self._volatility_low = self.config.get("volatility_low", 0.5)
        
        # Lookback periods
        self._adx_period = self.config.get("adx_period", 14)
        self._atr_period = self.config.get("atr_period", 14)
        self._volatility_period = self.config.get("volatility_period", 20)
    
    def detect(self, df: pd.DataFrame) -> RegimeAnalysis:
        """
        Detect current market regime
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            RegimeAnalysis with detected regime
        """
        if df is None or len(df) < self._adx_period + 5:
            return RegimeAnalysis(
                regime=MarketRegime.RANGING,
                confidence=0.5,
                volatility=1.0,
                trend_strength=0.0,
                metrics={},
            )
        
        # Calculate indicators
        adx = self._calculate_adx(df)
        atr = self._calculate_atr(df)
        volatility_ratio = self._calculate_volatility_ratio(df)
        trend_direction = self._get_trend_direction(df)
        
        # Determine regime
        regime, confidence = self._classify_regime(
            adx, volatility_ratio, trend_direction
        )
        
        return RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            volatility=volatility_ratio,
            trend_strength=adx / 100.0,
            metrics={
                "adx": adx,
                "atr": atr,
                "volatility_ratio": volatility_ratio,
                "trend_direction": 1 if trend_direction == "up" else -1,
            },
        )
    
    def _classify_regime(
        self,
        adx: float,
        volatility_ratio: float,
        trend_direction: str
    ) -> tuple[MarketRegime, float]:
        """Classify market regime"""
        # High volatility
        if volatility_ratio > self._volatility_high:
            return MarketRegime.VOLATILE, 0.8
        
        # Low volatility
        if volatility_ratio < self._volatility_low:
            return MarketRegime.QUIET, 0.8
        
        # Strong trend
        if adx > self._adx_trend_threshold:
            if trend_direction == "up":
                return MarketRegime.TRENDING_UP, min(adx / 50, 1.0)
            else:
                return MarketRegime.TRENDING_DOWN, min(adx / 50, 1.0)
        
        # Weak trend = ranging
        return MarketRegime.RANGING, 0.6
    
    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """Calculate ADX (Average Directional Index)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed values
        atr = tr.rolling(self._adx_period).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(self._adx_period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(self._adx_period).mean() / atr
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.rolling(self._adx_period).mean()
        
        return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 20.0
    
    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """Calculate ATR"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self._atr_period).mean().iloc[-1]
        
        return float(atr) if not pd.isna(atr) else 0.0
    
    def _calculate_volatility_ratio(self, df: pd.DataFrame) -> float:
        """Calculate volatility ratio (current vs historical)"""
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < self._volatility_period * 2:
            return 1.0
        
        current_vol = returns.tail(self._volatility_period).std()
        historical_vol = returns.std()
        
        if historical_vol == 0:
            return 1.0
        
        return current_vol / historical_vol
    
    def _get_trend_direction(self, df: pd.DataFrame) -> str:
        """Get trend direction using moving averages"""
        close = df['close']
        
        fast_ma = close.rolling(10).mean().iloc[-1]
        slow_ma = close.rolling(20).mean().iloc[-1]
        
        return "up" if fast_ma > slow_ma else "down"
    
    def get_regime_description(self, regime: MarketRegime) -> str:
        """Get human-readable regime description"""
        descriptions = {
            MarketRegime.TRENDING_UP: "Strong uptrend - trend following strategies",
            MarketRegime.TRENDING_DOWN: "Strong downtrend - trend following strategies",
            MarketRegime.RANGING: "Sideways market - mean reversion strategies",
            MarketRegime.VOLATILE: "High volatility - reduce position sizes",
            MarketRegime.QUIET: "Low volatility - breakout strategies",
            MarketRegime.TRANSITIONING: "Regime change - wait for confirmation",
        }
        return descriptions.get(regime, "Unknown regime")
