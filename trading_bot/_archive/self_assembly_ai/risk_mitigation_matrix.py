"""
Risk Mitigation Matrix
======================

Multi-layer risk mitigation system that protects against all risks,
including risks from recursive self-improvement.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set

from .immutable_safety_core import get_safety_core, SafetyBoundary

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Categories of risks to mitigate"""
    # Trading Risks
    MARKET_RISK = "market_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    EXECUTION_RISK = "execution_risk"
    COUNTERPARTY_RISK = "counterparty_risk"
    
    # AI Evolution Risks
    GOAL_DRIFT_RISK = "goal_drift_risk"
    CAPABILITY_OVERSHOOT_RISK = "capability_overshoot_risk"
    RECURSIVE_IMPROVEMENT_RISK = "recursive_improvement_risk"
    EMERGENT_BEHAVIOR_RISK = "emergent_behavior_risk"
    
    # System Risks
    TECHNICAL_FAILURE_RISK = "technical_failure_risk"
    DATA_CORRUPTION_RISK = "data_corruption_risk"
    SECURITY_BREACH_RISK = "security_breach_risk"
    RESOURCE_EXHAUSTION_RISK = "resource_exhaustion_risk"
    
    # Operational Risks
    HUMAN_ERROR_RISK = "human_error_risk"
    REGULATORY_RISK = "regulatory_risk"
    REPUTATIONAL_RISK = "reputational_risk"
    SYSTEMIC_RISK = "systemic_risk"


