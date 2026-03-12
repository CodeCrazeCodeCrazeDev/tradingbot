"""
Autonomous Pipeline Service
============================

Wraps Autonomous Pipeline module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AutonomousPipelineService(BaseService):
    """
    Autonomous Pipeline Service - Deployment and Discovery
    
    Provides:
    - Pipeline orchestrator
    - Discovery engine
    - Deployment pipeline
    - Rollback manager
    """
    
    SERVICE_NAME = "autonomous_pipeline"
    SERVICE_TYPE = "pipeline"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 120.0) if config else 120.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._discovery = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AutonomousPipelineService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AutonomousPipelineService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._orchestrator is not None, self._discovery is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Autonomous Pipeline components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.autonomous_pipeline import AutonomousPipelineOrchestrator
            self._orchestrator = AutonomousPipelineOrchestrator()
            logger.info("AutonomousPipelineOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"AutonomousPipelineOrchestrator not available: {e}")
        
        try:
            from trading_bot.autonomous_pipeline import DiscoveryEngine
            self._discovery = DiscoveryEngine()
            logger.info("DiscoveryEngine loaded")
        except ImportError as e:
            logger.warning(f"DiscoveryEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
