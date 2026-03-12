"""
Recursive Strategy Evolution

Strategies that evolve themselves recursively - each generation of strategies
creates better strategies, which in turn create even better strategies.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
import random
import json

logger = logging.getLogger(__name__)


class StrategyGeneration(Enum):
    """Strategy evolution generations"""
    GEN_0_BASELINE = 0
    GEN_1_IMPROVED = 1
    GEN_2_OPTIMIZED = 2
    GEN_3_EVOLVED = 3
    GEN_4_META_EVOLVED = 4
    GEN_5_RECURSIVE = 5


@dataclass
class StrategyMutation:
    """Represents a mutation in strategy evolution"""
    mutation_id: str
    parent_strategy_id: str
    generation: int
    mutation_type: str
    parameters_changed: Dict[str, Any]
    performance_delta: float
    timestamp: datetime
    
    def is_beneficial(self) -> bool:
        """Check if mutation improved performance"""
        return self.performance_delta > 0


@dataclass
class EvolvingStrategy:
    """A strategy that can evolve itself"""
    strategy_id: str
    generation: StrategyGeneration
    parent_id: Optional[str]
    parameters: Dict[str, Any]
    performance_history: List[float] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    fitness_score: float = 0.0
    
    def add_performance(self, performance: float):
        """Add performance measurement"""
        self.performance_history.append(performance)
        self.fitness_score = sum(self.performance_history) / len(self.performance_history)
    
    def get_avg_performance(self) -> float:
        """Get average performance"""
        if not self.performance_history:
            return 0.0
        return self.fitness_score


class RecursiveStrategyEvolution:
    """
    Recursive strategy evolution engine.
    
    Strategies evolve through:
    1. Mutation - Random parameter changes
    2. Crossover - Combining successful strategies
    3. Selection - Keeping best performers
    4. Meta-evolution - Evolving the evolution process itself
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_generations = self.config.get('max_generations', 6)
        self.population_size = self.config.get('population_size', 20)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.3)
        
        self.strategies: Dict[str, EvolvingStrategy] = {}
        self.mutations: Dict[str, StrategyMutation] = {}
        self.generation_best: Dict[int, str] = {}
        self.evolution_history: List[Dict[str, Any]] = []
        
        self._initialize_baseline_strategies()
        logger.info("RecursiveStrategyEvolution initialized")
    
    def _initialize_baseline_strategies(self):
        """Initialize baseline (Gen 0) strategies"""
        baseline_strategies = [
            {'type': 'trend_following', 'lookback': 20, 'threshold': 0.02},
            {'type': 'mean_reversion', 'lookback': 10, 'std_dev': 2.0},
            {'type': 'momentum', 'period': 14, 'threshold': 0.5},
            {'type': 'breakout', 'period': 20, 'multiplier': 1.5},
        ]
        
        for i, params in enumerate(baseline_strategies):
            strategy_id = f"gen0_strategy_{i}"
            strategy = EvolvingStrategy(
                strategy_id=strategy_id,
                generation=StrategyGeneration.GEN_0_BASELINE,
                parent_id=None,
                parameters=params
            )
            self.strategies[strategy_id] = strategy
    
    async def evolve_generation(
        self,
        current_generation: int,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evolve one generation of strategies.
        
        Args:
            current_generation: Current generation number
            market_data: Market data for evaluation
            
        Returns:
            Evolution results
        """
        if current_generation >= self.max_generations:
            return {'status': 'max_generations_reached'}
        
        # Get current generation strategies
        current_strategies = [
            s for s in self.strategies.values()
            if s.generation.value == current_generation
        ]
        
        if not current_strategies:
            return {'status': 'no_strategies_in_generation'}
        
        # Evaluate all strategies
        await self._evaluate_strategies(current_strategies, market_data)
        
        # Select best performers
        elite = self._select_elite(current_strategies)
        
        # Generate next generation
        next_gen_strategies = []
        
        # Keep elite (elitism)
        next_gen_strategies.extend(elite)
        
        # Create offspring through mutation
        mutations = await self._mutate_strategies(elite, current_generation + 1)
        next_gen_strategies.extend(mutations)
        
        # Create offspring through crossover
        crossovers = await self._crossover_strategies(elite, current_generation + 1)
        next_gen_strategies.extend(crossovers)
        
        # Add to population
        for strategy in next_gen_strategies:
            self.strategies[strategy.strategy_id] = strategy
        
        # Track best of generation
        best = max(current_strategies, key=lambda s: s.fitness_score)
        self.generation_best[current_generation] = best.strategy_id
        
        # Record evolution history
        self.evolution_history.append({
            'generation': current_generation,
            'population_size': len(current_strategies),
            'best_fitness': best.fitness_score,
            'avg_fitness': sum(s.fitness_score for s in current_strategies) / len(current_strategies),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Meta-evolution: Improve evolution parameters
        await self._meta_evolve(current_generation)
        
        return {
            'generation': current_generation,
            'strategies_evaluated': len(current_strategies),
            'next_gen_created': len(next_gen_strategies),
            'best_fitness': best.fitness_score,
            'best_strategy_id': best.strategy_id
        }
    
    async def _evaluate_strategies(
        self,
        strategies: List[EvolvingStrategy],
        market_data: Optional[Dict[str, Any]]
    ):
        """Evaluate strategies on market data"""
        for strategy in strategies:
            # Simulate strategy performance
            performance = await self._simulate_strategy(strategy, market_data)
            strategy.add_performance(performance)
    
    async def _simulate_strategy(
        self,
        strategy: EvolvingStrategy,
        market_data: Optional[Dict[str, Any]]
    ) -> float:
        """Simulate strategy and return performance"""
        # Placeholder - would run actual backtest
        base_performance = 0.5
        
        # Add some randomness based on parameters
        param_bonus = sum(hash(str(v)) % 100 for v in strategy.parameters.values()) / 1000
        
        return base_performance + param_bonus
    
    def _select_elite(
        self,
        strategies: List[EvolvingStrategy],
        elite_ratio: float = 0.2
    ) -> List[EvolvingStrategy]:
        """Select top performing strategies"""
        sorted_strategies = sorted(
            strategies,
            key=lambda s: s.fitness_score,
            reverse=True
        )
        
        elite_count = max(1, int(len(strategies) * elite_ratio))
        return sorted_strategies[:elite_count]
    
    async def _mutate_strategies(
        self,
        parent_strategies: List[EvolvingStrategy],
        next_generation: int
    ) -> List[EvolvingStrategy]:
        """Create mutated versions of strategies"""
        mutated = []
        
        for parent in parent_strategies:
            if random.random() < self.mutation_rate:
                mutated_strategy = await self._mutate_strategy(parent, next_generation)
                mutated.append(mutated_strategy)
        
        return mutated
    
    async def _mutate_strategy(
        self,
        parent: EvolvingStrategy,
        generation: int
    ) -> EvolvingStrategy:
        """Mutate a single strategy"""
        mutation_id = f"mutation_{datetime.utcnow().timestamp()}"
        strategy_id = f"gen{generation}_mutated_{mutation_id}"
        
        # Copy parent parameters
        new_params = parent.parameters.copy()
        
        # Mutate random parameter
        param_to_mutate = random.choice(list(new_params.keys()))
        old_value = new_params[param_to_mutate]
        
        # Apply mutation
        if isinstance(old_value, (int, float)):
            mutation_factor = random.uniform(0.8, 1.2)
            new_params[param_to_mutate] = old_value * mutation_factor
        
        # Create mutated strategy
        mutated = EvolvingStrategy(
            strategy_id=strategy_id,
            generation=StrategyGeneration(min(generation, 5)),
            parent_id=parent.strategy_id,
            parameters=new_params
        )
        
        # Record mutation
        mutation = StrategyMutation(
            mutation_id=mutation_id,
            parent_strategy_id=parent.strategy_id,
            generation=generation,
            mutation_type='parameter_mutation',
            parameters_changed={param_to_mutate: new_params[param_to_mutate]},
            performance_delta=0.0,  # Will be updated after evaluation
            timestamp=datetime.utcnow()
        )
        
        self.mutations[mutation_id] = mutation
        parent.children.append(strategy_id)
        mutated.mutations.append(mutation_id)
        
        return mutated
    
    async def _crossover_strategies(
        self,
        parent_strategies: List[EvolvingStrategy],
        next_generation: int
    ) -> List[EvolvingStrategy]:
        """Create offspring through crossover"""
        offspring = []
        
        for i in range(0, len(parent_strategies) - 1, 2):
            if random.random() < self.crossover_rate:
                parent1 = parent_strategies[i]
                parent2 = parent_strategies[i + 1]
                
                child = await self._crossover_two_strategies(
                    parent1, parent2, next_generation
                )
                offspring.append(child)
        
        return offspring
    
    async def _crossover_two_strategies(
        self,
        parent1: EvolvingStrategy,
        parent2: EvolvingStrategy,
        generation: int
    ) -> EvolvingStrategy:
        """Crossover two strategies to create offspring"""
        strategy_id = f"gen{generation}_crossover_{datetime.utcnow().timestamp()}"
        
        # Combine parameters from both parents
        new_params = {}
        all_keys = set(parent1.parameters.keys()) | set(parent2.parameters.keys())
        
        for key in all_keys:
            if key in parent1.parameters and key in parent2.parameters:
                # Average the values
                val1 = parent1.parameters[key]
                val2 = parent2.parameters[key]
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    new_params[key] = (val1 + val2) / 2
                else:
                    new_params[key] = random.choice([val1, val2])
            elif key in parent1.parameters:
                new_params[key] = parent1.parameters[key]
            else:
                new_params[key] = parent2.parameters[key]
        
        # Create offspring
        offspring = EvolvingStrategy(
            strategy_id=strategy_id,
            generation=StrategyGeneration(min(generation, 5)),
            parent_id=f"{parent1.strategy_id}+{parent2.strategy_id}",
            parameters=new_params
        )
        
        parent1.children.append(strategy_id)
        parent2.children.append(strategy_id)
        
        return offspring
    
    async def _meta_evolve(self, generation: int):
        """
        Meta-evolution: Evolve the evolution process itself.
        
        This is the recursive part - we analyze how well evolution is working
        and adjust the evolution parameters.
        """
        if len(self.evolution_history) < 3:
            return
        
        # Analyze recent evolution effectiveness
        recent_history = self.evolution_history[-3:]
        
        # Check if fitness is improving
        fitness_trend = [h['best_fitness'] for h in recent_history]
        is_improving = all(fitness_trend[i] > fitness_trend[i-1] 
                          for i in range(1, len(fitness_trend)))
        
        if is_improving:
            # Evolution is working well, can be more aggressive
            self.mutation_rate = min(0.3, self.mutation_rate * 1.1)
            logger.info(f"Increased mutation rate to {self.mutation_rate}")
        else:
            # Evolution is stagnating, be more conservative
            self.mutation_rate = max(0.05, self.mutation_rate * 0.9)
            logger.info(f"Decreased mutation rate to {self.mutation_rate}")
        
        # Adjust crossover rate based on diversity
        avg_fitness = recent_history[-1]['avg_fitness']
        best_fitness = recent_history[-1]['best_fitness']
        diversity = (best_fitness - avg_fitness) / (best_fitness + 1e-6)
        
        if diversity < 0.1:
            # Low diversity, increase crossover to explore
            self.crossover_rate = min(0.5, self.crossover_rate * 1.1)
        else:
            # High diversity, can reduce crossover
            self.crossover_rate = max(0.1, self.crossover_rate * 0.9)
    
    async def recursive_evolve(
        self,
        num_generations: int,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recursively evolve strategies for multiple generations.
        
        Each generation creates better strategies, which are used to create
        even better strategies in the next generation.
        """
        results = []
        
        for gen in range(num_generations):
            result = await self.evolve_generation(gen, market_data)
            results.append(result)
            
            # Check for convergence
            if self._has_converged():
                logger.info(f"Evolution converged at generation {gen}")
                break
        
        return {
            'generations_evolved': len(results),
            'final_best_fitness': results[-1]['best_fitness'] if results else 0,
            'total_strategies': len(self.strategies),
            'evolution_history': self.evolution_history
        }
    
    def _has_converged(self, window: int = 5, threshold: float = 0.01) -> bool:
        """Check if evolution has converged"""
        if len(self.evolution_history) < window:
            return False
        
        recent = self.evolution_history[-window:]
        fitness_values = [h['best_fitness'] for h in recent]
        
        # Check if fitness improvement is below threshold
        max_improvement = max(fitness_values[i] - fitness_values[i-1] 
                            for i in range(1, len(fitness_values)))
        
        return max_improvement < threshold
    
    def get_best_strategy(self) -> Optional[EvolvingStrategy]:
        """Get the best strategy across all generations"""
        if not self.strategies:
            return None
        
        return max(self.strategies.values(), key=lambda s: s.fitness_score)
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution process"""
        best = self.get_best_strategy()
        
        return {
            'total_strategies': len(self.strategies),
            'total_mutations': len(self.mutations),
            'generations_evolved': len(self.evolution_history),
            'best_strategy': {
                'id': best.strategy_id if best else None,
                'generation': best.generation.value if best else None,
                'fitness': best.fitness_score if best else 0,
                'parameters': best.parameters if best else {}
            },
            'current_mutation_rate': self.mutation_rate,
            'current_crossover_rate': self.crossover_rate,
            'evolution_history': self.evolution_history
        }
