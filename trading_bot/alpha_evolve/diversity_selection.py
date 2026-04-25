"""
Diversity-Aware Selection System
Implements diversity-preserving selection mechanisms to prevent premature convergence.
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import logging

from .evolution_engine import Individual
from .strategy_genome import StrategyGenome

logger = logging.getLogger(__name__)


@dataclass
class DiversityMetrics:
    """Metrics for population diversity"""
    phenotypic_diversity: float  # Based on fitness values
    genotypic_diversity: float   # Based on genome similarity
    behavioral_diversity: float # Based on trading patterns
    entropy: float              # Information entropy of population
    effective_population: float  # Effective population size


class DiversitySelector:
    """
    Diversity-aware selection that maintains population diversity.
    
    Uses multiple diversity metrics to ensure genetic variety
    and prevent premature convergence to local optima.
    """
    
    def __init__(self,
                 diversity_threshold: float = 0.3,
                 diversity_weight: float = 0.3,
                 calculate_diversity: Optional[Callable[[List[Individual]], float]] = None):
        """
        Initialize diversity selector.
        
        Args:
            diversity_threshold: Minimum acceptable diversity level
            diversity_weight: Weight given to diversity in selection (0-1)
            calculate_diversity: Optional custom diversity function
        """
        self.diversity_threshold = diversity_threshold
        self.diversity_weight = diversity_weight
        self.custom_diversity_fn = calculate_diversity
        
        # Selection history
        self.selection_history: List[Dict] = []
        
        logger.info(f"DiversitySelector initialized: threshold={diversity_threshold}, "
                   f"weight={diversity_weight}")
    
    def select_with_diversity(self,
                             population: List[Individual],
                             num_to_select: int) -> List[Individual]:
        """
        Select individuals balancing fitness and diversity.
        
        Uses multi-objective selection considering both fitness
        and contribution to population diversity.
        """
        if len(population) <= num_to_select:
            return population
        
        selected = []
        remaining = population.copy()
        
        # Calculate diversity metrics
        diversity_metrics = self._calculate_diversity_metrics(population)
        
        # If diversity is already low, prioritize it more
        if diversity_metrics.genotypic_diversity < self.diversity_threshold:
            effective_diversity_weight = self.diversity_weight * 1.5
        else:
            effective_diversity_weight = self.diversity_weight
        
        while len(selected) < num_to_select and remaining:
            # Calculate selection scores for remaining individuals
            scores = []
            
            for individual in remaining:
                # Fitness component
                fitness_score = individual.fitness.total_fitness if individual.fitness else 0.0
                
                # Diversity contribution component
                if selected:
                    diversity_contribution = self._diversity_contribution(individual, selected)
                else:
                    diversity_contribution = 1.0  # First individual contributes max diversity
                
                # Combined score
                combined_score = (
                    (1 - effective_diversity_weight) * fitness_score +
                    effective_diversity_weight * diversity_contribution
                )
                
                scores.append(combined_score)
            
            # Select individual with highest combined score
            if scores:
                best_idx = np.argmax(scores)
                selected.append(remaining.pop(best_idx))
        
        # Log selection
        self.selection_history.append({
            'num_selected': len(selected),
            'diversity_metrics': {
                'phenotypic': diversity_metrics.phenotypic_diversity,
                'genotypic': diversity_metrics.genotypic_diversity,
                'effective_pop': diversity_metrics.effective_population
            }
        })
        
        return selected
    
    def _diversity_contribution(self,
                               individual: Individual,
                               selected: List[Individual]) -> float:
        """
        Calculate how much diversity an individual contributes.
        
        Returns higher values for individuals that are genetically
        different from already selected individuals.
        """
        if not selected:
            return 1.0
        
        # Calculate average distance to selected individuals
        distances = []
        for selected_ind in selected:
            distance = self._genetic_distance(individual.genome, selected_ind.genome)
            distances.append(distance)
        
        avg_distance = np.mean(distances)
        
        # Normalize to 0-1 range (approximate)
        # Higher distance = more diverse = better
        return min(1.0, avg_distance / 5.0)  # Assume max meaningful distance is 5
    
    def _genetic_distance(self, genome1: StrategyGenome, genome2: StrategyGenome) -> float:
        """Calculate genetic distance between two genomes"""
        # Get signal types
        signals1 = {s.signal_type.value: s for s in genome1.signals}
        signals2 = {s.signal_type.value: s for s in genome2.signals}
        
        # Calculate distance based on signal differences
        all_types = set(signals1.keys()) | set(signals2.keys())
        if not all_types:
            return 0.0
        
        total_distance = 0.0
        
        for signal_type in all_types:
            if signal_type in signals1 and signal_type in signals2:
                s1 = signals1[signal_type]
                s2 = signals2[signal_type]
                
                # Weight difference
                weight_diff = abs(s1.weight - s2.weight)
                
                # Threshold difference (normalized)
                threshold_diff = abs(s1.threshold - s2.threshold)
                
                # Lookback difference (normalized)
                lookback_diff = abs(s1.lookback_period - s2.lookback_period) / 100.0
                
                total_distance += weight_diff + threshold_diff + lookback_diff
            else:
                # One has signal, other doesn't - large distance
                total_distance += 2.0
        
        # Add aggregation type difference
        if genome1.aggregation_type != genome2.aggregation_type:
            total_distance += 1.0
        
        # Add position sizing difference
        if genome1.position_sizing != genome2.position_sizing:
            total_distance += 1.0
        
        return total_distance / max(len(all_types), 1)
    
    def _calculate_diversity_metrics(self, population: List[Individual]) -> DiversityMetrics:
        """Calculate comprehensive diversity metrics"""
        if len(population) < 2:
            return DiversityMetrics(0, 0, 0, 0, len(population))
        
        # Phenotypic diversity (fitness variance)
        fitness_values = [ind.fitness.total_fitness for ind in population if ind.fitness]
        if fitness_values:
            phenotypic_diversity = np.std(fitness_values) / (np.mean(fitness_values) + 1e-10)
        else:
            phenotypic_diversity = 0.0
        
        # Genotypic diversity (average pairwise distance)
        total_distance = 0.0
        count = 0
        
        for i, ind1 in enumerate(population):
            for ind2 in population[i+1:]:
                distance = self._genetic_distance(ind1.genome, ind2.genome)
                total_distance += distance
                count += 1
        
        genotypic_diversity = total_distance / count if count > 0 else 0.0
        
        # Behavioral diversity (placeholder - would need trading history)
        behavioral_diversity = genotypic_diversity * 0.8  # Approximation
        
        # Entropy calculation (based on fitness distribution)
        if fitness_values:
            # Normalize fitness to probabilities
            total_fitness = sum(fitness_values)
            if total_fitness > 0:
                probs = np.array(fitness_values) / total_fitness
                probs = probs[probs > 0]  # Remove zeros for log
                entropy = -np.sum(probs * np.log(probs))
            else:
                entropy = 0.0
        else:
            entropy = 0.0
        
        # Effective population size (based on genotypic diversity)
        effective_population = len(population) * min(1.0, genotypic_diversity * 2)
        
        return DiversityMetrics(
            phenotypic_diversity=min(1.0, phenotypic_diversity),
            genotypic_diversity=min(1.0, genotypic_diversity),
            behavioral_diversity=min(1.0, behavioral_diversity),
            entropy=entropy,
            effective_population=effective_population
        )
    
    def is_diversity_critical(self, population: List[Individual]) -> bool:
        """Check if diversity has fallen below critical threshold"""
        metrics = self._calculate_diversity_metrics(population)
        return metrics.genotypic_diversity < self.diversity_threshold
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get statistics about selection process"""
        if not self.selection_history:
            return {}
        
        recent = self.selection_history[-10:]  # Last 10 selections
        
        return {
            'total_selections': len(self.selection_history),
            'avg_diversity_phenotypic': np.mean([r['diversity_metrics']['phenotypic'] for r in recent]),
            'avg_diversity_genotypic': np.mean([r['diversity_metrics']['genotypic'] for r in recent]),
            'avg_effective_population': np.mean([r['diversity_metrics']['effective_pop'] for r in recent])
        }


