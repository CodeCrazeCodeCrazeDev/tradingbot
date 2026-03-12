"""
Alerts Service
==============

Wraps Alerts module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlertsService(BaseService):
    """
    Alerts Service - Alert Management and Notifications
    
    Provides:
    - Alert manager
    - Alert system
    """
    
    SERVICE_NAME = "alerts"
    SERVICE_TYPE = "notifications"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["risk_monitor"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        self._alert_manager = None
        self._alert_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.RISK_LIMIT_BREACH, EventTypes.SYSTEM_ERROR, EventTypes.DRAWDOWN_WARNING],
                self._on_alert_event
            )
        logger.info("AlertsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        logger.info("AlertsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._alert_manager is not None, self._alert_system is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Alerts components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alerts import AlertManager
            self._alert_manager = AlertManager()
            logger.info("AlertManager loaded")
        except ImportError as e:
            logger.warning(f"AlertManager not available: {e}")
        
        try:
            from trading_bot.alerts import AlertSystem
            self._alert_system = AlertSystem()
            logger.info("AlertSystem loaded")
        except ImportError as e:
            logger.warning(f"AlertSystem not available: {e}")
    
    async def _on_alert_event(self, event: Event) -> None:
        """Process alert-worthy events"""
        if self._alert_system:
            try:
                # Trigger alert based on event
                pass
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
