"""
from typing import Callable, Dict, List, Optional, Set, Tuple
Ensemble Meta-Learner
=====================
Advanced ensemble learning with regime-specific models.

Features:
- Weighted model ensemble
- Stacked generalization
- Regime-specific ensembles
- Voting systems
- Confidence-based switching
- Dynamic weight optimization
- Model performance tracking

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.ensemble import (
        RandomForestClassifier, GradientBoostingClassifier,
        RandomForestRegressor, GradientBoostingRegressor,
        VotingClassifier, StackingClassifier
    )
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, f1_score, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of models in ensemble"""
    RANDOM_FOREST = auto()
    GRADIENT_BOOSTING = auto()
    NEURAL_NETWORK = auto()
    LOGISTIC = auto()
    SVM = auto()
    LSTM = auto()
    TRANSFORMER = auto()
    RULE_BASED = auto()


class VotingMethod(Enum):
    """Voting methods for ensemble"""
    HARD = auto()      # Majority vote
    SOFT = auto()      # Probability average
    WEIGHTED = auto()  # Weighted by performance
    CONFIDENCE = auto() # Use most confident
    CONSENSUS = auto()  # Require agreement


class RegimeType(Enum):
    """Market regime types"""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    CRISIS = auto()


@dataclass
class ModelInfo:
    """Information about a model in the ensemble"""
    model_id: str
    model_type: ModelType
    name: str
    
    # Model object
    model: Any = None
    
    # Performance metrics
    accuracy: float = 0.5
    precision: float = 0.5
    recall: float = 0.5
    f1_score: float = 0.5
    sharpe_ratio: float = 0.0
    
    # Weight in ensemble
    weight: float = 1.0
    
    # Regime performance
    regime_performance: Dict[str, float] = field(default_factory=dict)
    
    # Training info
    last_trained: Optional[datetime] = None
    training_samples: int = 0
    
    # Confidence calibration
    calibration_factor: float = 1.0


@dataclass
class EnsemblePrediction:
    """Prediction from ensemble"""
    timestamp: datetime
    
    # Prediction
    prediction: Any
    confidence: float
    
    # Individual model predictions
    model_predictions: Dict[str, Any] = field(default_factory=dict)
    model_confidences: Dict[str, float] = field(default_factory=dict)
    
    # Voting info
    voting_method: VotingMethod = VotingMethod.WEIGHTED
    agreement_ratio: float = 0.0
    
    # Regime
    current_regime: Optional[RegimeType] = None


