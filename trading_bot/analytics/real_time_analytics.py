"""
Real-Time Analytics Engine
==========================

Live performance tracking, metrics calculation, and alerting.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import deque
import numpy as np
import threading

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    acknowledged: bool = False


@dataclass
class PerformanceSnapshot:
    """Trading performance snapshot"""
    timestamp: datetime
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    exposure: float
    positions_count: int


class MetricsCollector:
    """Collects and stores metrics"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, float] = {}
        self._lock = threading.Lock()
        
    def record(self, name: str, value: float, tags: Optional[Dict] = None, metric_type: MetricType = MetricType.GAUGE):
        """Record a metric value"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_history)
                
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=metric_type
            )
            self._metrics[name].append(metric)
            
    def increment(self, name: str, value: float = 1.0):
        """Increment a counter"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            self._counters[name] += value
            
    def get_latest(self, name: str) -> Optional[Metric]:
        """Get latest value for a metric"""
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1]
            return None
            
    def get_history(self, name: str, limit: int = 100) -> List[Metric]:
        """Get metric history"""
        with self._lock:
            if name in self._metrics:
                return list(self._metrics[name])[-limit:]
            return []
            
    def get_stats(self, name: str, window_minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a metric over a time window"""
        with self._lock:
            if name not in self._metrics:
                return {}
                
            cutoff = datetime.now() - timedelta(minutes=window_minutes)
            values = [m.value for m in self._metrics[name] if m.timestamp > cutoff]
            
            if not values:
                return {}
                
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'median': np.median(values),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99)
            }
            
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        with self._lock:
            result = {}
            for name, history in self._metrics.items():
                if history:
                    result[name] = history[-1].value
            for name, value in self._counters.items():
                result[f"{name}_total"] = value
            return result


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self._rules: Dict[str, Dict] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=1000)
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
    def add_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,  # 'gt', 'lt', 'eq', 'gte', 'lte'
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        cooldown_minutes: int = 5
    ):
        """Add an alert rule"""
        self._rules[name] = {
            'metric_name': metric_name,
            'condition': condition,
            'threshold': threshold,
            'severity': severity,
            'cooldown_minutes': cooldown_minutes,
            'last_triggered': None
        }
        
    def remove_rule(self, name: str):
        """Remove an alert rule"""
        if name in self._rules:
            del self._rules[name]
            
    def check_metric(self, metric_name: str, value: float):
        """Check if metric triggers any alerts"""
        for rule_name, rule in self._rules.items():
            if rule['metric_name'] != metric_name:
                continue
                
            # Check cooldown
            if rule['last_triggered']:
                cooldown = timedelta(minutes=rule['cooldown_minutes'])
                if datetime.now() - rule['last_triggered'] < cooldown:
                    continue
                    
            # Check condition
            triggered = False
            condition = rule['condition']
            threshold = rule['threshold']
            
            if condition == 'gt' and value > threshold:
                triggered = True
            elif condition == 'lt' and value < threshold:
                triggered = True
            elif condition == 'eq' and value == threshold:
                triggered = True
            elif condition == 'gte' and value >= threshold:
                triggered = True
            elif condition == 'lte' and value <= threshold:
                triggered = True
                
            if triggered:
                self._trigger_alert(rule_name, rule, value)
                
    def _trigger_alert(self, rule_name: str, rule: Dict, value: float):
        """Trigger an alert"""
        import uuid
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            name=rule_name,
            severity=rule['severity'],
            message=f"{rule['metric_name']} {rule['condition']} {rule['threshold']} (current: {value})",
            metric_name=rule['metric_name'],
            current_value=value,
            threshold=rule['threshold'],
            timestamp=datetime.now()
        )
        
        with self._lock:
            self._active_alerts[alert.alert_id] = alert
            self._alert_history.append(alert)
            rule['last_triggered'] = datetime.now()
            
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
                
        logger.warning(f"Alert triggered: {alert.name} - {alert.message}")
        
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        with self._lock:
            if alert_id in self._active_alerts:
                self._active_alerts[alert_id].acknowledged = True
                
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self._lock:
            return list(self._active_alerts.values())
            
    def add_callback(self, callback: Callable):
        """Add alert callback"""
        self._callbacks.append(callback)


class RealTimeAnalytics:
    """
    Real-time analytics engine for trading performance.
    
    Features:
    - Live PnL tracking
    - Performance metrics calculation
    - Alert management
    - Historical analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        
        # Trading state
        self._trades: List[Dict] = []
        self._positions: Dict[str, Dict] = {}
        self._equity_curve: deque = deque(maxlen=10000)
        self._initial_capital = config.get('initial_capital', 100000)
        self._current_capital = self._initial_capital
        
        # Setup default alert rules
        self._setup_default_alerts()
        
        logger.info("RealTimeAnalytics initialized")
        
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # Drawdown alert
        self.alerts.add_rule(
            name='high_drawdown',
            metric_name='drawdown',
            condition='gt',
            threshold=0.1,  # 10%
            severity=AlertSeverity.WARNING
        )
        
        # Critical drawdown
        self.alerts.add_rule(
            name='critical_drawdown',
            metric_name='drawdown',
            condition='gt',
            threshold=0.2,  # 20%
            severity=AlertSeverity.CRITICAL
        )
        
        # Win rate alert
        self.alerts.add_rule(
            name='low_win_rate',
            metric_name='win_rate',
            condition='lt',
            threshold=0.4,  # 40%
            severity=AlertSeverity.WARNING
        )
        
        # Exposure alert
        self.alerts.add_rule(
            name='high_exposure',
            metric_name='exposure',
            condition='gt',
            threshold=0.8,  # 80%
            severity=AlertSeverity.WARNING
        )
        
    def record_trade(self, trade: Dict):
        """Record a completed trade"""
        self._trades.append({
            **trade,
            'timestamp': datetime.now()
        })
        
        # Update metrics
        pnl = trade.get('pnl', 0)
        self._current_capital += pnl
        
        self.metrics.record('trade_pnl', pnl)
        self.metrics.increment('total_trades')
        
        if pnl > 0:
            self.metrics.increment('winning_trades')
        else:
            self.metrics.increment('losing_trades')
            
        # Update equity curve
        self._equity_curve.append({
            'timestamp': datetime.now(),
            'equity': self._current_capital
        })
        
        # Calculate and record metrics
        self._update_performance_metrics()
        
    def update_position(self, symbol: str, position: Dict):
        """Update position information"""
        self._positions[symbol] = {
            **position,
            'updated_at': datetime.now()
        }
        
        # Calculate exposure
        total_exposure = sum(
            abs(p.get('value', 0)) for p in self._positions.values()
        )
        exposure_ratio = total_exposure / self._current_capital if self._current_capital > 0 else 0
        
        self.metrics.record('exposure', exposure_ratio)
        self.alerts.check_metric('exposure', exposure_ratio)
        
    def close_position(self, symbol: str):
        """Close a position"""
        if symbol in self._positions:
            del self._positions[symbol]
            
    def _update_performance_metrics(self):
        """Update all performance metrics"""
        if not self._trades:
            return
            
        # Calculate metrics
        pnls = [t.get('pnl', 0) for t in self._trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p <= 0]
        
        # Win rate
        win_rate = len(winning) / len(pnls) if pnls else 0
        self.metrics.record('win_rate', win_rate)
        self.alerts.check_metric('win_rate', win_rate)
        
        # Average win/loss
        avg_win = np.mean(winning) if winning else 0
        avg_loss = np.mean(losing) if losing else 0
        self.metrics.record('avg_win', avg_win)
        self.metrics.record('avg_loss', abs(avg_loss))
        
        # Profit factor
        gross_profit = sum(winning)
        gross_loss = abs(sum(losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        self.metrics.record('profit_factor', profit_factor)
        
        # Total PnL
        total_pnl = sum(pnls)
        self.metrics.record('total_pnl', total_pnl)
        
        # Return
        total_return = (self._current_capital - self._initial_capital) / self._initial_capital
        self.metrics.record('total_return', total_return)
        
        # Drawdown
        if self._equity_curve:
            equities = [e['equity'] for e in self._equity_curve]
            peak = max(equities)
            current = equities[-1]
            drawdown = (peak - current) / peak if peak > 0 else 0
            self.metrics.record('drawdown', drawdown)
            self.alerts.check_metric('drawdown', drawdown)
            
            # Max drawdown
            max_dd = 0
            peak = equities[0]
            for eq in equities:
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak
                max_dd = max(max_dd, dd)
            self.metrics.record('max_drawdown', max_dd)
            
        # Sharpe ratio (simplified)
        if len(pnls) > 1:
            returns = np.array(pnls) / self._initial_capital
            sharpe = np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            self.metrics.record('sharpe_ratio', sharpe)
            
    def get_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        metrics = self.metrics.get_all_metrics()
        
        # Calculate unrealized PnL
        unrealized_pnl = sum(
            p.get('unrealized_pnl', 0) for p in self._positions.values()
        )
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            total_pnl=metrics.get('total_pnl', 0),
            realized_pnl=metrics.get('total_pnl', 0),
            unrealized_pnl=unrealized_pnl,
            win_rate=metrics.get('win_rate', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            max_drawdown=metrics.get('max_drawdown', 0),
            total_trades=int(metrics.get('total_trades_total', 0)),
            winning_trades=int(metrics.get('winning_trades_total', 0)),
            losing_trades=int(metrics.get('losing_trades_total', 0)),
            avg_win=metrics.get('avg_win', 0),
            avg_loss=metrics.get('avg_loss', 0),
            profit_factor=metrics.get('profit_factor', 0),
            exposure=metrics.get('exposure', 0),
            positions_count=len(self._positions)
        )
        
    def get_equity_curve(self) -> List[Dict]:
        """Get equity curve data"""
        return list(self._equity_curve)
        
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        return self._trades[-limit:]
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        snapshot = self.get_snapshot()
        
        return {
            'snapshot': {
                'total_pnl': snapshot.total_pnl,
                'win_rate': snapshot.win_rate,
                'sharpe_ratio': snapshot.sharpe_ratio,
                'max_drawdown': snapshot.max_drawdown,
                'total_trades': snapshot.total_trades,
                'profit_factor': snapshot.profit_factor,
                'exposure': snapshot.exposure
            },
            'equity_curve': self.get_equity_curve()[-100:],
            'recent_trades': self.get_trade_history(10),
            'active_alerts': [
                {
                    'name': a.name,
                    'severity': a.severity.value,
                    'message': a.message,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in self.alerts.get_active_alerts()
            ],
            'positions': list(self._positions.values()),
            'metrics': self.metrics.get_all_metrics()
        }


def create_analytics(config: Optional[Dict] = None) -> RealTimeAnalytics:
    """Factory function to create analytics engine"""
    return RealTimeAnalytics(config)


if __name__ == "__main__":
    # Demo
    analytics = create_analytics({'initial_capital': 100000})
    
    # Simulate some trades
    import random
    
    for i in range(20):
        pnl = random.uniform(-500, 800)
        analytics.record_trade({
            'symbol': 'EURUSD',
            'direction': 'long' if random.random() > 0.5 else 'short',
            'entry_price': 1.1000,
            'exit_price': 1.1000 + pnl/10000,
            'quantity': 10000,
            'pnl': pnl
        })
        
    # Get snapshot
    snapshot = analytics.get_snapshot()
    print("\n=== Performance Snapshot ===")
    print(f"Total PnL: ${snapshot.total_pnl:,.2f}")
    print(f"Win Rate: {snapshot.win_rate:.1%}")
    print(f"Profit Factor: {snapshot.profit_factor:.2f}")
    print(f"Max Drawdown: {snapshot.max_drawdown:.1%}")
    print(f"Total Trades: {snapshot.total_trades}")
    
    # Check alerts
    alerts = analytics.alerts.get_active_alerts()
    if alerts:
        print(f"\n=== Active Alerts ({len(alerts)}) ===")
        for alert in alerts:
            print(f"  [{alert.severity.value}] {alert.name}: {alert.message}")
