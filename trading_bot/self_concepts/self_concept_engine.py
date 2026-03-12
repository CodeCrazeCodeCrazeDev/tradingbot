"""
Self-Concept Engine - Core orchestrator for all 100 self-concepts.
Each concept is a discrete, measurable capability that the bot uses
to introspect, adapt, and improve its own trading performance.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ConceptCategory(Enum):
    AWARENESS = "self_awareness"
    DIAGNOSIS = "self_diagnosis"
    OPTIMIZATION = "self_optimization"
    PROTECTION = "self_protection"
    LEARNING = "self_learning"
    ADAPTATION = "self_adaptation"
    CORRECTION = "self_correction"
    EVOLUTION = "self_evolution"
    COORDINATION = "self_coordination"
    TRANSCENDENCE = "self_transcendence"


class ConceptStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


@dataclass
class SelfConcept:
    """A single self-concept: a discrete autonomous capability."""
    id: int
    name: str
    category: ConceptCategory
    description: str
    status: ConceptStatus = ConceptStatus.IDLE
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown_seconds: float = 5.0
    impact_score: float = 0.0
    enabled: bool = True

    def can_trigger(self) -> bool:
        if not self.enabled or self.status == ConceptStatus.DISABLED:
            return False
        if self.last_triggered is None:
            return True
        elapsed = (datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown_seconds

    def record_trigger(self, impact: float = 0.0):
        self.last_triggered = datetime.now()
        self.trigger_count += 1
        self.status = ConceptStatus.TRIGGERED
        self.impact_score = 0.9 * self.impact_score + 0.1 * impact


class SelfConceptEngine:
    """
    Master engine that manages all 100 self-concepts.
    Provides pre_trade and post_trade hooks for the main trading loop.
    """

    def __init__(self):
        self.concepts: Dict[int, SelfConcept] = {}
        self.category_modules: Dict[ConceptCategory, Any] = {}
        self.metrics: Dict[str, float] = {
            'total_triggers': 0,
            'avg_impact': 0.0,
            'active_concepts': 0,
            'last_cycle_ms': 0.0,
        }
        self._load_all_concepts()
        logger.info(f"SelfConceptEngine initialized with {len(self.concepts)} concepts")

    def _load_all_concepts(self):
        """Load all 100 self-concepts from category modules."""
        from .self_awareness_concepts import SelfAwarenessConcepts
        from .self_diagnosis_concepts import SelfDiagnosisConcepts
        from .self_optimization_concepts import SelfOptimizationConcepts
        from .self_protection_concepts import SelfProtectionConcepts
        from .self_learning_concepts import SelfLearningConcepts
        from .self_adaptation_concepts import SelfAdaptationConcepts
        from .self_correction_concepts import SelfCorrectionConcepts
        from .self_evolution_concepts import SelfEvolutionConcepts
        from .self_coordination_concepts import SelfCoordinationConcepts
        from .self_transcendence_concepts import SelfTranscendenceConcepts

        modules = [
            (ConceptCategory.AWARENESS, SelfAwarenessConcepts()),
            (ConceptCategory.DIAGNOSIS, SelfDiagnosisConcepts()),
            (ConceptCategory.OPTIMIZATION, SelfOptimizationConcepts()),
            (ConceptCategory.PROTECTION, SelfProtectionConcepts()),
            (ConceptCategory.LEARNING, SelfLearningConcepts()),
            (ConceptCategory.ADAPTATION, SelfAdaptationConcepts()),
            (ConceptCategory.CORRECTION, SelfCorrectionConcepts()),
            (ConceptCategory.EVOLUTION, SelfEvolutionConcepts()),
            (ConceptCategory.COORDINATION, SelfCoordinationConcepts()),
            (ConceptCategory.TRANSCENDENCE, SelfTranscendenceConcepts()),
        ]

        for category, module in modules:
            self.category_modules[category] = module
            for concept in module.get_concepts():
                self.concepts[concept.id] = concept

    def pre_trade_process(self, market_snapshot: Dict) -> Dict:
        """Run all pre-trade self-concepts on the market snapshot."""
        t0 = time.perf_counter()
        enriched = dict(market_snapshot)
        self_signals = {}

        for category, module in self.category_modules.items():
            try:
                result = module.pre_trade(enriched)
                if isinstance(result, dict):
                    self_signals.update(result)
                    for concept in module.get_concepts():
                        if concept.can_trigger():
                            concept.record_trigger(impact=result.get('impact', 0.0))
                            self.metrics['total_triggers'] += 1
            except Exception as e:
                logger.debug(f"Self-concept {category.value} pre-trade: {e}")

        enriched['self_concepts'] = self_signals
        self.metrics['last_cycle_ms'] = (time.perf_counter() - t0) * 1000
        self.metrics['active_concepts'] = sum(
            1 for c in self.concepts.values() if c.status == ConceptStatus.TRIGGERED
        )
        return enriched

    def post_trade_process(self, trade_info: Dict):
        """Run all post-trade self-concepts."""
        for category, module in self.category_modules.items():
            try:
                module.post_trade(trade_info)
            except Exception as e:
                logger.debug(f"Self-concept {category.value} post-trade: {e}")

    def get_status(self) -> Dict:
        """Return status of all self-concepts."""
        by_category = {}
        for cat in ConceptCategory:
            concepts = [c for c in self.concepts.values() if c.category == cat]
            by_category[cat.value] = {
                'count': len(concepts),
                'active': sum(1 for c in concepts if c.status == ConceptStatus.TRIGGERED),
                'total_triggers': sum(c.trigger_count for c in concepts),
                'avg_impact': sum(c.impact_score for c in concepts) / max(len(concepts), 1),
            }
        return {
            'total_concepts': len(self.concepts),
            'metrics': self.metrics,
            'by_category': by_category,
        }
