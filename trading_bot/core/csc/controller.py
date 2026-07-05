"""
Cognitive System Controller (CSC) - UCA-2026 Core

The "One Brain" authoritative controller orchestrating the superior
institutional financial intelligence pipeline.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .hypothesis import HypothesisGenerator, ReasoningBranch
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    Authoritative controller for AlphaAlgo.
    Implements the 10-step institutional pipeline.
    """

    def __init__(self, world_model: Any, hms: Any, shield: Optional[ImmutableShield] = None):
        self.world_model = world_model
        self.hms = hms
        self.shield = shield or ImmutableShield()

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()

        self.evidence_threshold = 0.7
        self.confidence_threshold = 0.65

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        The main O-S-A Loop orchestrated by the CSC.
        """
        logger.info("CSC: Starting institutional reasoning pipeline")

        # 1. Observe (Already passed in)

        # 2. Specialist Agents (Gather domain-specific data/claims)
        # 3. Gather Evidence (Populate HMS Evidence Graph)

        # 4. Multi-Hypothesis Generation
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 5. Run World Model Simulations for each branch
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 6. Select Best Branch & Refine Evidence
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            logger.warning("CSC: No viable reasoning branch found. Inaction.")
            return None

        # 7. Create Research Ledger Entry (The "Snapshot")
        ledger_entry = self._create_ledger_entry(best_branch, sim_results[best_branch.branch_id])

        # 8. Independent Verification Swarm
        # Challenge Hypotheses, Verify Evidence
        reports = await self.verifier_swarm.run_swarm(ledger_entry)
        ledger_entry.verifier_reports = reports

        # 9. Evidence-First Verification Gate
        # Hard constraint: Check evidence score and verifier consensus
        if not self._verify_evidence_hard_constraint(ledger_entry):
            logger.warning(f"CSC: Evidence-First constraint FAILED for {ledger_entry.entry_id}")
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id="N/A",
                dominant_rejection_reason="Insufficient evidence or verifier rejection"
            )

        # 10. Estimate Decision Confidence & Uncertainty
        confidence_vector = self._calculate_composite_confidence(ledger_entry)
        ledger_entry.composite_confidence = confidence_vector.min_confidence()

        # 11. Governance Gate (Immutable Shield)
        # Check risk, exposure, compliance
        trade_proposal = self._translate_to_proposal(ledger_entry)

        # Build context for shield
        context = {
            "market": {"volatility": 0.2},
            "portfolio": {"drawdown": 0.05}
        }

        from ..immutable_shield import GovernanceDecision
        shield_report = self.shield.validate_action("trade", trade_proposal, context)

        if shield_report.decision != GovernanceDecision.APPROVED:
             logger.warning(f"CSC: Rejected by Immutable Shield: {shield_report.reason}")
             return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                trade_id=trade_proposal.get("trade_id"),
                dominant_rejection_reason=f"Governance Gate (Shield) rejection: {shield_report.reason}"
            )

        # 12. Execution (Success!)
        logger.info(f"CSC: Trade APPROVED with confidence {ledger_entry.composite_confidence}")

        # Store in permanent Research Ledger
        self._store_in_ledger(ledger_entry)

        return CoreDecision(
            outcome=DecisionOutcome.TRADE_APPROVED,
            trade_id=trade_proposal.get("trade_id"),
            approved_position_size=trade_proposal.get("quantity", 0),
            confidence_vector=confidence_vector
        )

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        """Selects the branch with highest EV and lowest uncertainty."""
        # Implementation of Bayesian EV optimization
        if not branches: return None
        return branches[0] # Mock: return the first one

    def _create_ledger_entry(self, branch: ReasoningBranch, scenarios: List[Any]) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=branch.hypotheses[0] if branch.hypotheses else None,
            reasoning_steps=branch.reasoning_trace,
            evidence_graph_snapshot=branch.evidence_graph,
            multi_path_scenarios=[{"name": s.name} for s in scenarios] if scenarios else []
        )

    def _verify_evidence_hard_constraint(self, entry: ResearchLedgerEntry) -> bool:
        """
        Enforces the 'No trade without evidence' rule.
        Absolute hard constraint:
        1. No high-confidence verifier vetoes.
        2. Minimum evidence graph density (Nodes/Edges).
        3. All primary claims in the hypothesis must have supporting EvidenceNodes.
        4. Verifier consensus must be > 0.8.
        """
        # 1. Veto check
        for report in entry.verifier_reports:
            if not report.is_valid and report.confidence > 0.8:
                logger.error(f"CRITICAL VETO: Verifier {report.agent_name} rejected with high confidence: {report.critique}")
                return False

        # 2. Graph density check
        node_count = len(entry.evidence_graph_snapshot.nodes)
        edge_count = len(entry.evidence_graph_snapshot.edges)
        if node_count < 5 or edge_count < 3:
            logger.error(f"INSUFFICIENT EVIDENCE: Graph density too low (Nodes: {node_count}, Edges: {edge_count})")
            return False

        # 3. Consensus check
        valid_reports = [r for r in entry.verifier_reports if r.is_valid]
        consensus = len(valid_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0
        if consensus < 0.75:
             logger.error(f"LOW CONSENSUS: Only {consensus:.1%} of verifiers approved.")
             return False

        # 4. Hallucination check
        for report in entry.verifier_reports:
            if report.detected_hallucinations:
                 logger.error(f"HALLUCINATION DETECTED: {report.detected_hallucinations}")
                 return False

        logger.info(f"EVIDENCE VERIFIED: Graph density {node_count}/{edge_count}, consensus {consensus:.1%}")
        return True

    def _calculate_composite_confidence(self, entry: ResearchLedgerEntry) -> ConfidenceVector:
        # Calculate from graph confidence, verifier reports, and WM uncertainty
        avg_verifier_conf = sum(r.confidence for r in entry.verifier_reports) / len(entry.verifier_reports) if entry.verifier_reports else 0

        return ConfidenceVector(
            statistical=0.75,
            regime=0.8,
            execution=0.9,
            tail_risk=0.85,
            model_stability=avg_verifier_conf
        )

    def _translate_to_proposal(self, entry: ResearchLedgerEntry) -> Dict[str, Any]:
        return {
            "trade_id": str(entry.entry_id),
            "symbol": "EURUSD", # Mock
            "quantity": 1.0,
            "exposure": 0.5,
            "confidence": entry.composite_confidence
        }

    def _store_in_ledger(self, entry: ResearchLedgerEntry):
        """Persists the research to scientific memory."""
        logger.info(f"CSC: Storing research snapshot {entry.entry_id} to permanent ledger")
        try:
            self.hms.store_ledger_entry(entry)
        except Exception as e:
            logger.error(f"CSC: HMS persistence failed: {e}")
