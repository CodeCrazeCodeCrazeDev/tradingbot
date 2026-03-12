"""
Alternative Data Service
========================

Wraps Alternative Data module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlternativeDataService(BaseService):
    """
    Alternative Data Service - Non-Traditional Data Sources
    
    Provides:
    - Satellite imagery analysis
    - Real-time sentiment engine
    """
    
    SERVICE_NAME = "alternative_data"
    SERVICE_TYPE = "data"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 120.0) if config else 120.0
        self._task: Optional[asyncio.Task] = None
        self._sentiment_engine = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlternativeDataService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlternativeDataService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._sentiment_engine else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Alternative Data components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alternative_data import RealTimeSentimentEngine
            self._sentiment_engine = RealTimeSentimentEngine()
            logger.info("RealTimeSentimentEngine loaded")
        except ImportError as e:
            logger.warning(f"RealTimeSentimentEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
