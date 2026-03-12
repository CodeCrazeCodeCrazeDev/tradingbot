"""
Self-Evolving Strategy System with Genetic Algorithms and Meta-Learning

This module implements strategy evolution, genetic programming, and meta-learning
for continuous strategy improvement and adaptation to market conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging
import random
import copy
import hashlib

logger = logging.getLogger(__name__)


class StrategyGene(Enum):
    """Strategy genetic components"""
    ENTRY_LOGIC = "entry_logic"
    EXIT_LOGIC = "exit_logic"
    POSITION_SIZING = "position_sizing"
    RISK_MANAGEMENT = "risk_management"
    TIMEFRAME = "timeframe"
    INDICATORS = "indicators"
    FILTERS = "filters"


class EvolutionOperator(Enum):
    """Genetic operators for evolution"""
    CROSSOVER = "crossover"
    MUTATION = "mutation"
    SELECTION = "selection"
    ELITISM = "elitism"
    SPECIATION = "speciation"


@dataclass
class StrategyDNA:
    """DNA encoding of a trading strategy"""
    strategy_id: str
    genes: Dict[StrategyGene, Any]
    fitness: float = 0.0
    age: int = 0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutations: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def clone(self) -> 'StrategyDNA':
        """Create a deep copy"""
        return copy.deepcopy(self)
    
    def get_hash(self) -> str:
        """Get unique hash of strategy DNA"""
        gene_str = str(sorted(self.genes.items()))
        return hashlib.md5(gene_str.encode()).hexdigest()[:16]


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    strategy_id: str
    total_trades: int = 0
    winning_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    avg_profit_per_trade: float = 0.0
    consistency_score: float = 0.0
    market_conditions: Dict[str, float] = field(default_factory=dict)
    
    def calculate_fitness(self) -> float:
        """Calculate overall fitness score"""
        if self.total_trades < 10:
            return 0.0
        
        # Multi-objective fitness
        profit_score = self.total_profit / max(abs(self.total_loss), 1.0)
        win_rate_score = self.win_rate
        sharpe_score = max(self.sharpe_ratio, 0) / 3.0  # Normalize
        consistency_score = self.consistency_score
        drawdown_penalty = 1.0 / (1.0 + abs(self.max_drawdown))
        
        fitness = (
            0.3 * profit_score +
            0.2 * win_rate_score +
            0.2 * sharpe_score +
            0.15 * consistency_score +
            0.15 * drawdown_penalty
        )
        
        return max(fitness, 0.0)


class GeneticOperators:
    """Genetic operators for strategy evolution"""
    
    @staticmethod
    def crossover(parent1: StrategyDNA, parent2: StrategyDNA) -> Tuple[StrategyDNA, StrategyDNA]:
        """Perform crossover between two strategies"""
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        # Single-point crossover
        genes = list(StrategyGene)
        crossover_point = random.randint(1, len(genes) - 1)
        
        for i, gene in enumerate(genes):
            if i >= crossover_point:
                child1.genes[gene], child2.genes[gene] = child2.genes[gene], child1.genes[gene]
        
        # Update metadata
        child1.strategy_id = f"child_{parent1.strategy_id[:8]}_{parent2.strategy_id[:8]}"
        child2.strategy_id = f"child_{parent2.strategy_id[:8]}_{parent1.strategy_id[:8]}"
        child1.parent_ids = [parent1.strategy_id, parent2.strategy_id]
        child2.parent_ids = [parent2.strategy_id, parent1.strategy_id]
        child1.generation = max(parent1.generation, parent2.generation) + 1
        child2.generation = max(parent1.generation, parent2.generation) + 1
        
        return child1, child2
    
    @staticmethod
    def mutate(strategy: StrategyDNA, mutation_rate: float = 0.1) -> StrategyDNA:
        """Mutate a strategy"""
        mutated = strategy.clone()
        
        for gene in StrategyGene:
            if random.random() < mutation_rate:
                mutated.genes[gene] = GeneticOperators._mutate_gene(gene, mutated.genes[gene])
                mutated.mutations += 1
        
        mutated.strategy_id = f"mutant_{strategy.strategy_id[:12]}"
        return mutated
    
    @staticmethod
    def _mutate_gene(gene: StrategyGene, current_value: Any) -> Any:
        """Mutate a specific gene"""
        if gene == StrategyGene.ENTRY_LOGIC:
            options = ['momentum', 'mean_reversion', 'breakout', 'pattern', 'ml_signal']
            return random.choice(options)
        
        elif gene == StrategyGene.EXIT_LOGIC:
            options = ['fixed_target', 'trailing_stop', 'time_based', 'signal_reversal', 'adaptive']
            return random.choice(options)
        
        elif gene == StrategyGene.POSITION_SIZING:
            return {
                'method': random.choice(['fixed', 'kelly', 'volatility', 'risk_parity']),
                'size': random.uniform(0.01, 0.1),
                'max_size': random.uniform(0.1, 0.3)
            }
        
        elif gene == StrategyGene.RISK_MANAGEMENT:
            return {
                'stop_loss': random.uniform(0.01, 0.05),
                'take_profit': random.uniform(0.02, 0.1),
                'max_drawdown': random.uniform(0.1, 0.3)
            }
        
        elif gene == StrategyGene.TIMEFRAME:
            return random.choice(['1m', '5m', '15m', '1h', '4h', '1d'])
        
        elif gene == StrategyGene.INDICATORS:
            all_indicators = ['sma', 'ema', 'rsi', 'macd', 'bbands', 'atr', 'adx', 'stoch']
            n_indicators = random.randint(2, 5)
            return random.sample(all_indicators, n_indicators)
        
        elif gene == StrategyGene.FILTERS:
            return {
                'volume_filter': random.choice([True, False]),
                'volatility_filter': random.choice([True, False]),
                'trend_filter': random.choice([True, False]),
                'time_filter': random.choice([True, False])
            }
        
        return current_value


class StrategyPopulation:
    """Manages a population of strategies"""
    
    def __init__(self, population_size: int = 50, elite_size: int = 5):
        self.population_size = population_size
        self.elite_size = elite_size
        self.strategies: Dict[str, StrategyDNA] = {}
        self.performances: Dict[str, StrategyPerformance] = {}
        self.generation = 0
        self.best_ever_fitness = 0.0
        self.best_ever_strategy: Optional[StrategyDNA] = None
        
    def initialize_population(self):
        """Create initial random population"""
        for i in range(self.population_size):
            strategy = self._create_random_strategy(f"gen0_ind{i}")
            self.strategies[strategy.strategy_id] = strategy
            self.performances[strategy.strategy_id] = StrategyPerformance(strategy.strategy_id)
        
        logger.info(f"Initialized population with {self.population_size} strategies")
    
    def _create_random_strategy(self, strategy_id: str) -> StrategyDNA:
        """Create a random strategy"""
        genes = {
            StrategyGene.ENTRY_LOGIC: random.choice(['momentum', 'mean_reversion', 'breakout']),
            StrategyGene.EXIT_LOGIC: random.choice(['fixed_target', 'trailing_stop', 'adaptive']),
            StrategyGene.POSITION_SIZING: {
                'method': random.choice(['fixed', 'kelly', 'volatility']),
                'size': random.uniform(0.01, 0.05),
                'max_size': random.uniform(0.1, 0.2)
            },
            StrategyGene.RISK_MANAGEMENT: {
                'stop_loss': random.uniform(0.01, 0.03),
                'take_profit': random.uniform(0.02, 0.06),
                'max_drawdown': random.uniform(0.1, 0.2)
            },
            StrategyGene.TIMEFRAME: random.choice(['5m', '15m', '1h', '4h']),
            StrategyGene.INDICATORS: random.sample(['sma', 'ema', 'rsi', 'macd', 'bbands', 'atr'], 3),
            StrategyGene.FILTERS: {
                'volume_filter': random.choice([True, False]),
                'volatility_filter': random.choice([True, False]),
                'trend_filter': random.choice([True, False])
            }
        }
        
        return StrategyDNA(
            strategy_id=strategy_id,
            genes=genes,
            generation=self.generation
        )
    
    def evolve_generation(self):
        """Evolve to next generation"""
        # Calculate fitness for all strategies
        for strategy_id, performance in self.performances.items():
            fitness = performance.calculate_fitness()
            if strategy_id in self.strategies:
                self.strategies[strategy_id].fitness = fitness
        
        # Sort by fitness
        sorted_strategies = sorted(
            self.strategies.values(),
            key=lambda s: s.fitness,
            reverse=True
        )
        
        # Track best ever
        if sorted_strategies and sorted_strategies[0].fitness > self.best_ever_fitness:
            self.best_ever_fitness = sorted_strategies[0].fitness
            self.best_ever_strategy = sorted_strategies[0].clone()
            logger.info(f"New best strategy found! Fitness: {self.best_ever_fitness:.4f}")
        
        # Elitism - keep top performers
        elite = sorted_strategies[:self.elite_size]
        
        # Selection - tournament selection
        selected = self._tournament_selection(sorted_strategies, self.population_size - self.elite_size)
        
        # Create new generation
        new_strategies = {}
        
        # Add elite
        for strategy in elite:
            new_strategies[strategy.strategy_id] = strategy
        
        # Crossover and mutation
        while len(new_strategies) < self.population_size:
            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = GeneticOperators.crossover(parent1, parent2)
            
            # Mutate children
            if random.random() < 0.3:
                child1 = GeneticOperators.mutate(child1, mutation_rate=0.1)
            if random.random() < 0.3:
                child2 = GeneticOperators.mutate(child2, mutation_rate=0.1)
            
            new_strategies[child1.strategy_id] = child1
            if len(new_strategies) < self.population_size:
                new_strategies[child2.strategy_id] = child2
        
        # Update population
        self.strategies = new_strategies
        self.generation += 1
        
        # Initialize performance tracking for new strategies
        for strategy_id in self.strategies:
            if strategy_id not in self.performances:
                self.performances[strategy_id] = StrategyPerformance(strategy_id)
        
        logger.info(f"Evolved to generation {self.generation}")
    
    def _tournament_selection(self, strategies: List[StrategyDNA], n: int) -> List[StrategyDNA]:
        """Tournament selection"""
        selected = []
        tournament_size = 3
        
        for _ in range(n):
            tournament = random.sample(strategies, min(tournament_size, len(strategies)))
            winner = max(tournament, key=lambda s: s.fitness)
            selected.append(winner)
        
        return selected
    
    def get_top_strategies(self, n: int = 10) -> List[StrategyDNA]:
        """Get top N strategies"""
        return sorted(
            self.strategies.values(),
            key=lambda s: s.fitness,
            reverse=True
        )[:n]


class MetaLearner:
    """Meta-learning for strategy adaptation"""
    
    def __init__(self):
        self.strategy_performance_history: Dict[str, List[float]] = {}
        self.market_condition_mapping: Dict[str, List[str]] = {}
        self.adaptation_memory: deque = deque(maxlen=1000)
        
    def learn_strategy_conditions(self, strategy_id: str, market_condition: str, performance: float):
        """Learn which strategies work in which conditions"""
        if market_condition not in self.market_condition_mapping:
            self.market_condition_mapping[market_condition] = []
        
        if strategy_id not in self.strategy_performance_history:
            self.strategy_performance_history[strategy_id] = []
        
        self.strategy_performance_history[strategy_id].append(performance)
        
        # Track good performers for this condition
        if performance > 0.6:  # Above threshold
            if strategy_id not in self.market_condition_mapping[market_condition]:
                self.market_condition_mapping[market_condition].append(strategy_id)
    
    def recommend_strategies(self, market_condition: str, n: int = 5) -> List[str]:
        """Recommend best strategies for current market condition"""
        if market_condition not in self.market_condition_mapping:
            return []
        
        candidates = self.market_condition_mapping[market_condition]
        
        # Sort by average performance
        scored = []
        for strategy_id in candidates:
            if strategy_id in self.strategy_performance_history:
                avg_perf = np.mean(self.strategy_performance_history[strategy_id][-20:])
                scored.append((strategy_id, avg_perf))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:n]]
    
    def adapt_to_regime_change(self, old_regime: str, new_regime: str) -> Dict[str, Any]:
        """Adapt strategies when market regime changes"""
        recommendations = {
            'switch_strategies': self.recommend_strategies(new_regime, n=3),
            'increase_caution': new_regime in ['high_volatility', 'crisis'],
            'suggested_adjustments': {}
        }
        
        if new_regime == 'high_volatility':
            recommendations['suggested_adjustments'] = {
                'position_size': 0.5,  # Reduce by 50%
                'stop_loss': 0.8,      # Tighter stops
                'take_profit': 1.5     # Wider targets
            }
        elif new_regime == 'trending':
            recommendations['suggested_adjustments'] = {
                'position_size': 1.2,  # Increase by 20%
                'stop_loss': 1.2,      # Wider stops
                'take_profit': 1.0
            }
        
        return recommendations


class StrategyEvolutionEngine:
    """Main engine for strategy evolution and adaptation"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.population = StrategyPopulation(
            population_size=self.config.get('population_size', 50),
            elite_size=self.config.get('elite_size', 5)
        )
        self.meta_learner = MetaLearner()
        self.active_strategies: Set[str] = set()
        self.evolution_history: List[Dict] = []
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the evolution engine"""
        self.population.initialize_population()
        
        # Activate top strategies
        top_strategies = self.population.get_top_strategies(5)
        self.active_strategies = {s.strategy_id for s in top_strategies}
        
        self.is_initialized = True
        logger.info("Strategy evolution engine initialized")
    
    async def record_strategy_performance(self, strategy_id: str, trade_result: Dict[str, Any]):
        """Record performance of a strategy"""
        if strategy_id not in self.population.performances:
            return
        
        perf = self.population.performances[strategy_id]
        perf.total_trades += 1
        
        profit = trade_result.get('profit', 0)
        if profit > 0:
            perf.winning_trades += 1
            perf.total_profit += profit
        else:
            perf.total_loss += abs(profit)
        
        perf.win_rate = perf.winning_trades / perf.total_trades
        perf.profit_factor = perf.total_profit / max(abs(perf.total_loss), 1.0)
        
        # Update meta-learner
        market_condition = trade_result.get('market_condition', 'unknown')
        self.meta_learner.learn_strategy_conditions(
            strategy_id,
            market_condition,
            1.0 if profit > 0 else 0.0
        )
    
    async def evolve(self):
        """Trigger evolution to next generation"""
        self.population.evolve_generation()
        
        # Update active strategies
        top_strategies = self.population.get_top_strategies(5)
        self.active_strategies = {s.strategy_id for s in top_strategies}
        
        # Record evolution event
        self.evolution_history.append({
            'generation': self.population.generation,
            'best_fitness': self.population.best_ever_fitness,
            'timestamp': datetime.utcnow(),
            'active_strategies': list(self.active_strategies)
        })
        
        logger.info(f"Evolution complete. Generation: {self.population.generation}, "
                   f"Best fitness: {self.population.best_ever_fitness:.4f}")
    
    def get_active_strategies(self) -> List[StrategyDNA]:
        """Get currently active strategies"""
        return [self.population.strategies[sid] for sid in self.active_strategies 
                if sid in self.population.strategies]
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get evolution status"""
        return {
            'generation': self.population.generation,
            'population_size': len(self.population.strategies),
            'active_strategies': len(self.active_strategies),
            'best_ever_fitness': self.population.best_ever_fitness,
            'best_strategy': self.population.best_ever_strategy.__dict__ if self.population.best_ever_strategy else None,
            'evolution_history': self.evolution_history[-10:]
        }


async def create_evolution_engine(config: Optional[Dict] = None) -> StrategyEvolutionEngine:
    """Factory function to create evolution engine"""
    engine = StrategyEvolutionEngine(config)
    await engine.initialize()
    return engine
