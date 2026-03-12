"""
Phase 5: Meta-Learning - Evolutionary Strategy Optimization
Evolves trading strategies through genetic algorithms
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from copy import deepcopy
import random

logger = logging.getLogger(__name__)


class TradingStrategy:
    """Base class for evolvable trading strategies."""
    
    def __init__(self, input_dim: int = 20, hidden_dim: int = 64):
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 3)  # BUY, SELL, HOLD
        )
        
        self.fitness = 0.0
        self.age = 0
        self.mutation_rate = 0.1
        self.generation = 0
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through strategy network."""
        return self.network(x)
    
    def mutate(self):
        """Apply random mutations to network weights."""
        with torch.no_grad():
            for param in self.network.parameters():
                # Random noise based on mutation rate
                noise = torch.randn_like(param) * self.mutation_rate
                param.add_(noise)
    
    def crossover(self, other: 'TradingStrategy') -> 'TradingStrategy':
        """Create child strategy through crossover."""
        child = TradingStrategy()
        
        # Inherit parameters from both parents
        with torch.no_grad():
            for child_param, self_param, other_param in zip(
                child.network.parameters(),
                self.network.parameters(),
                other.network.parameters()
            ):
                # Random mixing of parameters
                mask = torch.rand_like(child_param) > 0.5
                child_param.data = (
                    torch.where(mask, self_param.data, other_param.data)
                )
        
        # Inherit some properties
        child.mutation_rate = (
            self.mutation_rate + other.mutation_rate
        ) / 2
        child.generation = max(self.generation, other.generation) + 1
        
        return child
    
    def to_dict(self) -> Dict:
        """Convert strategy to dictionary."""
        return {
            'weights': {
                name: param.data.clone()
                for name, param in self.network.named_parameters()
            },
            'fitness': self.fitness,
            'age': self.age,
            'mutation_rate': self.mutation_rate,
            'generation': self.generation
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradingStrategy':
        """Create strategy from dictionary."""
        strategy = cls()
        
        # Load weights
        with torch.no_grad():
            for name, param in strategy.network.named_parameters():
                param.data = data['weights'][name].clone()
        
        strategy.fitness = data['fitness']
        strategy.age = data['age']
        strategy.mutation_rate = data['mutation_rate']
        strategy.generation = data['generation']
        
        return strategy


class EvolutionaryOptimizer:
    """
    Evolves population of trading strategies.
    Uses genetic algorithms for optimization.
    """
    
    def __init__(
        self,
        population_size: int = 100,
        elite_size: int = 10,
        mutation_rate: float = 0.1
    ):
        self.population_size = population_size
        self.elite_size = elite_size
        self.base_mutation_rate = mutation_rate
        
        # Initialize population
        self.population = [
            TradingStrategy() for _ in range(population_size)
        ]
        
        # Evolution history
        self.generation = 0
        self.history = []
        
        logger.info("✅ Evolutionary Optimizer initialized")
        logger.info(f"   Population size: {population_size}")
        logger.info(f"   Elite size: {elite_size}")
        logger.info(f"   Base mutation rate: {mutation_rate}")
    
    def evolve(
        self,
        fitness_fn,
        num_generations: int = 100,
        target_fitness: Optional[float] = None
    ):
        """
        Evolve population for specified generations.
        
        Args:
            fitness_fn: Function to evaluate strategy fitness
            num_generations: Number of generations to evolve
            target_fitness: Optional target fitness to reach
        """
        logger.info(f"🧬 Starting evolution for {num_generations} generations")
        
        for gen in range(num_generations):
            self.generation += 1
            
            # Evaluate fitness
            self._evaluate_population(fitness_fn)
            
            # Sort by fitness
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            
            # Record statistics
            stats = self._get_generation_stats()
            self.history.append(stats)
            
            logger.info(f"\nGeneration {self.generation}:")
            logger.info(f"Best fitness: {stats['best_fitness']:.4f}")
            logger.info(f"Avg fitness: {stats['avg_fitness']:.4f}")
            logger.info(f"Diversity: {stats['diversity']:.4f}")
            
            # Check if target reached
            if (target_fitness is not None and 
                stats['best_fitness'] >= target_fitness):
                logger.info(f"🎯 Target fitness {target_fitness} reached!")
                break
            
            # Create next generation
            self._create_next_generation()
    
    def _evaluate_population(self, fitness_fn):
        """Evaluate fitness of all strategies."""
        for strategy in self.population:
            strategy.fitness = fitness_fn(strategy)
            strategy.age += 1
    
    def _create_next_generation(self):
        """Create next generation through selection and reproduction."""
        next_gen = []
        
        # Keep elite strategies
        elite = self.population[:self.elite_size]
        next_gen.extend(deepcopy(elite))
        
        # Fill rest through tournament selection and crossover
        while len(next_gen) < self.population_size:
            parent1 = self._tournament_select()
            parent2 = self._tournament_select()
            
            child = parent1.crossover(parent2)
            
            # Mutation
            if random.random() < self.base_mutation_rate:
                child.mutate()
            
            next_gen.append(child)
        
        self.population = next_gen
    
    def _tournament_select(self, tournament_size: int = 5) -> TradingStrategy:
        """Select strategy through tournament selection."""
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda x: x.fitness)
    
    def _get_generation_stats(self) -> Dict:
        """Calculate statistics for current generation."""
        fitnesses = [s.fitness for s in self.population]
        
        # Calculate diversity through parameter variance
        param_vectors = []
        for strategy in self.population:
            params = []
            for param in strategy.network.parameters():
                params.extend(param.data.flatten().tolist())
            param_vectors.append(params)
        
        param_vectors = np.array(param_vectors)
        diversity = np.mean(np.std(param_vectors, axis=0))
        
        return {
            'generation': self.generation,
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'worst_fitness': min(fitnesses),
            'diversity': float(diversity),
            'population_size': len(self.population)
        }
    
    def get_best_strategy(self) -> TradingStrategy:
        """Get best strategy from current population."""
        return max(self.population, key=lambda x: x.fitness)
    
    def get_evolution_summary(self) -> Dict:
        """Get summary of evolution progress."""
        if not self.history:
            return {}
        
        return {
            'generations': self.generation,
            'best_fitness_ever': max(h['best_fitness'] for h in self.history),
            'current_best_fitness': self.history[-1]['best_fitness'],
            'avg_fitness_history': [h['avg_fitness'] for h in self.history],
            'diversity_history': [h['diversity'] for h in self.history],
            'latest_improvement': self._get_latest_improvement()
        }
    
    def _get_latest_improvement(self) -> int:
        """Get number of generations since last improvement."""
        if len(self.history) < 2:
            return 0
        
        best_fitness = self.history[0]['best_fitness']
        last_improvement = 0
        
        for i, stats in enumerate(self.history[1:], 1):
            if stats['best_fitness'] > best_fitness:
                best_fitness = stats['best_fitness']
                last_improvement = i
        
        return self.generation - last_improvement
    
    def save_population(self, filepath: str):
        """Save current population."""
        state = {
            'population': [s.to_dict() for s in self.population],
            'generation': self.generation,
            'history': self.history
        }
        torch.save(state, filepath)
        logger.info(f"💾 Population saved to {filepath}")
    
    def load_population(self, filepath: str):
        """Load saved population."""
        state = torch.load(filepath)
        
        self.population = [
            TradingStrategy.from_dict(data)
            for data in state['population']
        ]
        self.generation = state['generation']
        self.history = state['history']
        
        logger.info(f"📂 Population loaded from {filepath}")
        logger.info(f"   Generation: {self.generation}")
        logger.info(f"   Population size: {len(self.population)}")


