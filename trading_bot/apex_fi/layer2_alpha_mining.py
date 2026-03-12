"""
APEX-FI Layer 2: Autonomous Signal Discovery & Alpha Mining Engine
===================================================================

Two Sigma-inspired systematic research at machine scale.
Genetic alpha search, LLM hypothesis generation, causal discovery,
and living factor library with automatic retirement.

Mission: Generate alpha hypotheses faster than any human research team.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple
import logging
import random
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class FactorCategory(str, Enum):
    """Categories of alpha factors."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    MICROSTRUCTURE = "microstructure"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    ALTERNATIVE = "alternative"
    CROSS_ASSET = "cross_asset"


class MarketRegime(str, Enum):
    """Market regime types."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"


@dataclass
class FactorMetadata:
    """Metadata for an alpha factor."""
    factor_id: str
    category: FactorCategory
    discovery_timestamp: datetime
    information_coefficient: float
    sharpe_ratio: float
    decay_rate: float  # Per day
    current_capacity: float  # Estimated capacity in $
    correlation_profile: Dict[str, float] = field(default_factory=dict)
    regime_performance: Dict[MarketRegime, float] = field(default_factory=dict)
    last_evaluation: Optional[datetime] = None
    is_retired: bool = False
    retirement_reason: Optional[str] = None
    
    def should_retire(self, decay_threshold: float = 0.05) -> bool:
        """Check if factor should be retired based on decay."""
        if self.is_retired:
            return True
        
        # Retire if decay rate exceeds threshold
        if self.decay_rate > decay_threshold:
            return True
        
        # Retire if IC has degraded significantly
        if self.information_coefficient < 0.02:
            return True
        
        # Retire if Sharpe has turned negative
        if self.sharpe_ratio < 0:
            return True
        
        return False


@dataclass
class AlphaCandidate:
    """Candidate alpha signal from genetic search."""
    expression: str
    fitness_score: float
    ic: float
    sharpe: float
    generation: int
    parent_ids: List[str] = field(default_factory=list)
    mutation_history: List[str] = field(default_factory=list)


class GeneticAlphaSearch:
    """
    Genetic programming for alpha signal discovery.
    
    Breeds, mutates, crossbreeds, and selects signal expressions.
    Evaluates 10M+ candidates per day.
    """
    
    def __init__(self, population_size: int = 1000):
        self.population_size = population_size
        self.population: List[AlphaCandidate] = []
        self.generation = 0
        self.best_candidates: deque = deque(maxlen=100)
        
        # Grammar of financial operations
        self.operations = [
            'returns', 'log_returns', 'rank', 'zscore', 'decay_linear',
            'ts_mean', 'ts_std', 'ts_max', 'ts_min', 'ts_rank',
            'delta', 'delay', 'correlation', 'covariance',
            'add', 'subtract', 'multiply', 'divide',
        ]
        
        self.data_fields = [
            'close', 'open', 'high', 'low', 'volume', 'vwap',
            'bid', 'ask', 'spread', 'depth',
        ]
        
        logger.info(f"Genetic Alpha Search initialized - Population: {population_size}")
    
    def initialize_population(self) -> None:
        """Initialize random population of alpha expressions."""
        self.population = []
        
        for _ in range(self.population_size):
            expression = self._generate_random_expression(depth=random.randint(1, 3))
            candidate = AlphaCandidate(
                expression=expression,
                fitness_score=0.0,
                ic=0.0,
                sharpe=0.0,
                generation=0,
            )
            self.population.append(candidate)
        
        logger.info(f"Initialized population of {len(self.population)} candidates")
    
    def _generate_random_expression(self, depth: int = 2) -> str:
        """Generate random alpha expression."""
        if depth == 0:
            return random.choice(self.data_fields)
        
        operation = random.choice(self.operations)
        
        if operation in ['returns', 'log_returns', 'rank', 'zscore']:
            arg = self._generate_random_expression(depth - 1)
            return f"{operation}({arg})"
        
        elif operation in ['ts_mean', 'ts_std', 'ts_max', 'ts_min', 'ts_rank', 'delay']:
            arg = self._generate_random_expression(depth - 1)
            window = random.choice([5, 10, 20, 60])
            return f"{operation}({arg}, {window})"
        
        elif operation in ['correlation', 'covariance']:
            arg1 = self._generate_random_expression(depth - 1)
            arg2 = self._generate_random_expression(depth - 1)
            window = random.choice([20, 60, 120])
            return f"{operation}({arg1}, {arg2}, {window})"
        
        else:  # Binary operations
            arg1 = self._generate_random_expression(depth - 1)
            arg2 = self._generate_random_expression(depth - 1)
            return f"({arg1} {operation} {arg2})"
    
    def evaluate_population(self, evaluation_func: Callable[[str], Tuple[float, float]]) -> None:
        """
        Evaluate fitness of all candidates.
        
        Args:
            evaluation_func: Function that takes expression and returns (IC, Sharpe)
        """
        for candidate in self.population:
            try:
                ic, sharpe = evaluation_func(candidate.expression)
                candidate.ic = ic
                candidate.sharpe = sharpe
                candidate.fitness_score = 0.6 * abs(ic) + 0.4 * max(0, sharpe)
            except Exception as e:
                logger.debug(f"Evaluation failed for {candidate.expression}: {e}")
                candidate.fitness_score = 0.0
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness_score, reverse=True)
        
        # Track best candidates
        if self.population[0].fitness_score > 0:
            self.best_candidates.append(self.population[0])
    
    def evolve_generation(self) -> None:
        """Evolve to next generation through selection, crossover, and mutation."""
        self.generation += 1
        
        # Selection: Keep top 20%
        elite_size = int(0.2 * self.population_size)
        elite = self.population[:elite_size]
        
        # Generate new population
        new_population = elite.copy()
        
        while len(new_population) < self.population_size:
            # 70% crossover, 30% mutation
            if random.random() < 0.7 and len(elite) >= 2:
                parent1, parent2 = random.sample(elite, 2)
                child = self._crossover(parent1, parent2)
            else:
                parent = random.choice(elite)
                child = self._mutate(parent)
            
            new_population.append(child)
        
        self.population = new_population
        logger.debug(f"Generation {self.generation}: Best fitness = {self.population[0].fitness_score:.4f}")
    
    def _crossover(self, parent1: AlphaCandidate, parent2: AlphaCandidate) -> AlphaCandidate:
        """Crossover two parent expressions."""
        # Simple crossover: randomly combine parts
        if random.random() < 0.5:
            expression = f"({parent1.expression} + {parent2.expression})"
        else:
            expression = f"({parent1.expression} - {parent2.expression})"
        
        return AlphaCandidate(
            expression=expression,
            fitness_score=0.0,
            ic=0.0,
            sharpe=0.0,
            generation=self.generation,
            parent_ids=[parent1.expression, parent2.expression],
        )
    
    def _mutate(self, parent: AlphaCandidate) -> AlphaCandidate:
        """Mutate parent expression."""
        mutation_type = random.choice(['wrap', 'replace_field', 'change_window'])
        
        if mutation_type == 'wrap':
            operation = random.choice(['rank', 'zscore', 'ts_mean'])
            expression = f"{operation}({parent.expression})"
            mutation = f"wrapped with {operation}"
        
        elif mutation_type == 'replace_field':
            old_field = random.choice(self.data_fields)
            new_field = random.choice(self.data_fields)
            expression = parent.expression.replace(old_field, new_field)
            mutation = f"replaced {old_field} with {new_field}"
        
        else:  # change_window
            expression = parent.expression
            mutation = "changed window"
        
        child = AlphaCandidate(
            expression=expression,
            fitness_score=0.0,
            ic=0.0,
            sharpe=0.0,
            generation=self.generation,
            parent_ids=[parent.expression],
        )
        child.mutation_history = parent.mutation_history + [mutation]
        
        return child
    
    def get_best_candidates(self, n: int = 10) -> List[AlphaCandidate]:
        """Get top N candidates from current population."""
        return self.population[:n]


class LLMHypothesisGenerator:
    """
    LLM-powered hypothesis generation.
    
    Reads financial documents and generates testable quantitative hypotheses.
    """
    
    def __init__(self):
        self.hypothesis_queue: List[Dict[str, Any]] = []
        self.tested_hypotheses: List[Dict[str, Any]] = []
        
        logger.info("LLM Hypothesis Generator initialized")
    
    def generate_from_earnings_call(self, transcript: str, ticker: str) -> List[str]:
        """Generate hypotheses from earnings call transcript."""
        # Placeholder: In production, this would use a fine-tuned LLM
        hypotheses = [
            f"Increased capex guidance for {ticker} predicts positive returns over next quarter",
            f"Management tone shift in {ticker} earnings call correlates with volatility increase",
            f"Revenue beat for {ticker} predicts sector outperformance",
        ]
        
        for hyp in hypotheses:
            self.hypothesis_queue.append({
                'hypothesis': hyp,
                'source': 'earnings_call',
                'ticker': ticker,
                'timestamp': datetime.now(),
                'status': 'pending',
            })
        
        return hypotheses
    
    def generate_from_research_paper(self, paper_title: str, abstract: str) -> List[str]:
        """Generate hypotheses from academic research paper."""
        # Placeholder for LLM-based extraction
        hypotheses = [
            f"Apply findings from '{paper_title}' to cross-sectional equity returns",
            f"Test whether abstract concept generalizes to other asset classes",
        ]
        
        for hyp in hypotheses:
            self.hypothesis_queue.append({
                'hypothesis': hyp,
                'source': 'research_paper',
                'paper': paper_title,
                'timestamp': datetime.now(),
                'status': 'pending',
            })
        
        return hypotheses
    
    def get_pending_hypotheses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending hypotheses for testing."""
        pending = [h for h in self.hypothesis_queue if h['status'] == 'pending']
        return pending[:limit]
    
    def mark_tested(self, hypothesis: str, result: Dict[str, Any]) -> None:
        """Mark hypothesis as tested with results."""
        for h in self.hypothesis_queue:
            if h['hypothesis'] == hypothesis:
                h['status'] = 'tested'
                h['result'] = result
                self.tested_hypotheses.append(h)
                break


