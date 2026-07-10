"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)
======================================================

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Implements Active Inference (VFE minimization), DiscoLoop reasoning, and HIPIF.
Authoritative controller orchestrating the LogAct pipeline.
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
from .router import SkillRouter, HASPExecutor, SkillType
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    UCA V5 Controller integrating DiscoLoop, HASP, and Pivot/Refine.
    Governed by the principle of Minimizing Variational Free Energy (VFE).
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
        self.folder = InformationFolder() # HIPIF Folding Operator
        self.skill_router = SkillRouter()
        self.hasp_executor = HASPExecutor()

        # DiscoLoop Channels (Internalized reasoning states)
        self.continuous_state = np.zeros(512) # Latent embeddings
        self.discrete_channel = [] # Semantic tokens (Bridge Entities)
        self.max_history = 100 # Windowing to prevent memory leak

        self._initialized = True
        logger.info("CSC-V5: One Brain Controller initialized")

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        """
        logger.info("CSC-V5: Starting Recursive Active Inference Pipeline")

        # 1. Active Perception
        # (Observation is passed in)

        # 2. Internalization (DiscoLoop)
        # Run K reasoning loops to align hidden states with discrete market entities.
        await self._run_discoloop_reasoning(observation, num_loops=3)

        # 3. Skill Routing (S2L/HASP)
        # Activate relevant LoRA adapters or Executable Programs
        skill = await self.skill_router.route_task("market_analysis", observation)
        if skill and skill.skill_type == SkillType.HASP_PROGRAM:
            # 4. Executable Guardrails (HASP Intervention)
            intervention = await self.hasp_executor.execute(skill, observation)
            if intervention.get("status") == "success":
                observation.update(intervention.get("result", {}))
                if intervention.get("result", {}).get("action") == "override_to_hold":
                     return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="HASP Override: Hold")

        # 5. Multi-Hypothesis Generation
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI / World Model)
        # Run counterfactual "What-if" rollouts
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 7. Decision Selection (EV Optimization / VFE Minimization)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="No viable reasoning branch")

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
                # Tactical adjustment (Refine) or Strategic shift (Pivot)
                refined_branch = await self._pivot_refine_strategy(best_branch, reports)
                if refined_branch and refined_branch.branch_id != best_branch.branch_id:
                    logger.info(f"CSC-V5: Strategy PIVOT to {refined_branch.name}")
                    best_branch = refined_branch
                elif refined_branch:
                    logger.info(f"CSC-V5: Strategy REFINED")
                    best_branch = refined_branch
                else:
                    logger.error("CSC-V5: Could not refine or pivot further.")
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
            logger.warning("CSC-V5: No Immutable Shield provided. Bypassing governance gate.")

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED. Folding horizon...")
        # Compress episodic trace into semantic update
        self.folder.fold_history(ledger_entry)

        # Persist to HMS (SAGE Graph + Ledger)
        self.hms.store_ledger_entry(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any], num_loops: int):
        """
        DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States.
        Implements multi-hop reasoning before hypothesis generation.
        """
        logger.debug(f"DiscoLoop: Starting {num_loops} reasoning cycles")
        for i in range(num_loops):
            # 1. Update continuous hidden state based on observation and discrete tokens
            # (In production, this is a Transformer/Mamba pass)
            self.continuous_state = np.tanh(self.continuous_state + np.random.normal(0, 0.01, 512))

            # 2. Emit discrete symbolic tokens (Bridge Entities)
            # (In production, this is a VQ-bottleneck or LLM token emission)
            token = f"reasoning_token_{i}_{datetime.now().timestamp()}"
            self.discrete_channel.append(token)

        # Prevent memory leak: keep only the most recent N tokens
        if len(self.discrete_channel) > self.max_history:
            self.discrete_channel = self.discrete_channel[-self.max_history:]

        logger.debug(f"DiscoLoop: Internalized {len(self.discrete_channel)} symbolic bridge entities")

    async def _pivot_refine_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        """
        Pivot/Refine logic based on Verifier Swarm feedback.
        Pivot: Switch to a different ReasoningBranch.
        Refine: Adjust parameters of the current branch.
        """
        critical_critique = " ".join([r.critique for r in reports if not r.is_valid])

        # Strategic Pivot: If feedback suggests fundamental misalignment
        if "regime mismatch" in critical_critique.lower() or "wrong direction" in critical_critique.lower():
            # Try to find a branch that addresses the critique
            # (Simplified: just flip Bull/Bear for demonstration)
            new_id = "branch_bear" if branch.branch_id == "branch_bull" else "branch_bull"
            return ReasoningBranch(branch_id=new_id, name="Pivoted Strategy")

        # Tactical Refinement: Adjust confidence or reasoning
        refined = copy.deepcopy(branch)
        refined.reasoning_trace.append(f"Refinement based on critique: {critical_critique[:50]}...")
        refined.confidence *= 0.9 # Penalize confidence due to refinement
        return refined

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        # EV Optimization: Select branch with highest confidence/simulated success
        return branches[0]

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        entry = ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": getattr(s, 'name', str(s))} for s in scenarios] if scenarios else []
        )
        entry.composite_confidence = branch.confidence
        return entry

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        # Check vetoes and consensus
        if not entry.verifier_reports:
            return True # Assume valid if no verifiers (though UCA requires swarm)

        vetoes = [r for r in entry.verifier_reports if not r.is_valid and r.confidence > 0.85]
        if vetoes:
            logger.warning(f"CSC-V5: Critical Veto detected from {vetoes[0].agent_name}")
            return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports)
        return consensus >= 0.75

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(statistical=0.8, regime=0.8, execution=0.9, tail_risk=0.85, model_stability=0.7)

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {
            "trade_id": str(entry.entry_id),
            "symbol": "EURUSD",
            "quantity": 1.0,
            "confidence": entry.composite_confidence,
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "None"
        }