class BaseModel:
    """Base class for ensemble models"""
    
    def __init__(self, model_id: str, name: str):
        self.model_id = model_id
        self.name = name
        self.is_fitted = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit the model - to be implemented by subclasses"""
        logger.warning(f"fit() not implemented for {self.name}")
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict - to be implemented by subclasses"""
        logger.warning(f"predict() not implemented for {self.name}")
        return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities - to be implemented by subclasses"""
        logger.warning(f"predict_proba() not implemented for {self.name}")
        return np.zeros((len(X), 2))


class SklearnModel(BaseModel):
    """Sklearn-based model wrapper"""
    
    def __init__(
        self,
        model_id: str,
        name: str,
        model_type: ModelType,
        **kwargs
    ):
        super().__init__(model_id, name)
        self.model_type = model_type
        
        if not SKLEARN_AVAILABLE:
            self.model = None
            return
        
        if model_type == ModelType.RANDOM_FOREST:
            self.model = RandomForestClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 10),
                random_state=42
            )
        elif model_type == ModelType.GRADIENT_BOOSTING:
            self.model = GradientBoostingClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 5),
                random_state=42
            )
        elif model_type == ModelType.LOGISTIC:
            self.model = LogisticRegression(
                max_iter=kwargs.get('max_iter', 1000),
                random_state=42
            )
        else:
            self.model = RandomForestClassifier(n_estimators=50, random_state=42)
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        if self.model is not None:
            self.model.fit(X, y)
            self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is not None and self.is_fitted:
            return self.model.predict(X)
        return np.zeros(len(X))
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is not None and self.is_fitted:
            return self.model.predict_proba(X)
        return np.ones((len(X), 2)) * 0.5


class NeuralModel(BaseModel):
    """Neural network model"""
    
    def __init__(
        self,
        model_id: str,
        name: str,
        input_dim: int = 10,
        hidden_dim: int = 64,
        output_dim: int = 2
    ):
        super().__init__(model_id, name)
        self.model_type = ModelType.NEURAL_NETWORK
        
        if not TORCH_AVAILABLE:
            self.model = None
            return
        
        self.model = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim),
            nn.Softmax(dim=1)
        )
        
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 100):
        if self.model is None:
            return
        
        if self.scaler:
            X = self.scaler.fit_transform(X)
        
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(epochs):
            self.model.train()
            optimizer.zero_grad()
            output = self.model(X_tensor)
            loss = criterion(output, y_tensor)
            loss.backward()
            optimizer.step()
        
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None or not self.is_fitted:
            return np.zeros(len(X))
        
        if self.scaler:
            X = self.scaler.transform(X)
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            output = self.model(X_tensor)
            return output.argmax(dim=1).numpy()
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is None or not self.is_fitted:
            return np.ones((len(X), 2)) * 0.5
        
        if self.scaler:
            X = self.scaler.transform(X)
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            return self.model(X_tensor).numpy()


class RuleBasedModel(BaseModel):
    """Rule-based model for ensemble"""
    
    def __init__(self, model_id: str, name: str, rules: List[Callable] = None):
        super().__init__(model_id, name)
        self.model_type = ModelType.RULE_BASED
        self.rules = rules or []
        self.is_fitted = True  # Rules don't need fitting
    
    def add_rule(self, rule: Callable):
        """Add a rule function"""
        self.rules.append(rule)
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        # Rules don't need fitting
        """Auto-implemented method."""
        logger.debug(f"{self.__class__.__name__}.fit called")
        return None
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        predictions = []
        
        for x in X:
            votes = [rule(x) for rule in self.rules]
            if votes:
                prediction = 1 if sum(votes) > len(votes) / 2 else 0
            else:
                prediction = 0
            predictions.append(prediction)
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        probas = []
        
        for x in X:
            votes = [rule(x) for rule in self.rules]
            if votes:
                prob_1 = sum(votes) / len(votes)
            else:
                prob_1 = 0.5
            probas.append([1 - prob_1, prob_1])
        
        return np.array(probas)


class WeightOptimizer:
    """Optimize ensemble weights"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def optimize_weights(
        self,
        model_predictions: Dict[str, np.ndarray],
        y_true: np.ndarray,
        method: str = 'sharpe'
    ) -> Dict[str, float]:
        """Optimize model weights"""
        
        model_names = list(model_predictions.keys())
        n_models = len(model_names)
        
        if n_models == 0:
            return {}
        
        # Stack predictions
        pred_matrix = np.column_stack([model_predictions[name] for name in model_names])
        
        if method == 'accuracy':
            # Weight by accuracy
            weights = {}
            for i, name in enumerate(model_names):
                acc = accuracy_score(y_true, pred_matrix[:, i])
                weights[name] = acc
        
        elif method == 'sharpe' and SCIPY_AVAILABLE:
            # Optimize for Sharpe-like metric
            def objective(w):
                combined = np.average(pred_matrix, axis=1, weights=w)
                combined_binary = (combined > 0.5).astype(int)
                
                # Calculate returns (assuming prediction correctness = return)
                returns = (combined_binary == y_true).astype(float) - 0.5
                
                if np.std(returns) == 0:
                    return 0
                
                sharpe = np.mean(returns) / np.std(returns)
                return -sharpe  # Minimize negative Sharpe
            
            # Constraints: weights sum to 1, all positive
            constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
            bounds = [(0.01, 1.0) for _ in range(n_models)]
            
            # Initial weights
            w0 = np.ones(n_models) / n_models
            
            result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)
            
            weights = {name: result.x[i] for i, name in enumerate(model_names)}
        
        else:
            # Equal weights
            weights = {name: 1.0 / n_models for name in model_names}
        
        return weights
    
    def calculate_regime_weights(
        self,
        model_infos: Dict[str, ModelInfo],
        current_regime: RegimeType
    ) -> Dict[str, float]:
        """Calculate weights based on regime performance"""
        
        weights = {}
        regime_key = current_regime.name
        
        for model_id, info in model_infos.items():
            # Get regime-specific performance
            regime_perf = info.regime_performance.get(regime_key, info.accuracy)
            
            # Weight is proportional to regime performance
            weights[model_id] = max(regime_perf, 0.1)
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights


