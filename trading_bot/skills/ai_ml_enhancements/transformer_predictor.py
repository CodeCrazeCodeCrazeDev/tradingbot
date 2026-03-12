"""
Skill #16: Transformer Price Predictor
======================================

Attention-based deep learning model for price forecasting
using transformer architecture.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PredictionHorizon(Enum):
    """Prediction time horizon."""
    TICK = "tick"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"


class PredictionType(Enum):
    """Type of prediction."""
    DIRECTION = "direction"
    MAGNITUDE = "magnitude"
    VOLATILITY = "volatility"
    REGIME = "regime"


@dataclass
class AttentionWeights:
    """Attention weights from transformer."""
    temporal_attention: np.ndarray
    feature_attention: np.ndarray
    cross_attention: np.ndarray
    important_timesteps: List[int]
    important_features: List[str]


@dataclass
class PricePrediction:
    """Single price prediction."""
    timestamp: datetime
    horizon: PredictionHorizon
    predicted_price: float
    predicted_direction: str
    confidence: float
    prediction_interval: Tuple[float, float]
    attention_weights: Optional[AttentionWeights]


@dataclass
class TransformerPredictionResult:
    """Complete transformer prediction result."""
    predictions: List[PricePrediction]
    ensemble_prediction: float
    ensemble_direction: str
    ensemble_confidence: float
    feature_importance: Dict[str, float]
    model_uncertainty: float
    trading_signal: str


class TransformerPricePredictor:
    """
    Advanced Transformer-based Price Prediction System.
    
    Uses self-attention mechanisms for time series forecasting.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.sequence_length = self.config.get('sequence_length', 60)
            self.num_heads = self.config.get('num_heads', 8)
            self.d_model = self.config.get('d_model', 64)
            self.num_layers = self.config.get('num_layers', 4)
            self.dropout = self.config.get('dropout', 0.1)
        
            # Model weights (simplified - in production would use PyTorch/TensorFlow)
            self.weights = self._initialize_weights()
            self.is_trained = False
        
            logger.info("TransformerPricePredictor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_weights(self) -> Dict:
        """Initialize transformer weights."""
        return {
            'query': np.random.randn(self.d_model, self.d_model) * 0.1,
            'key': np.random.randn(self.d_model, self.d_model) * 0.1,
            'value': np.random.randn(self.d_model, self.d_model) * 0.1,
            'output': np.random.randn(self.d_model, 1) * 0.1,
            'embedding': np.random.randn(10, self.d_model) * 0.1,  # 10 features
        }
    
    def predict(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        horizons: List[PredictionHorizon] = None
    ) -> TransformerPredictionResult:
        """
        Generate price predictions.
        
        Args:
            prices: Historical prices
            volumes: Historical volumes
            timestamps: Timestamps
            horizons: Prediction horizons
            
        Returns:
            TransformerPredictionResult with predictions
        """
        try:
            if len(prices) < self.sequence_length:
                return self._create_empty_result()
        
            horizons = horizons or [PredictionHorizon.HOUR, PredictionHorizon.DAY]
        
            # Prepare features
            features = self._prepare_features(prices, volumes)
        
            # Generate predictions for each horizon
            predictions = []
            for horizon in horizons:
                pred = self._predict_horizon(features, prices, timestamps, horizon)
                predictions.append(pred)
        
            # Ensemble prediction
            ensemble_price = np.mean([p.predicted_price for p in predictions])
        
            # Ensemble direction
            up_votes = sum(1 for p in predictions if p.predicted_direction == 'up')
            ensemble_direction = 'up' if up_votes > len(predictions) / 2 else 'down'
        
            # Ensemble confidence
            ensemble_confidence = np.mean([p.confidence for p in predictions])
        
            # Feature importance from attention
            feature_importance = self._calculate_feature_importance(features)
        
            # Model uncertainty
            uncertainty = self._calculate_uncertainty(predictions)
        
            # Trading signal
            signal = self._generate_signal(
                ensemble_direction, ensemble_confidence, uncertainty
            )
        
            return TransformerPredictionResult(
                predictions=predictions,
                ensemble_prediction=ensemble_price,
                ensemble_direction=ensemble_direction,
                ensemble_confidence=ensemble_confidence,
                feature_importance=feature_importance,
                model_uncertainty=uncertainty,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def _prepare_features(
        self,
        prices: np.ndarray,
        volumes: np.ndarray
    ) -> np.ndarray:
        """Prepare input features for transformer."""
        try:
            n = len(prices)
        
            # Calculate various features
            returns = np.diff(prices) / prices[:-1]
            returns = np.concatenate([[0], returns])
        
            # Moving averages
            ma_5 = self._moving_average(prices, 5)
            ma_20 = self._moving_average(prices, 20)
        
            # Volatility
            volatility = self._rolling_std(returns, 20)
        
            # Volume features
            vol_ma = self._moving_average(volumes, 20)
            vol_ratio = volumes / (vol_ma + 1e-10)
        
            # RSI
            rsi = self._calculate_rsi(prices, 14)
        
            # MACD
            macd, signal = self._calculate_macd(prices)
        
            # Combine features
            features = np.column_stack([
                prices / prices[-1],  # Normalized price
                returns,
                ma_5 / prices,
                ma_20 / prices,
                volatility,
                vol_ratio,
                rsi / 100,
                macd,
                signal,
                (prices - ma_20) / (ma_20 + 1e-10)  # Distance from MA
            ])
        
            return features[-self.sequence_length:]
        except Exception as e:
            logger.error(f"Error in _prepare_features: {e}")
            raise
    
    def _moving_average(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate moving average."""
        try:
            ma = np.convolve(data, np.ones(window)/window, mode='same')
            return ma
        except Exception as e:
            logger.error(f"Error in _moving_average: {e}")
            raise
    
    def _rolling_std(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling standard deviation."""
        try:
            result = np.zeros(len(data))
            for i in range(window, len(data)):
                result[i] = np.std(data[i-window:i])
            return result
        except Exception as e:
            logger.error(f"Error in _rolling_std: {e}")
            raise
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI."""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
        
            avg_gain = self._moving_average(gains, period)
            avg_loss = self._moving_average(losses, period)
        
            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
        
            return np.concatenate([[50], rsi])
        except Exception as e:
            logger.error(f"Error in _calculate_rsi: {e}")
            raise
    
    def _calculate_macd(
        self,
        prices: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate MACD."""
        try:
            ema_fast = self._ema(prices, fast)
            ema_slow = self._ema(prices, slow)
        
            macd_line = ema_fast - ema_slow
            signal_line = self._ema(macd_line, signal)
        
            return macd_line, signal_line
        except Exception as e:
            logger.error(f"Error in _calculate_macd: {e}")
            raise
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate exponential moving average."""
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
    
    def _predict_horizon(
        self,
        features: np.ndarray,
        prices: np.ndarray,
        timestamps: List[datetime],
        horizon: PredictionHorizon
    ) -> PricePrediction:
        """Generate prediction for a specific horizon."""
        try:
            current_price = prices[-1]
        
            # Apply transformer layers (simplified)
            attention_output, attention_weights = self._transformer_forward(features)
        
            # Predict return
            predicted_return = self._predict_return(attention_output, horizon)
        
            # Convert to price
            predicted_price = current_price * (1 + predicted_return)
        
            # Direction
            direction = 'up' if predicted_return > 0 else 'down'
        
            # Confidence based on attention concentration
            confidence = self._calculate_prediction_confidence(attention_weights)
        
            # Prediction interval
            volatility = np.std(np.diff(prices[-20:]) / prices[-21:-1])
            interval_width = volatility * self._get_horizon_multiplier(horizon) * 2
            interval = (
                predicted_price * (1 - interval_width),
                predicted_price * (1 + interval_width)
            )
        
            return PricePrediction(
                timestamp=timestamps[-1],
                horizon=horizon,
                predicted_price=predicted_price,
                predicted_direction=direction,
                confidence=confidence,
                prediction_interval=interval,
                attention_weights=attention_weights
            )
        except Exception as e:
            logger.error(f"Error in _predict_horizon: {e}")
            raise
    
    def _transformer_forward(
        self,
        features: np.ndarray
    ) -> Tuple[np.ndarray, AttentionWeights]:
        """Forward pass through transformer (simplified)."""
        # Embed features
        try:
            embedded = features @ self.weights['embedding'].T[:features.shape[1], :]
        
            # Self-attention (simplified)
            Q = embedded @ self.weights['query']
            K = embedded @ self.weights['key']
            V = embedded @ self.weights['value']
        
            # Attention scores
            scores = Q @ K.T / np.sqrt(self.d_model)
            attention = self._softmax(scores)
        
            # Apply attention
            output = attention @ V
        
            # Create attention weights object
            attention_weights = AttentionWeights(
                temporal_attention=attention,
                feature_attention=np.mean(np.abs(self.weights['embedding']), axis=1),
                cross_attention=attention,
                important_timesteps=list(np.argsort(np.sum(attention, axis=0))[-5:]),
                important_features=['price', 'returns', 'ma_5', 'ma_20', 'volatility']
            )
        
            return output, attention_weights
        except Exception as e:
            logger.error(f"Error in _transformer_forward: {e}")
            raise
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        try:
            exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
            return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
        except Exception as e:
            logger.error(f"Error in _softmax: {e}")
            raise
    
    def _predict_return(
        self,
        attention_output: np.ndarray,
        horizon: PredictionHorizon
    ) -> float:
        """Predict return from attention output."""
        # Aggregate output
        try:
            aggregated = np.mean(attention_output, axis=0)
        
            # Project to return
            raw_prediction = aggregated @ self.weights['output']
        
            # Scale by horizon
            multiplier = self._get_horizon_multiplier(horizon)
        
            # Clip to reasonable range
            predicted_return = np.clip(raw_prediction[0] * multiplier, -0.1, 0.1)
        
            return predicted_return
        except Exception as e:
            logger.error(f"Error in _predict_return: {e}")
            raise
    
    def _get_horizon_multiplier(self, horizon: PredictionHorizon) -> float:
        """Get multiplier for prediction horizon."""
        try:
            multipliers = {
                PredictionHorizon.TICK: 0.001,
                PredictionHorizon.MINUTE: 0.005,
                PredictionHorizon.HOUR: 0.02,
                PredictionHorizon.DAY: 0.05,
                PredictionHorizon.WEEK: 0.1,
            }
            return multipliers.get(horizon, 0.02)
        except Exception as e:
            logger.error(f"Error in _get_horizon_multiplier: {e}")
            raise
    
    def _calculate_prediction_confidence(
        self,
        attention_weights: AttentionWeights
    ) -> float:
        """Calculate confidence from attention weights."""
        # Higher concentration = higher confidence
        try:
            temporal = attention_weights.temporal_attention
        
            # Entropy of attention (lower = more concentrated = higher confidence)
            entropy = -np.sum(temporal * np.log(temporal + 1e-10)) / np.log(temporal.shape[0])
        
            confidence = 1 - entropy
            return max(0.3, min(0.9, confidence))
        except Exception as e:
            logger.error(f"Error in _calculate_prediction_confidence: {e}")
            raise
    
    def _calculate_feature_importance(
        self,
        features: np.ndarray
    ) -> Dict[str, float]:
        """Calculate feature importance from model."""
        try:
            feature_names = [
                'price', 'returns', 'ma_5', 'ma_20', 'volatility',
                'volume_ratio', 'rsi', 'macd', 'signal', 'ma_distance'
            ]
        
            # Use embedding weights as proxy for importance
            importance = np.mean(np.abs(self.weights['embedding']), axis=1)
            importance = importance / np.sum(importance)
        
            return {
                name: float(imp)
                for name, imp in zip(feature_names, importance)
            }
        except Exception as e:
            logger.error(f"Error in _calculate_feature_importance: {e}")
            raise
    
    def _calculate_uncertainty(
        self,
        predictions: List[PricePrediction]
    ) -> float:
        """Calculate model uncertainty."""
        try:
            if len(predictions) < 2:
                return 0.5
        
            # Variance in predictions
            prices = [p.predicted_price for p in predictions]
            confidences = [p.confidence for p in predictions]
        
            price_std = np.std(prices) / np.mean(prices)
            conf_std = np.std(confidences)
        
            uncertainty = (price_std + conf_std) / 2
            return min(1.0, uncertainty)
        except Exception as e:
            logger.error(f"Error in _calculate_uncertainty: {e}")
            raise
    
    def _generate_signal(
        self,
        direction: str,
        confidence: float,
        uncertainty: float
    ) -> str:
        """Generate trading signal."""
        try:
            if uncertainty > 0.5:
                return f"UNCERTAIN: High model uncertainty ({uncertainty:.0%}). Wait for clarity."
        
            if confidence < 0.5:
                return f"WEAK SIGNAL: Low confidence ({confidence:.0%}). Consider smaller position."
        
            if direction == 'up':
                return f"BUY SIGNAL: {confidence:.0%} confidence, {uncertainty:.0%} uncertainty"
            else:
                return f"SELL SIGNAL: {confidence:.0%} confidence, {uncertainty:.0%} uncertainty"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def train(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        epochs: int = 100,
        learning_rate: float = 0.001
    ):
        """Train the transformer model."""
        try:
            logger.info(f"Training transformer for {epochs} epochs...")
        
            # Simplified training loop
            for epoch in range(epochs):
                features = self._prepare_features(prices, volumes)
            
                # Forward pass
                output, _ = self._transformer_forward(features)
            
                # Calculate loss (simplified MSE)
                target = np.diff(prices[-self.sequence_length:]) / prices[-self.sequence_length:-1]
                prediction = output @ self.weights['output']
                loss = np.mean((prediction.flatten()[:len(target)] - target) ** 2)
            
                # Backward pass (simplified gradient descent)
                gradient = 2 * (prediction.flatten()[:len(target)] - target)
                self.weights['output'] -= learning_rate * np.outer(
                    np.mean(output, axis=0),
                    np.mean(gradient)
                )
            
                if epoch % 20 == 0:
                    logger.info(f"Epoch {epoch}, Loss: {loss:.6f}")
        
            self.is_trained = True
            logger.info("Training complete")
        except Exception as e:
            logger.error(f"Error in train: {e}")
            raise
    
    def _create_empty_result(self) -> TransformerPredictionResult:
        """Create empty result for insufficient data."""
        return TransformerPredictionResult(
            predictions=[],
            ensemble_prediction=0,
            ensemble_direction='neutral',
            ensemble_confidence=0,
            feature_importance={},
            model_uncertainty=1.0,
            trading_signal="Insufficient data"
        )
