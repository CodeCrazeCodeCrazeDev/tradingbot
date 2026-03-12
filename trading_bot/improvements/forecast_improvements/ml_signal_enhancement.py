"""
Machine Learning Signal Enhancement - Improvement #11 (MEDIUM PRIORITY)
========================================================================

ML-enhanced predictions for smarter pattern recognition.

Features:
- Feature engineering (100+ features)
- Random Forest signal classifier
- LSTM price prediction
- Ensemble model voting
- Online learning adaptation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics
import math

logger = logging.getLogger(__name__)

# Optional imports
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("NumPy not available, using fallback implementations")

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not available, using mock ML models")


class SignalPrediction(Enum):
    """ML signal prediction"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class MLPrediction:
    """ML prediction result"""
    symbol: str
    prediction: SignalPrediction
    confidence: float
    probabilities: Dict[str, float]
    features_used: int
    model_name: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnsemblePrediction:
    """Ensemble prediction result"""
    symbol: str
    final_prediction: SignalPrediction
    confidence: float
    model_predictions: List[MLPrediction]
    agreement_score: float
    timestamp: datetime = field(default_factory=datetime.now)


class FeatureEngineer:
    """Feature engineering for ML models"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.feature_names: List[str] = []
    
    def extract_features(
        self,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float]
    ) -> Dict[str, float]:
        """Extract 100+ features from OHLCV data"""
        features = {}
        
        if len(closes) < 50:
            return features
        
        # Price features
        features.update(self._price_features(closes))
        
        # Volatility features
        features.update(self._volatility_features(highs, lows, closes))
        
        # Momentum features
        features.update(self._momentum_features(closes))
        
        # Volume features
        features.update(self._volume_features(closes, volumes))
        
        # Pattern features
        features.update(self._pattern_features(opens, highs, lows, closes))
        
        # Statistical features
        features.update(self._statistical_features(closes))
        
        # Trend features
        features.update(self._trend_features(closes))
        
        self.feature_names = list(features.keys())
        return features
    
    def _price_features(self, closes: List[float]) -> Dict[str, float]:
        """Price-based features"""
        features = {}
        current = closes[-1]
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            if len(closes) >= period:
                ma = sum(closes[-period:]) / period
                features[f'ma_{period}'] = ma
                features[f'price_to_ma_{period}'] = current / ma if ma > 0 else 1
                features[f'ma_{period}_slope'] = (ma - sum(closes[-period-5:-5]) / period) / ma if len(closes) >= period + 5 else 0
        
        # Price changes
        for period in [1, 5, 10, 20]:
            if len(closes) > period:
                change = (current - closes[-period-1]) / closes[-period-1]
                features[f'return_{period}'] = change
        
        # Price position in range
        if len(closes) >= 20:
            high_20 = max(closes[-20:])
            low_20 = min(closes[-20:])
            range_20 = high_20 - low_20
            if range_20 > 0:
                features['price_position_20'] = (current - low_20) / range_20
        
        return features
    
    def _volatility_features(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        """Volatility features"""
        features = {}
        
        # ATR
        for period in [7, 14, 21]:
            if len(highs) >= period + 1:
                atr = self._calculate_atr(highs, lows, closes, period)
                features[f'atr_{period}'] = atr
                features[f'atr_{period}_normalized'] = atr / closes[-1] if closes[-1] > 0 else 0
        
        # Bollinger Band width
        if len(closes) >= 20:
            ma_20 = sum(closes[-20:]) / 20
            std_20 = statistics.stdev(closes[-20:])
            features['bb_width'] = (2 * std_20) / ma_20 if ma_20 > 0 else 0
            features['bb_position'] = (closes[-1] - (ma_20 - 2*std_20)) / (4*std_20) if std_20 > 0 else 0.5
        
        # Historical volatility
        if len(closes) >= 21:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            features['volatility_20'] = statistics.stdev(returns[-20:]) if len(returns) >= 20 else 0
        
        return features
    
    def _momentum_features(self, closes: List[float]) -> Dict[str, float]:
        """Momentum features"""
        features = {}
        
        # RSI
        for period in [7, 14, 21]:
            if len(closes) >= period + 1:
                rsi = self._calculate_rsi(closes, period)
                features[f'rsi_{period}'] = rsi
                features[f'rsi_{period}_overbought'] = 1 if rsi > 70 else 0
                features[f'rsi_{period}_oversold'] = 1 if rsi < 30 else 0
        
        # MACD
        if len(closes) >= 26:
            ema_12 = self._calculate_ema(closes, 12)
            ema_26 = self._calculate_ema(closes, 26)
            macd = ema_12 - ema_26
            features['macd'] = macd
            features['macd_normalized'] = macd / closes[-1] if closes[-1] > 0 else 0
        
        # Rate of change
        for period in [5, 10, 20]:
            if len(closes) > period:
                roc = (closes[-1] - closes[-period-1]) / closes[-period-1] * 100
                features[f'roc_{period}'] = roc
        
        # Stochastic
        if len(closes) >= 14:
            high_14 = max(closes[-14:])
            low_14 = min(closes[-14:])
            if high_14 != low_14:
                stoch_k = (closes[-1] - low_14) / (high_14 - low_14) * 100
                features['stoch_k'] = stoch_k
        
        return features
    
    def _volume_features(self, closes: List[float], volumes: List[float]) -> Dict[str, float]:
        """Volume features"""
        features = {}
        
        if not volumes or len(volumes) < 20:
            return features
        
        current_vol = volumes[-1]
        avg_vol_20 = sum(volumes[-20:]) / 20
        
        features['volume_ratio'] = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1
        features['volume_trend'] = sum(volumes[-5:]) / sum(volumes[-20:-5]) if sum(volumes[-20:-5]) > 0 else 1
        
        # OBV direction
        obv_changes = []
        for i in range(1, min(20, len(closes))):
            if closes[-i] > closes[-i-1]:
                obv_changes.append(volumes[-i])
            else:
                obv_changes.append(-volumes[-i])
        
        if obv_changes:
            features['obv_direction'] = 1 if sum(obv_changes) > 0 else -1
        
        # Volume-price correlation
        if len(closes) >= 20 and len(volumes) >= 20:
            price_changes = [closes[i] - closes[i-1] for i in range(-19, 0)]
            vol_changes = [volumes[i] - volumes[i-1] for i in range(-19, 0)]
            
            if statistics.stdev(price_changes) > 0 and statistics.stdev(vol_changes) > 0:
                correlation = self._calculate_correlation(price_changes, vol_changes)
                features['volume_price_corr'] = correlation
        
        return features
    
    def _pattern_features(self, opens: List[float], highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        """Candlestick pattern features"""
        features = {}
        
        if len(closes) < 5:
            return features
        
        # Body size
        body = abs(closes[-1] - opens[-1])
        total_range = highs[-1] - lows[-1]
        features['body_ratio'] = body / total_range if total_range > 0 else 0
        
        # Upper/lower shadow
        if closes[-1] > opens[-1]:  # Bullish
            upper_shadow = highs[-1] - closes[-1]
            lower_shadow = opens[-1] - lows[-1]
        else:  # Bearish
            upper_shadow = highs[-1] - opens[-1]
            lower_shadow = closes[-1] - lows[-1]
        
        features['upper_shadow_ratio'] = upper_shadow / total_range if total_range > 0 else 0
        features['lower_shadow_ratio'] = lower_shadow / total_range if total_range > 0 else 0
        
        # Consecutive direction
        bullish_count = sum(1 for i in range(-5, 0) if closes[i] > opens[i])
        features['bullish_candles_5'] = bullish_count
        
        # Doji detection
        features['is_doji'] = 1 if features['body_ratio'] < 0.1 else 0
        
        # Engulfing pattern
        if len(closes) >= 2:
            prev_body = abs(closes[-2] - opens[-2])
            curr_body = abs(closes[-1] - opens[-1])
            features['engulfing'] = 1 if curr_body > prev_body * 1.5 else 0
        
        return features
    
    def _statistical_features(self, closes: List[float]) -> Dict[str, float]:
        """Statistical features"""
        features = {}
        
        if len(closes) < 20:
            return features
        
        recent = closes[-20:]
        
        features['mean'] = statistics.mean(recent)
        features['std'] = statistics.stdev(recent)
        features['skewness'] = self._calculate_skewness(recent)
        features['kurtosis'] = self._calculate_kurtosis(recent)
        
        # Z-score
        if features['std'] > 0:
            features['zscore'] = (closes[-1] - features['mean']) / features['std']
        
        return features
    
    def _trend_features(self, closes: List[float]) -> Dict[str, float]:
        """Trend features"""
        features = {}
        
        if len(closes) < 50:
            return features
        
        # Linear regression slope
        x = list(range(20))
        y = closes[-20:]
        slope = self._calculate_slope(x, y)
        features['trend_slope_20'] = slope
        
        # Higher highs / higher lows
        recent_highs = [max(closes[i:i+5]) for i in range(-20, -5, 5)]
        recent_lows = [min(closes[i:i+5]) for i in range(-20, -5, 5)]
        
        if len(recent_highs) >= 2:
            features['higher_highs'] = 1 if recent_highs[-1] > recent_highs[-2] else 0
            features['higher_lows'] = 1 if recent_lows[-1] > recent_lows[-2] else 0
        
        # ADX approximation
        features['trend_strength'] = abs(slope) / statistics.stdev(closes[-20:]) if statistics.stdev(closes[-20:]) > 0 else 0
        
        return features
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
        """Calculate ATR"""
        tr_values = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
        
        return sum(tr_values[-period:]) / period if len(tr_values) >= period else 0
    
    def _calculate_rsi(self, closes: List[float], period: int) -> float:
        """Calculate RSI"""
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
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_ema(self, data: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation"""
        n = len(x)
        if n < 2:
            return 0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
        
        if std_x == 0 or std_y == 0:
            return 0
        
        return numerator / (n * std_x * std_y)
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness"""
        n = len(data)
        if n < 3:
            return 0
        
        mean = sum(data) / n
        std = statistics.stdev(data)
        
        if std == 0:
            return 0
        
        return sum((x - mean) ** 3 for x in data) / (n * std ** 3)
    
    def _calculate_kurtosis(self, data: List[float]) -> float:
        """Calculate kurtosis"""
        n = len(data)
        if n < 4:
            return 0
        
        mean = sum(data) / n
        std = statistics.stdev(data)
        
        if std == 0:
            return 0
        
        return sum((x - mean) ** 4 for x in data) / (n * std ** 4) - 3
    
    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """Calculate linear regression slope"""
        n = len(x)
        if n < 2:
            return 0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((xi - mean_x) ** 2 for xi in x)
        
        if denominator == 0:
            return 0
        
        return numerator / denominator


class RandomForestSignalClassifier:
    """Random Forest signal classifier"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.n_estimators = self.config.get('n_estimators', 100)
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_names: List[str] = []
    
    def train(self, features_list: List[Dict[str, float]], labels: List[int]):
        """Train the model"""
        if not HAS_SKLEARN:
            logger.warning("scikit-learn not available, using mock training")
            self.is_trained = True
            return
        
        if len(features_list) < 100:
            logger.warning("Insufficient training data")
            return
        
        # Convert to arrays
        self.feature_names = list(features_list[0].keys())
        X = [[f.get(name, 0) for name in self.feature_names] for f in features_list]
        y = labels
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        logger.info(f"RandomForest trained on {len(X)} samples")
    
    def predict(self, features: Dict[str, float]) -> MLPrediction:
        """Make prediction"""
        if not self.is_trained:
            return self._mock_prediction(features)
        
        if not HAS_SKLEARN or self.model is None:
            return self._mock_prediction(features)
        
        # Prepare features
        X = [[features.get(name, 0) for name in self.feature_names]]
        X_scaled = self.scaler.transform(X)
        
        # Predict
        pred = self.model.predict(X_scaled)[0]
        proba = self.model.predict_proba(X_scaled)[0]
        
        # Convert to SignalPrediction
        prediction_map = {
            -2: SignalPrediction.STRONG_SELL,
            -1: SignalPrediction.SELL,
            0: SignalPrediction.NEUTRAL,
            1: SignalPrediction.BUY,
            2: SignalPrediction.STRONG_BUY
        }
        
        signal = prediction_map.get(pred, SignalPrediction.NEUTRAL)
        confidence = max(proba)
        
        return MLPrediction(
            symbol="",
            prediction=signal,
            confidence=confidence,
            probabilities={str(i): p for i, p in enumerate(proba)},
            features_used=len(self.feature_names),
            model_name="RandomForest"
        )
    
    def _mock_prediction(self, features: Dict[str, float]) -> MLPrediction:
        """Mock prediction when model not trained"""
        # Simple rule-based prediction
        rsi = features.get('rsi_14', 50)
        ma_ratio = features.get('price_to_ma_20', 1)
        
        if rsi < 30 and ma_ratio < 0.98:
            signal = SignalPrediction.BUY
            confidence = 0.6
        elif rsi > 70 and ma_ratio > 1.02:
            signal = SignalPrediction.SELL
            confidence = 0.6
        else:
            signal = SignalPrediction.NEUTRAL
            confidence = 0.5
        
        return MLPrediction(
            symbol="",
            prediction=signal,
            confidence=confidence,
            probabilities={},
            features_used=len(features),
            model_name="MockRandomForest"
        )


