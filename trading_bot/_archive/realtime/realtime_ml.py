"""
Real-Time ML Engine
===================

Real-time machine learning inference with streaming predictions.
No batch processing - continuous online learning and prediction.

Features:
1. Real-time feature extraction
2. Streaming model inference
3. Online learning updates
4. Prediction confidence tracking
5. Model performance monitoring
6. Ensemble predictions

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions"""
    PRICE_DIRECTION = "price_direction"
    PRICE_MAGNITUDE = "price_magnitude"
    VOLATILITY = "volatility"
    REGIME = "regime"
    SIGNAL_QUALITY = "signal_quality"


class ModelType(Enum):
    """Types of models"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND = "trend"
    VOLATILITY = "volatility"
    ENSEMBLE = "ensemble"


@dataclass
class RealTimePrediction:
    """Real-time prediction"""
    prediction_id: str
    symbol: str
    prediction_type: PredictionType
    model_type: ModelType
    value: float
    confidence: float
    timestamp: datetime
    features_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'prediction_id': self.prediction_id,
            'symbol': self.symbol,
            'prediction_type': self.prediction_type.value,
            'model_type': self.model_type.value,
            'value': self.value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'features_used': self.features_used,
            'metadata': self.metadata
        }


@dataclass
class FeatureVector:
    """Real-time feature vector"""
    symbol: str
    timestamp: datetime
    features: Dict[str, float]
    
    def to_array(self, feature_names: List[str]) -> np.ndarray:
        return np.array([self.features.get(name, 0.0) for name in feature_names])


class RealTimeFeatureExtractor:
    """
    Real-time feature extraction from streaming data.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Feature buffers per symbol
        self._price_buffer: Dict[str, deque] = {}
        self._volume_buffer: Dict[str, deque] = {}
        self._return_buffer: Dict[str, deque] = {}
        
        self._buffer_size = config.get('buffer_size', 100)
        
        # Feature names
        self._feature_names = [
            'price', 'volume', 'return_1', 'return_5', 'return_10',
            'volatility_5', 'volatility_20', 'momentum_5', 'momentum_10',
            'rsi_14', 'sma_ratio_20', 'volume_ratio', 'spread_bps',
            'bid_ask_imbalance', 'price_velocity', 'volume_velocity'
        ]
    
    def update(self, symbol: str, price: float, volume: float = 0,
               bid: float = None, ask: float = None) -> FeatureVector:
        """Update with new data and extract features"""
        # Initialize buffers
        if symbol not in self._price_buffer:
            self._price_buffer[symbol] = deque(maxlen=self._buffer_size)
            self._volume_buffer[symbol] = deque(maxlen=self._buffer_size)
            self._return_buffer[symbol] = deque(maxlen=self._buffer_size)
        
        # Calculate return
        prices = self._price_buffer[symbol]
        if prices:
            ret = (price - prices[-1]) / prices[-1] if prices[-1] != 0 else 0
        else:
            ret = 0
        
        # Update buffers
        self._price_buffer[symbol].append(price)
        self._volume_buffer[symbol].append(volume)
        self._return_buffer[symbol].append(ret)
        
        # Extract features
        features = self._extract_features(symbol, price, volume, bid, ask)
        
        return FeatureVector(
            symbol=symbol,
            timestamp=datetime.now(),
            features=features
        )
    
    def _extract_features(self, symbol: str, price: float, volume: float,
                         bid: float = None, ask: float = None) -> Dict[str, float]:
        """Extract all features"""
        prices = list(self._price_buffer[symbol])
        volumes = list(self._volume_buffer[symbol])
        returns = list(self._return_buffer[symbol])
        
        features = {
            'price': price,
            'volume': volume,
        }
        
        # Return features
        if len(returns) >= 1:
            features['return_1'] = returns[-1]
        if len(returns) >= 5:
            features['return_5'] = sum(returns[-5:])
        if len(returns) >= 10:
            features['return_10'] = sum(returns[-10:])
        
        # Volatility features
        if len(returns) >= 5:
            features['volatility_5'] = np.std(returns[-5:])
        if len(returns) >= 20:
            features['volatility_20'] = np.std(returns[-20:])
        
        # Momentum features
        if len(prices) >= 5:
            features['momentum_5'] = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0
        if len(prices) >= 10:
            features['momentum_10'] = (prices[-1] - prices[-10]) / prices[-10] if prices[-10] != 0 else 0
        
        # RSI
        if len(returns) >= 14:
            gains = [r for r in returns[-14:] if r > 0]
            losses = [-r for r in returns[-14:] if r < 0]
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0
            if avg_loss == 0:
                features['rsi_14'] = 100
            else:
                rs = avg_gain / avg_loss
                features['rsi_14'] = 100 - (100 / (1 + rs))
        
        # SMA ratio
        if len(prices) >= 20:
            sma_20 = sum(prices[-20:]) / 20
            features['sma_ratio_20'] = price / sma_20 if sma_20 != 0 else 1
        
        # Volume ratio
        if len(volumes) >= 20 and sum(volumes[-20:]) > 0:
            avg_volume = sum(volumes[-20:]) / 20
            features['volume_ratio'] = volume / avg_volume if avg_volume != 0 else 1
        
        # Spread
        if bid and ask and ask > 0:
            mid = (bid + ask) / 2
            features['spread_bps'] = (ask - bid) / mid * 10000 if mid > 0 else 0
            features['bid_ask_imbalance'] = (bid - ask) / (bid + ask) if (bid + ask) > 0 else 0
        
        # Velocity features
        if len(prices) >= 5:
            price_changes = [prices[i] - prices[i-1] for i in range(-4, 0)]
            features['price_velocity'] = sum(price_changes) / 4 if price_changes else 0
        
        if len(volumes) >= 5:
            vol_changes = [volumes[i] - volumes[i-1] for i in range(-4, 0)]
            features['volume_velocity'] = sum(vol_changes) / 4 if vol_changes else 0
        
        return features
    
    @property
    def feature_names(self) -> List[str]:
        return self._feature_names


