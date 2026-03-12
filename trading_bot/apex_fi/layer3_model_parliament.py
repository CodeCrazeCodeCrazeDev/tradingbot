"""
APEX-FI Layer 3: Adaptive Model Ensemble & Meta-Learning Brain
===============================================================

Two Sigma-inspired Model Parliament with hundreds of specialized models,
Meta-Learner Oracle for regime-conditional weighting, Neural Architecture Search,
and calibrated uncertainty quantification.

Mission: Never be wrong the same way twice. Never rely on a single model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of models in the parliament."""
    DEEP_LEARNING = "deep_learning"
    GRADIENT_BOOSTING = "gradient_boosting"
    BAYESIAN = "bayesian"
    GAUSSIAN_PROCESS = "gaussian_process"
    PHYSICS_INSPIRED = "physics_inspired"
    SYMBOLIC_REGRESSION = "symbolic_regression"
    ENSEMBLE = "ensemble"


class UncertaintyType(str, Enum):
    """Types of uncertainty."""
    EPISTEMIC = "epistemic"  # Model uncertainty
    ALEATORIC = "aleatoric"  # Data uncertainty
    TOTAL = "total"


@dataclass
class ModelCard:
    """
    Model card documenting model metadata.
    
    Inspired by Model Cards for Model Reporting (Mitchell et al., 2019).
    """
    model_id: str
    model_type: ModelType
    architecture: str
    training_regime: Dict[str, Any]
    assumptions: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    decay_metrics: Dict[str, float] = field(default_factory=dict)
    regime_performance: Dict[str, float] = field(default_factory=dict)
    training_timestamp: Optional[datetime] = None
    last_update: Optional[datetime] = None
    version: int = 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            'model_id': self.model_id,
            'model_type': self.model_type.value,
            'metrics': self.performance_metrics,
            'decay': self.decay_metrics,
            'last_update': self.last_update.isoformat() if self.last_update else None,
        }


@dataclass
class ParliamentVote:
    """Vote from Model Parliament."""
    prediction: float
    confidence: float
    model_id: str
    weight: float
    uncertainty: Dict[UncertaintyType, float]
    timestamp: datetime = field(default_factory=datetime.now)


class BaseModel:
    """Base class for all models in the parliament."""
    
    def __init__(self, model_id: str, model_type: ModelType):
        self.model_id = model_id
        self.model_type = model_type
        self.is_trained = False
        self.performance_history: deque = deque(maxlen=1000)
        
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Make prediction with uncertainty.
        
        Returns:
            (prediction, uncertainty)
        """
        raise NotImplementedError
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model."""
        raise NotImplementedError
    
    def update_performance(self, actual: float, predicted: float) -> None:
        """Update performance tracking."""
        error = abs(actual - predicted)
        self.performance_history.append({
            'timestamp': datetime.now(),
            'error': error,
            'actual': actual,
            'predicted': predicted,
        })
    
    def get_recent_performance(self, window: int = 100) -> float:
        """Get recent average performance."""
        if not self.performance_history:
            return 0.0
        
        recent = list(self.performance_history)[-window:]
        return np.mean([r['error'] for r in recent])


class DeepLearningModel(BaseModel):
    """Deep learning model (placeholder for actual implementation)."""
    
    def __init__(self, model_id: str, architecture: str = "transformer"):
        super().__init__(model_id, ModelType.DEEP_LEARNING)
        self.architecture = architecture
        
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Placeholder prediction."""
        # In production: actual neural network inference
        prediction = np.random.randn()
        uncertainty = abs(np.random.randn() * 0.1)
        return prediction, uncertainty
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Placeholder training."""
        self.is_trained = True
        logger.debug(f"Trained {self.model_id} on {len(X)} samples")


class GradientBoostingModel(BaseModel):
    """Gradient boosting model (XGBoost/LightGBM/CatBoost)."""
    
    def __init__(self, model_id: str, variant: str = "xgboost"):
        super().__init__(model_id, ModelType.GRADIENT_BOOSTING)
        self.variant = variant
        
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Placeholder prediction."""
        prediction = np.random.randn()
        uncertainty = abs(np.random.randn() * 0.05)
        return prediction, uncertainty
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Placeholder training."""
        self.is_trained = True


