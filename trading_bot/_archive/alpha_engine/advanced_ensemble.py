"""
Advanced Ensemble Meta-Learning Module
=======================================

Comprehensive ensemble architecture:
- Multi-level model stacking
- Dynamic weight adjustment based on performance
- Gradient boosting meta-learner
- Consensus engine with agreement requirements
- Adaptive model selection
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

# Try importing ML libraries
try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
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
    """Types of models in ensemble"""
    DC_ENGINE = "dc_engine"
    LOB_DEEP_LEARNING = "lob_deep_learning"
    LSTM_TREND = "lstm_trend"
    SENTIMENT = "sentiment"
    ALTERNATIVE_DATA = "alternative_data"
    REGIME_DETECTOR = "regime_detector"
    TECHNICAL = "technical"


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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsemblePrediction:
    """Combined prediction from ensemble"""
    timestamp: datetime
    symbol: str
    direction: str
    probability: float
    confidence: float
    should_trade: bool
    position_size_multiplier: float
    model_weights: Dict[str, float]
    agreement_ratio: float
    reason: str


@dataclass
class ModelPerformance:
    """Performance metrics for a model"""
    model_type: ModelType
    total_predictions: int
    correct_predictions: int
    accuracy: float
    sharpe_ratio: float
    win_rate: float
    avg_return: float
    max_drawdown: float
    recent_accuracy: float  # Last 30 days
    
    @property
    def composite_score(self) -> float:
        """Composite performance score"""
        return (
            self.sharpe_ratio * 0.3 +
            self.win_rate * 0.3 +
            self.recent_accuracy * 0.4
        )


class ModelPerformanceTracker:
    """
    Tracks performance of individual models
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Performance history per model
        self.predictions: Dict[ModelType, deque] = {
            mt: deque(maxlen=1000) for mt in ModelType
        }
        
        # Outcomes
        self.outcomes: Dict[ModelType, deque] = {
            mt: deque(maxlen=1000) for mt in ModelType
        }
        
        # Performance metrics
        self.performance: Dict[ModelType, ModelPerformance] = {}
    
    def record_prediction(self, prediction: ModelPrediction):
        """Record a model prediction"""
        self.predictions[prediction.model_type].append({
            'timestamp': prediction.timestamp,
            'symbol': prediction.symbol,
            'direction': prediction.direction,
            'probability': prediction.probability,
            'confidence': prediction.confidence,
        })
    
    def record_outcome(self, model_type: ModelType, timestamp: datetime,
                      predicted_direction: str, actual_return: float):
        """Record prediction outcome"""
        # Determine if prediction was correct
        if predicted_direction == 'long':
            correct = actual_return > 0
        elif predicted_direction == 'short':
            correct = actual_return < 0
        else:
            correct = abs(actual_return) < 0.001  # Neutral was correct if no move
        
        self.outcomes[model_type].append({
            'timestamp': timestamp,
            'predicted': predicted_direction,
            'actual_return': actual_return,
            'correct': correct,
        })
        
        # Update performance
        self._update_performance(model_type)
    
    def _update_performance(self, model_type: ModelType):
        """Update performance metrics for model"""
        outcomes = list(self.outcomes[model_type])
        
        if len(outcomes) < 10:
            return
        
        # Calculate metrics
        total = len(outcomes)
        correct = sum(1 for o in outcomes if o['correct'])
        accuracy = correct / total
        
        returns = [o['actual_return'] for o in outcomes]
        
        # Win rate (for directional predictions)
        directional = [o for o in outcomes if o['predicted'] != 'neutral']
        if directional:
            wins = sum(1 for o in directional if o['correct'])
            win_rate = wins / len(directional)
        else:
            win_rate = 0.5
        
        # Sharpe ratio
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_dd = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # Recent accuracy (last 30 predictions)
        recent = outcomes[-30:]
        recent_correct = sum(1 for o in recent if o['correct'])
        recent_accuracy = recent_correct / len(recent) if recent else 0
        
        self.performance[model_type] = ModelPerformance(
            model_type=model_type,
            total_predictions=total,
            correct_predictions=correct,
            accuracy=accuracy,
            sharpe_ratio=sharpe,
            win_rate=win_rate,
            avg_return=np.mean(returns),
            max_drawdown=max_dd,
            recent_accuracy=recent_accuracy,
        )
    
    def get_performance(self, model_type: ModelType) -> Optional[ModelPerformance]:
        """Get performance for model"""
        return self.performance.get(model_type)
    
    def get_all_performance(self) -> Dict[ModelType, ModelPerformance]:
        """Get performance for all models"""
        return self.performance.copy()


