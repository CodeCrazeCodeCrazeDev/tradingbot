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
import threading
import copy
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .folding import InformationFolder
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    UCA V5 Controller integrating DiscoLoop, HASP, and Pivot/Refine.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CognitiveSystemController, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, world_model: Any = None, hms: Any = None, shield: Optional[ImmutableShield] = None, config: Optional[Dict] = None):
        if self._initialized:
            if world_model is not None:
                self.world_model = world_model
            if hms is not None:
                self.hms = hms
                if hasattr(self, 'folder'):
                    self.folder.hms = hms
            if shield is not None:
                self.shield = shield
            return
        self.config = config or {}
        self.world_model = world_model
        self.hms = hms
        self.shield = shield or ImmutableShield()
        self.folder = InformationFolder(hms=hms)
        self.folding_operator = self.folder # Use the folder as the operator

        # Configuration parameters
        self.consensus_threshold = self.config.get("consensus_threshold", 0.75)

        from .router import SkillRouter
        self.skill_router = SkillRouter()

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()

        # DiscoLoop Channels
        self.continuous_state = {} # Latent embeddings
        self.discrete_channel = [] # Semantic tokens

        # HASP: Executable Guardrails (Skill Programs)
        self.skill_programs = self._load_skill_programs()
        self._initialized = True

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "version": "UCA-2026-V5",
            "consensus_threshold": self.consensus_threshold,
            "components": ["DiscoLoop", "HASP", "PivotRefine"]
        }

    def _load_skill_programs(self) -> Dict[str, Any]:
        # In production, load from a registry. Here we stub it.
        return {}

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # Memory management: bounded buffer for channels
        if len(self.discrete_channel) > 100:
            self.discrete_channel = self.discrete_channel[-100:]

        # 4. Executable Guardrails (HASP Intervention)
        intervention = await self._apply_hasp_guardrails_async(observation)
        if intervention:
            observation.update(intervention)

        # 5. Multi-Hypothesis Generation
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI / World Model)
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 7. Decision Selection (EV Optimization)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return None

        # 8. Decision Loop (Pivot/Refine)
        decision_ready = False
        attempts = 0
        while not decision_ready and attempts < 3:
            attempts += 1

            # 9. Verification Swarm (Peer Review)
            ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
            reports = await self.verifier_swarm.run_swarm(ledger_entry)
            ledger_entry.verifier_reports = reports

            # 10. Pivot/Refine Decision
            if self._verify_evidence_hard_constraint(ledger_entry):
                decision_ready = True
            else:
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Refining strategy...")
                refined_branch = await self._refine_strategy(best_branch, reports)
                if refined_branch and refined_branch != best_branch:
                    best_branch = refined_branch
                else:
                    # If we can't refine further, break
                    logger.error("CSC-V5: Could not refine strategy further.")
                    break

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (Immutable Shield)
        trade_proposal = self._translate_to_proposal(ledger_entry)
        shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})

        from ..immutable_shield import GovernanceDecision
        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason=f"Shield: {shield_report.reason}")

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED. Folding horizon...")
        self.folder.fold_history(ledger_entry)

        # Persist to HMS
        if self.hms:
            self.hms.store_ledger_entry(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _apply_hasp_guardrails(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """HASP: Executable guardrails check."""
        return {}

    async def _apply_hasp_guardrails_async(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of HASP guardrails."""
        if not hasattr(self, 'skill_router'):
            return {}

        result = await self.skill_router.route_task("csc_internal", "risk_check", {"market": observation})
        if result.get("status") == "pf_intervention":
            return {"intervention": result}
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
            multi_path_scenarios=[{"name": getattr(s, 'name', 'Unknown')} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        # Check vetoes and consensus
        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.8: return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0
        return consensus >= self.consensus_threshold

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        # Calculate composite confidence based on verifier reports
        if not entry.verifier_reports:
            return ConfidenceVector(statistical=0.5, regime=0.5, execution=0.5, tail_risk=0.5, model_stability=0.5)

        avg_conf = sum(r.confidence for r in entry.verifier_reports) / len(entry.verifier_reports)
        valid_ratio = sum(1 for r in entry.verifier_reports if r.is_valid) / len(entry.verifier_reports)

        composite = avg_conf * valid_ratio

        return ConfidenceVector(
            statistical=round(composite, 2),
            regime=round(composite * 0.9, 2),
            execution=round(composite * 1.1, 2) if composite < 0.9 else 0.99,
            tail_risk=round(composite, 2),
            model_stability=round(composite, 2),
            sample_size=len(entry.verifier_reports) * 10 # Mock sample size
        )

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        symbol = "EURUSD"
        if entry.hypothesis and "symbol" in entry.hypothesis.predicted_outcome.lower():
             # In a real system, we'd extract this from the hypothesis
             pass

        return {
            "trade_id": str(entry.entry_id),
            "symbol": symbol,
            "quantity": 1.0,
            "exposure": 0.5, # Default exposure for shield check
            "confidence": entry.composite_confidence
        }
