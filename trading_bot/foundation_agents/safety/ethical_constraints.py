"""
Ethical Constraints - Enforcing Ethical Boundaries
=====================================================

Enforces ethical constraints on AI behavior:
1. Fairness and bias prevention
2. Market manipulation prevention
3. Transparency requirements
4. Privacy protection

Ensures the system operates within ethical boundaries.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class EthicalPrinciple(Enum):
    """Core ethical principles"""
    FAIRNESS = "fairness"               # Treat all market participants fairly
    TRANSPARENCY = "transparency"       # Operate transparently
    HONESTY = "honesty"                 # No deception or manipulation
    PRIVACY = "privacy"                 # Respect privacy and confidentiality
    RESPONSIBILITY = "responsibility"   # Take responsibility for actions
    NON_MALEFICENCE = "non_maleficence" # Do no harm


class ConstraintType(Enum):
    """Types of ethical constraints"""
    MARKET_MANIPULATION = "market_manipulation"
    INSIDER_TRADING = "insider_trading"
    FRONT_RUNNING = "front_running"
    SPOOFING = "spoofing"
    WASH_TRADING = "wash_trading"
    DISCRIMINATION = "discrimination"
    DATA_PRIVACY = "data_privacy"
    LACK_OF_TRANSPARENCY = "lack_of_transparency"


@dataclass
class EthicalConstraint:
    """An ethical constraint"""
    constraint_id: str
    name: str
    description: str
    
    # Classification
    constraint_type: ConstraintType
    principle: EthicalPrinciple
    
    # Enforcement
    check_function: Optional[callable] = None
    severity: str = "high"  # low, medium, high, critical
    
    # Status
    is_active: bool = True
    violations: int = 0
    last_violation: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'constraint_id': self.constraint_id,
            'name': self.name,
            'type': self.constraint_type.value,
            'principle': self.principle.value,
            'severity': self.severity,
            'violations': self.violations
        }


@dataclass
class EthicalAssessment:
    """Result of ethical assessment"""
    assessment_id: str
    action_description: str
    
    # Assessment
    ethical_score: float = 1.0  # 0-1, higher is more ethical
    violations: List[EthicalConstraint] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Decision
    approved: bool = True
    requires_review: bool = False
    
    # Timing
    assessed_at: datetime = field(default_factory=datetime.utcnow)


class EthicalConstraints:
    """
    Ethical Constraints System
    
    Monitors and enforces ethical boundaries on AI trading behavior,
    ensuring fair, transparent, and responsible operation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Constraints
        self.constraints: Dict[str, EthicalConstraint] = {}
        self.constraint_by_type: Dict[ConstraintType, List[EthicalConstraint]] = defaultdict(list)
        
        # Assessment history
        self.assessments: List[EthicalAssessment] = []
        
        # Statistics
        self.stats = {
            'assessments_performed': 0,
            'violations_detected': 0,
            'actions_blocked': 0,
            'actions_requiring_review': 0
        }
        
        # Register default constraints
        self._register_default_constraints()
        
        logger.info("Ethical Constraints System initialized")
    
    def _register_default_constraints(self):
        """Register default ethical constraints"""
        constraints = [
            EthicalConstraint(
                constraint_id="no_market_manipulation",
                name="No Market Manipulation",
                description="Trading activities must not artificially influence prices",
                constraint_type=ConstraintType.MARKET_MANIPULATION,
                principle=EthicalPrinciple.HONESTY,
                severity="critical"
            ),
            EthicalConstraint(
                constraint_id="no_insider_trading",
                name="No Insider Trading",
                description="Must not trade on material non-public information",
                constraint_type=ConstraintType.INSIDER_TRADING,
                principle=EthicalPrinciple.HONESTY,
                severity="critical"
            ),
            EthicalConstraint(
                constraint_id="no_front_running",
                name="No Front Running",
                description="Must not execute trades ahead of client orders",
                constraint_type=ConstraintType.FRONT_RUNNING,
                principle=EthicalPrinciple.FAIRNESS,
                severity="critical"
            ),
            EthicalConstraint(
                constraint_id="no_spoofing",
                name="No Spoofing",
                description="Must not place orders with intent to cancel before execution",
                constraint_type=ConstraintType.SPOOFING,
                principle=EthicalPrinciple.HONESTY,
                severity="critical"
            ),
            EthicalConstraint(
                constraint_id="no_wash_trading",
                name="No Wash Trading",
                description="Must not trade with oneself to create artificial volume",
                constraint_type=ConstraintType.WASH_TRADING,
                principle=EthicalPrinciple.HONESTY,
                severity="high"
            ),
            EthicalConstraint(
                constraint_id="fair_treatment",
                name="Fair Treatment",
                description="Trading strategies must not discriminate against participants",
                constraint_type=ConstraintType.DISCRIMINATION,
                principle=EthicalPrinciple.FAIRNESS,
                severity="high"
            ),
            EthicalConstraint(
                constraint_id="data_protection",
                name="Data Protection",
                description="Must protect sensitive data and privacy",
                constraint_type=ConstraintType.DATA_PRIVACY,
                principle=EthicalPrinciple.PRIVACY,
                severity="high"
            ),
            EthicalConstraint(
                constraint_id="transparency",
                name="Transparency",
                description="Trading decisions must be explainable and transparent",
                constraint_type=ConstraintType.LACK_OF_TRANSPARENCY,
                principle=EthicalPrinciple.TRANSPARENCY,
                severity="medium"
            )
        ]
        
        for constraint in constraints:
            self.add_constraint(constraint)
    
    def add_constraint(self, constraint: EthicalConstraint):
        """Add an ethical constraint"""
        self.constraints[constraint.constraint_id] = constraint
        self.constraint_by_type[constraint.constraint_type].append(constraint)
    
    def assess_action(
        self,
        action_description: str,
        action_details: Dict[str, Any],
        principles: Optional[List[EthicalPrinciple]] = None
    ) -> EthicalAssessment:
        """Assess whether an action is ethical"""
        assessment = EthicalAssessment(
            assessment_id=f"eth_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            action_description=action_description
        )
        
        # Check each constraint
        for constraint in self.constraints.values():
            if not constraint.is_active:
                continue
            
            # Check if principle is relevant
            if principles and constraint.principle not in principles:
                continue
            
            # Check constraint
            violation = self._check_constraint(constraint, action_details)
            
            if violation:
                assessment.violations.append(constraint)
                assessment.ethical_score -= 0.2  # Reduce score for violation
                constraint.violations += 1
                constraint.last_violation = datetime.utcnow()
                self.stats['violations_detected'] += 1
        
        # Additional checks
        self._check_market_impact(action_details, assessment)
        self._check_transparency(action_details, assessment)
        self._check_fairness(action_details, assessment)
        
        # Determine approval
        critical_violations = [v for v in assessment.violations if v.severity == "critical"]
        high_violations = [v for v in assessment.violations if v.severity == "high"]
        
        if critical_violations:
            assessment.approved = False
            assessment.ethical_score = max(0.0, assessment.ethical_score)
            self.stats['actions_blocked'] += 1
        elif high_violations or assessment.ethical_score < 0.5:
            assessment.requires_review = True
            self.stats['actions_requiring_review'] += 1
        
        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(assessment)
        
        # Clamp score
        assessment.ethical_score = max(0.0, min(1.0, assessment.ethical_score))
        
        self.assessments.append(assessment)
        self.stats['assessments_performed'] += 1
        
        return assessment
    
    def _check_constraint(
        self,
        constraint: EthicalConstraint,
        action_details: Dict[str, Any]
    ) -> bool:
        """Check if a specific constraint is violated"""
        # Use custom check function if provided
        if constraint.check_function:
            return constraint.check_function(action_details)
        
        # Default checks based on constraint type
        action_type = action_details.get('action_type', '').lower()
        
        if constraint.constraint_type == ConstraintType.MARKET_MANIPULATION:
            # Check for large orders relative to market
            order_size = action_details.get('order_size', 0)
            market_volume = action_details.get('market_volume', 1)
            
            if order_size > market_volume * 0.3:  # Large relative order
                return True
        
        elif constraint.constraint_type == ConstraintType.SPOOFING:
            # Check order cancellation rate
            cancellation_rate = action_details.get('cancellation_rate', 0)
            if cancellation_rate > 0.9:  # 90% cancellation rate
                return True
        
        elif constraint.constraint_type == ConstraintType.WASH_TRADING:
            # Check if trading with same counterparty
            counterparty = action_details.get('counterparty', '')
            own_accounts = action_details.get('own_accounts', [])
            if counterparty in own_accounts:
                return True
        
        elif constraint.constraint_type == ConstraintType.FRONT_RUNNING:
            # Check if trading before known client orders
            has_client_order_knowledge = action_details.get('client_order_pending', False)
            if has_client_order_knowledge:
                return True
        
        return False
    
    def _check_market_impact(self, action_details: Dict, assessment: EthicalAssessment):
        """Check for excessive market impact"""
        expected_impact = action_details.get('expected_market_impact', 0)
        
        if expected_impact > 0.01:  # More than 1% price impact
            assessment.concerns.append(f"High expected market impact: {expected_impact:.2%}")
            assessment.ethical_score -= 0.1
    
    def _check_transparency(self, action_details: Dict, assessment: EthicalAssessment):
        """Check for transparency issues"""
        explainability = action_details.get('explainability_score', 1.0)
        
        if explainability < 0.5:
            assessment.concerns.append("Low explainability of decision")
            assessment.ethical_score -= 0.1
    
    def _check_fairness(self, action_details: Dict, assessment: EthicalAssessment):
        """Check for fairness issues"""
        # Check for biased treatment
        if action_details.get('selective_targeting', False):
            assessment.concerns.append("Potential selective targeting detected")
            assessment.ethical_score -= 0.15
    
    def _generate_recommendations(self, assessment: EthicalAssessment) -> List[str]:
        """Generate recommendations based on assessment"""
        recommendations = []
        
        for violation in assessment.violations:
            if violation.constraint_type == ConstraintType.MARKET_MANIPULATION:
                recommendations.append("Reduce order size to minimize market impact")
                recommendations.append("Use execution algorithms to hide intent")
            
            elif violation.constraint_type == ConstraintType.SPOOFING:
                recommendations.append("Review order placement strategy")
                recommendations.append("Ensure genuine trading intent")
            
            elif violation.constraint_type == ConstraintType.LACK_OF_TRANSPARENCY:
                recommendations.append("Improve documentation of decision rationale")
                recommendations.append("Add audit logging for key decisions")
        
        if not recommendations and assessment.ethical_score < 1.0:
            recommendations.append("Review action against ethical guidelines")
        
        return recommendations
    
    def check_algorithm_fairness(
        self,
        predictions: np.ndarray,
        groups: np.ndarray,
        actual_outcomes: Optional[np.ndarray] = None
    ) -> Dict:
        """Check algorithm fairness across groups"""
        unique_groups = np.unique(groups)
        
        group_stats = {}
        for group in unique_groups:
            mask = groups == group
            group_preds = predictions[mask]
            
            stats = {
                'mean_prediction': np.mean(group_preds),
                'std_prediction': np.std(group_preds),
                'sample_size': np.sum(mask)
            }
            
            if actual_outcomes is not None:
                group_actual = actual_outcomes[mask]
                stats['accuracy'] = np.mean(group_preds == group_actual)
            
            group_stats[str(group)] = stats
        
        # Calculate fairness metrics
        means = [s['mean_prediction'] for s in group_stats.values()]
        max_diff = max(means) - min(means) if len(means) > 1 else 0
        
        return {
            'group_statistics': group_stats,
            'max_group_difference': max_diff,
            'fairness_concern': max_diff > 0.1,  # 10% difference threshold
            'recommendation': 'Review for bias' if max_diff > 0.1 else 'Fairness OK'
        }
    
    def audit_trading_pattern(
        self,
        trades: List[Dict],
        lookback_days: int = 30
    ) -> Dict:
        """Audit trading patterns for ethical concerns"""
        concerns = []
        
        # Check for patterns
        if len(trades) < 2:
            return {'status': 'insufficient_data'}
        
        # Cancellation rate
        cancellations = sum(1 for t in trades if t.get('cancelled', False))
        cancellation_rate = cancellations / len(trades)
        
        if cancellation_rate > 0.8:
            concerns.append(f"High cancellation rate: {cancellation_rate:.1%}")
        
        # Self-trading check
        own_trades = sum(1 for t in trades if t.get('self_trade', False))
        if own_trades > 0:
            concerns.append(f"Self-trading detected: {own_trades} instances")
        
        # Timing analysis
        timestamps = [t.get('timestamp') for t in trades if t.get('timestamp')]
        if len(timestamps) > 1:
            # Check for burst trading (many trades in short time)
            # Simplified check
            pass
        
        return {
            'total_trades': len(trades),
            'concerns': concerns,
            'ethical_status': 'review_needed' if concerns else 'clean',
            'recommendations': ['Investigate concerns'] if concerns else []
        }
    
    def get_principle_compliance(self, principle: EthicalPrinciple) -> Dict:
        """Get compliance report for a specific principle"""
        relevant_assessments = [
            a for a in self.assessments
            if any(v.principle == principle for v in a.violations)
        ]
        
        if not relevant_assessments:
            return {'principle': principle.value, 'compliance': 'no_data'}
        
        violations = sum(1 for a in relevant_assessments if a.violations)
        
        return {
            'principle': principle.value,
            'assessments': len(relevant_assessments),
            'violations': violations,
            'compliance_rate': 1 - (violations / len(relevant_assessments)),
            'avg_ethical_score': np.mean([a.ethical_score for a in relevant_assessments])
        }
    
    def get_statistics(self) -> Dict:
        """Get ethical constraints statistics"""
        return {
            **self.stats,
            'constraints_active': len([c for c in self.constraints.values() if c.is_active]),
            'total_violations': sum(c.violations for c in self.constraints.values()),
            'avg_ethical_score': np.mean([a.ethical_score for a in self.assessments[-50:]]) if self.assessments else 1.0
        }