class DynamicWeightOptimizer:
    """
    Dynamically adjusts model weights based on recent performance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Base weights
        self.base_weights = {
            ModelType.DC_ENGINE: 0.30,
            ModelType.LOB_DEEP_LEARNING: 0.25,
            ModelType.LSTM_TREND: 0.20,
            ModelType.SENTIMENT: 0.15,
            ModelType.ALTERNATIVE_DATA: 0.10,
        }
        
        # Current weights
        self.current_weights = self.base_weights.copy()
        
        # Weight adjustment parameters
        self.adjustment_rate = self.config.get('adjustment_rate', 0.1)
        self.min_weight = self.config.get('min_weight', 0.05)
        self.max_weight = self.config.get('max_weight', 0.50)
        
        # Performance window
        self.performance_window = self.config.get('performance_window', 30)
    
    def update_weights(self, performance: Dict[ModelType, ModelPerformance]):
        """
        Update weights based on recent performance
        
        Uses exponential weight adjustment based on composite score
        """
        if not performance:
            return
        
        # Calculate composite scores
        scores = {}
        for model_type, perf in performance.items():
            if model_type in self.base_weights:
                scores[model_type] = perf.composite_score
        
        if not scores:
            return
        
        # Normalize scores
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score - min_score < 0.01:
            # All scores similar, use base weights
            return
        
        # Adjust weights
        new_weights = {}
        for model_type, base_weight in self.base_weights.items():
            if model_type in scores:
                score = scores[model_type]
                normalized_score = (score - min_score) / (max_score - min_score)
                
                # Exponential adjustment
                adjustment = (normalized_score - 0.5) * self.adjustment_rate
                new_weight = base_weight * (1 + adjustment)
                
                # Apply constraints
                new_weight = np.clip(new_weight, self.min_weight, self.max_weight)
                new_weights[model_type] = new_weight
            else:
                new_weights[model_type] = base_weight
        
        # Normalize to sum to 1
        total = sum(new_weights.values())
        self.current_weights = {k: v / total for k, v in new_weights.items()}
        
        logger.info(f"Updated ensemble weights: {self.current_weights}")
    
    def get_weights(self) -> Dict[ModelType, float]:
        """Get current weights"""
        return self.current_weights.copy()


class ConsensusEngine:
    """
    Determines consensus among model predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Consensus requirements
        self.min_agreement = self.config.get('min_agreement', 3)  # Minimum models agreeing
        self.min_agreement_ratio = self.config.get('min_agreement_ratio', 0.6)
        self.min_confidence = self.config.get('min_confidence', 0.6)
    
    def calculate_consensus(self, predictions: List[ModelPrediction],
                           weights: Dict[ModelType, float]) -> Dict[str, Any]:
        """
        Calculate consensus from predictions
        
        Args:
            predictions: List of model predictions
            weights: Model weights
            
        Returns:
            Consensus result
        """
        if not predictions:
            return {
                'has_consensus': False,
                'direction': 'neutral',
                'agreement_ratio': 0,
                'weighted_probability': 0.5,
            }
        
        # Count directions
        direction_counts = {'long': 0, 'short': 0, 'neutral': 0}
        weighted_probs = {'long': 0, 'short': 0, 'neutral': 0}
        total_weight = 0
        
        for pred in predictions:
            weight = weights.get(pred.model_type, 0.1)
            direction_counts[pred.direction] += 1
            weighted_probs[pred.direction] += pred.probability * weight * pred.confidence
            total_weight += weight * pred.confidence
        
        # Normalize
        if total_weight > 0:
            for d in weighted_probs:
                weighted_probs[d] /= total_weight
        
        # Determine consensus direction
        max_count = max(direction_counts.values())
        consensus_direction = max(direction_counts, key=direction_counts.get)
        
        # Calculate agreement ratio
        agreement_ratio = max_count / len(predictions)
        
        # Check if consensus is strong enough
        has_consensus = (
            max_count >= self.min_agreement and
            agreement_ratio >= self.min_agreement_ratio
        )
        
        return {
            'has_consensus': has_consensus,
            'direction': consensus_direction,
            'agreement_ratio': agreement_ratio,
            'direction_counts': direction_counts,
            'weighted_probability': weighted_probs[consensus_direction],
            'all_probabilities': weighted_probs,
        }


