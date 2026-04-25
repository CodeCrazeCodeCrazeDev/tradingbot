"""
Evolution Engine: Core evolutionary loop for strategy discovery.

Implements the complete evolutionary cycle:
Generate → Mutate → Evaluate → Select → Repeat

With strict selection pressure and massive parallel search.
"""

from typing import List, Dict, Tuple, Optional, Callable
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle

from .strategy_genome import StrategyGenome, SearchSpace
from .genetic_operators import GeneticOperators
from .backtesting_engine import LeakageFreeBacktester, BacktestResult
from .fitness_evaluator import MultiObjectiveFitness, FitnessScore
from .walk_forward import WalkForwardValidator, WalkForwardResult


logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """Individual in the population"""
    genome: StrategyGenome
    fitness: Optional[FitnessScore] = None
    backtest_result: Optional[BacktestResult] = None
    walkforward_result: Optional[WalkForwardResult] = None
    generation: int = 0
    
    def get_id(self) -> str:
        return self.genome.get_genome_id()


@dataclass
class GenerationStats:
    """Statistics for a generation"""
    generation: int
    population_size: int
    
    best_fitness: float
    avg_fitness: float
    median_fitness: float
    worst_fitness: float
    
    best_sharpe: float
    avg_sharpe: float
    
    best_genome_id: str
    
    diversity_score: float
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvolutionConfig:
    """Configuration for evolution engine"""
    population_size: int = 100
    elite_size: int = 10
    tournament_size: int = 3
    
    mutation_rate: float = 0.15
    crossover_rate: float = 0.7
    
    max_generations: int = 100
    convergence_threshold: float = 0.001
    convergence_generations: int = 10
    
    use_walkforward: bool = True
    walkforward_frequency: int = 5
    
    parallel_workers: int = 4
    
    save_frequency: int = 5
    save_directory: str = "alpha_evolve_results"


