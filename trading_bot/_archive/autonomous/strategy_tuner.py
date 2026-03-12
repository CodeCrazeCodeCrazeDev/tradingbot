"""
Autonomous Strategy Tuner ($0 Budget)
Self-optimizing parameters using genetic algorithms
Continuous performance monitoring and adjustment
"""

import numpy as np
from typing import Callable, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from scipy.optimize import differential_evolution, minimize
import json
import os
import numpy

import logging
logger = logging.getLogger(__name__)



@dataclass
class OptimizationResult:
    """Optimization result"""
    strategy_name: str
    original_params: Dict
    optimized_params: Dict
    original_performance: float
    optimized_performance: float
    improvement: float
    iterations: int
    timestamp: datetime


class GeneticOptimizer:
    """Genetic algorithm optimizer (free)"""
    
    def __init__(self, population_size: int = 50, generations: int = 100):
        self.population_size = population_size
        self.generations = generations
        self.history: List[Dict] = []
        
    def optimize(
        self,
        objective_func: Callable,
        bounds: List[Tuple[float, float]],
        maximize: bool = True
    ) -> Dict:
        """Optimize using genetic algorithm"""
        
        # Use scipy's differential evolution (genetic algorithm)
        result = differential_evolution(
            func=lambda x: -objective_func(x) if maximize else objective_func(x),
            bounds=bounds,
            maxiter=self.generations,
            popsize=self.population_size // len(bounds),
            seed=42,
            workers=1,
            updating='deferred',
            polish=True
        )
        
        return {
            'best_params': result.x.tolist(),
            'best_score': -result.fun if maximize else result.fun,
            'iterations': result.nit,
            'success': result.success,
            'message': result.message
        }


class BayesianOptimizer:
    """Bayesian optimization (free, simplified)"""
    
    def __init__(self, n_iterations: int = 50):
        self.n_iterations = n_iterations
        
    def optimize(
        self,
        objective_func: Callable,
        bounds: List[Tuple[float, float]]
    ) -> Dict:
        """Optimize using Bayesian approach (simplified)"""
        
        # Random search with adaptive sampling
        best_params = None
        best_score = -np.inf
        
        # Initial random samples
        n_random = min(10, self.n_iterations // 2)
        
        for i in range(self.n_iterations):
            if i < n_random:
                # Random sampling
                params = [np.random.uniform(low, high) for low, high in bounds]
            else:
                # Exploit best region with noise
                if best_params is not None:
                    noise = np.random.randn(len(bounds)) * 0.1
                    params = np.clip(
                        np.array(best_params) + noise,
                        [b[0] for b in bounds],
                        [b[1] for b in bounds]
                    ).tolist()
                else:
                    params = [np.random.uniform(low, high) for low, high in bounds]
            
            # Evaluate
            score = objective_func(params)
            
            if score > best_score:
                best_score = score
                best_params = params
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': self.n_iterations,
            'success': True
        }


class GridSearchOptimizer:
    """Grid search optimizer (free)"""
    
    def __init__(self, n_points: int = 10):
        self.n_points = n_points
        
    def optimize(
        self,
        objective_func: Callable,
        bounds: List[Tuple[float, float]]
    ) -> Dict:
        """Optimize using grid search"""
        
        # Create grid
        grids = [np.linspace(low, high, self.n_points) for low, high in bounds]
        
        best_params = None
        best_score = -np.inf
        total_iterations = 0
        
        # Evaluate all combinations
        def evaluate_grid(grid_idx, current_params):
            nonlocal best_params, best_score, total_iterations
            
            if grid_idx == len(grids):
                # Evaluate this combination
                score = objective_func(current_params)
                total_iterations += 1
                
                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()
                return
            
            # Iterate through this dimension
            for value in grids[grid_idx]:
                current_params[grid_idx] = value
                evaluate_grid(grid_idx + 1, current_params)
        
        evaluate_grid(0, [0] * len(bounds))
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': total_iterations,
            'success': True
        }


