"""
Automated hyperparameter tuning using Optuna.
Optimizes model parameters for maximum performance.
"""

import logging
import json
import numpy as np
from typing import Dict, Optional, Callable
from loguru import logger

try:
    import torch
except ImportError:
    torch = None

try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    RandomForestRegressor = None

try:
    import optuna
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not installed. Install with: pip install optuna")


class HyperparameterTuner:
    """Automated hyperparameter optimization."""
    
    def __init__(self, n_trials: int = 100, timeout: int = 3600):
        """
        Initialize hyperparameter tuner.
        
        Args:
            n_trials: Number of optimization trials
            timeout: Timeout in seconds
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna required for hyperparameter tuning")
        
        self.n_trials = n_trials
        self.timeout = timeout
        self.best_params = {}
        
        logger.info(f"Hyperparameter tuner initialized ({n_trials} trials)")
    
    def tune_transformer(self, train_data, val_data, objective_metric='val_loss'):
        """
        Tune Transformer hyperparameters.
        
        Args:
            train_data: Training data tuple (X, y)
            val_data: Validation data tuple (X, y)
            objective_metric: Metric to optimize
            
        Returns:
            Best hyperparameters
        """
        X_train, y_train = train_data
        X_val, y_val = val_data
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'd_model': trial.suggest_categorical('d_model', [64, 128, 256, 512]),
                'nhead': trial.suggest_categorical('nhead', [4, 8, 16]),
                'num_layers': trial.suggest_int('num_layers', 2, 8),
                'dropout': trial.suggest_float('dropout', 0.0, 0.5),
                'lr': trial.suggest_loguniform('lr', 1e-5, 1e-2),
                'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64, 128])
            }
            
            # Train model with these parameters
            from trading_bot.ml.transformer_model import TransformerPredictor
            
            model = TransformerPredictor(
                input_dim=X_train.shape[1],
                d_model=params['d_model'],
                nhead=params['nhead'],
                num_layers=params['num_layers'],
                dropout=params['dropout']
            )
            
            # Train
            metrics = model.train(X_train, y_train, epochs=20)
            
            # Evaluate on validation
            val_predictions = []
            for i in range(len(X_val)):
                pred = model.predict(X_val[i:i+1])
                val_predictions.append(pred)
            
            val_loss = np.mean((np.array(val_predictions) - y_val) ** 2)
            
            return val_loss
        
        # Create study
        study = optuna.create_study(
            direction='minimize',
            sampler=TPESampler(),
            pruner=MedianPruner()
        )
        
        # Optimize
        study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)
        
        self.best_params['transformer'] = study.best_params
        
        logger.success(f"Best Transformer params: {study.best_params}")
        logger.info(f"Best validation loss: {study.best_value:.6f}")
        
        return study.best_params
    
    def tune_ppo(self, env, objective_metric='episode_reward'):
        """
        Tune PPO hyperparameters.
        
        Args:
            env: Trading environment
            objective_metric: Metric to optimize
            
        Returns:
            Best hyperparameters
        """
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'lr': trial.suggest_loguniform('lr', 1e-5, 1e-3),
                'gamma': trial.suggest_float('gamma', 0.9, 0.999),
                'epsilon': trial.suggest_float('epsilon', 0.1, 0.3),
                'gae_lambda': trial.suggest_float('gae_lambda', 0.9, 0.99),
                'value_coef': trial.suggest_float('value_coef', 0.3, 0.7),
                'entropy_coef': trial.suggest_float('entropy_coef', 0.001, 0.1)
            }
            
            # Train agent
            from trading_bot.ml.ppo_agent import PPOAgent
            
            agent = PPOAgent(
                state_dim=env.data.shape[1],
                action_dim=3,
                config=params
            )
            
            # Run episodes
            total_reward = 0
            for episode in range(10):
                state = env.reset()
                episode_reward = 0
                done = False
                
                while not done:
                    action, log_prob, value, _ = agent.select_action(state)
                    next_state, reward, done = env.step(action)
                    agent.store_transition(state, action, log_prob, reward, value, done)
                    state = next_state
                    episode_reward += reward
                
                agent.update()
                total_reward += episode_reward
            
            avg_reward = total_reward / 10
            return -avg_reward  # Negative because Optuna minimizes
        
        # Create study
        study = optuna.create_study(
            direction='minimize',
            sampler=TPESampler()
        )
        
        # Optimize
        study.optimize(objective, n_trials=self.n_trials // 2, timeout=self.timeout)
        
        self.best_params['ppo'] = study.best_params
        
        logger.success(f"Best PPO params: {study.best_params}")
        logger.info(f"Best avg reward: {-study.best_value:.2f}")
        
        return study.best_params
    
    def tune_risk_parameters(self, returns_data):
        """
        Tune risk management parameters.
        
        Args:
            returns_data: Historical returns
            
        Returns:
            Best risk parameters
        """
        
        def objective(trial):
            params = {
                'max_risk_per_trade': trial.suggest_float('max_risk_per_trade', 0.005, 0.03),
                'max_drawdown': trial.suggest_float('max_drawdown', 0.10, 0.25),
                'kelly_fraction': trial.suggest_float('kelly_fraction', 0.25, 0.75),
                'var_confidence': trial.suggest_float('var_confidence', 0.90, 0.99)
            }
            
            # Simulate portfolio with these parameters
            from trading_bot.risk.advanced_risk_metrics import AdvancedRiskMetrics
            
            metrics = AdvancedRiskMetrics()
            
            # Calculate risk-adjusted return
            sharpe = metrics.calculate_sharpe_ratio(returns_data)
            max_dd, _, _ = metrics.calculate_max_drawdown(np.cumprod(1 + returns_data))
            
            # Objective: maximize Sharpe while minimizing drawdown
            score = sharpe / (max_dd + 0.01)
            
            return -score  # Negative because Optuna minimizes
        
        # Create study
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=50)
        
        self.best_params['risk'] = study.best_params
        
        logger.success(f"Best risk params: {study.best_params}")
        
        return study.best_params
    
    def save_best_params(self, filepath: str = 'config/optimized_params.json'):
        """Save best parameters to file."""
        from pathlib import Path
        
        Path(filepath).parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.best_params, f, indent=2)
        
        logger.success(f"Best parameters saved to {filepath}")
    
    def load_best_params(self, filepath: str = 'config/optimized_params.json'):
        """Load best parameters from file."""
        
        with open(filepath, 'r') as f:
            self.best_params = json.load(f)
        
        logger.info(f"Parameters loaded from {filepath}")
        return self.best_params


class FeatureSelector:
    """Automated feature selection and optimization."""
    
    def __init__(self, method: str = 'shap'):
        """
        Initialize feature selector.
        
        Args:
            method: Selection method ('shap', 'mutual_info', 'recursive')
        """
        self.method = method
        self.selected_features = []
        self.feature_importance = {}
        
        logger.info(f"Feature selector initialized (method: {method})")
    
    def select_features(self, X, y, n_features: int = 50):
        """
        Select top N features.
        
        Args:
            X: Feature matrix
            y: Target vector
            n_features: Number of features to select
            
        Returns:
            Selected feature indices
        """
        if self.method == 'mutual_info':
            return self._mutual_info_selection(X, y, n_features)
        elif self.method == 'recursive':
            return self._recursive_selection(X, y, n_features)
        else:
            return self._shap_selection(X, y, n_features)
    
    def _mutual_info_selection(self, X, y, n_features):
        """Mutual information based selection."""
        from sklearn.feature_selection import mutual_info_regression
        
        mi_scores = mutual_info_regression(X, y)
        top_indices = np.argsort(mi_scores)[-n_features:]
        
        self.selected_features = top_indices.tolist()
        self.feature_importance = dict(enumerate(mi_scores))
        
        logger.info(f"Selected {n_features} features using mutual information")
        return top_indices
    
    def _recursive_selection(self, X, y, n_features):
        """Recursive feature elimination."""
        from sklearn.feature_selection import RFE
        
        estimator = RandomForestRegressor(n_estimators=100, random_state=42)
        selector = RFE(estimator, n_features_to_select=n_features)
        selector.fit(X, y)
        
        self.selected_features = np.where(selector.support_)[0].tolist()
        self.feature_importance = dict(enumerate(selector.ranking_))
        
        logger.info(f"Selected {n_features} features using RFE")
        return self.selected_features
    
    def _shap_selection(self, X, y, n_features):
        """SHAP-based feature selection."""
        try:
            import shap

            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Calculate SHAP values
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X[:100])  # Sample for speed
            
            # Get feature importance
            importance = np.abs(shap_values).mean(axis=0)
            top_indices = np.argsort(importance)[-n_features:]
            
            self.selected_features = top_indices.tolist()
            self.feature_importance = dict(enumerate(importance))
            
            logger.info(f"Selected {n_features} features using SHAP")
            return top_indices
            
        except ImportError:
            logger.warning("SHAP not available, falling back to mutual info")
            return self._mutual_info_selection(X, y, n_features)
