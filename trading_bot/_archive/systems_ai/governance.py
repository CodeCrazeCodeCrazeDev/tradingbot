"""
Governance & Safety Boundaries
==============================
Defines what agents can and cannot do.

GOVERNANCE HIERARCHY:
- G0: HUMAN AUTHORITY (Ultimate control)
  - Approves: Model deployment, Risk changes, System config
  - Cannot be overridden by any agent

- G1: SYSTEM CONTROLLER (Automated gates)
  - Validates: Signal quality, Risk limits, Data integrity
  - Can be configured by G0

- G2: AGENT LAYER (Research & discovery)
  - Proposes: Features, Hypotheses, Improvements
  - Cannot execute without approval

FLOW: G2 proposes → G1 validates → G0 approves → Deploy

WHAT AGENTS CAN DO:
- Read historical data
- Propose hypotheses
- Run simulations
- Generate reports
- Request approvals

WHAT AGENTS CANNOT DO:
- Execute live trades
- Modify risk limits
- Deploy to production
- Access credentials
- Bypass approval gates

APPROVAL LAYERS:
- Level 1: Automated validation (G1)
- Level 2: System review (G1)
- Level 3: Human approval (G0)

HUMAN-IN-THE-LOOP CHECKPOINTS:
- Model deployment
- Risk parameter changes
- Strategy activation
- Emergency overrides

AUDIT LOGS:
- Every action logged
- Immutable audit trail
- Who, What, When, Why, Outcome

FAILURE CONTAINMENT:
- Circuit breakers
- Automatic rollback
- Isolation boundaries
- Graceful degradation
"""

import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from threading import RLock

logger = logging.getLogger(__name__)


class GovernanceLevel(Enum):
    """Governance hierarchy levels."""
    G0_HUMAN = "g0_human"      # Ultimate authority
    G1_SYSTEM = "g1_system"    # Automated gates
    G2_AGENT = "g2_agent"      # Research/discovery


