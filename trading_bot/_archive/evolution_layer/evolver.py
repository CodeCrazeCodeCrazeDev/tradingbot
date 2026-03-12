"""
AlphaAlgo Code Evolver - Safe Code Evolution

This module handles code evolution and improvement proposals.
All evolution is bounded by the IMMUTABLE reward model constraints.
Code changes REQUIRE human approval before deployment.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import hashlib
import json
from pathlib import Path

from .reward_model import get_reward_model, is_valid_action

logger = logging.getLogger(__name__)


class EvolutionType(Enum):
    """Types of evolution proposals"""
    PARAMETER_CHANGE = "parameter_change"
    STRATEGY_ADDITION = "strategy_addition"
    STRATEGY_REMOVAL = "strategy_removal"
    INDICATOR_ADDITION = "indicator_addition"
    RISK_ADJUSTMENT = "risk_adjustment"
    EXECUTION_IMPROVEMENT = "execution_improvement"
    BUG_FIX = "bug_fix"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class EvolutionStatus(Enum):
    """Status of evolution proposal"""
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"


@dataclass
class EvolutionProposal:
    """A proposed evolution/improvement"""
    proposal_id: str
    evolution_type: EvolutionType
    status: EvolutionStatus
    
    # What to change
    target_component: str
    description: str
    rationale: str
    
    # The change itself
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    
    # Expected impact
    expected_improvement: float
    risk_assessment: str
    
    # Validation
    passes_constraints: bool
    constraint_violations: List[str]
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    applied_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'evolution_type': self.evolution_type.value,
            'status': self.status.value,
            'target_component': self.target_component,
            'description': self.description,
            'rationale': self.rationale,
            'before_state': self.before_state,
            'after_state': self.after_state,
            'expected_improvement': self.expected_improvement,
            'risk_assessment': self.risk_assessment,
            'passes_constraints': self.passes_constraints,
            'constraint_violations': self.constraint_violations,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
        }


@dataclass
class EvolutionResult:
    """Result of applying an evolution"""
    success: bool
    proposal_id: str
    
    # Outcome
    actual_improvement: float
    side_effects: List[str]
    
    # Rollback info
    can_rollback: bool
    rollback_state: Optional[Dict[str, Any]] = None
    
    # Metadata
    applied_at: datetime = field(default_factory=datetime.now)


class CodeEvolver:
    """
    Safe code evolution system.
    
    Key principles:
    1. All evolution is bounded by the IMMUTABLE reward model
    2. Code changes REQUIRE human approval
    3. All changes are reversible (rollback capability)
    4. Evolution cannot modify the reward model itself
    5. Evolution cannot increase risk limits
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reward_model = get_reward_model()
        
        # Proposal storage
        self._proposals: Dict[str, EvolutionProposal] = {}
        self._applied_evolutions: List[EvolutionResult] = []
        
        # Rollback states
        self._rollback_states: Dict[str, Dict[str, Any]] = {}
        
        # Storage path
        self._storage_path = Path(self.config.get('storage_path', 'evolution_state'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("CodeEvolver initialized")
    
    def propose_evolution(
        self,
        evolution_type: EvolutionType,
        target_component: str,
        description: str,
        rationale: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        expected_improvement: float
    ) -> EvolutionProposal:
        """
        Propose a code evolution.
        
        This creates a proposal that MUST be approved by a human
        before it can be applied.
        """
        # Generate proposal ID
        proposal_id = self._generate_proposal_id(
            evolution_type, target_component, description
        )
        
        # Validate against reward model constraints
        passes_constraints, violations = self._validate_evolution(
            evolution_type, after_state
        )
        
        # Assess risk
        risk_assessment = self._assess_risk(evolution_type, before_state, after_state)
        
        proposal = EvolutionProposal(
            proposal_id=proposal_id,
            evolution_type=evolution_type,
            status=EvolutionStatus.PROPOSED,
            target_component=target_component,
            description=description,
            rationale=rationale,
            before_state=before_state,
            after_state=after_state,
            expected_improvement=expected_improvement,
            risk_assessment=risk_assessment,
            passes_constraints=passes_constraints,
            constraint_violations=violations,
        )
        
        # Store proposal
        self._proposals[proposal_id] = proposal
        
        # If it passes constraints, mark as pending approval
        if passes_constraints:
            proposal.status = EvolutionStatus.PENDING_APPROVAL
            logger.info(f"Evolution proposal {proposal_id} created and pending approval")
        else:
            proposal.status = EvolutionStatus.REJECTED
            logger.warning(f"Evolution proposal {proposal_id} rejected: {violations}")
        
        # Save to disk
        self._save_proposal(proposal)
        
        return proposal
    
    def approve_evolution(
        self, 
        proposal_id: str, 
        approver: str
    ) -> bool:
        """
        Approve an evolution proposal (HUMAN ACTION REQUIRED).
        
        This should only be called by the human approval layer.
        """
        if proposal_id not in self._proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != EvolutionStatus.PENDING_APPROVAL:
            logger.error(f"Proposal {proposal_id} is not pending approval")
            return False
        
        if not proposal.passes_constraints:
            logger.error(f"Cannot approve proposal that violates constraints")
            return False
        
        proposal.status = EvolutionStatus.APPROVED
        proposal.approved_at = datetime.now()
        proposal.approved_by = approver
        
        logger.info(f"Evolution proposal {proposal_id} approved by {approver}")
        self._save_proposal(proposal)
        
        return True
    
    def reject_evolution(
        self, 
        proposal_id: str, 
        reason: str
    ) -> bool:
        """Reject an evolution proposal"""
        if proposal_id not in self._proposals:
            return False
        
        proposal = self._proposals[proposal_id]
        proposal.status = EvolutionStatus.REJECTED
        proposal.constraint_violations.append(f"Rejected: {reason}")
        
        logger.info(f"Evolution proposal {proposal_id} rejected: {reason}")
        self._save_proposal(proposal)
        
        return True
    
    def apply_evolution(
        self, 
        proposal_id: str,
        apply_fn: callable
    ) -> EvolutionResult:
        """
        Apply an approved evolution.
        
        Args:
            proposal_id: ID of the approved proposal
            apply_fn: Function that applies the change (receives after_state)
        
        Returns:
            EvolutionResult with outcome
        """
        if proposal_id not in self._proposals:
            return EvolutionResult(
                success=False,
                proposal_id=proposal_id,
                actual_improvement=0,
                side_effects=["Proposal not found"],
                can_rollback=False,
            )
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != EvolutionStatus.APPROVED:
            return EvolutionResult(
                success=False,
                proposal_id=proposal_id,
                actual_improvement=0,
                side_effects=["Proposal not approved"],
                can_rollback=False,
            )
        
        # Store rollback state
        self._rollback_states[proposal_id] = proposal.before_state.copy()
        
        try:
            # Apply the change
            apply_fn(proposal.after_state)
            
            # Update proposal status
            proposal.status = EvolutionStatus.APPLIED
            proposal.applied_at = datetime.now()
            
            result = EvolutionResult(
                success=True,
                proposal_id=proposal_id,
                actual_improvement=proposal.expected_improvement,  # Will be updated later
                side_effects=[],
                can_rollback=True,
                rollback_state=proposal.before_state,
            )
            
            self._applied_evolutions.append(result)
            logger.info(f"Evolution {proposal_id} applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply evolution {proposal_id}: {e}")
            result = EvolutionResult(
                success=False,
                proposal_id=proposal_id,
                actual_improvement=0,
                side_effects=[str(e)],
                can_rollback=True,
                rollback_state=proposal.before_state,
            )
        
        self._save_proposal(proposal)
        return result
    
    def rollback_evolution(
        self, 
        proposal_id: str,
        rollback_fn: callable
    ) -> bool:
        """
        Rollback an applied evolution.
        
        Args:
            proposal_id: ID of the evolution to rollback
            rollback_fn: Function that applies the rollback (receives before_state)
        """
        if proposal_id not in self._rollback_states:
            logger.error(f"No rollback state for {proposal_id}")
            return False
        try:
        
            rollback_state = self._rollback_states[proposal_id]
            rollback_fn(rollback_state)
            
            # Update proposal status
            if proposal_id in self._proposals:
                self._proposals[proposal_id].status = EvolutionStatus.ROLLED_BACK
                self._save_proposal(self._proposals[proposal_id])
            
            logger.info(f"Evolution {proposal_id} rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback evolution {proposal_id}: {e}")
            return False
    
    def _validate_evolution(
        self, 
        evolution_type: EvolutionType,
        after_state: Dict[str, Any]
    ) -> tuple:
        """Validate evolution against reward model constraints"""
        violations = []
        
        # Check if action is valid according to reward model
        action = {
            'evolution_type': evolution_type.value,
            **after_state,
        }
        
        if not is_valid_action(action):
            violations.append("Action violates reward model constraints")
        
        # Specific checks
        if evolution_type == EvolutionType.RISK_ADJUSTMENT:
            risk = after_state.get('risk', {})
            if risk.get('base_risk_percent', 0) > 0.02:
                violations.append("Risk per trade exceeds 2% limit")
            if risk.get('max_drawdown', 0) > 0.20:
                violations.append("Max drawdown exceeds 20% limit")
        
        # Cannot modify reward model
        if after_state.get('modifies_reward_model', False):
            violations.append("Cannot modify reward model")
        
        # Cannot disable risk limits
        if after_state.get('disables_risk_limits', False):
            violations.append("Cannot disable risk limits")
        
        # Cannot bypass human approval
        if after_state.get('bypasses_human_approval', False):
            violations.append("Cannot bypass human approval")
        
        passes = len(violations) == 0
        return passes, violations
    
    def _assess_risk(
        self,
        evolution_type: EvolutionType,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any]
    ) -> str:
        """Assess risk level of evolution"""
        # High risk evolutions
        high_risk_types = [
            EvolutionType.RISK_ADJUSTMENT,
            EvolutionType.STRATEGY_REMOVAL,
        ]
        
        if evolution_type in high_risk_types:
            return "HIGH - Requires careful review"
        
        # Medium risk
        medium_risk_types = [
            EvolutionType.STRATEGY_ADDITION,
            EvolutionType.EXECUTION_IMPROVEMENT,
        ]
        
        if evolution_type in medium_risk_types:
            return "MEDIUM - Standard review required"
        
        # Low risk
        return "LOW - Minor change"
    
    def _generate_proposal_id(
        self,
        evolution_type: EvolutionType,
        target: str,
        description: str
    ) -> str:
        """Generate unique proposal ID"""
        data = f"{evolution_type.value}{target}{description}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _save_proposal(self, proposal: EvolutionProposal) -> None:
        """Save proposal to disk"""
        try:
            path = self._storage_path / f"proposal_{proposal.proposal_id}.json"
            with open(path, 'w') as f:
                json.dump(proposal.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save proposal: {e}")
    
    def get_pending_proposals(self) -> List[EvolutionProposal]:
        """Get all pending approval proposals"""
        return [
            p for p in self._proposals.values()
            if p.status == EvolutionStatus.PENDING_APPROVAL
        ]
    
    def get_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get a specific proposal"""
        return self._proposals.get(proposal_id)
    
    def get_evolution_history(self) -> List[EvolutionResult]:
        """Get history of applied evolutions"""
        return self._applied_evolutions.copy()
