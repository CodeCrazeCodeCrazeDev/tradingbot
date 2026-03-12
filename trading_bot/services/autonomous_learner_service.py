"""
Autonomous Learner Service
==========================

Wraps Autonomous Learner module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AutonomousLearnerService(BaseService):
    """
    Autonomous Learner Service - Continuous Learning
    
    Provides:
    - Learning orchestrator
    """
    
    SERVICE_NAME = "autonomous_learner"
    SERVICE_TYPE = "learning"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["ai_core"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AutonomousLearnerService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AutonomousLearnerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._orchestrator else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Autonomous Learner components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.autonomous_learner import LearningOrchestrator
            self._orchestrator = LearningOrchestrator()
            logger.info("LearningOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"LearningOrchestrator not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
