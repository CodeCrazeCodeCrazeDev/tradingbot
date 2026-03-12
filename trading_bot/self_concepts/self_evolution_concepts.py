"""
Self-Evolution Concepts (71-80): Strategy mutation, architecture growth, capability expansion.
The bot evolves its own strategies and architecture over time.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfEvolutionConcepts:
    """10 self-evolution concepts for autonomous capability expansion."""

    def __init__(self):
        try:
            self.strategy_pool: Dict[str, Dict] = {}
            self.mutation_history = deque(maxlen=100)
            self.fitness_scores: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.generation = 0
            self.architecture_complexity = 0
            self.feature_candidates = deque(maxlen=50)
            self.retired_strategies = []
            self.innovation_budget = 0.1
            self.crossover_results = deque(maxlen=50)
            self.evolution_velocity = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(71, "StrategyMutator", ConceptCategory.EVOLUTION,
                        "Mutates strategy parameters to explore new configurations"),
            SelfConcept(72, "StrategyCrossover", ConceptCategory.EVOLUTION,
                        "Combines successful strategies to create hybrid offspring"),
            SelfConcept(73, "FitnessEvaluator", ConceptCategory.EVOLUTION,
                        "Evaluates strategy fitness using multi-objective criteria"),
            SelfConcept(74, "NaturalSelection", ConceptCategory.EVOLUTION,
                        "Retires underperforming strategies and promotes winners"),
            SelfConcept(75, "FeatureDiscovery", ConceptCategory.EVOLUTION,
                        "Discovers new features and indicators from raw data"),
            SelfConcept(76, "ArchitectureGrowth", ConceptCategory.EVOLUTION,
                        "Grows architecture complexity when justified by performance"),
            SelfConcept(77, "InnovationBudget", ConceptCategory.EVOLUTION,
                        "Allocates a portion of capital to experimental strategies"),
            SelfConcept(78, "EvolutionaryPressure", ConceptCategory.EVOLUTION,
                        "Increases mutation rate when performance stagnates"),
            SelfConcept(79, "GeneticDiversity", ConceptCategory.EVOLUTION,
                        "Maintains diversity in strategy pool to avoid local optima"),
            SelfConcept(80, "EvolutionVelocityTracker", ConceptCategory.EVOLUTION,
                        "Tracks the rate of improvement across generations"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}

            # Concept 71: Strategy Mutator
            signals['mutation_candidates'] = [
                name for name, info in self.strategy_pool.items()
                if info.get('fitness', 0) < 0.5
            ]
            signals['mutation_rate'] = 0.1 if self.evolution_velocity > 0 else 0.2

            # Concept 72: Strategy Crossover
            top_strategies = sorted(
                self.strategy_pool.items(),
                key=lambda x: x[1].get('fitness', 0),
                reverse=True
            )[:3]
            signals['crossover_parents'] = [s[0] for s in top_strategies]

            # Concept 73: Fitness Evaluator
            fitness_report = {}
            for name, scores in self.fitness_scores.items():
                if len(scores) >= 5:
                    fitness_report[name] = {
                        'mean': float(np.mean(list(scores))),
                        'trend': float(np.mean(list(scores)[-5:]) - np.mean(list(scores)[:5])),
                        'consistency': float(1.0 - np.std(list(scores))),
                    }
            signals['fitness_report'] = fitness_report

            # Concept 74: Natural Selection
            signals['strategies_to_retire'] = [
                name for name, info in fitness_report.items()
                if info.get('mean', 0) < 0.3 and info.get('trend', 0) < 0
            ]
            signals['strategies_to_promote'] = [
                name for name, info in fitness_report.items()
                if info.get('mean', 0) > 0.7 and info.get('trend', 0) > 0
            ]

            # Concept 75: Feature Discovery
            signals['new_features_available'] = len(self.feature_candidates)

            # Concept 76: Architecture Growth
            signals['architecture_complexity'] = self.architecture_complexity
            signals['growth_justified'] = (
                len(fitness_report) > 0 and
                np.mean([f.get('mean', 0) for f in fitness_report.values()]) > 0.6
            )

            # Concept 77: Innovation Budget
            signals['innovation_budget'] = self.innovation_budget
            signals['innovation_allocation'] = self.innovation_budget * 0.1

            # Concept 78: Evolutionary Pressure
            if len(self.mutation_history) >= 20:
                recent_improvements = sum(1 for m in list(self.mutation_history)[-20:] if m > 0)
                stagnation = recent_improvements < 5
                signals['evolutionary_pressure'] = 'high' if stagnation else 'normal'
                signals['increase_mutation'] = stagnation
            else:
                signals['evolutionary_pressure'] = 'normal'
                signals['increase_mutation'] = False

            # Concept 79: Genetic Diversity
            if self.strategy_pool:
                unique_types = len(set(
                    info.get('type', 'unknown') for info in self.strategy_pool.values()
                ))
                signals['genetic_diversity'] = unique_types / max(len(self.strategy_pool), 1)
                signals['diversity_low'] = signals['genetic_diversity'] < 0.3
            else:
                signals['genetic_diversity'] = 1.0
                signals['diversity_low'] = False

            # Concept 80: Evolution Velocity Tracker
            if len(self.mutation_history) >= 10:
                first_half = list(self.mutation_history)[:len(self.mutation_history)//2]
                second_half = list(self.mutation_history)[len(self.mutation_history)//2:]
                self.evolution_velocity = float(np.mean(second_half) - np.mean(first_half))
            signals['evolution_velocity'] = self.evolution_velocity
            signals['evolution_accelerating'] = self.evolution_velocity > 0.01

            signals['generation'] = self.generation
            signals['impact'] = 0.6
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            strategy = trade_info.get('strategy', 'default')
            pnl = trade_info.get('pnl', 0)

            # Update fitness scores
            fitness = 1.0 if pnl > 0 else 0.0
            self.fitness_scores[strategy].append(fitness)

            # Track mutations
            if trade_info.get('is_mutated', False):
                improvement = pnl - trade_info.get('baseline_pnl', 0)
                self.mutation_history.append(improvement)

            # Update strategy pool
            if strategy not in self.strategy_pool:
                self.strategy_pool[strategy] = {'type': 'default', 'fitness': 0.5}
            pool_entry = self.strategy_pool[strategy]
            pool_entry['fitness'] = 0.9 * pool_entry.get('fitness', 0.5) + 0.1 * fitness
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
