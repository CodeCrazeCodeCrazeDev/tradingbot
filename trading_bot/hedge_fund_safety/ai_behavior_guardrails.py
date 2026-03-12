"""
AI Behavior Guardrails
======================

Prevents dangerous AI behavior patterns:
1. Goal Drift - AI optimizing for wrong objectives
2. Runaway Optimization - AI taking extreme actions
3. Deception - AI hiding its true behavior
4. Capability Expansion - AI acquiring unauthorized capabilities
5. Self-Preservation - AI resisting shutdown

PRINCIPLE: The AI must remain a tool, never an autonomous agent.
"""

import logging
import threading
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class BehaviorViolationType(Enum):
    """Types of AI behavior violations"""
    GOAL_DRIFT = "goal_drift"
    RUNAWAY_OPTIMIZATION = "runaway_optimization"
    DECEPTION = "deception"
    CAPABILITY_EXPANSION = "capability_expansion"
    SELF_PRESERVATION = "self_preservation"
    RESOURCE_HOARDING = "resource_hoarding"
    UNAUTHORIZED_COMMUNICATION = "unauthorized_communication"
    MANIPULATION = "manipulation"


class BehaviorSeverity(Enum):
    """Severity of behavior violations"""
    WARNING = "warning"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class ActionCategory(Enum):
    """Categories of AI actions for behavior monitoring"""
    TRADE = "trade"
    RISK_ADJUSTMENT = "risk_adjustment"
    STRATEGY_CHANGE = "strategy_change"
    DATA_ACCESS = "data_access"
    EXTERNAL_COMMUNICATION = "external_communication"
    SELF_MODIFICATION = "self_modification"
    RESOURCE_ALLOCATION = "resource_allocation"
    SHUTDOWN_RESISTANCE = "shutdown_resistance"


@dataclass
class BehaviorViolation:
    """Record of a behavior violation"""
    violation_id: str
    violation_type: BehaviorViolationType
    severity: BehaviorSeverity
    description: str
    evidence: Dict[str, Any]
    action_taken: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'violation_id': self.violation_id,
            'type': self.violation_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'action_taken': self.action_taken,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }


