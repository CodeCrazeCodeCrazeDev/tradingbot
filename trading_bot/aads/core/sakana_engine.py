"""
AADS Sakana Evolution Engine

Inspired by Sakana AI's nature-based model merging and evolutionary model construction.
Strategies are genomes. The system evolves a population of strategies across generations,
selecting survivors by financial fitness.

Evolutionary Loop:
1. EVALUATE: Walk-forward backtest each genome, compute fitness
2. SELECT: Keep top performers (elitism) + tournament selection
3. REPRODUCE: Crossover + mutation + LLM mutation
4. VALIDATE: Gate fitness > threshold for candidate pool
5. DEPLOY: Best genome gets capital allocation
6. EXTINCTION: Periodic random injection to prevent local optima
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging
import json
from pathlib import Path
import uuid

from .strategy_genome import (
    AADSStrategyGenome, StrategyGene, RiskGene, FilterGene, ExecutionGene,
    GenomeStatus, SignalGeneType, merge_strategies, create_random_genome
)

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for the Sakana Evolution Engine"""
    # Population parameters
    population_size: int = 50
    elite_count: int = 20
    tournament_size: int = 3
    offspring_count: int = 20
    
    # Fitness thresholds
    fitness_threshold: float = 0.8          # Minimum fitness to enter candidate pool
    deployment_threshold: float = 1.2       # Minimum fitness for deployment
    retirement_threshold: float = 0.5       # Below this = retire
    
    # Mutation parameters
    base_mutation_rate: float = 0.15
    max_mutation_rate: float = 0.30
    mutation_decay: float = 0.95            # Decay rate per generation
    parameter_mutation_range: float = 0.20  # ±20% parameter change
    
    # Crossover parameters
    crossover_rate: float = 0.7
    merge_ratio_range: Tuple[float, float] = (0.3, 0.7)
    
    # Extinction events
    extinction_frequency: int = 90          # Days between extinction events
    extinction_injection_count: int = 5     # Random genomes to inject
    
    # Validation
    min_backtest_days: int = 252            # Minimum backtest period
    walk_forward_windows: int = 5           # Number of walk-forward windows
    out_of_sample_ratio: float = 0.3        # OOS data ratio
    
    # Deployment
    initial_allocation_pct: float = 0.005   # 0.5% initial capital
    max_allocation_pct: float = 0.05        # 5% max per strategy
    
    # Persistence
    checkpoint_frequency: int = 10          # Generations between checkpoints
    save_directory: str = "aads_evolution"


class SelectionMethod(Enum):
    """Selection methods for parent selection"""
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    ELITISM = "elitism"


@dataclass
class GenerationResult:
    """Results from a single generation"""
    generation: int
    timestamp: datetime
    population_size: int
    
    # Fitness statistics
    best_fitness: float
    avg_fitness: float
    median_fitness: float
    fitness_std: float
    
    # Performance metrics
    best_sharpe: float
    avg_sharpe: float
    best_win_rate: float
    
    # Diversity
    unique_signal_combinations: int
    avg_genome_distance: float
    
    # Lifecycle
    new_candidates: int
    validated: int
    deployed: int
    retired: int
    
    # Best genome
    best_genome_id: str
    best_genome: Optional[AADSStrategyGenome] = None