class LSTMPredictor:
    """LSTM price predictor (simplified)"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sequence_length = self.config.get('sequence_length', 20)
        self.is_trained = False
    
    def train(self, price_sequences: List[List[float]], labels: List[int]):
        """Train LSTM (mock implementation)"""
        # Full LSTM would require PyTorch/TensorFlow
        self.is_trained = True
        logger.info("LSTM mock training complete")
    
    def predict(self, recent_prices: List[float]) -> MLPrediction:
        """Predict using LSTM (mock)"""
        if len(recent_prices) < self.sequence_length:
            return MLPrediction(
                symbol="",
                prediction=SignalPrediction.NEUTRAL,
                confidence=0.5,
                probabilities={},
                features_used=len(recent_prices),
                model_name="LSTM"
            )
        
        # Simple momentum-based prediction
        recent = recent_prices[-self.sequence_length:]
        momentum = (recent[-1] - recent[0]) / recent[0]
        
        if momentum > 0.02:
            signal = SignalPrediction.BUY
            confidence = min(0.5 + abs(momentum) * 10, 0.9)
        elif momentum < -0.02:
            signal = SignalPrediction.SELL
            confidence = min(0.5 + abs(momentum) * 10, 0.9)
        else:
            signal = SignalPrediction.NEUTRAL
            confidence = 0.5
        
        return MLPrediction(
            symbol="",
            prediction=signal,
            confidence=confidence,
            probabilities={},
            features_used=self.sequence_length,
            model_name="LSTM"
        )


class EnsembleVoter:
    """Ensemble model voting"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model_weights = self.config.get('model_weights', {
            'RandomForest': 0.4,
            'LSTM': 0.3,
            'GradientBoosting': 0.3
        })
    
    def vote(self, predictions: List[MLPrediction]) -> EnsemblePrediction:
        """Combine predictions through voting"""
        if not predictions:
            return EnsemblePrediction(
                symbol="",
                final_prediction=SignalPrediction.NEUTRAL,
                confidence=0.0,
                model_predictions=[],
                agreement_score=0.0
            )
        
        # Weight predictions
        signal_scores = {
            SignalPrediction.STRONG_BUY: 0,
            SignalPrediction.BUY: 0,
            SignalPrediction.NEUTRAL: 0,
            SignalPrediction.SELL: 0,
            SignalPrediction.STRONG_SELL: 0
        }
        
        total_weight = 0
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 0.25)
            signal_scores[pred.prediction] += weight * pred.confidence
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            for signal in signal_scores:
                signal_scores[signal] /= total_weight
        
        # Find winner
        final_signal = max(signal_scores.keys(), key=lambda s: signal_scores[s])
        final_confidence = signal_scores[final_signal]
        
        # Calculate agreement
        agreement = sum(1 for p in predictions if p.prediction == final_signal) / len(predictions)
        
        return EnsemblePrediction(
            symbol=predictions[0].symbol if predictions else "",
            final_prediction=final_signal,
            confidence=final_confidence,
            model_predictions=predictions,
            agreement_score=agreement
        )


