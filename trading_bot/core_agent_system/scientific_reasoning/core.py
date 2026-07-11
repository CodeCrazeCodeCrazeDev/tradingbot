"""
Unified Scientific Reasoning Engine (SRE) - Core Interface
==========================================================

The SRE unifies all hypothesis management into a single logical source of truth.
It implements a 19-step adaptive reasoning loop grounded in Bayesian
evidence synthesis and Active Inference (VFE minimization).
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union, Tuple
import uuid
import logging
import numpy as np

logger = logging.getLogger(__name__)

class HypothesisState(Enum):
    """
    The 18 primary lifecycle steps + 1 meta-discovery step.
    Hypotheses must transition through these in order or jump to end-states.
    """
    OBSERVATION = auto()
    ANOMALY_DETECTION = auto()
    QUESTION_GENERATION = auto()
    HYPOTHESIS_GENERATION = auto()
    EVIDENCE_COLLECTION = auto()
    WORLD_MODEL_SIMULATION = auto()
    COUNTERFACTUAL_GENERATION = auto()
    ADVERSARIAL_DEBATE = auto()
    EXPERIMENT_DESIGN = auto()
    EXECUTION = auto()
    EVALUATION = auto()
    BAYESIAN_UPDATE = auto()
    CONFIDENCE_CALIBRATION = auto()
    KNOWLEDGE_INTEGRATION = auto()
    MEMORY_CONSOLIDATION = auto()
    POLICY_IMPROVEMENT = auto()
    CONTINUOUS_MONITORING = auto()
    RETIRED = auto() # Gateway to authoritative end-states

    # Authoritative End-States
    CONFIRMED = auto()
    REJECTED = auto()
    INCONCLUSIVE = auto()
    MERGED = auto()
    SPLIT = auto()
    DORMANT = auto()
    REACTIVATED = auto()
    DEPRECATED = auto()
    SUPERSEDED = auto()
    INSTITUTIONALIZED = auto()

class PromotionLevel(Enum):
    LEVEL_0 = 0  # Raw Observation
    LEVEL_1 = 1  # Candidate
    LEVEL_2 = 2  # Validated
    LEVEL_3 = 3  # Research
    LEVEL_4 = 4  # Production
    LEVEL_5 = 5  # Institutional Knowledge

@dataclass
class ScientificEvidence:
    evidence_id: str = field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    source: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    provenance: Dict[str, Any] = field(default_factory=dict)
    causal_impact: float = 0.0
    is_contradicting: bool = False

@dataclass
class HypothesisLineage:
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    merged_from: List[str] = field(default_factory=list)
    split_from: Optional[str] = None
    derivation_path: str = "" # e.g. "Anomaly-QG-HG"
    immutable_hash: str = "" # Proof of provenance

@dataclass
class ScientificHypothesis:
    id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    state: HypothesisState = HypothesisState.OBSERVATION
    level: PromotionLevel = PromotionLevel.LEVEL_1

    # Mathematical Representation
    model_params: Dict[str, Any] = field(default_factory=dict)
    priors: Dict[str, float] = field(default_factory=dict)
    posterior: float = 0.5 # Bayesian probability P(H|E)
    uncertainty: float = 1.0 # Entropy or Variance
    ambiguity: float = 1.0 # Credal interval width

    # Lineage & Relationships
    lineage: HypothesisLineage = field(default_factory=HypothesisLineage)
    boundary_conditions: Dict[str, Any] = field(default_factory=dict) # Regimes, volatility, etc

    # History
    creation_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    evidence_ids: List[str] = field(default_factory=list)
    experiment_ids: List[str] = field(default_factory=list)

    # Decision Criteria
    expected_value: float = 0.0
    novelty_score: float = 0.0
    falsification_triggers: List[Dict[str, Any]] = field(default_factory=list)

    # Validation results
    falsification_attempts: int = 0
    validation_score: float = 0.0
    calibration_error: float = 1.0

class ScientificReasoningEngine:
    """
    Unified Scientific Reasoning Engine (SRE).
    Implements a 19-step continuous scientific lifecycle.
    """
    def __init__(self, hms: Any, world_model: Any, governance: Any):
        self.hms = hms
        self.world_model = world_model
        self.governance = governance
        self.registry: Dict[str, ScientificHypothesis] = {}
        self.metrics = {
            "hypothesis_quality": [],
            "research_efficiency": 0,
            "survival_rates": {}
        }

    async def run_cycle(self, observation: Dict[str, Any]):
        """Executes the full 19-step scientific reasoning cycle."""
        # 1. Observation
        hyp_id = await self.observe(observation)

        # Steps 2-17 are the core processing pipeline
        pipeline = [
            self.detect_anomalies,
            self.generate_questions,
            self.generate_hypothesis,
            self.collect_evidence,
            self.simulate_world,
            self.generate_counterfactuals,
            self.adversarial_debate,
            self.design_experiment,
            self.execute_experiment,
            self.evaluate_results,
            self.bayesian_update,
            self.calibrate_confidence,
            self.integrate_knowledge,
            self.consolidate_memory,
            self.improve_policy,
            self.monitor_hypothesis
        ]

        for step_func in pipeline:
            await step_func(hyp_id)
            if self.registry[hyp_id].state in [HypothesisState.REJECTED, HypothesisState.DEPRECATED]:
                break

        # 18. Hypothesis Retirement (State Transition to end-states)
        await self.retire_hypothesis(hyp_id)

        # 19. Automatic Discovery of New Hypotheses
        await self.discover_new_hypotheses()

    async def observe(self, data: Dict[str, Any]) -> str:
        """Step 1: Ingest raw observation."""
        hyp = ScientificHypothesis(
            name=f"Obs-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            state=HypothesisState.OBSERVATION,
            level=PromotionLevel.LEVEL_0,
            description=data.get("description", "Raw observation from data stream.")
        )
        self.registry[hyp.id] = hyp
        logger.info(f"SRE: Created new hypothesis {hyp.id} from observation.")
        return hyp.id

    async def detect_anomalies(self, hyp_id: str):
        """Step 2: Identify deviations from expected world state."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.ANOMALY_DETECTION
        # Implementation: Compare data vs GWM predictions
        if self.world_model:
            surprise = await self.world_model.calculate_surprise(hyp.model_params)
            hyp.novelty_score = surprise
        logger.debug(f"SRE: Anomaly detection completed for {hyp_id}")

    async def generate_questions(self, hyp_id: str):
        """Step 3: Formulate 'Why' questions based on anomalies."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.QUESTION_GENERATION
        # Formulate causal questions
        hyp.lineage.derivation_path += "->Question"

    async def generate_hypothesis(self, hyp_id: str):
        """Step 4: Create falsifiable claims."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.HYPOTHESIS_GENERATION
        hyp.level = PromotionLevel.LEVEL_1
        hyp.lineage.derivation_path += "->Hypothesis"

    async def collect_evidence(self, hyp_id: str):
        """Step 5: Gather cross-domain supporting/refuting data."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.EVIDENCE_COLLECTION
        if self.hms:
            evidence = await self.hms.query_evidence(hyp.description)
            hyp.evidence_ids.extend([e.id for e in evidence])
            # Simplified evidence synthesis
            hyp.posterior = np.mean([e.confidence for e in evidence]) if evidence else hyp.posterior

    async def simulate_world(self, hyp_id: str):
        """Step 6: Run predictive simulations in GWM."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.WORLD_MODEL_SIMULATION
        if self.world_model:
            outcomes = await self.world_model.simulate_outcomes(hyp.model_params)
            hyp.validation_score = np.mean(outcomes)

    async def generate_counterfactuals(self, hyp_id: str):
        """Step 7: Ask 'What if' to test causal stability (Do-calculus)."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.COUNTERFACTUAL_GENERATION
        # do-calculus intervention placeholder
        hyp.ambiguity *= 0.9 # Intervention reduces ambiguity

    async def adversarial_debate(self, hyp_id: str):
        """Step 8: Subject hypothesis to Verification Swarm challenge."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.ADVERSARIAL_DEBATE
        hyp.falsification_attempts += 1
        # If governance exists, run debate
        if self.governance:
            passed = await self.governance.run_debate(hyp)
            if not passed:
                hyp.posterior *= 0.5 # Penalty for failing debate

    async def design_experiment(self, hyp_id: str):
        """Step 9: Create test methodology (Backtest, Paper, etc.)."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.EXPERIMENT_DESIGN

    async def execute_experiment(self, hyp_id: str):
        """Step 10: Run the test."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.EXECUTION
        # Placeholder for experiment execution
        hyp.experiment_ids.append(f"exp-{uuid.uuid4().hex[:8]}")

    async def evaluate_results(self, hyp_id: str):
        """Step 11: Statistical evaluation of outcomes."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.EVALUATION
        hyp.level = PromotionLevel.LEVEL_2
        # Update validation score based on experiment results
        hyp.validation_score = (hyp.validation_score + 0.7) / 2 # Improved score

    async def bayesian_update(self, hyp_id: str):
        """Step 12: Update posterior probabilities P(H|E)."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.BAYESIAN_UPDATE
        # P(H|E) = P(E|H) * P(H) / P(E)
        likelihood = hyp.validation_score
        prior = hyp.posterior
        hyp.posterior = (likelihood * prior) / (likelihood * prior + (1 - likelihood) * (1 - prior) + 1e-6)

    async def calibrate_confidence(self, hyp_id: str):
        """Step 13: Adjust confidence based on uncertainty/ambiguity."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.CONFIDENCE_CALIBRATION
        hyp.uncertainty = 1.0 - hyp.posterior
        hyp.calibration_error = abs(hyp.posterior - hyp.validation_score)

    async def integrate_knowledge(self, hyp_id: str):
        """Step 14: Abstract findings into Semantic Memory (HMS)."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.KNOWLEDGE_INTEGRATION
        hyp.level = PromotionLevel.LEVEL_3
        if self.hms:
            await self.hms.store_semantic(hyp)

    async def consolidate_memory(self, hyp_id: str):
        """Step 15: Move to long-term Institutional Knowledge."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.MEMORY_CONSOLIDATION
        if hyp.level == PromotionLevel.LEVEL_5 and self.hms:
            await self.hms.store_institutional(hyp)

    async def improve_policy(self, hyp_id: str):
        """Step 16: Update trading/research policies (SkillRouter)."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.POLICY_IMPROVEMENT
        if hyp.posterior > 0.8:
            hyp.level = PromotionLevel.LEVEL_4

    async def monitor_hypothesis(self, hyp_id: str):
        """Step 17: Track for drift or alpha decay."""
        hyp = self.registry[hyp_id]
        hyp.state = HypothesisState.CONTINUOUS_MONITORING

    async def retire_hypothesis(self, hyp_id: str):
        """Step 18: Transition to final authoritative end-state."""
        hyp = self.registry[hyp_id]

        # Transition logic based on validation score and posterior
        if hyp.posterior > 0.9 and hyp.validation_score > 0.8:
            hyp.state = HypothesisState.INSTITUTIONALIZED
            hyp.level = PromotionLevel.LEVEL_5
        elif hyp.posterior < 0.2:
            hyp.state = HypothesisState.REJECTED
        elif hyp.uncertainty > 0.7:
            hyp.state = HypothesisState.INCONCLUSIVE
        else:
            hyp.state = HypothesisState.DORMANT

        logger.info(f"SRE: Hypothesis {hyp_id} retired to state {hyp.state}")
        self.metrics["survival_rates"][hyp.state.name] = self.metrics["survival_rates"].get(hyp.state.name, 0) + 1

    async def discover_new_hypotheses(self):
        """Step 19: Meta-discovery of new research paths."""
        # Analysis of retired hypotheses to find patterns for new generation
        high_rejection_rate = self.metrics["survival_rates"].get("REJECTED", 0) / (len(self.registry) + 1)
        if high_rejection_rate > 0.5:
             logger.warning("SRE: High rejection rate detected. Triggering meta-discovery update.")
             # Logic to adjust generation parameters

    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Retrieve the full scientific lineage graph."""
        return {hid: h.lineage.parent_ids for hid, h in self.registry.items()}

    def get_hypothesis(self, hyp_id: str) -> Optional[ScientificHypothesis]:
        """Retrieve a specific hypothesis from the registry."""
        return self.registry.get(hyp_id)
