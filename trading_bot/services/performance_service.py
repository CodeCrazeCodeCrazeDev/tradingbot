"""
Performance Service - Performance Tracking
============================================

Wraps Performance tracking capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class PerformanceService(BaseService):
    """
    Performance Service - Performance Tracking
    
    Provides:
    - P&L tracking
    - Performance metrics
    - Sharpe ratio calculation
    - Drawdown analysis
    """
    
    SERVICE_NAME = "performance"
    SERVICE_TYPE = "orchestration"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["database"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._performance_tracker = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PerformanceService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("PerformanceService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._performance_tracker else 0
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Performance components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.performance import PerformanceTracker
            self._performance_tracker = PerformanceTracker()
            logger.info("PerformanceTracker loaded")
        except ImportError as e:
            logger.warning(f"PerformanceTracker not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
