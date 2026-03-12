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
        try:
            self.config = config or {}
            self.hidden_size = self.config.get('hidden_size', 64)
            self.num_heads = self.config.get('num_heads', 4)
            self.dropout = self.config.get('dropout', 0.1)
            self.quantiles = self.config.get('quantiles', [0.1, 0.5, 0.9])
        
            self.weights = self._initialize_weights()
            logger.info("TemporalFusionTransformer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
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
        try:
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
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def _prepare_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Prepare input features."""
        try:
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
        except Exception as e:
            logger.error(f"Error in _prepare_features: {e}")
            raise
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential moving average."""
        try:
            alpha = 2 / (period + 1)
            ema = np.zeros(len(data))
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema
        except Exception as e:
            logger.error(f"Error in _ema: {e}")
            raise
    
    def _rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """Rolling standard deviation."""
        try:
            result = np.zeros(len(data))
            for i in range(window, len(data)):
                result[i] = np.std(data[i-window:i])
            return result
        except Exception as e:
            logger.error(f"Error in _rolling_std: {e}")
            raise
    
    def _rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index."""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
        
            avg_gain = self._ema(np.concatenate([[0], gains]), period)
            avg_loss = self._ema(np.concatenate([[0], losses]), period)
        
            rs = avg_gain / (avg_loss + 1e-10)
            return 100 - (100 / (1 + rs))
        except Exception as e:
            logger.error(f"Error in _rsi: {e}")
            raise
    
    def _macd(self, prices: np.ndarray) -> np.ndarray:
        """MACD indicator."""
        try:
            ema12 = self._ema(prices, 12)
            ema26 = self._ema(prices, 26)
            return (ema12 - ema26) / prices
        except Exception as e:
            logger.error(f"Error in _macd: {e}")
            raise
    
    def _bollinger_position(self, prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Position within Bollinger Bands."""
        try:
            ma = self._ema(prices, period)
            std = self._rolling_std(prices, period)
            upper = ma + 2 * std
            lower = ma - 2 * std
            return (prices - lower) / (upper - lower + 1e-10)
        except Exception as e:
            logger.error(f"Error in _bollinger_position: {e}")
            raise
    
    def _variable_selection(self, features: np.ndarray) -> np.ndarray:
        """Select important variables."""
        # Simplified variable selection using softmax
        try:
            importance = np.abs(features).mean(axis=0)
            selection = np.exp(importance) / np.sum(np.exp(importance))
            return selection
        except Exception as e:
            logger.error(f"Error in _variable_selection: {e}")
            raise
    
    def _encode_past(self, features: np.ndarray, var_selection: np.ndarray) -> np.ndarray:
        """Encode past observations."""
        # Weight features by selection
        try:
            weighted = features * var_selection
        
            # Simple LSTM-like encoding (simplified)
            hidden = np.zeros(self.hidden_size)
            for t in range(len(weighted)):
                # Project features
                projected = np.tanh(weighted[t] @ self.weights['encoder'][:len(weighted[t]), :])
                # Update hidden state
                hidden = 0.9 * hidden + 0.1 * projected
        
            return hidden
        except Exception as e:
            logger.error(f"Error in _encode_past: {e}")
            raise
    
    def _predict_horizon(
        self,
        encoded: np.ndarray,
        horizon: int,
        current_price: float
    ) -> QuantilePrediction:
        """Predict for a specific horizon."""
        # Decode
        try:
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
        except Exception as e:
            logger.error(f"Error in _predict_horizon: {e}")
            raise
    
    def _calculate_attention(self, encoded: np.ndarray) -> TemporalAttention:
        """Calculate attention weights."""
        # Simplified attention calculation
        try:
            attention_scores = np.abs(encoded @ self.weights['attention'])
            attention_weights = np.exp(attention_scores) / np.sum(np.exp(attention_scores))
        
            return TemporalAttention(
                past_attention=attention_weights,
                future_attention=attention_weights,
                static_attention=attention_weights,
                important_lags=[1, 5, 10, 20]
            )
        except Exception as e:
            logger.error(f"Error in _calculate_attention: {e}")
            raise
    
    def _get_feature_importance(self, var_selection: np.ndarray) -> Dict[str, float]:
        """Get feature importance scores."""
        try:
            names = ['price', 'returns', 'ema5', 'ema20', 'volatility',
                     'volume', 'rsi', 'macd', 'bollinger', 'time']
            return {name: float(var_selection[i]) for i, name in enumerate(names)}
        except Exception as e:
            logger.error(f"Error in _get_feature_importance: {e}")
            raise
    
    def _generate_signal(
        self,
        predictions: Dict[int, QuantilePrediction],
        attention: TemporalAttention
    ) -> str:
        """Generate trading signal."""
        # Use median prediction
        try:
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
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _calculate_confidence(self, predictions: Dict[int, QuantilePrediction]) -> float:
        """Calculate prediction confidence."""
        try:
            if not predictions:
                return 0.0
        
            # Narrower prediction intervals = higher confidence
            intervals = [(p.q90 - p.q10) / p.mean for p in predictions.values()]
            avg_interval = np.mean(intervals)
        
            confidence = max(0.3, min(0.9, 1 - avg_interval * 10))
            return confidence
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
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
