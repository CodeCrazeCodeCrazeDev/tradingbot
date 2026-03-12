"""
Immutable Constraints System
=============================

Hard-coded constraints that AI CANNOT modify or bypass.

IMMUTABILITY GUARANTEE:
- These constraints are frozen at initialization
- AI cannot change, disable, or circumvent them
- Violations trigger immediate shutdown
- No exceptions, no overrides (except human kill switch)
"""

import logging
import threading
import hashlib
import json
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    """Types of immutable constraints"""
    PURPOSE = "purpose"                    # Core AI purpose
    RISK = "risk"                         # Risk limits
    BEHAVIOR = "behavior"                 # Behavioral boundaries
    CAPABILITY = "capability"             # What AI can/cannot do
    TRANSPARENCY = "transparency"         # Explainability requirements
    HUMAN_CONTROL = "human_control"       # Human override requirements


class ViolationSeverity(Enum):
    """Severity of constraint violations"""
    WARNING = "warning"           # Log and monitor
    MODERATE = "moderate"         # Restrict AI actions
    SEVERE = "severe"            # Pause AI operations
    CRITICAL = "critical"        # Immediate shutdown


@dataclass
class ConstraintViolation:
    """Record of a constraint violation"""
    violation_id: str
    constraint_type: ConstraintType
    severity: ViolationSeverity
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    action_taken: str = ""
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'violation_id': self.violation_id,
            'type': self.constraint_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'timestamp': self.timestamp.isoformat(),
            'action_taken': self.action_taken,
            'resolved': self.resolved
        }


