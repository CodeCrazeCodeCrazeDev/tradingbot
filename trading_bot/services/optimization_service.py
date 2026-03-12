"""
Optimization Service - Strategy Optimization
=============================================

Wraps Strategy Optimization capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class OptimizationService(BaseService):
    """
    Optimization Service - Strategy Optimization
    
    Provides:
    - Parameter optimization
    - Genetic algorithms
    - Bayesian optimization
    - Walk-forward optimization
    """
    
    SERVICE_NAME = "optimization"
    SERVICE_TYPE = "intelligence"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = ["backtesting"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        self._optimizer = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("OptimizationService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("OptimizationService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._optimizer else 0
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Optimization components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.optimization import StrategyOptimizer
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
