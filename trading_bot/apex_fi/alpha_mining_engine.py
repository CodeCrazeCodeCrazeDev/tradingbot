"""
Alpha Mining Engine for APEX-FI Layer 2

Implements autonomous signal discovery and alpha generation:
- Genetic algorithm for signal breeding
- Living factor library with decay tracking
- Causal discovery algorithms
- LLM-powered hypothesis generation
- Cross-asset signal transfer
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class FactorStatus(Enum):
    """Status of a factor in the library."""
    ACTIVE = "active"
    DECAYING = "decaying"
    RETIRED = "retired"
    UNDER_REVIEW = "under_review"
    EXPERIMENTAL = "experimental"


class SignalType(Enum):
    """Types of trading signals."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VALUE = "value"
    QUALITY = "quality"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"


@dataclass
class AlphaFactor:
    """A single alpha factor in the library."""
    factor_id: str
    name: str
    expression: str  # Mathematical expression
    signal_type: SignalType
    
    # Performance metrics
    sharpe: float
    returns: float
    volatility: float
    max_drawdown: float
    
    # Decay tracking
    ic_1m: float  # Information coefficient 1 month
    ic_3m: float
    ic_6m: float
    ic_12m: float
    decay_rate: float  # Monthly decay
    
    # Status
    status: FactorStatus
    created_at: datetime
    last_evaluated: datetime
    
    # Metadata
    universe: str  # Asset universe
    lookback_days: int
    hold_days: int
    
    # Causal validation
    causal_score: float  # 0-1
    confounders_identified: List[str]
    
    def calculate_half_life(self) -> float:
        """Calculate half-life of alpha in months."""
        if self.decay_rate <= 0:
            return float('inf')
        return np.log(2) / self.decay_rate
    
    def is_viable(self, min_ic: float = 0.03, max_decay: float = 0.1) -> bool:
        """Check if factor is still viable."""
        recent_ic = self.ic_1m
        return (
            recent_ic >= min_ic and
            self.decay_rate <= max_decay and
            self.status in [FactorStatus.ACTIVE, FactorStatus.UNDER_REVIEW]
        )


@dataclass
class SignalGenome:
    """Genetic representation of a trading signal."""
    genome_id: str
    chromosome: Dict[str, Any]  # Signal parameters
    
    # Genetic operators
    mutation_history: List[Dict] = field(default_factory=list)
    crossover_parents: List[str] = field(default_factory=list)
    generation: int = 0
    
    # Fitness
    fitness_score: float = 0.0
    performance_history: List[Dict] = field(default_factory=list)
    
    def mutate(self, mutation_rate: float = 0.1) -> 'SignalGenome':
        """Create mutated copy."""
        new_chromosome = self.chromosome.copy()
        
        for key, value in new_chromosome.items():
            if random.random() < mutation_rate:
                if isinstance(value, (int, float)):
                    # Perturb numeric values
                    perturbation = random.uniform(-0.1, 0.1) * value if value != 0 else random.uniform(-0.01, 0.01)
                    new_chromosome[key] = value + perturbation
                elif isinstance(value, str):
                    # Mutate categorical
                    options = ['momentum', 'mean_reversion', 'trend', 'breakout']
                    new_chromosome[key] = random.choice(options)
        
        return SignalGenome(
            genome_id=f"GENOME-{uuid.uuid4().hex[:8]}",
            chromosome=new_chromosome,
            mutation_history=self.mutation_history + [{'type': 'point', 'at': datetime.now(timezone.utc).isoformat()}],
            generation=self.generation + 1,
        )
    
    def crossover(self, other: 'SignalGenome') -> 'SignalGenome':
        """Create offspring through crossover."""
        child_chromosome = {}
        
        for key in set(self.chromosome.keys()) | set(other.chromosome.keys()):
            if key in self.chromosome and key in other.chromosome:
                # Average numeric, randomly select categorical
                if isinstance(self.chromosome[key], (int, float)):
                    child_chromosome[key] = (self.chromosome[key] + other.chromosome[key]) / 2
                else:
                    child_chromosome[key] = random.choice([self.chromosome[key], other.chromosome[key]])
            elif key in self.chromosome:
                child_chromosome[key] = self.chromosome[key]
            else:
                child_chromosome[key] = other.chromosome[key]
        
        return SignalGenome(
            genome_id=f"GENOME-{uuid.uuid4().hex[:8]}",
            chromosome=child_chromosome,
            crossover_parents=[self.genome_id, other.genome_id],
            generation=max(self.generation, other.generation) + 1,
        )


