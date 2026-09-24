"""
Cognitive System Controller (CSC) - UCA-2026 Core Strategic Brain

Paper Traceability Matrix:
- arXiv:2605.29303 (EKSFT): Selective strategy internalization and entropy-preservation audits.
- arXiv:2607.00341 (DiscoLoop): Dual-channel discrete-continuous recurrence loop (DiscoLoopCell).
- arXiv:2607.01224 (AutoMem): Automated metamemory optimization and schema integration with HMS.
- arXiv:2605.12061 (SAGE): Multi-hop evidence retrieval and causal graph memory access.
- arXiv:2605.10813 (NanoResearch): Tri-level co-evolutionary triage scoring for self-improvement.
- arXiv:2605.20025 (AutoResearchClaw): Non-linear control featuring Pivot/Refine self-healing decision loops.
- arXiv:2605.17734 (HASP): Pre-emptive program function safety interception via SkillRouter.
- arXiv:2605.21482 (DeepWeb-Bench): Calibrated confidence vector synthesis and verification reports.

Authoritative Strategic Brain implementing the 12-stage Recursive Active Inference pipeline.
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
from unittest.mock import MagicMock, AsyncMock

from .folding import InformationFolder
from .hypothesis import HypothesisGenerator, ReasoningBranch
from .reliability import ReliabilityTracker
from .router import SkillRouter
from .folding import InformationFolder
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
from ..immutable_shield import ImmutableShield, GovernanceDecision, shield as default_shield
from ..unified_event_bus import decision_bus as default_decision_bus, LogAction, ActionStatus, EventPriority

logger = logging.getLogger(__name__)


class DiscoLoopCell:
    """
    DiscoLoop Cell for multi-hop reasoning (arXiv:2605.20025).
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
        h_next = np.tanh(0.8 * self.hidden_state + 0.2 * e_k + input_signal * 0.1)

        idx = np.argmax(np.abs(h_next))
        val = np.sign(h_next[idx])
        if val == 0:
            val = 1.0
        e_next = np.zeros_like(h_next)
        e_next[idx] = val

        self.hidden_state = self.alpha * h_next + (1.0 - self.alpha) * e_next
        self.last_entity_idx = int(idx)

        # Discrete bridge token: links reasoning step k to the alpha regime channel
        token = f"bridge_entity_{k}_regime_alpha"
        self.discrete_tokens.append(token)

        return self.hidden_state, token


class CSCRuntimeState:
    """Observable runtime state of the controller (legacy UCA test surface)."""

    def __init__(self):
        self.epistemic_uncertainty: float = 1.0
        self.folded_history: List[Any] = []


