"""
AI Service
==========

Wraps AI module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AIService(BaseService):
    """
    AI Service - Autonomous Tuning and Self-Optimization
    
    Provides:
    - Autonomous tuner
    - Genetic optimizer
    - Bayesian optimizer
    - AI optimizer
    - Model optimizer
    """
    
    SERVICE_NAME = "ai"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 120.0) if config else 120.0
        self._task: Optional[asyncio.Task] = None
        self._tuner = None
        self._optimizer = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AIService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AIService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._tuner is not None, self._optimizer is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 AI components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.ai import AutonomousTuner
            self._tuner = AutonomousTuner()
            logger.info("AutonomousTuner loaded")
        except ImportError as e:
            logger.warning(f"AutonomousTuner not available: {e}")
        
        try:
            from trading_bot.ai import AIOptimizer
            self._optimizer = AIOptimizer()
            logger.info("AIOptimizer loaded")
        except ImportError as e:
            logger.warning(f"AIOptimizer not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
