"""
Auto Optimizer Service
======================

Wraps Auto Optimizer module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AutoOptimizerService(BaseService):
    """
    Auto Optimizer Service - Strategy Optimization
    
    Provides:
    - Strategy optimizer
    - Genetic optimizer
    - Bayesian optimizer
    - Grid search optimizer
    """
    
    SERVICE_NAME = "auto_optimizer"
    SERVICE_TYPE = "optimization"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = ["backtesting"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 600.0) if config else 600.0
        self._task: Optional[asyncio.Task] = None
        self._optimizer = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AutoOptimizerService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AutoOptimizerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._optimizer else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Auto Optimizer components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.auto_optimizer import StrategyOptimizer
            self._optimizer = StrategyOptimizer()
            logger.info("StrategyOptimizer loaded")
        except ImportError as e:
            logger.warning(f"StrategyOptimizer not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
