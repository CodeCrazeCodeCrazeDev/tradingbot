"""
Strategy Evolution Engine for AAMIS V3 Extended

Advanced genetic programming-based strategy evolution with:
- Gene-based strategy representation
- Crossover and mutation operations
- Fitness evaluation with multi-objective optimization
- Population diversity maintenance
- Strategy genealogy tracking
"""

import asyncio
import numpy as np
import random
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import uuid
import hashlib

logger = logging.getLogger(__name__)


class StrategyGeneType(Enum):
    """Types of strategy genes."""
    ENTRY_CONDITION = "entry_condition"
    EXIT_CONDITION = "exit_condition"
    POSITION_SIZING = "position_sizing"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIME_FILTER = "time_filter"
    INDICATOR_PARAM = "indicator_param"
    RISK_FILTER = "risk_filter"


class GeneValueType(Enum):
    """Value types for genes."""
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    THRESHOLD = "threshold"
    TIMEFRAME = "timeframe"


@dataclass
class StrategyGene:
    """A single gene in the strategy genome."""
    gene_id: str
    gene_type: StrategyGeneType
    value_type: GeneValueType
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[Any]] = None
    mutation_rate: float = 0.1
    description: str = ""
    
    def mutate(self, strength: float = 1.0) -> 'StrategyGene':
        """Create mutated version of this gene."""
        if random.random() > self.mutation_rate * strength:
            return self  # No mutation
        
        new_value = self.value
        
        if self.value_type == GeneValueType.FLOAT:
            if self.min_value is not None and self.max_value is not None:
                range_val = (self.max_value - self.min_value) * strength * 0.1
                new_value = self.value + random.uniform(-range_val, range_val)
                new_value = max(self.min_value, min(self.max_value, new_value))
        
        elif self.value_type == GeneValueType.INTEGER:
            if self.min_value is not None and self.max_value is not None:
                delta = int((self.max_value - self.min_value) * strength * 0.1)
                delta = max(1, delta)
                new_value = self.value + random.randint(-delta, delta)
                new_value = int(max(self.min_value, min(self.max_value, new_value)))
        
        elif self.value_type == GeneValueType.BOOLEAN:
            if random.random() < 0.1 * strength:
                new_value = not self.value
        
        elif self.value_type == GeneValueType.CHOICE and self.choices:
            if random.random() < 0.2 * strength:
                new_value = random.choice(self.choices)
        
        elif self.value_type == GeneValueType.THRESHOLD:
            # Thresholds mutate more carefully
            if random.random() < 0.1 * strength:
                new_value = self.value * random.uniform(0.9, 1.1)
        
        return StrategyGene(
            gene_id=f"GENE-{uuid.uuid4().hex[:8]}",
            gene_type=self.gene_type,
            value_type=self.value_type,
            value=new_value,
            min_value=self.min_value,
            max_value=self.max_value,
            choices=self.choices,
            mutation_rate=self.mutation_rate,
            description=self.description,
        )
    
    def crossover(self, other: 'StrategyGene', crossover_point: float = 0.5) -> 'StrategyGene':
        """Create child gene from crossover with another gene."""
        if self.gene_type != other.gene_type:
            raise ValueError("Cannot crossover genes of different types")
        
        # Choose value based on crossover point
        if random.random() < crossover_point:
            new_value = self.value
        else:
            new_value = other.value
        
        # Average the mutation rates
        new_mutation_rate = (self.mutation_rate + other.mutation_rate) / 2
        
        return StrategyGene(
            gene_id=f"GENE-{uuid.uuid4().hex[:8]}",
            gene_type=self.gene_type,
            value_type=self.value_type,
            value=new_value,
            min_value=self.min_value,
            max_value=self.max_value,
            choices=self.choices,
            mutation_rate=new_mutation_rate,
            description=self.description,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gene to dictionary."""
        return {
            'gene_id': self.gene_id,
            'gene_type': self.gene_type.value,
            'value_type': self.value_type.value,
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'choices': self.choices,
            'mutation_rate': self.mutation_rate,
            'description': self.description,
        }


@dataclass
class StrategyGenome:
    """Complete genome representing a trading strategy."""
    genome_id: str
    genes: Dict[StrategyGeneType, List[StrategyGene]]
    generation: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parent_ids: List[str] = field(default_factory=list)
    
    # Fitness metrics
    fitness: Dict[str, float] = field(default_factory=dict)
    rank: Optional[int] = None
    
    # Performance history
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    live_results: Dict[str, Any] = field(default_factory=dict)
    
    def get_gene_hash(self) -> str:
        """Generate hash of all gene values for identity."""
        gene_values = []
        for gene_type in sorted(self.genes.keys(), key=lambda x: x.value):
            for gene in sorted(self.genes[gene_type], key=lambda x: x.gene_id):
                gene_values.append(f"{gene_type.value}:{gene.value}")
        
        gene_str = "|".join(gene_values)
        return hashlib.md5(gene_str.encode()).hexdigest()[:16]
    
    def mutate(self, mutation_strength: float = 1.0) -> 'StrategyGenome':
        """Create mutated version of this genome."""
        new_genes = {}
        for gene_type, genes in self.genes.items():
            new_genes[gene_type] = [gene.mutate(mutation_strength) for gene in genes]
        
        return StrategyGenome(
            genome_id=f"GENOME-{uuid.uuid4().hex[:12]}",
            genes=new_genes,
            generation=self.generation + 1,
            parent_ids=[self.genome_id],
            fitness={},  # Reset fitness - needs re-evaluation
        )
    
    def crossover(self, other: 'StrategyGenome', crossover_rate: float = 0.5) -> 'StrategyGenome':
        """Create child genome from crossover with another genome."""
        new_genes = {}
        
        # Combine gene types from both parents
        all_types = set(self.genes.keys()) | set(other.genes.keys())
        
        for gene_type in all_types:
            self_genes = self.genes.get(gene_type, [])
            other_genes = other.genes.get(gene_type, [])
            
            # Match genes by position
            max_len = max(len(self_genes), len(other_genes))
            new_genes_list = []
            
            for i in range(max_len):
                if i < len(self_genes) and i < len(other_genes):
                    # Crossover between matching genes
                    if random.random() < crossover_rate:
                        new_gene = self_genes[i].crossover(other_genes[i])
                    else:
                        new_gene = self_genes[i] if random.random() < 0.5 else other_genes[i]
                elif i < len(self_genes):
                    new_gene = self_genes[i]
                else:
                    new_gene = other_genes[i]
                
                new_genes_list.append(new_gene)
            
            new_genes[gene_type] = new_genes_list
        
        return StrategyGenome(
            genome_id=f"GENOME-{uuid.uuid4().hex[:12]}",
            genes=new_genes,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.genome_id, other.genome_id],
            fitness={},
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert genome to dictionary."""
        return {
            'genome_id': self.genome_id,
            'genome_hash': self.get_gene_hash(),
            'generation': self.generation,
            'genes': {
                gt.value: [g.to_dict() for g in genes]
                for gt, genes in self.genes.items()
            },
            'created_at': self.created_at.isoformat(),
            'parent_ids': self.parent_ids,
            'fitness': self.fitness,
            'rank': self.rank,
        }


@dataclass
class FitnessEvaluation:
    """Multi-objective fitness evaluation."""
    genome_id: str
    metrics: Dict[str, float]
    objectives: Dict[str, float]
    
    # Normalized scores
    sharpe_score: float
    return_score: float
    drawdown_score: float
    consistency_score: float
    robustness_score: float
    
    # Overall fitness (weighted combination)
    overall_fitness: float
    
    # Pareto dominance info
    dominated_by_count: int = 0
    dominates: List[str] = field(default_factory=list)
    
    def dominates_other(self, other: 'FitnessEvaluation') -> bool:
        """Check if this evaluation dominates another (Pareto dominance)."""
        # Check if this is at least as good on all objectives
        at_least_as_good = (
            self.sharpe_score >= other.sharpe_score and
            self.return_score >= other.return_score and
            self.drawdown_score >= other.drawdown_score and
            self.consistency_score >= other.consistency_score and
            self.robustness_score >= other.robustness_score
        )
        
        # Check if this is strictly better on at least one objective
        strictly_better = (
            self.sharpe_score > other.sharpe_score or
            self.return_score > other.return_score or
            self.drawdown_score > other.drawdown_score or
            self.consistency_score > other.consistency_score or
            self.robustness_score > other.robustness_score
        )
        
        return at_least_as_good and strictly_better


class StrategyEvolutionEngine:
    """
    Evolutionary engine for trading strategy optimization.
    
    Features:
    - Genetic programming with gene-based representation
    - Multi-objective optimization (Sharpe, return, drawdown, etc.)
    - Pareto frontier maintenance
    - Population diversity management
    - Genealogy tracking
    - Adaptive mutation rates
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'strategy_evolution'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Population parameters
        self.population_size = self.config.get('population_size', 50)
        self.elite_size = self.config.get('elite_size', 5)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        self.tournament_size = self.config.get('tournament_size', 3)
        
        # Population and history
        self._population: List[StrategyGenome] = []
        self._pareto_front: List[StrategyGenome] = []
        self._genealogy: Dict[str, Dict] = {}  # genome_id -> genealogy info
        self._generation = 0
        
        # Fitness function
        self._fitness_evaluator: Optional[Callable] = None
        
        # Statistics
        self._evolution_history: List[Dict] = []
        
        logger.info(f"✅ Strategy Evolution Engine initialized (pop={self.population_size})")
    
    def initialize_population(self, seed_genomes: Optional[List[StrategyGenome]] = None):
        """Initialize the population with seed genomes or random genomes."""
        if seed_genomes:
            self._population = seed_genomes[:self.population_size]
            
            # Fill remaining with mutations of seeds
            while len(self._population) < self.population_size:
                parent = random.choice(seed_genomes)
                child = parent.mutate(mutation_strength=0.5)
                self._population.append(child)
        else:
            self._population = self._create_random_population()
        
        logger.info(f"Initialized population with {len(self._population)} genomes")
    
    def _create_random_population(self) -> List[StrategyGenome]:
        """Create random initial population."""
        population = []
        
        for i in range(self.population_size):
            genome = self._create_random_genome()
            population.append(genome)
        
        return population
    
    def _create_random_genome(self) -> StrategyGenome:
        """Create a random strategy genome."""
        genes = {}
        
        # Entry condition genes
        genes[StrategyGeneType.ENTRY_CONDITION] = [
            StrategyGene(
                gene_id=f"ENTRY-{i}",
                gene_type=StrategyGeneType.ENTRY_CONDITION,
                value_type=GeneValueType.CHOICE,
                value=random.choice(['momentum', 'mean_reversion', 'breakout', 'trend_following']),
                choices=['momentum', 'mean_reversion', 'breakout', 'trend_following'],
                description="Entry strategy type",
            ),
            StrategyGene(
                gene_id="ENTRY-THRESH",
                gene_type=StrategyGeneType.ENTRY_CONDITION,
                value_type=GeneValueType.THRESHOLD,
                value=random.uniform(0.001, 0.05),
                min_value=0.0001,
                max_value=0.1,
                description="Entry threshold",
            ),
        ]
        
        # Exit condition genes
        genes[StrategyGeneType.EXIT_CONDITION] = [
            StrategyGene(
                gene_id="EXIT-TYPE",
                gene_type=StrategyGeneType.EXIT_CONDITION,
                value_type=GeneValueType.CHOICE,
                value=random.choice(['time_based', 'target_based', 'signal_based']),
                choices=['time_based', 'target_based', 'signal_based'],
            ),
        ]
        
        # Position sizing genes
        genes[StrategyGeneType.POSITION_SIZING] = [
            StrategyGene(
                gene_id="POS-METHOD",
                gene_type=StrategyGeneType.POSITION_SIZING,
                value_type=GeneValueType.CHOICE,
                value=random.choice(['fixed', 'kelly', 'percent_risk', 'volatility_adjusted']),
                choices=['fixed', 'kelly', 'percent_risk', 'volatility_adjusted'],
            ),
            StrategyGene(
                gene_id="POS-SIZE",
                gene_type=StrategyGeneType.POSITION_SIZING,
                value_type=GeneValueType.FLOAT,
                value=random.uniform(0.01, 0.5),
                min_value=0.01,
                max_value=1.0,
                description="Position size fraction",
            ),
        ]
        
        # Stop loss genes
        genes[StrategyGeneType.STOP_LOSS] = [
            StrategyGene(
                gene_id="SL-PCT",
                gene_type=StrategyGeneType.STOP_LOSS,
                value_type=GeneValueType.FLOAT,
                value=random.uniform(0.01, 0.10),
                min_value=0.005,
                max_value=0.20,
                description="Stop loss percentage",
            ),
        ]
        
        # Take profit genes
        genes[StrategyGeneType.TAKE_PROFIT] = [
            StrategyGene(
                gene_id="TP-PCT",
                gene_type=StrategyGeneType.TAKE_PROFIT,
                value_type=GeneValueType.FLOAT,
                value=random.uniform(0.02, 0.20),
                min_value=0.01,
                max_value=0.50,
                description="Take profit percentage",
            ),
            StrategyGene(
                gene_id="TP-RATIO",
                gene_type=StrategyGeneType.TAKE_PROFIT,
                value_type=GeneValueType.FLOAT,
                value=random.uniform(1.5, 3.0),
                min_value=1.0,
                max_value=5.0,
                description="Risk/reward ratio",
            ),
        ]
        
        # Time filter genes
        genes[StrategyGeneType.TIME_FILTER] = [
            StrategyGene(
                gene_id="TF-ENABLED",
                gene_type=StrategyGeneType.TIME_FILTER,
                value_type=GeneValueType.BOOLEAN,
                value=random.choice([True, False]),
            ),
            StrategyGene(
                gene_id="TF-HOUR-START",
                gene_type=StrategyGeneType.TIME_FILTER,
                value_type=GeneValueType.INTEGER,
                value=random.randint(9, 14),
                min_value=0,
                max_value=23,
            ),
            StrategyGene(
                gene_id="TF-HOUR-END",
                gene_type=StrategyGeneType.TIME_FILTER,
                value_type=GeneValueType.INTEGER,
                value=random.randint(15, 20),
                min_value=0,
                max_value=23,
            ),
        ]
        
        return StrategyGenome(
            genome_id=f"GENOME-{uuid.uuid4().hex[:12]}",
            genes=genes,
            generation=0,
        )
    
    async def evolve_generation(self, fitness_evaluator: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Evolve one generation.
        
        Args:
            fitness_evaluator: Function to evaluate fitness
        
        Returns:
            Generation statistics
        """
        if fitness_evaluator:
            self._fitness_evaluator = fitness_evaluator
        
        # Evaluate fitness of all genomes
        logger.info(f"Evaluating fitness for generation {self._generation}")
        fitness_scores = await self._evaluate_population()
        
        # Update Pareto front
        self._update_pareto_front(fitness_scores)
        
        # Assign ranks based on Pareto dominance
        self._assign_pareto_ranks(fitness_scores)
        
        # Select parents
        parents = self._select_parents(fitness_scores)
        
        # Create offspring
        offspring = self._create_offspring(parents)
        
        # Elite preservation
        elite = self._select_elite(fitness_scores)
        
        # Form new population
        self._population = elite + offspring[:self.population_size - len(elite)]
        
        # Collect statistics
        stats = self._collect_generation_stats(fitness_scores)
        self._evolution_history.append(stats)
        
        self._generation += 1
        
        logger.info(f"Generation {self._generation} complete: best_fitness={stats['best_fitness']:.4f}, "
                   f"pareto_size={len(self._pareto_front)}")
        
        return stats
    
    async def _evaluate_population(self) -> Dict[str, FitnessEvaluation]:
        """Evaluate fitness for entire population."""
        fitness_scores = {}
        
        for genome in self._population:
            if self._fitness_evaluator:
                fitness = await self._fitness_evaluator(genome)
            else:
                fitness = self._default_fitness_evaluation(genome)
            
            fitness_scores[genome.genome_id] = fitness
            genome.fitness = fitness.metrics
        
        return fitness_scores
    
    def _default_fitness_evaluation(self, genome: StrategyGenome) -> FitnessEvaluation:
        """Default fitness evaluation (placeholder)."""
        # This would normally run backtests
        # For now, generate random but correlated scores
        base_score = random.uniform(0.3, 0.9)
        
        return FitnessEvaluation(
            genome_id=genome.genome_id,
            metrics={
                'sharpe': base_score * 2,
                'total_return': base_score * 0.5,
                'max_drawdown': (1 - base_score) * 0.2,
                'win_rate': base_score * 0.8,
            },
            objectives={
                'sharpe': base_score * 2,
                'return': base_score * 0.5,
                'drawdown': -(1 - base_score) * 0.2,  # Minimize drawdown
            },
            sharpe_score=base_score * 2,
            return_score=base_score * 0.5,
            drawdown_score=1 - (1 - base_score) * 0.2,
            consistency_score=base_score * 0.9,
            robustness_score=base_score * 0.85,
            overall_fitness=base_score,
        )
    
    def _update_pareto_front(self, fitness_scores: Dict[str, FitnessEvaluation]):
        """Update Pareto front with non-dominated solutions."""
        # Clear current front
        self._pareto_front = []
        
        # Find non-dominated solutions
        evaluations = list(fitness_scores.values())
        
        for i, eval_i in enumerate(evaluations):
            dominated = False
            
            for j, eval_j in enumerate(evaluations):
                if i != j and eval_j.dominates_other(eval_i):
                    dominated = True
                    eval_i.dominated_by_count += 1
                    eval_j.dominates.append(eval_i.genome_id)
                    break
            
            if not dominated:
                # Find genome
                for genome in self._population:
                    if genome.genome_id == eval_i.genome_id:
                        self._pareto_front.append(genome)
                        break
    
    def _assign_pareto_ranks(self, fitness_scores: Dict[str, FitnessEvaluation]):
        """Assign ranks to genomes based on Pareto dominance."""
        # Rank 1 = Pareto front
        # Higher ranks = more dominated
        for genome in self._population:
            fitness = fitness_scores.get(genome.genome_id)
            if fitness:
                genome.rank = fitness.dominated_by_count + 1
    
    def _select_parents(self, fitness_scores: Dict[str, FitnessEvaluation]) -> List[StrategyGenome]:
        """Select parents using tournament selection."""
        parents = []
        
        while len(parents) < self.population_size:
            # Tournament selection
            tournament = random.sample(self._population, min(self.tournament_size, len(self._population)))
            
            # Select best in tournament (lowest rank, then highest fitness)
            best = min(tournament, key=lambda g: (
                g.rank if g.rank is not None else 999,
                -fitness_scores.get(g.genome_id, FitnessEvaluation(
                    genome_id=g.genome_id, metrics={}, objectives={},
                    sharpe_score=0, return_score=0, drawdown_score=0,
                    consistency_score=0, robustness_score=0, overall_fitness=0
                )).overall_fitness
            ))
            
            parents.append(best)
        
        return parents
    
    def _create_offspring(self, parents: List[StrategyGenome]) -> List[StrategyGenome]:
        """Create offspring through crossover and mutation."""
        offspring = []
        
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i + 1] if i + 1 < len(parents) else parents[0]
            
            # Crossover
            if random.random() < self.crossover_rate:
                child1 = parent1.crossover(parent2)
                child2 = parent2.crossover(parent1)
            else:
                child1 = parent1.mutate(mutation_strength=0.1)
                child2 = parent2.mutate(mutation_strength=0.1)
            
            # Mutation
            child1 = child1.mutate(mutation_strength=self.mutation_rate)
            child2 = child2.mutate(mutation_strength=self.mutation_rate)
            
            offspring.extend([child1, child2])
        
        return offspring
    
    def _select_elite(self, fitness_scores: Dict[str, FitnessEvaluation]) -> List[StrategyGenome]:
        """Select elite genomes to preserve."""
        # Sort by rank and fitness
        sorted_pop = sorted(
            self._population,
            key=lambda g: (
                g.rank if g.rank is not None else 999,
                -fitness_scores.get(g.genome_id, FitnessEvaluation(
                    genome_id=g.genome_id, metrics={}, objectives={},
                    sharpe_score=0, return_score=0, drawdown_score=0,
                    consistency_score=0, robustness_score=0, overall_fitness=0
                )).overall_fitness
            )
        )
        
        return sorted_pop[:self.elite_size]
    
    def _collect_generation_stats(self, fitness_scores: Dict[str, FitnessEvaluation]) -> Dict[str, Any]:
        """Collect statistics about the generation."""
        scores = [f.overall_fitness for f in fitness_scores.values()]
        
        return {
            'generation': self._generation,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'population_size': len(self._population),
            'pareto_front_size': len(self._pareto_front),
            'best_fitness': max(scores) if scores else 0,
            'worst_fitness': min(scores) if scores else 0,
            'mean_fitness': np.mean(scores) if scores else 0,
            'std_fitness': np.std(scores) if scores else 0,
            'unique_genome_hashes': len(set(g.get_gene_hash() for g in self._population)),
        }
    
    def get_best_strategy(self) -> Optional[StrategyGenome]:
        """Get the best strategy from current population."""
        if not self._population:
            return None
        
        return min(
            self._population,
            key=lambda g: (g.rank if g.rank is not None else 999,)
        )
    
    def get_pareto_front(self) -> List[StrategyGenome]:
        """Get current Pareto front."""
        return self._pareto_front.copy()
    
    def export_genome(self, genome: StrategyGenome, filepath: str):
        """Export genome to file."""
        with open(filepath, 'w') as f:
            json.dump(genome.to_dict(), f, indent=2, default=str)
    
    def get_evolution_history(self) -> List[Dict]:
        """Get evolution history."""
        return self._evolution_history.copy()


# Example usage
async def example_evolution():
    """Example of strategy evolution."""
    engine = StrategyEvolutionEngine(config={
        'population_size': 20,
        'elite_size': 3,
        'mutation_rate': 0.15,
        'crossover_rate': 0.8,
    })
    
    # Initialize population
    engine.initialize_population()
    
    # Evolve for 5 generations
    for gen in range(5):
        stats = await engine.evolve_generation()
        print(f"Generation {gen + 1}: best={stats['best_fitness']:.4f}, "
              f"mean={stats['mean_fitness']:.4f}, pareto={stats['pareto_front_size']}")
    
    # Get best strategy
    best = engine.get_best_strategy()
    if best:
        print(f"\nBest Strategy: {best.genome_id}")
        print(f"Generation: {best.generation}")
        print(f"Fitness: {best.fitness}")
        print(f"Gene Hash: {best.get_gene_hash()}")
    
    # Get Pareto front
    pareto = engine.get_pareto_front()
    print(f"\nPareto front size: {len(pareto)}")


if __name__ == "__main__":
    asyncio.run(example_evolution())