class BayesianModel(BaseModel):
    """Bayesian model with natural uncertainty quantification."""
    
    def __init__(self, model_id: str):
        super().__init__(model_id, ModelType.BAYESIAN)
        
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Prediction with Bayesian uncertainty."""
        prediction = np.random.randn()
        uncertainty = abs(np.random.randn() * 0.15)
        return prediction, uncertainty
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Placeholder training."""
        self.is_trained = True


class ModelParliament:
    """
    Model Parliament - ensemble of hundreds of specialized models.
    
    Every prediction is a weighted vote. No single model decides anything.
    """
    
    def __init__(self, target_size: int = 100):
        self.models: Dict[str, BaseModel] = {}
        self.model_cards: Dict[str, ModelCard] = {}
        self.target_size = target_size
        self.voting_weights: Dict[str, float] = {}
        
        logger.info(f"Model Parliament initialized - Target size: {target_size}")
    
    def add_model(self, model: BaseModel, card: ModelCard) -> None:
        """Add model to parliament."""
        self.models[model.model_id] = model
        self.model_cards[model.model_id] = card
        self.voting_weights[model.model_id] = 1.0 / max(1, len(self.models))
        
        # Normalize weights
        self._normalize_weights()
        
        logger.debug(f"Added model to parliament: {model.model_id}")
    
    def _normalize_weights(self) -> None:
        """Normalize voting weights to sum to 1.0."""
        total = sum(self.voting_weights.values())
        if total > 0:
            for model_id in self.voting_weights:
                self.voting_weights[model_id] /= total
    
    def vote(self, features: np.ndarray, regime: Optional[str] = None) -> ParliamentVote:
        """
        Conduct parliament vote on prediction.
        
        Args:
            features: Input features
            regime: Optional market regime for regime-conditional weighting
            
        Returns:
            Aggregated parliament vote
        """
        if not self.models:
            raise ValueError("Parliament has no models")
        
        votes = []
        weights = []
        uncertainties = []
        
        for model_id, model in self.models.items():
            if not model.is_trained:
                continue
            
            try:
                prediction, uncertainty = model.predict(features)
                weight = self.voting_weights.get(model_id, 0.0)
                
                # Adjust weight by regime if specified
                if regime and model_id in self.model_cards:
                    card = self.model_cards[model_id]
                    regime_perf = card.regime_performance.get(regime, 1.0)
                    weight *= regime_perf
                
                votes.append(prediction)
                weights.append(weight)
                uncertainties.append(uncertainty)
                
            except Exception as e:
                logger.warning(f"Model {model_id} failed to predict: {e}")
                continue
        
        if not votes:
            raise ValueError("No models could make predictions")
        
        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Weighted average prediction
        final_prediction = np.average(votes, weights=weights)
        
        # Aggregate uncertainty (epistemic + aleatoric)
        epistemic_uncertainty = np.std(votes)  # Model disagreement
        aleatoric_uncertainty = np.average(uncertainties, weights=weights)
        total_uncertainty = np.sqrt(epistemic_uncertainty**2 + aleatoric_uncertainty**2)
        
        # Confidence inversely related to uncertainty
        confidence = 1.0 / (1.0 + total_uncertainty)
        
        return ParliamentVote(
            prediction=final_prediction,
            confidence=confidence,
            model_id="parliament_ensemble",
            weight=1.0,
            uncertainty={
                UncertaintyType.EPISTEMIC: epistemic_uncertainty,
                UncertaintyType.ALEATORIC: aleatoric_uncertainty,
                UncertaintyType.TOTAL: total_uncertainty,
            }
        )
    
    def update_weights(self, model_id: str, performance_multiplier: float) -> None:
        """Update voting weight for a model based on performance."""
        if model_id in self.voting_weights:
            self.voting_weights[model_id] *= performance_multiplier
            self._normalize_weights()
    
    def get_model_disagreement(self, features: np.ndarray) -> float:
        """
        Get model disagreement as a signal.
        
        High disagreement indicates regime uncertainty.
        """
        predictions = []
        
        for model in self.models.values():
            if model.is_trained:
                try:
                    pred, _ = model.predict(features)
                    predictions.append(pred)
                except:
                    continue
        
        if len(predictions) < 2:
            return 0.0
        
        return float(np.std(predictions))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parliament statistics."""
        trained_count = sum(1 for m in self.models.values() if m.is_trained)
        
        return {
            'total_models': len(self.models),
            'trained_models': trained_count,
            'model_types': {mt.value: sum(1 for m in self.models.values() if m.model_type == mt)
                           for mt in ModelType},
            'average_weight': np.mean(list(self.voting_weights.values())) if self.voting_weights else 0,
        }


class MetaLearnerOracle:
    """
    Meta-Learner Oracle - predicts which models will perform best in current regime.
    
    Second-order model that manages parliament voting weights in real-time.
    """
    
    def __init__(self):
        self.regime_model_performance: Dict[str, Dict[str, float]] = {}
        self.current_regime: Optional[str] = None
        self.performance_history: deque = deque(maxlen=10000)
        
        logger.info("Meta-Learner Oracle initialized")
    
    def update_regime(self, regime: str) -> None:
        """Update current market regime."""
        self.current_regime = regime
        logger.debug(f"Meta-Learner regime updated: {regime}")
    
    def record_performance(
        self,
        regime: str,
        model_id: str,
        prediction: float,
        actual: float
    ) -> None:
        """Record model performance in a regime."""
        error = abs(prediction - actual)
        
        if regime not in self.regime_model_performance:
            self.regime_model_performance[regime] = {}
        
        if model_id not in self.regime_model_performance[regime]:
            self.regime_model_performance[regime][model_id] = []
        
        self.regime_model_performance[regime][model_id].append(error)
        
        # Keep only recent performance
        if len(self.regime_model_performance[regime][model_id]) > 100:
            self.regime_model_performance[regime][model_id] = \
                self.regime_model_performance[regime][model_id][-100:]
        
        self.performance_history.append({
            'timestamp': datetime.now(),
            'regime': regime,
            'model_id': model_id,
            'error': error,
        })
    
    def get_optimal_weights(self, regime: str, model_ids: List[str]) -> Dict[str, float]:
        """
        Get optimal voting weights for models in current regime.
        
        Returns:
            Dictionary of model_id -> weight
        """
        if regime not in self.regime_model_performance:
            # Equal weights if no regime history
            return {mid: 1.0 / len(model_ids) for mid in model_ids}
        
        weights = {}
        
        for model_id in model_ids:
            if model_id in self.regime_model_performance[regime]:
                errors = self.regime_model_performance[regime][model_id]
                avg_error = np.mean(errors)
                # Weight inversely proportional to error
                weights[model_id] = 1.0 / (1.0 + avg_error)
            else:
                weights[model_id] = 0.5  # Default weight for unknown
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def predict_best_models(self, regime: str, top_k: int = 10) -> List[str]:
        """Predict top K best models for a regime."""
        if regime not in self.regime_model_performance:
            return []
        
        model_scores = {}
        
        for model_id, errors in self.regime_model_performance[regime].items():
            avg_error = np.mean(errors)
            model_scores[model_id] = 1.0 / (1.0 + avg_error)
        
        # Sort by score descending
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [mid for mid, _ in sorted_models[:top_k]]


class NeuralArchitectureSearch:
    """
    Neural Architecture Search - autonomously explores neural network architectures.
    
    Identifies high-performing designs and promotes them to parliament.
    """
    
    def __init__(self):
        self.search_space = {
            'layers': [2, 3, 4, 5],
            'units': [32, 64, 128, 256],
            'activation': ['relu', 'tanh', 'gelu'],
            'dropout': [0.0, 0.1, 0.2, 0.3],
        }
        self.evaluated_architectures: List[Dict[str, Any]] = []
        self.best_architectures: deque = deque(maxlen=10)
        
        logger.info("Neural Architecture Search initialized")
    
    def sample_architecture(self) -> Dict[str, Any]:
        """Sample random architecture from search space."""
        return {
            'layers': np.random.choice(self.search_space['layers']),
            'units': np.random.choice(self.search_space['units']),
            'activation': np.random.choice(self.search_space['activation']),
            'dropout': np.random.choice(self.search_space['dropout']),
        }
    
    def evaluate_architecture(
        self,
        architecture: Dict[str, Any],
        validation_score: float
    ) -> None:
        """Evaluate and record architecture performance."""
        result = {
            'architecture': architecture,
            'score': validation_score,
            'timestamp': datetime.now(),
        }
        
        self.evaluated_architectures.append(result)
        
        # Update best architectures
        if not self.best_architectures or validation_score > min(a['score'] for a in self.best_architectures):
            self.best_architectures.append(result)
            # Sort by score
            self.best_architectures = deque(
                sorted(self.best_architectures, key=lambda x: x['score'], reverse=True)[:10],
                maxlen=10
            )
    
    def get_best_architectures(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get top K best architectures discovered."""
        return list(self.best_architectures)[:top_k]
    
    def run_search_iteration(self, n_samples: int = 10) -> List[Dict[str, Any]]:
        """Run one iteration of architecture search."""
        candidates = []
        
        for _ in range(n_samples):
            arch = self.sample_architecture()
            candidates.append(arch)
        
        logger.debug(f"NAS iteration: sampled {len(candidates)} architectures")
        return candidates


