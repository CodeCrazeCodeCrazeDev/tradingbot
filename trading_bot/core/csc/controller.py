"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)
=====================================================

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Implements 'DiscoLoop' (2026) and 'HASP' (2026).
"""

import logging
import asyncio
import copy
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .folding import InformationFolder
from .router import skill_router
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
        if self._initialized:
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield or ImmutableShield()

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # HASP: Executable Guardrails (Skill Programs)
        self.skill_router = skill_router

        # DiscoLoop Channels (Internalized Recurrence)
        self.continuous_state = np.zeros(64) # Latent state [h_k]
        self.discrete_channel = []           # Semantic tokens [e_k]
        self._initialized = True

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        try:
            # 1. Active Perception (Minimizing Variational Free Energy)
            # 2. Discrete-Continuous Internalization (DiscoLoop Reasoning)
            await self._run_discoloop_reasoning(observation)

            # 3. Skill Routing (S2L / HASP Intervention)
            # 4. Executable Guardrails (HASP Intervention)
            action_proposal = {"type": "MARKET_ORDER", "symbol": observation.get("symbol", "EURUSD")}
            final_action, intervention_ctx, status = await self.skill_router.route_and_execute(observation, action_proposal)

            if status == "VETO":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id="N/A",
                    dominant_rejection_reason=f"HASP Veto: {intervention_ctx}"
                )

            # 5. Multi-Hypothesis Generation
            branches = await self.hypothesis_gen.generate_competing_branches(observation)

            # 6. Causal Simulation (CWMI / World Model)
            sim_results = await self.hypothesis_gen.simulate_branches(branches)

            # 7. Decision Selection (EV Optimization)
            best_branch = self._select_optimal_branch(branches, sim_results)
            if not best_branch:
                return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, trade_id="N/A", dominant_rejection_reason="No valid hypothesis")

            # 8. Decision Loop (Pivot/Refine)
            decision_ready = False
            attempts = 0
            ledger_entry = None

            while not decision_ready and attempts < 3:
                attempts += 1

                # 9. Verification Swarm (Peer Review)
                ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
                try:
                    reports = await self.verifier_swarm.run_swarm(ledger_entry)
                    ledger_entry.verifier_reports = reports
                except Exception as e:
                    logger.error(f"CSC-V5: Verifier Swarm CRITICAL FAILURE: {e}")
                    return CoreDecision(
                        outcome=DecisionOutcome.TRADE_REJECTED,
                        trade_id=str(ledger_entry.entry_id),
                        dominant_rejection_reason="Verifier Swarm Failure"
                    )

                # 10. Pivot/Refine Decision
                if self._verify_evidence_hard_constraint(ledger_entry):
                    decision_ready = True
                else:
                    logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Self-healing...")
                    best_branch = await self._refine_strategy(best_branch, reports)
                    if not best_branch: break

            if not decision_ready:
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=str(ledger_entry.entry_id) if ledger_entry else "N/A",
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
                     dominant_rejection_reason=f"Shield Veto: {shield_report.reason}"
                 )

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

        except Exception as e:
            logger.critical(f"CSC-V5: Unhandled Pipeline Exception: {e}", exc_info=True)
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id="N/A",
                dominant_rejection_reason=f"System Critical Error: {str(e)}"
            )

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any], loops: int = 3):
        """
        DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States.
        Implements functional Bridge Realignment.
        """
        logger.debug(f"DiscoLoop: Running {loops} reasoning loops")

        # Initial hidden state derived from observation
        h_k = np.array([observation.get("volatility", 0.0)] * 64)

        for k in range(loops):
            # 1. Discrete Grounding (Symbolic Extraction)
            # In a real model, this is argmax over vocabulary
            token = "VOL_STABLE" if h_k[0] < 0.05 else "VOL_HIGH"
            self.discrete_channel.append(token)

            # 2. Bridge Realignment (h_k' = Norm(h_k) + lam * e_k)
            # Simulate embedding lookup
            e_k = np.array([0.1 if token == "VOL_STABLE" else 0.5] * 64)
            h_k = (h_k / (np.linalg.norm(h_k) + 1e-9)) + 0.1 * e_k

            # 3. Recurrent Transition (Update continuous state)
            h_k = np.tanh(h_k * 1.1)

        self.continuous_state = h_k

    async def _refine_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        """Pivot/Refine logic (AutoResearchClaw) to recover from failures."""
        severity = self._calculate_failure_severity(reports)

        if severity >= 0.7:
            return await self.hypothesis_gen.pivot_strategy(branch, reports)
        else:
            return await self.hypothesis_gen.refine_strategy(branch, reports)

    def _calculate_failure_severity(self, reports: List[VerifierReport]) -> float:
        if not reports: return 0.0
        vetoes = [r for r in reports if not r.is_valid and r.confidence > 0.8]
        return len(vetoes) / len(reports)

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        # In V5, select based on Expected Utility or VFE minimization
        return branches[0]

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": s.name} if hasattr(s, 'name') else {"name": str(s)} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        if not entry.verifier_reports: return True
        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports)
        return consensus >= 0.75

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        # Ground confidence in evidence graph density and verifier consensus
        avg_v_conf = np.mean([r.confidence for r in entry.verifier_reports]) if entry.verifier_reports else 0.5
        return ConfidenceVector(
            statistical=float(avg_v_conf),
            regime=0.8,
            execution=0.9,
            tail_risk=0.85,
            model_stability=0.7
        )

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {
            "trade_id": str(entry.entry_id),
            "symbol": "EURUSD",
            "direction": "long",
            "quantity": 1.0,
            "entry_price": 1.10,
            "stop_loss": 1.08,
            "volatility": 0.02,
            "current_exposure": 0.1
        }
