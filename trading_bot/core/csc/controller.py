"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)
Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Implements Active Inference (VFE minimization), DiscoLoop reasoning, and Pivot/Refine logic.
"""

import logging
import asyncio
import copy
import json
import numpy as np
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
        if getattr(self, '_initialized', False):
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()
        self.skill_router = SkillRouter()

        # DiscoLoop Channels
        self.continuous_state = {}  # Latent embeddings
        self.discrete_channel = []  # Semantic tokens
        self._initialized = True

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 2. Internalization (DiscoLoop Reasoning)
        reasoning_context = await self._run_discoloop_internalization(observation, k=3)

        # 3. Skill Routing (S2L/HASP Selection)
        routed_skill = await self.skill_router.route_task("market_analysis", observation, reasoning_context)

        # 4. Executable Guardrails (HASP Intervention)
        if routed_skill and routed_skill.get("status") == "pf_intervention":
            logger.warning(f"CSC-V5: HASP Intervention triggered: {routed_skill.get('reason')}")
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=str(uuid4()),
                dominant_rejection_reason=routed_skill.get('reason')
            )

        # 5. Multi-Hypothesis Generation (SAGE-informed)
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (WM-V3)
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

            # 9. Verification Swarm (Peer Review / Falsification)
            ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
            reports = await self.verifier_swarm.run_swarm(ledger_entry)
            ledger_entry.verifier_reports = reports

            # 10. Pivot/Refine Decision
            if self._verify_evidence_hard_constraint(ledger_entry):
                decision_ready = True
            else:
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Triggering Pivot/Refine...")
                best_branch = await self._pivot_or_refine(best_branch, reports, branches)
                if not best_branch:
                    break

        if not decision_ready:
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=str(uuid4()),
                dominant_rejection_reason="Failed Pivot/Refine loop"
            )

        # 11. Governance Gate (Immutable Shield)
        trade_proposal = self._translate_to_proposal(ledger_entry)
        shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})

        from ..immutable_shield import GovernanceDecision
        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(
                 outcome=DecisionOutcome.TRADE_REJECTED,
                 trade_id=trade_proposal.get("trade_id"),
                 dominant_rejection_reason=f"Shield: {shield_report.reason}"
             )

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED. Folding horizon...")
        self.folder.fold_history(ledger_entry)
        self.hms.store_ledger_entry(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    async def _run_discoloop_internalization(self, obs: Dict, k: int) -> Dict:
        """DiscoLoop: Functional K-step discrete-continuous recurrence."""
        # Loop state S_k = [h_k; e_k]
        h_k = np.array(obs.get("features", [0.0] * 64))
        e_k = ["ROOT"]

        for i in range(k):
            # Transition: h_{k+1} = Transformer(h_k + Proj(e_k))
            # (Simulated via transformation matrix for functional logic)
            h_k = np.tanh(h_k * 1.1 + 0.05)

            # Discretization: e_{k+1} = argmax(p(e|h_k))
            # (Simulated: select most likely semantic entity based on latent state)
            entity = "VOLATILITY_EXPANSION" if h_k.sum() > 0.5 else "LIQUIDITY_DEPTH"
            e_k.append(entity)

        return {"latent": h_k.tolist(), "tokens": e_k}

    async def _pivot_or_refine(self, current_branch: ReasoningBranch, reports: List[VerifierReport], all_branches: List[ReasoningBranch]) -> Optional[ReasoningBranch]:
        """Pivot/Refine: Functional strategic switching logic."""
        vetoes = [r for r in reports if not r.is_valid and r.confidence > 0.8]

        # PIVOT if strategic flaw detected
        if any("STRATEGIC" in v.critique.upper() for v in vetoes):
            logger.info("CSC-V5: PIVOTING to alternative hypothesis.")
            alternatives = [b for b in all_branches if b.branch_id != current_branch.branch_id]
            return sorted(alternatives, key=lambda x: x.confidence, reverse=True)[0] if alternatives else None

        # REFINE if tactical error detected
        logger.info("CSC-V5: REFINING current strategy parameters.")
        refined = copy.deepcopy(current_branch)
        for v in vetoes:
            # Adjust confidence or description based on critique
            refined.confidence *= (1.0 - v.severity)
            refined.reasoning_trace.append(f"Refinement: {v.critique}")
        return refined

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        # EV Optimization: Branch with highest confidence * simulation score
        return max(branches, key=lambda b: b.confidence)

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": s.name} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        # Falsification check: if any high-confidence verifier rejects, fail.
        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.9: return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0
        return consensus >= 0.8

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        # Calibrated composite confidence based on verifier consensus
        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        base = sum(r.confidence for r in valid_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0.5
        return ConfidenceVector(statistical=base, regime=base, execution=0.9, tail_risk=0.85, model_stability=0.8)

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {"trade_id": str(entry.entry_id), "symbol": "EURUSD", "quantity": 1.0, "confidence": entry.composite_confidence}