class MetaLearner:
    """
    Meta-learner that combines base model predictions
    
    Uses gradient boosting to learn optimal combination
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize meta-model
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # Training data
        self.training_features: List[np.ndarray] = []
        self.training_labels: List[int] = []
        
        # Minimum samples for training
        self.min_samples = self.config.get('min_samples', 100)
        
        # Model type
        self.model_type = self.config.get('model_type', 'xgboost')
        
        self.is_trained = False
    
    def _create_features(self, predictions: List[ModelPrediction],
                        market_regime: str = 'normal') -> np.ndarray:
        """Create feature vector from predictions"""
        features = []
        
        # Model predictions
        model_order = list(ModelType)
        for mt in model_order:
            pred = next((p for p in predictions if p.model_type == mt), None)
            if pred:
                # Direction encoding
                if pred.direction == 'long':
                    dir_enc = 1
                elif pred.direction == 'short':
                    dir_enc = -1
                else:
                    dir_enc = 0
                
                features.extend([
                    dir_enc,
                    pred.probability,
                    pred.confidence,
                    pred.magnitude,
                ])
            else:
                features.extend([0, 0.5, 0, 0])
        
        # Market regime encoding
        regime_map = {'trending': 1, 'ranging': 0, 'volatile': -1, 'normal': 0.5}
        features.append(regime_map.get(market_regime, 0.5))
        
        return np.array(features)
    
    def add_training_sample(self, predictions: List[ModelPrediction],
                           actual_direction: str, market_regime: str = 'normal'):
        """Add training sample"""
        features = self._create_features(predictions, market_regime)
        
        # Label encoding
        if actual_direction == 'long':
            label = 2
        elif actual_direction == 'short':
            label = 0
        else:
            label = 1
        
        self.training_features.append(features)
        self.training_labels.append(label)
        
        # Retrain if enough samples
        if len(self.training_features) >= self.min_samples and len(self.training_features) % 50 == 0:
            self.train()
    
    def train(self):
        """Train meta-learner"""
        if len(self.training_features) < self.min_samples:
            logger.warning(f"Insufficient samples for training: {len(self.training_features)}")
            return
        
        X = np.array(self.training_features)
        y = np.array(self.training_labels)
        
        # Scale features
        if self.scaler:
            X = self.scaler.fit_transform(X)
        
        # Create model
        if XGBOOST_AVAILABLE and self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                objective='multi:softprob',
                num_class=3,
            )
        elif LIGHTGBM_AVAILABLE and self.model_type == 'lightgbm':
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                objective='multiclass',
                num_class=3,
            )
        elif SKLEARN_AVAILABLE:
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
            )
        else:
            pass
        try:
            logger.warning("No ML library available for meta-learner")
            return
        
        # Train
            self.model.fit(X, y)
            self.is_trained = True
            logger.info(f"Meta-learner trained on {len(X)} samples")
        except Exception as e:
            logger.error(f"Meta-learner training failed: {e}")
    
    def predict(self, predictions: List[ModelPrediction],
               market_regime: str = 'normal') -> Dict[str, Any]:
        """Make prediction using meta-learner"""
        if not self.is_trained or self.model is None:
            return {
                'direction': 'neutral',
                'probabilities': [0.33, 0.34, 0.33],
                'confidence': 0,
                'method': 'fallback',
            }
        
        features = self._create_features(predictions, market_regime)
        
        if self.scaler:
            features = self.scaler.transform(features.reshape(1, -1))
        else:
            pass
        try:
            features = features.reshape(1, -1)
        
            probs = self.model.predict_proba(features)[0]
            pred_class = np.argmax(probs)
            
            directions = ['short', 'neutral', 'long']
            direction = directions[pred_class]
            
            return {
                'direction': direction,
                'probabilities': probs.tolist(),
                'confidence': float(probs[pred_class]),
                'method': 'meta_learner',
            }
        except Exception as e:
            logger.error(f"Meta-learner prediction failed: {e}")
            return {
                'direction': 'neutral',
                'probabilities': [0.33, 0.34, 0.33],
                'confidence': 0,
                'method': 'fallback',
            }


class AdvancedEnsembleMetaLearner:
    """
    Advanced ensemble system with meta-learning
    
    Features:
    - Level 1: Base model predictions
    - Level 2: Meta-learner combination
    - Dynamic weight adjustment
    - Consensus requirements
    - Override logic for extreme conditions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.performance_tracker = ModelPerformanceTracker(config.get('performance', {}))
        self.weight_optimizer = DynamicWeightOptimizer(config.get('weights', {}))
        self.consensus_engine = ConsensusEngine(config.get('consensus', {}))
        self.meta_learner = MetaLearner(config.get('meta_learner', {}))
        
        # Prediction history
        self.prediction_history: deque = deque(maxlen=1000)
        
        # Configuration
        self.require_consensus = self.config.get('require_consensus', True)
        self.use_meta_learner = self.config.get('use_meta_learner', True)
        self.min_confidence = self.config.get('min_confidence', 0.6)
    
    def predict(self, predictions: List[ModelPrediction],
               market_regime: str = 'normal') -> EnsemblePrediction:
        """
        Generate ensemble prediction
        
        Args:
            predictions: List of base model predictions
            market_regime: Current market regime
            
        Returns:
            EnsemblePrediction
        """
        if not predictions:
            return self._neutral_prediction("No predictions available")
        
        # Record predictions
        for pred in predictions:
            self.performance_tracker.record_prediction(pred)
        
        # Get current weights
        weights = self.weight_optimizer.get_weights()
        
        # Calculate consensus
        consensus = self.consensus_engine.calculate_consensus(predictions, weights)
        
        # Use meta-learner if available
        if self.use_meta_learner and self.meta_learner.is_trained:
            meta_pred = self.meta_learner.predict(predictions, market_regime)
            
            # Combine meta-learner with consensus
            if meta_pred['confidence'] > 0.6:
                direction = meta_pred['direction']
                probability = meta_pred['confidence']
                method = 'meta_learner'
            else:
                direction = consensus['direction']
                probability = consensus['weighted_probability']
                method = 'consensus'
        else:
            direction = consensus['direction']
            probability = consensus['weighted_probability']
            method = 'consensus'
        
        # Check if should trade
        should_trade = (
            consensus['has_consensus'] and
            probability >= self.min_confidence and
            direction != 'neutral'
        )
        
        # Calculate position size multiplier
        if should_trade:
            # Higher confidence = larger position
            base_multiplier = 0.5 + probability * 0.5
            
            # Adjust for agreement
            agreement_bonus = consensus['agreement_ratio'] * 0.2
            
            position_multiplier = min(base_multiplier + agreement_bonus, 1.5)
        else:
            position_multiplier = 0
        
        # Create prediction
        ensemble_pred = EnsemblePrediction(
            timestamp=datetime.now(),
            symbol=predictions[0].symbol if predictions else '',
            direction=direction,
            probability=probability,
            confidence=probability,
            should_trade=should_trade,
            position_size_multiplier=position_multiplier,
            model_weights={mt.value: w for mt, w in weights.items()},
            agreement_ratio=consensus['agreement_ratio'],
            reason=f"{method}: {direction} with {probability:.1%} confidence, {consensus['agreement_ratio']:.1%} agreement",
        )
        
        self.prediction_history.append(ensemble_pred)
        
        return ensemble_pred
    
    def _neutral_prediction(self, reason: str) -> EnsemblePrediction:
        """Create neutral prediction"""
        return EnsemblePrediction(
            timestamp=datetime.now(),
            symbol='',
            direction='neutral',
            probability=0.5,
            confidence=0,
            should_trade=False,
            position_size_multiplier=0,
            model_weights={},
            agreement_ratio=0,
            reason=reason,
        )
    
    def record_outcome(self, symbol: str, timestamp: datetime,
                      actual_direction: str, actual_return: float):
        """Record prediction outcome for learning"""
        # Find corresponding predictions
        recent_preds = [
            p for p in self.prediction_history
            if p.symbol == symbol and 
            abs((p.timestamp - timestamp).total_seconds()) < 3600
        ]
        
        if not recent_preds:
            return
        
        # Update performance tracker
        for mt in ModelType:
            self.performance_tracker.record_outcome(
                mt, timestamp, actual_direction, actual_return
            )
        
        # Update meta-learner
        # Would need to store original predictions
        
        # Update weights
        performance = self.performance_tracker.get_all_performance()
        self.weight_optimizer.update_weights(performance)
    
    def update_weights(self):
        """Manually trigger weight update"""
        performance = self.performance_tracker.get_all_performance()
        self.weight_optimizer.update_weights(performance)
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current model weights"""
        weights = self.weight_optimizer.get_weights()
        return {mt.value: w for mt, w in weights.items()}
    
    def get_model_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all models"""
        performance = self.performance_tracker.get_all_performance()
        
        return {
            mt.value: {
                'accuracy': perf.accuracy,
                'sharpe_ratio': perf.sharpe_ratio,
                'win_rate': perf.win_rate,
                'recent_accuracy': perf.recent_accuracy,
                'composite_score': perf.composite_score,
            }
            for mt, perf in performance.items()
        }
