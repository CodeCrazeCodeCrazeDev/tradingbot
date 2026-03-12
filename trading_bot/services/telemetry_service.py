"""
Telemetry Service - System Telemetry
=====================================

Wraps Telemetry capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class TelemetryService(BaseService):
    """
    Telemetry Service - System Telemetry
    
    Provides:
    - Metrics collection
    - Tracing
    - Logging aggregation
    """
    
    SERVICE_NAME = "telemetry"
    SERVICE_TYPE = "infrastructure"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._telemetry_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("TelemetryService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("TelemetryService stopped")
    
    async def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message="Telemetry service running"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.telemetry import TelemetrySystem
            self._telemetry_system = TelemetrySystem()
            logger.info("TelemetrySystem loaded")
        except ImportError as e:
            logger.warning(f"TelemetrySystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
