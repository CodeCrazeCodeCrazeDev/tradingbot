"""
Feature Flag Framework

Allows toggling any new feature on/off for a percentage of trades or in
specific market conditions without deploying new code.

Features:
- Dynamic feature toggling
- Percentage-based rollout
- Market condition-based activation
- A/B testing support
- Real-time configuration updates
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import numpy as np
from collections import deque
import json
import hashlib

logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Feature flag status"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    PERCENTAGE = "percentage"
    CONDITIONAL = "conditional"
    AB_TEST = "ab_test"


class RolloutStage(Enum):
    """Feature rollout stages"""
    DEVELOPMENT = "development"
    ALPHA = "alpha"
    BETA = "beta"
    CANARY = "canary"
    GENERAL_AVAILABILITY = "general_availability"


@dataclass
class FeatureCondition:
    """Condition for feature activation"""
    condition_type: str  # 'volatility', 'regime', 'time', 'symbol', 'custom'
    operator: str  # 'gt', 'lt', 'eq', 'in', 'not_in'
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        actual = context.get(self.condition_type)
        
        if actual is None:
            return False
        
        if self.operator == 'gt':
            return actual > self.value
        elif self.operator == 'lt':
            return actual < self.value
        elif self.operator == 'eq':
            return actual == self.value
        elif self.operator == 'in':
            return actual in self.value
        elif self.operator == 'not_in':
            return actual not in self.value
        elif self.operator == 'between':
            return self.value[0] <= actual <= self.value[1]
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'condition_type': self.condition_type,
            'operator': self.operator,
            'value': self.value
        }


@dataclass
class FeatureFlag:
    """Single feature flag"""
    name: str
    description: str
    status: FeatureStatus
    percentage: float = 100.0  # Rollout percentage
    conditions: List[FeatureCondition] = field(default_factory=list)
    rollout_stage: RolloutStage = RolloutStage.DEVELOPMENT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    ab_test_group: Optional[str] = None
    
    # Metrics
    evaluations: int = 0
    activations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'percentage': self.percentage,
            'conditions': [c.to_dict() for c in self.conditions],
            'rollout_stage': self.rollout_stage.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'owner': self.owner,
            'tags': self.tags,
            'evaluations': self.evaluations,
            'activations': self.activations,
            'activation_rate': self.activations / self.evaluations if self.evaluations > 0 else 0
        }


@dataclass
class ABTestResult:
    """A/B test result"""
    test_name: str
    group_a_name: str
    group_b_name: str
    group_a_trades: int
    group_b_trades: int
    group_a_pnl: float
    group_b_pnl: float
    group_a_win_rate: float
    group_b_win_rate: float
    statistical_significance: float
    winner: str
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'test_name': self.test_name,
            'group_a': {
                'name': self.group_a_name,
                'trades': self.group_a_trades,
                'pnl': self.group_a_pnl,
                'win_rate': self.group_a_win_rate
            },
            'group_b': {
                'name': self.group_b_name,
                'trades': self.group_b_trades,
                'pnl': self.group_b_pnl,
                'win_rate': self.group_b_win_rate
            },
            'statistical_significance': self.statistical_significance,
            'winner': self.winner,
            'recommendation': self.recommendation
        }


class FeatureFlagFramework:
    """
    Feature Flag Framework
    
    Enables safe, gradual rollout of new features with
    real-time control and A/B testing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Feature flags
        self.flags: Dict[str, FeatureFlag] = {}
        
        # A/B test tracking
        self.ab_tests: Dict[str, Dict[str, List[Dict]]] = {}
        
        # Evaluation history
        self.evaluation_history: deque = deque(maxlen=10000)
        
        # User/trade assignments for consistent bucketing
        self.assignments: Dict[str, str] = {}
        
        # Callbacks for feature changes
        self.change_callbacks: List[Callable] = []
        
        logger.info("FeatureFlagFramework initialized")
    
    def create_flag(
        self,
        name: str,
        description: str,
        status: FeatureStatus = FeatureStatus.DISABLED,
        percentage: float = 100.0,
        conditions: Optional[List[Dict[str, Any]]] = None,
        rollout_stage: RolloutStage = RolloutStage.DEVELOPMENT,
        owner: str = "",
        tags: Optional[List[str]] = None
    ) -> FeatureFlag:
        """Create a new feature flag"""
        # Parse conditions
        parsed_conditions = []
        if conditions:
            for cond in conditions:
                parsed_conditions.append(FeatureCondition(
                    condition_type=cond['type'],
                    operator=cond['operator'],
                    value=cond['value']
                ))
        
        flag = FeatureFlag(
            name=name,
            description=description,
            status=status,
            percentage=percentage,
            conditions=parsed_conditions,
            rollout_stage=rollout_stage,
            owner=owner,
            tags=tags or []
        )
        
        self.flags[name] = flag
        
        logger.info(f"Created feature flag: {name} ({status.value})")
        
        return flag
    
    def is_enabled(
        self,
        flag_name: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            flag_name: Name of the feature flag
            context: Context for conditional evaluation
            user_id: User/trade ID for consistent bucketing
        """
        flag = self.flags.get(flag_name)
        
        if not flag:
            return False
        
        flag.evaluations += 1
        context = context or {}
        
        # Check status
        if flag.status == FeatureStatus.DISABLED:
            return False
        
        if flag.status == FeatureStatus.ENABLED:
            flag.activations += 1
            return True
        
        if flag.status == FeatureStatus.PERCENTAGE:
            # Consistent bucketing based on user_id
            if user_id:
                bucket = self._get_bucket(flag_name, user_id)
            else:
                bucket = np.random.random() * 100
            
            enabled = bucket < flag.percentage
            if enabled:
                flag.activations += 1
            return enabled
        
        if flag.status == FeatureStatus.CONDITIONAL:
            # All conditions must be met
            if not flag.conditions:
                return False
            
            all_met = all(cond.evaluate(context) for cond in flag.conditions)
            if all_met:
                flag.activations += 1
            return all_met
        
        if flag.status == FeatureStatus.AB_TEST:
            # Assign to test group
            group = self._get_ab_group(flag_name, user_id or str(np.random.random()))
            enabled = group == 'B'  # Group B gets the new feature
            if enabled:
                flag.activations += 1
            return enabled
        
        return False
    
    def _get_bucket(self, flag_name: str, user_id: str) -> float:
        """Get consistent bucket for user"""
        key = f"{flag_name}:{user_id}"
        
        if key in self.assignments:
            return float(self.assignments[key])
        
        # Hash-based bucketing for consistency
        hash_val = hashlib.md5(key.encode()).hexdigest()
        bucket = int(hash_val[:8], 16) / 0xFFFFFFFF * 100
        
        self.assignments[key] = str(bucket)
        
        return bucket
    
    def _get_ab_group(self, flag_name: str, user_id: str) -> str:
        """Get A/B test group for user"""
        bucket = self._get_bucket(flag_name, user_id)
        return 'A' if bucket < 50 else 'B'
    
    def update_flag(
        self,
        flag_name: str,
        status: Optional[FeatureStatus] = None,
        percentage: Optional[float] = None,
        conditions: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[FeatureFlag]:
        """Update a feature flag"""
        flag = self.flags.get(flag_name)
        
        if not flag:
            return None
        
        if status is not None:
            flag.status = status
        
        if percentage is not None:
            flag.percentage = percentage
        
        if conditions is not None:
            flag.conditions = [
                FeatureCondition(
                    condition_type=c['type'],
                    operator=c['operator'],
                    value=c['value']
                )
                for c in conditions
            ]
        
        flag.updated_at = datetime.now()
        
        # Notify callbacks
        for callback in self.change_callbacks:
            try:
                callback(flag_name, flag)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"Updated feature flag: {flag_name}")
        
        return flag
    
    def gradual_rollout(
        self,
        flag_name: str,
        target_percentage: float,
        steps: int = 5,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Plan gradual rollout of a feature
        
        Returns schedule of percentage increases
        """
        flag = self.flags.get(flag_name)
        
        if not flag:
            return []
        
        current = flag.percentage if flag.status == FeatureStatus.PERCENTAGE else 0
        step_size = (target_percentage - current) / steps
        
        schedule = []
        for i in range(steps):
            new_pct = current + step_size * (i + 1)
            schedule.append({
                'step': i + 1,
                'percentage': new_pct,
                'scheduled_time': datetime.now() + timedelta(minutes=interval_minutes * (i + 1)),
                'status': 'pending'
            })
        
        return schedule
    
    def start_ab_test(
        self,
        flag_name: str,
        test_name: str,
        group_a_name: str = "Control",
        group_b_name: str = "Treatment"
    ):
        """Start an A/B test for a feature"""
        flag = self.flags.get(flag_name)
        
        if not flag:
            return
        
        flag.status = FeatureStatus.AB_TEST
        flag.ab_test_group = test_name
        
        self.ab_tests[test_name] = {
            'flag_name': flag_name,
            'group_a_name': group_a_name,
            'group_b_name': group_b_name,
            'group_a_results': [],
            'group_b_results': []
        }
        
        logger.info(f"Started A/B test: {test_name} for {flag_name}")
    
    def record_ab_result(
        self,
        test_name: str,
        user_id: str,
        pnl: float,
        won: bool
    ):
        """Record result for A/B test"""
        if test_name not in self.ab_tests:
            return
        
        test = self.ab_tests[test_name]
        flag_name = test['flag_name']
        
        group = self._get_ab_group(flag_name, user_id)
        
        result = {
            'user_id': user_id,
            'pnl': pnl,
            'won': won,
            'timestamp': datetime.now()
        }
        
        if group == 'A':
            test['group_a_results'].append(result)
        else:
            test['group_b_results'].append(result)
    
    def analyze_ab_test(self, test_name: str) -> Optional[ABTestResult]:
        """Analyze A/B test results"""
        if test_name not in self.ab_tests:
            return None
        
        test = self.ab_tests[test_name]
        
        group_a = test['group_a_results']
        group_b = test['group_b_results']
        
        if not group_a or not group_b:
            return None
        
        # Calculate metrics
        a_trades = len(group_a)
        b_trades = len(group_b)
        
        a_pnl = sum(r['pnl'] for r in group_a)
        b_pnl = sum(r['pnl'] for r in group_b)
        
        a_wins = sum(1 for r in group_a if r['won'])
        b_wins = sum(1 for r in group_b if r['won'])
        
        a_win_rate = a_wins / a_trades if a_trades > 0 else 0
        b_win_rate = b_wins / b_trades if b_trades > 0 else 0
        
        # Statistical significance (simplified z-test)
        if a_trades > 10 and b_trades > 10:
            pooled_rate = (a_wins + b_wins) / (a_trades + b_trades)
            se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/a_trades + 1/b_trades))
            if se > 0:
                z = abs(a_win_rate - b_win_rate) / se
                significance = min(0.99, z / 3)  # Rough approximation
            else:
                significance = 0
        else:
            significance = 0
        
        # Determine winner
        if b_pnl > a_pnl * 1.1 and significance > 0.8:
            winner = test['group_b_name']
            recommendation = f"DEPLOY {test['group_b_name']} - Significant improvement"
        elif a_pnl > b_pnl * 1.1 and significance > 0.8:
            winner = test['group_a_name']
            recommendation = f"KEEP {test['group_a_name']} - Control is better"
        else:
            winner = "Inconclusive"
            recommendation = "Continue testing - Need more data"
        
        return ABTestResult(
            test_name=test_name,
            group_a_name=test['group_a_name'],
            group_b_name=test['group_b_name'],
            group_a_trades=a_trades,
            group_b_trades=b_trades,
            group_a_pnl=a_pnl,
            group_b_pnl=b_pnl,
            group_a_win_rate=a_win_rate,
            group_b_win_rate=b_win_rate,
            statistical_significance=significance,
            winner=winner,
            recommendation=recommendation
        )
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags"""
        return {name: flag.to_dict() for name, flag in self.flags.items()}
    
    def get_enabled_flags(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get list of enabled flags for context"""
        enabled = []
        for name in self.flags:
            if self.is_enabled(name, context):
                enabled.append(name)
        return enabled
    
    def export_config(self) -> str:
        """Export configuration as JSON"""
        config = {
            'flags': {name: flag.to_dict() for name, flag in self.flags.items()},
            'ab_tests': {
                name: {
                    'flag_name': test['flag_name'],
                    'group_a_name': test['group_a_name'],
                    'group_b_name': test['group_b_name'],
                    'group_a_count': len(test['group_a_results']),
                    'group_b_count': len(test['group_b_results'])
                }
                for name, test in self.ab_tests.items()
            }
        }
        return json.dumps(config, indent=2, default=str)
    
    def on_change(self, callback: Callable):
        """Register callback for flag changes"""
        self.change_callbacks.append(callback)


# Factory function
def create_feature_flags(config: Optional[Dict[str, Any]] = None) -> FeatureFlagFramework:
    """Create feature flag framework"""
    return FeatureFlagFramework(config)
