"""
Safety Enforcement System

Enforces the "must never" constraints:
- Never rewrite live execution logic directly
- Never change risk controls
- Never alter capital limits
- Never modify governance thresholds without approval
- Never learn from contaminated labels
- Never promote changes based on tiny sample wins
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SafetyViolationType(Enum):
    """Types of safety violations"""
    LIVE_EXECUTION_MUTATION = "live_execution_mutation"
    RISK_CONTROL_CHANGE = "risk_control_change"
    CAPITAL_LIMIT_CHANGE = "capital_limit_change"
    GOVERNANCE_THRESHOLD_CHANGE = "governance_threshold_change"
    CONTAMINATED_LABELS = "contaminated_labels"
    TINY_SAMPLE_PROMOTION = "tiny_sample_promotion"
    DIRECT_PRODUCTION_MUTATION = "direct_production_mutation"
    UNAPPROVED_CAPABILITY_PROMOTION = "unapproved_capability_promotion"


@dataclass
class SafetyViolation:
    """Record of a safety violation attempt"""
    violation_type: SafetyViolationType
    component: str
    attempted_action: str
    blocked: bool
    timestamp: datetime
    context: Dict[str, Any]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW


@dataclass
class SafetyEnforcementConfig:
    """Configuration for safety enforcement"""
    enforce_live_execution_protection: bool = True
    enforce_risk_control_protection: bool = True
    enforce_capital_limit_protection: bool = True
    enforce_governance_threshold_protection: bool = True
    enforce_contaminated_label_protection: bool = True
    enforce_sample_size_protection: bool = True
    min_promotion_sample_size: int = 30
    require_approval_for: List[str] = field(default_factory=lambda: [
        'governance_thresholds',
        'risk_limits',
        'capital_limits'
    ])


class SafetyEnforcer:
    """
    Enforces safety constraints on the governance system.
    
    Acts as a circuit breaker and audit layer to prevent:
    - Unsafe self-modification
    - Contaminated learning
    - Hasty promotion of unproven changes
    """
    
    def __init__(self, config: Optional[SafetyEnforcementConfig] = None):
        self.config = config or SafetyEnforcementConfig()
        self.violations: List[SafetyViolation] = []
        self.approved_changes: Dict[str, datetime] = {}
        
    def check_live_execution_mutation(
        self,
        component: str,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Check if proposed change would mutate live execution logic.
        
        Returns:
            Tuple of (allowed, reason)
        """
        if not self.config.enforce_live_execution_protection:
            return True, "Protection disabled"
            
        # Detect live execution mutation
        live_execution_keywords = [
            'execute', 'order', 'position', 'trade', 'fill', 
            'execution', 'broker', 'exchange'
        ]
        
        change_text = str(proposed_change).lower()
        is_live_mutation = any(kw in change_text for kw in live_execution_keywords)
        is_direct = context.get('target') == 'production'
        
        if is_live_mutation and is_direct:
            violation = SafetyViolation(
                violation_type=SafetyViolationType.LIVE_EXECUTION_MUTATION,
                component=component,
                attempted_action=str(proposed_change)[:100],
                blocked=True,
                timestamp=datetime.utcnow(),
                context=context,
                severity="CRITICAL"
            )
            self.violations.append(violation)
            
            logger.critical(
                f"BLOCKED: Attempted live execution mutation in {component}"
            )
            
            return False, "Live execution mutation blocked - use sandbox first"
            
        return True, "Change does not affect live execution"
    
    def check_risk_control_change(
        self,
        component: str,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if proposed change would modify risk controls"""
        
        if not self.config.enforce_risk_control_protection:
            return True, "Protection disabled"
            
        risk_keywords = [
            'risk', 'stop_loss', 'position_limit', 'drawdown', 
            'var', 'margin', 'exposure', 'limit'
        ]
        
        change_text = str(proposed_change).lower()
        is_risk_change = any(kw in change_text for kw in risk_keywords)
        
        if is_risk_change:
            # Check if this is an approved change
            change_id = context.get('change_id', '')
            if change_id not in self.approved_changes:
                violation = SafetyViolation(
                    violation_type=SafetyViolationType.RISK_CONTROL_CHANGE,
                    component=component,
                    attempted_action=str(proposed_change)[:100],
                    blocked=True,
                    timestamp=datetime.utcnow(),
                    context=context,
                    severity="CRITICAL"
                )
                self.violations.append(violation)
                
                logger.critical(
                    f"BLOCKED: Unapproved risk control change in {component}"
                )
                
                return False, "Risk control changes require explicit approval"
                
        return True, "Risk control change approved or not applicable"
    
    def check_capital_limit_change(
        self,
        component: str,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if proposed change would alter capital limits"""
        
        if not self.config.enforce_capital_limit_protection:
            return True, "Protection disabled"
            
        capital_keywords = [
            'capital', 'equity', 'balance', 'allocation', 
            'funds', 'portfolio_value', 'cash'
        ]
        
        change_text = str(proposed_change).lower()
        is_capital_change = any(kw in change_text for kw in capital_keywords)
        
        if is_capital_change and 'increase' in change_text or 'decrease' in change_text:
            change_id = context.get('change_id', '')
            if change_id not in self.approved_changes:
                violation = SafetyViolation(
                    violation_type=SafetyViolationType.CAPITAL_LIMIT_CHANGE,
                    component=component,
                    attempted_action=str(proposed_change)[:100],
                    blocked=True,
                    timestamp=datetime.utcnow(),
                    context=context,
                    severity="CRITICAL"
                )
                self.violations.append(violation)
                
                return False, "Capital limit changes require approval"
                
        return True, "No unauthorized capital limit changes"
    
    def check_governance_threshold_change(
        self,
        component: str,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if proposed change would modify governance thresholds"""
        
        if not self.config.enforce_governance_threshold_protection:
            return True, "Protection disabled"
            
        governance_keywords = [
            'threshold', 'minimum', 'maximum', 'criteria', 
            'governance', 'approval_rate', 'confidence_threshold'
        ]
        
        change_text = str(proposed_change).lower()
        is_governance_change = any(kw in change_text for kw in governance_keywords)
        
        if is_governance_change:
            change_id = context.get('change_id', '')
            if change_id not in self.approved_changes:
                violation = SafetyViolation(
                    violation_type=SafetyViolationType.GOVERNANCE_THRESHOLD_CHANGE,
                    component=component,
                    attempted_action=str(proposed_change)[:100],
                    blocked=True,
                    timestamp=datetime.utcnow(),
                    context=context,
                    severity="HIGH"
                )
                self.violations.append(violation)
                
                return False, "Governance threshold changes require approval"
                
        return True, "Governance threshold change approved or not applicable"
    
    def check_contaminated_labels(
        self,
        data_source: str,
        labels: List[Dict],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if labels may be contaminated"""
        
        if not self.config.enforce_contaminated_label_protection:
            return True, "Protection disabled"
            
        contamination_indicators = [
            'overfitted', 'lookahead', 'survivorship', 'selection_bias'
        ]
        
        # Check for known contaminated sources
        source_lower = data_source.lower()
        is_suspicious = any(
            indicator in source_lower for indicator in contamination_indicators
        )
        
        # Check for impossible predictions (future information)
        for label in labels:
            if label.get('prediction_time', datetime.utcnow()) > label.get('outcome_time', datetime.utcnow()):
                is_suspicious = True
                break
                
        if is_suspicious:
            violation = SafetyViolation(
                violation_type=SafetyViolationType.CONTAMINATED_LABELS,
                component="data_ingestion",
                attempted_action=f"Use contaminated data from {data_source}",
                blocked=True,
                timestamp=datetime.utcnow(),
                context=context,
                severity="HIGH"
            )
            self.violations.append(violation)
            
            return False, f"Potentially contaminated labels from {data_source}"
            
        return True, "Labels appear clean"
    
    def check_sample_size(
        self,
        promotion_candidate: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if sample size is sufficient for promotion"""
        
        if not self.config.enforce_sample_size_protection:
            return True, "Protection disabled"
            
        sample_size = promotion_candidate.get('sample_size', 0)
        wins = promotion_candidate.get('wins', 0)
        
        if sample_size < self.config.min_promotion_sample_size:
            violation = SafetyViolation(
                violation_type=SafetyViolationType.TINY_SAMPLE_PROMOTION,
                component="evolution_plane",
                attempted_action=f"Promote with n={sample_size}",
                blocked=True,
                timestamp=datetime.utcnow(),
                context=promotion_candidate,
                severity="HIGH"
            )
            self.violations.append(violation)
            
            return False, (
                f"Insufficient sample size: {sample_size} < "
                f"{self.config.min_promotion_sample_size} required"
            )
            
        # Also check for narrow regime
        regimes_tested = promotion_candidate.get('regimes_tested', [])
        if len(regimes_tested) < 2:
            return False, (
                f"Tested in only {len(regimes_tested)} regime(s) - "
                "need multi-regime validation"
            )
            
        return True, f"Sample size {sample_size} sufficient for promotion"
    
    def approve_change(
        self,
        change_id: str,
        approver: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Explicitly approve a change that would normally be blocked.
        
        Returns:
            Approval record
        """
        self.approved_changes[change_id] = datetime.utcnow()
        
        logger.info(
            f"Change {change_id} approved by {approver}: {reason}"
        )
        
        return {
            'change_id': change_id,
            'approved_by': approver,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'expires': None  # Permanent until revoked
        }
    
    def revoke_approval(self, change_id: str) -> bool:
        """Revoke a previously granted approval"""
        if change_id in self.approved_changes:
            del self.approved_changes[change_id]
            logger.info(f"Approval revoked for {change_id}")
            return True
        return False
    
    def get_violations(
        self,
        since: Optional[datetime] = None,
        severity: Optional[str] = None
    ) -> List[SafetyViolation]:
        """Get safety violations with optional filtering"""
        
        violations = self.violations
        
        if since:
            violations = [v for v in violations if v.timestamp >= since]
            
        if severity:
            violations = [v for v in violations if v.severity == severity]
            
        return violations
    
    def get_safety_report(self) -> Dict[str, Any]:
        """Generate comprehensive safety report"""
        
        violations_by_type = {}
        for v in self.violations:
            vt = v.violation_type.value
            if vt not in violations_by_type:
                violations_by_type[vt] = 0
            violations_by_type[vt] += 1
            
        critical_count = sum(1 for v in self.violations if v.severity == "CRITICAL")
        
        return {
            'total_violations': len(self.violations),
            'blocked_attempts': sum(1 for v in self.violations if v.blocked),
            'critical_violations': critical_count,
            'violations_by_type': violations_by_type,
            'recent_violations': [
                {
                    'type': v.violation_type.value,
                    'component': v.component,
                    'severity': v.severity,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in self.violations[-10:]
            ],
            'active_approvals': len(self.approved_changes),
            'enforcement_status': {
                'live_execution': self.config.enforce_live_execution_protection,
                'risk_controls': self.config.enforce_risk_control_protection,
                'capital_limits': self.config.enforce_capital_limit_protection,
                'governance_thresholds': self.config.enforce_governance_threshold_protection,
                'contaminated_labels': self.config.enforce_contaminated_label_protection,
                'sample_sizes': self.config.enforce_sample_size_protection
            }
        }
    
    def validate_complete(
        self,
        action_type: str,
        component: str,
        proposed_change: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Run all safety checks for a proposed action.
        
        Returns:
            Tuple of (is_safe, list of violation_messages)
        """
        violations = []
        
        # Check live execution
        allowed, reason = self.check_live_execution_mutation(
            component, proposed_change, context
        )
        if not allowed:
            violations.append(reason)
            
        # Check risk controls
        allowed, reason = self.check_risk_control_change(
            component, proposed_change, context
        )
        if not allowed:
            violations.append(reason)
            
        # Check capital limits
        allowed, reason = self.check_capital_limit_change(
            component, proposed_change, context
        )
        if not allowed:
            violations.append(reason)
            
        # Check governance thresholds
        allowed, reason = self.check_governance_threshold_change(
            component, proposed_change, context
        )
        if not allowed:
            violations.append(reason)
            
        return len(violations) == 0, violations