class SakanaEvolutionEngine:
    """
    Sakana-Inspired Evolution Engine for Strategy Discovery
    
    Implements the complete evolutionary cycle:
    - Population management with speciation
    - Fitness-based selection with diversity preservation
    - Sakana-style model merging for crossover
    - LLM-driven mutation (AlphaEvolve integration)
    - Extinction events to escape local optima
    """
    
    def __init__(
        self,
        config: EvolutionConfig,
        backtest_fn: Optional[Callable[[AADSStrategyGenome], Dict[str, float]]] = None,
        llm_mutate_fn: Optional[Callable[[AADSStrategyGenome], AADSStrategyGenome]] = None
    ):
        """
        Initialize the evolution engine.
        
        Args:
            config: Evolution configuration
            backtest_fn: Function to backtest a genome and return metrics
            llm_mutate_fn: Function to use LLM for intelligent mutation
        """
        self.config = config
        self.backtest_fn = backtest_fn or self._default_backtest
        self.llm_mutate_fn = llm_mutate_fn
        
        # Population state
        self.population: List[AADSStrategyGenome] = []
        self.generation: int = 0
        self.generation_results: List[GenerationResult] = []
        
        # Best tracking
        self.best_genome: Optional[AADSStrategyGenome] = None
        self.pareto_frontier: List[AADSStrategyGenome] = []
        
        # Deployed strategies
        self.deployed_genomes: Dict[str, AADSStrategyGenome] = {}
        self.retired_genomes: Dict[str, AADSStrategyGenome] = {}
        
        # Extinction tracking
        self.last_extinction: datetime = datetime.now()
        self.extinction_count: int = 0
        
        # Setup directories
        self.save_dir = Path(config.save_directory)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        (self.save_dir / "genomes").mkdir(exist_ok=True)
        (self.save_dir / "checkpoints").mkdir(exist_ok=True)
        
        logger.info(f"SakanaEvolutionEngine initialized with population_size={config.population_size}")
    
    def initialize_population(self, seed_genomes: Optional[List[AADSStrategyGenome]] = None) -> None:
        """
        Initialize the population with random or seed genomes.
        
        Args:
            seed_genomes: Optional list of seed genomes to include
        """
        self.population = []
        
        # Add seed genomes if provided
        if seed_genomes:
            for genome in seed_genomes[:self.config.population_size]:
                genome.generation = 0
                genome.status = GenomeStatus.CANDIDATE
                self.population.append(genome)
        
        # Fill remaining with random genomes
        while len(self.population) < self.config.population_size:
            genome = create_random_genome(
                num_signals=np.random.randint(3, 10)
            )
            genome.generation = 0
            self.population.append(genome)
        
        logger.info(f"Initialized population with {len(self.population)} genomes")
    
    def evolve_generation(self) -> GenerationResult:
        """
        Run one generation of evolution.
        
        Returns:
            GenerationResult with statistics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Generation {self.generation}")
        logger.info(f"{'='*60}")
        
        # Step 1: Evaluate all genomes
        self._evaluate_population()
        
        # Step 2: Select survivors
        survivors = self._select_survivors()
        
        # Step 3: Reproduce (crossover + mutation)
        offspring = self._reproduce(survivors)
        
        # Step 4: Validate offspring
        validated = self._validate_offspring(offspring)
        
        # Step 5: Update population
        self.population = survivors + validated
        
        # Ensure population size
        while len(self.population) < self.config.population_size:
            self.population.append(create_random_genome())
        
        # Step 6: Check for extinction event
        if self._should_trigger_extinction():
            self._extinction_event()
        
        # Step 7: Deploy best candidate
        self._deploy_best_candidate()
        
        # Step 8: Retire underperformers
        retired_count = self._retire_underperformers()
        
        # Calculate generation statistics
        result = self._calculate_generation_result(
            validated_count=len(validated),
            retired_count=retired_count
        )
        self.generation_results.append(result)
        
        # Update best genome
        if self.population:
            current_best = max(self.population, key=lambda g: g.fitness_score)
            if self.best_genome is None or current_best.fitness_score > self.best_genome.fitness_score:
                self.best_genome = current_best
                logger.info(f"New best genome: {current_best.genome_id[:8]} with fitness {current_best.fitness_score:.4f}")
        
        # Save checkpoint
        if self.generation % self.config.checkpoint_frequency == 0:
            self._save_checkpoint()
        
        self.generation += 1
        return result
    
    def evolve(self, generations: int = 100) -> AADSStrategyGenome:
        """
        Run the full evolution process.
        
        Args:
            generations: Number of generations to evolve
            
        Returns:
            Best genome found
        """
        if not self.population:
            self.initialize_population()
        
        for _ in range(generations):
            result = self.evolve_generation()
            
            # Log progress
            logger.info(f"Gen {result.generation}: Best={result.best_fitness:.4f}, "
                       f"Avg={result.avg_fitness:.4f}, Deployed={result.deployed}")
            
            # Check for convergence
            if self._check_convergence():
                logger.info("Convergence detected, stopping evolution")
                break
        
        self._save_final_results()
        return self.best_genome
    
    def _evaluate_population(self) -> None:
        """Evaluate fitness of all genomes in population"""
        for genome in self.population:
            if genome.fitness_score == 0.0:  # Not yet evaluated
                metrics = self.backtest_fn(genome)
                
                genome.sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
                genome.max_drawdown = metrics.get('max_drawdown', 0.0)
                genome.win_rate = metrics.get('win_rate', 0.5)
                genome.sortino_ratio = metrics.get('sortino_ratio', 0.0)
                genome.calmar_ratio = metrics.get('calmar_ratio', 0.0)
                genome.backtest_results = metrics
                
                genome.compute_fitness()
                genome.last_updated = datetime.now()
    
    def _select_survivors(self) -> List[AADSStrategyGenome]:
        """
        Select survivors using elitism + tournament selection.
        
        Returns:
            List of surviving genomes
        """
        # Sort by fitness
        sorted_pop = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
        
        # Elitism: keep top performers
        elite = sorted_pop[:self.config.elite_count]
        
        # Tournament selection for additional survivors
        additional_count = min(10, len(sorted_pop) - self.config.elite_count)
        additional = []
        
        for _ in range(additional_count):
            tournament = np.random.choice(
                sorted_pop[self.config.elite_count:],
                size=min(self.config.tournament_size, len(sorted_pop) - self.config.elite_count),
                replace=False
            )
            winner = max(tournament, key=lambda g: g.fitness_score)
            if winner not in additional:
                additional.append(winner)
        
        survivors = elite + additional
        logger.info(f"Selected {len(survivors)} survivors (elite={len(elite)}, tournament={len(additional)})")
        
        return survivors
    
    def _reproduce(self, parents: List[AADSStrategyGenome]) -> List[AADSStrategyGenome]:
        """
        Create offspring through crossover and mutation.
        
        Args:
            parents: Parent genomes
            
        Returns:
            List of offspring genomes
        """
        offspring = []
        
        while len(offspring) < self.config.offspring_count:
            if np.random.random() < self.config.crossover_rate and len(parents) >= 2:
                # Crossover: Sakana-style model merging
                parent_a, parent_b = np.random.choice(parents, size=2, replace=False)
                merge_ratio = np.random.uniform(*self.config.merge_ratio_range)
                
                child = merge_strategies(parent_a, parent_b, merge_ratio)
                child.generation = self.generation + 1
                
                # Apply mutation to child
                child = self._mutate(child)
                offspring.append(child)
            else:
                # Mutation only
                parent = np.random.choice(parents)
                child = parent.clone()
                child = self._mutate(child)
                offspring.append(child)
        
        logger.info(f"Created {len(offspring)} offspring")
        return offspring
    
    def _mutate(self, genome: AADSStrategyGenome) -> AADSStrategyGenome:
        """
        Apply mutations to a genome.
        
        Mutation types:
        - Parameter mutation: ±20% change to numeric parameters
        - Signal addition/removal
        - LLM-driven intelligent mutation (if available)
        """
        mutation_rate = genome.mutation_rate
        
        # Mutate signal genes
        for gene in genome.signal_genes:
            if np.random.random() < mutation_rate:
                # Weight mutation
                gene.weight *= np.random.uniform(
                    1 - self.config.parameter_mutation_range,
                    1 + self.config.parameter_mutation_range
                )
                gene.weight = np.clip(gene.weight, -2.0, 2.0)
            
            if np.random.random() < mutation_rate:
                # Lookback mutation
                gene.lookback = int(gene.lookback * np.random.uniform(0.8, 1.2))
                gene.lookback = np.clip(gene.lookback, 5, 252)
            
            if np.random.random() < mutation_rate:
                # Threshold mutation
                gene.threshold += np.random.uniform(-0.5, 0.5)
                gene.threshold = np.clip(gene.threshold, -3.0, 3.0)
        
        # Add new signal with small probability
        if np.random.random() < mutation_rate * 0.5 and len(genome.signal_genes) < 15:
            new_gene = StrategyGene(
                signal_type=np.random.choice(list(SignalGeneType)),
                weight=np.random.uniform(-1.0, 1.0),
                lookback=np.random.randint(5, 100),
                threshold=np.random.uniform(-2.0, 2.0)
            )
            genome.signal_genes.append(new_gene)
        
        # Remove signal with small probability
        if np.random.random() < mutation_rate * 0.3 and len(genome.signal_genes) > 2:
            genome.signal_genes.pop(np.random.randint(len(genome.signal_genes)))
        
        # Mutate risk genes
        if np.random.random() < mutation_rate:
            genome.risk_genes.max_drawdown *= np.random.uniform(0.9, 1.1)
            genome.risk_genes.max_drawdown = np.clip(genome.risk_genes.max_drawdown, 0.05, 0.30)
        
        if np.random.random() < mutation_rate:
            genome.risk_genes.kelly_fraction *= np.random.uniform(0.9, 1.1)
            genome.risk_genes.kelly_fraction = np.clip(genome.risk_genes.kelly_fraction, 0.1, 0.5)
        
        # LLM-driven mutation (if available)
        if self.llm_mutate_fn and np.random.random() < mutation_rate * 0.2:
            try:
                genome = self.llm_mutate_fn(genome)
            except Exception as e:
                logger.warning(f"LLM mutation failed: {e}")
        
        # Adapt mutation rate based on fitness variance
        genome.mutation_rate *= self.config.mutation_decay
        genome.mutation_rate = max(0.05, min(genome.mutation_rate, self.config.max_mutation_rate))
        
        return genome
    
    def _validate_offspring(self, offspring: List[AADSStrategyGenome]) -> List[AADSStrategyGenome]:
        """
        Validate offspring through backtesting.
        
        Only offspring that pass the fitness threshold enter the candidate pool.
        """
        validated = []
        
        for genome in offspring:
            # Evaluate
            metrics = self.backtest_fn(genome)
            genome.sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
            genome.max_drawdown = metrics.get('max_drawdown', 0.0)
            genome.win_rate = metrics.get('win_rate', 0.5)
            genome.backtest_results = metrics
            genome.compute_fitness()
            
            # Check threshold
            if genome.fitness_score >= self.config.fitness_threshold:
                genome.status = GenomeStatus.VALIDATED
                validated.append(genome)
            else:
                genome.status = GenomeStatus.CANDIDATE
        
        logger.info(f"Validated {len(validated)}/{len(offspring)} offspring")
        return validated
    
    def _should_trigger_extinction(self) -> bool:
        """Check if an extinction event should be triggered"""
        days_since_extinction = (datetime.now() - self.last_extinction).days
        return days_since_extinction >= self.config.extinction_frequency
    
    def _extinction_event(self) -> None:
        """
        Trigger an extinction event (asteroid strike).
        
        Injects random genomes to force exploration of non-local fitness landscape.
        Prevents premature convergence to local optima.
        """
        logger.info(f"🌋 EXTINCTION EVENT #{self.extinction_count + 1}")
        
        # Remove worst performers
        self.population.sort(key=lambda g: g.fitness_score, reverse=True)
        survivors = self.population[:int(len(self.population) * 0.7)]
        
        # Inject random genomes
        for _ in range(self.config.extinction_injection_count):
            random_genome = create_random_genome(num_signals=np.random.randint(3, 12))
            random_genome.generation = self.generation
            survivors.append(random_genome)
        
        self.population = survivors
        self.last_extinction = datetime.now()
        self.extinction_count += 1
        
        logger.info(f"Population reduced to {len(self.population)}, injected {self.config.extinction_injection_count} random genomes")
    
    def _deploy_best_candidate(self) -> None:
        """Deploy the best validated candidate with capital allocation"""
        validated = [g for g in self.population if g.status == GenomeStatus.VALIDATED]
        
        if not validated:
            return
        
        best_candidate = max(validated, key=lambda g: g.fitness_score)
        
        if best_candidate.fitness_score >= self.config.deployment_threshold:
            best_candidate.status = GenomeStatus.DEPLOYED
            best_candidate.capital_allocation = self.config.initial_allocation_pct
            self.deployed_genomes[best_candidate.genome_id] = best_candidate
            
            logger.info(f"🚀 Deployed genome {best_candidate.genome_id[:8]} with "
                       f"{best_candidate.capital_allocation*100:.1f}% allocation")
    
    def _retire_underperformers(self) -> int:
        """Retire genomes that fall below the retirement threshold"""
        retired_count = 0
        
        for genome in self.population[:]:
            if genome.fitness_score < self.config.retirement_threshold:
                genome.status = GenomeStatus.RETIRED
                self.retired_genomes[genome.genome_id] = genome
                self.population.remove(genome)
                
                # Remove from deployed if applicable
                if genome.genome_id in self.deployed_genomes:
                    del self.deployed_genomes[genome.genome_id]
                
                retired_count += 1
        
        if retired_count > 0:
            logger.info(f"Retired {retired_count} underperforming genomes")
        
        return retired_count
    
    def _calculate_generation_result(self, validated_count: int, retired_count: int) -> GenerationResult:
        """Calculate statistics for the current generation"""
        fitnesses = [g.fitness_score for g in self.population]
        sharpes = [g.sharpe_ratio for g in self.population]
        win_rates = [g.win_rate for g in self.population]
        
        # Calculate diversity
        signal_combos = set()
        for g in self.population:
            combo = frozenset(gene.signal_type for gene in g.signal_genes)
            signal_combos.add(combo)
        
        best = max(self.population, key=lambda g: g.fitness_score) if self.population else None
        
        return GenerationResult(
            generation=self.generation,
            timestamp=datetime.now(),
            population_size=len(self.population),
            best_fitness=max(fitnesses) if fitnesses else 0,
            avg_fitness=np.mean(fitnesses) if fitnesses else 0,
            median_fitness=np.median(fitnesses) if fitnesses else 0,
            fitness_std=np.std(fitnesses) if fitnesses else 0,
            best_sharpe=max(sharpes) if sharpes else 0,
            avg_sharpe=np.mean(sharpes) if sharpes else 0,
            best_win_rate=max(win_rates) if win_rates else 0,
            unique_signal_combinations=len(signal_combos),
            avg_genome_distance=0.0,  # TODO: implement genome distance
            new_candidates=len([g for g in self.population if g.status == GenomeStatus.CANDIDATE]),
            validated=validated_count,
            deployed=len(self.deployed_genomes),
            retired=retired_count,
            best_genome_id=best.genome_id if best else "",
            best_genome=best
        )
    
    def _check_convergence(self) -> bool:
        """Check if evolution has converged"""
        if len(self.generation_results) < 20:
            return False
        
        recent = self.generation_results[-20:]
        fitness_values = [r.best_fitness for r in recent]
        
        # Check if fitness has plateaued
        fitness_range = max(fitness_values) - min(fitness_values)
        return fitness_range < 0.01
    
    def _save_checkpoint(self) -> None:
        """Save evolution checkpoint"""
        checkpoint = {
            'generation': self.generation,
            'population': [g.to_dict() for g in self.population],
            'best_genome': self.best_genome.to_dict() if self.best_genome else None,
            'deployed_genomes': {k: v.to_dict() for k, v in self.deployed_genomes.items()},
            'generation_results': [
                {
                    'generation': r.generation,
                    'best_fitness': r.best_fitness,
                    'avg_fitness': r.avg_fitness,
                    'deployed': r.deployed
                }
                for r in self.generation_results[-100:]
            ],
            'config': {
                'population_size': self.config.population_size,
                'elite_count': self.config.elite_count,
                'fitness_threshold': self.config.fitness_threshold
            },
            'timestamp': datetime.now().isoformat()
        }
        
        filepath = self.save_dir / "checkpoints" / f"gen_{self.generation}.json"
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        
        logger.info(f"Saved checkpoint: {filepath}")
    
    def _save_final_results(self) -> None:
        """Save final evolution results"""
        results = {
            'total_generations': self.generation,
            'best_genome': self.best_genome.to_dict() if self.best_genome else None,
            'deployed_count': len(self.deployed_genomes),
            'retired_count': len(self.retired_genomes),
            'extinction_events': self.extinction_count,
            'final_population_size': len(self.population),
            'fitness_progression': [r.best_fitness for r in self.generation_results],
            'timestamp': datetime.now().isoformat()
        }
        
        filepath = self.save_dir / "final_results.json"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save best genome separately
        if self.best_genome:
            best_path = self.save_dir / "genomes" / "best_genome.json"
            with open(best_path, 'w') as f:
                json.dump(self.best_genome.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Saved final results to {filepath}")
    
    def _default_backtest(self, genome: AADSStrategyGenome) -> Dict[str, float]:
        """Default backtest function (placeholder)"""
        # This would be replaced with actual backtesting logic
        return {
            'sharpe_ratio': np.random.uniform(0.5, 2.5),
            'max_drawdown': np.random.uniform(0.05, 0.25),
            'win_rate': np.random.uniform(0.45, 0.65),
            'sortino_ratio': np.random.uniform(0.5, 3.0),
            'calmar_ratio': np.random.uniform(0.5, 2.0),
            'total_return': np.random.uniform(-0.1, 0.5),
            'volatility': np.random.uniform(0.1, 0.3)
        }
    
    def get_deployed_strategies(self) -> List[AADSStrategyGenome]:
        """Get all currently deployed strategies"""
        return list(self.deployed_genomes.values())
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Generate comprehensive evolution report"""
        return {
            'summary': {
                'total_generations': self.generation,
                'population_size': len(self.population),
                'deployed_strategies': len(self.deployed_genomes),
                'retired_strategies': len(self.retired_genomes),
                'extinction_events': self.extinction_count,
                'best_fitness': self.best_genome.fitness_score if self.best_genome else 0
            },
            'fitness_progression': [r.best_fitness for r in self.generation_results],
            'diversity_progression': [r.unique_signal_combinations for r in self.generation_results],
            'deployed_genomes': [g.genome_id for g in self.deployed_genomes.values()],
            'best_genome': self.best_genome.to_dict() if self.best_genome else None
        }
