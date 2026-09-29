"""
SuperPowerful AI Orchestrator
============================================================

Facade over the superpowerful_ai intelligence modules with an
explicit operating mode.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIMode(Enum):
    BALANCED = "balanced"
    LEARNING = "learning"
    EVOLUTION = "evolution"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class SuperPowerfulAI:
    """Coordinates the superpowerful_ai capability modules."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        mode_raw = self.config.get("mode", "balanced")
        self.mode = (mode_raw if isinstance(mode_raw, AIMode)
                     else AIMode(str(mode_raw).lower()))
        self._modules: Dict[str, Any] = {}
        self._running = False
        logger.info(f"SuperPowerfulAI initialized (mode={self.mode.value})")

    def register_module(self, name: str, module: Any) -> None:
        self._modules[name] = module

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    def status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "running": self._running,
            "modules": sorted(self._modules.keys()),
        }

    async def process(self, payload: Any = None) -> Dict[str, Any]:
        return {"mode": self.mode.value, "processed": payload is not None}
