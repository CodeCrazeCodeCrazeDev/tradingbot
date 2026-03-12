"""
Phase 8: Production Deployment - Performance Monitoring
Real-time monitoring and alerting system
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    latency: float  # ms
    throughput: float  # trades/sec
    error_rate: float  # errors/sec
    success_rate: float  # successful trades %
    pnl: float  # profit/loss
    sharpe: float
    drawdown: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'latency': self.latency,
            'throughput': self.throughput,
            'error_rate': self.error_rate,
            'success_rate': self.success_rate,
            'pnl': self.pnl,
            'sharpe': self.sharpe,
            'drawdown': self.drawdown,
            'timestamp': self.timestamp
        }


class PerformanceMonitor:
    """
    Real-time performance monitoring system.
    Tracks metrics and generates alerts.
    """
    
    def __init__(
        self,
        metrics_dir: str = "metrics",
        alert_dir: str = "alerts"
    ):
        # Performance thresholds
        self.thresholds = {
            'latency': {
                'critical': 1000,  # ms
                'warning': 500
            },
            'error_rate': {
                'critical': 0.1,  # 10% errors
                'warning': 0.05
            },
            'success_rate': {
                'critical': 0.5,  # 50% success
                'warning': 0.7
            },
            'drawdown': {
                'critical': 0.2,  # 20% drawdown
                'warning': 0.1
            }
        }
        
        # Metrics storage
        self.metrics_dir = metrics_dir
        self.alert_dir = alert_dir
        os.makedirs(metrics_dir, exist_ok=True)
        os.makedirs(alert_dir, exist_ok=True)
        
        # Performance history
        self.history = []
        self.alerts = []
        
        # Current state
        self.is_healthy = True
        self.current_alerts = set()
        
        logger.info("✅ Performance Monitor initialized")
        logger.info(f"   Metrics dir: {metrics_dir}")
        logger.info(f"   Alert dir: {alert_dir}")
    
    def update_metrics(
        self,
        metrics: PerformanceMetrics
    ) -> List[Dict]:
        """
        Update performance metrics and check for alerts.
        
        Args:
            metrics: New performance metrics
        
        Returns:
            List of new alerts if any
        """
        # Add to history
        self.history.append(metrics)
        
        # Check for alerts
        new_alerts = self._check_alerts(metrics)
        
        # Update health status
        self.is_healthy = not any(
            alert['level'] == 'critical'
            for alert in new_alerts
        )
        
        # Save metrics
        self._save_metrics(metrics)
        
        # Save and return new alerts
        if new_alerts:
            self.alerts.extend(new_alerts)
            self._save_alerts(new_alerts)
        
        return new_alerts
    
    def _check_alerts(
        self,
        metrics: PerformanceMetrics
    ) -> List[Dict]:
        """Check for alert conditions."""
        new_alerts = []
        
        # Check latency
        if metrics.latency > self.thresholds['latency']['critical']:
            new_alerts.append(self._create_alert(
                'latency',
                'critical',
                f"High latency: {metrics.latency:.1f}ms"
            ))
        elif metrics.latency > self.thresholds['latency']['warning']:
            new_alerts.append(self._create_alert(
                'latency',
                'warning',
                f"Elevated latency: {metrics.latency:.1f}ms"
            ))
        
        # Check error rate
        if metrics.error_rate > self.thresholds['error_rate']['critical']:
            new_alerts.append(self._create_alert(
                'error_rate',
                'critical',
                f"High error rate: {metrics.error_rate:.1%}"
            ))
        elif metrics.error_rate > self.thresholds['error_rate']['warning']:
            new_alerts.append(self._create_alert(
                'error_rate',
                'warning',
                f"Elevated error rate: {metrics.error_rate:.1%}"
            ))
        
        # Check success rate
        if metrics.success_rate < self.thresholds['success_rate']['critical']:
            new_alerts.append(self._create_alert(
                'success_rate',
                'critical',
                f"Low success rate: {metrics.success_rate:.1%}"
            ))
        elif metrics.success_rate < self.thresholds['success_rate']['warning']:
            new_alerts.append(self._create_alert(
                'success_rate',
                'warning',
                f"Declining success rate: {metrics.success_rate:.1%}"
            ))
        
        # Check drawdown
        if metrics.drawdown > self.thresholds['drawdown']['critical']:
            new_alerts.append(self._create_alert(
                'drawdown',
                'critical',
                f"High drawdown: {metrics.drawdown:.1%}"
            ))
        elif metrics.drawdown > self.thresholds['drawdown']['warning']:
            new_alerts.append(self._create_alert(
                'drawdown',
                'warning',
                f"Significant drawdown: {metrics.drawdown:.1%}"
            ))
        
        return new_alerts
    
    def _create_alert(
        self,
        metric: str,
        level: str,
        message: str
    ) -> Dict:
        """Create alert dictionary."""
        alert_id = f"{metric}_{level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = {
            'id': alert_id,
            'metric': metric,
            'level': level,
            'message': message,
            'timestamp': datetime.now(),
            'acknowledged': False
        }
        
        # Add to current alerts
        self.current_alerts.add(alert_id)
        
        return alert
    
    def _save_metrics(self, metrics: PerformanceMetrics):
        """Save metrics to file."""
        date_str = metrics.timestamp.strftime('%Y%m%d')
        filepath = os.path.join(self.metrics_dir, f"metrics_{date_str}.json")
        
        # Convert to serializable format
        data = {
            k: str(v) if isinstance(v, datetime) else v
            for k, v in metrics.to_dict().items()
        }
        
        # Append to file
        with open(filepath, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def _save_alerts(self, alerts: List[Dict]):
        """Save alerts to file."""
        date_str = datetime.now().strftime('%Y%m%d')
        filepath = os.path.join(self.alert_dir, f"alerts_{date_str}.json")
        
        # Convert to serializable format
        data = [
            {
                k: str(v) if isinstance(v, datetime) else v
                for k, v in alert.items()
            }
            for alert in alerts
        ]
        
        # Append to file
        with open(filepath, 'a') as f:
            for alert in data:
                f.write(json.dumps(alert) + '\n')
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        if alert_id in self.current_alerts:
            # Find alert in history
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    break
            
            # Remove from current alerts
            self.current_alerts.remove(alert_id)
            
            logger.info(f"✅ Alert {alert_id} acknowledged")
    
    def get_current_alerts(
        self,
        level: Optional[str] = None
    ) -> List[Dict]:
        """Get current active alerts."""
        alerts = [
            alert for alert in self.alerts
            if alert['id'] in self.current_alerts
        ]
        
        if level:
            alerts = [
                alert for alert in alerts
                if alert['level'] == level
            ]
        
        return alerts
    
    def get_metrics_summary(
        self,
        window: timedelta = timedelta(hours=1)
    ) -> Dict:
        """
        Get summary of recent metrics.
        
        Args:
            window: Time window to analyze
        """
        if not self.history:
            return {}
        
        # Get recent metrics
        cutoff = datetime.now() - window
        recent = [
            m for m in self.history
            if m.timestamp > cutoff
        ]
        
        if not recent:
            return {}
        
        # Calculate statistics
        summary = {
            'latency': {
                'current': recent[-1].latency,
                'mean': np.mean([m.latency for m in recent]),
                'max': max(m.latency for m in recent),
                'min': min(m.latency for m in recent)
            },
            'throughput': {
                'current': recent[-1].throughput,
                'mean': np.mean([m.throughput for m in recent]),
                'total': sum(m.throughput for m in recent)
            },
            'error_rate': {
                'current': recent[-1].error_rate,
                'mean': np.mean([m.error_rate for m in recent])
            },
            'success_rate': {
                'current': recent[-1].success_rate,
                'mean': np.mean([m.success_rate for m in recent])
            },
            'pnl': {
                'current': recent[-1].pnl,
                'total': sum(m.pnl for m in recent)
            },
            'sharpe': recent[-1].sharpe,
            'drawdown': recent[-1].drawdown,
            'is_healthy': self.is_healthy,
            'active_alerts': len(self.current_alerts)
        }
        
        return summary
    
    def generate_report(self) -> str:
        """Generate performance report."""
        summary = self.get_metrics_summary()
        if not summary:
            return "No metrics available"
        
        report = [
            "PERFORMANCE REPORT",
            "=" * 50,
            f"\nSystem Health: {'✅ HEALTHY' if self.is_healthy else '❌ UNHEALTHY'}",
            f"Active Alerts: {summary['active_alerts']}",
            
            "\nPERFORMANCE METRICS:",
            f"Latency: {summary['latency']['current']:.1f}ms "
            f"(avg: {summary['latency']['mean']:.1f}ms)",
            f"Throughput: {summary['throughput']['current']:.1f} trades/sec "
            f"(avg: {summary['throughput']['mean']:.1f})",
            f"Error Rate: {summary['error_rate']['current']:.1%} "
            f"(avg: {summary['error_rate']['mean']:.1%})",
            f"Success Rate: {summary['success_rate']['current']:.1%} "
            f"(avg: {summary['success_rate']['mean']:.1%})",
            
            "\nTRADING METRICS:",
            f"Current P/L: ${summary['pnl']['current']:.2f}",
            f"Total P/L: ${summary['pnl']['total']:.2f}",
            f"Sharpe Ratio: {summary['sharpe']:.2f}",
            f"Max Drawdown: {summary['drawdown']:.1%}",
            
            "\nACTIVE ALERTS:"
        ]
        
        # Add active alerts
        alerts = self.get_current_alerts()
        if alerts:
            for alert in alerts:
                report.append(
                    f"- [{alert['level'].upper()}] {alert['message']}"
                )
        else:
            report.append("- No active alerts")
        
        return "\n".join(report)
    
    def save_state(self, filepath: str):
        """Save monitor state."""
        state = {
            'thresholds': self.thresholds,
            'history': [m.to_dict() for m in self.history],
            'alerts': self.alerts,
            'current_alerts': list(self.current_alerts),
            'is_healthy': self.is_healthy
        }
        torch.save(state, filepath)
        logger.info(f"💾 Performance Monitor state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load monitor state."""
        state = torch.load(filepath)
        
        self.thresholds = state['thresholds']
        self.history = [PerformanceMetrics(**m) for m in state['history']]
        self.alerts = state['alerts']
        self.current_alerts = set(state['current_alerts'])
        self.is_healthy = state['is_healthy']
        
        logger.info(f"📂 Performance Monitor state loaded from {filepath}")
        logger.info(f"   History samples: {len(self.history)}")
        logger.info(f"   Active alerts: {len(self.current_alerts)}")
