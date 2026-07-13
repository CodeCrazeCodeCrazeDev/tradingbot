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

    # Bayesian Meta-data
    p_lower: float = 0.0 # Credal lower bound
    p_upper: float = 1.0 # Credal upper bound
    vfe: float = 100.0   # Variational Free Energy score

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

    async def run_cycle(self, observation: Dict[str, Any]):
        """Executes the full 19-step scientific reasoning cycle."""
        # 1. Observation
        hyp_id = await self.observe(observation)

        # Steps 2-17 are the core processing pipeline
        pipeline = [
            (HypothesisState.ANOMALY_DETECTION, self.detect_anomalies),
            (HypothesisState.QUESTION_GENERATION, self.generate_questions),
            (HypothesisState.HYPOTHESIS_GENERATION, self.generate_hypothesis),
            (HypothesisState.EVIDENCE_COLLECTION, self.collect_evidence),
            (HypothesisState.WORLD_MODEL_SIMULATION, self.simulate_world),
            (HypothesisState.COUNTERFACTUAL_GENERATION, self.generate_counterfactuals),
            (HypothesisState.ADVERSARIAL_DEBATE, self.adversarial_debate),
            (HypothesisState.EXPERIMENT_DESIGN, self.design_experiment),
            (HypothesisState.EXECUTION, self.execute_experiment),
            (HypothesisState.EVALUATION, self.evaluate_results),
            (HypothesisState.BAYESIAN_UPDATE, self.bayesian_update),
            (HypothesisState.CONFIDENCE_CALIBRATION, self.calibrate_confidence),
            (HypothesisState.KNOWLEDGE_INTEGRATION, self.integrate_knowledge),
            (HypothesisState.MEMORY_CONSOLIDATION, self.consolidate_memory),
            (HypothesisState.POLICY_IMPROVEMENT, self.improve_policy),
            (HypothesisState.CONTINUOUS_MONITORING, self.monitor_hypothesis)
        ]

        for state, step_func in pipeline:
            self.registry[hyp_id].state = state
            await step_func(hyp_id)
            self.registry[hyp_id].last_update = datetime.now()

            # Check for early termination or rejection
            if self.registry[hyp_id].state in [HypothesisState.REJECTED, HypothesisState.DEPRECATED, HypothesisState.SUPERSEDED]:
                logger.info(f"SRE: Early termination for {hyp_id} at state {state}")
                break

        # 18. Hypothesis Retirement (State Transition to end-states)
        if self.registry[hyp_id].state != HypothesisState.REJECTED:
            self.registry[hyp_id].state = HypothesisState.RETIRED
            await self.retire_hypothesis(hyp_id)

        # 19. Automatic Discovery of New Hypotheses
        await self.discover_new_hypotheses()

    async def observe(self, data: Dict[str, Any]) -> str:
        """Step 1: Ingest raw observation."""
        hyp = ScientificHypothesis(
            name=f"Obs-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            state=HypothesisState.OBSERVATION,
            level=PromotionLevel.LEVEL_0
        )
        self.registry[hyp.id] = hyp
        logger.info(f"SRE: Created new hypothesis {hyp.id} from observation.")
        return hyp.id

    async def detect_anomalies(self, hyp_id: str):
        """Step 2: Identify deviations from expected world state."""
        self.registry[hyp_id].state = HypothesisState.ANOMALY_DETECTION
        # Implementation: Compare data vs GWM predictions

    async def generate_questions(self, hyp_id: str):
        """Step 3: Formulate 'Why' questions based on anomalies."""
        self.registry[hyp_id].state = HypothesisState.QUESTION_GENERATION

    async def generate_hypothesis(self, hyp_id: str):
        """Step 4: Create falsifiable claims."""
        self.registry[hyp_id].state = HypothesisState.HYPOTHESIS_GENERATION
        self.registry[hyp_id].level = PromotionLevel.LEVEL_1

    async def collect_evidence(self, hyp_id: str):
        """Step 5: Gather cross-domain supporting/refuting data."""
        self.registry[hyp_id].state = HypothesisState.EVIDENCE_COLLECTION

    async def simulate_world(self, hyp_id: str):
        """Step 6: Run predictive simulations in GWM."""
        self.registry[hyp_id].state = HypothesisState.WORLD_MODEL_SIMULATION

    async def generate_counterfactuals(self, hyp_id: str):
        """Step 7: Ask 'What if' to test causal stability (Do-calculus)."""
        self.registry[hyp_id].state = HypothesisState.COUNTERFACTUAL_GENERATION

    async def adversarial_debate(self, hyp_id: str):
        """Step 8: Subject hypothesis to Verification Swarm challenge."""
        self.registry[hyp_id].state = HypothesisState.ADVERSARIAL_DEBATE
        self.registry[hyp_id].falsification_attempts += 1

    async def design_experiment(self, hyp_id: str):
        """Step 9: Create test methodology (Backtest, Paper, etc.)."""
        self.registry[hyp_id].state = HypothesisState.EXPERIMENT_DESIGN

    async def execute_experiment(self, hyp_id: str):
        """Step 10: Run the test."""
        self.registry[hyp_id].state = HypothesisState.EXECUTION

    async def evaluate_results(self, hyp_id: str):
        """Step 11: Statistical evaluation of outcomes."""
        self.registry[hyp_id].state = HypothesisState.EVALUATION
        self.registry[hyp_id].level = PromotionLevel.LEVEL_2

    async def bayesian_update(self, hyp_id: str):
        """Step 12: Update posterior probabilities P(H|E)."""
        self.registry[hyp_id].state = HypothesisState.BAYESIAN_UPDATE

    async def calibrate_confidence(self, hyp_id: str):
        """Step 13: Adjust confidence based on uncertainty/ambiguity."""
        self.registry[hyp_id].state = HypothesisState.CONFIDENCE_CALIBRATION

    async def integrate_knowledge(self, hyp_id: str):
        """Step 14: Abstract findings into Semantic Memory (HMS)."""
        self.registry[hyp_id].state = HypothesisState.KNOWLEDGE_INTEGRATION
        self.registry[hyp_id].level = PromotionLevel.LEVEL_3

    async def consolidate_memory(self, hyp_id: str):
        """Step 15: Move to long-term Institutional Knowledge."""
        self.registry[hyp_id].state = HypothesisState.MEMORY_CONSOLIDATION

    async def improve_policy(self, hyp_id: str):
        """Step 16: Update trading/research policies (SkillRouter)."""
        self.registry[hyp_id].state = HypothesisState.POLICY_IMPROVEMENT
        self.registry[hyp_id].level = PromotionLevel.LEVEL_4

    async def monitor_hypothesis(self, hyp_id: str):
        """Step 17: Track for drift or alpha decay."""
        self.registry[hyp_id].state = HypothesisState.CONTINUOUS_MONITORING

    async def retire_hypothesis(self, hyp_id: str):
        """Step 18: Transition to final authoritative end-state."""
        hyp = self.registry[hyp_id]

        # Authoritative transition logic
        if hyp.posterior > 0.95 and hyp.validation_score > 0.9:
            hyp.state = HypothesisState.INSTITUTIONALIZED
            hyp.level = PromotionLevel.LEVEL_5
        elif hyp.posterior > 0.8 and hyp.validation_score > 0.7:
            hyp.state = HypothesisState.CONFIRMED
            hyp.level = PromotionLevel.LEVEL_4
        elif hyp.posterior < 0.15:
            hyp.state = HypothesisState.REJECTED
        elif hyp.uncertainty > 0.8:
            hyp.state = HypothesisState.INCONCLUSIVE
        elif hyp.ambiguity > 0.7:
            hyp.state = HypothesisState.DORMANT
        else:
            hyp.state = HypothesisState.DEPRECATED

        logger.info(f"SRE: Hypothesis {hyp_id} retired to state {hyp.state}")

    async def discover_new_hypotheses(self):
        """Step 19: Meta-discovery of new research paths and self-improvement."""
        # Calculate current failure rate
        total = len(self.registry)
        if total < 10:
            return

        rejected = len([h for h in self.registry.values() if h.state == HypothesisState.REJECTED])
        rejection_rate = rejected / total

        if rejection_rate > 0.7:
            logger.warning(f"SRE: High rejection rate detected ({rejection_rate:.2f}). Triggering self-improvement.")
            # Trigger: Relax prior constraints or adjust anomaly thresholds
            await self.hms.store_research_finding({
                "type": "SRE_SELF_IMPROVEMENT",
                "reason": "HIGH_REJECTION_RATE",
                "rate": rejection_rate,
                "action": "ADJUST_GENERATION_PARAMETERS"
            })

    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Retrieve the full scientific lineage graph."""
        return {hid: h.lineage.parent_ids for hid, h in self.registry.items()}

    def get_hypothesis(self, hyp_id: str) -> Optional[ScientificHypothesis]:
        """Retrieve a specific hypothesis from the registry."""
        return self.registry.get(hyp_id)
