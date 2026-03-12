"""
Autonomous Parameter Tuner
AI system that continuously tunes parameters in real-time
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Types of parameters"""
    CONTINUOUS = "continuous"  # e.g., 0.01 to 0.1
    DISCRETE = "discrete"      # e.g., [5, 10, 20, 50]
    CATEGORICAL = "categorical" # e.g., ['fast', 'medium', 'slow']


@dataclass
class Parameter:
    """Parameter definition"""
    name: str
    type: ParameterType
    current_value: any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    possible_values: Optional[List] = None
    learning_rate: float = 0.1
    exploration_rate: float = 0.2


class AutonomousTuner:
    """
    Autonomous parameter tuning using reinforcement learning
    """
    
    def __init__(self):
        try:
            self.parameters: Dict[str, Parameter] = {}
            self.performance_history = []
            self.q_table = {}  # Q-learning table
            self.learning_rate = 0.1
            self.discount_factor = 0.95
            self.exploration_rate = 0.2
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def register_parameter(self, param: Parameter):
        """Register a parameter for tuning"""
        try:
            self.parameters[param.name] = param
            logger.info(f"Registered parameter: {param.name}")
        except Exception as e:
            logger.error(f"Error in register_parameter: {e}")
            raise
    
    def get_state_key(self) -> str:
        """Get current state as key for Q-table"""
        # Use recent performance as state
        try:
            if len(self.performance_history) < 5:
                return "initial"
        
            recent = self.performance_history[-5:]
            avg_reward = np.mean(recent)
        
            if avg_reward > 0.7:
                return "high_performance"
            elif avg_reward > 0.4:
                return "medium_performance"
            else:
                return "low_performance"
        except Exception as e:
            logger.error(f"Error in get_state_key: {e}")
            raise
    
    def select_action(self, param_name: str) -> any:
        """Select action (parameter value) using epsilon-greedy"""
        try:
            param = self.parameters[param_name]
            state = self.get_state_key()
        
            # Exploration vs exploitation
            if np.random.random() < self.exploration_rate:
                # Explore: random action
                return self._random_action(param)
            else:
                # Exploit: best known action
                return self._best_action(param, state)
        except Exception as e:
            logger.error(f"Error in select_action: {e}")
            raise
    
    def _random_action(self, param: Parameter) -> any:
        """Generate random action"""
        try:
            if param.type == ParameterType.CONTINUOUS:
                return np.random.uniform(param.min_value, param.max_value)
            elif param.type == ParameterType.DISCRETE:
                return np.random.choice(param.possible_values)
            elif param.type == ParameterType.CATEGORICAL:
                return np.random.choice(param.possible_values)
        except Exception as e:
            logger.error(f"Error in _random_action: {e}")
            raise
    
    def _best_action(self, param: Parameter, state: str) -> any:
        """Get best known action from Q-table"""
        try:
            key = f"{param.name}_{state}"
        
            if key not in self.q_table:
                return param.current_value
        
            # Get action with highest Q-value
            best_action = max(self.q_table[key].items(), key=lambda x: x[1])[0]
            return best_action
        except Exception as e:
            logger.error(f"Error in _best_action: {e}")
            raise
    
    def update_q_value(self, param_name: str, action: any, 
                      reward: float, next_state: str):
        """Update Q-value using Q-learning"""
        try:
            state = self.get_state_key()
            key = f"{param_name}_{state}"
        
            # Initialize if needed
            if key not in self.q_table:
                self.q_table[key] = {}
        
            # Get current Q-value
            current_q = self.q_table[key].get(action, 0)
        
            # Get max Q-value for next state
            next_key = f"{param_name}_{next_state}"
            if next_key in self.q_table and self.q_table[next_key]:
                max_next_q = max(self.q_table[next_key].values())
            else:
                max_next_q = 0
        
            # Q-learning update
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * max_next_q - current_q
            )
        
            self.q_table[key][action] = new_q
        except Exception as e:
            logger.error(f"Error in update_q_value: {e}")
            raise
    
    def tune_parameter(self, param_name: str, performance: float) -> any:
        """Tune a single parameter"""
        try:
            if param_name not in self.parameters:
                logger.error(f"Parameter {param_name} not registered")
                return None
        
            param = self.parameters[param_name]
        
            # Select new value
            new_value = self.select_action(param_name)
        
            # Calculate reward (performance improvement)
            if self.performance_history:
                baseline = np.mean(self.performance_history[-10:])
                reward = (performance - baseline) / max(abs(baseline), 0.01)
            else:
                reward = performance
        
            # Update Q-value
            self.update_q_value(param_name, new_value, reward, self.get_state_key())
        
            # Update parameter
            param.current_value = new_value
        
            # Track performance
            self.performance_history.append(performance)
        
            logger.info(f"Tuned {param_name}: {new_value} (reward: {reward:.3f})")
        
            return new_value
        except Exception as e:
            logger.error(f"Error in tune_parameter: {e}")
            raise
    
    def tune_all_parameters(self, performance: float) -> Dict[str, any]:
        """Tune all registered parameters"""
        try:
            results = {}
        
            for param_name in self.parameters:
                new_value = self.tune_parameter(param_name, performance)
                results[param_name] = new_value
        
            return results
        except Exception as e:
            logger.error(f"Error in tune_all_parameters: {e}")
            raise
    
    def get_tuning_summary(self) -> Dict:
        """Get summary of tuning process"""
        return {
            'total_parameters': len(self.parameters),
            'total_updates': len(self.performance_history),
            'avg_performance': np.mean(self.performance_history) if self.performance_history else 0,
            'exploration_rate': self.exploration_rate,
            'parameters': {
                name: {
                    'current_value': param.current_value,
                    'type': param.type.value
                }
                for name, param in self.parameters.items()
            }
        }


