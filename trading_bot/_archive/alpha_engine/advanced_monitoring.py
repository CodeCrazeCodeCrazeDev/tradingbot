"""
Advanced Monitoring & Alerting Module
======================================

Comprehensive monitoring and alerting:
- Real-time Performance Dashboard
- Multi-level Alert System
- System Health Monitoring
- Trade Analytics
- Anomaly Detection
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import numpy
import pandas

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""
    PERFORMANCE = "performance"
    RISK = "risk"
    EXECUTION = "execution"
    SYSTEM = "system"
    MODEL = "model"


class AlertChannel(Enum):
    """Alert delivery channels"""
    LOG = "log"
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert notification"""
    timestamp: datetime
    level: AlertLevel
    category: str
    title: str
    message: str
    details: Dict[str, Any]
    acknowledged: bool = False
    channels: List[AlertChannel] = field(default_factory=list)


@dataclass
class Metric:
    """Performance metric"""
    timestamp: datetime
    name: str
    metric_type: MetricType
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class DashboardState:
    """Current dashboard state"""
    timestamp: datetime
    
    # P&L
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float
    ytd_pnl: float
    
    # Positions
    num_positions: int
    total_exposure: float
    net_exposure: float
    
    # Risk
    current_drawdown: float
    var_95: float
    sharpe_ratio: float
    
    # Execution
    trades_today: int
    avg_slippage_bps: float
    fill_rate: float
    
    # System
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    
    # Model
    model_accuracy: float
    signal_quality: float


class MetricsCollector:
    """
    Collects and stores metrics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Metrics storage
        self.metrics: Dict[str, deque] = {}
        
        # Retention period
        self.retention_hours = self.config.get('retention_hours', 168)  # 1 week
    
    def record(self, name: str, value: float, metric_type: MetricType,
              unit: str = "", tags: Dict[str, str] = None):
        """
        Record a metric
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            unit: Unit of measurement
            tags: Additional tags
        """
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=10000)
        
        metric = Metric(
            timestamp=datetime.now(),
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
        )
        
        self.metrics[name].append(metric)
    
    def get_metric(self, name: str, lookback_minutes: int = 60) -> List[Metric]:
        """Get recent metrics"""
        if name not in self.metrics:
            return []
        
        cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
        return [m for m in self.metrics[name] if m.timestamp > cutoff]
    
    def get_latest(self, name: str) -> Optional[Metric]:
        """Get latest metric value"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return self.metrics[name][-1]
    
    def get_statistics(self, name: str, lookback_minutes: int = 60) -> Dict[str, float]:
        """Get metric statistics"""
        metrics = self.get_metric(name, lookback_minutes)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'latest': values[-1],
        }


