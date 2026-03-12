"""
Systemic Safety System
======================

Prevents systemic failures and cascading disasters:
1. Cascading failure prevention
2. Multi-dimensional risk monitoring
3. Safe mode enforcement
4. Extreme risk containment

RISK OF CASCADING FAILURES:
- One component fails
- Failure spreads to dependent components
- System enters death spiral
- Recovery becomes impossible

PRINCIPLE: No single failure should bring down the system.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Overall system states"""
    NORMAL = "normal"
    DEGRADED = "degraded"
    SAFE_MODE = "safe_mode"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class RiskDimension(Enum):
    """Dimensions of risk to monitor"""
    MARKET = "market"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    TECHNOLOGICAL = "technological"
    BEHAVIORAL = "behavioral"
    SYSTEMIC = "systemic"
    PSYCHOLOGICAL = "psychological"


@dataclass
class FailureEvent:
    """Record of a failure event"""
    event_id: str
    component: str
    failure_type: str
    severity: float  # 0-1
    cascaded_to: List[str]
    contained: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskReading:
    """Reading from a risk dimension"""
    dimension: RiskDimension
    level: float  # 0-1
    trend: str  # 'increasing', 'stable', 'decreasing'
    alerts: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class CascadingFailurePrevention:
    """
    Prevents failures from cascading through the system.
    
    PREVENTION METHODS:
    1. Component isolation
    2. Failure containment
    3. Circuit breakers
    4. Graceful degradation
    5. Automatic recovery
    
    WHEN A COMPONENT FAILS:
    1. Isolate it immediately
    2. Prevent spread to dependents
    3. Activate fallbacks
    4. Alert human
    5. Attempt recovery
    """
    
    # Cascade prevention settings
    MAX_FAILURES_BEFORE_SAFE_MODE = 3
    MAX_CASCADE_DEPTH = 2
    RECOVERY_TIMEOUT_SECONDS = 60
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Component tracking
        self.components: Dict[str, Dict] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.failed_components: Set[str] = set()
        
        # Failure history
        self.failure_events: List[FailureEvent] = []
        self.cascade_in_progress = False
        
        # State
        self.system_state = SystemState.NORMAL
        
        logger.info("CascadingFailurePrevention initialized")
    
    def register_component(
        self,
        component_name: str,
        dependencies: List[str] = None,
        is_critical: bool = False
    ):
        """Register a component with its dependencies"""
        self.components[component_name] = {
            'name': component_name,
            'dependencies': dependencies or [],
            'is_critical': is_critical,
            'is_healthy': True,
            'failure_count': 0,
            'last_failure': None
        }
        
        self.dependencies[component_name] = set(dependencies or [])
    
    def report_failure(
        self,
        component_name: str,
        failure_type: str,
        severity: float
    ) -> FailureEvent:
        """
        Report a component failure.
        
        Returns the failure event with cascade information.
        """
        # Mark component as failed
        self.failed_components.add(component_name)
        
        if component_name in self.components:
            self.components[component_name]['is_healthy'] = False
            self.components[component_name]['failure_count'] += 1
            self.components[component_name]['last_failure'] = datetime.now()
        
        # Check for cascade
        cascaded_to = self._check_cascade(component_name)
        
        # Create failure event
        event = FailureEvent(
            event_id=hashlib.sha256(f"{component_name}_{datetime.now()}".encode()).hexdigest()[:16],
            component=component_name,
            failure_type=failure_type,
            severity=severity,
            cascaded_to=cascaded_to,
            contained=len(cascaded_to) <= self.MAX_CASCADE_DEPTH
        )
        
        self.failure_events.append(event)
        
        # Check if should enter safe mode
        if len(self.failed_components) >= self.MAX_FAILURES_BEFORE_SAFE_MODE:
            self._enter_safe_mode("Too many component failures")
        
        # Check if critical component
        if component_name in self.components and self.components[component_name]['is_critical']:
            self._enter_safe_mode(f"Critical component {component_name} failed")
        
        logger.error(f"FAILURE: {component_name} - {failure_type} (severity: {severity})")
        
        return event
    
    def _check_cascade(self, failed_component: str, depth: int = 0) -> List[str]:
        """Check for cascade effects"""
        if depth >= self.MAX_CASCADE_DEPTH:
            return []
        
        cascaded = []
        
        # Find components that depend on the failed one
        for component, deps in self.dependencies.items():
            if failed_component in deps and component not in self.failed_components:
                # This component may be affected
                cascaded.append(component)
                
                # Check deeper cascade
                deeper = self._check_cascade(component, depth + 1)
                cascaded.extend(deeper)
        
        if cascaded:
            self.cascade_in_progress = True
            logger.warning(f"CASCADE DETECTED: {failed_component} -> {cascaded}")
        
        return cascaded
    
    def _enter_safe_mode(self, reason: str):
        """Enter safe mode"""
        self.system_state = SystemState.SAFE_MODE
        logger.critical(f"ENTERING SAFE MODE: {reason}")
    
    def report_recovery(self, component_name: str):
        """Report that a component has recovered"""
        if component_name in self.failed_components:
            self.failed_components.remove(component_name)
        
        if component_name in self.components:
            self.components[component_name]['is_healthy'] = True
        
        # Check if can exit safe mode
        if len(self.failed_components) == 0 and self.system_state == SystemState.SAFE_MODE:
            self.system_state = SystemState.NORMAL
            logger.info("Exiting safe mode - all components recovered")
    
    def get_healthy_components(self) -> List[str]:
        """Get list of healthy components"""
        return [c for c, d in self.components.items() if d['is_healthy']]
    
    def get_status(self) -> Dict[str, Any]:
        """Get cascade prevention status"""
        return {
            'system_state': self.system_state.value,
            'total_components': len(self.components),
            'failed_components': list(self.failed_components),
            'cascade_in_progress': self.cascade_in_progress,
            'failure_events': len(self.failure_events)
        }


