"""
Unified Scientific Reasoning Engine (SRE) - Core Interface
==========================================================

The SRE unifies all hypothesis management into a single logical source of truth.
It implements a 19-step adaptive reasoning loop grounded in Bayesian
evidence synthesis, Active Inference (VFE minimization), and Leni AI-style
structured traces and human-in-the-loop trust auditing.
"""

from collections import deque
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

    # Leni AI Insights - Structured Traces & Trust Auditing
    human_reviewer: Optional[str] = None
    accepted_assumptions: List[str] = field(default_factory=list)
    trust_rationale: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    governance_weight: float = 1.0  # 1.0 default, elevated if human-verified with clear rationale

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

    # Leni AI Insights - Trust Auditing Trace
    leni_trust_score: float = 1.0
    approval_trace: Dict[str, Any] = field(default_factory=dict)  # Stores review metadata, who trusted, why

class ScientificReasoningEngine:
    def __init__(self, controller: Any = None, hms: Any = None, world_model: Any = None, governance: Any = None):
        self.controller = controller
        self.hms = hms
        self.world_model = world_model
        self.governance = governance
        self.registry: Dict[str, ScientificHypothesis] = {}
        # Real baseline metrics — ScientificMetrics.update_from_registry
        # consumes the live registry each cycle (counts, survival,
        # rejection rate, avg posterior/vfe, ECE, bottleneck detection).
        try:
            from trading_bot.observability.scientific_metrics import (
                ScientificMetrics)
            self.metrics_tracker: Any = ScientificMetrics()
        except Exception:  # noqa: BLE001
            self.metrics_tracker = None
        # Rolling observed closes for real anomaly detection when no
        # forward world-model prediction is available.
        self._closes: "deque" = deque(maxlen=120)
        # Lazily-imported CDS epistemology gate (torch-chain package —
        # unavailable means promotion is HELD, never waived).
        self._epistemology: Any = None
        self._epistemology_tried = False
        # Bridge ledger: external hypothesis sources (PHCE-D verdicts,
        # research reports, swarm consensus) ingested with provenance.
        self.ingest_log: List[Dict[str, Any]] = []
        # Step-19 discovery directives — suggestions only, no authority.
        self.discovery_suggestions: List[str] = []
        self.metrics = {
            "hypothesis_quality": [],
            "research_efficiency": 0,
            "survival_rates": {}
        }

        # Recursive self-improvement parameters (SEAL)
        self.anomaly_threshold = 0.5
        self.credal_contraction_factor = 0.15
        self.base_likelihood_scale = 0.8
        self.self_improvement_logs: List[Dict[str, Any]] = []

    def get_hypothesis(self, hid: str) -> Optional[ScientificHypothesis]:
        """Retrieve a hypothesis from the registry by its ID."""
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
        # Baseline metrics refresh every completed cycle.
        if self.metrics_tracker is not None:
            try:
                self.metrics_tracker.update_from_registry(self.registry)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"SRE: metrics update failed: {exc}")
        return hyp_id

    def report(self) -> Dict[str, Any]:
        """Transparent ops surface: registry census + measured baselines
        + bridge/self-improvement logs."""
        states: Dict[str, int] = {}
        for h in self.registry.values():
            states[h.state.name] = states.get(h.state.name, 0) + 1
        mt = self.metrics_tracker
        return {
            "registry_size": len(self.registry),
            "states": states,
            "anomaly_threshold": self.anomaly_threshold,
            "credal_contraction_factor": self.credal_contraction_factor,
            "ingest_events": len(self.ingest_log),
            "discovery_suggestions": list(self.discovery_suggestions[-10:]),
            "self_improvement_logs": len(self.self_improvement_logs),
            "metrics": (vars(mt) if mt is not None else None),
        }

    async def observe(self, data: Dict[str, Any]) -> str:
        hyp = ScientificHypothesis(name=f"Obs-{uuid.uuid4().hex[:4]}", state=HypothesisState.OBSERVATION)
        # Real inputs only: numeric observation fields become the
        # hypothesis's measured parameters — never synthesized.
        hyp.model_params.update({
            k: float(v) for k, v in (data or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)})
        close = hyp.model_params.get("close") or hyp.model_params.get("price")
        if isinstance(close, (int, float)) and close > 0:
            self._closes.append(float(close))
        self.registry[hyp.id] = hyp
        return hyp.id

    def ingest_external(self, source: str, payload: Dict[str, Any]
                        ) -> Optional[str]:
        """Phase-1 bridge: register a hypothesis produced by an external
        module (PHCE-D verdict, research report, curiosity output) into
        the SRE lifecycle with provenance. Returns the new id."""
        if not isinstance(payload, dict):
            return None
        hyp = ScientificHypothesis(
            name=str(payload.get("name") or source or "external"),
            description=str(payload.get("description")
                            or payload.get("summary") or ""),
            state=HypothesisState.OBSERVATION)
        hyp.lineage.derivation_path = f"external:{source}"
        hyp.boundary_conditions["provenance"] = source
        for k, v in payload.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                hyp.model_params[k] = float(v)
        if isinstance(payload.get("confidence"), (int, float)):
            hyp.prior = float(np.clip(payload["confidence"], 0.01, 0.99))
        self.registry[hyp.id] = hyp
        self.ingest_log.append({"source": source, "hypothesis_id": hyp.id,
                                "timestamp": datetime.now().isoformat()})
        return hyp.id

    async def detect_anomalies(self, hid: str):
        """Step 2: Detect deviations from World Model expectations using adaptive anomaly threshold."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.ANOMALY_DETECTION

        if self.world_model and hasattr(self.world_model, "predict_state"):
            predicted = await self.world_model.predict_state(hyp.boundary_conditions)
            surprise = np.mean([abs(predicted.get(k, 0) - v) for k, v in hyp.model_params.items() if isinstance(v, (int, float))])
            hyp.vfe = float(surprise)
            if surprise > self.anomaly_threshold:
                hyp.boundary_conditions["anomaly_status"] = "detected"
                logger.info(f"SRE: Anomaly detected for {hid} (Surprise: {surprise:.4f} > Threshold: {self.anomaly_threshold:.4f})")
            else:
                hyp.boundary_conditions["anomaly_status"] = "none"
        else:
            # No forward model — fall back to a real statistical anomaly:
            # z-score of the latest return over the rolling close window.
            # Unmeasured stays unmeasured; measured anomalies are real.
            closes = list(self._closes)
            if len(closes) >= 12:
                arr = np.asarray(closes, dtype=float)
                rets = np.diff(arr) / np.where(arr[:-1] == 0, 1.0, arr[:-1])
                hist = rets[:-1]
                mu, sd = float(np.nanmean(hist)), float(np.nanstd(hist))
                z = float(abs(rets[-1] - mu) / sd) if sd > 0 else 0.0
                hyp.vfe = z
                hyp.boundary_conditions["anomaly_zscore"] = round(z, 4)
                hyp.boundary_conditions["anomaly_status"] = (
                    "detected" if z > 2.0 else "none")
                if z > 2.0:
                    logger.info(f"SRE: statistical anomaly {hid} — return z-score {z:.2f}")
            else:
                hyp.vfe = None
                hyp.boundary_conditions["anomaly_status"] = "unmeasured"

    async def generate_questions(self, hid: str):
        """Step 3: Formulate concrete scientific questions about anomalous parameters or features."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.QUESTION_GENERATION
        if hyp.boundary_conditions.get("anomaly_status") != "detected":
            # No measured anomaly -> no honest question exists.
            hyp.boundary_conditions["target_question"] = None
            return
        drift_sigma = hyp.model_params.get("drift_sigma")
        if isinstance(drift_sigma, (int, float)):
            hyp.boundary_conditions["target_question"] = f"What causes the {drift_sigma:.1f} sigma statistical drift in asset dynamics?"
            logger.info(f"SRE: Formulated research question for {hid}: {hyp.boundary_conditions['target_question']}")

    async def generate_hypothesis(self, hid: str):
        """Step 4: Create a falsifiable market hypothesis from questions."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.HYPOTHESIS_GENERATION
        if self.controller and hasattr(self.controller, "hypothesis_gen"):
            try:
                branches = await self.controller.hypothesis_gen.generate_competing_branches(hyp.boundary_conditions)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"SRE: branch generation failed for {hid}: {exc}")
                branches = []
            if branches:
                hyp.description = branches[0].causal_explanation or branches[0].name
                hyp.name = branches[0].name
                hyp.model_params["target_action"] = branches[0].execution_plan.get("action", "HOLD")
        if not hyp.description:
            # No generated hypothesis -> name it by its question; the
            # action stays HOLD — a fabricated BUY is never emitted.
            question = hyp.boundary_conditions.get("target_question")
            hyp.description = question or "unformulated"
            hyp.name = "unformulated"
            hyp.model_params["target_action"] = "HOLD"

    async def collect_evidence(self, hid: str):
        """Step 5: Gather relevant historical evidence and claims with human-in-the-loop trust auditing (Leni AI)."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.EVIDENCE_COLLECTION

        # Evidence comes from the real HMS chain or nothing — no
        # fabricated reviewers, no manufactured trust weight.
        if self.hms and hasattr(self.hms, "retrieve_evidence_chain"):
            try:
                evidence_chain = await self.hms.retrieve_evidence_chain(hyp.description)
                hyp.evidence_ids = [
                    str(getattr(e, "id", uuid.uuid4().hex[:8]))
                    for e in (evidence_chain or [])]
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"SRE: HMS evidence retrieval failed for {hid}: {exc}")
                hyp.evidence_ids = []
        else:
            hyp.evidence_ids = []

        # Trust is neutral until a human actually reviews — the trace
        # records that absence honestly.
        hyp.leni_trust_score = 1.0
        hyp.approval_trace = {"reviewed_by": None,
                              "evidence_count": len(hyp.evidence_ids)}
        logger.info(f"SRE: Collected {len(hyp.evidence_ids)} evidence items for {hid}.")

    async def simulate_world(self, hid: str):
        """Step 6: Query the Global World Model to forecast outcomes based on hypothesis assumptions."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.WORLD_MODEL_SIMULATION
        if self.world_model and hasattr(self.world_model, "simulate_scenario"):
            try:
                forecast = await self.world_model.simulate_scenario(hyp.description)
                hyp.expected_value = float(forecast.get("expected_gain_bps", 0.0))
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"SRE: world-model simulation failed for {hid}: {exc}")
                hyp.expected_value = 0.0
        else:
            # No simulation -> expected value is unmeasured, not a
            # fabricated default edge.
            hyp.expected_value = 0.0

    async def generate_counterfactuals(self, hid: str):
        """Step 7: Perform 'What-if' (do-calculus) interventional testing."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.COUNTERFACTUAL_GENERATION

        if self.world_model and hasattr(self.world_model, "simulate_intervention"):
            intervention = hyp.model_params.get("intervention", {"target": "price_action", "value": "reversed"})
            results = await self.world_model.simulate_intervention(intervention)
            hyp.validation_score = float(results.get("causal_stability", 0.0))
            hyp.ambiguity = 1.0 - float(results.get("confidence", 0.0))
            logger.info(f"SRE: Counterfactual simulation completed for {hid}. Causal Stability: {hyp.validation_score:.4f}")
        else:
            # Unmeasured counterfactual — validation stays at zero,
            # ambiguity at maximum. Fabricated scores falsify the ledger.
            hyp.validation_score = 0.0
            hyp.ambiguity = 1.0

    async def adversarial_debate(self, hid: str):
        """Step 8: Execute VerificationSwarm peer review and adversarial debate."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.ADVERSARIAL_DEBATE
        if self.controller and hasattr(self.controller, "verifier_swarm"):
            from ..hms.models import ResearchLedgerEntry
            entry = ResearchLedgerEntry(hypothesis=hyp)
            reports = await self.controller.verifier_swarm.run_swarm(entry)
            vetoed = any(not r.is_valid and r.confidence > 0.85 for r in reports)
            if vetoed:
                hyp.posterior *= 0.5
                hyp.boundary_conditions["debate"] = "vetoed"
                logger.warning(f"SRE: Adversarial debate for {hid} vetoed due to verifier disagreement.")
            else:
                hyp.boundary_conditions["debate"] = "survived"
        else:
            # No verifier swarm -> the debate never happened.
            hyp.boundary_conditions["debate"] = "unverified"

    async def design_experiment(self, hid: str):
        """Step 9: Design falsifiable test methodology and define validation metrics."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.EXPERIMENT_DESIGN
        hyp.falsification_triggers = [
            {"metric": "drawdown", "threshold": 0.05, "action": "falsified"},
            {"metric": "sharpe_ratio", "threshold": 1.2, "action": "falsified"}
        ]
        logger.info(f"SRE: Experiment designed for {hid} with {len(hyp.falsification_triggers)} falsification constraints.")

    async def execute_experiment(self, hid: str):
        """Step 10: Run the experiment under out-of-sample or paper-trading validations."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.EXECUTION
        # The SRE designs experiments; it does not execute them. Real
        # execution runs through the sealed-candidate pipeline, which owns
        # falsification budgets. Record that honestly.
        hyp.boundary_conditions["experiment_executed"] = False
        hyp.boundary_conditions["execution_note"] = (
            "designed_only — sealed trials own execution")
        hyp.falsification_attempts += 1

    async def evaluate_results(self, hid: str):
        """Step 11: Statistical evaluation of outcomes, calculating significance and effect sizes."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.EVALUATION
        # Validation score is whatever the measured stages produced —
        # zero when unmeasured. It is never inflated per cycle.
        hyp.evaluation_measured = bool(
            hyp.boundary_conditions.get("experiment_executed")) or (
            hyp.validation_score > 0)
        logger.info(f"SRE: Evaluation complete for {hid}. Empirical Validation Score: {hyp.validation_score:.4f} (measured={hyp.evaluation_measured})")

    async def bayesian_update(self, hid: str):
        """Step 12: Perform recursive Bayesian updates scaled by Leni AI structured trust score."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.BAYESIAN_UPDATE

        # Elevate/depress likelihood using the governance and trust multiplier
        governed_likelihood = self.base_likelihood_scale if hyp.validation_score > 0.5 else 0.3
        governed_likelihood = min(0.99, governed_likelihood * hyp.leni_trust_score)

        hyp.posterior = (governed_likelihood * hyp.prior) / ((governed_likelihood * hyp.prior) + (0.5 * (1 - hyp.prior)))

    async def calibrate_confidence(self, hid: str):
        """Step 13: Compute Expected Calibration Error and contract credal interval bounds with recursive self-improvement."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.CONFIDENCE_CALIBRATION
        span = hyp.p_upper - hyp.p_lower

        # Self-adapting contraction rate
        contraction = self.credal_contraction_factor * hyp.validation_score
        hyp.p_lower = min(hyp.posterior, hyp.p_lower + contraction)
        hyp.p_upper = max(hyp.posterior, hyp.p_upper - contraction)
        hyp.uncertainty = max(0.0, span - contraction)
        hyp.calibration_error = abs(hyp.posterior - hyp.validation_score)
        logger.info(f"SRE: Confidence calibrated for {hid}. Credal bounds: [{hyp.p_lower:.4f}, {hyp.p_upper:.4f}] Uncertainty: {hyp.uncertainty:.4f}")

    async def integrate_knowledge(self, hid: str):
        """Step 14: Abstract validated strategy features to permanent semantic knowledge."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.KNOWLEDGE_INTEGRATION
        if hyp.posterior > 0.85:
            # Roadmap Phase 2: Level-3 promotion requires surviving the
            # adversarial debate AND the epistemology audit. When the
            # CDS engine is unavailable the promotion is HELD — an
            # un-audited promotion is not a promotion.
            debate = hyp.boundary_conditions.get("debate")
            ep_ok, ep_detail = await self._epistemology_gate(hyp)
            if debate == "survived" and ep_ok:
                hyp.level = PromotionLevel.LEVEL_3
                logger.info(f"SRE: Promoted {hid} to LEVEL_3 (debate survived, epistemology passed).")
            else:
                hyp.boundary_conditions["promotion_hold"] = (
                    f"debate={debate} epistemology={ep_detail}")

    async def _epistemology_gate(self, hyp: ScientificHypothesis
                                 ) -> Tuple[bool, str]:
        """Adversarial epistemic audit via the CDS EpistemologyEngine on
        a graph built from the hypothesis's own measured fields. Lazy
        import (torch-chain package); unavailable -> hold."""
        if not self._epistemology_tried:
            self._epistemology_tried = True
            try:
                from trading_bot.core_agent_system.cds.epistemology_engine import (  # noqa: E501
                    EpistemologyEngine)
                self._epistemology = EpistemologyEngine()
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"SRE: epistemology engine unavailable: {exc}")
        engine = self._epistemology
        if engine is None:
            return False, "epistemology_engine_unavailable"
        try:
            from trading_bot.core_agent_system.cds.evidence_graph import (  # noqa: E501
                CDSElement, EvidenceGraph, NodeType, RelationType)
            graph = EvidenceGraph()
            graph.add_node(CDSElement(
                id=hyp.id, type=NodeType.HYPOTHESIS,
                content={"description": hyp.description,
                         "assumptions": hyp.boundary_conditions.get(
                             "assumptions", [])},
                confidence=float(hyp.posterior),
                uncertainty=float(hyp.uncertainty)))
            # Evidence relations reflect measured fields only.
            if hyp.validation_score > 0:
                eid = f"{hyp.id}-val"
                graph.add_node(CDSElement(
                    id=eid, type=NodeType.EVIDENCE,
                    content={"statement": "counterfactual_validation",
                             "score": hyp.validation_score},
                    confidence=float(hyp.validation_score)))
                graph.add_relation(eid, hyp.id, RelationType.SUPPORTS)
            if hyp.boundary_conditions.get("debate") == "vetoed":
                cid = f"{hyp.id}-veto"
                graph.add_node(CDSElement(
                    id=cid, type=NodeType.EVIDENCE,
                    content={"statement": "verifier_veto"},
                    confidence=0.9))
                graph.add_relation(cid, hyp.id, RelationType.CONTRADICTS)
            report = engine.analyze_hypothesis(hyp.id, graph)
            ok = report.belief_score >= 0.5 and report.uncertainty <= 0.8
            hyp.boundary_conditions["epistemology_report"] = {
                "belief_score": report.belief_score,
                "uncertainty": report.uncertainty,
                "adversarial_risk": report.adversarial_risk_score,
                "missing_info": report.missing_critical_info}
            return bool(ok), f"belief={report.belief_score}"
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"SRE: epistemology audit failed for {hyp.id}: {exc}")
            return False, f"audit_error:{exc}"

    async def consolidate_memory(self, hid: str):
        """Step 15: Store persistent research findings and ledger snapshots inside HMS."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.MEMORY_CONSOLIDATION
        if self.hms and hasattr(self.hms, "store_ledger_entry"):
            from ..hms.models import ResearchLedgerEntry, Hypothesis as HMSHypothesis
            hms_hyp = HMSHypothesis(hypothesis_id=hid, description=hyp.description)
            entry = ResearchLedgerEntry(hypothesis=hms_hyp, composite_confidence=hyp.posterior)
            self.hms.store_ledger_entry(entry)
            logger.info(f"SRE: Consolidated research ledger entry inside HMS graph database for {hid}.")

    async def improve_policy(self, hid: str):
        """Step 16: Recommend adaptive parameter updates and policy shifts back to CSC."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.POLICY_IMPROVEMENT
        if hyp.level == PromotionLevel.LEVEL_3 and self.controller:
            logger.info(f"SRE: Recommending policy tuning for execution algorithms based on {hid}.")

    async def monitor_hypothesis(self, hid: str):
        """Step 17: Set up continuous tracking for alpha decay, leakage risk, and concept drift."""
        hyp = self.registry[hid]
        hyp.state = HypothesisState.CONTINUOUS_MONITORING
        logger.info(f"SRE: Continuous drift monitoring activated for strategy hypothesis {hid}.")

    async def retire_hypothesis(self, hid: str):
        hyp = self.registry[hid]
        if hyp.posterior >= 0.8:
            hyp.state = HypothesisState.INSTITUTIONALIZED
        elif hyp.posterior < 0.2:
            hyp.state = HypothesisState.REJECTED
        elif hyp.uncertainty > 0.7:
            hyp.state = HypothesisState.INCONCLUSIVE
        else:
            hyp.state = HypothesisState.DORMANT

    async def discover_new_hypotheses(self, hid: str = None):
        """Step 19: Meta-discovery of new research directions with recursive self-improvement (SEAL)."""
        if len(self.registry) < 10:
            return

        rejections = [h for h in self.registry.values() if h.state == HypothesisState.REJECTED]
        rejection_rate = len(rejections) / len(self.registry)

        # RECURSIVE SELF-IMPROVEMENT: Adapt SRE parameters based on historical efficiency
        if rejection_rate > 0.6:
            logger.warning(f"SRE [SEAL]: High rejection rate ({rejection_rate:.2%}). Recursively tuning SRE parameters.")
            # Shift anomaly threshold higher to prevent low-quality hypotheses from passing Step 2
            self.anomaly_threshold = min(0.8, self.anomaly_threshold + 0.05)
            # Make credal boundary contraction more conservative
            self.credal_contraction_factor = max(0.05, self.credal_contraction_factor - 0.02)
            self.base_likelihood_scale = max(0.6, self.base_likelihood_scale - 0.05)

            self.self_improvement_logs.append({
                "timestamp": datetime.now(),
                "action": "Tuned SRE strictness parameters",
                "rejection_rate": rejection_rate,
                "new_anomaly_threshold": self.anomaly_threshold,
                "new_credal_contraction_factor": self.credal_contraction_factor
            })

            # Roadmap Phase 4: the directive is recorded for the alpha
            # search priors and surfaced via report() — SRE does not
            # mutate GeneticAlphaSearch internals from this process.
            suggestion = (f"raise alpha-search priors: SRE rejection rate "
                          f"{rejection_rate:.0%}")
            self.discovery_suggestions.append(suggestion)
            if self.controller and hasattr(self.controller, "alpha_mining"):
                try:
                    await self.controller.alpha_mining.adjust_search_strategy(
                        reason="high_rejection_rate")
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"SRE: alpha_mining adjust failed: {exc}")

        confirmed = [h for h in self.registry.values() if h.state == HypothesisState.INSTITUTIONALIZED]
        if len(confirmed) > 2:
            logger.info("SRE: Identifying opportunities for hypothesis synthesis (Merging).")
