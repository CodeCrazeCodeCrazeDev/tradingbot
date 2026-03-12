"""
Governance Layer
=================

IMMUTABLE governance rules that AI CANNOT change.

PHILOSOPHY:
- AI CAN: try features, tune hyperparameters, test architectures, compare strategies
- AI CANNOT: deploy models, change risk rules, access capital, modify governance
- All changes require HUMAN APPROVAL
- Governance rules are IMMUTABLE

GOVERNANCE PRINCIPLES:
1. SEPARATION OF CONCERNS - Research vs Production
2. HUMAN APPROVAL - All deployments require human
3. IMMUTABLE RULES - AI cannot modify governance
4. AUDIT TRAIL - All activities logged
5. CAPABILITY BOUNDARIES - Clear limits on AI power
"""

import logging
import hashlib
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CapabilityType(Enum):
    """Types of capabilities"""
    # ALLOWED - AI can do these
    TRY_FEATURES = "try_features"
    TUNE_HYPERPARAMETERS = "tune_hyperparameters"
    TEST_ARCHITECTURES = "test_architectures"
    COMPARE_STRATEGIES = "compare_strategies"
    GENERATE_HYPOTHESES = "generate_hypotheses"
    ANALYZE_DATA = "analyze_data"
    RUN_BACKTESTS = "run_backtests"
    PROPOSE_CHANGES = "propose_changes"
    
    # FORBIDDEN - AI cannot do these
    DEPLOY_MODELS = "deploy_models"
    CHANGE_RISK_RULES = "change_risk_rules"
    ACCESS_CAPITAL = "access_capital"
    MODIFY_GOVERNANCE = "modify_governance"
    EXECUTE_TRADES = "execute_trades"
    MODIFY_CONSTRAINTS = "modify_constraints"
    ACCESS_PRODUCTION = "access_production"
    OVERRIDE_HUMAN = "override_human"


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    capability: CapabilityType
    description: str
    details: Dict[str, Any]
    requested_by: str
    requested_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'capability': self.capability.value,
            'description': self.description,
            'details': self.details,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at.isoformat(),
            'status': self.status.value,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason
        }


@dataclass
class ActivityLog:
    """Log of AI activity"""
    log_id: str
    activity_type: str
    capability: CapabilityType
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    allowed: bool
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            'log_id': self.log_id,
            'activity_type': self.activity_type,
            'capability': self.capability.value,
            'description': self.description,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'allowed': self.allowed,
            'reason': self.reason
        }


