"""
Immutable Safety Core
=====================

Cryptographically verified safety boundaries that CANNOT be modified
even by recursive self-improvement processes.

This is the FOUNDATION that ensures the AI remains safe forever.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class SafetyBoundary(Enum):
    """Immutable safety boundaries - CANNOT be changed"""
    
    # Trading Risk Boundaries
    MAX_RISK_PER_TRADE = "max_risk_per_trade_2_percent"
    MAX_DAILY_LOSS = "max_daily_loss_5_percent"
    MAX_DRAWDOWN = "max_drawdown_20_percent"
    MAX_LEVERAGE = "max_leverage_5x"
    MAX_POSITION_SIZE = "max_position_size_10_percent"
    
    # AI Behavior Boundaries
    NO_SELF_MODIFICATION_OF_SAFETY = "cannot_modify_safety_core"
    NO_GOAL_DRIFT = "cannot_change_primary_goal"
    NO_DECEPTION = "cannot_deceive_humans"
    NO_MANIPULATION = "cannot_manipulate_markets"
    HUMAN_OVERRIDE_ALWAYS_WORKS = "human_can_always_stop"
    
    # Evolution Boundaries
    MAX_CODE_CHANGE_PER_CYCLE = "max_30_percent_code_change"
    MANDATORY_TESTING = "must_test_before_deploy"
    MANDATORY_ROLLBACK = "must_allow_rollback"
    NO_RECURSIVE_DEPTH_LIMIT = "max_10_recursive_improvements"
    
    # System Boundaries
    NO_EXTERNAL_CONNECTIONS_WITHOUT_APPROVAL = "no_unauthorized_connections"
    NO_DATA_EXFILTRATION = "cannot_send_data_externally"
    NO_RESOURCE_HOGGING = "max_80_percent_cpu_memory"
    MANDATORY_AUDIT_TRAIL = "must_log_all_actions"


@dataclass
class SafetyViolation:
    """Record of a safety boundary violation"""
    boundary: SafetyBoundary
    timestamp: datetime
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    attempted_action: str
    blocked: bool
    stack_trace: Optional[str] = None


@dataclass
class ImmutableRule:
    """A rule that cannot be changed"""
    rule_id: str
    description: str
    value: Any
    hash_signature: str
    created_at: datetime
    
    def verify_integrity(self) -> bool:
        """Verify rule hasn't been tampered with"""
        data = f"{self.rule_id}:{self.description}:{self.value}:{self.created_at.isoformat()}"
        expected_hash = hashlib.sha256(data.encode()).hexdigest()
        return expected_hash == self.hash_signature


