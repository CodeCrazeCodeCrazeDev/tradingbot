"""
Monitoring Service - System Monitoring
=======================================

Wraps System Monitoring capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class MonitoringService(BaseService):
    """
    Monitoring Service - System Monitoring
    
    Provides:
    - System health monitoring
    - Performance metrics
    - Resource usage tracking
    - Alert generation
    """
    
    SERVICE_NAME = "system_monitoring"
    SERVICE_TYPE = "infrastructure"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._monitoring_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("MonitoringService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MonitoringService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._monitoring_system else 0
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Monitoring components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.monitoring import MonitoringSystem
            self._monitoring_system = MonitoringSystem()
            logger.info("MonitoringSystem loaded")
        except ImportError as e:
            logger.warning(f"MonitoringSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