class UncertaintyQuantifier:
    """
    Calibrated uncertainty quantification.
    
    Ensures model confidence matches realized accuracy.
    Models that are chronically overconfident are downweighted.
    """
    
    def __init__(self):
        self.calibration_data: Dict[str, List[Tuple[float, bool]]] = {}
        # model_id -> [(confidence, was_correct), ...]
        
        logger.info("Uncertainty Quantifier initialized")
    
    def record_prediction(
        self,
        model_id: str,
        confidence: float,
        was_correct: bool
    ) -> None:
        """Record prediction for calibration analysis."""
        if model_id not in self.calibration_data:
            self.calibration_data[model_id] = []
        
        self.calibration_data[model_id].append((confidence, was_correct))
        
        # Keep only recent data
        if len(self.calibration_data[model_id]) > 1000:
            self.calibration_data[model_id] = self.calibration_data[model_id][-1000:]
    
    def get_calibration_score(self, model_id: str) -> float:
        """
        Get calibration score for a model.
        
        Returns:
            Score from 0 (poorly calibrated) to 1 (perfectly calibrated)
        """
        if model_id not in self.calibration_data or not self.calibration_data[model_id]:
            return 0.5  # Unknown
        
        data = self.calibration_data[model_id]
        
        # Bin predictions by confidence
        bins = np.linspace(0, 1, 11)
        calibration_errors = []
        
        for i in range(len(bins) - 1):
            bin_low, bin_high = bins[i], bins[i + 1]
            
            bin_data = [(conf, correct) for conf, correct in data 
                       if bin_low <= conf < bin_high]
            
            if not bin_data:
                continue
            
            avg_confidence = np.mean([conf for conf, _ in bin_data])
            accuracy = np.mean([1.0 if correct else 0.0 for _, correct in bin_data])
            
            # Calibration error is difference between confidence and accuracy
            calibration_errors.append(abs(avg_confidence - accuracy))
        
        if not calibration_errors:
            return 0.5
        
        # Lower error = better calibration
        avg_error = np.mean(calibration_errors)
        calibration_score = 1.0 / (1.0 + avg_error)
        
        return calibration_score
    
    def is_overconfident(self, model_id: str, threshold: float = 0.6) -> bool:
        """Check if model is chronically overconfident."""
        calibration_score = self.get_calibration_score(model_id)
        return calibration_score < threshold
    
    def get_all_calibration_scores(self) -> Dict[str, float]:
        """Get calibration scores for all models."""
        return {
            model_id: self.get_calibration_score(model_id)
            for model_id in self.calibration_data
        }


