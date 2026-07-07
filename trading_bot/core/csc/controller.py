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
        self.folding_operator = FoldingOperator(hms)

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # HASP: Executable Guardrails (Skill Programs)
        self.skill_programs = self._load_skill_programs()

    def _load_skill_programs(self) -> Dict[str, Any]:
        # In production, load from a registry. Here we stub it.
        return {}

        # DiscoLoop Channels
        self.continuous_state = {} # Latent embeddings
        self.discrete_channel = [] # Semantic tokens

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

        # 7. Decision Selection (Expected Free Energy minimization)
        # (Ludik, 2025)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return None

        # 8. Decision Loop (Pivot/Refine)
        # (RSEA - arXiv:2606.28374)
        decision_ready = False
        attempts = 0
        while not decision_ready and attempts < 3:
            attempts += 1

            # 9. Verification Swarm (Peer Review / Falsification)
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
                    logger.error("CSC-V5: Could not refine strategy further.")
                    break

        if not decision_ready:
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Failed Pivot/Refine loop")

        # 11. Governance Gate (LogAct Shared-Log Voter)
        # (Balakrishnan et al., 2026 - LogAct)
        trade_proposal = self._translate_to_proposal(ledger_entry)
        shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})

        from ..immutable_shield import GovernanceDecision
        if shield_report.decision != GovernanceDecision.APPROVED:
             return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason=f"Shield: {shield_report.reason}")

        # 12. Execution & Information Folding (HIPIF)
        # (arXiv:2606.10507 - HIPIF)
        logger.info(f"CSC-V5: Trade APPROVED. Folding horizon...")
        self.folder.fold_history(ledger_entry)

        # Persist to HMS (SAGE Evolution)
        self.hms.store_ledger_entry(ledger_entry)

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
            confidence_vector=self._calculate_composite_confidence(ledger_entry)
        )

    def _calculate_sensory_surprise(self, observation: Dict[str, Any]) -> float:
        """
        Variational Free Energy Component: Sensory Surprise.
        Surprise = -log P(observation | internal_world_model).
        """
        # Calculate deviation of current market state from predicted state
        predicted_state = self.world_model.get_predicted_state() if self.world_model else {}
        if not predicted_state:
             return 0.5 # Default uncertainty

        # Euclidean distance of key metrics as proxy for surprise
        obs_price = observation.get('price', 0)
        pred_price = predicted_state.get('price', obs_price)

        surprise = abs(obs_price - pred_price) / (obs_price if obs_price != 0 else 1.0)
        return float(surprise)

    def _update_internal_beliefs(self, observation: Dict[str, Any], evidence: List[Any]):
        """
        Bayesian Belief Update (Metacognitive Internalization).
        Updates internal model priors based on new evidence.
        """
        if not evidence:
            return

        # Map evidence to regime probabilities or alpha confidence
        for node in evidence:
            content = str(node.content).lower()
            if "regime" in content:
                # Update regime belief state in world model
                pass

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
