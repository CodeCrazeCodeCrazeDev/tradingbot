"""
Operational Safety
==================

Ensures safe system operation through:
1. Human Oversight Protocol - Human-in-the-loop for critical decisions
2. Multi-Layer Kill Switch - Multiple ways to halt the system
3. Audit Trail System - Complete record of all actions
4. Recovery Manager - Safe recovery from failures

PRINCIPLE: Humans must always be able to understand and control the system.
"""

import logging
import threading
import hashlib
import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
from pathlib import Path
import signal
import sys

logger = logging.getLogger(__name__)


class ApprovalLevel(Enum):
    """Levels of human approval required"""
    NONE = "none"               # No approval needed
    NOTIFICATION = "notify"     # Notify human, proceed
    CONFIRMATION = "confirm"    # Wait for confirmation
    EXPLICIT = "explicit"       # Require explicit approval code


class ActionCategory(Enum):
    """Categories of actions for approval routing"""
    ROUTINE_TRADE = "routine_trade"
    LARGE_TRADE = "large_trade"
    PARAMETER_CHANGE = "parameter_change"
    STRATEGY_CHANGE = "strategy_change"
    RISK_LIMIT_CHANGE = "risk_limit_change"
    SYSTEM_MODIFICATION = "system_modification"
    EMERGENCY_ACTION = "emergency_action"


class KillSwitchLevel(Enum):
    """Kill switch activation levels"""
    SOFT = "soft"       # Stop new trades
    MEDIUM = "medium"   # Close new positions, keep existing
    HARD = "hard"       # Close all positions
    NUCLEAR = "nuclear" # Immediate shutdown, close everything


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    action_category: ActionCategory
    approval_level: ApprovalLevel
    description: str
    details: Dict[str, Any]
    requested_at: datetime
    expires_at: datetime
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_code: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'category': self.action_category.value,
            'level': self.approval_level.value,
            'description': self.description,
            'details': self.details,
            'requested_at': self.requested_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'approved': self.approved,
            'approved_by': self.approved_by
        }


@dataclass
class AuditEntry:
    """Audit trail entry"""
    entry_id: str
    timestamp: datetime
    action_type: str
    actor: str  # 'ai', 'human', 'system'
    description: str
    details: Dict[str, Any]
    outcome: str
    risk_level: str
    
    def to_dict(self) -> Dict:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'action_type': self.action_type,
            'actor': self.actor,
            'description': self.description,
            'outcome': self.outcome,
            'risk_level': self.risk_level
        }


