"""
DeepChart Service
=================

Wraps DeepChart module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DeepChartService(BaseService):
    """
    DeepChart Service - Advanced Chart Analysis
    
    Provides:
    - DeepChart orchestrator
    - Inference engine
    - Intent orchestrator
    - Market intelligence orchestrator
    """
    
    SERVICE_NAME = "deepchart"
    SERVICE_TYPE = "analysis"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._inference = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DeepChartService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DeepChartService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._orchestrator is not None, self._inference is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 DeepChart components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.deepchart import DeepChartOrchestrator
            self._orchestrator = DeepChartOrchestrator()
            logger.info("DeepChartOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"DeepChartOrchestrator not available: {e}")
        
        try:
            from trading_bot.deepchart import InferenceEngine
            self._inference = InferenceEngine()
            logger.info("InferenceEngine loaded")
        except ImportError as e:
            logger.warning(f"InferenceEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
