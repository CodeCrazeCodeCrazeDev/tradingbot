"""
Strategy Evolution System
==========================
Genetic algorithm-based strategy evolution where market selection pressure
determines which strategies survive.

Features:
- Strategy DNA and mutation
- Population management
- Concept drift detection
- Evolutionary selection
"""

import logging
import random
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import copy
import numpy

logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of strategy mutations"""
    PARAMETER_TWEAK = "parameter_tweak"
    RULE_ADDITION = "rule_addition"
    RULE_REMOVAL = "rule_removal"
    CROSSOVER = "crossover"
    RANDOM = "random"


@dataclass
class StrategyDNA:
    """
    Genetic representation of a trading strategy.
    
    Contains all the "genes" that define strategy behavior.
    """
    strategy_id: str
    name: str
    
    # Core parameters (genes)
    entry_threshold: float = 0.6
    exit_threshold: float = 0.4
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    position_size_pct: float = 0.01
    max_hold_time_hours: float = 24.0
    
    # Indicator parameters
    fast_period: int = 10
    slow_period: int = 20
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    
    # Rules (gene sequences)
    entry_rules: List[str] = field(default_factory=list)
    exit_rules: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    
    # Metadata
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Fitness (determined by market)
    fitness: float = 0.0
    trades: int = 0
    wins: int = 0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'entry_threshold': self.entry_threshold,
            'exit_threshold': self.exit_threshold,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'position_size_pct': self.position_size_pct,
            'max_hold_time_hours': self.max_hold_time_hours,
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'entry_rules': self.entry_rules,
            'exit_rules': self.exit_rules,
            'filters': self.filters,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'mutations': self.mutations,
            'fitness': self.fitness,
            'trades': self.trades,
            'wins': self.wins,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown
        }
    
    @property
    def win_rate(self) -> float:
        try:
            if self.trades == 0:
                return 0.0
            return self.wins / self.trades
        except Exception as e:
            logger.error(f"Error in win_rate: {e}")
            raise


class StrategyMutation:
    """
    Handles mutation of strategy DNA.
    
    Mutations introduce variation for evolution.
    """
    
    def __init__(self, mutation_rate: float = 0.2):
        try:
            self.mutation_rate = mutation_rate
            self.mutation_history: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def mutate(self, dna: StrategyDNA) -> StrategyDNA:
        """Apply random mutations to strategy DNA"""
        try:
            mutated = copy.deepcopy(dna)
            mutated.strategy_id = f"strat_{datetime.now().timestamp()}"
            mutated.generation += 1
            mutated.parent_ids = [dna.strategy_id]
            mutated.mutations = []
        
            # Parameter mutations
            if random.random() < self.mutation_rate:
                mutated.entry_threshold = self._mutate_float(dna.entry_threshold, 0.3, 0.9)
                mutated.mutations.append("entry_threshold")
        
            if random.random() < self.mutation_rate:
                mutated.exit_threshold = self._mutate_float(dna.exit_threshold, 0.2, 0.8)
                mutated.mutations.append("exit_threshold")
        
            if random.random() < self.mutation_rate:
                mutated.stop_loss_pct = self._mutate_float(dna.stop_loss_pct, 0.005, 0.05)
                mutated.mutations.append("stop_loss_pct")
        
            if random.random() < self.mutation_rate:
                mutated.take_profit_pct = self._mutate_float(dna.take_profit_pct, 0.01, 0.10)
                mutated.mutations.append("take_profit_pct")
        
            if random.random() < self.mutation_rate:
                mutated.fast_period = self._mutate_int(dna.fast_period, 5, 50)
                mutated.mutations.append("fast_period")
        
            if random.random() < self.mutation_rate:
                mutated.slow_period = self._mutate_int(dna.slow_period, 10, 100)
                mutated.mutations.append("slow_period")
        
            if random.random() < self.mutation_rate:
                mutated.rsi_period = self._mutate_int(dna.rsi_period, 7, 28)
                mutated.mutations.append("rsi_period")
        
            # Ensure slow > fast
            if mutated.slow_period <= mutated.fast_period:
                mutated.slow_period = mutated.fast_period + 10
        
            self.mutation_history.append({
                'parent_id': dna.strategy_id,
                'child_id': mutated.strategy_id,
                'mutations': mutated.mutations,
                'timestamp': datetime.now().isoformat()
            })
        
            return mutated
        except Exception as e:
            logger.error(f"Error in mutate: {e}")
            raise
    
    def _mutate_float(self, value: float, min_val: float, max_val: float) -> float:
        """Mutate a float value with gaussian noise"""
        try:
            noise = random.gauss(0, 0.1) * value
            new_value = value + noise
            return max(min_val, min(max_val, new_value))
        except Exception as e:
            logger.error(f"Error in _mutate_float: {e}")
            raise
    
    def _mutate_int(self, value: int, min_val: int, max_val: int) -> int:
        """Mutate an integer value"""
        try:
            noise = random.randint(-3, 3)
            new_value = value + noise
            return max(min_val, min(max_val, new_value))
        except Exception as e:
            logger.error(f"Error in _mutate_int: {e}")
            raise


class GeneticOptimizer:
    """
    Genetic algorithm optimizer for strategy evolution.
    
    Uses crossover and mutation to create new strategies.
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.crossover_rate = config.get('crossover_rate', 0.7)
            self.mutation_rate = config.get('mutation_rate', 0.2)
            self.elite_ratio = config.get('elite_ratio', 0.1)
        
            self.mutator = StrategyMutation(self.mutation_rate)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def crossover(self, parent1: StrategyDNA, parent2: StrategyDNA) -> StrategyDNA:
        """
        Create offspring by combining genes from two parents.
        """
        try:
            child = StrategyDNA(
                strategy_id=f"strat_{datetime.now().timestamp()}",
                name=f"cross_{parent1.name}_{parent2.name}",
                generation=max(parent1.generation, parent2.generation) + 1,
                parent_ids=[parent1.strategy_id, parent2.strategy_id]
            )
        
            # Randomly select genes from each parent
            child.entry_threshold = random.choice([parent1.entry_threshold, parent2.entry_threshold])
            child.exit_threshold = random.choice([parent1.exit_threshold, parent2.exit_threshold])
            child.stop_loss_pct = random.choice([parent1.stop_loss_pct, parent2.stop_loss_pct])
            child.take_profit_pct = random.choice([parent1.take_profit_pct, parent2.take_profit_pct])
            child.position_size_pct = random.choice([parent1.position_size_pct, parent2.position_size_pct])
            child.fast_period = random.choice([parent1.fast_period, parent2.fast_period])
            child.slow_period = random.choice([parent1.slow_period, parent2.slow_period])
            child.rsi_period = random.choice([parent1.rsi_period, parent2.rsi_period])
            child.rsi_overbought = random.choice([parent1.rsi_overbought, parent2.rsi_overbought])
            child.rsi_oversold = random.choice([parent1.rsi_oversold, parent2.rsi_oversold])
        
            # Combine rules
            child.entry_rules = list(set(parent1.entry_rules + parent2.entry_rules))
            child.exit_rules = list(set(parent1.exit_rules + parent2.exit_rules))
            child.filters = list(set(parent1.filters + parent2.filters))
        
            # Ensure slow > fast
            if child.slow_period <= child.fast_period:
                child.slow_period = child.fast_period + 10
        
            return child
        except Exception as e:
            logger.error(f"Error in crossover: {e}")
            raise
    
    def evolve_population(
        self,
        population: List[StrategyDNA],
        fitness_scores: Dict[str, float]
    ) -> List[StrategyDNA]:
        """
        Evolve a population of strategies.
        
        Steps:
        1. Sort by fitness
        2. Keep elite strategies
        3. Create offspring through crossover
        4. Apply mutations
        """
        # Sort by fitness
        try:
            sorted_pop = sorted(
                population,
                key=lambda s: fitness_scores.get(s.strategy_id, 0),
                reverse=True
            )
        
            pop_size = len(population)
            elite_count = max(1, int(pop_size * self.elite_ratio))
        
            # Keep elite (top performers survive unchanged)
            new_population = sorted_pop[:elite_count]
        
            # Create offspring to fill remaining slots
            while len(new_population) < pop_size:
                # Select parents (tournament selection)
                parent1 = self._tournament_select(sorted_pop, fitness_scores)
                parent2 = self._tournament_select(sorted_pop, fitness_scores)
            
                # Crossover
                if random.random() < self.crossover_rate:
                    child = self.crossover(parent1, parent2)
                else:
                    child = copy.deepcopy(random.choice([parent1, parent2]))
                    child.strategy_id = f"strat_{datetime.now().timestamp()}"
                    child.generation += 1
            
                # Mutation
                if random.random() < self.mutation_rate:
                    child = self.mutator.mutate(child)
            
                new_population.append(child)
        
            return new_population
        except Exception as e:
            logger.error(f"Error in evolve_population: {e}")
            raise
    
    def _tournament_select(
        self,
        population: List[StrategyDNA],
        fitness_scores: Dict[str, float],
        tournament_size: int = 3
    ) -> StrategyDNA:
        """Select parent using tournament selection"""
        try:
            tournament = random.sample(population, min(tournament_size, len(population)))
            return max(tournament, key=lambda s: fitness_scores.get(s.strategy_id, 0))
        except Exception as e:
            logger.error(f"Error in _tournament_select: {e}")
            raise


