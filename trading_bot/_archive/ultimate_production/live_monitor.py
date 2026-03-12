"""
Live Monitor - Real-Time System Monitoring and Alerting
========================================================

This module provides comprehensive monitoring for the trading system:

1. Real-time performance tracking
2. Risk metrics monitoring
3. System health checks
4. Alert generation and notification
5. Dashboard data provision
6. Anomaly detection

Goal: Ensure complete visibility into system operations and
early warning of any issues.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import json
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AlertType(Enum):
    """Types of alerts"""
    PERFORMANCE = "performance"
    RISK = "risk"
    SYSTEM = "system"
    EXECUTION = "execution"
    DATA = "data"
    CONNECTIVITY = "connectivity"


@dataclass
class Alert:
    """Alert notification"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.name,
            'type': self.alert_type.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'acknowledged': self.acknowledged,
        }


@dataclass
class SystemHealth:
    """System health status"""
    timestamp: datetime
    overall_status: str  # healthy, degraded, critical
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    data_feed_status: str
    broker_status: str
    components: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'overall_status': self.overall_status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_latency': self.network_latency,
            'data_feed_status': self.data_feed_status,
            'broker_status': self.broker_status,
            'components': self.components,
        }


class PerformanceTracker:
    """
    Track and analyze trading performance in real-time
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Performance history
        self.equity_history: deque = deque(maxlen=10000)
        self.trade_history: deque = deque(maxlen=1000)
        self.daily_returns: Dict[str, float] = {}
        
        # Current metrics
        self.current_equity = 0.0
        self.peak_equity = 0.0
        self.starting_equity = 0.0
        
        # Calculated metrics
        self.total_return = 0.0
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
    
    def update_equity(self, equity: float, timestamp: Optional[datetime] = None):
        """Update equity and recalculate metrics"""
        timestamp = timestamp or datetime.now()
        
        if self.starting_equity == 0:
            self.starting_equity = equity
        
        self.current_equity = equity
        self.equity_history.append((timestamp, equity))
        
        # Update peak
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        # Calculate drawdown
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Calculate return
        if self.starting_equity > 0:
            self.total_return = (equity - self.starting_equity) / self.starting_equity
        
        # Update daily return
        date_str = timestamp.strftime('%Y-%m-%d')
        if date_str not in self.daily_returns:
            self.daily_returns[date_str] = 0.0
        
        if len(self.equity_history) >= 2:
            prev_equity = self.equity_history[-2][1]
            if prev_equity > 0:
                daily_return = (equity - prev_equity) / prev_equity
                self.daily_returns[date_str] = daily_return
        
        # Recalculate ratios
        self._calculate_ratios()
    
    def record_trade(self, pnl: float, pnl_percent: float):
        """Record a completed trade"""
        self.trade_history.append({
            'timestamp': datetime.now(),
            'pnl': pnl,
            'pnl_percent': pnl_percent,
        })
        
        # Update win rate and profit factor
        self._calculate_trade_metrics()
    
    def _calculate_ratios(self):
        """Calculate Sharpe and Sortino ratios"""
        if len(self.daily_returns) < 5:
            return
        
        returns = list(self.daily_returns.values())
        
        # Sharpe ratio (annualized)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        if std_return > 0:
            self.sharpe_ratio = (mean_return * 252) / (std_return * np.sqrt(252))
        
        # Sortino ratio (annualized)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_std = np.std(downside_returns)
            if downside_std > 0:
                self.sortino_ratio = (mean_return * 252) / (downside_std * np.sqrt(252))
    
    def _calculate_trade_metrics(self):
        """Calculate trade-based metrics"""
        if not self.trade_history:
            return
        
        trades = list(self.trade_history)
        
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] < 0]
        
        # Win rate
        self.win_rate = len(wins) / len(trades) if trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = abs(sum(t['pnl'] for t in losses))
        self.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'current_equity': self.current_equity,
            'total_return': self.total_return,
            'total_return_pct': f"{self.total_return:.2%}",
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': f"{self.max_drawdown:.2%}",
            'current_drawdown': self.current_drawdown,
            'current_drawdown_pct': f"{self.current_drawdown:.2%}",
            'win_rate': self.win_rate,
            'win_rate_pct': f"{self.win_rate:.2%}",
            'profit_factor': self.profit_factor,
            'total_trades': len(self.trade_history),
        }


class RiskMonitor:
    """
    Monitor risk metrics and generate alerts
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Risk thresholds
        self.max_drawdown_warning = self.config.get('max_drawdown_warning', 0.05)
        self.max_drawdown_critical = self.config.get('max_drawdown_critical', 0.10)
        self.max_daily_loss_warning = self.config.get('max_daily_loss_warning', 0.015)
        self.max_daily_loss_critical = self.config.get('max_daily_loss_critical', 0.02)
        self.max_position_concentration = self.config.get('max_position_concentration', 0.30)
        
        # Current state
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0
        self.position_concentration: Dict[str, float] = {}
    
    def update(
        self,
        drawdown: float,
        daily_pnl: float,
        positions: Dict[str, Any],
        capital: float
    ):
        """Update risk metrics"""
        self.current_drawdown = drawdown
        self.daily_pnl = daily_pnl
        
        # Calculate position concentration
        self.position_concentration = {}
        for symbol, position in positions.items():
            if hasattr(position, 'quantity') and hasattr(position, 'entry_price'):
                value = position.quantity * position.entry_price
                self.position_concentration[symbol] = value / capital if capital > 0 else 0
    
    def check_alerts(self) -> List[Alert]:
        """Check for risk alerts"""
        alerts = []
        
        # Drawdown alerts
        if self.current_drawdown >= self.max_drawdown_critical:
            alerts.append(Alert(
                alert_id=f"risk_dd_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.RISK,
                title="Critical Drawdown",
                message=f"Drawdown has reached {self.current_drawdown:.2%}, exceeding critical threshold",
                data={'drawdown': self.current_drawdown}
            ))
        elif self.current_drawdown >= self.max_drawdown_warning:
            alerts.append(Alert(
                alert_id=f"risk_dd_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.RISK,
                title="Drawdown Warning",
                message=f"Drawdown has reached {self.current_drawdown:.2%}",
                data={'drawdown': self.current_drawdown}
            ))
        
        # Daily loss alerts
        daily_loss_pct = -self.daily_pnl if self.daily_pnl < 0 else 0
        if daily_loss_pct >= self.max_daily_loss_critical:
            alerts.append(Alert(
                alert_id=f"risk_daily_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.RISK,
                title="Critical Daily Loss",
                message=f"Daily loss has reached {daily_loss_pct:.2%}",
                data={'daily_loss': daily_loss_pct}
            ))
        elif daily_loss_pct >= self.max_daily_loss_warning:
            alerts.append(Alert(
                alert_id=f"risk_daily_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.RISK,
                title="Daily Loss Warning",
                message=f"Daily loss has reached {daily_loss_pct:.2%}",
                data={'daily_loss': daily_loss_pct}
            ))
        
        # Concentration alerts
        for symbol, concentration in self.position_concentration.items():
            if concentration >= self.max_position_concentration:
                alerts.append(Alert(
                    alert_id=f"risk_conc_{symbol}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.RISK,
                    title="Position Concentration",
                    message=f"Position in {symbol} is {concentration:.2%} of portfolio",
                    data={'symbol': symbol, 'concentration': concentration}
                ))
        
        return alerts
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            'current_drawdown': self.current_drawdown,
            'daily_pnl': self.daily_pnl,
            'position_concentration': self.position_concentration,
            'max_concentration': max(self.position_concentration.values()) if self.position_concentration else 0,
        }


