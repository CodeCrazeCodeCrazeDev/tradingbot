"""
Monitoring System - Comprehensive monitoring and feedback loop

This module provides a unified monitoring system for tracking performance,
system health, and providing feedback for continuous improvement.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
import threading
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Tracks trading performance metrics"""
    
    def __init__(self):
        self.trades = []
        self.daily_pnl = {}
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'total_pnl': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'recovery_factor': 0.0,
            'expectancy': 0.0
        }
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """
        Add a trade to the performance metrics
        
        Args:
            trade: Trade information including symbol, entry_price, exit_price,
                  quantity, entry_time, exit_time, pnl, etc.
        """
        self.trades.append(trade)
        
        # Update daily P&L
        date_str = trade['exit_time'].strftime('%Y-%m-%d')
        if date_str not in self.daily_pnl:
            self.daily_pnl[date_str] = 0.0
        self.daily_pnl[date_str] += trade['pnl']
        
        # Update metrics
        self._calculate_metrics()
    
    def _calculate_metrics(self) -> None:
        """Calculate performance metrics from trades"""
        if not self.trades:
            return
        
        # Basic metrics
        self.metrics['total_trades'] = len(self.trades)
        self.metrics['winning_trades'] = sum(1 for t in self.trades if t['pnl'] > 0)
        self.metrics['losing_trades'] = sum(1 for t in self.trades if t['pnl'] <= 0)
        
        # Win rate
        if self.metrics['total_trades'] > 0:
            self.metrics['win_rate'] = self.metrics['winning_trades'] / self.metrics['total_trades']
        
        # P&L metrics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        self.metrics['total_pnl'] = sum(t['pnl'] for t in self.trades)
        
        # Average win/loss
        if winning_trades:
            self.metrics['average_win'] = gross_profit / len(winning_trades)
            self.metrics['largest_win'] = max(t['pnl'] for t in winning_trades)
        
        if losing_trades:
            self.metrics['average_loss'] = gross_loss / len(losing_trades)
            self.metrics['largest_loss'] = abs(min(t['pnl'] for t in losing_trades))
        
        # Profit factor
        if gross_loss > 0:
            self.metrics['profit_factor'] = gross_profit / gross_loss
        
        # Expectancy
        if self.metrics['total_trades'] > 0:
            self.metrics['expectancy'] = self.metrics['total_pnl'] / self.metrics['total_trades']
        
        # Calculate drawdown
        equity_curve = self._calculate_equity_curve()
        max_dd, max_dd_pct = self._calculate_drawdown(equity_curve)
        self.metrics['max_drawdown'] = max_dd
        self.metrics['max_drawdown_pct'] = max_dd_pct
        
        # Recovery factor
        if max_dd > 0:
            self.metrics['recovery_factor'] = self.metrics['total_pnl'] / max_dd
        
        # Calculate Sharpe and Sortino ratios
        daily_returns = self._calculate_daily_returns()
        if len(daily_returns) > 1:
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            
            if std_return > 0:
                self.metrics['sharpe_ratio'] = (avg_return / std_return) * np.sqrt(252)
            
            # Sortino ratio (downside deviation)
            negative_returns = [r for r in daily_returns if r < 0]
            if negative_returns:
                downside_deviation = np.std(negative_returns)
                if downside_deviation > 0:
                    self.metrics['sortino_ratio'] = (avg_return / downside_deviation) * np.sqrt(252)
    
    def _calculate_equity_curve(self) -> List[float]:
        """Calculate equity curve from trades"""
        equity = [0.0]
        
        for trade in sorted(self.trades, key=lambda t: t['exit_time']):
            equity.append(equity[-1] + trade['pnl'])
        
        return equity
    
    def _calculate_drawdown(self, equity_curve: List[float]) -> Tuple[float, float]:
        """Calculate maximum drawdown and drawdown percentage"""
        max_dd = 0.0
        max_dd_pct = 0.0
        peak = equity_curve[0]
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = (dd / peak) if peak > 0 else 0.0
        
        return max_dd, max_dd_pct
    
    def _calculate_daily_returns(self) -> List[float]:
        """Calculate daily returns from daily P&L"""
        if not self.daily_pnl:
            return []
        
        # Sort daily P&L by date
        sorted_pnl = sorted(self.daily_pnl.items())
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(sorted_pnl)):
            prev_date, prev_pnl = sorted_pnl[i-1]
            curr_date, curr_pnl = sorted_pnl[i]
            
            daily_returns.append(curr_pnl)
        
        return daily_returns
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics
    
    def get_daily_pnl(self) -> Dict[str, float]:
        """Get daily P&L"""
        return self.daily_pnl
    
    def get_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades"""
        return sorted(self.trades, key=lambda t: t['exit_time'], reverse=True)[:limit]


class SystemHealthMonitor:
    """Monitors system health and resource usage"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Component status
        self.components = {
            'data_feed': {'status': 'unknown', 'last_update': None, 'details': {}},
            'analysis': {'status': 'unknown', 'last_update': None, 'details': {}},
            'execution': {'status': 'unknown', 'last_update': None, 'details': {}},
            'risk_management': {'status': 'unknown', 'last_update': None, 'details': {}},
            'database': {'status': 'unknown', 'last_update': None, 'details': {}}
        }
        
        # Resource usage
        self.resources = {
            'cpu': {'usage': 0.0, 'limit': self.config.get('cpu_limit', 80.0)},
            'memory': {'usage': 0.0, 'limit': self.config.get('memory_limit', 80.0)},
            'disk': {'usage': 0.0, 'limit': self.config.get('disk_limit', 80.0)},
            'network': {'tx_bytes': 0, 'rx_bytes': 0, 'errors': 0}
        }
        
        # Error tracking
        self.errors = deque(maxlen=100)
        
        # Start monitoring thread
        self.stop_event = threading.Event()
        self.monitor_thread = None
        
        # Thresholds
        self.thresholds = self.config.get('thresholds', {
            'latency_ms': 100,
            'error_rate': 0.01,
            'data_delay_sec': 5
        })
    
    def start(self) -> None:
        """Start system health monitoring"""
        if self.monitor_thread is not None:
            return
        
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("System health monitoring started")
    
    def stop(self) -> None:
        """Stop system health monitoring"""
        if self.monitor_thread is None:
            return
        
        self.stop_event.set()
        self.monitor_thread.join(timeout=5)
        self.monitor_thread = None
        
        logger.info("System health monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Background thread for system monitoring"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, resource monitoring limited")
            psutil = None
        
        while not self.stop_event.is_set():
            try:
                # Update resource usage
                if psutil:
                    # CPU usage
                    self.resources['cpu']['usage'] = psutil.cpu_percent(interval=None)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.resources['memory']['usage'] = memory.percent
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    self.resources['disk']['usage'] = disk.percent
                    
                    # Network usage
                    net_io = psutil.net_io_counters()
                    self.resources['network']['tx_bytes'] = net_io.bytes_sent
                    self.resources['network']['rx_bytes'] = net_io.bytes_recv
                
                # Check component health
                self._check_component_health()
                
                # Check resource thresholds
                self._check_resource_thresholds()
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
            
            # Sleep until next check
            self.stop_event.wait(self.config.get('monitor_interval', 5))
    
    def _check_component_health(self) -> None:
        """Check health of system components"""
        # This would normally query each component for its status
        # For now, we'll just update timestamps
        for component in self.components:
            if self.components[component]['status'] != 'error':
                self.components[component]['last_update'] = datetime.now()
    
    def _check_resource_thresholds(self) -> None:
        """Check if resource usage exceeds thresholds"""
        # Check CPU usage
        if self.resources['cpu']['usage'] > self.resources['cpu']['limit']:
            self.add_error('system', 'high_cpu_usage', 
                          f"CPU usage ({self.resources['cpu']['usage']}%) exceeds limit ({self.resources['cpu']['limit']}%)")
        
        # Check memory usage
        if self.resources['memory']['usage'] > self.resources['memory']['limit']:
            self.add_error('system', 'high_memory_usage', 
                          f"Memory usage ({self.resources['memory']['usage']}%) exceeds limit ({self.resources['memory']['limit']}%)")
        
        # Check disk usage
        if self.resources['disk']['usage'] > self.resources['disk']['limit']:
            self.add_error('system', 'high_disk_usage', 
                          f"Disk usage ({self.resources['disk']['usage']}%) exceeds limit ({self.resources['disk']['limit']}%)")
    
    def update_component_status(self, component: str, status: str, 
                              details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update status of a system component
        
        Args:
            component: Component name
            status: Status ('ok', 'warning', 'error', 'unknown')
            details: Additional status details
        """
        if component not in self.components:
            self.components[component] = {'status': 'unknown', 'last_update': None, 'details': {}}
        
        self.components[component]['status'] = status
        self.components[component]['last_update'] = datetime.now()
        
        if details:
            self.components[component]['details'].update(details)
    
    def add_error(self, component: str, error_type: str, message: str) -> None:
        """
        Add an error to the error log
        
        Args:
            component: Component that generated the error
            error_type: Type of error
            message: Error message
        """
        error = {
            'timestamp': datetime.now(),
            'component': component,
            'type': error_type,
            'message': message
        }
        
        self.errors.append(error)
        logger.error(f"{component} error: {message}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Determine overall status
        component_statuses = [c['status'] for c in self.components.values()]
        
        if 'error' in component_statuses:
            overall_status = 'error'
        elif 'warning' in component_statuses:
            overall_status = 'warning'
        elif all(s == 'ok' for s in component_statuses):
            overall_status = 'ok'
        else:
            overall_status = 'unknown'
        
        # Count errors in last hour
        now = datetime.now()
        recent_errors = [e for e in self.errors if (now - e['timestamp']).total_seconds() < 3600]
        
        return {
            'status': overall_status,
            'components': self.components,
            'resources': self.resources,
            'error_count': len(recent_errors),
            'last_update': datetime.now()
        }
    
    def get_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent errors"""
        return list(self.errors)[-limit:]


class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Alert storage
        self.alerts = deque(maxlen=1000)
        
        # Alert levels
        self.levels = {
            'critical': {'color': '#dc3545', 'priority': 1},
            'warning': {'color': '#ffc107', 'priority': 2},
            'info': {'color': '#17a2b8', 'priority': 3}
        }
        
        # Notification channels
        self.channels = self.config.get('channels', ['console'])
        
        logger.info("Alert manager initialized")
    
    def add_alert(self, level: str, component: str, message: str, 
                details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new alert
        
        Args:
            level: Alert level ('critical', 'warning', 'info')
            component: Component that generated the alert
            message: Alert message
            details: Additional alert details
            
        Returns:
            The created alert
        """
        if level not in self.levels:
            level = 'info'
        
        alert = {
            'id': f"alert_{int(time.time())}_{len(self.alerts)}",
            'timestamp': datetime.now(),
            'level': level,
            'component': component,
            'message': message,
            'details': details or {},
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.info(f"Alert added: [{level}] {component} - {message}")
        return alert
    
    def _send_notifications(self, alert: Dict[str, Any]) -> None:
        """
        Send notifications for an alert
        
        Args:
            alert: Alert to send notifications for
        """
        # Only send notifications for critical and warning alerts
        if alert['level'] == 'info':
            return
        
        for channel in self.channels:
            if channel == 'console':
                logger.warning(f"ALERT: [{alert['level']}] {alert['component']} - {alert['message']}")
            elif channel == 'email':
                self._send_email_alert(alert)
            elif channel == 'sms':
                self._send_sms_alert(alert)
    
    def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """Send email notification for an alert"""
        # This would normally send an email
        # For now, just log it
        logger.info(f"Would send email alert: {alert['message']}")
    
    def _send_sms_alert(self, alert: Dict[str, Any]) -> None:
        """Send SMS notification for an alert"""
        # This would normally send an SMS
        # For now, just log it
        logger.info(f"Would send SMS alert: {alert['message']}")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            True if alert was acknowledged
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now()
                return True
        
        return False
    
    def get_alerts(self, level: Optional[str] = None, 
                 acknowledged: Optional[bool] = None,
                 limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get alerts filtered by level and acknowledgement status
        
        Args:
            level: Filter by alert level
            acknowledged: Filter by acknowledgement status
            limit: Maximum number of alerts to return
            
        Returns:
            List of matching alerts
        """
        result = list(self.alerts)
        
        if level:
            result = [a for a in result if a['level'] == level]
        
        if acknowledged is not None:
            result = [a for a in result if a['acknowledged'] == acknowledged]
        
        # Sort by timestamp (newest first)
        result.sort(key=lambda a: a['timestamp'], reverse=True)
        
        return result[:limit]


class MonitoringSystem:
    """
    Comprehensive monitoring system that integrates performance tracking,
    system health monitoring, and alerting.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.performance = PerformanceMetrics()
        self.health = SystemHealthMonitor(self.config.get('health', {}))
        self.alerts = AlertManager(self.config.get('alerts', {}))
        
        # Start health monitoring
        self.health.start()
        
        logger.info("Monitoring system initialized")
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """
        Add a trade to performance metrics
        
        Args:
            trade: Trade information
        """
        self.performance.add_trade(trade)
        
        # Check for notable trades
        if trade['pnl'] > 0 and trade['pnl'] > self.performance.metrics.get('average_win', 0) * 2:
            self.alerts.add_alert('info', 'trading', f"Large winning trade: {trade['symbol']} ({trade['pnl']})",
                                details={'trade': trade})
        elif trade['pnl'] < 0 and abs(trade['pnl']) > self.performance.metrics.get('average_loss', 0) * 2:
            self.alerts.add_alert('warning', 'trading', f"Large losing trade: {trade['symbol']} ({trade['pnl']})",
                                details={'trade': trade})
    
    def update_component_status(self, component: str, status: str, 
                              details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update status of a system component
        
        Args:
            component: Component name
            status: Status ('ok', 'warning', 'error', 'unknown')
            details: Additional status details
        """
        self.health.update_component_status(component, status, details)
        
        # Generate alerts for warning/error status
        if status == 'warning':
            self.alerts.add_alert('warning', component, f"{component} status: {status}",
                                details=details)
        elif status == 'error':
            self.alerts.add_alert('critical', component, f"{component} status: {status}",
                                details=details)
    
    def add_error(self, component: str, error_type: str, message: str) -> None:
        """
        Add an error to the error log
        
        Args:
            component: Component that generated the error
            error_type: Type of error
            message: Error message
        """
        self.health.add_error(component, error_type, message)
        
        # Generate alert for error
        self.alerts.add_alert('warning', component, f"Error: {message}",
                            details={'type': error_type})
    
    def add_alert(self, level: str, component: str, message: str, 
                details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new alert
        
        Args:
            level: Alert level ('critical', 'warning', 'info')
            component: Component that generated the alert
            message: Alert message
            details: Additional alert details
            
        Returns:
            The created alert
        """
        return self.alerts.add_alert(level, component, message, details)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data for dashboard
        
        Returns:
            Dictionary with performance metrics, system status, and alerts
        """
        return {
            'performance': {
                'metrics': self.performance.get_metrics(),
                'daily_pnl': self.performance.get_daily_pnl(),
                'recent_trades': self.performance.get_trades(10)
            },
            'system': self.health.get_system_status(),
            'alerts': self.alerts.get_alerts(limit=10)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance.get_metrics()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return self.health.get_system_status()
    
    def get_alerts(self, level: Optional[str] = None, 
                 acknowledged: Optional[bool] = None,
                 limit: int = 50) -> List[Dict[str, Any]]:
        """Get alerts"""
        return self.alerts.get_alerts(level, acknowledged, limit)
    
    def shutdown(self) -> None:
        """Shutdown monitoring system"""
        self.health.stop()
        logger.info("Monitoring system shutdown")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create monitoring system
    monitoring = MonitoringSystem()
    
    # Add some sample trades
    monitoring.add_trade({
        'symbol': 'EURUSD',
        'entry_price': 1.1000,
        'exit_price': 1.1050,
        'quantity': 1.0,
        'entry_time': datetime.now() - timedelta(hours=2),
        'exit_time': datetime.now() - timedelta(hours=1),
        'pnl': 50.0,
        'commission': 1.0,
        'strategy': 'trend_following'
    })
    
    monitoring.add_trade({
        'symbol': 'GBPUSD',
        'entry_price': 1.2500,
        'exit_price': 1.2450,
        'quantity': 1.0,
        'entry_time': datetime.now() - timedelta(hours=1),
        'exit_time': datetime.now() - timedelta(minutes=30),
        'pnl': -50.0,
        'commission': 1.0,
        'strategy': 'breakout'
    })
    
    # Update component status
    monitoring.update_component_status('data_feed', 'ok', {'latency_ms': 15})
    monitoring.update_component_status('analysis', 'ok', {'processing_time_ms': 25})
    monitoring.update_component_status('execution', 'warning', {'latency_ms': 120})
    
    # Add an error
    monitoring.add_error('execution', 'high_latency', 'Execution latency exceeds threshold')
    
    # Get dashboard data
    dashboard_data = monitoring.get_dashboard_data()
    
    # Print some information
    logger.info("Performance Metrics:")
    for key, value in dashboard_data['performance']['metrics'].items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\nSystem Status:")
    logger.info(f"  Overall: {dashboard_data['system']['status']}")
    for component, status in dashboard_data['system']['components'].items():
        logger.info(f"  {component}: {status['status']}")
    
    logger.info("\nAlerts:")
    for alert in dashboard_data['alerts']:
        logger.info(f"  [{alert['level']}] {alert['component']}: {alert['message']}")
    
    # Shutdown
    monitoring.shutdown()
