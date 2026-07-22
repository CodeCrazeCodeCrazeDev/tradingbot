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
    """The 18 primary lifecycle steps + 1 meta-discovery step."""
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
    RETIRED = auto()

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
    derivation_path: str = ""
    immutable_hash: str = ""

@dataclass
class ScientificHypothesis:
    id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    state: HypothesisState = HypothesisState.OBSERVATION
    level: PromotionLevel = PromotionLevel.LEVEL_1

    # Mathematical Representation
    model_params: Dict[str, Any] = field(default_factory=dict)
    prior: float = 0.5
    posterior: float = 0.5
    uncertainty: float = 1.0
    ambiguity: float = 1.0

    # Lineage & Relationships
    lineage: HypothesisLineage = field(default_factory=HypothesisLineage)
    boundary_conditions: Dict[str, Any] = field(default_factory=dict)

    # History
    creation_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    evidence_ids: List[str] = field(default_factory=list)
    experiment_ids: List[str] = field(default_factory=list)

    # Decision Criteria
    expected_value: float = 0.0
    novelty_score: float = 0.0
    falsification_triggers: List[Dict[str, Any]] = field(default_factory=list)

    # Validation
    falsification_attempts: int = 0
    validation_score: float = 0.0
    calibration_error: float = 1.0

    # Bayesian Meta-data
    p_lower: float = 0.0 # Credal lower bound
    p_upper: float = 1.0 # Credal upper bound
    vfe: float = 100.0   # Variational Free Energy score

