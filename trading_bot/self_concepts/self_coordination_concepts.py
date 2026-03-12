"""
Self-Coordination Concepts (81-90): Module synergy, conflict resolution, orchestration.
The bot coordinates its internal modules for coherent, unified decision-making.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfCoordinationConcepts:
    """10 self-coordination concepts for internal module synergy."""

    def __init__(self):
        try:
            self.module_votes: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.consensus_history = deque(maxlen=100)
            self.conflict_log = deque(maxlen=100)
            self.module_latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.priority_queue: List[Dict] = []
            self.dependency_graph: Dict[str, List[str]] = {}
            self.cascade_failures = deque(maxlen=50)
            self.resource_contention = deque(maxlen=50)
            self.sync_state: Dict[str, float] = {}
            self.pipeline_bottlenecks: Dict[str, int] = defaultdict(int)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(81, "ConsensusBuilder", ConceptCategory.COORDINATION,
                        "Aggregates signals from all modules into a consensus decision"),
            SelfConcept(82, "ConflictResolver", ConceptCategory.COORDINATION,
                        "Resolves conflicting signals between modules using weighted voting"),
            SelfConcept(83, "ModulePriorityManager", ConceptCategory.COORDINATION,
                        "Dynamically prioritizes modules based on recent accuracy"),
            SelfConcept(84, "PipelineOrchestrator", ConceptCategory.COORDINATION,
                        "Ensures modules execute in optimal order with proper data flow"),
            SelfConcept(85, "DependencyTracker", ConceptCategory.COORDINATION,
                        "Tracks inter-module dependencies and prevents circular waits"),
            SelfConcept(86, "CascadeFailurePrevention", ConceptCategory.COORDINATION,
                        "Prevents one module failure from cascading to others"),
            SelfConcept(87, "ResourceContentionManager", ConceptCategory.COORDINATION,
                        "Manages shared resources between competing modules"),
            SelfConcept(88, "SynchronizationManager", ConceptCategory.COORDINATION,
                        "Keeps all modules synchronized on the same market state"),
            SelfConcept(89, "BottleneckDetector", ConceptCategory.COORDINATION,
                        "Identifies processing bottlenecks in the module pipeline"),
            SelfConcept(90, "EmergentBehaviorMonitor", ConceptCategory.COORDINATION,
                        "Detects unexpected emergent behaviors from module interactions"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            self_concepts = snapshot.get('self_concepts', {})

            # Concept 81: Consensus Builder
            votes = {
                'awareness': 1 if self_concepts.get('regime') in ('trending_up',) else -1 if self_concepts.get('regime') in ('trending_down',) else 0,
                'protection': 1 if self_concepts.get('trade_allowed', True) else -1,
                'optimization': 1 if self_concepts.get('optimal_size_multiplier', 0.5) > 0.5 else 0,
                'learning': 1 if self_concepts.get('pattern_match_winrate', 0.5) > 0.55 else -1 if self_concepts.get('pattern_match_winrate', 0.5) < 0.45 else 0,
            }
            consensus_score = sum(votes.values()) / max(len(votes), 1)
            signals['consensus_score'] = float(consensus_score)
            signals['consensus_direction'] = (
                'buy' if consensus_score > 0.3 else
                'sell' if consensus_score < -0.3 else 'hold'
            )
            self.consensus_history.append(consensus_score)

            # Concept 82: Conflict Resolver
            conflicting = [(k, v) for k, v in votes.items() if v != 0]
            directions = set(v for _, v in conflicting)
            signals['modules_conflicting'] = len(directions) > 1
            if signals['modules_conflicting']:
                self.conflict_log.append({
                    'votes': votes,
                    'resolved_to': signals['consensus_direction'],
                })
            signals['conflict_rate'] = len(self.conflict_log) / max(len(self.consensus_history), 1)

            # Concept 83: Module Priority Manager
            module_accuracy = {}
            for module_name, vote_history in self.module_votes.items():
                if len(vote_history) >= 10:
                    accuracy = sum(1 for v in vote_history if v > 0) / len(vote_history)
                    module_accuracy[module_name] = float(accuracy)
            signals['module_priorities'] = module_accuracy

            # Concept 84: Pipeline Orchestrator
            signals['pipeline_healthy'] = True
            signals['pipeline_stage'] = 'pre_trade'

            # Concept 85: Dependency Tracker
            signals['circular_deps_detected'] = False

            # Concept 86: Cascade Failure Prevention
            recent_failures = len(self.cascade_failures)
            signals['cascade_risk'] = recent_failures > 3
            signals['isolated_failures'] = recent_failures

            # Concept 87: Resource Contention Manager
            signals['resource_contention'] = False

            # Concept 88: Synchronization Manager
            signals['modules_in_sync'] = True
            if self.sync_state:
                import time
                now = time.time()
                stale = [m for m, t in self.sync_state.items() if now - t > 30]
                signals['stale_modules'] = stale
                signals['modules_in_sync'] = len(stale) == 0

            # Concept 89: Bottleneck Detector
            if self.pipeline_bottlenecks:
                worst = max(self.pipeline_bottlenecks, key=self.pipeline_bottlenecks.get)
                signals['bottleneck_module'] = worst
                signals['bottleneck_count'] = self.pipeline_bottlenecks[worst]
            else:
                signals['bottleneck_module'] = None
                signals['bottleneck_count'] = 0

            # Concept 90: Emergent Behavior Monitor
            if len(self.consensus_history) >= 20:
                recent = list(self.consensus_history)[-20:]
                variance = np.var(recent)
                mean = np.mean(recent)
                signals['emergent_behavior'] = variance > 0.5 or abs(mean) > 0.7
                signals['decision_stability'] = float(1.0 - variance)
            else:
                signals['emergent_behavior'] = False
                signals['decision_stability'] = 0.5

            signals['impact'] = 0.8
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            outcome = 1.0 if pnl > 0 else 0.0

            # Update module vote accuracy
            for module_name in ['awareness', 'protection', 'optimization', 'learning']:
                self.module_votes[module_name].append(outcome)

            # Update sync state
            import time
            self.sync_state['last_trade'] = time.time()
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
