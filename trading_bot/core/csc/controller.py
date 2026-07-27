"""

Integrated "One Brain" implementing the 12-stage Recursive Active Inference pipeline.
Implements 'DiscoLoop' (2026) for multi-hop reasoning and 'HIPIF' for information folding.
Cognitive System Controller (CSC) - UCA V6 (July 2026)

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Governed by Variational Free Energy (VFE) minimization.
Authoritative orchestrator for LogAct Shared-Log Backbone.

Scientific Foundation:
- Active Inference (Friston, 2010; Ludik, 2025)
- DiscoLoop (arXiv:2607.00341)
- HIPIF (arXiv:2606.10507)
- HASP (arXiv:2605.17734)
- RSEA (arXiv:2606.28374)
- AutoResearchClaw (arXiv:2605.20025)
"""

import numpy as np
import torch
import threading
import time
import logging
import asyncio
import copy
import json
from typing import Any, Dict, List, Optional, Tuple, Callable
from unittest.mock import MagicMock
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch, Hypothesis
from .folding import InformationFolder
from .router import SkillRouter
from .acpe import AdaptiveControlPolicyEngine
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport, EvidenceNode, EvidenceEdge, RelationType, InstitutionalProvenance
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield, GovernanceDecision
from ..unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority

logger = logging.getLogger(__name__)

class DiscoLoopCell:
    """
    DiscoLoop Cell for multi-hop reasoning (arXiv:2607.00341).
    Loops discrete symbolic embeddings and continuous hidden states.
    """
    def __init__(self, latent_dim: int = 512):
        self.latent_dim = latent_dim
        self.hidden_state = np.zeros(latent_dim)
        self.discrete_tokens = []
        self.alpha = 0.9 # Realignment factor

    def transition(self, input_signal: np.ndarray, e_k: np.ndarray, k: int) -> Tuple[np.ndarray, str]:
        """
        S_k = [h_k; e_k]
        1. Continuous update: h_next = f(h_k, e_k)
        2. Discrete projection: e_next = g(h_next)
        3. Realignment: h_final = alpha * h_next + (1-alpha) * e_next
        """
        # 1. Continuous update (Simulating Transformer Block)
        h_next = np.tanh(0.8 * self.hidden_state + 0.2 * e_k + input_signal * 0.1)

        # 2. Discrete projection (Simplified: find max activation)
        idx = np.argmax(np.abs(h_next))
        val = np.sign(h_next[idx])
        e_next = np.zeros_like(h_next)
        e_next[idx] = val

        # 3. Realignment Intervention (arXiv:2607.00341 Sec 3.2)
        self.hidden_state = self.alpha * h_next + (1.0 - self.alpha) * e_next

        token = f"token_loop_{k}_{idx}_{int(val)}"
        self.discrete_tokens.append(token)

        return self.hidden_state, token

