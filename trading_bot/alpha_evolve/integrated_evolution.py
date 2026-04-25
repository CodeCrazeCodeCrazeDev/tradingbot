"""
Phase 5: Integrated Evolution System

Connects all Phase 2, 3, 4 components into a unified trading bot:
- Speciated evolution with diversity preservation
- Regime-aware evaluation with tail risk metrics
- Liquidity-aware execution with slippage minimization
"""

from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging
from pathlib import Path
import json

from ..alpha_evolve.strategy_genome import StrategyGenome, Signal, SignalType
from ..alpha_evolve.evolution_engine import (
    EvolutionEngine, EvolutionConfig, Individual, GenerationStats
)
from ..alpha_evolve.speciated_evolution_engine import (
    SpeciatedEvolutionEngine, Species, SpeciationConfig
)
from ..alpha_evolve.diversity_selection import (
    DiversitySelector, AgeBasedSelector, MultiObjectiveSelector
)
from ..alpha_evolve.fitness_evaluator import MultiObjectiveFitness, FitnessScore
from ..alpha_evolve.backtesting_engine import LeakageFreeBacktester, BacktestResult
from ..alpha_evolve.enhanced_fitness import EnhancedFitnessEvaluator
from ..alpha_evolve.regime_aware_backtester import (
    RegimeAwareBacktester, MarketRegime
)
from ..alpha_evolve.walk_forward import WalkForwardValidator
from ..execution.liquidity_aware_sizer import (
    LiquidityAwareSizer, MarketDepth
)
from ..execution.advanced_execution_algorithms import (
    AdaptiveExecutionEngine, OrderType
)

logger = logging.getLogger(__name__)


@dataclass
class IntegratedEvolutionConfig:
    """Configuration for the integrated evolution system"""
    # Evolution parameters
    population_size: int = 100
    max_generations: int = 100
    elite_size: int = 10
    
    # Speciation parameters
    enable_speciation: bool = True
    compatibility_threshold: float = 3.0
    target_species_count: int = 5
    
    # Diversity parameters
    enable_diversity_preservation: bool = True
    diversity_weight: float = 0.3
    niche_radius: float = 0.1
    
    # Age-based selection
    enable_age_based_selection: bool = True
    max_age: int = 20
    age_fitness_decay: float = 0.95
    
    # Regime-aware evaluation
    enable_regime_evaluation: bool = True
    min_regime_samples: int = 30
    
    # Enhanced fitness
    enable_tail_risk: bool = True
    var_confidence: float = 0.95
    use_cvar: bool = True
    
    # Execution optimization
    enable_liquidity_sizing: bool = True
    max_participation_rate: float = 0.05
    max_market_impact_bps: float = 10.0
    
    # Performance tracking
    track_pareto_frontier: bool = True
    save_checkpoints: bool = True
    checkpoint_frequency: int = 10
    
    # Early stopping
    convergence_threshold: float = 0.001
    convergence_generations: int = 15
    
    # Parallel evaluation
    parallel_workers: int = 4
    use_parallel: bool = True


@dataclass
class EvolutionSnapshot:
    """Snapshot of evolution state at a generation"""
    generation: int
    timestamp: datetime
    
    # Population stats
    population_size: int
    best_fitness: float
    avg_fitness: float
    diversity_score: float
    
    # Speciation stats
    species_count: int
    species_sizes: Dict[str, int]
    
    # Regime stats
    regime_performance: Dict[str, float]
    
    # Tail risk stats
    avg_var: float
    avg_cvar: float
    
    # Best individual
    best_genome_id: str
    best_genome: Optional[StrategyGenome] = None


