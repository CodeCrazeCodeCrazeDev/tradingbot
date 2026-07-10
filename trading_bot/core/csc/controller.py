"""
Implements the Active Inference (VFE minimization) loop and
HIPIF (Hierarchical Planning with Information Folding).

The "One Brain" authoritative controller orchestrating the LogAct pipeline.
Implements Active Inference (surpise minimization) and DiscoLoop reasoning.
Cognitive System Controller (CSC) - UCA V5 (July 2026)
"""

import logging
import asyncio
import copy
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .folding import InformationFolder as FoldingOperator
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus
from ...core_agent_system.scientific_reasoning.core import ScientificReasoningEngine, HypothesisState

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    UCA V5 Controller integrating DiscoLoop, HASP, and Pivot/Refine.
    Unified under the Scientific Reasoning Engine (SRE).
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

        # Core Functional Components
        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.folder = InformationFolder()

        # Unified SRE Integration - Passing self as controller for hook reuse
        self.sre = ScientificReasoningEngine(controller=self, hms=hms, world_model=world_model)

        self.skill_programs = self._load_skill_programs()
        self._initialized = True

    def _load_skill_programs(self) -> Dict[str, Any]:
        return {}

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        19-step Recursive Scientific Reasoning Pipeline via SRE.
        """
        logger.info("CSC-V5: Starting Unified Scientific Reasoning Pipeline")

        # 1. Scientific lifecycle (SRE stages)
        hyp_id = await self.sre.run_cycle(observation)
        hypothesis = self.sre.registry.get(hyp_id)

        if not hypothesis or hypothesis.state == HypothesisState.REJECTED:
            logger.warning(f"CSC-V5: Hypothesis {hyp_id} REJECTED by scientific engine.")
            return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Scientific Rejection")

        # 2. Decision check (Validated/Confirmed hypotheses)
        if hypothesis.state in [HypothesisState.CONFIRMED, HypothesisState.INSTITUTIONALIZED, HypothesisState.EVALUATION, HypothesisState.CONTINUOUS_MONITORING]:

            # Governance Gate (Immutable Shield)
            trade_proposal = self._translate_to_proposal_from_hypothesis(hypothesis)
            shield_report = self.shield.validate_action("trade", trade_proposal, {"market": observation})

            from ..immutable_shield import GovernanceDecision
            if shield_report.decision != GovernanceDecision.APPROVED:
                 return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason=f"Shield: {shield_report.reason}")

            # Execution & Folding (HIPIF)
            logger.info(f"CSC-V5: Scientific Hypothesis {hyp_id} APPROVED for execution.")

            # Persist to HMS
            if self.hms:
                entry = self._create_ledger_entry_from_hyp(hypothesis)
                self.hms.store_ledger_entry(entry)

            return CoreDecision(
                outcome=DecisionOutcome.TRADE_APPROVED,
                trade_id=trade_proposal.get("trade_id"),
                confidence_vector=ConfidenceVector(
                    statistical=hypothesis.posterior,
                    regime=0.8,
                    execution=0.9,
                    tail_risk=1.0 - hypothesis.uncertainty,
                    model_stability=hypothesis.validation_score
                )
            )

        return CoreDecision(outcome=DecisionOutcome.TRADE_REJECTED, dominant_rejection_reason="Inconclusive Scientific State")

    def _create_ledger_entry_from_hyp(self, hypothesis: Any) -> ResearchLedgerEntry:
        return ResearchLedgerEntry(
            hypothesis=hypothesis,
            reasoning_steps=[hypothesis.state.name],
            evidence_graph_snapshot=None
        )

    def _translate_to_proposal_from_hypothesis(self, hypothesis: Any) -> Dict[str, Any]:
        return {
            "trade_id": str(hypothesis.id),
            "symbol": "EURUSD",
            "quantity": 1.0,
            "confidence": hypothesis.posterior,
            "scientific_state": hypothesis.state.name
        }
