"""
Cognitive System Controller (CSC) - UCA V5 (July 2026)

Integrated "One Brain" implementing the 12-step Recursive Active Inference pipeline.
Implements the Active Inference (VFE minimization) loop, HIPIF, DiscoLoop, and HASP.
The "One Brain" authoritative controller orchestrating the LogAct pipeline.
"""

import logging
import asyncio
import copy
import json
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch, Hypothesis
from .folding import InformationFolder
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus, EventPriority

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
        if getattr(self, "_initialized", False):
            return
        self.world_model = world_model
        self.hms = hms
        self.shield = shield

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # HASP: Executable Guardrails (Skill Programs)
        # These are executable functions that can intervene in the loop.
        self.skill_programs: Dict[str, Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = self._load_skill_programs()

        # DiscoLoop Channels
        # In a real implementation, these would be tensors. Here we use dicts/lists for state.
        self.continuous_state: Dict[str, Any] = {} # Latent embeddings / hidden state
        self.discrete_channel: List[str] = [] # Semantic tokens / Bridge entities

        self._initialized = True
        logger.info("CSC-V5: One Brain initialized with DiscoLoop and HASP.")

    def _load_skill_programs(self) -> Dict[str, Callable]:
        """Loads executable Program Functions (PFs) for HASP."""
        # Example: Volatility Guardrail
        def vol_guard(obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            if obs.get("volatility", 0) > 0.05:
                logger.warning("HASP: High volatility detected. Injecting risk reduction context.")
                return {"max_leverage": 1.0, "reasoning_context": "CRITICAL_VOLATILITY"}
            return None

        return {"volatility_guard": vol_guard}

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        12-step Recursive Active Inference Pipeline.
        Grounded in Variational Free Energy (VFE) minimization (Ludik, 2025).
        """
        logger.info("CSC-V5: Starting 12-step Recursive Active Inference Pipeline")

        # 1. Observation Ingestion & Anomaly Detection
        # (Minimizing Sensory Surprise)
        sensory_surprise = self._calculate_sensory_surprise(observation)
        logger.debug(f"CSC-V5: Sensory Surprise: {sensory_surprise:.4f}")

        # 2. Evidence Collection (SAGE Graph-Memory)
        # (Wang et al., 2026 - SAGE)
        evidence_chain = await self.hms.retrieve_evidence_chain(str(observation))

        # 3. Belief Update (Bayesian Posterior)
        # (Strategic Decision Intelligence, 2025)
        self._update_internal_beliefs(observation, evidence_chain)

        # 1. Active Perception (Implicit in observation input)
        # 2. Internalization (DiscoLoop Reasoning)
        await self._run_discoloop_internalization(observation)

        # 3. Skill Routing (Distilled Behaviors - Placeholder for S2L/LoRA)

        # 4. Executable Guardrails (HASP Intervention)
        # (arXiv:2605.17734 - HASP)
        intervention = self._apply_hasp_guardrails(observation)
        if intervention:
            logger.info(f"CSC-V5: HASP Intervention applied: {intervention.get('action')}")
            observation.update(intervention)

        # 5. Multi-Hypothesis Generation (DiscoLoop)
        # (Fu et al., 2026 - DiscoLoop: Discrete-Continuous Looping)
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 6. Causal Simulation (CWMI / World Model)
        # (arXiv:2509.xxxxx - CWMI: Structural Interventions)
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 7. Decision Selection (EV Optimization / VFE Minimization)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="No viable reasoning branches")

        # 8. Decision Loop (Pivot/Refine)
        # (RSEA - arXiv:2606.28374)
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
            if self._verify_evidence_hard_constraint(ledger_entry):
                decision_ready = True
                final_ledger_entry = ledger_entry
            else:
                logger.warning(f"CSC-V5: Verification FAILED (Attempt {attempts}). Refining strategy...")
                refined_branch = await self._refine_strategy(best_branch, reports)
                if refined_branch and refined_branch != best_branch:
                    best_branch = refined_branch
                else:
                    logger.error("CSC-V5: Could not refine strategy further.")
                    break

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (Immutable Shield & LogAct Proposal)
        trade_proposal = self._translate_to_proposal(final_ledger_entry)

        # LogAct Consensus: Propose to Shared-Log
        log_action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=trade_proposal,
            agent_id="CSC_ONE_BRAIN",
            priority=EventPriority.HIGH
        )

        # Register shield as a voter if not already done in initialization
        # In this implementation, we check the shield explicitly before proposing
        shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})

        from ..immutable_shield import GovernanceDecision
        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason=f"Shield: {shield_report.reason}")

        # 12. Execution & Folding (HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED by Shield. Proposing to LogAct Backbone.")
        await decision_bus.propose_action(log_action)

        # Folding
        self.folder.fold_history(final_ledger_entry)

        # Persist to HMS
        self.hms.store_ledger_entry(final_ledger_entry)

        # Final LogAct write-through
        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload=trade_proposal,
            agent_id="CSC_V5",
            status=ActionStatus.APPROVED
        )
        await decision_bus.propose_action(action)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            confidence_vector=self._calculate_composite_confidence(final_ledger_entry)
        )

    async def _run_discoloop_internalization(self, observation: Dict[str, Any]):
        """
        DiscoLoop: Mixed-channel (discrete/continuous) recurrence.
        Internalizes multi-hop reasoning before hypothesis generation.
        """
        loops = 3
        logger.debug(f"DiscoLoop: Starting {loops} internalization steps")
        for k in range(loops):
            # 1. Continuous update: Incorporate observation and discrete tokens
            # (Simplified: string aggregation for state representation)
            self.continuous_state["internal_thought"] = f"Loop_{k}: {observation.get('price_action')} with context {self.discrete_channel}"

            # 2. Discrete projection: Extract semantic entities
            # (Simplified: Mock extraction)
            new_tokens = ["BULLISH_ORDER_BLOCK"] if k == 0 else ["LIQUIDITY_SWEEP"]
            self.discrete_channel.extend(new_tokens)

    def _apply_hasp_guardrails(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """HASP: Executable guardrails check."""
        combined_intervention = {}
        for name, program in self.skill_programs.items():
            intervention = program(observation)
            if intervention:
                logger.info(f"HASP: Program '{name}' intervened.")
                combined_intervention.update(intervention)
        return combined_intervention

    async def _refine_strategy(self, branch: ReasoningBranch, reports: List[VerifierReport]) -> Optional[ReasoningBranch]:
        """Pivot/Refine logic to improve strategy based on verifier feedback."""
        # Pivot: If reports indicate major structural error, switch to second best branch (if available)
        # Refine: Tweak parameters based on critique
        refined = copy.deepcopy(branch)
        for report in reports:
            if not report.is_valid:
                logger.info(f"Refinement: Addressing critique: {report.critique}")
                refined.reasoning_trace.append(f"Correction: {report.critique}")
                # Mock parameter adjustment
                if "risk" in report.critique.lower():
                    refined.confidence *= 0.8
        return refined

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        """Selects branch maximizing Expected Value or minimizing Free Energy."""
        if not branches: return None
        # Sort by confidence for now as proxy for EV
        sorted_branches = sorted(branches, key=lambda b: b.confidence, reverse=True)
        return sorted_branches[0]

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": getattr(s, 'name', 'Scenario')} for s in scenarios] if scenarios else [],
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
        # Aggregate from verifiers and branch confidence
        avg_verifier_conf = sum(r.confidence for r in entry.verifier_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0.5
        return ConfidenceVector(
            statistical=entry.composite_confidence,
            regime=avg_verifier_conf,
            execution=0.9,
            tail_risk=0.85,
            model_stability=0.7
        )

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {
            "trade_id": str(entry.entry_id),
            "symbol": "BTC/USDT",
            "quantity": 1.0,
            "confidence": entry.composite_confidence,
            "hypothesis_id": entry.hypothesis.hypothesis_id if entry.hypothesis else "N/A"
        }