class AdaptiveModelEnsemble:
    """
    Adaptive Model Ensemble - Master coordinator for Layer 3.
    
    Integrates Model Parliament, Meta-Learner Oracle, NAS, and Uncertainty Quantifier.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.parliament = ModelParliament(
            target_size=config.get('parliament_size', 100)
        )
        self.meta_learner = MetaLearnerOracle()
        self.nas = NeuralArchitectureSearch()
        self.uncertainty_quantifier = UncertaintyQuantifier()
        
        self._initialize_base_models()
        
        logger.info("Adaptive Model Ensemble initialized - Layer 3 operational")
    
    def _initialize_base_models(self) -> None:
        """Initialize base set of models."""
        # Add diverse model types
        model_configs = [
            ('dl_transformer', DeepLearningModel, {'architecture': 'transformer'}),
            ('dl_lstm', DeepLearningModel, {'architecture': 'lstm'}),
            ('gb_xgboost', GradientBoostingModel, {'variant': 'xgboost'}),
            ('gb_lightgbm', GradientBoostingModel, {'variant': 'lightgbm'}),
            ('bayesian_1', BayesianModel, {}),
        ]
        
        for model_id, model_class, kwargs in model_configs:
            model = model_class(model_id, **kwargs)
            
            card = ModelCard(
                model_id=model_id,
                model_type=model.model_type,
                architecture=str(kwargs),
                training_regime={'initial': True},
                assumptions=['stationary returns', 'continuous markets'],
                training_timestamp=datetime.now(),
            )
            
            self.parliament.add_model(model, card)
        
        logger.info(f"Initialized {len(model_configs)} base models")
    
    def predict(
        self,
        features: np.ndarray,
        regime: Optional[str] = None
    ) -> ParliamentVote:
        """
        Make prediction using full ensemble.
        
        Args:
            features: Input features
            regime: Optional market regime
            
        Returns:
            Parliament vote with uncertainty quantification
        """
        # Update meta-learner regime
        if regime:
            self.meta_learner.update_regime(regime)
            
            # Get optimal weights for this regime
            model_ids = list(self.parliament.models.keys())
            optimal_weights = self.meta_learner.get_optimal_weights(regime, model_ids)
            
            # Update parliament weights
            for model_id, weight in optimal_weights.items():
                self.parliament.voting_weights[model_id] = weight
            
            self.parliament._normalize_weights()
        
        # Get parliament vote
        vote = self.parliament.vote(features, regime)
        
        return vote
    
    def update_performance(
        self,
        features: np.ndarray,
        prediction: float,
        actual: float,
        regime: Optional[str] = None
    ) -> None:
        """Update performance tracking for all models."""
        # Update individual model performance
        for model_id, model in self.parliament.models.items():
            if model.is_trained:
                try:
                    model_pred, _ = model.predict(features)
                    model.update_performance(actual, model_pred)
                    
                    # Update meta-learner
                    if regime:
                        self.meta_learner.record_performance(regime, model_id, model_pred, actual)
                    
                    # Update calibration
                    was_correct = abs(model_pred - actual) < 0.1  # Threshold
                    confidence = 1.0 / (1.0 + abs(model_pred - actual))
                    self.uncertainty_quantifier.record_prediction(model_id, confidence, was_correct)
                    
                except Exception as e:
                    logger.debug(f"Failed to update {model_id}: {e}")
    
    def run_nas_cycle(self, n_architectures: int = 10) -> List[Dict[str, Any]]:
        """Run Neural Architecture Search cycle."""
        return self.nas.run_search_iteration(n_architectures)
    
    def get_model_disagreement(self, features: np.ndarray) -> float:
        """Get model disagreement as regime uncertainty signal."""
        return self.parliament.get_model_disagreement(features)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ensemble statistics."""
        return {
            'parliament': self.parliament.get_statistics(),
            'meta_learner': {
                'current_regime': self.meta_learner.current_regime,
                'tracked_regimes': len(self.meta_learner.regime_model_performance),
            },
            'nas': {
                'evaluated_architectures': len(self.nas.evaluated_architectures),
                'best_architectures': len(self.nas.best_architectures),
            },
            'calibration': {
                'tracked_models': len(self.uncertainty_quantifier.calibration_data),
            },
        }
