"""
from typing import Dict, List, Optional, Set, Tuple
Uncertainty Quantification Module
=================================
Advanced uncertainty estimation for predictions.

Methods:
- Monte Carlo Dropout
- Quantile Regression
- Bootstrap Ensembles
- Prediction Intervals
- Conformal Prediction

Tracking:
- Sharpness decay
- Win-rate decay
- Residual drift
- Regime mismatch
- Seasonality decay
- Drawdown clustering

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.special import erfinv
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import cross_val_predict
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class UncertaintyType(Enum):
    """Types of uncertainty"""
    ALEATORIC = auto()   # Data uncertainty
    EPISTEMIC = auto()   # Model uncertainty
    TOTAL = auto()


class DecayType(Enum):
    """Types of performance decay"""
    SHARPNESS = auto()
    WIN_RATE = auto()
    RESIDUAL_DRIFT = auto()
    REGIME_MISMATCH = auto()
    SEASONALITY = auto()
    DRAWDOWN_CLUSTER = auto()


@dataclass
class PredictionInterval:
    """Prediction with uncertainty interval"""
    timestamp: datetime
    
    # Point prediction
    prediction: float
    
    # Intervals
    lower_50: float = 0.0
    upper_50: float = 0.0
    lower_90: float = 0.0
    upper_90: float = 0.0
    lower_95: float = 0.0
    upper_95: float = 0.0
    
    # Uncertainty decomposition
    aleatoric_uncertainty: float = 0.0
    epistemic_uncertainty: float = 0.0
    total_uncertainty: float = 0.0
    
    # Confidence
    confidence: float = 0.5


@dataclass
class DecayMetrics:
    """Performance decay metrics"""
    timestamp: datetime
    
    # Decay values
    sharpness_decay: float = 0.0
    win_rate_decay: float = 0.0
    residual_drift: float = 0.0
    regime_mismatch: float = 0.0
    seasonality_decay: float = 0.0
    drawdown_clustering: float = 0.0
    
    # Overall health
    model_health: float = 1.0
    retrain_recommended: bool = False


class MCDropoutPredictor(nn.Module):
    """Monte Carlo Dropout for uncertainty estimation"""
    
    def __init__(self, input_dim: int = 10, hidden_dim: int = 64, dropout_rate: float = 0.2):
        super().__init__()
        
        self.dropout_rate = dropout_rate
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, x, training: bool = True):
        if training:
            return self.network(x)
        else:
            # Enable dropout during inference for MC sampling
            self.train()
            return self.network(x)
    
    def predict_with_uncertainty(
        self,
        x: torch.Tensor,
        n_samples: int = 100
    ) -> Tuple[float, float, float]:
        """Predict with MC Dropout uncertainty"""
        
        self.train()  # Enable dropout
        
        predictions = []
        for _ in range(n_samples):
            with torch.no_grad():
                pred = self.network(x)
                predictions.append(pred.numpy())
        
        predictions = np.array(predictions).flatten()
        
        mean_pred = np.mean(predictions)
        epistemic = np.var(predictions)  # Model uncertainty
        
        return mean_pred, epistemic, np.std(predictions)


class QuantileRegressor:
    """Quantile regression for prediction intervals"""
    
    def __init__(self, quantiles: List[float] = None):
        self.quantiles = quantiles or [0.025, 0.05, 0.25, 0.5, 0.75, 0.95, 0.975]
        self.models: Dict[float, Any] = {}
        self.is_fitted = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit quantile regressors"""
        
        if not SKLEARN_AVAILABLE:
            return
        
        for q in self.quantiles:
            model = GradientBoostingRegressor(
                loss='quantile',
                alpha=q,
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            model.fit(X, y)
            self.models[q] = model
        
        self.is_fitted = True
    
    def predict_intervals(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict with quantile intervals"""
        
        if not self.is_fitted:
            return {}
        
        predictions = {}
        for q, model in self.models.items():
            predictions[f'q{int(q*100)}'] = model.predict(X)
        
        return predictions
    
    def get_prediction_interval(
        self,
        X: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get prediction interval at confidence level"""
        
        if not self.is_fitted:
            return np.zeros(len(X)), np.zeros(len(X)), np.zeros(len(X))
        
        alpha = (1 - confidence) / 2
        
        lower_q = alpha
        upper_q = 1 - alpha
        median_q = 0.5
        
        # Find closest quantiles
        lower_key = min(self.quantiles, key=lambda x: abs(x - lower_q))
        upper_key = min(self.quantiles, key=lambda x: abs(x - upper_q))
        median_key = min(self.quantiles, key=lambda x: abs(x - median_q))
        
        lower = self.models[lower_key].predict(X)
        upper = self.models[upper_key].predict(X)
        median = self.models[median_key].predict(X)
        
        return lower, median, upper


class BootstrapEnsemble:
    """Bootstrap ensemble for uncertainty"""
    
    def __init__(self, n_estimators: int = 50, base_model_class: Any = None):
        self.n_estimators = n_estimators
        self.base_model_class = base_model_class
        self.models: List[Any] = []
        self.is_fitted = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit bootstrap ensemble"""
        
        if not SKLEARN_AVAILABLE:
            return
        
        n_samples = len(X)
        
        for i in range(self.n_estimators):
            # Bootstrap sample
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_boot = X[indices]
            y_boot = y[indices]
            
            # Fit model
            if self.base_model_class:
                model = self.base_model_class()
            else:
                model = GradientBoostingRegressor(
                    n_estimators=50,
                    max_depth=4,
                    random_state=i
                )
            
            model.fit(X_boot, y_boot)
            self.models.append(model)
        
        self.is_fitted = True
    
    def predict_with_uncertainty(
        self,
        X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with bootstrap uncertainty"""
        
        if not self.is_fitted:
            return np.zeros(len(X)), np.zeros(len(X)), np.zeros(len(X))
        
        predictions = np.array([model.predict(X) for model in self.models])
        
        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)
        
        # Epistemic uncertainty from bootstrap variance
        epistemic = std_pred
        
        return mean_pred, epistemic, std_pred


class ConformalPredictor:
    """Conformal prediction for valid intervals"""
    
    def __init__(self, base_model: Any = None):
        self.base_model = base_model
        self.calibration_scores: List[float] = []
        self.is_calibrated = False
        
    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        """Fit base model"""
        if self.base_model is None and SKLEARN_AVAILABLE:
            self.base_model = GradientBoostingRegressor(n_estimators=100)
        
        if self.base_model:
            self.base_model.fit(X_train, y_train)
    
    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray):
        """Calibrate with holdout set"""
        
        if self.base_model is None:
            return
        
        predictions = self.base_model.predict(X_cal)
        
        # Non-conformity scores (absolute residuals)
        self.calibration_scores = np.abs(y_cal - predictions).tolist()
        self.is_calibrated = True
    
    def predict_interval(
        self,
        X: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with conformal interval"""
        
        if not self.is_calibrated or self.base_model is None:
            return np.zeros(len(X)), np.zeros(len(X)), np.zeros(len(X))
        
        predictions = self.base_model.predict(X)
        
        # Get quantile of calibration scores
        q = np.percentile(self.calibration_scores, confidence * 100)
        
        lower = predictions - q
        upper = predictions + q
        
        return lower, predictions, upper


class DecayTracker:
    """Track various types of performance decay"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # History
        self.prediction_history: deque = deque(maxlen=1000)
        self.actual_history: deque = deque(maxlen=1000)
        self.regime_history: deque = deque(maxlen=1000)
        self.pnl_history: deque = deque(maxlen=1000)
        
        # Baseline metrics
        self.baseline_sharpness: float = 0.0
        self.baseline_win_rate: float = 0.5
        self.baseline_residual_std: float = 0.0
        
    def add_prediction(
        self,
        prediction: float,
        actual: float,
        regime: str = "",
        pnl: float = 0.0
    ):
        """Add prediction-actual pair"""
        
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'actual': actual
        })
        self.actual_history.append(actual)
        self.regime_history.append(regime)
        self.pnl_history.append(pnl)
    
    def set_baseline(self):
        """Set baseline metrics from current history"""
        
        if len(self.prediction_history) < 50:
            return
        
        preds = [p['prediction'] for p in self.prediction_history]
        actuals = [p['actual'] for p in self.prediction_history]
        
        # Sharpness (prediction variance)
        self.baseline_sharpness = np.std(preds)
        
        # Win rate
        correct = sum(1 for p, a in zip(preds, actuals) if np.sign(p) == np.sign(a))
        self.baseline_win_rate = correct / len(preds)
        
        # Residual std
        residuals = np.array(actuals) - np.array(preds)
        self.baseline_residual_std = np.std(residuals)
    
    def calculate_decay(self, lookback: int = 100) -> DecayMetrics:
        """Calculate all decay metrics"""
        
        if len(self.prediction_history) < lookback:
            return DecayMetrics(timestamp=datetime.now())
        
        recent = list(self.prediction_history)[-lookback:]
        preds = [p['prediction'] for p in recent]
        actuals = [p['actual'] for p in recent]
        
        # Sharpness decay
        current_sharpness = np.std(preds)
        if self.baseline_sharpness > 0:
            sharpness_decay = 1 - current_sharpness / self.baseline_sharpness
        else:
            sharpness_decay = 0
        
        # Win rate decay
        correct = sum(1 for p, a in zip(preds, actuals) if np.sign(p) == np.sign(a))
        current_win_rate = correct / len(preds)
        win_rate_decay = self.baseline_win_rate - current_win_rate
        
        # Residual drift
        residuals = np.array(actuals) - np.array(preds)
        residual_mean = np.mean(residuals)
        residual_drift = abs(residual_mean) / (self.baseline_residual_std + 1e-10)
        
        # Regime mismatch
        recent_regimes = list(self.regime_history)[-lookback:]
        if recent_regimes:
            regime_changes = sum(1 for i in range(1, len(recent_regimes)) 
                               if recent_regimes[i] != recent_regimes[i-1])
            regime_mismatch = regime_changes / len(recent_regimes)
        else:
            regime_mismatch = 0
        
        # Seasonality decay (compare to same time period)
        seasonality_decay = self._calculate_seasonality_decay(recent)
        
        # Drawdown clustering
        pnls = list(self.pnl_history)[-lookback:]
        drawdown_clustering = self._calculate_drawdown_clustering(pnls)
        
        # Overall health
        health_factors = [
            1 - abs(sharpness_decay),
            1 - abs(win_rate_decay),
            1 - min(residual_drift, 1),
            1 - regime_mismatch,
            1 - seasonality_decay,
            1 - drawdown_clustering
        ]
        model_health = np.mean(health_factors)
        
        # Retrain recommendation
        retrain_recommended = (
            model_health < 0.6 or
            abs(win_rate_decay) > 0.1 or
            residual_drift > 2.0
        )
        
        return DecayMetrics(
            timestamp=datetime.now(),
            sharpness_decay=sharpness_decay,
            win_rate_decay=win_rate_decay,
            residual_drift=residual_drift,
            regime_mismatch=regime_mismatch,
            seasonality_decay=seasonality_decay,
            drawdown_clustering=drawdown_clustering,
            model_health=model_health,
            retrain_recommended=retrain_recommended
        )
    
    def _calculate_seasonality_decay(self, recent: List[Dict]) -> float:
        """Calculate seasonality-related decay"""
        
        if len(recent) < 20:
            return 0
        
        # Group by hour of day
        hourly_errors = {}
        for p in recent:
            hour = p['timestamp'].hour
            error = abs(p['actual'] - p['prediction'])
            if hour not in hourly_errors:
                hourly_errors[hour] = []
            hourly_errors[hour].append(error)
        
        if len(hourly_errors) < 5:
            return 0
        
        # Check for systematic hourly patterns
        hourly_means = [np.mean(errors) for errors in hourly_errors.values()]
        cv = np.std(hourly_means) / (np.mean(hourly_means) + 1e-10)
        
        return min(cv, 1.0)
    
    def _calculate_drawdown_clustering(self, pnls: List[float]) -> float:
        """Calculate drawdown clustering"""
        
        if len(pnls) < 20:
            return 0
        
        # Find consecutive losses
        max_consecutive = 0
        current_consecutive = 0
        
        for pnl in pnls:
            if pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        # Normalize (5+ consecutive losses is concerning)
        return min(max_consecutive / 5, 1.0)