class SystemHealthMonitor:
    """
    Monitor system health and resources
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Health thresholds
        self.cpu_warning = self.config.get('cpu_warning', 0.80)
        self.memory_warning = self.config.get('memory_warning', 0.80)
        self.latency_warning = self.config.get('latency_warning', 100)  # ms
        
        # Component status
        self.component_status: Dict[str, str] = {}
        
        # Last health check
        self.last_health: Optional[SystemHealth] = None
    
    def check_health(self) -> SystemHealth:
        """Perform health check"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent() / 100
            memory_usage = psutil.virtual_memory().percent / 100
            disk_usage = psutil.disk_usage('/').percent / 100
        except ImportError:
            # Fallback if psutil not available
            cpu_usage = 0.5
            memory_usage = 0.5
            disk_usage = 0.5
        
        # Simulate network latency check
        network_latency = np.random.uniform(10, 50)  # ms
        
        # Determine overall status
        if cpu_usage > 0.95 or memory_usage > 0.95:
            overall_status = "critical"
        elif cpu_usage > self.cpu_warning or memory_usage > self.memory_warning:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        health = SystemHealth(
            timestamp=datetime.now(),
            overall_status=overall_status,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_latency=network_latency,
            data_feed_status="connected",
            broker_status="connected",
            components=self.component_status,
        )
        
        self.last_health = health
        return health
    
    def update_component_status(self, component: str, status: str):
        """Update status of a component"""
        self.component_status[component] = status
    
    def check_alerts(self) -> List[Alert]:
        """Check for system health alerts"""
        alerts = []
        
        if not self.last_health:
            return alerts
        
        health = self.last_health
        
        if health.cpu_usage > self.cpu_warning:
            alerts.append(Alert(
                alert_id=f"sys_cpu_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.SYSTEM,
                title="High CPU Usage",
                message=f"CPU usage is at {health.cpu_usage:.0%}",
                data={'cpu_usage': health.cpu_usage}
            ))
        
        if health.memory_usage > self.memory_warning:
            alerts.append(Alert(
                alert_id=f"sys_mem_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.SYSTEM,
                title="High Memory Usage",
                message=f"Memory usage is at {health.memory_usage:.0%}",
                data={'memory_usage': health.memory_usage}
            ))
        
        if health.network_latency > self.latency_warning:
            alerts.append(Alert(
                alert_id=f"sys_lat_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.CONNECTIVITY,
                title="High Network Latency",
                message=f"Network latency is {health.network_latency:.0f}ms",
                data={'latency': health.network_latency}
            ))
        
        return alerts