class ConceptDriftDetector:
    """
    Detects when market fundamentally changes (concept drift).
    
    Types of drift:
    - Gradual: Slow evolution over months/years
    - Sudden: Abrupt regime change
    - Recurring: Cyclical changes
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.window_size = config.get('window_size', 100)
            self.drift_threshold = config.get('drift_threshold', 0.01)
        
            self.performance_window: deque = deque(maxlen=self.window_size * 2)
            self.drift_events: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_observation(self, performance: float):
        """Add a performance observation"""
        try:
            self.performance_window.append({
                'value': performance,
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Error in add_observation: {e}")
            raise
    
    def check_for_drift(self) -> Tuple[bool, Optional[str], float]:
        """
        Check if concept drift has occurred.
        
        Returns:
            Tuple of (drift_detected, drift_type, p_value)
        """
        try:
            if len(self.performance_window) < self.window_size:
                return False, None, 1.0
        
            observations = [o['value'] for o in self.performance_window]
        
            # Split into recent vs historical
            split_point = len(observations) // 2
            historical = observations[:split_point]
            recent = observations[split_point:]
        
            # Simple statistical test (mean comparison)
            hist_mean = np.mean(historical)
            recent_mean = np.mean(recent)
            hist_std = np.std(historical) if len(historical) > 1 else 0.01
        
            # Z-score for difference
            z_score = abs(recent_mean - hist_mean) / max(hist_std, 0.01)
        
            # Approximate p-value (simplified)
            p_value = 2 * (1 - min(0.9999, 0.5 + 0.5 * np.tanh(z_score / 2)))
        
            drift_detected = p_value < self.drift_threshold
        
            if drift_detected:
                # Determine drift type
                if recent_mean < hist_mean * 0.5:
                    drift_type = "SUDDEN_DEGRADATION"
                elif recent_mean > hist_mean * 1.5:
                    drift_type = "SUDDEN_IMPROVEMENT"
                else:
                    drift_type = "GRADUAL_SHIFT"
            
                self.drift_events.append({
                    'type': drift_type,
                    'timestamp': datetime.now().isoformat(),
                    'historical_mean': hist_mean,
                    'recent_mean': recent_mean,
                    'p_value': p_value
                })
            
                logger.warning(f"🚨 CONCEPT DRIFT DETECTED: {drift_type}")
                logger.warning(f"Historical mean: {hist_mean:.4f}, Recent mean: {recent_mean:.4f}")
            
                return True, drift_type, p_value
        
            return False, None, p_value
        except Exception as e:
            logger.error(f"Error in check_for_drift: {e}")
            raise
    
    def get_drift_response(self, drift_type: str) -> Dict:
        """Get recommended response to drift"""
        try:
            responses = {
                "SUDDEN_DEGRADATION": {
                    'exploration_rate': 0.5,
                    'position_multiplier': 0.5,
                    'learning_rate_multiplier': 2.0,
                    'action': 'RAPID_RELEARNING'
                },
                "SUDDEN_IMPROVEMENT": {
                    'exploration_rate': 0.3,
                    'position_multiplier': 1.0,
                    'learning_rate_multiplier': 1.5,
                    'action': 'CAUTIOUS_EXPLOITATION'
                },
                "GRADUAL_SHIFT": {
                    'exploration_rate': 0.4,
                    'position_multiplier': 0.8,
                    'learning_rate_multiplier': 1.2,
                    'action': 'ADAPTIVE_LEARNING'
                }
            }
        
            return responses.get(drift_type, {
                'exploration_rate': 0.3,
                'position_multiplier': 1.0,
                'learning_rate_multiplier': 1.0,
                'action': 'NORMAL'
            })
        except Exception as e:
            logger.error(f"Error in get_drift_response: {e}")
            raise


class PopulationManager:
    """
    Manages the population of strategies.
    
    Handles:
    - Population initialization
    - Fitness evaluation
    - Selection and reproduction
    - Population statistics
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.max_population = config.get('max_population', 50)
            self.min_population = config.get('min_population', 10)
        
            self.population: List[StrategyDNA] = []
            self.fitness_history: Dict[str, List[float]] = {}
            self.generation: int = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def initialize_population(self, templates: List[Dict] = None) -> List[StrategyDNA]:
        """Initialize population with template strategies"""
        try:
            templates = templates or []
        
            # Create from templates
            for i, template in enumerate(templates[:self.max_population]):
                dna = StrategyDNA(
                    strategy_id=f"strat_init_{i}",
                    name=template.get('name', f'strategy_{i}'),
                    entry_threshold=template.get('entry_threshold', 0.6),
                    exit_threshold=template.get('exit_threshold', 0.4),
                    stop_loss_pct=template.get('stop_loss_pct', 0.02),
                    take_profit_pct=template.get('take_profit_pct', 0.04),
                    generation=0
                )
                self.population.append(dna)
        
            # Fill remaining with random strategies
            while len(self.population) < self.min_population:
                dna = StrategyDNA(
                    strategy_id=f"strat_rand_{len(self.population)}",
                    name=f"random_strategy_{len(self.population)}",
                    entry_threshold=random.uniform(0.4, 0.8),
                    exit_threshold=random.uniform(0.3, 0.6),
                    stop_loss_pct=random.uniform(0.01, 0.03),
                    take_profit_pct=random.uniform(0.02, 0.06),
                    fast_period=random.randint(5, 20),
                    slow_period=random.randint(20, 50),
                    generation=0
                )
                self.population.append(dna)
        
            logger.info(f"Population initialized with {len(self.population)} strategies")
            return self.population
        except Exception as e:
            logger.error(f"Error in initialize_population: {e}")
            raise
    
    def update_fitness(self, strategy_id: str, fitness: float):
        """Update fitness for a strategy"""
        try:
            for strategy in self.population:
                if strategy.strategy_id == strategy_id:
                    strategy.fitness = fitness
                
                    if strategy_id not in self.fitness_history:
                        self.fitness_history[strategy_id] = []
                    self.fitness_history[strategy_id].append(fitness)
                
                    break
        except Exception as e:
            logger.error(f"Error in update_fitness: {e}")
            raise
    
    def get_fitness_scores(self) -> Dict[str, float]:
        """Get current fitness scores for all strategies"""
        return {s.strategy_id: s.fitness for s in self.population}
    
    def get_best_strategies(self, n: int = 5) -> List[StrategyDNA]:
        """Get top N strategies by fitness"""
        try:
            sorted_pop = sorted(self.population, key=lambda s: s.fitness, reverse=True)
            return sorted_pop[:n]
        except Exception as e:
            logger.error(f"Error in get_best_strategies: {e}")
            raise
    
    def get_population_stats(self) -> Dict:
        """Get population statistics"""
        try:
            if not self.population:
                return {'size': 0}
        
            fitness_values = [s.fitness for s in self.population]
        
            return {
                'size': len(self.population),
                'generation': self.generation,
                'avg_fitness': np.mean(fitness_values),
                'max_fitness': np.max(fitness_values),
                'min_fitness': np.min(fitness_values),
                'std_fitness': np.std(fitness_values),
                'best_strategy': self.get_best_strategies(1)[0].strategy_id if self.population else None
            }
        except Exception as e:
            logger.error(f"Error in get_population_stats: {e}")
            raise


