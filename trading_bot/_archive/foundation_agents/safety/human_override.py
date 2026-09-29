"""
Human Override - Human Control and Intervention System
=========================================================

Implements human oversight and control mechanisms:
1. Override triggers and handling
2. Approval workflows
3. Emergency stops
4. Audit logging

Based on the Foundation Agents paper (arXiv:2504.01990) safety systems.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from collections import deque
import uuid
import threading

logger = logging.getLogger(__name__)


class OverrideType(Enum):
    """Types of human overrides"""
    EMERGENCY_STOP = "emergency_stop"
    PAUSE_TRADING = "pause_trading"
    CANCEL_ORDER = "cancel_order"
    MODIFY_POSITION = "modify_position"
    CHANGE_PARAMETERS = "change_parameters"
    APPROVE_ACTION = "approve_action"
    REJECT_ACTION = "reject_action"
    MANUAL_INTERVENTION = "manual_intervention"


class ApprovalStatus(Enum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ControlLevel(Enum):
    """Levels of human control"""
    FULL_AUTONOMY = 1       # AI operates independently
    MONITORED = 2           # Human monitors but doesn't intervene
    SUPERVISED = 3          # Human approves major decisions
    COLLABORATIVE = 4       # Human and AI work together
    HUMAN_IN_LOOP = 5       # Human approves all decisions
    MANUAL_ONLY = 6         # Human makes all decisions


@dataclass
class OverrideEvent:
    """A human override event"""
    event_id: str
    override_type: OverrideType
    
    # Details
    reason: str
    description: str
    
    # Actor
    human_id: str
    
    # Target
    target_type: str  # "order", "position", "strategy", "system"
    target_id: Optional[str] = None
    
    # Action taken
    action_taken: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    executed: bool = False
    execution_result: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'override_type': self.override_type.value,
            'reason': self.reason,
            'human_id': self.human_id,
            'target_type': self.target_type,
            'executed': self.executed,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ApprovalRequest:
    """A request for human approval"""
    request_id: str
    action_type: str
    
    # Details
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Risk assessment
    risk_level: str = "medium"  # low, medium, high, critical
    estimated_impact: str = ""
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # Response
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    
    # Escalation
    escalation_level: int = 0
    escalated_to: Optional[str] = None
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'action_type': self.action_type,
            'description': self.description,
            'risk_level': self.risk_level,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'is_expired': self.is_expired()
        }


@dataclass
class AuditEntry:
    """An audit log entry"""
    entry_id: str
    event_type: str
    
    # Details
    description: str
    actor: str  # human or system
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Before/After state
    before_state: Optional[Dict] = None
    after_state: Optional[Dict] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'entry_id': self.entry_id,
            'event_type': self.event_type,
            'description': self.description,
            'actor': self.actor,
            'timestamp': self.timestamp.isoformat()
        }


class EmergencyStop:
    """Emergency stop mechanism"""
    
    def __init__(self):
        self.is_stopped = False
        self.stop_reason: Optional[str] = None
        self.stopped_at: Optional[datetime] = None
        self.stopped_by: Optional[str] = None
        self.callbacks: List[Callable] = []
        self._lock = threading.Lock()
    
    def trigger(self, reason: str, human_id: str) -> bool:
        """Trigger emergency stop"""
        with self._lock:
            if self.is_stopped:
                return False
            
            self.is_stopped = True
            self.stop_reason = reason
            self.stopped_at = datetime.utcnow()
            self.stopped_by = human_id
            
            # Execute callbacks
            for callback in self.callbacks:
                try:
                    callback(reason, human_id)
                except Exception as e:
                    logger.error(f"Emergency stop callback error: {e}")
            
            logger.critical(f"EMERGENCY STOP triggered by {human_id}: {reason}")
            
            return True
    
    def reset(self, human_id: str, confirmation: str) -> bool:
        """Reset emergency stop"""
        with self._lock:
            if not self.is_stopped:
                return False
            
            if confirmation != "CONFIRM_RESET":
                return False
            
            self.is_stopped = False
            self.stop_reason = None
            self.stopped_at = None
            self.stopped_by = None
            
            logger.info(f"Emergency stop reset by {human_id}")
            
            return True
    
    def register_callback(self, callback: Callable):
        """Register callback for emergency stop"""
        self.callbacks.append(callback)
    
    def status(self) -> Dict:
        return {
            'is_stopped': self.is_stopped,
            'reason': self.stop_reason,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'stopped_by': self.stopped_by
        }


class ApprovalWorkflow:
    """Manages approval workflows"""
    
    def __init__(self, default_timeout_minutes: int = 30):
        self.default_timeout = timedelta(minutes=default_timeout_minutes)
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: deque = deque(maxlen=1000)
        self.approval_callbacks: Dict[str, Callable] = {}
    
    def create_request(
        self,
        action_type: str,
        description: str,
        details: Optional[Dict] = None,
        risk_level: str = "medium",
        timeout_minutes: Optional[int] = None
    ) -> ApprovalRequest:
        """Create an approval request"""
        timeout = timedelta(minutes=timeout_minutes) if timeout_minutes else self.default_timeout
        
        request = ApprovalRequest(
            request_id=str(uuid.uuid4())[:8],
            action_type=action_type,
            description=description,
            details=details or {},
            risk_level=risk_level,
            expires_at=datetime.utcnow() + timeout
        )
        
        self.pending_requests[request.request_id] = request
        
        logger.info(f"Approval request created: {request.request_id}")
        
        return request
    
    def approve(
        self,
        request_id: str,
        human_id: str,
        notes: str = ""
    ) -> bool:
        """Approve a request"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            self.completed_requests.append(request)
            del self.pending_requests[request_id]
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_by = human_id
        request.responded_at = datetime.utcnow()
        request.details['approval_notes'] = notes
        
        self.completed_requests.append(request)
        del self.pending_requests[request_id]
        
        # Execute callback if registered
        if request_id in self.approval_callbacks:
            try:
                self.approval_callbacks[request_id](True, request)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
        
        logger.info(f"Request {request_id} approved by {human_id}")
        
        return True
    
    def reject(
        self,
        request_id: str,
        human_id: str,
        reason: str
    ) -> bool:
        """Reject a request"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        
        request.status = ApprovalStatus.REJECTED
        request.approved_by = human_id
        request.rejection_reason = reason
        request.responded_at = datetime.utcnow()
        
        self.completed_requests.append(request)
        del self.pending_requests[request_id]
        
        # Execute callback if registered
        if request_id in self.approval_callbacks:
            try:
                self.approval_callbacks[request_id](False, request)
            except Exception as e:
                logger.error(f"Rejection callback error: {e}")
        
        logger.info(f"Request {request_id} rejected by {human_id}: {reason}")
        
        return True
    
    def escalate(
        self,
        request_id: str,
        escalate_to: str
    ) -> bool:
        """Escalate a request"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        request.escalation_level += 1
        request.escalated_to = escalate_to
        request.status = ApprovalStatus.ESCALATED
        
        logger.info(f"Request {request_id} escalated to {escalate_to}")
        
        return True
    
    def register_callback(self, request_id: str, callback: Callable):
        """Register callback for approval/rejection"""
        self.approval_callbacks[request_id] = callback
    
    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending requests"""
        # Check for expired
        expired = []
        for rid, request in self.pending_requests.items():
            if request.is_expired():
                request.status = ApprovalStatus.EXPIRED
                expired.append(rid)
        
        for rid in expired:
            self.completed_requests.append(self.pending_requests[rid])
            del self.pending_requests[rid]
        
        return list(self.pending_requests.values())
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request"""
        return self.pending_requests.get(request_id)


