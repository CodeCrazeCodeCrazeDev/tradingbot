"""
Critical Fixes Service
======================

Wraps Critical Fixes module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class CriticalFixesService(BaseService):
    """
    Critical Fixes Service - Safety and Position Management
    
    Provides:
    - Master safety orchestrator
    - Position state manager
    """
    
    SERVICE_NAME = "critical_fixes"
    SERVICE_TYPE = "safety"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        self._safety_orchestrator = None
        self._position_manager = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CriticalFixesService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CriticalFixesService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._safety_orchestrator is not None, self._position_manager is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Critical Fixes components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.critical_fixes import MasterSafetyOrchestrator
            self._safety_orchestrator = MasterSafetyOrchestrator()
            logger.info("MasterSafetyOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"MasterSafetyOrchestrator not available: {e}")
        
        try:
            from trading_bot.critical_fixes import PositionStateManager
            self._position_manager = PositionStateManager()
            logger.info("PositionStateManager loaded")
        except ImportError as e:
            logger.warning(f"PositionStateManager not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