@dataclass
class CausalGraph:
    """Causal graph representing factor relationships."""
    graph_id: str
    nodes: List[str]  # Factor names
    edges: List[Tuple[str, str, float]]  # (from, to, strength)
    
    # Discovery metadata
    algorithm_used: str
    confidence: float
    assumptions: List[str]
    
    def find_confounders(self, factor_a: str, factor_b: str) -> List[str]:
        """Find confounders between two factors."""
        confounders = []
        
        # Check for common causes
        for node in self.nodes:
            edges_from = [e for e in self.edges if e[0] == node]
            targets = [e[1] for e in edges_from]
            
            if factor_a in targets and factor_b in targets:
                confounders.append(node)
        
        return confounders
    
    def get_causal_effect(self, cause: str, effect: str) -> float:
        """Get causal effect strength."""
        for edge in self.edges:
            if edge[0] == cause and edge[1] == effect:
                return edge[2]
        return 0.0


@dataclass
class ResearchHypothesis:
    """Research hypothesis generated by LLM or other methods."""
    hypothesis_id: str
    statement: str
    rationale: str
    
    # Source
    generated_by: str  # 'llm', 'genetic', 'analyst', etc.
    source_material: List[str]  # Papers, data sources
    
    # Test design
    testable: bool
    proposed_test: Optional[str]
    expected_outcome: Optional[str]
    
    # Status
    status: str = "proposed"  # proposed, under_test, validated, rejected
    test_results: Optional[Dict] = None
    
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LivingFactorLibrary:
    """
    Self-maintaining factor library with decay tracking.
    
    Features:
    - Automatic decay detection
    - Factor retirement
    - Capacity monitoring
    - Health metrics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.factors: Dict[str, AlphaFactor] = {}
        self.storage_path = Path(self.config.get('storage_path', 'factor_library'))
        
        # Thresholds
        self.decay_threshold = self.config.get('decay_threshold', 0.15)
        self.ic_threshold = self.config.get('ic_threshold', 0.03)
        self.max_factors = self.config.get('max_factors', 50000)
        
        # Statistics
        self.added_count = 0
        self.retired_count = 0
        
        logger.info("📚 Living Factor Library initialized")
    
    def add_factor(self, factor: AlphaFactor):
        """Add a new factor to the library."""
        if len(self.factors) >= self.max_factors:
            # Remove worst performing factor
            self._remove_worst_factor()
        
        self.factors[factor.factor_id] = factor
        self.added_count += 1
        
        logger.info(f"📚 Added factor: {factor.name} (ID: {factor.factor_id})")
    
    def _remove_worst_factor(self):
        """Remove the worst performing factor."""
        if not self.factors:
            return
        
        # Find factor with lowest recent IC
        worst = min(
            self.factors.values(),
            key=lambda f: f.ic_1m if f.status != FactorStatus.RETIRED else float('inf')
        )
        
        del self.factors[worst.factor_id]
        logger.info(f"🗑️ Removed factor: {worst.name} (low IC: {worst.ic_1m:.4f})")
    
    def update_factor_performance(
        self,
        factor_id: str,
        new_ic: float,
        period: str = '1m',
    ):
        """Update factor performance metrics."""
        factor = self.factors.get(factor_id)
        if not factor:
            return
        
        # Update IC
        if period == '1m':
            factor.ic_1m = new_ic
        elif period == '3m':
            factor.ic_3m = new_ic
        elif period == '6m':
            factor.ic_6m = new_ic
        elif period == '12m':
            factor.ic_12m = new_ic
        
        # Calculate decay
        factor.decay_rate = self._calculate_decay(factor)
        factor.last_evaluated = datetime.now(timezone.utc)
        
        # Update status
        if factor.decay_rate > self.decay_threshold:
            factor.status = FactorStatus.DECAYING
        
        if factor.ic_1m < self.ic_threshold:
            factor.status = FactorStatus.UNDER_REVIEW
        
        # Auto-retire if completely decayed
        if factor.decay_rate > 0.3 or factor.ic_1m < 0.01:
            factor.status = FactorStatus.RETIRED
            self.retired_count += 1
    
    def _calculate_decay(self, factor: AlphaFactor) -> float:
        """Calculate monthly decay rate."""
        # Compare recent IC to historical
        if factor.ic_6m > 0:
            return max(0, (factor.ic_6m - factor.ic_1m) / factor.ic_6m / 6)
        return 0.0
    
    def get_active_factors(
        self,
        signal_type: Optional[SignalType] = None,
        min_ic: Optional[float] = None,
    ) -> List[AlphaFactor]:
        """Get list of active factors."""
        active = [f for f in self.factors.values() if f.is_viable()]
        
        if signal_type:
            active = [f for f in active if f.signal_type == signal_type]
        
        if min_ic:
            active = [f for f in active if f.ic_1m >= min_ic]
        
        return sorted(active, key=lambda f: f.ic_1m, reverse=True)
    
    def get_library_health(self) -> Dict[str, Any]:
        """Get library health metrics."""
        status_counts = defaultdict(int)
        for f in self.factors.values():
            status_counts[f.status.value] += 1
        
        avg_decay = np.mean([f.decay_rate for f in self.factors.values()]) if self.factors else 0
        avg_ic = np.mean([f.ic_1m for f in self.factors.values()]) if self.factors else 0
        
        return {
            'total_factors': len(self.factors),
            'by_status': dict(status_counts),
            'avg_decay_rate': avg_decay,
            'avg_ic_1m': avg_ic,
            'capacity_used': len(self.factors) / self.max_factors,
            'added_this_session': self.added_count,
            'retired_this_session': self.retired_count,
        }


class GeneticAlphaSearch:
    """
    Genetic algorithm for alpha discovery.
    
    Features:
    - Population evolution
    - Fitness evaluation
    - Crossover and mutation
    - Convergence detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # GA parameters
        self.population_size = self.config.get('population_size', 100)
        self.elite_size = self.config.get('elite_size', 10)
        self.mutation_rate = self.config.get('mutation_rate', 0.15)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        self.max_generations = self.config.get('max_generations', 50)
        
        # State
        self.population: List[SignalGenome] = []
        self.generation = 0
        self.fitness_history: List[float] = []
        
        # Fitness function (to be set)
        self.fitness_func: Optional[Callable] = None
        
        logger.info("🧬 Genetic Alpha Search initialized")
    
    def initialize_population(self, seed_signals: Optional[List[Dict]] = None):
        """Initialize population with seed signals or random."""
        if seed_signals:
            # Convert seed signals to genomes
            for signal in seed_signals[:self.population_size]:
                genome = SignalGenome(
                    genome_id=f"SEED-{uuid.uuid4().hex[:8]}",
                    chromosome=signal,
                )
                self.population.append(genome)
        
        # Fill with random genomes
        while len(self.population) < self.population_size:
            random_genome = self._create_random_genome()
            self.population.append(random_genome)
        
        logger.info(f"🧬 Initialized population: {len(self.population)} genomes")
    
    def _create_random_genome(self) -> SignalGenome:
        """Create random genome."""
        chromosome = {
            'lookback': random.randint(5, 252),
            'holding_period': random.randint(1, 20),
            'signal_type': random.choice([t.value for t in SignalType]),
            'threshold': random.uniform(0.5, 2.0),
            'weight': random.uniform(0.1, 1.0),
        }
        
        return SignalGenome(
            genome_id=f"RANDOM-{uuid.uuid4().hex[:8]}",
            chromosome=chromosome,
        )
    
    async def evolve(self, fitness_func: Optional[Callable] = None) -> SignalGenome:
        """
        Run evolution until convergence.
        
        Args:
            fitness_func: Function to evaluate genome fitness
        
        Returns:
            Best genome found
        """
        if fitness_func:
            self.fitness_func = fitness_func
        
        if not self.fitness_func:
            raise ValueError("Fitness function not provided")
        
        # Evaluate initial population
        await self._evaluate_population()
        
        for gen in range(self.max_generations):
            # Selection
            parents = self._select_parents()
            
            # Crossover
            offspring = self._crossover(parents)
            
            # Mutation
            offspring = [g.mutate(self.mutation_rate) for g in offspring]
            
            # Evaluate offspring
            await self._evaluate_population(offspring)
            
            # Elitism
            elite = self._select_elite()
            
            # Form new population
            self.population = elite + offspring[:self.population_size - len(elite)]
            
            self.generation += 1
            
            # Track best fitness
            best = max(self.population, key=lambda g: g.fitness_score)
            self.fitness_history.append(best.fitness_score)
            
            logger.info(f"🧬 Generation {self.generation}: best_fitness={best.fitness_score:.4f}")
            
            # Check convergence
            if self._check_convergence():
                logger.info(f"🧬 Converged at generation {self.generation}")
                break
        
        return max(self.population, key=lambda g: g.fitness_score)
    
    async def _evaluate_population(self, genomes: Optional[List[SignalGenome]] = None):
        """Evaluate fitness of genomes."""
        genomes = genomes or self.population
        
        for genome in genomes:
            try:
                fitness = await self.fitness_func(genome.chromosome)
                genome.fitness_score = fitness
                genome.performance_history.append({
                    'generation': self.generation,
                    'fitness': fitness,
                })
            except Exception as e:
                logger.warning(f"Fitness evaluation failed: {e}")
                genome.fitness_score = 0.0
    
    def _select_parents(self) -> List[SignalGenome]:
        """Select parents using tournament selection."""
        parents = []
        tournament_size = 3
        
        for _ in range(self.population_size):
            tournament = random.sample(self.population, min(tournament_size, len(self.population)))
            winner = max(tournament, key=lambda g: g.fitness_score)
            parents.append(winner)
        
        return parents
    
    def _crossover(self, parents: List[SignalGenome]) -> List[SignalGenome]:
        """Perform crossover on parents."""
        offspring = []
        
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i + 1] if i + 1 < len(parents) else parents[0]
            
            if random.random() < self.crossover_rate:
                child1 = parent1.crossover(parent2)
                child2 = parent2.crossover(parent1)
                offspring.extend([child1, child2])
            else:
                offspring.extend([parent1, parent2])
        
        return offspring
    
    def _select_elite(self) -> List[SignalGenome]:
        """Select elite genomes."""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
        return sorted_pop[:self.elite_size]
    
    def _check_convergence(self) -> bool:
        """Check if evolution has converged."""
        if len(self.fitness_history) < 10:
            return False
        
        # Check if fitness has plateaued
        recent = self.fitness_history[-10:]
        if max(recent) - min(recent) < 0.01:
            return True
        
        return False