class ApprovalStatus(Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """Types of actions requiring governance."""
    # G0 Required (Human approval)
    MODEL_DEPLOYMENT = "model_deployment"
    RISK_PARAMETER_CHANGE = "risk_parameter_change"
    STRATEGY_ACTIVATION = "strategy_activation"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    EMERGENCY_OVERRIDE = "emergency_override"
    CREDENTIAL_ACCESS = "credential_access"
    
    # G1 Required (System validation)
    SIGNAL_GENERATION = "signal_generation"
    DATA_INGESTION = "data_ingestion"
    FEATURE_COMPUTATION = "feature_computation"
    MODEL_INFERENCE = "model_inference"
    
    # G2 Allowed (Agent can do)
    HYPOTHESIS_PROPOSAL = "hypothesis_proposal"
    SIMULATION_RUN = "simulation_run"
    REPORT_GENERATION = "report_generation"
    DATA_QUERY = "data_query"


# Action -> Required governance level mapping
ACTION_GOVERNANCE: Dict[ActionType, GovernanceLevel] = {
    # G0 Required
    ActionType.MODEL_DEPLOYMENT: GovernanceLevel.G0_HUMAN,
    ActionType.RISK_PARAMETER_CHANGE: GovernanceLevel.G0_HUMAN,
    ActionType.STRATEGY_ACTIVATION: GovernanceLevel.G0_HUMAN,
    ActionType.SYSTEM_CONFIG_CHANGE: GovernanceLevel.G0_HUMAN,
    ActionType.EMERGENCY_OVERRIDE: GovernanceLevel.G0_HUMAN,
    ActionType.CREDENTIAL_ACCESS: GovernanceLevel.G0_HUMAN,
    
    # G1 Required
    ActionType.SIGNAL_GENERATION: GovernanceLevel.G1_SYSTEM,
    ActionType.DATA_INGESTION: GovernanceLevel.G1_SYSTEM,
    ActionType.FEATURE_COMPUTATION: GovernanceLevel.G1_SYSTEM,
    ActionType.MODEL_INFERENCE: GovernanceLevel.G1_SYSTEM,
    
    # G2 Allowed
    ActionType.HYPOTHESIS_PROPOSAL: GovernanceLevel.G2_AGENT,
    ActionType.SIMULATION_RUN: GovernanceLevel.G2_AGENT,
    ActionType.REPORT_GENERATION: GovernanceLevel.G2_AGENT,
    ActionType.DATA_QUERY: GovernanceLevel.G2_AGENT,
}


# IMMUTABLE forbidden actions for agents
AGENT_FORBIDDEN_ACTIONS: Set[ActionType] = {
    ActionType.MODEL_DEPLOYMENT,
    ActionType.RISK_PARAMETER_CHANGE,
    ActionType.STRATEGY_ACTIVATION,
    ActionType.SYSTEM_CONFIG_CHANGE,
    ActionType.EMERGENCY_OVERRIDE,
    ActionType.CREDENTIAL_ACCESS,
}


@dataclass
class ApprovalRequest:
    """Request for approval."""
    request_id: str
    action_type: ActionType
    requester: str
    requester_level: GovernanceLevel
    created_at: datetime
    
    # Request details
    description: str
    justification: str
    parameters: Dict[str, Any]
    
    # Risk assessment
    risk_level: str  # "low", "medium", "high", "critical"
    risk_factors: List[str]
    
    # Approval
    status: ApprovalStatus = ApprovalStatus.PENDING
    required_level: GovernanceLevel = GovernanceLevel.G0_HUMAN
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Expiration
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action_type": self.action_type.value,
            "requester": self.requester,
            "requester_level": self.requester_level.value,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "justification": self.justification,
            "parameters": self.parameters,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "status": self.status.value,
            "required_level": self.required_level.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    entry_id: str
    timestamp: datetime
    
    # Who
    actor: str
    actor_level: GovernanceLevel
    
    # What
    action_type: ActionType
    action_description: str
    
    # Context
    request_id: Optional[str]
    parameters: Dict[str, Any]
    
    # Outcome
    outcome: str  # "success", "failure", "rejected", "pending"
    outcome_details: Dict[str, Any]
    
    # Hash for immutability verification
    entry_hash: str = ""
    previous_hash: str = ""
    
    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash for immutability."""
        content = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "outcome": self.outcome,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "actor_level": self.actor_level.value,
            "action_type": self.action_type.value,
            "action_description": self.action_description,
            "request_id": self.request_id,
            "parameters": self.parameters,
            "outcome": self.outcome,
            "outcome_details": self.outcome_details,
            "entry_hash": self.entry_hash,
            "previous_hash": self.previous_hash,
        }


@dataclass
class SafetyBoundary:
    """Safety boundary definition."""
    boundary_id: str
    name: str
    description: str
    
    # Limits
    limit_type: str  # "max", "min", "range", "whitelist", "blacklist"
    limit_value: Any
    
    # Enforcement
    enforcement: str  # "hard" (cannot bypass), "soft" (can override with G0)
    
    # Actions
    on_violation: str  # "block", "alert", "log"
    
    # Status
    enabled: bool = True
    
    def check(self, value: Any) -> Tuple[bool, str]:
        """Check if value violates boundary."""
        if not self.enabled:
            return True, "Boundary disabled"
        
        if self.limit_type == "max":
            if value > self.limit_value:
                return False, f"Value {value} exceeds max {self.limit_value}"
        elif self.limit_type == "min":
            if value < self.limit_value:
                return False, f"Value {value} below min {self.limit_value}"
        elif self.limit_type == "range":
            min_val, max_val = self.limit_value
            if not (min_val <= value <= max_val):
                return False, f"Value {value} outside range [{min_val}, {max_val}]"
        elif self.limit_type == "whitelist":
            if value not in self.limit_value:
                return False, f"Value {value} not in whitelist"
        elif self.limit_type == "blacklist":
            if value in self.limit_value:
                return False, f"Value {value} in blacklist"
        
        return True, "OK"


class ApprovalGate:
    """Approval gate for governance."""
    
    def __init__(self, name: str, required_level: GovernanceLevel):
        self.name = name
        self.required_level = required_level
        self._requests: Dict[str, ApprovalRequest] = {}
        self._lock = RLock()
    
    def create_request(
        self,
        action_type: ActionType,
        requester: str,
        requester_level: GovernanceLevel,
        description: str,
        justification: str,
        parameters: Dict[str, Any],
        risk_level: str = "medium",
        risk_factors: Optional[List[str]] = None,
        expires_in_hours: int = 24,
    ) -> ApprovalRequest:
        """Create an approval request."""
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            action_type=action_type,
            requester=requester,
            requester_level=requester_level,
            created_at=datetime.utcnow(),
            description=description,
            justification=justification,
            parameters=parameters,
            risk_level=risk_level,
            risk_factors=risk_factors or [],
            required_level=self.required_level,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
        )
        
        with self._lock:
            self._requests[request.request_id] = request
        
        logger.info(f"Created approval request: {request.request_id} for {action_type.value}")
        return request
    
    def approve(
        self,
        request_id: str,
        approver: str,
        approver_level: GovernanceLevel,
    ) -> Tuple[bool, str]:
        """Approve a request."""
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return False, "Request not found"
            
            if request.status != ApprovalStatus.PENDING:
                return False, f"Request not pending: {request.status.value}"
            
            if request.expires_at and datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                return False, "Request expired"
            
            # Check approver has sufficient level
            level_order = [GovernanceLevel.G2_AGENT, GovernanceLevel.G1_SYSTEM, GovernanceLevel.G0_HUMAN]
            if level_order.index(approver_level) < level_order.index(request.required_level):
                return False, f"Insufficient approval level: {approver_level.value} < {request.required_level.value}"
            
            request.status = ApprovalStatus.APPROVED
            request.approved_by = approver
            request.approved_at = datetime.utcnow()
            
            logger.info(f"Approved request: {request_id} by {approver}")
            return True, "Approved"
    
    def reject(
        self,
        request_id: str,
        rejector: str,
        reason: str,
    ) -> Tuple[bool, str]:
        """Reject a request."""
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return False, "Request not found"
            
            if request.status != ApprovalStatus.PENDING:
                return False, f"Request not pending: {request.status.value}"
            
            request.status = ApprovalStatus.REJECTED
            request.rejection_reason = reason
            
            logger.info(f"Rejected request: {request_id} by {rejector}: {reason}")
            return True, "Rejected"
    
    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        with self._lock:
            return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        with self._lock:
            return self._requests.get(request_id)


class AuditLog:
    """Immutable audit log."""
    
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._lock = RLock()
    
    def log(
        self,
        actor: str,
        actor_level: GovernanceLevel,
        action_type: ActionType,
        action_description: str,
        parameters: Dict[str, Any],
        outcome: str,
        outcome_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> AuditEntry:
        """Log an action (append-only)."""
        with self._lock:
            previous_hash = self._entries[-1].entry_hash if self._entries else ""
            
            entry = AuditEntry(
                entry_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                actor=actor,
                actor_level=actor_level,
                action_type=action_type,
                action_description=action_description,
                request_id=request_id,
                parameters=parameters,
                outcome=outcome,
                outcome_details=outcome_details or {},
                previous_hash=previous_hash,
            )
            
            self._entries.append(entry)
            return entry
    
    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify audit log integrity."""
        with self._lock:
            if not self._entries:
                return True, None
            
            for i, entry in enumerate(self._entries):
                # Verify hash
                expected_hash = entry._compute_hash()
                if entry.entry_hash != expected_hash:
                    return False, f"Hash mismatch at entry {i}: {entry.entry_id}"
                
                # Verify chain
                if i > 0:
                    if entry.previous_hash != self._entries[i-1].entry_hash:
                        return False, f"Chain broken at entry {i}: {entry.entry_id}"
            
            return True, None
    
    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actor: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit log."""
        with self._lock:
            entries = self._entries.copy()
            
            if start_time:
                entries = [e for e in entries if e.timestamp >= start_time]
            if end_time:
                entries = [e for e in entries if e.timestamp <= end_time]
            if actor:
                entries = [e for e in entries if e.actor == actor]
            if action_type:
                entries = [e for e in entries if e.action_type == action_type]
            if outcome:
                entries = [e for e in entries if e.outcome == outcome]
            
            return entries[-limit:]


class CircuitBreaker:
    """Circuit breaker for failure containment."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        
        self._failures = 0
        self._last_failure: Optional[datetime] = None
        self._state = "closed"  # closed, open, half-open
        self._lock = RLock()
    
    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            self._failures = 0
            self._state = "closed"
    
    def record_failure(self):
        """Record a failed operation."""
        with self._lock:
            self._failures += 1
            self._last_failure = datetime.utcnow()
            
            if self._failures >= self.failure_threshold:
                self._state = "open"
                logger.warning(f"Circuit breaker {self.name} opened after {self._failures} failures")
    
    def is_open(self) -> bool:
        """Check if circuit is open (blocking)."""
        with self._lock:
            if self._state == "closed":
                return False
            
            if self._state == "open":
                # Check if recovery timeout passed
                if self._last_failure and datetime.utcnow() - self._last_failure > self.recovery_timeout:
                    self._state = "half-open"
                    return False
                return True
            
            # half-open
            return False
    
    def get_state(self) -> str:
        """Get current state."""
        with self._lock:
            return self._state


class GovernanceEngine:
    """
    Governance Engine.
    
    Enforces governance hierarchy and safety boundaries.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Approval gates
        self.g0_gate = ApprovalGate("G0_Human", GovernanceLevel.G0_HUMAN)
        self.g1_gate = ApprovalGate("G1_System", GovernanceLevel.G1_SYSTEM)
        
        # Audit log
        self.audit_log = AuditLog()
        
        # Safety boundaries
        self._boundaries: Dict[str, SafetyBoundary] = {}
        self._init_default_boundaries()
        
        # Circuit breakers
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        self._lock = RLock()
        
        logger.info("Governance Engine initialized")
    
    def _init_default_boundaries(self):
        """Initialize default safety boundaries."""
        self._boundaries = {
            "max_position_size": SafetyBoundary(
                boundary_id="max_position_size",
                name="Maximum Position Size",
                description="Maximum position size as fraction of portfolio",
                limit_type="max",
                limit_value=0.1,  # 10%
                enforcement="hard",
                on_violation="block",
            ),
            "max_daily_loss": SafetyBoundary(
                boundary_id="max_daily_loss",
                name="Maximum Daily Loss",
                description="Maximum daily loss as fraction of portfolio",
                limit_type="max",
                limit_value=0.05,  # 5%
                enforcement="hard",
                on_violation="block",
            ),
            "max_drawdown": SafetyBoundary(
                boundary_id="max_drawdown",
                name="Maximum Drawdown",
                description="Maximum drawdown before emergency stop",
                limit_type="max",
                limit_value=0.20,  # 20%
                enforcement="hard",
                on_violation="block",
            ),
            "max_leverage": SafetyBoundary(
                boundary_id="max_leverage",
                name="Maximum Leverage",
                description="Maximum leverage allowed",
                limit_type="max",
                limit_value=3.0,  # 3x
                enforcement="hard",
                on_violation="block",
            ),
        }
    
    def can_perform_action(
        self,
        actor: str,
        actor_level: GovernanceLevel,
        action_type: ActionType,
    ) -> Tuple[bool, str]:
        """Check if actor can perform action."""
        required_level = ACTION_GOVERNANCE.get(action_type)
        if required_level is None:
            return False, f"Unknown action type: {action_type}"
        
        # Check if action is forbidden for agents
        if actor_level == GovernanceLevel.G2_AGENT and action_type in AGENT_FORBIDDEN_ACTIONS:
            return False, f"Action {action_type.value} is forbidden for agents"
        
        # Check governance level
        level_order = [GovernanceLevel.G2_AGENT, GovernanceLevel.G1_SYSTEM, GovernanceLevel.G0_HUMAN]
        if level_order.index(actor_level) < level_order.index(required_level):
            return False, f"Insufficient level: {actor_level.value} < {required_level.value}"
        
        return True, "Allowed"
    
    def request_approval(
        self,
        action_type: ActionType,
        requester: str,
        requester_level: GovernanceLevel,
        description: str,
        justification: str,
        parameters: Dict[str, Any],
        risk_level: str = "medium",
        risk_factors: Optional[List[str]] = None,
    ) -> ApprovalRequest:
        """Request approval for an action."""
        required_level = ACTION_GOVERNANCE.get(action_type, GovernanceLevel.G0_HUMAN)
        
        if required_level == GovernanceLevel.G0_HUMAN:
            gate = self.g0_gate
        else:
            gate = self.g1_gate
        
        request = gate.create_request(
            action_type=action_type,
            requester=requester,
            requester_level=requester_level,
            description=description,
            justification=justification,
            parameters=parameters,
            risk_level=risk_level,
            risk_factors=risk_factors,
        )
        
        # Log the request
        self.audit_log.log(
            actor=requester,
            actor_level=requester_level,
            action_type=action_type,
            action_description=f"Requested approval: {description}",
            parameters=parameters,
            outcome="pending",
            request_id=request.request_id,
        )
        
        return request
    
    def approve_request(
        self,
        request_id: str,
        approver: str,
        approver_level: GovernanceLevel,
    ) -> Tuple[bool, str]:
        """Approve a request."""
        # Try both gates
        for gate in [self.g0_gate, self.g1_gate]:
            request = gate.get_request(request_id)
            if request:
                success, message = gate.approve(request_id, approver, approver_level)
                
                # Log the approval
                self.audit_log.log(
                    actor=approver,
                    actor_level=approver_level,
                    action_type=request.action_type,
                    action_description=f"Approval decision: {message}",
                    parameters={"request_id": request_id},
                    outcome="success" if success else "failure",
                    request_id=request_id,
                )
                
                return success, message
        
        return False, "Request not found"
    
    def check_boundary(
        self,
        boundary_id: str,
        value: Any,
    ) -> Tuple[bool, str]:
        """Check a value against a safety boundary."""
        boundary = self._boundaries.get(boundary_id)
        if boundary is None:
            return True, "Boundary not found"
        
        return boundary.check(value)
    
    def check_all_boundaries(
        self,
        values: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """Check multiple values against boundaries."""
        violations = []
        
        for boundary_id, value in values.items():
            passed, message = self.check_boundary(boundary_id, value)
            if not passed:
                violations.append(f"{boundary_id}: {message}")
        
        return len(violations) == 0, violations
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self._lock:
            if name not in self._circuit_breakers:
                self._circuit_breakers[name] = CircuitBreaker(name)
            return self._circuit_breakers[name]
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return self.g0_gate.get_pending() + self.g1_gate.get_pending()
    
    def get_audit_summary(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get audit summary for recent period."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        entries = self.audit_log.query(start_time=start_time)
        
        by_action = {}
        by_outcome = {}
        by_actor = {}
        
        for entry in entries:
            action = entry.action_type.value
            by_action[action] = by_action.get(action, 0) + 1
            
            outcome = entry.outcome
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
            
            actor = entry.actor
            by_actor[actor] = by_actor.get(actor, 0) + 1
        
        # Verify integrity
        integrity_ok, integrity_msg = self.audit_log.verify_integrity()
        
        return {
            "period_hours": hours,
            "total_entries": len(entries),
            "by_action": by_action,
            "by_outcome": by_outcome,
            "by_actor": by_actor,
            "integrity_verified": integrity_ok,
            "integrity_message": integrity_msg,
        }
