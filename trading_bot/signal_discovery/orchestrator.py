"""
Signal Discovery Orchestrator
============================================================

Coordinates the Layer-1 anomaly-hunting agents: registers them,
runs detection sweeps, aggregates MarketAnomaly reports, and
exposes health/status summaries to upstream layers.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .agents.base_agent import BaseAnomalyAgent, MarketAnomaly, AgentHealth

logger = logging.getLogger(__name__)


class SignalDiscoveryOrchestrator:
    """Manages the fleet of anomaly-detection agents."""

    def __init__(self, check_interval_seconds: float = 60.0):
        self.check_interval_seconds = check_interval_seconds
        self._agents: List[BaseAnomalyAgent] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._anomaly_log: List[MarketAnomaly] = []
        self._max_log = 5000

    def register_agent(self, agent: BaseAnomalyAgent) -> None:
        self._agents.append(agent)
        logger.info(f"Orchestrator: registered {agent.agent_type} ({agent.agent_id})")

    def spawn_default_agents(self) -> int:
        """Instantiate one of each bundled agent type."""
        spawned = 0
        from .agents.financial_api_agents import FinancialAPIAgent
        from .agents.research_paper_agents import ResearchPaperAgent
        from .agents.social_media_agents import SocialMediaAgent
        from .agents.dark_pool_agents import DarkPoolAgent
        from .agents.developer_activity_agents import DeveloperActivityAgent
        from .agents.protocol_launch_agents import ProtocolLaunchAgent
        from .agents.economic_release_agents import EconomicReleaseAgent
        for cls in (FinancialAPIAgent, ResearchPaperAgent, SocialMediaAgent,
                    DarkPoolAgent, DeveloperActivityAgent, ProtocolLaunchAgent,
                    EconomicReleaseAgent):
            try:
                self.register_agent(cls(agent_id=f"{cls.__name__.lower()}_0"))
                spawned += 1
            except Exception as e:
                logger.warning(f"Orchestrator: could not spawn {cls.__name__}: {e}")
        return spawned

    async def sweep(self) -> List[MarketAnomaly]:
        """Run one detection pass across all agents; return new anomalies."""
        found: List[MarketAnomaly] = []
        for agent in self._agents:
            try:
                anomalies = await agent.detect_anomalies()
            except Exception as e:
                logger.warning(f"Orchestrator: {agent.agent_id} sweep failed: {e}")
                continue
            for a in anomalies or []:
                found.append(a)
                self._anomaly_log.append(a)
        if len(self._anomaly_log) > self._max_log:
            self._anomaly_log = self._anomaly_log[-self._max_log:]
        return found

    async def run(self) -> None:
        """Continuously sweep all agents until stopped."""
        self._running = True
        while self._running:
            await self.sweep()
            await asyncio.sleep(self.check_interval_seconds)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.ensure_future(self.run())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def health(self) -> Dict[str, Any]:
        return {
            "agents": len(self._agents),
            "running": self._running,
            "anomalies_logged": len(self._anomaly_log),
            "agent_health": {a.agent_id: getattr(a, "_health", None) for a in self._agents},
        }

    def recent_anomalies(self, limit: int = 50) -> List[MarketAnomaly]:
        return self._anomaly_log[-limit:]