class AgeBasedSelector:
    """
    Selection mechanism that considers individual age to promote diversity.
    
    Prevents a few super-fit individuals from dominating the population
    by giving younger individuals a chance to prove themselves.
    """
    
    def __init__(self,
                 max_age: int = 20,
                 age_fitness_decay: float = 0.95,
                 min_selection_probability: float = 0.1):
        """
        Initialize age-based selector.
        
        Args:
            max_age: Maximum age before individual is removed
            age_fitness_decay: Factor by which fitness decays per generation
            min_selection_probability: Minimum selection probability
        """
        self.max_age = max_age
        self.age_fitness_decay = age_fitness_decay
        self.min_selection_probability = min_selection_probability
        
        logger.info(f"AgeBasedSelector initialized: max_age={max_age}, "
                   f"decay={age_fitness_decay}")
    
    def calculate_age_adjusted_fitness(self, individual: Individual) -> float:
        """
        Calculate fitness adjusted for age.
        
        Older individuals have their fitness decayed to make room
        for younger, potentially better solutions.
        """
        if not individual.fitness:
            return 0.0
        
        base_fitness = individual.fitness.total_fitness
        age = individual.generation  # Age in generations
        
        # Apply age decay
        adjusted_fitness = base_fitness * (self.age_fitness_decay ** age)
        
        # Ensure minimum probability
        if base_fitness > 0:
            adjusted_fitness = max(adjusted_fitness, base_fitness * self.min_selection_probability)
        
        return adjusted_fitness
    
    def select_survivors(self,
                         population: List[Individual],
                         num_survivors: int) -> List[Individual]:
        """
        Select survivors based on age-adjusted fitness.
        """
        if len(population) <= num_survivors:
            return population
        
        # Calculate age-adjusted fitness for all
        adjusted_fitness = [
            (ind, self.calculate_age_adjusted_fitness(ind))
            for ind in population
        ]
        
        # Sort by adjusted fitness (descending)
        adjusted_fitness.sort(key=lambda x: x[1], reverse=True)
        
        # Select top individuals
        survivors = [ind for ind, _ in adjusted_fitness[:num_survivors]]
        
        # Log age distribution
        ages = [ind.generation for ind in survivors]
        logger.debug(f"Survivor age distribution: mean={np.mean(ages):.1f}, "
                    f"max={max(ages)}, min={min(ages)}")
        
        return survivors
    
    def should_retire(self, individual: Individual) -> bool:
        """Check if individual should be retired due to age"""
        return individual.generation >= self.max_age
    
    def get_age_statistics(self, population: List[Individual]) -> Dict[str, Any]:
        """Get statistics about age distribution in population"""
        ages = [ind.generation for ind in population]
        
        return {
            'mean_age': np.mean(ages) if ages else 0,
            'max_age': max(ages) if ages else 0,
            'min_age': min(ages) if ages else 0,
            'std_age': np.std(ages) if ages else 0,
            'retirement_rate': sum(1 for a in ages if a >= self.max_age) / len(ages) if ages else 0
        }


