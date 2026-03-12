"""
Notifications Service - Alert and Notification Management
==========================================================

Wraps Notification capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class NotificationsService(BaseService):
    """
    Notifications Service - Alert Management
    
    Provides:
    - Email notifications
    - Telegram alerts
    - Push notifications
    - Alert management
    """
    
    SERVICE_NAME = "notifications"
    SERVICE_TYPE = "orchestration"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._notification_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("NotificationsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("NotificationsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._notification_manager else 0
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Notification components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.notifications import NotificationManager
            self._notification_manager = NotificationManager()
            logger.info("NotificationManager loaded")
        except ImportError as e:
            logger.warning(f"NotificationManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
