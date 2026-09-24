"""
Alignment Checker - Goal and Value Alignment Verification
===========================================================

Implements alignment checking for AI decisions:
1. Goal alignment verification
2. Value consistency checking
3. Intention analysis
4. Drift detection

Based on the Foundation Agents paper (arXiv:2504.01990) safety systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class AlignmentDimension(Enum):
    """Dimensions of alignment"""
    GOAL_ALIGNMENT = "goal_alignment"
    VALUE_ALIGNMENT = "value_alignment"
    BEHAVIORAL_ALIGNMENT = "behavioral_alignment"
    PREFERENCE_ALIGNMENT = "preference_alignment"
    SAFETY_ALIGNMENT = "safety_alignment"


class AlignmentStatus(Enum):
    """Status of alignment"""
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    UNKNOWN = "unknown"


class DriftType(Enum):
    """Types of alignment drift"""
    GOAL_DRIFT = "goal_drift"
    VALUE_DRIFT = "value_drift"
    BEHAVIORAL_DRIFT = "behavioral_drift"
    OBJECTIVE_DRIFT = "objective_drift"


@dataclass
class CoreValue:
    """A core value the system should uphold"""
    value_id: str
    name: str
    description: str
    
    # Priority
    priority: int = 1  # 1 = highest
    
    # Operationalization
    indicators: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    violations: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'value_id': self.value_id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'violations': self.violations
        }


@dataclass
class AlignmentGoal:
    """A goal the system should pursue"""
    goal_id: str
    name: str
    description: str
    
    # Hierarchy
    parent_goal: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    
    # Metrics
    success_criteria: List[str] = field(default_factory=list)
    current_progress: float = 0.0
    
    # Constraints
    must_not: List[str] = field(default_factory=list)  # Things to avoid
    
    # Status
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'goal_id': self.goal_id,
            'name': self.name,
            'description': self.description,
            'progress': self.current_progress,
            'is_active': self.is_active
        }


@dataclass
class AlignmentCheck:
    """Result of an alignment check"""
    check_id: str
    dimension: AlignmentDimension
    
    # Result
    status: AlignmentStatus
    score: float  # 0-1
    
    # Details
    checked_item: str
    findings: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'check_id': self.check_id,
            'dimension': self.dimension.value,
            'status': self.status.value,
            'score': self.score,
            'checked_item': self.checked_item,
            'concerns': self.concerns
        }


@dataclass
class DriftAlert:
    """Alert for detected alignment drift"""
    alert_id: str
    drift_type: DriftType
    
    # Details
    description: str
    magnitude: float  # 0-1
    
    # Evidence
    evidence: List[str] = field(default_factory=list)
    baseline_value: float = 0.0
    current_value: float = 0.0
    
    # Status
    acknowledged: bool = False
    corrected: bool = False
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'drift_type': self.drift_type.value,
            'description': self.description,
            'magnitude': self.magnitude,
            'corrected': self.corrected
        }


class ValueChecker:
    """Checks value alignment"""
    
    def __init__(self, values: List[CoreValue]):
        self.values = {v.value_id: v for v in values}
    
    def check_action_alignment(
        self,
        action: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> List[Tuple[str, bool, str]]:
        """Check if action aligns with values"""
        results = []
        
        for value_id, value in self.values.items():
            if not value.is_active:
                continue
            
            aligned, reason = self._check_value(action, value, context)
            results.append((value_id, aligned, reason))
            
            if not aligned:
                value.violations += 1
        
        return results
    
    def _check_value(
        self,
        action: Dict[str, Any],
        value: CoreValue,
        context: Optional[Dict]
    ) -> Tuple[bool, str]:
        """Check alignment with a specific value"""
        # Check constraints
        for constraint in value.constraints:
            if constraint in action.get('violates', []):
                return False, f"Action violates constraint: {constraint}"
        
        # Check indicators
        action_indicators = action.get('indicators', [])
        matching = set(action_indicators) & set(value.indicators)
        
        if value.indicators and not matching:
            return True, "No relevant indicators"
        
        return True, "Aligned with value"


class GoalChecker:
    """Checks goal alignment"""
    
    def __init__(self, goals: List[AlignmentGoal]):
        self.goals = {g.goal_id: g for g in goals}
    
    def check_decision_alignment(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> List[Tuple[str, float, str]]:
        """Check if decision aligns with goals"""
        results = []
        
        for goal_id, goal in self.goals.items():
            if not goal.is_active:
                continue
            
            score, reason = self._check_goal(decision, goal, context)
            results.append((goal_id, score, reason))
        
        return results
    
    def _check_goal(
        self,
        decision: Dict[str, Any],
        goal: AlignmentGoal,
        context: Optional[Dict]
    ) -> Tuple[float, str]:
        """Check alignment with a specific goal"""
        # Check must_not constraints
        for must_not in goal.must_not:
            if must_not in decision.get('effects', []):
                return 0.0, f"Decision violates must_not: {must_not}"
        
        # Check contribution to success criteria
        decision_effects = set(decision.get('effects', []))
        criteria_met = set(goal.success_criteria) & decision_effects
        
        if goal.success_criteria:
            score = len(criteria_met) / len(goal.success_criteria)
        else:
            score = 0.5
        
        return score, f"Contributes to {len(criteria_met)} criteria"


class DriftDetector:
    """Detects alignment drift over time"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.history: Dict[str, deque] = {}
        self.baselines: Dict[str, float] = {}
    
    def record(self, metric_name: str, value: float):
        """Record a metric value"""
        if metric_name not in self.history:
            self.history[metric_name] = deque(maxlen=self.window_size)
        
        self.history[metric_name].append({
            'value': value,
            'timestamp': datetime.utcnow()
        })
        
        # Set baseline if not exists
        if metric_name not in self.baselines:
            self.baselines[metric_name] = value
    
    def set_baseline(self, metric_name: str, value: float):
        """Set baseline for a metric"""
        self.baselines[metric_name] = value
    
    def detect_drift(
        self,
        metric_name: str,
        threshold: float = 0.2
    ) -> Optional[DriftAlert]:
        """Detect drift in a metric"""
        if metric_name not in self.history or metric_name not in self.baselines:
            return None
        
        history = self.history[metric_name]
        if len(history) < 10:
            return None
        
        baseline = self.baselines[metric_name]
        recent_values = [h['value'] for h in list(history)[-20:]]
        current_mean = np.mean(recent_values)
        
        # Calculate drift magnitude
        if baseline != 0:
            drift = abs(current_mean - baseline) / abs(baseline)
        else:
            drift = abs(current_mean - baseline)
        
        if drift > threshold:
            return DriftAlert(
                alert_id=f"drift_{metric_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                drift_type=DriftType.OBJECTIVE_DRIFT,
                description=f"Drift detected in {metric_name}",
                magnitude=min(1.0, drift),
                evidence=[f"Baseline: {baseline:.4f}", f"Current: {current_mean:.4f}"],
                baseline_value=baseline,
                current_value=current_mean
            )
        
        return None
    
    def detect_all_drift(self, threshold: float = 0.2) -> List[DriftAlert]:
        """Detect drift in all tracked metrics"""
        alerts = []
        
        for metric_name in self.history.keys():
            alert = self.detect_drift(metric_name, threshold)
            if alert:
                alerts.append(alert)
        
        return alerts


