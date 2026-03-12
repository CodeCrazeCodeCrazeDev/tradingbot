"""
Database Service
================

Wraps Database module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DatabaseService(BaseService):
    """
    Database Service - Database Management
    
    Provides:
    - Database manager
    - Cache manager
    - Persistence manager
    - Shared memory manager
    """
    
    SERVICE_NAME = "database"
    SERVICE_TYPE = "database"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._db_manager = None
        self._cache_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DatabaseService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DatabaseService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._db_manager is not None, self._cache_manager is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Database components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.database import DatabaseManager
            self._db_manager = DatabaseManager()
            logger.info("DatabaseManager loaded")
        except ImportError as e:
            logger.warning(f"DatabaseManager not available: {e}")
        
        try:
            from trading_bot.database import CacheManager
            self._cache_manager = CacheManager()
            logger.info("CacheManager loaded")
        except ImportError as e:
            logger.warning(f"CacheManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