class StackedEnsemble:
    """Stacked generalization ensemble"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_models: List[BaseModel] = []
        self.meta_model: Optional[BaseModel] = None
        self.is_fitted = False
        
    def add_base_model(self, model: BaseModel):
        """Add a base model"""
        self.base_models.append(model)
    
    def set_meta_model(self, model: BaseModel):
        """Set the meta model"""
        self.meta_model = model
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit stacked ensemble"""
        
        if not self.base_models:
            return
        
        # Fit base models and get predictions
        base_predictions = []
        
        for model in self.base_models:
            model.fit(X, y)
            preds = model.predict_proba(X)
            base_predictions.append(preds[:, 1] if preds.shape[1] > 1 else preds.flatten())
        
        # Stack predictions as meta features
        meta_features = np.column_stack(base_predictions)
        
        # Fit meta model
        if self.meta_model is None:
            self.meta_model = SklearnModel(
                'meta', 'MetaModel', ModelType.LOGISTIC
            )
        
        self.meta_model.fit(meta_features, y)
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using stacked ensemble"""
        
        if not self.is_fitted:
            return np.zeros(len(X))
        
        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            preds = model.predict_proba(X)
            base_predictions.append(preds[:, 1] if preds.shape[1] > 1 else preds.flatten())
        
        # Stack as meta features
        meta_features = np.column_stack(base_predictions)
        
        # Meta model prediction
        return self.meta_model.predict(meta_features)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities"""
        
        if not self.is_fitted:
            return np.ones((len(X), 2)) * 0.5
        
        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            preds = model.predict_proba(X)
            base_predictions.append(preds[:, 1] if preds.shape[1] > 1 else preds.flatten())
        
        # Stack as meta features
        meta_features = np.column_stack(base_predictions)
        
        # Meta model prediction
        return self.meta_model.predict_proba(meta_features)


