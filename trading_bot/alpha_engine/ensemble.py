"""
Ensemble Model Architecture
============================

Meta-learning framework for combining multiple prediction models:
- AlphaEngine DC Signal
- LOB Deep Learning Prediction
- LSTM Trend Predictor
- Sentiment Aggregator
- Alternative Data Signals

Features:
- Dynamic weight adjustment based on performance
- Gradient boosting meta-learner
- Consensus engine with voting
- Model performance tracking
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class ModelType(Enum):
    """Types of base models in ensemble"""
    DC_ENGINE = "dc_engine"
    DEEP_LOB = "deep_lob"
    LSTM_TREND = "lstm_trend"
    SENTIMENT = "sentiment"
    ALT_DATA = "alt_data"
    TECHNICAL = "technical"
    REGIME = "regime"


@dataclass
class ModelPrediction:
    """Prediction from a single model"""
    model_type: ModelType
    timestamp: datetime
    symbol: str
    direction: str  # 'long', 'short', 'neutral'
    probability: float  # 0 to 1
    confidence: float  # 0 to 1
    magnitude: float  # Expected move size
    features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsemblePrediction:
    """Combined prediction from ensemble"""
    timestamp: datetime
    symbol: str
    direction: str
    probability: float
    confidence: float
    magnitude: float
    model_agreement: float  # 0 to 1
    contributing_models: List[str]
    model_weights: Dict[str, float]
    individual_predictions: Dict[str, ModelPrediction]
    should_trade: bool
    position_size_multiplier: float
    reason: str


class ModelPerformanceTracker:
    """
    Tracks performance of individual models for weight adjustment
    """
    
    def __init__(self, window_days: int = 30):
        self.window_days = window_days
        self.predictions: Dict[ModelType, deque] = {}
        self.outcomes: Dict[ModelType, deque] = {}
        
        for model_type in ModelType:
            self.predictions[model_type] = deque(maxlen=1000)
            self.outcomes[model_type] = deque(maxlen=1000)
    
    def record_prediction(self, prediction: ModelPrediction):
        """Record a model prediction"""
        self.predictions[prediction.model_type].append({
            'timestamp': prediction.timestamp,
            'symbol': prediction.symbol,
            'direction': prediction.direction,
            'probability': prediction.probability,
            'confidence': prediction.confidence,
        })
    
    def record_outcome(self, model_type: ModelType, symbol: str,
                      timestamp: datetime, actual_direction: str,
                      actual_return: float):
        """Record actual outcome for a prediction"""
        self.outcomes[model_type].append({
            'timestamp': timestamp,
            'symbol': symbol,
            'actual_direction': actual_direction,
            'actual_return': actual_return,
        })
    
    def get_model_metrics(self, model_type: ModelType) -> Dict[str, float]:
        """Calculate performance metrics for a model"""
        predictions = list(self.predictions[model_type])
        outcomes = list(self.outcomes[model_type])
        
        if not predictions or not outcomes:
            return {
                'accuracy': 0.5,
                'sharpe': 0,
                'win_rate': 0.5,
                'profit_factor': 1.0,
                'max_drawdown': 0,
            }
        
        # Match predictions with outcomes
        correct = 0
        total = 0
        returns = []
        
        cutoff = datetime.now() - timedelta(days=self.window_days)
        
        for pred in predictions:
            if pred['timestamp'] < cutoff:
                continue
            
            # Find matching outcome
            for outcome in outcomes:
                if (outcome['symbol'] == pred['symbol'] and 
                    abs((outcome['timestamp'] - pred['timestamp']).total_seconds()) < 3600):
                    
                    total += 1
                    if pred['direction'] == outcome['actual_direction']:
                        correct += 1
                    
                    # Calculate return based on prediction
                    if pred['direction'] == 'long':
                        returns.append(outcome['actual_return'])
                    elif pred['direction'] == 'short':
                        returns.append(-outcome['actual_return'])
                    break
        
        if total == 0:
            return {
                'accuracy': 0.5,
                'sharpe': 0,
                'win_rate': 0.5,
                'profit_factor': 1.0,
                'max_drawdown': 0,
            }
        
        accuracy = correct / total
        
        # Calculate Sharpe ratio
        if returns:
            returns = np.array(returns)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
            win_rate = np.sum(returns > 0) / len(returns)
            
            gains = returns[returns > 0]
            losses = returns[returns < 0]
            profit_factor = np.sum(gains) / (abs(np.sum(losses)) + 1e-10)
            
            # Max drawdown
            cumulative = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = running_max - cumulative
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        else:
            sharpe = 0
            win_rate = 0.5
            profit_factor = 1.0
            max_drawdown = 0
        
        return {
            'accuracy': accuracy,
            'sharpe': sharpe,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sample_size': total,
        }


class ModelWeightOptimizer:
    """
    Dynamically adjusts model weights based on performance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initial weights
        self.weights = {
            ModelType.DC_ENGINE: 0.30,
            ModelType.DEEP_LOB: 0.25,
            ModelType.LSTM_TREND: 0.20,
            ModelType.SENTIMENT: 0.15,
            ModelType.ALT_DATA: 0.10,
        }
        
        # Performance tracker
        self.tracker = ModelPerformanceTracker(
            window_days=self.config.get('performance_window', 30)
        )
        
        # Weight bounds
        self.min_weight = self.config.get('min_weight', 0.05)
        self.max_weight = self.config.get('max_weight', 0.50)
        
        # Adjustment rate
        self.adjustment_rate = self.config.get('adjustment_rate', 0.1)
    
    def update_weights(self):
        """
        Update model weights based on recent performance
        
        Uses exponential adjustment based on Sharpe ratio and accuracy
        """
        scores = {}
        
        for model_type in self.weights.keys():
            metrics = self.tracker.get_model_metrics(model_type)
            
            # Composite score
            score = (
                metrics['sharpe'] * 0.5 +
                (metrics['accuracy'] - 0.5) * 2 * 0.3 +
                (metrics['win_rate'] - 0.5) * 2 * 0.2
            )
            
            # Penalize high drawdown
            score -= metrics['max_drawdown'] * 0.2
            
            scores[model_type] = score
        
        # Adjust weights
        for model_type, score in scores.items():
            current_weight = self.weights[model_type]
            
            # Exponential adjustment
            adjustment = self.adjustment_rate * score
            new_weight = current_weight * (1 + adjustment)
            
            # Apply bounds
            new_weight = np.clip(new_weight, self.min_weight, self.max_weight)
            self.weights[model_type] = new_weight
        
        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
        
        logger.info(f"Updated model weights: {self.weights}")
    
    def get_weight(self, model_type: ModelType) -> float:
        """Get current weight for a model"""
        return self.weights.get(model_type, 0.1)
    
    def record_prediction(self, prediction: ModelPrediction):
        """Record prediction for tracking"""
        self.tracker.record_prediction(prediction)
    
    def record_outcome(self, model_type: ModelType, symbol: str,
                      timestamp: datetime, actual_direction: str,
                      actual_return: float):
        """Record outcome for tracking"""
        self.tracker.record_outcome(model_type, symbol, timestamp,
                                   actual_direction, actual_return)


