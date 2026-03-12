"""
Skill #28: Model Ensemble Stacker
=================================

Combines multiple models using stacking and blending
for improved prediction accuracy.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelPrediction:
    """Prediction from a single model."""
    model_name: str
    prediction: float
    confidence: float
    weight: float


@dataclass
class EnsembleResult:
    """Ensemble stacking result."""
    final_prediction: float
    model_predictions: List[ModelPrediction]
    model_weights: Dict[str, float]
    diversity_score: float
    ensemble_confidence: float
    trading_signal: str


class ModelEnsembleStacker:
    """Ensemble stacking for combining multiple models."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.meta_learner_weights = np.random.randn(10) * 0.1
            self.model_performance: Dict[str, List[float]] = {}
            logger.info("ModelEnsembleStacker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def predict(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        base_predictions: Optional[Dict[str, float]] = None
    ) -> EnsembleResult:
        """Generate ensemble prediction."""
        try:
            if len(prices) < 20:
                return self._create_empty_result()
        
            # Get base model predictions
            if base_predictions is None:
                base_predictions = self._generate_base_predictions(prices, volumes)
        
            # Calculate model weights
            weights = self._calculate_weights(base_predictions)
        
            # Stack predictions
            model_preds = []
            for name, pred in base_predictions.items():
                conf = self._estimate_confidence(name, pred)
                model_preds.append(ModelPrediction(
                    model_name=name,
                    prediction=pred,
                    confidence=conf,
                    weight=weights.get(name, 1.0 / len(base_predictions))
                ))
        
            # Meta-learner combination
            final_pred = self._meta_predict(model_preds)
        
            # Calculate diversity
            diversity = self._calculate_diversity(base_predictions)
        
            # Ensemble confidence
            ensemble_conf = self._calculate_ensemble_confidence(model_preds, diversity)
        
            signal = self._generate_signal(final_pred, ensemble_conf)
        
            return EnsembleResult(
                final_prediction=final_pred,
                model_predictions=model_preds,
                model_weights=weights,
                diversity_score=diversity,
                ensemble_confidence=ensemble_conf,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def _generate_base_predictions(
        self,
        prices: np.ndarray,
        volumes: np.ndarray
    ) -> Dict[str, float]:
        """Generate predictions from base models."""
        try:
            returns = np.diff(prices) / prices[:-1]
        
            predictions = {
                'momentum': np.mean(returns[-5:]) * 10,
                'mean_reversion': -np.mean(returns[-5:]) * 5,
                'trend_following': np.sign(prices[-1] - prices[-20]) * 0.02,
                'volatility': np.std(returns[-10:]) * np.sign(returns[-1]),
                'volume_weighted': np.mean(returns[-5:] * volumes[-5:] / np.mean(volumes)) * 10,
            }
        
            return predictions
        except Exception as e:
            logger.error(f"Error in _generate_base_predictions: {e}")
            raise
    
    def _calculate_weights(self, predictions: Dict[str, float]) -> Dict[str, float]:
        """Calculate model weights based on historical performance."""
        try:
            weights = {}
            total_perf = 0
        
            for name in predictions:
                if name in self.model_performance and self.model_performance[name]:
                    perf = np.mean(self.model_performance[name][-20:])
                    perf = max(0.1, perf + 1)  # Ensure positive
                else:
                    perf = 1.0
                weights[name] = perf
                total_perf += perf
        
            # Normalize
            return {k: v / total_perf for k, v in weights.items()}
        except Exception as e:
            logger.error(f"Error in _calculate_weights: {e}")
            raise
    
    def _estimate_confidence(self, model_name: str, prediction: float) -> float:
        """Estimate confidence for a model prediction."""
        try:
            if model_name in self.model_performance:
                history = self.model_performance[model_name]
                if len(history) > 5:
                    accuracy = np.mean([1 if h > 0 else 0 for h in history[-10:]])
                    return accuracy
            return 0.5
        except Exception as e:
            logger.error(f"Error in _estimate_confidence: {e}")
            raise
    
    def _meta_predict(self, predictions: List[ModelPrediction]) -> float:
        """Combine predictions using meta-learner."""
        try:
            weighted_sum = sum(p.prediction * p.weight for p in predictions)
            return float(np.clip(weighted_sum, -0.1, 0.1))
        except Exception as e:
            logger.error(f"Error in _meta_predict: {e}")
            raise
    
    def _calculate_diversity(self, predictions: Dict[str, float]) -> float:
        """Calculate diversity among model predictions."""
        try:
            preds = list(predictions.values())
            if len(preds) < 2:
                return 0.0
        
            # Correlation-based diversity
            std = np.std(preds)
            mean_abs = np.mean(np.abs(preds))
        
            if mean_abs == 0:
                return 0.0
        
            return min(1.0, std / mean_abs)
        except Exception as e:
            logger.error(f"Error in _calculate_diversity: {e}")
            raise
    
    def _calculate_ensemble_confidence(
        self,
        predictions: List[ModelPrediction],
        diversity: float
    ) -> float:
        """Calculate ensemble confidence."""
        # Agreement among models
        try:
            signs = [np.sign(p.prediction) for p in predictions]
            agreement = abs(np.mean(signs))
        
            # Weighted confidence
            weighted_conf = sum(p.confidence * p.weight for p in predictions)
        
            # Higher diversity with agreement = higher confidence
            return min(0.95, weighted_conf * (0.5 + 0.5 * agreement))
        except Exception as e:
            logger.error(f"Error in _calculate_ensemble_confidence: {e}")
            raise
    
    def update_performance(self, model_name: str, actual_return: float, predicted_return: float):
        """Update model performance history."""
        try:
            if model_name not in self.model_performance:
                self.model_performance[model_name] = []
        
            # Score: positive if prediction direction was correct
            score = 1 if np.sign(actual_return) == np.sign(predicted_return) else -1
            self.model_performance[model_name].append(score)
        
            # Keep last 100
            if len(self.model_performance[model_name]) > 100:
                self.model_performance[model_name] = self.model_performance[model_name][-100:]
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise
    
    def _generate_signal(self, prediction: float, confidence: float) -> str:
        """Generate trading signal."""
        try:
            if confidence < 0.4:
                return f"LOW CONFIDENCE ({confidence:.0%}): Ensemble disagreement"
        
            if prediction > 0.02:
                return f"BUY: Ensemble predicts +{prediction:.1%} ({confidence:.0%} confidence)"
            elif prediction < -0.02:
                return f"SELL: Ensemble predicts {prediction:.1%} ({confidence:.0%} confidence)"
            return f"NEUTRAL: Ensemble predicts {prediction:.1%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> EnsembleResult:
        """Create empty result."""
        return EnsembleResult(
            final_prediction=0,
            model_predictions=[],
            model_weights={},
            diversity_score=0,
            ensemble_confidence=0,
            trading_signal="Insufficient data"
        )
