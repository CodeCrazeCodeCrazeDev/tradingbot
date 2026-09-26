"""
Autonomous Superintelligence Meta-Orchestrator
============================================================

Meta-level coordinator: registers subsystem engines, sequences
their lifecycle, and surfaces an aggregate status. Distinct from
the class-level `AutonomousSuperintelligence` facade — this is
the scheduling/registry layer underneath it.
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetaOrchestrator:
    """Schedules and supervises the subsystem's engines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        import warnings
        warnings.warn(
            "MetaOrchestrator is a deprecated duplicate; canonical "
            "orchestrator is trading_bot.core.csc.controller."
            "CognitiveSystemController.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self._engines: Dict[str, Any] = {}
        self._task_queue: Deque[Dict[str, Any]] = deque()
        self._running = False
        self._history: List[Dict[str, Any]] = []

    def register(self, name: str, engine: Any) -> None:
        self._engines[name] = engine
        logger.debug(f"MetaOrchestrator: registered {name}")

    def submit_task(self, task: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._task_queue.append({"task": task, "payload": payload or {},
                                 "queued_at": datetime.now().isoformat()})

    async def dispatch_next(self) -> Optional[Dict[str, Any]]:
        """Route the next queued task to the first engine that handles it."""
        if not self._task_queue:
            return None
        item = self._task_queue.popleft()
        for name, eng in self._engines.items():
            handler = getattr(eng, "handle_task", None) or getattr(eng, "execute_task", None)
            if callable(handler):
                try:
                    res = handler(item["task"], item["payload"])
                    res = await res if asyncio.iscoroutine(res) else res
                    result = {"task": item["task"], "engine": name, "result": res}
                    self._history.append(result)
                    return result
                except Exception as e:
                    logger.warning(f"MetaOrchestrator: {name} failed on {item['task']}: {e}")
        result = {"task": item["task"], "engine": None, "result": {"status": "unhandled"}}
        self._history.append(result)
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "engines": sorted(self._engines.keys()),
            "queued": len(self._task_queue),
            "dispatched": len(self._history),
        }

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