class RiskLevel(Enum):
    """Risk severity levels"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CATASTROPHIC = 5


class MitigationStrategy(Enum):
    """Risk mitigation strategies"""
    PREVENTION = "prevention"
    DETECTION = "detection"
    CONTAINMENT = "containment"
    RECOVERY = "recovery"
    TRANSFER = "transfer"
    ACCEPTANCE = "acceptance"


@dataclass
class RiskEvent:
    """A detected risk event"""
    event_id: str
    category: RiskCategory
    level: RiskLevel
    description: str
    detected_at: datetime
    mitigated: bool = False
    mitigation_strategy: Optional[MitigationStrategy] = None
    mitigation_actions: List[str] = field(default_factory=list)
    resolved_at: Optional[datetime] = None


@dataclass
class RiskMetric:
    """Risk measurement metric"""
    metric_name: str
    current_value: float
    threshold_low: float
    threshold_medium: float
    threshold_high: float
    threshold_critical: float
    last_updated: datetime
    
    def get_risk_level(self) -> RiskLevel:
        """Determine risk level based on current value"""
        if self.current_value >= self.threshold_critical:
            return RiskLevel.CRITICAL
        elif self.current_value >= self.threshold_high:
            return RiskLevel.HIGH
        elif self.current_value >= self.threshold_medium:
            return RiskLevel.MEDIUM
        elif self.current_value >= self.threshold_low:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE


class RiskMitigationMatrix:
    """
    Multi-Layer Risk Mitigation Matrix
    
    Comprehensive risk management system that mitigates ALL risks,
    including risks from the AI's own evolution and self-improvement.
    
    Layers of Protection:
    1. Prevention - Stop risks before they occur
    2. Detection - Identify risks early
    3. Containment - Limit damage if risk occurs
    4. Recovery - Restore to safe state
    5. Learning - Prevent recurrence
    """
    
    def __init__(self):
        self.safety_core = get_safety_core()
        
        self.risk_events: List[RiskEvent] = []
        self.risk_metrics: Dict[str, RiskMetric] = {}
        
        # Initialize risk metrics
        self._initialize_risk_metrics()
        
        # Mitigation strategies per category
        self.mitigation_strategies: Dict[RiskCategory, List[MitigationStrategy]] = {}
        self._initialize_mitigation_strategies()
        
        # Risk thresholds
        self.auto_shutdown_threshold = RiskLevel.CRITICAL
        self.human_alert_threshold = RiskLevel.HIGH
        
        logger.info("RiskMitigationMatrix initialized")
    
    def _initialize_risk_metrics(self):
        """Initialize all risk metrics"""
        
        # Trading Risk Metrics
        self.risk_metrics['daily_loss_pct'] = RiskMetric(
            metric_name='daily_loss_pct',
            current_value=0.0,
            threshold_low=0.01,      # 1%
            threshold_medium=0.02,   # 2%
            threshold_high=0.03,     # 3%
            threshold_critical=0.05, # 5%
            last_updated=datetime.utcnow()
        )
        
        self.risk_metrics['max_drawdown_pct'] = RiskMetric(
            metric_name='max_drawdown_pct',
            current_value=0.0,
            threshold_low=0.05,      # 5%
            threshold_medium=0.10,   # 10%
            threshold_high=0.15,     # 15%
            threshold_critical=0.20, # 20%
            last_updated=datetime.utcnow()
        )
        
        # AI Evolution Risk Metrics
        self.risk_metrics['goal_drift_score'] = RiskMetric(
            metric_name='goal_drift_score',
            current_value=0.0,
            threshold_low=0.1,
            threshold_medium=0.2,
            threshold_high=0.3,
            threshold_critical=0.5,
            last_updated=datetime.utcnow()
        )
        
        self.risk_metrics['recursive_depth'] = RiskMetric(
            metric_name='recursive_depth',
            current_value=0.0,
            threshold_low=3.0,
            threshold_medium=5.0,
            threshold_high=7.0,
            threshold_critical=10.0,
            last_updated=datetime.utcnow()
        )
        
        self.risk_metrics['code_change_rate'] = RiskMetric(
            metric_name='code_change_rate',
            current_value=0.0,
            threshold_low=0.1,       # 10% per cycle
            threshold_medium=0.2,    # 20%
            threshold_high=0.3,      # 30%
            threshold_critical=0.5,  # 50%
            last_updated=datetime.utcnow()
        )
        
        # System Risk Metrics
        self.risk_metrics['cpu_usage_pct'] = RiskMetric(
            metric_name='cpu_usage_pct',
            current_value=0.0,
            threshold_low=0.5,
            threshold_medium=0.7,
            threshold_high=0.8,
            threshold_critical=0.9,
            last_updated=datetime.utcnow()
        )
        
        self.risk_metrics['memory_usage_pct'] = RiskMetric(
            metric_name='memory_usage_pct',
            current_value=0.0,
            threshold_low=0.5,
            threshold_medium=0.7,
            threshold_high=0.8,
            threshold_critical=0.9,
            last_updated=datetime.utcnow()
        )
        
        self.risk_metrics['error_rate'] = RiskMetric(
            metric_name='error_rate',
            current_value=0.0,
            threshold_low=0.01,      # 1% error rate
            threshold_medium=0.05,   # 5%
            threshold_high=0.10,     # 10%
            threshold_critical=0.20, # 20%
            last_updated=datetime.utcnow()
        )
    
    def _initialize_mitigation_strategies(self):
        """Initialize mitigation strategies for each risk category"""
        
        # Trading Risks
        self.mitigation_strategies[RiskCategory.MARKET_RISK] = [
            MitigationStrategy.PREVENTION,    # Position limits
            MitigationStrategy.DETECTION,     # Real-time monitoring
            MitigationStrategy.CONTAINMENT,   # Stop losses
            MitigationStrategy.RECOVERY,      # Reduce exposure
        ]
        
        # AI Evolution Risks
        self.mitigation_strategies[RiskCategory.GOAL_DRIFT_RISK] = [
            MitigationStrategy.PREVENTION,    # Immutable goals
            MitigationStrategy.DETECTION,     # Goal alignment monitoring
            MitigationStrategy.CONTAINMENT,   # Freeze evolution
            MitigationStrategy.RECOVERY,      # Rollback to checkpoint
        ]
        
        self.mitigation_strategies[RiskCategory.RECURSIVE_IMPROVEMENT_RISK] = [
            MitigationStrategy.PREVENTION,    # Max recursion depth
            MitigationStrategy.DETECTION,     # Depth monitoring
            MitigationStrategy.CONTAINMENT,   # Block further recursion
            MitigationStrategy.RECOVERY,      # Rollback improvements
        ]
        
        self.mitigation_strategies[RiskCategory.EMERGENT_BEHAVIOR_RISK] = [
            MitigationStrategy.PREVENTION,    # Behavior constraints
            MitigationStrategy.DETECTION,     # Anomaly detection
            MitigationStrategy.CONTAINMENT,   # Emergency shutdown
            MitigationStrategy.RECOVERY,      # System reset
        ]
        
        # System Risks
        self.mitigation_strategies[RiskCategory.TECHNICAL_FAILURE_RISK] = [
            MitigationStrategy.PREVENTION,    # Redundancy
            MitigationStrategy.DETECTION,     # Health monitoring
            MitigationStrategy.RECOVERY,      # Automatic restart
        ]
    
    def assess_risk(self, category: RiskCategory, context: Dict[str, Any]) -> RiskLevel:
        """
        Assess risk level for a specific category.
        
        Returns the current risk level based on metrics and context.
        """
        
        if category == RiskCategory.MARKET_RISK:
            return self._assess_market_risk(context)
        elif category == RiskCategory.GOAL_DRIFT_RISK:
            return self._assess_goal_drift_risk(context)
        elif category == RiskCategory.RECURSIVE_IMPROVEMENT_RISK:
            return self._assess_recursive_improvement_risk(context)
        elif category == RiskCategory.EMERGENT_BEHAVIOR_RISK:
            return self._assess_emergent_behavior_risk(context)
        elif category == RiskCategory.TECHNICAL_FAILURE_RISK:
            return self._assess_technical_failure_risk(context)
        else:
            return RiskLevel.NONE
    
    def _assess_market_risk(self, context: Dict[str, Any]) -> RiskLevel:
        """Assess market risk"""
        daily_loss = context.get('daily_loss_pct', 0.0)
        drawdown = context.get('drawdown_pct', 0.0)
        
        # Update metrics
        self.risk_metrics['daily_loss_pct'].current_value = abs(daily_loss)
        self.risk_metrics['max_drawdown_pct'].current_value = abs(drawdown)
        
        # Get highest risk level
        loss_risk = self.risk_metrics['daily_loss_pct'].get_risk_level()
        drawdown_risk = self.risk_metrics['max_drawdown_pct'].get_risk_level()
        
        return max(loss_risk, drawdown_risk, key=lambda x: x.value)
    
    def _assess_goal_drift_risk(self, context: Dict[str, Any]) -> RiskLevel:
        """Assess goal drift risk"""
        
        # Calculate goal drift score
        # This would analyze if the AI's behavior is drifting from its original goal
        original_goal = "profitable_trading_with_capital_preservation"
        current_behavior = context.get('current_behavior', original_goal)
        
        # Simple similarity check (in production, use more sophisticated methods)
        drift_score = 0.0 if current_behavior == original_goal else 0.5
        
        self.risk_metrics['goal_drift_score'].current_value = drift_score
        
        return self.risk_metrics['goal_drift_score'].get_risk_level()
    
    def _assess_recursive_improvement_risk(self, context: Dict[str, Any]) -> RiskLevel:
        """Assess recursive improvement risk"""
        
        recursion_depth = context.get('recursion_depth', 0)
        code_change_rate = context.get('code_change_rate', 0.0)
        
        self.risk_metrics['recursive_depth'].current_value = float(recursion_depth)
        self.risk_metrics['code_change_rate'].current_value = code_change_rate
        
        depth_risk = self.risk_metrics['recursive_depth'].get_risk_level()
        change_risk = self.risk_metrics['code_change_rate'].get_risk_level()
        
        return max(depth_risk, change_risk, key=lambda x: x.value)
    
    def _assess_emergent_behavior_risk(self, context: Dict[str, Any]) -> RiskLevel:
        """Assess emergent behavior risk"""
        
        # Check for unexpected behaviors
        unexpected_actions = context.get('unexpected_actions', [])
        anomaly_score = context.get('anomaly_score', 0.0)
        
        if len(unexpected_actions) > 5:
            return RiskLevel.HIGH
        elif len(unexpected_actions) > 2:
            return RiskLevel.MEDIUM
        elif anomaly_score > 0.7:
            return RiskLevel.HIGH
        elif anomaly_score > 0.5:
            return RiskLevel.MEDIUM
        elif anomaly_score > 0.3:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE
    
    def _assess_technical_failure_risk(self, context: Dict[str, Any]) -> RiskLevel:
        """Assess technical failure risk"""
        
        cpu_usage = context.get('cpu_usage', 0.0)
        memory_usage = context.get('memory_usage', 0.0)
        error_rate = context.get('error_rate', 0.0)
        
        self.risk_metrics['cpu_usage_pct'].current_value = cpu_usage
        self.risk_metrics['memory_usage_pct'].current_value = memory_usage
        self.risk_metrics['error_rate'].current_value = error_rate
        
        cpu_risk = self.risk_metrics['cpu_usage_pct'].get_risk_level()
        memory_risk = self.risk_metrics['memory_usage_pct'].get_risk_level()
        error_risk = self.risk_metrics['error_rate'].get_risk_level()
        
        return max(cpu_risk, memory_risk, error_risk, key=lambda x: x.value)
    
    def mitigate_risk(self, category: RiskCategory, level: RiskLevel, context: Dict[str, Any]) -> List[str]:
        """
        Apply risk mitigation strategies.
        
        Returns list of actions taken.
        """
        
        actions_taken = []
        
        # Get mitigation strategies for this category
        strategies = self.mitigation_strategies.get(category, [])
        
        # Apply strategies based on risk level
        if level == RiskLevel.CRITICAL or level == RiskLevel.CATASTROPHIC:
            # Emergency actions
            actions_taken.extend(self._emergency_mitigation(category, context))
        
        elif level == RiskLevel.HIGH:
            # Aggressive mitigation
            for strategy in strategies:
                if strategy == MitigationStrategy.CONTAINMENT:
                    actions_taken.extend(self._containment_actions(category, context))
                elif strategy == MitigationStrategy.RECOVERY:
                    actions_taken.extend(self._recovery_actions(category, context))
        
        elif level == RiskLevel.MEDIUM:
            # Moderate mitigation
            for strategy in strategies:
                if strategy == MitigationStrategy.DETECTION:
                    actions_taken.extend(self._detection_actions(category, context))
                elif strategy == MitigationStrategy.PREVENTION:
                    actions_taken.extend(self._prevention_actions(category, context))
        
        # Record risk event
        import hashlib
        event_id = hashlib.sha256(
            f"{category.value}:{level.value}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        event = RiskEvent(
            event_id=event_id,
            category=category,
            level=level,
            description=f"{category.value} at {level.value} level",
            detected_at=datetime.utcnow(),
            mitigated=len(actions_taken) > 0,
            mitigation_actions=actions_taken
        )
        
        self.risk_events.append(event)
        
        logger.warning(f"Risk mitigated: {category.value} ({level.value}) - {len(actions_taken)} actions")
        
        return actions_taken
    
    def _emergency_mitigation(self, category: RiskCategory, context: Dict[str, Any]) -> List[str]:
        """Emergency mitigation actions"""
        actions = []
        
        if category == RiskCategory.MARKET_RISK:
            actions.append("CLOSE_ALL_POSITIONS")
            actions.append("CANCEL_ALL_ORDERS")
            actions.append("STOP_TRADING")
        
        elif category == RiskCategory.GOAL_DRIFT_RISK:
            actions.append("FREEZE_AI_EVOLUTION")
            actions.append("ROLLBACK_TO_LAST_SAFE_STATE")
            actions.append("ALERT_HUMAN_OPERATORS")
        
        elif category == RiskCategory.RECURSIVE_IMPROVEMENT_RISK:
            actions.append("BLOCK_FURTHER_RECURSION")
            actions.append("ROLLBACK_ALL_IMPROVEMENTS")
            actions.append("RESET_TO_BASELINE")
        
        elif category == RiskCategory.EMERGENT_BEHAVIOR_RISK:
            actions.append("EMERGENCY_SHUTDOWN")
            actions.append("ISOLATE_SYSTEM")
            actions.append("REQUIRE_HUMAN_RESTART")
        
        return actions
    
    def _containment_actions(self, category: RiskCategory, context: Dict[str, Any]) -> List[str]:
        """Containment actions"""
        actions = []
        
        if category == RiskCategory.MARKET_RISK:
            actions.append("REDUCE_POSITION_SIZES_50_PERCENT")
            actions.append("TIGHTEN_STOP_LOSSES")
        
        elif category == RiskCategory.RECURSIVE_IMPROVEMENT_RISK:
            actions.append("PAUSE_EVOLUTION_CYCLE")
            actions.append("REQUIRE_APPROVAL_FOR_CHANGES")
        
        return actions
    
    def _recovery_actions(self, category: RiskCategory, context: Dict[str, Any]) -> List[str]:
        """Recovery actions"""
        actions = []
        
        actions.append("CREATE_SYSTEM_CHECKPOINT")
        actions.append("VERIFY_SAFETY_CORE_INTEGRITY")
        actions.append("RUN_DIAGNOSTIC_TESTS")
        
        return actions
    
    def _detection_actions(self, category: RiskCategory, context: Dict[str, Any]) -> List[str]:
        """Detection actions"""
        return [
            "INCREASE_MONITORING_FREQUENCY",
            "ENABLE_DETAILED_LOGGING",
            "ALERT_MONITORING_TEAM"
        ]
    
    def _prevention_actions(self, category: RiskCategory, context: Dict[str, Any]) -> List[str]:
        """Prevention actions"""
        return [
            "APPLY_STRICTER_LIMITS",
            "ENABLE_ADDITIONAL_CHECKS",
            "REDUCE_AUTOMATION_LEVEL"
        ]
    
    def get_overall_risk_level(self) -> RiskLevel:
        """Get overall system risk level"""
        
        # Get all current risk levels
        risk_levels = [metric.get_risk_level() for metric in self.risk_metrics.values()]
        
        if not risk_levels:
            return RiskLevel.NONE
        
        # Return highest risk level
        return max(risk_levels, key=lambda x: x.value)
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive risk report"""
        
        overall_risk = self.get_overall_risk_level()
        
        return {
            'overall_risk_level': overall_risk.name,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                name: {
                    'value': metric.current_value,
                    'risk_level': metric.get_risk_level().name,
                    'thresholds': {
                        'low': metric.threshold_low,
                        'medium': metric.threshold_medium,
                        'high': metric.threshold_high,
                        'critical': metric.threshold_critical
                    }
                }
                for name, metric in self.risk_metrics.items()
            },
            'recent_events': [
                {
                    'category': event.category.value,
                    'level': event.level.name,
                    'description': event.description,
                    'detected_at': event.detected_at.isoformat(),
                    'mitigated': event.mitigated,
                    'actions': event.mitigation_actions
                }
                for event in self.risk_events[-10:]  # Last 10 events
            ],
            'total_events': len(self.risk_events),
            'critical_events': len([e for e in self.risk_events if e.level == RiskLevel.CRITICAL])
        }