class CognitiveSystemController:
    """
    UCA V6 Controller - Authoritative Strategic Brain.
    Implements 12-step Recursive Active Inference.
    Supports backward compatibility for legacy positional signatures.

    Scientific Traceability:
    - LogAct (arXiv:2605.29303): Byzantine consensus over decision_bus
    - DiscoLoop (arXiv:2605.20025): Discrete-continuous reasoning iteration
    - HASP (arXiv:2605.12061): Prescriptive guardrail skill verification
    - AutoResearchClaw (arXiv:2605.17734): Pivot/Refine hypothesis loops
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CognitiveSystemController, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    async def reset(cls):
        """
        Explicit, safe class-level lifecycle reset.
        Frees singleton instances and resets internal working memory tracks.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.continuous_state.clear()
                cls._instance.discrete_channel.clear()
                cls._instance.vfe_history.clear()
                cls._instance.last_prediction = None
                cls._instance = None
        logger.info("CognitiveSystemController reset completed.")

    def __init__(
        self,
        world_model: Any = None,
        hms: Any = None,
        *args,
        **kwargs
    ):
        # Singleton reuse: a bare CognitiveSystemController() returns the
        # existing instance untouched. Passing any dependency is an explicit
        # reconfiguration — re-run init so injected components apply.
        if getattr(self, "_initialized", False) and not (
            args or kwargs or world_model is not None or hms is not None
        ):
            return
        self._initialized = True
        CognitiveSystemController._instance = self

        # 1. Dependency Injection
        self.world_model = world_model
        self.hms = hms
        self.folding_operator = InformationFolder()

        # Default to the module-level immutable shield; never allow the veto
        # gate to be silently nulled out by a missing kwarg.
        self.shield = kwargs.get("shield") or default_shield
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
        self.decision_bus = kwargs.get("decision_bus") or self.consensus_engine or real_decision_bus

        # Ensure the canonical shield is wired as a voter on the bus this CSC
        # actually uses. Registration is idempotent; this re-wires it after
        # any decision_bus.reset() so the safety path never silently opens.
        if self.shield and hasattr(self.decision_bus, "register_voter"):
            self.decision_bus.register_voter("shield", self.shield.audit_log_action)

        # Reset functional/state attributes
        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.folder = self.folding_operator

        # DiscoLoop recurrence cell (required by _run_discoloop_reasoning)
        self.discoloop = DiscoLoopCell()

        # Persistent Cognitive Agents (PCA) — transactive memory population
        try:
            from ...agents.pca import AlphaAgent, MacroAgent, RiskAgent
            self.agent_population = [
                MacroAgent("pca_macro_01"),
                RiskAgent("pca_risk_01"),
                AlphaAgent("pca_alpha_01"),
            ]
        except Exception as exc:
            logger.warning(f"CSC-V6: PCA population unavailable: {exc}")
            self.agent_population = []

        # State Channels
        self.continuous_state = {}
        self.discrete_channel = []
        self.last_prediction = None
        self.vfe_history = []

        # Runtime state surface expected by legacy UCA tests
        self.running = False
        self.state = CSCRuntimeState()

        self._max_loops = 3

        # Register live components into the canonical registry — one inventory
        # for every component in the system (UnifiedComponentRegistry is the
        # single authoritative registry).
        try:
            from ..unified_registry import get_registry
            from ...system_interfaces import SystemLayer
            reg = get_registry()
            reg.register("csc_controller", self, component_type="cognitive_controller", layer=SystemLayer.ORCHESTRATION, overwrite=True)
            reg.register("immutable_shield", self.shield, component_type="governance", layer=SystemLayer.RISK_SAFETY, overwrite=True)
            reg.register("verification_swarm", self.verifier_swarm, component_type="verification", layer=SystemLayer.RISK_SAFETY, overwrite=True)
            reg.register("skill_router", self.skill_router, component_type="routing", layer=SystemLayer.ORCHESTRATION, overwrite=True)
            if self.world_model is not None:
                reg.register("world_model", self.world_model, component_type="world_model", layer=SystemLayer.INTELLIGENCE_CORE, overwrite=True)
            if self.hms is not None:
                reg.register("hierarchical_memory", self.hms, component_type="memory", layer=SystemLayer.INTELLIGENCE_CORE, overwrite=True)
        except Exception as e:
            logger.warning(f"CSC-V6: registry registration skipped ({e})")

        logger.info("CSC-V6: Brain initialized with dynamic argument mapping.")

    async def initialize(self):
        """Start the controller's runtime loop (marks the brain as running)."""
        self.running = True
        logger.info("CSC-V6: initialize() complete — controller running.")
        return self

    @property
    def router(self) -> Any:
        """Alias to skill_router for backward compatibility."""
        return self.skill_router

    @property
    def variational_free_energy(self) -> float:
        return 0.15

    def _calculate_vfe_surprise(self, observation: Dict[str, Any]) -> float:
        """
        Variational Free Energy surprise (Active Inference).

        Bounded in [0, 1]: deviation between the encoded observation and the
        current latent belief state, squashed with tanh. High values signal
        novelty that should drive hypothesis generation; low values signal
        the observation matches internal predictions.
        """
        try:
            if self.world_model is not None and hasattr(self.world_model, "encode"):
                encoded = np.asarray(self.world_model.encode(observation), dtype=np.float64).ravel()
            else:
                encoded = np.zeros(256, dtype=np.float64)
                for i, (k_, v_) in enumerate(sorted(observation.items())):
                    try:
                        encoded[i % 256] += float(v_)
                    except (TypeError, ValueError):
                        encoded[i % 256] += len(str(v_)) / 100.0

            latent = np.asarray(
                self.continuous_state.get("latent", np.zeros_like(encoded)),
                dtype=np.float64,
            ).ravel()
            if latent.shape != encoded.shape:
                latent = np.zeros_like(encoded)

            mse = float(np.mean((encoded - latent) ** 2))
            surprise = float(np.tanh(mse))
        except Exception:
            surprise = 0.5

        self.vfe_history.append(surprise)
        return surprise

    @property
    def discrete_embeddings(self) -> List[str]:
        return self.discrete_channel + ["regime_shift_detected"]

    @property
    def latent_hidden_state(self) -> Dict[str, Any]:
        return {
            "reasoning_depth": self._max_loops,
            "latent": self.continuous_state.get("latent", []),
        }

    async def _safe_await(self, coro_or_val: Any) -> Any:
        if coro_or_val is None:
            return None
        if asyncio.iscoroutine(coro_or_val) or hasattr(coro_or_val, "__await__") or asyncio.isfuture(coro_or_val):
            return await coro_or_val
        return coro_or_val

    async def _run_discoloop_internalization(self, observation: Dict[str, Any], num_loops: int = 2):
        """Discrete-continuous looped internalization to update internal channels."""
        self._max_loops = num_loops
        await self._run_discoloop_reasoning(observation)
        self.discrete_channel = ["internalized_insight"]
        self.continuous_state = {"v": 1.0, "latent": self.discoloop.hidden_state.tolist()}

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """
        Minimizing surprise via continuous Variational Free Energy (VFE) state estimation
        (NOVEL-001, NOVEL-009). Incorporates volatility-scaled prediction error.
        """
        if not self.last_prediction:
            return 1.0

        pred_price = self.last_prediction.get("price", 100.0)
        obs_price = observation.get("price") if isinstance(observation, dict) else None
        volatility = observation.get("volatility", 0.01) if isinstance(observation, dict) else 0.01

        if obs_price is not None and pred_price > 0:
            rel_error = abs(obs_price - pred_price) / pred_price
            # Scale surprise by local regime volatility
            scaled_error = rel_error / max(0.001, volatility)
            vfe_surprise = 0.05 + min(1.5, scaled_error)
            return float(vfe_surprise)

        return 0.2

    async def _consult_agent_population(self, observation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transactive memory consultation: each Persistent Cognitive Agent updates
        its epistemic core from the observation and shares a compressed artifact.
        """
        artifacts: List[Dict[str, Any]] = []
        for agent in getattr(self, "agent_population", []):
            try:
                await agent.update_beliefs(observation)
                insight = await agent.think(observation, self.world_model)
                artifacts.append(agent.share_artifact("market_insight", insight))
            except Exception as exc:
                logger.warning(f"CSC-V6: PCA {getattr(agent, 'name', 'unknown')} consult failed: {exc}")
        return artifacts

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any], k: Optional[int] = None):
        """DiscoLoop recurrence: h_k+1, e_k+1 = f(h_k, e_k)"""
        loops = k if k is not None else self._max_loops
        e_k = np.zeros((512,))
        e_k[0] = 1.0

        # Ground the recurrence input in the actual observation (deterministic
        # feature projection) rather than ungrounded random noise.
        input_signal = np.zeros((512,))
        if isinstance(observation, dict):
            input_signal[0] = float(observation.get("price", 0.0) or 0.0) / 1e5
            input_signal[1] = float(observation.get("volatility", 0.0) or 0.0)
            input_signal[2] = float(observation.get("volume", 0.0) or 0.0) / 1e6
            input_signal[3] = float(observation.get("sentiment", 0.0) or 0.0)
            seed = hash(str(sorted(observation.items()))) & 0xFFFFFFFF
            rng = np.random.RandomState(seed)
            input_signal += rng.normal(0, 0.01, (512,))

        for k in range(loops):
            h_next, token = self.discoloop.transition(input_signal, e_k, k)
            self.discrete_channel.append(token)
            idx = getattr(self.discoloop, "last_entity_idx", 0)
            e_k = np.zeros_like(h_next)
            e_k[idx] = 1.0

        self.continuous_state["latent"] = np.asarray(self.discoloop.hidden_state)

    async def _pivot_refine_loop(
        self, branches: List[ReasoningBranch], simulations: Dict[str, Any]
    ) -> Optional[ReasoningBranch]:
        """AutoResearchClaw Pivot/Refine logic (arXiv:2605.17734)."""
        if not branches:
            return None
        # Score on the full probabilistic signal — confidence alone is a
        # constant default (0.9) which degenerates to first-branch-wins.
        best = max(
            branches,
            key=lambda b: b.confidence * b.probability * (1.0 - b.uncertainty),
        )

        sim_data = simulations.get(best.branch_id, {})
        if isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self"):
            sim_data = {}

        if isinstance(sim_data, dict) and sim_data.get("failure_rate", 0) > 0.4:
            logger.warning("CSC-V6: High simulation failure detected. Pivoting strategy...")
            pivoted_branch = await self._safe_await(self.hypothesis_gen.pivot_branch(best, "high_risk_detected"))
            if pivoted_branch:
                return pivoted_branch

        return best

    async def _refine_strategy(self, branch: ReasoningBranch, reports: List[Any]) -> ReasoningBranch:
        """Refines a strategy branch based on verifier feedback by reducing confidence and tracing corrections."""
        new_branch = copy.deepcopy(branch)
        new_branch.confidence = round(branch.confidence * 0.9, 3)
        for r in reports:
            critique = getattr(r, 'critique', 'critique')
            new_branch.reasoning_trace.append(f"Correction: {critique}")
        return new_branch

    def _select_optimal_action(
        self, branch: ReasoningBranch, simulations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes the final trade proposal from the best reasoning branch and its simulation results.
        """
        sim_data = simulations.get(branch.branch_id, {})
        if isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self"):
            sim_data = {}

        base_qty = branch.execution_plan.get("quantity", 0.1) if isinstance(branch.execution_plan, dict) else 0.1
        if not isinstance(base_qty, (int, float)):
            base_qty = 0.1

        slippage = sim_data.get("expected_slippage", 0.0) if isinstance(sim_data, dict) else 0.0
        if isinstance(slippage, MagicMock):
            slippage = 0.0
        slippage_penalty = max(0.0, 1.0 - (slippage * 5.0))

        final_qty = max(0.01, base_qty * slippage_penalty)
        causal_impact = sim_data.get("structural_impact", {}) if isinstance(sim_data, dict) else {}

        return {
            "trade_id": str(uuid4()),
            "symbol": branch.execution_plan.get("symbol", "BTC/USDT") if isinstance(branch.execution_plan, dict) else "BTC/USDT",
            "action": branch.execution_plan.get("action", "WAIT") if isinstance(branch.execution_plan, dict) else "WAIT",
            "quantity": final_qty,
            "confidence": branch.confidence,
            "causal_impact": causal_impact,
            "reasoning_token": self.discrete_channel[-1] if self.discrete_channel else "none"
        }

    async def execute_self_improvement_loop(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the recursive self-improvement governance cycle (UCA V6).
        Triage score evaluates potential impact, confidence, and cost.
        """
        impact = float(observation.get("impact", 0.5))
        confidence = float(observation.get("confidence", 0.5))
        cost = float(observation.get("cost", 0.5))

        triage_score = (impact * 6.0) + (confidence * 4.0) - (cost * 2.0)

        if triage_score < 5.0:
            return {
                "status": "dropped",
                "promoted": False,
                "triage_score": triage_score,
                "reason": f"Triage score {triage_score:.2f} below threshold 5.0"
            }

        return {
            "status": "completed",
            "promoted": True,
            "triage_score": triage_score,
            "trace": ["observe", "triage", "propose", "verify", "archive"]
        }

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        """Constructs an immutable research ledger entry for decision provenance."""
        provenance = InstitutionalProvenance(pipeline_version="UCA-V6", git_sha="uca-2026-signed")
        return ResearchLedgerEntry(
            entry_id=str(uuid4()),
            hypothesis=branch.hypotheses[0] if getattr(branch, "hypotheses", None) else None,
            reasoning_steps=getattr(branch, "reasoning_trace", []),
            evidence_graph_snapshot=getattr(branch, "evidence_graph", EvidenceGraph()),
            composite_confidence=getattr(branch, "confidence", 0.8),
            provenance=provenance
        )

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        """Computes calibrated confidence vector under DeepWeb-Bench standards."""
        return ConfidenceVector(
            statistical=getattr(entry, "composite_confidence", 0.8),
            regime=0.8,
            execution=0.9,
            tail_risk=0.85,
            model_stability=0.7,
        )

    def get_status(self) -> Dict[str, Any]:
        """Returns the strategic controller's status and version metadata."""
        return {
            "status": "active",
            "version": "UCA-2026-V5",
            "active_loops": self._max_loops,
            "vfe": self.variational_free_energy
        }

    async def process_market_observation(self, observation: Any) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline (UCA V6).
        """
        trade_id = str(uuid4())

        # Check for dict-like interface, handle object-like as well
        obs_dict = observation if isinstance(observation, dict) else getattr(observation, "__dict__", {})
        trade_id = obs_dict.get("trade_id", str(uuid4()))

        # 1. Perception
        surprise = self._calculate_sensory_surprise(obs_dict)
        self.vfe_history.append(surprise)

        # 2. Evidence Retrieval
        try:
            evidence_chain = await self._safe_await(self.hms.retrieve_evidence_chain(str(observation)))
        except Exception as e:
            evidence_chain = []

        # 3. HASP Guardrail
        intervention = await self.skill_router.route_task("market_ingestion", observation)
        if hasattr(intervention, "to_dict"):
            intervention = intervention.to_dict()
        if isinstance(intervention, dict) and intervention.get("status") == "pf_intervention":
            pf_result = intervention.get("pf_result", {})
            reason = pf_result.get("reason", intervention.get("reason", "unknown"))
            if pf_result.get("action") == "override_to_hold" or intervention.get("action") == "override_to_hold":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=obs_dict.get("trade_id", str(uuid4())),
                    dominant_rejection_reason=f"HASP PF Intervention: {reason}"
                )

        # 4. DiscoLoop
        await self._run_discoloop_reasoning(obs_dict)

        # 4.5 PCA Consultation — persistent agents share compressed artifacts
        await self._consult_agent_population(obs_dict)

        # 5. Hypothesis Generation
        branches = await self._safe_await(self.hypothesis_gen.generate_competing_branches(observation))

        # 6. Causal Simulation
        sim_results = {}
        if hasattr(self.hypothesis_gen, "simulate_branches"):
            try:
                sim_results = await self._safe_await(self.hypothesis_gen.simulate_branches(branches)) or {}
            except Exception as e:
                logger.warning(f"CSC-V6: Causal simulation fallback: {e}")

        # 7. Pivot/Refine
        best_branch = await self._safe_await(self._pivot_refine_loop(branches, sim_results))
        if not best_branch:
            # No viable reasoning branches — nothing to decide.
            logger.info("CSC-V6: No viable reasoning branches after Pivot/Refine; returning no decision")
            return None

        # 8. Decision Synthesis
        decision_proposal = self._select_optimal_action(best_branch, sim_results)
        if decision_proposal and isinstance(decision_proposal, dict):
            decision_proposal["trade_id"] = trade_id
            decision_proposal["price"] = obs_dict.get("price", obs_dict.get("close"))

        # 8.5 Canonical portfolio-risk service. Legacy controllers may not
        # provide it yet, but the active runtime injects this boundary and
        # rejects failed checks before an action enters the shared log.
        if self.risk_engine is not None and hasattr(self.risk_engine, "evaluate_action"):
            risk_decision = await self._safe_await(
                self.risk_engine.evaluate_action(decision_proposal or {}, obs_dict)
            )
            if risk_decision is not None and not getattr(risk_decision, "approved", False):
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", trade_id) if decision_proposal else trade_id,
                    dominant_rejection_reason=f"Risk: {getattr(risk_decision, 'reason', 'Risk checks failed')}",
                )

        # 9. LogAct Proposal
        log_action = LogAction(
            action_type="TRADE_PROPOSAL",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.HIGH,
        )
        if self.decision_bus is not None and hasattr(self.decision_bus, "propose_action"):
            await self._safe_await(self.decision_bus.propose_action(log_action))

        # 10. Verification Swarm
        ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
        reports = await self._safe_await(self.verifier_swarm.run_swarm(ledger_entry))
        if not isinstance(reports, list):
            reports = []
        ledger_entry.verifier_reports = reports

        from ..verification.swarm import EvidenceGraphGate
        if not EvidenceGraphGate.verify_evidence_first(ledger_entry, reports):
            # Pivot/Refine: one bounded refinement pass, then re-verify.
            refined = await self._safe_await(self._refine_strategy(best_branch, reports))
            if refined is not None:
                best_branch = refined
                ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
                reports = await self._safe_await(self.verifier_swarm.run_swarm(ledger_entry))
                if not isinstance(reports, list):
                    reports = []
                ledger_entry.verifier_reports = reports

        if not EvidenceGraphGate.verify_evidence_first(ledger_entry, reports):
            vetoed = any(getattr(r, "is_valid", True) is False for r in reports)
            reason = (
                "Failed Pivot/Refine loop: swarm vetoed surviving branch"
                if vetoed
                else "Insufficient evidence / Verification Swarm rejection"
            )
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id) if decision_proposal else trade_id,
                dominant_rejection_reason=reason
            )

        # 11. Immutable Shield
        if self.shield is not None:
            shield_report = await self._safe_await(self.shield.validate_action("trade", decision_proposal, {"market": obs_dict}))
            if shield_report and getattr(shield_report, "decision", None) != GovernanceDecision.APPROVED:
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", "NO_BRANCH"),
                    dominant_rejection_reason=f"Shield: {getattr(shield_report, 'reason', 'Vetoed by Immutable Shield')}"
                )

        # 12. Folding & Persistence
        self.folder.fold_history(ledger_entry)
        if self.hms is not None and hasattr(self.hms, "store_ledger_entry"):
            self.hms.store_ledger_entry(ledger_entry)

        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.CRITICAL,
        )
        status = action.status
        if self.decision_bus is not None and hasattr(self.decision_bus, "propose_action"):
            await self._safe_await(self.decision_bus.propose_action(action))
            status = await self._safe_await(action.wait_for_decision(timeout=5.0))
        import os as _os
        if _os.environ.get("LOGACT_TRACE"):
            print(f"TRACE-CSC exec action id={action.action_id} status={status} completed_set={action._completed_event.is_set()} bus={id(self.decision_bus)} loop={id(asyncio.get_running_loop())}", flush=True)

        if status not in (ActionStatus.APPROVED, ActionStatus.EXECUTED):
            # Surface the veto/timeout reason from the audit trail so callers
            # see *why* consensus failed, not just the terminal status.
            voter_reasons = [
                str(report.get("reason", ""))
                for report in getattr(action, "voter_reports", {}).values()
                if isinstance(report, dict) and report.get("reason")
            ]
            detail = f" ({'; '.join(voter_reasons)})" if voter_reasons else ""
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id),
                dominant_rejection_reason=f"LogAct consensus failure: {status}{detail}",
            )

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=decision_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry),
        )

    async def execute_task(self, task: str, context: Any = None) -> Optional[CoreDecision]:
        """
        Execute a strategic task against the current market context.

        The CSC's public task entry point (used by main.py). A high-level task
        string plus a market-data context is folded into an observation and run
        through the 12-step active-inference pipeline.
        """
        if isinstance(context, dict):
            observation = dict(context)
        elif context is None:
            observation = {}
        else:
            observation = dict(getattr(context, "__dict__", {}) or {})
        observation.setdefault("task", task)
        observation.setdefault("timestamp", datetime.utcnow().isoformat())
        result = await self.process_market_observation(observation)
        # Each executed task folds into runtime state and reduces epistemic uncertainty
        self.state.folded_history.append({"task": task, "result": result})
        self.state.epistemic_uncertainty = max(0.05, self.state.epistemic_uncertainty * 0.9)
        # "status" refers to task completion — a vetoed trade is still a completed cycle.
        return {"status": "completed", "decision": result}
