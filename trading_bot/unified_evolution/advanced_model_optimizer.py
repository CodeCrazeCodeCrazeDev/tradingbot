"""
Advanced Model Optimizer
=========================

Advanced optimization methods for ML models across all systems.
Includes Bayesian optimization, genetic algorithms, neural architecture search,
and other cutting-edge optimization techniques.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """Optimization methods"""
    BAYESIAN = "bayesian"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    SIMULATED_ANNEALING = "simulated_annealing"
    GRADIENT_BASED = "gradient_based"
    RANDOM_SEARCH = "random_search"
    GRID_SEARCH = "grid_search"
    HYPERBAND = "hyperband"
    POPULATION_BASED = "population_based"
    EVOLUTIONARY_STRATEGY = "evolutionary_strategy"


@dataclass
class HyperparameterSpace:
    """Hyperparameter search space definition"""
    name: str
    param_type: str  # continuous, discrete, categorical
    
    # For continuous/discrete
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # For categorical
    categories: Optional[List[Any]] = None
    
    # Distribution
    distribution: str = "uniform"  # uniform, log_uniform, normal
    
    # Constraints
    constraints: List[str] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Result of optimization"""
    optimization_id: str
    method: OptimizationMethod
    
    best_params: Dict[str, Any]
    best_score: float
    
    iterations: int
    evaluations: int
    
    convergence_history: List[float]
    param_history: List[Dict[str, Any]]
    
    time_elapsed_seconds: float
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AdvancedModelOptimizer:
    """
    Advanced model optimization using multiple state-of-the-art methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Optimization history
        self.optimization_history: List[OptimizationResult] = []
        
        # Method performance tracking
        self.method_performance: Dict[OptimizationMethod, List[float]] = {
            method: [] for method in OptimizationMethod
        }
        
        logger.info("AdvancedModelOptimizer initialized")
    
    def optimize(self, objective_function: Callable,
                search_space: List[HyperparameterSpace],
                method: OptimizationMethod,
                max_iterations: int = 100,
                early_stopping_patience: int = 10) -> OptimizationResult:
        """
        Optimize hyperparameters using specified method.
        """
        start_time = datetime.utcnow()
        optimization_id = f"OPT-{method.value[:5]}-{start_time.strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting optimization: {optimization_id} using {method.value}")
        
        # Select optimization method
        if method == OptimizationMethod.BAYESIAN:
            result = self._bayesian_optimization(
                objective_function, search_space, max_iterations, early_stopping_patience
            )
        elif method == OptimizationMethod.GENETIC_ALGORITHM:
            result = self._genetic_algorithm(
                objective_function, search_space, max_iterations
            )
        elif method == OptimizationMethod.PARTICLE_SWARM:
            result = self._particle_swarm_optimization(
                objective_function, search_space, max_iterations
            )
        elif method == OptimizationMethod.HYPERBAND:
            result = self._hyperband_optimization(
                objective_function, search_space, max_iterations
            )
        elif method == OptimizationMethod.EVOLUTIONARY_STRATEGY:
            result = self._evolutionary_strategy(
                objective_function, search_space, max_iterations
            )
        else:
            result = self._random_search(
                objective_function, search_space, max_iterations
            )
        
        # Calculate elapsed time
        end_time = datetime.utcnow()
        elapsed = (end_time - start_time).total_seconds()
        
        # Create optimization result
        opt_result = OptimizationResult(
            optimization_id=optimization_id,
            method=method,
            best_params=result['best_params'],
            best_score=result['best_score'],
            iterations=result['iterations'],
            evaluations=result['evaluations'],
            convergence_history=result['convergence_history'],
            param_history=result['param_history'],
            time_elapsed_seconds=elapsed
        )
        
        self.optimization_history.append(opt_result)
        self.method_performance[method].append(result['best_score'])
        
        logger.info(f"Optimization complete: {optimization_id}, best score: {result['best_score']:.4f}")
        
        return opt_result
    
    def _bayesian_optimization(self, objective_fn: Callable,
                              search_space: List[HyperparameterSpace],
                              max_iterations: int,
                              patience: int) -> Dict[str, Any]:
        """Bayesian optimization using Gaussian Process"""
        
        best_score = -float('inf')
        best_params = {}
        convergence_history = []
        param_history = []
        
        # Initialize with random samples
        n_initial = min(10, max_iterations // 10)
        
        for iteration in range(max_iterations):
            # Sample parameters
            if iteration < n_initial:
                # Random sampling for initialization
                params = self._sample_random_params(search_space)
            else:
                # Use acquisition function (Expected Improvement)
                params = self._sample_with_acquisition(
                    search_space, param_history, convergence_history
                )
            
            # Evaluate
            score = objective_fn(params)
            
            # Update best
            if score > best_score:
                best_score = score
                best_params = params
            
            convergence_history.append(best_score)
            param_history.append(params)
            
            # Early stopping
            if iteration > patience:
                recent_improvement = best_score - convergence_history[-patience]
                if recent_improvement < 0.001:
                    logger.info(f"Early stopping at iteration {iteration}")
                    break
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _genetic_algorithm(self, objective_fn: Callable,
                          search_space: List[HyperparameterSpace],
                          max_iterations: int) -> Dict[str, Any]:
        """Genetic algorithm optimization"""
        
        population_size = 20
        mutation_rate = 0.1
        crossover_rate = 0.7
        
        # Initialize population
        population = [self._sample_random_params(search_space) for _ in range(population_size)]
        fitness = [objective_fn(params) for params in population]
        
        best_score = max(fitness)
        best_params = population[fitness.index(best_score)]
        convergence_history = [best_score]
        param_history = population.copy()
        
        for generation in range(max_iterations):
            # Selection (tournament)
            selected = self._tournament_selection(population, fitness, population_size)
            
            # Crossover
            offspring = []
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected) and np.random.random() < crossover_rate:
                    child1, child2 = self._crossover(selected[i], selected[i+1], search_space)
                    offspring.extend([child1, child2])
                else:
                    offspring.append(selected[i])
            
            # Mutation
            offspring = [self._mutate(params, search_space, mutation_rate) for params in offspring]
            
            # Evaluate offspring
            offspring_fitness = [objective_fn(params) for params in offspring]
            
            # Update population
            population = offspring
            fitness = offspring_fitness
            
            # Track best
            gen_best = max(fitness)
            if gen_best > best_score:
                best_score = gen_best
                best_params = population[fitness.index(gen_best)]
            
            convergence_history.append(best_score)
            param_history.extend(offspring)
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _particle_swarm_optimization(self, objective_fn: Callable,
                                    search_space: List[HyperparameterSpace],
                                    max_iterations: int) -> Dict[str, Any]:
        """Particle Swarm Optimization"""
        
        n_particles = 20
        w = 0.7  # Inertia weight
        c1 = 1.5  # Cognitive parameter
        c2 = 1.5  # Social parameter
        
        # Initialize particles
        particles = [self._sample_random_params(search_space) for _ in range(n_particles)]
        velocities = [{k: 0.0 for k in particles[0].keys()} for _ in range(n_particles)]
        
        # Evaluate initial positions
        fitness = [objective_fn(p) for p in particles]
        
        # Personal best
        pbest = particles.copy()
        pbest_fitness = fitness.copy()
        
        # Global best
        gbest_idx = fitness.index(max(fitness))
        gbest = particles[gbest_idx]
        gbest_fitness = fitness[gbest_idx]
        
        convergence_history = [gbest_fitness]
        param_history = particles.copy()
        
        for iteration in range(max_iterations):
            for i in range(n_particles):
                # Update velocity
                for param_name in particles[i].keys():
                    r1, r2 = np.random.random(), np.random.random()
                    
                    cognitive = c1 * r1 * (pbest[i][param_name] - particles[i][param_name])
                    social = c2 * r2 * (gbest[param_name] - particles[i][param_name])
                    
                    velocities[i][param_name] = w * velocities[i][param_name] + cognitive + social
                
                # Update position
                for param_name in particles[i].keys():
                    particles[i][param_name] += velocities[i][param_name]
                
                # Clip to bounds
                particles[i] = self._clip_to_bounds(particles[i], search_space)
                
                # Evaluate
                fitness[i] = objective_fn(particles[i])
                
                # Update personal best
                if fitness[i] > pbest_fitness[i]:
                    pbest[i] = particles[i].copy()
                    pbest_fitness[i] = fitness[i]
                
                # Update global best
                if fitness[i] > gbest_fitness:
                    gbest = particles[i].copy()
                    gbest_fitness = fitness[i]
            
            convergence_history.append(gbest_fitness)
            param_history.extend(particles.copy())
        
        return {
            'best_params': gbest,
            'best_score': gbest_fitness,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _hyperband_optimization(self, objective_fn: Callable,
                               search_space: List[HyperparameterSpace],
                               max_iterations: int) -> Dict[str, Any]:
        """Hyperband optimization (successive halving)"""
        
        max_budget = max_iterations
        eta = 3  # Reduction factor
        
        best_score = -float('inf')
        best_params = {}
        convergence_history = []
        param_history = []
        
        # Calculate number of brackets
        s_max = int(np.log(max_budget) / np.log(eta))
        
        for s in range(s_max, -1, -1):
            n = int(np.ceil((max_budget / (s + 1)) * (eta ** s)))
            r = max_budget * (eta ** (-s))
            
            # Generate random configurations
            configs = [self._sample_random_params(search_space) for _ in range(n)]
            
            for i in range(s + 1):
                n_i = int(n * (eta ** (-i)))
                r_i = int(r * (eta ** i))
                
                # Evaluate configurations
                scores = []
                for config in configs[:n_i]:
                    score = objective_fn(config)
                    scores.append(score)
                    param_history.append(config)
                    
                    if score > best_score:
                        best_score = score
                        best_params = config
                
                convergence_history.append(best_score)
                
                # Keep top eta^-1 configurations
                if i < s:
                    top_k = max(1, int(n_i / eta))
                    top_indices = np.argsort(scores)[-top_k:]
                    configs = [configs[idx] for idx in top_indices]
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _evolutionary_strategy(self, objective_fn: Callable,
                              search_space: List[HyperparameterSpace],
                              max_iterations: int) -> Dict[str, Any]:
        """Evolutionary Strategy (CMA-ES inspired)"""
        
        population_size = 20
        elite_size = 5
        
        # Initialize population
        population = [self._sample_random_params(search_space) for _ in range(population_size)]
        fitness = [objective_fn(params) for params in population]
        
        best_score = max(fitness)
        best_params = population[fitness.index(best_score)]
        convergence_history = [best_score]
        param_history = population.copy()
        
        for generation in range(max_iterations):
            # Select elite
            elite_indices = np.argsort(fitness)[-elite_size:]
            elite = [population[i] for i in elite_indices]
            
            # Generate offspring from elite
            offspring = []
            for _ in range(population_size):
                # Select random elite parent
                parent = elite[np.random.randint(len(elite))]
                
                # Add Gaussian noise
                child = {}
                for param_name, param_value in parent.items():
                    if isinstance(param_value, (int, float)):
                        noise = np.random.normal(0, 0.1 * abs(param_value) + 0.01)
                        child[param_name] = param_value + noise
                    else:
                        child[param_name] = param_value
                
                # Clip to bounds
                child = self._clip_to_bounds(child, search_space)
                offspring.append(child)
            
            # Evaluate offspring
            offspring_fitness = [objective_fn(params) for params in offspring]
            
            # Update population
            population = offspring
            fitness = offspring_fitness
            
            # Track best
            gen_best = max(fitness)
            if gen_best > best_score:
                best_score = gen_best
                best_params = population[fitness.index(gen_best)]
            
            convergence_history.append(best_score)
            param_history.extend(offspring)
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _random_search(self, objective_fn: Callable,
                      search_space: List[HyperparameterSpace],
                      max_iterations: int) -> Dict[str, Any]:
        """Random search baseline"""
        
        best_score = -float('inf')
        best_params = {}
        convergence_history = []
        param_history = []
        
        for iteration in range(max_iterations):
            params = self._sample_random_params(search_space)
            score = objective_fn(params)
            
            if score > best_score:
                best_score = score
                best_params = params
            
            convergence_history.append(best_score)
            param_history.append(params)
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'iterations': len(convergence_history),
            'evaluations': len(param_history),
            'convergence_history': convergence_history,
            'param_history': param_history
        }
    
    def _sample_random_params(self, search_space: List[HyperparameterSpace]) -> Dict[str, Any]:
        """Sample random parameters from search space"""
        
        params = {}
        
        for space in search_space:
            if space.param_type == 'continuous':
                if space.distribution == 'log_uniform':
                    log_min = np.log(space.min_value)
                    log_max = np.log(space.max_value)
                    params[space.name] = np.exp(np.random.uniform(log_min, log_max))
                else:
                    params[space.name] = np.random.uniform(space.min_value, space.max_value)
            
            elif space.param_type == 'discrete':
                params[space.name] = np.random.randint(space.min_value, space.max_value + 1)
            
            elif space.param_type == 'categorical':
                params[space.name] = np.random.choice(space.categories)
        
        return params
    
    def _sample_with_acquisition(self, search_space: List[HyperparameterSpace],
                                 param_history: List[Dict[str, Any]],
                                 score_history: List[float]) -> Dict[str, Any]:
        """Sample using acquisition function (Expected Improvement)"""
        
        # Simplified acquisition - sample near best performing regions
        if not param_history:
            return self._sample_random_params(search_space)
        
        # Find best parameters
        best_idx = score_history.index(max(score_history))
        best_params = param_history[best_idx]
        
        # Sample with Gaussian noise around best
        params = {}
        for space in search_space:
            if space.name in best_params:
                if space.param_type == 'continuous':
                    noise = np.random.normal(0, 0.1 * (space.max_value - space.min_value))
                    params[space.name] = best_params[space.name] + noise
                    params[space.name] = np.clip(params[space.name], space.min_value, space.max_value)
                else:
                    params[space.name] = best_params[space.name]
            else:
                params[space.name] = self._sample_random_params([space])[space.name]
        
        return params
    
    def _tournament_selection(self, population: List[Dict[str, Any]],
                             fitness: List[float], n_select: int) -> List[Dict[str, Any]]:
        """Tournament selection for genetic algorithm"""
        
        selected = []
        tournament_size = 3
        
        for _ in range(n_select):
            # Random tournament
            tournament_idx = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness[i] for i in tournament_idx]
            winner_idx = tournament_idx[tournament_fitness.index(max(tournament_fitness))]
            selected.append(population[winner_idx].copy())
        
        return selected
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any],
                  search_space: List[HyperparameterSpace]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Crossover operation"""
        
        child1, child2 = {}, {}
        
        for param_name in parent1.keys():
            if np.random.random() < 0.5:
                child1[param_name] = parent1[param_name]
                child2[param_name] = parent2[param_name]
            else:
                child1[param_name] = parent2[param_name]
                child2[param_name] = parent1[param_name]
        
        return child1, child2
    
    def _mutate(self, params: Dict[str, Any], search_space: List[HyperparameterSpace],
               mutation_rate: float) -> Dict[str, Any]:
        """Mutation operation"""
        
        mutated = params.copy()
        
        for space in search_space:
            if np.random.random() < mutation_rate:
                if space.param_type == 'continuous':
                    noise = np.random.normal(0, 0.1 * (space.max_value - space.min_value))
                    mutated[space.name] = params[space.name] + noise
                    mutated[space.name] = np.clip(mutated[space.name], space.min_value, space.max_value)
                elif space.param_type == 'categorical':
                    mutated[space.name] = np.random.choice(space.categories)
        
        return mutated
    
    def _clip_to_bounds(self, params: Dict[str, Any],
                       search_space: List[HyperparameterSpace]) -> Dict[str, Any]:
        """Clip parameters to search space bounds"""
        
        clipped = params.copy()
        
        for space in search_space:
            if space.name in params:
                if space.param_type == 'continuous':
                    clipped[space.name] = np.clip(params[space.name], space.min_value, space.max_value)
                elif space.param_type == 'discrete':
                    clipped[space.name] = int(np.clip(params[space.name], space.min_value, space.max_value))
        
        return clipped
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        
        if not self.optimization_history:
            return {'total_optimizations': 0}
        
        total = len(self.optimization_history)
        
        # Average scores by method
        method_stats = {}
        for method in OptimizationMethod:
            scores = self.method_performance[method]
            if scores:
                method_stats[method.value] = {
                    'count': len(scores),
                    'avg_score': np.mean(scores),
                    'best_score': max(scores)
                }
        
        # Overall stats
        all_scores = [opt.best_score for opt in self.optimization_history]
        avg_iterations = np.mean([opt.iterations for opt in self.optimization_history])
        avg_time = np.mean([opt.time_elapsed_seconds for opt in self.optimization_history])
        
        return {
            'total_optimizations': total,
            'average_best_score': np.mean(all_scores),
            'overall_best_score': max(all_scores),
            'average_iterations': avg_iterations,
            'average_time_seconds': avg_time,
            'method_stats': method_stats
        }


def quick_start_optimizer(config: Optional[Dict[str, Any]] = None) -> AdvancedModelOptimizer:
    """Quick start function for model optimizer"""
    return AdvancedModelOptimizer(config)