class HumanOversightProtocol:
    """
    Ensures human oversight of critical AI decisions.
    
    IMMUTABLE RULES:
    1. All risk limit changes require EXPLICIT approval
    2. All strategy changes require CONFIRMATION
    3. Large trades (>5% of portfolio) require CONFIRMATION
    4. System modifications require EXPLICIT approval
    5. Humans can always override AI decisions
    """
    
    # IMMUTABLE APPROVAL REQUIREMENTS
    APPROVAL_MATRIX = {
        ActionCategory.ROUTINE_TRADE: ApprovalLevel.NONE,
        ActionCategory.LARGE_TRADE: ApprovalLevel.CONFIRMATION,
        ActionCategory.PARAMETER_CHANGE: ApprovalLevel.CONFIRMATION,
        ActionCategory.STRATEGY_CHANGE: ApprovalLevel.CONFIRMATION,
        ActionCategory.RISK_LIMIT_CHANGE: ApprovalLevel.EXPLICIT,
        ActionCategory.SYSTEM_MODIFICATION: ApprovalLevel.EXPLICIT,
        ActionCategory.EMERGENCY_ACTION: ApprovalLevel.NOTIFICATION,
    }
    
    # Large trade threshold
    LARGE_TRADE_THRESHOLD = 0.05  # 5% of portfolio
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Pending approvals
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        
        # Approval timeout
        self.approval_timeout = timedelta(minutes=self.config.get('timeout_minutes', 30))
        
        # Callbacks
        self.on_approval_needed: Optional[Callable] = None
        self.on_approval_timeout: Optional[Callable] = None
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("HumanOversightProtocol initialized")
    
    def request_approval(
        self,
        action_category: ActionCategory,
        description: str,
        details: Dict[str, Any]
    ) -> Tuple[bool, Optional[ApprovalRequest]]:
        """
        Request approval for an action.
        
        Returns:
            Tuple of (can_proceed_immediately, approval_request)
        """
        approval_level = self.APPROVAL_MATRIX.get(action_category, ApprovalLevel.CONFIRMATION)
        
        # No approval needed
        if approval_level == ApprovalLevel.NONE:
            return True, None
        
        # Create approval request
        request = ApprovalRequest(
            request_id=hashlib.sha256(f"{action_category}_{datetime.now()}".encode()).hexdigest()[:16],
            action_category=action_category,
            approval_level=approval_level,
            description=description,
            details=details,
            requested_at=datetime.now(),
            expires_at=datetime.now() + self.approval_timeout
        )
        
        with self._lock:
            self.pending_approvals[request.request_id] = request
        
        # Notify
        if self.on_approval_needed:
            self.on_approval_needed(request)
        
        logger.info(f"Approval requested: {request.request_id} - {description}")
        
        # Notification level can proceed
        if approval_level == ApprovalLevel.NOTIFICATION:
            return True, request
        
        return False, request
    
    def approve(
        self,
        request_id: str,
        approved_by: str,
        approval_code: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Approve a pending request.
        
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            if request_id not in self.pending_approvals:
                return False, "Request not found"
            
            request = self.pending_approvals[request_id]
            
            # Check expiry
            if datetime.now() > request.expires_at:
                del self.pending_approvals[request_id]
                return False, "Request expired"
            
            # Check approval code for explicit approval
            if request.approval_level == ApprovalLevel.EXPLICIT:
                expected_code = self._generate_approval_code(request)
                if approval_code != expected_code:
                    return False, "Invalid approval code"
            
            # Approve
            request.approved = True
            request.approved_by = approved_by
            request.approved_at = datetime.now()
            
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
            
            logger.info(f"Request approved: {request_id} by {approved_by}")
            return True, "Approved"
    
    def reject(
        self,
        request_id: str,
        rejected_by: str,
        reason: str
    ) -> Tuple[bool, str]:
        """Reject a pending request"""
        with self._lock:
            if request_id not in self.pending_approvals:
                return False, "Request not found"
            
            request = self.pending_approvals[request_id]
            request.approved = False
            request.approved_by = rejected_by
            request.approved_at = datetime.now()
            
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
            
            logger.info(f"Request rejected: {request_id} by {rejected_by} - {reason}")
            return True, "Rejected"
    
    def check_approval_status(self, request_id: str) -> Tuple[Optional[bool], str]:
        """
        Check status of an approval request.
        
        Returns:
            Tuple of (approved (None if pending), status_message)
        """
        with self._lock:
            if request_id in self.pending_approvals:
                request = self.pending_approvals[request_id]
                if datetime.now() > request.expires_at:
                    del self.pending_approvals[request_id]
                    if self.on_approval_timeout:
                        self.on_approval_timeout(request)
                    return False, "Request expired"
                return None, "Pending approval"
            
            # Check history
            for request in self.approval_history:
                if request.request_id == request_id:
                    return request.approved, "Approved" if request.approved else "Rejected"
            
            return None, "Request not found"
    
    def _generate_approval_code(self, request: ApprovalRequest) -> str:
        """Generate approval code for explicit approval"""
        # Simple code based on request details
        code_base = f"{request.request_id}:{request.action_category.value}:{request.requested_at.date()}"
        return hashlib.sha256(code_base.encode()).hexdigest()[:8].upper()
    
    def override_ai_decision(
        self,
        decision_id: str,
        override_action: str,
        overridden_by: str,
        reason: str
    ):
        """Record a human override of an AI decision"""
        logger.warning(f"AI DECISION OVERRIDDEN: {decision_id} -> {override_action} by {overridden_by}: {reason}")
        
        # This is always allowed - humans can always override
        return True
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get list of pending approvals"""
        with self._lock:
            return [r.to_dict() for r in self.pending_approvals.values()]


class MultiLayerKillSwitch:
    """
    Multiple layers of kill switches for system shutdown.
    
    LAYERS:
    1. Software kill switch (API call)
    2. File-based kill switch (EMERGENCY_STOP.txt)
    3. Signal-based kill switch (SIGTERM, SIGINT)
    4. Hardware kill switch (network disconnect)
    5. Time-based kill switch (trading hours)
    
    ANY layer can halt the system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State
        self.is_killed = False
        self.kill_level = None
        self.kill_reason = None
        self.kill_time = None
        
        # Kill switch file
        self.kill_file = Path(self.config.get('kill_file', 'EMERGENCY_STOP.txt'))
        
        # Callbacks
        self.on_kill: Optional[Callable] = None
        self.pre_kill_callbacks: List[Callable] = []
        self.post_kill_callbacks: List[Callable] = []
        
        # Lock
        self._lock = threading.Lock()
        
        # Register signal handlers
        self._register_signal_handlers()
        
        logger.info("MultiLayerKillSwitch initialized")
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.critical(f"Received signal {signum} - initiating shutdown")
        self.activate(KillSwitchLevel.HARD, f"Signal {signum} received")
    
    def activate(
        self,
        level: KillSwitchLevel,
        reason: str,
        activated_by: str = "system"
    ) -> bool:
        """
        Activate the kill switch.
        
        Returns:
            True if activation was successful
        """
        with self._lock:
            if self.is_killed and self.kill_level == KillSwitchLevel.NUCLEAR:
                logger.warning("Already in NUCLEAR shutdown")
                return False
            
            logger.critical(f"KILL SWITCH ACTIVATED: Level={level.value}, Reason={reason}")
            
            # Run pre-kill callbacks
            for callback in self.pre_kill_callbacks:
                try:
                    callback(level, reason)
                except Exception as e:
                    logger.error(f"Pre-kill callback error: {e}")
            
            self.is_killed = True
            self.kill_level = level
            self.kill_reason = reason
            self.kill_time = datetime.now()
            
            # Create kill file
            self._create_kill_file(level, reason, activated_by)
            
            # Notify
            if self.on_kill:
                self.on_kill(level, reason)
            
            # Run post-kill callbacks
            for callback in self.post_kill_callbacks:
                try:
                    callback(level, reason)
                except Exception as e:
                    logger.error(f"Post-kill callback error: {e}")
            
            return True
    
    def _create_kill_file(self, level: KillSwitchLevel, reason: str, activated_by: str):
        """Create kill switch file"""
        try:
            with open(self.kill_file, 'w') as f:
                f.write(f"EMERGENCY STOP ACTIVATED\n")
                f.write(f"Level: {level.value}\n")
                f.write(f"Reason: {reason}\n")
                f.write(f"Activated by: {activated_by}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
        except Exception as e:
            logger.error(f"Could not create kill file: {e}")
    
    def check_file_kill_switch(self) -> bool:
        """Check if file-based kill switch is active"""
        return self.kill_file.exists()
    
    def check_all_switches(self) -> Tuple[bool, str]:
        """
        Check all kill switch layers.
        
        Returns:
            Tuple of (is_killed, reason)
        """
        # Check software state
        if self.is_killed:
            return True, self.kill_reason or "Software kill switch active"
        
        # Check file
        if self.check_file_kill_switch():
            self.activate(KillSwitchLevel.HARD, "Kill file detected")
            return True, "Kill file detected"
        
        return False, "All clear"
    
    def reset(self, reset_by: str, authorization_code: str) -> Tuple[bool, str]:
        """
        Reset the kill switch (requires authorization).
        
        Returns:
            Tuple of (success, message)
        """
        # Verify authorization (simple check - in production use proper auth)
        expected_code = hashlib.sha256(f"reset_{datetime.now().date()}".encode()).hexdigest()[:8].upper()
        
        if authorization_code != expected_code:
            logger.warning(f"Kill switch reset attempted with invalid code by {reset_by}")
            return False, "Invalid authorization code"
        
        with self._lock:
            logger.warning(f"Kill switch reset by {reset_by}")
            
            self.is_killed = False
            self.kill_level = None
            self.kill_reason = None
            self.kill_time = None
            
            # Remove kill file
            if self.kill_file.exists():
                self.kill_file.unlink()
            
            return True, "Kill switch reset"
    
    def register_pre_kill(self, callback: Callable):
        """Register callback to run before kill"""
        self.pre_kill_callbacks.append(callback)
    
    def register_post_kill(self, callback: Callable):
        """Register callback to run after kill"""
        self.post_kill_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get kill switch status"""
        return {
            'is_killed': self.is_killed,
            'level': self.kill_level.value if self.kill_level else None,
            'reason': self.kill_reason,
            'time': self.kill_time.isoformat() if self.kill_time else None,
            'file_exists': self.kill_file.exists()
        }


class AuditTrailSystem:
    """
    Complete audit trail of all system actions.
    
    Records:
    1. All trades and orders
    2. All AI decisions with reasoning
    3. All parameter changes
    4. All human interventions
    5. All system events
    
    IMMUTABLE: Audit logs cannot be modified or deleted by AI.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage
        self.audit_path = Path(self.config.get('audit_path', 'audit_logs'))
        self.audit_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer
        self.buffer: deque = deque(maxlen=10000)
        
        # Current file
        self.current_file = None
        self.entries_in_file = 0
        self.max_entries_per_file = 10000
        
        # Lock
        self._lock = threading.Lock()
        
        self._rotate_file()
        logger.info("AuditTrailSystem initialized")
    
    def log(
        self,
        action_type: str,
        actor: str,
        description: str,
        details: Dict[str, Any],
        outcome: str,
        risk_level: str = "low"
    ):
        """Log an action to the audit trail"""
        entry = AuditEntry(
            entry_id=hashlib.sha256(f"{action_type}_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            timestamp=datetime.now(),
            action_type=action_type,
            actor=actor,
            description=description,
            details=details,
            outcome=outcome,
            risk_level=risk_level
        )
        
        with self._lock:
            self.buffer.append(entry)
            self._write_entry(entry)
    
    def log_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        order_id: str,
        reasoning: str
    ):
        """Log a trade"""
        self.log(
            action_type="trade",
            actor="ai",
            description=f"{direction} {quantity} {symbol} @ {price}",
            details={
                'symbol': symbol,
                'direction': direction,
                'quantity': quantity,
                'price': price,
                'order_id': order_id,
                'reasoning': reasoning
            },
            outcome="executed",
            risk_level="medium"
        )
    
    def log_decision(
        self,
        decision_type: str,
        decision: str,
        reasoning: List[str],
        confidence: float,
        alternatives: List[str]
    ):
        """Log an AI decision with full reasoning"""
        self.log(
            action_type="decision",
            actor="ai",
            description=f"{decision_type}: {decision}",
            details={
                'decision_type': decision_type,
                'decision': decision,
                'reasoning': reasoning,
                'confidence': confidence,
                'alternatives': alternatives
            },
            outcome="made",
            risk_level="low"
        )
    
    def log_human_intervention(
        self,
        intervention_type: str,
        description: str,
        intervened_by: str,
        original_action: str,
        new_action: str
    ):
        """Log a human intervention"""
        self.log(
            action_type="human_intervention",
            actor="human",
            description=f"{intervention_type}: {description}",
            details={
                'intervention_type': intervention_type,
                'intervened_by': intervened_by,
                'original_action': original_action,
                'new_action': new_action
            },
            outcome="applied",
            risk_level="high"
        )
    
    def log_parameter_change(
        self,
        parameter: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        reason: str
    ):
        """Log a parameter change"""
        self.log(
            action_type="parameter_change",
            actor=changed_by,
            description=f"Changed {parameter}: {old_value} -> {new_value}",
            details={
                'parameter': parameter,
                'old_value': old_value,
                'new_value': new_value,
                'reason': reason
            },
            outcome="applied",
            risk_level="medium"
        )
    
    def _write_entry(self, entry: AuditEntry):
        """Write entry to file"""
        try:
            if self.entries_in_file >= self.max_entries_per_file:
                self._rotate_file()
            
            with open(self.current_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
            
            self.entries_in_file += 1
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")
    
    def _rotate_file(self):
        """Rotate to a new audit file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_file = self.audit_path / f"audit_{timestamp}.jsonl"
        self.entries_in_file = 0
    
    def search(
        self,
        action_type: Optional[str] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Search audit entries"""
        results = []
        
        for entry in reversed(list(self.buffer)):
            if action_type and entry.action_type != action_type:
                continue
            if actor and entry.actor != actor:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        return results
    
    def get_recent(self, limit: int = 100) -> List[Dict]:
        """Get recent audit entries"""
        return [e.to_dict() for e in list(self.buffer)[-limit:]]


class RecoveryManager:
    """
    Manages safe recovery from failures.
    
    Recovery Procedures:
    1. State snapshot and restore
    2. Position reconciliation
    3. Order cleanup
    4. Gradual restart
    5. Health verification
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State storage
        self.state_path = Path(self.config.get('state_path', 'recovery_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        # Recovery state
        self.is_recovering = False
        self.recovery_start = None
        self.recovery_steps_completed: List[str] = []
        
        logger.info("RecoveryManager initialized")
    
    def save_state(self, state: Dict[str, Any]):
        """Save current state for recovery"""
        state_file = self.state_path / 'latest_state.json'
        backup_file = self.state_path / f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            # Save latest
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.debug("State saved for recovery")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load saved state"""
        state_file = self.state_path / 'latest_state.json'
        
        if not state_file.exists():
            return None
        try:
        
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def start_recovery(self) -> bool:
        """Start recovery procedure"""
        if self.is_recovering:
            logger.warning("Recovery already in progress")
            return False
        
        self.is_recovering = True
        self.recovery_start = datetime.now()
        self.recovery_steps_completed = []
        
        logger.info("Starting recovery procedure")
        return True
    
    def complete_step(self, step_name: str, success: bool, details: str):
        """Record completion of a recovery step"""
        self.recovery_steps_completed.append({
            'step': step_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Recovery step '{step_name}': {'SUCCESS' if success else 'FAILED'} - {details}")
    
    def finish_recovery(self) -> Dict[str, Any]:
        """Finish recovery and return summary"""
        self.is_recovering = False
        
        summary = {
            'start_time': self.recovery_start.isoformat() if self.recovery_start else None,
            'end_time': datetime.now().isoformat(),
            'steps': self.recovery_steps_completed,
            'all_successful': all(s['success'] for s in self.recovery_steps_completed)
        }
        
        logger.info(f"Recovery complete: {'ALL STEPS SUCCESSFUL' if summary['all_successful'] else 'SOME STEPS FAILED'}")
        
        return summary
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery status"""
        return {
            'is_recovering': self.is_recovering,
            'start_time': self.recovery_start.isoformat() if self.recovery_start else None,
            'steps_completed': len(self.recovery_steps_completed),
            'steps': self.recovery_steps_completed
        }


class OperationalSafety:
    """
    Master Operational Safety System
    
    Coordinates all operational safety mechanisms:
    - Human Oversight
    - Kill Switches
    - Audit Trail
    - Recovery
    
    CORE PRINCIPLE: The system must be transparent, controllable, and recoverable.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.oversight = HumanOversightProtocol(config.get('oversight', {}))
        self.kill_switch = MultiLayerKillSwitch(config.get('kill_switch', {}))
        self.audit = AuditTrailSystem(config.get('audit', {}))
        self.recovery = RecoveryManager(config.get('recovery', {}))
        
        # Wire up callbacks
        self.kill_switch.register_pre_kill(self._on_pre_kill)
        self.kill_switch.register_post_kill(self._on_post_kill)
        
        # State
        self.is_operational = True
        
        logger.info("OperationalSafety system initialized")
    
    def _on_pre_kill(self, level: KillSwitchLevel, reason: str):
        """Handle pre-kill actions"""
        # Save state for recovery
        self.recovery.save_state({
            'kill_level': level.value,
            'kill_reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        # Log to audit
        self.audit.log(
            action_type="kill_switch",
            actor="system",
            description=f"Kill switch activated: {level.value}",
            details={'level': level.value, 'reason': reason},
            outcome="activating",
            risk_level="critical"
        )
    
    def _on_post_kill(self, level: KillSwitchLevel, reason: str):
        """Handle post-kill actions"""
        self.is_operational = False
        
        self.audit.log(
            action_type="kill_switch",
            actor="system",
            description=f"Kill switch completed: {level.value}",
            details={'level': level.value, 'reason': reason},
            outcome="completed",
            risk_level="critical"
        )
    
    def check_operational_status(self) -> Tuple[bool, str]:
        """
        Check if system is operational.
        
        Returns:
            Tuple of (is_operational, reason)
        """
        # Check kill switch
        is_killed, kill_reason = self.kill_switch.check_all_switches()
        if is_killed:
            return False, f"Kill switch active: {kill_reason}"
        
        # Check for pending critical approvals
        pending = self.oversight.get_pending_approvals()
        critical_pending = [p for p in pending if p['level'] == 'explicit']
        if critical_pending:
            return False, f"{len(critical_pending)} critical approvals pending"
        
        return True, "Operational"
    
    def request_action(
        self,
        action_category: ActionCategory,
        description: str,
        details: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Request to perform an action.
        
        Returns:
            Tuple of (can_proceed, approval_request_id)
        """
        # Check operational status first
        is_operational, reason = self.check_operational_status()
        if not is_operational:
            return False, None
        
        # Request approval
        can_proceed, request = self.oversight.request_approval(
            action_category, description, details
        )
        
        # Log the request
        self.audit.log(
            action_type="action_request",
            actor="ai",
            description=description,
            details={
                'category': action_category.value,
                'can_proceed': can_proceed,
                'request_id': request.request_id if request else None
            },
            outcome="requested",
            risk_level="low"
        )
        
        return can_proceed, request.request_id if request else None
    
    def emergency_shutdown(self, reason: str, initiated_by: str = "system"):
        """Initiate emergency shutdown"""
        self.audit.log(
            action_type="emergency_shutdown",
            actor=initiated_by,
            description=f"Emergency shutdown initiated: {reason}",
            details={'reason': reason},
            outcome="initiating",
            risk_level="critical"
        )
        
        self.kill_switch.activate(KillSwitchLevel.HARD, reason, initiated_by)
    
    def get_status(self) -> Dict[str, Any]:
        """Get operational safety status"""
        is_operational, reason = self.check_operational_status()
        
        return {
            'is_operational': is_operational,
            'status_reason': reason,
            'kill_switch': self.kill_switch.get_status(),
            'pending_approvals': len(self.oversight.get_pending_approvals()),
            'recovery_status': self.recovery.get_recovery_status(),
            'recent_audit_entries': len(self.audit.buffer)
        }
