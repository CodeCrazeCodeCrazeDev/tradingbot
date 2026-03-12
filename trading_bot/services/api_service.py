"""
API Service
===========

Wraps API module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class APIService(BaseService):
    """
    API Service - REST API and Rate Limiting
    
    Provides:
    - Trading API server
    - Rate limiting
    - Multi-rate limiter
    """
    
    SERVICE_NAME = "api"
    SERVICE_TYPE = "api"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._api_server = None
        self._rate_limiter = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("APIService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("APIService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._api_server is not None, self._rate_limiter is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 API components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.api import TradingAPIServer
            self._api_server = TradingAPIServer
            logger.info("TradingAPIServer loaded")
        except ImportError as e:
            logger.warning(f"TradingAPIServer not available: {e}")
        
        try:
            from trading_bot.api import RateLimiter
            self._rate_limiter = RateLimiter
            logger.info("RateLimiter loaded")
        except ImportError as e:
            logger.warning(f"RateLimiter not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
