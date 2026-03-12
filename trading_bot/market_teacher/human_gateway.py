"""
Human Approval Gateway
=======================
Human-in-the-loop system for all major decisions.

Features:
- Approval request management
- Human override capabilities
- Dashboard interface
- Audit trail
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import deque
import json

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    MODIFIED = "modified"


class ApprovalPriority(Enum):
    """Priority of approval requests"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    request_type: str
    priority: ApprovalPriority
    title: str
    description: str
    details: Dict = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    modifications: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'request_type': self.request_type,
            'priority': self.priority.value,
            'title': self.title,
            'description': self.description,
            'details': self.details,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'rejection_reason': self.rejection_reason,
            'modifications': self.modifications
        }


@dataclass
class HumanOverride:
    """Record of a human override action"""
    override_id: str
    override_type: str
    action: str
    reason: str
    operator: str
    timestamp: datetime = field(default_factory=datetime.now)
    affected_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'override_id': self.override_id,
            'override_type': self.override_type,
            'action': self.action,
            'reason': self.reason,
            'operator': self.operator,
            'timestamp': self.timestamp.isoformat(),
            'affected_components': self.affected_components
        }


class DashboardInterface:
    """
    Interface for human dashboard.
    
    Provides:
    - Pending approvals view
    - System status
    - Override controls
    - Audit log
    """
    
    def __init__(self):
        self.notifications: deque = deque(maxlen=1000)
        self.alerts: deque = deque(maxlen=100)
        
    def add_notification(self, notification: Dict):
        """Add a notification"""
        notification['timestamp'] = datetime.now().isoformat()
        self.notifications.append(notification)
    
    def add_alert(self, alert: Dict):
        """Add an alert"""
        alert['timestamp'] = datetime.now().isoformat()
        self.alerts.append(alert)
        logger.warning(f"ALERT: {alert.get('message', 'Unknown alert')}")
    
    def get_pending_approvals(self, gateway: 'HumanApprovalGateway') -> List[Dict]:
        """Get all pending approvals"""
        return [r.to_dict() for r in gateway.pending_requests.values()]
    
    def get_recent_notifications(self, count: int = 50) -> List[Dict]:
        """Get recent notifications"""
        return list(self.notifications)[-count:]
    
    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        return list(self.alerts)
    
    def get_system_status(self, gateway: 'HumanApprovalGateway') -> Dict:
        """Get overall system status"""
        return {
            'pending_approvals': len(gateway.pending_requests),
            'approved_today': gateway.get_approvals_today(),
            'rejected_today': gateway.get_rejections_today(),
            'active_alerts': len(self.alerts),
            'last_human_action': gateway.last_human_action.isoformat() if gateway.last_human_action else None
        }


