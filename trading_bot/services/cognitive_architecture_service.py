"""
Cognitive Architecture Service
==============================

Wraps Cognitive Architecture module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class CognitiveArchitectureService(BaseService):
    """
    Cognitive Architecture Service - Multi-Layer Cognitive System
    
    Provides:
    - Cognitive core
    - Market state detection
    - Neuro-symbolic reasoning
    - Self-healing and auto-repair
    """
    
    SERVICE_NAME = "cognitive_architecture"
    SERVICE_TYPE = "cognitive"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._cognitive_core = None
        self._neuro_symbolic = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CognitiveArchitectureService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CognitiveArchitectureService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._cognitive_core is not None, self._neuro_symbolic is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Cognitive Architecture components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
            self._cognitive_core = AlphaAlgoCognitiveCore()
            logger.info("AlphaAlgoCognitiveCore loaded")
        except ImportError as e:
            logger.warning(f"AlphaAlgoCognitiveCore not available: {e}")
        
        try:
            from trading_bot.cognitive_architecture import NeuroSymbolicSystem
            self._neuro_symbolic = NeuroSymbolicSystem()
            logger.info("NeuroSymbolicSystem loaded")
        except ImportError as e:
            logger.warning(f"NeuroSymbolicSystem not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
