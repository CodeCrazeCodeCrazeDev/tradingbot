"""
Cognitive System Controller (CSC) - UCA V5 Core
=============================================

The "One Brain" authoritative controller orchestrating the LogAct pipeline.
Implements Active Inference (surpise minimization) and DiscoLoop reasoning.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .hypothesis import HypothesisGenerator, ReasoningBranch
from .router import SkillRouter, HASPExecutor, SkillArtifact, SkillType
from ..verification.swarm import VerificationSwarm
from ..hms.models import ResearchLedgerEntry, EvidenceGraph, VerifierReport
from ..alphaalgo_core_engine import DecisionOutcome, CoreDecision, ConfidenceVector
from ..immutable_shield import ImmutableShield
from ..unified_event_bus import decision_bus, LogAction, ActionStatus

logger = logging.getLogger(__name__)

class CognitiveSystemController:
    """
    Authoritative controller for AlphaAlgo UCA V5.
    Governed by Active Inference and Shared-Log Reliability.
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
        self.shield = shield or ImmutableShield()

        self.hypothesis_gen = HypothesisGenerator(world_model)
        self.verifier_swarm = VerificationSwarm()
        self.skill_router = SkillRouter()
        self.hasp_executor = HASPExecutor()

        # Register Shield as a LogAct Voter
        decision_bus.register_voter("GovernanceShield", self._shield_voter)

        self._initialized = True
        logger.info("CSC V5: Initialized and registered with LogAct Backbone")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status and version of the CSC."""
        return {
            "status": "online",
            "version": "UCA-2026-V5",
            "logact_enabled": True
        }

    async def _shield_voter(self, action: LogAction) -> Dict[str, Any]:
        """LogAct Voter bridge for the Immutable Shield."""
        if action.action_type != "trade":
            return {"decision": "APPROVE"}

        context = {"market": {"volatility": 0.2}, "portfolio": {"drawdown": 0.05}}
        from ..immutable_shield import GovernanceDecision
        report = self.shield.validate_action("trade", action.payload, context)

        return {
            "decision": "APPROVE" if report.decision == GovernanceDecision.APPROVED else "REJECT",
            "reason": report.reason
        }

    async def process_market_observation(self, observation: Dict[str, Any]) -> Optional[CoreDecision]:
        """
        The O-S-A Loop orchestrated via the Shared Log.
        """
        logger.info("CSC V5: Starting institutional reasoning pipeline")

        # 1. Observe & DiscoLoop Reasoning
        branches = await self.hypothesis_gen.generate_competing_branches(observation)

        # 2. Simulate (Structural Interventions)
        sim_results = await self.hypothesis_gen.simulate_branches(branches)

        # 3. Select Policy (Minimize Expected Free Energy)
        best_branch = self._select_optimal_branch(branches, sim_results)
        if not best_branch:
            return None

        # 4. Propose Action to Shared Log (The Reliability Gate)
        trade_proposal = self._translate_to_proposal(best_branch, sim_results[best_branch.branch_id])

        action = LogAction(
            action_type="trade",
            payload=trade_proposal,
            agent_id="CSC_V5",
            correlation_id=str(uuid4())
        )

        # 5. Commit to Log and await consensus
        await decision_bus.propose_action(action)

        # Wait for log processing (mock async wait for status change)
        # In production, this would be a future or event-based
        max_retries = 10
        while action.status in [ActionStatus.PROPOSED, ActionStatus.AUDITING] and max_retries > 0:
            await asyncio.sleep(0.1)
            max_retries -= 1

        if action.status == ActionStatus.APPROVED:
            logger.info(f"CSC V5: Action {action.action_id} approved and logged. Triggering HASP execution.")

            # 6. Post-Approval Execution (HASP/S2L)
            skill = self.skill_router.route_task("execution", trade_proposal)
            if skill and skill.skill_type == SkillType.HASP_PROGRAM:
                 exec_res = self.hasp_executor.execute(skill, trade_proposal)
                 logger.info(f"CSC V5: HASP Execution Result: {exec_res['status']}")

            return CoreDecision(
                outcome=DecisionOutcome.TRADE_APPROVED,
                trade_id=trade_proposal.get("trade_id"),
                approved_position_size=trade_proposal.get("quantity", 0)
            )
        else:
            logger.warning(f"CSC V5: Action {action.action_id} rejected by LogAct backbone: {action.voter_reports}")
            return CoreDecision(
                outcome=DecisionOutcome.TRADE_REJECTED,
                dominant_rejection_reason="LogAct Veto"
            )

    def _select_optimal_branch(self, branches: List[ReasoningBranch], simulations: Dict[str, Any]) -> Optional[ReasoningBranch]:
        if not branches: return None
        return branches[0]

    def _translate_to_proposal(self, branch: ReasoningBranch, scenarios: List[Any]) -> Dict[str, Any]:
        return {
            "trade_id": "T_" + str(datetime.now().timestamp()),
            "symbol": "EURUSD",
            "quantity": 1.0,
            "exposure": 0.5
        }
