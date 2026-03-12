"""
Bayesian Parameter Optimization for Trading Strategies
Uses Bayesian optimization to find optimal strategy parameters
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import asyncio
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass, field

# Bayesian optimization libraries
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from scipy.stats import norm
from scipy.optimize import minimize
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class ParameterSpace:
    """Parameter space for optimization"""
    name: str
    lower_bound: float
    upper_bound: float
    type: str = "continuous"  # continuous, integer, categorical
    log_scale: bool = False
    categories: List[Any] = field(default_factory=list)
    
    def sample(self) -> Any:
        """Sample a random value from the parameter space"""
        if self.type == "continuous":
            if self.log_scale:
                return np.exp(np.random.uniform(np.log(self.lower_bound), 
                                              np.log(self.upper_bound)))
            else:
                return np.random.uniform(self.lower_bound, self.upper_bound)
        elif self.type == "integer":
            return np.random.randint(int(self.lower_bound), int(self.upper_bound) + 1)
        elif self.type == "categorical":
            return np.random.choice(self.categories)
        else:
            raise ValueError(f"Unknown parameter type: {self.type}")
    
    def transform(self, value: Any) -> float:
        """Transform parameter value to [0, 1] range for GP"""
        if self.type == "continuous":
            if self.log_scale:
                return (np.log(value) - np.log(self.lower_bound)) / (np.log(self.upper_bound) - np.log(self.lower_bound))
            else:
                return (value - self.lower_bound) / (self.upper_bound - self.lower_bound)
        elif self.type == "integer":
            return (value - self.lower_bound) / (self.upper_bound - self.lower_bound)
        elif self.type == "categorical":
            return self.categories.index(value) / (len(self.categories) - 1) if len(self.categories) > 1 else 0.5
        else:
            raise ValueError(f"Unknown parameter type: {self.type}")
    
    def inverse_transform(self, normalized: float) -> Any:
        """Transform normalized value back to parameter space"""
        if self.type == "continuous":
            if self.log_scale:
                return np.exp(normalized * (np.log(self.upper_bound) - np.log(self.lower_bound)) + np.log(self.lower_bound))
            else:
                return normalized * (self.upper_bound - self.lower_bound) + self.lower_bound
        elif self.type == "integer":
            value = normalized * (self.upper_bound - self.lower_bound) + self.lower_bound
            return int(np.round(value))
        elif self.type == "categorical":
            index = int(np.round(normalized * (len(self.categories) - 1)))
            return self.categories[index]
        else:
            raise ValueError(f"Unknown parameter type: {self.type}")


class BayesianOptimizer:
    """
    Bayesian optimization for trading strategy parameters
    
    Features:
    - Gaussian Process surrogate model
    - Expected Improvement acquisition function
    - Efficient exploration of parameter space
    - Handles continuous, integer, and categorical parameters
    - Parallel evaluation support
    - Visualization of optimization progress
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Optimization parameters
        self.n_initial_points = self.config.get('n_initial_points', 10)
        self.n_iterations = self.config.get('n_iterations', 50)
        self.exploration_weight = self.config.get('exploration_weight', 0.1)
        self.n_restarts = self.config.get('n_restarts', 25)
        
        # Parameter space
        self.parameter_space: Dict[str, ParameterSpace] = {}
        
        # Optimization history
        self.X: List[Dict[str, Any]] = []  # Parameters
        self.y: List[float] = []  # Objective values
        
        # Gaussian Process model
        self.gp = None
        self.kernel = Matern(nu=2.5)
        
        # Best result
        self.best_params = None
        self.best_score = float('-inf')
        
        # Output directory
        self.output_dir = Path(self.config.get('output_dir', 'optimization_results'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Bayesian optimizer initialized")
    
    def add_parameter(self, name: str, lower_bound: float, upper_bound: float, 
                     param_type: str = "continuous", log_scale: bool = False,
                     categories: Optional[List[Any]] = None):
        """Add parameter to optimization space"""
        self.parameter_space[name] = ParameterSpace(
            name=name,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            type=param_type,
            log_scale=log_scale,
            categories=categories or []
        )
        logger.debug(f"Added parameter {name} to optimization space")
    
    def optimize(self, objective_function: Callable[[Dict[str, Any]], float], 
                maximize: bool = True) -> Dict[str, Any]:
        """
        Run Bayesian optimization
        
        Args:
            objective_function: Function to maximize/minimize
            maximize: Whether to maximize (True) or minimize (False)
            
        Returns:
            Best parameters found
        """
        sign = 1 if maximize else -1
        
        # Initial random sampling
        logger.info(f"Starting with {self.n_initial_points} initial random points")
        for _ in range(self.n_initial_points):
            params = self._sample_parameters()
            score = sign * objective_function(params)
            
            self.X.append(params)
            self.y.append(score)
            
            if score > self.best_score:
                self.best_score = score
                self.best_params = params.copy()
                logger.info(f"New best score: {sign * score:.6f}, params: {params}")
        
        # Initialize GP model
        self._update_model()
        
        # Main optimization loop
        logger.info(f"Starting {self.n_iterations} optimization iterations")
        for i in range(self.n_iterations):
            # Find next point to evaluate
            next_params = self._get_next_point(sign)
            
            # Evaluate objective
            score = sign * objective_function(next_params)
            
            # Update data
            self.X.append(next_params)
            self.y.append(score)
            
            # Update model
            self._update_model()
            
            # Update best
            if score > self.best_score:
                self.best_score = score
                self.best_params = next_params.copy()
                logger.info(f"Iteration {i+1}/{self.n_iterations}: New best score: {sign * score:.6f}")
            
            # Log progress
            if (i + 1) % 5 == 0:
                logger.info(f"Completed {i+1}/{self.n_iterations} iterations, best score: {sign * self.best_score:.6f}")
        
        logger.info(f"Optimization complete. Best score: {sign * self.best_score:.6f}, params: {self.best_params}")
        
        # Save results
        self._save_results(sign)
        
        return self.best_params
    
    async def optimize_async(self, objective_function: Callable[[Dict[str, Any]], float], 
                          maximize: bool = True) -> Dict[str, Any]:
        """
        Run Bayesian optimization asynchronously
        
        Args:
            objective_function: Async function to maximize/minimize
            maximize: Whether to maximize (True) or minimize (False)
            
        Returns:
            Best parameters found
        """
        sign = 1 if maximize else -1
        
        # Initial random sampling
        logger.info(f"Starting with {self.n_initial_points} initial random points")
        for _ in range(self.n_initial_points):
            params = self._sample_parameters()
            score = sign * await objective_function(params)
            
            self.X.append(params)
            self.y.append(score)
            
            if score > self.best_score:
                self.best_score = score
                self.best_params = params.copy()
                logger.info(f"New best score: {sign * score:.6f}, params: {params}")
        
        # Initialize GP model
        self._update_model()
        
        # Main optimization loop
        logger.info(f"Starting {self.n_iterations} optimization iterations")
        for i in range(self.n_iterations):
            # Find next point to evaluate
            next_params = self._get_next_point(sign)
            
            # Evaluate objective
            score = sign * await objective_function(next_params)
            
            # Update data
            self.X.append(next_params)
            self.y.append(score)
            
            # Update model
            self._update_model()
            
            # Update best
            if score > self.best_score:
                self.best_score = score
                self.best_params = next_params.copy()
                logger.info(f"Iteration {i+1}/{self.n_iterations}: New best score: {sign * score:.6f}")
            
            # Log progress
            if (i + 1) % 5 == 0:
                logger.info(f"Completed {i+1}/{self.n_iterations} iterations, best score: {sign * self.best_score:.6f}")
        
        logger.info(f"Optimization complete. Best score: {sign * self.best_score:.6f}, params: {self.best_params}")
        
        # Save results
        self._save_results(sign)
        
        return self.best_params
    
    def _sample_parameters(self) -> Dict[str, Any]:
        """Sample random parameters from the parameter space"""
        return {name: space.sample() for name, space in self.parameter_space.items()}
    
    def _update_model(self):
        """Update Gaussian Process model with current data"""
        # Transform parameters to array
        X_array = self._params_to_array(self.X)
        y_array = np.array(self.y).reshape(-1, 1)
        
        # Create and fit GP model
        self.gp = GaussianProcessRegressor(
            kernel=self.kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=42
        )
        self.gp.fit(X_array, y_array)
    
    def _params_to_array(self, params_list: List[Dict[str, Any]]) -> np.ndarray:
        """Convert list of parameter dictionaries to normalized array"""
        X_array = np.zeros((len(params_list), len(self.parameter_space)))
        
        for i, params in enumerate(params_list):
            for j, (name, space) in enumerate(self.parameter_space.items()):
                X_array[i, j] = space.transform(params[name])
        
        return X_array
    
    def _array_to_params(self, X_array: np.ndarray) -> Dict[str, Any]:
        """Convert normalized array back to parameter dictionary"""
        params = {}
        
        for j, (name, space) in enumerate(self.parameter_space.items()):
            params[name] = space.inverse_transform(X_array[j])
        
        return params
    
    def _expected_improvement(self, X: np.ndarray, sign: int = 1) -> np.ndarray:
        """
        Expected Improvement acquisition function
        
        Args:
            X: Points to evaluate EI at
            sign: 1 for maximization, -1 for minimization
            
        Returns:
            Expected improvement values
        """
        # Get mean and std from GP
        mu, sigma = self.gp.predict(X, return_std=True)
        
        # Best observed value
        y_best = max(self.y)
        
        # Calculate improvement
        with np.errstate(divide='ignore'):
            improvement = mu - y_best - self.exploration_weight
            Z = improvement / sigma
            ei = improvement * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma == 0.0] = 0.0
        
        return ei
    
    def _get_next_point(self, sign: int = 1) -> Dict[str, Any]:
        """
        Get next point to evaluate using Expected Improvement
        
        Args:
            sign: 1 for maximization, -1 for minimization
            
        Returns:
            Next parameters to evaluate
        """
        # Define negative EI function for minimization
        def negative_ei(x):
            return -self._expected_improvement(x.reshape(1, -1), sign)[0]
        
        # Start from multiple random points
        best_x = None
        best_ei = float('-inf')
        
        for _ in range(self.n_restarts):
            # Random starting point
            x0 = np.random.rand(len(self.parameter_space))
            
            # Minimize negative EI
            bounds = [(0, 1) for _ in range(len(self.parameter_space))]
            result = minimize(negative_ei, x0, bounds=bounds, method='L-BFGS-B')
            
            if result.success and -result.fun > best_ei:
                best_ei = -result.fun
                best_x = result.x
        
        # If optimization failed, sample randomly
        if best_x is None:
            best_x = np.random.rand(len(self.parameter_space))
        
        # Convert back to parameter dictionary
        next_params = self._array_to_params(best_x)
        
        return next_params
    
    def _save_results(self, sign: int):
        """Save optimization results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = self.output_dir / f"optimization_{timestamp}"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save parameters and scores
        results = {
            'parameters': self.X,
            'scores': [sign * y for y in self.y],
            'best_parameters': self.best_params,
            'best_score': sign * self.best_score,
            'parameter_space': {
                name: {
                    'lower_bound': space.lower_bound,
                    'upper_bound': space.upper_bound,
                    'type': space.type,
                    'log_scale': space.log_scale,
                    'categories': space.categories
                }
                for name, space in self.parameter_space.items()
            }
        }
        
        with open(results_dir / 'results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Plot optimization progress
        self._plot_optimization_progress(results_dir / 'progress.png', sign)
        
        # Plot parameter importance
        self._plot_parameter_importance(results_dir / 'importance.png')
        
        logger.info(f"Saved optimization results to {results_dir}")
    
    def _plot_optimization_progress(self, file_path: str, sign: int):
        """Plot optimization progress"""
        plt.figure(figsize=(10, 6))
        
        # Convert to cumulative maximum
        scores = np.array([sign * y for y in self.y])
        cummax = np.maximum.accumulate(scores)
        
        plt.plot(range(1, len(scores) + 1), scores, 'o-', alpha=0.3, label='Objective')
        plt.plot(range(1, len(cummax) + 1), cummax, 'r-', label='Best so far')
        
        plt.xlabel('Iteration')
        plt.ylabel('Objective Value')
        plt.title('Optimization Progress')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()
    
    def _plot_parameter_importance(self, file_path: str):
        """Plot parameter importance based on GP model"""
        if self.gp is None or len(self.X) < 10:
            return
        
        # Get kernel lengthscales
        if hasattr(self.gp.kernel_, 'length_scale'):
            lengthscales = self.gp.kernel_.length_scale
            if not isinstance(lengthscales, np.ndarray):
                lengthscales = np.array([lengthscales] * len(self.parameter_space))
            
            # Inverse lengthscale as importance
            importance = 1.0 / lengthscales
            importance = importance / importance.sum()
            
            # Plot
            plt.figure(figsize=(10, 6))
            
            param_names = list(self.parameter_space.keys())
            y_pos = np.arange(len(param_names))
            
            plt.barh(y_pos, importance, align='center')
            plt.yticks(y_pos, param_names)
            plt.xlabel('Relative Importance')
            plt.title('Parameter Importance')
            
            plt.tight_layout()
            plt.savefig(file_path)
            plt.close()
    
    def get_optimization_history(self) -> Dict[str, Any]:
        """Get optimization history"""
        return {
            'parameters': self.X,
            'scores': self.y,
            'best_parameters': self.best_params,
            'best_score': self.best_score
        }


class StrategyOptimizer:
    """
    Optimizer for trading strategy parameters
    
    Features:
    - Bayesian optimization of strategy parameters
    - Backtesting-based objective function
    - Cross-validation across market regimes
    - Robustness checks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize Bayesian optimizer
        self.optimizer = BayesianOptimizer(self.config.get('bayesian_optimizer', {}))
        
        # Default parameter space
        self._setup_default_parameter_space()
        
        # Optimization results
        self.optimization_results = {}
        
        logger.info("Strategy optimizer initialized")
    
    def _setup_default_parameter_space(self):
        """Setup default parameter space for strategy optimization"""
        # Position sizing parameters
        self.optimizer.add_parameter('position_size_multiplier', 0.1, 2.0, 'continuous')
        self.optimizer.add_parameter('max_position_size', 0.1, 5.0, 'continuous')
        
        # Entry parameters
        self.optimizer.add_parameter('entry_threshold', 0.5, 0.95, 'continuous')
        self.optimizer.add_parameter('entry_confirmation_required', 0, 1, 'integer')
        
        # Exit parameters
        self.optimizer.add_parameter('stop_loss_multiplier', 0.5, 2.0, 'continuous')
        self.optimizer.add_parameter('take_profit_multiplier', 0.5, 2.0, 'continuous')
        self.optimizer.add_parameter('trailing_stop_enabled', 0, 1, 'integer')
        self.optimizer.add_parameter('trailing_stop_distance', 0.01, 0.1, 'continuous')
        
        # Risk parameters
        self.optimizer.add_parameter('risk_per_trade', 0.001, 0.03, 'continuous')
        
        logger.debug("Setup default parameter space")
    
    def optimize_strategy(self, backtest_function: Callable[[Dict[str, Any]], float],
                         market_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Optimize strategy parameters using Bayesian optimization
        
        Args:
            backtest_function: Function that runs backtest and returns performance metric
            market_data: Optional market data for cross-validation
            
        Returns:
            Optimized strategy parameters
        """
        logger.info("Starting strategy optimization")
        
        # Run optimization
        best_params = self.optimizer.optimize(backtest_function, maximize=True)
        
        # Store results
        self.optimization_results = self.optimizer.get_optimization_history()
        
        return best_params
    
    async def optimize_strategy_async(self, backtest_function: Callable[[Dict[str, Any]], float],
                                    market_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Optimize strategy parameters using Bayesian optimization (async version)
        
        Args:
            backtest_function: Async function that runs backtest and returns performance metric
            market_data: Optional market data for cross-validation
            
        Returns:
            Optimized strategy parameters
        """
        logger.info("Starting async strategy optimization")
        
        # Run optimization
        best_params = await self.optimizer.optimize_async(backtest_function, maximize=True)
        
        # Store results
        self.optimization_results = self.optimizer.get_optimization_history()
        
        return best_params
    
    def optimize_by_regime(self, backtest_function: Callable[[Dict[str, Any], int], float],
                         regimes: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Optimize strategy parameters for each market regime
        
        Args:
            backtest_function: Function that runs backtest for a specific regime
            regimes: List of regime IDs to optimize for
            
        Returns:
            Dictionary of optimized parameters by regime
        """
        regime_params = {}
        
        for regime_id in regimes:
            logger.info(f"Optimizing parameters for regime {regime_id}")
            
            # Create regime-specific objective function
            def objective(params):
                return backtest_function(params, regime_id)
            
            # Reset optimizer for each regime
            self.optimizer = BayesianOptimizer(self.config.get('bayesian_optimizer', {}))
            self._setup_default_parameter_space()
            
            # Run optimization
            best_params = self.optimizer.optimize(objective, maximize=True)
            
            # Store results
            regime_params[regime_id] = best_params
            
            logger.info(f"Completed optimization for regime {regime_id}")
        
        return regime_params
    
    def get_optimization_results(self) -> Dict[str, Any]:
        """Get optimization results"""
        return self.optimization_results
