"""
Integrated Brain Service
========================

Wraps the Research-Grade IntegratedAgentSystem as an event-driven service.
This makes IAS the central brain for the entire AlphaAlgo ecosystem.
"""

import warnings
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core.event_bus import Event, EventTypes

logger = logging.getLogger(__name__)


class IntegratedBrainService(BaseService):
    """
    Integrated Brain Service - Unified AI Controller

    Provides:
    - Research-grade agent coordination
    - Autonomous self-improvement
    - Multi-agent swarm intelligence
    """

    SERVICE_NAME = "integrated_brain"
    SERVICE_TYPE = "intelligence"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["analysis", "risk", "msos"]

    def __init__(self, config: Optional[Dict] = None):
        warnings.warn("IntegratedBrainService is a legacy/quarantined component: loop/capital surface outside the canonical runtime. It carries no production authority.", DeprecationWarning, stacklevel=2)
        super().__init__(config)
        self.brain: Optional[IntegratedAgentSystem] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True

        # Initialize the actual IAS brain
        self.brain = IntegratedAgentSystem(self.config)
        await self.brain.initialize()

        # IAS background task disabled: the integrated agent system is a
        # parallel production authority; the canonical runtime owns it.
        self._task = None
        logger.warning("Integrated brain service worker disabled; canonical runtime owns the loop")

        # Subscribe to relevant events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.ALPHA_SIGNAL],
                self._on_event
            )

        logger.info("IntegratedBrainService started and IAS initialized")

    async def stop(self) -> None:
        self._running = False
        if self.brain:
            await self.brain.shutdown()
        if self._task:
            self._task.cancel()
        logger.info("IntegratedBrainService stopped")

    async def health_check(self) -> ServiceHealth:
        healthy = self._running and self.brain and self.brain.running
        status = self.brain.get_comprehensive_status() if self.brain else {}

        return ServiceHealth(
            healthy=healthy,
            last_check=datetime.utcnow(),
            message="IAS Operational" if healthy else "IAS Offline",
            metrics={
                'agents': status.get('agents', {}).get('total_agents', 0),
                'iteration': status.get('self_play', {}).get('iteration', 0)
            }
        )

    async def _on_event(self, event: Event) -> None:
        """Handle incoming events and route to IAS for task execution"""
        if not self.brain or not self._running:
            return

        # Signal->execution routing disabled: agent-to-execution edges are
        # forbidden — only the canonical CSC->risk->shield->execution path
        # may act on alpha signals.
        if event.event_type == EventTypes.ALPHA_SIGNAL:
            logger.warning(
                "Alpha signal routing to legacy brain disabled; canonical "
                "decision path owns signal handling"
            )

    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Direct interface to the brain"""
        if not self.brain:
            return {'success': False, 'error': 'Brain not initialized'}
        return await self.brain.execute_task(task, context)
