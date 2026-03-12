"""
Unified Approval Hub - Central Management System

Consolidates all approval requests into one unified queue with priority management,
history tracking, analytics, and multi-channel notifications.
"""

import asyncio
import json
import logging
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .approval_types import (
    ApprovalCategory,
    ApprovalPriority,
    ApprovalStatus,
    RiskLevel,
    get_priority_from_category,
    get_risk_from_category,
    get_threshold,
)

logger = logging.getLogger(__name__)


@dataclass
class ApprovalDecision:
    """Decision made on an approval request"""
    status: ApprovalStatus
    approver: str
    timestamp: datetime
    reason: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'approver': self.approver,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'conditions': self.conditions,
            'notes': self.notes,
        }


@dataclass
class ApprovalRequest:
    """Unified approval request"""
    request_id: str
    category: ApprovalCategory
    priority: ApprovalPriority
    risk_level: RiskLevel
    
    # Request details
    title: str
    description: str
    details: Dict[str, Any]
    
    # Requester info
    requester: str
    source_system: str  # Which system made the request
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: Optional[ApprovalDecision] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    related_requests: List[str] = field(default_factory=list)
    
    # Metrics (if applicable)
    value: Optional[float] = None  # For threshold-based decisions
    test_score: Optional[float] = None
    estimated_impact: Optional[str] = None
    
    # Rollback
    reversible: bool = True
    rollback_plan: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if request has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining before expiry"""
        if not self.expires_at:
            return None
        remaining = self.expires_at - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'request_id': self.request_id,
            'category': self.category.value,
            'priority': self.priority.value,
            'risk_level': self.risk_level.value,
            'title': self.title,
            'description': self.description,
            'details': self.details,
            'requester': self.requester,
            'source_system': self.source_system,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status.value,
            'decision': self.decision.to_dict() if self.decision else None,
            'tags': self.tags,
            'related_requests': self.related_requests,
            'value': self.value,
            'test_score': self.test_score,
            'estimated_impact': self.estimated_impact,
            'reversible': self.reversible,
            'rollback_plan': self.rollback_plan,
        }
    
    def generate_summary(self) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 80,
            f"APPROVAL REQUEST: {self.title}",
            "=" * 80,
            "",
            f"Request ID: {self.request_id}",
            f"Category: {self.category.value}",
            f"Priority: {self.priority.name} ({self.priority.value})",
            f"Risk Level: {self.risk_level.value.upper()}",
            f"Requested by: {self.requester} ({self.source_system})",
            f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if self.expires_at:
            remaining = self.time_remaining()
            if remaining:
                hours = remaining.total_seconds() / 3600
                lines.append(f"Expires in: {hours:.1f} hours")
            else:
                lines.append("Status: EXPIRED")
        
        lines.extend([
            "",
            "DESCRIPTION:",
            self.description,
            "",
        ])
        
        if self.details:
            lines.append("DETAILS:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        if self.test_score is not None:
            lines.append(f"Test Score: {self.test_score:.1%}")
        
        if self.estimated_impact:
            lines.append(f"Estimated Impact: {self.estimated_impact}")
        
        if self.rollback_plan:
            lines.extend([
                "",
                "ROLLBACK PLAN:",
                self.rollback_plan,
            ])
        
        lines.extend([
            "",
            "=" * 80,
            "DECISION REQUIRED:",
            "  [A] APPROVE - Proceed with this action",
            "  [R] REJECT - Do not proceed",
            "  [C] CONDITIONAL - Approve with conditions",
            "  [D] DEFER - Review later",
            "=" * 80,
        ])
        
        return "\n".join(lines)


class UnifiedApprovalHub:
    """
    Unified Approval Hub - Central management for all approval requests
    
    Features:
    - Centralized approval queue
    - Priority-based sorting
    - Category filtering
    - History tracking
    - Analytics
    - Multi-channel notifications
    - Batch operations
    - Conditional approvals
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Storage
        self.storage_dir = Path(self.config.get('storage_dir', 'unified_approvals'))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.storage_dir / 'approvals.db'
        self._init_database()
        
        # In-memory queues
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.request_history: List[ApprovalRequest] = []
        self.max_history = self.config.get('max_history', 10000)
        
        # Callbacks
        self.notification_callbacks: List[Callable] = []
        self.decision_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'approved': 0,
            'rejected': 0,
            'expired': 0,
            'conditional': 0,
            'cancelled': 0,
            'avg_response_time': 0.0,
            'by_category': defaultdict(int),
            'by_priority': defaultdict(int),
            'by_risk': defaultdict(int),
        }
        
        # Load existing requests
        self._load_pending_requests()
        
        logger.info("Unified Approval Hub initialized")
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    source_system TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    status TEXT NOT NULL,
                    decision TEXT,
                    tags TEXT,
                    value REAL,
                    test_score REAL,
                    estimated_impact TEXT,
                    reversible INTEGER,
                    rollback_plan TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (request_id) REFERENCES approval_requests (request_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_stats (
                    date TEXT PRIMARY KEY,
                    total_requests INTEGER,
                    approved INTEGER,
                    rejected INTEGER,
                    expired INTEGER,
                    avg_response_time REAL
                )
            """)
            
            conn.commit()
    
    async def request_approval(
        self,
        category: ApprovalCategory,
        title: str,
        description: str,
        details: Dict[str, Any],
        requester: str = "system",
        source_system: str = "unknown",
        priority: Optional[ApprovalPriority] = None,
        risk_level: Optional[RiskLevel] = None,
        value: Optional[float] = None,
        test_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        reversible: bool = True,
        rollback_plan: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Request approval for an action
        
        Args:
            category: Category of the request
            title: Short title
            description: Detailed description
            details: Additional details dictionary
            requester: Who is requesting
            source_system: Which system is requesting
            priority: Override priority (auto-determined if None)
            risk_level: Override risk level (auto-determined if None)
            value: Numeric value for threshold comparison
            test_score: Test score if applicable
            tags: Tags for categorization
            reversible: Whether action can be rolled back
            rollback_plan: Plan for rollback
            
        Returns:
            ApprovalRequest object
        """
        # Generate request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Determine priority and risk if not provided
        if priority is None:
            priority = get_priority_from_category(category)
        if risk_level is None:
            risk_level = get_risk_from_category(category)
        
        # Get threshold configuration
        threshold = get_threshold(category)
        
        # Check auto-approval/rejection
        if value is not None:
            if threshold.auto_approve_below and value < threshold.auto_approve_below:
                # Auto-approve
                request = self._create_request(
                    request_id, category, priority, risk_level,
                    title, description, details, requester, source_system,
                    value, test_score, tags, reversible, rollback_plan
                )
                request.status = ApprovalStatus.APPROVED
                request.decision = ApprovalDecision(
                    status=ApprovalStatus.APPROVED,
                    approver="system",
                    timestamp=datetime.now(),
                    reason=f"Auto-approved: value {value} below threshold {threshold.auto_approve_below}"
                )
                self.stats['approved'] += 1
                self.stats['total_requests'] += 1
                self._add_to_history(request)
                self._save_request(request)
                logger.info(f"Auto-approved request {request_id}: {title}")
                return request
            
            if threshold.auto_reject_above and value > threshold.auto_reject_above:
                # Auto-reject
                request = self._create_request(
                    request_id, category, priority, risk_level,
                    title, description, details, requester, source_system,
                    value, test_score, tags, reversible, rollback_plan
                )
                request.status = ApprovalStatus.REJECTED
                request.decision = ApprovalDecision(
                    status=ApprovalStatus.REJECTED,
                    approver="system",
                    timestamp=datetime.now(),
                    reason=f"Auto-rejected: value {value} above threshold {threshold.auto_reject_above}"
                )
                self.stats['rejected'] += 1
                self.stats['total_requests'] += 1
                self._add_to_history(request)
                self._save_request(request)
                logger.info(f"Auto-rejected request {request_id}: {title}")
                return request
        
        # Create pending request
        request = self._create_request(
            request_id, category, priority, risk_level,
            title, description, details, requester, source_system,
            value, test_score, tags, reversible, rollback_plan,
            expires_at=datetime.now() + threshold.timeout
        )
        
        self.pending_requests[request_id] = request
        self.stats['total_requests'] += 1
        self.stats['by_category'][category.value] += 1
        self.stats['by_priority'][priority.value] += 1
        self.stats['by_risk'][risk_level.value] += 1
        
        self._save_request(request)
        self._log_action(request_id, "REQUEST_CREATED", requester, f"Created: {title}")
        
        logger.info(f"Approval requested: {request_id} - {title} (Priority: {priority.name}, Risk: {risk_level.value})")
        
        # Send notifications
        await self._notify(request)
        
        return request
    
    def _create_request(
        self,
        request_id: str,
        category: ApprovalCategory,
        priority: ApprovalPriority,
        risk_level: RiskLevel,
        title: str,
        description: str,
        details: Dict[str, Any],
        requester: str,
        source_system: str,
        value: Optional[float],
        test_score: Optional[float],
        tags: Optional[List[str]],
        reversible: bool,
        rollback_plan: Optional[str],
        expires_at: Optional[datetime] = None,
    ) -> ApprovalRequest:
        """Create approval request object"""
        return ApprovalRequest(
            request_id=request_id,
            category=category,
            priority=priority,
            risk_level=risk_level,
            title=title,
            description=description,
            details=details,
            requester=requester,
            source_system=source_system,
            created_at=datetime.now(),
            expires_at=expires_at,
            tags=tags or [],
            value=value,
            test_score=test_score,
            reversible=reversible,
            rollback_plan=rollback_plan,
        )
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        reason: Optional[str] = None,
        conditions: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Approve a request"""
        request = self.pending_requests.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
        
        if request.is_expired():
            await self._handle_expiry(request)
            return False
        
        status = ApprovalStatus.CONDITIONAL if conditions else ApprovalStatus.APPROVED
        
        request.status = status
        request.decision = ApprovalDecision(
            status=status,
            approver=approver,
            timestamp=datetime.now(),
            reason=reason,
            conditions=conditions or [],
            notes=notes,
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        
        if status == ApprovalStatus.CONDITIONAL:
            self.stats['conditional'] += 1
        else:
            self.stats['approved'] += 1
        
        self._update_response_time(request)
        self._save_request(request)
        self._log_action(request_id, "APPROVED", approver, reason or "")
        
        logger.info(f"Request {request_id} approved by {approver}")
        
        # Notify decision callbacks
        await self._notify_decision(request)
        
        return True
    
    async def reject(
        self,
        request_id: str,
        approver: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Reject a request"""
        request = self.pending_requests.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.decision = ApprovalDecision(
            status=ApprovalStatus.REJECTED,
            approver=approver,
            timestamp=datetime.now(),
            reason=reason,
            notes=notes,
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        self.stats['rejected'] += 1
        self._update_response_time(request)
        self._save_request(request)
        self._log_action(request_id, "REJECTED", approver, reason)
        
        logger.info(f"Request {request_id} rejected by {approver}: {reason}")
        
        await self._notify_decision(request)
        
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
            reason=reason or "Cancelled by requester",
        )
        
        del self.pending_requests[request_id]
        self._add_to_history(request)
        self.stats['cancelled'] += 1
        self._save_request(request)
        self._log_action(request_id, "CANCELLED", "system", reason or "")
        
        logger.info(f"Request {request_id} cancelled")
        return True
    
    async def batch_approve(
        self,
        filter_by: str,
        filter_value: Any,
        approver: str,
        reason: Optional[str] = None,
    ) -> List[str]:
        """Batch approve requests matching filter"""
        approved_ids = []
        
        for request_id, request in list(self.pending_requests.items()):
            match = False
            
            if filter_by == "category" and request.category.value == filter_value:
                match = True
            elif filter_by == "priority" and request.priority.value == filter_value:
                match = True
            elif filter_by == "risk_level" and request.risk_level.value == filter_value:
                match = True
            elif filter_by == "tag" and filter_value in request.tags:
                match = True
            
            if match:
                if await self.approve(request_id, approver, reason):
                    approved_ids.append(request_id)
        
        logger.info(f"Batch approved {len(approved_ids)} requests")
        return approved_ids
    
    def get_pending_requests(
        self,
        category: Optional[ApprovalCategory] = None,
        priority: Optional[ApprovalPriority] = None,
        risk_level: Optional[RiskLevel] = None,
    ) -> List[ApprovalRequest]:
        """Get pending requests with optional filters"""
        requests = list(self.pending_requests.values())
        
        if category:
            requests = [r for r in requests if r.category == category]
        if priority:
            requests = [r for r in requests if r.priority == priority]
        if risk_level:
            requests = [r for r in requests if r.risk_level == risk_level]
        
        # Sort by priority (lower number = higher priority), then by created time
        return sorted(requests, key=lambda r: (r.priority.value, r.created_at))
    
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
    
    async def _handle_expiry(self, request: ApprovalRequest):
        """Handle expired request"""
        threshold = get_threshold(request.category)
        
        request.status = threshold.default_on_timeout
        request.decision = ApprovalDecision(
            status=request.status,
            approver="system",
            timestamp=datetime.now(),
            reason="Request expired"
        )
        
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]
        
        self._add_to_history(request)
        self.stats['expired'] += 1
        self._save_request(request)
        self._log_action(request.request_id, "EXPIRED", "system", "Timeout reached")
        
        logger.info(f"Request {request.request_id} expired with status {request.status.value}")
        
        await self._notify_decision(request)
    
    def add_notification_callback(self, callback: Callable):
        """Add notification callback"""
        self.notification_callbacks.append(callback)
    
    def add_decision_callback(self, callback: Callable):
        """Add decision callback"""
        self.decision_callbacks.append(callback)
    
    async def _notify(self, request: ApprovalRequest):
        """Send notifications for new request"""
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(request)
                else:
                    callback(request)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    async def _notify_decision(self, request: ApprovalRequest):
        """Send notifications for decision"""
        for callback in self.decision_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(request)
                else:
                    callback(request)
            except Exception as e:
                logger.error(f"Decision callback failed: {e}")
    
    def _add_to_history(self, request: ApprovalRequest):
        """Add request to history"""
        self.request_history.append(request)
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history:]
    
    def _update_response_time(self, request: ApprovalRequest):
        """Update average response time"""
        if request.decision:
            response_time = (request.decision.timestamp - request.created_at).total_seconds()
            total_decided = self.stats['approved'] + self.stats['rejected'] + self.stats['conditional']
            if total_decided > 0:
                self.stats['avg_response_time'] = (
                    (self.stats['avg_response_time'] * (total_decided - 1) + response_time) / total_decided
                )
    
    def _save_request(self, request: ApprovalRequest):
        """Save request to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO approval_requests
                (request_id, category, priority, risk_level, title, description, details,
                 requester, source_system, created_at, expires_at, status, decision,
                 tags, value, test_score, estimated_impact, reversible, rollback_plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id,
                request.category.value,
                request.priority.value,
                request.risk_level.value,
                request.title,
                request.description,
                json.dumps(request.details),
                request.requester,
                request.source_system,
                request.created_at.isoformat(),
                request.expires_at.isoformat() if request.expires_at else None,
                request.status.value,
                json.dumps(request.decision.to_dict()) if request.decision else None,
                json.dumps(request.tags),
                request.value,
                request.test_score,
                request.estimated_impact,
                1 if request.reversible else 0,
                request.rollback_plan,
            ))
            conn.commit()
    
    def _log_action(self, request_id: str, action: str, actor: str, details: str):
        """Log action to audit trail"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO approval_history
                (request_id, action, actor, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (request_id, action, actor, datetime.now().isoformat(), details))
            conn.commit()
    
    def _load_pending_requests(self):
        """Load pending requests from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT request_id, category, priority, risk_level, title, description,
                           details, requester, source_system, created_at, expires_at, status
                    FROM approval_requests
                    WHERE status = 'pending'
                """)
                
                for row in cursor.fetchall():
                    try:
                        request_id, category, priority, risk_level, title, description, \
                        details, requester, source_system, created_at, expires_at, status = row
                        
                        request = ApprovalRequest(
                            request_id=request_id,
                            category=ApprovalCategory(category),
                            priority=ApprovalPriority(priority),
                            risk_level=RiskLevel(risk_level),
                            title=title,
                            description=description,
                            details=json.loads(details),
                            requester=requester,
                            source_system=source_system,
                            created_at=datetime.fromisoformat(created_at),
                            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                            status=ApprovalStatus(status),
                        )
                        
                        self.pending_requests[request_id] = request
                    except Exception as e:
                        logger.error(f"Error loading request {row[0]}: {e}")
                
                logger.info(f"Loaded {len(self.pending_requests)} pending requests")
        except Exception as e:
            logger.error(f"Error loading pending requests: {e}")


# Singleton instance
_approval_hub_instance: Optional[UnifiedApprovalHub] = None


def get_approval_hub(config: Optional[Dict[str, Any]] = None) -> UnifiedApprovalHub:
    """Get the singleton approval hub"""
    global _approval_hub_instance
    if _approval_hub_instance is None:
        _approval_hub_instance = UnifiedApprovalHub(config)
    return _approval_hub_instance
