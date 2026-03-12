"""
Core API Service
================

Wraps Core API module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class CoreAPIService(BaseService):
    """
    Core API Service - System Events and Interfaces
    
    Provides:
    - System events
    - Risk manager interface
    - Evolution engine interface
    """
    
    SERVICE_NAME = "core_api"
    SERVICE_TYPE = "api"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._loaded = False
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CoreAPIService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CoreAPIService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running and self._loaded,
            last_check=datetime.utcnow(),
            message="Core API components loaded" if self._loaded else "Core API not loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.core_api import SystemEvent, IRiskManager
            self._loaded = True
            logger.info("Core API interfaces loaded")
        except ImportError as e:
            logger.warning(f"Core API not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