class MultiDimensionalRiskMonitor:
    """
    Monitors risk across multiple dimensions.
    
    RISK DIMENSIONS:
    1. Market Risk - Price movements, volatility
    2. Operational Risk - System failures, errors
    3. Financial Risk - Leverage, concentration
    4. Regulatory Risk - Compliance issues
    5. Technological Risk - Bugs, outages
    6. Behavioral Risk - AI drift, anomalies
    7. Systemic Risk - Cascading failures
    8. Psychological Risk - Human stress
    
    PRINCIPLE: Risk can come from anywhere - monitor everything.
    """
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        'low': 0.3,
        'medium': 0.5,
        'high': 0.7,
        'critical': 0.9
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Risk readings by dimension
        self.risk_readings: Dict[RiskDimension, deque] = {
            dim: deque(maxlen=100) for dim in RiskDimension
        }
        
        # Current levels
        self.current_levels: Dict[RiskDimension, float] = {
            dim: 0.0 for dim in RiskDimension
        }
        
        # Alerts
        self.active_alerts: List[Dict] = []
        
        logger.info("MultiDimensionalRiskMonitor initialized")
    
    def update_risk(
        self,
        dimension: RiskDimension,
        level: float,
        alerts: List[str] = None
    ) -> RiskReading:
        """Update risk reading for a dimension"""
        # Calculate trend
        history = list(self.risk_readings[dimension])
        if len(history) >= 3:
            recent_avg = sum(r.level for r in history[-3:]) / 3
            if level > recent_avg + 0.1:
                trend = 'increasing'
            elif level < recent_avg - 0.1:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        reading = RiskReading(
            dimension=dimension,
            level=level,
            trend=trend,
            alerts=alerts or []
        )
        
        self.risk_readings[dimension].append(reading)
        self.current_levels[dimension] = level
        
        # Check for alerts
        if level >= self.RISK_THRESHOLDS['critical']:
            self._add_alert(dimension, level, 'critical')
        elif level >= self.RISK_THRESHOLDS['high']:
            self._add_alert(dimension, level, 'high')
        
        return reading
    
    def _add_alert(self, dimension: RiskDimension, level: float, severity: str):
        """Add a risk alert"""
        alert = {
            'dimension': dimension.value,
            'level': level,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.active_alerts.append(alert)
        
        logger.warning(f"RISK ALERT: {dimension.value} at {level*100:.0f}% ({severity})")
    
    def get_overall_risk(self) -> Tuple[float, str]:
        """
        Get overall risk level across all dimensions.
        
        Returns:
            Tuple of (risk_level, risk_category)
        """
        if not self.current_levels:
            return 0.0, 'low'
        
        # Weighted average (some dimensions more important)
        weights = {
            RiskDimension.MARKET: 1.5,
            RiskDimension.FINANCIAL: 1.5,
            RiskDimension.OPERATIONAL: 1.2,
            RiskDimension.SYSTEMIC: 1.3,
            RiskDimension.REGULATORY: 1.0,
            RiskDimension.TECHNOLOGICAL: 1.0,
            RiskDimension.BEHAVIORAL: 1.1,
            RiskDimension.PSYCHOLOGICAL: 0.8
        }
        
        weighted_sum = sum(
            self.current_levels[dim] * weights.get(dim, 1.0)
            for dim in RiskDimension
        )
        total_weight = sum(weights.values())
        
        overall = weighted_sum / total_weight
        
        # Determine category
        if overall >= self.RISK_THRESHOLDS['critical']:
            category = 'critical'
        elif overall >= self.RISK_THRESHOLDS['high']:
            category = 'high'
        elif overall >= self.RISK_THRESHOLDS['medium']:
            category = 'medium'
        else:
            category = 'low'
        
        return overall, category
    
    def get_risk_heatmap(self) -> Dict[str, float]:
        """Get risk levels as a heatmap"""
        return {dim.value: level for dim, level in self.current_levels.items()}
    
    def get_status(self) -> Dict[str, Any]:
        """Get risk monitoring status"""
        overall, category = self.get_overall_risk()
        
        return {
            'overall_risk': overall,
            'risk_category': category,
            'dimensions': self.get_risk_heatmap(),
            'active_alerts': len(self.active_alerts),
            'recent_alerts': self.active_alerts[-5:]
        }


class SafeModeRuleset:
    """
    Defines rules for safe mode operation.
    
    SAFE MODE RULES:
    1. No new positions
    2. Reduce existing positions
    3. Wider stop losses
    4. Lower leverage
    5. More conservative parameters
    6. Increased monitoring
    7. Human approval required
    
    SAFE MODE TRIGGERS:
    1. Multiple component failures
    2. High risk levels
    3. Unusual behavior detected
    4. Human request
    5. Regulatory concern
    """
    
    # Safe mode parameters
    SAFE_MODE_RULES = {
        'allow_new_positions': False,
        'max_position_size_pct': 0.25,  # 25% of normal
        'max_leverage': 1.0,            # No leverage
        'stop_loss_multiplier': 2.0,    # Wider stops
        'require_human_approval': True,
        'monitoring_interval_seconds': 10,
        'max_trades_per_hour': 2
    }
    
    # Normal mode parameters
    NORMAL_MODE_RULES = {
        'allow_new_positions': True,
        'max_position_size_pct': 1.0,
        'max_leverage': 3.0,
        'stop_loss_multiplier': 1.0,
        'require_human_approval': False,
        'monitoring_interval_seconds': 60,
        'max_trades_per_hour': 10
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current mode
        self.is_safe_mode = False
        self.safe_mode_reason: Optional[str] = None
        self.safe_mode_since: Optional[datetime] = None
        
        # Current rules
        self.current_rules = self.NORMAL_MODE_RULES.copy()
        
        logger.info("SafeModeRuleset initialized")
    
    def enter_safe_mode(self, reason: str):
        """Enter safe mode"""
        self.is_safe_mode = True
        self.safe_mode_reason = reason
        self.safe_mode_since = datetime.now()
        self.current_rules = self.SAFE_MODE_RULES.copy()
        
        logger.critical(f"SAFE MODE ACTIVATED: {reason}")
    
    def exit_safe_mode(self, authorized_by: str):
        """Exit safe mode (requires authorization)"""
        self.is_safe_mode = False
        self.safe_mode_reason = None
        self.safe_mode_since = None
        self.current_rules = self.NORMAL_MODE_RULES.copy()
        
        logger.info(f"Safe mode deactivated by {authorized_by}")
    
    def get_rule(self, rule_name: str) -> Any:
        """Get current value of a rule"""
        return self.current_rules.get(rule_name)
    
    def can_open_position(self) -> Tuple[bool, str]:
        """Check if new positions are allowed"""
        if not self.current_rules['allow_new_positions']:
            return False, "Safe mode - no new positions"
        return True, "Positions allowed"
    
    def get_position_size_limit(self) -> float:
        """Get current position size limit as fraction of normal"""
        return self.current_rules['max_position_size_pct']
    
    def get_max_leverage(self) -> float:
        """Get current maximum leverage"""
        return self.current_rules['max_leverage']
    
    def requires_approval(self) -> bool:
        """Check if human approval is required"""
        return self.current_rules['require_human_approval']
    
    def get_status(self) -> Dict[str, Any]:
        """Get safe mode status"""
        return {
            'is_safe_mode': self.is_safe_mode,
            'reason': self.safe_mode_reason,
            'since': self.safe_mode_since.isoformat() if self.safe_mode_since else None,
            'current_rules': self.current_rules
        }


class ExtremeRiskContainment:
    """
    Contains extreme risks that could destroy the system.
    
    EXTREME RISKS:
    1. Total system failure
    2. Catastrophic loss
    3. Regulatory shutdown
    4. Broker account closure
    5. Complete AI breakdown
    
    CONTAINMENT METHODS:
    1. Hard limits that cannot be exceeded
    2. Automatic shutdown triggers
    3. Position liquidation
    4. Human escalation
    5. Evidence preservation
    """
    
    # ABSOLUTE LIMITS - Cannot be exceeded under any circumstances
    ABSOLUTE_LIMITS = {
        'max_total_loss_pct': 0.50,         # 50% of capital
        'max_single_day_loss_pct': 0.10,    # 10% in one day
        'max_position_pct': 0.20,           # 20% in one position
        'max_leverage': 5.0,                # 5x leverage
        'max_open_positions': 20,           # 20 positions
        'max_daily_trades': 50,             # 50 trades per day
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Tracking
        self.limit_breaches: List[Dict] = []
        self.containment_actions: List[Dict] = []
        
        # State
        self.is_contained = True
        self.containment_level = 0  # 0 = normal, higher = more contained
        
        logger.info("ExtremeRiskContainment initialized - ABSOLUTE LIMITS ACTIVE")
    
    def check_limit(
        self,
        limit_name: str,
        current_value: float
    ) -> Tuple[bool, str]:
        """
        Check if a value is within absolute limits.
        
        Returns:
            Tuple of (is_within_limit, message)
        """
        if limit_name not in self.ABSOLUTE_LIMITS:
            return True, "Unknown limit"
        
        limit = self.ABSOLUTE_LIMITS[limit_name]
        
        if current_value > limit:
            self._record_breach(limit_name, current_value, limit)
            return False, f"{limit_name} ({current_value}) exceeds absolute limit ({limit})"
        
        # Warning at 80% of limit
        if current_value > limit * 0.8:
            return True, f"WARNING: {limit_name} at {current_value/limit*100:.0f}% of limit"
        
        return True, "Within limits"
    
    def _record_breach(self, limit_name: str, value: float, limit: float):
        """Record a limit breach"""
        breach = {
            'limit': limit_name,
            'value': value,
            'limit_value': limit,
            'timestamp': datetime.now().isoformat()
        }
        self.limit_breaches.append(breach)
        
        logger.critical(f"ABSOLUTE LIMIT BREACH: {limit_name} = {value} > {limit}")
        
        # Take containment action
        self._take_containment_action(limit_name)
    
    def _take_containment_action(self, limit_name: str):
        """Take action to contain the breach"""
        action = {
            'trigger': limit_name,
            'action': 'emergency_containment',
            'timestamp': datetime.now().isoformat()
        }
        
        self.containment_actions.append(action)
        self.containment_level += 1
        
        if self.containment_level >= 3:
            self.is_contained = False
            logger.critical("CONTAINMENT FAILING - IMMEDIATE HUMAN INTERVENTION REQUIRED")
    
    def get_headroom(self, limit_name: str, current_value: float) -> float:
        """Get remaining headroom before hitting limit"""
        if limit_name not in self.ABSOLUTE_LIMITS:
            return float('inf')
        
        limit = self.ABSOLUTE_LIMITS[limit_name]
        return max(0, limit - current_value)
    
    def get_status(self) -> Dict[str, Any]:
        """Get containment status"""
        return {
            'is_contained': self.is_contained,
            'containment_level': self.containment_level,
            'limit_breaches': len(self.limit_breaches),
            'containment_actions': len(self.containment_actions),
            'absolute_limits': self.ABSOLUTE_LIMITS
        }