class EvolutionEngine:
    """
    Main evolution engine for strategy discovery.
    
    Orchestrates the complete evolutionary process with:
    - Population management
    - Fitness evaluation
    - Selection and breeding
    - Mutation and crossover
    - Convergence detection
    - Result tracking
    """
    
    def __init__(
        self,
        config: EvolutionConfig,
        search_space: SearchSpace,
        market_data: pd.DataFrame
    ):
        """
        Initialize evolution engine.
        
        Args:
            config: Evolution configuration
            search_space: Search space for strategies
            market_data: Market data for backtesting
        """
        self.config = config
        self.search_space = search_space
        self.market_data = market_data
        
        self.genetic_ops = GeneticOperators(
            search_space=search_space,
            mutation_rate=config.mutation_rate
        )
        
        self.fitness_evaluator = MultiObjectiveFitness()
        
        self.walkforward_validator = WalkForwardValidator()
        
        self.population: List[Individual] = []
        self.generation_stats: List[GenerationStats] = []
        self.current_generation = 0
        
        self.best_individual: Optional[Individual] = None
        self.pareto_frontier: List[Individual] = []
        
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup directories for saving results"""
        self.save_dir = Path(self.config.save_directory)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        (self.save_dir / "genomes").mkdir(exist_ok=True)
        (self.save_dir / "checkpoints").mkdir(exist_ok=True)
        (self.save_dir / "logs").mkdir(exist_ok=True)
    
    def evolve(self) -> Individual:
        """
        Run the complete evolution process.
        
        Returns:
            Best individual found
        """
        logger.info(f"Starting evolution with population size {self.config.population_size}")
        
        self._initialize_population()
        
        for generation in range(self.config.max_generations):
            self.current_generation = generation
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Generation {generation + 1}/{self.config.max_generations}")
            logger.info(f"{'='*60}")
            
            self._evaluate_population()
            
            stats = self._calculate_generation_stats()
            self.generation_stats.append(stats)
            self._log_generation_stats(stats)
            
            self._update_best_and_pareto()
            
            if self._check_convergence():
                logger.info(f"Convergence detected at generation {generation}")
                break
            
            self._breed_next_generation()
            
            if (generation + 1) % self.config.save_frequency == 0:
                self._save_checkpoint()
        
        logger.info("\nEvolution complete!")
        self._save_final_results()
        
        return self.best_individual
    
    def _initialize_population(self):
        """Initialize population with random genomes"""
        logger.info("Initializing population...")
        
        self.population = []
        
        for i in range(self.config.population_size):
            genome = self.search_space.random_genome()
            individual = Individual(genome=genome, generation=0)
            self.population.append(individual)
        
        logger.info(f"Created {len(self.population)} random individuals")
    
    def _evaluate_population(self):
        """Evaluate fitness of all individuals in population"""
        logger.info("Evaluating population...")
        
        unevaluated = [ind for ind in self.population if ind.fitness is None]
        
        if not unevaluated:
            return
        
        if self.config.parallel_workers > 1:
            self._evaluate_parallel(unevaluated)
        else:
            self._evaluate_sequential(unevaluated)
        
        logger.info(f"Evaluated {len(unevaluated)} individuals")
    
    def _evaluate_sequential(self, individuals: List[Individual]):
        """Evaluate individuals sequentially"""
        for i, individual in enumerate(individuals):
            if i % 10 == 0:
                logger.info(f"  Evaluating {i+1}/{len(individuals)}...")
            
            self._evaluate_individual(individual)
    
    def _evaluate_parallel(self, individuals: List[Individual]):
        """Evaluate individuals in parallel"""
        with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures = {
                executor.submit(
                    self._evaluate_individual_static,
                    individual.genome,
                    self.market_data,
                    self.config.use_walkforward and 
                    (self.current_generation % self.config.walkforward_frequency == 0)
                ): individual
                for individual in individuals
            }
            
            for i, future in enumerate(as_completed(futures)):
                if i % 10 == 0:
                    logger.info(f"  Completed {i+1}/{len(individuals)}...")
                
                individual = futures[future]
                try:
                    fitness, backtest_result, walkforward_result = future.result()
                    individual.fitness = fitness
                    individual.backtest_result = backtest_result
                    individual.walkforward_result = walkforward_result
                except Exception as e:
                    logger.error(f"Error evaluating individual: {e}")
                    individual.fitness = FitnessScore(
                        sharpe_ratio=0, max_drawdown=0, regime_stability=0,
                        tail_risk=0, complexity_penalty=0, total_fitness=0, metrics={}
                    )
    
    @staticmethod
    def _evaluate_individual_static(
        genome: StrategyGenome,
        market_data: pd.DataFrame,
        use_walkforward: bool
    ) -> Tuple[FitnessScore, BacktestResult, Optional[WalkForwardResult]]:
        """Static method for parallel evaluation"""
        backtester = LeakageFreeBacktester(market_data)
        backtest_result = backtester.backtest(genome)
        
        fitness_evaluator = MultiObjectiveFitness()
        fitness = fitness_evaluator.evaluate(
            backtest_result,
            genome.get_complexity(),
            market_data
        )
        
        walkforward_result = None
        if use_walkforward:
            validator = WalkForwardValidator()
            walkforward_result = validator.validate(
                genome, market_data, fitness_evaluator
            )
            
            if walkforward_result.overfitting_score > 0.5:
                fitness.total_fitness *= 0.5
        
        return fitness, backtest_result, walkforward_result
    
    def _evaluate_individual(self, individual: Individual):
        """Evaluate a single individual"""
        fitness, backtest_result, walkforward_result = self._evaluate_individual_static(
            individual.genome,
            self.market_data,
            self.config.use_walkforward and 
            (self.current_generation % self.config.walkforward_frequency == 0)
        )
        
        individual.fitness = fitness
        individual.backtest_result = backtest_result
        individual.walkforward_result = walkforward_result
    
    def _calculate_generation_stats(self) -> GenerationStats:
        """Calculate statistics for current generation"""
        fitnesses = [ind.fitness.total_fitness for ind in self.population if ind.fitness]
        sharpes = [ind.fitness.sharpe_ratio for ind in self.population if ind.fitness]
        
        best_ind = max(self.population, key=lambda x: x.fitness.total_fitness if x.fitness else 0)
        
        diversity = self._calculate_population_diversity()
        
        return GenerationStats(
            generation=self.current_generation,
            population_size=len(self.population),
            best_fitness=max(fitnesses) if fitnesses else 0,
            avg_fitness=np.mean(fitnesses) if fitnesses else 0,
            median_fitness=np.median(fitnesses) if fitnesses else 0,
            worst_fitness=min(fitnesses) if fitnesses else 0,
            best_sharpe=max(sharpes) if sharpes else 0,
            avg_sharpe=np.mean(sharpes) if sharpes else 0,
            best_genome_id=best_ind.get_id(),
            diversity_score=diversity
        )
    
    def _log_generation_stats(self, stats: GenerationStats):
        """Log generation statistics"""
        logger.info(f"\nGeneration {stats.generation} Statistics:")
        logger.info(f"  Population Size: {stats.population_size}")
        logger.info(f"  Best Fitness:    {stats.best_fitness:.4f}")
        logger.info(f"  Avg Fitness:     {stats.avg_fitness:.4f}")
        logger.info(f"  Median Fitness:  {stats.median_fitness:.4f}")
        logger.info(f"  Best Sharpe:     {stats.best_sharpe:.4f}")
        logger.info(f"  Diversity:       {stats.diversity_score:.4f}")
    
    def _update_best_and_pareto(self):
        """Update best individual and Pareto frontier"""
        current_best = max(
            self.population,
            key=lambda x: x.fitness.total_fitness if x.fitness else 0
        )
        
        if self.best_individual is None or \
           current_best.fitness.total_fitness > self.best_individual.fitness.total_fitness:
            self.best_individual = current_best
            logger.info(f"  New best individual! Fitness: {current_best.fitness.total_fitness:.4f}")
        
        fitness_scores = [
            (ind.get_id(), ind.fitness)
            for ind in self.population
            if ind.fitness
        ]
        
        pareto_ids = self.fitness_evaluator.get_pareto_frontier(fitness_scores)
        self.pareto_frontier = [
            ind for ind in self.population
            if ind.get_id() in pareto_ids
        ]
        
        logger.info(f"  Pareto frontier size: {len(self.pareto_frontier)}")
    
    def _check_convergence(self) -> bool:
        """Check if evolution has converged"""
        if len(self.generation_stats) < self.config.convergence_generations:
            return False
        
        recent_stats = self.generation_stats[-self.config.convergence_generations:]
        best_fitnesses = [s.best_fitness for s in recent_stats]
        
        fitness_range = max(best_fitnesses) - min(best_fitnesses)
        
        if fitness_range < self.config.convergence_threshold:
            return True
        
        return False
    
    def _breed_next_generation(self):
        """Breed next generation using selection and genetic operators"""
        logger.info("Breeding next generation...")
        
        population_with_fitness = [
            (ind, ind.fitness.total_fitness)
            for ind in self.population
            if ind.fitness
        ]
        
        elite = self.genetic_ops.elitism_selection(
            population_with_fitness,
            self.config.elite_size
        )
        
        next_generation = [Individual(genome=g.clone(), generation=self.current_generation + 1) 
                          for g in elite]
        
        while len(next_generation) < self.config.population_size:
            if np.random.random() < self.config.crossover_rate:
                parent1 = self.genetic_ops.tournament_selection(
                    population_with_fitness,
                    self.config.tournament_size
                )
                parent2 = self.genetic_ops.tournament_selection(
                    population_with_fitness,
                    self.config.tournament_size
                )
                
                offspring1, offspring2 = self.genetic_ops.crossover(parent1, parent2)
                
                next_generation.append(Individual(
                    genome=offspring1,
                    generation=self.current_generation + 1
                ))
                
                if len(next_generation) < self.config.population_size:
                    next_generation.append(Individual(
                        genome=offspring2,
                        generation=self.current_generation + 1
                    ))
            
            else:
                parent = self.genetic_ops.tournament_selection(
                    population_with_fitness,
                    self.config.tournament_size
                )
                
                mutated = self.genetic_ops.mutate(parent)
                
                next_generation.append(Individual(
                    genome=mutated,
                    generation=self.current_generation + 1
                ))
        
        self.population = next_generation[:self.config.population_size]
        
        logger.info(f"Created {len(self.population)} individuals for next generation")
    
    def _calculate_population_diversity(self) -> float:
        """Calculate diversity of current population"""
        if len(self.population) < 2:
            return 0.0
        
        signal_types_sets = [
            set(s.signal_type for s in ind.genome.signals)
            for ind in self.population
        ]
        
        unique_combinations = len(set(frozenset(s) for s in signal_types_sets))
        diversity = unique_combinations / len(self.population)
        
        return diversity
    
    def _save_checkpoint(self):
        """Save checkpoint of current evolution state"""
        checkpoint_path = self.save_dir / "checkpoints" / f"gen_{self.current_generation}.pkl"
        
        checkpoint = {
            'generation': self.current_generation,
            'population': self.population,
            'best_individual': self.best_individual,
            'pareto_frontier': self.pareto_frontier,
            'generation_stats': self.generation_stats,
            'config': self.config
        }
        
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        logger.info(f"Saved checkpoint to {checkpoint_path}")
    
    def _save_final_results(self):
        """Save final evolution results"""
        results_path = self.save_dir / "final_results.json"
        
        results = {
            'best_genome': self.best_individual.genome.to_dict(),
            'best_fitness': self.best_individual.fitness.total_fitness,
            'best_sharpe': self.best_individual.fitness.sharpe_ratio,
            'total_generations': self.current_generation + 1,
            'pareto_frontier_size': len(self.pareto_frontier),
            'generation_stats': [
                {
                    'generation': s.generation,
                    'best_fitness': s.best_fitness,
                    'avg_fitness': s.avg_fitness,
                    'diversity': s.diversity_score
                }
                for s in self.generation_stats
            ]
        }
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved final results to {results_path}")
        
        best_genome_path = self.save_dir / "best_genome.json"
        with open(best_genome_path, 'w') as f:
            json.dump(self.best_individual.genome.to_dict(), f, indent=2)
        
        logger.info(f"Saved best genome to {best_genome_path}")
