"""
AI Engineer Service
===================

Wraps AI Engineer module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AIEngineerService(BaseService):
    """
    AI Engineer Service - Autonomous Orchestration with Safeguards
    
    Provides:
    - Autonomous orchestrator
    - Integrated safeguard system
    - Safe code generation
    """
    
    SERVICE_NAME = "ai_engineer"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["ai_core"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 180.0) if config else 180.0
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._safeguards = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AIEngineerService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AIEngineerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._orchestrator is not None, self._safeguards is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 AI Engineer components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.ai_engineer import AutonomousOrchestrator
            self._orchestrator = AutonomousOrchestrator()
            logger.info("AutonomousOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"AutonomousOrchestrator not available: {e}")
        
        try:
            from trading_bot.ai_engineer import SafeguardSystem
            self._safeguards = SafeguardSystem()
            logger.info("SafeguardSystem loaded")
        except ImportError as e:
            logger.warning(f"SafeguardSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