class UncertaintyQuantifier:
    """
    Complete Uncertainty Quantification Module.
    
    Methods:
    - Monte Carlo Dropout
    - Quantile Regression
    - Bootstrap Ensembles
    - Conformal Prediction
    
    Tracking:
    - Sharpness decay
    - Win-rate decay
    - Residual drift
    - Regime mismatch
    - Seasonality decay
    - Drawdown clustering
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Uncertainty estimators
        self.mc_dropout = None
        if TORCH_AVAILABLE:
            self.mc_dropout = MCDropoutPredictor(
                input_dim=self.config.get('input_dim', 10)
            )
        
        self.quantile_regressor = QuantileRegressor()
        self.bootstrap_ensemble = BootstrapEnsemble(
            n_estimators=self.config.get('n_bootstrap', 50)
        )
        self.conformal_predictor = ConformalPredictor()
        
        # Decay tracker
        self.decay_tracker = DecayTracker(config)
        
        # History
        self.interval_history: List[PredictionInterval] = []
        
        logger.info("UncertaintyQuantifier initialized")
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_cal: np.ndarray = None,
        y_cal: np.ndarray = None
    ):
        """Fit all uncertainty estimators"""
        
        # Fit quantile regressor
        self.quantile_regressor.fit(X_train, y_train)
        
        # Fit bootstrap ensemble
        self.bootstrap_ensemble.fit(X_train, y_train)
        
        # Fit and calibrate conformal predictor
        self.conformal_predictor.fit(X_train, y_train)
        if X_cal is not None and y_cal is not None:
            self.conformal_predictor.calibrate(X_cal, y_cal)
        
        # Fit MC Dropout
        if self.mc_dropout and TORCH_AVAILABLE:
            X_tensor = torch.FloatTensor(X_train)
            y_tensor = torch.FloatTensor(y_train).unsqueeze(1)
            
            optimizer = torch.optim.Adam(self.mc_dropout.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            for epoch in range(100):
                self.mc_dropout.train()
                optimizer.zero_grad()
                output = self.mc_dropout(X_tensor)
                loss = criterion(output, y_tensor)
                loss.backward()
                optimizer.step()
        
        logger.info("Uncertainty estimators fitted")
    
    def predict_with_uncertainty(
        self,
        X: np.ndarray,
        method: str = 'ensemble'
    ) -> PredictionInterval:
        """Predict with uncertainty estimation"""
        
        X = np.atleast_2d(X)
        
        if method == 'mc_dropout' and self.mc_dropout and TORCH_AVAILABLE:
            X_tensor = torch.FloatTensor(X)
            mean_pred, epistemic, std = self.mc_dropout.predict_with_uncertainty(X_tensor)
            
            # Assume aleatoric from residuals
            aleatoric = std * 0.5
            total = np.sqrt(epistemic + aleatoric**2)
            
        elif method == 'quantile':
            lower_95, median, upper_95 = self.quantile_regressor.get_prediction_interval(X, 0.95)
            lower_50, _, upper_50 = self.quantile_regressor.get_prediction_interval(X, 0.50)
            
            mean_pred = median[0]
            total = (upper_95[0] - lower_95[0]) / 4
            epistemic = total * 0.6
            aleatoric = total * 0.4
            
        elif method == 'conformal':
            lower_95, median, upper_95 = self.conformal_predictor.predict_interval(X, 0.95)
            
            mean_pred = median[0]
            total = (upper_95[0] - lower_95[0]) / 4
            epistemic = total * 0.5
            aleatoric = total * 0.5
            
        else:  # ensemble (default)
            mean_pred, epistemic, std = self.bootstrap_ensemble.predict_with_uncertainty(X)
            mean_pred = mean_pred[0]
            epistemic = epistemic[0]
            aleatoric = std[0] * 0.5
            total = np.sqrt(epistemic**2 + aleatoric**2)
        
        # Calculate intervals
        if SCIPY_AVAILABLE:
            z_50 = stats.norm.ppf(0.75)
            z_90 = stats.norm.ppf(0.95)
            z_95 = stats.norm.ppf(0.975)
        else:
            z_50, z_90, z_95 = 0.67, 1.65, 1.96
        
        interval = PredictionInterval(
            timestamp=datetime.now(),
            prediction=mean_pred,
            lower_50=mean_pred - z_50 * total,
            upper_50=mean_pred + z_50 * total,
            lower_90=mean_pred - z_90 * total,
            upper_90=mean_pred + z_90 * total,
            lower_95=mean_pred - z_95 * total,
            upper_95=mean_pred + z_95 * total,
            aleatoric_uncertainty=aleatoric,
            epistemic_uncertainty=epistemic,
            total_uncertainty=total,
            confidence=1 / (1 + total)
        )
        
        self.interval_history.append(interval)
        
        return interval
    
    def update_actuals(
        self,
        prediction: float,
        actual: float,
        regime: str = "",
        pnl: float = 0.0
    ):
        """Update with actual values for decay tracking"""
        self.decay_tracker.add_prediction(prediction, actual, regime, pnl)
    
    def get_decay_metrics(self, lookback: int = 100) -> DecayMetrics:
        """Get current decay metrics"""
        return self.decay_tracker.calculate_decay(lookback)
    
    def set_baseline(self):
        """Set baseline for decay tracking"""
        self.decay_tracker.set_baseline()
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get overall model health assessment"""
        
        decay = self.get_decay_metrics()
        
        return {
            'health_score': decay.model_health,
            'retrain_recommended': decay.retrain_recommended,
            'decay_breakdown': {
                'sharpness': decay.sharpness_decay,
                'win_rate': decay.win_rate_decay,
                'residual_drift': decay.residual_drift,
                'regime_mismatch': decay.regime_mismatch,
                'seasonality': decay.seasonality_decay,
                'drawdown_clustering': decay.drawdown_clustering
            },
            'recommendations': self._generate_recommendations(decay)
        }
    
    def _generate_recommendations(self, decay: DecayMetrics) -> List[str]:
        """Generate recommendations based on decay"""
        
        recommendations = []
        
        if decay.win_rate_decay > 0.1:
            recommendations.append("Win rate declining - consider retraining or strategy review")
        
        if decay.residual_drift > 1.5:
            recommendations.append("Significant residual drift - model may be biased")
        
        if decay.regime_mismatch > 0.3:
            recommendations.append("Frequent regime changes - consider regime-specific models")
        
        if decay.seasonality_decay > 0.5:
            recommendations.append("Seasonality patterns detected - add time-based features")
        
        if decay.drawdown_clustering > 0.6:
            recommendations.append("Drawdown clustering detected - review risk management")
        
        if decay.model_health < 0.5:
            recommendations.append("CRITICAL: Model health low - immediate retraining recommended")
        
        return recommendations


# Factory function
def create_uncertainty_quantifier(config: Optional[Dict] = None) -> UncertaintyQuantifier:
    """Create and return an UncertaintyQuantifier instance"""
    return UncertaintyQuantifier(config)
