"""
Strategy Service - Strategy Management
=======================================

Wraps Strategy management capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class StrategyService(BaseService):
    """
    Strategy Service - Strategy Management
    
    Provides:
    - Strategy selection
    - Strategy execution
    - Strategy optimization
    - Multi-strategy coordination
    """
    
    SERVICE_NAME = "strategy"
    SERVICE_TYPE = "signals"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["signals"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._strategy_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("StrategyService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("StrategyService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._strategy_manager else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Strategy components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.strategy import StrategyManager
            self._strategy_manager = StrategyManager()
            logger.info("StrategyManager loaded")
        except ImportError as e:
            logger.warning(f"StrategyManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
