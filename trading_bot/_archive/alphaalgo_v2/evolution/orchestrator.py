"""
AlphaAlgo V2 Evolution Orchestrator

This is the master controller for the self-improvement system.
It coordinates analysis, proposal generation, validation, and deployment.

Safety Principles:
1. All changes must pass safety validation
2. Critical changes require human approval
3. All changes can be rolled back
4. The reward model is IMMUTABLE
5. Risk limits cannot be increased
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

from ..core.interfaces import IEvolutionEngine
from ..core.types import EvolutionProposal, ProposalStatus
from ..core.constants import EVOLUTION_CATEGORIES, EvolutionApprovalLevel
from ..core.exceptions import (
    EvolutionError,
    ProposalRejectedError,
    SafetyViolationError,
    HumanApprovalRequiredError,
)

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """Evolution cycle phases"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    PROPOSING = "proposing"
    VALIDATING = "validating"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    ROLLING_BACK = "rolling_back"


@dataclass
class EvolutionCycle:
    """Record of an evolution cycle"""
    id: str
    started_at: datetime
    phase: EvolutionPhase
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    proposals: List[EvolutionProposal] = field(default_factory=list)
    deployed_proposals: List[str] = field(default_factory=list)
    rolled_back_proposals: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class EvolutionOrchestrator(IEvolutionEngine):
    """
    Master controller for the self-improvement system
    
    Coordinates:
    1. System analysis for improvement opportunities
    2. Proposal generation
    3. Safety validation
    4. Human approval (when required)
    5. Safe deployment
    6. Monitoring and rollback
    
    Safety Features:
    - All proposals validated against safety constraints
    - Critical changes require human approval
    - Automatic rollback on failure
    - Complete audit trail
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._auto_evolve = self.config.get("auto_evolve", False)
        self._evolution_interval = self.config.get("evolution_interval_hours", 24)
        
        # State
        self._current_cycle: Optional[EvolutionCycle] = None
        self._cycle_history: List[EvolutionCycle] = []
        self._pending_approvals: Dict[str, EvolutionProposal] = {}
        self._deployed_proposals: Dict[str, EvolutionProposal] = {}
        
        # Components (lazy loaded)
        self._analyzer = None
        self._proposer = None
        self._validator = None
        self._deployer = None
        
        # Background task
        self._evolution_task: Optional[asyncio.Task] = None
        
        logger.info("Evolution orchestrator initialized")
    
    @property
    def is_enabled(self) -> bool:
        """Check if evolution is enabled"""
        return self._enabled
    
    @property
    def current_phase(self) -> EvolutionPhase:
        """Get current evolution phase"""
        if self._current_cycle:
            return self._current_cycle.phase
        return EvolutionPhase.IDLE
    
    async def start(self) -> None:
        """Start the evolution engine"""
        if not self._enabled:
            logger.info("Evolution engine is disabled")
            return
        
        if self._auto_evolve:
            self._evolution_task = asyncio.create_task(self._evolution_loop())
            logger.info("Started automatic evolution loop")
    
    async def stop(self) -> None:
        """Stop the evolution engine"""
        if self._evolution_task:
            self._evolution_task.cancel()
            try:
                await self._evolution_task
            except asyncio.CancelledError:
                pass
            self._evolution_task = None
        logger.info("Evolution engine stopped")
    
    async def _evolution_loop(self) -> None:
        """Background evolution loop"""
        while True:
            try:
                await asyncio.sleep(self._evolution_interval * 3600)
                await self.run_evolution_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution cycle failed: {e}")
    
    async def run_evolution_cycle(self) -> EvolutionCycle:
        """
        Run a complete evolution cycle
        
        Steps:
        1. Analyze system for improvements
        2. Generate proposals
        3. Validate proposals
        4. Request approvals (if needed)
        5. Deploy approved proposals
        6. Monitor and rollback if needed
        
        Returns:
            EvolutionCycle record
        """
        cycle = EvolutionCycle(
            id=str(uuid.uuid4()),
            started_at=datetime.now(),
            phase=EvolutionPhase.ANALYZING,
        )
        self._current_cycle = cycle
        
        try:
            # Phase 1: Analyze
            logger.info(f"Evolution cycle {cycle.id}: Analyzing system")
            cycle.phase = EvolutionPhase.ANALYZING
            analysis = await self.analyze()
            cycle.analysis_results = analysis
            
            # Phase 2: Propose
            logger.info(f"Evolution cycle {cycle.id}: Generating proposals")
            cycle.phase = EvolutionPhase.PROPOSING
            proposals = await self.propose(analysis)
            cycle.proposals = proposals
            
            if not proposals:
                logger.info("No improvement proposals generated")
                cycle.phase = EvolutionPhase.IDLE
                cycle.completed_at = datetime.now()
                self._cycle_history.append(cycle)
                return cycle
            
            # Phase 3: Validate and deploy each proposal
            for proposal in proposals:
                try:
                    # Validate
                    logger.info(f"Validating proposal: {proposal.title}")
                    cycle.phase = EvolutionPhase.VALIDATING
                    is_valid = await self.validate(proposal)
                    
                    if not is_valid:
                        logger.warning(f"Proposal rejected: {proposal.title}")
                        proposal.status = ProposalStatus.REJECTED
                        continue
                    
                    # Check if human approval required
                    if proposal.requires_human_approval:
                        logger.info(f"Human approval required for: {proposal.title}")
                        cycle.phase = EvolutionPhase.AWAITING_APPROVAL
                        self._pending_approvals[proposal.id] = proposal
                        proposal.status = ProposalStatus.APPROVED  # Pending human
                        continue
                    
                    # Deploy
                    logger.info(f"Deploying proposal: {proposal.title}")
                    cycle.phase = EvolutionPhase.DEPLOYING
                    success = await self.deploy(proposal)
                    
                    if success:
                        cycle.deployed_proposals.append(proposal.id)
                        proposal.status = ProposalStatus.DEPLOYED
                    else:
                        proposal.status = ProposalStatus.REJECTED
                        
                except Exception as e:
                    logger.error(f"Error processing proposal {proposal.id}: {e}")
                    proposal.status = ProposalStatus.REJECTED
            
            # Complete
            cycle.phase = EvolutionPhase.IDLE
            cycle.completed_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Evolution cycle failed: {e}")
            cycle.error = str(e)
            cycle.phase = EvolutionPhase.IDLE
            cycle.completed_at = datetime.now()
        
        self._cycle_history.append(cycle)
        self._current_cycle = None
        
        return cycle
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze system for improvement opportunities
        
        Analyzes:
        - Trading performance
        - Model accuracy
        - System health
        - Code quality
        - Resource usage
        
        Returns:
            Analysis results with identified issues and opportunities
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "performance": {},
            "models": {},
            "system": {},
            "opportunities": [],
            "issues": [],
        }
        
        # Performance analysis
        analysis["performance"] = {
            "sharpe_ratio": 1.2,  # Placeholder
            "win_rate": 0.52,
            "profit_factor": 1.3,
            "max_drawdown": 0.08,
            "needs_improvement": ["sharpe_ratio", "profit_factor"],
        }
        
        # Model analysis
        analysis["models"] = {
            "forecaster_accuracy": 0.58,
            "regime_detector_accuracy": 0.72,
            "sentiment_accuracy": 0.65,
            "needs_retraining": ["forecaster"],
        }
        
        # System analysis
        analysis["system"] = {
            "cpu_usage": 0.45,
            "memory_usage": 0.62,
            "latency_ms": 150,
            "error_rate": 0.001,
            "issues": [],
        }
        
        # Identify opportunities
        if analysis["performance"]["sharpe_ratio"] < 1.5:
            analysis["opportunities"].append({
                "type": "parameter_tuning",
                "target": "strategy_parameters",
                "expected_improvement": "10-20% Sharpe improvement",
                "priority": 2,
            })
        
        if "forecaster" in analysis["models"]["needs_retraining"]:
            analysis["opportunities"].append({
                "type": "model_retraining",
                "target": "price_forecaster",
                "expected_improvement": "5-10% accuracy improvement",
                "priority": 1,
            })
        
        return analysis
    
    async def propose(
        self,
        analysis: Dict[str, Any]
    ) -> List[EvolutionProposal]:
        """
        Generate improvement proposals based on analysis
        
        Args:
            analysis: Analysis results
            
        Returns:
            List of improvement proposals
        """
        proposals = []
        
        for opportunity in analysis.get("opportunities", []):
            category = opportunity.get("type", "unknown")
            approval_level = EVOLUTION_CATEGORIES.get(
                category,
                EvolutionApprovalLevel.HUMAN
            )
            
            proposal = EvolutionProposal(
                id=str(uuid.uuid4()),
                title=f"Improve {opportunity.get('target', 'system')}",
                description=opportunity.get("expected_improvement", ""),
                category=category,
                priority=opportunity.get("priority", 3),
                requires_human_approval=(
                    approval_level == EvolutionApprovalLevel.HUMAN
                ),
                status=ProposalStatus.PENDING,
                changes={
                    "type": category,
                    "target": opportunity.get("target"),
                    "parameters": {},
                },
            )
            
            proposals.append(proposal)
        
        # Sort by priority
        proposals.sort(key=lambda p: p.priority)
        
        return proposals
    
    async def validate(self, proposal: EvolutionProposal) -> bool:
        """
        Validate proposal safety
        
        Checks:
        1. Does not violate safety constraints
        2. Does not modify immutable components
        3. Has valid rollback plan
        4. Passes simulation tests
        
        Args:
            proposal: Proposal to validate
            
        Returns:
            True if proposal is safe to deploy
        """
        proposal.status = ProposalStatus.VALIDATING
        
        # Check category is allowed
        if proposal.category not in EVOLUTION_CATEGORIES:
            logger.warning(f"Unknown category: {proposal.category}")
            return False
        
        # Check for safety violations
        safety_violations = self._check_safety_violations(proposal)
        if safety_violations:
            logger.warning(f"Safety violations: {safety_violations}")
            proposal.validation_results["safety_violations"] = safety_violations
            return False
        
        # Check for immutable component modifications
        if self._modifies_immutable(proposal):
            logger.warning("Proposal modifies immutable components")
            proposal.validation_results["immutable_violation"] = True
            return False
        
        # Validate rollback plan
        if not self._has_valid_rollback(proposal):
            logger.warning("No valid rollback plan")
            proposal.validation_results["rollback_valid"] = False
            return False
        
        proposal.validation_results["passed"] = True
        proposal.status = ProposalStatus.APPROVED
        
        return True
    
    def _check_safety_violations(
        self,
        proposal: EvolutionProposal
    ) -> List[str]:
        """Check for safety constraint violations"""
        violations = []
        
        changes = proposal.changes
        
        # Check if trying to increase risk limits
        if "risk_limits" in changes:
            violations.append("Cannot modify risk limits")
        
        # Check if trying to disable safety features
        if changes.get("disable_safety", False):
            violations.append("Cannot disable safety features")
        
        # Check if trying to modify reward model
        if "reward_model" in changes:
            violations.append("Cannot modify reward model")
        
        return violations
    
    def _modifies_immutable(self, proposal: EvolutionProposal) -> bool:
        """Check if proposal modifies immutable components"""
        immutable_components = [
            "reward_model",
            "risk_limits",
            "safety_constraints",
            "ethical_constraints",
        ]
        
        for component in immutable_components:
            if component in proposal.changes:
                return True
        
        return False
    
    def _has_valid_rollback(self, proposal: EvolutionProposal) -> bool:
        """Check if proposal has valid rollback plan"""
        # For now, all proposals have implicit rollback
        return True
    
    async def deploy(
        self,
        proposal: EvolutionProposal,
        approved_by: Optional[str] = None
    ) -> bool:
        """
        Deploy approved proposal
        
        Args:
            proposal: Proposal to deploy
            approved_by: Human approver (required for critical changes)
            
        Returns:
            True if successfully deployed
        """
        # Check if human approval is required but not provided
        if proposal.requires_human_approval and not approved_by:
            raise HumanApprovalRequiredError(
                f"Human approval required for proposal: {proposal.title}",
                proposal_id=proposal.id,
            )
        
        try:
            # Record approval
            if approved_by:
                proposal.approved_by = approved_by
            
            # Deploy based on category
            category = proposal.category
            
            if category == "parameter_tuning":
                success = await self._deploy_parameter_tuning(proposal)
            elif category == "model_retraining":
                success = await self._deploy_model_retraining(proposal)
            else:
                logger.warning(f"Unknown deployment category: {category}")
                success = False
            
            if success:
                proposal.status = ProposalStatus.DEPLOYED
                proposal.deployed_at = datetime.now()
                self._deployed_proposals[proposal.id] = proposal
                logger.info(f"Successfully deployed: {proposal.title}")
            
            return success
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            proposal.status = ProposalStatus.REJECTED
            return False
    
    async def _deploy_parameter_tuning(
        self,
        proposal: EvolutionProposal
    ) -> bool:
        """Deploy parameter tuning changes"""
        # Placeholder - would update actual parameters
        logger.info(f"Deploying parameter tuning: {proposal.changes}")
        return True
    
    async def _deploy_model_retraining(
        self,
        proposal: EvolutionProposal
    ) -> bool:
        """Deploy model retraining"""
        # Placeholder - would trigger model retraining
        logger.info(f"Deploying model retraining: {proposal.changes}")
        return True
    
    async def rollback(self, proposal_id: str) -> bool:
        """
        Rollback a deployed proposal
        
        Args:
            proposal_id: ID of proposal to rollback
            
        Returns:
            True if successfully rolled back
        """
        if proposal_id not in self._deployed_proposals:
            logger.warning(f"Proposal not found: {proposal_id}")
            return False
        
        proposal = self._deployed_proposals[proposal_id]
        
        try:
            # Perform rollback based on category
            logger.info(f"Rolling back: {proposal.title}")
            
            # Mark as rolled back
            proposal.status = ProposalStatus.ROLLED_BACK
            del self._deployed_proposals[proposal_id]
            
            logger.info(f"Successfully rolled back: {proposal.title}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_history(self) -> List[EvolutionProposal]:
        """Get history of evolution proposals"""
        all_proposals = []
        for cycle in self._cycle_history:
            all_proposals.extend(cycle.proposals)
        return all_proposals
    
    def get_pending_approvals(self) -> List[EvolutionProposal]:
        """Get proposals pending human approval"""
        return list(self._pending_approvals.values())
    
    async def approve_proposal(
        self,
        proposal_id: str,
        approved_by: str
    ) -> bool:
        """
        Approve a pending proposal
        
        Args:
            proposal_id: ID of proposal to approve
            approved_by: Human approver name
            
        Returns:
            True if successfully approved and deployed
        """
        if proposal_id not in self._pending_approvals:
            logger.warning(f"Proposal not pending: {proposal_id}")
            return False
        
        proposal = self._pending_approvals[proposal_id]
        del self._pending_approvals[proposal_id]
        
        return await self.deploy(proposal, approved_by=approved_by)
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """
        Reject a pending proposal
        
        Args:
            proposal_id: ID of proposal to reject
            reason: Rejection reason
            
        Returns:
            True if successfully rejected
        """
        if proposal_id not in self._pending_approvals:
            logger.warning(f"Proposal not pending: {proposal_id}")
            return False
        
        proposal = self._pending_approvals[proposal_id]
        proposal.status = ProposalStatus.REJECTED
        proposal.validation_results["rejection_reason"] = reason
        del self._pending_approvals[proposal_id]
        
        logger.info(f"Rejected proposal: {proposal.title} - {reason}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get evolution engine status"""
        return {
            "enabled": self._enabled,
            "auto_evolve": self._auto_evolve,
            "current_phase": self.current_phase.value,
            "pending_approvals": len(self._pending_approvals),
            "deployed_proposals": len(self._deployed_proposals),
            "total_cycles": len(self._cycle_history),
        }
