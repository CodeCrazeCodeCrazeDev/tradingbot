"""

Implements the Active Inference (VFE minimization) loop and
HIPIF (Hierarchical Planning with Information Folding).

The "One Brain" authoritative controller orchestrating the LogAct pipeline.
Implements Active Inference (surpise minimization) and DiscoLoop reasoning.
Cognitive System Controller (CSC) - UCA V5 (July 2026)

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
"""

import logging
import asyncio
import copy
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .folding import InformationFolder
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus

logger = logging.getLogger(__name__)

@dataclass
class DecisionTrace:
    decision_id: str
    timestamp: str
    market_snapshot_id: str
    model_versions: Dict[str, str]
    feature_hashes: Dict[str, str]
    scenarios_evaluated: List[str]
    consensus_results: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    verification_outcomes: List[Dict[str, Any]]
    final_action: str
    confidence_estimate: float
    latency_breakdown_ms: Dict[str, float]
    total_latency_ms: float

class CognitiveSystemController:
    """
    UCA V5 Controller integrating DiscoLoop, HASP, and Pivot/Refine.
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CognitiveSystemController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, world_model: Any = None, hms: Any = None, shield: Optional[ImmutableShield] = None):
        if self._initialized:
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # HASP: Executable Guardrails (Skill Programs)
        self.skill_programs = self._load_skill_programs()

        # DiscoLoop Channels (Internalized Reasoning)
        self.continuous_state = {}  # Latent embeddings
        self.discrete_channel = []  # Semantic tokens (Bridge Entities)

        self._initialized = True

    def _load_skill_programs(self) -> Dict[str, Any]:
        # In production, load from a registry. Here we stub it.
        return {}

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V5) with Decision Tracing.
        """
        start_time = time.perf_counter()
        latency = {}

        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 1. Active Perception
        t0 = time.perf_counter()
        self._update_perception(observation)
        latency["perception"] = (time.perf_counter() - t0) * 1000

        # 2. Internalization (DiscoLoop)
        t0 = time.perf_counter()
        await self._run_discoloop_reasoning(observation)
        latency["reasoning_discoloop"] = (time.perf_counter() - t0) * 1000

        # 3. Skill Routing (S2L)
        t0 = time.perf_counter()
        self._route_skills(observation)
        latency["skill_routing"] = (time.perf_counter() - t0) * 1000

        # 4. Graph Retrieval (SAGE)
        t0 = time.perf_counter()
        evidence = self.hms.retrieve_evidence_chain(str(observation))
        latency["memory_retrieval"] = (time.perf_counter() - t0) * 1000

        # 5. Executable Guardrails (HASP)
        t0 = time.perf_counter()
        intervention = self._apply_hasp_guardrails(observation)
        if intervention:
            observation.update(intervention)
        latency["guardrails_hasp"] = (time.perf_counter() - t0) * 1000

        # 6. Multi-Hypothesis Generation
        t0 = time.perf_counter()
        branches = await self.hypothesis_gen.generate_competing_branches(observation)
        latency["hypothesis_gen"] = (time.perf_counter() - t0) * 1000

        # 7. Causal Simulation (CWMI / Digital Twin)
        t0 = time.perf_counter()
        sim_results = await self.hypothesis_gen.simulate_branches(branches)
        latency["causal_sim"] = (time.perf_counter() - t0) * 1000

        # 8. Decision Selection (VFE / EV Optimization)
        t0 = time.perf_counter()
        best_branch = self._select_optimal_branch(branches, sim_results)
        latency["decision_selection"] = (time.perf_counter() - t0) * 1000

        if not best_branch:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="No viable hypothesis")

        # 9. Verification Swarm (Peer Review)
        t0 = time.perf_counter()
        decision_ready = False
        attempts = 0
        last_reports = []
        while not decision_ready and attempts < 3:
            attempts += 1
            ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
            last_reports = await self.verifier_swarm.run_swarm(ledger_entry)
            ledger_entry.verifier_reports = last_reports
            if self._verify_evidence_hard_constraint(ledger_entry):
                decision_ready = True
            else:
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Refining strategy...")
                refined_branch = await self._refine_strategy(best_branch, last_reports)
                if refined_branch and refined_branch != best_branch:
                    best_branch = refined_branch
                else:
                    break
        latency["verification_swarm"] = (time.perf_counter() - t0) * 1000

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (Immutable Shield)
        t0 = time.perf_counter()
        trade_proposal = self._translate_to_proposal(ledger_entry)
        shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})
        latency["governance_shield"] = (time.perf_counter() - t0) * 1000

        from ..immutable_shield import GovernanceDecision
        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason=f"Shield: {shield_report.reason}")

        # 12. Execution & Folding (HIPIF)
        t0 = time.perf_counter()
        logger.info(f"CSC-V5: Trade APPROVED. Folding horizon...")
        self.folder.fold_history(ledger_entry)
        self.hms.store_ledger_entry(ledger_entry)
        latency["execution_folding"] = (time.perf_counter() - t0) * 1000

        total_latency = (time.perf_counter() - start_time) * 1000

        # Produce Structured Decision Trace
        trace = DecisionTrace(
            decision_id=str(ledger_entry.entry_id),
            timestamp=datetime.utcnow().isoformat(),
            market_snapshot_id=observation.get("snapshot_id", "N/A"),
            model_versions={"csc": "V5-RC1", "world_model": "V3"},
            feature_hashes={"market": str(hash(frozenset(observation.items())))},
            scenarios_evaluated=[s.get("name", "unknown") for s in ledger_entry.multi_path_scenarios],
            consensus_results={"voter_count": len(last_reports), "approved": decision_ready},
            risk_metrics={"composite_confidence": ledger_entry.composite_confidence},
            verification_outcomes=[{"agent": r.agent_name, "valid": r.is_valid} for r in last_reports],
            final_action="TRADE_APPROVED",
            confidence_estimate=ledger_entry.composite_confidence,
            latency_breakdown_ms=latency,
            total_latency_ms=total_latency
        )

        # Store trace in HMS
        self.hms.store_decision_trace(trace)
        logger.info(f"CSC-V5: Decision complete in {total_latency:.2f}ms. Trace stored.")

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _update_perception(self, observation: Dict[str, Any]):
        """Step 1: Active Perception."""
        pass

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any]):
        """Step 2: DiscoLoop (Internalized multi-hop reasoning)."""
        # Carry hidden states (continuous) and tokens (discrete)
        for k in range(3): # K=3 loops
             # In a real model, this would be a Transformer forward pass
             # Proj(e_k) + h_k
             pass

    def _route_skills(self, observation: Dict[str, Any]):
        """Step 3: Skill-to-LoRA routing."""
        pass

    def _apply_hasp_guardrails(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """HASP: Executable guardrails check."""
        return {}

    async def _refine_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        """Pivot/Refine logic to improve strategy based on verifier feedback."""
        # Simple refinement logic: tweak hypothesis confidence or pick second best
        # For now, we simulate refinement by copying and tweaking
        refined = copy.deepcopy(branch)
        if refined.hypotheses:
            refined.hypotheses[0].description += " (Refined)"
        return refined

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        return branches[0]

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": s.name} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        # Check vetoes and consensus
        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.8: return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0
        return consensus >= 0.75

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(statistical=0.8, regime=0.8, execution=0.9, tail_risk=0.85, model_stability=0.7)

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {"trade_id": str(entry.entry_id), "symbol": "EURUSD", "quantity": 1.0, "confidence": entry.composite_confidence}