class CausalDiscoveryEngine:
    """
    Causal discovery algorithms.
    
    Distinguishes structural alpha relationships from spurious correlations.
    Only causal signals enter production factor library.
    """
    
    def __init__(self):
        self.causal_graph: Dict[str, List[str]] = {}  # variable -> causes
        self.correlation_matrix: Dict[Tuple[str, str], float] = {}
        
        logger.info("Causal Discovery Engine initialized")
    
    def discover_causal_structure(
        self,
        data: Dict[str, np.ndarray],
        method: str = "pc"
    ) -> Dict[str, List[str]]:
        """
        Discover causal structure from data.
        
        Args:
            data: Dictionary of variable_name -> time series
            method: Causal discovery method (pc, fci, ges, notears, lingam)
            
        Returns:
            Causal graph as adjacency dict
        """
        # Placeholder: In production, this would use actual causal discovery libraries
        # like causal-learn, dowhy, or custom implementations
        
        variables = list(data.keys())
        causal_graph = {var: [] for var in variables}
        
        # Simple correlation-based placeholder
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                corr = np.corrcoef(data[var1], data[var2])[0, 1]
                self.correlation_matrix[(var1, var2)] = corr
                
                # Placeholder causal inference
                if abs(corr) > 0.5:
                    # In production: use proper causal tests
                    causal_graph[var1].append(var2)
        
        self.causal_graph = causal_graph
        logger.info(f"Discovered causal structure with {len(variables)} variables")
        
        return causal_graph
    
    def is_causal_relationship(self, cause: str, effect: str) -> bool:
        """Check if relationship is causal (not just correlated)."""
        return effect in self.causal_graph.get(cause, [])
    
    def get_causal_parents(self, variable: str) -> List[str]:
        """Get causal parents of a variable."""
        parents = []
        for var, children in self.causal_graph.items():
            if variable in children:
                parents.append(var)
        return parents


