"""
AlphaAlgo Alert Manager - Multi-Channel Alerts

This module handles sending alerts to humans through multiple channels.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import asyncio
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class AlertChannel(Enum):
    """Alert delivery channels"""
    LOG = "log"
    FILE = "file"
    CONSOLE = "console"
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """An alert to be sent to humans"""
    alert_id: str
    priority: AlertPriority
    title: str
    message: str
    
    # Context
    category: str
    source: str
    
    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Delivery
    channels: List[AlertChannel] = field(default_factory=list)
    delivered_to: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'source': self.source,
            'data': self.data,
            'channels': [c.value for c in self.channels],
            'delivered_to': self.delivered_to,
            'created_at': self.created_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
        }


class AlertManager:
    """
    Multi-channel alert manager.
    
    Sends alerts to humans through various channels based on priority.
    """
    
    # Default channels by priority
    DEFAULT_CHANNELS = {
        AlertPriority.LOW: [AlertChannel.LOG, AlertChannel.FILE],
        AlertPriority.MEDIUM: [AlertChannel.LOG, AlertChannel.FILE, AlertChannel.CONSOLE],
        AlertPriority.HIGH: [AlertChannel.LOG, AlertChannel.FILE, AlertChannel.TELEGRAM],
        AlertPriority.CRITICAL: [AlertChannel.LOG, AlertChannel.FILE, AlertChannel.TELEGRAM, AlertChannel.EMAIL],
        AlertPriority.EMERGENCY: [AlertChannel.LOG, AlertChannel.FILE, AlertChannel.TELEGRAM, AlertChannel.EMAIL, AlertChannel.SMS],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Channel handlers
        self._handlers: Dict[AlertChannel, Callable] = {
            AlertChannel.LOG: self._handle_log,
            AlertChannel.FILE: self._handle_file,
            AlertChannel.CONSOLE: self._handle_console,
        }
        
        # Alert history
        self._alerts: List[Alert] = []
        self._max_alerts = 10000
        
        # Pending acknowledgments
        self._pending_ack: Dict[str, Alert] = {}
        
        # Storage
        self._storage_path = Path(self.config.get('storage_path', 'alerts'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self._rate_limits: Dict[str, datetime] = {}
        self._min_interval_seconds = self.config.get('min_interval_seconds', 60)
        
        logger.info("AlertManager initialized")
    
    def register_handler(self, channel: AlertChannel, handler: Callable) -> None:
        """Register a handler for a channel"""
        self._handlers[channel] = handler
        logger.info(f"Registered handler for {channel.value}")
    
    async def send_alert(
        self,
        priority: AlertPriority,
        title: str,
        message: str,
        category: str = "general",
        source: str = "system",
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> Alert:
        """
        Send an alert through appropriate channels.
        
        Args:
            priority: Alert priority
            title: Alert title
            message: Alert message
            category: Alert category
            source: Source of the alert
            data: Additional data
            channels: Override default channels
        
        Returns:
            The created Alert
        """
        import uuid
        
        # Check rate limiting
        rate_key = f"{category}:{title}"
        if rate_key in self._rate_limits:
            elapsed = (datetime.now() - self._rate_limits[rate_key]).total_seconds()
            if elapsed < self._min_interval_seconds:
                logger.debug(f"Alert rate limited: {rate_key}")
                # Return existing alert
                for alert in reversed(self._alerts):
                    if alert.title == title and alert.category == category:
                        return alert
        
        # Determine channels
        if channels is None:
            channels = self.DEFAULT_CHANNELS.get(priority, [AlertChannel.LOG])
        
        # Create alert
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            priority=priority,
            title=title,
            message=message,
            category=category,
            source=source,
            data=data or {},
            channels=channels,
        )
        
        # Send through channels
        for channel in channels:
            if channel in self._handlers:
                try:
                    handler = self._handlers[channel]
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                    alert.delivered_to.append(channel.value)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
        
        alert.delivered_at = datetime.now()
        
        # Store alert
        self._alerts.append(alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]
        
        # Track for acknowledgment if high priority
        if priority.value >= AlertPriority.HIGH.value:
            self._pending_ack[alert.alert_id] = alert
        
        # Update rate limit
        self._rate_limits[rate_key] = datetime.now()
        
        # Save to file
        self._save_alert(alert)
        
        return alert
    
    def acknowledge(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self._pending_ack:
            alert = self._pending_ack[alert_id]
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = user
            del self._pending_ack[alert_id]
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def get_pending_acknowledgments(self) -> List[Dict[str, Any]]:
        """Get alerts pending acknowledgment"""
        return [a.to_dict() for a in self._pending_ack.values()]
    
    def get_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        alerts = self._alerts
        
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        return [a.to_dict() for a in alerts[-limit:]]
    
    # =========================================================================
    # DEFAULT HANDLERS
    # =========================================================================
    
    def _handle_log(self, alert: Alert) -> None:
        """Log alert"""
        level_map = {
            AlertPriority.LOW: logging.DEBUG,
            AlertPriority.MEDIUM: logging.INFO,
            AlertPriority.HIGH: logging.WARNING,
            AlertPriority.CRITICAL: logging.ERROR,
            AlertPriority.EMERGENCY: logging.CRITICAL,
        }
        level = level_map.get(alert.priority, logging.INFO)
        logger.log(level, f"[{alert.category}] {alert.title}: {alert.message}")
    
    def _handle_file(self, alert: Alert) -> None:
        """Save alert to file"""
        self._save_alert(alert)
    
    def _handle_console(self, alert: Alert) -> None:
        """Print alert to console"""
        priority_symbols = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "📢",
            AlertPriority.HIGH: "⚠️",
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.EMERGENCY: "🆘",
        }
        symbol = priority_symbols.get(alert.priority, "📢")
        logger.info(f"\n{symbol} [{alert.priority.name}] {alert.title}")
        logger.info(f"   {alert.message}")
        if alert.data:
            logger.info(f"   Data: {json.dumps(alert.data, indent=2)}")
    
    def _save_alert(self, alert: Alert) -> None:
        """Save alert to file"""
        try:
            date_str = alert.created_at.strftime('%Y%m%d')
            path = self._storage_path / f"alerts_{date_str}.json"
            
            # Load existing alerts
            alerts = []
            if path.exists():
                with open(path, 'r') as f:
                    alerts = json.load(f)
            
            # Append new alert
            alerts.append(alert.to_dict())
            
            # Save
            with open(path, 'w') as f:
                json.dump(alerts, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_alert_manager_instance: Optional[AlertManager] = None


def get_alert_manager(config: Optional[Dict[str, Any]] = None) -> AlertManager:
    """Get the singleton alert manager"""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager(config)
    return _alert_manager_instance


async def send_alert(
    priority: AlertPriority,
    title: str,
    message: str,
    category: str = "general",
    data: Optional[Dict[str, Any]] = None
) -> Alert:
    """Send alert using singleton manager"""
    manager = get_alert_manager()
    return await manager.send_alert(priority, title, message, category, data=data)


async def send_critical_alert(title: str, message: str, data: Optional[Dict[str, Any]] = None) -> Alert:
    """Send a critical alert"""
    return await send_alert(AlertPriority.CRITICAL, title, message, "critical", data)


async def send_emergency_alert(title: str, message: str, data: Optional[Dict[str, Any]] = None) -> Alert:
    """Send an emergency alert"""
    return await send_alert(AlertPriority.EMERGENCY, title, message, "emergency", data)
