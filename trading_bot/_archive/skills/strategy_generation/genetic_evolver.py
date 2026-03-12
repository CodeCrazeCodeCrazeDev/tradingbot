"""
Skill #61: Genetic Strategy Evolver
===================================

Evolves trading strategies using genetic algorithms.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """Trading strategy genome."""
    genes: np.ndarray
    fitness: float
    generation: int


@dataclass
class GeneticResult:
    """Genetic evolution result."""
    best_strategy: Strategy
    population_fitness: List[float]
    generations_evolved: int
    convergence_rate: float
    trading_signal: str


class GeneticStrategyEvolver:
    """Evolves strategies using genetic algorithms."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.population_size = self.config.get('population_size', 50)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        logger.info("GeneticStrategyEvolver initialized")
    
    def evolve(self, prices: np.ndarray, generations: int = 50) -> GeneticResult:
        """Evolve strategies on price data."""
        if len(prices) < 50:
            return self._create_empty_result()
        
        # Initialize population
        population = [Strategy(np.random.randn(10), 0, 0) for _ in range(self.population_size)]
        
        fitness_history = []
        for gen in range(generations):
            # Evaluate fitness
            for s in population:
                s.fitness = self._evaluate_fitness(s, prices)
                s.generation = gen
            
            fitness_history.append(max(s.fitness for s in population))
            
            # Selection and reproduction
            population = self._evolve_generation(population)
        
        best = max(population, key=lambda s: s.fitness)
        convergence = (fitness_history[-1] - fitness_history[0]) / (generations + 1e-10)
        
        signal = self._generate_signal(best, convergence)
        
        return GeneticResult(
            best_strategy=best, population_fitness=fitness_history,
            generations_evolved=generations, convergence_rate=convergence,
            trading_signal=signal
        )
    
    def _evaluate_fitness(self, strategy: Strategy, prices: np.ndarray) -> float:
        """Evaluate strategy fitness."""
        returns = np.diff(prices) / prices[:-1]
        signals = np.tanh(np.convolve(returns[-50:], strategy.genes[:min(10, len(returns))], mode='same'))
        pnl = np.sum(signals[:-1] * returns[-len(signals)+1:])
        sharpe = pnl / (np.std(returns) + 1e-10)
        return sharpe
    
    def _evolve_generation(self, population: List[Strategy]) -> List[Strategy]:
        """Evolve to next generation."""
        # Sort by fitness
        population.sort(key=lambda s: s.fitness, reverse=True)
        
        # Keep top 20%
        elite = population[:self.population_size // 5]
        
        # Breed rest
        new_pop = elite.copy()
        while len(new_pop) < self.population_size:
            p1, p2 = np.random.choice(elite, 2, replace=False)
            child_genes = self._crossover(p1.genes, p2.genes)
            child_genes = self._mutate(child_genes)
            new_pop.append(Strategy(child_genes, 0, 0))
        
        return new_pop
    
    def _crossover(self, g1: np.ndarray, g2: np.ndarray) -> np.ndarray:
        """Crossover two genomes."""
        if np.random.random() < self.crossover_rate:
            point = np.random.randint(1, len(g1))
            return np.concatenate([g1[:point], g2[point:]])
        return g1.copy()
    
    def _mutate(self, genes: np.ndarray) -> np.ndarray:
        """Mutate genome."""
        mask = np.random.random(len(genes)) < self.mutation_rate
        genes[mask] += np.random.randn(np.sum(mask)) * 0.1
        return genes
    
    def _generate_signal(self, best: Strategy, conv: float) -> str:
        return f"EVOLVED: Fitness {best.fitness:.3f}, convergence {conv:.4f}"
    
    def _create_empty_result(self) -> GeneticResult:
        return GeneticResult(Strategy(np.array([]), 0, 0), [], 0, 0, "Insufficient data")
