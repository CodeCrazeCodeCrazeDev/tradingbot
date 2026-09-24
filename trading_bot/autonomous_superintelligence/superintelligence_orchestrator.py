"""
Autonomous Superintelligence Orchestrator
============================================================

Coordinates the autonomous_superintelligence subsystem engines
(research, experiments, resources, discovery) behind one facade.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutonomousSuperintelligence:
    """Facade coordinating the autonomous superintelligence engines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._engines: Dict[str, Any] = {}
        self._running = False
        self.started_at: Optional[datetime] = None
        logger.info("AutonomousSuperintelligence initialized")

    def register_engine(self, name: str, engine: Any) -> None:
        self._engines[name] = engine

    async def start(self) -> None:
        self._running = True
        self.started_at = datetime.now()
        for name, eng in self._engines.items():
            starter = getattr(eng, "start", None)
            if callable(starter):
                try:
                    res = starter()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"Engine {name} start failed: {e}")

    async def stop(self) -> None:
        self._running = False
        for name, eng in self._engines.items():
            stopper = getattr(eng, "stop", None)
            if callable(stopper):
                try:
                    res = stopper()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    logger.warning(f"Engine {name} stop failed: {e}")

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "engines": sorted(self._engines.keys()),
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }

    async def step(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one coordination step across engines that expose it."""
        results = {}
        for name, eng in self._engines.items():
            fn = getattr(eng, "step", None) or getattr(eng, "run_once", None)
            if callable(fn):
                try:
                    res = fn(context or {})
                    results[name] = await res if asyncio.iscoroutine(res) else res
                except Exception as e:
                    results[name] = {"error": str(e)}
        return results