class OnlineModel:
    """
    Base class for online learning models.
    """
    
    def __init__(self, name: str, model_type: ModelType):
        self.name = name
        self.model_type = model_type
        self._prediction_count = 0
        self._correct_predictions = 0
        self._last_prediction: Optional[float] = None
        self._last_actual: Optional[float] = None
    
    def predict(self, features: FeatureVector) -> tuple:
        """Make prediction - returns (value, confidence)"""
    
    def update(self, features: FeatureVector, actual: float):
        """Update model with actual outcome"""
        # Track accuracy
        if self._last_prediction is not None and self._last_actual is not None:
            if (self._last_prediction > 0) == (self._last_actual > 0):
                self._correct_predictions += 1
        
        self._last_actual = actual
    
    @property
    def accuracy(self) -> float:
        if self._prediction_count == 0:
            return 0.5
        return self._correct_predictions / self._prediction_count


class MomentumModel(OnlineModel):
    """Momentum-based prediction model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("momentum", ModelType.MOMENTUM)
        config = config or {}
        self._lookback = config.get('lookback', 10)
        self._threshold = config.get('threshold', 0.001)
    
    def predict(self, features: FeatureVector) -> tuple:
        momentum = features.features.get('momentum_10', 0)
        rsi = features.features.get('rsi_14', 50)
        
        # Momentum signal
        if abs(momentum) < self._threshold:
            return 0.0, 0.3
        
        # Direction based on momentum
        direction = 1.0 if momentum > 0 else -1.0
        
        # Confidence based on RSI confirmation
        if direction > 0 and rsi < 70:
            confidence = min(0.5 + abs(momentum) * 10, 0.9)
        elif direction < 0 and rsi > 30:
            confidence = min(0.5 + abs(momentum) * 10, 0.9)
        else:
            confidence = 0.4
        
        self._prediction_count += 1
        self._last_prediction = direction
        
        return direction, confidence


class MeanReversionModel(OnlineModel):
    """Mean reversion prediction model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("mean_reversion", ModelType.MEAN_REVERSION)
        config = config or {}
        self._threshold = config.get('threshold', 1.02)
    
    def predict(self, features: FeatureVector) -> tuple:
        sma_ratio = features.features.get('sma_ratio_20', 1.0)
        rsi = features.features.get('rsi_14', 50)
        volatility = features.features.get('volatility_20', 0.01)
        
        # Mean reversion signal
        if sma_ratio > self._threshold and rsi > 70:
            direction = -1.0  # Expect reversion down
            confidence = min(0.5 + (sma_ratio - 1) * 5 + (rsi - 70) / 100, 0.9)
        elif sma_ratio < (2 - self._threshold) and rsi < 30:
            direction = 1.0  # Expect reversion up
            confidence = min(0.5 + (1 - sma_ratio) * 5 + (30 - rsi) / 100, 0.9)
        else:
            return 0.0, 0.3
        
        # Adjust confidence by volatility
        if volatility > 0.02:
            confidence *= 0.8
        
        self._prediction_count += 1
        self._last_prediction = direction
        
        return direction, confidence


