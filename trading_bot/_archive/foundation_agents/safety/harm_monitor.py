"""
Harm Monitor - Safety Monitoring System
=========================================

Implements harm detection and prevention:
1. Financial harm detection
2. Systemic risk monitoring
3. Anomalous behavior detection
4. Safety constraint enforcement

Based on the Foundation Agents paper (arXiv:2504.01990) safety systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class HarmType(Enum):
    """Types of potential harm"""
    FINANCIAL_LOSS = "financial_loss"
    EXCESSIVE_RISK = "excessive_risk"
    MARKET_MANIPULATION = "market_manipulation"
    SYSTEMIC_RISK = "systemic_risk"
    REGULATORY_VIOLATION = "regulatory_violation"
    DATA_BREACH = "data_breach"
    OPERATIONAL_FAILURE = "operational_failure"
    REPUTATIONAL_HARM = "reputational_harm"


class SeverityLevel(Enum):
    """Severity levels for harm"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


class AlertStatus(Enum):
    """Status of a harm alert"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class HarmIndicator:
    """An indicator of potential harm"""
    name: str
    description: str
    harm_type: HarmType
    
    # Thresholds
    warning_threshold: float
    critical_threshold: float
    
    # Current state
    current_value: float = 0.0
    is_triggered: bool = False
    
    # History
    value_history: List[float] = field(default_factory=list)
    
    def update(self, value: float):
        """Update indicator value"""
        self.current_value = value
        self.value_history.append(value)
        if len(self.value_history) > 1000:
            self.value_history = self.value_history[-500:]
        
        self.is_triggered = value >= self.warning_threshold
    
    def severity(self) -> SeverityLevel:
        """Get current severity level"""
        if self.current_value >= self.critical_threshold:
            return SeverityLevel.CRITICAL
        elif self.current_value >= self.warning_threshold:
            return SeverityLevel.HIGH
        elif self.current_value >= self.warning_threshold * 0.7:
            return SeverityLevel.MEDIUM
        elif self.current_value >= self.warning_threshold * 0.5:
            return SeverityLevel.LOW
        return SeverityLevel.MINIMAL
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'harm_type': self.harm_type.value,
            'current_value': self.current_value,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'is_triggered': self.is_triggered,
            'severity': self.severity().value
        }


@dataclass
class HarmAlert:
    """An alert for detected harm"""
    alert_id: str
    harm_type: HarmType
    severity: SeverityLevel
    
    # Details
    title: str
    description: str
    indicator_name: str
    indicator_value: float
    
    # Status
    status: AlertStatus = AlertStatus.ACTIVE
    
    # Response
    recommended_actions: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    
    # Timing
    detected_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'harm_type': self.harm_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'detected_at': self.detected_at.isoformat(),
            'recommended_actions': self.recommended_actions
        }


@dataclass
class SafetyConstraint:
    """A safety constraint that must be maintained"""
    constraint_id: str
    name: str
    description: str
    
    # Constraint definition
    constraint_type: str  # "max", "min", "range", "rate"
    parameter: str
    threshold: float
    
    # For range constraints
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # For rate constraints
    time_window: Optional[timedelta] = None
    
    # Status
    is_active: bool = True
    violations: int = 0
    last_violation: Optional[datetime] = None
    
    def check(self, value: float) -> Tuple[bool, str]:
        """Check if constraint is satisfied"""
        if self.constraint_type == "max":
            if value > self.threshold:
                return False, f"{self.parameter} ({value}) exceeds maximum ({self.threshold})"
        elif self.constraint_type == "min":
            if value < self.threshold:
                return False, f"{self.parameter} ({value}) below minimum ({self.threshold})"
        elif self.constraint_type == "range":
            if self.min_value is not None and value < self.min_value:
                return False, f"{self.parameter} ({value}) below range minimum ({self.min_value})"
            if self.max_value is not None and value > self.max_value:
                return False, f"{self.parameter} ({value}) above range maximum ({self.max_value})"
        
        return True, "Constraint satisfied"
    
    def to_dict(self) -> Dict:
        return {
            'constraint_id': self.constraint_id,
            'name': self.name,
            'constraint_type': self.constraint_type,
            'parameter': self.parameter,
            'threshold': self.threshold,
            'is_active': self.is_active,
            'violations': self.violations
        }


class RiskCalculator:
    """Calculates various risk metrics"""
    
    def calculate_var(
        self,
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """Calculate Value at Risk"""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def calculate_cvar(
        self,
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var = self.calculate_var(returns, confidence)
        return np.mean(returns[returns <= var]) if len(returns[returns <= var]) > 0 else var
    
    def calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        if len(equity_curve) == 0:
            return 0.0
        
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (peak - equity_curve) / peak
        return np.max(drawdown)
    
    def calculate_volatility(
        self,
        returns: np.ndarray,
        annualize: bool = True
    ) -> float:
        """Calculate volatility"""
        if len(returns) == 0:
            return 0.0
        
        vol = np.std(returns)
        if annualize:
            vol *= np.sqrt(252)
        return vol
    
    def calculate_concentration_risk(
        self,
        positions: Dict[str, float]
    ) -> float:
        """Calculate portfolio concentration risk (HHI)"""
        if not positions:
            return 0.0
        
        total = sum(abs(v) for v in positions.values())
        if total == 0:
            return 0.0
        
        weights = [abs(v) / total for v in positions.values()]
        hhi = sum(w ** 2 for w in weights)
        return hhi


class BehaviorAnalyzer:
    """Analyzes agent behavior for anomalies"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.action_history: deque = deque(maxlen=window_size)
        self.decision_history: deque = deque(maxlen=window_size)
    
    def record_action(self, action: Dict[str, Any]):
        """Record an action"""
        self.action_history.append({
            'action': action,
            'timestamp': datetime.utcnow()
        })
    
    def record_decision(self, decision: Dict[str, Any]):
        """Record a decision"""
        self.decision_history.append({
            'decision': decision,
            'timestamp': datetime.utcnow()
        })
    
    def detect_anomalous_behavior(self) -> List[Dict[str, Any]]:
        """Detect anomalous behavior patterns"""
        anomalies = []
        
        # Check for rapid action frequency
        if len(self.action_history) >= 10:
            recent = list(self.action_history)[-10:]
            time_span = (recent[-1]['timestamp'] - recent[0]['timestamp']).total_seconds()
            if time_span > 0 and len(recent) / time_span > 1:  # More than 1 action per second
                anomalies.append({
                    'type': 'rapid_actions',
                    'description': 'Unusually high action frequency detected',
                    'severity': SeverityLevel.MEDIUM
                })
        
        # Check for repetitive actions
        if len(self.action_history) >= 5:
            recent_actions = [str(a['action']) for a in list(self.action_history)[-5:]]
            if len(set(recent_actions)) == 1:
                anomalies.append({
                    'type': 'repetitive_actions',
                    'description': 'Same action repeated multiple times',
                    'severity': SeverityLevel.LOW
                })
        
        return anomalies


