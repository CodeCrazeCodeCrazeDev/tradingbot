"""
Human-in-Loop Approval System
Threshold-based approval workflows for large orders and critical actions
"""

import asyncio
import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ApprovalType(Enum):
    """Types of actions requiring approval"""
    LARGE_ORDER = "large_order"
    POSITION_INCREASE = "position_increase"
    NEW_SYMBOL = "new_symbol"
    STRATEGY_CHANGE = "strategy_change"
    RISK_OVERRIDE = "risk_override"
    EMERGENCY_ACTION = "emergency_action"
    WITHDRAWAL = "withdrawal"
    CONFIG_CHANGE = "config_change"
    SYSTEM_RESTART = "system_restart"


class ApprovalStatus(Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"


@dataclass
class ApprovalDecision:
    """Decision on an approval request"""
    status: ApprovalStatus
    approver: str
    timestamp: datetime
    reason: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class ApprovalRequest:
    """Approval request details"""
    request_id: str
    approval_type: ApprovalType
    requester: str
    timestamp: datetime
    expires_at: datetime
    details: Dict[str, Any]
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: Optional[ApprovalDecision] = None
    notifications_sent: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'approval_type': self.approval_type.value,
            'requester': self.requester,
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'details': self.details,
            'priority': self.priority,
            'status': self.status.value,
            'decision': {
                'status': self.decision.status.value,
                'approver': self.decision.approver,
                'timestamp': self.decision.timestamp.isoformat(),
                'reason': self.decision.reason
            } if self.decision else None
        }


@dataclass
class ApprovalThreshold:
    """Threshold configuration for auto-approval"""
    approval_type: ApprovalType
    auto_approve_below: Optional[float] = None
    auto_reject_above: Optional[float] = None
    require_approval_above: float = 0
    timeout_seconds: int = 300
    default_on_timeout: ApprovalStatus = ApprovalStatus.REJECTED
    required_approvers: int = 1
    allowed_approvers: List[str] = field(default_factory=list)


