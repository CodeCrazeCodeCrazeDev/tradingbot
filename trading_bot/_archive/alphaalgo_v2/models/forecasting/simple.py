"""
AlphaAlgo V2 Simple Forecaster

Simple price forecasting using statistical methods.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class Forecast:
    """Price forecast result"""
    direction: str  # "up", "down", "neutral"
    confidence: float
    predicted_change: float
    predicted_price: float
    horizon_bars: int
    method: str


class SimpleForecaster:
    """
    Simple statistical forecaster
    
    Methods:
    - Moving average trend
    - Momentum
    - Mean reversion
    - Ensemble of above
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._horizon = self.config.get("horizon_bars", 5)
    
    def forecast(
        self,
        df: pd.DataFrame,
        method: str = "ensemble"
    ) -> Forecast:
        """
        Generate price forecast
        
        Args:
            df: OHLCV DataFrame
            method: Forecasting method
            
        Returns:
            Forecast result
        """
        if df is None or len(df) < 30:
            return Forecast(
                direction="neutral",
                confidence=0.0,
                predicted_change=0.0,
                predicted_price=0.0,
                horizon_bars=self._horizon,
                method=method,
            )
        
        current_price = float(df['close'].iloc[-1])
        
        if method == "trend":
            return self._forecast_trend(df, current_price)
        elif method == "momentum":
            return self._forecast_momentum(df, current_price)
        elif method == "mean_reversion":
            return self._forecast_mean_reversion(df, current_price)
        else:
            return self._forecast_ensemble(df, current_price)
    
    def _forecast_trend(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Forecast:
        """Trend-based forecast using moving averages"""
        close = df['close']
        
        # Calculate trend
        fast_ma = close.rolling(10).mean().iloc[-1]
        slow_ma = close.rolling(20).mean().iloc[-1]
        
        # Trend strength
        trend_strength = abs(fast_ma - slow_ma) / slow_ma
        
        if fast_ma > slow_ma:
            direction = "up"
            predicted_change = trend_strength * self._horizon * 0.1
        else:
            direction = "down"
            predicted_change = -trend_strength * self._horizon * 0.1
        
        predicted_price = current_price * (1 + predicted_change)
        confidence = min(trend_strength * 10, 0.8)
        
        return Forecast(
            direction=direction,
            confidence=confidence,
            predicted_change=predicted_change,
            predicted_price=predicted_price,
            horizon_bars=self._horizon,
            method="trend",
        )
    
    def _forecast_momentum(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Forecast:
        """Momentum-based forecast"""
        close = df['close']
        
        # Calculate momentum
        returns = close.pct_change()
        momentum = returns.tail(10).mean()
        
        if momentum > 0:
            direction = "up"
        elif momentum < 0:
            direction = "down"
        else:
            direction = "neutral"
        
        predicted_change = momentum * self._horizon
        predicted_price = current_price * (1 + predicted_change)
        confidence = min(abs(momentum) * 50, 0.8)
        
        return Forecast(
            direction=direction,
            confidence=confidence,
            predicted_change=predicted_change,
            predicted_price=predicted_price,
            horizon_bars=self._horizon,
            method="momentum",
        )
    
    def _forecast_mean_reversion(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Forecast:
        """Mean reversion forecast"""
        close = df['close']
        
        # Calculate deviation from mean
        mean_price = close.rolling(20).mean().iloc[-1]
        std_price = close.rolling(20).std().iloc[-1]
        
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        # Expect reversion
        if z_score > 1:
            direction = "down"
            predicted_change = -abs(z_score) * 0.01 * self._horizon
        elif z_score < -1:
            direction = "up"
            predicted_change = abs(z_score) * 0.01 * self._horizon
        else:
            direction = "neutral"
            predicted_change = 0.0
        
        predicted_price = current_price * (1 + predicted_change)
        confidence = min(abs(z_score) * 0.3, 0.7)
        
        return Forecast(
            direction=direction,
            confidence=confidence,
            predicted_change=predicted_change,
            predicted_price=predicted_price,
            horizon_bars=self._horizon,
            method="mean_reversion",
        )
    
    def _forecast_ensemble(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Forecast:
        """Ensemble of all methods"""
        trend = self._forecast_trend(df, current_price)
        momentum = self._forecast_momentum(df, current_price)
        mean_rev = self._forecast_mean_reversion(df, current_price)
        
        # Weighted average
        weights = {
            "trend": 0.4,
            "momentum": 0.35,
            "mean_reversion": 0.25,
        }
        
        forecasts = [
            (trend, weights["trend"]),
            (momentum, weights["momentum"]),
            (mean_rev, weights["mean_reversion"]),
        ]
        
        # Aggregate
        total_change = sum(f.predicted_change * w for f, w in forecasts)
        total_confidence = sum(f.confidence * w for f, w in forecasts)
        
        if total_change > 0.001:
            direction = "up"
        elif total_change < -0.001:
            direction = "down"
        else:
            direction = "neutral"
        
        return Forecast(
            direction=direction,
            confidence=total_confidence,
            predicted_change=total_change,
            predicted_price=current_price * (1 + total_change),
            horizon_bars=self._horizon,
            method="ensemble",
        )