class SignalAggregator:
    """
    Aggregates signals from multiple models
    """
    
    def __init__(self, weight_optimizer: ModelWeightOptimizer = None):
        self.weight_optimizer = weight_optimizer or ModelWeightOptimizer()
        self.signal_buffer: deque = deque(maxlen=1000)
    
    def aggregate(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """
        Aggregate multiple model predictions
        
        Args:
            predictions: List of predictions from different models
            
        Returns:
            Aggregated signal dictionary
        """
        if not predictions:
            return {
                'direction': 'neutral',
                'probability': 0.5,
                'confidence': 0,
                'agreement': 0,
            }
        
        # Weight predictions
        weighted_long = 0
        weighted_short = 0
        total_weight = 0
        
        for pred in predictions:
            weight = self.weight_optimizer.get_weight(pred.model_type)
            weight *= pred.confidence
            
            if pred.direction == 'long':
                weighted_long += pred.probability * weight
            elif pred.direction == 'short':
                weighted_short += pred.probability * weight
            
            total_weight += weight
            
            # Record for tracking
            self.weight_optimizer.record_prediction(pred)
        
        if total_weight == 0:
            return {
                'direction': 'neutral',
                'probability': 0.5,
                'confidence': 0,
                'agreement': 0,
            }
        
        # Normalize
        long_prob = weighted_long / total_weight
        short_prob = weighted_short / total_weight
        
        # Determine direction
        if long_prob > short_prob and long_prob > 0.5:
            direction = 'long'
            probability = long_prob
        elif short_prob > long_prob and short_prob > 0.5:
            direction = 'short'
            probability = short_prob
        else:
            direction = 'neutral'
            probability = 0.5
        
        # Calculate agreement (how many models agree)
        directions = [p.direction for p in predictions]
        agreement = max(
            directions.count('long'),
            directions.count('short'),
            directions.count('neutral')
        ) / len(directions)
        
        # Confidence based on agreement and individual confidences
        avg_confidence = np.mean([p.confidence for p in predictions])
        confidence = agreement * 0.5 + avg_confidence * 0.5
        
        return {
            'direction': direction,
            'probability': probability,
            'confidence': confidence,
            'agreement': agreement,
            'long_prob': long_prob,
            'short_prob': short_prob,
        }


class ConsensusEngine:
    """
    Implements consensus-based decision making
    
    Requires minimum agreement threshold for trade execution
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Minimum models that must agree
        self.min_agreement = self.config.get('min_agreement', 3)
        self.total_models = self.config.get('total_models', 5)
        
        # Confidence thresholds
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.high_confidence = self.config.get('high_confidence', 0.8)
        
        # Override conditions
        self.sentiment_extreme_threshold = self.config.get('sentiment_extreme', 70)
        self.lob_unusual_threshold = self.config.get('lob_unusual', 0.8)
    
    def evaluate(self, predictions: List[ModelPrediction],
                aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate consensus and determine if trade should be taken
        
        Args:
            predictions: Individual model predictions
            aggregated: Aggregated signal from SignalAggregator
            
        Returns:
            Consensus decision dictionary
        """
        # Count agreements
        direction = aggregated['direction']
        agreeing_models = [p for p in predictions if p.direction == direction]
        agreement_count = len(agreeing_models)
        
        # Check minimum agreement
        meets_agreement = agreement_count >= self.min_agreement
        
        # Check confidence
        meets_confidence = aggregated['confidence'] >= self.min_confidence
        
        # Check for overrides
        override_reason = None
        
        # Sentiment extreme override
        sentiment_pred = next((p for p in predictions 
                              if p.model_type == ModelType.SENTIMENT), None)
        if sentiment_pred:
            sentiment_score = sentiment_pred.metadata.get('score', 0)
            if abs(sentiment_score) > self.sentiment_extreme_threshold:
                override_reason = f"Extreme sentiment ({sentiment_score:.0f})"
        
        # LOB unusual pattern override
        lob_pred = next((p for p in predictions 
                        if p.model_type == ModelType.DEEP_LOB), None)
        if lob_pred:
            unusual_score = lob_pred.metadata.get('unusual_pattern', 0)
            if unusual_score > self.lob_unusual_threshold:
                override_reason = f"Unusual LOB pattern ({unusual_score:.2f})"
        
        # Determine if should trade
        should_trade = meets_agreement and meets_confidence and not override_reason
        
        # Position size multiplier based on confidence
        if aggregated['confidence'] >= self.high_confidence:
            size_multiplier = 1.2
        elif aggregated['confidence'] >= self.min_confidence:
            size_multiplier = 1.0
        else:
            size_multiplier = 0.5
        
        # Adjust for agreement
        size_multiplier *= (agreement_count / self.total_models)
        
        return {
            'should_trade': should_trade,
            'direction': direction,
            'agreement_count': agreement_count,
            'agreement_ratio': agreement_count / len(predictions),
            'meets_agreement': meets_agreement,
            'meets_confidence': meets_confidence,
            'override_reason': override_reason,
            'size_multiplier': size_multiplier,
            'agreeing_models': [p.model_type.value for p in agreeing_models],
        }


class EnsembleMetaLearner:
    """
    Meta-learner that combines base model predictions
    
    Uses gradient boosting to learn optimal combination
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.weight_optimizer = ModelWeightOptimizer(config.get('weight_optimizer', {}))
        self.signal_aggregator = SignalAggregator(self.weight_optimizer)
        self.consensus_engine = ConsensusEngine(config.get('consensus', {}))
        
        # Meta-learner model
        self.meta_model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        
        # Training data buffer
        self.training_buffer: deque = deque(maxlen=10000)
        
        # Feature names for meta-learner
        self.feature_names = [
            'dc_prob', 'dc_conf',
            'lob_prob', 'lob_conf',
            'lstm_prob', 'lstm_conf',
            'sentiment_prob', 'sentiment_conf',
            'alt_data_prob', 'alt_data_conf',
            'agreement_ratio', 'avg_confidence',
            'regime_trending', 'regime_volatile',
        ]
    
    def _initialize_meta_model(self):
        """Initialize the meta-learner model"""
        if XGBOOST_AVAILABLE:
            self.meta_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                objective='binary:logistic',
                eval_metric='auc',
            )
            logger.info("Using XGBoost meta-learner")
        elif LIGHTGBM_AVAILABLE:
            self.meta_model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
            )
            logger.info("Using LightGBM meta-learner")
        elif SKLEARN_AVAILABLE:
            self.meta_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
            )
            logger.info("Using sklearn GradientBoosting meta-learner")
        else:
            logger.warning("No ML library available for meta-learner")
    
    def predict(self, predictions: List[ModelPrediction],
               market_regime: Dict[str, Any] = None) -> EnsemblePrediction:
        """
        Generate ensemble prediction
        
        Args:
            predictions: List of base model predictions
            market_regime: Current market regime information
            
        Returns:
            EnsemblePrediction object
        """
        if not predictions:
            return self._empty_prediction()
        
        # Simple aggregation
        aggregated = self.signal_aggregator.aggregate(predictions)
        
        # Consensus evaluation
        consensus = self.consensus_engine.evaluate(predictions, aggregated)
        
        # Meta-learner prediction (if trained)
        if self.is_trained and self.meta_model is not None:
            features = self._extract_features(predictions, aggregated, market_regime)
            meta_prob = self._meta_predict(features)
            
            # Blend meta prediction with aggregated
            final_prob = aggregated['probability'] * 0.6 + meta_prob * 0.4
        else:
            final_prob = aggregated['probability']
        
        # Build individual predictions dict
        individual = {p.model_type.value: p for p in predictions}
        
        # Build weights dict
        weights = {p.model_type.value: self.weight_optimizer.get_weight(p.model_type) 
                  for p in predictions}
        
        return EnsemblePrediction(
            timestamp=datetime.now(),
            symbol=predictions[0].symbol if predictions else '',
            direction=consensus['direction'],
            probability=final_prob,
            confidence=aggregated['confidence'],
            magnitude=np.mean([p.magnitude for p in predictions]),
            model_agreement=consensus['agreement_ratio'],
            contributing_models=consensus['agreeing_models'],
            model_weights=weights,
            individual_predictions=individual,
            should_trade=consensus['should_trade'],
            position_size_multiplier=consensus['size_multiplier'],
            reason=consensus.get('override_reason', 'Consensus reached'),
        )
    
    def _extract_features(self, predictions: List[ModelPrediction],
                         aggregated: Dict[str, Any],
                         market_regime: Dict[str, Any] = None) -> np.ndarray:
        """Extract features for meta-learner"""
        features = {}
        
        # Model predictions
        for model_type in ModelType:
            pred = next((p for p in predictions if p.model_type == model_type), None)
            if pred:
                features[f'{model_type.value}_prob'] = pred.probability
                features[f'{model_type.value}_conf'] = pred.confidence
            else:
                features[f'{model_type.value}_prob'] = 0.5
                features[f'{model_type.value}_conf'] = 0
        
        # Aggregated features
        features['agreement_ratio'] = aggregated.get('agreement', 0)
        features['avg_confidence'] = aggregated.get('confidence', 0)
        
        # Regime features
        if market_regime:
            features['regime_trending'] = 1 if market_regime.get('regime') == 'trending' else 0
            features['regime_volatile'] = 1 if market_regime.get('regime') == 'volatile' else 0
        else:
            features['regime_trending'] = 0
            features['regime_volatile'] = 0
        
        # Convert to array
        feature_array = np.array([features.get(name, 0) for name in self.feature_names])
        return feature_array
    
    def _meta_predict(self, features: np.ndarray) -> float:
        """Get meta-learner prediction"""
        if self.scaler is not None:
            features = self.scaler.transform(features.reshape(1, -1))
        else:
            pass
        try:
            features = features.reshape(1, -1)
        
            prob = self.meta_model.predict_proba(features)[0, 1]
            return prob
        except Exception as e:
            logger.error(f"Meta prediction failed: {e}")
            return 0.5
    
    def add_training_sample(self, predictions: List[ModelPrediction],
                           market_regime: Dict[str, Any],
                           actual_return: float):
        """Add training sample for meta-learner"""
        aggregated = self.signal_aggregator.aggregate(predictions)
        features = self._extract_features(predictions, aggregated, market_regime)
        
        # Label: 1 if profitable, 0 otherwise
        label = 1 if actual_return > 0 else 0
        
        self.training_buffer.append({
            'features': features,
            'label': label,
            'return': actual_return,
        })
    
    def train_meta_learner(self, min_samples: int = 500):
        """Train the meta-learner on collected samples"""
        if len(self.training_buffer) < min_samples:
            logger.warning(f"Not enough samples for training: {len(self.training_buffer)}/{min_samples}")
            return False
        
        if self.meta_model is None:
            self._initialize_meta_model()
        
        if self.meta_model is None:
            return False
        
        # Prepare data
        X = np.array([s['features'] for s in self.training_buffer])
        y = np.array([s['label'] for s in self.training_buffer])
        
        # Scale features
        if self.scaler is not None:
            X = self.scaler.fit_transform(X)
        
        # Train
        try:
            self.meta_model.fit(X, y)
            self.is_trained = True
            
            # Cross-validation score
            if SKLEARN_AVAILABLE:
                scores = cross_val_score(self.meta_model, X, y, cv=5)
                logger.info(f"Meta-learner trained. CV accuracy: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
            
            return True
        except Exception as e:
            logger.error(f"Meta-learner training failed: {e}")
            return False
    
    def update_weights(self):
        """Update model weights based on performance"""
        self.weight_optimizer.update_weights()
    
    def record_outcome(self, symbol: str, timestamp: datetime,
                      actual_direction: str, actual_return: float):
        """Record actual outcome for all models"""
        for model_type in ModelType:
            self.weight_optimizer.record_outcome(
                model_type, symbol, timestamp, actual_direction, actual_return
            )
    
    def _empty_prediction(self) -> EnsemblePrediction:
        """Return empty prediction when no data available"""
        return EnsemblePrediction(
            timestamp=datetime.now(),
            symbol='',
            direction='neutral',
            probability=0.5,
            confidence=0,
            magnitude=0,
            model_agreement=0,
            contributing_models=[],
            model_weights={},
            individual_predictions={},
            should_trade=False,
            position_size_multiplier=0,
            reason='No predictions available',
        )
    
    def get_model_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all models"""
        return {
            model_type.value: self.weight_optimizer.tracker.get_model_metrics(model_type)
            for model_type in ModelType
        }
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current model weights"""
        return {k.value: v for k, v in self.weight_optimizer.weights.items()}
