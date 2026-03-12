"""
Data Sources Service
====================

Wraps Data Sources module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DataSourcesService(BaseService):
    """
    Data Sources Service - Free Data Providers
    
    Provides:
    - Yahoo Finance provider
    - CoinGecko provider
    - FRED provider
    - News API provider
    """
    
    SERVICE_NAME = "data_sources"
    SERVICE_TYPE = "data"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._aggregator = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DataSourcesService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DataSourcesService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._aggregator else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Data Sources components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.data_sources import FreeDataAggregator
            self._aggregator = FreeDataAggregator()
            logger.info("FreeDataAggregator loaded")
        except ImportError as e:
            logger.warning(f"FreeDataAggregator not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