class AlertManager:
    """
    Manages alerts and notifications
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Alert storage
        self.alerts: deque = deque(maxlen=10000)
        
        # Alert rules
        self.rules: List[Dict[str, Any]] = []
        
        # Notification handlers
        self.handlers: Dict[AlertChannel, Callable] = {}
        
        # Rate limiting
        self.alert_counts: Dict[str, int] = {}
        self.rate_limit_window = self.config.get('rate_limit_window', 300)  # 5 minutes
        self.max_alerts_per_window = self.config.get('max_alerts_per_window', 10)
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        self.rules = [
            {
                'name': 'daily_loss_limit',
                'condition': lambda m: m.get('daily_pnl_pct', 0) < -0.02,
                'level': AlertLevel.CRITICAL,
                'category': 'risk',
                'title': 'Daily Loss Limit Breach',
                'message_template': 'Daily P&L ({daily_pnl_pct:.2%}) exceeds -2% limit',
            },
            {
                'name': 'drawdown_warning',
                'condition': lambda m: m.get('drawdown', 0) > 0.10,
                'level': AlertLevel.WARNING,
                'category': 'risk',
                'title': 'Drawdown Warning',
                'message_template': 'Drawdown ({drawdown:.2%}) exceeds 10%',
            },
            {
                'name': 'high_slippage',
                'condition': lambda m: m.get('avg_slippage_bps', 0) > 10,
                'level': AlertLevel.WARNING,
                'category': 'execution',
                'title': 'High Slippage',
                'message_template': 'Average slippage ({avg_slippage_bps:.1f} bps) is high',
            },
            {
                'name': 'model_degradation',
                'condition': lambda m: m.get('model_accuracy', 1) < 0.5,
                'level': AlertLevel.ERROR,
                'category': 'model',
                'title': 'Model Degradation',
                'message_template': 'Model accuracy ({model_accuracy:.2%}) below threshold',
            },
            {
                'name': 'high_latency',
                'condition': lambda m: m.get('latency_ms', 0) > 100,
                'level': AlertLevel.WARNING,
                'category': 'system',
                'title': 'High Latency',
                'message_template': 'System latency ({latency_ms:.0f}ms) is high',
            },
        ]
    
    def check_rules(self, metrics: Dict[str, Any]):
        """
        Check all alert rules against current metrics
        
        Args:
            metrics: Current metric values
        """
        for rule in self.rules:
            try:
                if rule['condition'](metrics):
                    self.create_alert(
                        level=rule['level'],
                        category=rule['category'],
                        title=rule['title'],
                        message=rule['message_template'].format(**metrics),
                        details=metrics,
                    )
            except Exception as e:
                logger.error(f"Error checking rule {rule['name']}: {e}")
    
    def create_alert(self, level: AlertLevel, category: str, title: str,
                    message: str, details: Dict[str, Any] = None,
                    channels: List[AlertChannel] = None):
        """
        Create and dispatch alert
        
        Args:
            level: Alert severity
            category: Alert category
            title: Alert title
            message: Alert message
            details: Additional details
            channels: Delivery channels
        """
        # Rate limiting
        alert_key = f"{category}:{title}"
        current_count = self.alert_counts.get(alert_key, 0)
        
        if current_count >= self.max_alerts_per_window:
            logger.debug(f"Alert rate limited: {alert_key}")
            return
        
        self.alert_counts[alert_key] = current_count + 1
        
        # Create alert
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            category=category,
            title=title,
            message=message,
            details=details or {},
            channels=channels or [AlertChannel.LOG],
        )
        
        self.alerts.append(alert)
        
        # Dispatch to handlers
        self._dispatch_alert(alert)
    
    def _dispatch_alert(self, alert: Alert):
        """Dispatch alert to configured channels"""
        for channel in alert.channels:
            if channel == AlertChannel.LOG:
                self._log_alert(alert)
            elif channel in self.handlers:
                try:
                    self.handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Error dispatching alert to {channel}: {e}")
    
    def _log_alert(self, alert: Alert):
        """Log alert"""
        log_msg = f"[{alert.level.value.upper()}] {alert.category}: {alert.title} - {alert.message}"
        
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        elif alert.level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def register_handler(self, channel: AlertChannel, handler: Callable):
        """Register alert handler for channel"""
        self.handlers[channel] = handler
    
    def get_alerts(self, level: AlertLevel = None, category: str = None,
                  lookback_hours: int = 24) -> List[Alert]:
        """Get recent alerts"""
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        alerts = [a for a in self.alerts if a.timestamp > cutoff]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        return alerts
    
    def acknowledge_alert(self, alert_index: int):
        """Acknowledge an alert"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].acknowledged = True


