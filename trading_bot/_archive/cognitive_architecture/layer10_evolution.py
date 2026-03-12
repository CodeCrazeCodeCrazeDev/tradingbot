"""
Layer 10: Continuous Evolution Engine
Autonomous improvement and strategy evolution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class EvolutionCycle:
    """Record of an evolution cycle."""
    cycle_id: int
    timestamp: datetime
    changes_made: List[str]
    performance_before: float
    performance_after: float
    success: bool


@dataclass
class Strategy:
    """Represents a trading strategy."""
    name: str
    parameters: Dict[str, float]
    performance: float = 0.0
    trades: int = 0
    active: bool = True


class ContinuousEvolutionEngine:
    """
    Continuous Evolution Engine - Layer 10 of Cognitive Architecture.
    Manages autonomous improvement of the trading system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.evolution_cycles: List[EvolutionCycle] = []
        self.current_cycle = 0
        self.learning_rate = config.get('learning_rate', 0.01) if config else 0.01
        self.mutation_rate = config.get('mutation_rate', 0.1) if config else 0.1
        logger.info("ContinuousEvolutionEngine initialized")
    
    def evolve(self, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Run an evolution cycle."""
        self.current_cycle += 1
        changes = []
        
        # Analyze performance
        current_performance = self._calculate_fitness(performance_metrics)
        
        # Determine what to evolve
        if performance_metrics.get('win_rate', 0.5) < 0.45:
            changes.append('adjust_entry_criteria')
        
        if performance_metrics.get('profit_factor', 1.0) < 1.2:
            changes.append('optimize_exit_strategy')
        
        if performance_metrics.get('max_drawdown', 0) > 0.15:
            changes.append('tighten_risk_controls')
        
        # Record cycle
        cycle = EvolutionCycle(
            cycle_id=self.current_cycle,
            timestamp=datetime.now(),
            changes_made=changes,
            performance_before=current_performance,
            performance_after=current_performance,  # Updated after changes applied
            success=len(changes) > 0
        )
        self.evolution_cycles.append(cycle)
        
        return {
            'cycle': self.current_cycle,
            'changes': changes,
            'performance': current_performance
        }
    
    def _calculate_fitness(self, metrics: Dict[str, float]) -> float:
        """Calculate fitness score from metrics."""
        weights = {
            'win_rate': 0.2,
            'profit_factor': 0.3,
            'sharpe_ratio': 0.3,
            'max_drawdown': 0.2
        }
        
        fitness = 0.0
        for metric, weight in weights.items():
            value = metrics.get(metric, 0.5)
            if metric == 'max_drawdown':
                # Lower drawdown is better
                normalized = 1.0 - min(value, 1.0)
            else:
                normalized = min(value, 2.0) / 2.0  # Normalize to 0-1
            fitness += normalized * weight
        
        return fitness
    
    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """Get history of evolution cycles."""
        return [
            {
                'cycle': c.cycle_id,
                'timestamp': c.timestamp.isoformat(),
                'changes': c.changes_made,
                'performance_change': c.performance_after - c.performance_before,
                'success': c.success
            }
            for c in self.evolution_cycles
        ]


class StrategyEvolver:
    """
    Evolves trading strategies using genetic algorithms.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.population: List[Strategy] = []
        self.generation = 0
        self.population_size = config.get('population_size', 20) if config else 20
        self.elite_count = config.get('elite_count', 2) if config else 2
        logger.info("StrategyEvolver initialized")
    
    def initialize_population(self, base_parameters: Dict[str, Tuple[float, float]]):
        """Initialize population with random strategies."""
        self.population = []
        
        for i in range(self.population_size):
            params = {}
            for param_name, (min_val, max_val) in base_parameters.items():
                params[param_name] = np.random.uniform(min_val, max_val)
            
            self.population.append(Strategy(
                name=f"strategy_{i}",
                parameters=params
            ))
        
        logger.info(f"Initialized population with {len(self.population)} strategies")
    
    def evaluate_population(self, evaluation_func) -> List[float]:
        """Evaluate all strategies in population."""
        scores = []
        for strategy in self.population:
            score = evaluation_func(strategy.parameters)
            strategy.performance = score
            scores.append(score)
        return scores
    
    def evolve_generation(self) -> List[Strategy]:
        """Evolve to next generation."""
        self.generation += 1
        
        # Sort by performance
        sorted_pop = sorted(self.population, key=lambda s: s.performance, reverse=True)
        
        # Keep elite
        new_population = sorted_pop[:self.elite_count]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_select(sorted_pop)
            parent2 = self._tournament_select(sorted_pop)
            
            # Crossover
            child_params = self._crossover(parent1.parameters, parent2.parameters)
            
            # Mutation
            child_params = self._mutate(child_params)
            
            new_population.append(Strategy(
                name=f"strategy_gen{self.generation}_{len(new_population)}",
                parameters=child_params
            ))
        
        self.population = new_population
        return self.population
    
    def _tournament_select(self, population: List[Strategy], 
                          tournament_size: int = 3) -> Strategy:
        """Select strategy using tournament selection."""
        tournament = np.random.choice(population, size=min(tournament_size, len(population)), replace=False)
        return max(tournament, key=lambda s: s.performance)
    
    def _crossover(self, params1: Dict[str, float], 
                   params2: Dict[str, float]) -> Dict[str, float]:
        """Crossover two parameter sets."""
        child = {}
        for key in params1:
            if np.random.random() < 0.5:
                child[key] = params1[key]
            else:
                child[key] = params2[key]
        return child
    
    def _mutate(self, params: Dict[str, float], 
                mutation_rate: float = 0.1) -> Dict[str, float]:
        """Mutate parameters."""
        mutated = params.copy()
        for key in mutated:
            if np.random.random() < mutation_rate:
                # Add Gaussian noise
                mutated[key] *= (1 + np.random.normal(0, 0.1))
        return mutated
    
    def get_best_strategy(self) -> Optional[Strategy]:
        """Get best performing strategy."""
        if not self.population:
            return None
        return max(self.population, key=lambda s: s.performance)


class ArchitectureRebalancer:
    """
    Rebalances system architecture based on performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.component_weights: Dict[str, float] = {
            'technical_analysis': 0.25,
            'sentiment_analysis': 0.15,
            'ml_predictions': 0.25,
            'risk_management': 0.20,
            'execution': 0.15
        }
        self.performance_history: Dict[str, List[float]] = {k: [] for k in self.component_weights}
        logger.info("ArchitectureRebalancer initialized")
    
    def record_performance(self, component: str, performance: float):
        """Record component performance."""
        if component in self.performance_history:
            self.performance_history[component].append(performance)
            # Keep bounded
            if len(self.performance_history[component]) > 100:
                self.performance_history[component] = self.performance_history[component][-100:]
    
    def rebalance(self) -> Dict[str, float]:
        """Rebalance component weights based on performance."""
        # Calculate average performance for each component
        avg_performance = {}
        for component, history in self.performance_history.items():
            if history:
                avg_performance[component] = np.mean(history)
            else:
                avg_performance[component] = 0.5
        
        # Adjust weights based on performance
        total_perf = sum(avg_performance.values())
        if total_perf > 0:
            for component in self.component_weights:
                # Blend current weight with performance-based weight
                perf_weight = avg_performance.get(component, 0.5) / total_perf
                current_weight = self.component_weights[component]
                # Slow adjustment
                self.component_weights[component] = 0.9 * current_weight + 0.1 * perf_weight
        
        # Normalize weights
        total_weight = sum(self.component_weights.values())
        if total_weight > 0:
            self.component_weights = {k: v / total_weight for k, v in self.component_weights.items()}
        
        logger.debug(f"Rebalanced weights: {self.component_weights}")
        return self.component_weights
    
    def get_component_weight(self, component: str) -> float:
        """Get weight for a component."""
        return self.component_weights.get(component, 0.1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get rebalancer status."""
        return {
            'weights': self.component_weights,
            'performance_samples': {k: len(v) for k, v in self.performance_history.items()}
        }
