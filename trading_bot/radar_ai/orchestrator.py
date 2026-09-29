"""
RadarAI Orchestrator
============================================================

Top-level coordinator for the RadarAI subsystem: owns the agent
fleet, the operation mode, and aggregate system health.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    RESEARCH = "research"


class SystemHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


class RadarAISystem:
    """Container for the instantiated RadarAI components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mode = OperationMode(self.config.get("mode", "paper"))
        self.agents: Dict[str, Any] = {}
        self.started_at: Optional[datetime] = None

    def register(self, name: str, component: Any) -> None:
        self.agents[name] = component

    def status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "components": sorted(self.agents.keys()),
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


class RadarAIOrchestrator:
    """Coordinates RadarAI agents and subsystem lifecycle."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.system = RadarAISystem(config)
        self._running = False
        self._agents: Dict[str, Any] = {}

    def register_agent(self, name: str, agent: Any) -> None:
        self._agents[name] = agent
        self.system.register(name, agent)

    async def start(self) -> None:
        self._running = True
        self.system.started_at = datetime.now()
        for name, agent in self._agents.items():
            starter = getattr(agent, "start", None)
            if callable(starter):
                try:
                    res = starter()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"RadarAI agent {name} start failed: {e}")
        logger.info(f"RadarAIOrchestrator started ({self.system.mode.value}, {len(self._agents)} agents)")

    async def stop(self) -> None:
        self._running = False
        for name, agent in self._agents.items():
            stopper = getattr(agent, "stop", None)
            if callable(stopper):
                try:
                    res = stopper()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"RadarAI agent {name} stop failed: {e}")

    def health(self) -> SystemHealth:
        if not self._running:
            return SystemHealth.OFFLINE
        return SystemHealth.HEALTHY if self._agents else SystemHealth.DEGRADED