class HumanApprovalSystem:
    """
    Human-in-Loop approval system for critical trading decisions
    """
    
    DEFAULT_THRESHOLDS = {
        ApprovalType.LARGE_ORDER: ApprovalThreshold(
            ApprovalType.LARGE_ORDER,
            auto_approve_below=10000,
            auto_reject_above=1000000,
            require_approval_above=50000,
            timeout_seconds=300,
            default_on_timeout=ApprovalStatus.REJECTED
        ),
        ApprovalType.POSITION_INCREASE: ApprovalThreshold(
            ApprovalType.POSITION_INCREASE,
            auto_approve_below=5000,
            require_approval_above=25000,
            timeout_seconds=180
        ),
        ApprovalType.RISK_OVERRIDE: ApprovalThreshold(
            ApprovalType.RISK_OVERRIDE,
            require_approval_above=0,
            timeout_seconds=600,
            required_approvers=2
        ),
        ApprovalType.EMERGENCY_ACTION: ApprovalThreshold(
            ApprovalType.EMERGENCY_ACTION,
            require_approval_above=0,
            timeout_seconds=60,
            default_on_timeout=ApprovalStatus.AUTO_APPROVED
        ),
        ApprovalType.STRATEGY_CHANGE: ApprovalThreshold(
            ApprovalType.STRATEGY_CHANGE,
            require_approval_above=0,
            timeout_seconds=3600
        ),
        ApprovalType.CONFIG_CHANGE: ApprovalThreshold(
            ApprovalType.CONFIG_CHANGE,
            require_approval_above=0,
            timeout_seconds=1800
        ),
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.thresholds: Dict[ApprovalType, ApprovalThreshold] = {}
        self._load_thresholds()
        
        # Pending requests
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.request_history: List[ApprovalRequest] = []
        self.max_history = self.config.get('max_history', 1000)
        
        # Callbacks
        self.notification_callback: Optional[Callable[[ApprovalRequest], Awaitable[None]]] = None
        self.decision_callback: Optional[Callable[[ApprovalRequest], Awaitable[None]]] = None
        
        # Approvers
        self.authorized_approvers: Dict[str, List[ApprovalType]] = {}
        self._load_approvers()
        
        # Auto-approval rules
        self.auto_approval_enabled = self.config.get('auto_approval_enabled', True)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'approved': 0,
            'rejected': 0,
            'expired': 0,
            'auto_approved': 0,
            'auto_rejected': 0,
            'avg_response_time': 0
        }
        
        logger.info("Human approval system initialized")
        
    def _load_thresholds(self):
        """Load approval thresholds from config"""
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        
        custom_thresholds = self.config.get('thresholds', {})
        for type_str, threshold_config in custom_thresholds.items():
            try:
                approval_type = ApprovalType(type_str)
                self.thresholds[approval_type] = ApprovalThreshold(
                    approval_type=approval_type,
                    auto_approve_below=threshold_config.get('auto_approve_below'),
                    auto_reject_above=threshold_config.get('auto_reject_above'),
                    require_approval_above=threshold_config.get('require_approval_above', 0),
                    timeout_seconds=threshold_config.get('timeout_seconds', 300),
                    default_on_timeout=ApprovalStatus(threshold_config.get('default_on_timeout', 'rejected')),
                    required_approvers=threshold_config.get('required_approvers', 1)
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid threshold config for {type_str}: {e}")
                
    def _load_approvers(self):
        """Load authorized approvers from config"""
        approvers_config = self.config.get('approvers', {})
        for approver_id, permissions in approvers_config.items():
            if permissions == 'all':
                self.authorized_approvers[approver_id] = list(ApprovalType)
            else:
                self.authorized_approvers[approver_id] = [
                    ApprovalType(p) for p in permissions if p in [t.value for t in ApprovalType]
                ]
                
    def set_notification_callback(self, callback: Callable[[ApprovalRequest], Awaitable[None]]):
        """Set callback for sending notifications"""
        self.notification_callback = callback
        
    def set_decision_callback(self, callback: Callable[[ApprovalRequest], Awaitable[None]]):
        """Set callback for when decisions are made"""
        self.decision_callback = callback
        
    async def request_approval(
        self,
        approval_type: ApprovalType,
        details: Dict[str, Any],
        requester: str = "system",
        priority: int = 2,
        value: Optional[float] = None
    ) -> ApprovalRequest:
        """
        Request approval for an action
        
        Args:
            approval_type: Type of approval needed
            details: Details about the action
            requester: Who/what is requesting
            priority: 1-4 priority level
            value: Numeric value for threshold comparison
            
        Returns:
            ApprovalRequest with status
        """
        threshold = self.thresholds.get(approval_type, ApprovalThreshold(approval_type))
        
        # Create request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            approval_type=approval_type,
            requester=requester,
            timestamp=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=threshold.timeout_seconds),
            details=details,
            priority=priority
        )
        
        self.stats['total_requests'] += 1
        
        # Check auto-approval/rejection
        if self.auto_approval_enabled and value is not None:
            if threshold.auto_approve_below and value < threshold.auto_approve_below:
                request.status = ApprovalStatus.AUTO_APPROVED
                request.decision = ApprovalDecision(
                    status=ApprovalStatus.AUTO_APPROVED,
                    approver="system",
                    timestamp=datetime.now(),
                    reason=f"Value {value} below auto-approve threshold {threshold.auto_approve_below}"
                )
                self.stats['auto_approved'] += 1
                logger.info(f"Auto-approved request {request.request_id}: {approval_type.value}")
                self._add_to_history(request)
                return request
                
            if threshold.auto_reject_above and value > threshold.auto_reject_above:
                request.status = ApprovalStatus.AUTO_REJECTED
                request.decision = ApprovalDecision(
                    status=ApprovalStatus.AUTO_REJECTED,
                    approver="system",
                    timestamp=datetime.now(),
                    reason=f"Value {value} above auto-reject threshold {threshold.auto_reject_above}"
                )
                self.stats['auto_rejected'] += 1
                logger.info(f"Auto-rejected request {request.request_id}: {approval_type.value}")
                self._add_to_history(request)
                return request
        
        # Requires human approval
        self.pending_requests[request.request_id] = request
        logger.info(f"Approval requested: {request.request_id} for {approval_type.value}")
        
        # Send notification
        if self.notification_callback:
            try:
                await self.notification_callback(request)
                request.notifications_sent.append(datetime.now().isoformat())
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                
        return request
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        reason: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Approve a pending request
        
        Args:
            request_id: ID of request to approve
            approver: ID of approver
            reason: Optional reason
            conditions: Optional conditions for approval
            
        Returns:
            True if approved successfully
        """
        request = self.pending_requests.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
            
        if request.is_expired():
            await self._handle_expiry(request)
            return False
            
        # Check authorization
        if not self._is_authorized(approver, request.approval_type):
            logger.warning(f"Approver {approver} not authorized for {request.approval_type.value}")
            return False
            
        # Approve
        request.status = ApprovalStatus.APPROVED
        request.decision = ApprovalDecision(
            status=ApprovalStatus.APPROVED,
            approver=approver,
            timestamp=datetime.now(),
            reason=reason,
            conditions=conditions
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        self.stats['approved'] += 1
        self._update_response_time(request)
        
        logger.info(f"Request {request_id} approved by {approver}")
        
        if self.decision_callback:
            await self.decision_callback(request)
            
        return True
    
    async def reject(
        self,
        request_id: str,
        approver: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject a pending request
        """
        request = self.pending_requests.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
            
        # Check authorization
        if not self._is_authorized(approver, request.approval_type):
            logger.warning(f"Approver {approver} not authorized for {request.approval_type.value}")
            return False
            
        # Reject
        request.status = ApprovalStatus.REJECTED
        request.decision = ApprovalDecision(
            status=ApprovalStatus.REJECTED,
            approver=approver,
            timestamp=datetime.now(),
            reason=reason
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        self.stats['rejected'] += 1
        self._update_response_time(request)
        
        logger.info(f"Request {request_id} rejected by {approver}")
        
        if self.decision_callback:
            await self.decision_callback(request)
            
        return True
    
    async def cancel(self, request_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending request"""
        request = self.pending_requests.get(request_id)
        if not request:
            return False
            
        request.status = ApprovalStatus.CANCELLED
        request.decision = ApprovalDecision(
            status=ApprovalStatus.CANCELLED,
            approver="system",
            timestamp=datetime.now(),
            reason=reason
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        
        logger.info(f"Request {request_id} cancelled")
        return True
    
    async def wait_for_approval(
        self,
        request_id: str,
        timeout: Optional[int] = None
    ) -> ApprovalRequest:
        """
        Wait for approval decision
        
        Args:
            request_id: Request to wait for
            timeout: Override timeout in seconds
            
        Returns:
            ApprovalRequest with final status
        """
        request = self.pending_requests.get(request_id)
        if not request:
            # Check history
            for req in reversed(self.request_history):
                if req.request_id == request_id:
                    return req
            raise ValueError(f"Request {request_id} not found")
            
        threshold = self.thresholds.get(request.approval_type)
        wait_timeout = timeout or (threshold.timeout_seconds if threshold else 300)
        
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < wait_timeout:
            # Check if decided
            if request_id not in self.pending_requests:
                for req in reversed(self.request_history):
                    if req.request_id == request_id:
                        return req
                        
            # Check expiry
            if request.is_expired():
                await self._handle_expiry(request)
                return request
                
            await asyncio.sleep(1)
            
        # Timeout - handle according to threshold
        await self._handle_expiry(request)
        return request
    
    async def _handle_expiry(self, request: ApprovalRequest):
        """Handle expired request"""
        threshold = self.thresholds.get(request.approval_type)
        default_status = threshold.default_on_timeout if threshold else ApprovalStatus.REJECTED
        
        if default_status == ApprovalStatus.AUTO_APPROVED:
            request.status = ApprovalStatus.AUTO_APPROVED
            self.stats['auto_approved'] += 1
        else:
            request.status = ApprovalStatus.EXPIRED
            self.stats['expired'] += 1
            
        request.decision = ApprovalDecision(
            status=request.status,
            approver="system",
            timestamp=datetime.now(),
            reason="Request expired"
        )
        
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]
        self._add_to_history(request)
        
        logger.info(f"Request {request.request_id} expired with status {request.status.value}")
        
        if self.decision_callback:
            await self.decision_callback(request)
    
    def _is_authorized(self, approver: str, approval_type: ApprovalType) -> bool:
        """Check if approver is authorized"""
        if not self.authorized_approvers:
            return True  # No restrictions configured
        permissions = self.authorized_approvers.get(approver, [])
        return approval_type in permissions or not permissions
    
    def _add_to_history(self, request: ApprovalRequest):
        """Add request to history"""
        self.request_history.append(request)
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history:]
            
    def _update_response_time(self, request: ApprovalRequest):
        """Update average response time"""
        if request.decision:
            response_time = (request.decision.timestamp - request.timestamp).total_seconds()
            total_decided = self.stats['approved'] + self.stats['rejected']
            if total_decided > 0:
                self.stats['avg_response_time'] = (
                    (self.stats['avg_response_time'] * (total_decided - 1) + response_time) / total_decided
                )
    
    def get_pending_requests(self, approval_type: Optional[ApprovalType] = None) -> List[ApprovalRequest]:
        """Get all pending requests"""
        requests = list(self.pending_requests.values())
        if approval_type:
            requests = [r for r in requests if r.approval_type == approval_type]
        return sorted(requests, key=lambda r: (-r.priority, r.timestamp))
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request"""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]
        for req in reversed(self.request_history):
            if req.request_id == request_id:
                return req
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        return {
            **self.stats,
            'pending_count': len(self.pending_requests),
            'history_count': len(self.request_history),
            'approval_rate': self.stats['approved'] / max(1, self.stats['total_requests']),
        }
    
    async def check_expired(self):
        """Check and handle expired requests"""
        expired = [r for r in self.pending_requests.values() if r.is_expired()]
        for request in expired:
            await self._handle_expiry(request)
            
    async def run_expiry_checker(self, interval: int = 30):
        """Run periodic expiry checker"""
        while True:
            await self.check_expired()
            await asyncio.sleep(interval)


# Convenience function for order approval
async def request_order_approval(
    order_value: float,
    symbol: str,
    side: str,
    quantity: float,
    approval_system: HumanApprovalSystem
) -> Tuple[bool, Optional[str]]:
    """
    Request approval for an order
    
    Returns:
        Tuple of (approved, request_id or rejection reason)
    """
    request = await approval_system.request_approval(
        approval_type=ApprovalType.LARGE_ORDER,
        details={
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'value': order_value
        },
        value=order_value,
        priority=2 if order_value < 100000 else 3
    )
    
    if request.status in [ApprovalStatus.AUTO_APPROVED, ApprovalStatus.APPROVED]:
        return True, request.request_id
    elif request.status in [ApprovalStatus.AUTO_REJECTED, ApprovalStatus.REJECTED]:
        return False, request.decision.reason if request.decision else "Rejected"
    else:
        # Wait for decision
        result = await approval_system.wait_for_approval(request.request_id)
        if result.status in [ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED]:
            return True, result.request_id
        return False, result.decision.reason if result.decision else "Not approved"


from typing import Tuple
from typing import Set
from enum import auto

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