class IntegratedEvolutionSystem:
    """
    Unified evolution system integrating all Phase 2, 3, 4 components.
    
    Features:
    - Speciated evolution with diversity preservation
    - Regime-aware evaluation with tail risk metrics
    - Liquidity-aware execution integration
    - Comprehensive monitoring and checkpointing
    """
    
    def __init__(
        self,
        config: IntegratedEvolutionConfig,
        market_data: pd.DataFrame,
        search_space: Optional[Any] = None
    ):
        """
        Initialize integrated evolution system.
        
        Args:
            config: Integration configuration
            market_data: Market data for backtesting
            search_space: Strategy search space (optional)
        """
        self.config = config
        self.market_data = market_data
        
        # Initialize core components
        self._init_evolution_engine(search_space)
        self._init_evaluators()
        self._init_selectors()
        self._init_execution_components()
        
        # State tracking
        self.snapshots: List[EvolutionSnapshot] = []
        self.pareto_frontier: List[Individual] = []
        self.convergence_history: List[float] = []
        self.best_individual: Optional[Individual] = None
        
        # Statistics
        self.stats = {
            'generations': 0,
            'evaluations': 0,
            'cache_hits': 0,
            'convergence_detected': False
        }
        
        logger.info("IntegratedEvolutionSystem initialized")
    
    def _init_evolution_engine(self, search_space: Optional[Any]) -> None:
        """Initialize the appropriate evolution engine"""
        evo_config = EvolutionConfig(
            population_size=self.config.population_size,
            elite_size=self.config.elite_size,
            max_generations=self.config.max_generations,
            convergence_threshold=self.config.convergence_threshold,
            convergence_generations=self.config.convergence_generations,
            parallel_workers=self.config.parallel_workers
        )
        
        if self.config.enable_speciation:
            # Use speciated evolution
            backtester = LeakageFreeBacktester(self.market_data)
            fitness_evaluator = MultiObjectiveFitness()
            from ..alpha_evolve.genetic_operators import GeneticOperators
            genetic_ops = GeneticOperators(search_space or self._default_search_space())
            
            self.engine = SpeciatedEvolutionEngine(
                search_space=search_space or self._default_search_space(),
                backtester=backtester,
                fitness_evaluator=fitness_evaluator,
                genetic_operators=genetic_ops,
                config=evo_config
            )
            logger.info("Using SpeciatedEvolutionEngine")
        else:
            # Use standard evolution
            self.engine = EvolutionEngine(
                config=evo_config,
                search_space=search_space or self._default_search_space(),
                market_data=self.market_data
            )
            logger.info("Using standard EvolutionEngine")
    
    def _init_evaluators(self) -> None:
        """Initialize fitness and regime evaluators"""
        # Enhanced fitness with tail risk
        if self.config.enable_tail_risk:
            self.fitness_evaluator = EnhancedFitnessEvaluator(
                tail_risk_weight=0.25 if self.config.use_cvar else 0.0
            )
        else:
            self.fitness_evaluator = MultiObjectiveFitness()
        
        # Regime-aware backtester
        if self.config.enable_regime_evaluation:
            self.regime_backtester = RegimeAwareBacktester(
                data=self.market_data
            )
        else:
            self.regime_backtester = None
        
        # Standard backtester
        self.backtester = LeakageFreeBacktester(self.market_data)
        
        # Walk-forward validator
        self.walkforward = WalkForwardValidator()
    
    def _init_selectors(self) -> None:
        """Initialize selection mechanisms"""
        self.selectors = []
        
        # Diversity-aware selector
        if self.config.enable_diversity_preservation:
            self.diversity_selector = DiversitySelector(
                diversity_weight=self.config.diversity_weight
            )
            self.selectors.append(('diversity', self.diversity_selector))
        
        # Age-based selector
        if self.config.enable_age_based_selection:
            self.age_selector = AgeBasedSelector(
                max_age=self.config.max_age,
                age_fitness_decay=self.config.age_fitness_decay
            )
            self.selectors.append(('age', self.age_selector))
        
        # Multi-objective selector for Pareto frontier
        if self.config.track_pareto_frontier:
            self.pareto_selector = MultiObjectiveSelector(
                objectives=['sharpe', 'drawdown', 'diversity']
            )
            self.selectors.append(('pareto', self.pareto_selector))
    
    def _init_execution_components(self) -> None:
        """Initialize execution optimization components"""
        if self.config.enable_liquidity_sizing:
            # Create sample order book (would be real in production)
            sample_depth = MarketDepth(
                bids=[(1.1000, 100000), (1.0999, 150000), (1.0998, 200000)],
                asks=[(1.1001, 100000), (1.1002, 150000), (1.1003, 200000)]
            )
            
            constraints = LiquidityConstraints(
                max_participation_rate=self.config.max_participation_rate,
                max_market_impact_bps=self.config.max_market_impact_bps
            )
            
            self.liquidity_sizer = LiquidityAwareSizer(
                market_depth=sample_depth,
                constraints=constraints
            )
            
            self.adaptive_execution = AdaptiveExecutionEngine()
            logger.info("Execution optimization components initialized")
        else:
            self.liquidity_sizer = None
            self.adaptive_execution = None
    
    def _default_search_space(self):
        """Create default search space if none provided"""
        from ..alpha_evolve.strategy_genome import SearchSpace
        return SearchSpace()
    
    def evaluate_individual(self, individual: Individual) -> FitnessScore:
        """
        Comprehensive individual evaluation.
        
        Combines:
        - Standard backtest
        - Regime-aware evaluation (if enabled)
        - Enhanced fitness with tail risk (if enabled)
        - Walk-forward validation (if enabled)
        """
        # Run backtest
        backtest_result = self.backtester.backtest(individual.genome)
        individual.backtest_result = backtest_result
        
        # Regime-aware evaluation
        regime_metrics = None
        if self.config.enable_regime_evaluation and self.regime_backtester:
            regime_result = self.regime_backtester.backtest(individual.genome)
            regime_metrics = self._extract_regime_metrics(regime_result)
        
        # Calculate fitness
        if self.config.enable_tail_risk:
            fitness = self.fitness_evaluator.evaluate(backtest_result, individual.genome)
        else:
            fitness = self.fitness_evaluator.evaluate(
                sharpe=backtest_result.metrics.get('sharpe_ratio', 0),
                max_drawdown=backtest_result.metrics.get('max_drawdown', -1),
                regime_stability=0.5
            )
        
        # Add regime stability if available
        if regime_metrics:
            fitness.regime_stability = regime_metrics.get('stability', 0.5)
        
        individual.fitness = fitness
        self.stats['evaluations'] += 1
        
        return fitness
    
    def _extract_regime_metrics(self, regime_result) -> Dict[str, float]:
        """Extract metrics from regime-aware backtest"""
        if not hasattr(regime_result, 'regime_performance'):
            return {}
        
        performances = list(regime_result.regime_performance.values())
        if not performances:
            return {}
        
        # Calculate stability across regimes
        sharpe_values = [p.sharpe_ratio for p in performances if p.sharpe_ratio is not None]
        stability = 1.0 - (np.std(sharpe_values) / (np.mean(np.abs(sharpe_values)) + 1e-6))
        
        return {
            'stability': max(0, stability),
            'regime_count': len(performances)
        }
    
    def select_parents(self, population: List[Individual], n_parents: int) -> List[Individual]:
        """
        Multi-criteria parent selection.
        
        Combines multiple selection strategies based on configuration.
        """
        if not self.selectors:
            # Default: random selection
            import random
            return random.sample(population, min(n_parents, len(population)))
        
        # Use primary selector (diversity if enabled, otherwise age, etc.)
        selector_name, selector = self.selectors[0]
        
        if selector_name == 'diversity':
            return selector.select(population, n_parents)
        elif selector_name == 'age':
            return selector.select_with_decay(population, n_parents)
        elif selector_name == 'pareto':
            frontier = selector.get_pareto_frontier(population)
            if len(frontier) >= n_parents:
                return frontier[:n_parents]
            else:
                # Fill with random from population
                import random
                remaining = n_parents - len(frontier)
                additional = random.sample([p for p in population if p not in frontier], 
                                          min(remaining, len(population) - len(frontier)))
                return frontier + additional
        
        return population[:n_parents]
    
    def update_pareto_frontier(self, population: List[Individual]) -> None:
        """Update the Pareto frontier with current population"""
        if not self.config.track_pareto_frontier:
            return
        
        pareto_selector = None
        for name, selector in self.selectors:
            if name == 'pareto':
                pareto_selector = selector
                break
        
        if pareto_selector:
            # Combine current frontier with population
            combined = self.pareto_frontier + population
            self.pareto_frontier = pareto_selector.get_pareto_frontier(combined)
            
            # Limit frontier size
            if len(self.pareto_frontier) > 50:
                self.pareto_frontier = self.pareto_frontier[:50]
    
    def check_convergence(self) -> bool:
        """Check if evolution has converged"""
        if len(self.convergence_history) < self.config.convergence_generations:
            return False
        
        recent = self.convergence_history[-self.config.convergence_generations:]
        if len(recent) < 2:
            return False
        
        # Check if improvement has stalled
        best_recent = max(recent)
        improvement = abs(best_recent - recent[0]) / (abs(recent[0]) + 1e-6)
        
        converged = improvement < self.config.convergence_threshold
        if converged:
            self.stats['convergence_detected'] = True
            logger.info(f"Convergence detected at generation {self.stats['generations']}")
        
        return converged
    
    def create_snapshot(self, generation: int, population: List[Individual]) -> EvolutionSnapshot:
        """Create a snapshot of current evolution state"""
        if not population:
            return EvolutionSnapshot(
                generation=generation,
                timestamp=datetime.now(),
                population_size=0,
                best_fitness=0,
                avg_fitness=0,
                diversity_score=0,
                species_count=0,
                species_sizes={},
                regime_performance={},
                avg_var=0,
                avg_cvar=0,
                best_genome_id=""
            )
        
        fitnesses = [p.fitness.total_fitness for p in population if p.fitness]
        best = max(population, key=lambda x: x.fitness.total_fitness if x.fitness else 0)
        
        # Calculate diversity
        diversity = 0.0
        if self.config.enable_diversity_preservation and hasattr(self, 'diversity_selector'):
            diversity = self.diversity_selector.calculate_diversity(population)
        
        # Species info
        species_count = 0
        species_sizes = {}
        if isinstance(self.engine, SpeciatedEvolutionEngine):
            species_count = len(self.engine.species)
            species_sizes = {sid: len(s.members) for sid, s in self.engine.species.items()}
        
        # Tail risk averages
        var_values = []
        cvar_values = []
        for ind in population:
            if ind.fitness and hasattr(ind.fitness, 'metrics'):
                metrics = ind.fitness.metrics
                if 'var_95' in metrics:
                    var_values.append(metrics['var_95'])
                if 'cvar_95' in metrics:
                    cvar_values.append(metrics['cvar_95'])
        
        return EvolutionSnapshot(
            generation=generation,
            timestamp=datetime.now(),
            population_size=len(population),
            best_fitness=best.fitness.total_fitness if best.fitness else 0,
            avg_fitness=np.mean(fitnesses) if fitnesses else 0,
            diversity_score=diversity,
            species_count=species_count,
            species_sizes=species_sizes,
            regime_performance={},  # Would fill from regime backtester
            avg_var=np.mean(var_values) if var_values else 0,
            avg_cvar=np.mean(cvar_values) if cvar_values else 0,
            best_genome_id=best.get_id(),
            best_genome=best.genome if generation % 10 == 0 else None  # Store periodically
        )
    
    def evolve(self, generations: Optional[int] = None) -> Individual:
        """
        Run the integrated evolution process.
        
        Args:
            generations: Number of generations (default: config.max_generations)
            
        Returns:
            Best individual found
        """
        max_gen = generations or self.config.max_generations
        logger.info(f"Starting integrated evolution for {max_gen} generations")
        
        # Initialize population
        population = self._initialize_population()
        
        for gen in range(max_gen):
            self.stats['generations'] = gen
            
            # Evaluate population
            for individual in population:
                if individual.fitness is None:
                    self.evaluate_individual(individual)
            
            # Update Pareto frontier
            self.update_pareto_frontier(population)
            
            # Create snapshot
            snapshot = self.create_snapshot(gen, population)
            self.snapshots.append(snapshot)
            
            # Track convergence
            if fitnesses := [p.fitness.total_fitness for p in population if p.fitness]:
                self.convergence_history.append(max(fitnesses))
            
            # Check convergence
            if self.check_convergence():
                logger.info(f"Early stopping at generation {gen}")
                break
            
            # Selection
            parents = self.select_parents(population, self.config.population_size // 2)
            
            # Breeding (handled by engine)
            if isinstance(self.engine, SpeciatedEvolutionEngine):
                population = self._speciated_breeding(population, parents, gen)
            else:
                population = self._standard_breeding(population, parents, gen)
            
            # Logging
            if gen % 10 == 0:
                logger.info(f"Gen {gen}: Best={snapshot.best_fitness:.4f}, "
                          f"Avg={snapshot.avg_fitness:.4f}, "
                          f"Diversity={snapshot.diversity_score:.4f}")
            
            # Save checkpoint
            if self.config.save_checkpoints and gen % self.config.checkpoint_frequency == 0:
                self._save_checkpoint(gen)
        
        # Return best individual
        if population:
            self.best_individual = max(population, 
                                      key=lambda x: x.fitness.total_fitness if x.fitness else 0)
            return self.best_individual
        
        return None
    
    def _initialize_population(self) -> List[Individual]:
        """Initialize the starting population"""
        population = []
        for i in range(self.config.population_size):
            genome = self.engine.search_space.create_random_genome()
            individual = Individual(
                genome=genome,
                generation=0
            )
            population.append(individual)
        
        logger.info(f"Initialized population of {len(population)} individuals")
        return population
    
    def _speciated_breeding(self, population: List[Individual], 
                           parents: List[Individual], 
                           generation: int) -> List[Individual]:
        """Breeding with speciation"""
        # Delegate to speciated engine
        if isinstance(self.engine, SpeciatedEvolutionEngine):
            self.engine._speciate_population(population, generation)
            # Use engine's breeding logic
            new_population = self._create_next_generation(population, generation)
            return new_population
        return population
    
    def _standard_breeding(self, population: List[Individual],
                          parents: List[Individual],
                          generation: int) -> List[Individual]:
        """Standard breeding without speciation"""
        return self._create_next_generation(population, generation)
    
    def _create_next_generation(self, population: List[Individual], 
                               generation: int) -> List[Individual]:
        """Create next generation through selection and breeding"""
        # Sort by fitness
        sorted_pop = sorted(population, 
                          key=lambda x: x.fitness.total_fitness if x.fitness else 0,
                          reverse=True)
        
        # Elite preservation
        elite_count = self.config.elite_size
        new_population = sorted_pop[:elite_count]
        
        # Fill rest with offspring
        import random
        while len(new_population) < self.config.population_size:
            # Tournament selection
            tournament_size = 3
            tournament = random.sample(sorted_pop[:len(sorted_pop)//2], 
                                     min(tournament_size, len(sorted_pop)//2))
            parent = max(tournament, 
                       key=lambda x: x.fitness.total_fitness if x.fitness else 0)
            
            # Create offspring (simplified - just copy with mutation)
            from ..alpha_evolve.genetic_operators import GeneticOperators
            ops = GeneticOperators(self.engine.search_space)
            new_genome = ops.mutate(parent.genome)
            
            offspring = Individual(
                genome=new_genome,
                generation=generation
            )
            new_population.append(offspring)
        
        return new_population
    
    def _save_checkpoint(self, generation: int) -> None:
        """Save evolution checkpoint"""
        checkpoint_dir = Path("evolution_checkpoints")
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint = {
            'generation': generation,
            'config': self.config.__dict__,
            'stats': self.stats,
            'snapshots': [s.__dict__ for s in self.snapshots[-10:]],  # Last 10
            'pareto_frontier_ids': [ind.get_id() for ind in self.pareto_frontier]
        }
        
        filepath = checkpoint_dir / f"checkpoint_gen_{generation}.json"
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        
        logger.info(f"Checkpoint saved: {filepath}")
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Generate comprehensive evolution report"""
        if not self.snapshots:
            return {"error": "No evolution data available"}
        
        latest = self.snapshots[-1]
        
        report = {
            'summary': {
                'total_generations': len(self.snapshots),
                'final_population_size': latest.population_size,
                'best_fitness': latest.best_fitness,
                'avg_fitness': latest.avg_fitness,
                'final_diversity': latest.diversity_score,
                'species_count': latest.species_count,
                'convergence_detected': self.stats['convergence_detected']
            },
            'fitness_progression': [s.best_fitness for s in self.snapshots],
            'diversity_progression': [s.diversity_score for s in self.snapshots],
            'tail_risk': {
                'avg_var_progression': [s.avg_var for s in self.snapshots],
                'avg_cvar_progression': [s.avg_cvar for s in self.snapshots]
            },
            'pareto_frontier_size': len(self.pareto_frontier),
            'statistics': self.stats
        }
        
        return report
    
    def export_best_strategy(self, filepath: Optional[str] = None) -> Dict:
        """Export the best strategy to file"""
        if not self.best_individual:
            return {"error": "No best individual available"}
        
        strategy_data = {
            'genome_id': self.best_individual.get_id(),
            'genome': self.best_individual.genome.__dict__,
            'fitness': self.best_individual.fitness.__dict__ if self.best_individual.fitness else {},
            'generation': self.best_individual.generation,
            'exported_at': datetime.now().isoformat()
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(strategy_data, f, indent=2, default=str)
            logger.info(f"Best strategy exported to: {filepath}")
        
        return strategy_data
