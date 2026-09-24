"""
Promotion System
=================

Manages the promotion of validated AI-generated changes to production.
Implements a rigorous multi-stage approval process.

Promotion Pipeline:
1. Experiment completes successfully in sandbox
2. Safety review passes
3. Performance validation passes
4. Human approval (for high-impact changes)
5. Staged rollout to production

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class PromotionStatus(Enum):
    """Status of a promotion request."""
    PENDING = auto()           # Awaiting review
    SAFETY_REVIEW = auto()     # Under safety review
    PERFORMANCE_REVIEW = auto()  # Under performance review
    AWAITING_APPROVAL = auto() # Awaiting human approval
    APPROVED = auto()          # Approved for promotion
    REJECTED = auto()          # Rejected
    STAGED = auto()            # In staged rollout
    PROMOTED = auto()          # Successfully promoted
    ROLLED_BACK = auto()       # Rolled back after promotion
    CANCELLED = auto()         # Cancelled


class PromotionType(Enum):
    """Types of promotions."""
    STRATEGY = "strategy"           # Trading strategy
    INDICATOR = "indicator"         # Technical indicator
    MODEL = "model"                 # ML model
    RISK_RULE = "risk_rule"         # Risk management rule
    CONFIGURATION = "configuration"  # Configuration change
    FEATURE = "feature"             # Feature engineering
    INTEGRATION = "integration"     # System integration


class ApprovalLevel(Enum):
    """Approval levels required."""
    AUTO = "auto"              # Automatic approval
    SINGLE = "single"          # Single human approval
    DUAL = "dual"              # Two human approvals
    COMMITTEE = "committee"    # Committee approval


@dataclass
class PromotionCriteria:
    """Criteria for promotion eligibility."""
    # Performance Requirements
    min_sharpe_ratio: float = 1.5
    min_win_rate: float = 0.55
    max_drawdown: float = 0.15
    min_profit_factor: float = 1.3
    min_trades: int = 100
    
    # Statistical Requirements
    max_p_value: float = 0.05
    min_confidence: float = 0.95
    
    # Safety Requirements
    safety_scan_passed: bool = True
    no_critical_issues: bool = True
    
    # Testing Requirements
    min_backtest_period_days: int = 365
    min_out_of_sample_ratio: float = 0.3
    
    # Approval Requirements
    approval_level: ApprovalLevel = ApprovalLevel.SINGLE
    require_human_approval: bool = True


@dataclass
class PromotionRequest:
    """A request to promote code to production."""
    request_id: str
    experiment_id: str
    promotion_type: PromotionType
    
    # Code Details
    code: str
    code_hash: str
    version: int
    
    # Requester
    requested_by: str  # Agent ID
    requested_at: datetime
    
    # Status
    status: PromotionStatus = PromotionStatus.PENDING
    
    # Review Results
    safety_review_passed: bool = False
    safety_review_notes: List[str] = field(default_factory=list)
    safety_reviewer: Optional[str] = None
    
    performance_review_passed: bool = False
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    performance_reviewer: Optional[str] = None
    
    # Approval
    approval_level: ApprovalLevel = ApprovalLevel.SINGLE
    approvals: List[Dict[str, Any]] = field(default_factory=list)
    rejections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Staging
    staged_at: Optional[datetime] = None
    staging_results: Dict[str, Any] = field(default_factory=dict)
    staging_duration_hours: float = 24.0
    
    # Promotion
    promoted_at: Optional[datetime] = None
    production_id: Optional[str] = None
    
    # Rollback
    rolled_back_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    
    # Metadata
    description: str = ""
    impact_assessment: str = ""
    rollback_plan: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'experiment_id': self.experiment_id,
            'promotion_type': self.promotion_type.value,
            'code_hash': self.code_hash,
            'version': self.version,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at.isoformat(),
            'status': self.status.name,
            'safety_review_passed': self.safety_review_passed,
            'safety_review_notes': self.safety_review_notes,
            'performance_review_passed': self.performance_review_passed,
            'performance_metrics': self.performance_metrics,
            'approval_level': self.approval_level.name,
            'approvals_count': len(self.approvals),
            'rejections_count': len(self.rejections),
            'staged_at': self.staged_at.isoformat() if self.staged_at else None,
            'promoted_at': self.promoted_at.isoformat() if self.promoted_at else None,
            'production_id': self.production_id,
            'description': self.description,
        }
    
    def get_required_approvals(self) -> int:
        """Get number of required approvals."""
        if self.approval_level == ApprovalLevel.AUTO:
            return 0
        elif self.approval_level == ApprovalLevel.SINGLE:
            return 1
        elif self.approval_level == ApprovalLevel.DUAL:
            return 2
        elif self.approval_level == ApprovalLevel.COMMITTEE:
            return 3
        return 1
    
    def has_sufficient_approvals(self) -> bool:
        """Check if request has sufficient approvals."""
        return len(self.approvals) >= self.get_required_approvals()


@dataclass
class StagingEnvironment:
    """A staging environment for testing promotions."""
    staging_id: str
    request_id: str
    created_at: datetime
    
    # Configuration
    traffic_percentage: float = 0.0  # Percentage of traffic to route
    duration_hours: float = 24.0
    
    # Status
    is_active: bool = True
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Results
    trades_executed: int = 0
    pnl: float = 0.0
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'staging_id': self.staging_id,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat(),
            'traffic_percentage': self.traffic_percentage,
            'duration_hours': self.duration_hours,
            'is_active': self.is_active,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'trades_executed': self.trades_executed,
            'pnl': self.pnl,
            'errors': self.errors,
            'metrics': self.metrics,
        }


@dataclass
class PromotionHistory:
    """History entry for a promotion."""
    history_id: str
    request_id: str
    timestamp: datetime
    action: str
    actor: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'history_id': self.history_id,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'actor': self.actor,
            'details': self.details,
        }


class PromotionSystem:
    """
    Manages promotion of AI-generated code to production.
    
    Implements a rigorous multi-stage process:
    1. Safety Review - Code passes safety scanner
    2. Performance Review - Meets performance criteria
    3. Human Approval - Required for high-impact changes
    4. Staged Rollout - Gradual deployment with monitoring
    5. Full Promotion - Complete deployment to production
    
    All promotions can be rolled back if issues are detected.
    """
    
    def __init__(
        self,
        criteria: Optional[PromotionCriteria] = None,
        storage_path: str = "promotion_system"
    ):
        """
        Initialize the promotion system.
        
        Args:
            criteria: Promotion criteria
            storage_path: Path for storage
        """
        self.criteria = criteria or PromotionCriteria()
        
        # Requests
        self._requests: Dict[str, PromotionRequest] = {}
        self._staging_environments: Dict[str, StagingEnvironment] = {}
        self._history: List[PromotionHistory] = []
        
        # Indices
        self._by_status: Dict[PromotionStatus, Set[str]] = {s: set() for s in PromotionStatus}
        self._by_experiment: Dict[str, Set[str]] = {}
        
        # Callbacks
        self._status_callbacks: List[Callable] = []
        self._approval_callbacks: List[Callable] = []
        
        # Production registry (promoted items)
        self._production_registry: Dict[str, Dict] = {}
        
        # Storage
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("PromotionSystem initialized")
    
    async def create_promotion_request(
        self,
        experiment_id: str,
        promotion_type: PromotionType,
        code: str,
        requested_by: str,
        description: str = "",
        impact_assessment: str = "",
        rollback_plan: str = "",
        approval_level: Optional[ApprovalLevel] = None,
    ) -> PromotionRequest:
        """
        Create a new promotion request.
        
        Args:
            experiment_id: ID of the experiment to promote
            promotion_type: Type of promotion
            code: Code to promote
            requested_by: Agent ID
            description: Description of the change
            impact_assessment: Impact assessment
            rollback_plan: Rollback plan
            approval_level: Override approval level
        
        Returns:
            Created PromotionRequest
        """
        request_id = f"PROM-{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Determine approval level
        if approval_level is None:
            approval_level = self._determine_approval_level(promotion_type)
        
        request = PromotionRequest(
            request_id=request_id,
            experiment_id=experiment_id,
            promotion_type=promotion_type,
            code=code,
            code_hash=code_hash,
            version=1,
            requested_by=requested_by,
            requested_at=datetime.now(timezone.utc),
            approval_level=approval_level,
            description=description,
            impact_assessment=impact_assessment,
            rollback_plan=rollback_plan,
        )
        
        self._requests[request_id] = request
        self._by_status[PromotionStatus.PENDING].add(request_id)
        
        if experiment_id not in self._by_experiment:
            self._by_experiment[experiment_id] = set()
        self._by_experiment[experiment_id].add(request_id)
        
        # Record history
        await self._record_history(request_id, 'CREATED', requested_by, {
            'promotion_type': promotion_type.value,
            'approval_level': approval_level.name,
        })
        
        logger.info(f"Created promotion request: {request_id} for experiment {experiment_id}")
        
        return request
    
    def _determine_approval_level(self, promotion_type: PromotionType) -> ApprovalLevel:
        """Determine required approval level based on promotion type."""
        high_impact = [PromotionType.STRATEGY, PromotionType.RISK_RULE, PromotionType.MODEL]
        medium_impact = [PromotionType.INDICATOR, PromotionType.FEATURE]
        
        if promotion_type in high_impact:
            return ApprovalLevel.DUAL
        elif promotion_type in medium_impact:
            return ApprovalLevel.SINGLE
        else:
            return ApprovalLevel.AUTO
    
    async def submit_safety_review(
        self,
        request_id: str,
        passed: bool,
        reviewer: str,
        notes: List[str],
    ) -> bool:
        """
        Submit safety review results.
        
        Args:
            request_id: Request ID
            passed: Whether review passed
            reviewer: Reviewer ID
            notes: Review notes
        
        Returns:
            True if submitted successfully
        """
        request = self._requests.get(request_id)
        if not request:
            return False
        
        request.safety_review_passed = passed
        request.safety_reviewer = reviewer
        request.safety_review_notes = notes
        
        if passed:
            await self._update_status(request_id, PromotionStatus.SAFETY_REVIEW)
            await self._record_history(request_id, 'SAFETY_REVIEW_PASSED', reviewer, {
                'notes': notes,
            })
        else:
            await self._update_status(request_id, PromotionStatus.REJECTED)
            await self._record_history(request_id, 'SAFETY_REVIEW_FAILED', reviewer, {
                'notes': notes,
            })
        
        return True
    
    async def submit_performance_review(
        self,
        request_id: str,
        metrics: Dict[str, float],
        reviewer: str,
    ) -> Tuple[bool, List[str]]:
        """
        Submit performance review results.
        
        Args:
            request_id: Request ID
            metrics: Performance metrics
            reviewer: Reviewer ID
        
        Returns:
            Tuple of (passed, list of issues)
        """
        request = self._requests.get(request_id)
        if not request:
            return False, ["Request not found"]
        
        request.performance_metrics = metrics
        request.performance_reviewer = reviewer
        
        # Check against criteria
        issues = []
        
        if 'sharpe_ratio' in metrics:
            if metrics['sharpe_ratio'] < self.criteria.min_sharpe_ratio:
                issues.append(f"Sharpe ratio {metrics['sharpe_ratio']:.2f} < {self.criteria.min_sharpe_ratio}")
        
        if 'win_rate' in metrics:
            if metrics['win_rate'] < self.criteria.min_win_rate:
                issues.append(f"Win rate {metrics['win_rate']:.2%} < {self.criteria.min_win_rate:.2%}")
        
        if 'max_drawdown' in metrics:
            if metrics['max_drawdown'] > self.criteria.max_drawdown:
                issues.append(f"Max drawdown {metrics['max_drawdown']:.2%} > {self.criteria.max_drawdown:.2%}")
        
        if 'profit_factor' in metrics:
            if metrics['profit_factor'] < self.criteria.min_profit_factor:
                issues.append(f"Profit factor {metrics['profit_factor']:.2f} < {self.criteria.min_profit_factor}")
        
        passed = len(issues) == 0
        request.performance_review_passed = passed
        
        if passed:
            if request.approval_level == ApprovalLevel.AUTO:
                await self._update_status(request_id, PromotionStatus.APPROVED)
            else:
                await self._update_status(request_id, PromotionStatus.AWAITING_APPROVAL)
            
            await self._record_history(request_id, 'PERFORMANCE_REVIEW_PASSED', reviewer, {
                'metrics': metrics,
            })
        else:
            await self._update_status(request_id, PromotionStatus.REJECTED)
            await self._record_history(request_id, 'PERFORMANCE_REVIEW_FAILED', reviewer, {
                'metrics': metrics,
                'issues': issues,
            })
        
        return passed, issues
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        comments: str = "",
    ) -> bool:
        """
        Approve a promotion request.
        
        Args:
            request_id: Request ID
            approver: Approver ID
            comments: Approval comments
        
        Returns:
            True if approval recorded
        """
        request = self._requests.get(request_id)
        if not request:
            return False
        
        if request.status != PromotionStatus.AWAITING_APPROVAL:
            return False
        
        # Check if approver already approved
        if any(a['approver'] == approver for a in request.approvals):
            return False
        
        request.approvals.append({
            'approver': approver,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'comments': comments,
        })
        
        await self._record_history(request_id, 'APPROVED', approver, {
            'comments': comments,
            'approval_count': len(request.approvals),
            'required': request.get_required_approvals(),
        })
        
        # Check if sufficient approvals
        if request.has_sufficient_approvals():
            await self._update_status(request_id, PromotionStatus.APPROVED)
            
            # Notify callbacks
            for callback in self._approval_callbacks:
                try:
                    await callback(request, 'approved')
                except Exception as e:
                    logger.error(f"Approval callback error: {e}")
        
        return True
    
    async def reject(
        self,
        request_id: str,
        rejector: str,
        reason: str,
    ) -> bool:
        """
        Reject a promotion request.
        
        Args:
            request_id: Request ID
            rejector: Rejector ID
            reason: Rejection reason
        
        Returns:
            True if rejection recorded
        """
        request = self._requests.get(request_id)
        if not request:
            return False
        
        request.rejections.append({
            'rejector': rejector,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': reason,
        })
        
        await self._update_status(request_id, PromotionStatus.REJECTED)
        
        await self._record_history(request_id, 'REJECTED', rejector, {
            'reason': reason,
        })
        
        return True
    
    async def start_staging(
        self,
        request_id: str,
        traffic_percentage: float = 5.0,
        duration_hours: float = 24.0,
    ) -> Optional[StagingEnvironment]:
        """
        Start staged rollout for a promotion.
        
        Args:
            request_id: Request ID
            traffic_percentage: Percentage of traffic to route
            duration_hours: Duration of staging
        
        Returns:
            StagingEnvironment if started
        """
        request = self._requests.get(request_id)
        if not request:
            return None
        
        if request.status != PromotionStatus.APPROVED:
            return None
        
        staging_id = f"STAGE-{uuid.uuid4().hex[:8]}"
        
        staging = StagingEnvironment(
            staging_id=staging_id,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
            traffic_percentage=traffic_percentage,
            duration_hours=duration_hours,
            started_at=datetime.now(timezone.utc),
        )
        
        self._staging_environments[staging_id] = staging
        
        request.staged_at = datetime.now(timezone.utc)
        request.staging_duration_hours = duration_hours
        
        await self._update_status(request_id, PromotionStatus.STAGED)
        
        await self._record_history(request_id, 'STAGING_STARTED', 'system', {
            'staging_id': staging_id,
            'traffic_percentage': traffic_percentage,
            'duration_hours': duration_hours,
        })
        
        logger.info(f"Started staging for {request_id}: {traffic_percentage}% traffic for {duration_hours}h")
        
        return staging
    
    async def update_staging_results(
        self,
        staging_id: str,
        trades: int,
        pnl: float,
        metrics: Dict[str, float],
        errors: Optional[List[str]] = None,
    ):
        """
        Update staging environment results.
        
        Args:
            staging_id: Staging ID
            trades: Number of trades executed
            pnl: Profit/loss
            metrics: Performance metrics
            errors: Any errors encountered
        """
        staging = self._staging_environments.get(staging_id)
        if not staging:
            return
        
        staging.trades_executed = trades
        staging.pnl = pnl
        staging.metrics = metrics
        
        if errors:
            staging.errors.extend(errors)
        
        # Update request
        request = self._requests.get(staging.request_id)
        if request:
            request.staging_results = {
                'trades': trades,
                'pnl': pnl,
                'metrics': metrics,
                'errors': staging.errors,
            }
    
    async def complete_staging(
        self,
        staging_id: str,
        success: bool,
    ) -> bool:
        """
        Complete staging and decide on promotion.
        
        Args:
            staging_id: Staging ID
            success: Whether staging was successful
        
        Returns:
            True if completed
        """
        staging = self._staging_environments.get(staging_id)
        if not staging:
            return False
        
        staging.is_active = False
        staging.ended_at = datetime.now(timezone.utc)
        
        request = self._requests.get(staging.request_id)
        if not request:
            return False
        
        if success:
            # Promote to production
            await self._promote_to_production(request)
        else:
            # Reject
            await self._update_status(request.request_id, PromotionStatus.REJECTED)
            await self._record_history(request.request_id, 'STAGING_FAILED', 'system', {
                'staging_id': staging_id,
                'errors': staging.errors,
            })
        
        return True
    
    async def _promote_to_production(self, request: PromotionRequest):
        """Promote request to production."""
        production_id = f"PROD-{uuid.uuid4().hex[:8]}"
        
        request.promoted_at = datetime.now(timezone.utc)
        request.production_id = production_id
        
        # Register in production
        self._production_registry[production_id] = {
            'production_id': production_id,
            'request_id': request.request_id,
            'experiment_id': request.experiment_id,
            'promotion_type': request.promotion_type.value,
            'code_hash': request.code_hash,
            'promoted_at': request.promoted_at.isoformat(),
            'version': request.version,
        }
        
        await self._update_status(request.request_id, PromotionStatus.PROMOTED)
        
        await self._record_history(request.request_id, 'PROMOTED', 'system', {
            'production_id': production_id,
        })
        
        # Persist
        await self._persist_production_item(production_id, request)
        
        logger.info(f"Promoted {request.request_id} to production as {production_id}")
    
    async def rollback(
        self,
        request_id: str,
        reason: str,
        actor: str,
    ) -> bool:
        """
        Rollback a promoted change.
        
        Args:
            request_id: Request ID
            reason: Rollback reason
            actor: Who initiated rollback
        
        Returns:
            True if rolled back
        """
        request = self._requests.get(request_id)
        if not request:
            return False
        
        if request.status != PromotionStatus.PROMOTED:
            return False
        
        request.rolled_back_at = datetime.now(timezone.utc)
        request.rollback_reason = reason
        
        # Remove from production registry
        if request.production_id:
            self._production_registry.pop(request.production_id, None)
        
        await self._update_status(request_id, PromotionStatus.ROLLED_BACK)
        
        await self._record_history(request_id, 'ROLLED_BACK', actor, {
            'reason': reason,
            'production_id': request.production_id,
        })
        
        logger.warning(f"Rolled back {request_id}: {reason}")
        
        return True
    
    async def _update_status(self, request_id: str, new_status: PromotionStatus):
        """Update request status."""
        request = self._requests.get(request_id)
        if not request:
            return
        
        old_status = request.status
        
        # Update indices
        self._by_status[old_status].discard(request_id)
        self._by_status[new_status].add(request_id)
        
        request.status = new_status
        
        # Notify callbacks
        for callback in self._status_callbacks:
            try:
                await callback(request, old_status, new_status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    async def _record_history(
        self,
        request_id: str,
        action: str,
        actor: str,
        details: Dict[str, Any],
    ):
        """Record history entry."""
        entry = PromotionHistory(
            history_id=f"HIST-{uuid.uuid4().hex[:8]}",
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=actor,
            details=details,
        )
        
        self._history.append(entry)
    
    async def _persist_production_item(self, production_id: str, request: PromotionRequest):
        """Persist production item to disk."""
        try:
            prod_path = self._storage_path / 'production'
            prod_path.mkdir(parents=True, exist_ok=True)
            
            prod_file = prod_path / f"{production_id}.json"
            
            data = {
                'production_id': production_id,
                'request': request.to_dict(),
                'code': request.code,
            }
            
            with open(prod_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist production item: {e}")
    
    def get_request(self, request_id: str) -> Optional[PromotionRequest]:
        """Get request by ID."""
        return self._requests.get(request_id)
    
    def get_requests_by_status(self, status: PromotionStatus) -> List[PromotionRequest]:
        """Get requests by status."""
        return [self._requests[rid] for rid in self._by_status.get(status, set())]
    
    def get_pending_approvals(self) -> List[PromotionRequest]:
        """Get requests awaiting approval."""
        return self.get_requests_by_status(PromotionStatus.AWAITING_APPROVAL)
    
    def get_production_items(self) -> Dict[str, Dict]:
        """Get all production items."""
        return self._production_registry.copy()
    
    def get_history(self, request_id: str) -> List[PromotionHistory]:
        """Get history for a request."""
        return [h for h in self._history if h.request_id == request_id]
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status changes."""
        self._status_callbacks.append(callback)
    
    def register_approval_callback(self, callback: Callable):
        """Register callback for approvals."""
        self._approval_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get promotion system statistics."""
        status_counts = {s.name: len(ids) for s, ids in self._by_status.items()}
        
        promoted = self.get_requests_by_status(PromotionStatus.PROMOTED)
        rolled_back = self.get_requests_by_status(PromotionStatus.ROLLED_BACK)
        
        return {
            'total_requests': len(self._requests),
            'by_status': status_counts,
            'production_items': len(self._production_registry),
            'active_staging': sum(1 for s in self._staging_environments.values() if s.is_active),
            'promotion_rate': len(promoted) / len(self._requests) if self._requests else 0,
            'rollback_rate': len(rolled_back) / len(promoted) if promoted else 0,
            'pending_approvals': len(self.get_pending_approvals()),
            'total_history_entries': len(self._history),
        }
