"""
Ultimate Approval System - Multi-tier approval workflows for trading operations.

Provides approval gates for high-risk operations including large orders,
strategy changes, and production deployments with timeout handling.
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApprovalLevel(Enum):
    """Approval requirement levels."""
    AUTO = "auto"              # Automatic approval (low risk)
    NOTIFY = "notify"          # Notify human, proceed automatically
    ADVISORY = "advisory"      # Suggest to human, wait briefly
    REQUIRED = "required"      # Human approval required
    CRITICAL = "critical"      # Multiple approvals required


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ActionCategory(Enum):
    """Categories of actions requiring approval."""
    TRADE_EXECUTION = "trade_execution"
    LARGE_ORDER = "large_order"
    STRATEGY_CHANGE = "strategy_change"
    RISK_OVERRIDE = "risk_override"
    SYSTEM_CONFIG = "system_config"
    PRODUCTION_DEPLOY = "production_deploy"
    EMERGENCY_ACTION = "emergency_action"
    CODE_MODIFICATION = "code_modification"
    BROKER_CONNECTION = "broker_connection"
    DATA_SOURCE_CHANGE = "data_source_change"


@dataclass
class ApprovalRequest:
    """A request for approval."""
    request_id: str
    category: ActionCategory
    level: ApprovalLevel
    status: ApprovalStatus = ApprovalStatus.PENDING
    description: str = ""
    requester: str = "system"
    approver: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    notes: List[str] = field(default_factory=list)


class UltimateApprovalSystem:
    """
    Multi-tier approval workflow system.

    Enforces approval gates based on action category and risk level.
    Integrates with:
    - trading_bot/approval/ (basic approval)
    - trading_bot/unified_approval/ (unified approval)
    - trading_bot/human_layer/ (human interface)
    - trading_bot/governance/ (governance workflows)
    """

    # Default approval requirements by category
    DEFAULT_REQUIREMENTS = {
        ActionCategory.TRADE_EXECUTION: ApprovalLevel.AUTO,
        ActionCategory.LARGE_ORDER: ApprovalLevel.REQUIRED,
        ActionCategory.STRATEGY_CHANGE: ApprovalLevel.REQUIRED,
        ActionCategory.RISK_OVERRIDE: ApprovalLevel.CRITICAL,
        ActionCategory.SYSTEM_CONFIG: ApprovalLevel.ADVISORY,
        ActionCategory.PRODUCTION_DEPLOY: ApprovalLevel.CRITICAL,
        ActionCategory.EMERGENCY_ACTION: ApprovalLevel.NOTIFY,
        ActionCategory.CODE_MODIFICATION: ApprovalLevel.CRITICAL,
        ActionCategory.BROKER_CONNECTION: ApprovalLevel.REQUIRED,
        ActionCategory.DATA_SOURCE_CHANGE: ApprovalLevel.ADVISORY,
    }

    # Default timeouts (seconds)
    DEFAULT_TIMEOUTS = {
        ApprovalLevel.AUTO: 0,
        ApprovalLevel.NOTIFY: 5,
        ApprovalLevel.ADVISORY: 60,
        ApprovalLevel.REQUIRED: 300,
        ApprovalLevel.CRITICAL: 600,
    }

    # Large order threshold (fraction of portfolio)
    LARGE_ORDER_THRESHOLD = 0.05  # 5% of portfolio

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._requests: Dict[str, ApprovalRequest] = {}
        self._requirements = dict(self.DEFAULT_REQUIREMENTS)
        self._timeouts = dict(self.DEFAULT_TIMEOUTS)
        self._callbacks: List[Callable] = []
        self._audit_log: List[Dict] = []

        # Apply config overrides
        if "requirements" in self._config:
            for cat_str, level_str in self._config["requirements"].items():
                try:
                    cat = ActionCategory(cat_str)
                    level = ApprovalLevel(level_str)
                    self._requirements[cat] = level
                except (ValueError, KeyError):
                    pass

        logger.info("UltimateApprovalSystem initialized")

    def request_approval(
        self,
        category: ActionCategory,
        description: str,
        details: Optional[Dict] = None,
        requester: str = "system",
        level_override: Optional[ApprovalLevel] = None,
    ) -> ApprovalRequest:
        """
        Submit an approval request.

        Returns the request object. Check request.status for result.
        AUTO level requests are immediately approved.
        """
        level = level_override or self._requirements.get(category, ApprovalLevel.REQUIRED)
        timeout = self._timeouts.get(level, 300)

        request = ApprovalRequest(
            request_id=str(uuid.uuid4())[:12],
            category=category,
            level=level,
            description=description,
            requester=requester,
            details=details or {},
            expires_at=datetime.utcnow() + timedelta(seconds=timeout) if timeout > 0 else None,
        )

        # Auto-approve low-risk actions
        if level == ApprovalLevel.AUTO:
            request.status = ApprovalStatus.APPROVED
            request.resolved_at = datetime.utcnow()
            request.approver = "auto"
            request.reason = "Auto-approved (low risk)"
            logger.debug("Auto-approved: %s", description)
        elif level == ApprovalLevel.NOTIFY:
            request.status = ApprovalStatus.APPROVED
            request.resolved_at = datetime.utcnow()
            request.approver = "auto_notify"
            request.reason = "Auto-approved with notification"
            logger.info("NOTIFY: %s - %s", category.value, description)
            self._notify_callbacks(request)
        else:
            logger.info("Approval required (%s): %s - %s",
                        level.value, category.value, description)
            self._notify_callbacks(request)

        self._requests[request.request_id] = request
        self._log_audit("request_created", request)

        return request

    def approve(
        self, request_id: str, approver: str = "human", reason: str = ""
    ) -> bool:
        """Approve a pending request."""
        request = self._requests.get(request_id)
        if not request:
            logger.error("Unknown request: %s", request_id)
            return False

        if request.status != ApprovalStatus.PENDING:
            logger.warning("Request %s is not pending (status=%s)",
                           request_id, request.status.value)
            return False

        # Check expiry
        if request.expires_at and datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            self._log_audit("request_expired", request)
            return False

        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.reason = reason
        request.resolved_at = datetime.utcnow()

        logger.info("Approved: %s by %s", request_id, approver)
        self._log_audit("request_approved", request)
        return True

    def reject(
        self, request_id: str, rejector: str = "human", reason: str = ""
    ) -> bool:
        """Reject a pending request."""
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.REJECTED
        request.approver = rejector
        request.reason = reason
        request.resolved_at = datetime.utcnow()

        logger.info("Rejected: %s by %s - %s", request_id, rejector, reason)
        self._log_audit("request_rejected", request)
        return True

    def check_status(self, request_id: str) -> ApprovalStatus:
        """Check the status of a request, handling expiry."""
        request = self._requests.get(request_id)
        if not request:
            return ApprovalStatus.REJECTED

        # Check expiry
        if (request.status == ApprovalStatus.PENDING and
                request.expires_at and datetime.utcnow() > request.expires_at):
            request.status = ApprovalStatus.EXPIRED
            self._log_audit("request_expired", request)

        return request.status

    def is_approved(self, request_id: str) -> bool:
        """Quick check if a request is approved."""
        return self.check_status(request_id) == ApprovalStatus.APPROVED

    def classify_trade(
        self, quantity: float, price: float, portfolio_value: float
    ) -> ActionCategory:
        """Classify a trade as normal or large order based on size."""
        trade_value = quantity * price
        if portfolio_value > 0 and trade_value / portfolio_value > self.LARGE_ORDER_THRESHOLD:
            return ActionCategory.LARGE_ORDER
        return ActionCategory.TRADE_EXECUTION

    def on_approval_event(self, callback: Callable) -> None:
        """Register a callback for approval events."""
        self._callbacks.append(callback)

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        self._expire_old_requests()
        return [r for r in self._requests.values()
                if r.status == ApprovalStatus.PENDING]

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]

    def get_status(self) -> Dict:
        """Get approval system status."""
        self._expire_old_requests()
        return {
            "total_requests": len(self._requests),
            "pending": sum(1 for r in self._requests.values()
                           if r.status == ApprovalStatus.PENDING),
            "approved": sum(1 for r in self._requests.values()
                            if r.status == ApprovalStatus.APPROVED),
            "rejected": sum(1 for r in self._requests.values()
                            if r.status == ApprovalStatus.REJECTED),
            "expired": sum(1 for r in self._requests.values()
                           if r.status == ApprovalStatus.EXPIRED),
            "audit_log_size": len(self._audit_log),
        }

    def _expire_old_requests(self) -> None:
        """Expire requests that have passed their timeout."""
        now = datetime.utcnow()
        for request in self._requests.values():
            if (request.status == ApprovalStatus.PENDING and
                    request.expires_at and now > request.expires_at):
                request.status = ApprovalStatus.EXPIRED
                self._log_audit("request_expired", request)

    def _notify_callbacks(self, request: ApprovalRequest) -> None:
        """Notify registered callbacks about an approval event."""
        for cb in self._callbacks:
            try:
                cb(request)
            except Exception as e:
                logger.error("Callback error: %s", e)

    def _log_audit(self, action: str, request: ApprovalRequest) -> None:
        """Log an audit entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "request_id": request.request_id,
            "category": request.category.value,
            "level": request.level.value,
            "status": request.status.value,
            "description": request.description,
            "approver": request.approver,
            "reason": request.reason,
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
