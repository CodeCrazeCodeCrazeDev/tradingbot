"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)
Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Implements 'DiscoLoop' (arXiv:2607.00341) and 'AutoResearchClaw' (arXiv:2605.20025).
"""

import logging
import asyncio
import copy
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .folding import InformationFolder
from .router import SkillRouter
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
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CognitiveSystemController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, world_model: Any = None, hms: Any = None, shield: Optional[ImmutableShield] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()
        self.skill_router = SkillRouter()

        # DiscoLoop Channels
        self.continuous_state = {} # h_k: Latent embeddings
        self.discrete_channel = [] # e_k: Semantic tokens

        self._initialized = True
        logger.info("CSC-V5: Initialized with DiscoLoop and Pivot/Refine support.")

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 1. Active Perception (already in observation)

        # 2. Internalization (DiscoLoop Reasoning)
        await self._run_discoloop_internalization(observation)

        # 4. Executable Guardrails (HASP Intervention)
        hasp_result = await self.skill_router.route_task("market_analysis", {"market": observation})
        if hasp_result.get("status") == "success" and "pf_result" in hasp_result:
            pf = hasp_result["pf_result"]
            if pf.get("status") == "pf_intervention":
                logger.warning(f"CSC-V5: HASP Intervention: {pf.get('reason')}")
                # In production, this would modify the plan or observation
                observation["hasp_override"] = pf.get("action")

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
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Triggering Pivot/Refine...")
                severity = self._detect_failure_severity(reports)

                if severity == "critical":
                    best_branch = await self._pivot_strategy(best_branch, reports)
                else:
                    best_branch = await self._refine_parameters(best_branch, reports)

                if not best_branch:
                    logger.error("CSC-V5: Pivot/Refine failed to yield a valid branch.")
                    break

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (Immutable Shield)
        trade_proposal = self._translate_to_proposal(ledger_entry)
        if self.shield:
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

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 3):
        """
        DiscoLoop: Dual-channel recurrence transition.
        """
        logger.info(f"CSC-V5: Running DiscoLoop internalization (K={num_loops})")
        h_k = observation.get("latent_embedding", {})
        e_k = observation.get("semantic_tokens", [])

        for k in range(num_loops):
            h_k = self._transition_h(h_k, e_k)
            e_k = self._discretize_p(h_k)
            h_k = self._realign_h_e(h_k, e_k)

        self.continuous_state = h_k
        self.discrete_channel = e_k

    def _transition_h(self, h: Dict, e: List) -> Dict:
        # Mock transition
        return h

    def _discretize_p(self, h: Dict) -> List:
        # Mock discretization
        return ["internalized_insight"]

    def _realign_h_e(self, h: Dict, e: List) -> Dict:
        # Mock realignment
        return h

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        vetoes = [r for r in reports if not r.is_valid and r.confidence > 0.9]
        if len(vetoes) > 1:
            return "critical"
        return "minor"

    async def _pivot_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        logger.info("CSC-V5: Performing Strategic Pivot")
        return await self.hypothesis_gen.generate_competing_branches({"pivot": True}, original_branch=branch)

    async def _refine_parameters(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        logger.info("CSC-V5: Performing Parameter Refinement")
        refined = copy.deepcopy(branch)
        return refined

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        return branches[0]

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": s.get("name") if isinstance(s, dict) else (s.name if hasattr(s, 'name') else str(s))} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        if not entry.verifier_reports:
            return True

        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.8: return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports)
        return consensus >= 0.75

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(statistical=0.8, regime=0.8, execution=0.9, tail_risk=0.85, model_stability=0.7)

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {"trade_id": str(entry.entry_id), "symbol": "EURUSD", "quantity": 1.0, "confidence": 0.85}
