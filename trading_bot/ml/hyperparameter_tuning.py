import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""Hyperparameter tuning for ML models.

This module provides utilities for optimizing hyperparameters of machine learning
models in the trading bot, including grid search, random search, Bayesian optimization,
and evolutionary algorithms.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from loguru import logger
import os
import time
import json
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
from functools import partial


class HyperparameterTuner:
    """Base class for hyperparameter tuning."""
    
    def __init__(self, model_class: Any, param_grid: Dict[str, List[Any]], 
                 scoring_func: Callable, cv_folds: int = 5, n_jobs: int = -1,
                 verbose: bool = True):
        """Initialize the hyperparameter tuner.
        
        Args:
            model_class: Class of the model to tune
            param_grid: Dictionary mapping parameter names to lists of values to try
            scoring_func: Function to score model performance
            cv_folds: Number of cross-validation folds
            n_jobs: Number of parallel jobs (-1 for all available cores)
            verbose: Whether to print verbose output
        """
        self.model_class = model_class
        self.param_grid = param_grid
        self.scoring_func = scoring_func
        self.cv_folds = cv_folds
        self.n_jobs = n_jobs if n_jobs > 0 else os.cpu_count() or 1
        self.verbose = verbose
        self.best_params = None
        self.best_score = float('-inf')
        self.results = []
        
        logger.info(f"Initialized {self.__class__.__name__} for hyperparameter tuning")
    
    def _evaluate_params(self, params: Dict[str, Any], X_train: np.ndarray, 
                        y_train: np.ndarray, X_val: np.ndarray, 
                        y_val: np.ndarray) -> float:
        """Evaluate a set of parameters using cross-validation.
        
        Args:
            params: Dictionary of parameters to evaluate
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Mean score across CV folds
        """
        try:
            # Initialize model with parameters
            model = self.model_class(**params)
            
            # Train the model
            model.train(X_train, y_train)
            
            # Evaluate the model
            score = self.scoring_func(model, X_val, y_val)
            
            return score
        except Exception as e:
            logger.warning(f"Error evaluating parameters {params}: {e}")
            return float('-inf')
    
    def _cross_validate(self, params: Dict[str, Any], X: np.ndarray, 
                       y: np.ndarray) -> float:
        """Perform cross-validation for a set of parameters.
        
        Args:
            params: Dictionary of parameters to evaluate
            X: Feature data
            y: Target data
            
        Returns:
            Mean score across CV folds
        """
        # Split data into folds
        fold_size = len(X) // self.cv_folds
        scores = []
        
        for i in range(self.cv_folds):
            # Define validation indices
            val_start = i * fold_size
            val_end = (i + 1) * fold_size if i < self.cv_folds - 1 else len(X)
            
            # Split data
            X_val = X[val_start:val_end]
            y_val = y[val_start:val_end]
            X_train = np.concatenate([X[:val_start], X[val_end:]])
            y_train = np.concatenate([y[:val_start], y[val_end:]])
            
            # Evaluate parameters
            score = self._evaluate_params(params, X_train, y_train, X_val, y_val)
            scores.append(score)
        
        # Return mean score
        return np.mean(scores)
    
    def tune(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Tune hyperparameters using the specified method.
        
        Args:
            X: Feature data
            y: Target data
            
        Returns:
            Dictionary of best parameters
        """
        # Default implementation using grid search
        logger.info("Starting hyperparameter tuning (default grid search)")
        
        from sklearn.model_selection import GridSearchCV
        from sklearn.ensemble import RandomForestClassifier
        
        # Default parameter grid
        param_grid = self.param_grid or {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 20],
            'min_samples_split': [2, 5, 10]
        }
        
        # Use model if provided, otherwise default to RandomForest
        model = self.model if hasattr(self, 'model') else RandomForestClassifier(random_state=42)
        
        # Perform grid search
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=min(self.cv_folds, 5),
            scoring=self.scoring_metric,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # Store results
        self.best_params = grid_search.best_params_
        self.best_score = grid_search.best_score_
        
        # Store all results
        for params, score in zip(grid_search.cv_results_['params'], grid_search.cv_results_['mean_test_score']):
            self.results.append({'params': params, 'score': score})
        
        logger.info(f"Best parameters: {self.best_params}")
        logger.info(f"Best score: {self.best_score:.4f}")
        
        return self.best_params
    
    def save_results(self, path: str) -> None:
        """Save tuning results to a file.
        
        Args:
            path: Path to save results
        """
        results = {
            'best_params': self.best_params,
            'best_score': float(self.best_score),
            'all_results': [
                {'params': res['params'], 'score': float(res['score'])}
                for res in self.results
            ]
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(results, f, indent=4)
        
        logger.info(f"Saved hyperparameter tuning results to {path}")
    
    def load_results(self, path: str) -> Dict[str, Any]:
        """Load tuning results from a file.
        
        Args:
            path: Path to load results from
            
        Returns:
            Dictionary of loaded results
        """
        with open(path, 'r') as f:
            results = json.load(f)
        
        self.best_params = results['best_params']
        self.best_score = results['best_score']
        self.results = results['all_results']
        
        logger.info(f"Loaded hyperparameter tuning results from {path}")
        return results


class GridSearchTuner(HyperparameterTuner):
    """Grid search for hyperparameter tuning."""
    
    def _get_param_combinations(self) -> List[Dict[str, Any]]:
        """Get all combinations of parameters from param_grid.
        
        Returns:
            List of parameter dictionaries
        """
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        
        # Generate all combinations
        combinations = []
        
        def generate_combinations(index, current_params):
            if index == len(param_names):
                combinations.append(current_params.copy())
                return
            
            for value in param_values[index]:
                current_params[param_names[index]] = value
                generate_combinations(index + 1, current_params)
        
        generate_combinations(0, {})
        return combinations
    
    def tune(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Tune hyperparameters using grid search.
        
        Args:
            X: Feature data
            y: Target data
            
        Returns:
            Dictionary of best parameters
        """
        logger.info("Starting grid search hyperparameter tuning")
        
        # Get all parameter combinations
        param_combinations = self._get_param_combinations()
        total_combinations = len(param_combinations)
        
        logger.info(f"Evaluating {total_combinations} parameter combinations")
        
        # Evaluate each combination
        self.results = []
        
        if self.n_jobs > 1:
            # Parallel evaluation
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []
                for params in param_combinations:
                    future = executor.submit(self._cross_validate, params, X, y)
                    futures.append((future, params))
                
                for i, (future, params) in enumerate(futures):
                    score = future.result()
                    self.results.append({'params': params, 'score': score})
                    
                    if score > self.best_score:
                        self.best_score = score
                        self.best_params = params
                    
                    if self.verbose:
                        logger.info(f"Combination {i+1}/{total_combinations}: "
                                   f"Score={score:.6f}, Best={self.best_score:.6f}")
        else:
            # Sequential evaluation
            for i, params in enumerate(param_combinations):
                score = self._cross_validate(params, X, y)
                self.results.append({'params': params, 'score': score})
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                
                if self.verbose:
                    logger.info(f"Combination {i+1}/{total_combinations}: "
                               f"Score={score:.6f}, Best={self.best_score:.6f}")
        
        # Sort results by score
        self.results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.success(f"Grid search complete. Best score: {self.best_score:.6f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params


class RandomSearchTuner(HyperparameterTuner):
    """Random search for hyperparameter tuning."""
    
    def __init__(self, model_class: Any, param_distributions: Dict[str, Any], 
                 scoring_func: Callable, n_iter: int = 10, cv_folds: int = 5, 
                 n_jobs: int = -1, verbose: bool = True, random_state: Optional[int] = None):
        """Initialize the random search tuner.
        
        Args:
            model_class: Class of the model to tune
            param_distributions: Dictionary mapping parameter names to distributions or lists
            scoring_func: Function to score model performance
            n_iter: Number of random combinations to try
            cv_folds: Number of cross-validation folds
            n_jobs: Number of parallel jobs (-1 for all available cores)
            verbose: Whether to print verbose output
            random_state: Random seed for reproducibility
        """
        super().__init__(model_class, param_distributions, scoring_func, cv_folds, n_jobs, verbose)
        self.n_iter = n_iter
        self.random_state = random_state
        
        if random_state is not None:
            np.random.seed(random_state)
            random.seed(random_state)
    
    def _sample_params(self) -> Dict[str, Any]:
        """Sample a random combination of parameters.
        
        Returns:
            Dictionary of sampled parameters
        """
        params = {}
        
        for param_name, param_dist in self.param_grid.items():
            if isinstance(param_dist, list):
                # Sample from list
                params[param_name] = random.choice(param_dist)
            elif hasattr(param_dist, 'rvs'):
                # Sample from scipy distribution
                params[param_name] = param_dist.rvs(1)[0]
            elif callable(param_dist):
                # Call function to get value
                params[param_name] = param_dist()
            else:
                # Use value directly
                params[param_name] = param_dist
        
        return params
    
    def tune(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Tune hyperparameters using random search.
        
        Args:
            X: Feature data
            y: Target data
            
        Returns:
            Dictionary of best parameters
        """
        logger.info(f"Starting random search with {self.n_iter} iterations")
        
        # Evaluate random combinations
        self.results = []
        
        if self.n_jobs > 1:
            # Parallel evaluation
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []
                param_samples = [self._sample_params() for _ in range(self.n_iter)]
                
                for params in param_samples:
                    future = executor.submit(self._cross_validate, params, X, y)
                    futures.append((future, params))
                
                for i, (future, params) in enumerate(futures):
                    score = future.result()
                    self.results.append({'params': params, 'score': score})
                    
                    if score > self.best_score:
                        self.best_score = score
                        self.best_params = params
                    
                    if self.verbose:
                        logger.info(f"Iteration {i+1}/{self.n_iter}: "
                                   f"Score={score:.6f}, Best={self.best_score:.6f}")
        else:
            # Sequential evaluation
            for i in range(self.n_iter):
                params = self._sample_params()
                score = self._cross_validate(params, X, y)
                self.results.append({'params': params, 'score': score})
                
                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params
                
                if self.verbose:
                    logger.info(f"Iteration {i+1}/{self.n_iter}: "
                               f"Score={score:.6f}, Best={self.best_score:.6f}")
        
        # Sort results by score
        self.results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.success(f"Random search complete. Best score: {self.best_score:.6f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params


class BayesianOptimizationTuner(HyperparameterTuner):
    """Bayesian optimization for hyperparameter tuning."""
    
    def __init__(self, model_class: Any, param_space: Dict[str, Tuple[float, float]], 
                 scoring_func: Callable, n_iter: int = 10, cv_folds: int = 5, 
                 n_jobs: int = -1, verbose: bool = True, random_state: Optional[int] = None,
                 n_initial_points: int = 5, acquisition_function: str = 'ei'):
        """Initialize the Bayesian optimization tuner.
        
        Args:
            model_class: Class of the model to tune
            param_space: Dictionary mapping parameter names to (min, max) tuples
            scoring_func: Function to score model performance
            n_iter: Number of iterations
            cv_folds: Number of cross-validation folds
            n_jobs: Number of parallel jobs (-1 for all available cores)
            verbose: Whether to print verbose output
            random_state: Random seed for reproducibility
            n_initial_points: Number of initial random points
            acquisition_function: Acquisition function ('ei', 'pi', or 'ucb')
        """
        super().__init__(model_class, param_space, scoring_func, cv_folds, n_jobs, verbose)
        self.n_iter = n_iter
        self.random_state = random_state
        self.n_initial_points = n_initial_points
        self.acquisition_function = acquisition_function
        
        # Check if scikit-optimize is available
        try:
            import skopt
            self.skopt = skopt
        except ImportError:
            logger.error("scikit-optimize is required for Bayesian optimization. "
                        "Install with 'pip install scikit-optimize'")
            raise
        
        # Convert param_space to skopt format
        self.space = []
        self.param_names = []
        
        for param_name, bounds in param_space.items():
            self.param_names.append(param_name)
            
            if isinstance(bounds, tuple) and len(bounds) == 2:
                # Continuous parameter
                self.space.append(self.skopt.space.Real(bounds[0], bounds[1], name=param_name))
            elif isinstance(bounds, list):
                # Categorical parameter
                self.space.append(self.skopt.space.Categorical(bounds, name=param_name))
            elif isinstance(bounds, dict) and 'values' in bounds:
                # Categorical parameter with explicit values
                self.space.append(self.skopt.space.Categorical(bounds['values'], name=param_name))
            elif isinstance(bounds, dict) and 'low' in bounds and 'high' in bounds:
                # Integer parameter
                if bounds.get('type') == 'int':
                    self.space.append(self.skopt.space.Integer(
                        bounds['low'], bounds['high'], name=param_name
                    ))
                else:
                    self.space.append(self.skopt.space.Real(
                        bounds['low'], bounds['high'], name=param_name
                    ))
    
    def _params_from_vector(self, x: List[Any]) -> Dict[str, Any]:
        """Convert parameter vector to dictionary.
        
        Args:
            x: Parameter vector
            
        Returns:
            Dictionary of parameters
        """
        return {name: value for name, value in zip(self.param_names, x)}
    
    def _objective(self, x: List[Any], X: np.ndarray, y: np.ndarray) -> float:
        """Objective function for Bayesian optimization.
        
        Args:
            x: Parameter vector
            X: Feature data
            y: Target data
            
        Returns:
            Negative score (for minimization)
        """
        params = self._params_from_vector(x)
        score = self._cross_validate(params, X, y)
        
        # Return negative score for minimization
        return -score
    
    def tune(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Tune hyperparameters using Bayesian optimization.
        
        Args:
            X: Feature data
            y: Target data
            
        Returns:
            Dictionary of best parameters
        """
        logger.info(f"Starting Bayesian optimization with {self.n_iter} iterations")
        
        # Create objective function
        objective = partial(self._objective, X=X, y=y)
        
        # Run optimization
        result = self.skopt.gp_minimize(
            objective,
            self.space,
            n_calls=self.n_iter,
            n_initial_points=self.n_initial_points,
            random_state=self.random_state,
            verbose=self.verbose,
            acq_func=self.acquisition_function
        )
        
        # Extract results
        self.best_params = self._params_from_vector(result.x)
        self.best_score = -result.fun
        
        # Store all results
        self.results = []
        for i, (x, score) in enumerate(zip(result.x_iters, result.func_vals)):
            params = self._params_from_vector(x)
            self.results.append({'params': params, 'score': -score})
        
        # Sort results by score
        self.results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.success(f"Bayesian optimization complete. Best score: {self.best_score:.6f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params


def optimize_transformer_model(df: pd.DataFrame, target_col: str = 'close',
                              n_iter: int = 20, cv_folds: int = 3,
                              tuning_method: str = 'random',
                              random_state: Optional[int] = None) -> Dict[str, Any]:
    """Optimize hyperparameters for TransformerModel.
    
    Args:
        df: DataFrame with features and target
        target_col: Target column name
        n_iter: Number of iterations for random/Bayesian search
        cv_folds: Number of cross-validation folds
        tuning_method: Tuning method ('grid', 'random', or 'bayesian')
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary of best parameters
    """
    from trading_bot.ml.predictive_models import TransformerModel
    from sklearn.metrics import mean_squared_error
    
    # Define scoring function
    def scoring_func(model, X_val, y_val):
        # Make predictions
        y_pred = model.predict(X_val)
        
        # Calculate RMSE
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        # Return negative RMSE (higher is better)
        return -rmse
    
    # Define parameter grid based on tuning method
    if tuning_method == 'grid':
        param_grid = {
            'n_head': [4, 8],
            'd_model': [64, 128],
            'n_layers': [2, 4],
            'dropout': [0.1, 0.2],
            'window_size': [30, 60],
            'batch_size': [16, 32],
            'learning_rate': [0.0001, 0.001]
        }
        
        tuner = GridSearchTuner(
            TransformerModel,
            param_grid,
            scoring_func,
            cv_folds=cv_folds,
            verbose=True
        )
    elif tuning_method == 'random':
        param_distributions = {
            'n_head': [4, 8, 12, 16],
            'd_model': [64, 96, 128, 160, 192, 256],
            'n_layers': [1, 2, 3, 4, 6],
            'dropout': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            'window_size': [20, 30, 40, 50, 60, 90],
            'batch_size': [8, 16, 32, 64],
            'learning_rate': [0.00001, 0.0001, 0.0005, 0.001, 0.005]
        }
        
        tuner = RandomSearchTuner(
            TransformerModel,
            param_distributions,
            scoring_func,
            n_iter=n_iter,
            cv_folds=cv_folds,
            verbose=True,
            random_state=random_state
        )
    elif tuning_method == 'bayesian':
        param_space = {
            'n_head': {'type': 'int', 'low': 2, 'high': 16},
            'd_model': {'type': 'int', 'low': 32, 'high': 256},
            'n_layers': {'type': 'int', 'low': 1, 'high': 6},
            'dropout': (0.0, 0.5),
            'window_size': {'type': 'int', 'low': 10, 'high': 100},
            'batch_size': {'values': [8, 16, 32, 64, 128]},
            'learning_rate': (0.00001, 0.01)
        }
        
        tuner = BayesianOptimizationTuner(
            TransformerModel,
            param_space,
            scoring_func,
            n_iter=n_iter,
            cv_folds=cv_folds,
            verbose=True,
            random_state=random_state
        )
    else:
        raise ValueError(f"Unknown tuning method: {tuning_method}")
    
    # Prepare data
    from sklearn.model_selection import train_test_split
    
    # Split data into train and test sets
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=random_state)
    
    # Prepare features and target
    X_train = train_df.drop(columns=[target_col]).values
    y_train = train_df[target_col].values
    
    # Tune hyperparameters
    best_params = tuner.tune(X_train, y_train)
    
    # Save results
    os.makedirs('results/hyperparameter_tuning', exist_ok=True)
    tuner.save_results(f'results/hyperparameter_tuning/transformer_model_{tuning_method}.json')
    
    return best_params


def optimize_ppo_agent(env, n_iter: int = 20, cv_folds: int = 3,
                      tuning_method: str = 'random',
                      random_state: Optional[int] = None) -> Dict[str, Any]:
    """Optimize hyperparameters for PPOAgent.
    
    Args:
        env: Trading environment
        n_iter: Number of iterations for random/Bayesian search
        cv_folds: Number of cross-validation folds
        tuning_method: Tuning method ('grid', 'random', or 'bayesian')
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary of best parameters
    """
    from trading_bot.ml.reinforcement_learning import PPOAgent
    
    # Define scoring function
    def scoring_func(model, env, episodes=5):
        # Run episodes and calculate average reward
        total_rewards = []
        
        for _ in range(episodes):
            state = env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                action = model.select_action(state)
                next_state, reward, done, _ = env.step(action)
                episode_reward += reward
                state = next_state
            
            total_rewards.append(episode_reward)
        
        # Return average reward
        return np.mean(total_rewards)
    
    # Define parameter grid based on tuning method
    if tuning_method == 'grid':
        param_grid = {
            'actor_lr': [0.0001, 0.0003],
            'critic_lr': [0.0001, 0.0003],
            'gamma': [0.95, 0.99],
            'gae_lambda': [0.9, 0.95],
            'clip_ratio': [0.1, 0.2],
            'value_coef': [0.5, 1.0],
            'entropy_coef': [0.01, 0.05]
        }
        
        tuner = GridSearchTuner(
            PPOAgent,
            param_grid,
            lambda model, X, y: scoring_func(model, env),
            cv_folds=cv_folds,
            verbose=True
        )
    elif tuning_method == 'random':
        param_distributions = {
            'actor_lr': [0.00003, 0.0001, 0.0003, 0.001],
            'critic_lr': [0.00003, 0.0001, 0.0003, 0.001],
            'gamma': [0.9, 0.95, 0.97, 0.99, 0.995],
            'gae_lambda': [0.8, 0.9, 0.92, 0.95, 0.97, 0.99],
            'clip_ratio': [0.1, 0.15, 0.2, 0.25, 0.3],
            'value_coef': [0.25, 0.5, 0.75, 1.0, 1.5],
            'entropy_coef': [0.001, 0.005, 0.01, 0.02, 0.05]
        }
        
        tuner = RandomSearchTuner(
            PPOAgent,
            param_distributions,
            lambda model, X, y: scoring_func(model, env),
            n_iter=n_iter,
            cv_folds=cv_folds,
            verbose=True,
            random_state=random_state
        )
    elif tuning_method == 'bayesian':
        param_space = {
            'actor_lr': (0.00001, 0.001),
            'critic_lr': (0.00001, 0.001),
            'gamma': (0.9, 0.999),
            'gae_lambda': (0.8, 0.99),
            'clip_ratio': (0.05, 0.3),
            'value_coef': (0.1, 2.0),
            'entropy_coef': (0.0001, 0.1)
        }
        
        tuner = BayesianOptimizationTuner(
            PPOAgent,
            param_space,
            lambda model, X, y: scoring_func(model, env),
            n_iter=n_iter,
            cv_folds=cv_folds,
            verbose=True,
            random_state=random_state
        )
    else:
        raise ValueError(f"Unknown tuning method: {tuning_method}")
    
    # Tune hyperparameters (using dummy data since we're using the environment)
    dummy_X = np.zeros((10, 10))
    dummy_y = np.zeros(10)
    best_params = tuner.tune(dummy_X, dummy_y)
    
    # Save results
    os.makedirs('results/hyperparameter_tuning', exist_ok=True)
    tuner.save_results(f'results/hyperparameter_tuning/ppo_agent_{tuning_method}.json')
    
    return best_params
