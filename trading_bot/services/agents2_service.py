"""
Agents2 Service
================

Wraps Agents2 module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class Agents2Service(BaseService):
    """
    Agents2 Service - Multi-Agent Coordination
    
    Provides:
    - Multi-agent coordinator
    - Risk manager agent
    - Specialized agents
    """
    
    SERVICE_NAME = "agents2"
    SERVICE_TYPE = "agents"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["agents"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._coordinator = None
        self._risk_agent = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Agents2Service started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Agents2Service stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([self._coordinator is not None, self._risk_agent is not None])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/2 Agents2 components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.agents2 import MultiAgentCoordinator
            self._coordinator = MultiAgentCoordinator()
            logger.info("MultiAgentCoordinator loaded")
        except ImportError as e:
            logger.warning(f"MultiAgentCoordinator not available: {e}")
        
        try:
            from trading_bot.agents2 import RiskManagerAgent
            self._risk_agent = RiskManagerAgent()
            logger.info("RiskManagerAgent loaded")
        except ImportError as e:
            logger.warning(f"RiskManagerAgent not available: {e}")
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
