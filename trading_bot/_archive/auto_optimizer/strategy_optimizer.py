"""
Automatic Strategy Optimizer
Uses genetic algorithms, Bayesian optimization, and grid search
"""

import logging
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """Optimization methods"""
    GENETIC = "genetic"
    BAYESIAN = "bayesian"
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    PARTICLE_SWARM = "particle_swarm"


@dataclass
class OptimizationResult:
    """Optimization result"""
    method: OptimizationMethod
    best_params: Dict[str, Any]
    best_score: float
    iterations: int
    duration_seconds: float
    all_results: List[Dict[str, Any]]
    timestamp: datetime


class GeneticOptimizer:
    """Genetic algorithm optimizer"""
    
    def __init__(self, population_size: int = 50, generations: int = 100, mutation_rate: float = 0.1):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
    
    def optimize(self, 
                 objective_func: Callable,
                 param_space: Dict[str, Tuple[float, float]],
                 maximize: bool = True) -> Dict[str, Any]:
        """
        Optimize using genetic algorithm
        
        Args:
            objective_func: Function to optimize
            param_space: Parameter space {param_name: (min, max)}
            maximize: Whether to maximize (True) or minimize (False)
            
        Returns:
            Best parameters found
        """
        # Initialize population
        population = self._initialize_population(param_space)
        
        best_individual = None
        best_score = float('-inf') if maximize else float('inf')
        
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                score = objective_func(individual)
                fitness_scores.append(score)
                
                # Track best
                if maximize and score > best_score:
                    best_score = score
                    best_individual = individual.copy()
                elif not maximize and score < best_score:
                    best_score = score
                    best_individual = individual.copy()
            
            # Selection
            selected = self._selection(population, fitness_scores, maximize)
            
            # Crossover
            offspring = self._crossover(selected, param_space)
            
            # Mutation
            population = self._mutation(offspring, param_space)
            
            if generation % 10 == 0:
                logger.info(f"Generation {generation}: Best score = {best_score:.4f}")
        
        return best_individual
    
    def _initialize_population(self, param_space: Dict[str, Tuple[float, float]]) -> List[Dict[str, float]]:
        """Initialize random population"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in param_space.items():
                individual[param] = np.random.uniform(min_val, max_val)
            population.append(individual)
        return population
    
    def _selection(self, population: List[Dict], fitness_scores: List[float], maximize: bool) -> List[Dict]:
        """Tournament selection"""
        selected = []
        for _ in range(len(population)):
            # Tournament
            idx1, idx2 = np.random.choice(len(population), 2, replace=False)
            if maximize:
                winner = idx1 if fitness_scores[idx1] > fitness_scores[idx2] else idx2
            else:
                winner = idx1 if fitness_scores[idx1] < fitness_scores[idx2] else idx2
            selected.append(population[winner].copy())
        return selected
    
    def _crossover(self, population: List[Dict], param_space: Dict) -> List[Dict]:
        """Single-point crossover"""
        offspring = []
        for i in range(0, len(population), 2):
            parent1 = population[i]
            parent2 = population[i + 1] if i + 1 < len(population) else population[0]
            
            # Crossover
            child1, child2 = {}, {}
            params = list(param_space.keys())
            crossover_point = np.random.randint(1, len(params))
            
            for j, param in enumerate(params):
                if j < crossover_point:
                    child1[param] = parent1[param]
                    child2[param] = parent2[param]
                else:
                    child1[param] = parent2[param]
                    child2[param] = parent1[param]
            
            offspring.extend([child1, child2])
        
        return offspring[:len(population)]
    
    def _mutation(self, population: List[Dict], param_space: Dict) -> List[Dict]:
        """Random mutation"""
        for individual in population:
            for param, (min_val, max_val) in param_space.items():
                if np.random.random() < self.mutation_rate:
                    individual[param] = np.random.uniform(min_val, max_val)
        return population


class BayesianOptimizer:
    """Bayesian optimization using Gaussian processes"""
    
    def __init__(self, n_iterations: int = 100, n_initial: int = 10):
        self.n_iterations = n_iterations
        self.n_initial = n_initial
    
    def optimize(self,
                 objective_func: Callable,
                 param_space: Dict[str, Tuple[float, float]],
                 maximize: bool = True) -> Dict[str, Any]:
        """
        Optimize using Bayesian optimization
        
        Args:
            objective_func: Function to optimize
            param_space: Parameter space
            maximize: Whether to maximize
            
        Returns:
            Best parameters found
        """
        try:
            from skopt import gp_minimize
            from skopt.space import Real
            
            # Define search space
            dimensions = [Real(min_val, max_val, name=param) 
                         for param, (min_val, max_val) in param_space.items()]
            
            # Wrapper function
            def objective_wrapper(params):
                param_dict = {name: val for name, val in zip(param_space.keys(), params)}
                score = objective_func(param_dict)
                return -score if maximize else score
            
            # Run optimization
            result = gp_minimize(
                objective_wrapper,
                dimensions,
                n_calls=self.n_iterations,
                n_initial_points=self.n_initial,
                random_state=42
            )
            
            # Extract best parameters
            best_params = {name: val for name, val in zip(param_space.keys(), result.x)}
            
            return best_params
        
        except ImportError:
            logger.warning("scikit-optimize not available, using random search")
            return self._random_search(objective_func, param_space, maximize)
    
    def _random_search(self, objective_func: Callable, param_space: Dict, maximize: bool) -> Dict[str, Any]:
        """Fallback random search"""
        best_params = None
        best_score = float('-inf') if maximize else float('inf')
        
        for _ in range(self.n_iterations):
            params = {param: np.random.uniform(min_val, max_val) 
                     for param, (min_val, max_val) in param_space.items()}
            
            score = objective_func(params)
            
            if maximize and score > best_score:
                best_score = score
                best_params = params
            elif not maximize and score < best_score:
                best_score = score
                best_params = params
        
        return best_params


class GridSearchOptimizer:
    """Grid search optimizer"""
    
    def __init__(self, n_points: int = 10):
        self.n_points = n_points
    
    def optimize(self,
                 objective_func: Callable,
                 param_space: Dict[str, Tuple[float, float]],
                 maximize: bool = True) -> Dict[str, Any]:
        """
        Optimize using grid search
        
        Args:
            objective_func: Function to optimize
            param_space: Parameter space
            maximize: Whether to maximize
            
        Returns:
            Best parameters found
        """
        # Create grid
        param_grids = {}
        for param, (min_val, max_val) in param_space.items():
            param_grids[param] = np.linspace(min_val, max_val, self.n_points)
        
        # Evaluate all combinations
        best_params = None
        best_score = float('-inf') if maximize else float('inf')
        
        def recursive_search(params_so_far, remaining_params):
            nonlocal best_params, best_score
            
            if not remaining_params:
                # Evaluate
                score = objective_func(params_so_far)
                
                if maximize and score > best_score:
                    best_score = score
                    best_params = params_so_far.copy()
                elif not maximize and score < best_score:
                    best_score = score
                    best_params = params_so_far.copy()
                return
            
            # Recurse
            param = remaining_params[0]
            for value in param_grids[param]:
                params_so_far[param] = value
                recursive_search(params_so_far, remaining_params[1:])
        
        recursive_search({}, list(param_space.keys()))
        
        return best_params


class StrategyOptimizer:
    """
    Automatic Strategy Optimizer
    Continuously optimizes trading parameters
    """
    
    def __init__(self, 
                 trading_bot: Any,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize strategy optimizer"""
        self.trading_bot = trading_bot
        self.config = config or {}
        
        # Optimizers
        self.genetic = GeneticOptimizer(
            population_size=self.config.get('population_size', 50),
            generations=self.config.get('generations', 100),
            mutation_rate=self.config.get('mutation_rate', 0.1)
        )
        
        self.bayesian = BayesianOptimizer(
            n_iterations=self.config.get('n_iterations', 100),
            n_initial=self.config.get('n_initial', 10)
        )
        
        self.grid_search = GridSearchOptimizer(
            n_points=self.config.get('n_points', 10)
        )
        
        # Optimization history
        self.history: List[OptimizationResult] = []
    
    def optimize(self,
                 param_space: Dict[str, Tuple[float, float]],
                 method: OptimizationMethod = OptimizationMethod.GENETIC,
                 maximize: bool = True) -> OptimizationResult:
        """
        Optimize strategy parameters
        
        Args:
            param_space: Parameter space to search
            method: Optimization method
            maximize: Whether to maximize objective
            
        Returns:
            Optimization result
        """
        start_time = datetime.now()
        
        # Define objective function
        def objective_func(params: Dict[str, Any]) -> float:
            return self._evaluate_params(params)
        
        # Run optimization
        if method == OptimizationMethod.GENETIC:
            best_params = self.genetic.optimize(objective_func, param_space, maximize)
        elif method == OptimizationMethod.BAYESIAN:
            best_params = self.bayesian.optimize(objective_func, param_space, maximize)
        elif method == OptimizationMethod.GRID_SEARCH:
            best_params = self.grid_search.optimize(objective_func, param_space, maximize)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Evaluate best parameters
        best_score = objective_func(best_params)
        
        # Create result
        duration = (datetime.now() - start_time).total_seconds()
        result = OptimizationResult(
            method=method,
            best_params=best_params,
            best_score=best_score,
            iterations=self._get_iterations(method),
            duration_seconds=duration,
            all_results=[],
            timestamp=datetime.now()
        )
        
        # Store in history
        self.history.append(result)
        
        logger.info(f"Optimization complete: {method.value}, Score: {best_score:.4f}")
        
        return result
    
    def _evaluate_params(self, params: Dict[str, Any]) -> float:
        """
        Evaluate parameter set
        
        Args:
            params: Parameters to evaluate
            
        Returns:
            Performance score
        """
        # Apply parameters to bot
        if hasattr(self.trading_bot, 'set_parameters'):
            self.trading_bot.set_parameters(params)
        
        # Run backtest or get performance
        if hasattr(self.trading_bot, 'backtest'):
            results = self.trading_bot.backtest(params)
            return results.get('sharpe_ratio', 0)
        elif hasattr(self.trading_bot, 'get_performance'):
            perf = self.trading_bot.get_performance()
            return perf.get('sharpe_ratio', 0)
        else:
            # Placeholder scoring
            return np.random.random()
    
    def _get_iterations(self, method: OptimizationMethod) -> int:
        """Get number of iterations for method"""
        if method == OptimizationMethod.GENETIC:
            return self.genetic.generations
        elif method == OptimizationMethod.BAYESIAN:
            return self.bayesian.n_iterations
        elif method == OptimizationMethod.GRID_SEARCH:
            return self.grid_search.n_points ** len(self.config.get('param_space', {}))
        return 0
    
    def auto_optimize(self, 
                     param_space: Dict[str, Tuple[float, float]],
                     interval_hours: int = 24):
        """
        Automatically optimize parameters periodically
        
        Args:
            param_space: Parameter space
            interval_hours: Hours between optimizations
        """
        import asyncio
        
        async def optimization_loop():
            while True:
                try:
                    logger.info("Starting automatic optimization...")
                    
                    # Run optimization
                    result = self.optimize(param_space, OptimizationMethod.GENETIC)
                    
                    # Apply best parameters
                    if hasattr(self.trading_bot, 'update_parameters'):
                        self.trading_bot.update_parameters(result.best_params)
                    
                    logger.info(f"Applied optimized parameters: {result.best_params}")
                    
                    # Wait for next optimization
                    await asyncio.sleep(interval_hours * 3600)
                
                except Exception as e:
                    logger.error(f"Auto-optimization error: {e}")
                    await asyncio.sleep(3600)
        
        # Start loop
        asyncio.create_task(optimization_loop())
    
    def get_best_result(self) -> Optional[OptimizationResult]:
        """Get best optimization result"""
        if not self.history:
            return None
        
        return max(self.history, key=lambda r: r.best_score)
    
    def export_results(self, filepath: str):
        """Export optimization results to file"""
        results_data = []
        for result in self.history:
            results_data.append({
                'method': result.method.value,
                'best_params': result.best_params,
                'best_score': result.best_score,
                'iterations': result.iterations,
                'duration_seconds': result.duration_seconds,
                'timestamp': result.timestamp.isoformat()
            })
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Exported {len(results_data)} optimization results to {filepath}")


__all__ = [
    'StrategyOptimizer',
    'OptimizationMethod',
    'OptimizationResult',
    'GeneticOptimizer',
    'BayesianOptimizer',
    'GridSearchOptimizer'
]