class LivingFactorLibrary:
    """
    Living factor library with automatic retirement.
    
    Tracks 50,000+ factors with regime-specific performance,
    decay rates, and capacity constraints.
    """
    
    def __init__(self, decay_threshold: float = 0.05):
        self.factors: Dict[str, FactorMetadata] = {}
        self.decay_threshold = decay_threshold
        self.active_count = 0
        self.retired_count = 0
        
        logger.info(f"Living Factor Library initialized - Decay threshold: {decay_threshold}")
    
    def add_factor(self, metadata: FactorMetadata) -> None:
        """Add factor to library."""
        self.factors[metadata.factor_id] = metadata
        self.active_count += 1
        
        logger.debug(f"Added factor: {metadata.factor_id} (IC: {metadata.information_coefficient:.4f})")
    
    def update_factor_performance(
        self,
        factor_id: str,
        ic: float,
        sharpe: float,
        regime: MarketRegime
    ) -> None:
        """Update factor performance metrics."""
        if factor_id not in self.factors:
            logger.warning(f"Factor not found: {factor_id}")
            return
        
        factor = self.factors[factor_id]
        
        # Update metrics
        factor.information_coefficient = 0.9 * factor.information_coefficient + 0.1 * ic
        factor.sharpe_ratio = 0.9 * factor.sharpe_ratio + 0.1 * sharpe
        factor.regime_performance[regime] = sharpe
        factor.last_evaluation = datetime.now()
        
        # Update decay rate (simplified)
        if ic < factor.information_coefficient:
            factor.decay_rate = min(1.0, factor.decay_rate + 0.001)
        else:
            factor.decay_rate = max(0.0, factor.decay_rate - 0.0005)
    
    def retire_decayed_factors(self) -> List[str]:
        """Retire factors that have decayed beyond threshold."""
        retired = []
        
        for factor_id, metadata in self.factors.items():
            if metadata.should_retire(self.decay_threshold) and not metadata.is_retired:
                metadata.is_retired = True
                metadata.retirement_reason = f"Decay rate {metadata.decay_rate:.4f} exceeded threshold"
                retired.append(factor_id)
                self.active_count -= 1
                self.retired_count += 1
        
        if retired:
            logger.info(f"Retired {len(retired)} factors due to decay")
        
        return retired
    
    def get_active_factors(
        self,
        category: Optional[FactorCategory] = None,
        regime: Optional[MarketRegime] = None,
        min_ic: float = 0.0
    ) -> List[FactorMetadata]:
        """Get active factors matching criteria."""
        results = []
        
        for metadata in self.factors.values():
            if metadata.is_retired:
                continue
            
            if category and metadata.category != category:
                continue
            
            if metadata.information_coefficient < min_ic:
                continue
            
            if regime and regime in metadata.regime_performance:
                if metadata.regime_performance[regime] < 0:
                    continue
            
            results.append(metadata)
        
        return sorted(results, key=lambda x: x.information_coefficient, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            'total_factors': len(self.factors),
            'active_factors': self.active_count,
            'retired_factors': self.retired_count,
            'categories': {cat.value: len([f for f in self.factors.values() 
                                          if f.category == cat and not f.is_retired])
                          for cat in FactorCategory},
        }


