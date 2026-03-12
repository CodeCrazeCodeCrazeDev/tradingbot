"""
Indicators Service - Technical Indicators
==========================================

Wraps Technical Indicators capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class IndicatorsService(BaseService):
    """
    Indicators Service - Technical Indicators
    
    Provides:
    - Technical indicator calculation
    - Custom indicator support
    - Multi-timeframe indicators
    """
    
    SERVICE_NAME = "indicators"
    SERVICE_TYPE = "signals"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._indicator_engine = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("IndicatorsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("IndicatorsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._indicator_engine else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Indicators components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.indicators import IndicatorEngine
            self._indicator_engine = IndicatorEngine()
            logger.info("IndicatorEngine loaded")
        except ImportError as e:
            logger.warning(f"IndicatorEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
