"""
Brokers Service
===============

Wraps Brokers module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class BrokersService(BaseService):
    """
    Brokers Service - Multi-Broker Connection Management
    
    Provides:
    - Broker connection manager
    - Multi-broker connection manager
    - Unified broker manager
    """
    
    SERVICE_NAME = "brokers"
    SERVICE_TYPE = "broker"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["broker"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._connection_manager = None
        self._unified_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BrokersService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BrokersService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._connection_manager is not None, self._unified_manager is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Brokers components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.brokers import MultiBrokerConnectionManager
            self._connection_manager = MultiBrokerConnectionManager()
            logger.info("MultiBrokerConnectionManager loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"MultiBrokerConnectionManager not available: {e}")
        
        try:
            from trading_bot.brokers import UnifiedBrokerManager
            self._unified_manager = UnifiedBrokerManager()
            logger.info("UnifiedBrokerManager loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"UnifiedBrokerManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