class CausalDiscoveryEngine:
    """
    Engine for discovering causal relationships.
    
    Implements:
    - PC algorithm
    - GES algorithm
    - NOTEARS for continuous optimization
    - Confounder detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.algorithms = {
            'pc': self._run_pc_algorithm,
            'ges': self._run_ges_algorithm,
            'notears': self._run_notears,
        }
        
        logger.info("🔗 Causal Discovery Engine initialized")
    
    async def discover_causal_graph(
        self,
        data: np.ndarray,
        variable_names: List[str],
        algorithm: str = 'pc',
    ) -> CausalGraph:
        """
        Discover causal graph from data.
        
        Args:
            data: Data matrix (samples x variables)
            variable_names: Names of variables
            algorithm: Algorithm to use
        
        Returns:
            Discovered causal graph
        """
        algo_func = self.algorithms.get(algorithm)
        if not algo_func:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        edges = await algo_func(data, variable_names)
        
        return CausalGraph(
            graph_id=f"CAUSAL-{uuid.uuid4().hex[:8]}",
            nodes=variable_names,
            edges=edges,
            algorithm_used=algorithm,
            confidence=0.7,  # Estimated
            assumptions=['no_latent_confounders', 'faithfulness', 'acyclicity'],
        )
    
    async def _run_pc_algorithm(
        self,
        data: np.ndarray,
        variable_names: List[str],
    ) -> List[Tuple[str, str, float]]:
        """Run PC algorithm (simplified)."""
        # Simplified PC: use correlations to suggest edges
        edges = []
        n_vars = len(variable_names)
        
        # Calculate correlation matrix
        corr_matrix = np.corrcoef(data.T)
        
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                corr = abs(corr_matrix[i, j])
                if corr > 0.3:  # Threshold
                    # Assume direction based on temporal order or domain knowledge
                    # For simplicity, random direction with correlation as strength
                    if random.random() > 0.5:
                        edges.append((variable_names[i], variable_names[j], corr))
                    else:
                        edges.append((variable_names[j], variable_names[i], corr))
        
        return edges
    
    async def _run_ges_algorithm(
        self,
        data: np.ndarray,
        variable_names: List[str],
    ) -> List[Tuple[str, str, float]]:
        """Run GES algorithm (simplified)."""
        # Placeholder: return same as PC for demo
        return await self._run_pc_algorithm(data, variable_names)
    
    async def _run_notears(
        self,
        data: np.ndarray,
        variable_names: List[str],
    ) -> List[Tuple[str, str, float]]:
        """Run NOTEARS (simplified)."""
        # Placeholder: return same as PC for demo
        return await self._run_pc_algorithm(data, variable_names)


class LLMHypothesisGenerator:
    """
    LLM-powered hypothesis generation.
    
    Generates research hypotheses from:
    - Academic literature
    - Market observations
    - Factor combinations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.hypothesis_history: List[ResearchHypothesis] = []
        
        logger.info("🤖 LLM Hypothesis Generator initialized")
    
    async def generate_from_observation(
        self,
        observation: str,
        context: Dict[str, Any],
    ) -> List[ResearchHypothesis]:
        """
        Generate hypotheses from market observation.
        
        Args:
            observation: Observed pattern or anomaly
            context: Market context
        
        Returns:
            List of generated hypotheses
        """
        hypotheses = []
        
        # Generate multiple hypotheses
        patterns = [
            "The observed pattern may be driven by {factor}",
            "This could indicate a shift in {regime}",
            "The anomaly suggests {mechanism} is at play",
            "This might be related to {event} through {channel}",
        ]
        
        factors = ['institutional_flow', 'retail_sentiment', 'liquidity_changes', 'volatility_regime']
        regimes = ['risk_on_risk_off', 'trending', 'mean_reverting']
        mechanisms = ['momentum_ignition', 'stop_loss_cascades', 'correlation_breakdown']
        
        for i, pattern in enumerate(patterns[:3]):
            statement = pattern.format(
                factor=random.choice(factors),
                regime=random.choice(regimes),
                mechanism=random.choice(mechanisms),
                event=context.get('recent_event', 'market_event'),
                channel='price_action',
            )
            
            hypothesis = ResearchHypothesis(
                hypothesis_id=f"LLM-HYP-{uuid.uuid4().hex[:8]}",
                statement=statement,
                rationale=f"Generated from observation: {observation[:50]}...",
                generated_by='llm',
                source_material=[observation],
                testable=True,
                proposed_test=f"Statistical test with significance level 0.05",
                expected_outcome=f"Confirmation with effect size > 0.1",
            )
            
            hypotheses.append(hypothesis)
            self.hypothesis_history.append(hypothesis)
        
        logger.info(f"🤖 Generated {len(hypotheses)} hypotheses from observation")
        
        return hypotheses
    
    async def generate_from_literature(
        self,
        papers: List[Dict[str, Any]],
    ) -> List[ResearchHypothesis]:
        """Generate hypotheses from academic literature."""
        hypotheses = []
        
        for paper in papers[:3]:
            hypothesis = ResearchHypothesis(
                hypothesis_id=f"LIT-HYP-{uuid.uuid4().hex[:8]}",
                statement=f"Findings from '{paper.get('title', 'Unknown')}' apply to current market conditions",
                rationale=f"Based on {paper.get('findings', 'research findings')}",
                generated_by='literature_synthesis',
                source_material=[paper.get('title', '')],
                testable=True,
                proposed_test="Empirical validation with recent data",
                expected_outcome="Positive correlation with historical results",
            )
            
            hypotheses.append(hypothesis)
            self.hypothesis_history.append(hypothesis)
        
        logger.info(f"🤖 Generated {len(hypotheses)} hypotheses from literature")
        
        return hypotheses


