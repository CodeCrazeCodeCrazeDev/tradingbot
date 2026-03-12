"""
Brain Service
=============

Wraps Brain module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class BrainService(BaseService):
    """
    Brain Service - Elite Brain Trading System
    
    Provides:
    - Elite brain controller
    - Brain trader
    - MT5 brain trader
    - Meta-learning system
    - Central controller
    """
    
    SERVICE_NAME = "brain"
    SERVICE_TYPE = "trading"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data", "ai_core"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._elite_brain = None
        self._brain_trader = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BrainService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BrainService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._elite_brain is not None, self._brain_trader is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Brain components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.brain import EliteBrainController
            self._elite_brain = EliteBrainController()
            logger.info("EliteBrainController loaded")
        except ImportError as e:
            logger.warning(f"EliteBrainController not available: {e}")
        
        try:
            from trading_bot.brain import BrainTrader
            self._brain_trader = BrainTrader()
            logger.info("BrainTrader loaded")
        except ImportError as e:
            logger.warning(f"BrainTrader not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