class EvolutionaryStrategyOptimizer:
    """
    Natural Evolution Strategies (NES) optimizer.
    Uses gradient-based evolution for faster optimization.
    """
    
    def __init__(
        self,
        strategy: TradingStrategy,
        population_size: int = 50,
        learning_rate: float = 0.01,
        sigma: float = 0.1
    ):
        self.strategy = strategy
        self.population_size = population_size
        self.learning_rate = learning_rate
        self.sigma = sigma
        
        self.generation = 0
        self.history = []
        
        logger.info("✅ NES Optimizer initialized")
        logger.info(f"   Population size: {population_size}")
        logger.info(f"   Learning rate: {learning_rate}")
        logger.info(f"   Sigma: {sigma}")
    
    def optimize(
        self,
        fitness_fn,
        num_generations: int = 100,
        target_fitness: Optional[float] = None
    ):
        """
        Optimize strategy using NES.
        
        Args:
            fitness_fn: Function to evaluate strategy fitness
            num_generations: Number of generations
            target_fitness: Optional target fitness
        """
        logger.info(f"🧬 Starting NES optimization for {num_generations} generations")
        
        for gen in range(num_generations):
            self.generation += 1
            
            # Generate perturbations
            epsilons = [
                torch.randn_like(param)
                for param in self.strategy.network.parameters()
            ]
            
            # Evaluate perturbed strategies
            rewards = []
            for eps in epsilons:
                # Create perturbed strategy
                perturbed = deepcopy(self.strategy)
                with torch.no_grad():
                    for param, e in zip(perturbed.network.parameters(), eps):
                        param.add_(self.sigma * e)
                
                # Evaluate
                fitness = fitness_fn(perturbed)
                rewards.append(fitness)
            
            # Convert to numpy array
            rewards = np.array(rewards)
            
            # Normalize rewards
            rewards = (rewards - np.mean(rewards)) / (np.std(rewards) + 1e-8)
            
            # Update strategy parameters
            with torch.no_grad():
                for param, eps in zip(
                    self.strategy.network.parameters(),
                    epsilons
                ):
                    # Gradient estimate
                    grad = np.mean([
                        r * e for r, e in zip(rewards, eps)
                    ], axis=0)
                    
                    # Update
                    param.add_(self.learning_rate * grad)
            
            # Record statistics
            stats = {
                'generation': self.generation,
                'best_fitness': np.max(rewards),
                'avg_fitness': np.mean(rewards),
                'worst_fitness': np.min(rewards)
            }
            self.history.append(stats)
            
            logger.info(f"\nGeneration {self.generation}:")
            logger.info(f"Best fitness: {stats['best_fitness']:.4f}")
            logger.info(f"Avg fitness: {stats['avg_fitness']:.4f}")
            
            # Check if target reached
            if (target_fitness is not None and 
                stats['best_fitness'] >= target_fitness):
                logger.info(f"🎯 Target fitness {target_fitness} reached!")
                break
    
    def get_optimization_summary(self) -> Dict:
        """Get summary of optimization progress."""
        if not self.history:
            return {}
        
        return {
            'generations': self.generation,
            'best_fitness_ever': max(h['best_fitness'] for h in self.history),
            'current_best_fitness': self.history[-1]['best_fitness'],
            'avg_fitness_history': [h['avg_fitness'] for h in self.history],
            'latest_improvement': self._get_latest_improvement()
        }
    
    def _get_latest_improvement(self) -> int:
        """Get number of generations since last improvement."""
        if len(self.history) < 2:
            return 0
        
        best_fitness = self.history[0]['best_fitness']
        last_improvement = 0
        
        for i, stats in enumerate(self.history[1:], 1):
            if stats['best_fitness'] > best_fitness:
                best_fitness = stats['best_fitness']
                last_improvement = i
        
        return self.generation - last_improvement
    
    def save_state(self, filepath: str):
        """Save optimizer state."""
        state = {
            'strategy': self.strategy.to_dict(),
            'generation': self.generation,
            'history': self.history,
            'hyperparameters': {
                'population_size': self.population_size,
                'learning_rate': self.learning_rate,
                'sigma': self.sigma
            }
        }
        torch.save(state, filepath)
        logger.info(f"💾 NES optimizer state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load optimizer state."""
        state = torch.load(filepath)
        
        self.strategy = TradingStrategy.from_dict(state['strategy'])
        self.generation = state['generation']
        self.history = state['history']
        
        # Load hyperparameters
        self.population_size = state['hyperparameters']['population_size']
        self.learning_rate = state['hyperparameters']['learning_rate']
        self.sigma = state['hyperparameters']['sigma']
        
        logger.info(f"📂 NES optimizer state loaded from {filepath}")
        logger.info(f"   Generation: {self.generation}")