class AuditLogger:
    """Logs all human override activities"""
    
    def __init__(self, max_entries: int = 10000):
        self.entries: deque = deque(maxlen=max_entries)
    
    def log(
        self,
        event_type: str,
        description: str,
        actor: str,
        context: Optional[Dict] = None,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None
    ) -> AuditEntry:
        """Log an audit entry"""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4())[:12],
            event_type=event_type,
            description=description,
            actor=actor,
            context=context or {},
            before_state=before_state,
            after_state=after_state
        )
        
        self.entries.append(entry)
        
        return entry
    
    def get_entries(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit entries with filters"""
        results = []
        
        for entry in reversed(self.entries):
            if event_type and entry.event_type != event_type:
                continue
            if actor and entry.actor != actor:
                continue
            if since and entry.timestamp < since:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def export(self, since: Optional[datetime] = None) -> List[Dict]:
        """Export audit log"""
        entries = self.get_entries(since=since, limit=10000)
        return [e.to_dict() for e in entries]


class HumanOverride:
    """
    Human Override System
    
    Provides mechanisms for human oversight, control,
    and intervention in the autonomous trading system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Control level
        self.control_level = ControlLevel(
            self.config.get('control_level', ControlLevel.SUPERVISED.value)
        )
        
        # Components
        self.emergency_stop = EmergencyStop()
        self.approval_workflow = ApprovalWorkflow()
        self.audit_logger = AuditLogger()
        
        # Override history
        self.override_history: List[OverrideEvent] = []
        
        # Authorized users
        self.authorized_users: Set[str] = set(
            self.config.get('authorized_users', ['admin'])
        )
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            'overrides_executed': 0,
            'approvals_requested': 0,
            'approvals_granted': 0,
            'approvals_rejected': 0,
            'emergency_stops': 0
        }
        
        logger.info(f"Human Override initialized with control level: {self.control_level.name}")
    
    def set_control_level(self, level: ControlLevel, human_id: str):
        """Set the control level"""
        if human_id not in self.authorized_users:
            logger.warning(f"Unauthorized control level change attempt by {human_id}")
            return False
        
        old_level = self.control_level
        self.control_level = level
        
        self.audit_logger.log(
            event_type="control_level_change",
            description=f"Control level changed from {old_level.name} to {level.name}",
            actor=human_id,
            before_state={'level': old_level.value},
            after_state={'level': level.value}
        )
        
        logger.info(f"Control level changed to {level.name} by {human_id}")
        
        return True
    
    def trigger_emergency_stop(self, reason: str, human_id: str) -> bool:
        """Trigger emergency stop"""
        if human_id not in self.authorized_users:
            logger.warning(f"Unauthorized emergency stop attempt by {human_id}")
            return False
        
        result = self.emergency_stop.trigger(reason, human_id)
        
        if result:
            self.stats['emergency_stops'] += 1
            
            self.audit_logger.log(
                event_type="emergency_stop",
                description=f"Emergency stop triggered: {reason}",
                actor=human_id
            )
            
            # Create override event
            event = OverrideEvent(
                event_id=str(uuid.uuid4())[:8],
                override_type=OverrideType.EMERGENCY_STOP,
                reason=reason,
                description="Emergency stop triggered",
                human_id=human_id,
                target_type="system",
                executed=True,
                executed_at=datetime.utcnow()
            )
            self.override_history.append(event)
        
        return result
    
    def reset_emergency_stop(self, human_id: str, confirmation: str) -> bool:
        """Reset emergency stop"""
        if human_id not in self.authorized_users:
            return False
        
        result = self.emergency_stop.reset(human_id, confirmation)
        
        if result:
            self.audit_logger.log(
                event_type="emergency_stop_reset",
                description="Emergency stop reset",
                actor=human_id
            )
        
        return result
    
    def request_approval(
        self,
        action_type: str,
        description: str,
        details: Optional[Dict] = None,
        risk_level: str = "medium",
        callback: Optional[Callable] = None
    ) -> ApprovalRequest:
        """Request human approval for an action"""
        request = self.approval_workflow.create_request(
            action_type=action_type,
            description=description,
            details=details,
            risk_level=risk_level
        )
        
        if callback:
            self.approval_workflow.register_callback(request.request_id, callback)
        
        self.stats['approvals_requested'] += 1
        
        self.audit_logger.log(
            event_type="approval_requested",
            description=f"Approval requested: {description}",
            actor="system",
            context={'request_id': request.request_id, 'risk_level': risk_level}
        )
        
        return request
    
    def approve_request(
        self,
        request_id: str,
        human_id: str,
        notes: str = ""
    ) -> bool:
        """Approve a pending request"""
        if human_id not in self.authorized_users:
            return False
        
        result = self.approval_workflow.approve(request_id, human_id, notes)
        
        if result:
            self.stats['approvals_granted'] += 1
            
            self.audit_logger.log(
                event_type="approval_granted",
                description=f"Request {request_id} approved",
                actor=human_id,
                context={'notes': notes}
            )
        
        return result
    
    def reject_request(
        self,
        request_id: str,
        human_id: str,
        reason: str
    ) -> bool:
        """Reject a pending request"""
        if human_id not in self.authorized_users:
            return False
        
        result = self.approval_workflow.reject(request_id, human_id, reason)
        
        if result:
            self.stats['approvals_rejected'] += 1
            
            self.audit_logger.log(
                event_type="approval_rejected",
                description=f"Request {request_id} rejected",
                actor=human_id,
                context={'reason': reason}
            )
        
        return result
    
    def execute_override(
        self,
        override_type: OverrideType,
        reason: str,
        human_id: str,
        target_type: str,
        target_id: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> OverrideEvent:
        """Execute a human override"""
        if human_id not in self.authorized_users:
            raise PermissionError(f"User {human_id} not authorized for overrides")
        
        event = OverrideEvent(
            event_id=str(uuid.uuid4())[:8],
            override_type=override_type,
            reason=reason,
            description=f"{override_type.value} on {target_type}",
            human_id=human_id,
            target_type=target_type,
            target_id=target_id,
            parameters=parameters or {}
        )
        
        # Execute handler if registered
        handler_key = f"{override_type.value}_{target_type}"
        if handler_key in self.action_handlers:
            try:
                result = self.action_handlers[handler_key](event)
                event.executed = True
                event.execution_result = str(result)
                event.executed_at = datetime.utcnow()
            except Exception as e:
                event.executed = False
                event.execution_result = f"Error: {str(e)}"
                logger.error(f"Override execution error: {e}")
        else:
            event.executed = True
            event.execution_result = "No handler registered"
            event.executed_at = datetime.utcnow()
        
        self.override_history.append(event)
        self.stats['overrides_executed'] += 1
        
        self.audit_logger.log(
            event_type="override_executed",
            description=f"{override_type.value}: {reason}",
            actor=human_id,
            context={
                'target_type': target_type,
                'target_id': target_id,
                'parameters': parameters
            }
        )
        
        return event
    
    def register_handler(self, override_type: OverrideType, target_type: str, handler: Callable):
        """Register a handler for override actions"""
        key = f"{override_type.value}_{target_type}"
        self.action_handlers[key] = handler
    
    def requires_approval(self, action_type: str, risk_level: str = "medium") -> bool:
        """Check if an action requires approval based on control level"""
        if self.control_level == ControlLevel.FULL_AUTONOMY:
            return False
        elif self.control_level == ControlLevel.MONITORED:
            return False
        elif self.control_level == ControlLevel.SUPERVISED:
            return risk_level in ["high", "critical"]
        elif self.control_level == ControlLevel.COLLABORATIVE:
            return risk_level in ["medium", "high", "critical"]
        elif self.control_level == ControlLevel.HUMAN_IN_LOOP:
            return True
        elif self.control_level == ControlLevel.MANUAL_ONLY:
            return True
        
        return False
    
    def add_authorized_user(self, user_id: str, added_by: str):
        """Add an authorized user"""
        if added_by not in self.authorized_users:
            return False
        
        self.authorized_users.add(user_id)
        
        self.audit_logger.log(
            event_type="user_authorized",
            description=f"User {user_id} authorized",
            actor=added_by
        )
        
        return True
    
    def remove_authorized_user(self, user_id: str, removed_by: str):
        """Remove an authorized user"""
        if removed_by not in self.authorized_users:
            return False
        
        if user_id == removed_by:
            return False  # Can't remove yourself
        
        self.authorized_users.discard(user_id)
        
        self.audit_logger.log(
            event_type="user_deauthorized",
            description=f"User {user_id} deauthorized",
            actor=removed_by
        )
        
        return True
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        return self.approval_workflow.get_pending()
    
    def get_override_history(
        self,
        override_type: Optional[OverrideType] = None,
        limit: int = 100
    ) -> List[OverrideEvent]:
        """Get override history"""
        history = self.override_history
        
        if override_type:
            history = [e for e in history if e.override_type == override_type]
        
        return history[-limit:]
    
    def get_audit_log(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit log entries"""
        return self.audit_logger.get_entries(since=since, limit=limit)
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall status"""
        return {
            'control_level': self.control_level.name,
            'emergency_stop': self.emergency_stop.status(),
            'pending_approvals': len(self.get_pending_approvals()),
            'authorized_users': len(self.authorized_users),
            'stats': self.stats
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            **self.stats,
            'control_level': self.control_level.name,
            'is_stopped': self.emergency_stop.is_stopped,
            'pending_approvals': len(self.get_pending_approvals()),
            'total_overrides': len(self.override_history),
            'audit_entries': len(self.audit_logger.entries)
        }
