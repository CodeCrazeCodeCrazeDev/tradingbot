"""
Genetic Operators: Mutation, crossover, and recombination for strategy evolution.

Real operators that modify strategy genomes:
- Add/remove signals
- Alter parameters
- Swap model components
- Recombine strategies
"""

from typing import List, Tuple, Optional
import numpy as np
from copy import deepcopy

from .strategy_genome import (
    StrategyGenome, Signal, SearchSpace, SignalType,
    AggregationType, PositionSizingType, RiskControl
)


class GeneticOperators:
    """
    Implements genetic operators for strategy evolution.
    
    All operators maintain genome validity and respect search space constraints.
    """
    
    def __init__(self, search_space: SearchSpace, mutation_rate: float = 0.1):
        self.search_space = search_space
        self.mutation_rate = mutation_rate
        self.mutation_strength = 0.2
    
    def mutate(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Apply random mutations to a genome.
        
        Mutation types:
        - Add signal
        - Remove signal
        - Modify signal parameters
        - Change aggregation method
        - Adjust risk controls
        - Modify position sizing
        """
        mutated = genome.clone()
        mutation_applied = False
        mutations = []
        
        if np.random.random() < self.mutation_rate:
            mutated = self._add_signal(mutated)
            mutations.append('add_signal')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate and len(mutated.signals) > 1:
            mutated = self._remove_signal(mutated)
            mutations.append('remove_signal')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate * 2:
            mutated = self._mutate_signal_parameters(mutated)
            mutations.append('mutate_signal_params')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate:
            mutated = self._mutate_aggregation(mutated)
            mutations.append('mutate_aggregation')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate:
            mutated = self._mutate_position_sizing(mutated)
            mutations.append('mutate_position_sizing')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate:
            mutated = self._mutate_risk_controls(mutated)
            mutations.append('mutate_risk_controls')
            mutation_applied = True
        
        if np.random.random() < self.mutation_rate:
            mutated = self._mutate_rebalance_frequency(mutated)
            mutations.append('mutate_rebalance_freq')
            mutation_applied = True
        
        if mutation_applied:
            mutated.metadata['generation'] = genome.metadata.get('generation', 0) + 1
            mutated.metadata['parent_ids'] = [genome.get_genome_id()]
            mutated.metadata['mutation_history'].append(mutations)
        
        mutated = self.search_space.clip_to_bounds(mutated)
        return mutated
    
    def _add_signal(self, genome: StrategyGenome) -> StrategyGenome:
        """Add a new random signal to the genome"""
        if len(genome.signals) < self.search_space.max_signals:
            new_signal = self.search_space.random_signal()
            genome.signals.append(new_signal)
        return genome
    
    def _remove_signal(self, genome: StrategyGenome) -> StrategyGenome:
        """Remove a random signal from the genome"""
        if len(genome.signals) > self.search_space.min_signals:
            idx = np.random.randint(len(genome.signals))
            genome.signals.pop(idx)
        return genome
    
    def _mutate_signal_parameters(self, genome: StrategyGenome) -> StrategyGenome:
        """Mutate parameters of a random signal"""
        if not genome.signals:
            return genome
        
        idx = np.random.randint(len(genome.signals))
        signal = genome.signals[idx]
        
        mutation_type = np.random.choice([
            'lookback', 'threshold', 'weight', 'type', 'all_params'
        ])
        
        if mutation_type == 'lookback':
            delta = int(np.random.normal(0, 20))
            signal.lookback_period = max(
                self.search_space.lookback_range[0],
                min(self.search_space.lookback_range[1], signal.lookback_period + delta)
            )
        
        elif mutation_type == 'threshold':
            delta = np.random.normal(0, 0.5)
            signal.threshold = np.clip(
                signal.threshold + delta,
                *self.search_space.threshold_range
            )
        
        elif mutation_type == 'weight':
            delta = np.random.normal(0, 0.2)
            signal.weight = np.clip(
                signal.weight + delta,
                *self.search_space.weight_range
            )
        
        elif mutation_type == 'type':
            signal.signal_type = np.random.choice(self.search_space.signal_types)
        
        elif mutation_type == 'all_params':
            for key in signal.parameters:
                if isinstance(signal.parameters[key], (int, float)):
                    signal.parameters[key] *= np.random.uniform(0.8, 1.2)
        
        return genome
    
    def _mutate_aggregation(self, genome: StrategyGenome) -> StrategyGenome:
        """Change the signal aggregation method"""
        genome.aggregation_type = np.random.choice(self.search_space.aggregation_types)
        return genome
    
    def _mutate_position_sizing(self, genome: StrategyGenome) -> StrategyGenome:
        """Change the position sizing method"""
        genome.position_sizing = np.random.choice(self.search_space.position_sizing_types)
        return genome
    
    def _mutate_risk_controls(self, genome: StrategyGenome) -> StrategyGenome:
        """Mutate risk control parameters"""
        rc = genome.risk_control
        
        param = np.random.choice([
            'max_position_size', 'max_leverage', 'stop_loss_pct', 
            'take_profit_pct', 'max_drawdown_limit'
        ])
        
        if param == 'max_position_size':
            rc.max_position_size *= np.random.uniform(0.8, 1.2)
            rc.max_position_size = np.clip(rc.max_position_size, *self.search_space.position_size_range)
        
        elif param == 'max_leverage':
            rc.max_leverage *= np.random.uniform(0.9, 1.1)
            rc.max_leverage = np.clip(rc.max_leverage, *self.search_space.leverage_range)
        
        elif param == 'stop_loss_pct':
            rc.stop_loss_pct *= np.random.uniform(0.8, 1.2)
            rc.stop_loss_pct = np.clip(rc.stop_loss_pct, *self.search_space.stop_loss_range)
        
        elif param == 'take_profit_pct':
            rc.take_profit_pct *= np.random.uniform(0.8, 1.2)
            rc.take_profit_pct = np.clip(rc.take_profit_pct, *self.search_space.take_profit_range)
        
        elif param == 'max_drawdown_limit':
            rc.max_drawdown_limit *= np.random.uniform(0.9, 1.1)
            rc.max_drawdown_limit = np.clip(rc.max_drawdown_limit, 0.05, 0.30)
        
        return genome
    
    def _mutate_rebalance_frequency(self, genome: StrategyGenome) -> StrategyGenome:
        """Mutate rebalancing frequency"""
        delta = np.random.choice([-1, 1]) * np.random.randint(1, 5)
        genome.rebalance_frequency = np.clip(
            genome.rebalance_frequency + delta,
            *self.search_space.rebalance_freq_range
        )
        return genome
    
    def crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """
        Perform crossover between two parent genomes.
        
        Creates two offspring by recombining parent genes.
        Uses multiple crossover strategies:
        - Signal crossover
        - Parameter crossover
        - Component swapping
        """
        offspring1 = parent1.clone()
        offspring2 = parent2.clone()
        
        crossover_type = np.random.choice(['signal', 'parameter', 'component'])
        
        if crossover_type == 'signal':
            offspring1, offspring2 = self._signal_crossover(parent1, parent2)
        
        elif crossover_type == 'parameter':
            offspring1, offspring2 = self._parameter_crossover(parent1, parent2)
        
        elif crossover_type == 'component':
            offspring1, offspring2 = self._component_crossover(parent1, parent2)
        
        offspring1.metadata['generation'] = max(
            parent1.metadata.get('generation', 0),
            parent2.metadata.get('generation', 0)
        ) + 1
        offspring2.metadata['generation'] = offspring1.metadata['generation']
        
        offspring1.metadata['parent_ids'] = [parent1.get_genome_id(), parent2.get_genome_id()]
        offspring2.metadata['parent_ids'] = [parent1.get_genome_id(), parent2.get_genome_id()]
        
        offspring1 = self.search_space.clip_to_bounds(offspring1)
        offspring2 = self.search_space.clip_to_bounds(offspring2)
        
        return offspring1, offspring2
    
    def _signal_crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """Crossover at signal level - exchange signals between parents"""
        offspring1 = parent1.clone()
        offspring2 = parent2.clone()
        
        if len(parent1.signals) > 0 and len(parent2.signals) > 0:
            crossover_point = np.random.randint(1, min(len(parent1.signals), len(parent2.signals)))
            
            offspring1.signals = parent1.signals[:crossover_point] + parent2.signals[crossover_point:]
            offspring2.signals = parent2.signals[:crossover_point] + parent1.signals[crossover_point:]
            
            if len(offspring1.signals) > self.search_space.max_signals:
                offspring1.signals = offspring1.signals[:self.search_space.max_signals]
            if len(offspring2.signals) > self.search_space.max_signals:
                offspring2.signals = offspring2.signals[:self.search_space.max_signals]
        
        return offspring1, offspring2
    
    def _parameter_crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """Crossover at parameter level - blend parameters"""
        offspring1 = parent1.clone()
        offspring2 = parent2.clone()
        
        alpha = np.random.uniform(0.3, 0.7)
        
        for i in range(min(len(offspring1.signals), len(offspring2.signals))):
            s1, s2 = offspring1.signals[i], offspring2.signals[i]
            
            new_lookback1 = int(alpha * s1.lookback_period + (1 - alpha) * s2.lookback_period)
            new_lookback2 = int((1 - alpha) * s1.lookback_period + alpha * s2.lookback_period)
            
            new_threshold1 = alpha * s1.threshold + (1 - alpha) * s2.threshold
            new_threshold2 = (1 - alpha) * s1.threshold + alpha * s2.threshold
            
            new_weight1 = alpha * s1.weight + (1 - alpha) * s2.weight
            new_weight2 = (1 - alpha) * s1.weight + alpha * s2.weight
            
            offspring1.signals[i].lookback_period = new_lookback1
            offspring1.signals[i].threshold = new_threshold1
            offspring1.signals[i].weight = new_weight1
            
            offspring2.signals[i].lookback_period = new_lookback2
            offspring2.signals[i].threshold = new_threshold2
            offspring2.signals[i].weight = new_weight2
        
        return offspring1, offspring2
    
    def _component_crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """Crossover at component level - swap major components"""
        offspring1 = parent1.clone()
        offspring2 = parent2.clone()
        
        if np.random.random() < 0.5:
            offspring1.aggregation_type, offspring2.aggregation_type = \
                offspring2.aggregation_type, offspring1.aggregation_type
        
        if np.random.random() < 0.5:
            offspring1.position_sizing, offspring2.position_sizing = \
                offspring2.position_sizing, offspring1.position_sizing
        
        if np.random.random() < 0.5:
            offspring1.risk_control, offspring2.risk_control = \
                deepcopy(offspring2.risk_control), deepcopy(offspring1.risk_control)
        
        return offspring1, offspring2
    
    def tournament_selection(
        self, 
        population: List[Tuple[StrategyGenome, float]], 
        tournament_size: int = 3
    ) -> StrategyGenome:
        """
        Select a genome using tournament selection.
        
        Args:
            population: List of (genome, fitness) tuples
            tournament_size: Number of individuals in tournament
        
        Returns:
            Selected genome
        """
        tournament = np.random.choice(len(population), size=tournament_size, replace=False)
        tournament_individuals = [population[i] for i in tournament]
        
        winner = max(tournament_individuals, key=lambda x: x[1])
        return winner[0]
    
    def elitism_selection(
        self,
        population: List[Tuple[StrategyGenome, float]],
        elite_size: int
    ) -> List[StrategyGenome]:
        """
        Select top performing genomes (elitism).
        
        Args:
            population: List of (genome, fitness) tuples
            elite_size: Number of elite individuals to select
        
        Returns:
            List of elite genomes
        """
        sorted_pop = sorted(population, key=lambda x: x[1], reverse=True)
        return [genome for genome, _ in sorted_pop[:elite_size]]
    
    def diversity_selection(
        self,
        population: List[Tuple[StrategyGenome, float]],
        num_select: int
    ) -> List[StrategyGenome]:
        """
        Select diverse genomes to maintain population diversity.
        
        Uses genome complexity and signal type diversity as metrics.
        """
        selected = []
        remaining = list(population)
        
        if remaining:
            best = max(remaining, key=lambda x: x[1])
            selected.append(best[0])
            remaining.remove(best)
        
        while len(selected) < num_select and remaining:
            max_diversity = -1
            most_diverse = None
            
            for genome, fitness in remaining:
                diversity = self._calculate_diversity(genome, selected)
                diversity_score = diversity * (1 + 0.1 * fitness)
                
                if diversity_score > max_diversity:
                    max_diversity = diversity_score
                    most_diverse = (genome, fitness)
            
            if most_diverse:
                selected.append(most_diverse[0])
                remaining.remove(most_diverse)
            else:
                break
        
        return selected
    
    def _calculate_diversity(self, genome: StrategyGenome, population: List[StrategyGenome]) -> float:
        """Calculate how diverse a genome is from a population"""
        if not population:
            return 1.0
        
        diversities = []
        for other in population:
            signal_type_diff = len(set(s.signal_type for s in genome.signals) - 
                                   set(s.signal_type for s in other.signals))
            
            complexity_diff = abs(genome.get_complexity() - other.get_complexity())
            
            component_diff = (
                (genome.aggregation_type != other.aggregation_type) +
                (genome.position_sizing != other.position_sizing)
            )
            
            diversity = signal_type_diff + 0.1 * complexity_diff + 5 * component_diff
            diversities.append(diversity)
        
        return np.mean(diversities)
