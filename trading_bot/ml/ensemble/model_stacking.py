"""
Ensemble Methods & Model Stacking

Combines multiple models (TFT, N-BEATS, LSTM, XGBoost) for robust predictions.
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple models
    
    Methods:
    - Simple averaging
    - Weighted averaging
    - Stacking with meta-learner
    - Variance reduction
    """
    
    def __init__(self, models: List, model_names: List[str]):
        """
        Args:
            models: List of trained models
            model_names: Names of models
        """
        self.models = models
        self.model_names = model_names
        self.weights = None
        self.meta_model = None
    
    def predict_average(self, X: np.ndarray) -> np.ndarray:
        """Simple average of all model predictions"""
        predictions = []
        
        for model in self.models:
            pred = self._get_prediction(model, X)
            predictions.append(pred)
        
        # Average
        ensemble_pred = np.mean(predictions, axis=0)
        
        logger.debug(f"Ensemble prediction (average): {ensemble_pred.mean():.4f}")
        
        return ensemble_pred
    
    def predict_weighted(self, X: np.ndarray, weights: Optional[np.ndarray] = None) -> np.ndarray:
        """Weighted average of model predictions"""
        if weights is None:
            weights = self.weights if self.weights is not None else np.ones(len(self.models)) / len(self.models)
        
        predictions = []
        
        for model in self.models:
            pred = self._get_prediction(model, X)
            predictions.append(pred)
        
        # Weighted average
        predictions = np.array(predictions)
        ensemble_pred = np.average(predictions, axis=0, weights=weights)
        
        logger.debug(f"Ensemble prediction (weighted): {ensemble_pred.mean():.4f}")
        
        return ensemble_pred
    
    def predict_stacked(self, X: np.ndarray) -> np.ndarray:
        """Stacking with meta-learner"""
        if self.meta_model is None:
            logger.warning("Meta-model not trained. Using weighted average.")
            return self.predict_weighted(X)
        
        # Get base model predictions
        base_predictions = []
        
        for model in self.models:
            pred = self._get_prediction(model, X)
            base_predictions.append(pred)
        
        # Stack predictions as features for meta-model
        stacked_features = np.column_stack(base_predictions)
        
        # Meta-model prediction
        ensemble_pred = self.meta_model.predict(stacked_features)
        
        logger.debug(f"Ensemble prediction (stacked): {ensemble_pred.mean():.4f}")
        
        return ensemble_pred
    
    def train_stacking(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray
    ):
        """
        Train stacking meta-model
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
        """
        # Get base model predictions on validation set
        base_predictions_train = []
        base_predictions_val = []
        
        for model in self.models:
            pred_train = self._get_prediction(model, X_train)
            pred_val = self._get_prediction(model, X_val)
            
            base_predictions_train.append(pred_train)
            base_predictions_val.append(pred_val)
        
        # Stack predictions
        stacked_train = np.column_stack(base_predictions_train)
        stacked_val = np.column_stack(base_predictions_val)
        
        # Train meta-model (simple linear regression)
        from sklearn.linear_model import Ridge
        
        self.meta_model = Ridge(alpha=1.0)
        self.meta_model.fit(stacked_train, y_train)
        
        # Evaluate
        val_pred = self.meta_model.predict(stacked_val)
        mse = np.mean((val_pred - y_val)**2)
        
        logger.info(f"Meta-model trained. Validation MSE: {mse:.6f}")
        logger.info(f"Meta-model weights: {self.meta_model.coef_}")
    
    def optimize_weights(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray
    ) -> np.ndarray:
        """
        Optimize ensemble weights to minimize validation error
        
        Args:
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Optimal weights
        """
        from scipy.optimize import minimize
        
        # Get base predictions
        base_predictions = []
        
        for model in self.models:
            pred = self._get_prediction(model, X_val)
            base_predictions.append(pred)
        
        base_predictions = np.array(base_predictions)
        
        # Objective: minimize MSE
        def objective(weights):
            ensemble_pred = np.average(base_predictions, axis=0, weights=weights)
            mse = np.mean((ensemble_pred - y_val)**2)
            return mse
        
        # Constraints: weights sum to 1, all non-negative
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = [(0, 1) for _ in range(len(self.models))]
        
        # Initial guess: equal weights
        w0 = np.ones(len(self.models)) / len(self.models)
        
        # Optimize
        result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        self.weights = result.x
        
        logger.info(f"Optimized weights: {dict(zip(self.model_names, self.weights))}")
        
        return self.weights
    
    def _get_prediction(self, model, X: np.ndarray) -> np.ndarray:
        """Get prediction from a model (handles different model types)"""
        try:
            # PyTorch model
            if isinstance(model, nn.Module):
                model.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X)
                    pred = model(X_tensor).cpu().numpy()
                return pred.flatten()
            
            # Sklearn-like model
            elif hasattr(model, 'predict'):
                pred = model.predict(X)
                return pred.flatten() if len(pred.shape) > 1 else pred
            
            # Custom model
            else:
                return model(X).flatten()
                
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return np.zeros(len(X))
    
    def get_prediction_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get prediction with uncertainty estimate
        
        Returns:
            Tuple of (mean_prediction, std_prediction)
        """
        predictions = []
        
        for model in self.models:
            pred = self._get_prediction(model, X)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)
        
        return mean_pred, std_pred


class VarianceReduction:
    """
    Variance reduction techniques for ensemble
    
    - Bootstrap aggregating (Bagging)
    - Boosting
    - Dropout ensembles
    """
    
    @staticmethod
    def bootstrap_predictions(
        model,
        X: np.ndarray,
        n_bootstrap: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Bootstrap predictions for uncertainty estimation
        
        Args:
            model: Model to use
            X: Input features
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            Tuple of (mean, std)
        """
        predictions = []
        
        for _ in range(n_bootstrap):
            # Bootstrap sample
            indices = np.random.choice(len(X), len(X), replace=True)
            X_boot = X[indices]
            
            # Predict
            if isinstance(model, nn.Module):
                model.eval()
                with torch.no_grad():
                    pred = model(torch.FloatTensor(X_boot)).cpu().numpy()
            else:
                pred = model.predict(X_boot)
            
            predictions.append(pred.flatten())
        
        predictions = np.array(predictions)
        
        mean = np.mean(predictions, axis=0)
        std = np.std(predictions, axis=0)
        
        return mean, std
    
    @staticmethod
    def dropout_ensemble(
        model: nn.Module,
        X: torch.Tensor,
        n_samples: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo Dropout for uncertainty
        
        Args:
            model: Neural network with dropout
            X: Input tensor
            n_samples: Number of forward passes
            
        Returns:
            Tuple of (mean, std)
        """
        model.train()  # Keep dropout active
        
        predictions = []
        
        with torch.no_grad():
            for _ in range(n_samples):
                pred = model(X).cpu().numpy()
                predictions.append(pred.flatten())
        
        predictions = np.array(predictions)
        
        mean = np.mean(predictions, axis=0)
        std = np.std(predictions, axis=0)
        
        return mean, std


class ModelSelector:
    """
    Adaptive model selection based on market conditions
    
    Selects best model for current regime
    """
    
    def __init__(self, models: List, model_names: List[str]):
        self.models = models
        self.model_names = model_names
        self.performance_history = {name: [] for name in model_names}
    
    def select_best_model(
        self,
        market_regime: str,
        recent_performance: Optional[Dict[str, float]] = None
    ) -> Tuple[object, str]:
        """
        Select best model for current market regime
        
        Args:
            market_regime: Current market regime ('trending', 'ranging', 'volatile')
            recent_performance: Recent performance metrics per model
            
        Returns:
            Tuple of (best_model, model_name)
        """
        if recent_performance:
            # Select based on recent performance
            best_name = max(recent_performance, key=recent_performance.get)
            best_idx = self.model_names.index(best_name)
            
            logger.info(f"Selected {best_name} based on performance: {recent_performance[best_name]:.4f}")
            
            return self.models[best_idx], best_name
        
        # Default selection based on regime
        regime_preferences = {
            'trending': 'LSTM',  # LSTMs good for trends
            'ranging': 'XGBoost',  # Tree models good for mean reversion
            'volatile': 'Ensemble'  # Ensemble for uncertainty
        }
        
        preferred = regime_preferences.get(market_regime, 'Ensemble')
        
        if preferred in self.model_names:
            idx = self.model_names.index(preferred)
            logger.info(f"Selected {preferred} for {market_regime} regime")
            return self.models[idx], preferred
        
        # Fallback to first model
        return self.models[0], self.model_names[0]
    
    def update_performance(self, model_name: str, performance: float):
        """Update performance history"""
        self.performance_history[model_name].append(performance)
        
        # Keep last 100 records
        if len(self.performance_history[model_name]) > 100:
            self.performance_history[model_name].pop(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("ENSEMBLE METHODS DEMO")
    print("="*60)
    
    # Create mock models
    class MockModel:
        def __init__(self, bias: float = 0.0):
            self.bias = bias
        
        def predict(self, X):
            return X.mean(axis=1) + self.bias + np.random.randn(len(X)) * 0.01
    
    # Create ensemble
    models = [
        MockModel(bias=0.0),
        MockModel(bias=0.01),
        MockModel(bias=-0.01)
    ]
    model_names = ['Model_A', 'Model_B', 'Model_C']
    
    ensemble = EnsemblePredictor(models, model_names)
    
    # Test data
    X_test = np.random.randn(100, 10)
    y_test = X_test.mean(axis=1)
    
    # Simple average
    logger.info("\nSimple Average Prediction:")
    pred_avg = ensemble.predict_average(X_test)
    mse_avg = np.mean((pred_avg - y_test)**2)
    logger.info(f"MSE: {mse_avg:.6f}")
    
    # Optimize weights
    logger.info("\nOptimizing Weights:")
    weights = ensemble.optimize_weights(X_test, y_test)
    
    # Weighted prediction
    logger.info("\nWeighted Prediction:")
    pred_weighted = ensemble.predict_weighted(X_test)
    mse_weighted = np.mean((pred_weighted - y_test)**2)
    logger.info(f"MSE: {mse_weighted:.6f}")
    
    # Train stacking
    logger.info("\nTraining Stacking Meta-Model:")
    X_train = np.random.randn(200, 10)
    y_train = X_train.mean(axis=1)
    ensemble.train_stacking(X_train, y_train, X_test, y_test)
    
    # Stacked prediction
    logger.info("\nStacked Prediction:")
    pred_stacked = ensemble.predict_stacked(X_test)
    mse_stacked = np.mean((pred_stacked - y_test)**2)
    logger.info(f"MSE: {mse_stacked:.6f}")
    
    # Uncertainty estimation
    logger.info("\nUncertainty Estimation:")
    mean_pred, std_pred = ensemble.get_prediction_uncertainty(X_test[:10])
    logger.info(f"Mean prediction: {mean_pred[:5]}")
    logger.info(f"Std prediction: {std_pred[:5]}")
    
    print("\n" + "="*60)
    logger.info("ENSEMBLE METHODS COMPLETE!")
    print("="*60)