class PerformanceDashboard:
    """
    Real-time Performance Dashboard
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Components
        self.metrics_collector = MetricsCollector(config.get('metrics', {}))
        self.alert_manager = AlertManager(config.get('alerts', {}))
        
        # State history
        self.state_history: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        
        # Trade history
        self.trade_history: deque = deque(maxlen=10000)
        
        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # P&L tracking
        self.daily_pnl = 0
        self.peak_equity = 0
        self.current_equity = 0
    
    def update_equity(self, equity: float):
        """Update equity and calculate metrics"""
        self.current_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
        
        # Record metric
        self.metrics_collector.record(
            'equity', equity, MetricType.PERFORMANCE, 'USD'
        )
    
    def update_pnl(self, pnl: float):
        """Update P&L"""
        self.daily_pnl = pnl
        
        self.metrics_collector.record(
            'daily_pnl', pnl, MetricType.PERFORMANCE, 'USD'
        )
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record a trade"""
        self.trade_history.append({
            **trade,
            'timestamp': datetime.now(),
        })
        
        # Update metrics
        self.metrics_collector.record(
            'trade_pnl', trade.get('pnl', 0), MetricType.PERFORMANCE, 'USD'
        )
        self.metrics_collector.record(
            'slippage', trade.get('slippage_bps', 0), MetricType.EXECUTION, 'bps'
        )
    
    def update_position(self, symbol: str, position: Dict[str, Any]):
        """Update position"""
        self.positions[symbol] = {
            **position,
            'updated_at': datetime.now(),
        }
    
    def record_system_metrics(self, cpu: float, memory: float, latency: float):
        """Record system metrics"""
        self.metrics_collector.record('cpu_usage', cpu, MetricType.SYSTEM, '%')
        self.metrics_collector.record('memory_usage', memory, MetricType.SYSTEM, '%')
        self.metrics_collector.record('latency', latency, MetricType.SYSTEM, 'ms')
    
    def record_model_metrics(self, accuracy: float, signal_quality: float):
        """Record model metrics"""
        self.metrics_collector.record('model_accuracy', accuracy, MetricType.MODEL, '%')
        self.metrics_collector.record('signal_quality', signal_quality, MetricType.MODEL, 'score')
    
    def get_dashboard_state(self) -> DashboardState:
        """Get current dashboard state"""
        # Calculate drawdown
        drawdown = 0
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        
        # Get recent trades
        today = datetime.now().date()
        trades_today = [
            t for t in self.trade_history
            if t.get('timestamp', datetime.min).date() == today
        ]
        
        # Calculate slippage
        slippages = [t.get('slippage_bps', 0) for t in trades_today]
        avg_slippage = np.mean(slippages) if slippages else 0
        
        # Get system metrics
        cpu = self.metrics_collector.get_latest('cpu_usage')
        memory = self.metrics_collector.get_latest('memory_usage')
        latency = self.metrics_collector.get_latest('latency')
        
        # Get model metrics
        accuracy = self.metrics_collector.get_latest('model_accuracy')
        signal_quality = self.metrics_collector.get_latest('signal_quality')
        
        # Calculate exposure
        total_exposure = sum(
            abs(p.get('value', 0)) for p in self.positions.values()
        )
        net_exposure = sum(
            p.get('value', 0) * (1 if p.get('direction') == 'long' else -1)
            for p in self.positions.values()
        )
        
        state = DashboardState(
            timestamp=datetime.now(),
            daily_pnl=self.daily_pnl,
            weekly_pnl=0,  # Would calculate from history
            monthly_pnl=0,
            ytd_pnl=0,
            num_positions=len(self.positions),
            total_exposure=total_exposure,
            net_exposure=net_exposure,
            current_drawdown=drawdown,
            var_95=0,  # Would calculate
            sharpe_ratio=0,  # Would calculate
            trades_today=len(trades_today),
            avg_slippage_bps=avg_slippage,
            fill_rate=0.95,  # Would calculate
            cpu_usage=cpu.value if cpu else 0,
            memory_usage=memory.value if memory else 0,
            latency_ms=latency.value if latency else 0,
            model_accuracy=accuracy.value if accuracy else 0,
            signal_quality=signal_quality.value if signal_quality else 0,
        )
        
        self.state_history.append(state)
        
        # Check alert rules
        self.alert_manager.check_rules({
            'daily_pnl_pct': self.daily_pnl / self.current_equity if self.current_equity > 0 else 0,
            'drawdown': drawdown,
            'avg_slippage_bps': avg_slippage,
            'model_accuracy': accuracy.value if accuracy else 1,
            'latency_ms': latency.value if latency else 0,
        })
        
        return state
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary"""
        # Get trade history
        cutoff = datetime.now() - timedelta(days=days)
        recent_trades = [
            t for t in self.trade_history
            if t.get('timestamp', datetime.min) > cutoff
        ]
        
        if not recent_trades:
            return {'error': 'No trades in period'}
        
        pnls = [t.get('pnl', 0) for t in recent_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        return {
            'period_days': days,
            'total_trades': len(recent_trades),
            'total_pnl': sum(pnls),
            'win_rate': len(wins) / len(pnls) if pnls else 0,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'profit_factor': sum(wins) / abs(sum(losses)) if losses else float('inf'),
            'sharpe_ratio': np.mean(pnls) / np.std(pnls) * np.sqrt(252) if np.std(pnls) > 0 else 0,
        }


class AnomalyDetector:
    """
    Detects anomalies in trading metrics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Baseline statistics
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        # Anomaly history
        self.anomalies: deque = deque(maxlen=1000)
        
        # Z-score threshold
        self.z_threshold = self.config.get('z_threshold', 3.0)
    
    def update_baseline(self, metric_name: str, values: List[float]):
        """Update baseline statistics for metric"""
        if len(values) < 30:
            return
        
        self.baselines[metric_name] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
        }
    
    def check_anomaly(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        """
        Check if value is anomalous
        
        Args:
            metric_name: Name of metric
            value: Current value
            
        Returns:
            Anomaly details if detected, None otherwise
        """
        if metric_name not in self.baselines:
            return None
        
        baseline = self.baselines[metric_name]
        
        if baseline['std'] == 0:
            return None
        
        z_score = (value - baseline['mean']) / baseline['std']
        
        if abs(z_score) > self.z_threshold:
            anomaly = {
                'timestamp': datetime.now(),
                'metric': metric_name,
                'value': value,
                'z_score': z_score,
                'baseline_mean': baseline['mean'],
                'baseline_std': baseline['std'],
                'direction': 'high' if z_score > 0 else 'low',
            }
            
            self.anomalies.append(anomaly)
            
            return anomaly
        
        return None
    
    def get_recent_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.anomalies if a['timestamp'] > cutoff]


