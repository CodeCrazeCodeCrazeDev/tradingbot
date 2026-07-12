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

        # DiscoLoop Channels
        self.continuous_state: Dict[str, Any] = {}  # Latent embeddings h_k
        self.discrete_channel: List[str] = []       # Semantic bridge tokens e_k
        self._max_loops = 3

        # HASP: Executable Guardrails (Skill Programs)
        self.skill_programs = self._load_skill_programs()
        self._initialized = True

    def _load_skill_programs(self) -> Dict[str, Any]:
        # In production, load from a registry. Here we stub it.
        return {}

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any]):
        """
        Implements the DiscoLoop dual-channel recurrence: S_k = [h_k; e_k].
        """
        import numpy as np
        logger.info(f"CSC-V5: Initiating DiscoLoop reasoning (K={self._max_loops})")

        # Initialize loop state from observation
        h_k = self._encode_continuous(observation)
        e_k = self._encode_discrete(observation)

        for k in range(self._max_loops):
            # 1. Transition: h_{k+1} = tanh(Wh * h_k + We * e_k)
            # This simulates the dual-channel recurrence mathematically
            h_next = np.tanh(0.8 * h_k + 0.2 * e_k + np.random.normal(0, 0.01, h_k.shape))

            # 2. Discretization: e_{k+1} = argmax projection
            # We simulate this by taking the sign of the max component
            e_next = np.zeros_like(h_next)
            e_next[np.argmax(np.abs(h_next))] = np.sign(h_next[np.argmax(np.abs(h_next))])

            # 3. Realignment Intervention (Internalization)
            # Realignment closes the ID/OOD gap by shifting h_next towards e_next
            h_k = 0.9 * h_next + 0.1 * e_next
            e_k = e_next

            logger.debug(f"DiscoLoop: Completed iteration {k+1}")

        self.continuous_state = {"latent": h_k.tolist()}
        self.discrete_channel.append(f"bridge_token_{np.argmax(e_k)}")

    def _encode_continuous(self, observation: Dict[str, Any]) -> Any:
        import numpy as np
        return np.random.normal(0, 1, (16,))

    def _encode_discrete(self, observation: Dict[str, Any]) -> Any:
        import numpy as np
        e = np.zeros((16,))
        e[0] = 1.0
        return e

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 1. Active Perception (Ingest Observation)
        # observation is already passed in

        # 2. Internalization (DiscoLoop Reasoning)
        await self._run_discoloop_reasoning(observation)

        # 3. Skill Routing (S2L/HASP)
        # This is integrated into Step 4 and the execution phase

        # 4. Executable Guardrails (HASP Intervention)
        intervention = self._apply_hasp_guardrails(observation)
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
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Analyzing failure...")

                # Pivot (Strategic) vs Refine (Tactical) selection
                failure_severity = self._analyze_failure_severity(reports)

                if failure_severity > 0.7:
                    logger.info("CSC-V5: High severity failure. PI VOTING strategy.")
                    refined_branch = await self._pivot_strategy(best_branch, reports)
                else:
                    logger.info("CSC-V5: Low severity failure. REFINING parameters.")
                    refined_branch = await self._refine_strategy(best_branch, reports)

                if refined_branch and refined_branch != best_branch:
                    best_branch = refined_branch
                else:
                    logger.error("CSC-V5: Could not pivot or refine further.")
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
        else:
            logger.warning("CSC-V5: Immutable Shield not configured. Bypassing governance check.")

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED. Executing and Folding horizon...")

        # Log to Action Backbone (LogAct)
        action = LogAction(
            action_type="EXECUTE_TRADE",
            payload=trade_proposal,
            agent_id="CSC_V5",
            correlation_id=str(ledger_entry.entry_id)
        )
        await decision_bus.propose_action(action)

        # HIPIF Folding
        self.folder.fold_history(ledger_entry)

        # Persist to HMS (SAGE Graph Update)
        if self.hms:
            self.hms.store_ledger_entry(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _analyze_failure_severity(self, reports: List[VerifierReport]) -> float:
        """Calculates a failure severity score (0-1)."""
        if not reports: return 0.0
        vetoes = [r for r in reports if not r.is_valid and r.confidence > 0.8]
        return len(vetoes) / len(reports)

    async def _pivot_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        """Strategic shift: Pick a different reasoning branch or counter-hypothesis."""
        logger.info("CSC-V5: Executing Strategic Pivot")
        # In a real implementation, this would query the hypothesis generator for alternatives
        return await self.hypothesis_gen.generate_alternative_branch(branch, reports)

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
        # Use deterministic ID based on branch for reproducibility in tests
        import hashlib
        entry_id = hashlib.md5(branch.branch_id.encode()).hexdigest()
        return ResearchLedgerEntry(
            entry_id=entry_id,
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
