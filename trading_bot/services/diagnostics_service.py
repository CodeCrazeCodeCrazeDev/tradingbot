"""
Diagnostics Service
===================

Wraps Diagnostics module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DiagnosticsService(BaseService):
    """
    Diagnostics Service - System Validation
    
    Provides:
    - System validator
    - System health report
    """
    
    SERVICE_NAME = "diagnostics"
    SERVICE_TYPE = "diagnostics"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._validator = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DiagnosticsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DiagnosticsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._validator else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Diagnostics components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.diagnostics import SystemValidator
            self._validator = SystemValidator()
            logger.info("SystemValidator loaded")
        except ImportError as e:
            logger.warning(f"SystemValidator not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
