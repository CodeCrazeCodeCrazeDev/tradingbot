import asyncio
import logging
logger = logging.getLogger(__name__)
"""Market Regime Detection System.

This module implements a sophisticated market regime detection system that
identifies different market conditions and adapts trading strategies accordingly.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from loguru import logger
try:
    import talib
    TALIB_AVAILABLE = True
except Exception:
    TALIB_AVAILABLE = False
    talib = None
    logger.warning("TA-Lib not available - using fallback indicators for MarketRegimeDetector")


class MarketRegime(Enum):
    """Market regime types."""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CRISIS = "crisis"
    SIDEWAYS = "sideways"  # Alias for RANGING


@dataclass
class RegimeSignal:
    """Market regime signal with confidence and metadata."""
    regime: MarketRegime
    confidence: float
    strength: float
    duration: int  # bars in current regime
    indicators: Dict[str, float]
    timestamp: datetime


class MarketRegimeDetector:
    """Advanced market regime detection system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the market regime detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.lookback_period = self.config.get('lookback_period', 100)
        self.volatility_window = self.config.get('volatility_window', 20)
        self.trend_window = self.config.get('trend_window', 50)
        
        # Regime thresholds
        self.thresholds = {
            'trend_strength': 0.6,
            'volatility_high': 2.0,
            'volatility_low': 0.5,
            'ranging_threshold': 0.3,
            'breakout_threshold': 1.5,
            'crisis_threshold': 3.0
        }
        
        self.current_regime = None
        self.regime_history = []
        self.regime_start_time = None
        
        logger.info("MarketRegimeDetector initialized")
    
    async def detect_regime_async(self, data: pd.DataFrame) -> RegimeSignal:
        """Async version of detect_regime."""
        return self.detect_regime(data)

    def detect_regime(self, data: pd.DataFrame) -> RegimeSignal:
        """Detect current market regime from price data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            RegimeSignal with detected regime and metadata
        """
        if len(data) < self.lookback_period:
            logger.warning("Insufficient data for regime detection")
            return self._default_regime()
        
        # Calculate technical indicators
        indicators = self._calculate_indicators(data)
        
        # Detect regime using multiple methods
        regime_scores = self._score_regimes(indicators, data)
        
        # Select regime with highest confidence
        best_regime = max(regime_scores.items(), key=lambda x: x[1]['confidence'])
        regime_type, regime_data = best_regime
        
        # Calculate regime duration
        duration = self._calculate_regime_duration(regime_type)
        
        # Create regime signal
        signal = RegimeSignal(
            regime=regime_type,
            confidence=regime_data['confidence'],
            strength=regime_data['strength'],
            duration=duration,
            indicators=indicators,
            timestamp=datetime.now()
        )
        
        # Update regime tracking
        self._update_regime_tracking(signal)
        
        logger.info(f"Detected regime: {regime_type.value} (confidence: {signal.confidence:.2f})")
        return signal
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators for regime detection."""
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        volume = data['volume'].values if 'volume' in data.columns else None
        
        indicators = {}
        
        if TALIB_AVAILABLE:
            # Trend indicators
            sma_20 = talib.SMA(close, timeperiod=20)
            sma_50 = talib.SMA(close, timeperiod=50)
            ema_12 = talib.EMA(close, timeperiod=12)
            ema_26 = talib.EMA(close, timeperiod=26)
            
            # Volatility indicators
            atr = talib.ATR(high, low, close, timeperiod=14)
            
            # Momentum indicators
            rsi = talib.RSI(close, timeperiod=14)
            macd, macd_signal, macd_hist = talib.MACD(close)
            
            # Range indicators
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
            
            # Volume indicators (if available)
            if volume is not None:
                volume_sma = talib.SMA(volume, timeperiod=20)
            else:
                volume_sma = None
        else:
            # Fallback implementations with pandas/numpy
            close_series = pd.Series(close)
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            
            # Trend indicators (SMA/EMA)
            sma_20 = close_series.rolling(20).mean().values
            sma_50 = close_series.rolling(50).mean().values
            ema_12 = close_series.ewm(span=12, adjust=False).mean().values
            ema_26 = close_series.ewm(span=26, adjust=False).mean().values
            
            # ATR (True Range average)
            prev_close = close_series.shift(1)
            tr = pd.concat([
                (high_series - low_series).abs(),
                (high_series - prev_close).abs(),
                (low_series - prev_close).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().values
            
            # RSI
            delta = close_series.diff()
            gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).values
            
            # MACD
            macd_line = close_series.ewm(span=12, adjust=False).mean() - close_series.ewm(span=26, adjust=False).mean()
            macd_signal_series = macd_line.ewm(span=9, adjust=False).mean()
            macd = macd_line.values
            macd_signal = macd_signal_series.values
            macd_hist = (macd_line - macd_signal_series).values
            
            # Bollinger Bands
            bb_middle_series = close_series.rolling(20).mean()
            bb_std = close_series.rolling(20).std()
            bb_upper = (bb_middle_series + 2 * bb_std).values
            bb_lower = (bb_middle_series - 2 * bb_std).values
            bb_middle = bb_middle_series.values
            
            # Volume SMA
            if volume is not None:
                volume_series = pd.Series(volume)
                volume_sma = volume_series.rolling(20).mean().values
            else:
                volume_sma = None
        
        # Trend strength and ratios
        last_20 = sma_20[-20:]
        valid = last_20[~np.isnan(last_20)] if isinstance(last_20, np.ndarray) else last_20
        if len(valid) >= 2:
            trend_slope = np.polyfit(range(len(valid)), valid, 1)[0]
        else:
            trend_slope = 0.0
        indicators['trend_slope'] = trend_slope
        indicators['sma_ratio'] = (sma_20[-1] / sma_50[-1]) if (len(sma_50) > 0 and not np.isnan(sma_50[-1])) else 1.0
        
        # Volatility
        indicators['atr'] = (atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else 0.0)
        indicators['volatility'] = (np.std(close[-20:]) / np.mean(close[-20:])) if np.mean(close[-20:]) != 0 else 0.0
        
        # Momentum
        indicators['rsi'] = (rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else 50.0)
        indicators['macd_hist'] = (macd_hist[-1] if len(macd_hist) > 0 and not np.isnan(macd_hist[-1]) else 0.0)
        
        # Range indicators
        bb_mid_last = (bb_middle[-1] if isinstance(bb_middle, np.ndarray) else (bb_middle if isinstance(bb_middle, float) else np.nan))
        if not np.isnan(bb_mid_last):
            bb_width = (bb_upper[-1] - bb_lower[-1]) / bb_mid_last
        else:
            bb_width = 0.0
        indicators['bb_width'] = bb_width
        
        # Price position in range
        denom = (bb_upper[-1] - bb_lower[-1])
        price_position = (close[-1] - bb_lower[-1]) / denom if denom and denom > 0 else 0.5
        indicators['price_position'] = price_position
        
        # Volume indicators (if available)
        if volume is not None and volume_sma is not None and len(volume_sma) > 0 and not np.isnan(volume_sma[-1]):
            indicators['volume_ratio'] = volume[-1] / volume_sma[-1]
        else:
            indicators['volume_ratio'] = 1.0
        
        return indicators
    
    def _score_regimes(self, indicators: Dict[str, float], data: pd.DataFrame) -> Dict[MarketRegime, Dict[str, float]]:
        """Score different market regimes based on indicators."""
        scores = {}
        
        # Trending Bull
        bull_score = 0.0
        if indicators['trend_slope'] > 0:
            bull_score += 0.3
        if indicators['sma_ratio'] > 1.02:
            bull_score += 0.3
        if indicators['rsi'] > 50:
            bull_score += 0.2
        if indicators['macd_hist'] > 0:
            bull_score += 0.2
        
        scores[MarketRegime.TRENDING_BULL] = {
            'confidence': min(bull_score, 1.0),
            'strength': abs(indicators['trend_slope']) * 1000
        }
        
        # Trending Bear
        bear_score = 0.0
        if indicators['trend_slope'] < 0:
            bear_score += 0.3
        if indicators['sma_ratio'] < 0.98:
            bear_score += 0.3
        if indicators['rsi'] < 50:
            bear_score += 0.2
        if indicators['macd_hist'] < 0:
            bear_score += 0.2
        
        scores[MarketRegime.TRENDING_BEAR] = {
            'confidence': min(bear_score, 1.0),
            'strength': abs(indicators['trend_slope']) * 1000
        }
        
        # Ranging
        ranging_score = 0.0
        if abs(indicators['trend_slope']) < 0.0001:
            ranging_score += 0.4
        if 0.98 <= indicators['sma_ratio'] <= 1.02:
            ranging_score += 0.3
        if indicators['bb_width'] < 0.05:
            ranging_score += 0.3
        
        scores[MarketRegime.RANGING] = {
            'confidence': min(ranging_score, 1.0),
            'strength': 1.0 - abs(indicators['trend_slope']) * 1000
        }
        
        # High Volatility
        high_vol_score = 0.0
        if indicators['volatility'] > self.thresholds['volatility_high'] * 0.01:
            high_vol_score += 0.5
        if indicators['atr'] > np.mean(data['close'].values[-20:]) * 0.02:
            high_vol_score += 0.3
        if indicators['volume_ratio'] > 1.5:
            high_vol_score += 0.2
        
        scores[MarketRegime.HIGH_VOLATILITY] = {
            'confidence': min(high_vol_score, 1.0),
            'strength': indicators['volatility'] * 100
        }
        
        # Low Volatility
        low_vol_score = 0.0
        if indicators['volatility'] < self.thresholds['volatility_low'] * 0.01:
            low_vol_score += 0.5
        if indicators['bb_width'] < 0.03:
            low_vol_score += 0.3
        if indicators['volume_ratio'] < 0.8:
            low_vol_score += 0.2
        
        scores[MarketRegime.LOW_VOLATILITY] = {
            'confidence': min(low_vol_score, 1.0),
            'strength': 1.0 / (indicators['volatility'] * 100 + 0.01)
        }
        
        # Breakout
        breakout_score = 0.0
        if indicators['price_position'] > 0.9 or indicators['price_position'] < 0.1:
            breakout_score += 0.4
        if indicators['volume_ratio'] > 1.5:
            breakout_score += 0.3
        if indicators['volatility'] > 0.015:
            breakout_score += 0.3
        
        scores[MarketRegime.BREAKOUT] = {
            'confidence': min(breakout_score, 1.0),
            'strength': indicators['volume_ratio']
        }
        
        # Crisis (extreme conditions)
        crisis_score = 0.0
        if indicators['volatility'] > 0.05:
            crisis_score += 0.5
        if indicators['rsi'] < 20 or indicators['rsi'] > 80:
            crisis_score += 0.3
        if indicators['volume_ratio'] > 3.0:
            crisis_score += 0.2
        
        scores[MarketRegime.CRISIS] = {
            'confidence': min(crisis_score, 1.0),
            'strength': indicators['volatility'] * 100
        }
        
        return scores
    
    def _calculate_regime_duration(self, regime: MarketRegime) -> int:
        """Calculate how long the current regime has been active."""
        if self.current_regime != regime:
            self.regime_start_time = datetime.now()
            return 1
        
        if self.regime_start_time:
            duration = (datetime.now() - self.regime_start_time).total_seconds() / 60  # minutes
            return int(duration)
        
        return 1
    
    def _update_regime_tracking(self, signal: RegimeSignal):
        """Update regime tracking history."""
        self.current_regime = signal.regime
        self.regime_history.append(signal)
        
        # Keep only recent history
        if len(self.regime_history) > 1000:
            self.regime_history = self.regime_history[-500:]
    
    def _default_regime(self) -> RegimeSignal:
        """Return default regime when detection fails."""
        return RegimeSignal(
            regime=MarketRegime.RANGING,
            confidence=0.5,
            strength=0.5,
            duration=1,
            indicators={},
            timestamp=datetime.now()
        )
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """Get statistics about regime history."""
        if not self.regime_history:
            return {}
        
        regime_counts = {}
        for signal in self.regime_history[-100:]:  # Last 100 signals
            regime = signal.regime.value
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        total = len(self.regime_history[-100:])
        regime_percentages = {k: (v / total) * 100 for k, v in regime_counts.items()}
        
        return {
            'current_regime': self.current_regime.value if self.current_regime else None,
            'regime_duration': self.regime_history[-1].duration if self.regime_history else 0,
            'regime_distribution': regime_percentages,
            'average_confidence': np.mean([s.confidence for s in self.regime_history[-50:]]) if self.regime_history else 0
        }
