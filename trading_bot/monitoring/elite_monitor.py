"""
Elite 5-Star Monitoring & Alert System
Real-time monitoring with multi-channel alerts
"""

import logging
import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels"""
    LOG = "log"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert message"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    
    def update(self, trade_pnl: float):
        """Update metrics with new trade"""
        self.total_trades += 1
        self.total_pnl += trade_pnl
        self.realized_pnl += trade_pnl
        
        if trade_pnl > 0:
            self.winning_trades += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            if trade_pnl > self.largest_win:
                self.largest_win = trade_pnl
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            if trade_pnl < self.largest_loss:
                self.largest_loss = trade_pnl
        
        # Calculate win rate
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        # Calculate averages
        self.average_win = sum([t for t in [trade_pnl] if t > 0]) / max(self.winning_trades, 1)
        self.average_loss = abs(sum([t for t in [trade_pnl] if t < 0])) / max(self.losing_trades, 1)
        
        # Calculate profit factor
        total_wins = self.average_win * self.winning_trades
        total_losses = self.average_loss * self.losing_trades
        self.profit_factor = total_wins / total_losses if total_losses > 0 else 0


class EliteMonitor:
    """
    Elite Monitoring System
    
    Features:
    - Real-time performance tracking
    - Multi-channel alerts
    - Health checks
    - Anomaly detection
    - Resource monitoring
    """
    
    def __init__(self, telegram_token: Optional[str] = None, 
                 telegram_chat_id: Optional[str] = None,
                 discord_webhook: Optional[str] = None):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_webhook = discord_webhook
        
        self.metrics = PerformanceMetrics()
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, bool] = {}
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        logger.info("Elite Monitor initialized")
    
    async def send_alert(self, level: AlertLevel, title: str, message: str, 
                        channels: Optional[List[AlertChannel]] = None, metadata: Dict = None):
        """
        Send alert through specified channels
        
        Args:
            level: Alert severity
            title: Alert title
            message: Alert message
            channels: List of channels to send to (default: all configured)
            metadata: Additional metadata
        """
        alert = Alert(level=level, title=title, message=message, metadata=metadata or {})
        self.alerts.append(alert)
        
        # Default to all channels if not specified
        if channels is None:
            channels = [AlertChannel.LOG]
            if self.telegram_token:
                channels.append(AlertChannel.TELEGRAM)
            if self.discord_webhook:
                channels.append(AlertChannel.DISCORD)
        
        # Send to each channel
        tasks = []
        for channel in channels:
            if channel == AlertChannel.LOG:
                self._log_alert(alert)
            elif channel == AlertChannel.TELEGRAM:
                tasks.append(self._send_telegram(alert))
            elif channel == AlertChannel.DISCORD:
                tasks.append(self._send_discord(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def _log_alert(self, alert: Alert):
        """Log alert"""
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(alert.level, logger.info)
        
        log_func(f"[{alert.level.value.upper()}] {alert.title}: {alert.message}")
    
    async def _send_telegram(self, alert: Alert):
        """Send alert via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        try:
        
            emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }.get(alert.level, "📢")
            
            text = f"{emoji} *{alert.title}*\n\n{alert.message}\n\n_{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_"
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                await session.post(url, json={
                    'chat_id': self.telegram_chat_id,
                    'text': text,
                    'parse_mode': 'Markdown'
                })
            
            logger.debug("Telegram alert sent")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def _send_discord(self, alert: Alert):
        """Send alert via Discord webhook"""
        if not self.discord_webhook:
            return
        try:
        
            color = {
                AlertLevel.INFO: 0x3498db,  # Blue
                AlertLevel.WARNING: 0xf39c12,  # Orange
                AlertLevel.ERROR: 0xe74c3c,  # Red
                AlertLevel.CRITICAL: 0x992d22  # Dark red
            }.get(alert.level, 0x95a5a6)
            
            embed = {
                'title': alert.title,
                'description': alert.message,
                'color': color,
                'timestamp': alert.timestamp.isoformat(),
                'footer': {'text': f'Level: {alert.level.value.upper()}'}
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(self.discord_webhook, json={'embeds': [embed]})
            
            logger.debug("Discord alert sent")
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def record_trade(self, pnl: float, symbol: str, direction: str):
        """Record trade and update metrics"""
        self.metrics.update(pnl)
        
        # Check for anomalies
        asyncio.create_task(self._check_anomalies(pnl))
        
        logger.info(f"Trade recorded: {symbol} {direction} PNL=${pnl:,.2f}")
    
    async def _check_anomalies(self, pnl: float):
        """Check for anomalous conditions"""
        # Consecutive losses alert
        if self.metrics.consecutive_losses >= 5:
            await self.send_alert(
                AlertLevel.WARNING,
                "Consecutive Losses Alert",
                f"⚠️ {self.metrics.consecutive_losses} consecutive losses detected!",
                metadata={'consecutive_losses': self.metrics.consecutive_losses}
            )
        
        # Large loss alert
        if pnl < -1000:  # Configurable threshold
            await self.send_alert(
                AlertLevel.ERROR,
                "Large Loss Alert",
                f"❌ Large loss detected: ${pnl:,.2f}",
                metadata={'loss': pnl}
            )
        
        # Drawdown alert
        if self.metrics.current_drawdown > 0.10:  # 10%
            await self.send_alert(
                AlertLevel.CRITICAL,
                "High Drawdown Alert",
                f"🚨 Drawdown: {self.metrics.current_drawdown:.2%}",
                metadata={'drawdown': self.metrics.current_drawdown}
            )
    
    def health_check(self, component: str, is_healthy: bool):
        """Update component health status"""
        self.health_checks[component] = is_healthy
        
        if not is_healthy:
            asyncio.create_task(self.send_alert(
                AlertLevel.ERROR,
                f"Health Check Failed: {component}",
                f"Component {component} is unhealthy",
                metadata={'component': component}
            ))
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        return {
            'total_trades': self.metrics.total_trades,
            'win_rate': f"{self.metrics.win_rate:.2%}",
            'profit_factor': f"{self.metrics.profit_factor:.2f}",
            'total_pnl': f"${self.metrics.total_pnl:,.2f}",
            'sharpe_ratio': f"{self.metrics.sharpe_ratio:.2f}",
            'max_drawdown': f"{self.metrics.max_drawdown:.2%}",
            'consecutive_wins': self.metrics.consecutive_wins,
            'consecutive_losses': self.metrics.consecutive_losses,
            'largest_win': f"${self.metrics.largest_win:,.2f}",
            'largest_loss': f"${self.metrics.largest_loss:,.2f}"
        }
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        all_healthy = all(self.health_checks.values()) if self.health_checks else True
        return {
            'overall_status': 'HEALTHY' if all_healthy else 'UNHEALTHY',
            'components': self.health_checks,
            'timestamp': datetime.now().isoformat()
        }
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)
    
    async def send_daily_summary(self):
        """Send daily performance summary"""
        summary = f"""
📊 *Daily Trading Summary*

Total Trades: {self.metrics.total_trades}
Win Rate: {self.metrics.win_rate:.2%}
Total P&L: ${self.metrics.total_pnl:,.2f}
Profit Factor: {self.metrics.profit_factor:.2f}

Wins: {self.metrics.winning_trades}
Losses: {self.metrics.losing_trades}
Avg Win: ${self.metrics.average_win:,.2f}
Avg Loss: ${self.metrics.average_loss:,.2f}

Max Drawdown: {self.metrics.max_drawdown:.2%}
"""
        await self.send_alert(
            AlertLevel.INFO,
            "Daily Summary",
            summary,
            metadata={'metrics': self.get_metrics()}
        )


# Export
__all__ = ['EliteMonitor', 'Alert', 'AlertLevel', 'AlertChannel', 'PerformanceMetrics']