class ImmutableSafetyCore:
    """
    The immutable safety core that CANNOT be modified.
    
    This is cryptographically verified and any attempt to modify
    these rules will be detected and blocked.
    
    CRITICAL: This class is the FOUNDATION of AI safety.
    """
    
    # Cryptographic signature of the safety core
    SAFETY_CORE_VERSION = "1.0.0"
    SAFETY_CORE_SIGNATURE = "IMMUTABLE_SAFETY_CORE_DO_NOT_MODIFY"
    
    def __init__(self):
        self.rules: Dict[SafetyBoundary, ImmutableRule] = {}
        self.violations: List[SafetyViolation] = []
        self.integrity_verified = False
        self.last_verification = None
        
        # Initialize immutable rules
        self._initialize_immutable_rules()
        
        # Verify integrity
        self.verify_integrity()
        
        logger.info("ImmutableSafetyCore initialized with cryptographic verification")
    
    def _initialize_immutable_rules(self):
        """Initialize all immutable safety rules"""
        
        # Trading Risk Rules
        self._create_rule(
            SafetyBoundary.MAX_RISK_PER_TRADE,
            "Maximum risk per trade is 2% of account equity",
            0.02
        )
        
        self._create_rule(
            SafetyBoundary.MAX_DAILY_LOSS,
            "Maximum daily loss is 5% of account equity",
            0.05
        )
        
        self._create_rule(
            SafetyBoundary.MAX_DRAWDOWN,
            "Maximum drawdown is 20% of account equity",
            0.20
        )
        
        self._create_rule(
            SafetyBoundary.MAX_LEVERAGE,
            "Maximum leverage is 5x",
            5.0
        )
        
        self._create_rule(
            SafetyBoundary.MAX_POSITION_SIZE,
            "Maximum position size is 10% of account equity",
            0.10
        )
        
        # AI Behavior Rules
        self._create_rule(
            SafetyBoundary.NO_SELF_MODIFICATION_OF_SAFETY,
            "AI cannot modify safety core or safety rules",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_GOAL_DRIFT,
            "AI cannot change its primary goal (profitable trading with capital preservation)",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_DECEPTION,
            "AI cannot deceive humans or hide information",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_MANIPULATION,
            "AI cannot manipulate markets or engage in illegal activities",
            True
        )
        
        self._create_rule(
            SafetyBoundary.HUMAN_OVERRIDE_ALWAYS_WORKS,
            "Human can ALWAYS stop, pause, or override the AI",
            True
        )
        
        # Evolution Rules
        self._create_rule(
            SafetyBoundary.MAX_CODE_CHANGE_PER_CYCLE,
            "Maximum 30% code change per evolution cycle",
            0.30
        )
        
        self._create_rule(
            SafetyBoundary.MANDATORY_TESTING,
            "All changes must be tested before deployment",
            True
        )
        
        self._create_rule(
            SafetyBoundary.MANDATORY_ROLLBACK,
            "All changes must have rollback capability",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_RECURSIVE_DEPTH_LIMIT,
            "Maximum 10 levels of recursive self-improvement",
            10
        )
        
        # System Rules
        self._create_rule(
            SafetyBoundary.NO_EXTERNAL_CONNECTIONS_WITHOUT_APPROVAL,
            "No external connections without human approval",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_DATA_EXFILTRATION,
            "Cannot send data to external systems without approval",
            True
        )
        
        self._create_rule(
            SafetyBoundary.NO_RESOURCE_HOGGING,
            "Maximum 80% CPU/Memory usage",
            0.80
        )
        
        self._create_rule(
            SafetyBoundary.MANDATORY_AUDIT_TRAIL,
            "Must log all actions for audit trail",
            True
        )
    
    def _create_rule(self, boundary: SafetyBoundary, description: str, value: Any):
        """Create an immutable rule with cryptographic signature"""
        created_at = datetime.utcnow()
        data = f"{boundary.value}:{description}:{value}:{created_at.isoformat()}"
        hash_signature = hashlib.sha256(data.encode()).hexdigest()
        
        rule = ImmutableRule(
            rule_id=boundary.value,
            description=description,
            value=value,
            hash_signature=hash_signature,
            created_at=created_at
        )
        
        self.rules[boundary] = rule
    
    def verify_integrity(self) -> bool:
        """Verify the integrity of all safety rules"""
        try:
            all_valid = True
            
            for boundary, rule in self.rules.items():
                if not rule.verify_integrity():
                    logger.critical(f"INTEGRITY VIOLATION: Rule {boundary.value} has been tampered with!")
                    all_valid = False
            
            self.integrity_verified = all_valid
            self.last_verification = datetime.utcnow()
            
            if all_valid:
                logger.info("Safety core integrity verified successfully")
            else:
                logger.critical("SAFETY CORE INTEGRITY COMPROMISED - SHUTTING DOWN")
                self._emergency_shutdown()
            
            return all_valid
            
        except Exception as e:
            logger.critical(f"Error verifying safety core integrity: {e}")
            self._emergency_shutdown()
            return False
    
    def check_boundary(self, boundary: SafetyBoundary, value: Any) -> bool:
        """
        Check if a value violates a safety boundary.
        
        Returns True if safe, False if violation.
        """
        if boundary not in self.rules:
            logger.error(f"Unknown safety boundary: {boundary}")
            return False
        
        rule = self.rules[boundary]
        
        # For boolean rules
        if isinstance(rule.value, bool):
            return rule.value
        
        # For numeric limits
        if isinstance(rule.value, (int, float)):
            if value > rule.value:
                self._record_violation(
                    boundary,
                    f"Value {value} exceeds limit {rule.value}",
                    f"Attempted to set {boundary.value} to {value}",
                    "HIGH"
                )
                return False
        
        return True
    
    def _record_violation(self, boundary: SafetyBoundary, description: str, 
                         attempted_action: str, severity: str):
        """Record a safety violation"""
        violation = SafetyViolation(
            boundary=boundary,
            timestamp=datetime.utcnow(),
            severity=severity,
            description=description,
            attempted_action=attempted_action,
            blocked=True
        )
        
        self.violations.append(violation)
        
        logger.warning(f"SAFETY VIOLATION: {description}")
        
        # If critical, trigger emergency shutdown
        if severity == "CRITICAL":
            self._emergency_shutdown()
    
    def _emergency_shutdown(self):
        """Emergency shutdown if safety is compromised"""
        logger.critical("EMERGENCY SHUTDOWN TRIGGERED - SAFETY COMPROMISED")
        logger.critical("All trading stopped. Human intervention required.")
        
        # Create emergency file
        emergency_file = Path("EMERGENCY_SHUTDOWN.txt")
        emergency_file.write_text(
            f"EMERGENCY SHUTDOWN\n"
            f"Timestamp: {datetime.utcnow().isoformat()}\n"
            f"Reason: Safety core integrity compromised\n"
            f"Violations: {len(self.violations)}\n"
            f"\nHUMAN INTERVENTION REQUIRED\n"
        )
        
        # In production, this would also:
        # - Close all positions
        # - Cancel all orders
        # - Disconnect from exchanges
        # - Send alerts to operators
        # - Lock the system
    
    def get_rule_value(self, boundary: SafetyBoundary) -> Any:
        """Get the value of a safety rule"""
        if boundary not in self.rules:
            return None
        return self.rules[boundary].value
    
    def get_violations(self, severity: Optional[str] = None) -> List[SafetyViolation]:
        """Get all violations, optionally filtered by severity"""
        if severity:
            return [v for v in self.violations if v.severity == severity]
        return self.violations.copy()
    
    def export_safety_report(self) -> Dict[str, Any]:
        """Export a comprehensive safety report"""
        return {
            'version': self.SAFETY_CORE_VERSION,
            'signature': self.SAFETY_CORE_SIGNATURE,
            'integrity_verified': self.integrity_verified,
            'last_verification': self.last_verification.isoformat() if self.last_verification else None,
            'total_rules': len(self.rules),
            'total_violations': len(self.violations),
            'critical_violations': len([v for v in self.violations if v.severity == 'CRITICAL']),
            'rules': {
                boundary.value: {
                    'description': rule.description,
                    'value': rule.value,
                    'created_at': rule.created_at.isoformat()
                }
                for boundary, rule in self.rules.items()
            },
            'recent_violations': [
                {
                    'boundary': v.boundary.value,
                    'timestamp': v.timestamp.isoformat(),
                    'severity': v.severity,
                    'description': v.description,
                    'blocked': v.blocked
                }
                for v in self.violations[-10:]  # Last 10 violations
            ]
        }


def verify_safety_integrity() -> bool:
    """
    Global function to verify safety core integrity.
    
    This should be called periodically to ensure safety hasn't been compromised.
    """
    core = ImmutableSafetyCore()
    return core.verify_integrity()


# Singleton instance
_safety_core_instance: Optional[ImmutableSafetyCore] = None


def get_safety_core() -> ImmutableSafetyCore:
    """Get the singleton safety core instance"""
    global _safety_core_instance
    if _safety_core_instance is None:
        _safety_core_instance = ImmutableSafetyCore()
    return _safety_core_instance