class RegimeSpecificEnsemble:
    """Ensemble with regime-specific models"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.regime_models: Dict[RegimeType, List[BaseModel]] = {}
        self.regime_weights: Dict[RegimeType, Dict[str, float]] = {}
        self.current_regime: RegimeType = RegimeType.RANGING
        
    def add_model_for_regime(self, regime: RegimeType, model: BaseModel):
        """Add model for specific regime"""
        
        if regime not in self.regime_models:
            self.regime_models[regime] = []
        
        self.regime_models[regime].append(model)
    
    def set_regime(self, regime: RegimeType):
        """Set current regime"""
        self.current_regime = regime
    
    def fit(self, X: np.ndarray, y: np.ndarray, regime_labels: np.ndarray):
        """Fit regime-specific models"""
        
        for regime in RegimeType:
            if regime not in self.regime_models:
                continue
            
            # Filter data for this regime
            mask = regime_labels == regime.value
            if mask.sum() < 10:
                continue
            
            X_regime = X[mask]
            y_regime = y[mask]
            
            # Fit models for this regime
            for model in self.regime_models[regime]:
                model.fit(X_regime, y_regime)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using current regime models"""
        
        models = self.regime_models.get(self.current_regime, [])
        
        if not models:
            return np.zeros(len(X))
        
        # Get predictions from all models
        predictions = []
        for model in models:
            if model.is_fitted:
                predictions.append(model.predict(X))
        
        if not predictions:
            return np.zeros(len(X))
        
        # Majority vote
        pred_matrix = np.column_stack(predictions)
        return (pred_matrix.mean(axis=1) > 0.5).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities"""
        
        models = self.regime_models.get(self.current_regime, [])
        
        if not models:
            return np.ones((len(X), 2)) * 0.5
        
        # Get predictions from all models
        probas = []
        for model in models:
            if model.is_fitted:
                probas.append(model.predict_proba(X))
        
        if not probas:
            return np.ones((len(X), 2)) * 0.5
        
        # Average probabilities
        return np.mean(probas, axis=0)


class EnsembleMetaLearner:
    """
    Complete Ensemble Meta-Learner.
    
    Features:
    - Weighted model ensemble
    - Stacked generalization
    - Regime-specific ensembles
    - Voting systems
    - Confidence-based switching
    - Dynamic weight optimization
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Models
        self.models: Dict[str, ModelInfo] = {}
        self.base_models: Dict[str, BaseModel] = {}
        
        # Ensemble types
        self.stacked_ensemble = StackedEnsemble(config)
        self.regime_ensemble = RegimeSpecificEnsemble(config)
        
        # Weight optimizer
        self.weight_optimizer = WeightOptimizer(config)
        
        # State
        self.current_regime: RegimeType = RegimeType.RANGING
        self.voting_method: VotingMethod = VotingMethod.WEIGHTED
        
        # Performance tracking
        self.prediction_history: List[EnsemblePrediction] = []
        
        # Initialize default models
        self._initialize_default_models()
        
        logger.info("EnsembleMetaLearner initialized")
    
    def _initialize_default_models(self):
        """Initialize default ensemble models"""
        
        # Random Forest
        rf_model = SklearnModel(
            'rf_1', 'RandomForest', ModelType.RANDOM_FOREST,
            n_estimators=100, max_depth=10
        )
        self.add_model(rf_model)
        
        # Gradient Boosting
        gb_model = SklearnModel(
            'gb_1', 'GradientBoosting', ModelType.GRADIENT_BOOSTING,
            n_estimators=100, max_depth=5
        )
        self.add_model(gb_model)
        
        # Logistic Regression
        lr_model = SklearnModel(
            'lr_1', 'LogisticRegression', ModelType.LOGISTIC
        )
        self.add_model(lr_model)
        
        # Neural Network
        if TORCH_AVAILABLE:
            nn_model = NeuralModel('nn_1', 'NeuralNetwork', input_dim=10)
            self.add_model(nn_model)
        
        # Rule-based model
        rule_model = RuleBasedModel('rule_1', 'RuleBased')
        rule_model.add_rule(lambda x: x[0] > 0 if len(x) > 0 else False)  # Simple rule
        self.add_model(rule_model)
    
    def add_model(self, model: BaseModel):
        """Add a model to the ensemble"""
        
        self.base_models[model.model_id] = model
        self.models[model.model_id] = ModelInfo(
            model_id=model.model_id,
            model_type=model.model_type if hasattr(model, 'model_type') else ModelType.RULE_BASED,
            name=model.name,
            model=model
        )
        
        # Add to stacked ensemble
        self.stacked_ensemble.add_base_model(model)
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        regime_labels: Optional[np.ndarray] = None
    ):
        """Fit all ensemble models"""
        
        logger.info("Fitting ensemble models...")
        
        # Fit individual models
        for model_id, model in self.base_models.items():
            model.fit(X, y)
            
            # Evaluate performance
            if model.is_fitted:
                preds = model.predict(X)
                self.models[model_id].accuracy = accuracy_score(y, preds)
                self.models[model_id].f1_score = f1_score(y, preds, average='weighted')
                self.models[model_id].last_trained = datetime.now()
                self.models[model_id].training_samples = len(X)
        
        # Fit stacked ensemble
        self.stacked_ensemble.fit(X, y)
        
        # Fit regime-specific ensemble if labels provided
        if regime_labels is not None:
            self.regime_ensemble.fit(X, y, regime_labels)
        
        # Optimize weights
        model_predictions = {}
        for model_id, model in self.base_models.items():
            if model.is_fitted:
                model_predictions[model_id] = model.predict(X)
        
        optimized_weights = self.weight_optimizer.optimize_weights(
            model_predictions, y, method='sharpe'
        )
        
        for model_id, weight in optimized_weights.items():
            self.models[model_id].weight = weight
        
        logger.info(f"Ensemble fitted with {len(self.base_models)} models")
    
    def predict(
        self,
        X: np.ndarray,
        voting_method: Optional[VotingMethod] = None,
        regime: Optional[RegimeType] = None
    ) -> EnsemblePrediction:
        """Make ensemble prediction"""
        
        if voting_method is None:
            voting_method = self.voting_method
        
        if regime is not None:
            self.current_regime = regime
            self.regime_ensemble.set_regime(regime)
        
        # Get individual predictions
        model_predictions = {}
        model_confidences = {}
        
        for model_id, model in self.base_models.items():
            if model.is_fitted:
                pred = model.predict(X)
                proba = model.predict_proba(X)
                
                model_predictions[model_id] = pred
                model_confidences[model_id] = np.max(proba, axis=1).mean()
        
        # Aggregate based on voting method
        if voting_method == VotingMethod.HARD:
            prediction, confidence = self._hard_vote(model_predictions)
        elif voting_method == VotingMethod.SOFT:
            prediction, confidence = self._soft_vote(X)
        elif voting_method == VotingMethod.WEIGHTED:
            prediction, confidence = self._weighted_vote(model_predictions)
        elif voting_method == VotingMethod.CONFIDENCE:
            prediction, confidence = self._confidence_vote(model_predictions, model_confidences)
        elif voting_method == VotingMethod.CONSENSUS:
            prediction, confidence = self._consensus_vote(model_predictions)
        else:
            prediction, confidence = self._weighted_vote(model_predictions)
        
        # Calculate agreement
        if model_predictions:
            pred_values = list(model_predictions.values())
            agreement = np.mean([
                np.mean(p == prediction) for p in pred_values
            ])
        else:
            agreement = 0.0
        
        result = EnsemblePrediction(
            timestamp=datetime.now(),
            prediction=prediction,
            confidence=confidence,
            model_predictions={k: v.tolist() if isinstance(v, np.ndarray) else v 
                            for k, v in model_predictions.items()},
            model_confidences=model_confidences,
            voting_method=voting_method,
            agreement_ratio=agreement,
            current_regime=self.current_regime
        )
        
        self.prediction_history.append(result)
        
        return result
    
    def _hard_vote(
        self,
        predictions: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, float]:
        """Hard voting (majority)"""
        
        if not predictions:
            return np.array([0]), 0.5
        
        pred_matrix = np.column_stack(list(predictions.values()))
        
        # Majority vote
        prediction = (pred_matrix.mean(axis=1) > 0.5).astype(int)
        
        # Confidence is agreement ratio
        confidence = np.abs(pred_matrix.mean(axis=1) - 0.5) * 2
        
        return prediction, confidence.mean()
    
    def _soft_vote(self, X: np.ndarray) -> Tuple[np.ndarray, float]:
        """Soft voting (probability average)"""
        
        probas = []
        for model in self.base_models.values():
            if model.is_fitted:
                probas.append(model.predict_proba(X))
        
        if not probas:
            return np.array([0]), 0.5
        
        avg_proba = np.mean(probas, axis=0)
        prediction = avg_proba.argmax(axis=1)
        confidence = avg_proba.max(axis=1).mean()
        
        return prediction, confidence
    
    def _weighted_vote(
        self,
        predictions: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, float]:
        """Weighted voting"""
        
        if not predictions:
            return np.array([0]), 0.5
        
        weighted_sum = np.zeros(len(list(predictions.values())[0]))
        total_weight = 0
        
        for model_id, pred in predictions.items():
            weight = self.models[model_id].weight
            weighted_sum += pred * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
        else:
            weighted_avg = weighted_sum
        
        prediction = (weighted_avg > 0.5).astype(int)
        confidence = np.abs(weighted_avg - 0.5).mean() * 2
        
        return prediction, confidence
    
    def _confidence_vote(
        self,
        predictions: Dict[str, np.ndarray],
        confidences: Dict[str, float]
    ) -> Tuple[np.ndarray, float]:
        """Use most confident model"""
        
        if not predictions or not confidences:
            return np.array([0]), 0.5
        
        # Find most confident model
        best_model = max(confidences.items(), key=lambda x: x[1])
        
        return predictions[best_model[0]], best_model[1]
    
    def _consensus_vote(
        self,
        predictions: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, float]:
        """Require consensus (high agreement)"""
        
        if not predictions:
            return np.array([0]), 0.5
        
        pred_matrix = np.column_stack(list(predictions.values()))
        
        # Check agreement
        agreement = np.abs(pred_matrix.mean(axis=1) - 0.5) * 2
        
        # Only predict when agreement is high
        prediction = np.where(
            agreement > 0.6,
            (pred_matrix.mean(axis=1) > 0.5).astype(int),
            -1  # No prediction
        )
        
        confidence = agreement.mean()
        
        return prediction, confidence
    
    def set_regime(self, regime: RegimeType):
        """Set current market regime"""
        self.current_regime = regime
        self.regime_ensemble.set_regime(regime)
        
        # Update weights for regime
        regime_weights = self.weight_optimizer.calculate_regime_weights(
            self.models, regime
        )
        
        for model_id, weight in regime_weights.items():
            self.models[model_id].weight = weight
    
    def update_model_performance(
        self,
        model_id: str,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        regime: Optional[RegimeType] = None
    ):
        """Update model performance metrics"""
        
        if model_id not in self.models:
            return
        
        info = self.models[model_id]
        
        # Update overall metrics
        info.accuracy = accuracy_score(y_true, y_pred)
        info.f1_score = f1_score(y_true, y_pred, average='weighted')
        
        # Update regime-specific performance
        if regime:
            info.regime_performance[regime.name] = info.accuracy
    
    def get_model_rankings(self) -> List[Tuple[str, float, Dict]]:
        """Get model rankings by performance"""
        
        rankings = []
        
        for model_id, info in self.models.items():
            rankings.append((
                model_id,
                info.weight,
                {
                    'accuracy': info.accuracy,
                    'f1_score': info.f1_score,
                    'regime_performance': info.regime_performance
                }
            ))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def get_ensemble_status(self) -> Dict[str, Any]:
        """Get ensemble status"""
        
        return {
            'total_models': len(self.models),
            'current_regime': self.current_regime.name,
            'voting_method': self.voting_method.name,
            'model_weights': {k: v.weight for k, v in self.models.items()},
            'model_accuracies': {k: v.accuracy for k, v in self.models.items()},
            'prediction_count': len(self.prediction_history)
        }


# Factory function
def create_ensemble(config: Optional[Dict] = None) -> EnsembleMetaLearner:
    """Create and return an EnsembleMetaLearner instance"""
    return EnsembleMetaLearner(config)
