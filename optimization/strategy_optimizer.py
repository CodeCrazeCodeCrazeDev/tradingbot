"""
Strategy optimization engine for AlphaAlgo 2.0
"""

import logging
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import optuna
from concurrent.futures import ProcessPoolExecutor
import joblib

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Strategy optimization results."""
    best_params: Dict
    best_score: float
    all_trials: List[Dict]
    optimization_time: float
    parameter_importance: Dict
    convergence_data: List[float]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class StrategyOptimizer:
    """
    Advanced strategy optimization engine.
    Uses Bayesian optimization for parameter tuning.
    """
    
    def __init__(
        self,
        n_trials: int = 100,
        n_jobs: int = -1,
        timeout: Optional[int] = None,
        random_state: int = 42
    ):
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.timeout = timeout
        self.random_state = random_state
        
        # Optimization state
        self.study = None
        self.best_trial = None
        self.parameter_ranges = {}
        
        logger.info("✅ Strategy Optimizer initialized")
        logger.info(f"   Trials: {n_trials}")
        logger.info(f"   Jobs: {n_jobs}")
    
    def optimize(
        self,
        objective_func: Callable,
        parameter_ranges: Dict,
        direction: str = 'maximize'
    ) -> OptimizationResult:
        """
        Optimize strategy parameters.
        
        Args:
            objective_func: Function to optimize
            parameter_ranges: Parameter ranges to search
            direction: 'maximize' or 'minimize'
        
        Returns:
            OptimizationResult object
        """
        try:
            logger.info("🚀 Starting strategy optimization...")
            start_time = datetime.now()
            
            self.parameter_ranges = parameter_ranges
            
            # Create study
            self.study = optuna.create_study(
                direction=direction,
                sampler=optuna.samplers.TPESampler(
                    seed=self.random_state
                )
            )
            
            # Run optimization
            self.study.optimize(
                lambda trial: self._objective_wrapper(
                    trial, objective_func
                ),
                n_trials=self.n_trials,
                n_jobs=self.n_jobs,
                timeout=self.timeout
            )
            
            # Calculate results
            optimization_time = (datetime.now() - start_time).total_seconds()
            
            results = OptimizationResult(
                best_params=self.study.best_params,
                best_score=self.study.best_value,
                all_trials=self._get_trial_data(),
                optimization_time=optimization_time,
                parameter_importance=self._calculate_importance(),
                convergence_data=self._get_convergence_data()
            )
            
            logger.info("✅ Optimization completed")
            logger.info(f"   Best score: {results.best_score:.4f}")
            logger.info(f"   Time taken: {optimization_time:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Optimization error: {str(e)}")
            raise
    
    def _objective_wrapper(
        self,
        trial: optuna.Trial,
        objective_func: Callable
    ) -> float:
        """Wrap objective function with parameter suggestions."""
        params = {}
        
        # Suggest parameters based on ranges
        for name, spec in self.parameter_ranges.items():
            param_type = spec['type']
            
            if param_type == 'int':
                params[name] = trial.suggest_int(
                    name,
                    spec['low'],
                    spec['high'],
                    step=spec.get('step', 1)
                )
            
            elif param_type == 'float':
                if spec.get('log', False):
                    params[name] = trial.suggest_loguniform(
                        name,
                        spec['low'],
                        spec['high']
                    )
                else:
                    params[name] = trial.suggest_float(
                        name,
                        spec['low'],
                        spec['high'],
                        step=spec.get('step')
                    )
            
            elif param_type == 'categorical':
                params[name] = trial.suggest_categorical(
                    name,
                    spec['choices']
                )
        
        # Run objective
        return objective_func(params)
    
    def _get_trial_data(self) -> List[Dict]:
        """Get data from all trials."""
        trials = []
        
        for trial in self.study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                trials.append({
                    'number': trial.number,
                    'params': trial.params,
                    'value': trial.value,
                    'duration': trial.duration.total_seconds()
                })
        
        return trials
    
    def _calculate_importance(self) -> Dict[str, float]:
        """Calculate parameter importance."""
        try:
            importance = optuna.importance.get_param_importances(
                self.study
            )
            return dict(importance)
        except Exception:
            # Fall back to correlation-based importance
            return self._calculate_correlation_importance()
    
    def _calculate_correlation_importance(self) -> Dict[str, float]:
        """Calculate importance based on correlation with objective."""
        importance = {}
        trials = self._get_trial_data()
        
        if not trials:
            return {}
        
        # Get values
        values = np.array([t['value'] for t in trials])
        
        # Calculate for each parameter
        for param in self.parameter_ranges.keys():
            param_values = []
            for trial in trials:
                if param in trial['params']:
                    param_values.append(trial['params'][param])
            
            if param_values:
                param_values = np.array(param_values)
                if len(param_values.shape) == 1:  # Numerical parameter
                    corr = abs(np.corrcoef(param_values, values)[0, 1])
                    importance[param] = max(0, corr)  # Handle NaN
                else:  # Categorical parameter
                    importance[param] = 0.0
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {
                k: v/total for k, v in importance.items()
            }
        
        return importance
    
    def _get_convergence_data(self) -> List[float]:
        """Get optimization convergence data."""
        values = []
        best_so_far = float('-inf')
        
        for trial in self.study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                best_so_far = max(best_so_far, trial.value)
                values.append(best_so_far)
        
        return values
    
    def cross_validate(
        self,
        params: Dict,
        objective_func: Callable,
        n_splits: int = 5
    ) -> Dict:
        """
        Cross validate strategy parameters.
        
        Args:
            params: Parameters to validate
            objective_func: Objective function
            n_splits: Number of CV splits
        
        Returns:
            Cross validation results
        """
        try:
            logger.info(f"🔄 Running {n_splits}-fold cross validation...")
            
            scores = []
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []
                
                # Submit jobs
                for i in range(n_splits):
                    future = executor.submit(
                        objective_func,
                        params,
                        fold=i
                    )
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    score = future.result()
                    scores.append(score)
            
            # Calculate statistics
            cv_results = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'scores': scores
            }
            
            logger.info("✅ Cross validation completed")
            logger.info(f"   Mean score: {cv_results['mean']:.4f} ± {cv_results['std']:.4f}")
            
            return cv_results
            
        except Exception as e:
            logger.error(f"❌ Cross validation error: {str(e)}")
            raise
    
    def optimize_portfolio(
        self,
        returns: np.ndarray,
        constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Optimize portfolio weights.
        
        Args:
            returns: Asset returns matrix
            constraints: Optional constraints
        
        Returns:
            Optimal weights
        """
        try:
            logger.info("📊 Running portfolio optimization...")
            
            n_assets = returns.shape[1]
            
            def objective(trial):
                weights = []
                remaining = 1.0
                
                # Generate weights that sum to 1
                for i in range(n_assets - 1):
                    if remaining <= 0:
                        weights.append(0.0)
                        continue
                    
                    w = trial.suggest_float(
                        f'w_{i}',
                        0.0,
                        remaining
                    )
                    weights.append(w)
                    remaining -= w
                
                weights.append(remaining)
                weights = np.array(weights)
                
                # Calculate portfolio metrics
                port_return = np.sum(returns.mean(axis=0) * weights) * 252
                port_vol = np.sqrt(
                    np.dot(weights.T, np.dot(returns.cov() * 252, weights))
                )
                
                # Sharpe ratio
                sharpe = port_return / port_vol
                
                return sharpe
            
            # Create study for portfolio optimization
            study = optuna.create_study(direction='maximize')
            
            # Run optimization
            study.optimize(
                objective,
                n_trials=self.n_trials,
                timeout=self.timeout
            )
            
            # Get optimal weights
            weights = []
            remaining = 1.0
            
            for i in range(n_assets - 1):
                if remaining <= 0:
                    weights.append(0.0)
                    continue
                
                w = study.best_params[f'w_{i}']
                weights.append(w)
                remaining -= w
            
            weights.append(remaining)
            weights = np.array(weights)
            
            # Calculate metrics
            port_return = np.sum(returns.mean(axis=0) * weights) * 252
            port_vol = np.sqrt(
                np.dot(weights.T, np.dot(returns.cov() * 252, weights))
            )
            sharpe = port_return / port_vol
            
            results = {
                'weights': weights.tolist(),
                'metrics': {
                    'return': float(port_return),
                    'volatility': float(port_vol),
                    'sharpe': float(sharpe)
                }
            }
            
            logger.info("✅ Portfolio optimization completed")
            logger.info(f"   Sharpe ratio: {sharpe:.4f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Portfolio optimization error: {str(e)}")
            raise
    
    def save_study(self, filepath: str):
        """Save optimization study."""
        if self.study is None:
            logger.warning("⚠️ No study to save")
            return
        
        joblib.dump(self.study, filepath)
        logger.info(f"💾 Study saved to {filepath}")
    
    def load_study(self, filepath: str):
        """Load optimization study."""
        self.study = joblib.load(filepath)
        logger.info(f"📂 Study loaded from {filepath}")
    
    def plot_optimization_history(
        self,
        filename: Optional[str] = None
    ):
        """Plot optimization history."""
        if self.study is None:
            logger.warning("⚠️ No study to plot")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
            
            # Plot optimization history
            optuna.visualization.plot_optimization_history(
                self.study
            ).write_image(ax1)
            
            # Plot parameter importance
            optuna.visualization.plot_param_importances(
                self.study
            ).write_image(ax2)
            
            plt.tight_layout()
            
            if filename:
                plt.savefig(filename)
                logger.info(f"✅ Optimization plot saved to {filename}")
            else:
                plt.show()
            
        except ImportError:
            logger.warning("⚠️ plotly not available for plotting")
