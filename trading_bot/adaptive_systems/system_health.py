import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""System Health Monitor with Failsafes.

This module implements comprehensive system health monitoring with automatic
failsafe mechanisms to ensure the trading bot remains stable and resilient.
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
try:
    import yaml
except ImportError:
    yaml = None
import pathlib


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class FailsafeAction(Enum):
    """Available failsafe actions."""
    LOG_WARNING = "log_warning"
    REDUCE_RISK = "reduce_risk"
    PAUSE_TRADING = "pause_trading"
    CLOSE_POSITIONS = "close_positions"
    EMERGENCY_STOP = "emergency_stop"
    RESTART_COMPONENT = "restart_component"


@dataclass
class HealthMetric:
    """Health monitoring metric."""
    name: str
    current_value: float
    threshold_warning: float
    threshold_critical: float
    threshold_emergency: float
    last_updated: datetime = field(default_factory=datetime.now)
    status: HealthStatus = HealthStatus.HEALTHY
    trend: List[float] = field(default_factory=list)


@dataclass
class FailsafeRule:
    """Failsafe rule definition."""
    condition: str
    action: FailsafeAction
    threshold: float
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class SystemHealthMonitor:
    """Comprehensive system health monitoring with failsafes."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the system health monitor.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.metrics = {}
        self.failsafe_rules = []
        self.callbacks = {}
        self.monitoring_active = False
        self.monitor_thread = None
        
        # System state tracking
        self.system_start_time = datetime.now()
        self.last_health_check = None
        self.health_history = []
        self.emergency_mode = False
        
        # Initialize metrics and rules
        self._initialize_metrics()
        self._initialize_failsafe_rules()
        
        logger.info("SystemHealthMonitor initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f).get('health_monitor', {})
            except Exception as e:
                logger.warning(f"Could not load health config: {e}")
        
        # Default configuration
        return {
            'enabled': True,
            'check_interval': 60,
            'thresholds': {
                'max_drawdown': 0.15,
                'consecutive_losses': 5,
                'win_rate_minimum': 0.3,
                'connection_timeout': 30,
                'memory_usage_max': 0.8,
                'cpu_usage_max': 0.9
            },
            'failsafes': {
                'emergency_stop': True,
                'position_closure': True,
                'risk_reduction': True,
                'strategy_pause': True
            }
        }
    
    def _initialize_metrics(self):
        """Initialize health monitoring metrics."""
        thresholds = self.config.get('thresholds', {})
        
        # Trading performance metrics
        self.metrics['drawdown'] = HealthMetric(
            name='drawdown',
            current_value=0.0,
            threshold_warning=thresholds.get('max_drawdown', 0.15) * 0.7,
            threshold_critical=thresholds.get('max_drawdown', 0.15) * 0.9,
            threshold_emergency=thresholds.get('max_drawdown', 0.15)
        )
        
        self.metrics['consecutive_losses'] = HealthMetric(
            name='consecutive_losses',
            current_value=0,
            threshold_warning=thresholds.get('consecutive_losses', 5) * 0.6,
            threshold_critical=thresholds.get('consecutive_losses', 5) * 0.8,
            threshold_emergency=thresholds.get('consecutive_losses', 5)
        )
        
        self.metrics['win_rate'] = HealthMetric(
            name='win_rate',
            current_value=0.5,
            threshold_warning=thresholds.get('win_rate_minimum', 0.3) * 1.2,
            threshold_critical=thresholds.get('win_rate_minimum', 0.3) * 1.1,
            threshold_emergency=thresholds.get('win_rate_minimum', 0.3)
        )
        
        # System resource metrics
        self.metrics['memory_usage'] = HealthMetric(
            name='memory_usage',
            current_value=0.0,
            threshold_warning=thresholds.get('memory_usage_max', 0.8) * 0.8,
            threshold_critical=thresholds.get('memory_usage_max', 0.8) * 0.9,
            threshold_emergency=thresholds.get('memory_usage_max', 0.8)
        )
        
        self.metrics['cpu_usage'] = HealthMetric(
            name='cpu_usage',
            current_value=0.0,
            threshold_warning=thresholds.get('cpu_usage_max', 0.9) * 0.8,
            threshold_critical=thresholds.get('cpu_usage_max', 0.9) * 0.9,
            threshold_emergency=thresholds.get('cpu_usage_max', 0.9)
        )
        
        # Connection and latency metrics
        self.metrics['connection_latency'] = HealthMetric(
            name='connection_latency',
            current_value=0.0,
            threshold_warning=thresholds.get('connection_timeout', 30) * 0.5,
            threshold_critical=thresholds.get('connection_timeout', 30) * 0.7,
            threshold_emergency=thresholds.get('connection_timeout', 30)
        )
    
    def _initialize_failsafe_rules(self):
        """Initialize failsafe rules."""
        failsafes = self.config.get('failsafes', {})
        
        if failsafes.get('emergency_stop', True):
            self.failsafe_rules.append(FailsafeRule(
                condition='drawdown >= threshold_emergency',
                action=FailsafeAction.EMERGENCY_STOP,
                threshold=self.metrics['drawdown'].threshold_emergency,
                cooldown_minutes=60
            ))
        
        if failsafes.get('position_closure', True):
            self.failsafe_rules.append(FailsafeRule(
                condition='consecutive_losses >= threshold_critical',
                action=FailsafeAction.CLOSE_POSITIONS,
                threshold=self.metrics['consecutive_losses'].threshold_critical,
                cooldown_minutes=30
            ))
        
        if failsafes.get('risk_reduction', True):
            self.failsafe_rules.append(FailsafeRule(
                condition='win_rate <= threshold_critical',
                action=FailsafeAction.REDUCE_RISK,
                threshold=self.metrics['win_rate'].threshold_critical,
                cooldown_minutes=15
            ))
        
        if failsafes.get('strategy_pause', True):
            self.failsafe_rules.append(FailsafeRule(
                condition='memory_usage >= threshold_critical',
                action=FailsafeAction.PAUSE_TRADING,
                threshold=self.metrics['memory_usage'].threshold_critical,
                cooldown_minutes=10
            ))
    
    def start_monitoring(self):
        """Start the health monitoring system."""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("System health monitoring started")
    
    def stop_monitoring(self):
        """Stop the health monitoring system."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("System health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        check_interval = self.config.get('check_interval', 60)
        
        while self.monitoring_active:
            try:
                self._perform_health_check()
                self._evaluate_failsafe_rules()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(check_interval)
    
    def _perform_health_check(self):
        """Perform comprehensive health check."""
        self.last_health_check = datetime.now()
        
        # Update system resource metrics
        self._update_system_metrics()
        
        # Update all metric statuses
        overall_status = HealthStatus.HEALTHY
        
        for metric in self.metrics.values():
            metric.status = self._calculate_metric_status(metric)
            
            # Update trend
            metric.trend.append(metric.current_value)
            if len(metric.trend) > 100:  # Keep last 100 readings
                metric.trend.pop(0)
            
            # Determine overall status
            if metric.status == HealthStatus.EMERGENCY:
                overall_status = HealthStatus.EMERGENCY
            elif metric.status == HealthStatus.CRITICAL and overall_status != HealthStatus.EMERGENCY:
                overall_status = HealthStatus.CRITICAL
            elif metric.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.WARNING
        
        # Store health snapshot
        health_snapshot = {
            'timestamp': self.last_health_check,
            'overall_status': overall_status,
            'metrics': {name: {
                'value': metric.current_value,
                'status': metric.status.value
            } for name, metric in self.metrics.items()}
        }
        
        self.health_history.append(health_snapshot)
        if len(self.health_history) > 1000:  # Keep last 1000 snapshots
            self.health_history.pop(0)
        
        # Log status if not healthy
        if overall_status != HealthStatus.HEALTHY:
            logger.warning(f"System health status: {overall_status.value}")
    
    def _update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].current_value = memory.percent / 100.0
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].current_value = cpu_percent / 100.0
            
            # Update timestamps
            for metric in self.metrics.values():
                if metric.name in ['memory_usage', 'cpu_usage']:
                    metric.last_updated = datetime.now()
                    
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def _calculate_metric_status(self, metric: HealthMetric) -> HealthStatus:
        """Calculate status for a metric based on thresholds."""
        value = metric.current_value
        
        # For metrics where lower is better (like win_rate), reverse logic
        if metric.name == 'win_rate':
            if value <= metric.threshold_emergency:
                return HealthStatus.EMERGENCY
            elif value <= metric.threshold_critical:
                return HealthStatus.CRITICAL
            elif value <= metric.threshold_warning:
                return HealthStatus.WARNING
        else:
            # For metrics where higher is worse
            if value >= metric.threshold_emergency:
                return HealthStatus.EMERGENCY
            elif value >= metric.threshold_critical:
                return HealthStatus.CRITICAL
            elif value >= metric.threshold_warning:
                return HealthStatus.WARNING
        
        return HealthStatus.HEALTHY
    
    def _evaluate_failsafe_rules(self):
        """Evaluate and trigger failsafe rules if necessary."""
        for rule in self.failsafe_rules:
            if self._should_trigger_rule(rule):
                self._trigger_failsafe(rule)
    
    def _should_trigger_rule(self, rule: FailsafeRule) -> bool:
        """Check if a failsafe rule should be triggered."""
        # Check cooldown
        if rule.last_triggered:
            cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
            if datetime.now() < cooldown_end:
                return False
        
        # Evaluate condition
        if 'drawdown' in rule.condition:
            return self.metrics['drawdown'].current_value >= rule.threshold
        elif 'consecutive_losses' in rule.condition:
            return self.metrics['consecutive_losses'].current_value >= rule.threshold
        elif 'win_rate' in rule.condition:
            return self.metrics['win_rate'].current_value <= rule.threshold
        elif 'memory_usage' in rule.condition:
            return self.metrics['memory_usage'].current_value >= rule.threshold
        elif 'cpu_usage' in rule.condition:
            return self.metrics['cpu_usage'].current_value >= rule.threshold
        
        return False
    
    def _trigger_failsafe(self, rule: FailsafeRule):
        """Trigger a failsafe action."""
        rule.last_triggered = datetime.now()
        rule.trigger_count += 1
        
        logger.critical(f"Triggering failsafe: {rule.action.value} (condition: {rule.condition})")
        
        # Execute failsafe action
        if rule.action == FailsafeAction.EMERGENCY_STOP:
            self._emergency_stop()
        elif rule.action == FailsafeAction.CLOSE_POSITIONS:
            self._close_all_positions()
        elif rule.action == FailsafeAction.REDUCE_RISK:
            self._reduce_risk()
        elif rule.action == FailsafeAction.PAUSE_TRADING:
            self._pause_trading()
        
        # Call registered callbacks
        callback = self.callbacks.get(rule.action)
        if callback:
            try:
                callback(rule)
            except Exception as e:
                logger.error(f"Error executing failsafe callback: {e}")
    
    def _emergency_stop(self):
        """Emergency stop all trading activities."""
        self.emergency_mode = True
        logger.critical("EMERGENCY STOP ACTIVATED - All trading halted")
        
        # Stop all trading activities
        self._close_all_positions()
        self._pause_trading()
    
    def _close_all_positions(self):
        """Close all open positions."""
        logger.warning("Failsafe: Closing all positions")
        # Implementation would close actual positions
        
    def _reduce_risk(self):
        """Reduce risk parameters."""
        logger.warning("Failsafe: Reducing risk parameters")
        # Implementation would reduce position sizes, tighten stops, etc.
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        if not self.health_history:
            return {'status': 'no_data'}
        
        latest = self.health_history[-1]
        
        # Calculate uptime
        uptime = datetime.now() - self.system_start_time
        
        # Count failsafe triggers
        total_triggers = sum(rule.trigger_count for rule in self.failsafe_rules)
        
        return {
            'overall_status': latest['overall_status'].value,
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'uptime_hours': uptime.total_seconds() / 3600,
            'emergency_mode': self.emergency_mode,
            'total_failsafe_triggers': total_triggers,
            'metrics': latest['metrics'],
            'recent_triggers': [
                {
                    'action': rule.action.value,
                    'trigger_count': rule.trigger_count,
                    'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None
                }
                for rule in self.failsafe_rules if rule.trigger_count > 0
            ]
        }