class GeneticOptimizer:
    """
    Genetic algorithm for parameter optimization
    """
    
    def __init__(self, population_size: int = 50):
        try:
            self.population_size = population_size
            self.population = []
            self.fitness_scores = []
            self.generation = 0
            self.best_individual = None
            self.best_fitness = -np.inf
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize_population(self, param_ranges: Dict[str, Tuple[float, float]]):
        """Initialize random population"""
        try:
            self.population = []
        
            for _ in range(self.population_size):
                individual = {
                    param: np.random.uniform(min_val, max_val)
                    for param, (min_val, max_val) in param_ranges.items()
                }
                self.population.append(individual)
        except Exception as e:
            logger.error(f"Error in initialize_population: {e}")
            raise
    
    def evaluate_fitness(self, individual: Dict, 
                        fitness_function) -> float:
        """Evaluate fitness of individual"""
        return fitness_function(individual)
    
    def select_parents(self) -> Tuple[Dict, Dict]:
        """Select two parents using tournament selection"""
        tournament_size = 5
        
        def tournament():
            """
            tournament function.

    Auto-documented by QwenCodeMender.
            """
            try:
                candidates = np.random.choice(
                    len(self.population), 
                    tournament_size, 
                    replace=False
                )
                best_idx = max(candidates, key=lambda i: self.fitness_scores[i])
                return self.population[best_idx]
            except Exception as e:
                logger.error(f"Error in tournament: {e}")
                raise
        
        return tournament(), tournament()
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Create offspring through crossover"""
        try:
            offspring = {}
        
            for param in parent1.keys():
                # Blend crossover
                alpha = np.random.random()
                offspring[param] = alpha * parent1[param] + (1 - alpha) * parent2[param]
        
            return offspring
        except Exception as e:
            logger.error(f"Error in crossover: {e}")
            raise
    
    def mutate(self, individual: Dict, mutation_rate: float = 0.1) -> Dict:
        """Mutate individual"""
        try:
            mutated = individual.copy()
        
            for param in mutated.keys():
                if np.random.random() < mutation_rate:
                    # Gaussian mutation
                    mutated[param] += np.random.randn() * 0.1 * mutated[param]
        
            return mutated
        except Exception as e:
            logger.error(f"Error in mutate: {e}")
            raise
    
    def evolve(self, fitness_function, generations: int = 100) -> Dict:
        """Run genetic algorithm"""
        try:
            for gen in range(generations):
                # Evaluate fitness
                self.fitness_scores = [
                    self.evaluate_fitness(ind, fitness_function)
                    for ind in self.population
                ]
            
                # Track best
                best_idx = np.argmax(self.fitness_scores)
                if self.fitness_scores[best_idx] > self.best_fitness:
                    self.best_fitness = self.fitness_scores[best_idx]
                    self.best_individual = self.population[best_idx].copy()
            
                # Create new population
                new_population = []
            
                # Elitism: keep best 10%
                elite_count = int(0.1 * self.population_size)
                elite_indices = np.argsort(self.fitness_scores)[-elite_count:]
                new_population.extend([self.population[i] for i in elite_indices])
            
                # Generate offspring
                while len(new_population) < self.population_size:
                    parent1, parent2 = self.select_parents()
                    offspring = self.crossover(parent1, parent2)
                    offspring = self.mutate(offspring)
                    new_population.append(offspring)
            
                self.population = new_population
                self.generation = gen
            
                if gen % 10 == 0:
                    logger.info(f"Generation {gen}: Best fitness = {self.best_fitness:.4f}")
        
            return self.best_individual
        except Exception as e:
            logger.error(f"Error in evolve: {e}")
            raise


class BayesianOptimizer:
    """
    Bayesian optimization for parameter tuning
    """
    
    def __init__(self):
        try:
            self.observations = []
            self.param_history = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def suggest_parameters(self, param_ranges: Dict[str, Tuple[float, float]],
                          n_suggestions: int = 1) -> List[Dict]:
        """Suggest next parameters to try using Bayesian optimization"""
        
        try:
            if len(self.observations) < 5:
                # Random exploration initially
                return [
                    {
                        param: np.random.uniform(min_val, max_val)
                        for param, (min_val, max_val) in param_ranges.items()
                    }
                    for _ in range(n_suggestions)
                ]
        
            # Use Gaussian Process (simplified)
            # In production, use libraries like scikit-optimize
            suggestions = []
        
            for _ in range(n_suggestions):
                # Expected Improvement acquisition function
                best_params = self.param_history[np.argmax(self.observations)]
            
                # Add some exploration noise
                suggested = {
                    param: best_params[param] + np.random.randn() * 0.1 * (max_val - min_val)
                    for param, (min_val, max_val) in param_ranges.items()
                }
            
                # Clip to bounds
                suggested = {
                    param: np.clip(val, *param_ranges[param])
                    for param, val in suggested.items()
                }
            
                suggestions.append(suggested)
        
            return suggestions
        except Exception as e:
            logger.error(f"Error in suggest_parameters: {e}")
            raise
    
    def update(self, parameters: Dict, performance: float):
        """Update with new observation"""
        try:
            self.param_history.append(parameters)
            self.observations.append(performance)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_best_parameters(self) -> Dict:
        """Get best parameters found so far"""
        try:
            if not self.observations:
                return {}
        
            best_idx = np.argmax(self.observations)
            return self.param_history[best_idx]
        except Exception as e:
            logger.error(f"Error in get_best_parameters: {e}")
            raise


# Example usage
if __name__ == '__main__':
    print("="*80)
    print("AUTONOMOUS PARAMETER TUNING DEMO".center(80))
    print("="*80)
    
    # Create tuner
    tuner = AutonomousTuner()
    
    # Register parameters
    tuner.register_parameter(Parameter(
        name='risk_per_trade',
        type=ParameterType.CONTINUOUS,
        current_value=0.01,
        min_value=0.005,
        max_value=0.05
    ))
    
    tuner.register_parameter(Parameter(
        name='stop_loss_pips',
        type=ParameterType.DISCRETE,
        current_value=20,
        possible_values=[10, 15, 20, 25, 30]
    ))
    
    # Simulate tuning
    logger.info("\nSimulating parameter tuning...")
    for i in range(50):
        # Simulate performance
        performance = 0.5 + np.random.randn() * 0.2
        
        # Tune parameters
        results = tuner.tune_all_parameters(performance)
        
        if i % 10 == 0:
            logger.info(f"\nIteration {i}:")
            logger.info(f"  Performance: {performance:.3f}")
            logger.info(f"  Parameters: {results}")
    
    # Get summary
    summary = tuner.get_tuning_summary()
    print("\n" + "="*80)
    print("TUNING SUMMARY".center(80))
    print("="*80)
    import json
    print(json.dumps(summary, indent=2, default=str))
