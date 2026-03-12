"""
REAL-TIME PERFORMANCE MONITOR
============================================================

Monitors trading system performance in real-time.

Features:
- Live trade tracking
- Real-time metrics calculation
- Performance alerts
- Risk monitoring
- System health checks

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import threading
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceAlert:
    """Performance alert."""
    alert_type: str  # WARNING, CRITICAL, INFO
    message: str
    timestamp: datetime
    metric: str
    value: float
    threshold: float


class RealTimePerformanceMonitor:
    """Monitors trading system performance in real-time."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize real-time monitor.
        
        Args:
            check_interval: Check interval in seconds
        """
        self.check_interval = check_interval
        self.is_running = False
        self.monitor_thread = None
        
        # Performance data
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.profit_today = 0.0
        self.drawdown_today = 0.0
        self.max_drawdown_today = 0.0
        
        # Alerts
        self.alerts: List[PerformanceAlert] = []
        
        # Thresholds
        self.thresholds = {
            'max_daily_loss': -500.0,
            'max_drawdown': 0.08,
            'min_win_rate': 0.55,
            'max_consecutive_losses': 5,
            'max_open_trades': 10
        }
        
        logger.info(f"Real-Time Performance Monitor initialized (interval: {check_interval}s)")
    
    def start(self):
        """Start monitoring."""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("✓ Real-time monitor started")
    
    def stop(self):
        """Stop monitoring."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("✓ Real-time monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self._check_performance()
                self._check_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
    
    def _check_performance(self):
        """Check current performance."""
        # This would be connected to live trading data
        logger.debug("Checking performance metrics...")
    
    def _check_alerts(self):
        """Check for alert conditions."""
        # Daily loss check
        if self.profit_today < self.thresholds['max_daily_loss']:
            self._add_alert(
                "CRITICAL",
                f"Daily loss limit exceeded: ${self.profit_today:,.2f}",
                "daily_loss",
                self.profit_today,
                self.thresholds['max_daily_loss']
            )
        
        # Drawdown check
        if self.drawdown_today > self.thresholds['max_drawdown']:
            self._add_alert(
                "WARNING",
                f"Drawdown exceeded: {self.drawdown_today:.1%}",
                "drawdown",
                self.drawdown_today,
                self.thresholds['max_drawdown']
            )
    
    def _add_alert(self, alert_type: str, message: str, metric: str,
                  value: float, threshold: float):
        """Add performance alert."""
        alert = PerformanceAlert(
            alert_type=alert_type,
            message=message,
            timestamp=datetime.now(),
            metric=metric,
            value=value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        # Log alert
        if alert_type == "CRITICAL":
            logger.critical(f"🚨 {message}")
        elif alert_type == "WARNING":
            logger.warning(f"⚠️ {message}")
        else:
            logger.info(f"ℹ️ {message}")
    
    def record_trade(self, symbol: str, direction: str, entry_price: float,
                    position_size: float, profit: float):
        """Record a trade."""
        self.trades_today += 1
        
        if profit > 0:
            self.wins_today += 1
        else:
            self.losses_today += 1
        
        self.profit_today += profit
        
        logger.info(f"Trade recorded: {symbol} {direction} | Profit: ${profit:,.2f}")
    
    def update_drawdown(self, drawdown: float):
        """Update current drawdown."""
        self.drawdown_today = drawdown
        
        if drawdown > self.max_drawdown_today:
            self.max_drawdown_today = drawdown
    
    def get_status_report(self) -> str:
        """Get real-time status report."""
        win_rate = self.wins_today / self.trades_today if self.trades_today > 0 else 0
        
        report = "\n" + "="*70 + "\n"
        report += "REAL-TIME PERFORMANCE STATUS\n"
        report += "="*70 + "\n\n"
        
        report += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "TODAY'S PERFORMANCE:\n"
        report += f"  Trades: {self.trades_today}\n"
        report += f"  Wins: {self.wins_today}\n"
        report += f"  Losses: {self.losses_today}\n"
        report += f"  Win Rate: {win_rate:.1%}\n"
        report += f"  Total Profit: ${self.profit_today:,.2f}\n\n"
        
        report += "RISK METRICS:\n"
        report += f"  Current Drawdown: {self.drawdown_today:.1%}\n"
        report += f"  Max Drawdown Today: {self.max_drawdown_today:.1%}\n\n"
        
        report += "ALERTS:\n"
        if self.alerts:
            for alert in self.alerts[-10:]:  # Last 10 alerts
                report += f"  [{alert.alert_type}] {alert.timestamp.strftime('%H:%M:%S')} - {alert.message}\n"
        else:
            report += "  No alerts\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report
    
    def get_health_check(self) -> Dict[str, bool]:
        """Get system health check."""
        health = {
            'daily_loss_ok': self.profit_today >= self.thresholds['max_daily_loss'],
            'drawdown_ok': self.drawdown_today <= self.thresholds['max_drawdown'],
            'win_rate_ok': (self.wins_today / self.trades_today if self.trades_today > 0 else 1) >= self.thresholds['min_win_rate'],
            'system_running': self.is_running
        }
        
        return health


class PerformanceDashboard:
    """Performance dashboard for monitoring."""
    
    def __init__(self, monitor: RealTimePerformanceMonitor):
        """Initialize dashboard."""
        self.monitor = monitor
        self.last_update = datetime.now()
    
    def display_dashboard(self):
        """Display performance dashboard."""
        dashboard = "\n" + "╔" + "="*68 + "╗\n"
        dashboard += "║" + " "*15 + "TRADING SYSTEM PERFORMANCE DASHBOARD" + " "*18 + "║\n"
        dashboard += "╠" + "="*68 + "╣\n"
        
        # Performance metrics
        win_rate = self.monitor.wins_today / self.monitor.trades_today if self.monitor.trades_today > 0 else 0
        
        dashboard += f"║ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " "*38 + "║\n"
        dashboard += "║" + "-"*68 + "║\n"
        
        dashboard += f"║ Trades Today: {self.monitor.trades_today:3d} | Wins: {self.monitor.wins_today:3d} | Losses: {self.monitor.losses_today:3d} | Win Rate: {win_rate:5.1%}" + " "*15 + "║\n"
        dashboard += f"║ Daily Profit: ${self.monitor.profit_today:10,.2f} | Drawdown: {self.monitor.drawdown_today:5.1%} | Max DD: {self.monitor.max_drawdown_today:5.1%}" + " "*8 + "║\n"
        dashboard += "║" + "-"*68 + "║\n"
        
        # Health status
        health = self.monitor.get_health_check()
        dashboard += "║ SYSTEM HEALTH:                                                    ║\n"
        
        for check, status in health.items():
            status_icon = "✓" if status else "✗"
            dashboard += f"║   {status_icon} {check.replace('_', ' ').title():40s} {'GOOD' if status else 'ALERT':20s} ║\n"
        
        dashboard += "║" + "-"*68 + "║\n"
        
        # Recent alerts
        dashboard += "║ RECENT ALERTS:                                                    ║\n"
        
        if self.monitor.alerts:
            for alert in self.monitor.alerts[-3:]:
                alert_icon = "🚨" if alert.alert_type == "CRITICAL" else "⚠️" if alert.alert_type == "WARNING" else "ℹ️"
                msg = alert.message[:55]
                dashboard += f"║   {alert_icon} {msg:55s} ║\n"
        else:
            dashboard += "║   No alerts                                                        ║\n"
        
        dashboard += "╚" + "="*68 + "╝\n"
        
        return dashboard


def main():
    """Main execution."""
    logger.info("Starting Real-Time Performance Monitor")
    
    try:
        # Initialize monitor
        monitor = RealTimePerformanceMonitor(check_interval=30)
        monitor.start()
        
        # Initialize dashboard
        dashboard = PerformanceDashboard(monitor)
        
        # Simulate trading
        logger.info("Simulating trades...")
        
        monitor.record_trade("EURUSD", "LONG", 1.0800, 0.25, 50.0)
        monitor.record_trade("EURUSD", "SHORT", 1.0850, 0.25, 75.0)
        monitor.record_trade("EURUSD", "LONG", 1.0820, 0.25, -30.0)
        monitor.record_trade("EURUSD", "LONG", 1.0810, 0.25, 100.0)
        
        monitor.update_drawdown(0.03)
        
        # Display dashboard
        logger.info(dashboard.display_dashboard())
        
        # Get status report
        logger.info(monitor.get_status_report())
        
        # Health check
        health = monitor.get_health_check()
        logger.info("\nSYSTEM HEALTH CHECK:")
        for check, status in health.items():
            status_str = "✓ PASS" if status else "✗ FAIL"
            logger.info(f"  {check}: {status_str}")
        
        # Stop monitor
        monitor.stop()
        
        logger.info("\n" + "="*70)
        logger.info("REAL-TIME MONITORING COMPLETE")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Monitoring failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
