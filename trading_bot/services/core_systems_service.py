"""
Core Systems Service
=====================

Wraps Core module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class CoreSystemsService(BaseService):
    """
    Core Systems Service - Central Trading System Components
    
    Provides:
    - Trading orchestrator
    - Circuit breaker manager
    - Monitoring system
    - Execution manager
    """
    
    SERVICE_NAME = "core_systems"
    SERVICE_TYPE = "core"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._circuit_breaker = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CoreSystemsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CoreSystemsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._orchestrator is not None, self._circuit_breaker is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Core Systems components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.core import TradingOrchestrator
            self._orchestrator = TradingOrchestrator
            logger.info("TradingOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"TradingOrchestrator not available: {e}")
        
        try:
            from trading_bot.core import CircuitBreakerManager
            self._circuit_breaker = CircuitBreakerManager()
            logger.info("CircuitBreakerManager loaded")
        except ImportError as e:
            logger.warning(f"CircuitBreakerManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
