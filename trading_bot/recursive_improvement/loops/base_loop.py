"""
Base Improvement Loop

Abstract base class for all specialized RSIE loops.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..recursive_core import ImprovementProposal, ImprovementDimension, ImprovementTier
from ..infrastructure import ExperimentManager, EvaluationPipeline, ImprovementMemory
from ..validation import ImprovementValidationPipeline
from ..approvals import ApprovalWorkflow

logger = logging.getLogger(__name__)

class BaseImprovementLoop(ABC):
    """
    Base class for RSIE improvement loops.
    Handles the common experiment -> validate -> approve flow.
    """

    def __init__(
        self,
        dimension: ImprovementDimension,
        config: Optional[Dict[str, Any]] = None
    ):
        self.dimension = dimension
        self.config = config or {}

        # Shared infrastructure
        self.experiments = ExperimentManager(self.config.get('experiments'))
        self.evaluation = EvaluationPipeline(self.config.get('evaluation'))
        self.validator = ImprovementValidationPipeline(self.config.get('validation'))
        self.memory = ImprovementMemory(self.config.get('storage_path', 'recursive_improvement_data'))
        self.approvals = ApprovalWorkflow(self.config.get('storage_path', 'recursive_improvement_data'))

        self.is_running = False

    @abstractmethod
    async def run_cycle(self, context: Optional[Dict[str, Any]] = None):
        """Run one complete improvement cycle for this dimension"""
        pass

    async def process_proposal(self, proposal: ImprovementProposal, test_data: Any) -> bool:
        """Standard processing for any proposal: Experiment -> Validate -> Approval -> Deploy"""

        # 1. Store proposal
        await self.memory.store_proposal(proposal)

        # 2. Run Experiment
        logger.info(f"[{self.dimension.value}] Starting experiment for {proposal.proposal_id}")
        exp_results = await self.experiments.run_improvement_experiment(proposal, test_data)

        # 3. Comprehensive Validation
        # In a real scenario, we'd have baseline results to compare against
        validation_report = await self.validator.validate(
            is_results=exp_results,
            oos_results=exp_results, # Simplified for stub
            baseline_results=None
        )

        proposal.validation_results = validation_report.metrics

        if not validation_report.passed_all:
            logger.warning(f"[{self.dimension.value}] Proposal {proposal.proposal_id} failed validation gates.")
            proposal.status = "REJECTED_BY_VALIDATION"
            await self.memory.store_proposal(proposal)
            return False

        # 4. Governance & Approval
        status = await self.approvals.submit_for_approval(proposal)
        proposal.status = status
        await self.memory.store_proposal(proposal)

        if status == "AUTO_APPROVED":
            return await self.deploy_improvement(proposal)
        elif status == "PENDING":
            logger.info(f"[{self.dimension.value}] Proposal {proposal.proposal_id} is pending human approval.")
            return False # Will be picked up later

        return False

    @abstractmethod
    async def deploy_improvement(self, proposal: ImprovementProposal) -> bool:
        """Deploy the validated and approved improvement to the system"""
        pass

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