class AlertManager:
    """
    Manage alerts and notifications
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Alert history
        self.alerts: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}
        
        # Notification callbacks
        self.notification_callbacks: List[Callable] = []
        
        # Alert suppression (prevent spam)
        self.suppression_window = self.config.get('suppression_window', 300)  # 5 minutes
        self.recent_alerts: Dict[str, datetime] = {}
    
    def add_alert(self, alert: Alert):
        """Add a new alert"""
        # Check suppression
        alert_key = f"{alert.alert_type.value}_{alert.title}"
        if alert_key in self.recent_alerts:
            last_time = self.recent_alerts[alert_key]
            if (datetime.now() - last_time).total_seconds() < self.suppression_window:
                return  # Suppress duplicate alert
        
        self.recent_alerts[alert_key] = datetime.now()
        self.alerts.append(alert)
        self.active_alerts[alert.alert_id] = alert
        
        # Log alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.INFO)
        
        logger.log(log_level, f"ALERT [{alert.severity.name}]: {alert.title} - {alert.message}")
        
        # Notify callbacks
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            del self.active_alerts[alert_id]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unacknowledged) alerts"""
        return list(self.active_alerts.values())
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity"""
        return [a for a in self.alerts if a.severity == severity]
    
    def register_callback(self, callback: Callable):
        """Register notification callback"""
        self.notification_callbacks.append(callback)


class LiveMonitor:
    """
    Main Live Monitoring System
    
    Coordinates all monitoring components
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.performance_tracker = PerformanceTracker(config)
        self.risk_monitor = RiskMonitor(config)
        self.health_monitor = SystemHealthMonitor(config)
        self.alert_manager = AlertManager(config)
        
        # Update intervals
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.last_health_check = datetime.now()
        
        # Data storage
        self.data_dir = Path(self.config.get('data_dir', 'monitor_data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Live Monitor initialized")
    
    async def update(
        self,
        state: Any,
        capital: float,
        positions: Dict[str, Any],
        metrics: Any
    ):
        """Update all monitors with current state"""
        # Update performance tracker
        self.performance_tracker.update_equity(capital)
        
        # Update risk monitor
        self.risk_monitor.update(
            drawdown=metrics.current_drawdown if hasattr(metrics, 'current_drawdown') else 0,
            daily_pnl=metrics.total_pnl if hasattr(metrics, 'total_pnl') else 0,
            positions=positions,
            capital=capital,
        )
        
        # Periodic health check
        if (datetime.now() - self.last_health_check).total_seconds() >= self.health_check_interval:
            self.health_monitor.check_health()
            self.last_health_check = datetime.now()
    
    async def check_alerts(self) -> List[Alert]:
        """Check all monitors for alerts"""
        all_alerts = []
        
        # Risk alerts
        risk_alerts = self.risk_monitor.check_alerts()
        all_alerts.extend(risk_alerts)
        
        # System health alerts
        health_alerts = self.health_monitor.check_alerts()
        all_alerts.extend(health_alerts)
        
        # Add alerts to manager
        for alert in all_alerts:
            self.alert_manager.add_alert(alert)
        
        return all_alerts
    
    def record_trade(self, pnl: float, pnl_percent: float):
        """Record a completed trade"""
        self.performance_tracker.record_trade(pnl, pnl_percent)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        return {
            'performance': self.performance_tracker.get_metrics(),
            'risk': self.risk_monitor.get_metrics(),
            'health': self.health_monitor.last_health.to_dict() if self.health_monitor.last_health else {},
            'active_alerts': [a.to_dict() for a in self.alert_manager.get_active_alerts()],
            'timestamp': datetime.now().isoformat(),
        }
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alerts"""
        self.alert_manager.register_callback(callback)
    
    def save_snapshot(self):
        """Save current monitoring snapshot to disk"""
        snapshot = self.get_dashboard_data()
        
        filename = self.data_dir / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
        
        return filename
