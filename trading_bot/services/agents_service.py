"""
Agents Service
==============

Wraps Agents module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AgentsService(BaseService):
    """
    Agents Service
    
    Provides multi-agent debate and decision-making:
    - Multi-agent debate system
    - Executor agent
    - Planner agent
    - Verifier agent
    """
    
    SERVICE_NAME = "agents"
    SERVICE_TYPE = "agents"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["ai_analysis"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        self._debate_system = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.SIGNAL_GENERATED],
                self._on_signal
            )
        logger.info("AgentsService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        logger.info("AgentsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = 1 if self._debate_system else 0
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Agents components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.agents import MultiAgentDebateSystem
            self._debate_system = MultiAgentDebateSystem()
            logger.info("MultiAgentDebateSystem loaded")
        except ImportError as e:
            logger.warning(f"MultiAgentDebateSystem not available: {e}")
    
    async def _on_signal(self, event: Event) -> None:
        pass
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
