"""
Analytics Service
=================

Wraps Analytics module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Analytics Service - Performance and Attribution Analytics
    
    Provides:
    - Alpha attribution system
    - Performance attribution
    - Psychological metrics
    - Real-time analytics
    """
    
    SERVICE_NAME = "analytics"
    SERVICE_TYPE = "analytics"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._alpha_attribution = None
        self._performance = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AnalyticsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AnalyticsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._alpha_attribution is not None,
            self._performance is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Analytics components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.analytics import AlphaAttributionSystem
            self._alpha_attribution = AlphaAttributionSystem()
            logger.info("AlphaAttributionSystem loaded")
        except ImportError as e:
            logger.warning(f"AlphaAttributionSystem not available: {e}")
        
        try:
            from trading_bot.analytics import PerformanceAttributionSystem
            self._performance = PerformanceAttributionSystem()
            logger.info("PerformanceAttributionSystem loaded")
        except ImportError as e:
            logger.warning(f"PerformanceAttributionSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
