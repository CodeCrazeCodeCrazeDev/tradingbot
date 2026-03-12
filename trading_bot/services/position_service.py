"""
Position Service - Position Management
=======================================

Wraps Position management capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class PositionService(BaseService):
    """
    Position Service - Position Management
    
    Provides:
    - Position tracking
    - P&L calculation
    - Position sizing
    - Stop-loss management
    """
    
    SERVICE_NAME = "position"
    SERVICE_TYPE = "execution"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["broker"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        self._position_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PositionService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("PositionService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._position_manager else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Position components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.position import PositionManager
            self._position_manager = PositionManager()
            logger.info("PositionManager loaded")
        except ImportError as e:
            logger.warning(f"PositionManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
