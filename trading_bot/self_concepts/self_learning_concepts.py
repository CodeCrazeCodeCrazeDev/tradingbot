"""
Self-Learning Concepts (41-50): Pattern extraction, knowledge accumulation, memory.
The bot learns from every trade and market observation to improve future decisions.
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfLearningConcepts:
    """10 self-learning concepts for continuous knowledge acquisition."""

    def __init__(self):
        try:
            self.pattern_memory: Dict[str, List[float]] = defaultdict(list)
            self.regime_transitions = deque(maxlen=200)
            self.last_regime = 'unknown'
            self.failure_patterns = deque(maxlen=100)
            self.success_patterns = deque(maxlen=100)
            self.market_fingerprints = deque(maxlen=500)
            self.edge_decay_tracker: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
            self.knowledge_base: Dict[str, Any] = {}
            self.analogy_cache: Dict[str, Dict] = {}
            self.feedback_buffer = deque(maxlen=200)
            self.meta_learning_state = {'learning_rate': 0.01, 'momentum': 0.0}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(41, "PatternMemoryBank", ConceptCategory.LEARNING,
                        "Stores and retrieves successful/failed trade patterns"),
            SelfConcept(42, "RegimeTransitionLearner", ConceptCategory.LEARNING,
                        "Learns regime transition probabilities from history"),
            SelfConcept(43, "FailurePostMortem", ConceptCategory.LEARNING,
                        "Extracts lessons from every losing trade"),
            SelfConcept(44, "SuccessAmplifier", ConceptCategory.LEARNING,
                        "Identifies and reinforces conditions that led to wins"),
            SelfConcept(45, "MarketFingerprinting", ConceptCategory.LEARNING,
                        "Creates fingerprints of market states for similarity matching"),
            SelfConcept(46, "EdgeDecayTracker", ConceptCategory.LEARNING,
                        "Monitors whether a strategy edge is decaying over time"),
            SelfConcept(47, "KnowledgeConsolidator", ConceptCategory.LEARNING,
                        "Consolidates scattered learnings into actionable rules"),
            SelfConcept(48, "AnalogyEngine", ConceptCategory.LEARNING,
                        "Finds analogous historical situations to current market"),
            SelfConcept(49, "ReinforcementFeedback", ConceptCategory.LEARNING,
                        "Provides reward/penalty signals to reinforce good behavior"),
            SelfConcept(50, "MetaLearningRate", ConceptCategory.LEARNING,
                        "Adjusts learning rate based on environment stability"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            price = snapshot.get('price', 0.0)
            vol = snapshot.get('volatility', 0.01)
            regime = snapshot.get('self_concepts', {}).get('regime', 'unknown')

            # Concept 41: Pattern Memory Bank
            fingerprint = self._create_fingerprint(snapshot)
            similar = self._find_similar_patterns(fingerprint)
            if similar:
                win_rate = sum(1 for s in similar if s > 0) / max(len(similar), 1)
                signals['pattern_match_winrate'] = float(win_rate)
                signals['pattern_match_count'] = len(similar)
            else:
                signals['pattern_match_winrate'] = 0.5
                signals['pattern_match_count'] = 0

            # Concept 42: Regime Transition Learner
            if regime != self.last_regime and self.last_regime != 'unknown':
                self.regime_transitions.append((self.last_regime, regime))
            self.last_regime = regime
            transition_probs = self._calc_transition_probs(regime)
            signals['regime_transition_probs'] = transition_probs
            signals['regime_stability'] = transition_probs.get(regime, 0.5)

            # Concept 43: Failure Post-Mortem
            if len(self.failure_patterns) >= 5:
                common_conditions = self._extract_common_conditions(self.failure_patterns)
                signals['failure_conditions_present'] = self._check_conditions(snapshot, common_conditions)
            else:
                signals['failure_conditions_present'] = False

            # Concept 44: Success Amplifier
            if len(self.success_patterns) >= 5:
                common_conditions = self._extract_common_conditions(self.success_patterns)
                signals['success_conditions_present'] = self._check_conditions(snapshot, common_conditions)
            else:
                signals['success_conditions_present'] = False

            # Concept 45: Market Fingerprinting
            self.market_fingerprints.append(fingerprint)
            signals['market_novelty'] = self._calc_novelty(fingerprint)

            # Concept 46: Edge Decay Tracker
            edge_signals = {}
            for strategy_name, results in self.edge_decay_tracker.items():
                if len(results) >= 20:
                    first_half = list(results)[:len(results)//2]
                    second_half = list(results)[len(results)//2:]
                    decay = np.mean(first_half) - np.mean(second_half)
                    edge_signals[strategy_name] = float(decay)
            signals['edge_decay'] = edge_signals
            signals['any_edge_decaying'] = any(v > 0.05 for v in edge_signals.values())

            # Concept 47: Knowledge Consolidator
            signals['knowledge_rules'] = len(self.knowledge_base)

            # Concept 48: Analogy Engine
            signals['historical_analogy'] = self._find_analogy(snapshot)

            # Concept 49: Reinforcement Feedback
            if len(self.feedback_buffer) >= 10:
                recent_reward = np.mean([f.get('reward', 0) for f in list(self.feedback_buffer)[-10:]])
                signals['reinforcement_signal'] = float(recent_reward)
            else:
                signals['reinforcement_signal'] = 0.0

            # Concept 50: Meta-Learning Rate
            if len(self.feedback_buffer) >= 20:
                recent_var = np.var([f.get('reward', 0) for f in list(self.feedback_buffer)[-20:]])
                self.meta_learning_state['learning_rate'] = max(0.001, min(0.1, 0.01 / max(recent_var, 0.01)))
            signals['meta_learning_rate'] = self.meta_learning_state['learning_rate']

            signals['impact'] = 0.7
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)
            fingerprint = trade_info.get('fingerprint', {})
            strategy = trade_info.get('strategy', 'default')

            if pnl > 0:
                self.success_patterns.append(trade_info)
            else:
                self.failure_patterns.append(trade_info)

            self.edge_decay_tracker[strategy].append(pnl)
            self.feedback_buffer.append({'reward': 1.0 if pnl > 0 else -1.0, 'pnl': pnl})

            # Consolidate knowledge periodically
            if len(self.feedback_buffer) % 50 == 0:
                self._consolidate_knowledge()
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise

    def _create_fingerprint(self, snapshot: Dict) -> Dict:
        return {
            'price': snapshot.get('price', 0),
            'vol': snapshot.get('volatility', 0),
            'rsi': snapshot.get('rsi', 50),
            'regime': snapshot.get('self_concepts', {}).get('regime', 'unknown'),
        }

    def _find_similar_patterns(self, fingerprint: Dict) -> List[float]:
        try:
            results = []
            for pattern in self.success_patterns:
                if pattern.get('fingerprint', {}).get('regime') == fingerprint.get('regime'):
                    results.append(pattern.get('pnl', 0))
            for pattern in self.failure_patterns:
                if pattern.get('fingerprint', {}).get('regime') == fingerprint.get('regime'):
                    results.append(pattern.get('pnl', 0))
            return results[-20:]
        except Exception as e:
            logger.error(f"Error in _find_similar_patterns: {e}")
            raise

    def _calc_transition_probs(self, current_regime: str) -> Dict[str, float]:
        try:
            transitions_from = [t[1] for t in self.regime_transitions if t[0] == current_regime]
            if not transitions_from:
                return {}
            counts = defaultdict(int)
            for t in transitions_from:
                counts[t] += 1
            total = len(transitions_from)
            return {k: v / total for k, v in counts.items()}
        except Exception as e:
            logger.error(f"Error in _calc_transition_probs: {e}")
            raise

    def _extract_common_conditions(self, patterns) -> Dict:
        try:
            if not patterns:
                return {}
            regimes = [p.get('regime', 'unknown') for p in patterns if isinstance(p, dict)]
            if regimes:
                most_common = max(set(regimes), key=regimes.count)
                return {'regime': most_common}
            return {}
        except Exception as e:
            logger.error(f"Error in _extract_common_conditions: {e}")
            raise

    def _check_conditions(self, snapshot: Dict, conditions: Dict) -> bool:
        try:
            regime = snapshot.get('self_concepts', {}).get('regime', 'unknown')
            return regime == conditions.get('regime')
        except Exception as e:
            logger.error(f"Error in _check_conditions: {e}")
            raise

    def _calc_novelty(self, fingerprint: Dict) -> float:
        try:
            if len(self.market_fingerprints) < 10:
                return 0.5
            regime_counts = defaultdict(int)
            for fp in self.market_fingerprints:
                regime_counts[fp.get('regime', 'unknown')] += 1
            current = fingerprint.get('regime', 'unknown')
            freq = regime_counts.get(current, 0) / len(self.market_fingerprints)
            return float(1.0 - freq)
        except Exception as e:
            logger.error(f"Error in _calc_novelty: {e}")
            raise

    def _find_analogy(self, snapshot: Dict) -> Optional[str]:
        try:
            regime = snapshot.get('self_concepts', {}).get('regime', 'unknown')
            vol_state = snapshot.get('self_concepts', {}).get('volatility_state', 'normal')
            key = f"{regime}_{vol_state}"
            return self.analogy_cache.get(key, None)
        except Exception as e:
            logger.error(f"Error in _find_analogy: {e}")
            raise

    def _consolidate_knowledge(self):
        try:
            if len(self.success_patterns) >= 10:
                conditions = self._extract_common_conditions(list(self.success_patterns)[-20:])
                if conditions:
                    self.knowledge_base['success_conditions'] = conditions
            if len(self.failure_patterns) >= 10:
                conditions = self._extract_common_conditions(list(self.failure_patterns)[-20:])
                if conditions:
                    self.knowledge_base['failure_conditions'] = conditions
        except Exception as e:
            logger.error(f"Error in _consolidate_knowledge: {e}")
            raise
