"""
Self-Transcendence Concepts (91-100): Meta-cognition, emergent intelligence, wisdom.
The bot reasons about its own reasoning, achieving higher-order intelligence.
"""

import logging
import numpy as np
from typing import Any, Dict, List
from collections import deque, defaultdict
from .self_concept_engine import SelfConcept, ConceptCategory

logger = logging.getLogger(__name__)


class SelfTranscendenceConcepts:
    """10 self-transcendence concepts for meta-cognitive intelligence."""

    def __init__(self):
        try:
            self.decision_quality_history = deque(maxlen=200)
            self.meta_confidence = 0.5
            self.concept_effectiveness: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))
            self.wisdom_rules: List[Dict] = []
            self.abstraction_level = 1
            self.paradigm_state = 'normal'
            self.intuition_signals = deque(maxlen=100)
            self.philosophical_state = 'learning'
            self.self_model_accuracy = deque(maxlen=100)
            self.transcendence_score = 0.0
            self.humility_score = 0.5
            self.uncertainty_history = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_concepts(self) -> List[SelfConcept]:
        return [
            SelfConcept(91, "MetaCognitionEngine", ConceptCategory.TRANSCENDENCE,
                        "Reasons about the quality of its own reasoning process"),
            SelfConcept(92, "ConceptEffectivenessAuditor", ConceptCategory.TRANSCENDENCE,
                        "Evaluates which self-concepts are actually improving performance"),
            SelfConcept(93, "WisdomAccumulator", ConceptCategory.TRANSCENDENCE,
                        "Distills high-level trading wisdom from accumulated experience"),
            SelfConcept(94, "AbstractionLevelManager", ConceptCategory.TRANSCENDENCE,
                        "Shifts between detailed and abstract analysis as needed"),
            SelfConcept(95, "ParadigmShiftDetector", ConceptCategory.TRANSCENDENCE,
                        "Detects when fundamental market assumptions need revision"),
            SelfConcept(96, "IntuitionSynthesizer", ConceptCategory.TRANSCENDENCE,
                        "Synthesizes a holistic intuition signal from all subsystems"),
            SelfConcept(97, "EpistemicHumility", ConceptCategory.TRANSCENDENCE,
                        "Knows the limits of its own knowledge and acts accordingly"),
            SelfConcept(98, "UncertaintyQuantifier", ConceptCategory.TRANSCENDENCE,
                        "Quantifies total uncertainty across all decision dimensions"),
            SelfConcept(99, "SelfModelAccuracy", ConceptCategory.TRANSCENDENCE,
                        "Measures how accurately the bot models its own behavior"),
            SelfConcept(100, "TranscendenceIntegrator", ConceptCategory.TRANSCENDENCE,
                        "Integrates all 100 concepts into a unified intelligence score"),
        ]

    def pre_trade(self, snapshot: Dict) -> Dict:
        try:
            signals = {}
            self_concepts = snapshot.get('self_concepts', {})

            # Concept 91: Meta-Cognition Engine
            if len(self.decision_quality_history) >= 10:
                recent_quality = list(self.decision_quality_history)[-10:]
                self.meta_confidence = float(np.mean(recent_quality))
                quality_trend = float(np.mean(recent_quality[-5:]) - np.mean(recent_quality[:5]))
                signals['meta_confidence'] = self.meta_confidence
                signals['reasoning_quality_trend'] = quality_trend
                signals['reasoning_improving'] = quality_trend > 0.02
            else:
                signals['meta_confidence'] = 0.5
                signals['reasoning_quality_trend'] = 0.0
                signals['reasoning_improving'] = False

            # Concept 92: Concept Effectiveness Auditor
            effective_concepts = []
            ineffective_concepts = []
            for concept_id, history in self.concept_effectiveness.items():
                if len(history) >= 10:
                    effectiveness = float(np.mean(list(history)))
                    if effectiveness > 0.6:
                        effective_concepts.append(concept_id)
                    elif effectiveness < 0.3:
                        ineffective_concepts.append(concept_id)
            signals['effective_concepts'] = effective_concepts
            signals['ineffective_concepts'] = ineffective_concepts
            signals['concept_utilization'] = len(effective_concepts) / 100.0

            # Concept 93: Wisdom Accumulator
            signals['wisdom_rules_count'] = len(self.wisdom_rules)
            signals['top_wisdom'] = self.wisdom_rules[:3] if self.wisdom_rules else []

            # Concept 94: Abstraction Level Manager
            vol_state = self_concepts.get('volatility_state', 'normal')
            stress = self_concepts.get('stress_level', 0)
            if stress > 0.5 or vol_state == 'extreme':
                self.abstraction_level = 3  # High-level only
            elif stress < 0.2 and vol_state in ('normal', 'low'):
                self.abstraction_level = 1  # Detailed analysis
            else:
                self.abstraction_level = 2  # Balanced
            signals['abstraction_level'] = self.abstraction_level

            # Concept 95: Paradigm Shift Detector
            consensus_stability = self_concepts.get('decision_stability', 0.5)
            edge_decaying = self_concepts.get('any_edge_decaying', False)
            if consensus_stability < 0.3 and edge_decaying:
                self.paradigm_state = 'shifting'
            elif consensus_stability > 0.7:
                self.paradigm_state = 'stable'
            else:
                self.paradigm_state = 'normal'
            signals['paradigm_state'] = self.paradigm_state
            signals['paradigm_shift_warning'] = self.paradigm_state == 'shifting'

            # Concept 96: Intuition Synthesizer
            intuition_inputs = [
                self_concepts.get('consensus_score', 0),
                self_concepts.get('pattern_match_winrate', 0.5) - 0.5,
                self_concepts.get('reinforcement_signal', 0),
                -1 if self_concepts.get('stress_level', 0) > 0.5 else 0,
                1 if self_concepts.get('success_conditions_present', False) else 0,
                -1 if self_concepts.get('failure_conditions_present', False) else 0,
            ]
            intuition = float(np.tanh(np.mean(intuition_inputs) * 2))
            self.intuition_signals.append(intuition)
            signals['intuition_signal'] = intuition
            signals['intuition_direction'] = (
                'strong_buy' if intuition > 0.5 else
                'buy' if intuition > 0.2 else
                'strong_sell' if intuition < -0.5 else
                'sell' if intuition < -0.2 else 'neutral'
            )

            # Concept 97: Epistemic Humility
            uncertainty = self_concepts.get('volatility_percentile', 0.5)
            conflict_rate = self_concepts.get('conflict_rate', 0)
            self.humility_score = min(1.0, 0.3 + uncertainty * 0.3 + conflict_rate * 0.4)
            signals['humility_score'] = self.humility_score
            signals['should_reduce_size'] = self.humility_score > 0.7
            signals['knowledge_gap'] = self.humility_score > 0.8

            # Concept 98: Uncertainty Quantifier
            uncertainties = [
                self_concepts.get('volatility_percentile', 0.5),
                1.0 - self_concepts.get('confidence', 0.5),
                1.0 - self_concepts.get('decision_stability', 0.5),
                self_concepts.get('false_signal_rate', 0),
            ]
            total_uncertainty = float(np.mean(uncertainties))
            self.uncertainty_history.append(total_uncertainty)
            signals['total_uncertainty'] = total_uncertainty
            signals['uncertainty_regime'] = (
                'very_high' if total_uncertainty > 0.7 else
                'high' if total_uncertainty > 0.5 else
                'moderate' if total_uncertainty > 0.3 else 'low'
            )

            # Concept 99: Self-Model Accuracy
            if len(self.self_model_accuracy) >= 10:
                accuracy = float(np.mean(list(self.self_model_accuracy)))
                signals['self_model_accuracy'] = accuracy
                signals['self_model_reliable'] = accuracy > 0.6
            else:
                signals['self_model_accuracy'] = 0.5
                signals['self_model_reliable'] = False

            # Concept 100: Transcendence Integrator
            concept_scores = [
                self.meta_confidence,
                len(effective_concepts) / 100.0,
                1.0 - self.humility_score * 0.5,  # Some humility is good
                1.0 - total_uncertainty,
                abs(intuition),
            ]
            self.transcendence_score = float(np.mean(concept_scores))
            signals['transcendence_score'] = self.transcendence_score
            signals['intelligence_level'] = (
                'transcendent' if self.transcendence_score > 0.8 else
                'advanced' if self.transcendence_score > 0.6 else
                'developing' if self.transcendence_score > 0.4 else 'nascent'
            )

            signals['impact'] = 1.0
            return signals
        except Exception as e:
            logger.error(f"Error in pre_trade: {e}")
            raise

    def post_trade(self, trade_info: Dict):
        try:
            pnl = trade_info.get('pnl', 0)

            # Update decision quality
            quality = 1.0 if pnl > 0 else 0.0
            self.decision_quality_history.append(quality)

            # Update self-model accuracy
            predicted = trade_info.get('predicted_direction', 0)
            actual_direction = 1 if pnl > 0 else -1
            if predicted != 0:
                accurate = (predicted > 0) == (actual_direction > 0)
                self.self_model_accuracy.append(1.0 if accurate else 0.0)

            # Accumulate wisdom from significant trades
            if abs(pnl) > trade_info.get('avg_pnl', 0) * 2:
                regime = trade_info.get('regime', 'unknown')
                if pnl > 0:
                    rule = {
                        'type': 'success',
                        'regime': regime,
                        'lesson': f"Strong win in {regime} regime - reinforce this pattern",
                    }
                else:
                    rule = {
                        'type': 'failure',
                        'regime': regime,
                        'lesson': f"Significant loss in {regime} regime - avoid this pattern",
                    }
                self.wisdom_rules.append(rule)
                if len(self.wisdom_rules) > 50:
                    self.wisdom_rules = self.wisdom_rules[-50:]
        except Exception as e:
            logger.error(f"Error in post_trade: {e}")
            raise
