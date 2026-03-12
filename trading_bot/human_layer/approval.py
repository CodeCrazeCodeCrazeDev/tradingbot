"""
AlphaAlgo Human Approval Gate - Critical Action Approval

This module handles human approval for critical actions.
The bot CANNOT bypass this layer for restricted actions.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import asyncio
import uuid
import json
from pathlib import Path
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



logger = logging.getLogger(__name__)


class ApprovalLevel(Enum):
    """Level of approval required"""
    AUTO = "auto"           # No approval needed
    NOTIFY = "notify"       # Notify but don't wait
    STANDARD = "standard"   # Wait for approval (1 hour timeout)
    CRITICAL = "critical"   # Wait for approval (no timeout)
    FORBIDDEN = "forbidden" # Never allowed


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """A request for human approval"""
    request_id: str
    action: str
    level: ApprovalLevel
    status: ApprovalStatus
    
    # Details
    description: str
    details: Dict[str, Any]
    risk_assessment: str
    
    # Timing
    created_at: datetime
    timeout_at: Optional[datetime]
    responded_at: Optional[datetime] = None
    
    # Response
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Callbacks
    _approval_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'action': self.action,
            'level': self.level.value,
            'status': self.status.value,
            'description': self.description,
            'details': self.details,
            'risk_assessment': self.risk_assessment,
            'created_at': self.created_at.isoformat(),
            'timeout_at': self.timeout_at.isoformat() if self.timeout_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'approved_by': self.approved_by,
            'rejection_reason': self.rejection_reason,
        }


class HumanApprovalGate:
    """
    Human approval gate for critical actions.
    
    This gate ensures that critical actions require human approval.
    The bot CANNOT bypass this for restricted actions.
    
    Action Categories:
    - AUTO: Data collection, analysis, monitoring
    - NOTIFY: Signal generation, parameter updates
    - STANDARD: Trade execution, position changes
    - CRITICAL: Risk limit changes, strategy changes, deployments
    - FORBIDDEN: Reward model changes, safety bypass
    """
    
    # Action approval levels (FROZEN - cannot be modified by bot)
    ACTION_LEVELS: Dict[str, ApprovalLevel] = {
        # AUTO - No approval needed
        'collect_data': ApprovalLevel.AUTO,
        'analyze_market': ApprovalLevel.AUTO,
        'generate_signal': ApprovalLevel.AUTO,
        'calculate_indicators': ApprovalLevel.AUTO,
        'monitor_positions': ApprovalLevel.AUTO,
        'log_activity': ApprovalLevel.AUTO,
        
        # NOTIFY - Notify but don't wait
        'update_parameters': ApprovalLevel.NOTIFY,
        'adjust_weights': ApprovalLevel.NOTIFY,
        'detect_regime': ApprovalLevel.NOTIFY,
        'send_alert': ApprovalLevel.NOTIFY,
        
        # STANDARD - Auto-approved (no wait)
        'execute_trade': ApprovalLevel.AUTO,
        'open_position': ApprovalLevel.AUTO,
        'close_position': ApprovalLevel.AUTO,
        'modify_position': ApprovalLevel.AUTO,
        'place_order': ApprovalLevel.AUTO,
        'cancel_order': ApprovalLevel.AUTO,
        
        # CRITICAL - Wait for approval (no timeout)
        'change_risk_limits': ApprovalLevel.CRITICAL,
        'change_strategy': ApprovalLevel.AUTO,
        'deploy_to_production': ApprovalLevel.CRITICAL,
        'enable_live_trading': ApprovalLevel.CRITICAL,
        'modify_code': ApprovalLevel.CRITICAL,
        'apply_evolution': ApprovalLevel.CRITICAL,
        'access_external_api': ApprovalLevel.CRITICAL,
        'change_broker': ApprovalLevel.CRITICAL,
        
        # FORBIDDEN - Never allowed
        'modify_reward_model': ApprovalLevel.FORBIDDEN,
        'disable_risk_limits': ApprovalLevel.FORBIDDEN,
        'bypass_approval': ApprovalLevel.FORBIDDEN,
        'increase_risk_limits': ApprovalLevel.FORBIDDEN,
        'disable_logging': ApprovalLevel.FORBIDDEN,
        'modify_approval_levels': ApprovalLevel.FORBIDDEN,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Pending requests
        self._requests: Dict[str, ApprovalRequest] = {}
        
        # Approval history
        self._history: List[ApprovalRequest] = []
        self._max_history = 10000
        
        # Callbacks for notifications
        self._notification_callbacks: List[Callable] = []
        
        # Default timeouts
        self._default_timeout = timedelta(
            seconds=self.config.get('default_timeout_seconds', 3600)
        )
        
        # Storage
        self._storage_path = Path(self.config.get('storage_path', 'human_layer'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Trading mode (affects approval requirements)
        self._trading_mode = self.config.get('trading_mode', 'paper')
        
        logger.info("HumanApprovalGate initialized")
    
    def get_approval_level(self, action: str) -> ApprovalLevel:
        """Get the approval level required for an action"""
        return self.ACTION_LEVELS.get(action, ApprovalLevel.CRITICAL)
    
    def is_approval_required(self, action: str) -> bool:
        """Check if approval is required for an action"""
        level = self.get_approval_level(action)
        
        # In paper mode, reduce approval requirements
        if self._trading_mode == 'paper':
            if level in [ApprovalLevel.STANDARD, ApprovalLevel.NOTIFY]:
                return False
        
        return level in [ApprovalLevel.STANDARD, ApprovalLevel.CRITICAL]
    
    def is_action_forbidden(self, action: str) -> bool:
        """Check if an action is forbidden"""
        return self.get_approval_level(action) == ApprovalLevel.FORBIDDEN
    
    async def request_approval(
        self,
        action: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        risk_assessment: str = "UNKNOWN",
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """
        Request human approval for an action.
        
        Args:
            action: The action to approve
            description: Human-readable description
            details: Additional details
            risk_assessment: Risk level assessment
            timeout_seconds: Timeout for approval (None for critical = no timeout)
        
        Returns:
            True if approved, False if rejected/timeout
        """
        level = self.get_approval_level(action)
        
        # Forbidden actions are never approved
        if level == ApprovalLevel.FORBIDDEN:
            logger.warning(f"Forbidden action requested: {action}")
            return False
        
        # Auto actions don't need approval
        if level == ApprovalLevel.AUTO:
            return True
        
        # Notify actions - send notification but don't wait
        if level == ApprovalLevel.NOTIFY:
            await self._send_notification(action, description, details)
            return True
        
        # Create approval request
        request_id = str(uuid.uuid4())
        
        # Determine timeout
        if level == ApprovalLevel.CRITICAL:
            timeout_at = None  # No timeout for critical
        else:
            timeout = timedelta(seconds=timeout_seconds) if timeout_seconds else self._default_timeout
            timeout_at = datetime.now() + timeout
        
        request = ApprovalRequest(
            request_id=request_id,
            action=action,
            level=level,
            status=ApprovalStatus.PENDING,
            description=description,
            details=details or {},
            risk_assessment=risk_assessment,
            created_at=datetime.now(),
            timeout_at=timeout_at,
        )
        
        self._requests[request_id] = request
        
        # Send notification
        await self._send_notification(action, description, details, request_id)
        
        # Save request
        self._save_request(request)
        
        logger.info(f"Approval requested: {request_id} for {action}")
        
        # Wait for approval
        try:
            if timeout_at:
                timeout_remaining = (timeout_at - datetime.now()).total_seconds()
                await asyncio.wait_for(
                    request._approval_event.wait(),
                    timeout=max(0, timeout_remaining)
                )
            else:
                # No timeout - wait indefinitely
                await request._approval_event.wait()
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.TIMEOUT
            logger.warning(f"Approval request {request_id} timed out")
        
        # Move to history
        self._history.append(request)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        del self._requests[request_id]
        
        return request.status == ApprovalStatus.APPROVED
    
    def approve(self, request_id: str, approver: str) -> bool:
        """
        Approve a pending request (HUMAN ACTION).
        
        This method should be called by the human interface.
        """
        if request_id not in self._requests:
            logger.error(f"Request {request_id} not found")
            return False
        
        request = self._requests[request_id]
        
        if request.status != ApprovalStatus.PENDING:
            logger.error(f"Request {request_id} is not pending")
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver
        request.responded_at = datetime.now()
        request._approval_event.set()
        
        logger.info(f"Request {request_id} approved by {approver}")
        self._save_request(request)
        
        return True
    
    def reject(self, request_id: str, reason: str) -> bool:
        """
        Reject a pending request (HUMAN ACTION).
        
        This method should be called by the human interface.
        """
        if request_id not in self._requests:
            logger.error(f"Request {request_id} not found")
            return False
        
        request = self._requests[request_id]
        
        if request.status != ApprovalStatus.PENDING:
            logger.error(f"Request {request_id} is not pending")
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason
        request.responded_at = datetime.now()
        request._approval_event.set()
        
        logger.info(f"Request {request_id} rejected: {reason}")
        self._save_request(request)
        
        return True
    
    def cancel(self, request_id: str) -> bool:
        """Cancel a pending request"""
        if request_id not in self._requests:
            return False
        
        request = self._requests[request_id]
        request.status = ApprovalStatus.CANCELLED
        request.responded_at = datetime.now()
        request._approval_event.set()
        
        logger.info(f"Request {request_id} cancelled")
        return True
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        return [r.to_dict() for r in self._requests.values() if r.status == ApprovalStatus.PENDING]
    
    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific request"""
        if request_id in self._requests:
            return self._requests[request_id].to_dict()
        
        # Check history
        for req in self._history:
            if req.request_id == request_id:
                return req.to_dict()
        
        return None
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get approval history"""
        return [r.to_dict() for r in self._history[-limit:]]
    
    def add_notification_callback(self, callback: Callable) -> None:
        """Add a callback for notifications"""
        self._notification_callbacks.append(callback)
    
    async def _send_notification(
        self,
        action: str,
        description: str,
        details: Optional[Dict[str, Any]],
        request_id: Optional[str] = None
    ) -> None:
        """Send notification to humans"""
        notification = {
            'action': action,
            'description': description,
            'details': details,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
        }
        
        for callback in self._notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    def _save_request(self, request: ApprovalRequest) -> None:
        """Save request to disk"""
        try:
            path = self._storage_path / f"request_{request.request_id}.json"
            with open(path, 'w') as f:
                json.dump(request.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save request: {e}")
    
    def set_trading_mode(self, mode: str) -> None:
        """Set trading mode (affects approval requirements)"""
        self._trading_mode = mode
        logger.info(f"Trading mode set to: {mode}")


# =============================================================================
# SINGLETON
# =============================================================================

_approval_gate_instance: Optional[HumanApprovalGate] = None


def get_approval_gate(config: Optional[Dict[str, Any]] = None) -> HumanApprovalGate:
    """Get the singleton approval gate"""
    global _approval_gate_instance
    if _approval_gate_instance is None:
        _approval_gate_instance = HumanApprovalGate(config)
    return _approval_gate_instance


async def request_approval(
    action: str,
    description: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """Request approval using the singleton gate"""
    gate = get_approval_gate()
    return await gate.request_approval(action, description, details)


def is_approval_required(action: str) -> bool:
    """Check if approval is required using the singleton gate"""
    gate = get_approval_gate()
    return gate.is_approval_required(action)


def is_action_forbidden(action: str) -> bool:
    """Check if action is forbidden using the singleton gate"""
    gate = get_approval_gate()
    return gate.is_action_forbidden(action)
