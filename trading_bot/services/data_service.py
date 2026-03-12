"""
Data Service
============

Wraps Data module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DataService(BaseService):
    """
    Data Service - Data Management
    
    Provides:
    - Data manager
    - Level 2 manager
    - Database backup manager
    """
    
    SERVICE_NAME = "data"
    SERVICE_TYPE = "data"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._data_manager = None
        self._level2_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DataService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DataService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._data_manager is not None, self._level2_manager is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Data components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.data import DataManager
            self._data_manager = DataManager()
            logger.info("DataManager loaded")
        except ImportError as e:
            logger.warning(f"DataManager not available: {e}")
        
        try:
            from trading_bot.data import Level2Manager
            self._level2_manager = Level2Manager()
            logger.info("Level2Manager loaded")
        except ImportError as e:
            logger.warning(f"Level2Manager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
