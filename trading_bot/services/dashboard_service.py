"""
Dashboard Service
=================

Wraps Dashboard module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DashboardService(BaseService):
    """
    Dashboard Service - UI and Monitoring Panels
    
    Provides:
    - System panel
    - Performance attribution
    - Survival dashboard
    """
    
    SERVICE_NAME = "dashboard"
    SERVICE_TYPE = "ui"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._system_panel = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DashboardService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DashboardService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._system_panel else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Dashboard components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.dashboard import SystemPanel
            self._system_panel = SystemPanel
            logger.info("SystemPanel loaded")
        except ImportError as e:
            logger.warning(f"SystemPanel not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
