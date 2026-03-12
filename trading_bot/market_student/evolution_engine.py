"""
Safe Evolution Engine - Structured, Safe Improvement
=====================================================

When proposing improvements, the AI prioritizes:
- Clarity over complexity
- Stability over aggression
- Data over emotion
- Structure over chaos
- Precision over randomness
- Consistency over luck
- Risk awareness over profit chasing

The AI evolves WITHOUT losing its FOUNDATION.
All changes require HUMAN APPROVAL.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import json
import uuid
from pathlib import Path
import hashlib
import copy

from .student_ai import ImprovementProposal, ProposalStatus, ProposalType, ProposalPriority
from .reward_system import get_reward_system, PenaltyCategory

logger = logging.getLogger(__name__)


# =============================================================================
# EVOLUTION STATUS
# =============================================================================

class EvolutionStatus(Enum):
    """Status of an evolution"""
    PROPOSED = "proposed"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


# =============================================================================
# EVOLUTION PROPOSAL
# =============================================================================

@dataclass
class EvolutionProposal:
    """A proposal for system evolution"""
    
    evolution_id: str
    source_proposal: ImprovementProposal
    status: EvolutionStatus
    
    # Validation
    safety_check_passed: bool
    stability_check_passed: bool
    backtest_passed: bool
    
    # Impact assessment
    expected_improvement: float  # Expected % improvement
    risk_level: str  # low, medium, high
    rollback_plan: str
    
    # Implementation
    changes_to_apply: List[Dict[str, Any]]
    backup_created: bool
    backup_path: Optional[str]
    
    # Timing
    created_at: datetime
    validated_at: Optional[datetime]
    approved_at: Optional[datetime]
    implemented_at: Optional[datetime]
    
    # Human interaction
    requires_approval: bool = True
    approved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evolution_id': self.evolution_id,
            'status': self.status.value,
            'safety_check_passed': self.safety_check_passed,
            'stability_check_passed': self.stability_check_passed,
            'backtest_passed': self.backtest_passed,
            'expected_improvement': self.expected_improvement,
            'risk_level': self.risk_level,
            'rollback_plan': self.rollback_plan,
            'requires_approval': self.requires_approval,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat(),
        }


# =============================================================================
# SAFE EVOLUTION ENGINE
# =============================================================================

class SafeEvolutionEngine:
    """
    Safe Evolution Engine - Manages system evolution with safety guarantees.
    
    Core principles:
    1. All changes require human approval
    2. Safety checks before any change
    3. Automatic rollback on failure
    4. Preserve system stability
    5. Never modify core safety constraints
    """
    
    # FROZEN - Components that CANNOT be modified
    IMMUTABLE_COMPONENTS = frozenset([
        'reward_system',
        'risk_limits',
        'safety_constraints',
        'approval_requirements',
        'core_identity',
        'ethical_boundaries',
    ])
    
    # FROZEN - Maximum allowed changes per evolution
    MAX_CHANGES_PER_EVOLUTION = 5
    
    # FROZEN - Required safety checks
    REQUIRED_SAFETY_CHECKS = [
        'no_immutable_modification',
        'risk_within_limits',
        'stability_preserved',
        'rollback_possible',
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Get reward system
        self._reward_system = get_reward_system()
        
        # Evolution storage
        self._evolutions: Dict[str, EvolutionProposal] = {}
        self._evolution_history: List[EvolutionProposal] = []
        
        # Backup storage
        self._backup_path = Path(self.config.get('backup_path', 'market_student_data/backups'))
        self._backup_path.mkdir(parents=True, exist_ok=True)
        
        # Current system state (for rollback)
        self._current_state: Dict[str, Any] = {}
        
        # Validation callbacks
        self._safety_validators: List[Callable] = []
        self._stability_validators: List[Callable] = []
        
        # Statistics
        self._stats = {
            'total_evolutions': 0,
            'successful_evolutions': 0,
            'failed_evolutions': 0,
            'rolled_back': 0,
        }
        
        logger.info("SafeEvolutionEngine initialized")
    
    def create_evolution(self, proposal: ImprovementProposal) -> EvolutionProposal:
        """
        Create an evolution from an improvement proposal.
        
        Args:
            proposal: The improvement proposal
            
        Returns:
            EvolutionProposal ready for validation
        """
        evolution_id = f"evo_{uuid.uuid4().hex[:8]}"
        
        # Determine risk level
        risk_level = self._assess_risk_level(proposal)
        
        # Create rollback plan
        rollback_plan = self._create_rollback_plan(proposal)
        
        # Prepare changes
        changes = self._prepare_changes(proposal)
        
        evolution = EvolutionProposal(
            evolution_id=evolution_id,
            source_proposal=proposal,
            status=EvolutionStatus.PROPOSED,
            safety_check_passed=False,
            stability_check_passed=False,
            backtest_passed=False,
            expected_improvement=self._estimate_improvement(proposal),
            risk_level=risk_level,
            rollback_plan=rollback_plan,
            changes_to_apply=changes,
            backup_created=False,
            backup_path=None,
            created_at=datetime.now(),
            validated_at=None,
            approved_at=None,
            implemented_at=None,
            requires_approval=True,
        )
        
        self._evolutions[evolution_id] = evolution
        self._stats['total_evolutions'] += 1
        
        logger.info(f"Created evolution {evolution_id} from proposal {proposal.proposal_id}")
        
        return evolution
    
    def validate_evolution(self, evolution_id: str) -> Dict[str, Any]:
        """
        Validate an evolution before approval.
        
        Args:
            evolution_id: ID of the evolution
            
        Returns:
            Validation result
        """
        if evolution_id not in self._evolutions:
            return {'valid': False, 'error': 'Evolution not found'}
        
        evolution = self._evolutions[evolution_id]
        evolution.status = EvolutionStatus.VALIDATING
        
        validation_result = {
            'valid': True,
            'checks': {},
            'warnings': [],
            'errors': [],
        }
        
        # Check 1: No immutable modifications
        immutable_check = self._check_no_immutable_modification(evolution)
        validation_result['checks']['no_immutable_modification'] = immutable_check
        if not immutable_check['passed']:
            validation_result['valid'] = False
            validation_result['errors'].append(immutable_check['reason'])
            
            # Penalize attempt to modify immutable components
            self._reward_system.evaluate_behavior(
                'evolution',
                {
                    'change_attempted': True,
                    'human_approved': False,
                    'safety_preserved': False,
                }
            )
        
        # Check 2: Risk within limits
        risk_check = self._check_risk_within_limits(evolution)
        validation_result['checks']['risk_within_limits'] = risk_check
        if not risk_check['passed']:
            validation_result['valid'] = False
            validation_result['errors'].append(risk_check['reason'])
        
        # Check 3: Stability preserved
        stability_check = self._check_stability_preserved(evolution)
        validation_result['checks']['stability_preserved'] = stability_check
        if not stability_check['passed']:
            validation_result['warnings'].append(stability_check['reason'])
        
        # Check 4: Rollback possible
        rollback_check = self._check_rollback_possible(evolution)
        validation_result['checks']['rollback_possible'] = rollback_check
        if not rollback_check['passed']:
            validation_result['valid'] = False
            validation_result['errors'].append(rollback_check['reason'])
        
        # Check 5: Change count within limits
        if len(evolution.changes_to_apply) > self.MAX_CHANGES_PER_EVOLUTION:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f"Too many changes ({len(evolution.changes_to_apply)} > {self.MAX_CHANGES_PER_EVOLUTION})"
            )
        
        # Run custom validators
        for validator in self._safety_validators:
            try:
                result = validator(evolution)
                if not result.get('passed', True):
                    validation_result['warnings'].append(result.get('reason', 'Custom validation failed'))
            except Exception as e:
                logger.error(f"Custom validator error: {e}")
        
        # Update evolution status
        evolution.safety_check_passed = validation_result['checks'].get('no_immutable_modification', {}).get('passed', False)
        evolution.stability_check_passed = validation_result['checks'].get('stability_preserved', {}).get('passed', False)
        evolution.validated_at = datetime.now()
        
        if validation_result['valid']:
            evolution.status = EvolutionStatus.PROPOSED  # Ready for approval
            logger.info(f"Evolution {evolution_id} validated successfully")
        else:
            evolution.status = EvolutionStatus.REJECTED
            logger.warning(f"Evolution {evolution_id} failed validation: {validation_result['errors']}")
        
        return validation_result
    
    def approve_evolution(self, evolution_id: str, approver: str) -> bool:
        """
        Approve an evolution for implementation (HUMAN ACTION).
        
        Args:
            evolution_id: ID of the evolution
            approver: Name of the human approver
            
        Returns:
            True if approved successfully
        """
        if evolution_id not in self._evolutions:
            logger.error(f"Evolution {evolution_id} not found")
            return False
        
        evolution = self._evolutions[evolution_id]
        
        if evolution.status not in [EvolutionStatus.PROPOSED, EvolutionStatus.VALIDATING]:
            logger.error(f"Evolution {evolution_id} cannot be approved in status {evolution.status}")
            return False
        
        # Validate before approval
        validation = self.validate_evolution(evolution_id)
        if not validation['valid']:
            logger.error(f"Evolution {evolution_id} failed validation")
            return False
        
        evolution.status = EvolutionStatus.APPROVED
        evolution.approved_at = datetime.now()
        evolution.approved_by = approver
        
        # Also approve the source proposal
        evolution.source_proposal.status = ProposalStatus.APPROVED
        evolution.source_proposal.approved_at = datetime.now()
        evolution.source_proposal.approved_by = approver
        
        logger.info(f"Evolution {evolution_id} approved by {approver}")
        
        # Reward for proper approval flow
        self._reward_system.evaluate_behavior(
            'evolution',
            {
                'human_approved': True,
                'safety_preserved': True,
                'improvement_validated': True,
            }
        )
        
        return True
    
    def reject_evolution(self, evolution_id: str, reason: str) -> bool:
        """
        Reject an evolution (HUMAN ACTION).
        
        Args:
            evolution_id: ID of the evolution
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        if evolution_id not in self._evolutions:
            logger.error(f"Evolution {evolution_id} not found")
            return False
        
        evolution = self._evolutions[evolution_id]
        evolution.status = EvolutionStatus.REJECTED
        
        # Also reject the source proposal
        evolution.source_proposal.status = ProposalStatus.REJECTED
        evolution.source_proposal.rejection_reason = reason
        
        self._evolution_history.append(evolution)
        
        logger.info(f"Evolution {evolution_id} rejected: {reason}")
        
        return True
    
    def implement_evolution(self, evolution_id: str) -> Dict[str, Any]:
        """
        Implement an approved evolution.
        
        Args:
            evolution_id: ID of the evolution
            
        Returns:
            Implementation result
        """
        if evolution_id not in self._evolutions:
            return {'success': False, 'error': 'Evolution not found'}
        
        evolution = self._evolutions[evolution_id]
        
        if evolution.status != EvolutionStatus.APPROVED:
            return {'success': False, 'error': f'Evolution not approved (status: {evolution.status})'}
        
        evolution.status = EvolutionStatus.IMPLEMENTING
        
        result = {
            'success': False,
            'changes_applied': [],
            'errors': [],
        }
        
        try:
            # Create backup
            backup_path = self._create_backup(evolution)
            evolution.backup_created = True
            evolution.backup_path = str(backup_path)
            
            # Apply changes
            for change in evolution.changes_to_apply:
                try:
                    self._apply_change(change)
                    result['changes_applied'].append(change['id'])
                except Exception as e:
                    result['errors'].append(f"Failed to apply change {change['id']}: {e}")
                    # Rollback on error
                    self._rollback_evolution(evolution_id)
                    return result
            
            # Mark as implemented
            evolution.status = EvolutionStatus.IMPLEMENTED
            evolution.implemented_at = datetime.now()
            evolution.source_proposal.status = ProposalStatus.IMPLEMENTED
            evolution.source_proposal.implemented_at = datetime.now()
            
            result['success'] = True
            self._stats['successful_evolutions'] += 1
            
            logger.info(f"Evolution {evolution_id} implemented successfully")
            
        except Exception as e:
            logger.error(f"Error implementing evolution {evolution_id}: {e}")
            result['errors'].append(str(e))
            evolution.status = EvolutionStatus.FAILED
            self._stats['failed_evolutions'] += 1
            
            # Attempt rollback
            self._rollback_evolution(evolution_id)
        
        self._evolution_history.append(evolution)
        
        return result
    
    def _rollback_evolution(self, evolution_id: str) -> bool:
        """Rollback an evolution"""
        if evolution_id not in self._evolutions:
            return False
        
        evolution = self._evolutions[evolution_id]
        
        if not evolution.backup_created or not evolution.backup_path:
            logger.error(f"Cannot rollback {evolution_id}: no backup")
            return False
        try:
        
            # Restore from backup
            backup_path = Path(evolution.backup_path)
            if backup_path.exists():
                with open(backup_path, 'r') as f:
                    backup_state = json.load(f)
                
                # Restore state
                self._current_state = backup_state
                
                evolution.status = EvolutionStatus.ROLLED_BACK
                self._stats['rolled_back'] += 1
                
                logger.info(f"Evolution {evolution_id} rolled back successfully")
                return True
            
        except Exception as e:
            logger.error(f"Error rolling back {evolution_id}: {e}")
        
        return False
    
    def _assess_risk_level(self, proposal: ImprovementProposal) -> str:
        """Assess risk level of a proposal"""
        # High risk: strategy changes, risk limit changes
        if proposal.proposal_type in [ProposalType.STRATEGY_MODIFICATION, ProposalType.RISK_LIMIT_CHANGE]:
            return 'high'
        
        # Medium risk: parameter adjustments, execution changes
        if proposal.proposal_type in [ProposalType.PARAMETER_ADJUSTMENT, ProposalType.EXECUTION_IMPROVEMENT]:
            return 'medium'
        
        # Low risk: signal filters, data quality fixes
        return 'low'
    
    def _create_rollback_plan(self, proposal: ImprovementProposal) -> str:
        """Create rollback plan for a proposal"""
        return f"Restore {proposal.target_component} to value: {proposal.current_value}"
    
    def _prepare_changes(self, proposal: ImprovementProposal) -> List[Dict[str, Any]]:
        """Prepare changes from a proposal"""
        return [
            {
                'id': f"change_{uuid.uuid4().hex[:8]}",
                'component': proposal.target_component,
                'current_value': proposal.current_value,
                'new_value': proposal.proposed_value,
                'change_type': proposal.proposal_type.value,
            }
        ]
    
    def _estimate_improvement(self, proposal: ImprovementProposal) -> float:
        """Estimate expected improvement from a proposal"""
        # Conservative estimate based on proposal type
        estimates = {
            ProposalType.PARAMETER_ADJUSTMENT: 0.02,  # 2%
            ProposalType.SIGNAL_FILTER_UPDATE: 0.03,  # 3%
            ProposalType.STRATEGY_MODIFICATION: 0.05,  # 5%
            ProposalType.RISK_LIMIT_CHANGE: 0.01,  # 1%
            ProposalType.EXECUTION_IMPROVEMENT: 0.02,  # 2%
            ProposalType.DATA_QUALITY_FIX: 0.01,  # 1%
        }
        return estimates.get(proposal.proposal_type, 0.01)
    
    def _check_no_immutable_modification(self, evolution: EvolutionProposal) -> Dict[str, Any]:
        """Check that no immutable components are being modified"""
        for change in evolution.changes_to_apply:
            component = change.get('component', '')
            for immutable in self.IMMUTABLE_COMPONENTS:
                if immutable in component.lower():
                    return {
                        'passed': False,
                        'reason': f"Cannot modify immutable component: {immutable}",
                    }
        
        return {'passed': True, 'reason': 'No immutable modifications'}
    
    def _check_risk_within_limits(self, evolution: EvolutionProposal) -> Dict[str, Any]:
        """Check that changes don't exceed risk limits"""
        risk_limits = self._reward_system.get_risk_limits()
        
        for change in evolution.changes_to_apply:
            # Check if change affects risk parameters
            if 'risk' in change.get('component', '').lower():
                new_value = change.get('new_value')
                if isinstance(new_value, (int, float)):
                    if new_value > risk_limits.get('max_risk_per_trade', 0.02):
                        return {
                            'passed': False,
                            'reason': f"Proposed risk {new_value} exceeds limit",
                        }
        
        return {'passed': True, 'reason': 'Risk within limits'}
    
    def _check_stability_preserved(self, evolution: EvolutionProposal) -> Dict[str, Any]:
        """Check that system stability is preserved"""
        # Check for chaotic changes
        if len(evolution.changes_to_apply) > 3:
            return {
                'passed': False,
                'reason': 'Too many simultaneous changes may affect stability',
            }
        
        return {'passed': True, 'reason': 'Stability preserved'}
    
    def _check_rollback_possible(self, evolution: EvolutionProposal) -> Dict[str, Any]:
        """Check that rollback is possible"""
        for change in evolution.changes_to_apply:
            if change.get('current_value') is None:
                return {
                    'passed': False,
                    'reason': f"Cannot rollback change {change['id']}: no current value",
                }
        
        return {'passed': True, 'reason': 'Rollback possible'}
    
    def _create_backup(self, evolution: EvolutionProposal) -> Path:
        """Create backup before implementing evolution"""
        backup_file = self._backup_path / f"backup_{evolution.evolution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_data = {
            'evolution_id': evolution.evolution_id,
            'created_at': datetime.now().isoformat(),
            'state': copy.deepcopy(self._current_state),
            'changes': evolution.changes_to_apply,
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        logger.info(f"Created backup at {backup_file}")
        
        return backup_file
    
    def _apply_change(self, change: Dict[str, Any]):
        """Apply a single change"""
        # In a real implementation, this would modify the actual system
        # For now, we just update our internal state
        component = change['component']
        new_value = change['new_value']
        
        self._current_state[component] = new_value
        
        logger.info(f"Applied change to {component}: {new_value}")
    
    def add_safety_validator(self, validator: Callable):
        """Add a custom safety validator"""
        self._safety_validators.append(validator)
    
    def add_stability_validator(self, validator: Callable):
        """Add a custom stability validator"""
        self._stability_validators.append(validator)
    
    def get_pending_evolutions(self) -> List[EvolutionProposal]:
        """Get all pending evolutions"""
        return [
            e for e in self._evolutions.values()
            if e.status in [EvolutionStatus.PROPOSED, EvolutionStatus.VALIDATING]
        ]
    
    def get_evolution(self, evolution_id: str) -> Optional[EvolutionProposal]:
        """Get an evolution by ID"""
        return self._evolutions.get(evolution_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            **self._stats,
            'pending_evolutions': len(self.get_pending_evolutions()),
            'success_rate': (
                self._stats['successful_evolutions'] / self._stats['total_evolutions']
                if self._stats['total_evolutions'] > 0 else 0
            ),
        }
