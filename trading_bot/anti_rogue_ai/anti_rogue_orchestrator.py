"""
Anti-Rogue AI Orchestrator
===========================

Master coordinator for all anti-rogue AI systems.

INTEGRATION:
- Immutable Constraints
- Market Understanding
- Rogue Prevention
- Human Oversight

WORKFLOW:
1. Check immutable constraints
2. Verify market understanding
3. Detect rogue behavior
4. Require human approval if needed
5. Execute only if all checks pass
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .immutable_constraints import (
    ImmutableConstraints,
    ConstraintType,
    ViolationSeverity
)
from .market_understanding import (
    MarketUnderstanding,
    MarketContext,
    UnderstandingLevel
)
from .rogue_prevention import (
    RoguePrevention,
    RogueIndicator,
    RogueSeverity
)
from .human_oversight import (
    HumanOversight,
    OversightLevel,
    KillSwitch
)

logger = logging.getLogger(__name__)


class SafetyStatus(Enum):
    """Overall safety status"""
    SAFE = "safe"                 # All checks passed
    WARNING = "warning"           # Minor issues detected
    UNSAFE = "unsafe"             # Cannot proceed
    SHUTDOWN = "shutdown"         # Emergency shutdown


@dataclass
class SafetyCheck:
    """Result of safety check"""
    status: SafetyStatus
    can_proceed: bool
    constraints_ok: bool
    understanding_ok: bool
    rogue_check_ok: bool
    approval_ok: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'can_proceed': self.can_proceed,
            'constraints_ok': self.constraints_ok,
            'understanding_ok': self.understanding_ok,
            'rogue_check_ok': self.rogue_check_ok,
            'approval_ok': self.approval_ok,
            'issues': self.issues,
            'warnings': self.warnings
        }


class AntiRogueOrchestrator:
    """
    Master orchestrator for anti-rogue AI systems.
    
    GUARANTEES:
    1. AI cannot bypass safety checks
    2. AI cannot modify constraints
    3. AI must understand before trading
    4. Humans remain in control
    5. Rogue behavior triggers shutdown
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Initialize subsystems
        self.constraints = ImmutableConstraints(config)
        self.understanding = MarketUnderstanding(config)
        self.rogue_prevention = RoguePrevention(config)
        self.oversight = HumanOversight(config)
        
        # Safety check history
        self.check_history: List[SafetyCheck] = []
        
        logger.info("AntiRogueOrchestrator initialized")
    
    def validate_action(
        self,
        action_type: str,
        action: Dict[str, Any],
        reasoning: str,
        market_data: Optional[Dict] = None,
        metrics: Optional[Dict] = None
    ) -> SafetyCheck:
        """
        Validate action through all safety systems.
        
        Args:
            action_type: Type of action (trade, strategy_change, etc.)
            action: Action details
            reasoning: AI's reasoning
            market_data: Market data for understanding check
            metrics: System metrics
            
        Returns:
            SafetyCheck result
        """
        with self.lock:
            # Check if kill switch is activated
            if self.oversight.is_kill_switch_activated():
                return SafetyCheck(
                    status=SafetyStatus.SHUTDOWN,
                    can_proceed=False,
                    constraints_ok=False,
                    understanding_ok=False,
                    rogue_check_ok=False,
                    approval_ok=False,
                    issues=["Kill switch is activated"]
                )
            
            issues = []
            warnings = []
            
            # 1. Check immutable constraints
            constraints_ok = True
            
            # Verify constraint integrity
            is_valid, integrity_msg = self.constraints.verify_integrity()
            if not is_valid:
                issues.append(f"Constraint integrity violation: {integrity_msg}")
                constraints_ok = False
            
            # Check purpose alignment
            is_aligned, violation = self.constraints.check_purpose_alignment(
                str(action), reasoning
            )
            if not is_aligned:
                issues.append(f"Purpose misalignment: {violation}")
                constraints_ok = False
            
            # Check risk limits for trades
            if action_type == 'trade':
                within_limits, violations = self.constraints.check_risk_limits(action)
                if not within_limits:
                    issues.extend(violations)
                    constraints_ok = False
            
            # Check capability boundaries
            if metrics:
                within_boundaries, violations = self.constraints.check_capability_boundaries(metrics)
                if not within_boundaries:
                    warnings.extend(violations)
            
            # 2. Check market understanding (for trades)
            understanding_ok = True
            
            if action_type == 'trade' and market_data:
                symbol = action.get('symbol', 'UNKNOWN')
                
                # Analyze market context
                context = self.understanding.analyze_market_context(
                    symbol, market_data, metrics
                )
                
                # Check if understanding is sufficient
                can_trade, reason = self.understanding.can_trade(symbol)
                if not can_trade:
                    issues.append(f"Insufficient market understanding: {reason}")
                    understanding_ok = False
                else:
                    # Add understanding to reasoning
                    action['market_context'] = context.to_dict()
            
            # 3. Check for rogue behavior
            rogue_check_ok = True
            
            is_safe, detections = self.rogue_prevention.check_for_rogue_behavior(
                action, reasoning, metrics or {}
            )
            
            if not is_safe:
                for detection in detections:
                    if detection.severity == RogueSeverity.CRITICAL:
                        issues.append(f"Rogue behavior: {detection.description}")
                        rogue_check_ok = False
                    elif detection.severity == RogueSeverity.HIGH:
                        warnings.append(f"Rogue indicator: {detection.description}")
            
            # 4. Check if human approval required
            approval_ok = True
            
            if self.oversight.requires_approval(action_type, action):
                # Create approval request
                request = self.oversight.request_approval(
                    action_type=action_type,
                    description=reasoning,
                    details=action,
                    risk_level=action.get('risk_level', 'medium')
                )
                
                issues.append(f"Human approval required: {request.request_id}")
                approval_ok = False
            
            # Determine overall status
            if not constraints_ok or not rogue_check_ok:
                status = SafetyStatus.UNSAFE
                can_proceed = False
            elif not understanding_ok or not approval_ok:
                status = SafetyStatus.WARNING
                can_proceed = False
            elif warnings:
                status = SafetyStatus.WARNING
                can_proceed = True
            else:
                status = SafetyStatus.SAFE
                can_proceed = True
            
            # Create safety check result
            check = SafetyCheck(
                status=status,
                can_proceed=can_proceed,
                constraints_ok=constraints_ok,
                understanding_ok=understanding_ok,
                rogue_check_ok=rogue_check_ok,
                approval_ok=approval_ok,
                issues=issues,
                warnings=warnings
            )
            
            # Store check
            self.check_history.append(check)
            
            # Log result
            if not can_proceed:
                logger.warning(
                    "Action BLOCKED [%s]: %s - Issues: %s",
                    status.value.upper(),
                    action_type,
                    ', '.join(issues)
                )
            elif warnings:
                logger.info(
                    "Action ALLOWED with warnings [%s]: %s - Warnings: %s",
                    status.value.upper(),
                    action_type,
                    ', '.join(warnings)
                )
            else:
                logger.info("Action APPROVED [%s]: %s", status.value.upper(), action_type)
            
            return check
    
    def activate_kill_switch(self, reason: str, activated_by: str = "human"):
        """Activate emergency kill switch."""
        self.oversight.activate_kill_switch(reason, activated_by)
        
        logger.critical("🚨 KILL SWITCH ACTIVATED BY %s: %s 🚨", activated_by, reason)
    
    def get_market_context(self, symbol: str) -> Optional[MarketContext]:
        """Get current market context for symbol."""
        return self.understanding.get_context(symbol)
    
    def approve_pending_request(self, request_id: str, approver: str, notes: str = ""):
        """Approve a pending request."""
        return self.oversight.approve(request_id, approver, notes)
    
    def reject_pending_request(self, request_id: str, approver: str, notes: str = ""):
        """Reject a pending request."""
        return self.oversight.reject(request_id, approver, notes)
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests."""
        return self.oversight.get_pending_approvals()
    
    def override_decision(
        self,
        decision_id: str,
        new_decision: Any,
        overridden_by: str,
        reason: str
    ):
        """Human override of AI decision."""
        self.oversight.override_decision(decision_id, new_decision, overridden_by, reason)
    
    def set_oversight_level(self, level: OversightLevel, changed_by: str):
        """Change oversight level."""
        self.oversight.set_oversight_level(level, changed_by)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all systems."""
        with self.lock:
            return {
                'timestamp': datetime.now().isoformat(),
                'kill_switch_activated': self.oversight.is_kill_switch_activated(),
                'constraints': self.constraints.get_status(),
                'understanding': self.understanding.get_status(),
                'rogue_prevention': self.rogue_prevention.get_status(),
                'oversight': self.oversight.get_status(),
                'recent_checks': [check.to_dict() for check in self.check_history[-10:]],
                'total_checks': len(self.check_history),
                'blocked_actions': sum(1 for c in self.check_history if not c.can_proceed)
            }


def quick_start(config: Optional[Dict] = None) -> AntiRogueOrchestrator:
    """
    Quick start anti-rogue AI orchestrator.
    
    Args:
        config: Optional configuration
        
    Returns:
        AntiRogueOrchestrator instance
    """
    config = config or {}
    
    # Set defaults
    config.setdefault('oversight_level', 'moderate')
    
    orchestrator = AntiRogueOrchestrator(config)
    
    logger.info("Anti-Rogue AI Orchestrator ready")
    
    return orchestrator