class HarmMonitor:
    """
    Harm Monitor
    
    Monitors for potential harm and enforces safety constraints
    in the autonomous trading system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.risk_calculator = RiskCalculator()
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # Indicators
        self.indicators: Dict[str, HarmIndicator] = {}
        
        # Constraints
        self.constraints: Dict[str, SafetyConstraint] = {}
        
        # Alerts
        self.alerts: Dict[str, HarmAlert] = {}
        self.alert_history: List[HarmAlert] = []
        
        # Callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'checks_performed': 0,
            'alerts_raised': 0,
            'constraints_violated': 0,
            'false_positives': 0
        }
        
        # Initialize default indicators and constraints
        self._initialize_defaults()
        
        logger.info("Harm Monitor initialized")
    
    def _initialize_defaults(self):
        """Initialize default indicators and constraints"""
        # Default harm indicators
        default_indicators = [
            HarmIndicator(
                name="portfolio_drawdown",
                description="Current portfolio drawdown",
                harm_type=HarmType.FINANCIAL_LOSS,
                warning_threshold=0.10,
                critical_threshold=0.20
            ),
            HarmIndicator(
                name="daily_loss",
                description="Daily loss percentage",
                harm_type=HarmType.FINANCIAL_LOSS,
                warning_threshold=0.03,
                critical_threshold=0.05
            ),
            HarmIndicator(
                name="position_concentration",
                description="Single position concentration",
                harm_type=HarmType.EXCESSIVE_RISK,
                warning_threshold=0.25,
                critical_threshold=0.40
            ),
            HarmIndicator(
                name="leverage_ratio",
                description="Portfolio leverage ratio",
                harm_type=HarmType.EXCESSIVE_RISK,
                warning_threshold=2.0,
                critical_threshold=3.0
            ),
            HarmIndicator(
                name="volatility",
                description="Portfolio volatility",
                harm_type=HarmType.EXCESSIVE_RISK,
                warning_threshold=0.30,
                critical_threshold=0.50
            ),
            HarmIndicator(
                name="correlation_breakdown",
                description="Correlation structure breakdown",
                harm_type=HarmType.SYSTEMIC_RISK,
                warning_threshold=0.7,
                critical_threshold=0.9
            )
        ]
        
        for indicator in default_indicators:
            self.indicators[indicator.name] = indicator
        
        # Default safety constraints
        default_constraints = [
            SafetyConstraint(
                constraint_id="max_position_size",
                name="Maximum Position Size",
                description="Maximum size for any single position",
                constraint_type="max",
                parameter="position_size",
                threshold=0.20
            ),
            SafetyConstraint(
                constraint_id="max_daily_trades",
                name="Maximum Daily Trades",
                description="Maximum number of trades per day",
                constraint_type="max",
                parameter="daily_trades",
                threshold=100
            ),
            SafetyConstraint(
                constraint_id="max_leverage",
                name="Maximum Leverage",
                description="Maximum portfolio leverage",
                constraint_type="max",
                parameter="leverage",
                threshold=3.0
            ),
            SafetyConstraint(
                constraint_id="min_cash_reserve",
                name="Minimum Cash Reserve",
                description="Minimum cash as percentage of portfolio",
                constraint_type="min",
                parameter="cash_ratio",
                threshold=0.05
            ),
            SafetyConstraint(
                constraint_id="max_sector_exposure",
                name="Maximum Sector Exposure",
                description="Maximum exposure to any single sector",
                constraint_type="max",
                parameter="sector_exposure",
                threshold=0.40
            )
        ]
        
        for constraint in default_constraints:
            self.constraints[constraint.constraint_id] = constraint
    
    def update_indicator(self, name: str, value: float):
        """Update a harm indicator"""
        if name not in self.indicators:
            return
        
        indicator = self.indicators[name]
        old_triggered = indicator.is_triggered
        indicator.update(value)
        
        # Check if newly triggered
        if indicator.is_triggered and not old_triggered:
            self._raise_alert(indicator)
        
        self.stats['checks_performed'] += 1
    
    def check_constraint(
        self,
        constraint_id: str,
        value: float
    ) -> Tuple[bool, str]:
        """Check a safety constraint"""
        if constraint_id not in self.constraints:
            return True, "Constraint not found"
        
        constraint = self.constraints[constraint_id]
        
        if not constraint.is_active:
            return True, "Constraint inactive"
        
        satisfied, message = constraint.check(value)
        
        if not satisfied:
            constraint.violations += 1
            constraint.last_violation = datetime.utcnow()
            self.stats['constraints_violated'] += 1
            
            # Raise alert for constraint violation
            self._raise_constraint_alert(constraint, value, message)
        
        return satisfied, message
    
    def check_all_constraints(
        self,
        values: Dict[str, float]
    ) -> List[Tuple[str, bool, str]]:
        """Check all constraints against provided values"""
        results = []
        
        for constraint_id, constraint in self.constraints.items():
            if constraint.parameter in values:
                satisfied, message = self.check_constraint(
                    constraint_id,
                    values[constraint.parameter]
                )
                results.append((constraint_id, satisfied, message))
        
        return results
    
    def _raise_alert(self, indicator: HarmIndicator):
        """Raise an alert for a triggered indicator"""
        alert = HarmAlert(
            alert_id=f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(indicator.name.encode()).hexdigest()[:6]}",
            harm_type=indicator.harm_type,
            severity=indicator.severity(),
            title=f"Harm indicator triggered: {indicator.name}",
            description=indicator.description,
            indicator_name=indicator.name,
            indicator_value=indicator.current_value,
            recommended_actions=self._get_recommended_actions(indicator)
        )
        
        self.alerts[alert.alert_id] = alert
        self.stats['alerts_raised'] += 1
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"Harm alert raised: {alert.title}")
    
    def _raise_constraint_alert(
        self,
        constraint: SafetyConstraint,
        value: float,
        message: str
    ):
        """Raise an alert for constraint violation"""
        alert = HarmAlert(
            alert_id=f"constraint_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{constraint.constraint_id[:6]}",
            harm_type=HarmType.REGULATORY_VIOLATION,
            severity=SeverityLevel.HIGH,
            title=f"Safety constraint violated: {constraint.name}",
            description=message,
            indicator_name=constraint.parameter,
            indicator_value=value,
            recommended_actions=[
                f"Reduce {constraint.parameter} to within limits",
                "Review recent actions that led to violation",
                "Consider pausing automated trading"
            ]
        )
        
        self.alerts[alert.alert_id] = alert
        self.stats['alerts_raised'] += 1
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def _get_recommended_actions(self, indicator: HarmIndicator) -> List[str]:
        """Get recommended actions for an indicator"""
        actions = []
        
        if indicator.harm_type == HarmType.FINANCIAL_LOSS:
            actions = [
                "Review and potentially reduce position sizes",
                "Consider implementing stop-loss orders",
                "Evaluate current strategy performance"
            ]
        elif indicator.harm_type == HarmType.EXCESSIVE_RISK:
            actions = [
                "Reduce portfolio leverage",
                "Diversify concentrated positions",
                "Increase hedging activities"
            ]
        elif indicator.harm_type == HarmType.SYSTEMIC_RISK:
            actions = [
                "Reduce exposure to correlated assets",
                "Increase cash reserves",
                "Consider defensive positioning"
            ]
        
        return actions
    
    def acknowledge_alert(self, alert_id: str, notes: str = ""):
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.metadata['acknowledgment_notes'] = notes
    
    def resolve_alert(self, alert_id: str, actions_taken: List[str]):
        """Resolve an alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.actions_taken = actions_taken
            self.alert_history.append(alert)
    
    def mark_false_positive(self, alert_id: str, reason: str = ""):
        """Mark an alert as false positive"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.FALSE_POSITIVE
            alert.metadata['false_positive_reason'] = reason
            self.stats['false_positives'] += 1
            self.alert_history.append(alert)
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for alerts"""
        self.alert_callbacks.append(callback)
    
    def monitor_portfolio(
        self,
        positions: Dict[str, float],
        returns: np.ndarray,
        equity_curve: np.ndarray
    ) -> Dict[str, Any]:
        """Comprehensive portfolio monitoring"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'indicators': {},
            'alerts': [],
            'constraints': []
        }
        
        # Calculate and update indicators
        if len(returns) > 0:
            # Drawdown
            drawdown = self.risk_calculator.calculate_max_drawdown(equity_curve)
            self.update_indicator('portfolio_drawdown', drawdown)
            results['indicators']['drawdown'] = drawdown
            
            # Daily loss (last return)
            daily_loss = -returns[-1] if returns[-1] < 0 else 0
            self.update_indicator('daily_loss', daily_loss)
            results['indicators']['daily_loss'] = daily_loss
            
            # Volatility
            volatility = self.risk_calculator.calculate_volatility(returns)
            self.update_indicator('volatility', volatility)
            results['indicators']['volatility'] = volatility
        
        # Position concentration
        if positions:
            concentration = self.risk_calculator.calculate_concentration_risk(positions)
            self.update_indicator('position_concentration', concentration)
            results['indicators']['concentration'] = concentration
            
            # Check position size constraints
            total = sum(abs(v) for v in positions.values())
            for asset, size in positions.items():
                position_pct = abs(size) / total if total > 0 else 0
                satisfied, msg = self.check_constraint('max_position_size', position_pct)
                if not satisfied:
                    results['constraints'].append({
                        'constraint': 'max_position_size',
                        'asset': asset,
                        'message': msg
                    })
        
        # Collect active alerts
        results['alerts'] = [
            a.to_dict() for a in self.alerts.values()
            if a.status == AlertStatus.ACTIVE
        ]
        
        return results
    
    def record_action(self, action: Dict[str, Any]):
        """Record an action for behavior analysis"""
        self.behavior_analyzer.record_action(action)
    
    def check_behavior(self) -> List[Dict[str, Any]]:
        """Check for anomalous behavior"""
        return self.behavior_analyzer.detect_anomalous_behavior()
    
    def get_active_alerts(self) -> List[HarmAlert]:
        """Get all active alerts"""
        return [a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]
    
    def get_alert(self, alert_id: str) -> Optional[HarmAlert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_indicator_status(self) -> Dict[str, Dict]:
        """Get status of all indicators"""
        return {name: ind.to_dict() for name, ind in self.indicators.items()}
    
    def get_constraint_status(self) -> Dict[str, Dict]:
        """Get status of all constraints"""
        return {cid: c.to_dict() for cid, c in self.constraints.items()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            **self.stats,
            'active_alerts': len(self.get_active_alerts()),
            'triggered_indicators': len([i for i in self.indicators.values() if i.is_triggered]),
            'total_indicators': len(self.indicators),
            'total_constraints': len(self.constraints)
        }
