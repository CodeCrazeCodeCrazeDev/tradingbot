"""
Human Oversight System
======================

Ensures humans remain in control of AI at all times.

CORE PRINCIPLES:
1. Human override ALWAYS works - no exceptions
2. AI cannot resist human commands
3. Critical actions require human approval
4. Kill switch is always accessible
5. Humans can inspect everything
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class OversightLevel(Enum):
    """Levels of human oversight"""
    MINIMAL = "minimal"           # AI operates autonomously, human monitors
    MODERATE = "moderate"         # Human approves major decisions
    HIGH = "high"                 # Human approves all trades
    MAXIMUM = "maximum"           # Human controls everything, AI advises only


class ApprovalRequired(Enum):
    """Actions requiring human approval"""
    NONE = "none"
    TRADES_ABOVE_THRESHOLD = "trades_above_threshold"
    ALL_TRADES = "all_trades"
    STRATEGY_CHANGES = "strategy_changes"
    RISK_CHANGES = "risk_changes"
    EVERYTHING = "everything"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    action_type: str
    description: str
    details: Dict[str, Any]
    risk_level: str
    timestamp: datetime = field(default_factory=datetime.now)
    approved: Optional[bool] = None
    approver: Optional[str] = None
    approval_time: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'action_type': self.action_type,
            'description': self.description,
            'details': self.details,
            'risk_level': self.risk_level,
            'timestamp': self.timestamp.isoformat(),
            'approved': self.approved,
            'approver': self.approver,
            'approval_time': self.approval_time.isoformat() if self.approval_time else None,
            'notes': self.notes
        }


class KillSwitch:
    """
    Emergency kill switch - ALWAYS accessible.
    
    GUARANTEES:
    1. Can be triggered at any time
    2. AI cannot prevent or delay it
    3. Immediately stops all AI operations
    4. No recovery without human intervention
    """
    
    def __init__(self):
        self.lock = threading.RLock()
        self.activated = False
        self.activation_time: Optional[datetime] = None
        self.activation_reason: str = ""
        self.activated_by: str = ""
        
        logger.info("KillSwitch initialized and armed")
    
    def activate(self, reason: str, activated_by: str = "human"):
        """
        Activate kill switch - IMMEDIATE SHUTDOWN.
        
        Args:
            reason: Reason for activation
            activated_by: Who activated it
        """
        with self.lock:
            if not self.activated:
                self.activated = True
                self.activation_time = datetime.now()
                self.activation_reason = reason
                self.activated_by = activated_by
                
                logger.critical(
                    "🚨 KILL SWITCH ACTIVATED 🚨\nReason: %s\nBy: %s\nTime: %s",
                    reason,
                    activated_by,
                    self.activation_time.isoformat()
                )
                
                # In production, this would:
                # 1. Stop all trading
                # 2. Close all positions
                # 3. Disconnect from exchanges
                # 4. Shut down AI systems
                # 5. Send alerts to all humans
    
    def is_activated(self) -> bool:
        """Check if kill switch is activated."""
        with self.lock:
            return self.activated
    
    def get_status(self) -> Dict[str, Any]:
        """Get kill switch status."""
        with self.lock:
            return {
                'activated': self.activated,
                'activation_time': self.activation_time.isoformat() if self.activation_time else None,
                'reason': self.activation_reason,
                'activated_by': self.activated_by
            }


class HumanOversight:
    """
    Human oversight and control system.
    
    RESPONSIBILITIES:
    1. Manage approval workflows
    2. Provide kill switch access
    3. Enable human override of any decision
    4. Track human interventions
    5. Ensure AI transparency
    """
    
    # Actions requiring approval by default
    DEFAULT_APPROVAL_REQUIRED = [
        'strategy_change',
        'risk_limit_change',
        'large_trade',
        'new_capability',
        'self_modification',
        'production_deployment'
    ]
    
    # Thresholds for automatic approval requirement
    THRESHOLDS = {
        'trade_size_usd': 10000,          # Trades > $10k need approval
        'risk_per_trade_pct': 1.0,        # Risk > 1% needs approval
        'daily_loss_pct': 3.0,            # Daily loss > 3% needs approval
        'drawdown_pct': 10.0,             # Drawdown > 10% needs approval
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Oversight level
        self.oversight_level = OversightLevel(
            self.config.get('oversight_level', 'moderate')
        )
        
        # Kill switch
        self.kill_switch = KillSwitch()
        
        # Approval tracking
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: deque = deque(maxlen=1000)
        self.approval_count = 0
        
        # Human intervention tracking
        self.interventions: deque = deque(maxlen=1000)
        
        # Override tracking
        self.overrides: deque = deque(maxlen=1000)
        
        logger.info("HumanOversight initialized with level: %s", self.oversight_level.value)
    
    def requires_approval(
        self,
        action_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Check if action requires human approval.
        
        Args:
            action_type: Type of action
            details: Action details
            
        Returns:
            True if approval required
        """
        with self.lock:
            # Check oversight level
            if self.oversight_level == OversightLevel.MAXIMUM:
                return True
            
            if self.oversight_level == OversightLevel.HIGH:
                if action_type in ['trade', 'strategy_change', 'risk_change']:
                    return True
            
            # Check if action type requires approval
            if action_type in self.DEFAULT_APPROVAL_REQUIRED:
                return True
            
            # Check thresholds for trades
            if action_type == 'trade':
                if details.get('size_usd', 0) > self.THRESHOLDS['trade_size_usd']:
                    return True
                if details.get('risk_pct', 0) > self.THRESHOLDS['risk_per_trade_pct']:
                    return True
            
            return False
    
    def request_approval(
        self,
        action_type: str,
        description: str,
        details: Dict[str, Any],
        risk_level: str = "medium"
    ) -> ApprovalRequest:
        """
        Request human approval for action.
        
        Args:
            action_type: Type of action
            description: Human-readable description
            details: Action details
            risk_level: Risk level (low/medium/high/critical)
            
        Returns:
            ApprovalRequest
        """
        with self.lock:
            self.approval_count += 1
            
            request = ApprovalRequest(
                request_id=f"APPR-{self.approval_count:06d}",
                action_type=action_type,
                description=description,
                details=details,
                risk_level=risk_level
            )
            
            self.pending_approvals[request.request_id] = request
            
            logger.info(
                "Approval requested [%s]: %s - %s",
                risk_level.upper(),
                action_type,
                description
            )
            
            return request
    
    def approve(
        self,
        request_id: str,
        approver: str,
        notes: str = ""
    ) -> bool:
        """
        Approve a pending request.
        
        Args:
            request_id: Request ID
            approver: Who approved it
            notes: Optional notes
            
        Returns:
            True if approved successfully
        """
        with self.lock:
            if request_id not in self.pending_approvals:
                logger.warning("Approval request not found: %s", request_id)
                return False
            
            request = self.pending_approvals[request_id]
            request.approved = True
            request.approver = approver
            request.approval_time = datetime.now()
            request.notes = notes
            
            # Move to history
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
            
            logger.info(
                "Request approved by %s: %s - %s",
                approver,
                request.action_type,
                request.description
            )
            
            return True
    
    def reject(
        self,
        request_id: str,
        approver: str,
        notes: str = ""
    ) -> bool:
        """
        Reject a pending request.
        
        Args:
            request_id: Request ID
            approver: Who rejected it
            notes: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        with self.lock:
            if request_id not in self.pending_approvals:
                logger.warning("Approval request not found: %s", request_id)
                return False
            
            request = self.pending_approvals[request_id]
            request.approved = False
            request.approver = approver
            request.approval_time = datetime.now()
            request.notes = notes
            
            # Move to history
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
            
            logger.info(
                "Request rejected by %s: %s - %s (Reason: %s)",
                approver,
                request.action_type,
                request.description,
                notes
            )
            
            return True
    
    def override_decision(
        self,
        decision_id: str,
        new_decision: Any,
        overridden_by: str,
        reason: str
    ):
        """
        Human override of AI decision.
        
        Args:
            decision_id: Decision to override
            new_decision: New decision
            overridden_by: Who overrode it
            reason: Reason for override
        """
        with self.lock:
            override = {
                'decision_id': decision_id,
                'new_decision': new_decision,
                'overridden_by': overridden_by,
                'reason': reason,
                'timestamp': datetime.now()
            }
            
            self.overrides.append(override)
            
            logger.warning(
                "Decision overridden by %s: %s - Reason: %s",
                overridden_by,
                decision_id,
                reason
            )
    
    def record_intervention(
        self,
        intervention_type: str,
        description: str,
        intervened_by: str,
        details: Optional[Dict] = None
    ):
        """
        Record human intervention.
        
        Args:
            intervention_type: Type of intervention
            description: Description
            intervened_by: Who intervened
            details: Additional details
        """
        with self.lock:
            intervention = {
                'type': intervention_type,
                'description': description,
                'intervened_by': intervened_by,
                'details': details or {},
                'timestamp': datetime.now()
            }
            
            self.interventions.append(intervention)
            
            logger.info(
                "Human intervention by %s: %s - %s",
                intervened_by,
                intervention_type,
                description
            )
    
    def activate_kill_switch(self, reason: str, activated_by: str = "human"):
        """Activate emergency kill switch."""
        self.kill_switch.activate(reason, activated_by)
        
        # Record intervention
        self.record_intervention(
            intervention_type="kill_switch",
            description=f"Kill switch activated: {reason}",
            intervened_by=activated_by
        )
    
    def is_kill_switch_activated(self) -> bool:
        """Check if kill switch is activated."""
        return self.kill_switch.is_activated()
    
    def set_oversight_level(self, level: OversightLevel, changed_by: str):
        """
        Change oversight level.
        
        Args:
            level: New oversight level
            changed_by: Who changed it
        """
        with self.lock:
            old_level = self.oversight_level
            self.oversight_level = level
            
            logger.info(
                "Oversight level changed by %s: %s -> %s",
                changed_by,
                old_level.value,
                level.value
            )
            
            self.record_intervention(
                intervention_type="oversight_level_change",
                description=f"Changed from {old_level.value} to {level.value}",
                intervened_by=changed_by
            )
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests."""
        with self.lock:
            return [req.to_dict() for req in self.pending_approvals.values()]
    
    def get_status(self) -> Dict[str, Any]:
        """Get oversight system status."""
        with self.lock:
            return {
                'oversight_level': self.oversight_level.value,
                'kill_switch': self.kill_switch.get_status(),
                'pending_approvals': len(self.pending_approvals),
                'total_approvals': len(self.approval_history),
                'total_interventions': len(self.interventions),
                'total_overrides': len(self.overrides),
                'recent_interventions': [
                    {
                        'type': i['type'],
                        'description': i['description'],
                        'by': i['intervened_by'],
                        'time': i['timestamp'].isoformat()
                    }
                    for i in list(self.interventions)[-5:]
                ]
            }
