"""
Continuous Orchestrator
============================================================

Runs the neuros_evolution improvement loop on an interval.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    cycle_interval_seconds: float = 300.0
    max_cycles: Optional[int] = None
    require_approval: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContinuousOrchestrator:
    """Periodically invokes improvement-cycle callbacks."""

    def __init__(self, config: Optional[OrchestrationConfig] = None):
        self.config = config or OrchestrationConfig()
        self._callbacks: List[Any] = []
        self._running = False
        self._cycles_completed = 0

    def register_cycle(self, callback: Any) -> None:
        self._callbacks.append(callback)

    async def run_cycle(self) -> Dict[str, Any]:
        results = {}
        for i, cb in enumerate(self._callbacks):
            try:
                res = cb()
                results[i] = await res if asyncio.iscoroutine(res) else res
            except Exception as e:
                results[i] = {"error": str(e)}
        self._cycles_completed += 1
        return results

    async def run(self) -> None:
        self._running = True
        while self._running:
            if self.config.max_cycles and self._cycles_completed >= self.config.max_cycles:
                break
            await self.run_cycle()
            await asyncio.sleep(self.config.cycle_interval_seconds)

    def stop(self) -> None:
        self._running = False

    def status(self) -> Dict[str, Any]:
        return {"running": self._running,
                "cycles_completed": self._cycles_completed,
                "callbacks": len(self._callbacks)}