class PerformanceMonitor:
    """Continuous performance monitoring (free)"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.performance_history: List[Dict] = []
        
    def record_performance(
        self,
        strategy_name: str,
        metrics: Dict
    ):
        """Record strategy performance"""
        
        self.performance_history.append({
            'strategy': strategy_name,
            'metrics': metrics,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.performance_history) > self.window_size:
            self.performance_history = self.performance_history[-self.window_size:]
    
    def get_performance_trend(self, strategy_name: str) -> Dict:
        """Get performance trend"""
        
        strategy_records = [
            r for r in self.performance_history
            if r['strategy'] == strategy_name
        ]
        
        if not strategy_records:
            return {'trend': 'unknown', 'degradation': False}
        
        # Calculate trend
        recent = strategy_records[-10:] if len(strategy_records) >= 10 else strategy_records
        older = strategy_records[-20:-10] if len(strategy_records) >= 20 else []
        
        if not older:
            return {'trend': 'insufficient_data', 'degradation': False}
        
        # Compare recent vs older performance
        recent_avg = np.mean([r['metrics'].get('sharpe_ratio', 0) for r in recent])
        older_avg = np.mean([r['metrics'].get('sharpe_ratio', 0) for r in older])
        
        degradation = recent_avg < older_avg * 0.8  # 20% degradation threshold
        
        return {
            'trend': 'declining' if recent_avg < older_avg else 'improving',
            'degradation': degradation,
            'recent_avg': recent_avg,
            'older_avg': older_avg,
            'change': (recent_avg - older_avg) / older_avg if older_avg != 0 else 0
        }
    
    def should_retune(self, strategy_name: str) -> bool:
        """Check if strategy needs retuning"""
        
        trend = self.get_performance_trend(strategy_name)
        return trend.get('degradation', False)


class AutonomousStrategyTuner:
    """Autonomous strategy tuner with continuous optimization"""
    
    def __init__(self, results_dir: str = './tuning_results'):
        self.genetic_optimizer = GeneticOptimizer()
        self.bayesian_optimizer = BayesianOptimizer()
        self.grid_optimizer = GridSearchOptimizer()
        self.performance_monitor = PerformanceMonitor()
        self.results_dir = results_dir
        self.optimization_history: List[OptimizationResult] = []
        
        # Create results directory
        os.makedirs(results_dir, exist_ok=True)
        
    def tune_strategy(
        self,
        strategy_name: str,
        strategy_func: Callable,
        param_bounds: Dict[str, Tuple[float, float]],
        test_data: np.ndarray,
        method: str = 'genetic'
    ) -> OptimizationResult:
        """Tune strategy parameters"""
        
        # Get original parameters (midpoint of bounds)
        original_params = {
            name: (bounds[0] + bounds[1]) / 2
            for name, bounds in param_bounds.items()
        }
        
        # Define objective function
        def objective(params_array):
            # Convert array to dict
            params_dict = {
                name: params_array[i]
                for i, name in enumerate(param_bounds.keys())
            }
            
            try:
                # Test strategy
                signals = strategy_func(test_data, **params_dict)
                
                # Calculate returns
                returns = np.diff(test_data) / test_data[:-1]
                strategy_returns = returns * signals[:-1]
                
                # Calculate Sharpe ratio
                if len(strategy_returns) > 0 and np.std(strategy_returns) > 0:
                    sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
                    return sharpe
                return -999
            except Exception:
                return -999
        
        # Optimize
        bounds_list = list(param_bounds.values())
        
        if method == 'genetic':
            result = self.genetic_optimizer.optimize(objective, bounds_list, maximize=True)
        elif method == 'bayesian':
            result = self.bayesian_optimizer.optimize(objective, bounds_list)
        elif method == 'grid':
            result = self.grid_optimizer.optimize(objective, bounds_list)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Convert optimized params back to dict
        optimized_params = {
            name: result['best_params'][i]
            for i, name in enumerate(param_bounds.keys())
        }
        
        # Calculate original performance
        original_performance = objective([original_params[name] for name in param_bounds.keys()])
        
        # Create result
        optimization_result = OptimizationResult(
            strategy_name=strategy_name,
            original_params=original_params,
            optimized_params=optimized_params,
            original_performance=original_performance,
            optimized_performance=result['best_score'],
            improvement=(result['best_score'] - original_performance) / abs(original_performance) if original_performance != 0 else 0,
            iterations=result['iterations'],
            timestamp=datetime.now()
        )
        
        # Save result
        self.optimization_history.append(optimization_result)
        self._save_result(optimization_result)
        
        return optimization_result
    
    def continuous_monitoring(
        self,
        strategy_name: str,
        current_performance: Dict
    ) -> Dict:
        """Monitor strategy performance continuously"""
        
        # Record performance
        self.performance_monitor.record_performance(strategy_name, current_performance)
        
        # Check if retuning needed
        should_retune = self.performance_monitor.should_retune(strategy_name)
        trend = self.performance_monitor.get_performance_trend(strategy_name)
        
        return {
            'strategy': strategy_name,
            'should_retune': should_retune,
            'trend': trend,
            'recommendation': 'retune_now' if should_retune else 'continue_monitoring',
            'timestamp': datetime.now()
        }
    
    def auto_tune_on_degradation(
        self,
        strategy_name: str,
        strategy_func: Callable,
        param_bounds: Dict[str, Tuple[float, float]],
        test_data: np.ndarray,
        current_performance: Dict
    ) -> Dict:
        """Automatically tune if performance degrades"""
        
        # Monitor performance
        monitoring_result = self.continuous_monitoring(strategy_name, current_performance)
        
        if monitoring_result['should_retune']:
            # Auto-tune
            tuning_result = self.tune_strategy(
                strategy_name,
                strategy_func,
                param_bounds,
                test_data,
                method='genetic'
            )
            
            return {
                'action': 'retuned',
                'monitoring': monitoring_result,
                'tuning': tuning_result,
                'new_params': tuning_result.optimized_params,
                'improvement': tuning_result.improvement
            }
        
        return {
            'action': 'no_action_needed',
            'monitoring': monitoring_result
        }
    
    def _save_result(self, result: OptimizationResult):
        """Save optimization result"""
        
        filename = f"{result.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        data = {
            'strategy_name': result.strategy_name,
            'original_params': result.original_params,
            'optimized_params': result.optimized_params,
            'original_performance': result.original_performance,
            'optimized_performance': result.optimized_performance,
            'improvement': result.improvement,
            'iterations': result.iterations,
            'timestamp': result.timestamp.isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_best_params(self, strategy_name: str) -> Dict:
        """Get best parameters for strategy"""
        
        strategy_results = [
            r for r in self.optimization_history
            if r.strategy_name == strategy_name
        ]
        
        if not strategy_results:
            return {}
        
        best_result = max(strategy_results, key=lambda r: r.optimized_performance)
        return best_result.optimized_params


# Example usage
if __name__ == '__main__':
    # Initialize tuner
    tuner = AutonomousStrategyTuner()
    
    # Generate test data
    np.random.seed(42)
    test_data = np.cumsum(np.random.randn(500) * 0.01) + 100
    
    # Define strategy
    def momentum_strategy(prices, lookback=20, threshold=0.02):
        signals = np.zeros(len(prices))
        for i in range(int(lookback), len(prices)):
            returns = (prices[i] - prices[int(i-lookback)]) / prices[int(i-lookback)]
            if returns > threshold:
                signals[i] = 1
            elif returns < -threshold:
                signals[i] = -1
        return signals
    
    # Define parameter bounds
    param_bounds = {
        'lookback': (10, 50),
        'threshold': (0.01, 0.1)
    }
    
    # Tune strategy
    logger.info("Tuning momentum strategy...")
    result = tuner.tune_strategy(
        strategy_name='momentum',
        strategy_func=momentum_strategy,
        param_bounds=param_bounds,
        test_data=test_data,
        method='genetic'
    )
    
    logger.info(f"\nOptimization Results:")
    logger.info(f"Original params: {result.original_params}")
    logger.info(f"Optimized params: {result.optimized_params}")
    logger.info(f"Original performance: {result.original_performance:.4f}")
    logger.info(f"Optimized performance: {result.optimized_performance:.4f}")
    logger.info(f"Improvement: {result.improvement:.2%}")
    logger.info(f"Iterations: {result.iterations}")
    
    # Simulate continuous monitoring
    print("\n" + "="*60)
    logger.info("Continuous Monitoring Demo:")
    
    for i in range(5):
        # Simulate performance
        performance = {
            'sharpe_ratio': 1.5 - i * 0.15,  # Degrading performance
            'return': 0.10 - i * 0.02
        }
        
        monitoring = tuner.continuous_monitoring('momentum', performance)
        logger.info(f"\nPeriod {i+1}:")
        logger.info(f"  Sharpe: {performance['sharpe_ratio']:.2f}")
        logger.info(f"  Should retune: {monitoring['should_retune']}")
        logger.info(f"  Trend: {monitoring['trend']['trend']}")