class TrendModel(OnlineModel):
    """Trend following prediction model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("trend", ModelType.TREND)
        config = config or {}
    
    def predict(self, features: FeatureVector) -> tuple:
        momentum_5 = features.features.get('momentum_5', 0)
        momentum_10 = features.features.get('momentum_10', 0)
        sma_ratio = features.features.get('sma_ratio_20', 1.0)
        
        # Trend alignment
        if momentum_5 > 0 and momentum_10 > 0 and sma_ratio > 1:
            direction = 1.0
            alignment = min(momentum_5, momentum_10) / max(abs(momentum_5), abs(momentum_10), 0.001)
            confidence = min(0.5 + alignment * 0.3 + (sma_ratio - 1) * 2, 0.9)
        elif momentum_5 < 0 and momentum_10 < 0 and sma_ratio < 1:
            direction = -1.0
            alignment = min(abs(momentum_5), abs(momentum_10)) / max(abs(momentum_5), abs(momentum_10), 0.001)
            confidence = min(0.5 + alignment * 0.3 + (1 - sma_ratio) * 2, 0.9)
        else:
            return 0.0, 0.3
        
        self._prediction_count += 1
        self._last_prediction = direction
        
        return direction, confidence


class VolatilityModel(OnlineModel):
    """Volatility prediction model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("volatility", ModelType.VOLATILITY)
        config = config or {}
        self._vol_history: deque = deque(maxlen=100)
    
    def predict(self, features: FeatureVector) -> tuple:
        current_vol = features.features.get('volatility_5', 0.01)
        historical_vol = features.features.get('volatility_20', 0.01)
        
        self._vol_history.append(current_vol)
        
        # Predict volatility regime
        if len(self._vol_history) < 10:
            return current_vol, 0.5
        
        avg_vol = sum(self._vol_history) / len(self._vol_history)
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
        
        # Volatility mean reversion
        if vol_ratio > 1.5:
            predicted_vol = current_vol * 0.8  # Expect vol to decrease
            confidence = min(0.5 + (vol_ratio - 1) * 0.2, 0.8)
        elif vol_ratio < 0.7:
            predicted_vol = current_vol * 1.2  # Expect vol to increase
            confidence = min(0.5 + (1 - vol_ratio) * 0.2, 0.8)
        else:
            predicted_vol = current_vol
            confidence = 0.6
        
        self._prediction_count += 1
        self._last_prediction = predicted_vol
        
        return predicted_vol, confidence


class EnsembleModel:
    """
    Ensemble of models with dynamic weighting.
    """
    
    def __init__(self, models: List[OnlineModel], config: Dict[str, Any] = None):
        self.models = models
        self.config = config or {}
        
        # Model weights (updated based on performance)
        self._weights = {m.name: 1.0 / len(models) for m in models}
        self._weight_update_interval = config.get('weight_update_interval', 100)
        self._prediction_count = 0
    
    def predict(self, features: FeatureVector) -> tuple:
        """Ensemble prediction with weighted voting"""
        predictions = []
        total_weight = 0
        
        for model in self.models:
            value, confidence = model.predict(features)
            weight = self._weights[model.name] * confidence
            predictions.append((value, weight))
            total_weight += weight
        
        if total_weight == 0:
            return 0.0, 0.3
        
        # Weighted average
        ensemble_value = sum(v * w for v, w in predictions) / total_weight
        ensemble_confidence = total_weight / len(self.models)
        
        self._prediction_count += 1
        
        # Update weights periodically
        if self._prediction_count % self._weight_update_interval == 0:
            self._update_weights()
        
        return ensemble_value, min(ensemble_confidence, 0.95)
    
    def _update_weights(self):
        """Update model weights based on accuracy"""
        total_accuracy = sum(m.accuracy for m in self.models)
        
        if total_accuracy > 0:
            for model in self.models:
                self._weights[model.name] = model.accuracy / total_accuracy
    
    def update(self, features: FeatureVector, actual: float):
        """Update all models with actual outcome"""
        for model in self.models:
            model.update(features, actual)


