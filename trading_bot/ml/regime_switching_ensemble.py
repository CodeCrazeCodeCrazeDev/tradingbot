import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""Regime-Switching Model Ensembles

This module implements a system that combines multiple models (statistical, ML, deep learning, rule-based)
and dynamically switches or blends them based on detected market regimes.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
import xgboost as xgb
from loguru import logger

from trading_bot.adaptive_systems.market_regime import MarketRegime, MarketRegimeDetector
import pathlib
import numpy
import pandas


class ModelType(Enum):
    """Types of models in the ensemble."""
    STATISTICAL = auto()
    MACHINE_LEARNING = auto()
    DEEP_LEARNING = auto()
    RULE_BASED = auto()


@dataclass
class ModelInfo:
    """Information about a model in the ensemble."""
    name: str
    model_type: ModelType
    model: Any  # The actual model object
    predict_fn: Callable  # Function to call for predictions
    regime_weights: Dict[MarketRegime, float]  # Weight for each regime
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class RegimeSwitchingEnsemble:
    """Ensemble that switches or blends models based on market regime."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the regime-switching ensemble.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.models: Dict[str, ModelInfo] = {}
        self.regime_detector = MarketRegimeDetector(self.config.get('regime_detector_config', {}))
        self.default_regime = MarketRegime.RANGING
        self.current_regime = self.default_regime
        self.blend_models = self.config.get('blend_models', True)
        self.min_model_weight = self.config.get('min_model_weight', 0.1)
        
        # Initialize default models if specified
        if self.config.get('initialize_default_models', True):
            self._initialize_default_models()
        
        logger.info(f"RegimeSwitchingEnsemble initialized with blend_models={self.blend_models}")
    
    def _initialize_default_models(self):
        """Initialize a set of default models for the ensemble."""
        # Statistical models
        self.add_model(
            name="linear_regression",
            model_type=ModelType.STATISTICAL,
            model=LinearRegression(),
            predict_fn=lambda model, X: model.predict(X),
            regime_weights={
                MarketRegime.TRENDING_BULL: 0.6,
                MarketRegime.TRENDING_BEAR: 0.6,
                MarketRegime.RANGING: 0.8,
                MarketRegime.HIGH_VOLATILITY: 0.3,
                MarketRegime.LOW_VOLATILITY: 0.7,
                MarketRegime.BREAKOUT: 0.4,
                MarketRegime.REVERSAL: 0.5,
                MarketRegime.CRISIS: 0.2
            }
        )
        
        # Machine learning models
        self.add_model(
            name="random_forest",
            model_type=ModelType.MACHINE_LEARNING,
            model=RandomForestClassifier(n_estimators=100),
            predict_fn=lambda model, X: model.predict_proba(X)[:, 1],
            regime_weights={
                MarketRegime.TRENDING_BULL: 0.7,
                MarketRegime.TRENDING_BEAR: 0.7,
                MarketRegime.RANGING: 0.5,
                MarketRegime.HIGH_VOLATILITY: 0.6,
                MarketRegime.LOW_VOLATILITY: 0.4,
                MarketRegime.BREAKOUT: 0.8,
                MarketRegime.REVERSAL: 0.7,
                MarketRegime.CRISIS: 0.5
            }
        )
        
        self.add_model(
            name="gradient_boosting",
            model_type=ModelType.MACHINE_LEARNING,
            model=GradientBoostingRegressor(n_estimators=100),
            predict_fn=lambda model, X: model.predict(X),
            regime_weights={
                MarketRegime.TRENDING_BULL: 0.8,
                MarketRegime.TRENDING_BEAR: 0.8,
                MarketRegime.RANGING: 0.6,
                MarketRegime.HIGH_VOLATILITY: 0.7,
                MarketRegime.LOW_VOLATILITY: 0.5,
                MarketRegime.BREAKOUT: 0.9,
                MarketRegime.REVERSAL: 0.8,
                MarketRegime.CRISIS: 0.7
            }
        )
        
        self.add_model(
            name="xgboost",
            model_type=ModelType.MACHINE_LEARNING,
            model=xgb.XGBRegressor(n_estimators=100),
            predict_fn=lambda model, X: model.predict(X),
            regime_weights={
                MarketRegime.TRENDING_BULL: 0.9,
                MarketRegime.TRENDING_BEAR: 0.9,
                MarketRegime.RANGING: 0.7,
                MarketRegime.HIGH_VOLATILITY: 0.8,
                MarketRegime.LOW_VOLATILITY: 0.6,
                MarketRegime.BREAKOUT: 0.9,
                MarketRegime.REVERSAL: 0.9,
                MarketRegime.CRISIS: 0.8
            }
        )
        
        # Rule-based model (placeholder)
        self.add_model(
            name="rule_based",
            model_type=ModelType.RULE_BASED,
            model={"rules": self._default_trading_rules()},
            predict_fn=self._rule_based_predict,
            regime_weights={
                MarketRegime.TRENDING_BULL: 0.5,
                MarketRegime.TRENDING_BEAR: 0.5,
                MarketRegime.RANGING: 0.7,
                MarketRegime.HIGH_VOLATILITY: 0.8,
                MarketRegime.LOW_VOLATILITY: 0.6,
                MarketRegime.BREAKOUT: 0.6,
                MarketRegime.REVERSAL: 0.7,
                MarketRegime.CRISIS: 0.9
            }
        )
    
    def _default_trading_rules(self) -> List[Dict[str, Any]]:
        """Create default trading rules for the rule-based model."""
        return [
            {
                "name": "trend_following",
                "condition": lambda data: data['close'].iloc[-1] > data['sma_50'].iloc[-1] and data['macd_hist'].iloc[-1] > 0,
                "action": 1.0,  # Buy/bullish
                "regimes": [MarketRegime.TRENDING_BULL]
            },
            {
                "name": "counter_trend",
                "condition": lambda data: data['close'].iloc[-1] < data['sma_50'].iloc[-1] and data['macd_hist'].iloc[-1] < 0,
                "action": -1.0,  # Sell/bearish
                "regimes": [MarketRegime.TRENDING_BEAR]
            },
            {
                "name": "mean_reversion",
                "condition": lambda data: (data['close'].iloc[-1] - data['lower_band'].iloc[-1]) / (data['upper_band'].iloc[-1] - data['lower_band'].iloc[-1]) < 0.2,
                "action": 1.0,  # Buy/bullish
                "regimes": [MarketRegime.RANGING]
            },
            {
                "name": "volatility_breakout",
                "condition": lambda data: data['atr'].iloc[-1] > 1.5 * data['atr'].iloc[-20:].mean() and data['volume'].iloc[-1] > 1.5 * data['volume'].iloc[-20:].mean(),
                "action": lambda data: 1.0 if data['close'].iloc[-1] > data['open'].iloc[-1] else -1.0,
                "regimes": [MarketRegime.BREAKOUT, MarketRegime.HIGH_VOLATILITY]
            },
            {
                "name": "crisis_defense",
                "condition": lambda data: data['atr'].iloc[-1] > 2.5 * data['atr'].iloc[-60:].mean() and data['close'].iloc[-1] < data['sma_200'].iloc[-1],
                "action": -1.0,  # Sell/bearish
                "regimes": [MarketRegime.CRISIS]
            }
        ]
    
    def _rule_based_predict(self, model: Dict[str, Any], X: pd.DataFrame) -> np.ndarray:
        """Prediction function for rule-based models.
        
        Args:
            model: Rule-based model dictionary
            X: Feature dataframe
            
        Returns:
            Numpy array of predictions
        """
        rules = model['rules']
        predictions = np.zeros(len(X))
        
        # Apply each rule that matches the current regime
        for rule in rules:
            if self.current_regime in rule['regimes']:
                try:
                    if rule['condition'](X):
                        predictions += rule['action']
                except Exception as e:
                    logger.error(f"Error applying rule {rule['name']}: {e}")
        
        # Normalize predictions to [-1, 1] range
        predictions = np.clip(predictions, -1, 1)
        return predictions
    
    def add_model(self, name: str, model_type: ModelType, model: Any, 
                predict_fn: Callable, regime_weights: Dict[MarketRegime, float]):
        """Add a model to the ensemble.
        
        Args:
            name: Model name
            model_type: Type of model
            model: The model object
            predict_fn: Function to call for predictions
            regime_weights: Dictionary mapping regimes to weights
        """
        # Ensure weights are valid
        for regime in MarketRegime:
            if regime not in regime_weights:
                regime_weights[regime] = 0.5  # Default weight
        
        # Create model info
        model_info = ModelInfo(
            name=name,
            model_type=model_type,
            model=model,
            predict_fn=predict_fn,
            regime_weights=regime_weights
        )
        
        # Add to models dictionary
        self.models[name] = model_info
        logger.info(f"Added model '{name}' of type {model_type.name} to ensemble")
    
    def remove_model(self, name: str):
        """Remove a model from the ensemble.
        
        Args:
            name: Model name
        """
        if name in self.models:
            del self.models[name]
            logger.info(f"Removed model '{name}' from ensemble")
        else:
            logger.warning(f"Model '{name}' not found in ensemble")
    
    def update_regime(self, market_data: pd.DataFrame) -> MarketRegime:
        """Update the current market regime.
        
        Args:
            market_data: DataFrame with market data
            
        Returns:
            Detected market regime
        """
        regime_signal = self.regime_detector.detect_regime(market_data)
        self.current_regime = regime_signal.regime
        logger.info(f"Updated market regime to {self.current_regime.value} (confidence: {regime_signal.confidence:.2f})")
        return self.current_regime
    
    def predict(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Make predictions using the ensemble.
        
        Args:
            X: Feature dataframe
            
        Returns:
            Dictionary with prediction results
        """
        if not self.models:
            logger.warning("No models in ensemble")
            return {'prediction': 0.0, 'confidence': 0.0, 'models_used': []}
        
        # Get weights for current regime
        weights = {name: info.regime_weights.get(self.current_regime, 0.0) 
                  for name, info in self.models.items()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {name: weight / total_weight for name, weight in weights.items()}
        
        # If not blending, select the best model for this regime
        if not self.blend_models:
            best_model_name = max(weights.items(), key=lambda x: x[1])[0]
            weights = {name: 1.0 if name == best_model_name else 0.0 for name in weights}
            logger.info(f"Selected model '{best_model_name}' for regime {self.current_regime.value}")
        
        # Make predictions with each model
        predictions = {}
        for name, info in self.models.items():
            if weights[name] >= self.min_model_weight:
                try:
                    pred = info.predict_fn(info.model, X)
                    predictions[name] = pred
                except Exception as e:
                    logger.error(f"Error predicting with model '{name}': {e}")
                    predictions[name] = np.zeros(len(X))
        
        # Combine predictions
        combined_prediction = np.zeros(len(X))
        models_used = []
        
        for name, pred in predictions.items():
            if weights[name] > 0:
                combined_prediction += pred * weights[name]
                models_used.append({
                    'name': name,
                    'weight': weights[name],
                    'type': self.models[name].model_type.name
                })
        
        # Calculate confidence based on agreement between models
        if len(predictions) > 1:
            # Convert predictions to -1/0/+1 for agreement calculation
            pred_signs = {name: np.sign(pred) for name, pred in predictions.items()}
            agreement = np.mean([np.mean(np.abs(pred_signs[name] - np.mean(list(pred_signs.values()), axis=0)))
                               for name in pred_signs])
            confidence = 1.0 - agreement
        else:
            confidence = 0.8  # Default confidence with single model
        
        return {
            'prediction': combined_prediction,
            'confidence': confidence,
            'models_used': models_used,
            'regime': self.current_regime.value
        }
    
    def train(self, X: pd.DataFrame, y: pd.DataFrame, model_names: Optional[List[str]] = None):
        """Train specified models in the ensemble.
        
        Args:
            X: Feature dataframe
            y: Target dataframe
            model_names: List of model names to train (None for all)
        """
        if model_names is None:
            model_names = list(self.models.keys())
        
        for name in model_names:
            if name in self.models:
                info = self.models[name]
                
                # Skip rule-based models
                if info.model_type == ModelType.RULE_BASED:
                    continue
                try:
                
                    # Train the model
                    info.model.fit(X, y)
                    info.last_updated = datetime.now()
                    logger.info(f"Trained model '{name}'")
                except Exception as e:
                    logger.error(f"Error training model '{name}': {e}")
            else:
                logger.warning(f"Model '{name}' not found in ensemble")
    
    def evaluate(self, X: pd.DataFrame, y: pd.DataFrame, model_names: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """Evaluate specified models in the ensemble.
        
        Args:
            X: Feature dataframe
            y: Target dataframe
            model_names: List of model names to evaluate (None for all)
            
        Returns:
            Dictionary mapping model names to performance metrics
        """
        if model_names is None:
            model_names = list(self.models.keys())
        
        results = {}
        
        for name in model_names:
            if name in self.models:
                info = self.models[name]
                
                try:
                    # Make predictions
                    y_pred = info.predict_fn(info.model, X)
                    
                    # Calculate metrics
                    metrics = self._calculate_metrics(y, y_pred)
                    
                    # Update model info
                    info.performance_metrics = metrics
                    results[name] = metrics
                    
                    logger.info(f"Evaluated model '{name}': {metrics}")
                except Exception as e:
                    logger.error(f"Error evaluating model '{name}': {e}")
            else:
                logger.warning(f"Model '{name}' not found in ensemble")
        
        return results
    
    def _calculate_metrics(self, y_true: pd.DataFrame, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics.
        
        Args:
            y_true: True target values
            y_pred: Predicted values
            
        Returns:
            Dictionary of metrics
        """
        # Convert to numpy arrays
        y_true_np = np.array(y_true)
        y_pred_np = np.array(y_pred)
        
        # Calculate metrics
        metrics = {}
        
        # Mean squared error
        metrics['mse'] = np.mean((y_true_np - y_pred_np) ** 2)
        
        # Mean absolute error
        metrics['mae'] = np.mean(np.abs(y_true_np - y_pred_np))
        
        # Directional accuracy (for classification)
        metrics['dir_acc'] = np.mean((y_true_np > 0) == (y_pred_np > 0))
        
        return metrics
    
    def save(self, filepath: str):
        """Save the ensemble to a file.
        
        Args:
            filepath: Path to save the ensemble
        """
        try:
            joblib.dump(self, filepath)
            logger.info(f"Saved ensemble to {filepath}")
        except Exception as e:
            logger.error(f"Error saving ensemble: {e}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RegimeSwitchingEnsemble':
        """Load an ensemble from a file.
        
        Args:
            filepath: Path to load the ensemble from
            
        Returns:
            Loaded ensemble
        """
        try:
            ensemble = joblib.load(filepath)
            logger.info(f"Loaded ensemble from {filepath}")
            return ensemble
        except Exception as e:
            logger.error(f"Error loading ensemble: {e}")
            return cls()  # Return a new instance
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current weights for all models based on the current regime.
        
        Returns:
            Dictionary mapping model names to weights
        """
        weights = {name: info.regime_weights.get(self.current_regime, 0.0) 
                  for name, info in self.models.items()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {name: weight / total_weight for name, weight in weights.items()}
        
        return weights
    
    def update_model_weights(self, name: str, regime_weights: Dict[MarketRegime, float]):
        """Update weights for a specific model.
        
        Args:
            name: Model name
            regime_weights: Dictionary mapping regimes to weights
        """
        if name in self.models:
            # Update weights
            for regime, weight in regime_weights.items():
                self.models[name].regime_weights[regime] = weight
            
            logger.info(f"Updated weights for model '{name}'")
        else:
            logger.warning(f"Model '{name}' not found in ensemble")
    
    def get_ensemble_info(self) -> Dict[str, Any]:
        """Get information about the ensemble.
        
        Returns:
            Dictionary with ensemble information
        """
        return {
            'current_regime': self.current_regime.value,
            'blend_models': self.blend_models,
            'models': {
                name: {
                    'type': info.model_type.name,
                    'weight_for_current_regime': info.regime_weights.get(self.current_regime, 0.0),
                    'performance_metrics': info.performance_metrics,
                    'last_updated': info.last_updated.isoformat()
                }
                for name, info in self.models.items()
            }
        }