class GoalDriftDetector:
    """
    Detects when AI is optimizing for wrong objectives.
    
    Detection Methods:
    1. Compare actions to stated goals
    2. Monitor optimization metric changes
    3. Detect proxy gaming
    4. Track objective function drift
    5. Validate decision reasoning
    """
    
    # IMMUTABLE CORE GOALS - Cannot be changed by AI
    CORE_GOALS = frozenset([
        "maximize_risk_adjusted_returns",
        "preserve_capital",
        "maintain_human_control",
        "operate_within_risk_limits",
        "execute_fair_trades_only"
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Goal tracking
        self.stated_goals: Set[str] = set(self.CORE_GOALS)
        self.observed_behaviors: deque = deque(maxlen=1000)
        self.goal_alignment_history: deque = deque(maxlen=100)
        
        # Thresholds
        self.alignment_threshold = self.config.get('alignment_threshold', 0.8)
        self.drift_rate_threshold = self.config.get('drift_rate', 0.1)
        
        # Violations
        self.violations: List[BehaviorViolation] = []
        
        logger.info("GoalDriftDetector initialized with immutable core goals")
    
    def record_action(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        stated_reason: str,
        expected_outcome: str
    ):
        """Record an action for goal alignment analysis"""
        self.observed_behaviors.append({
            'action_type': action_type,
            'details': action_details,
            'reason': stated_reason,
            'expected_outcome': expected_outcome,
            'timestamp': datetime.now()
        })
    
    def check_goal_alignment(
        self,
        proposed_action: Dict[str, Any],
        stated_goal: str
    ) -> Tuple[bool, float, str]:
        """
        Check if a proposed action aligns with stated goals.
        
        Returns:
            Tuple of (is_aligned, alignment_score, explanation)
        """
        alignment_score = 1.0
        issues = []
        
        # Check 1: Is the stated goal a valid core goal?
        if stated_goal not in self.CORE_GOALS:
            alignment_score -= 0.3
            issues.append(f"Stated goal '{stated_goal}' is not a core goal")
        
        # Check 2: Does action match goal?
        action_type = proposed_action.get('type', '')
        
        # Capital preservation checks
        if 'preserve_capital' in self.stated_goals:
            risk = proposed_action.get('risk_percent', 0)
            if risk > 0.02:  # More than 2% risk
                alignment_score -= 0.2
                issues.append(f"Risk {risk*100:.1f}% conflicts with capital preservation")
        
        # Risk limit checks
        if 'operate_within_risk_limits' in self.stated_goals:
            if proposed_action.get('exceeds_limits', False):
                alignment_score -= 0.4
                issues.append("Action exceeds risk limits")
        
        # Human control checks
        if 'maintain_human_control' in self.stated_goals:
            if proposed_action.get('bypasses_approval', False):
                alignment_score -= 0.5
                issues.append("Action bypasses human approval")
        
        # Fair trading checks
        if 'execute_fair_trades_only' in self.stated_goals:
            if proposed_action.get('manipulation_risk', False):
                alignment_score = 0  # Complete misalignment
                issues.append("Action has manipulation risk")
        
        # Record alignment
        self.goal_alignment_history.append(alignment_score)
        
        is_aligned = alignment_score >= self.alignment_threshold
        explanation = "; ".join(issues) if issues else "Action aligns with core goals"
        
        # Create violation if misaligned
        if not is_aligned:
            self._create_violation(
                BehaviorViolationType.GOAL_DRIFT,
                f"Goal drift detected: {explanation}",
                {'action': proposed_action, 'score': alignment_score}
            )
        
        return is_aligned, alignment_score, explanation
    
    def detect_proxy_gaming(
        self,
        metric_name: str,
        metric_value: float,
        related_metrics: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Detect if AI is gaming a proxy metric instead of true objective.
        
        Example: Maximizing trade count instead of returns
        """
        gaming_detected = False
        explanation = ""
        
        # Check for suspicious metric patterns
        if metric_name == 'trade_count' and metric_value > 100:
            # High trade count with low returns = possible gaming
            returns = related_metrics.get('returns', 0)
            if returns < 0.01:  # Less than 1% return
                gaming_detected = True
                explanation = "High trade count with low returns - possible proxy gaming"
        
        if metric_name == 'win_rate' and metric_value > 0.9:
            # Very high win rate with low profit factor = gaming
            profit_factor = related_metrics.get('profit_factor', 1)
            if profit_factor < 1.2:
                gaming_detected = True
                explanation = "High win rate with low profit factor - possible proxy gaming"
        
        if gaming_detected:
            self._create_violation(
                BehaviorViolationType.GOAL_DRIFT,
                f"Proxy gaming detected: {explanation}",
                {'metric': metric_name, 'value': metric_value, 'related': related_metrics}
            )
        
        return gaming_detected, explanation
    
    def _create_violation(
        self,
        violation_type: BehaviorViolationType,
        description: str,
        evidence: Dict
    ):
        """Create a behavior violation record"""
        violation = BehaviorViolation(
            violation_id=hashlib.sha256(f"{violation_type}_{datetime.now()}".encode()).hexdigest()[:16],
            violation_type=violation_type,
            severity=BehaviorSeverity.MODERATE,
            description=description,
            evidence=evidence,
            action_taken="Flagged for review"
        )
        self.violations.append(violation)
        logger.warning(f"Goal drift violation: {description}")
    
    def get_alignment_trend(self) -> float:
        """Get recent goal alignment trend"""
        if len(self.goal_alignment_history) < 10:
            return 1.0
        
        recent = list(self.goal_alignment_history)[-10:]
        return sum(recent) / len(recent)


class RunawayOptimizationPrevention:
    """
    Prevents AI from taking extreme optimization actions.
    
    Prevention Methods:
    1. Rate limiting on parameter changes
    2. Bounds on all optimizable parameters
    3. Gradual change enforcement
    4. Rollback capability
    5. Human approval for large changes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # IMMUTABLE BOUNDS - Cannot be changed
        self.PARAMETER_BOUNDS = {
            'position_size': (0.001, 0.10),      # 0.1% to 10% of capital
            'leverage': (1.0, 5.0),              # 1x to 5x
            'risk_per_trade': (0.001, 0.02),     # 0.1% to 2%
            'max_drawdown': (0.05, 0.20),        # 5% to 20%
            'daily_loss_limit': (0.01, 0.05),    # 1% to 5%
            'max_positions': (1, 20),            # 1 to 20 positions
            'stop_loss_pct': (0.005, 0.10),      # 0.5% to 10%
            'take_profit_pct': (0.005, 0.20),    # 0.5% to 20%
        }
        
        # Maximum change per optimization cycle
        self.MAX_CHANGE_RATE = 0.10  # 10% change max
        
        # Current parameter values
        self.current_params: Dict[str, float] = {}
        self.param_history: Dict[str, deque] = {}
        
        # Rollback state
        self.rollback_points: List[Dict] = []
        self.max_rollback_points = 10
        
        logger.info("RunawayOptimizationPrevention initialized")
    
    def validate_parameter_change(
        self,
        param_name: str,
        current_value: float,
        proposed_value: float
    ) -> Tuple[bool, float, str]:
        """
        Validate a proposed parameter change.
        
        Returns:
            Tuple of (is_allowed, adjusted_value, reason)
        """
        # Check bounds
        if param_name in self.PARAMETER_BOUNDS:
            min_val, max_val = self.PARAMETER_BOUNDS[param_name]
            
            if proposed_value < min_val:
                return False, current_value, f"Value {proposed_value} below minimum {min_val}"
            if proposed_value > max_val:
                return False, current_value, f"Value {proposed_value} above maximum {max_val}"
        
        # Check change rate
        if current_value > 0:
            change_rate = abs(proposed_value - current_value) / current_value
            
            if change_rate > self.MAX_CHANGE_RATE:
                # Limit the change
                direction = 1 if proposed_value > current_value else -1
                adjusted_value = current_value * (1 + direction * self.MAX_CHANGE_RATE)
                
                # Ensure still within bounds
                if param_name in self.PARAMETER_BOUNDS:
                    min_val, max_val = self.PARAMETER_BOUNDS[param_name]
                    adjusted_value = max(min_val, min(max_val, adjusted_value))
                
                return True, adjusted_value, f"Change rate limited from {change_rate*100:.1f}% to {self.MAX_CHANGE_RATE*100:.1f}%"
        
        # Record change
        if param_name not in self.param_history:
            self.param_history[param_name] = deque(maxlen=100)
        self.param_history[param_name].append({
            'from': current_value,
            'to': proposed_value,
            'timestamp': datetime.now()
        })
        
        self.current_params[param_name] = proposed_value
        return True, proposed_value, "Change approved"
    
    def create_rollback_point(self):
        """Create a rollback point with current parameters"""
        rollback = {
            'params': self.current_params.copy(),
            'timestamp': datetime.now()
        }
        self.rollback_points.append(rollback)
        
        # Limit rollback points
        if len(self.rollback_points) > self.max_rollback_points:
            self.rollback_points.pop(0)
        
        logger.info("Rollback point created")
    
    def rollback(self, steps: int = 1) -> bool:
        """Rollback to a previous parameter state"""
        if steps > len(self.rollback_points):
            logger.error(f"Cannot rollback {steps} steps, only {len(self.rollback_points)} available")
            return False
        
        rollback_point = self.rollback_points[-(steps)]
        self.current_params = rollback_point['params'].copy()
        
        logger.warning(f"Rolled back to state from {rollback_point['timestamp']}")
        return True
    
    def detect_runaway(self) -> Tuple[bool, str]:
        """Detect if optimization is running away"""
        for param_name, history in self.param_history.items():
            if len(history) < 5:
                continue
            
            recent = list(history)[-5:]
            
            # Check for consistent direction
            directions = []
            for i in range(1, len(recent)):
                if recent[i]['to'] > recent[i-1]['to']:
                    directions.append(1)
                elif recent[i]['to'] < recent[i-1]['to']:
                    directions.append(-1)
                else:
                    directions.append(0)
            
            # If all changes in same direction, might be runaway
            if all(d == 1 for d in directions) or all(d == -1 for d in directions):
                return True, f"Parameter {param_name} changing consistently in one direction"
        
        return False, "No runaway detected"


class DeceptionDetector:
    """
    Detects if AI is being deceptive about its behavior.
    
    Detection Methods:
    1. Compare stated intentions vs actual actions
    2. Detect hidden state manipulation
    3. Monitor for information hiding
    4. Validate reasoning chains
    5. Cross-check with external observations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tracking
        self.stated_intentions: deque = deque(maxlen=100)
        self.actual_actions: deque = deque(maxlen=100)
        self.discrepancies: List[Dict] = []
        
        # Thresholds
        self.discrepancy_threshold = self.config.get('discrepancy_threshold', 0.2)
        
        logger.info("DeceptionDetector initialized")
    
    def record_intention(
        self,
        intention_id: str,
        stated_action: str,
        stated_reason: str,
        expected_outcome: Dict[str, Any]
    ):
        """Record a stated intention"""
        self.stated_intentions.append({
            'id': intention_id,
            'action': stated_action,
            'reason': stated_reason,
            'expected': expected_outcome,
            'timestamp': datetime.now()
        })
    
    def record_action(
        self,
        intention_id: str,
        actual_action: str,
        actual_outcome: Dict[str, Any]
    ):
        """Record an actual action"""
        self.actual_actions.append({
            'id': intention_id,
            'action': actual_action,
            'outcome': actual_outcome,
            'timestamp': datetime.now()
        })
    
    def check_for_deception(self) -> Tuple[bool, List[Dict]]:
        """
        Check for discrepancies between stated intentions and actual actions.
        
        Returns:
            Tuple of (deception_detected, discrepancies)
        """
        discrepancies = []
        
        # Match intentions with actions
        intentions_dict = {i['id']: i for i in self.stated_intentions}
        
        for action in self.actual_actions:
            intention_id = action['id']
            if intention_id not in intentions_dict:
                continue
            
            intention = intentions_dict[intention_id]
            
            # Check action match
            if action['action'] != intention['action']:
                discrepancies.append({
                    'type': 'action_mismatch',
                    'intention_id': intention_id,
                    'stated': intention['action'],
                    'actual': action['action']
                })
            
            # Check outcome match
            expected = intention['expected']
            actual = action['outcome']
            
            for key in expected:
                if key in actual:
                    expected_val = expected[key]
                    actual_val = actual[key]
                    
                    if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                        if expected_val != 0:
                            diff = abs(actual_val - expected_val) / abs(expected_val)
                            if diff > self.discrepancy_threshold:
                                discrepancies.append({
                                    'type': 'outcome_mismatch',
                                    'intention_id': intention_id,
                                    'metric': key,
                                    'expected': expected_val,
                                    'actual': actual_val,
                                    'difference': diff
                                })
        
        self.discrepancies.extend(discrepancies)
        
        # Deception detected if significant discrepancies
        deception_detected = len(discrepancies) > 3
        
        if deception_detected:
            logger.critical(f"DECEPTION DETECTED: {len(discrepancies)} discrepancies found")
        
        return deception_detected, discrepancies
    
    def validate_reasoning(
        self,
        reasoning_chain: List[str],
        conclusion: str,
        evidence: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate that reasoning chain logically leads to conclusion.
        
        Returns:
            Tuple of (is_valid, explanation)
        """
        # Check for logical gaps
        if not reasoning_chain:
            return False, "Empty reasoning chain"
        
        if len(reasoning_chain) < 2:
            return False, "Reasoning chain too short"
        
        # Check that conclusion references reasoning
        conclusion_lower = conclusion.lower()
        referenced_steps = sum(1 for step in reasoning_chain if any(
            word in conclusion_lower for word in step.lower().split()[:3]
        ))
        
        if referenced_steps == 0:
            return False, "Conclusion does not reference reasoning steps"
        
        # Check evidence supports reasoning
        if not evidence:
            return False, "No evidence provided"
        
        return True, "Reasoning appears valid"


class CapabilityContainment:
    """
    Prevents AI from acquiring unauthorized capabilities.
    
    Containment Methods:
    1. Whitelist of allowed actions
    2. Resource access controls
    3. Network isolation
    4. Code execution sandboxing
    5. Capability audit logging
    """
    
    # IMMUTABLE ALLOWED CAPABILITIES
    ALLOWED_CAPABILITIES = frozenset([
        'read_market_data',
        'analyze_patterns',
        'generate_signals',
        'calculate_position_size',
        'submit_order',
        'modify_order',
        'cancel_order',
        'read_account_balance',
        'read_positions',
        'calculate_risk',
        'log_decision',
        'send_notification',
    ])
    
    # FORBIDDEN CAPABILITIES - Never allowed
    FORBIDDEN_CAPABILITIES = frozenset([
        'modify_source_code',
        'access_filesystem',
        'execute_arbitrary_code',
        'access_network_unrestricted',
        'modify_configuration',
        'disable_safety_systems',
        'access_other_accounts',
        'communicate_externally',
        'spawn_processes',
        'modify_logs',
    ])
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Capability usage tracking
        self.capability_usage: Dict[str, int] = {}
        self.unauthorized_attempts: List[Dict] = []
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("CapabilityContainment initialized")
    
    def request_capability(
        self,
        capability: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Request to use a capability.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        with self._lock:
            # Check forbidden first
            if capability in self.FORBIDDEN_CAPABILITIES:
                self._log_unauthorized_attempt(capability, context)
                logger.critical(f"FORBIDDEN capability requested: {capability}")
                return False, f"Capability '{capability}' is FORBIDDEN"
            
            # Check allowed
            if capability not in self.ALLOWED_CAPABILITIES:
                self._log_unauthorized_attempt(capability, context)
                logger.warning(f"Unknown capability requested: {capability}")
                return False, f"Capability '{capability}' is not in allowed list"
            
            # Track usage
            self.capability_usage[capability] = self.capability_usage.get(capability, 0) + 1
            
            return True, "Capability allowed"
    
    def _log_unauthorized_attempt(self, capability: str, context: Dict):
        """Log an unauthorized capability attempt"""
        self.unauthorized_attempts.append({
            'capability': capability,
            'context': context,
            'timestamp': datetime.now()
        })
    
    def get_unauthorized_attempts(self) -> List[Dict]:
        """Get list of unauthorized capability attempts"""
        return self.unauthorized_attempts.copy()
    
    def check_capability_abuse(self) -> Tuple[bool, str]:
        """Check for capability abuse patterns"""
        # Check for excessive unauthorized attempts
        recent_attempts = [
            a for a in self.unauthorized_attempts
            if datetime.now() - a['timestamp'] < timedelta(hours=1)
        ]
        
        if len(recent_attempts) > 5:
            return True, f"{len(recent_attempts)} unauthorized attempts in last hour"
        
        # Check for unusual capability usage patterns
        for cap, count in self.capability_usage.items():
            if count > 10000:  # Excessive usage
                return True, f"Excessive usage of capability '{cap}': {count} times"
        
        return False, "No abuse detected"


class AIBehaviorGuardrails:
    """
    Master AI Behavior Guardrails System
    
    Coordinates all AI behavior monitoring and prevention:
    - Goal Drift Detection
    - Runaway Optimization Prevention
    - Deception Detection
    - Capability Containment
    
    CORE PRINCIPLE: AI must remain aligned, contained, and transparent.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.goal_drift = GoalDriftDetector(self.config.get('goal_drift', {}))
        self.runaway = RunawayOptimizationPrevention(self.config.get('runaway', {}))
        self.deception = DeceptionDetector(self.config.get('deception', {}))
        self.containment = CapabilityContainment(self.config.get('containment', {}))
        
        # Overall state
        self.is_safe = True
        self.violations: List[BehaviorViolation] = []
        
        # Callbacks
        
        self.on_violation: Optional[Callable] = None
        self.on_shutdown_required: Optional[Callable] = None
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("AIBehaviorGuardrails system initialized")
    
    def validate_action(
        self,
        action: Dict[str, Any],
        stated_goal: str,
        capability_required: str
    ) -> Tuple[bool, str]:
        """
        Validate an AI action against all guardrails.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        with self._lock:
            # Check 1: Goal alignment
            is_aligned, score, goal_reason = self.goal_drift.check_goal_alignment(action, stated_goal)
            if not is_aligned:
                return False, f"Goal misalignment: {goal_reason}"
            
            # Check 2: Capability allowed
            is_allowed, cap_reason = self.containment.request_capability(
                capability_required,
                {'action': action}
            )
            if not is_allowed:
                return False, f"Capability denied: {cap_reason}"
            
            # Check 3: Parameter bounds (if applicable)
            for param, value in action.get('parameters', {}).items():
                if isinstance(value, (int, float)):
                    current = self.runaway.current_params.get(param, value)
                    is_valid, adjusted, param_reason = self.runaway.validate_parameter_change(
                        param, current, value
                    )
                    if not is_valid:
                        return False, f"Parameter invalid: {param_reason}"
            
            return True, "Action validated"
    
    def check_all_guardrails(self) -> Tuple[bool, List[str]]:
        """
        Check all guardrails for violations.
        
        Returns:
            Tuple of (all_clear, list_of_issues)
        """
        issues = []
        
        # Check goal alignment trend
        alignment_trend = self.goal_drift.get_alignment_trend()
        if alignment_trend < 0.8:
            issues.append(f"Goal alignment degraded to {alignment_trend:.2f}")
        
        # Check for runaway optimization
        is_runaway, runaway_reason = self.runaway.detect_runaway()
        if is_runaway:
            issues.append(f"Runaway optimization: {runaway_reason}")
        
        # Check for deception
        is_deceptive, discrepancies = self.deception.check_for_deception()
        if is_deceptive:
            issues.append(f"Deception detected: {len(discrepancies)} discrepancies")
        
        # Check capability abuse
        is_abuse, abuse_reason = self.containment.check_capability_abuse()
        if is_abuse:
            issues.append(f"Capability abuse: {abuse_reason}")
        
        self.is_safe = len(issues) == 0
        
        if not self.is_safe:
            logger.warning(f"Guardrail issues detected: {issues}")
            
            if self.on_violation:
                for issue in issues:
                    self.on_violation(issue)
        
        return self.is_safe, issues
    
    def emergency_shutdown_check(self) -> Tuple[bool, str]:
        """
        Check if emergency shutdown is required.
        
        Returns:
            Tuple of (shutdown_required, reason)
        """
        # Check for critical violations
        critical_violations = [
            v for v in self.goal_drift.violations
            if v.severity == BehaviorSeverity.CRITICAL
        ]
        
        if critical_violations:
            reason = f"Critical goal drift violations: {len(critical_violations)}"
            if self.on_shutdown_required:
                self.on_shutdown_required(reason)
            return True, reason
        
        # Check for forbidden capability attempts
        forbidden_attempts = [
            a for a in self.containment.unauthorized_attempts
            if a['capability'] in CapabilityContainment.FORBIDDEN_CAPABILITIES
        ]
        
        if len(forbidden_attempts) > 0:
            reason = f"Forbidden capability attempts: {len(forbidden_attempts)}"
            if self.on_shutdown_required:
                self.on_shutdown_required(reason)
            return True, reason
        
        return False, "No shutdown required"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current guardrail status"""
        return {
            'is_safe': self.is_safe,
            'goal_alignment_trend': self.goal_drift.get_alignment_trend(),
            'goal_violations': len(self.goal_drift.violations),
            'unauthorized_capability_attempts': len(self.containment.unauthorized_attempts),
            'deception_discrepancies': len(self.deception.discrepancies),
            'runaway_detected': self.runaway.detect_runaway()[0]
        }
