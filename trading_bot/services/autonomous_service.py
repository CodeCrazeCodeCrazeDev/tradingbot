"""
Autonomous Service
==================

Wraps Autonomous module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AutonomousService(BaseService):
    """
    Autonomous Service - Self-Healing and Self-Optimization
    
    Provides:
    - Self-healing system
    - Self-optimizing engine
    - Self-checklist orchestrator
    - Self-memory system
    """
    
    SERVICE_NAME = "autonomous"
    SERVICE_TYPE = "autonomous"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._self_healing = None
        self._self_optimizing = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AutonomousService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AutonomousService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._self_healing is not None, self._self_optimizing is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Autonomous components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.autonomous import SelfHealingSystem
            self._self_healing = SelfHealingSystem()
            logger.info("SelfHealingSystem loaded")
        except ImportError as e:
            logger.warning(f"SelfHealingSystem not available: {e}")
        
        try:
            from trading_bot.autonomous import SelfOptimizingEngine
            self._self_optimizing = SelfOptimizingEngine()
            logger.info("SelfOptimizingEngine loaded")
        except ImportError as e:
            logger.warning(f"SelfOptimizingEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