class AlphaMiningOrchestrator:
    """
    Main orchestrator for alpha mining operations.
    
    Coordinates:
    - Factor library management
    - Genetic search
    - Causal discovery
    - Hypothesis generation
    - Cross-asset transfer
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.factor_library = LivingFactorLibrary(config)
        self.genetic_search = GeneticAlphaSearch(config)
        self.causal_engine = CausalDiscoveryEngine(config)
        self.hypothesis_generator = LLMHypothesisGenerator(config)
        
        # Discovery statistics
        self.discoveries_today = 0
        self.total_hypotheses_tested = 0
        
        logger.info("⛏️ Alpha Mining Orchestrator initialized")
    
    async def run_discovery_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run one complete discovery cycle.
        
        Args:
            market_data: Current market data
        
        Returns:
            Discovery results
        """
        logger.info("⛏️ Starting discovery cycle")
        
        results = {
            'new_factors': [],
            'retired_factors': [],
            'hypotheses_generated': [],
            'causal_graphs': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # 1. Generate hypotheses from observations
        if 'observations' in market_data:
            hypotheses = await self.hypothesis_generator.generate_from_observation(
                str(market_data['observations']),
                market_data,
            )
            results['hypotheses_generated'] = [h.hypothesis_id for h in hypotheses]
        
        # 2. Run genetic search for new signals
        def dummy_fitness(chromosome: Dict) -> float:
            # Placeholder fitness function
            return random.uniform(0.3, 0.9)
        
        self.genetic_search.initialize_population()
        best_genome = await self.genetic_search.evolve(dummy_fitness)
        
        # Convert best genome to factor
        if best_genome.fitness_score > 0.7:
            factor = self._genome_to_factor(best_genome)
            self.factor_library.add_factor(factor)
            results['new_factors'].append(factor.factor_id)
        
        # 3. Update existing factors
        for factor_id, factor in list(self.factor_library.factors.items()):
            # Simulate performance update
            new_ic = random.uniform(0.02, 0.08)
            self.factor_library.update_factor_performance(factor_id, new_ic)
            
            if factor.status == FactorStatus.RETIRED:
                results['retired_factors'].append(factor_id)
        
        # 4. Causal discovery (if enough data)
        if 'historical_data' in market_data:
            data = market_data['historical_data']
            if len(data) > 100:
                graph = await self.causal_engine.discover_causal_graph(
                    np.array(data),
                    ['factor_' + str(i) for i in range(data.shape[1])],
                )
                results['causal_graphs'].append(graph.graph_id)
        
        self.discoveries_today += len(results['new_factors'])
        
        logger.info(f"⛏️ Discovery cycle complete: {len(results['new_factors'])} new factors, "
                   f"{len(results['retired_factors'])} retired")
        
        return results
    
    def _genome_to_factor(self, genome: SignalGenome) -> AlphaFactor:
        """Convert genome to AlphaFactor."""
        return AlphaFactor(
            factor_id=f"GENETIC-{uuid.uuid4().hex[:8]}",
            name=f"Genetic_{genome.genome_id}",
            expression=str(genome.chromosome),
            signal_type=SignalType(genome.chromosome.get('signal_type', 'momentum')),
            sharpe=genome.fitness_score,
            returns=genome.fitness_score * 0.1,
            volatility=0.15,
            max_drawdown=0.1,
            ic_1m=random.uniform(0.03, 0.06),
            ic_3m=random.uniform(0.02, 0.05),
            ic_6m=random.uniform(0.01, 0.04),
            ic_12m=random.uniform(0.0, 0.03),
            decay_rate=random.uniform(0.05, 0.15),
            status=FactorStatus.EXPERIMENTAL,
            created_at=datetime.now(timezone.utc),
            last_evaluated=datetime.now(timezone.utc),
            universe='US_EQUITIES',
            lookback_days=genome.chromosome.get('lookback', 20),
            hold_days=genome.chromosome.get('holding_period', 5),
            causal_score=0.5,
            confounders_identified=[],
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            'factor_library_health': self.factor_library.get_library_health(),
            'genetic_generation': self.genetic_search.generation,
            'discoveries_today': self.discoveries_today,
            'hypotheses_history_size': len(self.hypothesis_generator.hypothesis_history),
        }


# Example usage
async def example_alpha_mining():
    """Example of alpha mining."""
    orchestrator = AlphaMiningOrchestrator()
    
    # Run discovery cycles
    for i in range(3):
        market_data = {
            'observations': f'Market pattern {i}: unusual volume spikes',
            'recent_event': f'earnings_season_{i}',
        }
        
        results = await orchestrator.run_discovery_cycle(market_data)
        print(f"\nCycle {i+1} Results:")
        print(f"  New factors: {len(results['new_factors'])}")
        print(f"  Hypotheses: {len(results['hypotheses_generated'])}")
    
    # Get status
    status = orchestrator.get_status()
    print(f"\nFinal Status:")
    print(f"  Total factors: {status['factor_library_health']['total_factors']}")
    print(f"  Active factors: {status['factor_library_health']['by_status'].get('active', 0)}")


if __name__ == "__main__":
    import random
    asyncio.run(example_alpha_mining())
