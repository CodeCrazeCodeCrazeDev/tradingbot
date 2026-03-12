"""
Alert Manager - Manages and routes alerts across the trading system
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """
    AlertSeverity class.

    Auto-documented by QwenCodeMender.
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """
    AlertChannel class.

    Auto-documented by QwenCodeMender.
    """
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime = None
    acknowledged: bool = False
    channels: List[AlertChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.alerts: Dict[str, Alert] = {}
        self.handlers: Dict[AlertChannel, Callable] = {}
        self._running = False
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        self.handlers[AlertChannel.LOG] = self._log_handler
    
    def _log_handler(self, alert: Alert):
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.INFO)
        logger.log(log_level, f"[{alert.source}] {alert.title}: {alert.message}")
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("AlertManager initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("AlertManager started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("AlertManager stopped")
        return True
    
    def send_alert(self, alert: Alert):
        self.alerts[alert.id] = alert
        for channel in alert.channels or [AlertChannel.LOG]:
            if channel in self.handlers:
                try:
                    self.handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Error sending alert via {channel}: {e}")
    
    def acknowledge(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        return [a for a in self.alerts.values() if not a.acknowledged]


_manager: Optional[AlertManager] = None

def get_manager() -> AlertManager:
    global _manager
    if _manager is None:
        _manager = AlertManager()
    return _manager

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_manager().initialize(config)

async def start() -> bool:
    return await get_manager().start()

async def stop() -> bool:
    return await get_manager().stop()
