"""
AlphaAlgo V2 Service
====================

Wraps AlphaAlgo V2 module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlphaAlgoV2Service(BaseService):
    """
    AlphaAlgo V2 Service - Next-Generation Trading System
    
    Provides:
    - V2 orchestrator
    - Evolution engine
    - Reward engine
    - Risk engine
    """
    
    SERVICE_NAME = "alphaalgo_v2"
    SERVICE_TYPE = "trading"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["alphaalgo_core"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlphaAlgoV2Service started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlphaAlgoV2Service stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._orchestrator else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 AlphaAlgo V2 components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alphaalgo_v2 import AlphaAlgoOrchestrator
            self._orchestrator = AlphaAlgoOrchestrator()
            logger.info("AlphaAlgoOrchestrator V2 loaded")
        except ImportError as e:
            logger.warning(f"AlphaAlgoOrchestrator V2 not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