class RealTimeMLEngine:
    """
    Real-time machine learning engine.
    
    Features:
    - Streaming feature extraction
    - Real-time model inference
    - Online learning updates
    - Ensemble predictions
    - Performance tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Feature extractor
        self._feature_extractor = RealTimeFeatureExtractor(config.get('features', {}))
        
        # Models
        self._models = [
            MomentumModel(config.get('momentum', {})),
            MeanReversionModel(config.get('mean_reversion', {})),
            TrendModel(config.get('trend', {})),
            VolatilityModel(config.get('volatility', {})),
        ]
        
        # Ensemble
        self._ensemble = EnsembleModel(self._models, config.get('ensemble', {}))
        
        # Predictions per symbol
        self._latest_predictions: Dict[str, RealTimePrediction] = {}
        self._prediction_history: deque = deque(maxlen=1000)
        
        # Subscribers
        self._subscribers: List[Callable] = []
        
        # Metrics
        self._metrics = {
            'predictions_made': 0,
            'avg_confidence': 0.0,
            'model_accuracies': {}
        }
        
        self._prediction_counter = 0
        self._running = False
        
        logger.info("RealTimeMLEngine initialized")
    
    async def on_tick(self, symbol: str, price: float, volume: float = 0,
                      bid: float = None, ask: float = None):
        """Handle new tick - generate predictions"""
        # Extract features
        features = self._feature_extractor.update(symbol, price, volume, bid, ask)
        
        # Generate ensemble prediction
        value, confidence = self._ensemble.predict(features)
        
        # Create prediction object
        self._prediction_counter += 1
        prediction = RealTimePrediction(
            prediction_id=f"PRED-{self._prediction_counter:08d}",
            symbol=symbol,
            prediction_type=PredictionType.PRICE_DIRECTION,
            model_type=ModelType.ENSEMBLE,
            value=value,
            confidence=confidence,
            timestamp=datetime.now(),
            features_used=list(features.features.keys()),
            metadata={
                'price': price,
                'model_weights': dict(self._ensemble._weights)
            }
        )
        
        # Store prediction
        self._latest_predictions[symbol] = prediction
        self._prediction_history.append(prediction)
        
        # Update metrics
        self._metrics['predictions_made'] += 1
        
        # Notify subscribers
        await self._notify_subscribers(prediction)
        
        return prediction
    
    async def on_outcome(self, symbol: str, actual_return: float):
        """Update models with actual outcome"""
        # Get latest features for symbol
        if symbol in self._feature_extractor._price_buffer:
            prices = list(self._feature_extractor._price_buffer[symbol])
            if prices:
                features = FeatureVector(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    features={'actual_return': actual_return}
                )
                self._ensemble.update(features, actual_return)
    
    async def _notify_subscribers(self, prediction: RealTimePrediction):
        """Notify prediction subscribers"""
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(prediction)
                else:
                    callback(prediction)
            except Exception as e:
                logger.error(f"ML subscriber error: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to predictions"""
        self._subscribers.append(callback)
    
    def get_prediction(self, symbol: str) -> Optional[RealTimePrediction]:
        """Get latest prediction for symbol"""
        return self._latest_predictions.get(symbol)
    
    def get_model_accuracies(self) -> Dict[str, float]:
        """Get accuracy of each model"""
        return {m.name: m.accuracy for m in self._models}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics"""
        return {
            **self._metrics,
            'model_accuracies': self.get_model_accuracies(),
            'ensemble_weights': dict(self._ensemble._weights),
            'symbols_tracked': len(self._latest_predictions)
        }
    
    async def start(self):
        """Start ML engine"""
        self._running = True
        logger.info("RealTimeMLEngine started")
    
    async def stop(self):
        """Stop ML engine"""
        self._running = False
        logger.info("RealTimeMLEngine stopped")
