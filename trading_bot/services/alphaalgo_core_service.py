"""
AlphaAlgo Core Service
======================

Wraps AlphaAlgo Core module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlphaAlgoCoreService(BaseService):
    """
    AlphaAlgo Core Service - Central Governance and Control
    
    Provides:
    - AlphaAlgo orchestrator
    - Central controller (G0/G1/G2 hierarchy)
    - Governance system
    - Fail-safe system
    - Security core
    - Self-repair engine
    """
    
    SERVICE_NAME = "alphaalgo_core"
    SERVICE_TYPE = "governance"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._controller = None
        self._fail_safe = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlphaAlgoCoreService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlphaAlgoCoreService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._orchestrator is not None,
            self._controller is not None,
            self._fail_safe is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 AlphaAlgo Core components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alphaalgo_core import AlphaAlgoOrchestrator
            self._orchestrator = AlphaAlgoOrchestrator()
            logger.info("AlphaAlgoOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"AlphaAlgoOrchestrator not available: {e}")
        
        try:
            from trading_bot.alphaalgo_core import CentralController
            self._controller = CentralController()
            logger.info("CentralController loaded")
        except ImportError as e:
            logger.warning(f"CentralController not available: {e}")
        
        try:
            from trading_bot.alphaalgo_core import FailSafeSystem
            self._fail_safe = FailSafeSystem()
            logger.info("FailSafeSystem loaded")
        except ImportError as e:
            logger.warning(f"FailSafeSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
