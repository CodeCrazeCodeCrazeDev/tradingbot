"""
Model Parliament for APEX-FI Layer 3

Adaptive ensemble of specialized models with:
- Weighted voting across model types
- Regime-conditional model selection
- Uncertainty quantification
- Model disagreement as signal
- Continuous architecture search
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import uuid

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of models in the parliament."""
    DEEP_LEARNING = "deep_learning"
    GRADIENT_BOOSTING = "gradient_boosting"
    BAYESIAN = "bayesian"
    PHYSICS_INSPIRED = "physics_inspired"
    STATISTICAL = "statistical"
    NEURAL_NETWORK = "neural_network"
    TRANSFORMER = "transformer"
    REINFORCEMENT = "reinforcement"


class MarketRegime(Enum):
    """Market regimes for conditional weighting."""
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    EARNINGS = "earnings"


@dataclass
class ModelMember:
    """A member of the model parliament."""
    model_id: str
    name: str
    model_type: ModelType
    
    # Model instance (callable)
    model: Callable
    
    # Performance tracking
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    regime_performance: Dict[str, float] = field(default_factory=dict)
    
    # Current weights
    base_weight: float = 1.0
    regime_weights: Dict[str, float] = field(default_factory=dict)
    
    # Uncertainty
    prediction_variance: float = 0.1
    calibration_score: float = 0.5
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Status
    is_active: bool = True
    failure_count: int = 0
    
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """Make prediction with uncertainty estimate."""
        try:
            prediction = self.model(features)
            uncertainty = self.prediction_variance
            return prediction, uncertainty
        except Exception as e:
            logger.warning(f"Model {self.model_id} failed: {e}")
            self.failure_count += 1
            return 0.0, float('inf')
    
    def update_performance(self, regime: str, accuracy: float):
        """Update performance for a regime."""
        self.regime_performance[regime] = accuracy
        self.performance_history.append({
            'regime': regime,
            'accuracy': accuracy,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class EnsemblePrediction:
    """Prediction from the ensemble."""
    prediction_id: str
    value: float
    
    # Uncertainty
    mean_prediction: float
    std_prediction: float
    prediction_interval: Tuple[float, float]
    
    # Model contributions
    individual_predictions: Dict[str, float]
    model_weights_used: Dict[str, float]
    
    # Disagreement metrics
    disagreement_index: float  # 0-1
    consensus_strength: float  # 0-1
    outlier_models: List[str]
    
    # Regime info
    detected_regime: Optional[str]
    regime_confidence: float
    
    # Conformal prediction
    conformal_interval: Optional[Tuple[float, float]] = None
    coverage_guarantee: float = 0.9
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetaLearnerPrediction:
    """Meta-learner output for model selection."""
    regime: MarketRegime
    regime_confidence: float
    recommended_models: List[str]
    model_weights: Dict[str, float]
    expected_ensemble_performance: float
    reasoning: str


class MetaLearnerOracle:
    """
    Meta-learner that predicts which models perform best per regime.
    
    Features:
    - Regime detection
    - Performance prediction
    - Model selection
    - Continuous learning
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Regime detector
        self.regime_detector: Optional[Callable] = None
        
        # Model performance predictions
        self.performance_predictions: Dict[str, Dict[str, float]] = {}
        
        # Learning rate
        self.learning_rate = self.config.get('meta_learning_rate', 0.1)
        
        logger.info("🔮 Meta-Learner Oracle initialized")
    
    def register_regime_detector(self, detector: Callable):
        """Register regime detection function."""
        self.regime_detector = detector
    
    async def predict_optimal_ensemble(
        self,
        market_features: np.ndarray,
        available_models: List[ModelMember],
    ) -> MetaLearnerPrediction:
        """
        Predict optimal ensemble for current market conditions.
        
        Args:
            market_features: Current market state
            available_models: Available model members
        
        Returns:
            Meta-learner prediction
        """
        # Detect regime
        if self.regime_detector:
            regime, confidence = self.regime_detector(market_features)
        else:
            # Default random regime
            regime = random.choice(list(MarketRegime))
            confidence = 0.6
        
        # Predict model performance in this regime
        model_scores = {}
        for model in available_models:
            # Use historical regime performance
            historical = model.regime_performance.get(regime.value, 0.5)
            
            # Add some prediction noise (in real system, use learned predictor)
            predicted = historical + random.uniform(-0.1, 0.1)
            model_scores[model.model_id] = max(0, min(1, predicted))
        
        # Select top models
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        top_models = [m[0] for m in sorted_models[:5]]  # Top 5
        
        # Normalize weights
        total_score = sum(model_scores[m] for m in top_models)
        weights = {m: model_scores[m] / total_score for m in top_models} if total_score > 0 else {m: 1/len(top_models) for m in top_models}
        
        # Calculate expected performance
        expected_perf = np.mean([model_scores[m] for m in top_models])
        
        return MetaLearnerPrediction(
            regime=regime,
            regime_confidence=confidence,
            recommended_models=top_models,
            model_weights=weights,
            expected_ensemble_performance=expected_perf,
            reasoning=f"Selected models based on historical performance in {regime.value} regime",
        )
    
    def update_from_outcome(
        self,
        prediction: MetaLearnerPrediction,
        actual_performance: float,
    ):
        """Update meta-learner based on actual outcomes."""
        # Simple gradient descent update
        error = prediction.expected_ensemble_performance - actual_performance
        
        # In real system, update learned parameters
        # For now, just log
        logger.debug(f"Meta-learner update: error={error:.4f}")


class ModelParliament:
    """
    Ensemble of models with adaptive weighting.
    
    Features:
    - Weighted voting
    - Regime-conditional selection
    - Uncertainty quantification
    - Model disagreement signals
    - Dynamic member addition/removal
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Members
        self.members: Dict[str, ModelMember] = {}
        self.active_members: Set[str] = set()
        
        # Meta-learner
        self.meta_learner = MetaLearnerOracle(config)
        
        # Ensemble history
        self.prediction_history: List[EnsemblePrediction] = []
        
        # Conformal prediction calibration
        self.calibration_data: List[Tuple[float, float]] = []  # (prediction, actual)
        
        # Configuration
        self.min_active_models = self.config.get('min_active_models', 3)
        self.max_active_models = self.config.get('max_active_models', 20)
        self.disagreement_threshold = self.config.get('disagreement_threshold', 0.3)
        
        logger.info("🏛️ Model Parliament initialized")
    
    def register_model(self, model: ModelMember):
        """Register a new model member."""
        self.members[model.model_id] = model
        if model.is_active:
            self.active_members.add(model.model_id)
        
        logger.info(f"🏛️ Registered model: {model.name} ({model.model_type.value})")
    
    def activate_model(self, model_id: str):
        """Activate a model."""
        if model_id in self.members:
            self.members[model_id].is_active = True
            self.active_members.add(model_id)
    
    def deactivate_model(self, model_id: str):
        """Deactivate a model."""
        if model_id in self.members:
            self.members[model_id].is_active = False
            self.active_members.discard(model_id)
    
    async def predict(
        self,
        features: np.ndarray,
        market_regime: Optional[str] = None,
        use_meta_learner: bool = True,
    ) -> EnsemblePrediction:
        """
        Generate ensemble prediction.
        
        Args:
            features: Input features
            market_regime: Current market regime (optional)
            use_meta_learner: Whether to use meta-learner for model selection
        
        Returns:
            Ensemble prediction with uncertainty
        """
        # Get active members
        active = [self.members[mid] for mid in self.active_members]
        
        if not active:
            raise ValueError("No active models in parliament")
        
        # Get model weights
        if use_meta_learner:
            meta_pred = await self.meta_learner.predict_optimal_ensemble(features, active)
            model_weights = meta_pred.model_weights
            detected_regime = meta_pred.regime.value
            regime_confidence = meta_pred.regime_confidence
        else:
            # Equal weights
            n = len(active)
            model_weights = {m.model_id: 1.0 / n for m in active}
            detected_regime = market_regime
            regime_confidence = 1.0
        
        # Collect predictions
        individual_preds = {}
        uncertainties = {}
        
        for model in active:
            if model.model_id in model_weights:
                pred, unc = model.predict(features)
                individual_preds[model.model_id] = pred
                uncertainties[model.model_id] = unc
        
        # Calculate weighted ensemble
        weighted_sum = sum(
            individual_preds[mid] * model_weights.get(mid, 0)
            for mid in individual_preds
        )
        total_weight = sum(model_weights.get(mid, 0) for mid in individual_preds)
        
        mean_pred = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Calculate ensemble variance
        variances = []
        for mid, pred in individual_preds.items():
            weight = model_weights.get(mid, 0)
            model_var = uncertainties[mid]
            variances.append(weight * (model_var + (pred - mean_pred) ** 2))
        
        ensemble_var = sum(variances) if variances else 0.1
        ensemble_std = np.sqrt(ensemble_var)
        
        # Prediction interval (95%)
        interval = (mean_pred - 1.96 * ensemble_std, mean_pred + 1.96 * ensemble_std)
        
        # Calculate disagreement metrics
        pred_values = list(individual_preds.values())
        disagreement = np.std(pred_values) / (abs(mean_pred) + 1e-10)
        
        # Identify outliers (models with predictions far from mean)
        outlier_threshold = 2.0 * ensemble_std
        outliers = [
            mid for mid, pred in individual_preds.items()
            if abs(pred - mean_pred) > outlier_threshold
        ]
        
        # Consensus strength
        consensus = 1 - min(1, disagreement)
        
        # Conformal prediction interval
        conformal_int = self._get_conformal_interval(mean_pred)
        
        prediction = EnsemblePrediction(
            prediction_id=f"ENS-{uuid.uuid4().hex[:10]}",
            value=mean_pred,
            mean_prediction=mean_pred,
            std_prediction=ensemble_std,
            prediction_interval=interval,
            individual_predictions=individual_preds,
            model_weights_used=model_weights,
            disagreement_index=disagreement,
            consensus_strength=consensus,
            outlier_models=outliers,
            detected_regime=detected_regime,
            regime_confidence=regime_confidence,
            conformal_interval=conformal_int,
        )
        
        self.prediction_history.append(prediction)
        
        logger.debug(f"🏛️ Ensemble prediction: {mean_pred:.4f} ± {ensemble_std:.4f}, "
                    f"disagreement={disagreement:.2f}")
        
        return prediction
    
    def _get_conformal_interval(self, prediction: float) -> Optional[Tuple[float, float]]:
        """Get conformal prediction interval."""
        if len(self.calibration_data) < 100:
            return None
        
        # Calculate nonconformity scores
        nonconf_scores = [
            abs(pred - actual) for pred, actual in self.calibration_data
        ]
        
        # Get quantile for desired coverage
        alpha = 1 - 0.9  # 90% coverage
        quantile = np.quantile(nonconf_scores, 1 - alpha)
        
        return (prediction - quantile, prediction + quantile)
    
    def update_from_outcome(
        self,
        prediction_id: str,
        actual_value: float,
    ):
        """Update ensemble based on actual outcome."""
        # Find prediction
        pred = None
        for p in self.prediction_history:
            if p.prediction_id == prediction_id:
                pred = p
                break
        
        if not pred:
            return
        
        # Add to calibration data
        self.calibration_data.append((pred.mean_prediction, actual_value))
        
        # Trim calibration data
        if len(self.calibration_data) > 10000:
            self.calibration_data = self.calibration_data[-5000:]
        
        # Update individual model performance
        for model_id, model_pred in pred.individual_predictions.items():
            accuracy = 1 - abs(model_pred - actual_value) / (abs(actual_value) + 1e-10)
            
            if model_id in self.members:
                self.members[model_id].update_performance(
                    pred.detected_regime or 'unknown',
                    max(0, min(1, accuracy))
                )
        
        # Update meta-learner
        if hasattr(self, '_last_meta_prediction'):
            self.meta_learner.update_from_outcome(
                self._last_meta_prediction,
                1 - abs(pred.mean_prediction - actual_value) / (abs(actual_value) + 1e-10)
            )
    
    def get_model_disagreement_signal(self, prediction: EnsemblePrediction) -> str:
        """
        Interpret model disagreement as market signal.
        
        High disagreement can indicate:
        - Regime uncertainty
        - Incoming volatility
        - Distribution shift
        """
        if prediction.disagreement_index > 0.7:
            return "EXTREME_UNCERTAINTY"
        elif prediction.disagreement_index > 0.5:
            return "HIGH_UNCERTAINTY"
        elif prediction.disagreement_index > 0.3:
            return "MODERATE_UNCERTAINTY"
        elif prediction.consensus_strength > 0.8:
            return "STRONG_CONSENSUS"
        else:
            return "NORMAL"
    
    def get_parliament_status(self) -> Dict[str, Any]:
        """Get parliament status."""
        # Calculate model type distribution
        type_counts = {}
        for model in self.members.values():
            t = model.model_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Calculate average performance
        avg_perf = np.mean([
            np.mean(list(m.regime_performance.values())) if m.regime_performance else 0.5
            for m in self.members.values()
        ]) if self.members else 0
        
        return {
            'total_models': len(self.members),
            'active_models': len(self.active_members),
            'by_type': type_counts,
            'average_performance': avg_perf,
            'prediction_history_size': len(self.prediction_history),
            'calibration_data_size': len(self.calibration_data),
        }


class NeuralArchitectureSearch:
    """
    Continuous neural architecture search.
    
    Features:
    - Architecture space exploration
    - Performance evaluation
    - Population-based training
    - Architecture evolution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Search space
        self.search_space = {
            'num_layers': [2, 4, 8, 16],
            'hidden_size': [64, 128, 256, 512],
            'activation': ['relu', 'tanh', 'swish', 'gelu'],
            'dropout': [0.0, 0.1, 0.2, 0.5],
            'learning_rate': [1e-4, 1e-3, 1e-2],
        }
        
        # Population
        self.population: List[Dict] = []
        self.population_size = self.config.get('nas_population_size', 20)
        
        logger.info("🔍 Neural Architecture Search initialized")
    
    def sample_architecture(self) -> Dict[str, Any]:
        """Sample random architecture from search space."""
        return {
            key: random.choice(values)
            for key, values in self.search_space.items()
        }
    
    def initialize_population(self):
        """Initialize population with random architectures."""
        self.population = [
            {
                'architecture': self.sample_architecture(),
                'fitness': 0.0,
                'evaluations': 0,
            }
            for _ in range(self.population_size)
        ]
    
    async def search_iteration(self, evaluator: Callable[[Dict], float]) -> Dict[str, Any]:
        """
        Run one NAS iteration.
        
        Args:
            evaluator: Function to evaluate architecture fitness
        
        Returns:
            Best architecture found
        """
        # Evaluate unevaluated architectures
        for individual in self.population:
            if individual['evaluations'] == 0:
                try:
                    fitness = await evaluator(individual['architecture'])
                    individual['fitness'] = fitness
                    individual['evaluations'] += 1
                except Exception as e:
                    logger.warning(f"Architecture evaluation failed: {e}")
                    individual['fitness'] = 0.0
        
        # Select top performers
        sorted_pop = sorted(self.population, key=lambda x: x['fitness'], reverse=True)
        elite = sorted_pop[:self.population_size // 2]
        
        # Generate offspring
        offspring = []
        for _ in range(self.population_size - len(elite)):
            parent = random.choice(elite)
            child_arch = self._mutate_architecture(parent['architecture'])
            offspring.append({
                'architecture': child_arch,
                'fitness': 0.0,
                'evaluations': 0,
            })
        
        # Form new population
        self.population = elite + offspring
        
        return sorted_pop[0]['architecture']
    
    def _mutate_architecture(self, architecture: Dict) -> Dict:
        """Mutate architecture."""
        mutated = architecture.copy()
        
        # Randomly mutate one parameter
        key_to_mutate = random.choice(list(self.search_space.keys()))
        mutated[key_to_mutate] = random.choice(self.search_space[key_to_mutate])
        
        return mutated


# Example usage
async def example_model_parliament():
    """Example of model parliament."""
    parliament = ModelParliament()
    
    # Create dummy models
    for i in range(5):
        model = ModelMember(
            model_id=f"model_{i}",
            name=f"Model {i}",
            model_type=random.choice(list(ModelType)),
            model=lambda x: random.uniform(-0.1, 0.1),  # Dummy predictor
            base_weight=1.0,
        )
        parliament.register_model(model)
    
    # Make prediction
    features = np.random.randn(10)
    prediction = await parliament.predict(features)
    
    print("Ensemble Prediction Results:")
    print(f"  Mean: {prediction.mean_prediction:.4f}")
    print(f"  Std: {prediction.std_prediction:.4f}")
    print(f"  95% CI: [{prediction.prediction_interval[0]:.4f}, {prediction.prediction_interval[1]:.4f}]")
    print(f"  Disagreement: {prediction.disagreement_index:.2f}")
    print(f"  Consensus: {prediction.consensus_strength:.2f}")
    print(f"  Detected Regime: {prediction.detected_regime}")
    
    # Disagreement signal
    signal = parliament.get_model_disagreement_signal(prediction)
    print(f"  Disagreement Signal: {signal}")
    
    # Status
    status = parliament.get_parliament_status()
    print(f"\nParliament Status: {status}")


if __name__ == "__main__":
    import random
    asyncio.run(example_model_parliament())
