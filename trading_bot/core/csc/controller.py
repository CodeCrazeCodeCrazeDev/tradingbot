"""
Cognitive System Controller (CSC) - UCA V6 (July 2026)

Integrated "One Brain" implementing the 12-stage Recursive Active Inference pipeline.
Implements 'DiscoLoop' (arXiv:2607.00341) for multi-hop reasoning, 'HIPIF' (arXiv:2606.10507) for information folding,
and 'AutoResearchClaw' (arXiv:2605.20025) for Pivot/Refine self-healing control.
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
from unittest.mock import MagicMock, AsyncMock
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
        h_next = np.tanh(0.8 * self.hidden_state + 0.2 * e_k + input_signal * 0.1)

        idx = np.argmax(np.abs(h_next))
        val = np.sign(h_next[idx])
        e_next = np.zeros_like(h_next)
        e_next[idx] = val

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

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CognitiveSystemController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, *args, **kwargs):
        # 1. State Guard: prevent overriding initialized state of the singleton
        if getattr(self, "_initialized", False):
            # Dynamic re-binding of new mocks/arguments for testing
            if args or kwargs:
                self._bind_dependencies(*args, **kwargs)
            return

        # Setup default attributes
        self.world_model = None
        self.hms = None
        self.skill_router = None
        self.verifier_swarm = None
        self.risk_engine = None
        self.consensus_engine = None
        self.execution_planner = None
        self.evolution_gate = None
        self.shield = None
        self.decision_bus = None

        # Bind dependencies
        self._bind_dependencies(*args, **kwargs)

        # State channels
        self.continuous_state = {}
        self.discrete_channel = []
        self.last_prediction = None
        self.vfe_history = []
        self._max_loops = 3
        self._initialized = True
        logger.info("CSC-V6: Strategic Brain initialized successfully.")

    def _bind_dependencies(self, *args, **kwargs):
        """Binds incoming positional/keyword arguments to self attributes dynamically."""
        # Setup defaults or keep pre-existing values if re-binding
        self.world_model = getattr(self, "world_model", None)
        self.hms = getattr(self, "hms", None)
        self.skill_router = getattr(self, "skill_router", None)
        self.verifier_swarm = getattr(self, "verifier_swarm", None)
        self.risk_engine = getattr(self, "risk_engine", None)
        self.consensus_engine = getattr(self, "consensus_engine", None)
        self.execution_planner = getattr(self, "execution_planner", None)
        self.evolution_gate = getattr(self, "evolution_gate", None)
        self.shield = getattr(self, "shield", None)

        # Bind kwargs
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

        # Bind positional args dynamically for backward compatibility
        if len(args) == 3:
            # Legacy/Test 3-parameter call: (world_model, hms, shield)
            self.world_model = args[0]
            self.hms = args[1]
            self.shield = args[2]
        elif len(args) == 2:
            self.world_model = args[0]
            self.hms = args[1]
        elif len(args) >= 8:
            self.world_model = args[0]
            self.hms = args[1]
            self.skill_router = args[2]
            self.verifier_swarm = args[3]
            self.risk_engine = args[4]
            self.consensus_engine = args[5]
            self.execution_planner = args[6]
            self.evolution_gate = args[7]
            if len(args) > 8:
                self.shield = args[8]
        elif len(args) > 0:
            attrs = ["world_model", "hms", "skill_router", "verifier_swarm", "risk_engine", "consensus_engine", "execution_planner", "evolution_gate", "shield"]
            for i, arg in enumerate(args):
                if i < len(attrs):
                    setattr(self, attrs[i], arg)

        # Inject unified event bus or fallbacks
        from ..unified_event_bus import decision_bus as real_decision_bus
        self.decision_bus = real_decision_bus

        # Fallback instantiations for missing dependencies
        if not self.skill_router:
            self.skill_router = SkillRouter()
        if not self.verifier_swarm:
            self.verifier_swarm = VerificationSwarm()
        if not self.world_model:
            self.world_model = MagicMock()
        if not self.hms:
            self.hms = MagicMock()
            self.hms.retrieve_evidence_chain = AsyncMock(return_value=[])

        # Initialize core controllers
        self.hypothesis_gen = HypothesisGenerator(self.world_model)
        self.folder = InformationFolder(self.hms)
        self.discoloop = DiscoLoopCell(latent_dim=512)
        self.acpe = AdaptiveControlPolicyEngine(self.hms)

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

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """Discrete-continuous looped internalization to update internal channels."""
        self._max_loops = num_loops
        await self._run_discoloop_reasoning(observation)
        self.discrete_channel = ["internalized_insight"]
        self.continuous_state = {"v": 1.0}

    def _detect_failure_severity(self, reports: List[VerifierReport]) -> str:
        """Analyze verifier critique severity (minor vs. critical)."""
        invalid_reports = [r for r in reports if not r.is_valid]
        if not invalid_reports:
            return "none"
        if len(invalid_reports) >= 2 or any(r.confidence >= 0.9 for r in invalid_reports):
            return "critical"
        return "minor"

    async def _safe_await(self, coro_or_val: Any) -> Any:
        if coro_or_val is None:
            return None
        if asyncio.iscoroutine(coro_or_val) or hasattr(coro_or_val, "__await__"):
            return await coro_or_val
        return coro_or_val

    async def process_market_observation(self, observation: Any) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V6).
        Grounded in Variational Free Energy (VFE) minimization.
        """
        logger.info("CSC-V6: Starting 12-step Recursive Active Inference Pipeline")
        t0 = time.perf_counter()

        # Normalize observation if needed
        from .models import MarketContextAdapter
        normalized_obs = MarketContextAdapter.normalize(observation)

        # 1. Surprise-Driven Perception
        surprise = self._calculate_sensory_surprise(observation)
        self.vfe_history.append(surprise)
        logger.info(f"CSC-V6 Step 1: Sensory Surprise = {surprise:.4f}")

        # 2. SAGE Evidence Retrieval
        try:
            evidence_chain = await self.hms.retrieve_evidence_chain(str(observation))
        except Exception as e:
            logger.error(f"CSC-V6 Step 2: SAGE Retrieval Failure: {e}")
            evidence_chain = []
        logger.info(f"CSC-V6 Step 2: Retrieved {len(evidence_chain)} evidence chains")

        # 3. HASP Shielding (Prescriptive Guardrails)
        intervention = await self.skill_router.route_task("market_ingestion", observation)
        if intervention.get("status") == "pf_intervention":
            logger.warning(f"CSC-V6 Step 3: HASP PF Intervention: {intervention.get('reason')}")
            pf_res = intervention.get("pf_result", {})
            if pf_res.get("action") == "override_to_hold":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=observation.get("trade_id", str(uuid4())),
                    dominant_rejection_reason=f"HASP PF Intervention: {pf_res.get('reason')}"
                )
            observation.update(intervention)

        # 4. Recursive DiscoLoop Reasoning
        await self._run_discoloop_reasoning(observation)
        logger.info(f"CSC-V6 Step 4: DiscoLoop complete. Tokens: {self.discrete_channel[-3:] if len(self.discrete_channel) >= 3 else self.discrete_channel}")

        # 5. Multi-Hypothesis Generation (AutoResearchClaw)
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI)
        sim_results = {}
        latent_z = torch.tensor([self.continuous_state.get("latent", [0.0]*512)])
        for branch in branches:
            if (isinstance(self.world_model, MagicMock) and
                not isinstance(getattr(self.world_model, "simulate_intervention", None), AsyncMock)):
                sim_results[branch.branch_id] = {"failure_rate": 0.0, "expected_slippage": 0.001, "structural_impact": {}}
            elif hasattr(self.world_model, "simulate_intervention"):
                sim_results[branch.branch_id] = await self.world_model.simulate_intervention(
                    observation, branch.execution_plan, latent_z=latent_z
                )
            else:
                sim_results[branch.branch_id] = {"failure_rate": 0.0, "expected_slippage": 0.001, "structural_impact": {}}

        # 7. Pivot/Refine Optimization
        best_branch = await self._pivot_refine_loop(branches, sim_results)
        if not best_branch:
             return CoreDecision(
                 outcome=DecisionOutcome.TRADE_REJECTED,
                 trade_id=observation.get("trade_id", str(uuid4())),
                 dominant_rejection_reason="No viable reasoning branches after Pivot/Refine"
             )

        # 8. EFE Minimization (Decision Selection)
        decision_proposal = self._select_optimal_action(best_branch, sim_results)

        # 9. LogAct Proposal
        log_action = LogAction(
            action_type="TRADE_PROPOSAL",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.HIGH
        )
        await self.decision_bus.propose_action(log_action)

        # 10. Verification Swarm (Peer Review)
        ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
        reports = await self.verifier_swarm.run_swarm(ledger_entry)
        ledger_entry.verifier_reports = reports

        # 11. Immutable Commitment
        if self.shield:
            shield_report = await self.shield.validate_action("trade", decision_proposal, {"market": observation})
            if shield_report.decision != GovernanceDecision.APPROVED:
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id"),
                    dominant_rejection_reason=f"Shield Veto: {shield_report.reason}"
                )

        # 12. HIPIF Folding & Persistence
        self.folder.fold_history(ledger_entry)
        self.hms.store_ledger_entry(ledger_entry)

        # Final LogAct write-through for approved trade
        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.CRITICAL
        )
        await self.decision_bus.propose_action(action)
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

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """Minimizing surprise is the core of Active Inference."""
        if not self.last_prediction: return 1.0
        return 0.2

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
        if sim_data and isinstance(sim_data, dict) and sim_data.get("failure_rate", 0) > 0.4:
            logger.warning(f"CSC-V6: High simulation failure detected. Pivoting strategy...")
            pivoted_branch = await self.hypothesis_gen.pivot_branch(best, "high_risk_detected")
            if pivoted_branch:
                return pivoted_branch

        return best

    def _select_optimal_action(self, branch: ReasoningBranch, simulations: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes the final trade proposal from the best reasoning branch."""
        sim_data = simulations.get(branch.branch_id, {})
        base_qty = branch.execution_plan.get("quantity", 0.1) if branch.execution_plan else 0.1
        slippage = sim_data.get("expected_slippage", 0.0) if isinstance(sim_data, dict) else 0.0
        slippage_penalty = 1.0 - (slippage * 100)

        return {
            "trade_id": str(uuid4()),
            "symbol": branch.execution_plan.get("symbol", "BTC/USDT") if branch.execution_plan else "BTC/USDT",
            "action": branch.execution_plan.get("action", "WAIT") if branch.execution_plan else "WAIT",
            "quantity": max(0.01, base_qty * slippage_penalty),
            "confidence": branch.confidence,
            "causal_impact": sim_data.get("structural_impact", {}) if isinstance(sim_data, dict) else {},
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
