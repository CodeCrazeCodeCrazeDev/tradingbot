"""
AlphaEvolve: Self-Evolving Edge Discovery and Capital Allocation Engine

A rigorous, statistically-grounded evolutionary search system for discovering,
validating, and exploiting decaying market edges faster than competitors.

Core Components:
- Strategy Genome: Formal representation of trading strategies
- Genetic Operators: Mutation, crossover, recombination
- Leakage-Free Backtesting: Realistic costs, slippage, no lookahead
- Multi-Objective Fitness: Sharpe, drawdown, regime stability, tail risk
- Walk-Forward Validation: Out-of-sample testing
- Evolutionary Loop: Generate → Mutate → Evaluate → Select → Repeat
"""

from .strategy_genome import StrategyGenome, Signal, SignalType, SearchSpace
from .genetic_operators import GeneticOperators
from .backtesting_engine import LeakageFreeBacktester
from .fitness_evaluator import MultiObjectiveFitness, FitnessScore
from .walk_forward import WalkForwardValidator
from .evolution_engine import EvolutionEngine, EvolutionConfig, Individual
from .edge_monitor import EdgeDecayMonitor
from .backtest_cache import BacktestCache
from .parallel_evaluator import ParallelEvaluator, DistributedEvaluator
from .speciated_evolution_engine import SpeciatedEvolutionEngine, Species, SpeciationConfig
from .diversity_selection import (
    DiversitySelector, DiversityMetrics, AgeBasedSelector,
    MultiObjectiveSelector
)
from .regime_aware_backtester import (
    RegimeAwareBacktester, RegimeClassifier, MarketRegime,
    RegimeMetrics, RegimeDetectionConfig, MonteCarloValidator
)
from .enhanced_fitness import EnhancedFitnessEvaluator, EnhancedFitnessScore
from .composite_strategy import (
    CompositeStrategy, AdaptiveSignal, CombinationType,
    CombinationLogic, create_composite_strategy, create_adaptive_strategy
)
from .integrated_evolution import (
    IntegratedEvolutionSystem, IntegratedEvolutionConfig,
    EvolutionSnapshot
)
from .distributed_evaluation import (
    DistributedEvaluationFramework, ParallelEvaluator,
    BacktestCache, EvaluationTask, EvaluationResult
)

__all__ = [
    # Core
    'StrategyGenome',
    'Signal',
    'SignalType',
    'SearchSpace',
    'GeneticOperators',
    'LeakageFreeBacktester',
    'MultiObjectiveFitness',
    'FitnessScore',
    'EvolutionEngine',
    'EvolutionConfig',
    'Individual',
    'WalkForwardValidator',
    'EdgeDecayMonitor',
    'BacktestCache',
    'ParallelEvaluator',
    'DistributedEvaluator',
    # Phase 2: Evolution Enhancements
    'SpeciatedEvolutionEngine',
    'Species',
    'SpeciationConfig',
    'DiversitySelector',
    'DiversityMetrics',
    'AgeBasedSelector',
    'MultiObjectiveSelector',
    # Phase 3: Evaluation Improvements
    'RegimeAwareBacktester',
    'RegimeClassifier',
    'MarketRegime',
    'RegimeMetrics',
    'RegimeDetectionConfig',
    'MonteCarloValidator',
    'EnhancedFitnessEvaluator',
    'EnhancedFitnessScore',
    # Strategy Representation
    'CompositeStrategy',
    'AdaptiveSignal',
    'CombinationType',
    'CombinationLogic',
    'create_composite_strategy',
    'create_adaptive_strategy',
    # Phase 5: Integration
    'IntegratedEvolutionSystem',
    'IntegratedEvolutionConfig',
    'EvolutionSnapshot',
    'DistributedEvaluationFramework',
    'BacktestCache',
    'EvaluationTask',
    'EvaluationResult',
]