class MultiObjectiveSelector:
    """
    Advanced multi-objective selection using Pareto frontier concepts.
    
    Maintains diversity by considering multiple objectives simultaneously
    rather than just a single fitness value.
    """
    
    def __init__(self,
                 objectives: Optional[List[str]] = None,
                 objective_weights: Optional[List[float]] = None):
        """
        Initialize multi-objective selector.
        
        Args:
            objectives: List of fitness metric names to optimize
            objective_weights: Weights for each objective
        """
        self.objectives = objectives or ['sharpe_ratio', 'max_drawdown', 'regime_stability']
        self.objective_weights = objective_weights or [0.5, 0.3, 0.2]
        
        if len(self.objectives) != len(self.objective_weights):
            raise ValueError("Number of objectives must match number of weights")
        
        # Normalize weights
        total = sum(self.objective_weights)
        self.objective_weights = [w / total for w in self.objective_weights]
        
        logger.info(f"MultiObjectiveSelector initialized: {len(self.objectives)} objectives")
    
    def dominates(self, ind1: Individual, ind2: Individual) -> bool:
        """
        Check if individual 1 dominates individual 2 in Pareto sense.
        
        Returns True if ind1 is at least as good in all objectives
        and strictly better in at least one objective.
        """
        if not ind1.fitness or not ind2.fitness:
            return False
        
        at_least_one_better = False
        
        for obj in self.objectives:
            val1 = getattr(ind1.fitness, obj, 0)
            val2 = getattr(ind2.fitness, obj, 0)
            
            # For metrics where lower is better (like drawdown)
            if obj == 'max_drawdown':
                if val1 > val2:
                    return False
                if val1 < val2:
                    at_least_one_better = True
            else:
                if val1 < val2:
                    return False
                if val1 > val2:
                    at_least_one_better = True
        
        return at_least_one_better
    
    def get_pareto_frontier(self, population: List[Individual]) -> List[Individual]:
        """Get non-dominated individuals (Pareto frontier)"""
        pareto_front = []
        
        for ind in population:
            dominated = False
            to_remove = []
            
            for p_ind in pareto_front:
                if self.dominates(p_ind, ind):
                    dominated = True
                    break
                if self.dominates(ind, p_ind):
                    to_remove.append(p_ind)
            
            if not dominated:
                pareto_front = [p for p in pareto_front if p not in to_remove]
                pareto_front.append(ind)
        
        return pareto_front
    
    def select_diverse_subset(self,
                             population: List[Individual],
                             num_to_select: int) -> List[Individual]:
        """
        Select diverse subset using Pareto frontier and crowding distance.
        """
        if len(population) <= num_to_select:
            return population
        
        # Get Pareto frontier
        pareto_front = self.get_pareto_frontier(population)
        
        selected = pareto_front.copy()
        
        # If Pareto front is smaller than needed, add others based on crowding distance
        if len(selected) < num_to_select:
            remaining = [ind for ind in population if ind not in selected]
            
            # Calculate crowding distance for remaining individuals
            crowding_distances = []
            for ind in remaining:
                distance = self._calculate_crowding_distance(ind, selected)
                crowding_distances.append((ind, distance))
            
            # Sort by crowding distance (descending) and add
            crowding_distances.sort(key=lambda x: x[1], reverse=True)
            
            needed = num_to_select - len(selected)
            selected.extend([ind for ind, _ in crowding_distances[:needed]])
        
        return selected[:num_to_select]
    
    def _calculate_crowding_distance(self,
                                  individual: Individual,
                                  reference_set: List[Individual]) -> float:
        """Calculate crowding distance to reference set"""
        if not reference_set:
            return float('inf')
        
        total_distance = 0.0
        
        for ref_ind in reference_set:
            if not individual.fitness or not ref_ind.fitness:
                continue
            
            # Sum of normalized differences across all objectives
            for obj in self.objectives:
                val1 = getattr(individual.fitness, obj, 0)
                val2 = getattr(ref_ind.fitness, obj, 0)
                total_distance += abs(val1 - val2)
        
        return total_distance / len(reference_set)
