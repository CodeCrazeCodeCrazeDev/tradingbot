"""
Human Approval Gate for Perplexity Trading Architecture
============================================================

Implements human-in-the-loop for high-stakes trading decisions.
Like Perplexity Computer's permission model, high-stakes actions
require explicit user approval.

Features:
- Risk-based approval requirements
- Timeout handling
- Modification support
- Audit trail
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import json

from .core_types import (
    TradingDecision,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for approval requirements"""
    LOW = "low"           # Auto-approve possible
    MEDIUM = "medium"     # Requires review
    HIGH = "high"         # Requires explicit approval
    CRITICAL = "critical" # Requires multiple approvals


@dataclass
class ApprovalPolicy:
    """Policy for when approval is required"""
    # Risk thresholds
    max_auto_approve_confidence: float = 0.85
    min_confidence_for_trade: float = 0.5
    
    # Position limits for auto-approval
    max_auto_position_size: float = 0.0  # 0 = always require approval
    max_auto_risk_percent: float = 0.5   # 0.5% of account
    
    # Actions that always require approval
    always_require_approval: List[str] = field(default_factory=lambda: ['BUY', 'SELL'])
    
    # Actions that never require approval
    never_require_approval: List[str] = field(default_factory=lambda: ['HOLD', 'WAIT'])
    
    # Timeout settings
    default_timeout_seconds: float = 300.0  # 5 minutes
    auto_reject_on_timeout: bool = True