class HumanApprovalGateway:
    """
    Gateway for all human approvals.
    
    All major decisions must pass through this gateway.
    Human has final say on everything.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.default_expiry_hours = config.get('default_expiry_hours', 24)
        self.auto_reject_expired = config.get('auto_reject_expired', True)
        
        # Request storage
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approved_requests: Dict[str, ApprovalRequest] = {}
        self.rejected_requests: Dict[str, ApprovalRequest] = {}
        
        # Override history
        self.overrides: List[HumanOverride] = []
        
        # Dashboard
        self.dashboard = DashboardInterface()
        
        # Callbacks
        self._approval_callbacks: List[Callable] = []
        self._rejection_callbacks: List[Callable] = []
        
        # Tracking
        self.last_human_action: Optional[datetime] = None
        self.approvals_by_date: Dict[str, int] = {}
        self.rejections_by_date: Dict[str, int] = {}
        
        logger.info("HumanApprovalGateway initialized")
    
    def request_approval(
        self,
        request_type: str,
        title: str,
        description: str,
        details: Dict = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        expiry_hours: Optional[int] = None
    ) -> ApprovalRequest:
        """
        Submit a request for human approval.
        
        Returns the created request.
        """
        request_id = f"req_{datetime.now().timestamp()}"
        
        expiry = None
        if expiry_hours or self.default_expiry_hours:
            hours = expiry_hours or self.default_expiry_hours
            expiry = datetime.now() + timedelta(hours=hours)
        
        request = ApprovalRequest(
            request_id=request_id,
            request_type=request_type,
            priority=priority,
            title=title,
            description=description,
            details=details or {},
            expires_at=expiry
        )
        
        self.pending_requests[request_id] = request
        
        # Notify dashboard
        self.dashboard.add_notification({
            'type': 'NEW_APPROVAL_REQUEST',
            'request_id': request_id,
            'title': title,
            'priority': priority.value
        })
        
        if priority == ApprovalPriority.CRITICAL:
            self.dashboard.add_alert({
                'type': 'CRITICAL_APPROVAL_NEEDED',
                'message': f"Critical approval needed: {title}",
                'request_id': request_id
            })
        
        logger.info(f"Approval requested: {title} (ID: {request_id})")
        
        return request
    
    def approve(
        self,
        request_id: str,
        approver: str,
        modifications: List[str] = None
    ) -> bool:
        """
        Approve a pending request.
        
        Returns True if successful.
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_requests.pop(request_id)
        request.status = ApprovalStatus.APPROVED if not modifications else ApprovalStatus.MODIFIED
        request.approved_at = datetime.now()
        request.approved_by = approver
        request.modifications = modifications or []
        
        self.approved_requests[request_id] = request
        self.last_human_action = datetime.now()
        
        # Track by date
        date_key = datetime.now().strftime('%Y-%m-%d')
        self.approvals_by_date[date_key] = self.approvals_by_date.get(date_key, 0) + 1
        
        # Notify callbacks
        for callback in self._approval_callbacks:
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Approval callback failed: {e}")
        
        logger.info(f"✓ Request approved by {approver}: {request.title}")
        
        return True
    
    def reject(
        self,
        request_id: str,
        rejector: str,
        reason: str = ""
    ) -> bool:
        """
        Reject a pending request.
        
        Returns True if successful.
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_requests.pop(request_id)
        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejector  # Using same field for rejector
        request.rejection_reason = reason
        
        self.rejected_requests[request_id] = request
        self.last_human_action = datetime.now()
        
        # Track by date
        date_key = datetime.now().strftime('%Y-%m-%d')
        self.rejections_by_date[date_key] = self.rejections_by_date.get(date_key, 0) + 1
        
        # Notify callbacks
        for callback in self._rejection_callbacks:
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Rejection callback failed: {e}")
        
        logger.info(f"✗ Request rejected by {rejector}: {request.title} - {reason}")
        
        return True
    
    def override(
        self,
        override_type: str,
        action: str,
        reason: str,
        operator: str,
        affected_components: List[str] = None
    ) -> HumanOverride:
        """
        Record a human override action.
        
        Human can override any AI decision.
        """
        override = HumanOverride(
            override_id=f"ovr_{datetime.now().timestamp()}",
            override_type=override_type,
            action=action,
            reason=reason,
            operator=operator,
            affected_components=affected_components or []
        )
        
        self.overrides.append(override)
        self.last_human_action = datetime.now()
        
        logger.info(f"🔧 HUMAN OVERRIDE by {operator}: {action}")
        logger.info(f"Reason: {reason}")
        
        return override
    
    def check_expired(self):
        """Check for and handle expired requests"""
        now = datetime.now()
        expired_ids = []
        
        for request_id, request in self.pending_requests.items():
            if request.expires_at and now > request.expires_at:
                expired_ids.append(request_id)
        
        for request_id in expired_ids:
            request = self.pending_requests.pop(request_id)
            request.status = ApprovalStatus.EXPIRED
            self.rejected_requests[request_id] = request
            
            logger.warning(f"Request expired: {request.title}")
    
    def is_approved(self, request_id: str) -> bool:
        """Check if a request is approved"""
        return request_id in self.approved_requests
    
    def is_pending(self, request_id: str) -> bool:
        """Check if a request is pending"""
        return request_id in self.pending_requests
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a request by ID"""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]
        if request_id in self.approved_requests:
            return self.approved_requests[request_id]
        if request_id in self.rejected_requests:
            return self.rejected_requests[request_id]
        return None
    
    def get_approvals_today(self) -> int:
        """Get number of approvals today"""
        date_key = datetime.now().strftime('%Y-%m-%d')
        return self.approvals_by_date.get(date_key, 0)
    
    def get_rejections_today(self) -> int:
        """Get number of rejections today"""
        date_key = datetime.now().strftime('%Y-%m-%d')
        return self.rejections_by_date.get(date_key, 0)
    
    def register_approval_callback(self, callback: Callable):
        """Register callback for approvals"""
        self._approval_callbacks.append(callback)
    
    def register_rejection_callback(self, callback: Callable):
        """Register callback for rejections"""
        self._rejection_callbacks.append(callback)
    
    def get_pending_by_priority(self) -> Dict[str, List[Dict]]:
        """Get pending requests grouped by priority"""
        by_priority = {p.value: [] for p in ApprovalPriority}
        
        for request in self.pending_requests.values():
            by_priority[request.priority.value].append(request.to_dict())
        
        return by_priority
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get audit log of all actions"""
        log = []
        
        # Add approvals
        for request in list(self.approved_requests.values())[-limit//2:]:
            log.append({
                'type': 'APPROVAL',
                'request_id': request.request_id,
                'title': request.title,
                'operator': request.approved_by,
                'timestamp': request.approved_at.isoformat() if request.approved_at else None
            })
        
        # Add rejections
        for request in list(self.rejected_requests.values())[-limit//2:]:
            log.append({
                'type': 'REJECTION',
                'request_id': request.request_id,
                'title': request.title,
                'operator': request.approved_by,
                'reason': request.rejection_reason,
                'timestamp': request.approved_at.isoformat() if request.approved_at else None
            })
        
        # Add overrides
        for override in self.overrides[-limit//4:]:
            log.append({
                'type': 'OVERRIDE',
                'override_id': override.override_id,
                'action': override.action,
                'operator': override.operator,
                'reason': override.reason,
                'timestamp': override.timestamp.isoformat()
            })
        
        # Sort by timestamp
        log.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return log[:limit]
    
    def get_status(self) -> Dict:
        """Get gateway status"""
        return {
            'pending_count': len(self.pending_requests),
            'approved_count': len(self.approved_requests),
            'rejected_count': len(self.rejected_requests),
            'override_count': len(self.overrides),
            'last_human_action': self.last_human_action.isoformat() if self.last_human_action else None,
            'approvals_today': self.get_approvals_today(),
            'rejections_today': self.get_rejections_today(),
            'pending_by_priority': {
                p.value: sum(1 for r in self.pending_requests.values() if r.priority == p)
                for p in ApprovalPriority
            }
        }


# Export all classes
__all__ = [
    'ApprovalStatus',
    'ApprovalPriority',
    'ApprovalRequest',
    'HumanOverride',
    'DashboardInterface',
    'HumanApprovalGateway'
]