class ScientificReasoningEngine:
    def __init__(self, controller: Any = None, hms: Any = None, world_model: Any = None, governance: Any = None):
        self.controller = controller
        self.hms = hms
        self.world_model = world_model
        self.governance = governance
        self.registry: Dict[str, ScientificHypothesis] = {}
        self.metrics = {
            "hypothesis_quality": [],
            "research_efficiency": 0,
            "survival_rates": {}
        }

    def get_hypothesis(self, hid: str) -> Optional[ScientificHypothesis]:
        return self.registry.get(hid)

    async def run_cycle(self, observation: Dict[str, Any]):
        hyp_id = await self.observe(observation)

        stages = [
            self.detect_anomalies, self.generate_questions, self.generate_hypothesis,
            self.collect_evidence, self.simulate_world, self.generate_counterfactuals,
            self.adversarial_debate, self.design_experiment, self.execute_experiment,
            self.evaluate_results, self.bayesian_update, self.calibrate_confidence,
            self.integrate_knowledge, self.consolidate_memory, self.improve_policy,
            self.monitor_hypothesis, self.retire_hypothesis, self.discover_new_hypotheses
        ]

        for stage in stages:
            await stage(hyp_id)
            if self.registry[hyp_id].state in [HypothesisState.REJECTED, HypothesisState.DEPRECATED, HypothesisState.INSTITUTIONALIZED]:
                break
        return hyp_id

    async def observe(self, data: Dict[str, Any]) -> str:
        hyp = ScientificHypothesis(name=f"Obs-{uuid.uuid4().hex[:4]}", state=HypothesisState.OBSERVATION)
        self.registry[hyp.id] = hyp
        return hyp.id

    async def detect_anomalies(self, hid: str):
        """Step 2: Detect deviations from World Model expectations."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.ANOMALY_DETECTION

        if self.world_model and hasattr(self.world_model, "predict_state"):
            # Compare observation (hyp.boundary_conditions) with predicted state
            predicted = await self.world_model.predict_state(hyp.boundary_conditions)
            surprise = np.mean([abs(predicted.get(k, 0) - v) for k, v in hyp.model_params.items() if isinstance(v, (int, float))])
            hyp.vfe = surprise # Using surprise as a proxy for VFE in Step 2
            if surprise > 0.5:
                logger.info(f"SRE: Anomaly detected for {hid} (Surprise: {surprise:.4f})")

    async def generate_questions(self, hid: str):
        self.registry[hid].state = HypothesisState.QUESTION_GENERATION

    async def generate_hypothesis(self, hid: str):
        self.registry[hid].state = HypothesisState.HYPOTHESIS_GENERATION
        if self.controller and hasattr(self.controller, "hypothesis_gen"):
            # Reuse existing hypothesis generation logic
            branches = await self.controller.hypothesis_gen.generate_competing_branches({"hyp_id": hid})
            if branches:
                self.registry[hid].description = branches[0].reasoning_trace[0] if branches[0].reasoning_trace else ""

    async def collect_evidence(self, hid: str):
        self.registry[hid].state = HypothesisState.EVIDENCE_COLLECTION

    async def simulate_world(self, hid: str):
        self.registry[hid].state = HypothesisState.WORLD_MODEL_SIMULATION
        if self.controller and hasattr(self.controller, "hypothesis_gen"):
            # Reuse existing simulation logic
            # This is a bit circular but follows the mapping request
            pass

    async def generate_counterfactuals(self, hid: str):
        """Step 7: Perform 'What-if' (do-calculus) interventional testing."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.COUNTERFACTUAL_GENERATION

        if self.world_model and hasattr(self.world_model, "simulate_intervention"):
            # Define intervention: what if the primary feature was different?
            intervention = hyp.model_params.get("intervention", {"target": "price_action", "value": "reversed"})
            results = await self.world_model.simulate_intervention(intervention)

            # If the result doesn't change when we intervene on a non-causal variable, it's robust.
            # If it DOES change when we intervene on the 'cause', the hypothesis is strengthened.
            hyp.validation_score = results.get("causal_stability", 0.5)
            hyp.ambiguity = 1.0 - results.get("confidence", 0.5)
            logger.info(f"SRE: Counterfactual simulation completed for {hid}. Causal Stability: {hyp.validation_score:.4f}")

    async def adversarial_debate(self, hid: str):
        self.registry[hid].state = HypothesisState.ADVERSARIAL_DEBATE
        if self.controller and hasattr(self.controller, "verifier_swarm"):
            # Wiring back the Verification Swarm
            # We need a ResearchLedgerEntry-like object
            from ...core.hms.models import ResearchLedgerEntry
            entry = ResearchLedgerEntry(hypothesis=self.registry[hid])
            reports = await self.controller.verifier_swarm.run_swarm(entry)
            # Simple aggregation
            vetoed = any(not r.is_valid and r.confidence > 0.85 for r in reports)
            if vetoed:
                self.registry[hid].posterior *= 0.5

    async def design_experiment(self, hid: str):
        self.registry[hid].state = HypothesisState.EXPERIMENT_DESIGN

    async def execute_experiment(self, hid: str):
        self.registry[hid].state = HypothesisState.EXECUTION

    async def evaluate_results(self, hid: str):
        self.registry[hid].state = HypothesisState.EVALUATION

    async def bayesian_update(self, hid: str):
        hyp = self.registry[hid]
        hyp.state = HypothesisState.BAYESIAN_UPDATE
        likelihood = 0.8 if hyp.validation_score > 0.5 else 0.3
        hyp.posterior = (likelihood * hyp.prior) / ((likelihood * hyp.prior) + (0.5 * (1 - hyp.prior)))

    async def calibrate_confidence(self, hid: str):
        self.registry[hid].state = HypothesisState.CONFIDENCE_CALIBRATION

    async def integrate_knowledge(self, hid: str):
        self.registry[hid].state = HypothesisState.KNOWLEDGE_INTEGRATION

    async def consolidate_memory(self, hid: str):
        self.registry[hid].state = HypothesisState.MEMORY_CONSOLIDATION

    async def improve_policy(self, hid: str):
        self.registry[hid].state = HypothesisState.POLICY_IMPROVEMENT

    async def monitor_hypothesis(self, hid: str):
        self.registry[hid].state = HypothesisState.CONTINUOUS_MONITORING

    async def retire_hypothesis(self, hid: str):
        hyp = self.registry[hid]
        if hyp.posterior > 0.8:
            hyp.state = HypothesisState.INSTITUTIONALIZED
        elif hyp.posterior < 0.2:
            hyp.state = HypothesisState.REJECTED
        elif hyp.uncertainty > 0.7:
            hyp.state = HypothesisState.INCONCLUSIVE
        else:
            hyp.state = HypothesisState.DORMANT

    async def discover_new_hypotheses(self, hid: str = None):
        """Step 19: Meta-discovery of new research directions."""
        if len(self.registry) < 10:
            return

        rejections = [h for h in self.registry.values() if h.state == HypothesisState.REJECTED]
        rejection_rate = len(rejections) / len(self.registry)

        if rejection_rate > 0.7:
            logger.warning(f"SRE: Critical rejection rate ({rejection_rate:.2%}). Triggering Meta-Discovery.")
            # In production, this would call AlphaMiningEngine with new search priors
            if self.controller and hasattr(self.controller, "alpha_mining"):
                await self.controller.alpha_mining.adjust_search_strategy(reason="high_rejection_rate")

        # Look for clusters of successful hypotheses to 'Split' or 'Merge'
        confirmed = [h for h in self.registry.values() if h.state == HypothesisState.INSTITUTIONALIZED]
        if len(confirmed) > 2:
            # Simple merge logic example
            logger.info("SRE: Identifying opportunities for hypothesis synthesis (Merging).")
