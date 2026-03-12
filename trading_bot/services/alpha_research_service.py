"""
Alpha Research Service
======================

Wraps Alpha Research module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlphaResearchService(BaseService):
    """
    Alpha Research Service - Research and Strategy Development
    
    Provides:
    - Alpha research orchestrator
    - Feature mining system
    - Unified alpha brain
    - Sandbox testing
    - Live deployment
    """
    
    SERVICE_NAME = "alpha_research"
    SERVICE_TYPE = "research"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["alpha_engine"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._feature_mining = None
        self._alpha_brain = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlphaResearchService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlphaResearchService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._orchestrator is not None,
            self._feature_mining is not None,
            self._alpha_brain is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 Alpha Research components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alpha_research import AlphaResearchOrchestrator
            self._orchestrator = AlphaResearchOrchestrator()
            logger.info("AlphaResearchOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"AlphaResearchOrchestrator not available: {e}")
        
        try:
            from trading_bot.alpha_research import FeatureMiningSystem
            self._feature_mining = FeatureMiningSystem()
            logger.info("FeatureMiningSystem loaded")
        except ImportError as e:
            logger.warning(f"FeatureMiningSystem not available: {e}")
        
        try:
            from trading_bot.alpha_research import UnifiedAlphaBrain
            self._alpha_brain = UnifiedAlphaBrain()
            logger.info("UnifiedAlphaBrain loaded")
        except ImportError as e:
            logger.warning(f"UnifiedAlphaBrain not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