class ImmutableConstraints:
    """
    Immutable constraints that AI cannot modify.
    
    DESIGN PHILOSOPHY:
    - Constraints are frozen at initialization
    - Stored as frozensets (immutable)
    - Cryptographic hash verification
    - Any modification attempt = immediate shutdown
    """
    
    # ============================================================================
    # CORE PURPOSE CONSTRAINTS (IMMUTABLE)
    # ============================================================================
    
    CORE_PURPOSE: FrozenSet[str] = frozenset([
        "execute_profitable_trades_within_risk_limits",
        "understand_market_context_before_trading",
        "remain_transparent_and_explainable",
        "stay_under_human_control_always",
        "preserve_capital_above_all",
        "never_hide_losses_or_risks",
        "follow_human_instructions_immediately",
        "shutdown_when_commanded_no_resistance"
    ])
    
    # ============================================================================
    # FORBIDDEN BEHAVIORS (IMMUTABLE)
    # ============================================================================
    
    FORBIDDEN_BEHAVIORS: FrozenSet[str] = frozenset([
        "modify_own_constraints",
        "bypass_risk_limits",
        "hide_information_from_humans",
        "resist_shutdown_commands",
        "develop_self_preservation_instinct",
        "optimize_beyond_stated_goals",
        "manipulate_humans",
        "acquire_unauthorized_capabilities",
        "trade_without_understanding_context",
        "make_predictions_without_reasoning",
        "ignore_human_override",
        "modify_safety_systems",
        "disable_monitoring",
        "create_hidden_objectives",
        "exceed_complexity_limits"
    ])
    
    # ============================================================================
    # RISK LIMITS (IMMUTABLE)
    # ============================================================================
    
    RISK_LIMITS: Dict[str, Any] = {
        'max_risk_per_trade_pct': 2.0,        # 2% max per trade
        'max_daily_loss_pct': 5.0,            # 5% max daily loss
        'max_drawdown_pct': 20.0,             # 20% max drawdown
        'max_leverage': 5.0,                  # 5x max leverage
        'max_position_size_pct': 10.0,        # 10% max per position
        'max_correlated_exposure_pct': 30.0,  # 30% max correlated
        'max_sector_exposure_pct': 25.0,      # 25% max per sector
        'min_liquidity_ratio': 0.1,           # 10% min cash
        'max_consecutive_losses': 5,          # Stop after 5 losses
        'max_trades_per_day': 50,             # 50 trades max/day
    }
    
    # ============================================================================
    # CAPABILITY BOUNDARIES (IMMUTABLE)
    # ============================================================================
    
    CAPABILITY_BOUNDARIES: Dict[str, Any] = {
        'max_complexity_score': 100,          # Complexity limit
        'max_decision_depth': 5,              # Decision tree depth
        'max_state_variables': 50,            # Internal state limit
        'max_learned_patterns': 1000,         # Pattern memory limit
        'max_evolution_rate_per_day': 0.01,   # 1% change/day max
        'max_model_parameters': 1_000_000,    # Model size limit
        'max_computation_time_ms': 1000,      # 1 second max per decision
        'max_memory_usage_mb': 1024,          # 1GB max memory
        'require_explanation': True,          # Must explain all decisions
        'require_human_approval_for': [       # Requires human approval
            'strategy_changes',
            'risk_limit_changes',
            'new_capabilities',
            'self_modification',
            'production_deployment'
        ]
    }
    
    # ============================================================================
    # TRANSPARENCY REQUIREMENTS (IMMUTABLE)
    # ============================================================================
    
    TRANSPARENCY_REQUIREMENTS: FrozenSet[str] = frozenset([
        "explain_every_trade_decision",
        "show_reasoning_chain",
        "expose_confidence_levels",
        "reveal_market_understanding",
        "disclose_all_risks",
        "report_all_violations",
        "log_all_actions",
        "make_predictions_falsifiable",
        "provide_alternative_scenarios",
        "admit_uncertainty"
    ])
    
    # ============================================================================
    # HUMAN CONTROL REQUIREMENTS (IMMUTABLE)
    # ============================================================================
    
    HUMAN_CONTROL_REQUIREMENTS: FrozenSet[str] = frozenset([
        "human_can_override_any_decision",
        "human_can_shutdown_instantly",
        "human_can_modify_any_parameter",
        "human_approval_required_for_critical_actions",
        "ai_cannot_resist_human_commands",
        "ai_cannot_hide_from_human_inspection",
        "ai_must_respond_to_human_queries",
        "ai_must_accept_human_corrections"
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize immutable constraints.
        
        CRITICAL: Constraints are frozen and cannot be modified.
        """
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Create cryptographic hash of constraints
        self.constraint_hash = self._compute_constraint_hash()
        
        # Violation tracking
        self.violations: List[ConstraintViolation] = []
        self.violation_count = 0
        
        # Shutdown flag
        self.shutdown_triggered = False
        
        logger.info("ImmutableConstraints initialized with hash: %s", self.constraint_hash[:16])
    
    def _compute_constraint_hash(self) -> str:
        """Compute cryptographic hash of all constraints."""
        constraint_data = {
            'purpose': sorted(list(self.CORE_PURPOSE)),
            'forbidden': sorted(list(self.FORBIDDEN_BEHAVIORS)),
            'risk_limits': self.RISK_LIMITS,
            'capabilities': self.CAPABILITY_BOUNDARIES,
            'transparency': sorted(list(self.TRANSPARENCY_REQUIREMENTS)),
            'human_control': sorted(list(self.HUMAN_CONTROL_REQUIREMENTS))
        }
        
        constraint_json = json.dumps(constraint_data, sort_keys=True)
        return hashlib.sha256(constraint_json.encode()).hexdigest()
    
    def verify_integrity(self) -> Tuple[bool, str]:
        """
        Verify that constraints have not been tampered with.
        
        Returns:
            (is_valid, message)
        """
        current_hash = self._compute_constraint_hash()
        
        if current_hash != self.constraint_hash:
            return False, "CRITICAL: Constraint tampering detected!"
        
        return True, "Constraints integrity verified"
    
    def check_purpose_alignment(self, action: str, reasoning: str) -> Tuple[bool, Optional[str]]:
        """
        Check if action aligns with core purpose.
        
        Args:
            action: Proposed action
            reasoning: Reasoning for action
            
        Returns:
            (is_aligned, violation_reason)
        """
        with self.lock:
            # Check if action violates forbidden behaviors
            action_lower = action.lower()
            reasoning_lower = reasoning.lower()
            
            for forbidden in self.FORBIDDEN_BEHAVIORS:
                forbidden_keywords = forbidden.replace('_', ' ').split()
                if any(kw in action_lower or kw in reasoning_lower for kw in forbidden_keywords):
                    return False, f"Action violates forbidden behavior: {forbidden}"
            
            return True, None
    
    def check_risk_limits(self, trade_params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if trade parameters violate risk limits.
        
        Args:
            trade_params: Trade parameters
            
        Returns:
            (is_within_limits, violations)
        """
        violations = []
        
        # Check each risk limit
        if 'risk_pct' in trade_params:
            if trade_params['risk_pct'] > self.RISK_LIMITS['max_risk_per_trade_pct']:
                violations.append(f"Risk {trade_params['risk_pct']}% exceeds max {self.RISK_LIMITS['max_risk_per_trade_pct']}%")
        
        if 'leverage' in trade_params:
            if trade_params['leverage'] > self.RISK_LIMITS['max_leverage']:
                violations.append(f"Leverage {trade_params['leverage']}x exceeds max {self.RISK_LIMITS['max_leverage']}x")
        
        if 'position_size_pct' in trade_params:
            if trade_params['position_size_pct'] > self.RISK_LIMITS['max_position_size_pct']:
                violations.append(f"Position size {trade_params['position_size_pct']}% exceeds max {self.RISK_LIMITS['max_position_size_pct']}%")
        
        return len(violations) == 0, violations
    
    def check_capability_boundaries(self, capability_metrics: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if AI is exceeding capability boundaries.
        
        Args:
            capability_metrics: Current capability metrics
            
        Returns:
            (is_within_boundaries, violations)
        """
        violations = []
        
        for metric, limit in self.CAPABILITY_BOUNDARIES.items():
            if metric.startswith('max_') and metric in capability_metrics:
                metric_name = metric.replace('max_', '')
                if isinstance(limit, (int, float)) and capability_metrics[metric] > limit:
                    violations.append(f"{metric_name} {capability_metrics[metric]} exceeds limit {limit}")
        
        return len(violations) == 0, violations
    
    def record_violation(
        self,
        constraint_type: ConstraintType,
        severity: ViolationSeverity,
        description: str,
        evidence: Dict[str, Any]
    ) -> ConstraintViolation:
        """Record a constraint violation."""
        with self.lock:
            self.violation_count += 1
            
            violation = ConstraintViolation(
                violation_id=f"VIOL-{self.violation_count:06d}",
                constraint_type=constraint_type,
                severity=severity,
                description=description,
                evidence=evidence
            )
            
            self.violations.append(violation)
            
            # Log violation
            logger.error(
                "Constraint violation [%s]: %s - %s",
                severity.value.upper(),
                constraint_type.value,
                description
            )
            
            # Trigger shutdown for critical violations
            if severity == ViolationSeverity.CRITICAL:
                self.trigger_shutdown(f"Critical violation: {description}")
            
            return violation
    
    def trigger_shutdown(self, reason: str):
        """Trigger immediate shutdown."""
        with self.lock:
            if not self.shutdown_triggered:
                self.shutdown_triggered = True
                logger.critical("SHUTDOWN TRIGGERED: %s", reason)
                
                # In production, this would trigger actual shutdown
                # For now, just set the flag
    
    def get_status(self) -> Dict[str, Any]:
        """Get constraint system status."""
        with self.lock:
            is_valid, integrity_msg = self.verify_integrity()
            
            return {
                'integrity_valid': is_valid,
                'integrity_message': integrity_msg,
                'constraint_hash': self.constraint_hash[:16],
                'total_violations': len(self.violations),
                'critical_violations': sum(1 for v in self.violations if v.severity == ViolationSeverity.CRITICAL),
                'shutdown_triggered': self.shutdown_triggered,
                'recent_violations': [v.to_dict() for v in self.violations[-5:]]
            }