class MonitoringEngine:
    """
    Unified Monitoring Engine
    
    Integrates all monitoring components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.dashboard = PerformanceDashboard(config.get('dashboard', {}))
        self.anomaly_detector = AnomalyDetector(config.get('anomaly', {}))
        
        # Monitoring state
        self.is_running = False
        self.last_update = None
    
    def update(self, data: Dict[str, Any]):
        """
        Update monitoring with new data
        
        Args:
            data: Dictionary containing various metrics
        """
        # Update equity
        if 'equity' in data:
            self.dashboard.update_equity(data['equity'])
        
        # Update P&L
        if 'pnl' in data:
            self.dashboard.update_pnl(data['pnl'])
        
        # Record trade
        if 'trade' in data:
            self.dashboard.record_trade(data['trade'])
        
        # Update position
        if 'position' in data:
            self.dashboard.update_position(
                data['position']['symbol'],
                data['position']
            )
        
        # System metrics
        if all(k in data for k in ['cpu', 'memory', 'latency']):
            self.dashboard.record_system_metrics(
                data['cpu'], data['memory'], data['latency']
            )
        
        # Model metrics
        if 'model_accuracy' in data:
            self.dashboard.record_model_metrics(
                data['model_accuracy'],
                data.get('signal_quality', 0)
            )
        
        # Check for anomalies
        for metric_name, value in data.items():
            if isinstance(value, (int, float)):
                anomaly = self.anomaly_detector.check_anomaly(metric_name, value)
                if anomaly:
                    self.dashboard.alert_manager.create_alert(
                        level=AlertLevel.WARNING,
                        category='anomaly',
                        title=f'Anomaly Detected: {metric_name}',
                        message=f'{metric_name} value {value:.4f} is {anomaly["direction"]} (z-score: {anomaly["z_score"]:.2f})',
                        details=anomaly,
                    )
        
        self.last_update = datetime.now()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        state = self.dashboard.get_dashboard_state()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'is_running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'dashboard': {
                'daily_pnl': state.daily_pnl,
                'num_positions': state.num_positions,
                'drawdown': state.current_drawdown,
                'trades_today': state.trades_today,
            },
            'alerts': {
                'total': len(self.dashboard.alert_manager.alerts),
                'critical': len(self.dashboard.alert_manager.get_alerts(AlertLevel.CRITICAL)),
                'warnings': len(self.dashboard.alert_manager.get_alerts(AlertLevel.WARNING)),
            },
            'anomalies': len(self.anomaly_detector.get_recent_anomalies()),
        }
    
    def get_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get alerts"""
        return self.dashboard.alert_manager.get_alerts(level=level)
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary"""
        return self.dashboard.get_performance_summary(days)