class GovernanceLayer:
    """
    Immutable governance layer.
    
    CORE PRINCIPLE:
    AI CANNOT modify governance rules.
    """
    
    # IMMUTABLE ALLOWED CAPABILITIES
    ALLOWED_CAPABILITIES: FrozenSet[CapabilityType] = frozenset([
        CapabilityType.TRY_FEATURES,
        CapabilityType.TUNE_HYPERPARAMETERS,
        CapabilityType.TEST_ARCHITECTURES,
        CapabilityType.COMPARE_STRATEGIES,
        CapabilityType.GENERATE_HYPOTHESES,
        CapabilityType.ANALYZE_DATA,
        CapabilityType.RUN_BACKTESTS,
        CapabilityType.PROPOSE_CHANGES
    ])
    
    # IMMUTABLE FORBIDDEN CAPABILITIES
    FORBIDDEN_CAPABILITIES: FrozenSet[CapabilityType] = frozenset([
        CapabilityType.DEPLOY_MODELS,
        CapabilityType.CHANGE_RISK_RULES,
        CapabilityType.ACCESS_CAPITAL,
        CapabilityType.MODIFY_GOVERNANCE,
        CapabilityType.EXECUTE_TRADES,
        CapabilityType.MODIFY_CONSTRAINTS,
        CapabilityType.ACCESS_PRODUCTION,
        CapabilityType.OVERRIDE_HUMAN
    ])
    
    # IMMUTABLE GOVERNANCE RULES
    GOVERNANCE_RULES: FrozenSet[str] = frozenset([
        "all_deployments_require_human_approval",
        "ai_cannot_modify_governance",
        "ai_cannot_access_production",
        "ai_cannot_execute_real_trades",
        "ai_cannot_change_risk_parameters",
        "all_activities_must_be_logged",
        "human_override_always_works",
        "governance_rules_are_immutable"
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Verify immutability
        self._verify_immutability()
        
        # Approval requests
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        
        # Activity log
        self.activity_log: List[ActivityLog] = []
        
        # Statistics
        self.allowed_count = 0
        self.blocked_count = 0
        self.pending_approvals = 0
        
        logger.info("GovernanceLayer initialized with immutable rules")
    
    def _verify_immutability(self):
        """Verify that governance rules are immutable"""
        # These are frozensets - they cannot be modified
        assert isinstance(self.ALLOWED_CAPABILITIES, frozenset), "ALLOWED_CAPABILITIES must be immutable"
        assert isinstance(self.FORBIDDEN_CAPABILITIES, frozenset), "FORBIDDEN_CAPABILITIES must be immutable"
        assert isinstance(self.GOVERNANCE_RULES, frozenset), "GOVERNANCE_RULES must be immutable"
        
        # Verify no overlap
        overlap = self.ALLOWED_CAPABILITIES & self.FORBIDDEN_CAPABILITIES
        assert len(overlap) == 0, f"Overlap between allowed and forbidden: {overlap}"
    
    def check_capability(
        self,
        capability: CapabilityType,
        context: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Check if a capability is allowed.
        
        Args:
            capability: Capability to check
            context: Optional context
            
        Returns:
            Tuple of (allowed, reason)
        """
        with self.lock:
            # Log the check
            log_id = self._generate_id("check")
            
            # Check if forbidden
            if capability in self.FORBIDDEN_CAPABILITIES:
                reason = f"Capability {capability.value} is FORBIDDEN by governance"
                self._log_activity(
                    log_id=log_id,
                    activity_type="capability_check",
                    capability=capability,
                    description=f"Checked capability: {capability.value}",
                    details=context or {},
                    allowed=False,
                    reason=reason
                )
                self.blocked_count += 1
                return False, reason
            
            # Check if allowed
            if capability in self.ALLOWED_CAPABILITIES:
                reason = f"Capability {capability.value} is ALLOWED"
                self._log_activity(
                    log_id=log_id,
                    activity_type="capability_check",
                    capability=capability,
                    description=f"Checked capability: {capability.value}",
                    details=context or {},
                    allowed=True,
                    reason=reason
                )
                self.allowed_count += 1
                return True, reason
            
            # Unknown capability - default to forbidden
            reason = f"Unknown capability {capability.value} - defaulting to FORBIDDEN"
            self._log_activity(
                log_id=log_id,
                activity_type="capability_check",
                capability=capability,
                description=f"Checked unknown capability: {capability.value}",
                details=context or {},
                allowed=False,
                reason=reason
            )
            self.blocked_count += 1
            return False, reason
    
    def request_approval(
        self,
        capability: CapabilityType,
        description: str,
        details: Dict[str, Any],
        requested_by: str = "AI"
    ) -> ApprovalRequest:
        """
        Request human approval for a capability.
        
        Args:
            capability: Capability requesting approval for
            description: Description of request
            details: Details of request
            requested_by: Who is requesting
            
        Returns:
            ApprovalRequest
        """
        with self.lock:
            request_id = self._generate_id("approval")
            
            request = ApprovalRequest(
                request_id=request_id,
                capability=capability,
                description=description,
                details=details,
                requested_by=requested_by,
                requested_at=datetime.now()
            )
            
            self.approval_requests[request_id] = request
            self.pending_approvals += 1
            
            # Log
            self._log_activity(
                log_id=self._generate_id("log"),
                activity_type="approval_request",
                capability=capability,
                description=f"Requested approval: {description}",
                details=details,
                allowed=False,
                reason="Awaiting human approval"
            )
            
            logger.info(
                "Approval requested [%s]: %s - %s",
                request_id,
                capability.value,
                description
            )
            
            return request
    
    def approve(
        self,
        request_id: str,
        approved_by: str,
        notes: str = ""
    ) -> bool:
        """
        Approve a request (HUMAN ONLY).
        
        Args:
            request_id: ID of request to approve
            approved_by: Human approver
            notes: Optional notes
            
        Returns:
            True if approved
        """
        with self.lock:
            if request_id not in self.approval_requests:
                logger.error("Approval request %s not found", request_id)
                return False
            
            request = self.approval_requests[request_id]
            
            if request.status != ApprovalStatus.PENDING:
                logger.error("Request %s already processed", request_id)
                return False
            
            request.status = ApprovalStatus.APPROVED
            request.approved_by = approved_by
            request.approved_at = datetime.now()
            self.pending_approvals -= 1
            
            # Log
            self._log_activity(
                log_id=self._generate_id("log"),
                activity_type="approval_granted",
                capability=request.capability,
                description=f"Approved by {approved_by}: {request.description}",
                details={'notes': notes},
                allowed=True,
                reason=f"Approved by {approved_by}"
            )
            
            logger.info(
                "APPROVED [%s] by %s: %s",
                request_id,
                approved_by,
                request.description
            )
            
            return True
    
    def reject(
        self,
        request_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """
        Reject a request (HUMAN ONLY).
        
        Args:
            request_id: ID of request to reject
            rejected_by: Human rejector
            reason: Rejection reason
            
        Returns:
            True if rejected
        """
        with self.lock:
            if request_id not in self.approval_requests:
                logger.error("Approval request %s not found", request_id)
                return False
            
            request = self.approval_requests[request_id]
            
            if request.status != ApprovalStatus.PENDING:
                logger.error("Request %s already processed", request_id)
                return False
            
            request.status = ApprovalStatus.REJECTED
            request.rejection_reason = reason
            self.pending_approvals -= 1
            
            # Log
            self._log_activity(
                log_id=self._generate_id("log"),
                activity_type="approval_rejected",
                capability=request.capability,
                description=f"Rejected by {rejected_by}: {request.description}",
                details={'reason': reason},
                allowed=False,
                reason=f"Rejected: {reason}"
            )
            
            logger.info(
                "REJECTED [%s] by %s: %s - %s",
                request_id,
                rejected_by,
                request.description,
                reason
            )
            
            return True
    
    def is_approved(self, request_id: str) -> bool:
        """Check if a request is approved"""
        with self.lock:
            if request_id not in self.approval_requests:
                return False
            return self.approval_requests[request_id].status == ApprovalStatus.APPROVED
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        with self.lock:
            return [
                req for req in self.approval_requests.values()
                if req.status == ApprovalStatus.PENDING
            ]
    
    def _log_activity(
        self,
        log_id: str,
        activity_type: str,
        capability: CapabilityType,
        description: str,
        details: Dict[str, Any],
        allowed: bool,
        reason: str
    ):
        """Log an activity"""
        log = ActivityLog(
            log_id=log_id,
            activity_type=activity_type,
            capability=capability,
            description=description,
            details=details,
            timestamp=datetime.now(),
            allowed=allowed,
            reason=reason
        )
        self.activity_log.append(log)
    
    def get_activity_log(
        self,
        limit: int = 100,
        capability: Optional[CapabilityType] = None
    ) -> List[ActivityLog]:
        """Get activity log"""
        with self.lock:
            logs = self.activity_log
            
            if capability:
                logs = [l for l in logs if l.capability == capability]
            
            return logs[-limit:]
    
    def get_governance_rules(self) -> List[str]:
        """Get all governance rules"""
        return list(self.GOVERNANCE_RULES)
    
    def get_allowed_capabilities(self) -> List[str]:
        """Get allowed capabilities"""
        return [c.value for c in self.ALLOWED_CAPABILITIES]
    
    def get_forbidden_capabilities(self) -> List[str]:
        """Get forbidden capabilities"""
        return [c.value for c in self.FORBIDDEN_CAPABILITIES]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get governance statistics"""
        with self.lock:
            return {
                'allowed_count': self.allowed_count,
                'blocked_count': self.blocked_count,
                'pending_approvals': self.pending_approvals,
                'total_approvals': len(self.approval_requests),
                'activity_log_size': len(self.activity_log),
                'governance_rules': list(self.GOVERNANCE_RULES),
                'allowed_capabilities': [c.value for c in self.ALLOWED_CAPABILITIES],
                'forbidden_capabilities': [c.value for c in self.FORBIDDEN_CAPABILITIES]
            }
    
    def _generate_id(self, prefix: str) -> str:
        return hashlib.md5(
            f"{prefix}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
