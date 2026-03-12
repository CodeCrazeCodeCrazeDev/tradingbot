"""
Live Trading Monitor - 24-48 Hour Monitoring System
Real-time monitoring, alerting, and performance tracking for live trading
"""

import time
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import deque

import logging

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

try:
    from loguru import logger
except ImportError:
    logger = logging.getLogger(__name__)

@dataclass
class TradeEvent:
    """Trade event data"""
    timestamp: datetime
    event_type: str  # 'entry', 'exit', 'stop_loss', 'take_profit'
    symbol: str
    direction: str
    lot_size: float
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    reason: Optional[str] = None

@dataclass
class SystemMetrics:
    """System health metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    active_positions: int
    daily_trades: int
    daily_pnl: float
    total_pnl: float
    win_rate: float
    current_drawdown: float
    api_latency_ms: float
    errors_count: int

class LiveMonitor:
    """
    Live Trading Monitor
    
    Features:
    - Real-time trade tracking
    - Performance metrics
    - System health monitoring
    - Automatic alerting
    - Daily reports
    - Emergency stop triggers
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize live monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_running = False
        self.monitor_thread = None
        
        # Data storage
        self.trades: List[TradeEvent] = []
        self.metrics_history: deque = deque(maxlen=1000)
        self.errors: List[Dict] = []
        self.alerts_sent: List[Dict] = []
        
        # Performance tracking
        self.start_time = datetime.now()
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        
        # Limits and thresholds
        self.max_daily_loss = self.config.get('max_daily_loss', 0.02)
        self.max_drawdown = self.config.get('max_drawdown', 0.10)
        self.max_daily_trades = self.config.get('max_daily_trades', 10)
        
        # Alert system
        self.alert_handlers = []
        self._setup_alert_handlers()
        
        # Monitoring interval
        self.monitor_interval = self.config.get('monitor_interval', 60)  # seconds
        
        # Reports directory
        self.reports_dir = Path('logs/monitoring_reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_alert_handlers(self):
        """Setup alert handlers (Telegram, Email, etc.)"""
        # Telegram
        telegram_config = self.config.get('telegram', {})
        if telegram_config.get('enabled'):
            try:
                from trading_bot.alerts.alert_system import TelegramAlert
                telegram = TelegramAlert(
                    bot_token=telegram_config.get('bot_token'),
                    chat_id=telegram_config.get('chat_id')
                )
                self.alert_handlers.append(telegram)
                logger.info("✅ Telegram alerts enabled")
            except Exception as e:
                logger.warning(f"Telegram alerts not available: {e}")
        
        # Email
        email_config = self.config.get('email', {})
        if email_config.get('enabled'):
            try:
                from trading_bot.alerts.alert_system import EmailAlert
                email = EmailAlert(email_config)
                self.alert_handlers.append(email)
                logger.info("✅ Email alerts enabled")
            except Exception as e:
                logger.warning(f"Email alerts not available: {e}")
    
    def start(self):
        """Start monitoring"""
        if self.is_running:
            logger.warning("Monitor already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🚀 Live monitor started")
        self.send_alert("🚀 Trading bot monitoring started", "INFO")
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Generate final report
        self.generate_report()
        
        logger.info("🛑 Live monitor stopped")
        self.send_alert("🛑 Trading bot monitoring stopped", "INFO")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Check for emergency stops
                self._check_emergency_stops(metrics)
                
                # Generate periodic reports
                self._check_report_schedule()
                
                # Sleep
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                self.record_error("monitor_loop", str(e))
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            import psutil
            process = psutil.Process()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=process.cpu_percent(),
                memory_mb=process.memory_info().rss / 1024 / 1024,
                active_positions=self._get_active_positions(),
                daily_trades=self.daily_trades,
                daily_pnl=self.daily_pnl,
                total_pnl=self.total_pnl,
                win_rate=self._calculate_win_rate(),
                current_drawdown=self.current_drawdown,
                api_latency_ms=self._measure_api_latency(),
                errors_count=len(self.errors)
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None
    
    def _get_active_positions(self) -> int:
        """Get number of active positions"""
        try:
            if mt5.initialize():
                positions = mt5.positions_get()
                return len(positions) if positions else 0
        except Exception:
            pass
        return 0
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from trades"""
        if not self.trades:
            return 0.0
        
        closed_trades = [t for t in self.trades if t.event_type in ['exit', 'stop_loss', 'take_profit']]
        if not closed_trades:
            return 0.0
        
        winning_trades = [t for t in closed_trades if t.profit_loss and t.profit_loss > 0]
        return len(winning_trades) / len(closed_trades)
    
    def _measure_api_latency(self) -> float:
        """Measure API response latency"""
        try:
            import requests
            start = time.time()
            requests.get('https://api.github.com', timeout=2)
            return (time.time() - start) * 1000
        except Exception:
            return 0.0
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions"""
        if not metrics:
            return
        
        # High CPU usage
        if metrics.cpu_percent > 80:
            self.send_alert(
                f"⚠️ High CPU usage: {metrics.cpu_percent:.1f}%",
                "WARNING"
            )
        
        # High memory usage
        if metrics.memory_mb > 1000:
            self.send_alert(
                f"⚠️ High memory usage: {metrics.memory_mb:.1f} MB",
                "WARNING"
            )
        
        # High API latency
        if metrics.api_latency_ms > 2000:
            self.send_alert(
                f"⚠️ High API latency: {metrics.api_latency_ms:.0f}ms",
                "WARNING"
            )
        
        # Low win rate (after 10+ trades)
        if len(self.trades) >= 10 and metrics.win_rate < 0.40:
            self.send_alert(
                f"⚠️ Low win rate: {metrics.win_rate:.1%} (target: >55%)",
                "WARNING"
            )
        
        # High drawdown
        if metrics.current_drawdown > 0.05:
            self.send_alert(
                f"⚠️ Drawdown alert: {metrics.current_drawdown:.1%}",
                "WARNING"
            )
    
    def _check_emergency_stops(self, metrics: SystemMetrics):
        """Check for emergency stop conditions"""
        if not metrics:
            return
        
        # Daily loss limit
        if abs(metrics.daily_pnl) > self.max_daily_loss:
            self.send_alert(
                f"🚨 EMERGENCY: Daily loss limit reached: {metrics.daily_pnl:.2%}",
                "CRITICAL"
            )
            self._trigger_emergency_stop("daily_loss_limit")
        
        # Maximum drawdown
        if metrics.current_drawdown > self.max_drawdown:
            self.send_alert(
                f"🚨 EMERGENCY: Maximum drawdown exceeded: {metrics.current_drawdown:.2%}",
                "CRITICAL"
            )
            self._trigger_emergency_stop("max_drawdown")
        
        # Daily trade limit
        if metrics.daily_trades >= self.max_daily_trades:
            self.send_alert(
                f"⚠️ Daily trade limit reached: {metrics.daily_trades}/{self.max_daily_trades}",
                "WARNING"
            )
    
    def _trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop"""
        logger.critical(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
        
        # Close all positions
        self._close_all_positions()
        
        # Stop the bot
        self.is_running = False
        
        # Generate emergency report
        self.generate_report(emergency=True)
    
    def _close_all_positions(self):
        """Close all open positions"""
        try:
            if not mt5.initialize():
                return
            
            positions = mt5.positions_get()
            if positions:
                for position in positions:
                    # Close position
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                        "position": position.ticket,
                        "deviation": 20,
                        "magic": 234000,
                        "comment": "Emergency close",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"✅ Closed position: {position.ticket}")
                    else:
                        logger.error(f"❌ Failed to close position: {result.comment}")
        
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def _check_report_schedule(self):
        """Check if it's time to generate a report"""
        now = datetime.now()
        
        # Daily report at midnight
        if now.hour == 0 and now.minute < self.monitor_interval / 60:
            self.generate_report()
            self._reset_daily_stats()
    
    def _reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_trades = 0
        self.daily_pnl = 0.0
    
    def record_trade(self, trade: TradeEvent):
        """Record a trade event"""
        self.trades.append(trade)
        
        if trade.event_type == 'entry':
            self.daily_trades += 1
            self.send_alert(
                f"📊 Trade opened: {trade.symbol} {trade.direction} {trade.lot_size} lots @ {trade.entry_price}",
                "INFO"
            )
        
        elif trade.event_type in ['exit', 'stop_loss', 'take_profit']:
            if trade.profit_loss:
                self.daily_pnl += trade.profit_loss
                self.total_pnl += trade.profit_loss
                
                # Update drawdown
                if self.total_pnl > self.peak_balance:
                    self.peak_balance = self.total_pnl
                
                if self.peak_balance > 0:
                    self.current_drawdown = (self.peak_balance - self.total_pnl) / self.peak_balance
                
                emoji = "✅" if trade.profit_loss > 0 else "❌"
                self.send_alert(
                    f"{emoji} Trade closed: {trade.symbol} {trade.direction}\n"
                    f"P/L: ${trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)\n"
                    f"Reason: {trade.reason}",
                    "INFO"
                )
    
    def record_error(self, component: str, error: str):
        """Record an error"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'error': error
        }
        self.errors.append(error_data)
        
        self.send_alert(
            f"❌ Error in {component}: {error}",
            "ERROR"
        )
    
    def send_alert(self, message: str, level: str = "INFO"):
        """Send alert through configured channels"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.alerts_sent.append(alert_data)
        
        # Send through alert handlers
        for handler in self.alert_handlers:
            try:
                handler.send(message, level)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def generate_report(self, emergency: bool = False):
        """Generate monitoring report"""
        report_type = "EMERGENCY" if emergency else "REGULAR"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'monitoring_duration': str(datetime.now() - self.start_time),
            
            'performance': {
                'total_trades': len(self.trades),
                'daily_trades': self.daily_trades,
                'win_rate': self._calculate_win_rate(),
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'current_drawdown': self.current_drawdown,
                'peak_balance': self.peak_balance
            },
            
            'system_health': {
                'errors_count': len(self.errors),
                'alerts_sent': len(self.alerts_sent),
                'active_positions': self._get_active_positions()
            },
            
            'recent_trades': [asdict(t) for t in self.trades[-10:]],
            'recent_errors': self.errors[-10:],
            'recent_alerts': self.alerts_sent[-20:]
        }
        
        # Save report
        report_file = self.reports_dir / f"monitor_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Report generated: {report_file}")
        
        # Send report summary
        self.send_alert(
            f"📊 {report_type} Report Generated\n"
            f"Trades: {len(self.trades)} (Win rate: {self._calculate_win_rate():.1%})\n"
            f"P/L: ${self.total_pnl:.2f}\n"
            f"Drawdown: {self.current_drawdown:.2%}\n"
            f"Errors: {len(self.errors)}",
            "INFO"
        )
        
        return report
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'uptime': str(datetime.now() - self.start_time),
            'total_trades': len(self.trades),
            'daily_trades': self.daily_trades,
            'win_rate': self._calculate_win_rate(),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'current_drawdown': self.current_drawdown,
            'errors_count': len(self.errors),
            'alerts_sent': len(self.alerts_sent)
        }

# Export
__all__ = ['LiveMonitor', 'TradeEvent', 'SystemMetrics']