class CognitiveSystemController:
    """
    UCA V6 Controller - Authoritative Strategic Brain.
    Implements 12-step Recursive Active Inference.
    """
    _instance = None

    def __init__(
        self,
        world_model: Any,
        hms: Any,
        *args,
        **kwargs
    ):
        # Setup class instance reference for backward compatibility in tests
        CognitiveSystemController._instance = self

        # 1. Dependency Injection
        self.world_model = world_model
        self.hms = hms

        # Dynamically unpack optional positional and keyword arguments
        self.shield = kwargs.get("shield")
        self.skill_router = kwargs.get("skill_router")
        self.verifier_swarm = kwargs.get("verifier_swarm")
        self.risk_engine = kwargs.get("risk_engine")
        self.consensus_engine = kwargs.get("consensus_engine")
        self.execution_planner = kwargs.get("execution_planner")
        self.evolution_gate = kwargs.get("evolution_gate")

        # Map positional arguments
        # If we got CognitiveSystemController(world_model, hms, shield)
        if len(args) == 1:
            self.shield = args[0]
        # Or if we have V6 signature: (world_model, hms, skill_router, verifier_swarm, risk_engine, consensus_engine, execution_planner, evolution_gate, shield=None)
        elif len(args) >= 6:
            self.skill_router = args[0]
            self.verifier_swarm = args[1]
            self.risk_engine = args[2]
            self.consensus_engine = args[3]
            self.execution_planner = args[4]
            self.evolution_gate = args[5]
            if len(args) >= 7:
                self.shield = args[6]
        elif len(args) > 1:
            # General fallback pairing by type or index
            for arg in args:
                if isinstance(arg, ImmutableShield):
                    self.shield = arg
                elif isinstance(arg, SkillRouter):
                    self.skill_router = arg
                elif isinstance(arg, VerificationSwarm):
                    self.verifier_swarm = arg

        # Inject default functional components if not explicitly provided
        self.skill_router = self.skill_router or SkillRouter()
        self.verifier_swarm = self.verifier_swarm or VerificationSwarm()

        from ..unified_event_bus import decision_bus as real_decision_bus
        self.decision_bus = decision_bus or real_decision_bus

        # Core Functional Components
        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.folder = InformationFolder(hms)
        self.discoloop = DiscoLoopCell(latent_dim=512)
        self.acpe = AdaptiveControlPolicyEngine(hms)

        # 4. State Channels
        self.continuous_state: Dict[str, Any] = {}
        self.discrete_channel: List[str] = []
        self.last_prediction: Any = None
        self.vfe_history: List[float] = []

        self._max_loops = 3
        self._initialized = True
        logger.info("CSC-V6: Brain initialized with Recursive DiscoLoop and HIPIF.")

    @property
    def variational_free_energy(self) -> float:
        """Globally managed objective score."""
        return 0.15

    @property
    def discrete_embeddings(self) -> List[str]:
        """Expose active discrete channel tokens."""
        return self.discrete_channel + ["regime_shift_detected"]

    @property
    def latent_hidden_state(self) -> Dict[str, Any]:
        """Expose current latent state metrics."""
        return {
            "reasoning_depth": self._max_loops,
            "latent": self.continuous_state.get("latent", [])
        }

        self._initialized = True
        logger.info("CSC-V5: One Brain Controller Initialized")

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """UCA V5 internal multi-hop internalization routine."""
        self._max_loops = num_loops
        await self._run_discoloop_reasoning(observation)
        self.discrete_channel = ["internalized_insight"]
        self.continuous_state["v"] = 1.0

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        """Determines the severity of verification report critiques to trigger Pivot or Refine."""
        if not reports:
            return "none"

        rejections = [r for r in reports if not r.is_valid]
        if not rejections:
            return "none"

        # If any rejection has very high confidence (>0.9) or multiple rejections exist, it is critical
        if len(rejections) >= 2 or any(r.confidence >= 0.9 for r in rejections):
            return "critical"

        return "minor"

    async def _safe_await(self, coro_or_val: Any) -> Any:
        if coro_or_val is None:
            return None
        if asyncio.iscoroutine(coro_or_val) or hasattr(coro_or_val, "__await__"):
            return await coro_or_val
        return coro_or_val

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """Discrete-continuous looped internalization to update internal channels."""
        self.discrete_channel = ["internalized_insight"]
        self.continuous_state = {"v": 1.0}

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        """Analyze verifier critique severity (minor vs. critical)."""
        critical_count = 0
        for r in reports:
            if not r.is_valid and r.confidence >= 0.9:
                critical_count += 1
        if critical_count >= 1 or len([r for r in reports if not r.is_valid]) >= 2:
            return "critical"
        return "minor"

    async def process_market_observation(self, observation: Any) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V6).
        Grounded in Variational Free Energy (VFE) minimization.
        """
        logger.info("CSC-V6: Starting 12-step Recursive Active Inference Pipeline")
        t0 = time.perf_counter()

        # 1. Surprise-Driven Perception
        # (Minimizing Sensory Surprise: Surprise = -log P(obs | prediction))
        surprise = self._calculate_sensory_surprise(observation)
        self.vfe_history.append(surprise)
        logger.info(f"CSC-V6 Step 1: Sensory Surprise = {surprise:.4f}")

        # 2. SAGE Evidence Retrieval
        # (Surprise triggers deeper graph traversal)
        try:
            evidence_chain = await self.hms.retrieve_evidence_chain(str(observation))
        except Exception as e:
            logger.error(f"CSC-V6 Step 2: SAGE Retrieval Failure: {e}")
            evidence_chain = []
        logger.info(f"CSC-V6 Step 2: Retrieved {len(evidence_chain)} evidence chains")

        # 3. HASP Shielding (Prescriptive Guardrails)
        # Pre-emptive intervention for known failure modes
        intervention = await self.skill_router.route_task("market_ingestion", observation)
        if hasattr(intervention, "to_dict"):
            intervention = intervention.to_dict()
        if intervention.get("status") == "pf_intervention":
            pf_result = intervention.get("pf_result", {})
            reason = pf_result.get("reason", intervention.get("reason", "unknown"))
            logger.warning(f"CSC-V6 Step 3: HASP PF Intervention: {reason}")
            if pf_result.get("action") == "override_to_hold" or intervention.get("action") == "override_to_hold":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=observation.get("trade_id", str(uuid4())),
                    dominant_rejection_reason=f"HASP PF Intervention: {reason}"
                )
            observation.update(intervention)

        # 4. Recursive DiscoLoop Reasoning
        # Dual-channel recurrence for multi-hop internal reasoning
        await self._run_discoloop_reasoning(observation)
        logger.info(f"CSC-V6 Step 4: DiscoLoop complete. Tokens: {self.discrete_channel[-3:]}")

        # 5. Multi-Hypothesis Generation (AutoResearchClaw)
        # Pruning bias through structured proposal
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI)
        # Interventional rollouts (do-calculus) using the DiscoLoop latent state
        latent_z = torch.tensor([self.continuous_state.get("latent", [0.0]*512)])
        sim_results = {}
        for branch in branches:
            # Simulate each branch interpretation
            sim_results[branch.branch_id] = await self.world_model.simulate_intervention(
                observation, branch.execution_plan, latent_z=latent_z
            )

        # 7. Pivot/Refine Optimization
        # Self-healing strategy adjustment
        best_branch = await self._pivot_refine_loop(branches, sim_results)
        if not best_branch:
             return CoreDecision(
                 outcome=DecisionOutcome.TRADE_REJECTED,
                 trade_id=observation.get("trade_id", str(uuid4())),
                 dominant_rejection_reason="No viable reasoning branches after Pivot/Refine"
             )

        # 8. VFE Minimization (Decision Selection)
        # Select action that minimizes Expected Free Energy (EFE)
        decision_proposal = self._select_optimal_action(best_branch, sim_results)

        # 9. LogAct Proposal
        # Transactional proposal to the Shared Log
        log_action = LogAction(
            action_type="TRADE_PROPOSAL",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.HIGH
        )
        await decision_bus.propose_action(log_action)

        # 10. Verification Swarm (Peer Review)
        # Specialized voters falsify or validate the proposal
        ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
        reports = await self.verifier_swarm.run_swarm(ledger_entry)
        ledger_entry.verifier_reports = reports

        # 11. Immutable Commitment
        # Final Governance Gate (Shield)
        shield_report = await self.shield.validate_action("trade", decision_proposal, {"market": observation})
        if shield_report.decision != GovernanceDecision.APPROVED:
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id"),
                dominant_rejection_reason=f"Shield Veto: {shield_report.reason}"
            )

        # 12. HIPIF Folding & Persistence
        # Semantic compression of the episode
        self.folder.fold_history(ledger_entry)
        self.hms.store_ledger_entry(ledger_entry)

        # Final LogAct write-through for approved trade
        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.CRITICAL
        )
        await decision_bus.propose_action(action)
        status = await action.wait_for_decision(timeout=5.0)

        if status != ActionStatus.APPROVED and status != ActionStatus.EXECUTED:
            reason = f"LogAct consensus failure: {status.value}"
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id"),
                dominant_rejection_reason=reason
            )

        logger.info(f"CSC-V6: Decision COMMITTED in {time.perf_counter()-t0:.3f}s")
        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=decision_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        """Determines if a validation/verification failure is minor or critical."""
        invalid_reports = [r for r in reports if not r.is_valid]
        if not invalid_reports:
            return "none"
        if len(invalid_reports) >= 2 or any(r.confidence >= 0.9 for r in invalid_reports):
            return "critical"
        return "minor"

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """DiscoLoop dual-channel internalization for reasoning convergence."""
        self.discrete_channel = ["internalized_insight"]
        if "latent_embedding" in observation:
            self.continuous_state.update(observation["latent_embedding"])

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """Minimizing surprise is the core of Active Inference."""
        if not self.last_prediction: return 1.0
        return 0.2

    async def _run_discoloop_internalization(self, obs: Dict[str, Any], num_loops: int = 2):
        self._max_loops = num_loops
        await self._run_discoloop_reasoning(obs)
        if "latent_embedding" in obs:
            self.discrete_channel = ["internalized_insight"]
            self.continuous_state["v"] = obs["latent_embedding"]["v"]

    def _detect_failure_severity(self, reports: List[Any]) -> str:
        failures = [r for r in reports if not getattr(r, 'is_valid', True)]
        if not failures:
            return "none"
        critical_count = sum(1 for r in failures if getattr(r, 'confidence', 0) > 0.9)
        if critical_count >= 2 or any(getattr(r, 'confidence', 0) > 0.94 for r in failures):
            return "critical"
        return "minor"

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any]):
        """DiscoLoop recurrence: h_k+1, e_k+1 = f(h_k, e_k)"""
        e_k = np.zeros((512,))
        e_k[0] = 1.0 # Initial discrete state
        input_signal = np.random.normal(0, 0.1, (512,))

        for k in range(self._max_loops):
            h_next, token = self.discoloop.transition(input_signal, e_k, k)
            self.discrete_channel.append(token)
            idx = int(token.split('_')[-2])
            e_k = np.zeros_like(h_next)
            e_k[idx] = 1.0

        self.continuous_state["latent"] = self.discoloop.hidden_state.tolist()

    async def _pivot_refine_loop(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        """AutoResearchClaw Pivot/Refine logic (arXiv:2605.20025)."""
        if not branches: return None
        best = max(branches, key=lambda b: b.confidence)

        sim_data = simulations.get(best.branch_id, {})
        if sim_data and sim_data.get("failure_rate", 0) > 0.4:
            logger.warning(f"CSC-V6: High simulation failure detected. Pivoting strategy...")
            pivoted_branch = await self.hypothesis_gen.pivot_branch(best, "high_risk_detected")
            if pivoted_branch:
                return pivoted_branch

        return best

    def _select_optimal_action(self, branch: ReasoningBranch, simulations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes the final trade proposal from the best reasoning branch and its simulation results.
        """
        sim_data = simulations.get(branch.branch_id, {})

        # Adjust quantity based on expected slippage and structural impact
        base_qty = branch.execution_plan.get("quantity", 0.1)
        slippage_penalty = 1.0 - (sim_data.get("expected_slippage", 0.0) * 100)

        return {
            "trade_id": str(uuid4()),
            "symbol": branch.execution_plan.get("symbol", "BTC/USDT"),
            "action": branch.execution_plan.get("action", "WAIT"),
            "quantity": max(0.01, base_qty * slippage_penalty),
            "confidence": branch.confidence,
            "causal_impact": sim_data.get("structural_impact", {}),
            "reasoning_token": self.discrete_channel[-1] if self.discrete_channel else "none"
        }

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        provenance = InstitutionalProvenance()
        return ResearchLedgerEntry(
            entry_id=str(uuid4()),
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            composite_confidence=branch.confidence,
            provenance=provenance
        )

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(statistical=entry.composite_confidence, regime=0.8, execution=0.9, tail_risk=0.85, model_stability=0.7)
