"""
Skill #95: Intelligent Alert System
===================================

Smart alerting based on market conditions and user preferences.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Trading alert."""
    alert_type: str
    severity: str
    message: str
    timestamp: datetime


@dataclass
class AlertResult:
    """Alert system result."""
    alerts: List[Alert]
    suppressed_count: int
    trading_signal: str


class IntelligentAlertSystem:
    """Intelligent alert management."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.alert_history: List[Alert] = []
        self.suppression_rules: Dict[str, int] = {}
        logger.info("IntelligentAlertSystem initialized")
    
    def create_alert(self, alert_type: str, severity: str, message: str) -> Alert:
        """Create an alert."""
        alert = Alert(alert_type, severity, message, datetime.now())
        self.alert_history.append(alert)
        return alert
    
    def check_conditions(self, conditions: Dict) -> AlertResult:
        """Check conditions and generate alerts."""
        alerts = []
        suppressed = 0
        
        if conditions.get('price_change', 0) > 0.05:
            alerts.append(self.create_alert('price', 'high', 'Large price movement detected'))
        
        if conditions.get('volume_spike', False):
            alerts.append(self.create_alert('volume', 'medium', 'Volume spike detected'))
        
        if conditions.get('drawdown', 0) > 0.1:
            alerts.append(self.create_alert('risk', 'critical', 'Drawdown threshold exceeded'))
        
        return AlertResult(
            alerts=alerts, suppressed_count=suppressed,
            trading_signal=f"ALERTS: {len(alerts)} new, {suppressed} suppressed"
        )
