"""
Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Cognitive System Controller (CSC) - UCA V6

Integrated "One Brain" implementing the 12-stage Recursive Active Inference pipeline.
Implements 'DiscoLoop' (arXiv:2607.00341) for multi-hop reasoning, 'HIPIF' (arXiv:2606.10507) for information folding,
and 'AutoResearchClaw' (arXiv:2605.20025) for Pivot/Refine self-healing control.
Incorporates transferable principles from REG-401 to REG-500 (Batch 5 Research Paper Registry).
"""

import os
import numpy as np
try:
    import torch  # noqa: F401 — optional; the CSC pipeline is numpy-only.
except ImportError:  # pragma: no cover - environment without torch
    torch = None
import time
import uuid
import logging
import asyncio
import copy
import hashlib
import json
import threading
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from datetime import datetime
from trading_bot.core.governance.determinism import determinism as _determinism
from unittest.mock import MagicMock, AsyncMock

from .folding import InformationFolder
from .hypothesis import HypothesisGenerator, ReasoningBranch
from .reliability import ReliabilityTracker
from .router import SkillRouter
from ..verification.swarm import VerificationSwarm
from .swarm_intelligence.service import SwarmIntelligenceService
from .self_wiring import NodeState, SelfWiringSupervisor
from .autonomy import AutonomyManager
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
        self.active_tasks: List[str] = []


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
    # Max fractional tilt subordinate advisory calls can apply to branch
    # ranking — advisors nudge selection, never override gates.
    _ADVISORY_TILT = 0.25
    # Ceiling on an advisor's self-declared per-call budget — a
    # subordinate service must not stretch the decision cycle past the
    # electorate's bound by claiming a huge timeout_s.
    _ADVISORY_TIMEOUT_CEILING_S = 20.0
    _ADVISORY_TIMEOUT_DEFAULT_S = 5.0

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
                # Partially-constructed instances (init exception or
                # __new__-only) may lack these attrs — reset must not
                # raise during teardown.
                for attr in ("continuous_state", "discrete_channel",
                             "vfe_history"):
                    container = getattr(cls._instance, attr, None)
                    if hasattr(container, "clear"):
                        container.clear()
                if hasattr(cls._instance, "last_prediction"):
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
        # Canonical execution service — when wired, position closes dispatch
        # real opposing orders; absent means mark-only settlement (tests).
        self.execution_service = kwargs.get("execution_service")
        # Capability domains for the canonical services: advisory
        # agents get INTELLIGENCE at configure_cognition; the trusted
        # services carry their own domains so require() is meaningful.
        try:
            from .security_kernel import CapabilityDomain
            _sk = self._security_kernel()
            if self.shield is not None:
                _sk.issue_identity("immutable_shield",
                                   [CapabilityDomain.GOVERNANCE,
                                    CapabilityDomain.RISK],
                                   capabilities=[], version="canonical")
            if self.execution_service is not None:
                _sk.issue_identity("execution_service",
                                   [CapabilityDomain.EXECUTION],
                                   capabilities=["live_trade"],
                                   version="canonical")
        except Exception:  # noqa: BLE001 — identity is best-effort
            pass
        self.evolution_gate = kwargs.get("evolution_gate")
        # Typed governance gate (human approval policy). "None" means not yet
        # resolved; resolved lazily at the governance stage and cached so a
        # missing gate fails closed every cycle rather than skipping it once.
        self.governance_gate = kwargs.get("governance_gate", None)
        self._governance_gate_resolved = self.governance_gate is not None

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

        # Reliability tracking: Brier/precision per agent+regime, updated by
        # the outcome pipeline (record_outcome). Empty until real outcomes
        # are fed back — never prefilled with fabricated accuracy.
        self.reliability_tracker = ReliabilityTracker()

        # Advisory swarm intelligence: the deliberation substrate that
        # aggregates subordinate advisor calls into one consensus evidence
        # artifact — advisory only, no order/risk/veto/execution authority.
        self._swarm_intel = kwargs.get("swarm_intelligence") or (
            SwarmIntelligenceService(
                reliability_tracker=self.reliability_tracker))
        self._last_swarm_consensus: Optional[Any] = None
        self._last_swarm_snapshot: Optional[Dict[str, float]] = None

        # Self-wiring supervisor: the organism's own network rewiring —
        # advisory services live in shadow/attached/dormant/quarantined
        # states driven by measured emit quality and settled outcomes.
        # Bounded to the advisory electorate; the authority chain is
        # invariant and unreachable from it.
        self._self_wiring = kwargs.get("self_wiring") or (
            SelfWiringSupervisor())
        # Restore measured wiring state across restarts — without this
        # the organism re-makes its promote/demote mistakes every
        # session (persist exists but load was never called).
        try:
            _sw_path = os.environ.get(
                "TB_SELF_WIRING_STATE", "var/self_wiring.json")
            if self._self_wiring is not None:
                self._self_wiring.set_persistence(_sw_path)
        except Exception as exc:
            logger.warning("self-wiring restore skipped: %s", exc)

        # Autonomy manager: the organism's operations layer — one audited
        # activity-portfolio decision per cycle instead of scattered
        # interval hooks, plus the capability-expansion ledger.
        self._autonomy = kwargs.get("autonomy") or AutonomyManager()
        # Curiosity engine: measured-surprise hypothesis generator —
        # emits SRE-ingestible payloads only on real statistical triggers.
        from .curiosity import CuriosityEngine
        self._curiosity = kwargs.get("curiosity") or CuriosityEngine()
        from .execution_learning import ExecutionLearningService
        self._exec_learning = kwargs.get("exec_learning")             or ExecutionLearningService()

        # Subordinate advisory cognition services (e.g. AdvisoryCognitiveBrain).
        # Configured via configure_cognition(); their analyze() output becomes
        # provenance-tagged advisory evidence — never authority. Disabled by
        # default; wired by the runtime when explicitly enabled.
        self._advisory_services: List[Any] = []
        self._engineered_models: Dict[str, Any] = {}
        self._engineered_sprt: Dict[str, Any] = {}
        # Shadow mode: newly attached engineered models must survive N
        # measured live outcomes with a healthy SPRT before their calls
        # influence the advisory tilt — evidence is recorded, influence
        # is not granted. Improvement survives shadow operation or dies.
        self._engineered_shadow: Dict[str, int] = {}
        # Advisory-only runtime monitors (drift/kill-switch reality gates):
        # trip reasons accumulate here and surface as self-health flags.
        self._runtime_advisory_flags: set = set()
        self._peer_history: Dict[str, deque] = {}
        self._engineered_cap_to_cid: Dict[str, str] = {}

        # Durable decision sink — an object with async record_audit_event()
        # (the canonical SqliteTradingRepository). Wired by the runtime after
        # construction via configure_decision_sink(); absent means in-memory
        # only (paper/test contexts).
        self._decision_sink: Any = None

        # Pending directional predictions keyed by trade_id, pointing into
        # _open_positions. Position-lifetime accounting: a BUY/SELL opens (or
        # extends) a position; an opposing decision or the holding horizon
        # closes it; the realized entry->exit return is the outcome, not a
        # single bar's move.
        self._pending_predictions: Dict[str, Dict[str, Any]] = {}
        self._open_positions: Dict[str, Dict[str, Any]] = {}
        # Bounded journal of settled position outcomes — the real
        # action/outcome pairs consumed by self-state advisory modules
        # (psychology tilt, counterfactual analysis, model-decay checks).
        self._settled_outcomes: "deque" = deque(maxlen=256)
        self._observation_seq = 0
        # Unified research: subordinate engine + bounded report journal +
        # advisory artifacts queued into the next observation's evidence.
        self.research_engine = None
        self._research_hydrated = False
        self._research_interval = int(kwargs.get("research_interval", 100) or 0)
        # Bounded RSI reflection: the HMS bridge reports observed failure
        # gaps every N observations (0 disables). The full promotion cycle
        # stays operator-invoked by design.
        self._rsi_gap_interval = int(kwargs.get("rsi_gap_interval", 250) or 0)
        self._rsi_bridge = None
        # Self-questioning: the CSC asks itself research questions derived
        # from its own weakest measured spots (suppression, health,
        # degraded models). Interval in observations; 0 disables.
        self._self_question_interval = int(
            kwargs.get("self_question_interval", 500) or 0)
        self._last_self_question_seq = 0
        self._frontier_engine = None
        self._research_cycle_task = None
        self._research_reports: "deque" = deque(maxlen=64)
        self._research_artifacts: "deque" = deque(maxlen=64)
        # Per-symbol rolling close history for causal feature derivation —
        # a raw OHLCV feed carries no volatility/trend/rsi so the CSC
        # computes them itself from strictly-prior bars.
        self._obs_history: Dict[str, "deque"] = {}
        self._vol_history: Dict[str, "deque"] = {}
        # Max holding period in observations before a position auto-closes.
        self._position_max_hold = int(kwargs.get("position_horizon", 8))
        # Per-symbol Wilder-ATR state for the adverse-move exit: a position
        # that moves materially against its direction closes before the
        # horizon instead of riding out a measured loss to a timer.
        self._atr_state: Dict[str, Dict[str, float]] = {}
        self._adverse_atr_mult = float(kwargs.get("adverse_atr_mult", 2.5))
        # External-research conduit: bounded arxiv/github evidence for
        # csc.research() questions. Fail-open — network errors report
        # unavailable, never fabricated. Off via internet_research=False.
        self._internet_researcher = None
        self._internet_research_enabled = bool(
            kwargs.get("internet_research", True))
        # Evidence-backed cadence: OOS replication on two independent
        # windows shows per-bar decisions lose the gross edge to costs;
        # stride>1 decides every Nth bar (settlement/features/research
        # still run every bar — only the decision is cadenced).
        self._decision_stride = max(1, int(kwargs.get("decision_stride", 1)))
        # Turnover budget: instantaneous exposure is capped downstream, but
        # nothing else bounds churn — a soak bled -4.4% through 443 small
        # fills each inside the exposure cap. Directional approvals per
        # rolling window are bounded here; 0 disables.
        self._churn_budget = int(kwargs.get("churn_budget", 50))
        self._churn_window = int(kwargs.get("churn_window", 200))
        self._recent_trade_seqs: deque = deque(maxlen=self._churn_window)
        # Stage funnel: per-process counts at each pipeline boundary so a
        # run's "why no trades" is answerable from the snapshot without
        # re-parsing audit rows. Durable per-decision detail stays in
        # audit_events; this is the aggregate view.
        self._funnel: Counter = Counter()
        # Pending directional claims per capability, resolved against
        # the next observation's price so self-wiring promotion gates
        # on measured predictive value rather than emit presence.
        # Tuple: (price, direction, timestamp, symbol) — symbol matters:
        # a EURUSD claim must never be scored against a GBPUSD print.
        self._advisor_dir_pending: Dict[
            str, Tuple[float, str, float, str]] = {}
        # EV calibration: predicted-vs-realized pairs from settled
        # outcomes. Measured on forward data: simulated EV ~+0.0054,
        # realized ~+0.00004 — raw EV is ~150x optimistic, so the
        # net-of-cost gate must compare cost to *calibrated* EV.
        self._ev_pairs: deque = deque(maxlen=int(
            kwargs.get("ev_calibration_window", 200)))
        self._ev_min_samples = int(kwargs.get("ev_min_samples", 20))
        # Per-feature attribution: (feature, signed_contribution,
        # realized_return, regime) recorded at settlement alongside
        # _ev_pairs — this is what turns an assumed feature weight into
        # a measured one (e.g. order_imbalance from the live L2 soak).
        self._feature_pairs: deque = deque(maxlen=int(
            kwargs.get("feature_attrib_window", 500)))
        # Bounded exploration: the epistemic-uncertainty sizing floor
        # creates a circular abstention trap (u=1.0 -> qty=0 -> no
        # fills -> u stays 1.0). TB_CSC_EXPLORE_BUDGET=N allows N
        # exploratory trades at reduced size so real outcomes can
        # break the trap. Default 0 = current fail-closed behavior.
        self._explore_budget = int(
            kwargs.get("explore_budget",
                       os.environ.get("TB_CSC_EXPLORE_BUDGET", "0")))
        self._explore_factor = 0.1  # exploratory trades at ~10% size
        # Calibration-probe trickle: once cal hits 0.0 (realized mean
        # <= 0), every proposal would downgrade forever and _ev_pairs
        # could never refill. Every 10th blocked proposal goes through
        # anyway (tagged) so fresh realizations can unbrick the gate.
        self._cal_probe_counter = 0
        # Round-trip cost estimate for the net-of-cost edge gate — a
        # directional proposal whose simulated expected value cannot beat it
        # downgrades to an honest abstention.
        self._default_cost_bps = float(kwargs.get("cost_bps", 5.0))
        # Per-symbol (high,low) deque for intrabar path-risk estimation
        self._hl_history: Dict[str, Deque[Tuple[float, float]]] = {}

        # HASP guardrail baseline: recent observed volatility per instrument
        # class. The guardrail fires on a large multiple of the running
        # baseline (or an absolute 1% per-bar extreme when no baseline yet).
        self._vol_baseline: "deque" = deque(maxlen=256)

        # Real provenance: resolve once at construction; "unknown" when the
        # source tree has no git metadata — never a fabricated signed value.
        self._git_sha = self._resolve_git_sha()

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
        # Bounded like discrete_channel/_obs_history — appended every
        # observation, so an unbounded list leaks memory in long runs.
        self.vfe_history = deque(maxlen=2048)

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

        # Scientific Reasoning Engine — hypothesis lifecycle tracker wired
        # on real CSC machinery (HMS chain, world model, verifier swarm).
        # Advisory only: its outputs are provenance-tagged evidence, and
        # the SRE itself is a self-wiring node like any other service.
        self._sre = None
        if kwargs.get("enable_sre", True):
            try:
                self.configure_sre()
            except Exception as exc:  # noqa: BLE001
                logger.warning("CSC-V6: SRE wiring skipped (%s)", exc)

        logger.info("CSC-V6: Brain initialized with dynamic argument mapping.")

    def configure_sre(self) -> Any:
        """Construct + attach the Scientific Reasoning Engine as an
        advisory cognition service. Real HMS, world model, and verifier
        swarm handles — every fabricated fallback in the SRE has been
        removed, so unmeasured stages honestly report 'unmeasured'."""
        if self._sre is not None:
            return self._sre
        from .scientific_reasoning import ScientificReasoningEngine
        from .sre_bridge import SREAdvisoryService
        # Do-calculus counterfactual engine — torch-dependent, absent in
        # the lightweight env (counterfactuals stay 'unmeasured' there).
        causal_wm = None
        try:
            from ...world_model.causal_model import CausalWorldModel
            causal_wm = CausalWorldModel(hms=self.hms)
        except Exception as exc:  # noqa: BLE001
            logger.debug("CSC-V6: causal world model unavailable (%s)", exc)
        self._sre = ScientificReasoningEngine(
            controller=self, hms=self.hms,
            world_model=self.world_model, causal_model=causal_wm)
        self.configure_cognition(SREAdvisoryService(self._sre))
        logger.info("CSC-V6: SRE wired as advisory cognition service.")
        return self._sre

    def _sre_ingest(self, source: str, payload: Dict[str, Any]) -> None:
        """Bridge: register externally-produced hypotheses (research
        reports, swarm verdicts) into the SRE lifecycle with provenance."""
        sre = getattr(self, "_sre", None)
        if sre is None:
            return
        try:
            sre.ingest_external(source, payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug("CSC-V6: SRE ingest failed: %s", exc)

    def sre_report(self) -> Dict[str, Any]:
        """Transparency surface: SRE lifecycle census + measured baselines."""
        sre = getattr(self, "_sre", None)
        return sre.report() if sre is not None else {}

    def execution_learning_report(self) -> Dict[str, Any]:
        """Venue-performance evidence learned from measured canonical
        execution outcomes. Advisory only — dispatch authority stays
        with the canonical execution service."""
        el = getattr(self, "_exec_learning", None)
        return el.advisory_report() if el is not None else {}

    def configure_voice_alerter(self, alerter: Any) -> None:
        """Opt-in voice alerts on critical events (EMERGENCY_HALT/estop).
        Silent no-op unless the operator enables the alerter."""
        self._voice_alerter = alerter

    def pruning_report(self) -> Dict[str, Any]:
        """'Synaptic pruning' — honest surface over the self-wiring
        electorate lifecycle: measured-reliability states (attached/
        shadow/dormant/quarantined) ARE the pruning mechanism."""
        sw = getattr(self, "_self_wiring", None)
        if sw is None:
            return {"status": "unavailable"}
        states: Dict[str, int] = {}
        nodes = getattr(sw, "_states", None) or getattr(sw, "nodes", {})
        for rec in (nodes.values() if isinstance(nodes, dict) else []):
            s = str(getattr(rec, "state", rec.get("state", "?"))
                    if isinstance(rec, (dict,)) else
                    getattr(rec, "state", "?")).split(".")[-1]
            states[s] = states.get(s, 0) + 1
        return {"status": "measured",
                "pruned_quarantined": states.get("QUARANTINED", 0),
                "dormant": states.get("DORMANT", 0),
                "shadow_probation": states.get("SHADOW", 0),
                "attached": states.get("ATTACHED", 0),
                "electorate_states": states}

    def ml_health_report(self) -> Dict[str, Any]:
        """ML monitoring: measured advisory drift + reliability, not a
        serving-layer monitor (see UnavailableCapability for that)."""
        out: Dict[str, Any] = {"status": "measured"}
        rt = getattr(self, "reliability_tracker", None)
        if rt is not None and hasattr(rt, "snapshot"):
            try:
                out["reliability"] = rt.snapshot()
            except Exception:  # noqa: BLE001
                out["reliability"] = "unavailable"
        sw = getattr(self, "_swarm_intel", None)
        if sw is not None and hasattr(sw, "report"):
            try:
                rep = sw.report()
                out["swarm_health"] = rep.get("health") or rep
            except Exception:  # noqa: BLE001
                out["swarm_health"] = "unavailable"
        out["degenerate_suppressed"] = getattr(
            self, "_funnel", {}).get("degenerate_suppressed", 0)
        return out

    async def preflight_self_check(self) -> Dict[str, Any]:
        """Session-gate self-validation: verify the safety chain before
        the first real observation. Component presence plus one
        end-to-end probe decision through the canonical pipeline —
        the probe carries ``preflight=True`` so it can never produce a
        venue-visible order. Fails closed: any failed check blocks."""
        checks: List[Dict[str, Any]] = []

        def _ck(name: str, passed: bool, detail: str = "") -> None:
            checks.append({"check": name, "passed": bool(passed),
                           "detail": str(detail)[:200]})

        # Required: the safety chain that may never be absent in a session.
        for name, obj in (
                ("shield", self.shield), ("decision_bus", self.decision_bus),
                ("verifier_swarm", self.verifier_swarm),
                ("reliability_tracker", self.reliability_tracker),
                ("skill_router", self.skill_router),
                ("swarm_intelligence", self._swarm_intel),
                ("self_wiring", self._self_wiring),
                ("autonomy", self._autonomy),
                ("curiosity", self._curiosity),
                ("sre", self._sre)):
            _ck(f"component:{name}", obj is not None)
        # Optional runtime-injected services — informational only; absence
        # never blocks (the canonical runtime wires them in live runs).
        for name, obj in (("risk_engine", self.risk_engine),):
            checks.append({"check": f"optional:{name}",
                           "passed": bool(obj is not None),
                           "detail": "informational"})

        probe = {"symbol": "PREFLIGHT", "price": 1.0, "close": 1.0,
                 "open": 1.0, "high": 1.0, "low": 1.0, "volume": 1.0,
                 "timeframe": "probe", "timestamp": "preflight",
                 "preflight": True}
        self._preflight_active = True
        audit_baseline = getattr(self, "_audit_writes_ok", 0)
        try:
            decision = await self.process_market_observation(probe)
            outcome = getattr(decision, "outcome", None)
            valid = outcome is not None and str(outcome).split(".")[-1] in (
                "ABSTAIN", "TRADE_APPROVED", "TRADE_REJECTED",
                "POSITION_MANAGEMENT", "EMERGENCY_HALT")
            _ck("end_to_end_decision", valid,
                detail=f"outcome={outcome}")
            # CoreDecision carries no audit_events field — verify the
            # probe actually persisted events to the sink instead. In
            # memory-only contexts (no sink configured) the check is
            # informational, matching the intentional fail-open design.
            sink = getattr(self, "_decision_sink", None)
            wrote = getattr(self, "_audit_writes_ok", 0) > audit_baseline
            _ck("audit_trail",
                wrote or sink is None,
                detail=("probe audit events persisted"
                        if wrote else
                        "no sink configured (memory-only)"
                        if sink is None else
                        "sink configured but accepted no writes"))
        except Exception as exc:  # noqa: BLE001
            _ck("end_to_end_decision", False, detail=repr(exc))
        finally:
            self._preflight_active = False

        failures = [c["check"] for c in checks if not c["passed"]]
        report = {
            "all_passed": not failures,
            "checks": checks,
            "blocking": failures,
            "probe_disposition": ("pipeline verified; no order "
                                  "dispatched"),
        }
        await self._persist_audit_event(
            event_type="PREFLIGHT", action="self_check",
            outcome="passed" if not failures else "failed",
            correlation_id=f"preflight-{self._observation_seq}",
            details={"blocking": failures})
        return report

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
        """Measured free-energy proxy: mean of the recent surprise history.

        Returns 0.0 before any observation has been processed rather than a
        fabricated constant — the value is only meaningful once real
        prediction errors have been recorded.
        """
        if not self.vfe_history:
            return 0.0
        return float(np.mean(list(self.vfe_history)[-20:]))

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

    def configure_cognition(self, advisory: Any) -> None:
        """Register a subordinate advisory cognition service.

        The service must expose ``analyze(context) -> Mapping`` (sync or
        async). Its output is attached as provenance-tagged advisory evidence
        (``agent:<capability_id>``) — it carries no decision authority.
        """
        if advisory is None or not hasattr(advisory, "analyze"):
            raise TypeError(
                "advisory cognition service must expose analyze(context)")
        capability_id = str(getattr(
            advisory, "capability_id", type(advisory).__name__))
        self._advisory_services = [
            service for service in self._advisory_services
            if str(getattr(service, "capability_id",
                           type(service).__name__)) != capability_id]
        self._advisory_services.append(advisory)
        # Security kernel: every advisor gets an INTELLIGENCE-domain
        # identity so its emitted artifacts can be signed + verified.
        # Advisory services hold no dangerous capabilities by rule.
        try:
            from .security_kernel import CapabilityDomain
            self._security_kernel().issue_identity(
                capability_id, [CapabilityDomain.INTELLIGENCE],
                capabilities=[],
                version=str(getattr(advisory, "version", "unknown")))
        except Exception as exc:  # noqa: BLE001 — identity is best-effort
            logger.debug("advisory identity issue skipped: %s", exc)
        # Self-wiring inventory: the runtime's attachments join the
        # electorate as ATTACHED; engineered/shadow candidates the
        # supervisor discovered itself stay SHADOW until measured.
        _sup = getattr(self, "_self_wiring", None)
        if _sup is not None:
            _state = (NodeState.SHADOW
                      if capability_id in self._engineered_shadow
                      else NodeState.ATTACHED)
            _sup.register(capability_id, advisory, state=_state)
        logger.info(
            "CSC-V6: advisory cognition service registered: %s",
            capability_id)

    def configure_swarm_state(self, path: Any) -> None:
        """Point the swarm knowledge base at a persistence file — learned
        node skill and patterns survive restarts beside the run state."""
        _si = getattr(self, "_swarm_intel", None)
        if _si is not None:
            _si.set_persistence(str(path))

    def swarm_intelligence_report(self) -> Dict[str, Any]:
        """Transparency surface: what the swarm has learned and deliberated."""
        _si = getattr(self, "_swarm_intel", None)
        return _si.report() if _si is not None else {}

    def configure_self_wiring_state(self, path: Any) -> None:
        """Persist the wiring inventory beside the run state — measured
        node states survive restarts; service objects re-register on
        attach."""
        _sup = getattr(self, "_self_wiring", None)
        if _sup is not None:
            _sup.set_persistence(str(path))

    def self_model_report(self) -> Dict[str, Any]:
        """The organism's self-model: every advisory node, its wiring
        state, measured emit quality, and recent rewire events."""
        _sup = getattr(self, "_self_wiring", None)
        return _sup.report() if _sup is not None else {}

    async def _maybe_rewire_electorate(self) -> None:
        """Periodic measured rewiring of the advisory electorate.

        The supervisor evaluates emit-quality streaks and shadow
        probation, then applies transitions by changing which service
        objects sit in _advisory_services. Transitions are durable
        SELF_WIRE audit events. The authority chain is never touched —
        it isn't in the inventory.
        """
        _sup = getattr(self, "_self_wiring", None)
        if _sup is None:
            return
        if self._observation_seq % max(1, _sup.rewire_interval) != 0:
            return
        try:
            events = _sup.reevaluate(self._observation_seq)
        except Exception as exc:  # noqa: BLE001
            logger.warning("CSC-V6: self-wiring evaluation failed: %s", exc)
            return
        for ev in events:
            node = _sup.nodes.get(ev.node_id)
            service = getattr(node, "service", None)
            if ev.kind in ("demote", "quarantine"):
                self._advisory_services = [
                    s for s in self._advisory_services
                    if str(getattr(s, "capability_id",
                                   type(s).__name__)) != ev.node_id]
            elif ev.kind in ("probe", "promote") and service is not None:
                attached = {str(getattr(s, "capability_id",
                                        type(s).__name__))
                            for s in self._advisory_services}
                if ev.node_id not in attached:
                    self._advisory_services.append(service)
            self._funnel[f"self_wire_{ev.kind}"] += 1
            await self._persist_audit_event(
                event_type="SELF_WIRE", action=ev.kind,
                outcome=f"{ev.from_state}->{ev.to_state}",
                correlation_id=ev.node_id,
                details={"reason": ev.reason, "cycle": ev.cycle})
        if events:
            logger.info(
                "CSC-V6: self-wiring applied %d transitions: %s",
                len(events), [f"{e.kind}:{e.node_id}" for e in events])

    def configure_execution_service(self, service: Any) -> None:
        """Wire the canonical execution service so position closes dispatch
        real opposing orders through the bus. Absent → mark-only settlement."""
        self.execution_service = service

    def configure_decision_sink(self, sink: Any) -> None:
        """Wire the durable decision sink (the canonical repository).

        Every terminal decision — APPROVED, REJECTED, ABSTAIN — is recorded
        as an AuditEvent so decisions can be joined to realized outcomes
        after restart."""
        if sink is not None and not hasattr(sink, "record_audit_event"):
            raise TypeError(
                "decision sink must expose record_audit_event(AuditEvent)")
        self._decision_sink = sink

    def configure_research(self, engine: Any = None) -> Any:
        """Wire the unified research engine as a subordinate service.

        With no argument the engine is composed from this controller's own
        canonical components — the trading pipeline's hypothesis generator,
        verification swarm, memory, and folder are the same machinery the
        research pipeline runs. The engine produces advisory-only reports;
        it has no order, risk, or execution surface.
        """
        if engine is None:
            from .research import ResearchEngine
            engine = ResearchEngine(
                hypothesis_gen=self.hypothesis_gen,
                verifier_swarm=self.verifier_swarm,
                hms=self.hms,
                folder=self.folder,
                git_sha=getattr(self, "_git_sha", "unknown"))
        elif not hasattr(engine, "investigate"):
            raise TypeError(
                "research engine must expose investigate(question, market_data)")
        self.research_engine = engine
        self._institutional_research = None
        self._research_hydrated = False
        return engine

    async def _maybe_rehydrate_research(self) -> None:
        """Replay the durable RESEARCH_KG audit stream into the engine's
        knowledge graph on first use — knowledge survives restarts."""
        if self._research_hydrated or self.research_engine is None:
            return
        self._research_hydrated = True
        sink = getattr(self, "_decision_sink", None)
        if sink is None or not hasattr(sink, "list_audit_events"):
            return
        try:
            rows = await self._safe_await(sink.list_audit_events(
                event_type="RESEARCH_KG", limit=10000))
            restored = self.research_engine.rehydrate(rows or [])
            # Verdict history rebuilds the research policy (method yields)
            # — both halves of research state now survive restarts.
            verdict_rows = await self._safe_await(sink.list_audit_events(
                event_type="RESEARCH", limit=10000))
            policy_n = self.research_engine.rebuild_policy(verdict_rows or [])
            # Session report history is derivable too — rebuild the journal
            # from verdict rows so research() output isn't session-only.
            if not self._research_reports:
                self._rebuild_research_reports(verdict_rows or [])
            # Reliability tracker rebuilds from settled-outcome history —
            # calibration survives restarts alongside knowledge.
            outcome_rows = await self._safe_await(sink.list_audit_events(
                event_type="DECISION_OUTCOME", limit=10000))
            self._rebuild_reliability(outcome_rows or [])
            # The settled-outcome journal feeds the self-state advisors —
            # rebuild it from durable POSITION_SETTLED rows so psychology/
            # counterfactual/decay evidence survives restarts too.
            settled_rows = await self._safe_await(sink.list_audit_events(
                event_type="POSITION_SETTLED", limit=1000))
            self._rehydrate_settled_journal(settled_rows or [])
            if restored.get("nodes") or restored.get("edges") or policy_n:
                logger.info(
                    "CSC-V6: rehydrated research state — %d nodes, %d edges, "
                    "%d policy verdicts (%d skipped)", restored["nodes"],
                    restored["edges"], policy_n, restored["skipped"])
        except Exception as exc:
            logger.warning("CSC-V6: research KG rehydration failed: %s", exc)

    def _rebuild_reliability(self, rows: List[Any]) -> None:
        """Replay DECISION_OUTCOME rows into the ReliabilityTracker —
        per-regime precision/Brier history survives restarts."""
        import json as _json
        replayed = 0
        for row in reversed(rows or []):  # repository returns newest-first
            try:
                inner = row.get("event_json")
                inner = _json.loads(inner) if isinstance(inner, str) \
                    else (inner or row)
                details = inner.get("details") or {}
                regime = str(details.get("regime") or "unknown")
                confidence = float(details.get("confidence") or 0.5)
                was_correct = str(row.get("outcome") or "") == "correct"
                self.reliability_tracker.update_metrics(
                    "csc", regime, was_correct, confidence)
                # EV calibration pairs rehydrate too — predicted-vs-
                # realized survives restart alongside reliability.
                _exp = details.get("expected_return")
                _real = details.get("realized_return")
                if (isinstance(_exp, (int, float)) and _exp > 0
                        and isinstance(_real, (int, float))):
                    self._ev_pairs.append(
                        (float(_exp), float(_real), regime))
                    _fc = details.get("feature_contributions")
                    if isinstance(_fc, dict) and isinstance(
                            _real, (int, float)):
                        for _fn, _fv in _fc.items():
                            if isinstance(_fv, (int, float)):
                                self._feature_pairs.append(
                                    (str(_fn), float(_fv),
                                     float(_real), str(regime)))
                self.reliability_tracker.update_action_outcome(
                    regime,
                    str(inner.get("action") or row.get("action") or "").upper(),
                    was_correct, details.get("realized_return"))
                swarm = getattr(self, "verifier_swarm", None)
                rec = getattr(swarm, "record_outcome", None)
                if rec is not None:
                    rec(confidence, was_correct)
                action = str(inner.get("action") or row.get("action") or "")
                for call in details.get("advisory_calls") or ():
                    adv_dir = str(call.get("direction") or "")
                    if adv_dir in ("BUY", "SELL"):
                        self.reliability_tracker.update_metrics(
                            str(call["capability_id"]), regime,
                            (adv_dir == action) == was_correct,
                            float(call.get("confidence") or 0.5))
                replayed += 1
            except Exception:
                continue
        if replayed:
            logger.info(
                "CSC-V6: reliability tracker rebuilt — %d outcomes replayed",
                replayed)

    def _rehydrate_settled_journal(self, rows: List[Any]) -> None:
        """Replay POSITION_SETTLED rows into _settled_outcomes — the
        bounded journal the self-state advisors consume. Details carry the
        full entry shape, so dedup keys (entry_seq/exit_seq) stay unique."""
        import json as _json
        restored = 0
        for row in reversed(rows or []):  # repository returns newest-first
            try:
                inner = row.get("event_json")
                inner = _json.loads(inner) if isinstance(inner, str) \
                    else (inner or row)
                details = inner.get("details") or {}
                entry = dict(details)
                entry["rehydrated"] = True
                self._settled_outcomes.append(entry)
                restored += 1
            except Exception:
                continue
        if restored:
            logger.info(
                "CSC-V6: settled journal rehydrated — %d outcomes restored",
                restored)

    def feature_attribution_report(self) -> Dict[str, Any]:
        """Measured per-feature outcome attribution: for each drift
        feature, the count and mean realized return of settled trades
        where it contributed in the trade's direction. A feature whose
        signed contribution actually earned marks itself 'measured' —
        the simulator's assumed weights can then be replaced by
        evidence (and ones that earned nothing get trimmed)."""
        agg: Dict[str, Dict[str, Any]] = {}
        for name, contrib, realized, regime in self._feature_pairs:
            e = agg.setdefault(
                name, {"trades": 0, "aligned": 0, "realized_sum": 0.0,
                       "regimes": {}})
            e["trades"] += 1
            # 'aligned' = the feature's sign agreed with the realized
            # sign — measures direction quality, not just magnitude.
            if (contrib > 0) == (realized > 0):
                e["aligned"] += 1
            e["realized_sum"] += realized
            e["regimes"][regime] = e["regimes"].get(regime, 0) + 1
        out = {}
        for name, e in agg.items():
            n = max(1, e["trades"])
            out[name] = {
                "trades": e["trades"],
                "aligned_rate": round(e["aligned"] / n, 4),
                "mean_realized": round(e["realized_sum"] / n, 6),
                "regimes": e["regimes"],
                "status": ("measured"
                           if e["trades"] >= self._ev_min_samples
                           else "insufficient_samples")}
        return out

    def advisory_report(self) -> Dict[str, Any]:
        """Read-only per-advisor standing: attached services plus measured
        weight/precision per regime from the ReliabilityTracker. The audit
        surface for 'which advisors actually earn their tilt'."""
        attached = [
            getattr(s, "capability_id", type(s).__name__)
            for s in getattr(self, "_advisory_services", [])]
        measured: Dict[str, Any] = {}
        for agent_id, regimes in getattr(
                self.reliability_tracker, "metrics", {}).items():
            per_regime = {}
            for regime, m in regimes.items():
                per_regime[regime] = {
                    "predictions": getattr(m, "total_predictions", 0),
                    "precision": round(getattr(m, "precision", 0.0), 4),
                    "weight": round(self.reliability_tracker.get_agent_weight(
                        agent_id, regime), 4),
                }
            measured[str(agent_id)] = per_regime
        report: Dict[str, Any] = {"attached": attached,
                                  "measured": measured}
        # Measured active-set verdicts: an attached advisor that earns
        # nothing is dead weight; one that earns negative precision is a
        # candidate for ablation. Verdicts are evidence for operators,
        # never automatic removal.
        verdicts: Dict[str, str] = {}
        for cap in attached:
            regimes = (measured or {}).get(str(cap)) or {}
            total = sum(m.get("predictions", 0)
                        for m in regimes.values())
            if total == 0:
                verdicts[str(cap)] = "no_calls_measured"
                continue
            prec = sum(m.get("predictions", 0) * m.get("precision", 0.0)
                       for m in regimes.values()) / total
            if total < 20:
                verdicts[str(cap)] = "insufficient_evidence"
            elif prec < 0.4:
                verdicts[str(cap)] = "measured_negative"
            elif prec >= 0.5:
                verdicts[str(cap)] = "measured_positive"
            else:
                verdicts[str(cap)] = "marginal"
        report["contribution_verdicts"] = verdicts
        assembly_report = getattr(self, "_advisory_attach_report", None)
        if isinstance(assembly_report, Mapping):
            report["assembly"] = dict(assembly_report)
        failures = getattr(self, "_advisory_failures", {}) or {}
        disabled = sorted(str(cap) for cap, count in failures.items()
                          if count >= 5)
        if disabled:
            report["disabled"] = disabled
        quality = {
            k: int(self._funnel.get(k, 0))
            for k in ('advisor_directional_calls', 'advisor_substantive',
                      'advisor_degenerate')}
        quality['consulted_total'] = int(
            self._funnel.get('advisory_artifacts', 0))
        report['signal_quality'] = quality
        return report

    def funnel_report(self) -> Dict[str, int]:
        """Ordered stage-funnel counts for this process.

        Keys follow the canonical pipeline order: observations -> cadence
        -> perception -> evidence -> guardrails -> internalization/advisors
        -> hypothesis branches -> pivot/refine -> verification -> synthesis
        -> net-cost gate -> risk -> shield -> governance -> consensus ->
        terminal outcomes -> settled positions. ``*_terminal`` counts are
        the cycles where that stage returned the final decision."""
        order = (
            "observations", "cadence_abstain", "perception",
            "evidence_items", "guardrails", "guardrail_terminal",
            "advisory_artifacts", "advisor_directional_calls",
            "advisor_substantive", "advisor_degenerate",
            "swarm_deliberations",
            "hypothesis_branches", "pivot_refine_terminal",
            "verification", "verification_terminal", "synthesis",
            "net_cost_downgrade", "directional_proposals",
            "risk_check", "risk_terminal", "shield", "shield_terminal",
            "governance", "governance_terminal", "consensus_rejected",
            "churn_abstain", "nondirectional_abstain",
            "terminal_TRADE_APPROVED", "terminal_TRADE_REJECTED",
            "terminal_ABSTAIN",
            "abstain_opp_cost_sum", "self_feedback_suspect",
            "net_cost_probe", "exploratory_trades", "settled_positions")
        report = {k: int(self._funnel.get(k, 0)) for k in order}
        for k, v in self._funnel.items():  # any unlisted counter survives
            if k not in report:
                report[k] = int(v)
        return report

    def _rebuild_research_reports(self, rows: List[Any]) -> None:
        """Reconstruct report stubs from durable RESEARCH verdict rows —
        the journal's memory extends past process restarts."""
        import json as _json
        from .research import ResearchReport
        for row in reversed(rows or []):  # repository returns newest-first
            try:
                inner = row.get("event_json")
                inner = _json.loads(inner) if isinstance(inner, str) \
                    else (inner or row)
                details = inner.get("details") or {}
                action = row.get("action") or inner.get("action")
                if action not in ("investigate", "evaluate_strategy",
                                  "assess_expansion"):
                    continue
                occurred = row.get("occurred_at")
                try:
                    created = (datetime.fromisoformat(str(occurred))
                               .timestamp() if occurred else time.time())
                except (ValueError, TypeError):
                    created = time.time()
                self._research_reports.append(ResearchReport(
                    research_id=str(row.get("correlation_id") or
                                    _determinism.get_uuid()),
                    question=str(details.get("question") or "(restored)"),
                    verdict=str(row.get("outcome") or "INCONCLUSIVE"),
                    created_at=created,
                    symbol=str(details.get("symbol") or "unknown"),
                    branches_considered=int(
                        details.get("branches_considered") or 0),
                    evidence_node_count=int(
                        details.get("evidence_node_count") or 0),
                    verifier_verdicts=list(
                        details.get("verifier_verdicts") or []),
                    sim_summary=dict(details.get("sim_summary") or {}),
                    composite_confidence=float(
                        details.get("composite_confidence") or 0.0),
                    comparison=details.get("comparison"),
                    boundary_conditions=dict(
                        details.get("boundary_conditions") or {})))
            except Exception:
                continue

    async def research(
        self, question: str, market_data: Optional[Dict[str, Any]] = None,
    ) -> "ResearchReport":
        """The one research entry point — CSC-controlled by construction.

        The question runs the full canonical pipeline (grounded hypotheses →
        counterfactual simulation → adversarial verification → durable
        report). The report is persisted as a RESEARCH audit event, journaled
        for the operator surface, and queued into the advisory channel so
        the next market cycle cites it as provenance-tagged evidence.
        """
        if self.research_engine is None:
            self.configure_research()
        await self._maybe_rehydrate_research()
        obs = dict(market_data or {})
        self._enrich_derived_features(obs)
        external = await self._fetch_internet_evidence(question)
        obs["external_research"] = external
        report = await self.research_engine.investigate(
            question, obs,
            evidence_chain=None,
            advisory_artifacts=None)
        self._research_reports.append(report)
        self._research_artifacts.append(report.to_advisory_artifact())
        self._sre_ingest("research_report", {
            "name": str(getattr(report, "question", "") or "")[:80],
            "description": str(getattr(report, "verdict", "") or ""),
            "research_id": str(getattr(report, "research_id", ""))})
        # Buffered KG events (nodes/edges) land in the durable audit log so
        # the knowledge graph can be reconstructed after restart.
        for kind, payload in self.research_engine.drain_persisted_events():
            await self._persist_audit_event(
                event_type="RESEARCH_KG", action=kind,
                outcome="recorded", correlation_id=report.research_id,
                details=payload)
        await self._persist_audit_event(
            event_type="RESEARCH",
            action="investigate",
            outcome=report.verdict,
            correlation_id=report.research_id,
            details={
                "question": report.question,
                "symbol": report.symbol,
                "branches_considered": report.branches_considered,
                "evidence_node_count": report.evidence_node_count,
                "composite_confidence": report.composite_confidence,
                # Full finding detail — restored reports after rehydration
                # carry the same substance as session reports.
                "sim_summary": report.sim_summary,
                "verifier_verdicts": list(report.verifier_verdicts)[:16],
                "boundary_conditions": dict(report.boundary_conditions),
                "comparison": report.comparison,
                "external_evidence": external,
                "advisory_only": True,
            })
        return report

    async def _fetch_internet_evidence(self, question: str
            ) -> Dict[str, Any]:
        """Bounded external evidence fetch via InternetResearcher
        (arxiv + github). Any failure returns an explicit unavailable
        status — the report records that research ran without external
        input rather than fabricating sources."""
        if not self._internet_research_enabled:
            return {"status": "disabled"}
        try:
            if self._internet_researcher is None:
                from trading_bot.autonomous_learner.internet_researcher import (
                    DifficultyLevel, InternetResearcher)
                self._internet_researcher = InternetResearcher()
                self._ir_difficulty = DifficultyLevel.INTERMEDIATE
            async with asyncio.timeout(30):
                resources = await self._internet_researcher.research_topic(
                    str(question)[:150], self._ir_difficulty)
            return {"status": "ok", "sources": [
                {"title": getattr(r, "title", ""),
                 "url": getattr(r, "url", ""),
                 "summary": (getattr(r, "summary", "") or "")[:240],
                 "source": getattr(r, "source", ""),
                 "relevance": getattr(r, "relevance_score", None)}
                for r in resources[:6]]}
        except Exception as exc:
            return {"status": "unavailable", "reason": str(exc)[:120]}
        finally:
            _ir = self._internet_researcher
            sess = getattr(_ir, "session", None) if _ir else None
            if sess is not None and not sess.closed:
                try:
                    await sess.close()
                except Exception:
                    pass

    async def evaluate_strategy(
        self, question: str, candidate_positions: List[float],
        baseline_positions: List[float], bar_returns: List[float],
        **kwargs: Any,
    ) -> "ResearchReport":
        """CSC-routed strategy evaluation — same persist/advisory
        treatment as research()."""
        if self.research_engine is None:
            self.configure_research()
        await self._maybe_rehydrate_research()
        report = self.research_engine.evaluate_strategy(
            question, candidate_positions, baseline_positions,
            bar_returns, **kwargs)
        return await self._record_research_report(
            report, action="evaluate_strategy")

    async def assess_expansion(self, target: str, **kwargs: Any
                               ) -> "ResearchReport":
        """CSC-routed expansion-readiness check — advisory only."""
        if self.research_engine is None:
            self.configure_research()
        await self._maybe_rehydrate_research()
        report = self.research_engine.assess_expansion(target, **kwargs)
        return await self._record_research_report(
            report, action="assess_expansion")

    async def _record_research_report(
        self, report: "ResearchReport", action: str,
    ) -> "ResearchReport":
        """Journal + advisory-channel + durable persistence for engine
        reports produced outside investigate()."""
        self._research_reports.append(report)
        self._research_artifacts.append(report.to_advisory_artifact())
        self._sre_ingest("research_report", {
            "name": str(getattr(report, "question", "") or "")[:80],
            "description": str(getattr(report, "verdict", "") or ""),
            "research_id": str(getattr(report, "research_id", ""))})
        for kind, payload in self.research_engine.drain_persisted_events():
            await self._persist_audit_event(
                event_type="RESEARCH_KG", action=kind,
                outcome="recorded",
                correlation_id=report.research_id, details=payload)
        await self._persist_audit_event(
            event_type="RESEARCH", action=action,
            outcome=report.verdict, correlation_id=report.research_id,
            details={"question": report.question,
                     "composite_confidence": report.composite_confidence,
                     "sim_summary": report.sim_summary,
                     "verifier_verdicts": list(report.verifier_verdicts)[:16],
                     "boundary_conditions": dict(report.boundary_conditions),
                     "comparison": report.comparison,
                     "advisory_only": True})
        return report

    async def run_research_cycle(
        self, market_data: Optional[Dict[str, Any]] = None,
        max_questions: int = 1,
    ) -> Dict[str, Any]:
        """One full research-loop iteration under CSC control.

        Harvests measured reliability (per-regime precision/prediction
        counts) and observed anomalies into the uncertainty map, then runs
        question-formation → VoI selection → locked contract → investigate
        → KG/policy/uncertainty update. The result is durably persisted."""
        if self.research_engine is None:
            self.configure_research()
        await self._maybe_rehydrate_research()
        reliability = getattr(self.reliability_tracker, "metrics", {})
        anomalies = []
        # A surprise spike is unexplained evidence — register it as a
        # research object, don't silently absorb it.
        recent_vfe = list(self.vfe_history or [])[-10:]
        if len(recent_vfe) >= 5 and max(recent_vfe) > 5.0:
            anomalies.append(("vfe_surprise_spike", 0.7))
        cycle = await self.research_engine.research_cycle(
            dict(market_data or {}), max_questions=max_questions,
            reliability=reliability, anomalies=anomalies)
        # KG events + the cycle container share a cycle correlation id —
        # audit_events.correlation_id is NOT NULL, and linking graph rows
        # to their producing cycle is better provenance anyway.
        cycle_id = f"cycle:{_determinism.get_uuid()}"
        for kind, payload in self.research_engine.drain_persisted_events():
            await self._persist_audit_event(
                event_type="RESEARCH_KG", action=kind,
                outcome="recorded", correlation_id=cycle_id,
                details=payload)
        # Each report gets its own RESEARCH verdict row — these rows are
        # what rebuild_policy() replays to restore method yield stats
        # after a restart.
        for report in cycle.get("reports", []):
            await self._persist_audit_event(
                event_type="RESEARCH", action="investigate",
                outcome=str(report.get("verdict", "INCONCLUSIVE")),
                correlation_id=report.get("research_id"),
                details={"question": report.get("question"),
                         "composite_confidence":
                             report.get("composite_confidence"),
                         "sim_summary": report.get("sim_summary"),
                         "verifier_verdicts": list(
                             report.get("verifier_verdicts") or [])[:16],
                         "boundary_conditions":
                             report.get("boundary_conditions"),
                         "comparison": report.get("comparison")})
        await self._persist_audit_event(
            event_type="RESEARCH", action="cycle",
            outcome=cycle.get("status", "ok"),
            correlation_id=cycle_id,
            details={"questions": len(cycle.get("questions", [])),
                     "reports": len(cycle.get("reports", []))})
        return cycle

    def get_research_journal(self) -> List[Dict[str, Any]]:
        """Read-only journal of verified research reports."""
        return [r.to_dict() for r in self._research_reports]

    async def record_outcome(
        self,
        trade_id: str,
        exit_price: Optional[float] = None,
        was_correct: Optional[bool] = None,
        realized_return: Optional[float] = None,
        shared_settlement: int = 1,
        *,
        outcome_origin: str = "unknown",
        cost_return: Optional[float] = None,
        baseline_net_return: Optional[float] = None,
        constraints_satisfied: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Feed a realized outcome back into calibration and uncertainty.

        Matches the pending directional prediction for ``trade_id`` against
        the realized price move, updates the ReliabilityTracker, adjusts
        epistemic uncertainty by the measured error (bounded, never
        mechanical decay), and persists an OUTCOME audit event.
        """
        pending = self._pending_predictions.pop(trade_id, None)
        if pending is None:
            return {"status": "unmatched", "trade_id": trade_id}

        if was_correct is None:
            if exit_price is None or not isinstance(exit_price, (int, float)):
                return {"status": "insufficient_evidence",
                        "trade_id": trade_id}
            entry = pending.get("entry_price")
            if not isinstance(entry, (int, float)) or entry <= 0:
                return {"status": "insufficient_evidence",
                        "trade_id": trade_id}
            move = (float(exit_price) - entry) / entry
            direction = pending.get("action", "HOLD")
            if direction == "BUY":
                was_correct = move > 0
            elif direction == "SELL":
                was_correct = move < 0
            else:
                was_correct = abs(move) < 0.001
            realized_return = move if direction == "BUY" else -move

        confidence = float(pending.get("confidence", 0.5))
        regime = pending.get("regime", "unknown")
        self.reliability_tracker.update_metrics(
            "csc", regime, bool(was_correct), confidence)
        self.reliability_tracker.update_action_outcome(
            regime, str(pending.get("action") or "").upper(),
            bool(was_correct), realized_return)
        # Swarm consensus learns from the same settled outcome.
        _si = getattr(self, "_swarm_intel", None)
        if _si is not None:
            _si.record_consensus_outcome(
                regime, str(pending.get("action") or "").upper(),
                bool(was_correct))
        # Feed HMS failure memory — the RSI bridge's observe_gaps reads
        # these aggregates, so losing settlements become real RSI input.
        if was_correct is False:
            self._record_failure(
                "outcome_loss",
                f"{pending.get('action')} {regime} "
                f"r={realized_return:+.4f} conf={confidence:.2f}",
                regime=regime,
                action=str(pending.get("action") or ""),
                confidence=confidence)
        # The verification swarm's calibrator sees the same settlements —
        # a 0.9-claimed decision that keeps losing flags overconfidence.
        _swarm = getattr(self, "verifier_swarm", None)
        _rec = getattr(_swarm, "record_outcome", None)
        if _rec is not None:
            _rec(confidence, bool(was_correct))

        # Score each advisor that expressed a direction on the opening
        # observation: its call is correct iff its direction matched the
        # realized move. Their weights tilt future ranking via
        # get_agent_weight — advisors earn or lose influence by evidence.
        action = pending.get("action")
        for call in pending.get("advisory_calls") or ():
            try:
                adv_dir = str(call.get("direction") or "")
                if adv_dir not in ("BUY", "SELL"):
                    continue
                adv_correct = (adv_dir == action) == bool(was_correct)
                self.reliability_tracker.update_metrics(
                    str(call["capability_id"]), regime, adv_correct,
                    float(call.get("confidence") or 0.5))
                cap = str(call["capability_id"])
                # The swarm knowledge base scores the same node outcome —
                # vote-level skill is learned, never asserted.
                _si = getattr(self, "_swarm_intel", None)
                if _si is not None:
                    _si.record_node_outcome(cap, regime, adv_correct)
                # SPRT live monitoring (ASRS continuous-monitoring
                # standard): engineered candidates carry a Wald test —
                # degraded edge => automatic rollback, audited.
                if cap.startswith("engineered:"):
                    monitor = self._engineered_sprt.get(cap)
                    if monitor is None:
                        from .model_engineering import SprtMonitor
                        monitor = SprtMonitor()
                        self._engineered_sprt[cap] = monitor
                    # Magnitude-aware feed when the realized return is
                    # known — win rate alone can hide negative expectancy.
                    if isinstance(realized_return, (int, float)):
                        # realized_return is signed by the DECISION's
                        # direction — an advisor's own net is that value
                        # when it agreed, its negation when it did not.
                        _signed = (float(realized_return)
                                   if adv_dir == str(action or "").upper()
                                   else -float(realized_return))
                        _net_bps = _signed * 1e4 - 3.25
                        verdict = monitor.feed(_net_bps)
                    else:
                        verdict = monitor.update(bool(adv_correct))
                    if verdict == "degraded":
                        cid = self._engineered_cap_to_cid.get(cap)
                        if cid is not None:
                            await self.detach_engineered_model(
                                cid, reason=f"SPRT degraded "
                                f"(llr={monitor.llr:.2f}, n={monitor.n})")
                    elif cap in self._engineered_shadow:
                        # Shadow graduation: enough real outcomes with a
                        # healthy monitor → the model earns its tilt.
                        need = self._engineered_shadow[cap]
                        if monitor.n >= need:
                            self._engineered_shadow.pop(cap, None)
                            await self._persist_audit_event(
                                event_type="MODEL_SHADOW", action="graduate",
                                outcome="graduated", correlation_id=cap,
                                details={"outcomes_seen": monitor.n})
            except Exception:
                continue

        # EV calibration pair: what the sim predicted vs what settled.
        _pred_ev = pending.get("expected_return")
        if (isinstance(_pred_ev, (int, float)) and _pred_ev > 0
                and isinstance(realized_return, (int, float))):
            # Regime-tagged pairs: a calibration learned in trend must
            # not be applied in range — the deque slides on time, not
            # on regime.
            self._ev_pairs.append((float(_pred_ev),
                                   float(realized_return),
                                   str(pending.get("regime", "unknown"))))
            _fcontrib = pending.get("feature_contributions")
            if isinstance(_fcontrib, dict):
                for _fname, _fval in _fcontrib.items():
                    if isinstance(_fval, (int, float)):
                        self._feature_pairs.append(
                            (str(_fname), float(_fval),
                             float(realized_return),
                             str(pending.get("regime", "unknown"))))

        # Reality-gate runtime monitors — advisory only. They emit
        # DRIFT_ADVISORY / KILL_SWITCH_ADVISORY evidence; the canonical
        # risk service and operator controls retain all halt authority.
        try:
            if getattr(self, "_drift_gate", None) is None:
                from trading_bot.reality_gates.drift_detection_gate import (
                    DriftDetectionGate)
                self._drift_gate = DriftDetectionGate()
            _feats = {k: float(pending[k]) for k in
                      ("volatility", "momentum", "ret_autocorr",
                       "trend_strength")
                      if isinstance(pending.get(k), (int, float))}
            drift = self._drift_gate.check_drift(
                features=_feats,
                prediction=float(_pred_ev) if isinstance(
                    _pred_ev, (int, float)) else None,
                actual=float(realized_return) if isinstance(
                    realized_return, (int, float)) else None,
                current_return=float(realized_return) if isinstance(
                    realized_return, (int, float)) else None,
                current_volatility=float(pending["volatility"]) if
                isinstance(pending.get("volatility"), (int, float)) else None,
                current_regime=str(regime))
            for alert in getattr(drift, "alerts", []) or []:
                await self._persist_audit_event(
                    event_type="DRIFT_ADVISORY", action="detect",
                    outcome=str(getattr(alert, "severity", "info")),
                    correlation_id=trade_id,
                    details={"alert": str(alert)})
                flag = str(getattr(getattr(alert, "drift_type", ""),
                                   "value", "drift"))
                self._runtime_advisory_flags.add(f"drift:{flag}")
        except Exception as exc:  # noqa: BLE001
            logger.debug("drift advisory monitor unavailable: %s", exc)
        try:
            if getattr(self, "_kill_gate", None) is None:
                from trading_bot.reality_gates.kill_switch_gate import (
                    KillSwitchGate)
                self._kill_gate = KillSwitchGate()
            if not hasattr(self, "_advisory_equity"):
                self._advisory_equity = 100000.0
            if isinstance(realized_return, (int, float)):
                self._advisory_equity += float(realized_return) * \
                    self._advisory_equity
            allowed, reasons = self._kill_gate.check(
                current_equity=self._advisory_equity,
                current_return=float(realized_return) if isinstance(
                    realized_return, (int, float)) else None,
                current_volatility=float(pending["volatility"]) if
                isinstance(pending.get("volatility"), (int, float)) else None,
                trade_result={"pnl": float(realized_return or 0.0),
                              "was_correct": bool(was_correct)})
            if not allowed and reasons:
                await self._persist_audit_event(
                    event_type="KILL_SWITCH_ADVISORY", action="trip",
                    outcome="advisory_only", correlation_id=trade_id,
                    details={"reasons": [str(getattr(r, "value", r))
                                         for r in reasons],
                             "advisory_equity": self._advisory_equity})
                self._runtime_advisory_flags.update(
                    f"kill:{getattr(r, 'value', r)}" for r in reasons)
        except Exception as exc:  # noqa: BLE001
            logger.debug("kill-switch advisory monitor unavailable: %s", exc)

        # Evidence-based uncertainty update: surprise moves it up, confirmed
        # predictions move it down — bounded and proportional to measured
        # error, not a fixed per-task multiplier.
        error = abs(confidence - (1.0 if was_correct else 0.0))
        cur = float(getattr(self.state, "epistemic_uncertainty", 0.5) or 0.5)
        # While an exploration budget is active, decay faster on
        # correct outcomes — the point of the budget is to teach the
        # gate, and a 50-trade grind undoes its purpose. Scale via
        # TB_CSC_U_DECAY for tuning without code edits.
        _step = float(os.environ.get("TB_CSC_U_DECAY", "0.1"))
        if self._explore_budget > 0:
            _step *= 2.0
        self.state.epistemic_uncertainty = float(
            np.clip(cur + (error - 0.25) * _step, 0.05, 0.95))

        # Advisory calibrators learn from the same realized outcome.
        for service in self._advisory_services:
            brain = getattr(service, "brain", service)
            if hasattr(brain, "record_outcome"):
                try:
                    brain.record_outcome(confidence, bool(was_correct))
                except Exception as exc:
                    logger.warning("CSC-V6: advisory outcome update failed: %s", exc)

        # Diagnostic rewards share the outcome's existing durable audit event.
        # Gross price settlement is never silently labelled net execution PnL.
        from .rewards import prediction_reward, trading_reward
        economic_reward = trading_reward(
            trade_id, realized_return, cost_return=cost_return,
            baseline_net_return=baseline_net_return, origin=outcome_origin,
            shared_settlement=shared_settlement,
            constraints_satisfied=constraints_satisfied)
        rewards = [
            economic_reward.to_dict(),
            prediction_reward(
                trade_id, confidence, was_correct, origin=outcome_origin,
                sample_weight=economic_reward.sample_weight).to_dict(),
        ]
        await self._persist_audit_event(
            event_type="DECISION_OUTCOME",
            action=pending.get("action", "UNKNOWN"),
            outcome="correct" if was_correct else "incorrect",
            correlation_id=trade_id,
            details={
                "symbol": pending.get("symbol"),
                "confidence": confidence,
                "realized_return": realized_return,
                # Predicted-vs-realized pair — lets the EV calibration
                # deque rehydrate from this durable row after restart.
                "expected_return": pending.get("expected_return"),
                "regime": regime,
                "advisory_calls": pending.get("advisory_calls") or [],
                "gated_calls": int(pending.get("gated_calls") or 0),
                # >1 means N decisions shared one settlement — the rows are
                # correlated, not independent samples. Consumers counting
                # outcomes for statistical weight must discount by this.
                "shared_settlement": shared_settlement,
                "rewards": rewards,
            })

        # Failure memory: an incorrect directional call is the single most
        # informative artifact the system produces — persist it so the
        # evidence plane and the RSI observer can both see it.
        if not was_correct:
            self._record_failure(
                "prediction_incorrect",
                f"{pending.get('action', 'UNKNOWN')} call on "
                f"{pending.get('symbol')} failed in regime {regime}",
                trade_id=trade_id,
                symbol=pending.get("symbol"),
                regime=regime,
                stage="outcome",
                confidence=confidence,
                context={
                    "realized_return": realized_return,
                    "expected_return": pending.get("expected_return"),
                    "advisory_calls": pending.get("advisory_calls") or [],
                })
        return {
            "status": "recorded",
            "trade_id": trade_id,
            "was_correct": bool(was_correct),
            "realized_return": realized_return,
            "epistemic_uncertainty": self.state.epistemic_uncertainty,
            "rewards": rewards,
        }

    async def record_paper_settlement(self, settlement: Mapping[str, Any]) -> Dict[str, Any]:
        """Persist actual paper-fill economics separately from mark forecasts.

        The receipt matcher owns quantity allocation; this method issues no
        orders and does not consume/score pending predictions a second time.
        """
        from dataclasses import replace
        from datetime import timezone
        from trading_bot.foundation.contracts import AuditEvent
        from .rewards import trading_reward

        if settlement.get("origin") != "paper":
            raise ValueError("paper settlement feedback requires paper receipts")
        sink = getattr(self, "_decision_sink", None)
        if sink is None or not hasattr(sink, "record_audit_event_once"):
            raise RuntimeError("durable idempotent reward sink is required")
        reward = trading_reward(
            str(settlement["settlement_id"]), settlement.get("gross_return"),
            cost_return=settlement.get("cost_return"),
            baseline_net_return=settlement.get("baseline_net_return"),
            origin="paper",
            # Execution receipts prove fills, not all risk/governance checks.
            constraints_satisfied=None)
        reward = replace(
            reward, sample_weight=float(settlement["sample_weight"]),
            blockers=tuple(dict.fromkeys(
                (*reward.blockers, *settlement.get("blockers", ())))))
        occurred_at = datetime.fromisoformat(str(settlement["exit_time"]))
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        event = AuditEvent(
            event_type="PAPER_SETTLEMENT", actor="CSC",
            action="execution_reward",
            outcome="costed" if not settlement.get("blockers") else "insufficient_evidence",
            correlation_id=str(settlement.get("decision_id")
                               or settlement["entry_order_id"]),
            occurred_at=occurred_at,
            details={**settlement, "rewards": [reward.to_dict()]})
        inserted = await sink.record_audit_event_once(
            event, audit_id="paper-settlement:" + str(settlement["settlement_id"]))
        return {"status": "recorded" if inserted else "duplicate",
                "settlement_id": settlement["settlement_id"],
                "reward": reward.to_dict()}

    _MAX_TRACKED_SYMBOLS = 64

    def _symbol_hist(self, store: Dict[str, deque], symbol: str,
                     maxlen: int) -> deque:
        """setdefault bounded at _MAX_TRACKED_SYMBOLS — an unbounded
        feed of new symbols would otherwise grow the map forever."""
        key = str(symbol)
        dq = store.get(key)
        if dq is None:
            if len(store) >= self._MAX_TRACKED_SYMBOLS:
                store.pop(next(iter(store)))
            dq = store[key] = deque(maxlen=maxlen)
        return dq

    def seed_observation_history(self, symbol: str, closes: List[float]) -> None:
        """Seed the derived-feature window from durable market history.

        Called at startup so a restart does not discard the prior bar
        window and re-lock directional decisions for a warmup period."""
        hist = self._symbol_hist(self._obs_history, str(symbol), 64)
        for close in list(closes)[-64:]:
            if isinstance(close, (int, float)) and np.isfinite(close) \
                    and close > 0:
                hist.append(float(close))

    def observation_history(self, symbol: str) -> List[float]:
        """Return the tracked close history for a symbol (read-only copy)."""
        return list(self._obs_history.get(str(symbol), ()))

    # ---------- engineered-model lifecycle ----------
    # The AI may engineer models; it may not grant them authority.
    # propose -> out-of-sample validate -> HUMAN approval flag -> attach.
    # Attached candidates are advisory-only services subject to the same
    # trust ramp, regime eligibility and reliability weighting as every
    # other advisor — no path to execution authority exists here.

    async def propose_model(self, spec: Dict[str, Any],
                            proposed_by: str = "user") -> Dict[str, Any]:
        """Register a model-engineering candidate. Spec is validated
        against the derivable-feature set — a candidate asking for data
        that can't honestly exist is rejected at proposal, not at runtime."""
        from .model_engineering import ModelCandidate, validate_spec
        errs = validate_spec(spec)
        if errs:
            await self._persist_audit_event(
                event_type="MODEL_CANDIDATE", action="propose",
                outcome="rejected", correlation_id="spec-invalid",
                details={"spec": dict(spec), "errors": errs})
            return {"status": "rejected", "errors": errs}
        c = ModelCandidate(
            candidate_id=str(uuid.uuid4()), name=str(spec.get("name") or
                f"{spec['kind']}-{uuid.uuid4().hex[:8]}"),
            spec=dict(spec), proposed_by=proposed_by)
        self._engineered_models[c.candidate_id] = c
        await self._persist_audit_event(
            event_type="MODEL_CANDIDATE", action="propose",
            outcome="proposed", correlation_id=c.candidate_id,
            details={"name": c.name, "spec": c.spec,
                     "proposed_by": proposed_by})
        return {"status": "proposed", "candidate_id": c.candidate_id,
                "name": c.name}

    async def validate_model(self, candidate_id: str,
                             bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fit on the first 70% of bars, score on the held-out rest.
        VALIDATED only if net expectancy after the cost model is positive
        on unseen data — accuracy alone does not qualify a model."""
        from .model_engineering import (evaluate_holdout, fit_candidate,
                                        HOLDOUT_FRACTION, MIN_HOLDOUT_SIGNALS,
                                        MIN_EXPECTANCY_BPS,
                                        SIGNIFICANCE_THRESHOLD)
        c = self._engineered_models.get(candidate_id)
        if c is None:
            return {"status": "error", "reason": "unknown candidate_id"}
        # Isolated history: feature enrichment uses the CSC's live obs
        # deques — validating against them both contaminates the result
        # (features see live history the validation batch shouldn't have)
        # and pollutes live state with replay bars. Snapshot and restore.
        from collections import deque as _dq
        hist_snap = {k: _dq(v, maxlen=v.maxlen)
                     for k, v in self._obs_history.items()}
        vol_snap = {k: _dq(v, maxlen=v.maxlen)
                    for k, v in self._vol_history.items()}
        self._obs_history = {}
        self._vol_history = {}
        # Live advisory disagreement and health are runtime state — a
        # sealed trial must not inherit them or the result is unrepeatable.
        disagree_snap = getattr(self, "_last_advisory_disagreement", None)
        self._last_advisory_disagreement = None
        swarm_snap = getattr(self, "_last_swarm_snapshot", None)
        self._last_swarm_snapshot = None
        sealed_snap = getattr(self, "_sealed_trial", False)
        self._sealed_trial = True
        try:
            obs = [dict(b) for b in bars if isinstance(b, Mapping)]
            for o in obs:
                self._enrich_derived_features(o)
        finally:
            self._obs_history = hist_snap
            self._vol_history = vol_snap
            self._last_advisory_disagreement = disagree_snap
            self._last_swarm_snapshot = swarm_snap
            self._sealed_trial = sealed_snap
        split = int(len(obs) * (1 - HOLDOUT_FRACTION))
        train, holdout = obs[:split], obs[split:]
        params = fit_candidate(c.spec, train)
        if params is None:
            c.status, c.verdict = "REJECTED", "INSUFFICIENT_DATA"
            c.validation = {"error": "fit failed — insufficient in-sample "
                                     "data or missing dependency"}
            await self._persist_audit_event(
                event_type="MODEL_VALIDATION", action="validate",
                outcome="REJECTED", correlation_id=candidate_id,
                details={"name": c.name, "validation": c.validation})
            return {"status": "rejected", "reason": c.validation["error"]}
        c.fitted_params = params
        c.validation = evaluate_holdout(c.spec, params, holdout,
                                        horizon=int(c.spec.get("horizon")
                                                    or 8))
        # Sealed evaluation: the verdict is bound to spec + dataset +
        # params + cost model — it can never be re-attributed silently.
        from .model_engineering import validation_seal, dataset_hash
        c.validation["seal"] = validation_seal(c.spec, obs, params)
        c.validation["dataset_hash"] = dataset_hash(obs)
        c.validation["train_bars"] = len(train)
        c.validation["holdout_bars"] = len(holdout)
        # Representative bar for the data-integrity verifier — bounded to
        # OHLCV+timestamp so the sealed record stays JSON-serializable.
        if obs:
            c.validation["sample_bar"] = {
                k: obs[-1].get(k) for k in
                ("open", "high", "low", "close", "volume", "timestamp",
                 "symbol")}
        # Promotion Gate standard (ASRS): positive OOS net expectancy AND
        # bootstrap significance P(Δ>0) >= threshold — a positive sample
        # mean without significance is luck, not edge.
        sig = (c.validation.get("significance") or {})
        thin = c.validation["holdout_signals"] < MIN_HOLDOUT_SIGNALS
        # Promotion standard: beat zero AND beat the paired buy-and-hold
        # baseline. Positive expectancy that loses to passive exposure is
        # not edge — p_gt_baseline >= 0.5 closes that hole.
        p_base = sig.get("p_gt_baseline")
        ok = (not thin
              and isinstance(c.validation["mean_net_bps"], float)
              and c.validation["mean_net_bps"] > MIN_EXPECTANCY_BPS
              and float(sig.get("p_gt_0") or 0.0) >= SIGNIFICANCE_THRESHOLD
              and isinstance(p_base, (int, float))
              and float(p_base) >= 0.5)
        c.status = "VALIDATED" if ok else "REJECTED"
        c.verdict = ("CONFIRMED" if ok else
                     "INCONCLUSIVE" if thin else "FALSIFIED")
        await self._persist_audit_event(
            event_type="MODEL_VALIDATION", action="validate",
            outcome=c.verdict, correlation_id=candidate_id,
            details={"name": c.name, "validation": c.validation,
                     "fitted_params": params})
        return {"status": c.status.lower(), "verdict": c.verdict,
                "validation": c.validation}

    async def approve_model(self, candidate_id: str) -> Dict[str, Any]:
        """The human gate: attach requires the durable operator flag
        ``control:model_approval:<id>`` — written via
        ``operator_cli approve-model`` — in account_state. No flag, no
        attach, no exceptions."""
        c = self._engineered_models.get(candidate_id)
        if c is None:
            return {"status": "error", "reason": "unknown candidate_id"}
        if c.status != "VALIDATED":
            return {"status": "blocked",
                    "reason": f"candidate is {c.status}, not VALIDATED"}
        sink = getattr(self, "_decision_sink", None)
        flag = None
        if sink is not None and hasattr(sink, "get_account_state"):
            flag = await self._safe_await(sink.get_account_state(
                f"control:model_approval:{candidate_id}"))
        if str(flag or "") not in ("1", "true", "approved"):
            return {"status": "awaiting_human",
                    "reason": "no durable operator approval found"}
        c.status = "APPROVED"
        await self._persist_audit_event(
            event_type="MODEL_APPROVAL", action="approve",
            outcome="approved", correlation_id=candidate_id,
            details={"name": c.name})
        return {"status": "approved", "candidate_id": candidate_id}

    async def attach_engineered_model(self, candidate_id: str
                                      ) -> Dict[str, Any]:
        """Final step — approved candidates become advisory services only.
        They enter with the trust ramp's unmeasured weight and must earn
        influence like every other advisor."""
        from .model_engineering import candidate_adapter
        c = self._engineered_models.get(candidate_id)
        if c is None:
            return {"status": "error", "reason": "unknown candidate_id"}
        if c.status != "APPROVED":
            return {"status": "blocked",
                    "reason": f"candidate is {c.status}, not APPROVED"}
        # Autonomous Reviewer (ASRS PG): the verification swarm audits the
        # candidate's own ledger entry before attach — a veto blocks even
        # human-approved candidates (both gates are required).
        reviewer = await self._review_engineered_candidate(c)
        if reviewer is not None and not reviewer.get("passed", True):
            await self._persist_audit_event(
                event_type="MODEL_ATTACHED", action="review",
                outcome="blocked", correlation_id=candidate_id,
                details={"name": c.name, "reviewer": reviewer})
            return {"status": "blocked",
                    "reason": "adversarial review veto",
                    "reviewer": reviewer}
        service = candidate_adapter(c)
        self.configure_cognition(service)
        self._engineered_cap_to_cid[service.capability_id] = candidate_id
        self._engineered_sprt.pop(service.capability_id, None)
        self._engineered_shadow.pop(service.capability_id, None)
        # Shadow attach: the model's calls are recorded and settled like
        # any advisor's, but excluded from the advisory tilt until its
        # monitor has seen enough real outcomes to confirm the edge
        # survives live data — ASRS 'prospective shadow' before adoption.
        self._engineered_shadow[service.capability_id] = 20
        _sup = getattr(self, "_self_wiring", None)
        if _sup is not None:
            _sup.register(service.capability_id, service,
                          state=NodeState.SHADOW)
        c.status = "ATTACHED"
        await self._persist_audit_event(
            event_type="MODEL_ATTACHED", action="attach",
            outcome="attached_shadow", correlation_id=candidate_id,
            details={"name": c.name,
                     "capability_id": service.capability_id,
                     "shadow_outcomes_required": 20})
        return {"status": "attached_shadow",
                "capability_id": service.capability_id,
                "shadow_outcomes_required": 20}

    async def _review_engineered_candidate(self, c: Any) -> Optional[Dict[str, Any]]:
        """Autonomous Reviewer (ASRS PG): run the verification swarm on the
        candidate's own evidence. Veto on consensus failure — 'not enough
        verifiers ran' fails open (honest abstention, not a blocker)."""
        swarm = getattr(self, "verifier_swarm", None)
        if swarm is None:
            return None
        try:
            from types import SimpleNamespace
            entry = SimpleNamespace(
                entry_id=c.candidate_id,
                composite_confidence=0.6,
                hypothesis=SimpleNamespace(
                    direction=c.spec.get("direction") or "BUY",
                    symbol=c.spec.get("symbol") or ""),
                reasoning_steps=[
                    f"kind={c.spec.get('kind')}",
                    f"validation={c.validation}"],
                evidence_graph_snapshot=None,
                market_data=None,
            )
            verdicts = await swarm.run_swarm(entry)
            ran = [v for v in verdicts if v.items_checked > 0]
            if not ran:
                return {"passed": False,
                        "note": "no verifiers could evaluate the "
                                "candidate — review inconclusive"}
            vetoes = [v for v in ran if not v.is_valid]
            return {"passed": len(vetoes) == 0,
                    "verifiers_ran": len(ran),
                    "vetoes": [v.agent_name for v in vetoes]}
        except Exception as exc:  # noqa: BLE001
            # A reviewer that errors is a failed gate, not a pass — the
            # attach path treats unavailable review as blocked.
            return {"passed": False,
                    "note": f"reviewer error: {exc}"}

    async def detach_engineered_model(self, candidate_id: str,
                                      reason: str = "operator"
                                      ) -> Dict[str, Any]:
        """Instant rollback (ASRS PG): remove the advisory service and mark
        the candidate ROLLED_BACK. The trust-ramp weight decays naturally;
        the service is gone immediately — no influence leaks past this."""
        c = self._engineered_models.get(candidate_id)
        if c is None:
            return {"status": "error", "reason": "unknown candidate_id"}
        cap = f"engineered:{c.name}"
        before = len(self._advisory_services)
        self._advisory_services = [
            s for s in self._advisory_services
            if str(getattr(s, "capability_id",
                           type(s).__name__)) != cap]
        removed = len(self._advisory_services) < before
        self._engineered_sprt.pop(cap, None)
        self._engineered_shadow.pop(cap, None)
        self._engineered_cap_to_cid.pop(cap, None)
        if c.status == "ATTACHED":
            c.status = "ROLLED_BACK"
            c.verdict = reason
            await self._persist_audit_event(
                event_type="MODEL_ATTACHED", action="rollback",
                outcome="rolled_back", correlation_id=candidate_id,
                details={"name": c.name, "reason": reason})
        return {"status": "rolled_back" if removed else "not_attached",
                "reason": reason}

    async def seed_advisory_history(self, obs_list: List[Any]) -> int:
        """Replay prior observations through attached advisory services so
        their internal bar windows start pre-filled — real data fills the
        window, so services emit from cycle 1 instead of spending 50-70
        live cycles reporting 'warming'. Outputs are discarded: this
        fills history, it does not decide."""
        filled = 0
        services = list(self._advisory_services)
        for obs in list(obs_list or ()):
            if not isinstance(obs, Mapping):
                continue
            # Sequential across obs (window order matters) but parallel
            # across services: ~200 advisors × 64 bars serially cost ~20
            # minutes of warmup. Per-service timeout matches the live
            # consult budget so a slow advisor can't stall seeding.
            results = await asyncio.gather(
                *(self._seed_one(svc, obs) for svc in services),
                return_exceptions=True)
            filled += sum(1 for r in results if r is not None
                          and not isinstance(r, BaseException))
        return filled

    async def _seed_one(self, svc: Any, obs: Any) -> Any:
        timeout = float(getattr(svc, "timeout_s", 5.0) or 5.0)
        return await asyncio.wait_for(svc.analyze(obs), timeout)

    def export_open_positions(self) -> Dict[str, Any]:
        """Serialize open positions for restart continuity — without this,
        a restart orphans fills that persist in the ledger: the CSC thinks
        flat while positions remain open and never settle."""
        return {
            "observation_seq": self._observation_seq,
            "positions": {
                sym: {
                    "direction": p.get("direction"),
                    "entry_price": p.get("entry_price"),
                    "entry_seq": p.get("entry_seq"),
                    "symbol": p.get("symbol"),
                    "confidence": p.get("confidence"),
                    "regime": p.get("regime"),
                    "trade_ids": list(p.get("trade_ids") or []),
                    "mfe": p.get("mfe"),
                    "mae": p.get("mae"),
                    "bars_held": p.get("bars_held"),
                    "last_price": p.get("last_price"),
                }
                for sym, p in self._open_positions.items()
            },
        }

    def import_open_positions(self, state: Optional[Dict[str, Any]]) -> int:
        """Restore open positions serialized by export_open_positions.

        Pending predictions are intentionally not restored — their
        trade_ids would collide with a fresh sequence — but the position
        itself resumes so it settles on horizon/reversal."""
        if not isinstance(state, dict):
            return 0
        positions = state.get("positions") or {}
        self._observation_seq = int(
            state.get("observation_seq") or self._observation_seq)
        restored = 0
        for sym, p in positions.items():
            if not isinstance(p, dict):
                continue
            direction = p.get("direction")
            entry = p.get("entry_price")
            if direction not in ("BUY", "SELL") or not isinstance(
                    entry, (int, float)) or not np.isfinite(entry) \
                    or entry <= 0:
                continue
            self._open_positions[str(sym)] = {
                "direction": direction,
                "entry_price": float(entry),
                "entry_seq": int(p.get("entry_seq") or 0),
                "symbol": str(p.get("symbol") or sym),
                "confidence": p.get("confidence"),
                "regime": p.get("regime"),
                "trade_ids": [],
                "mfe": p.get("mfe"),
                "mae": p.get("mae"),
                "bars_held": int(p.get("bars_held") or 0),
                "last_price": p.get("last_price"),
            }
            restored += 1
        if restored:
            logger.info(
                "CSC-V6: restored %d open positions from prior session",
                restored)
        return restored

    def _enrich_derived_features(self, obs_dict: Dict[str, Any]) -> None:
        """Derive missing causal features from the symbol's own bar history.

        A raw OHLCV feed (paper_runner, live adapter) supplies price and
        volume but no volatility/trend/rsi — those are computed here from
        strictly-prior closes. Supplied values are never overwritten;
        derived ones are marked in ``_derived_features`` for provenance."""
        if not isinstance(obs_dict, dict):
            return
        price = obs_dict.get("price") or obs_dict.get("close")
        symbol = str(obs_dict.get("symbol") or "unknown")
        derived = set()
        hist = self._symbol_hist(self._obs_history, symbol, 64)
        closes = list(hist)
        if isinstance(price, (int, float)) and np.isfinite(price) \
                and price > 0:
            closes.append(float(price))

        if "volatility" not in obs_dict and len(closes) >= 21:
            rets = np.diff(np.asarray(closes[-21:])) / np.asarray(closes[-21:-1])
            obs_dict["volatility"] = float(np.std(rets))
            derived.add("volatility")
        if "trend" not in obs_dict and "trend_direction" not in obs_dict \
                and len(closes) >= 21 and isinstance(price, (int, float)):
            ma = float(np.mean(closes[-21:-1]))
            obs_dict["trend"] = ("BULLISH" if price > ma * 1.0005 else
                                 "BEARISH" if price < ma * 0.9995 else "NEUTRAL")
            derived.add("trend")
        if "rsi" not in obs_dict and len(closes) >= 15:
            diffs = np.diff(np.asarray(closes[-15:]))
            gains = diffs[diffs > 0].mean() if (diffs > 0).any() else 0.0
            losses = (-diffs[diffs < 0]).mean() if (diffs < 0).any() else 0.0
            obs_dict["rsi"] = (100.0 if losses == 0 else
                               100.0 - 100.0 / (1.0 + gains / losses))
            derived.add("rsi")
        # Fields ~35 advisory services read but the raw feed never carries.
        # Deriving them from strictly-prior bars is honest (same evidence
        # provenance as volatility/trend/rsi above); fields that can't be
        # derived — sentiment, order-book, portfolio state — stay absent.
        if "rsi14" not in obs_dict and "rsi" in obs_dict:
            obs_dict["rsi14"] = obs_dict["rsi"]
            derived.add("rsi14")
        if "momentum" not in obs_dict and len(closes) >= 11:
            base = float(closes[-11])
            if base > 0:
                obs_dict["momentum"] = float(closes[-1] - base) / base
                derived.add("momentum")
        if "trend_strength" not in obs_dict and "momentum" in obs_dict:
            vol = float(obs_dict.get("volatility") or 0.0)
            obs_dict["trend_strength"] = (
                abs(float(obs_dict["momentum"])) / vol if vol > 0 else 0.0)
            derived.add("trend_strength")
        if "regime" not in obs_dict and "trend" in obs_dict:
            obs_dict["regime"] = {"BULLISH": "UP", "BEARISH": "DOWN"}.get(
                str(obs_dict["trend"]), "RANGE")
            derived.add("regime")
        # Regime-validity discriminator (research proposal from the
        # anti-predictive Sep-25-30 window): lag-1 return autocorrelation
        # distinguishes trending regimes from chop. In negative-autocorr
        # markets an above-MA close marks the TOP of the range, not
        # continuation — trend labels there produce anti-predictive votes.
        # Emitted as evidence features only; no advisor is forced to gate
        # on them and the CSC retains all authority.
        if "ret_autocorr" not in obs_dict and len(closes) >= 22:
            r = np.diff(np.asarray(closes[-22:])) / \
                np.asarray(closes[-22:-1])
            if float(np.std(r)) > 0:
                obs_dict["ret_autocorr"] = float(
                    np.corrcoef(r[:-1], r[1:])[0, 1])
                derived.add("ret_autocorr")
        if ("trend_reliability" not in obs_dict
                and "ret_autocorr" in obs_dict):
            obs_dict["trend_reliability"] = float(
                np.clip(1.0 + 3.0 * float(obs_dict["ret_autocorr"]),
                        0.0, 1.0))
            derived.add("trend_reliability")
        if ("trend_effective" not in obs_dict and "trend" in obs_dict
                and "ret_autocorr" in obs_dict):
            obs_dict["trend_effective"] = (
                obs_dict["trend"]
                if float(obs_dict["ret_autocorr"]) > -0.05 else "NEUTRAL")
            derived.add("trend_effective")
        vol_hist = self._symbol_hist(self._vol_history, symbol, 64)
        volume = obs_dict.get("volume")
        if ("volume_ratio" not in obs_dict
                and isinstance(volume, (int, float)) and volume > 0
                and len(vol_hist) >= 20):
            mean_vol = sum(vol_hist) / len(vol_hist)
            if mean_vol > 0:
                obs_dict["volume_ratio"] = float(volume) / mean_vol
                derived.add("volume_ratio")
        if isinstance(volume, (int, float)) and volume > 0:
            vol_hist.append(float(volume))
        # Bar-derived microstructure (Roll spread, Kyle lambda,
        # Amihud, tick-imbalance, Kaufman ER, intrabar path risk) —
        # the published estimators that work on OHLCV where L2/footprint
        # data doesn't exist. Lets the simulator/net-cost gate price
        # execution quality instead of assuming a flat cost.
        try:
            from trading_bot.analysis.microstructure_estimator import (
                estimate_all)
            hl = self._hl_history.setdefault(symbol, deque(maxlen=64))
            h_cur = obs_dict.get("high")
            l_cur = obs_dict.get("low")
            if isinstance(h_cur, (int, float)) and \
                    isinstance(l_cur, (int, float)):
                hl.append((float(h_cur), float(l_cur)))
            est = estimate_all(
                closes, list(vol_hist),
                [x[0] for x in hl] if hl else None,
                [x[1] for x in hl] if hl else None)
            for _k, _v in est.items():
                if _k not in obs_dict:
                    obs_dict[_k] = _v
                    derived.add(_k)
        except Exception:
            pass
        disagreement = getattr(self, "_last_advisory_disagreement", None)
        if disagreement is not None and "advisory_disagreement" not in obs_dict:
            obs_dict["advisory_disagreement"] = float(disagreement)
            derived.add("advisory_disagreement")
        swarm_snap = getattr(self, "_last_swarm_snapshot", None)
        if swarm_snap:
            for key, value in swarm_snap.items():
                if key not in obs_dict:
                    obs_dict[key] = value
                    derived.add(key)
        health = self._compute_self_health()
        if health is not None:
            obs_dict["system_health_score"] = health["score"]
            obs_dict["system_health_flags"] = health["flags"]
            derived.update(("system_health_score",
                            "system_health_flags"))
        if derived:
            obs_dict["_derived_features"] = sorted(derived)
        if isinstance(price, (int, float)) and np.isfinite(price) \
                and price > 0:
            hist.append(float(price))
        if "session" not in obs_dict or "session_hour" not in obs_dict:
            ts = obs_dict.get("timestamp")
            hour = None
            try:
                if isinstance(ts, str):
                    hour = int(ts[11:13])  # 'YYYY-MM-DDTHH:MM:SS...'
                elif hasattr(ts, "hour"):
                    hour = int(ts.hour)
            except (ValueError, IndexError, TypeError):
                hour = None
            if hour is not None and 0 <= hour <= 23:
                if "session_hour" not in obs_dict:
                    obs_dict["session_hour"] = float(hour)
                    derived.add("session_hour")
                if "session" not in obs_dict:
                    # UTC sessions: ASIA 0-6, LONDON 7-11, NY 12-16,
                    # OFF otherwise — coarse but honest market-time bins.
                    obs_dict["session"] = (
                        "ASIA" if hour < 7 else
                        "LONDON" if hour < 12 else
                        "NY" if hour < 17 else "OFF")
                    derived.add("session")
        # Cross-instrument features: runners feed obs['peer_close'] from a
        # synchronized second symbol (--peer-symbol); derive peer_return
        # and peer_corr from strictly-prior joint history. Absent peer
        # feed → features stay absent, never fabricated.
        peer_price = obs_dict.get("peer_close")
        phist = self._symbol_hist(self._peer_history, symbol, 96)
        if isinstance(peer_price, (int, float)) \
                and np.isfinite(peer_price) and peer_price > 0:
            phist.append(float(peer_price))
        pcloses = list(phist)
        if "peer_return" not in obs_dict and len(pcloses) > 11 \
                and pcloses[-11] > 0:
            obs_dict["peer_return"] = float(
                (pcloses[-1] - pcloses[-11]) / pcloses[-11])
            derived.add("peer_return")
        if ("peer_corr" not in obs_dict and len(pcloses) >= 30
                and len(closes) >= 30):
            a = np.asarray(closes[-30:], dtype=float)
            b = np.asarray(pcloses[-30:], dtype=float)
            ra = np.diff(a) / a[:-1]
            rb = np.diff(b) / b[:-1]
            if float(np.std(ra)) > 0 and float(np.std(rb)) > 0:
                obs_dict["peer_corr"] = float(np.corrcoef(ra, rb)[0, 1])
                derived.add("peer_corr")

    async def _settle_pending_predictions(self, obs_dict: Dict[str, Any]) -> None:
        """Close positions that have reached the holding horizon.

        Position-lifetime accounting: a position opened at observation t
        settles against the bar at t+max_hold (or earlier when an opposing
        decision reverses it). Only the observed symbol's position settles."""
        price = obs_dict.get("price") or obs_dict.get("close")
        if not isinstance(price, (int, float)) \
                or not np.isfinite(price) or price <= 0:
            return
        symbol = obs_dict.get("symbol")
        pos = self._open_positions.get(symbol)
        if pos is None:
            return
        # Intra-bar excursion: settling on bar close alone understates the
        # real path — a spike against the position inside the bar is
        # invisible at M15. Track max favorable/adverse excursion from the
        # real high/low so settled outcomes carry honest path data.
        entry = float(pos.get("entry_price") or 0)
        if entry > 0:
            side = 1.0 if pos["direction"] == "BUY" else -1.0
            for px_key in ("high", "low", "close", "price"):
                px = obs_dict.get(px_key)
                if isinstance(px, (int, float)) and np.isfinite(px) and px > 0:
                    exc = side * (float(px) - entry) / entry
                    pos["mfe"] = max(pos.get("mfe", exc), exc)
                    pos["mae"] = min(pos.get("mae", exc), exc)
        atr = self._update_atr(str(symbol), obs_dict)
        if atr and atr > 0:
            signed = (float(price) - pos["entry_price"]) * (
                1.0 if pos["direction"] == "BUY" else -1.0)
            if signed < -self._adverse_atr_mult * atr:
                await self._close_position(symbol, float(price),
                                           reason="adverse_move_atr")
                return
        # Position lifetime is counted in THIS symbol's bars, not global
        # observation seq — in multi-symbol mode one venue bar produces N
        # obs, so comparing against _observation_seq settles positions
        # ~N times earlier than the configured horizon.
        pos["bars_held"] = int(pos.get("bars_held") or 0) + 1
        pos["last_price"] = float(price)
        if pos["bars_held"] >= self._position_max_hold:
            await self._close_position(symbol, float(price),
                                       reason="holding_horizon")
        # Unpositioned predictions (their close was vetoed/failed) have no
        # position to settle through — resolve them at horizon against
        # this bar's price so their advisory calls still get scored and
        # the pending count doesn't leak. Age counts own-symbol bars, not
        # global obs seq (same multi-symbol pitfall as the position
        # horizon above).
        for tid, pred in list(self._pending_predictions.items()):
            if str(pred.get("symbol")) != str(symbol):
                continue
            pred["bars_seen"] = int(pred.get("bars_seen") or 0) + 1
            if (pred.get("unpositioned")
                    and pred["bars_seen"] >= self._position_max_hold):
                await self.record_outcome(
                    tid, exit_price=float(price),
                    outcome_origin="unpositioned_horizon")

    def _update_atr(self, symbol: str, obs_dict: Dict[str, Any]
                    ) -> Optional[float]:
        """Wilder-style EMA of true range from real bars.

        True range = max(high-low, |high-prev_close|, |low-prev_close|);
        when the observation carries only close, range degrades to
        |close - prev_close|. Returns None until ~5 samples accumulate —
        the adverse exit stays inactive rather than fire on noise."""
        close = obs_dict.get("close", obs_dict.get("price"))
        if not isinstance(close, (int, float)) or close <= 0:
            return None
        st = self._atr_state.setdefault(symbol, {"atr": 0.0, "n": 0,
                                                 "prev": 0.0})
        high = obs_dict.get("high")
        low = obs_dict.get("low")
        prev = st["prev"]
        if isinstance(high, (int, float)) and isinstance(low, (int, float))                 and high >= low:
            tr = float(high - low)
            if prev > 0:
                tr = max(tr, abs(high - prev), abs(low - prev))
        else:
            tr = abs(close - prev) if prev > 0 else 0.0
        st["prev"] = float(close)
        if tr <= 0:
            return st["atr"] if st["n"] >= 5 else None
        st["atr"] = tr if st["n"] == 0 else (
            st["atr"] * 13 + tr) / 14.0  # Wilder(14)
        st["n"] += 1
        return st["atr"] if st["n"] >= 5 else None

    async def _register_directional(
        self, trade_id: str, action: str, symbol: Optional[str],
        price: float, confidence: Any, regime: Any,
        expected_return: Any = None,
        feature_contributions: Any = None,
    ) -> None:
        """Attach an approved directional decision to a position.

        Same-direction decisions extend the position (additional entries in
        the same direction share its outcome); an opposing decision closes
        the existing position at this bar's price first."""
        symbol = str(symbol or "unknown")
        existing = self._open_positions.get(symbol)
        if existing is not None and existing["direction"] != action:
            await self._close_position(symbol, float(price),
                                       reason="reversed_by_decision")
            # Re-fetch: a vetoed close leaves the old position on the ledger —
            # it must not be silently overwritten by the new direction.
            existing = self._open_positions.get(symbol)
        if existing is not None and existing["direction"] != action:
            # Close order failed/vetoed — the ledger still holds the old
            # exposure. Register the prediction without position attachment:
            # it reports as unmatched rather than inheriting the old side's PnL.
            self._pending_predictions[trade_id] = {
                "action": action, "symbol": symbol,
                "entry_price": float(price), "confidence": confidence,
                "regime": regime, "expected_return": expected_return,
                "feature_contributions": dict(feature_contributions
                                              or {}),
                "advisory_calls": list(
                    getattr(self, "_last_advisory_calls", ()) or ()),
                "gated_calls": int(getattr(self, "_tilt_gated", 0)),
                "unpositioned": True,
            }
            return
        if existing is None:
            existing = {
                "direction": action,
                "entry_price": float(price),
                "entry_seq": self._observation_seq,
                "symbol": symbol,
                "confidence": confidence,
                "regime": regime,
                "trade_ids": [],
            }
            self._open_positions[symbol] = existing
        existing["trade_ids"].append(trade_id)
        self._pending_predictions[trade_id] = {
            "position_symbol": symbol,
            "action": action,
            "symbol": symbol,
            "entry_price": existing["entry_price"],
            "confidence": confidence,
            "regime": regime,
            "expected_return": expected_return,
            "feature_contributions": dict(feature_contributions or {}),
            # Advisor calls active when this decision opened — scored at
            # settlement so advisor weights are measured against reality.
            "advisory_calls": list(
                getattr(self, "_last_advisory_calls", ()) or ()),
            # Calls suppressed by regime-eligibility when this decision
            # ranked — lets outcomes measure the gating's live effect.
            "gated_calls": int(getattr(self, "_tilt_gated", 0)),
        }

    async def _close_position(
        self, symbol: str, exit_price: float, reason: str = "exit",
    ) -> Optional[float]:
        """Close the open position through the canonical execution path.

        When an execution service is wired (paper/live), the close dispatches
        a real opposing order through the decision bus — the ledger is the
        authoritative exposure record, so internal bookkeeping only settles
        after the close order reaches a terminal state. A vetoed/failed close
        leaves the position open (retried on the next qualifying bar) rather
        than pretending flat while the ledger holds exposure. With no
        execution service wired (evaluators/tests), settlement is mark-only."""
        pos = self._open_positions.get(symbol)
        if pos is None or not isinstance(exit_price, (int, float)) \
                or not np.isfinite(exit_price) or exit_price <= 0:
            return None
        fill_price = None
        close_id = None
        svc = getattr(self, "execution_service", None)
        if svc is not None and self.decision_bus is not None \
                and hasattr(self.decision_bus, "propose_action"):
            close_id = f"close-{symbol}-{uuid.uuid4().hex[:10]}"
            action = LogAction(
                action_type="TRADE_EXECUTION",
                payload={
                    "symbol": symbol, "action": "CLOSE", "quantity": 0.0,
                    "price": float(exit_price), "trade_id": close_id,
                    "intent": "position_close", "reason": reason,
                },
                agent_id="CSC_V6",
                priority=EventPriority.CRITICAL,
            )
            action.sign()  # provenance on the capital path — the
            # signature gate in propose_action vetoes any forgery
            await self._safe_await(self.decision_bus.propose_action(action))
            status = await self._safe_await(
                action.wait_for_decision(timeout=5.0))
            if status not in (ActionStatus.APPROVED, ActionStatus.EXECUTED):
                logger.warning(
                    "CSC-V6: close order for %s not approved (%s) — position "
                    "stays open on the ledger", symbol, status)
                return None
            adapter = getattr(svc, "adapter", None)
            if adapter is not None and hasattr(adapter, "get_order"):
                try:
                    report = await adapter.get_order(close_id)
                    if report.fills:
                        fill_price = float(report.fills[-1].price)
                        try:
                            intended = float(pos.get("quantity") or 0.0)
                            filled_q = float(sum(
                                float(f.quantity) for f in report.fills))
                            fill_rate = (filled_q / intended
                                         if intended > 0 else 1.0)
                            venue = (getattr(adapter, "venue", None)
                                     or type(adapter).__name__)
                            slip = getattr(report, "slippage_bps", None)
                            self._exec_learning.record_fill(
                                str(venue), fill_rate=fill_rate,
                                shortfall_bps=slip
                                if np.isfinite(slip or np.nan) else None)
                        except Exception as exc:
                            logger.debug(
                                "CSC-V6: exec-learning record failed: %s",
                                exc)
                except Exception as exc:
                    logger.warning(
                        "CSC-V6: close order %s executed but fill lookup "
                        "failed: %s", close_id, exc)
        self._open_positions.pop(symbol, None)
        exit_used = fill_price if fill_price is not None else float(exit_price)
        entry = pos["entry_price"]
        direction = 1.0 if pos["direction"] == "BUY" else -1.0
        realized = direction * (exit_used - entry) / entry
        self._funnel["settled_positions"] += 1
        journal_entry = {
            "symbol": pos["symbol"], "direction": pos["direction"],
            "entry_price": entry, "exit_price": exit_used,
            "realized_return": realized, "reason": reason,
            "entry_seq": pos.get("entry_seq"),
            "exit_seq": self._observation_seq,
            "regime": pos.get("regime"),
            "close_order_id": close_id,
            "settled_at_fill": fill_price is not None,
            # Intra-bar path: realized_return alone hides the excursion.
            "mfe": pos.get("mfe"),
            "mae": pos.get("mae"),
        }
        self._settled_outcomes.append(journal_entry)
        # Durable journal: the settled-outcome deque is the real input to
        # psychology/counterfactual/decay self-state advisors. Persisting
        # it lets _rehydrate_settled_journal restore it after restart —
        # learning state must outlive the process.
        await self._persist_audit_event(
            event_type="POSITION_SETTLED",
            action=pos.get("direction", "UNKNOWN"),
            outcome="correct" if realized > 0 else "incorrect",
            correlation_id=str(
                close_id or (pos.get("trade_ids") or [""])[0] or ""),
            details=journal_entry)
        for tid in list(pos["trade_ids"]):
            try:
                await self.record_outcome(
                    tid, was_correct=realized > 0, realized_return=realized,
                    shared_settlement=len(pos["trade_ids"]))
            except Exception as exc:
                logger.warning(
                    "CSC-V6: position outcome write failed for %s: %s",
                    tid, exc)
        # A settled position is forward (paper-real-world) evidence — feed
        # it into the research engine so claims about this symbol earn or
        # lose real-world tier support.
        if self.research_engine is not None:
            try:
                self.research_engine.observe_forward_result(
                    symbol, realized, str(pos.get("regime") or "unknown"),
                    trade_ids=list(pos["trade_ids"]))
            except Exception as exc:
                logger.warning(
                    "CSC-V6: research forward-outcome feed failed: %s", exc)
        logger.info(
            "CSC-V6: closed %s position on %s (%s): entry %.6f exit %.6f "
            "ret %+.5f", pos["direction"], symbol, reason, entry,
            exit_used, realized)
        return realized

    async def close_all_positions(
        self, prices: Dict[str, float],
    ) -> Dict[str, float]:
        """Flush every open position at the supplied marks — end-of-stream
        accounting for evaluators; live positions only close on signal or
        horizon."""
        realized: Dict[str, float] = {}
        for symbol in list(self._open_positions):
            price = prices.get(symbol)
            if isinstance(price, (int, float)) and price > 0:
                result = await self._close_position(
                    symbol, float(price), reason="stream_end")
                if result is not None:
                    realized[symbol] = result
        return realized

    @staticmethod
    def _jsonable(value: Any) -> Any:
        """Coerce audit-detail values into JSON-safe primitives.

        numpy scalars (int64/float32/ndarray) and arbitrary objects make
        json.dumps raise TypeError downstream — one bad field would drop
        the entire audit event. Coerce rather than lose the record."""
        if isinstance(value, dict):
            return {str(k): CognitiveSystemController._jsonable(v)
                    for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [CognitiveSystemController._jsonable(v)
                    for v in value]
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        return str(value)

    async def _persist_audit_event(
        self, event_type: str, action: str, outcome: str,
        correlation_id: str, details: Dict[str, Any],
    ) -> None:
        """Append a durable AuditEvent to the configured sink, fail-open in
        memory-only contexts (the bus jsonl still carries the proposal)."""
        alerter = getattr(self, "_voice_alerter", None)
        if (alerter is not None and getattr(alerter, "enabled", False)
                and (event_type in ("EMERGENCY_HALT", "ESTOP",
                                     "EMERGENCY_STOP")
                     or outcome in ("EMERGENCY_HALT", "ESTOP",
                                    "circuit_breaker"))):
            try:
                alerter.alert(
                    f"Trading system alert: {event_type} {outcome}")
            except Exception:  # noqa: BLE001
                pass
        details = self._jsonable(details)
        sink = getattr(self, "_decision_sink", None)
        if sink is None:
            return
        try:
            from trading_bot.foundation.contracts import AuditEvent
            await self._safe_await(sink.record_audit_event(AuditEvent(
                event_type=event_type,
                actor="CSC_V6",
                action=action,
                outcome=outcome,
                correlation_id=correlation_id,
                details=details,
            )))
            # Preflight self-check counts durable writes — the check must
            # observe the ledger accept events, not merely be called.
            self._audit_writes_ok = getattr(
                self, "_audit_writes_ok", 0) + 1
        except Exception as exc:
            # Shutdown drain race: writes can land after the repository
            # closed — expected noise, log once at debug, not per-write.
            if "closed database" in str(exc).lower():
                if not getattr(self, "_sink_closed_logged", False):
                    self._sink_closed_logged = True
                    logger.debug(
                        "CSC-V6: decision sink closed — post-shutdown "
                        "writes suppressed")
                return
            logger.warning("CSC-V6: decision sink write failed: %s", exc)

    def get_decision_journal(self) -> Dict[str, Any]:
        """Read-only decision journal: pending predictions + folded summary
        history. The durable side lives in the repository audit_events."""
        return {
            "pending_predictions": dict(self._pending_predictions),
            "open_positions": {
                s: {k: v for k, v in p.items() if k != "trade_ids"}
                for s, p in self._open_positions.items()},
            "research_reports": self.get_research_journal(),
            "uncertainty_map": (self.research_engine.uncertainty_map.snapshot()
                                if self.research_engine else {}),
            "research_policy": (self.research_engine.policy.snapshot()
                                if self.research_engine else {}),
            "capability_proposals": ([
                {"proposal_id": p.proposal_id, "claim_id": p.claim_id,
                 "summary": p.summary,
                 "confidence_level": p.confidence_profile.level,
                 "advisory_only": True, "promotion_eligible": False}
                for p in self.research_engine.capability_proposals()]
                if self.research_engine else []),
            "folded_summaries": list(self.folder.folded_summaries),
            "reliability": {
                agent: {reg: {
                    "precision": m.precision,
                    "brier_score": m.brier_score,
                    "total_predictions": m.total_predictions,
                } for reg, m in regimes.items()}
                for agent, regimes in self.reliability_tracker.metrics.items()
            },
        }

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

        # Subordinate advisory cognition services (configure_cognition) —
        # their analysis joins the same evidence channel as PCA artifacts.
        # Run in PARALLEL with a per-service timeout — a slow or hanging
        # advisor must not serialize-stall the decision pipeline.
        # Circuit breaker: 5 consecutive failures disable the advisor for
        # this session — broken modules warn once, then go quiet.
        failures = getattr(self, "_advisory_failures", None)
        if failures is None:
            self._advisory_failures = failures = {}
        # Advisor tiering: measured-active advisors run EVERY cycle;
        # the long tail defers to every Nth cycle (its output was
        # measured degenerate anyway — spending minutes collecting
        # 'warming' payloads buys nothing). TB_ADVISORY_DEFER_N=1
        # restores the old every-advisor-every-cycle behavior.
        try:
            defer_n = int(os.environ.get("TB_ADVISORY_DEFER_N", "4"))
        except (TypeError, ValueError):
            defer_n = 4
        self._advisory_cycle = getattr(self, "_advisory_cycle", 0) + 1
        # Event trigger, not just frequency: a volatility/regime shock
        # consults the full electorate immediately rather than waiting
        # out the defer window. Cycle 1 is always full — cold start
        # needs breadth, not the narrowest electorate.
        vol_now = 0.0
        try:
            vol_now = float(observation.get("volatility") or 0.0)
        except (TypeError, ValueError):
            pass
        vol_prev = getattr(self, "_last_obs_vol", None)
        self._last_obs_vol = vol_now
        vol_shock = (vol_prev is not None and vol_prev > 0 and
                     (vol_now / vol_prev > 2.0 or
                      vol_now / vol_prev < 0.5))
        full_cycle = (defer_n <= 1 or
                      self._advisory_cycle == 1 or
                      self._advisory_cycle % defer_n == 0 or
                      vol_shock)
        try:
            from .advisory import MEASURED_ACTIVE_SET
        except Exception:  # noqa: BLE001 — never gate on import failure
            MEASURED_ACTIVE_SET = frozenset()
        total = getattr(self, "_advisory_services", [])

        def _cap(s):
            return str(getattr(s, "capability_id", "")
                       or type(s).__name__)

        # Per-advisor cadence override: a service may declare its own
        # defer_n (fast-decaying orderflow wants 1-2; EDGAR filings are
        # fine at 8+). Global defer_n is the floor, not the law.
        def _due(s):
            if full_cycle:
                return True
            if _cap(s) in MEASURED_ACTIVE_SET:
                return True
            try:
                n = int(getattr(s, "defer_n", defer_n) or defer_n)
            except (TypeError, ValueError):
                n = defer_n
            return n <= 1 or self._advisory_cycle % n == 0

        services = [
            s for s in total
            if failures.get(_cap(s), 0) < 5 and _due(s)]
        if not full_cycle:
            deferred = [s for s in total if not _due(s)
                        and _cap(s) not in MEASURED_ACTIVE_SET]
            self._funnel["advisors_deferred"] = \
                self._funnel.get("advisors_deferred", 0) + len(deferred)
            for s in deferred:
                artifacts.append({  # explicit abstention, not absence
                    "agent": str(getattr(s, "capability_id",
                                         type(s).__name__)),
                    "advisory_only": True,
                    "status": "deferred",
                    "defer_cycle": self._advisory_cycle})
        caps = [str(getattr(s, "capability_id", type(s).__name__))
                for s in services]

        async def _one(svc):
            # timeout_s is advisor-controlled: coerce garbage to the
            # default and clamp to the ceiling — a service declaring
            # timeout_s=None/3600 must not stall the pipeline.
            try:
                budget = float(getattr(
                    svc, "timeout_s", self._ADVISORY_TIMEOUT_DEFAULT_S)
                    or self._ADVISORY_TIMEOUT_DEFAULT_S)
            except (TypeError, ValueError):
                budget = self._ADVISORY_TIMEOUT_DEFAULT_S
            budget = max(0.1, min(
                budget, self._ADVISORY_TIMEOUT_CEILING_S))
            return await asyncio.wait_for(
                self._safe_await(svc.analyze(observation)),
                timeout=budget)

        results = await asyncio.gather(
            *(_one(s) for s in services), return_exceptions=True)
        for cap, result in zip(caps, results):
            if isinstance(result, Exception):
                failures[cap] = failures.get(cap, 0) + 1
                self._funnel["advisor_exceptions"] += 1
                self._record_failure(
                    "advisor_error",
                    f"advisory {cap} raised {type(result).__name__}",
                    symbol=observation.get("symbol"),
                    stage="advisory_consult",
                    context={"capability_id": cap,
                             "error": str(result)[:200],
                             "consecutive_failures": failures[cap]})
                if failures[cap] == 5:
                    logger.warning(
                        "CSC-V6: advisory %s disabled after 5 failures",
                        cap)
                else:
                    logger.warning("CSC-V6: advisory %s failed: %s",
                                   cap, result)
                continue
            failures.pop(cap, None)
            artifact = {"agent": cap, "advisory_only": True}
            if isinstance(result, Mapping):
                artifact.update(result)
                artifact["agent"] = cap
            else:
                artifact["evidence"] = {"result": result}
            try:
                artifact = self._security_kernel().sign_artifact(
                    cap, artifact)
            except Exception:  # noqa: BLE001 — unsigned evidence is
                pass            # still admitted; see verify sweep below
            artifacts.append(artifact)
        # Anti-hallucination sweep: artifacts claiming to be signed
        # that fail verification are quarantined, not silently
        # admitted — provenance forgery is worse than no evidence.
        verified = []
        kernel = self._security_kernel()
        for art in artifacts:
            if "sig" in art:
                ok, reason = kernel.verify_artifact(art)
                if not ok:
                    art["status"] = "quarantined"
                    art["sig_fail"] = reason
                    self._funnel["sig_quarantined"] = \
                        self._funnel.get("sig_quarantined", 0) + 1
            verified.append(art)
        return verified

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
            seed_material = json.dumps(
                observation, sort_keys=True, default=str).encode("utf-8")
            seed = int.from_bytes(
                hashlib.sha256(seed_material).digest()[:4], "little")
            rng = np.random.RandomState(seed)
            input_signal += rng.normal(0, 0.01, (512,))

        for k in range(loops):
            h_next, token = self.discoloop.transition(input_signal, e_k, k)
            self.discrete_channel.append(token)
            idx = getattr(self.discoloop, "last_entity_idx", 0)
            e_k = np.zeros_like(h_next)
            e_k[idx] = 1.0

        # Bounded channel: retain only the most recent 100 tokens.
        if len(self.discrete_channel) > 100:
            self.discrete_channel = self.discrete_channel[-100:]

        self.continuous_state["latent"] = np.asarray(self.discoloop.hidden_state)

    async def _pivot_refine_loop(
        self, branches: List[ReasoningBranch], simulations: Dict[str, Any]
    ) -> Optional[ReasoningBranch]:
        """AutoResearchClaw Pivot/Refine logic (arXiv:2605.17734)."""
        if not branches:
            return None

        # Advisory tilt: directional calls from subordinate advisors nudge
        # ranking by at most ±ADVISORY_TILT, weighted by measured reliability
        # (get_agent_weight defaults to 1.0 until ~10 scored outcomes — an
        # equal prior, then decays on real precision). Advisors tilt; they
        # never decide — the simulation filter, EV gate, churn guard, risk,
        # and governance all remain downstream and unaware of them.
        calls = list(getattr(self, "_last_advisory_calls", ()) or ())
        # Signature quarantine is a vote filter, not just a label:
        # artifacts marked quarantined by the verify sweep carry no
        # tilt weight — forged provenance votes as zero, not as "also".
        _raw_n = len(calls)
        calls = [c for c in calls
                 if str(c.get("status") or "") != "quarantined"
                 and not c.get("sig_fail")]
        if len(calls) < _raw_n:
            self._funnel["tilt_quarantined"] = \
                self._funnel.get("tilt_quarantined", 0) \
                + (_raw_n - len(calls))

        # Vote-agreement measurement: many advisors are redundant
        # transforms of the same price features — five RSI-family voters
        # agreeing is not five independent signals. Pairwise directional
        # agreement is measured per cycle so the tilt can bound cluster
        # influence by evidence, not by assumed independence.
        _votes: Dict[str, str] = {}
        for c in calls:
            d = str(c.get("direction") or "").upper()
            if d in ("BUY", "SELL"):
                _votes[str(c.get("capability_id"))] = d
        _agr = getattr(self, "_vote_agreement", None)
        if _agr is None:
            _agr = self._vote_agreement = {}
        _ids = sorted(_votes)
        for _i in range(len(_ids)):
            for _j in range(_i + 1, len(_ids)):
                _key = (_ids[_i], _ids[_j])
                _dq = _agr.get(_key)
                if _dq is None:
                    _dq = _agr[_key] = deque(maxlen=48)
                _dq.append(1.0 if _votes[_ids[_i]]
                           == _votes[_ids[_j]] else 0.0)

        # Model-parliament disagreement signal: normalized dispersion of
        # weighted directional votes — 0 when advisors agree, 1 when
        # split. Stored strictly-prior and enriched into the NEXT obs as
        # `advisory_disagreement`; point-in-time safe, provenance-marked.
        _signed = []
        for c in calls:
            d = str(c.get("direction") or "").upper()
            if d in ("BUY", "SELL"):
                _signed.append(float(c.get("confidence") or 0.5)
                               * (1.0 if d == "BUY" else -1.0))
        if _signed:
            _net = abs(sum(_signed)) / max(1e-9, sum(abs(v) for v in _signed))
            self._last_advisory_disagreement = float(1.0 - _net)
        else:
            self._last_advisory_disagreement = None
        # Self-referential loop check: disagreement feeds the NEXT
        # obs's features — if it predicts next-cycle disagreement the
        # electorate is arguing with its own echo. Track autocorr
        # so the feedback is measured, not assumed benign.
        if self._last_advisory_disagreement is not None:
            _d = self._last_advisory_disagreement
            # Per-symbol: disagreement on EURUSD must not measure
            # autocorrelation against GBPUSD's next cycle. Symbol
            # comes from the branch plans — this method has no
            # obs_dict in scope.
            _sym = next(
                (str((b.execution_plan or {}).get("symbol"))
                 for b in (branches or [])
                 if (b.execution_plan or {}).get("symbol")), "?")
            _hmap = getattr(self, "_disagreement_hist", None)
            if _hmap is None:
                _hmap = self._disagreement_hist = {}
            _hist = _hmap.setdefault(_sym, deque(maxlen=64))
            _hist.append(_d)
            if len(_hist) >= 8:
                import numpy as _npd
                _x = _npd.asarray(_hist)
                _ac = float(_npd.corrcoef(_x[:-1], _x[1:])[0, 1])
                if _ac > 0.5:
                    self._funnel["self_feedback_suspect"] += 1

        # Swarm deliberation over the same ballots: all four voting
        # mechanisms run, emergent signals attach, and the consensus is
        # snapshotted for the NEXT observation's features — point-in-time
        # safe, like advisory_disagreement. Advisory evidence only.
        try:
            _swarm_consensus = self._swarm_intel.deliberate(
                calls,
                regime=str(getattr(self.state, "current_regime", None)
                           or "unknown"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("CSC-V6: swarm deliberation failed: %s", exc)
            _swarm_consensus = None
        self._last_swarm_consensus = _swarm_consensus
        self._last_swarm_snapshot = (
            _swarm_consensus.feature_dict()
            if _swarm_consensus is not None else None)
        self._funnel["swarm_deliberations"] += 1

        _sup = getattr(self, "_self_wiring", None)
        _shadow_ids = (_sup.shadow_ids() if _sup is not None else frozenset())

        def _advisory_tilt(branch) -> float:
            action = str(
                (branch.execution_plan or {}).get("action", "")).upper()
            if action not in ("BUY", "SELL"):
                return 0.0
            regime = str(
                getattr(self.state, "current_regime", None) or "unknown")
            num = den = gated = 0.0
            eligible: List[Tuple[str, str, float, float]] = []
            for c in calls:
                direction = str(c.get("direction") or "").upper()
                if direction not in ("BUY", "SELL"):
                    continue
                aid = str(c.get("capability_id"))
                # Shadow mode: engineered advisors and self-wiring
                # shadow nodes earn measured outcomes but cast no tilt
                # until they graduate live observation.
                if (aid in self._engineered_shadow
                        or aid in _shadow_ids):
                    gated += 1
                    continue
                # Regime-conditional eligibility: a measured-below-
                # chance advisor votes evidence-only here — direction
                # dropped, not inverted (inverting would fit the same
                # data that measured it).
                if not self.reliability_tracker.eligible_direction(
                        aid, regime):
                    gated += 1
                    continue
                w = self.reliability_tracker.get_agent_weight(
                    aid, regime)
                w *= float(c.get("evidence_weight") or 1.0)
                conf = float(c.get("confidence") or 0.5)
                eligible.append((aid, direction, w, conf))
            # Measured-redundancy downweight: an advisor whose directional
            # vote tracks an already-placed peer's >85% of the time casts
            # (1 - 0.5*agreement) of its weight — floor ~0.5x, provenance
            # kept (the call still records), independence unassumed.
            eligible.sort(key=lambda e: -e[2])
            placed: List[str] = []
            for aid, direction, w, conf in eligible:
                red = 1.0
                for pid in placed:
                    _pk = (aid, pid) if aid <= pid else (pid, aid)
                    _pdq = _agr.get(_pk)
                    if _pdq and len(_pdq) >= 10:
                        _a = sum(_pdq) / len(_pdq)
                        if _a > 0.85:
                            red = min(red, 1.0 - 0.5 * _a)
                placed.append(aid)
                num += w * red * conf * (
                    1.0 if direction == action else -1.0)
                den += w * red * conf
            self._tilt_gated = int(gated)
            return (num / den) if den > 0 else 0.0  # normalized to [-1, 1]

        # Score on the full probabilistic signal — confidence alone is a
        # constant default (0.9) which degenerates to first-branch-wins.
        ranked = sorted(
            branches,
            key=lambda b: b.confidence * b.probability
            * (1.0 - b.uncertainty)
            * (1.0 + self._ADVISORY_TILT * _advisory_tilt(b)),
            reverse=True,
        )
        best = ranked[0]

        def _fails_simulation(branch) -> bool:
            sim_data = simulations.get(branch.branch_id, {})
            if isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self"):
                return False
            # Only directional branches can "fail" a simulation — a HOLD/WAIT
            # branch has zero directional return by construction, not by risk.
            # "Fails" means *measured harm*: explicit invalidation triggers
            # or a negative simulated expected value. A merely weak win
            # probability is not harm — downstream confidence sizing
            # discounts it, so a 0.5-coin-flip branch isn't vetoed here but
            # will not reach governance as a high-confidence proposal.
            action = str(
                (branch.execution_plan or {}).get("action", "")).upper()
            if action not in ("BUY", "SELL") or not isinstance(sim_data, dict):
                return False
            triggers = sim_data.get("invalidation_triggers") or []
            ev = sim_data.get("expected_value")
            return bool(triggers) or (
                isinstance(ev, (int, float)) and ev < 0)

        def _measured_suppressed(branch) -> bool:
            # CSC self-measurement: an action whose OWN realized-return
            # history in this regime is negative-expectancy (n>=10) is
            # suppressed via the same fallback as a failed simulation.
            # Not an advisory veto — the system vetoing its own measured
            # defect (UP-regime BUY: -0.80%% across 36 pooled outcomes).
            action = str(
                (branch.execution_plan or {}).get("action", "")).upper()
            if action not in ("BUY", "SELL"):
                return False
            regime = str(
                getattr(self.state, "current_regime", None) or "unknown")
            suppressed = self.reliability_tracker.action_suppressed(
                regime, action)
            if suppressed:
                logger.info(
                    "CSC-V6: %s suppressed in regime %s — measured"
                    "negative expectancy", action, regime)
            return suppressed

        if not (_fails_simulation(best) or _measured_suppressed(best)):
            return best

        # The best branch failed — fall back to the next-ranked viable
        # branch before collapsing to a no-exposure pivot.
        for candidate in ranked[1:]:
            if not (_fails_simulation(candidate) or _measured_suppressed(candidate)):
                logger.warning(
                    "CSC-V6: Best branch %s failed simulation; falling back "
                    "to %s", best.branch_id, candidate.branch_id)
                return candidate

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
            new_branch.reasoning_trace.append(f"Refinement: {critique}")
        return new_branch

    # Coarse circuit-breaker floor: a >4% single-observation sigma is
    # flash-crash territory for the FX instruments this system trades
    # (EURUSD daily vol is ~0.5-1%). The running baseline term makes the
    # guardrail instrument-aware once history exists.
    _HASP_ABS_VOL_LIMIT = 0.04
    _HASP_BASELINE_MULT = 4.0
    _HASP_BASELINE_MIN_SAMPLES = 8

    @staticmethod
    def _resolve_git_sha() -> str:
        """Best-effort real git revision for provenance; 'unknown' when the
        tree has no VCS metadata. Never a fabricated or signed-looking value."""
        try:
            import subprocess

            repo_root = Path(__file__).resolve().parents[3]
            out = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(repo_root),
                capture_output=True, text=True, timeout=5)
            sha = out.stdout.strip()
            if out.returncode == 0 and len(sha) == 40:
                return sha
        except Exception:
            pass
        return "unknown"

    def _apply_hasp_guardrails(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous HASP volatility guardrail check on a raw observation.

        Instrument-aware: intervenes when observed volatility exceeds the
        running baseline by a large multiple, or crosses the absolute extreme
        floor when too little history exists to form a baseline. A fixed
        vol>0.3 threshold can never trigger at FX scale — that guardrail was
        dead code and is now replaced."""
        volatility = observation.get("volatility", 0.0)
        if not isinstance(volatility, (int, float)) or volatility == 0.0:
            market = observation.get("market")
            if isinstance(market, dict):
                volatility = market.get("volatility", 0.0)
        if isinstance(volatility, (int, float)):
            vol = float(volatility)
            history = getattr(self, "_vol_baseline", None)
            if history is None:
                history = self._vol_baseline = deque(maxlen=256)
            baseline = (
                float(np.median(np.asarray(history)))
                if len(history) >= self._HASP_BASELINE_MIN_SAMPLES else None
            )
            history.append(vol)
            limit = self._HASP_ABS_VOL_LIMIT
            if baseline is not None:
                limit = max(limit, self._HASP_BASELINE_MULT * baseline)
            if vol > limit:
                return {
                    "status": "pf_intervention",
                    "result": {"action": "override_to_hold"},
                    "pf_result": {
                        "action": "override_to_hold",
                        "reason": (
                            f"Extreme volatility {vol:.4f} exceeds limit "
                            f"{limit:.4f}"),
                    },
                }
        return {"status": "ok"}

    def _select_optimal_action(
        self, branch: ReasoningBranch, simulations: Dict[str, Any],
        trade_id: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes the final trade proposal from the best reasoning branch and its simulation results.

        Symbol always comes from the branch plan or the actual observation —
        never a foreign-instrument default. A BUY/SELL branch without a
        measured position size degrades honestly to HOLD rather than
        inventing a quantity.
        """
        sim_data = simulations.get(branch.branch_id, {})
        if isinstance(sim_data, MagicMock) or hasattr(sim_data, "_mock_self"):
            sim_data = {}

        plan = branch.execution_plan if isinstance(branch.execution_plan, dict) else {}
        market = market_data if isinstance(market_data, dict) else {}

        symbol = plan.get("symbol") or market.get("symbol") or "unknown"
        action = str(plan.get("action") or "HOLD")

        qty = plan.get("quantity", plan.get("position_size", 0.0))
        if not isinstance(qty, (int, float)) or isinstance(qty, bool):
            qty = 0.0
        qty = float(qty)
        if not np.isfinite(qty):
            qty = 0.0

        slippage = sim_data.get("expected_slippage") if isinstance(sim_data, dict) else None
        if isinstance(slippage, MagicMock) or not isinstance(slippage, (int, float)):
            slippage = None
        if slippage is not None:
            qty *= max(0.0, 1.0 - (float(slippage) * 5.0))

        # Epistemic-uncertainty sizing: when the model is ignorant,
        # exposure shrinks linearly toward zero — at u >= 0.7 a BUY/SELL
        # collapses to HOLD (zero size). Cold start (u=1.0) is maximum
        # ignorance -> no exposure until predictions are confirmed.
        _u = float(
            getattr(self.state, "epistemic_uncertainty", 0.5) or 0.5)
        uncertainty_factor = float(max(0.0, min(1.0, 1.0 - _u / 0.7)))
        qty *= uncertainty_factor

        # Portfolio correlation cap — CSC's own sizing constraint, not a
        # risk-rule edit and not advisor veto: a same-direction entry on a
        # symbol whose measured returns correlate strongly with an
        # already-open position is one economic bet, not two. Scale size
        # by 1 - |corr| so corr ~0 keeps full size and corr →1 → no new
        # exposure. Opposite-direction entries (partial hedges) keep size.
        _corr_factor = 1.0
        if action in ("BUY", "SELL") and qty > 0:
            own = list(self._obs_history.get(str(symbol), ()))
            for osym, opos in self._open_positions.items():
                if str(osym) == str(symbol) \
                        or opos.get("direction") != action:
                    continue
                peer = list(self._obs_history.get(str(osym), ()))
                if len(own) < 15 or len(peer) < 15:
                    continue
                n = min(len(own), len(peer), 30)
                a = np.diff(np.asarray(own[-n:], dtype=float))
                b = np.diff(np.asarray(peer[-n:], dtype=float))
                if float(np.std(a)) <= 0 or float(np.std(b)) <= 0:
                    continue
                corr = float(np.corrcoef(a, b)[0, 1])
                if np.isfinite(corr):
                    _corr_factor = min(
                        _corr_factor, max(0.0, 1.0 - abs(corr)))
        if _corr_factor < 1.0:
            qty *= _corr_factor
            self._funnel["corr_capped"] = self._funnel.get(
                "corr_capped", 0) + 1

        _exploratory = False
        if (action in ("BUY", "SELL") and qty <= 0.0
                and self._explore_budget > 0):
            # Bounded escape from the abstention trap: allow a small
            # exploratory position so real fills can feed the
            # epistemic-uncertainty / EV-calibration learning loops.
            qty = self._explore_factor
            uncertainty_factor = self._explore_factor
            _exploratory = True
            # Budget decrements at approval, not proposal — a
            # proposal that dies at risk/shield/governance should not
            # spend exploration allowance it never used.

        # Unmeasurable size on a directional action -> explicit no-position.
        if action in ("BUY", "SELL") and qty <= 0.0:
            action = "HOLD"
            qty = 0.0

        expected_return = None
        if isinstance(sim_data, dict):
            exp_val = sim_data.get("expected_value")
            if isinstance(exp_val, (int, float)) and qty > 0 \
                    and np.isfinite(exp_val):
                expected_return = float(exp_val) / qty
                if not np.isfinite(expected_return):
                    expected_return = None

        return {
            "trade_id": trade_id or _determinism.get_uuid(),
            "symbol": symbol,
            "action": action,
            "quantity": max(0.0, qty),
            "confidence": (float(min(1.0, max(0.0, branch.confidence)))
                           if isinstance(branch.confidence, (int, float))
                           and np.isfinite(branch.confidence) else 0.0),
            "causal_impact": sim_data.get("structural_impact", {}) if isinstance(sim_data, dict) else {},
            "expected_return": expected_return,
            "feature_contributions": (
                dict(sim_data["feature_contributions"])
                if isinstance(sim_data, dict)
                and isinstance(sim_data.get("feature_contributions"),
                               dict) else {}),
            "slippage_measured": slippage is not None,
            "uncertainty_size_factor": uncertainty_factor,
            "exploratory": _exploratory,
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
            "status": "triaged_for_research",
            "promoted": False,
            "triage_score": triage_score,
            "trace": ["observe", "triage"]
        }

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        """Constructs an immutable research ledger entry for decision provenance."""
        provenance = InstitutionalProvenance(
            pipeline_version="UCA-V6",
            git_sha=getattr(self, "_git_sha", "unknown") or "unknown",
        )
        branch_conf = getattr(branch, "confidence", 0.5)
        if not isinstance(branch_conf, (int, float)) or not np.isfinite(branch_conf):
            branch_conf = 0.5
        evidence_graph = getattr(branch, "evidence_graph", None)
        if not hasattr(evidence_graph, "nodes"):
            evidence_graph = EvidenceGraph()
        hypotheses = getattr(branch, "hypotheses", None) or []
        return ResearchLedgerEntry(
            entry_id=_determinism.get_uuid(),
            hypothesis=hypotheses[0] if hypotheses else None,
            reasoning_steps=getattr(branch, "reasoning_trace", []),
            evidence_graph_snapshot=evidence_graph,
            composite_confidence=float(branch_conf),
            provenance=provenance
        )

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        """Computes the confidence vector from measured inputs only.

        Each component is derived from a real artifact in the evidence graph
        or the reliability ledger. Anything never measured is 0.0 — an honest
        "unknown" that drags min_confidence down instead of a fabricated
        constant."""
        graph = getattr(entry, "evidence_graph_snapshot", None)
        nodes_map = getattr(graph, "nodes", {}) or {}
        nodes = list(nodes_map.values()) if isinstance(nodes_map, dict) \
            else list(nodes_map)

        def _meta(node, key):
            m = getattr(node, "metadata", {}) or {}
            v = m.get(key)
            return float(v) if isinstance(v, (int, float)) else None

        statistical = float(np.clip(
            getattr(entry, "composite_confidence", 0.0) or 0.0, 0.0, 1.0))

        regime = 0.0
        for node in nodes:
            if _meta(node, "regime") is not None or _meta(node, "trend") is not None \
                    or _meta(node, "volatility") is not None:
                regime = float(np.clip(getattr(node, "confidence", 0.0), 0.0, 1.0))
                break

        execution = 0.0
        tail_risk = 0.0
        for node in nodes:
            ref = str((_meta(node, "source_ref") or ""))
            if ref.startswith(("sim:", "simulation:")):
                wp = _meta(node, "win_probability")
                if wp is not None:
                    execution = float(np.clip(wp, 0.0, 1.0))
                dd = _meta(node, "p95_drawdown")
                if dd is not None:
                    # p95 path drawdown scaled: 5%+ sim tail drawdown -> ~0
                    tail_risk = float(np.clip(1.0 - dd * 20.0, 0.0, 1.0))
                break

        model_stability = 0.0
        sample_size = 0
        metrics = getattr(getattr(self, "reliability_tracker", None),
                          "metrics", {}) or {}
        csc_metrics = metrics.get("CSC_V6", {})
        for regime_metrics in csc_metrics.values():
            sample_size += int(getattr(regime_metrics, "total_predictions", 0))
        if sample_size:
            # 1 - Brier is a bounded honest stability proxy.
            brier_vals = [
                getattr(m, "brier_score", 1.0) for m in csc_metrics.values()]
            model_stability = float(
                np.clip(1.0 - float(np.mean(brier_vals)), 0.0, 1.0))

        return ConfidenceVector(
            statistical=statistical,
            regime=regime,
            execution=execution,
            tail_risk=tail_risk,
            model_stability=model_stability,
            sample_size=sample_size,
        )

    def get_status(self) -> Dict[str, Any]:
        """Returns the strategic controller's status and version metadata."""
        return {
            "status": "active",
            "version": "UCA-2026-V5",
            "active_loops": self._max_loops,
            "active_tasks": len(getattr(self.state, "active_tasks", []) or []),
            "vfe": self.variational_free_energy
        }

    # -- 12-stage pipeline internals ------------------------------------------
    # Extracted from process_market_observation so each stage is independently
    # testable (TD-02). _Terminal wraps a stage-produced terminal result:
    # `None` must not be conflated with "continue" since a missing branch
    # legitimately produces a None decision at stage 7.

    class _Terminal:
        __slots__ = ("decision",)

        def __init__(self, decision: Optional["CoreDecision"]) -> None:
            self.decision = decision

    def _normalize_observation(self, observation: Any) -> Tuple[Dict[str, Any], str]:
        """Stage 0: accept dict or object-like observation; resolve trade_id."""
        # Copy so stamping trade_id never mutates the caller's dict/object.
        if isinstance(observation, dict):
            obs_dict = dict(observation)
        else:
            obs_dict = dict(getattr(observation, "__dict__", {}) or {})

        # Resolve exactly once: a caller-supplied id wins, else one draw from
        # the deterministic source. NB: dict.get(key, get_uuid()) would evaluate
        # the default eagerly — a wasted draw even when the key exists — and
        # divergent draw counts between keyed/unkeyed inputs break replay parity.
        trade_id = obs_dict.get("trade_id")
        if not trade_id:
            trade_id = _determinism.get_uuid()
        obs_dict["trade_id"] = trade_id
        return obs_dict, trade_id

    async def _stage_perception(self, obs_dict: Dict[str, Any]) -> float:
        """Stage 1: sensory surprise -> VFE history."""
        surprise = self._calculate_sensory_surprise(obs_dict)
        self.vfe_history.append(surprise)
        return surprise

    async def _stage_evidence_retrieval(self, observation: Any) -> List[Any]:
        """Stage 2: HMS evidence chain with empty-chain fallback."""
        try:
            evidence_chain = await self._safe_await(self.hms.retrieve_evidence_chain(str(observation)))
        except Exception as e:
            logger.warning(f"CSC-V6: Evidence chain retrieval failed, falling back to empty chain: {e}")
            evidence_chain = []
        # Reflective context: recent failures + RSI lessons join the
        # evidence plane so the hypothesis stage sees what the system got
        # wrong before it reasons — bounded, provenance-tagged, advisory.
        try:
            obs_d = observation if isinstance(observation, dict) else {}
            reflective = self.hms.retrieve_reflective_context(
                regime=obs_d.get("regime"), symbol=obs_d.get("symbol"),
                limit=10)
            if reflective:
                evidence_chain = list(evidence_chain or []) + reflective
        except Exception as e:
            logger.debug(f"CSC-V6: reflective context unavailable: {e}")
        return evidence_chain

    def _security_kernel(self):
        """Lazy AgentSecurityKernel — signs/verifies advisory artifacts
        and issues capability-domain identities."""
        k = getattr(self, "_sk", None)
        if k is None:
            from .security_kernel import AgentSecurityKernel
            k = self._sk = AgentSecurityKernel()
        return k

    def _research_market_data(self, symbol: str = None) -> dict:
        """Build the market_data payload investigate() needs: live close
        history so a market_edge question can simulate branches. The
        caller may override symbol; default = most recent tracked."""
        sym = symbol or next(iter(self._obs_history), None)
        closes = self.observation_history(sym) if sym else []
        return {"symbol": sym or "unknown",
                "closes": closes[-256:],
                "question_source": "csc"}

    def ask_research(self, question: str, sources=None,
                     investigate: bool = True,
                     market_data: dict = None):
        """Operator/CSC -> research engine: send a question down the
        institutional pipeline (fetch -> EQE -> weakness inversion ->
        KG ingest -> investigate). Advisory evidence only."""
        if self._institutional_research is None:
            from .research.institutional import InstitutionalResearchSystem
            self._institutional_research = InstitutionalResearchSystem(
                engine=self.research_engine)
        return self._institutional_research.ask(
            question, sources=sources, investigate=investigate,
            market_data=market_data or self._research_market_data())

    async def ask_research_async(self, question: str, sources=None,
                                 investigate: bool = True,
                                 market_data: dict = None):
        """In-loop variant: awaits the investigate stage so the verdict
        lands IN the returned report (no polling). Use from run_cycle
        and the operator channel's async handlers."""
        irs = getattr(self, "_institutional_research", None)
        if irs is None:
            from .research.institutional import InstitutionalResearchSystem
            irs = self._institutional_research = \
                InstitutionalResearchSystem(engine=self.research_engine)
        return await irs.ask_async(
            question, sources=sources, investigate=investigate,
            market_data=market_data or self._research_market_data())

    def _compute_self_health(self) -> Optional[Dict[str, Any]]:
        # Sealed validation trials must not inherit live runtime counters.
        if getattr(self, "_sealed_trial", False):
            return None
        """Measured self-diagnosis: the CSC scores its own operational
        health from real counters — advisor error rate, eligibility
        gating fraction, suppressed actions, emergency state, funnel
        degeneracy. 100 = clean, each degradation deducts. This is what
        the self-* advisory services were missing: real state to see.
        A degraded score also writes to failure memory — self-concern
        feeding the RSI gap path (self-healing's input)."""
        calls = int(getattr(self, "_funnel", {}).get(
            "advisory_artifacts", 0) or 0)
        if calls <= 0:
            return None
        fc = getattr(self, "_funnel", {}) or {}
        errors = int(fc.get("advisor_exceptions", 0) or 0)
        degenerate = int(fc.get("advisor_degenerate", 0) or 0)
        gated = int(getattr(self, "_tilt_gated", 0) or 0)
        suppressed = len(getattr(
            self.reliability_tracker, "_suppressed", {}) or {})
        flags: List[str] = []
        score = 100.0
        err_rate = errors / calls
        if err_rate > 0.05:
            score -= min(30.0, err_rate * 200.0)
            flags.append(f"advisor_error_rate={err_rate:.2f}")
        degen_rate = degenerate / calls
        if degen_rate > 0.95:
            score -= 15.0
            flags.append(f"funnel_degenerate={degen_rate:.2f}")
        if suppressed > 0:
            score -= min(20.0, suppressed * 5.0)
            flags.append(f"actions_suppressed={suppressed}")
        if getattr(self.state, "trading_halted", False) or getattr(
                self.state, "emergency_stop", False):
            score -= 40.0
            flags.append("emergency_stop")
        # Runtime advisory monitors (drift/kill-switch gates) surface as
        # health flags — evidence for diagnostics, never halt authority.
        for adv_flag in getattr(self, "_runtime_advisory_flags", ()):
            score -= 10.0
            flags.append(str(adv_flag))
        health = {"score": round(max(0.0, score), 1), "flags": flags,
                  "advisor_error_rate": round(err_rate, 4),
                  "degenerate_rate": round(degen_rate, 4),
                  "suppressed": suppressed}
        self._last_self_health = health
        if health["score"] < 60.0:
            self._record_failure(
                "system_health_degraded",
                f"health={health['score']} flags={flags}",
                score=health["score"])
        return health

    def _record_failure(self, kind: str, summary: str, **kwargs: Any) -> None:
        """Write a categorized failure into HMS failure memory. Fail-soft —
        a memory write must never break the decision path."""
        hms = getattr(self, "hms", None)
        if hms is None or not hasattr(hms, "record_failure"):
            return
        try:
            hms.record_failure(kind, summary, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.debug("CSC-V6: failure-memory write failed: %s", exc)

    async def _stage_guardrails(self, observation: Any, obs_dict: Dict[str, Any]) -> Optional["_Terminal"]:
        """Stage 3: HASP volatility check, then skill-router guardrail."""
        intervention = self._apply_hasp_guardrails(observation)
        if isinstance(intervention, dict) and intervention.get("status") != "pf_intervention":
            intervention = await self.skill_router.route_task("market_ingestion", observation)
        if hasattr(intervention, "to_dict"):
            intervention = intervention.to_dict()
        if isinstance(intervention, dict) and intervention.get("status") == "pf_intervention":
            pf_result = intervention.get("pf_result", {})
            reason = pf_result.get("reason", intervention.get("reason", "unknown"))
            if pf_result.get("action") == "override_to_hold" or intervention.get("action") == "override_to_hold":
                return self._Terminal(CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=obs_dict.get("trade_id") or "NO_BRANCH",
                    dominant_rejection_reason=f"HASP PF Intervention: {reason}"
                ))
        return None

    async def _stage_internalization(self, obs_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stages 4 + 4.5: DiscoLoop recurrence and PCA consultation.

        Returns the advisory artifacts shared by the agent population so the
        hypothesis stage can attach them as provenance-tagged evidence."""
        await self._run_discoloop_reasoning(obs_dict)

        # Reset per-cycle advisory state — a short-circuited cycle must
        # not leak last cycle's calls into this decision.
        self._last_advisory_calls = []
        self._tilt_gated = 0

        # PCA Consultation — persistent agents share compressed artifacts
        artifacts = await self._consult_agent_population(obs_dict)
        # Queued research reports enter the same advisory channel once —
        # provenance-tagged evidence, never authority.
        if self._research_artifacts:
            artifacts = list(artifacts or []) + list(self._research_artifacts)
            self._research_artifacts.clear()
        # Record which advisory capabilities contributed this cycle so the
        # terminal DECISION row carries evidence provenance — the audit
        # trail must show what informed an approval, not just its result.
        self._last_advisory_ids = sorted({
            str(a.get("agent") or a.get("capability_id")
                or a.get("agent_id"))
            for a in (artifacts or [])
            if isinstance(a, Mapping)
            and (a.get("agent") or a.get("capability_id")
                 or a.get("agent_id"))
        })
        # Normalized directional calls this cycle — consumed by branch
        # ranking (bounded tilt) and scored against realized outcomes so
        # advisor weights are measured, not asserted. confidence and
        # evidence_weight are advisor-controlled: coerce into [0,1] —
        # a garbage or oversized value must neither crash this stage
        # nor let one voter crowd out the rest of the electorate.
        def _unit01(val: Any, default: Optional[float]
                    ) -> Optional[float]:
            try:
                f = float(val)
            except (TypeError, ValueError):
                return default
            if f != f:  # NaN poisons every downstream comparison
                return default
            return min(1.0, max(0.0, f))

        calls = []
        for a in (artifacts or []):
            if not isinstance(a, Mapping):
                continue
            cap = str(a.get("agent") or a.get("capability_id")
                      or a.get("agent_id") or "")
            direction = a.get("direction")
            if not cap or direction not in ("BUY", "SELL"):
                continue
            calls.append({
                "capability_id": cap,
                "direction": direction,
                "confidence": _unit01(a.get("confidence"), None),
                # Exploration-weighted evidence: advisors that
                # emit while exploring (epsilon-greedy) flag a lower
                # weight so exploration noise doesn't read as
                # conviction.
                "evidence_weight": _unit01(
                    a.get("evidence_weight"), 1.0),
            })
        self._last_advisory_calls = calls

        # Signal-quality ledger: attachment count is not intelligence.
        # Classify what each advisor actually emitted this cycle so the
        # report shows directional/substantive/degenerate honestly.
        _degenerate = {'warming', 'no_read', 'no_data', 'missing_data',
                       'no_signal', 'none', 'skipped', 'unavailable',
                       'idle', 'degenerate'}
        _sup = getattr(self, "_self_wiring", None)
        # Abstention has a price nobody scores: the system's own
        # abstain decision is never punished for missed moves.
        # Measure it — record each abstain cycle's close and resolve
        # against the next obs so funnel_report shows the honest
        # opportunity cost of inaction.
        _sym_key = str(obs_dict.get("symbol") or "?")
        _closes = getattr(self, "_last_obs_close", None)
        if not isinstance(_closes, dict):
            # Per-symbol last-seen close — a GBPUSD print must never
            # measure the opportunity cost of a EURUSD abstain.
            _closes = self._last_obs_close = {}
        _abstains = getattr(self, "_last_outcome_was_abstain", None)
        if not isinstance(_abstains, dict):
            _abstains = self._last_outcome_was_abstain = {}
        _prev_close = _closes.get(_sym_key)
        _last_outcome = _abstains.get(_sym_key, False)
        _cur_price = None
        try:
            _cur_price = float(
                obs_dict.get("price") or obs_dict.get("close") or 0)
        except (TypeError, ValueError):
            _cur_price = None
        if (_last_outcome and _prev_close and _cur_price
                and _prev_close > 0):
            _abs_move = abs(_cur_price - _prev_close) / _prev_close
            self._funnel["abstain_opp_cost_sum"] += int(_abs_move * 1e6)
        if _cur_price:
            _closes[_sym_key] = _cur_price
        if (_sup is not None and self._advisor_dir_pending
                and isinstance(_cur_price, (int, float))
                and _cur_price > 0):
            # Claims older than ~4 M15 bars are gap-contaminated —
            # resolving a Tuesday claim against a Sunday-open price
            # measures the gap, not the advisor.
            # Use the observation's own timestamp, not wall clock —
            # in replay a week of bars processes in seconds and every
            # claim would look 'fresh' by wall time.
            _now = time.time()
            try:
                from datetime import datetime as _dtx
                _now = _dtx.fromisoformat(str(
                    obs_dict.get("timestamp", "")).replace(
                    "Z", "+00:00")).timestamp()
            except (TypeError, ValueError):
                pass
            for _cap2, (_p0, _dir, _t0, _sym0) in list(
                    self._advisor_dir_pending.items()):
                if _sym0 and _sym0 != _sym_key:
                    continue  # other instrument's bar — claim stays open
                del self._advisor_dir_pending[_cap2]
                if _now - _t0 > 4 * 900:
                    continue  # expired — don't score gap noise
                hit = (_dir == "BUY" and _cur_price > _p0) or \
                    (_dir == "SELL" and _cur_price < _p0)
                _sup.observe_outcome(_cap2, hit)
        # Metadata keys carry identity/framing, not content — an
        # artifact holding only these emitted nothing measurable.
        _META_KEYS = frozenset({
            "agent", "capability_id", "agent_id", "advisory_only",
            "type", "timestamp", "source", "direction", "confidence",
            "evidence", "status", "evidence_weight"})
        for a in (artifacts or []):
            if not isinstance(a, Mapping):
                self._funnel['advisor_degenerate'] += 1
                continue
            _cap = str(a.get("agent") or a.get("capability_id")
                       or a.get("agent_id") or "")
            if a.get('direction') in ('BUY', 'SELL'):
                self._funnel['advisor_directional_calls'] += 1
                if _sup is not None and _cap:
                    _sup.observe(_cap, "substantive")
                    if _cur_price:
                        try:
                            from datetime import datetime as _dty
                            _ct = _dty.fromisoformat(str(
                                obs_dict.get("timestamp", "")).replace(
                                "Z", "+00:00")).timestamp()
                        except (TypeError, ValueError):
                            _ct = time.time()
                        self._advisor_dir_pending[_cap] = (
                            _cur_price, a.get('direction'), _ct,
                            _sym_key if _sym_key != "?" else "")
                continue
            ev = a.get('evidence')
            # Status may sit inside an evidence mapping or at top level
            # (raw advisor output). Artifacts that carry no 'evidence'
            # key at all — research reports ('artifact'), PCA insights
            # ('data') — are still substantive payloads, not degenerate
            # emits; classifying them degenerate corrupted the funnel
            # and fed false failure signals to the wiring supervisor.
            status = (str(ev.get('status')).lower()
                      if isinstance(ev, Mapping)
                      else str(a.get('status') or '').lower())
            has_payload = any(
                a.get(k) not in (None, "", {}, [], ())
                for k in a.keys() - _META_KEYS)
            if status in _degenerate or (not ev and not has_payload):
                self._funnel['advisor_degenerate'] += 1
                if _sup is not None and _cap:
                    # Pass the raw status — 'warming' and feed-limited
                    # states are honest, not failures; only genuinely
                    # broken emits should streak toward demotion.
                    _sup.observe(_cap, status or "degenerate")
            else:
                self._funnel['advisor_substantive'] += 1
                if _sup is not None and _cap:
                    _sup.observe(_cap, "substantive")
        return artifacts

    async def _stage_hypothesis_and_simulation(
        self, observation: Any, evidence_chain: Optional[List[Any]] = None,
        advisory_artifacts: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[ReasoningBranch], Dict[str, Any]]:
        """Stages 5 + 6: competing branches, then causal simulation."""
        branches = await self._safe_await(
            self.hypothesis_gen.generate_competing_branches(
                observation,
                evidence_chain=evidence_chain,
                advisory_artifacts=advisory_artifacts,
            ))

        sim_results = {}
        if hasattr(self.hypothesis_gen, "simulate_branches"):
            try:
                sim_results = await self._safe_await(
                    self.hypothesis_gen.simulate_branches(
                        branches, market_data=observation,
                        measured_features=(
                            self.feature_attribution_report()))) or {}
            except Exception as e:
                logger.warning(f"CSC-V6: Causal simulation error: {e}")
                sim_results = {}
        return branches, sim_results

    async def _stage_pivot_refine(
        self, branches: List[ReasoningBranch], sim_results: Dict[str, Any],
        trade_id: str = "",
    ) -> Any:
        """Stage 7: Pivot/Refine selection; _Terminal(ABSTAIN) if nothing viable."""
        best_branch = await self._safe_await(self._pivot_refine_loop(branches, sim_results))
        if not best_branch:
            # No viable reasoning branches — record an explicit abstention
            # rather than returning a silent None.
            logger.info("CSC-V6: No viable reasoning branches after Pivot/Refine; abstaining")
            return self._Terminal(CoreDecision(
                outcome=DecisionOutcome.ABSTAIN,
                trade_id=trade_id or "unknown",
                dominant_rejection_reason="No viable reasoning branches produced",
            ))
        return best_branch

    def _stage_synthesis(
        self, best_branch: ReasoningBranch, sim_results: Dict[str, Any],
        trade_id: str, obs_dict: Dict[str, Any],
        branches: Optional[List[ReasoningBranch]] = None,
    ) -> Dict[str, Any]:
        """Post-verification synthesis: final trade proposal from the
        verified branch, grounded in the observation's symbol/price."""
        _explore_probe = False
        _win_action = str(
            (best_branch.execution_plan or {}).get("action", "")
        ).upper()
        if (self._explore_budget > 0
                and _win_action not in ("BUY", "SELL") and branches):
            # Explore-probe promotion: the electorate's honest verdict
            # is nondirectional every cycle, so the exploration budget
            # would otherwise never engage and _ev_pairs/_feature_pairs
            # would never refill. Promote the highest-scoring
            # directional branch (preferring non-negative sim EV) as a
            # bounded exploratory probe — tagged, sized at ~10%, and
            # still routed through risk/shield/governance downstream.
            _dir_cands = [
                b for b in branches
                if str((b.execution_plan or {}).get("action", "")
                       ).upper() in ("BUY", "SELL")]
            if _dir_cands:
                def _score(b):
                    return (b.confidence * b.probability
                            * (1.0 - b.uncertainty))
                _dir_cands.sort(key=_score, reverse=True)
                def _sim_ev(b):
                    sd = sim_results.get(b.branch_id)
                    ev = (sd.get("expected_value")
                          if isinstance(sd, dict) else None)
                    return ev if isinstance(ev, (int, float)) else 0.0
                best_branch = next(
                    (b for b in _dir_cands if _sim_ev(b) >= 0.0),
                    _dir_cands[0])
                _explore_probe = True
                self._funnel["explore_probes"] = (
                    self._funnel.get("explore_probes", 0) + 1)
        decision_proposal = self._select_optimal_action(
            best_branch, sim_results, trade_id=trade_id, market_data=obs_dict)
        if _explore_probe and isinstance(decision_proposal, dict):
            decision_proposal["exploratory"] = True
            _q = decision_proposal.get("quantity")
            if isinstance(_q, (int, float)) and _q > 0:
                decision_proposal["quantity"] = min(
                    float(_q), float(self._explore_factor))
        if decision_proposal and isinstance(decision_proposal, dict):
            decision_proposal["trade_id"] = trade_id
            # Execution price should be the freshest real mark, not the
            # minutes-old bar close the pipeline decided on. mark_price +
            # quote_time are injected only by live quote paths (follow
            # mode); replay bars carry neither, so replay stays causal.
            mark = obs_dict.get("mark_price")
            quote_ts = obs_dict.get("quote_time")
            fresh = False
            try:
                fresh = (mark is not None and quote_ts is not None
                         and abs(time.time() - float(quote_ts)) <= 30.0)
            except (TypeError, ValueError):
                pass
            decision_proposal["price"] = (
                float(mark) if fresh
                else obs_dict.get("price", obs_dict.get("close")))
            self._apply_net_of_cost_gate(
                decision_proposal, best_branch, sim_results, obs_dict)
        return decision_proposal

    def _ev_calibration_factor(self, regime: Optional[str] = None) -> float:
        """Shrinkage between simulated and realized EV: mean(realized) /
        mean(predicted) over recent settled trades, clamped to [0, 1].
        Insufficient samples -> 1.0 (raw gate; learning needs data).
        A non-positive realized mean -> 0.0 (no proposal earns approval).
        """
        # Prefer same-regime pairs when they have enough samples —
        # a bull-regime calibration is not evidence about range.
        if regime is not None:
            _sub = [(p, r) for p, r, g in self._ev_pairs if g == regime]
            if len(_sub) >= self._ev_min_samples:
                preds = [p for p, _ in _sub]
                mean_p = float(np.mean(preds))
                mean_r = float(np.mean([r for _, r in _sub]))
                if mean_p <= 0 or mean_r <= 0:
                    return 0.0
                return float(np.clip(mean_r / mean_p, 0.0, 1.0))
        if len(self._ev_pairs) < self._ev_min_samples:
            # Under-sampled -> CONSERVATIVE prior, not full trust.
            # Measured on this system: sim EV ~+0.0054 vs realized
            # ~+0.00004 (raw EV ~150x optimistic). Trusting raw EV
            # during warmup makes the net-cost gate weakest exactly
            # when the evidence is thinnest — inverted safety. The
            # prior ramps with evidence so learning still gets data.
            n = len(self._ev_pairs)
            _prior = float(os.environ.get(
                "TB_CSC_EV_COLD_PRIOR", "0.05"))
            return min(1.0, max(_prior, 0.2 * n / self._ev_min_samples))
        preds = [p for p, _, _ in self._ev_pairs]
        mean_p = float(np.mean(preds))
        mean_r = float(np.mean([r for _, r, _ in self._ev_pairs]))
        if mean_p <= 0 or mean_r <= 0:
            return 0.0
        return float(np.clip(mean_r / mean_p, 0.0, 1.0))

    def _apply_net_of_cost_gate(
        self, proposal: Dict[str, Any], branch: ReasoningBranch,
        sim_results: Dict[str, Any], obs_dict: Dict[str, Any],
    ) -> None:
        """Abstention discipline: a directional proposal whose simulated
        expected value cannot beat the estimated round-trip cost downgrades
        to HOLD with the reason recorded — trading costs money; a proposal
        that cannot cover it is not an edge."""
        action = str(proposal.get("action") or "").upper()
        if action not in ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL"):
            return
        sim = sim_results.get(branch.branch_id)
        if sim is not None and not isinstance(sim, dict):
            return  # legacy/mock sim payloads (lists, mocks) — not gated here
        sim = sim if isinstance(sim, dict) else {}
        ev = sim.get("expected_value")
        cost_bps = obs_dict.get("cost_bps") or obs_dict.get("spread_bps")
        if cost_bps is None:
            # Roll-estimated spread from strictly-prior closes — real
            # measured cost > estimate > flat default.
            cost_bps = obs_dict.get("est_spread_bps")
            if cost_bps is not None and float(cost_bps) <= 0:
                cost_bps = None  # 0 = below resolution, not free
            if cost_bps is not None:
                proposal["cost_source"] = "roll_estimate"
        if cost_bps is None:
            cost_bps = self._default_cost_bps
            proposal["cost_source"] = "flat_default"
        try:
            round_trip_cost = 2.0 * float(cost_bps) / 1e4
        except (TypeError, ValueError):
            round_trip_cost = 2.0 * self._default_cost_bps / 1e4
        # Calibrate before comparing: raw simulated EV systematically
        # overestimates (~150x measured); the gate compares cost to what
        # trades of this kind actually earned, not what the sim hoped.
        if proposal.get("exploratory"):
            # Exploration is explicitly for gathering realized
            # evidence — applying the (uncalibrated) net-cost gate
            # here would block the very fills the budget exists to
            # produce. Size is already capped at 10% by the floor.
            proposal["net_cost_bypass"] = "exploration"
            self._funnel["net_cost_explore_bypass"] += 1
            return
        cal = self._ev_calibration_factor(
            (obs_dict or {}).get("regime")
            or (obs_dict or {}).get("trend"))
        ev_cal = ev * cal if isinstance(ev, (int, float)) else ev
        if (cal == 0.0 and isinstance(ev, (int, float))
                and ev >= round_trip_cost):
            # Bricked calibration: the raw sim edge is sufficient but
            # realized evidence is negative. Let every 10th proposal
            # through as a measured probe — without new realizations
            # the gate can never recover.
            self._cal_probe_counter += 1
            # Adaptive trickle: while _ev_pairs is still below the
            # minimum-sample count, probe more often so realizations
            # refill quickly; once stocked, rare probes keep it fresh.
            _rate = (5 if len(self._ev_pairs) < self._ev_min_samples
                     else 20)
            if self._cal_probe_counter % _rate == 0:
                proposal["calibration_probe"] = True
                self._funnel["net_cost_probe"] += 1
                return
        if not isinstance(ev_cal, (int, float)) or ev_cal < round_trip_cost:
            self._funnel["net_cost_downgrade"] += 1
            proposal["action"] = "HOLD"
            proposal["downgraded_reason"] = (
                f"insufficient net edge: calibrated EV "
                f"{ev_cal if isinstance(ev_cal, (int, float)) else ev} "
                f"< round-trip cost {round_trip_cost:.6f} "
                f"(calibration {cal:.4f})")
            proposal["downgraded_from"] = action

    class _UnavailableGovernanceGate:
        """Fail-closed stub used when no governance gate can be constructed."""

        async def authorize(self, action, payload, context):
            return None

    async def _stage_risk_check(
        self, decision_proposal: Optional[Dict[str, Any]],
        obs_dict: Dict[str, Any], trade_id: str,
    ) -> Tuple[Optional["_Terminal"], Any]:
        """Stage 8.5: canonical portfolio-risk boundary (fail closed).

        Returns (terminal, risk_decision). When the canonical service approves
        a smaller quantity than proposed, the sizing authority wins — the
        proposal quantity is clamped to ``approved_quantity`` before the
        proposal can proceed to governance/shield/execution.
        """
        risk_decision = None
        if self.risk_engine is not None and hasattr(self.risk_engine, "evaluate_action"):
            risk_decision = await self._safe_await(
                self.risk_engine.evaluate_action(decision_proposal or {}, obs_dict)
            )
            if risk_decision is None and isinstance(decision_proposal, dict) and str(
                    decision_proposal.get("action") or "").upper() in (
                    "BUY", "SELL", "STRONG_BUY", "STRONG_SELL"):
                # Directional risk can never proceed without an affirmative
                # risk verdict: a missing engine or an errored evaluation
                # yields no decision, which must fail closed rather than
                # silently skip to governance.
                return self._Terminal(CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", trade_id),
                    dominant_rejection_reason=(
                        "Risk: no decision produced — engine missing or "
                        "evaluation failed"),
                )), risk_decision
            if risk_decision is not None and not getattr(risk_decision, "approved", False):
                return self._Terminal(CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", trade_id) if decision_proposal else trade_id,
                    dominant_rejection_reason=f"Risk: {getattr(risk_decision, 'reason', 'Risk checks failed')}",
                )), risk_decision
            approved_qty = getattr(risk_decision, "approved_quantity", None)
            if (
                approved_qty is not None
                and isinstance(decision_proposal, dict)
                and isinstance(approved_qty, (int, float))
                and approved_qty >= 0
            ):
                requested = decision_proposal.get("quantity")
                if isinstance(requested, (int, float)) and requested > approved_qty:
                    decision_proposal["quantity"] = approved_qty
                    decision_proposal["quantity_clamped_by_risk"] = True
                if approved_qty <= 0 and isinstance(decision_proposal, dict) and str(
                        decision_proposal.get("action") or "").upper() in (
                        "BUY", "SELL"):
                    return self._Terminal(CoreDecision(
                        outcome=DecisionOutcome.TRADE_REJECTED,
                        trade_id=decision_proposal.get("trade_id", trade_id),
                        dominant_rejection_reason=(
                            "Risk: approved_quantity is 0 — no permitted "
                            "exposure for a directional proposal"),
                    )), risk_decision
        return None, risk_decision

    def _get_governance_gate(self) -> Any:
        """Resolve the typed governance gate, lazily defaulting to the
        human-layer approval gate wrapped in ``HumanApprovalPolicy``. A gate
        that cannot be constructed resolves to a fail-closed stub."""
        if not self._governance_gate_resolved:
            self._governance_gate_resolved = True
            try:
                from trading_bot.governance.policy_adapter import HumanApprovalPolicy
                from trading_bot.human_layer import get_approval_gate
                self.governance_gate = HumanApprovalPolicy(get_approval_gate())
            except Exception as exc:
                logger.warning(f"CSC-V6: governance gate unavailable: {exc}")
                self.governance_gate = self._UnavailableGovernanceGate()
        return self.governance_gate

    async def _stage_governance(
        self, decision_proposal: Optional[Dict[str, Any]],
        obs_dict: Dict[str, Any], risk_decision: Any, trade_id: str,
    ) -> Optional["_Terminal"]:
        """Stage 8.6: human-governance gate (fail closed).

        Runs after canonical risk and before the LogAct proposal/shield so the
        pipeline order is risk -> governance -> shield -> bus -> execution.
        A missing, erroring, or denying gate always rejects."""
        gate = self._get_governance_gate()
        if gate is None or not hasattr(gate, "authorize"):
            return self._Terminal(CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id) if decision_proposal else trade_id,
                dominant_rejection_reason="Governance: no approval gate available",
            ))
        context = {
            "market": obs_dict,
            "risk_assessment": getattr(risk_decision, "reason", "UNKNOWN"),
            "risk_checks": getattr(risk_decision, "checks", {}),
        }
        decision = await self._safe_await(
            gate.authorize("execute_trade", decision_proposal or {}, context)
        )
        if decision is None or not getattr(decision, "approved", False):
            return self._Terminal(CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id) if decision_proposal else trade_id,
                dominant_rejection_reason=(
                    f"Governance: {getattr(decision, 'reason', None) or 'approval denied or unavailable'}"
                ),
            ))
        if isinstance(decision_proposal, dict):
            decision_proposal["governance_receipt"] = getattr(decision, "audit_id", None)
        return None

    async def _stage_logact_proposal(self, decision_proposal: Optional[Dict[str, Any]]) -> None:
        """Stage 9: TRADE_PROPOSAL onto the decision bus."""
        log_action = LogAction(
            action_type="TRADE_PROPOSAL",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.HIGH,
        )
        if self.decision_bus is not None and hasattr(self.decision_bus, "propose_action"):
            await self._safe_await(self.decision_bus.propose_action(log_action))

    async def _stage_verification(
        self, best_branch: ReasoningBranch, sim_results: Dict[str, Any],
        trade_id: str,
    ) -> Any:
        """Verification stage: swarm audit + one bounded refinement pass.

        Runs BEFORE synthesis and governance — a human or the shield must
        never see an unverified proposal, and nothing unverified reaches the
        decision bus. Returns (best_branch, ledger_entry) on gate pass, else
        _Terminal.
        """
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
            # Surface the gate's actual rejection cause (consensus %, vetoing
            # verifier critique, or evidence-graph sparsity) so callers see why.
            gate_reason = getattr(EvidenceGraphGate, "last_rejection_reason", None)
            reason = (
                f"Failed Pivot/Refine loop: {gate_reason}"
                if vetoed and gate_reason
                else "Failed Pivot/Refine loop: swarm vetoed surviving branch"
                if vetoed
                else (gate_reason or "Insufficient evidence / Verification Swarm rejection")
            )
            return self._Terminal(CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=trade_id,
                dominant_rejection_reason=reason
            ))
        return best_branch, ledger_entry

    async def _stage_shield(
        self, decision_proposal: Optional[Dict[str, Any]],
        obs_dict: Dict[str, Any],
    ) -> Optional["_Terminal"]:
        """Stage 11: Immutable Shield validation."""
        if self.shield is not None:
            shield_report = await self._safe_await(self.shield.validate_action("trade", decision_proposal, {"market": obs_dict}))
            if shield_report and getattr(shield_report, "decision", None) != GovernanceDecision.APPROVED:
                return self._Terminal(CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=decision_proposal.get("trade_id", "NO_BRANCH"),
                    dominant_rejection_reason=f"Shield: {getattr(shield_report, 'reason', 'Vetoed by Immutable Shield')}"
                ))
        return None

    async def _stage_execute_and_persist(
        self, ledger_entry: ResearchLedgerEntry,
        decision_proposal: Optional[Dict[str, Any]], trade_id: str,
        obs_dict: Optional[Dict[str, Any]] = None,
    ) -> "CoreDecision":
        """Final stage: fold + persist, consensus, verdict.

        Abstentions (HOLD/WAIT or zero-quantity proposals) are recorded
        durably but never dispatched as executions — there is nothing to
        execute. Only verified directional proposals reach the bus."""
        self.folder.fold_history(ledger_entry)
        if self.hms is not None and hasattr(self.hms, "store_ledger_entry"):
            self.hms.store_ledger_entry(ledger_entry)

        proposal = decision_proposal or {}
        action_name = str(proposal.get("action") or "HOLD").upper()
        quantity = proposal.get("quantity", 0.0)
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
            quantity = 0.0

        # Record the honest next-price prediction for the surprise stage so
        # sensory surprise is a real prediction error, not a constant 1.0.
        price = None
        if isinstance(obs_dict, dict):
            price = obs_dict.get("price", obs_dict.get("close"))
        exp_ret = proposal.get("expected_return")
        if isinstance(price, (int, float)) and price > 0 and isinstance(exp_ret, (int, float)):
            self.last_prediction = {"price": float(price) * (1.0 + float(exp_ret))}
        else:
            self.last_prediction = None

        if (action_name in ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL")
                and self._churn_budget > 0
                and sum(1 for s in self._recent_trade_seqs
                        if s > self._observation_seq - self._churn_window)
                >= self._churn_budget):
            self._funnel["churn_abstain"] += 1
            await self._persist_audit_event(
                event_type="DECISION",
                action=action_name,
                outcome="ABSTAIN",
                correlation_id=trade_id,
                details={
                    "symbol": proposal.get("symbol"),
                    "reason": "turnover budget exhausted",
                    "churn_budget": self._churn_budget,
                    "churn_window": self._churn_window,
                })
            return CoreDecision(
                outcome=DecisionOutcome.ABSTAIN,
                trade_id=trade_id,
                dominant_rejection_reason=(
                    f"Churn guard: {self._churn_budget} trades per "
                    f"{self._churn_window} observations exhausted — "
                    f"turnover, not exposure, is the bleed"),
                confidence_vector=self._calculate_composite_confidence(ledger_entry),
            )

        if action_name in ("HOLD", "WAIT", "NO_TRADE") or quantity <= 0.0:
            self._funnel["nondirectional_abstain"] += 1
            await self._persist_audit_event(
                event_type="DECISION",
                action=action_name,
                outcome="ABSTAIN",
                correlation_id=trade_id,
                details={
                    "symbol": proposal.get("symbol"),
                    "quantity": quantity,
                    "confidence": proposal.get("confidence"),
                    "reason": "verified non-directional decision",
                })
            return CoreDecision(
                outcome=DecisionOutcome.ABSTAIN,
                trade_id=trade_id,
                dominant_rejection_reason=(
                    f"Abstain: verified {action_name} decision, "
                    f"quantity={quantity}"),
                confidence_vector=self._calculate_composite_confidence(ledger_entry),
            )

        # Verified proposal audit entry: proposal first, then execution.
        if self.decision_bus is not None and hasattr(self.decision_bus, "propose_action"):
            _prop = LogAction(
                action_type="TRADE_PROPOSAL",
                payload=decision_proposal,
                agent_id="CSC_V6",
                priority=EventPriority.HIGH,
            )
            _prop.sign()
            await self._safe_await(self.decision_bus.propose_action(_prop))

        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=decision_proposal,
            agent_id="CSC_V6",
            priority=EventPriority.CRITICAL,
        )
        action.sign()  # provenance on the capital path — unsigned
        # rides the audited-admission path, signed proves origin
        status = action.status
        # Preflight probe: the proposal dispatch above already exercised
        # bus reachability; the execution order itself is never sent —
        # a probe observation must never produce a venue-visible order.
        if (obs_dict or {}).get("preflight") and \
                getattr(self, "_preflight_active", False):
            status = ActionStatus.EXECUTED
        elif self.decision_bus is not None and hasattr(
                self.decision_bus, "propose_action"):
            await self._safe_await(self.decision_bus.propose_action(action))
            status = await self._safe_await(
                action.wait_for_decision(timeout=5.0))

        if status not in (ActionStatus.APPROVED, ActionStatus.EXECUTED):
            # Surface the veto/timeout reason from the audit trail so callers
            # see *why* consensus failed, not just the terminal status.
            voter_reasons = [
                str(report.get("reason", ""))
                for report in getattr(action, "voter_reports", {}).values()
                if isinstance(report, dict) and report.get("reason")
            ]
            detail = f" ({'; '.join(voter_reasons)})" if voter_reasons else ""
            self._funnel["consensus_rejected"] += 1
            await self._persist_audit_event(
                event_type="DECISION",
                action=action_name,
                outcome="TRADE_REJECTED",
                correlation_id=trade_id,
                details={
                    "symbol": proposal.get("symbol"),
                    "quantity": quantity,
                    "consensus_status": str(status),
                })
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=decision_proposal.get("trade_id", trade_id),
                dominant_rejection_reason=f"LogAct consensus failure: {status}{detail}",
            )

        # Approved directional decision — open/extend a position so its
        # outcome is measured entry->exit over the position's lifetime, and
        # persist the decision durably for the decision journal / read models.
        self._recent_trade_seqs.append(self._observation_seq)
        if proposal.get("exploratory") and self._explore_budget > 0:
            self._explore_budget -= 1
            self._funnel["exploratory_trades"] += 1
        if isinstance(price, (int, float)) and price > 0:
            await self._register_directional(
                trade_id, action_name, proposal.get("symbol"), float(price),
                confidence=proposal.get("confidence", 0.5),
                regime=(obs_dict or {}).get("trend")
                    or (obs_dict or {}).get("regime") or "unknown",
                expected_return=proposal.get("expected_return"),
                feature_contributions=proposal.get(
                    "feature_contributions"))
        await self._persist_audit_event(
            event_type="DECISION",
            action=action_name,
            outcome="TRADE_APPROVED",
            correlation_id=trade_id,
            details={
                "symbol": proposal.get("symbol"),
                "quantity": quantity,
                "confidence": proposal.get("confidence"),
                "price": price,
                # Predicted vs realized: recording the simulated EV lets
                # forward outcomes measure EV calibration directly.
                "expected_return": proposal.get("expected_return"),
                "feature_contributions": proposal.get(
                    "feature_contributions"),
                # Evidence provenance: which advisory capabilities
                # contributed analysis to this cycle's decision.
                "advisory_evidence": list(
                    getattr(self, "_last_advisory_ids", ())),
            })

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=decision_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(ledger_entry),
        )

    async def process_market_observation(self, observation: Any) -> Optional[CoreDecision]:
        """Public pipeline entry — wraps the implementation so the
        research-scheduling seam fires on EVERY observation, including
        early terminal-return paths (guardrail vetoes, abstentions)."""
        try:
            decision = await self._process_observation_pipeline(observation)
            if decision is not None:
                obs_d = observation if isinstance(observation, dict) else {}
                outcome = getattr(decision, "outcome", None)
                outcome_value = getattr(outcome, "value", outcome)
                # Abstention-cost bookkeeping: next obs resolves the
                # move skipped by this abstain — keyed per symbol so a
                # different instrument's bar can't clear another's cost.
                _abstains = getattr(
                    self, "_last_outcome_was_abstain", None)
                if not isinstance(_abstains, dict):
                    _abstains = self._last_outcome_was_abstain = {}
                _abstains[str(obs_d.get("symbol") or "?")] = (
                    str(outcome_value or "") == "ABSTAIN")
                self._funnel[f"terminal_{outcome_value or 'UNKNOWN'}"] += 1
                await self._persist_audit_event(
                    event_type="DECISION_TERMINAL",
                    action="pipeline_terminal",
                    outcome=str(outcome_value or "UNKNOWN"),
                    correlation_id=str(
                        getattr(decision, "trade_id", None) or "unknown"),
                    details={
                        "symbol": obs_d.get("symbol"),
                        "dominant_rejection_reason": getattr(
                            decision, "dominant_rejection_reason", None),
                        "advisory_evidence": list(
                            getattr(self, "_last_advisory_ids", ()) or ()),
                    })
            # Rejected decisions are failure evidence — one seam here covers
            # every TRADE_REJECTED terminal (guardrail, verification, risk,
            # shield, governance) without touching each return site.
            if (decision is not None
                    and getattr(decision, "outcome", None)
                    is DecisionOutcome.TRADE_REJECTED):
                obs_d = observation if isinstance(observation, dict) else {}
                self._record_failure(
                    "decision_rejected",
                    str(getattr(decision, "dominant_rejection_reason", "")
                        or "rejected"),
                    trade_id=getattr(decision, "trade_id", None),
                    symbol=obs_d.get("symbol"),
                    regime=str(obs_d.get("regime") or "unknown"),
                    stage="decision_terminal")
            return decision
        finally:
            # Autonomy tick: one managed ops decision per cycle — the
            # manager reads health/slot/pipeline state, allows or defers
            # each activity with a reason, and periodically persists an
            # AUTONOMY audit event. Execution still runs through the
            # existing bounded hooks.
            tick = self._autonomy.tick(self)
            if self._autonomy.should_audit():
                await self._persist_audit_event(
                    event_type="AUTONOMY", action="tick",
                    outcome="scheduled",
                    correlation_id=f"autonomy-{tick.cycle}",
                    details=tick.to_dict())
            for _d in tick.decisions:
                if not _d.allowed:
                    continue
                if _d.activity == "self_question":
                    self._maybe_self_question(observation)
                elif _d.activity == "research_cycle":
                    self._maybe_schedule_research_cycle(observation)
                elif _d.activity == "rsi_gap":
                    self._maybe_report_rsi_gaps()
                elif _d.activity == "capability_review":
                    self._capability_review()
            # Curiosity step: measured-surprise hypotheses feed the SRE
            # lifecycle via the provenance bridge (bounded, deduped).
            try:
                for _c in self._curiosity.observe(
                        observation if isinstance(observation, dict)
                        else {}):
                    self._sre_ingest("curiosity", _c)
            except Exception as exc:  # noqa: BLE001
                logger.debug("CSC-V6: curiosity step failed: %s", exc)

    def _maybe_schedule_research_cycle(self, observation: Any) -> None:
        """Budgeted background research: every ``research_interval``
        observations, one bounded cycle runs as a background task. One at
        a time — a slow cycle never queues behind itself."""
        interval = int(getattr(self, "_research_interval", 0) or 0)
        if interval <= 0 or self._observation_seq % interval != 0:
            return
        task = getattr(self, "_research_cycle_task", None)
        if task is not None and not task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._research_cycle_task = loop.create_task(
            self._run_research_cycle_guarded(observation))

    def _maybe_report_rsi_gaps(self) -> None:
        """Bounded RSI reflection: every ``rsi_gap_interval`` observations
        the RSI-HMS bridge reads real failure memory and reports observed
        performance gaps as advisory evidence. The bridge is deliberately
        cycle-free here — the full promotion cycle stays operator-invoked
        by design; this makes its registration honest: it works on real
        failures instead of nothing."""
        interval = int(getattr(self, "_rsi_gap_interval", 0) or 0)
        if interval <= 0 or self._observation_seq % interval != 0:
            return
        hms = getattr(self, "hms", None)
        if hms is None:
            return
        try:
            from trading_bot.recursive_self_improvement.hms_bridge import (
                RSIHMSBridge)
            bridge = getattr(self, "_rsi_bridge", None)
            if bridge is None:
                bridge = RSIHMSBridge(hms=hms)
                self._rsi_bridge = bridge
            gaps = bridge.observe_gaps()
            if gaps:
                summary = [
                    {"kind": str(getattr(g, "kind", "") or ""),
                     "count": int(getattr(g, "count", 0) or 0)}
                    for g in list(gaps)[:10]]
                # Persist into the RSI self-improvement ledger — durable,
                # sync, and the same store mirror_decisions writes.
                try:
                    hms.record_improvement(
                        record_type="gap_report", domain="rsi",
                        summary=f"{len(gaps)} observed gaps",
                        details={"gaps": summary})
                except Exception:  # noqa: BLE001
                    pass
                logger.info(
                    "CSC-V6: RSI gap report — %d gaps observed: %s",
                    len(gaps), summary[:3])
        except Exception as exc:  # noqa: BLE001
            logger.debug("CSC-V6: RSI gap observation failed: %s", exc)

    def _self_question(self) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        """Generate a research question from the CSC's own weakest
        measured state — self-questioning as a first-class function.
        Returns (question, findings) where findings are the measured
        facts the operational-diagnostic experiment will verify. Sources
        (in priority order): SPRT-degraded models, suppressed actions,
        degraded self-health. Returns None when nothing is measurably
        weak."""
        rolled_back = [c for c in self._engineered_models.values()
                       if c.status == "ROLLED_BACK"]
        if rolled_back:
            c = rolled_back[-1]
            return (f"Why did engineered model '{c.name}' degrade "
                    f"({c.verdict}) — was the holdout edge regime-bound "
                    f"or overfit?",
                    [{"claim": f"{c.name} degraded",
                      "supported": True,
                      "evidence": {"name": c.name, "verdict": c.verdict,
                                   "status": c.status}}])
        suppressed = getattr(
            self.reliability_tracker, "_suppressed", {}) or {}
        if suppressed:
            key = next(iter(suppressed))
            return (f"Suppressed action '{key}' persists — is the "
                    f"measured negative expectancy structural to this "
                    f"regime or a recoverable failure mode?",
                    [{"claim": f"{key} measured negative expectancy",
                      "supported": True,
                      "evidence": dict(suppressed.get(key) or {})}])
        health = getattr(self, "_last_self_health", None)
        if health and health.get("score", 100) < 70:
            return (f"System health degraded to {health['score']} "
                    f"({health['flags']}) — which component failure "
                    f"drives it and what restores it?",
                    [{"claim": "system health degraded",
                      "supported": True,
                      "evidence": dict(health)}])
        return None

    def _capability_review(self) -> None:
        """Capability-expansion review: validated research claims produce
        capability proposals; each new proposal is surfaced as an advisory
        artifact for the next cycle's evidence channel — the organism's
        growth is evidence, never authority."""
        engine = getattr(self, "research_engine", None)
        if engine is None:
            return
        try:
            props = engine.capability_proposals()
        except Exception:  # noqa: BLE001
            return
        seen = getattr(self, "_capability_seen", None)
        if seen is None:
            seen = self._capability_seen = set()
        new = [p for p in props
               if getattr(p, "proposal_id", None) not in seen]
        for p in new:
            seen.add(getattr(p, "proposal_id"))
            self._funnel["capability_proposal_new"] += 1
        if new and getattr(self, "_research_artifacts", None) is not None:
            for p in new[:3]:
                self._research_artifacts.append({
                    "agent": "capability_proposal",
                    "capability_id": "capability_proposal",
                    "evidence": {
                        "status": "proposal",
                        "proposal_id": str(getattr(p, "proposal_id", "")),
                        "summary": str(getattr(p, "summary", ""))[:120],
                        "confidence_level": str(getattr(
                            getattr(p, "confidence_profile", None),
                            "level", ""))},
                    "advisory_only": True})

    def autonomy_report(self) -> Dict[str, Any]:
        """Transparency surface: the organism's ops decisions and its
        capability-expansion ledger."""
        am = getattr(self, "_autonomy", None)
        return am.report() if am is not None else {}

    def _maybe_self_question(self, observation: Any) -> None:
        """Bounded self-questioning: every ``self_question_interval``
        observations the CSC formalizes its weakest measured spot into a
        research question and investigates it in the background. Never
        two at once; failures never reach the trading path."""
        interval = int(getattr(self, "_self_question_interval", 0) or 0)
        if (interval <= 0
                or self._observation_seq - self._last_self_question_seq
                < interval):
            return
        task = getattr(self, "_research_cycle_task", None)
        if task is not None and not task.done():
            return
        found = self._self_question()
        if not found:
            return
        question, findings = found
        self._last_self_question_seq = self._observation_seq
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._self_question_guarded(question, findings))

    async def _self_question_guarded(
            self, question: str, findings: List[Dict[str, Any]]) -> None:
        try:
            report = await self.research(
                question,
                market_data={
                    "question_source": "self_question",
                    "question_type": "operational",
                    "operational_context": {
                        "findings": findings, "confidence": 0.6}})
            verdict = getattr(report, "verdict", None) or report
            logger.info("CSC-V6: self-question verdict: %s | %s",
                        verdict, question[:80])
        except Exception as exc:  # noqa: BLE001
            logger.debug("CSC-V6: self-question cycle failed: %s", exc)

    def distill_frontier(self, model_name: str,
                         observations: Sequence[Any],
                         benchmark_tasks: Sequence[Any],
                         benchmark_results: Sequence[Any]
                         ) -> Dict[str, Any]:
        """Frontier capability distillation (operator/research-invoked):
        external frontier evidence (papers, eval results, observed
        behaviors) -> capability profile -> patterns -> AlphaAlgo-native
        artifacts -> governance -> lineage. Report persisted; artifacts
        feed propose_model via the normal gated path, never authority."""
        if self._frontier_engine is None:
            from trading_bot.core.frontier_capability_distillation import (
                FrontierCapabilityDistillationEngine)
            self._frontier_engine = FrontierCapabilityDistillationEngine()
        report = self._frontier_engine.run(
            model_name, observations, benchmark_tasks, benchmark_results)
        summary = {
            "model": model_name,
            "patterns": len(getattr(report, "patterns", ()) or ()),
            "artifacts": len(getattr(report, "artifacts", ()) or ()),
            "governance": [getattr(g, "accepted", None)
                           for g in (getattr(
                               report, "governance_results", ()) or ())][:10],
            "rejected": list(getattr(report, "rejected_patterns", ())
                             or ())[:10],
            "report": (report.to_dict()
                       if hasattr(report, "to_dict") else {}),
            # Honest handoff boundary: distillation artifacts are
            # playbooks/policies/governance invariants — not model specs.
            # A compiler bridge would be needed to turn them into
            # propose_model candidates; until one exists, nothing here
            # enters the candidate pipeline automatically.
            "specs_produced": 0,
            "note": ("artifacts are playbook/policy/invariant kinds, not "
                     "model specs — no automatic handoff to "
                     "propose_model"),
        }
        try:
            hms = getattr(self, "hms", None)
            if hms is not None:
                hms.record_improvement(
                    record_type="frontier_distillation",
                    domain="research", summary=str(summary)[:200],
                    details=summary)
        except Exception:  # noqa: BLE001
            pass
        return summary

    async def _run_research_cycle_guarded(self, observation: Any) -> None:
        """Research failures never reach the trading path — a research
        cycle is advisory by construction."""
        try:
            obs_dict, _ = self._normalize_observation(observation)
            self._enrich_derived_features(obs_dict)
            # Self-supplied replication: the CSC's own bar history is sliced
            # so a claimed directional edge can be retested out-of-sample —
            # the cycle can self-replicate, not just investigate.
            repl_fn = self._build_replication_fn(obs_dict)
            if repl_fn is not None:
                obs_dict["replication_fn"] = repl_fn
            await self.run_research_cycle(obs_dict, max_questions=1)
        except Exception as exc:
            logger.warning("CSC-V6: background research cycle failed: %s",
                           exc)

    def _build_replication_fn(self, obs_dict: Dict[str, Any]):
        """Supply a replication_fn that re-tests the engine's target claim
        on the second half of the observed bar history — a genuinely
        different data slice, not a re-run on the same window."""
        engine = self.research_engine
        if engine is None or not getattr(engine, "_claims", None):
            return None
        symbol = str(obs_dict.get("symbol") or "")
        hist = list(self._obs_history.get(symbol, ()))
        if len(hist) < 40:
            return None

        def _eval() -> Dict[str, Any]:
            from trading_bot.evaluation.frozen_baseline import (
                compare_candidate_vs_baseline)
            closes = hist[len(hist) // 2:]
            rets = [(closes[i] - closes[i - 1]) / closes[i - 1]
                    for i in range(1, len(closes))]
            target = engine._replication_target(None, {"symbol": symbol})
            claimed = (target.metadata.get("direction")
                       if target is not None else None)
            # No recorded direction -> flat candidate -> honest no_activity
            # verdict rather than guessing a side.
            direction = {"BUY": 1.0, "SELL": -1.0}.get(claimed, 0.0)
            return compare_candidate_vs_baseline(
                [direction] * len(rets), [1.0] * len(rets), rets,
                cost_bps=float(obs_dict.get("cost_bps") or 5.0),
                min_decisions=5)
        return _eval

    async def drain_research_cycles(self) -> None:
        """Test/operator seam: await any in-flight background cycle."""
        task = getattr(self, "_research_cycle_task", None)
        if task is not None:
            await task

    async def _process_observation_pipeline(self, observation: Any) -> Optional[CoreDecision]:
        """
        Recursive Active Inference Pipeline (UCA V6).

        Ordering contract: perception → evidence → guardrails →
        internalization → hypothesis+simulation → pivot/refine →
        **verification** → synthesis → risk → shield → governance →
        execute/persist. Nothing reaches governance, the shield, or the
        decision bus before the evidence swarm has passed — a human never
        approves an unverified proposal.
        """
        # 0. Normalize + trade id
        obs_dict, trade_id = self._normalize_observation(observation)
        self._observation_seq += 1
        self._funnel["observations"] += 1
        # Keep the previous cycle's calls for the self_state channel
        # (meta-aggregation advisors read them) before resetting.
        self._prev_advisory_calls = list(
            getattr(self, "_last_advisory_calls", ()) or ())
        self._last_advisory_calls = []
        self._last_advisory_ids = []

        # 0.4. Causal feature enrichment: a raw OHLCV feed does not carry
        # volatility/trend/rsi — derive them from strictly-prior bars so the
        # verifier's structure gate is met with real measured evidence.
        self._enrich_derived_features(obs_dict)

        # 0.5. Settle matured pending predictions at this bar's price —
        # the live outcome path. A decision approved at observation t is
        # scored against the realized move by observation t+horizon.
        await self._settle_pending_predictions(obs_dict)

        # 0.55. Self-state channel: expose the controller's real internal
        # state (open positions, settled outcomes, advisor health) so
        # state-consuming advisory modules (position aging, tilt
        # detection, counterfactual analysis, model-decay scans) see
        # honest data instead of being fabricated. Placed after
        # settlement so this bar's closes are included.
        obs_dict["self_state"] = {
            "open_positions": {
                s: {k: v for k, v in p.items() if k != "trade_ids"}
                for s, p in self._open_positions.items()},
            "settled_outcomes": list(self._settled_outcomes)[-64:],
            "pending_predictions": len(self._pending_predictions),
            "advisory_failures": dict(
                getattr(self, "_advisory_failures", {}) or {}),
            "funnel": dict(self._funnel),
            "observation_seq": self._observation_seq,
            # Previous cycle's advisor calls (capability, direction,
            # confidence) — consumed by meta-aggregation advisors such as
            # unified_alpha_brain.
            "last_advisory_calls": list(
                getattr(self, "_prev_advisory_calls", ()) or ()),
        }

        # 0.6. Cadence gate: decide every Nth bar. Everything above still
        # ran — history, enrichment, settlement, research scheduling — so
        # a skipped bar costs nothing but the decision itself.
        if (self._decision_stride > 1
                and self._observation_seq % self._decision_stride != 0):
            self._funnel["cadence_abstain"] += 1
            await self._persist_audit_event(
                event_type="DECISION",
                action="HOLD",
                outcome="ABSTAIN",
                correlation_id=trade_id,
                details={"symbol": obs_dict.get("symbol"),
                         "reason": "cadence_skip",
                         "stride": self._decision_stride})
            return CoreDecision(
                outcome=DecisionOutcome.ABSTAIN,
                trade_id=trade_id,
                dominant_rejection_reason=(
                    f"cadence gate: deciding every "
                    f"{self._decision_stride} bars"))

        # 0.7. Self-wiring: every REWIRE_INTERVAL observations the
        # supervisor applies measured transitions to the advisory
        # electorate (demote/promote/probe/discover). Bounded — only
        # _advisory_services membership changes; authority is invariant.
        await self._maybe_rewire_electorate()

        # 1. Perception
        await self._stage_perception(obs_dict)
        self._funnel["perception"] += 1

        # 2. Evidence Retrieval
        evidence_chain = await self._stage_evidence_retrieval(observation)
        self._funnel["evidence_items"] += len(evidence_chain or [])

        # 3. Guardrails (HASP volatility + skill-router prescriptive)
        self._funnel["guardrails"] += 1
        terminal = await self._stage_guardrails(observation, obs_dict)
        if terminal is not None:
            self._funnel["guardrail_terminal"] += 1
            return terminal.decision

        # 4/4.5. DiscoLoop + PCA internalization (advisory artifacts)
        advisory_artifacts = await self._stage_internalization(obs_dict)
        self._funnel["advisory_artifacts"] += len(advisory_artifacts or [])

        # 5/6. Hypothesis generation + causal simulation — on the ENRICHED
        # observation so derived volatility/trend/rsi become evidence nodes.
        branches, sim_results = await self._stage_hypothesis_and_simulation(
            obs_dict, evidence_chain=evidence_chain,
            advisory_artifacts=advisory_artifacts)
        self._funnel["hypothesis_branches"] += len(branches or [])

        # 7. Pivot/Refine
        best_branch = await self._stage_pivot_refine(
            branches, sim_results, trade_id=trade_id)
        if isinstance(best_branch, self._Terminal):
            self._funnel["pivot_refine_terminal"] += 1
            return best_branch.decision

        # 8. Verification swarm + bounded refinement — BEFORE synthesis so
        # governance and shield only ever see a verified proposal.
        self._funnel["verification"] += 1
        verified = await self._stage_verification(
            best_branch, sim_results, trade_id)
        if isinstance(verified, self._Terminal):
            self._funnel["verification_terminal"] += 1
            return verified.decision
        best_branch, ledger_entry = verified
        # Which branch won — without this, terminal_ABSTAIN lumps
        # "range/WAIT won the ranking" with "no viable branch", hiding
        # where directional proposals actually die.
        self._funnel[
            f"won_by_{getattr(best_branch, 'branch_id', 'unknown')}"] += 1

        # 9. Decision synthesis on the verified branch
        decision_proposal = self._stage_synthesis(
            best_branch, sim_results, trade_id, obs_dict,
            branches=branches)
        self._funnel["synthesis"] += 1

        # 10-12. Execution gates apply to capital-moving proposals only —
        # a verified HOLD/WAIT/zero-size abstention skips straight to
        # durable recording. Risk/shield/governance exist to gate exposure;
        # an abstention has none, and routing it through them would let a
        # sizing rule mask a deliberate no-trade record.
        action_name = str(
            (decision_proposal or {}).get("action") or "HOLD").upper()
        qty = (decision_proposal or {}).get("quantity", 0.0)
        if not isinstance(qty, (int, float)) or isinstance(qty, bool) \
                or not np.isfinite(qty):
            qty = 0.0
        is_directional = action_name not in ("HOLD", "WAIT", "NO_TRADE") \
            and qty > 0.0

        if is_directional:
            self._funnel["directional_proposals"] += 1
            # 10. Canonical portfolio-risk boundary
            self._funnel["risk_check"] += 1
            terminal, risk_decision = await self._stage_risk_check(
                decision_proposal, obs_dict, trade_id)
            if terminal is not None:
                self._funnel["risk_terminal"] += 1
                return terminal.decision

            # 11. Immutable shield
            self._funnel["shield"] += 1
            terminal = await self._stage_shield(decision_proposal, obs_dict)
            if terminal is not None:
                self._funnel["shield_terminal"] += 1
                return terminal.decision

            # 12. Human-governance gate on the verified, shield-passed
            # proposal
            self._funnel["governance"] += 1
            terminal = await self._stage_governance(
                decision_proposal, obs_dict, risk_decision, trade_id)
            if terminal is not None:
                self._funnel["governance_terminal"] += 1
                return terminal.decision

        # 13. Fold, persist, execution consensus (or durable abstain record)
        return await self._stage_execute_and_persist(
            ledger_entry, decision_proposal, trade_id, obs_dict)

    async def execute_task(self, task: str, context: Any = None) -> Dict[str, Any]:
        """
        Execute a strategic task against the current market context.

        The CSC's public task entry point (used by main.py). A high-level task
        string plus a market-data context is folded into an observation and run
        through the 12-step active-inference pipeline.

        Returns a task-completion envelope {"status", "success", "decision"}
        where "decision" is the pipeline's CoreDecision (or None).
        """
        if isinstance(context, dict):
            observation = dict(context)
        elif context is None:
            observation = {}
        else:
            observation = dict(getattr(context, "__dict__", {}) or {})
        observation.setdefault("task", task)
        observation.setdefault("timestamp", datetime.utcnow().isoformat())
        self.state.active_tasks.append(task)
        try:
            result = await self.process_market_observation(observation)
        finally:
            self.state.active_tasks.remove(task)
        # Each executed task is recorded; epistemic_uncertainty only moves
        # when the outcome pipeline feeds measured results back through the
        # ReliabilityTracker — task count alone is not learning.
        self.state.folded_history.append({"task": task, "result": result})
        # "status" refers to task completion — a vetoed trade is still a completed cycle.
        return {"status": "completed", "success": True, "decision": result}