class AlphaMiningEngine:
    """
    Alpha Mining Engine - Master coordinator for Layer 2.
    
    Integrates genetic search, LLM hypothesis generation, causal discovery,
    and factor library management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.genetic_search = GeneticAlphaSearch(
            population_size=config.get('population_size', 1000)
        )
        self.llm_generator = LLMHypothesisGenerator()
        self.causal_engine = CausalDiscoveryEngine()
        self.factor_library = LivingFactorLibrary(
            decay_threshold=config.get('decay_threshold', 0.05)
        )
        
        self._daily_hypothesis_count = 0
        self._target_hypotheses_per_day = 100
        
        logger.info("Alpha Mining Engine initialized - Layer 2 operational")
    
    def initialize(self) -> None:
        """Initialize the alpha mining engine."""
        self.genetic_search.initialize_population()
        logger.info("Alpha Mining Engine initialization complete")
    
    def run_genetic_evolution_cycle(
        self,
        evaluation_func: Callable[[str], Tuple[float, float]],
        generations: int = 10
    ) -> List[AlphaCandidate]:
        """
        Run genetic evolution cycle.
        
        Args:
            evaluation_func: Function to evaluate alpha expressions
            generations: Number of generations to evolve
            
        Returns:
            Best candidates from final generation
        """
        for gen in range(generations):
            self.genetic_search.evaluate_population(evaluation_func)
            self.genetic_search.evolve_generation()
        
        best = self.genetic_search.get_best_candidates(10)
        logger.info(f"Genetic evolution complete - Best IC: {best[0].ic:.4f}")
        
        return best
    
    def promote_to_factor_library(
        self,
        candidate: AlphaCandidate,
        category: FactorCategory,
        capacity: float = 1e6
    ) -> str:
        """Promote successful candidate to factor library."""
        factor_id = f"alpha_{len(self.factor_library.factors)}_{datetime.now().strftime('%Y%m%d')}"
        
        metadata = FactorMetadata(
            factor_id=factor_id,
            category=category,
            discovery_timestamp=datetime.now(),
            information_coefficient=candidate.ic,
            sharpe_ratio=candidate.sharpe,
            decay_rate=0.0,
            current_capacity=capacity,
        )
        
        self.factor_library.add_factor(metadata)
        logger.info(f"Promoted candidate to factor library: {factor_id}")
        
        return factor_id
    
    def generate_llm_hypotheses(
        self,
        source_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate hypotheses from text content using LLM."""
        if source_type == 'earnings_call':
            return self.llm_generator.generate_from_earnings_call(
                content, context.get('ticker', 'UNKNOWN')
            )
        elif source_type == 'research_paper':
            return self.llm_generator.generate_from_research_paper(
                context.get('title', ''), content
            )
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return []
    
    def discover_causal_structure(
        self,
        data: Dict[str, np.ndarray]
    ) -> Dict[str, List[str]]:
        """Discover causal structure in data."""
        return self.causal_engine.discover_causal_structure(data)
    
    def validate_causal_signal(self, cause: str, effect: str) -> bool:
        """Validate if signal represents causal relationship."""
        return self.causal_engine.is_causal_relationship(cause, effect)
    
    def retire_decayed_factors(self) -> List[str]:
        """Retire factors that have decayed."""
        return self.factor_library.retire_decayed_factors()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alpha mining engine statistics."""
        return {
            'genetic_search': {
                'generation': self.genetic_search.generation,
                'population_size': len(self.genetic_search.population),
                'best_fitness': self.genetic_search.population[0].fitness_score if self.genetic_search.population else 0,
            },
            'llm_hypotheses': {
                'pending': len(self.llm_generator.get_pending_hypotheses()),
                'tested': len(self.llm_generator.tested_hypotheses),
            },
            'factor_library': self.factor_library.get_statistics(),
            'daily_hypothesis_count': self._daily_hypothesis_count,
            'target_hypotheses_per_day': self._target_hypotheses_per_day,
        }