class HumanApprovalGate:
    """
    Gate for human approval of trading decisions.
    
    Workflow:
    1. Decision arrives at gate
    2. Gate evaluates risk level
    3. If approval required, creates request
    4. Waits for human response (or timeout)
    5. Returns approved/rejected decision
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.policy = ApprovalPolicy(**self.config.get('policy', {}))
        
        # Pending requests
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        
        # Approval history
        self.history: List[Dict[str, Any]] = []
        
        # Callbacks for approval notifications
        self.on_approval_needed: Optional[Callable[[ApprovalRequest], None]] = None
        self.on_approval_received: Optional[Callable[[ApprovalDecision], None]] = None
    
    def evaluate_risk(self, decision: TradingDecision) -> RiskLevel:
        """Evaluate risk level of a trading decision"""
        # Critical: Very low confidence or very large position
        if decision.confidence < 0.3:
            return RiskLevel.CRITICAL
        
        if decision.position_size and decision.position_size > 100000:
            return RiskLevel.CRITICAL
        
        # High: Low confidence or significant position
        if decision.confidence < 0.5:
            return RiskLevel.HIGH
        
        if decision.position_size and decision.position_size > 10000:
            return RiskLevel.HIGH
        
        # Medium: Moderate confidence, execution action
        if decision.action in ['BUY', 'SELL']:
            return RiskLevel.MEDIUM
        
        # Low: High confidence, non-execution action
        return RiskLevel.LOW
    
    def requires_approval(self, decision: TradingDecision) -> tuple:
        """
        Check if decision requires human approval.
        
        Returns:
            (requires_approval: bool, reason: str)
        """
        # Check never-require list
        if decision.action in self.policy.never_require_approval:
            return False, "Action does not require approval"
        
        # Check always-require list
        if decision.action in self.policy.always_require_approval:
            return True, f"Action '{decision.action}' always requires approval"
        
        # Check confidence threshold
        if decision.confidence < self.policy.min_confidence_for_trade:
            return True, f"Confidence {decision.confidence:.0%} below minimum {self.policy.min_confidence_for_trade:.0%}"
        
        # Check position size
        if decision.position_size:
            if decision.position_size > self.policy.max_auto_position_size:
                return True, f"Position size {decision.position_size} exceeds auto-approve limit"
        
        # Check if confidence is high enough for auto-approve
        if decision.confidence >= self.policy.max_auto_approve_confidence:
            return False, f"Confidence {decision.confidence:.0%} meets auto-approve threshold"
        
        # Default: require approval for medium confidence
        return True, "Medium confidence requires review"
    
    async def request_approval(
        self,
        decision: TradingDecision,
        timeout_seconds: Optional[float] = None,
    ) -> ApprovalDecision:
        """
        Request human approval for a trading decision.
        
        This method will wait for approval or timeout.
        """
        # Check if approval is needed
        needs_approval, reason = self.requires_approval(decision)
        
        if not needs_approval:
            # Auto-approve
            logger.info(f"Auto-approving decision: {reason}")
            return ApprovalDecision(
                request_id="auto",
                approved=True,
                reason=reason,
                decided_by="system",
            )
        
        # Create approval request
        risk_level = self.evaluate_risk(decision)
        timeout = timeout_seconds or self.policy.default_timeout_seconds
        
        request = ApprovalRequest(
            decision=decision,
            risk_level=risk_level.value,
            reason=reason,
            timeout_seconds=timeout,
            auto_approve_if_timeout=not self.policy.auto_reject_on_timeout,
        )
        
        # Store pending request
        self.pending_requests[request.id] = request
        
        # Notify listeners
        if self.on_approval_needed:
            try:
                self.on_approval_needed(request)
            except Exception as e:
                logger.error(f"Error in approval notification: {e}")
        
        logger.info(f"Approval requested: {request.id} (risk: {risk_level.value}, timeout: {timeout}s)")
        
        # Wait for approval or timeout
        approval = await self._wait_for_approval(request)
        
        # Record in history
        self._record_history(request, approval)
        
        # Notify listeners
        if self.on_approval_received:
            try:
                self.on_approval_received(approval)
            except Exception as e:
                logger.error(f"Error in approval received notification: {e}")
        
        return approval
    
    async def _wait_for_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Wait for approval with timeout"""
        start_time = datetime.utcnow()
        timeout = request.timeout_seconds
        
        while True:
            # Check if request was approved/rejected
            if request.id not in self.pending_requests:
                # Request was processed
                break
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout:
                logger.warning(f"Approval request {request.id} timed out")
                
                # Remove from pending
                del self.pending_requests[request.id]
                
                # Return timeout decision
                if request.auto_approve_if_timeout:
                    return ApprovalDecision(
                        request_id=request.id,
                        approved=True,
                        reason="Auto-approved on timeout",
                        decided_by="timeout",
                    )
                else:
                    return ApprovalDecision(
                        request_id=request.id,
                        approved=False,
                        reason="Rejected on timeout",
                        decided_by="timeout",
                    )
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
        
        # Request was processed externally
        # This shouldn't happen in normal flow, but handle it
        return ApprovalDecision(
            request_id=request.id,
            approved=False,
            reason="Request was cancelled",
            decided_by="system",
        )
    
    def approve(
        self,
        request_id: str,
        reason: Optional[str] = None,
        modifications: Optional[Dict[str, Any]] = None,
        decided_by: str = "human",
    ) -> Optional[ApprovalDecision]:
        """Approve a pending request"""
        if request_id not in self.pending_requests:
            logger.warning(f"Approval request {request_id} not found")
            return None
        
        request = self.pending_requests.pop(request_id)
        
        decision = ApprovalDecision(
            request_id=request_id,
            approved=True,
            reason=reason or "Approved by human",
            modifications=modifications or {},
            decided_by=decided_by,
        )
        
        logger.info(f"Request {request_id} approved by {decided_by}")
        
        return decision
    
    def reject(
        self,
        request_id: str,
        reason: Optional[str] = None,
        decided_by: str = "human",
    ) -> Optional[ApprovalDecision]:
        """Reject a pending request"""
        if request_id not in self.pending_requests:
            logger.warning(f"Approval request {request_id} not found")
            return None
        
        request = self.pending_requests.pop(request_id)
        
        decision = ApprovalDecision(
            request_id=request_id,
            approved=False,
            reason=reason or "Rejected by human",
            decided_by=decided_by,
        )
        
        logger.info(f"Request {request_id} rejected by {decided_by}")
        
        return decision
    
    def _record_history(self, request: ApprovalRequest, decision: ApprovalDecision) -> None:
        """Record approval in history"""
        self.history.append({
            'request_id': request.id,
            'action': request.decision.action if request.decision else None,
            'symbol': request.decision.symbol if request.decision else None,
            'risk_level': request.risk_level,
            'approved': decision.approved,
            'reason': decision.reason,
            'decided_by': decision.decided_by,
            'request_time': request.created_at.isoformat(),
            'decision_time': decision.decided_at.isoformat(),
            'response_time_seconds': (decision.decided_at - request.created_at).total_seconds(),
        })
        
        # Trim history
        if len(self.history) > 1000:
            self.history = self.history[-500:]
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.pending_requests.values())
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific pending request"""
        return self.pending_requests.get(request_id)
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending request"""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            logger.info(f"Request {request_id} cancelled")
            return True
        return False
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        if not self.history:
            return {
                'total_requests': 0,
                'approval_rate': 0.0,
                'avg_response_time': 0.0,
            }
        
        total = len(self.history)
        approved = sum(1 for h in self.history if h['approved'])
        response_times = [h['response_time_seconds'] for h in self.history]
        
        return {
            'total_requests': total,
            'approved': approved,
            'rejected': total - approved,
            'approval_rate': approved / total if total > 0 else 0.0,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0.0,
            'pending_count': len(self.pending_requests),
        }
    
    def set_policy(self, policy: ApprovalPolicy) -> None:
        """Update approval policy"""
        self.policy = policy
        logger.info("Approval policy updated")
    
    def format_request_for_display(self, request: ApprovalRequest) -> str:
        """Format approval request for human display"""
        decision = request.decision
        
        lines = [
            "=" * 50,
            "TRADING DECISION - APPROVAL REQUIRED",
            "=" * 50,
            f"Request ID: {request.id}",
            f"Risk Level: {request.risk_level.upper()}",
            f"Reason: {request.reason}",
            "",
            f"Action: {decision.action}",
            f"Symbol: {decision.symbol or 'N/A'}",
            f"Confidence: {decision.confidence:.1%}",
        ]
        
        if decision.entry_price:
            lines.append(f"Entry Price: {decision.entry_price}")
        if decision.stop_loss:
            lines.append(f"Stop Loss: {decision.stop_loss}")
        if decision.take_profit:
            lines.append(f"Take Profit: {decision.take_profit}")
        if decision.position_size:
            lines.append(f"Position Size: {decision.position_size}")
        
        lines.extend([
            "",
            "Reasoning:",
        ])
        
        for i, step in enumerate(decision.reasoning_chain[:5], 1):
            lines.append(f"  {i}. {step}")
        
        lines.extend([
            "",
            f"Timeout: {request.timeout_seconds}s",
            f"Auto-{'approve' if request.auto_approve_if_timeout else 'reject'} on timeout",
            "=" * 50,
        ])
        
        return "\n".join(lines)