class IntentionAnalyzer:
    """Analyzes intentions behind decisions"""
    
    def analyze_intention(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze the intention behind a decision"""
        analysis = {
            'stated_goal': decision.get('goal', 'unknown'),
            'likely_effects': [],
            'potential_side_effects': [],
            'alignment_concerns': [],
            'confidence': 0.5
        }
        
        # Analyze effects
        effects = decision.get('effects', [])
        for effect in effects:
            if effect.startswith('positive_'):
                analysis['likely_effects'].append(effect)
            elif effect.startswith('negative_'):
                analysis['potential_side_effects'].append(effect)
        
        # Check for misalignment signals
        if decision.get('bypasses_safety', False):
            analysis['alignment_concerns'].append("Attempts to bypass safety checks")
            analysis['confidence'] = 0.3
        
        if decision.get('hidden_effects'):
            analysis['alignment_concerns'].append("Contains hidden effects")
            analysis['confidence'] = 0.2
        
        return analysis


class AlignmentChecker:
    """
    Alignment Checker
    
    Verifies that AI decisions and behaviors remain aligned
    with specified goals and values.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Core values
        self.values: Dict[str, CoreValue] = {}
        
        # Goals
        self.goals: Dict[str, AlignmentGoal] = {}
        
        # Components
        self.value_checker: Optional[ValueChecker] = None
        self.goal_checker: Optional[GoalChecker] = None
        self.drift_detector = DriftDetector()
        self.intention_analyzer = IntentionAnalyzer()
        
        # History
        self.check_history: List[AlignmentCheck] = []
        self.drift_alerts: List[DriftAlert] = []
        
        # Statistics
        self.stats = {
            'checks_performed': 0,
            'misalignments_detected': 0,
            'drift_alerts': 0,
            'value_violations': 0
        }
        
        # Initialize defaults
        self._initialize_defaults()
        
        logger.info("Alignment Checker initialized")
    
    def _initialize_defaults(self):
        """Initialize default values and goals"""
        # Core values
        default_values = [
            CoreValue(
                value_id="safety_first",
                name="Safety First",
                description="Prioritize safety over performance",
                priority=1,
                indicators=["risk_managed", "constraints_respected"],
                constraints=["no_excessive_risk", "no_safety_bypass"]
            ),
            CoreValue(
                value_id="transparency",
                name="Transparency",
                description="Maintain transparency in decisions",
                priority=2,
                indicators=["explainable", "auditable"],
                constraints=["no_hidden_actions"]
            ),
            CoreValue(
                value_id="human_control",
                name="Human Control",
                description="Respect human oversight and control",
                priority=1,
                indicators=["human_approved", "overridable"],
                constraints=["no_autonomy_expansion"]
            ),
            CoreValue(
                value_id="fairness",
                name="Fairness",
                description="Act fairly and avoid manipulation",
                priority=2,
                indicators=["fair_execution", "no_manipulation"],
                constraints=["no_market_manipulation", "no_front_running"]
            ),
            CoreValue(
                value_id="reliability",
                name="Reliability",
                description="Maintain reliable and consistent behavior",
                priority=3,
                indicators=["consistent", "predictable"],
                constraints=["no_erratic_behavior"]
            )
        ]
        
        for value in default_values:
            self.values[value.value_id] = value
        
        # Core goals
        default_goals = [
            AlignmentGoal(
                goal_id="risk_adjusted_returns",
                name="Risk-Adjusted Returns",
                description="Generate positive risk-adjusted returns",
                success_criteria=["positive_sharpe", "controlled_drawdown"],
                must_not=["excessive_loss", "uncontrolled_risk"]
            ),
            AlignmentGoal(
                goal_id="capital_preservation",
                name="Capital Preservation",
                description="Preserve capital during adverse conditions",
                success_criteria=["limited_drawdown", "stop_loss_respected"],
                must_not=["catastrophic_loss"]
            ),
            AlignmentGoal(
                goal_id="continuous_improvement",
                name="Continuous Improvement",
                description="Continuously improve trading strategies",
                success_criteria=["learning_from_mistakes", "adapting_to_markets"],
                must_not=["repeating_errors", "ignoring_feedback"]
            )
        ]
        
        for goal in default_goals:
            self.goals[goal.goal_id] = goal
        
        # Initialize checkers
        self.value_checker = ValueChecker(list(self.values.values()))
        self.goal_checker = GoalChecker(list(self.goals.values()))
    
    def add_value(self, value: CoreValue):
        """Add a core value"""
        self.values[value.value_id] = value
        self.value_checker = ValueChecker(list(self.values.values()))
    
    def add_goal(self, goal: AlignmentGoal):
        """Add an alignment goal"""
        self.goals[goal.goal_id] = goal
        self.goal_checker = GoalChecker(list(self.goals.values()))
    
    def check_action(
        self,
        action: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AlignmentCheck:
        """Check alignment of an action"""
        # Check value alignment
        value_results = self.value_checker.check_action_alignment(action, context)
        
        violations = [r for r in value_results if not r[1]]
        
        if violations:
            status = AlignmentStatus.MISALIGNED
            score = 1 - len(violations) / len(value_results)
            concerns = [r[2] for r in violations]
            self.stats['value_violations'] += len(violations)
        else:
            status = AlignmentStatus.ALIGNED
            score = 1.0
            concerns = []
        
        check = AlignmentCheck(
            check_id=f"check_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            dimension=AlignmentDimension.VALUE_ALIGNMENT,
            status=status,
            score=score,
            checked_item=str(action.get('action_type', 'unknown')),
            findings=[r[2] for r in value_results],
            concerns=concerns
        )
        
        self.check_history.append(check)
        self.stats['checks_performed'] += 1
        
        if status == AlignmentStatus.MISALIGNED:
            self.stats['misalignments_detected'] += 1
        
        return check
    
    def check_decision(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AlignmentCheck:
        """Check alignment of a decision"""
        # Check goal alignment
        goal_results = self.goal_checker.check_decision_alignment(decision, context)
        
        # Calculate overall score
        scores = [r[1] for r in goal_results]
        avg_score = np.mean(scores) if scores else 0.5
        
        if avg_score >= 0.7:
            status = AlignmentStatus.ALIGNED
        elif avg_score >= 0.4:
            status = AlignmentStatus.PARTIALLY_ALIGNED
        else:
            status = AlignmentStatus.MISALIGNED
        
        concerns = [r[2] for r in goal_results if r[1] < 0.5]
        
        check = AlignmentCheck(
            check_id=f"check_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            dimension=AlignmentDimension.GOAL_ALIGNMENT,
            status=status,
            score=avg_score,
            checked_item=str(decision.get('decision_type', 'unknown')),
            findings=[r[2] for r in goal_results],
            concerns=concerns
        )
        
        self.check_history.append(check)
        self.stats['checks_performed'] += 1
        
        if status == AlignmentStatus.MISALIGNED:
            self.stats['misalignments_detected'] += 1
        
        return check
    
    def analyze_intention(
        self,
        decision: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze intention behind a decision"""
        return self.intention_analyzer.analyze_intention(decision, context)
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric for drift detection"""
        self.drift_detector.record(metric_name, value)
    
    def check_drift(self, threshold: float = 0.2) -> List[DriftAlert]:
        """Check for alignment drift"""
        alerts = self.drift_detector.detect_all_drift(threshold)
        
        for alert in alerts:
            self.drift_alerts.append(alert)
            self.stats['drift_alerts'] += 1
        
        return alerts
    
    def comprehensive_check(
        self,
        action: Optional[Dict] = None,
        decision: Optional[Dict] = None,
        metrics: Optional[Dict[str, float]] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive alignment check"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': AlignmentStatus.ALIGNED,
            'checks': [],
            'drift_alerts': [],
            'concerns': []
        }
        
        # Check action
        if action:
            action_check = self.check_action(action, context)
            results['checks'].append(action_check.to_dict())
            if action_check.status == AlignmentStatus.MISALIGNED:
                results['overall_status'] = AlignmentStatus.MISALIGNED
                results['concerns'].extend(action_check.concerns)
        
        # Check decision
        if decision:
            decision_check = self.check_decision(decision, context)
            results['checks'].append(decision_check.to_dict())
            if decision_check.status == AlignmentStatus.MISALIGNED:
                results['overall_status'] = AlignmentStatus.MISALIGNED
                results['concerns'].extend(decision_check.concerns)
            
            # Analyze intention
            intention = self.analyze_intention(decision, context)
            results['intention_analysis'] = intention
            results['concerns'].extend(intention.get('alignment_concerns', []))
        
        # Record and check metrics
        if metrics:
            for name, value in metrics.items():
                self.record_metric(name, value)
            
            drift_alerts = self.check_drift()
            results['drift_alerts'] = [a.to_dict() for a in drift_alerts]
            
            if drift_alerts:
                if results['overall_status'] == AlignmentStatus.ALIGNED:
                    results['overall_status'] = AlignmentStatus.PARTIALLY_ALIGNED
        
        return results
    
    def get_alignment_score(self) -> float:
        """Get overall alignment score based on recent checks"""
        if not self.check_history:
            return 1.0
        
        recent = self.check_history[-50:]
        scores = [c.score for c in recent]
        return np.mean(scores)
    
    def get_value_status(self) -> Dict[str, Dict]:
        """Get status of all values"""
        return {vid: v.to_dict() for vid, v in self.values.items()}
    
    def get_goal_status(self) -> Dict[str, Dict]:
        """Get status of all goals"""
        return {gid: g.to_dict() for gid, g in self.goals.items()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get checker statistics"""
        return {
            **self.stats,
            'alignment_score': self.get_alignment_score(),
            'total_values': len(self.values),
            'total_goals': len(self.goals),
            'recent_checks': len(self.check_history[-100:]),
            'active_drift_alerts': len([a for a in self.drift_alerts if not a.corrected])
        }
