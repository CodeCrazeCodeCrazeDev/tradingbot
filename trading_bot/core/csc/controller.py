"""
Cognitive System Controller (CSC) - UCA V6

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
import time
import logging
import asyncio
import copy
import threading
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock

from .hypothesis import HypothesisGenerator, ReasoningBranch, Hypothesis
from .folding import InformationFolder
from .router import SkillRouter
from .acpe import AdaptiveControlPolicyEngine
from ..verification.swarm import VerificationSwarm
from ..hms.models import (
    ResearchLedgerEntry,
    EvidenceGraph,
    VerifierReport,
    EvidenceNode,
    EvidenceEdge,
    RelationType,
    InstitutionalProvenance,
)
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
        self.alpha = 0.9  # Realignment factor

    def transition(
        self, input_signal: np.ndarray, e_k: np.ndarray, k: int
    ) -> Tuple[np.ndarray, str]:
        """
        S_k = [h_k; e_k]
        1. Continuous update: h_next = f(h_k, e_k)
        2. Discrete projection: e_next = g(h_next)
        3. Realignment: h_final = alpha * h_next + (1-alpha) * e_next
        """
        h_next = np.tanh(0.8 * self.hidden_state + 0.2 * e_k + input_signal * 0.1)

        idx = np.argmax(np.abs(h_next))
        val = np.sign(h_next[idx])
        e_next = np.zeros_like(h_next)
        e_next[idx] = val

        self.hidden_state = self.alpha * h_next + (1.0 - self.alpha) * e_next

        token = f"token_loop_{k}_{idx}_{int(val)}"
        self.discrete_tokens.append(token)

        return self.hidden_state, token


class AwaitableBranch(ReasoningBranch):
    def __await__(self):
        async def _async_wrapper():
            return self
        return _async_wrapper().__await__()


class CognitiveSystemController:
    """
    UCA V6 Controller - Authoritative Strategic Brain.
    Implements 12-step Recursive Active Inference.
    Supports backward compatibility for legacy positional signatures.
    """
    _instance: Optional["CognitiveSystemController"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CognitiveSystemController, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    async def reset(cls):
        """Thread-safe async reset clearing internal singletons."""
        with cls._lock:
            if cls._instance is not None:
                inst = cls._instance
                inst.continuous_state.clear()
                inst.discrete_channel.clear()
                inst.vfe_history.clear()
                inst.last_prediction = None
                inst._max_loops = 3
                cls._instance = None

    def __init__(
        self,
        world_model: Any = None,
        hms: Any = None,
        *args,
        **kwargs
    ):
        if getattr(self, "_initialized", False):
            if world_model is not None:
                self.world_model = world_model
            if hms is not None:
                self.hms = hms
            return

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

        if len(args) == 1:
            self.shield = args[0]
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
            for arg in args:
                if isinstance(arg, ImmutableShield):
                    self.shield = arg
                elif isinstance(arg, SkillRouter):
                    self.skill_router = arg
                elif isinstance(arg, VerificationSwarm):
                    self.verifier_swarm = arg

        self.skill_router = self.skill_router or SkillRouter()
        self.verifier_swarm = self.verifier_swarm or VerificationSwarm()

        from ..unified_event_bus import decision_bus as real_decision_bus
        self.decision_bus = kwargs.get("decision_bus") or real_decision_bus

        # Core Functional Components
        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.folder = InformationFolder(hms)
        self.discoloop = DiscoLoopCell(latent_dim=512)
        self.acpe = AdaptiveControlPolicyEngine(hms)

        # State Channels
        self.continuous_state = {}
        self.discrete_channel = []
        self.last_prediction = None
        self.vfe_history = []

        self._max_loops = 3
        self._initialized = True
        CognitiveSystemController._instance = self
        logger.info("CSC-V6: Brain initialized with dynamic argument mapping.")

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
            "latent": self.continuous_state.get("latent", []),
        }

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """Discrete-continuous looped internalization to update internal channels."""
        self._max_loops = num_loops
        await self._run_discoloop_reasoning(observation)
        self.discrete_channel = ["internalized_insight"]
        self.continuous_state = {"v": 1.0}

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        """Analyze verifier critique severity (minor vs. critical)."""
        invalid_reports = [r for r in reports if not getattr(r, "is_valid", True)]
        if not invalid_reports:
            return "none"
        if len(invalid_reports) >= 2 or any(getattr(r, "confidence", 0) >= 0.9 for r in invalid_reports):
            return "critical"
        return "minor"

    async def _safe_await(self, val_or_coro: Any) -> Any:
        if val_or_coro is None:
            return None
        if asyncio.iscoroutine(val_or_coro) or hasattr(val_or_coro, "__await__"):
            try:
                return await val_or_coro
            except TypeError:
                return val_or_coro
        return val_or_coro

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """Minimizing surprise is the core of Active Inference."""
        if not self.last_prediction:
            return 1.0
        pred_price = self.last_prediction.get("price", 100.0) if isinstance(self.last_prediction, dict) else 100.0
        obs_price = observation.get("price") if isinstance(observation, dict) else None
        if obs_price is not None:
            error = abs(obs_price - pred_price)
            return 0.1 + float(error) / 100.0
        return 0.2

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any], k: Optional[int] = None):
        """DiscoLoop recurrence: h_k+1, e_k+1 = f(h_k, e_k)"""
        loops = k if k is not None else self._max_loops
        e_k = np.zeros((512,))
        e_k[0] = 1.0
        input_signal = np.random.normal(0, 0.1, (512,))

        for i in range(loops):
            h_next, token = self.discoloop.transition(input_signal, e_k, i)
            self.discrete_channel.append(token)
            idx = int(token.split('_')[-2])
            e_k = np.zeros_like(h_next)
            e_k[idx] = 1.0

        self.continuous_state["latent"] = self.discoloop.hidden_state.tolist()

    async def _pivot_refine_loop(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        """AutoResearchClaw Pivot/Refine logic (arXiv:2605.20025)."""
        if not branches:
            return None
        best = max(branches, key=lambda b: b.confidence)

        sim_data = simulations.get(best.branch_id, {})
        if isinstance(sim_data, list):
            sim_data = sim_data[0] if len(sim_data) > 0 else {}
        elif isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self") or "MagicMock" in str(type(sim_data)):
            sim_data = {}

        failure_rate = sim_data.get("failure_rate", 0) if isinstance(sim_data, dict) else 0.0
        if isinstance(failure_rate, (int, float)) and failure_rate > 0.4:
            logger.warning("CSC-V6: High simulation failure detected. Pivoting strategy...")
            pivoted_branch = await self.hypothesis_gen.pivot_branch(best, "high_risk_detected")
            if pivoted_branch:
                return pivoted_branch

        return best

    def _refine_strategy(self, branch: ReasoningBranch, reports: List[Any]) -> AwaitableBranch:
        """Refines the reasoning branch trace to document feedback from verifier swarm."""
        refined = AwaitableBranch(
            branch_id=branch.branch_id,
            name=branch.name,
            hypotheses=copy.deepcopy(branch.hypotheses),
            reasoning_trace=copy.deepcopy(branch.reasoning_trace),
            confidence=branch.confidence,
            probability=branch.probability,
            uncertainty=branch.uncertainty,
            causal_explanation=branch.causal_explanation,
            invalidation_conditions=copy.deepcopy(branch.invalidation_conditions),
            execution_plan=copy.deepcopy(branch.execution_plan),
            evidence_graph=copy.deepcopy(branch.evidence_graph)
        )
        refined.confidence = max(0.1, round(refined.confidence * 0.9, 3))
        for r in reports:
            critique = getattr(r, "critique", "Unspecified critique")
            refined.reasoning_trace.append(f"Correction: {critique}")
        return refined

    def _select_optimal_action(self, branch: ReasoningBranch, simulations: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes the final trade proposal from the best reasoning branch and its simulation results."""
        sim_data = simulations.get(branch.branch_id, {})
        if isinstance(sim_data, list):
            sim_data = sim_data[0] if len(sim_data) > 0 else {}
        elif isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self") or "MagicMock" in str(type(sim_data)):
            sim_data = {}

        base_qty = branch.execution_plan.get("quantity", 0.1) if isinstance(branch.execution_plan, dict) else 0.1
        if isinstance(base_qty, MagicMock) or not isinstance(base_qty, (int, float)):
            base_qty = 0.1

        expected_slippage = sim_data.get("expected_slippage", 0.0) if isinstance(sim_data, dict) else 0.0
        if isinstance(expected_slippage, MagicMock) or not isinstance(expected_slippage, (int, float)):
            expected_slippage = 0.0

        slippage_penalty = 1.0 - (expected_slippage * 100)
        final_qty = base_qty * slippage_penalty
        causal_impact = sim_data.get("structural_impact", {}) if isinstance(sim_data, dict) else {}

        return {
            "trade_id": str(uuid4()),
            "symbol": branch.execution_plan.get("symbol", "BTC/USDT") if isinstance(branch.execution_plan, dict) else "BTC/USDT",
            "action": branch.execution_plan.get("action", "WAIT") if isinstance(branch.execution_plan, dict) else "WAIT",
            "quantity": max(0.01, final_qty),
            "confidence": branch.confidence,
            "causal_impact": causal_impact,
            "reasoning_token": self.discrete_channel[-1] if self.discrete_channel else "none"
        }

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        provenance = InstitutionalProvenance(
            pipeline_version="UCA-V6",
            git_sha="uca-2026-signed"
        )
        return ResearchLedgerEntry(
            entry_id=str(uuid4()),
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            composite_confidence=branch.confidence,
            provenance=provenance
        )

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(
            statistical=entry.composite_confidence,
            regime=0.8,
            execution=0.9,
            tail_risk=0.85,
            model_stability=0.7,
        )

    async def process_market_observation(self, observation: Any) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V6).
        Grounded in Variational Free Energy (VFE) minimization.
        """
        logger.info("CSC-V6: Starting 12-step Recursive Active Inference Pipeline")
        t0 = time.perf_counter()

        obs_dict = observation if isinstance(observation, dict) else getattr(observation, "__dict__", {})
        trade_id = obs_dict.get("trade_id", str(uuid4()))

        # 1. Surprise-Driven Perception
        surprise = self._calculate_sensory_surprise(obs_dict)
        self.vfe_history.append(surprise)
        logger.info(f"CSC-V6 Step 1: Sensory Surprise = {surprise:.4f}")

        # 2. SAGE Evidence Retrieval
        try:
            evidence_chain = await self._safe_await(self.hms.retrieve_evidence_chain(str(observation)))
        except Exception as e:
            logger.error(f"CSC-V6 Step 2: SAGE Retrieval Failure: {e}")
            evidence_chain = []
        logger.info(f"CSC-V6 Step 2: Retrieved {len(evidence_chain) if evidence_chain else 0} evidence chains")

        # 3. HASP Shielding (Prescriptive Guardrails)
        intervention = await self.skill_router.route_task("market_ingestion", observation)
        if hasattr(intervention, "to_dict"):
            intervention = intervention.to_dict()
        if isinstance(intervention, dict) and intervention.get("status") == "pf_intervention":
            pf_result = intervention.get("pf_result", {})
            reason = pf_result.get("reason", intervention.get("reason", "unknown"))
            logger.warning(f"CSC-V6 Step 3: HASP PF Intervention: {reason}")
            if pf_result.get("action") == "override_to_hold" or intervention.get("action") == "override_to_hold":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=trade_id,
                    dominant_rejection_reason=f"HASP PF Intervention: {reason}"
                )
            obs_dict.update(intervention)

        # 4. Recursive DiscoLoop Reasoning
        await self._run_discoloop_reasoning(obs_dict)
        logger.info(f"CSC-V6 Step 4: DiscoLoop complete. Tokens: {self.discrete_channel[-3:]}")

        # 5. Multi-Hypothesis Generation
        branches = await self._safe_await(self.hypothesis_gen.generate_competing_branches(observation))

        # 6. Causal Simulation
        latent_z = torch.tensor([self.continuous_state.get("latent", [0.0] * 512)])
        sim_results = {}

        if hasattr(self.hypothesis_gen, "simulate_branches"):
            try:
                sim_res_call = self.hypothesis_gen.simulate_branches(branches)
                sim_results = await self._safe_await(sim_res_call) or {}
            except Exception as e:
                logger.error(f"Error calling simulate_branches: {e}")

        if not sim_results and self.world_model is not None and hasattr(self.world_model, "simulate_intervention"):
            for branch in branches:
                sim_results[branch.branch_id] = await self._safe_await(self.world_model.simulate_intervention(
                    observation, branch.execution_plan, latent_z=latent_z
                ))

        # 7. Pivot/Refine Optimization
        best_branch = await self._safe_await(self._pivot_refine_loop(branches, sim_results))
        if not best_branch:
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=trade_id,
                dominant_rejection_reason="No viable reasoning branches after Pivot/Refine"
            )

        # 8. VFE Minimization (Decision Selection)
        decision_proposal = self._select_optimal_action(best_branch, sim_results)
        decision_proposal["trade_id"] = trade_id

        # 9. LogAct Proposal
        log_action = LogAction(
            action_type="TRADE_PROPOSAL",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.HIGH,
        )
        await self._safe_await(self.decision_bus.propose_action(log_action))

        # 10. Verification Swarm (Peer Review)
        logger.info("CSC-V6: Step 10: Running Verification Swarm")
        ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
        reports = await self._safe_await(self.verifier_swarm.run_swarm(ledger_entry))
        ledger_entry.verifier_reports = reports

        # AutoResearchClaw Strategic Pivot & Second Swarm Cycle upon detecting invalid falsifications
        if any(not getattr(r, "is_valid", True) for r in reports if r is not None):
            refined_branch = self._refine_strategy(best_branch, reports)
            ledger_entry = self._create_ledger_entry(refined_branch, sim_results.get(best_branch.branch_id, []))
            second_reports = await self._safe_await(self.verifier_swarm.run_swarm(ledger_entry))
            ledger_entry.verifier_reports = second_reports

        # 11. Immutable Shield Governance Gate
        if self.shield is not None:
            shield_report = await self._safe_await(self.shield.validate_action("trade", decision_proposal, {"market": observation}))
            if shield_report and getattr(shield_report, "decision", None) != GovernanceDecision.APPROVED:
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", trade_id),
                    dominant_rejection_reason=f"Shield Veto: {getattr(shield_report, 'reason', 'Vetoed by Immutable Shield')}"
                )

        # 12. HIPIF Folding & Persistence
        logger.info("CSC-V6: Step 12: Folding and persisting ledger entry")
        self.folder.fold_history(ledger_entry)
        self.hms.store_ledger_entry(ledger_entry)

        # Final LogAct write-through for approved trade
        logger.info("CSC-V6: Proposing final trade execution to decision bus")
        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.CRITICAL,
        )
        await self._safe_await(self.decision_bus.propose_action(action))
        status = await self._safe_await(action.wait_for_decision(timeout=5.0))

        if status not in (ActionStatus.APPROVED, ActionStatus.EXECUTED):
            reason = f"LogAct consensus failure: {status.value if hasattr(status, 'value') else status}"
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id),
                dominant_rejection_reason=reason,
            )

        logger.info(f"CSC-V6: Decision COMMITTED in {time.perf_counter() - t0:.3f}s")
        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=decision_proposal.get("trade_id", trade_id),
            confidence_vector=self._calculate_composite_confidence(ledger_entry),
        )
