"""
Decision Layer Service
======================

Wraps Decision Layer module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class DecisionLayerService(BaseService):
    """
    Decision Layer Service - Trading Decision Engine
    
    Provides:
    - Innovative decision engine
    - Meta decision orchestrator
    """
    
    SERVICE_NAME = "decision_layer"
    SERVICE_TYPE = "decision"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["integrated_brain"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        self._brain_service = None
        
    async def start(self) -> None:
        self._running = True

        # Get reference to the brain service
        registry = self.get_registry()
        if registry:
            self._brain_service = registry.get_service("integrated_brain")

        self._task = asyncio.create_task(self._run_loop())
        logger.info("DecisionLayerService started (Consolidated to IntegratedBrain)")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DecisionLayerService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._decision_engine else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Decision Layer components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.decision_layer import InnovativeDecisionEngine
            self._decision_engine = InnovativeDecisionEngine()
            logger.info("InnovativeDecisionEngine loaded")
        except ImportError as e:
            logger.warning(f"InnovativeDecisionEngine not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                if self._brain_service:
                    # Periodically request top-level decision from the brain
                    task_desc = "Evaluate overall market state and propose next strategic action"
                    result = await self._brain_service.execute_task(task_desc)
                    logger.debug(f"Strategic update: {result.get('success')}")

                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decision loop error: {e}")
                await asyncio.sleep(self._interval)