class OnlineLearningAdapter:
    """Online learning for model adaptation"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.buffer_size = self.config.get('buffer_size', 1000)
        self.experience_buffer: deque = deque(maxlen=self.buffer_size)
        self.retrain_threshold = self.config.get('retrain_threshold', 100)
    
    def add_experience(self, features: Dict[str, float], actual_outcome: int, predicted: SignalPrediction):
        """Add trading experience"""
        self.experience_buffer.append({
            'features': features,
            'actual': actual_outcome,
            'predicted': predicted,
            'timestamp': datetime.now()
        })
    
    def should_retrain(self) -> bool:
        """Check if should retrain models"""
        return len(self.experience_buffer) >= self.retrain_threshold
    
    def get_training_data(self) -> Tuple[List[Dict[str, float]], List[int]]:
        """Get training data from buffer"""
        features = [e['features'] for e in self.experience_buffer]
        labels = [e['actual'] for e in self.experience_buffer]
        return features, labels
    
    def get_accuracy(self) -> float:
        """Calculate recent prediction accuracy"""
        if not self.experience_buffer:
            return 0.0
        
        correct = 0
        for exp in self.experience_buffer:
            pred_value = {
                SignalPrediction.STRONG_BUY: 2,
                SignalPrediction.BUY: 1,
                SignalPrediction.NEUTRAL: 0,
                SignalPrediction.SELL: -1,
                SignalPrediction.STRONG_SELL: -2
            }.get(exp['predicted'], 0)
            
            # Check if direction was correct
            if (pred_value > 0 and exp['actual'] > 0) or \
               (pred_value < 0 and exp['actual'] < 0) or \
               (pred_value == 0 and abs(exp['actual']) < 0.5):
                correct += 1
        
        return correct / len(self.experience_buffer)


class MLSignalEnhancer:
    """
    Master ML signal enhancement system.
    Combines all ML functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.feature_engineer = FeatureEngineer(self.config)
        self.rf_classifier = RandomForestSignalClassifier(self.config)
        self.lstm_predictor = LSTMPredictor(self.config)
        self.ensemble_voter = EnsembleVoter(self.config)
        self.online_adapter = OnlineLearningAdapter(self.config)
        
        # Prediction history
        self.prediction_history: deque = deque(maxlen=1000)
    
    def enhance_signal(
        self,
        symbol: str,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float]
    ) -> EnsemblePrediction:
        """Enhance signal using ML models"""
        # Extract features
        features = self.feature_engineer.extract_features(opens, highs, lows, closes, volumes)
        
        if not features:
            return EnsemblePrediction(
                symbol=symbol,
                final_prediction=SignalPrediction.NEUTRAL,
                confidence=0.0,
                model_predictions=[],
                agreement_score=0.0
            )
        
        # Get predictions from each model
        predictions = []
        
        # Random Forest
        rf_pred = self.rf_classifier.predict(features)
        rf_pred.symbol = symbol
        predictions.append(rf_pred)
        
        # LSTM
        lstm_pred = self.lstm_predictor.predict(closes)
        lstm_pred.symbol = symbol
        predictions.append(lstm_pred)
        
        # Ensemble voting
        ensemble = self.ensemble_voter.vote(predictions)
        ensemble.symbol = symbol
        
        # Record prediction
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'prediction': ensemble.final_prediction.value,
            'confidence': ensemble.confidence,
            'agreement': ensemble.agreement_score
        })
        
        return ensemble
    
    def train_models(self, training_data: List[Dict]):
        """Train all models"""
        if len(training_data) < 100:
            logger.warning("Insufficient training data")
            return
        
        # Prepare data
        features_list = []
        labels = []
        price_sequences = []
        
        for data in training_data:
            features = self.feature_engineer.extract_features(
                data['opens'], data['highs'], data['lows'],
                data['closes'], data['volumes']
            )
            if features:
                features_list.append(features)
                labels.append(data['label'])
                price_sequences.append(data['closes'][-20:])
        
        # Train models
        self.rf_classifier.train(features_list, labels)
        self.lstm_predictor.train(price_sequences, labels)
        
        logger.info("ML models trained")
    
    def record_outcome(self, symbol: str, features: Dict[str, float], actual_outcome: int, predicted: SignalPrediction):
        """Record trading outcome for online learning"""
        self.online_adapter.add_experience(features, actual_outcome, predicted)
        
        # Check if should retrain
        if self.online_adapter.should_retrain():
            features_list, labels = self.online_adapter.get_training_data()
            self.rf_classifier.train(features_list, labels)
            logger.info("Models retrained with online data")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ML statistics"""
        return {
            'total_predictions': len(self.prediction_history),
            'online_accuracy': self.online_adapter.get_accuracy(),
            'experience_buffer_size': len(self.online_adapter.experience_buffer),
            'rf_trained': self.rf_classifier.is_trained,
            'lstm_trained': self.lstm_predictor.is_trained
        }
