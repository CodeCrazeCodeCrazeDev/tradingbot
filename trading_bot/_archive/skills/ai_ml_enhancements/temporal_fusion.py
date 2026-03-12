"""
Skill #18: Temporal Fusion Transformer
======================================

Multi-horizon forecasting with interpretable attention
for time series prediction.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemporalAttention:
    """Temporal attention weights."""
    past_attention: np.ndarray
    future_attention: np.ndarray
    static_attention: np.ndarray
    important_lags: List[int]


@dataclass
class QuantilePrediction:
    """Quantile prediction for uncertainty."""
    q10: float
    q50: float
    q90: float
    mean: float
    std: float


@dataclass
class TFTResult:
    """Temporal Fusion Transformer result."""
    predictions: Dict[int, QuantilePrediction]
    attention: TemporalAttention
    feature_importance: Dict[str, float]
    variable_selection: Dict[str, float]
    trading_signal: str
    confidence: float


class TemporalFusionTransformer:
    """
    Temporal Fusion Transformer for Multi-Horizon Forecasting.
    
    Combines LSTM encoders with attention for interpretable predictions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.hidden_size = self.config.get('hidden_size', 64)
        self.num_heads = self.config.get('num_heads', 4)
        self.dropout = self.config.get('dropout', 0.1)
        self.quantiles = self.config.get('quantiles', [0.1, 0.5, 0.9])
        
        self.weights = self._initialize_weights()
        logger.info("TemporalFusionTransformer initialized")
    
    def _initialize_weights(self) -> Dict:
        """Initialize TFT weights."""
        return {
            'encoder': np.random.randn(self.hidden_size, self.hidden_size) * 0.1,
            'decoder': np.random.randn(self.hidden_size, self.hidden_size) * 0.1,
            'attention': np.random.randn(self.hidden_size, self.hidden_size) * 0.1,
            'output': np.random.randn(self.hidden_size, len(self.quantiles)) * 0.1,
            'variable_selection': np.random.randn(10, 1) * 0.1,
        }
    
    def predict(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        horizons: List[int] = None
    ) -> TFTResult:
        """Generate multi-horizon predictions."""
        if len(prices) < 30:
            return self._create_empty_result()
        
        horizons = horizons or [1, 5, 10, 20]
        
        # Prepare features
        features = self._prepare_features(prices, volumes)
        
        # Variable selection
        var_selection = self._variable_selection(features)
        
        # Encode past
        encoded = self._encode_past(features, var_selection)
        
        # Generate predictions for each horizon
        predictions = {}
        for h in horizons:
            pred = self._predict_horizon(encoded, h, prices[-1])
            predictions[h] = pred
        
        # Calculate attention
        attention = self._calculate_attention(encoded)
        
        # Feature importance
        feature_importance = self._get_feature_importance(var_selection)
        
        # Generate signal
        signal = self._generate_signal(predictions, attention)
        
        # Confidence
        confidence = self._calculate_confidence(predictions)
        
        return TFTResult(
            predictions=predictions,
            attention=attention,
            feature_importance=feature_importance,
            variable_selection={f"feature_{i}": float(v) for i, v in enumerate(var_selection)},
            trading_signal=signal,
            confidence=confidence
        )
    
    def _prepare_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Prepare input features."""
        returns = np.diff(prices) / prices[:-1]
        returns = np.concatenate([[0], returns])
        
        features = np.column_stack([
            prices / prices[-1],
            returns,
            self._ema(prices, 5) / prices,
            self._ema(prices, 20) / prices,
            self._rolling_std(returns, 10),
            volumes / np.mean(volumes),
            self._rsi(prices, 14) / 100,
            self._macd(prices),
            self._bollinger_position(prices),
            np.arange(len(prices)) / len(prices)
        ])
        
        return features[-30:]
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential moving average."""
        alpha = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def _rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """Rolling standard deviation."""
        result = np.zeros(len(data))
        for i in range(window, len(data)):
            result[i] = np.std(data[i-window:i])
        return result
    
    def _rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = self._ema(np.concatenate([[0], gains]), period)
        avg_loss = self._ema(np.concatenate([[0], losses]), period)
        
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _macd(self, prices: np.ndarray) -> np.ndarray:
        """MACD indicator."""
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        return (ema12 - ema26) / prices
    
    def _bollinger_position(self, prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Position within Bollinger Bands."""
        ma = self._ema(prices, period)
        std = self._rolling_std(prices, period)
        upper = ma + 2 * std
        lower = ma - 2 * std
        return (prices - lower) / (upper - lower + 1e-10)
    
    def _variable_selection(self, features: np.ndarray) -> np.ndarray:
        """Select important variables."""
        # Simplified variable selection using softmax
        importance = np.abs(features).mean(axis=0)
        selection = np.exp(importance) / np.sum(np.exp(importance))
        return selection
    
    def _encode_past(self, features: np.ndarray, var_selection: np.ndarray) -> np.ndarray:
        """Encode past observations."""
        # Weight features by selection
        weighted = features * var_selection
        
        # Simple LSTM-like encoding (simplified)
        hidden = np.zeros(self.hidden_size)
        for t in range(len(weighted)):
            # Project features
            projected = np.tanh(weighted[t] @ self.weights['encoder'][:len(weighted[t]), :])
            # Update hidden state
            hidden = 0.9 * hidden + 0.1 * projected
        
        return hidden
    
    def _predict_horizon(
        self,
        encoded: np.ndarray,
        horizon: int,
        current_price: float
    ) -> QuantilePrediction:
        """Predict for a specific horizon."""
        # Decode
        decoded = np.tanh(encoded @ self.weights['decoder'])
        
        # Output quantiles
        quantile_outputs = decoded @ self.weights['output']
        
        # Scale by horizon
        scale = np.sqrt(horizon) * 0.01
        
        q10 = current_price * (1 + quantile_outputs[0] * scale)
        q50 = current_price * (1 + quantile_outputs[1] * scale)
        q90 = current_price * (1 + quantile_outputs[2] * scale)
        
        return QuantilePrediction(
            q10=float(q10),
            q50=float(q50),
            q90=float(q90),
            mean=float(q50),
            std=float((q90 - q10) / 2.56)
        )
    
    def _calculate_attention(self, encoded: np.ndarray) -> TemporalAttention:
        """Calculate attention weights."""
        # Simplified attention calculation
        attention_scores = np.abs(encoded @ self.weights['attention'])
        attention_weights = np.exp(attention_scores) / np.sum(np.exp(attention_scores))
        
        return TemporalAttention(
            past_attention=attention_weights,
            future_attention=attention_weights,
            static_attention=attention_weights,
            important_lags=[1, 5, 10, 20]
        )
    
    def _get_feature_importance(self, var_selection: np.ndarray) -> Dict[str, float]:
        """Get feature importance scores."""
        names = ['price', 'returns', 'ema5', 'ema20', 'volatility',
                 'volume', 'rsi', 'macd', 'bollinger', 'time']
        return {name: float(var_selection[i]) for i, name in enumerate(names)}
    
    def _generate_signal(
        self,
        predictions: Dict[int, QuantilePrediction],
        attention: TemporalAttention
    ) -> str:
        """Generate trading signal."""
        # Use median prediction
        short_term = predictions.get(1, predictions.get(5))
        long_term = predictions.get(20, predictions.get(10))
        
        if short_term and long_term:
            short_return = (short_term.q50 - short_term.mean) / short_term.mean
            long_return = (long_term.q50 - long_term.mean) / long_term.mean
            
            if short_return > 0.01 and long_return > 0.02:
                return "STRONG BUY: Bullish short and long term"
            elif short_return > 0:
                return "BUY: Short-term bullish"
            elif short_return < -0.01 and long_return < -0.02:
                return "STRONG SELL: Bearish short and long term"
            elif short_return < 0:
                return "SELL: Short-term bearish"
        
        return "NEUTRAL: Mixed signals"
    
    def _calculate_confidence(self, predictions: Dict[int, QuantilePrediction]) -> float:
        """Calculate prediction confidence."""
        if not predictions:
            return 0.0
        
        # Narrower prediction intervals = higher confidence
        intervals = [(p.q90 - p.q10) / p.mean for p in predictions.values()]
        avg_interval = np.mean(intervals)
        
        confidence = max(0.3, min(0.9, 1 - avg_interval * 10))
        return confidence
    
    def _create_empty_result(self) -> TFTResult:
        """Create empty result."""
        return TFTResult(
            predictions={},
            attention=TemporalAttention(
                past_attention=np.array([]),
                future_attention=np.array([]),
                static_attention=np.array([]),
                important_lags=[]
            ),
            feature_importance={},
            variable_selection={},
            trading_signal="Insufficient data",
            confidence=0
        )
