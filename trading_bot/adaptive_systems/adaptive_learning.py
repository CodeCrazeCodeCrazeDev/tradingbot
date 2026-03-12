import logging
logger = logging.getLogger(__name__)
"""Adaptive Learning and Model Retraining System.

This module implements continuous model retraining and adaptive learning
capabilities that evolve the bot's intelligence over time.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
import threading
import queue
import numpy
import pandas


class ModelType(Enum):
    """Types of models for retraining."""
    PRICE_PREDICTOR = "price_predictor"
    REGIME_CLASSIFIER = "regime_classifier"
    RISK_ESTIMATOR = "risk_estimator"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    STRATEGY_SELECTOR = "strategy_selector"


@dataclass
class ModelPerformance:
    """Model performance tracking."""
    model_type: ModelType
    accuracy: float
    last_retrain: datetime
    training_samples: int
    validation_score: float
    improvement_rate: float
    retrain_count: int = 0
    performance_history: List[float] = field(default_factory=list)


class AdaptiveLearningEngine:
    """Continuous learning and model retraining system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the adaptive learning engine."""
        self.config = config or {}
        self.models = {}
        self.model_performance = {}
        self.training_queue = queue.Queue()
        self.retraining_active = False
        
        # Learning parameters
        self.retrain_threshold = self.config.get('retrain_threshold', 0.05)  # 5% performance drop
        self.min_samples_retrain = self.config.get('min_samples_retrain', 100)
        self.retrain_frequency_hours = self.config.get('retrain_frequency_hours', 24)
        
        # Data storage
        self.training_data = {model_type: [] for model_type in ModelType}
        self.feature_importance = {}
        
        # Initialize models
        self._initialize_models()
        
        logger.info("AdaptiveLearningEngine initialized")
    
    def _initialize_models(self):
        """Initialize machine learning models."""
        # Price prediction model
        self.models[ModelType.PRICE_PREDICTOR] = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        
        # Market regime classifier
        self.models[ModelType.REGIME_CLASSIFIER] = GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, random_state=42
        )
        
        # Risk estimation model
        self.models[ModelType.RISK_ESTIMATOR] = MLPRegressor(
            hidden_layer_sizes=(50, 25), max_iter=500, random_state=42
        )
        
        # Initialize performance tracking
        for model_type in ModelType:
            self.model_performance[model_type] = ModelPerformance(
                model_type=model_type,
                accuracy=0.5,
                last_retrain=datetime.now(),
                training_samples=0,
                validation_score=0.0,
                improvement_rate=0.0
            )
    
    def add_training_sample(self, model_type: ModelType, features: List[float], 
                           target: float, metadata: Optional[Dict] = None):
        """Add a new training sample for a model.
        
        Args:
            model_type: Type of model to train
            features: Feature vector
            target: Target value
            metadata: Additional metadata
        """
        sample = {
            'features': features,
            'target': target,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        
        self.training_data[model_type].append(sample)
        
        # Keep only recent samples
        max_samples = self.config.get('max_training_samples', 10000)
        if len(self.training_data[model_type]) > max_samples:
            self.training_data[model_type] = self.training_data[model_type][-max_samples:]
        
        # Check if retraining is needed
        self._check_retrain_trigger(model_type)
    
    def _check_retrain_trigger(self, model_type: ModelType):
        """Check if model retraining should be triggered."""
        perf = self.model_performance[model_type]
        data_count = len(self.training_data[model_type])
        
        # Trigger conditions
        should_retrain = False
        
        # Minimum samples reached
        if data_count >= self.min_samples_retrain and perf.training_samples == 0:
            should_retrain = True
            
        # Performance degradation
        if len(perf.performance_history) >= 10:
            recent_avg = np.mean(perf.performance_history[-5:])
            older_avg = np.mean(perf.performance_history[-10:-5])
            if recent_avg < older_avg - self.retrain_threshold:
                should_retrain = True
        
        # Time-based retraining
        time_since_retrain = datetime.now() - perf.last_retrain
        if time_since_retrain.total_seconds() > self.retrain_frequency_hours * 3600:
            should_retrain = True
        
        if should_retrain and data_count >= self.min_samples_retrain:
            self._queue_retraining(model_type)
    
    def _queue_retraining(self, model_type: ModelType):
        """Queue a model for retraining."""
        if not self.training_queue.empty():
            # Check if already queued
            temp_queue = []
            already_queued = False
            
            while not self.training_queue.empty():
                item = self.training_queue.get()
                if item == model_type:
                    already_queued = True
                temp_queue.append(item)
            
            # Restore queue
            for item in temp_queue:
                self.training_queue.put(item)
            
            if already_queued:
                return
        
        self.training_queue.put(model_type)
        logger.info(f"Queued {model_type.value} for retraining")
        
        # Start retraining thread if not active
        if not self.retraining_active:
            self._start_retraining_thread()
    
    def _start_retraining_thread(self):
        """Start the model retraining thread."""
        def retraining_worker():
            """
            retraining_worker function.

    Auto-documented by QwenCodeMender.
            """
            self.retraining_active = True
            
            while not self.training_queue.empty():
                try:
                    model_type = self.training_queue.get(timeout=1)
                    self._retrain_model(model_type)
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error in retraining worker: {e}")
            
            self.retraining_active = False
        
        thread = threading.Thread(target=retraining_worker, daemon=True)
        thread.start()
    
    def _retrain_model(self, model_type: ModelType):
        """Retrain a specific model."""
        logger.info(f"Starting retraining for {model_type.value}")
        
        try:
            # Prepare training data
            X, y = self._prepare_training_data(model_type)
            
            if len(X) < self.min_samples_retrain:
                logger.warning(f"Insufficient data for {model_type.value}: {len(X)}")
                return
            
            # Split data chronologically
            split_point = int(len(X) * 0.8)
            X_train, X_test = X[:split_point], X[split_point:]
            y_train, y_test = y[:split_point], y[split_point:]
            
            # Train model
            model = self.models[model_type]
            model.fit(X_train, y_train)
            
            # Evaluate performance
            if model_type in [ModelType.REGIME_CLASSIFIER, ModelType.STRATEGY_SELECTOR]:
                score = accuracy_score(y_test, model.predict(X_test))
            else:
                predictions = model.predict(X_test)
                score = 1.0 / (1.0 + mean_squared_error(y_test, predictions))
            
            # Update performance tracking
            perf = self.model_performance[model_type]
            old_score = perf.accuracy
            perf.accuracy = score
            perf.last_retrain = datetime.now()
            perf.training_samples = len(X)
            perf.retrain_count += 1
            perf.improvement_rate = (score - old_score) / (old_score + 1e-6)
            perf.performance_history.append(score)
            
            # Keep performance history manageable
            if len(perf.performance_history) > 100:
                perf.performance_history = perf.performance_history[-50:]
            
            # Update feature importance
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[model_type] = model.feature_importances_.tolist()
            
            # Save model
            self._save_model(model_type, model)
            
            logger.info(f"Retrained {model_type.value}: accuracy={score:.3f}, "
                       f"improvement={perf.improvement_rate:.3f}")
            
        except Exception as e:
            logger.error(f"Error retraining {model_type.value}: {e}")
    
    def _prepare_training_data(self, model_type: ModelType) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for a model."""
        samples = self.training_data[model_type]
        
        if not samples:
            return np.array([]), np.array([])
        
        # Extract features and targets
        X = np.array([sample['features'] for sample in samples])
        y = np.array([sample['target'] for sample in samples])
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        y = np.nan_to_num(y, nan=0.0)
        
        return X, y
    
    def _save_model(self, model_type: ModelType, model):
        """Save a trained model to disk."""
        try:
            filename = f"models/{model_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            joblib.dump(model, filename)
            logger.debug(f"Saved model {model_type.value} to {filename}")
        except Exception as e:
            logger.warning(f"Could not save model {model_type.value}: {e}")
    
    def predict(self, model_type: ModelType, features: List[float]) -> Optional[float]:
        """Make a prediction using a trained model."""
        if model_type not in self.models:
            return None
        try:
        
            model = self.models[model_type]
            features_array = np.array(features).reshape(1, -1)
            prediction = model.predict(features_array)[0]
            
            # Update model performance tracking
            # (In real implementation, you'd compare with actual outcomes later)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction with {model_type.value}: {e}")
            return None
    
    def get_model_insights(self, model_type: ModelType) -> Dict[str, Any]:
        """Get insights about a model's performance and behavior."""
        if model_type not in self.model_performance:
            return {}
        
        perf = self.model_performance[model_type]
        insights = {
            'accuracy': perf.accuracy,
            'training_samples': perf.training_samples,
            'retrain_count': perf.retrain_count,
            'improvement_rate': perf.improvement_rate,
            'last_retrain': perf.last_retrain.isoformat(),
            'performance_trend': 'improving' if perf.improvement_rate > 0 else 'declining'
        }
        
        # Add feature importance if available
        if model_type in self.feature_importance:
            insights['feature_importance'] = self.feature_importance[model_type]
        
        # Performance stability
        if len(perf.performance_history) >= 5:
            stability = np.std(perf.performance_history[-5:])
            insights['stability'] = 'stable' if stability < 0.05 else 'unstable'
        
        return insights
    
    def force_retrain_all(self):
        """Force retraining of all models."""
        logger.info("Forcing retraining of all models")
        
        for model_type in ModelType:
            if len(self.training_data[model_type]) >= self.min_samples_retrain:
                self._queue_retraining(model_type)
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning system status."""
        status = {
            'retraining_active': self.retraining_active,
            'queued_models': self.training_queue.qsize(),
            'models': {}
        }
        
        for model_type, perf in self.model_performance.items():
            status['models'][model_type.value] = {
                'accuracy': perf.accuracy,
                'training_samples': perf.training_samples,
                'data_available': len(self.training_data[model_type]),
                'retrain_count': perf.retrain_count,
                'last_retrain': perf.last_retrain.isoformat(),
                'needs_retrain': len(self.training_data[model_type]) >= self.min_samples_retrain
            }
        
        return status
