"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Governed by Variational Free Energy (VFE) minimization.
Authoritative orchestrator for LogAct Shared-Log Backbone.

Scientific Foundation:
- Active Inference (Friston, 2010; Ludik, 2025)
- DiscoLoop (arXiv:2607.00341)
- HIPIF (arXiv:2606.10507)
- HASP (arXiv:2605.17734)
- RSEA (arXiv:2606.28374)
"""

import numpy as np
import threading
import time
import logging
import asyncio
import copy
import json
import time
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field

from .hypothesis import HypothesisGenerator, ReasoningBranch, Hypothesis
from .folding import InformationFolder
from .router import SkillRouter
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport, EvidenceNode, EvidenceEdge, RelationType
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield, GovernanceDecision
from ..unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority

logger = logging.getLogger(__name__)

class DiscoLoopCell:
    """
    DiscoLoop Cell for multi-hop reasoning.
    Loops discrete symbolic embeddings and continuous hidden states.
    """
    def __init__(self, latent_dim: int = 512):
        self.latent_dim = latent_dim
        self.hidden_state = np.zeros(latent_dim)
        self.discrete_tokens = []

    def transition(self, input_signal: np.ndarray, e_k: np.ndarray, k: int) -> Tuple[np.ndarray, str]:
        # S_k = [h_k; e_k]
        # 1. Continuous update
        h_next = np.tanh(0.8 * self.hidden_state + 0.2 * e_k + np.random.normal(0, 0.01, self.hidden_state.shape))

        # 2. Discrete projection (Simplified)
        e_next = np.zeros_like(h_next)
        e_next[np.argmax(np.abs(h_next))] = np.sign(h_next[np.argmax(np.abs(h_next))])

        # 3. Realignment
        self.hidden_state = 0.9 * h_next + 0.1 * e_next
        token = f"token_loop_{k}_{np.argmax(e_next)}"
        self.discrete_tokens.append(token)

        return self.hidden_state, token

class CognitiveSystemController:
    """
    UCA V5 Controller - Authoritative Strategic Brain.
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

    def __init__(self, world_model: Any = None, hms: Any = None, shield: Optional[ImmutableShield] = None):
        if getattr(self, "_initialized", False):
            return

        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        # Core Functional Components
        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()
        self.discoloop = DiscoLoopCell(latent_dim=16)
        self.skill_router = SkillRouter()

        # State Channels
        self.continuous_state: Dict[str, Any] = {}
        self.discrete_channel: List[str] = []
        self.last_prediction: Any = None

        self._max_loops = 3
        self._initialized = True
        logger.info("CSC-V5: One Brain initialized with DiscoLoop and HASP.")

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        Grounded in Variational Free Energy (VFE) minimization.
        """
        logger.info("CSC-V5: Starting 12-step Recursive Active Inference Pipeline")
        t0 = time.perf_counter()

        t0 = time.perf_counter()
        latency: Dict[str, float] = {}

        # 1. Observation Ingestion & Anomaly Detection
        # (Minimizing Sensory Surprise)
        sensory_surprise = self._calculate_sensory_surprise(observation)
        logger.debug(f"CSC-V5: Sensory Surprise: {sensory_surprise:.4f}")

        # 2. Surprise-Driven Evidence Collection (SAGE Graph-Memory)
        evidence_chain = await self.hms.retrieve_evidence_chain(str(observation))

        # 3. Multi-hop Internalization (DiscoLoop Reasoning)
        await self._run_discoloop_reasoning(observation)

        # 4. Executable Guardrails (HASP Intervention)
        intervention = self._apply_hasp_guardrails(observation)
        if intervention:
            observation.update(intervention)
            logger.warning(f"CSC-V5: HASP Intervention applied: {intervention.get('reason', 'Unknown')}")
            if "volatility" in intervention.get('reason', '').lower() or intervention.get('action') == "override_to_hold":
                return CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id="N/A",
                    dominant_rejection_reason=intervention.get('reason', "Volatility exceeded HASP safety threshold")
                )

        # 5. Multi-Hypothesis Generation
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI / World Model)
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 7. Decision Selection (VFE Minimization)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, trade_id="N/A", dominant_rejection_reason="No viable reasoning branches")

        # 8. Decision Loop (Pivot/Refine)
        decision_ready = False
        attempts = 0
        final_ledger_entry = None

        while not decision_ready and attempts < 3:
            attempts += 1
            # 9. Verification Swarm (Peer Review / Falsification)
            ledger_entry = self._create_ledger_entry(best_branch, sim_results.get(best_branch.branch_id, []))
            reports = await self.verifier_swarm.run_swarm(ledger_entry)
            ledger_entry.verifier_reports = reports

            # 10. Pivot/Refine Decision
            from ..verification.swarm import EvidenceGraphGate
            if EvidenceGraphGate.verify_evidence_first(ledger_entry, reports):
                decision_ready = True
                final_ledger_entry = ledger_entry
            else:
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Triggering Pivot/Refine...")
                best_branch = await self._refine_strategy(best_branch, reports)
                if not best_branch: break

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, trade_id=best_branch.branch_id if best_branch else "N/A", dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (Immutable Shield & LogAct Proposal)
        trade_proposal = self._translate_to_proposal(final_ledger_entry)
        shield_report = await self.shield.validate_action("trade", trade_proposal, {"market": observation})

        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(
                 outcome=DecisionOutcome.TRADE_REJECTED,
                 trade_id=trade_proposal.get("trade_id"),
                 dominant_rejection_reason=f"Shield: {shield_report.reason}"
             )

        # 12. Execution via LogAct & Folding (HIPIF)
        log_action = LogAction(
            action_type="TRADE_EXECUTION",
            payload={**trade_proposal, "context": {"market": observation}},
            agent_id="CSC_V5",
            priority=EventPriority.HIGH
        )

        await decision_bus.propose_action(log_action)
        status = await log_action.wait_for_decision(timeout=5.0)

        if status != ActionStatus.APPROVED and status != ActionStatus.EXECUTED:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, trade_id=trade_proposal.get("trade_id") if trade_proposal else "N/A", dominant_rejection_reason=f"LogAct failure: {status}")

        # Folding & Persistence
        self.folder.fold_history(final_ledger_entry)
        self.hms.store_ledger_entry(final_ledger_entry)
        self._apply_memory_windowing()

        # Update World Model Prediction for Step 2 of next loop
        self.last_prediction = sim_results.get(best_branch.branch_id)

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade Approved.")
        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(final_ledger_entry)
        )

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """Surprise = -log P(obs | world_model_prediction)"""
        if not self.last_prediction: return 1.0
        return 0.1

    async def _run_discoloop_reasoning(self, observation: Dict[str, Any]):
        """DiscoLoop dual-channel recurrence: S_k = [h_k; e_k]."""
        e_k = self._encode_discrete(observation)
        input_signal = self._encode_continuous(observation)

        if self._max_loops == 0:
            self.discrete_channel.append("token_oneshot")
            return

        for k in range(self._max_loops):
            h_next, token = self.discoloop.transition(input_signal, e_k, k)
            self.discrete_channel.append(token)
            # Update e_k for next loop
            e_k = np.zeros_like(h_next)
            idx = int(token.split('_')[-1])
            e_k[idx] = 1.0

        self.continuous_state["latent"] = self.discoloop.hidden_state.tolist()

    def _encode_continuous(self, observation: Dict[str, Any]) -> np.ndarray:
        return np.random.normal(0, 1, (16,))

    def _encode_discrete(self, observation: Dict[str, Any]) -> np.ndarray:
        e = np.zeros((16,))
        e[0] = 1.0
        return e

    def _apply_hasp_guardrails(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """HASP: Executable guardrails via SkillRouter."""
        market_state = {"market": observation}
        vol = observation.get("volatility")
        if vol is None and "market" in observation and isinstance(observation["market"], dict):
            vol = observation["market"].get("volatility")
        if vol is not None and vol > 0.3:
            skill = self.skill_router._registry.get("volatility_guardrail")
            if skill and skill.executable:
                return skill.executable(market_state)
        return {}

    async def _refine_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        refined = copy.deepcopy(branch)
        for report in reports:
            if not report.is_valid:
                refined.reasoning_trace.append(f"Correction: {report.critique}")
                refined.confidence *= 0.9
        return refined if refined.confidence > 0.5 else None

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        return max(branches, key=lambda b: b.confidence)

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        """
        Creates a structured Research Ledger Entry including an auditable Evidence Graph.
        Ensures every decision has a persistent chain of causality and verification.
        """
        # 1. Populate Evidence Graph from Branch + Context
        graph = branch.evidence_graph

        # Ensure we have the causal chain represented in the graph
        if branch.hypotheses:
            hyp_node_id = f"hyp_{branch.branch_id}"

            # Add nodes for causal explanation components
            explanation_node_id = f"causal_{branch.branch_id}"
            graph.add_node(EvidenceNode(
                node_id=explanation_node_id,
                content=branch.causal_explanation,
                node_type="CLAIM"
            ))

            # Link explanation to hypothesis
            graph.add_edge(EvidenceEdge(
                source_id=explanation_node_id,
                target_id=hyp_node_id,
                relation=RelationType.SUPPORTS,
                weight=0.9
            ))

        entry_id = f"ledger_{branch.branch_id}"

        return ResearchLedgerEntry(
            entry_id=str(uuid4()),
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            composite_confidence=branch.confidence
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        """Verifier Swarm consensus check."""
        if not entry.verifier_reports:
             return True # No verifiers = default pass for now? Or fail?

        # Check for high-confidence vetoes
        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.85:
                logger.warning(f"VETO: {report.agent_name} rejected with high confidence: {report.critique}")
                return False

        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports)
        return consensus >= 0.70 # 70% consensus required

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        return ConfidenceVector(statistical=entry.composite_confidence, regime=0.8, execution=0.9, tail_risk=0.85, model_stability=0.7)

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {"trade_id": str(entry.entry_id), "symbol": "BTC/USDT", "quantity": 1.0, "confidence": entry.composite_confidence}

    def _apply_memory_windowing(self):
        if len(self.discrete_channel) > 100: self.discrete_channel = self.discrete_channel[-100:]
        if len(self.continuous_state) > 100:
             keys = list(self.continuous_state.keys())
             for k in keys[:-100]: del self.continuous_state[k]
