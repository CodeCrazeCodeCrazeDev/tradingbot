"""
Speciated Evolution Engine
Implements speciation and diversity preservation for the evolutionary algorithm.
Prevents premature convergence by maintaining multiple species in the population.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from collections import defaultdict
import uuid

from .strategy_genome import StrategyGenome, SearchSpace
from .genetic_operators import GeneticOperators
from .backtesting_engine import LeakageFreeBacktester, BacktestResult
from .fitness_evaluator import MultiObjectiveFitness, FitnessScore
from .walk_forward import WalkForwardValidator, WalkForwardResult
from .evolution_engine import EvolutionEngine, Individual, GenerationStats

logger = logging.getLogger(__name__)


@dataclass
class Species:
    """Represents a species in the population"""
    species_id: str
    representative: Individual
    members: List[Individual] = field(default_factory=list)
    created_at: int = 0
    age: int = 0
    
    def get_average_fitness(self) -> float:
        """Calculate average fitness of species members"""
        if not self.members:
            return 0.0
        return np.mean([m.fitness.total_fitness for m in self.members if m.fitness])
    
    def get_best_fitness(self) -> float:
        """Get best fitness in species"""
        if not self.members:
            return 0.0
        fitness_values = [m.fitness.total_fitness for m in self.members if m.fitness]
        return max(fitness_values) if fitness_values else 0.0


@dataclass
class SpeciationConfig:
    """Configuration for speciation"""
    compatibility_threshold: float = 3.0
    excess_coefficient: float = 1.0
    disjoint_coefficient: float = 1.0
    weight_coefficient: float = 0.4
    target_species_count: int = 5
    min_species_size: int = 5
    max_species_age: int = 50
    stagnation_threshold: int = 15


class SpeciatedEvolutionEngine(EvolutionEngine):
    """
    Evolution engine with speciation support.
    
    Maintains multiple species to preserve diversity and prevent
    premature convergence to local optima.
    """
    
    def __init__(self, 
                 search_space: SearchSpace,
                 backtester: LeakageFreeBacktester,
                 fitness_evaluator: MultiObjectiveFitness,
                 genetic_operators: GeneticOperators,
                 config: Optional[Dict] = None):
        super().__init__(config=config, search_space=search_space, market_data=backtester.data)
        
        # Handle both dict and EvolutionConfig objects
        if isinstance(config, dict):
            speciation_dict = config.get('speciation', {}) if config else {}
        else:
            # EvolutionConfig object - extract speciation settings if they exist
            speciation_dict = getattr(config, 'speciation', {}) if config else {}
        
        self.speciation_config = SpeciationConfig(**speciation_dict)
        
        # Species management
        self.species: Dict[str, Species] = {}
        self.species_history: List[Dict] = []
        self.genome_to_species: Dict[str, str] = {}
        
        # Speciation statistics
        self.speciation_stats = {
            'species_count': [],
            'avg_species_size': [],
            'extinctions': 0
        }
        
        logger.info("SpeciatedEvolutionEngine initialized")
    
    def _speciate_population(self, population: List[Individual], generation: int) -> None:
        """
        Assign individuals to species based on compatibility.
        
        Uses NEAT-style compatibility distance calculation.
        """
        # Clear existing species members
        for species in self.species.values():
            species.members = []
            species.age += 1
        
        # Assign individuals to species
        for individual in population:
            assigned = False
            
            # Try to find compatible species
            for species_id, species in self.species.items():
                distance = self._compatibility_distance(
                    individual.genome,
                    species.representative.genome
                )
                
                if distance < self.speciation_config.compatibility_threshold:
                    species.members.append(individual)
                    self.genome_to_species[individual.get_id()] = species_id
                    assigned = True
                    break
            
            # Create new species if not compatible with any existing
            if not assigned:
                new_species_id = str(uuid.uuid4())
                new_species = Species(
                    species_id=new_species_id,
                    representative=individual,
                    members=[individual],
                    created_at=generation,
                    age=0
                )
                self.species[new_species_id] = new_species
                self.genome_to_species[individual.get_id()] = new_species_id
        
        # Remove empty species
        empty_species = [sid for sid, s in self.species.items() if not s.members]
        for sid in empty_species:
            del self.species[sid]
        
        # Update representatives
        self._update_representatives()
        
        logger.info(f"Generation {generation}: {len(self.species)} species formed")
    
    def _compatibility_distance(self, 
                              genome1: StrategyGenome, 
                              genome2: StrategyGenome) -> float:
        """
        Calculate compatibility distance between two genomes.
        
        Based on NEAT compatibility formula:
        distance = c1*E/N + c2*D/N + c3*W
        """
        signals1 = {s.signal_type.value: s for s in genome1.signals}
        signals2 = {s.signal_type.value: s for s in genome2.signals}
        
        # Count excess and disjoint genes
        all_types = set(signals1.keys()) | set(signals2.keys())
        matching = set(signals1.keys()) & set(signals2.keys())
        disjoint = (set(signals1.keys()) | set(signals2.keys())) - matching
        
        excess = len(disjoint)
        disjoint_count = len(disjoint)
        
        N = max(len(signals1), len(signals2), 1)
        
        # Calculate weight differences for matching genes
        weight_diff = 0.0
        for signal_type in matching:
            s1 = signals1[signal_type]
            s2 = signals2[signal_type]
            weight_diff += abs(s1.weight - s2.weight)
            weight_diff += abs(s1.threshold - s2.threshold) / 10.0
        
        if matching:
            weight_diff /= len(matching)
        
        # Compatibility distance
        distance = (
            self.speciation_config.excess_coefficient * excess / N +
            self.speciation_config.disjoint_coefficient * disjoint_count / N +
            self.speciation_config.weight_coefficient * weight_diff
        )
        
        return distance
    
    def _update_representatives(self) -> None:
        """Update species representatives to the most central member"""
        for species in self.species.values():
            if not species.members:
                continue
            
            # Find member with minimum average distance to other members
            min_avg_distance = float('inf')
            best_representative = species.members[0]
            
            for member in species.members:
                total_distance = sum(
                    self._compatibility_distance(member.genome, other.genome)
                    for other in species.members
                )
                avg_distance = total_distance / len(species.members)
                
                if avg_distance < min_avg_distance:
                    min_avg_distance = avg_distance
                    best_representative = member
            
            species.representative = best_representative
    
    def _calculate_offspring_counts(self, 
                                   population_size: int) -> Dict[str, int]:
        """
        Calculate how many offspring each species should produce.
        
        Based on shared fitness and species age.
        """
        if not self.species:
            return {}
        
        # Calculate adjusted fitness for each species
        species_fitness = {}
        for species_id, species in self.species.items():
            if not species.members:
                continue
            
            # Calculate shared fitness (average fitness of members)
            avg_fitness = species.get_average_fitness()
            
            # Penalize old species (stagnation)
            if species.age > self.speciation_config.stagnation_threshold:
                penalty = 0.5
            else:
                penalty = 1.0
            
            species_fitness[species_id] = avg_fitness * penalty
        
        # Calculate offspring counts
        total_fitness = sum(species_fitness.values())
        if total_fitness == 0:
            # Equal distribution
            offspring_counts = {sid: population_size // len(self.species) 
                              for sid in self.species}
        else:
            offspring_counts = {}
            for species_id, fitness in species_fitness.items():
                share = fitness / total_fitness
                offspring_counts[species_id] = max(
                    self.speciation_config.min_species_size,
                    int(share * population_size)
                )
        
        return offspring_counts
    
    def _select_parents_from_species(self, species: Species) -> Tuple[Individual, Individual]:
        """Select parents from within a species"""
        if len(species.members) < 2:
            # If only one member, use it twice
            if species.members:
                return species.members[0], species.members[0]
            else:
                raise ValueError("Empty species")
        
        # Tournament selection within species
        parent1 = self._tournament_select(species.members)
        parent2 = self._tournament_select(species.members)
        
        # Ensure different parents if possible
        if len(species.members) > 1 and parent1 == parent2:
            candidates = [m for m in species.members if m != parent1]
            parent2 = np.random.choice(candidates)
        
        return parent1, parent2
    
    def _tournament_select(self, 
                          individuals: List[Individual], 
                          tournament_size: int = 3) -> Individual:
        """Tournament selection within a group"""
        if len(individuals) <= tournament_size:
            candidates = individuals
        else:
            candidates = np.random.choice(individuals, tournament_size, replace=False)
        
        # Select best from tournament
        return max(candidates, key=lambda x: x.fitness.total_fitness if x.fitness else 0)
    
    def _remove_stagnant_species(self, generation: int) -> int:
        """Remove species that haven't improved for a long time"""
        removed = 0
        stagnant = []
        
        for species_id, species in self.species.items():
            # Check if species is too old and stagnant
            if (species.age > self.speciation_config.max_species_age and 
                not species.members):
                stagnant.append(species_id)
            elif (species.age > self.speciation_config.stagnation_threshold * 2 and
                  species.get_average_fitness() == 0):
                stagnant.append(species_id)
        
        for species_id in stagnant:
            del self.species[species_id]
            removed += 1
        
        if removed > 0:
            logger.info(f"Removed {removed} stagnant species")
        
        return removed
    
    def evolve_generation(self, 
                         generation: int, 
                         evaluator: Optional[Callable] = None) -> Tuple[List[Individual], GenerationStats]:
        """
        Evolve one generation with speciation.
        
        Overrides parent method to include speciation logic.
        """
        # Speciate population
        self._speciate_population(self.population, generation)
        
        # Remove stagnant species
        self._remove_stagnant_species(generation)
        
        # Calculate offspring counts per species
        offspring_counts = self._calculate_offspring_counts(self.population_size)
        
        # Generate new population
        new_population = []
        
        for species_id, count in offspring_counts.items():
            if species_id not in self.species:
                continue
            
            species = self.species[species_id]
            
            # Keep elite from species
            elite_count = max(1, int(count * self.elitism_rate))
            sorted_members = sorted(
                species.members,
                key=lambda x: x.fitness.total_fitness if x.fitness else 0,
                reverse=True
            )
            new_population.extend(sorted_members[:elite_count])
            
            # Generate offspring through crossover
            while len(new_population) < sum(offspring_counts.values()) and count > 0:
                try:
                    parent1, parent2 = self._select_parents_from_species(species)
                    
                    # Crossover
                    if np.random.random() < self.crossover_rate:
                        child_genome = self.genetic_operators.crossover(
                            parent1.genome, parent2.genome
                        )
                    else:
                        child_genome = parent1.genome.clone()
                    
                    # Mutation
                    if np.random.random() < self.mutation_rate:
                        child_genome = self.genetic_operators.mutate(child_genome)
                    
                    # Create individual
                    child = Individual(
                        genome=child_genome,
                        generation=generation
                    )
                    new_population.append(child)
                    count -= 1
                    
                except Exception as e:
                    logger.error(f"Error creating offspring: {e}")
                    break
        
        # Trim to exact population size
        new_population = new_population[:self.population_size]
        
        # Update population
        self.population = new_population
        
        # Generate statistics
        stats = self._generate_stats(generation)
        
        # Log speciation info
        logger.info(f"Generation {generation}: {len(self.species)} species, "
                   f"best fitness: {stats.best_fitness:.4f}")
        
        return self.population, stats
    
    def _generate_stats(self, generation: int) -> GenerationStats:
        """Generate statistics for current generation"""
        fitness_scores = [ind.fitness.total_fitness for ind in self.population if ind.fitness]
        
        if not fitness_scores:
            return GenerationStats(
                generation=generation,
                population_size=len(self.population),
                best_fitness=0.0,
                avg_fitness=0.0,
                worst_fitness=0.0,
                diversity=0.0
            )
        
        # Calculate diversity based on species count
        diversity = len(self.species) / self.speciation_config.target_species_count
        
        return GenerationStats(
            generation=generation,
            population_size=len(self.population),
            best_fitness=max(fitness_scores),
            avg_fitness=np.mean(fitness_scores),
            worst_fitness=min(fitness_scores),
            diversity=diversity
        )
    
    def get_species_info(self) -> Dict[str, Any]:
        """Get information about current species"""
        return {
            'species_count': len(self.species),
            'species_details': [
                {
                    'id': s.species_id,
                    'size': len(s.members),
                    'age': s.age,
                    'avg_fitness': s.get_average_fitness(),
                    'best_fitness': s.get_best_fitness()
                }
                for s in self.species.values()
            ],
            'total_population': len(self.population)
        }