class EvolutionaryStrategySystem:
    """
    Master system for evolutionary strategy optimization.
    
    The market is the fitness function:
    - Good strategies (profits) survive and reproduce
    - Bad strategies (losses) are eliminated
    - Over time, strategies evolve to fit current market
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.population_manager = PopulationManager(config)
            self.genetic_optimizer = GeneticOptimizer(config)
            self.drift_detector = ConceptDriftDetector(config)
            self.mutator = StrategyMutation(config.get('mutation_rate', 0.2))
        
            self.evolution_history: List[Dict] = []
            self.market_feedback_period_days = config.get('feedback_period_days', 30)
        
            logger.info("EvolutionaryStrategySystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize(self, templates: List[Dict] = None):
        """Initialize the evolutionary system"""
        try:
            self.population_manager.initialize_population(templates)
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def evolve(self) -> Dict:
        """
        Run one evolution cycle.
        
        Let the market teach us which strategies work.
        """
        try:
            self.population_manager.generation += 1
            generation = self.population_manager.generation
        
            # Get current fitness scores
            fitness_scores = self.population_manager.get_fitness_scores()
        
            # Check for concept drift
            avg_fitness = np.mean(list(fitness_scores.values())) if fitness_scores else 0
            self.drift_detector.add_observation(avg_fitness)
            drift_detected, drift_type, _ = self.drift_detector.check_for_drift()
        
            if drift_detected:
                logger.warning(f"Concept drift detected: {drift_type}")
                response = self.drift_detector.get_drift_response(drift_type)
                # Increase mutation rate during drift
                self.mutator.mutation_rate = min(0.5, self.mutator.mutation_rate * 1.5)
        
            # Evolve population
            old_population = self.population_manager.population.copy()
            new_population = self.genetic_optimizer.evolve_population(
                old_population,
                fitness_scores
            )
        
            self.population_manager.population = new_population
        
            # Log evolution
            stats = self.population_manager.get_population_stats()
        
            evolution_record = {
                'generation': generation,
                'timestamp': datetime.now().isoformat(),
                'population_size': len(new_population),
                'avg_fitness': stats['avg_fitness'],
                'max_fitness': stats['max_fitness'],
                'drift_detected': drift_detected,
                'drift_type': drift_type
            }
        
            self.evolution_history.append(evolution_record)
        
            logger.info(f"Generation {generation}: Avg fitness = {stats['avg_fitness']:.4f}, Max = {stats['max_fitness']:.4f}")
        
            return evolution_record
        except Exception as e:
            logger.error(f"Error in evolve: {e}")
            raise
    
    def evaluate_strategy(self, strategy_id: str, trades: List[Dict]) -> float:
        """
        Evaluate a strategy based on its trades.
        
        The market grades the strategy through P&L.
        """
        try:
            if not trades:
                return 0.0
        
            # Calculate metrics
            pnls = [t.get('pnl', 0) for t in trades]
            wins = sum(1 for p in pnls if p > 0)
        
            total_pnl = sum(pnls)
            win_rate = wins / len(trades)
        
            # Calculate Sharpe-like ratio
            if len(pnls) > 1:
                returns_std = np.std(pnls)
                sharpe = np.mean(pnls) / max(returns_std, 0.0001) * np.sqrt(252)
            else:
                sharpe = 0.0
        
            # Fitness is combination of metrics
            fitness = (
                0.4 * sharpe +
                0.3 * win_rate +
                0.3 * min(1.0, max(-1.0, total_pnl))
            )
        
            # Update strategy
            for strategy in self.population_manager.population:
                if strategy.strategy_id == strategy_id:
                    strategy.trades = len(trades)
                    strategy.wins = wins
                    strategy.sharpe_ratio = sharpe
                    strategy.fitness = fitness
                    break
        
            self.population_manager.update_fitness(strategy_id, fitness)
        
            return fitness
        except Exception as e:
            logger.error(f"Error in evaluate_strategy: {e}")
            raise
    
    def get_best_strategies(self, n: int = 5) -> List[Dict]:
        """Get the best performing strategies"""
        try:
            best = self.population_manager.get_best_strategies(n)
            return [s.to_dict() for s in best]
        except Exception as e:
            logger.error(f"Error in get_best_strategies: {e}")
            raise
    
    def get_evolution_summary(self) -> Dict:
        """Get summary of evolution progress"""
        return {
            'current_generation': self.population_manager.generation,
            'population_stats': self.population_manager.get_population_stats(),
            'drift_events': len(self.drift_detector.drift_events),
            'evolution_history': self.evolution_history[-10:],
            'best_strategies': self.get_best_strategies(3)
        }


# Export all classes
__all__ = [
    'MutationType',
    'StrategyDNA',
    'StrategyMutation',
    'GeneticOptimizer',
    'ConceptDriftDetector',
    'PopulationManager',
    'EvolutionaryStrategySystem'
]
