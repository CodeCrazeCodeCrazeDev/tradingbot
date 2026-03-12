"""
Elite System Service
=====================
Wraps Elite System capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class EliteSystemService(BaseService):
    SERVICE_NAME = "elite_system"
    SERVICE_TYPE = "intelligence"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["brain"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("EliteSystemService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EliteSystemService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message="Elite System running" if self._running else "Stopped"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.elite_system import EliteMasterSystem
            self._system = EliteMasterSystem()
            logger.info("EliteMasterSystem loaded")
        except ImportError as e:
            logger.warning(f"EliteMasterSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
