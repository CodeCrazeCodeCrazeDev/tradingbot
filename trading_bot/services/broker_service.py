"""
Broker Service
==============

Wraps Broker module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class BrokerService(BaseService):
    """
    Broker Service - Broker Integration
    
    Provides:
    - Broker interface
    - Binance broker
    - IB broker
    """
    
    SERVICE_NAME = "broker"
    SERVICE_TYPE = "broker"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        self._broker_interface = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BrokerService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BrokerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._broker_interface else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Broker components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.broker import BrokerInterface
            self._broker_interface = BrokerInterface
            logger.info("BrokerInterface loaded")
        except ImportError as e:
            logger.warning(f"BrokerInterface not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
