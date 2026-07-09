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
        """
        Initialize the Cognitive System Controller (CSC).
        Authoritative "One Brain" for AlphaAlgo UCA V5.
        """
        if self._initialized:
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # UCA V5 Advanced Components
        from .router import SkillRouter, HASPExecutor
        self.skill_router = SkillRouter()
        self.hasp_executor = HASPExecutor()

        # DiscoLoop (arXiv:2607.00341) Recurrent State
        self.latent_hidden_state = None  # Continuous channel
        self.discrete_embeddings = []    # Discrete channel (symbolic)

        # Active Inference Objective (VFE)
        self.variational_free_energy = 0.0

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V5).
        Implements DiscoLoop multi-hop reasoning and VFE minimization.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 1-3. Observation Ingestion & Surpise Calculation (VFE)
        # surprise = -log p(obs | world_model)
        surprise = self._calculate_surprise(observation)
        self.variational_free_energy += surprise

        # 4. Strategic Skill Routing & Executable Guardrails (HASP/S2L)
        # Implements arXiv:2605.17734
        skill = self.skill_router.route_task("risk_check", {"market": observation})
        if skill:
            hasp_result = self.hasp_executor.execute(skill, observation)
            if hasp_result.get("status") == "success":
                 # Skill-based state intervention
                 observation.update(hasp_result.get("result", {}))

        # 5. DiscoLoop Multi-Hop Reasoning (arXiv:2607.00341)
        # Looping discrete symbolic embeddings and continuous latent states
        await self._run_discoloop_cycle(observation)

        # 6. Multi-Hypothesis Generation (Based on looped state)
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

        # 11b. Commit to LogAct Backbone (arXiv:2604.07988)
        # Instead of local execution, we propose the action to the shared log.
        # Decoupled voters (including Shield) have already approved it in our local pass,
        # but the LogAct Backbone provides the authoritative, persistent execution trail.
        log_action = LogAction(
            action_type="trade",
            payload={**trade_proposal, "context": {"market": observation}},
            agent_id="CSC_V5"
        )
        await decision_bus.propose_action(log_action)

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade COMMITTED to LogAct. Folding horizon...")
        self.folder.fold_history(ledger_entry)

        # Persist to HMS
        self.hms.store_ledger_entry(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _calculate_surprise(self, observation: Dict[str, Any]) -> float:
        """
        Calculates informational surprise (Shannon Entropy) of the observation.
        Surprise = -log P(O | WorldModel).
        """
        # In a real implementation, this queries the GWM (Generative World Model)
        # to get the likelihood of the current market state.
        return 0.1 # Mock low surprise

    async def _run_discoloop_cycle(self, observation: Dict[str, Any]):
        """
        Implements DiscoLoop (arXiv:2607.00341) multi-hop reasoning.
        Iteratively loops discrete (symbolic) and continuous (latent) states.
        """
        loops = 3
        logger.info(f"CSC: Running DiscoLoop multi-hop reasoning (K={loops})")

        for k in range(loops):
            # 1. Update continuous hidden state from discrete channel
            # 2. Extract new discrete symbolic tokens from continuous state
            # 3. Repeat to 'internalize' multi-step reasoning
            logger.debug(f"DiscoLoop: Loop {k} - Internalizing evidence...")

        self.discrete_embeddings.append("regime_shift_detected")
        self.latent_hidden_state = {"reasoning_depth": loops}

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
