"""AlphaAlgo Orchestrator - flat-path shim with minimal deleted-class shims."""

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List

from trading_bot.foundation.runtime import ModularMonolithRuntime

try:
    from trading_bot.alphaalgo_core.fail_safe import *  # noqa: F401,F403
    from trading_bot.alphaalgo_core.fail_safe import SafetyCheckResult  # noqa: F401
except ImportError:
    pass


@dataclass
class AlphaAlgoConfig:
    """Top-level AlphaAlgo orchestration config."""

    mode: str = "paper"
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    risk_per_trade: float = 0.02
    max_positions: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlphaAlgoOrchestrator:
    """Minimal system-level orchestrator for AlphaAlgo subsystems."""

    def __init__(self, config: AlphaAlgoConfig = None):
        warnings.warn(
            "AlphaAlgoOrchestrator is a compatibility facade; use "
            "ModularMonolithRuntime instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or AlphaAlgoConfig()
        self.running = False
        self.modules: Dict[str, Any] = {}
        self._runtime = ModularMonolithRuntime({
            "mode": self.config.mode,
            "symbols": self.config.symbols,
            "risk_per_trade": self.config.risk_per_trade,
            "max_positions": self.config.max_positions,
            **self.config.metadata,
        })

    async def start(self):
        await self._runtime.start()
        self.running = True
        self.modules = {
            item["name"]: item for item in self._runtime.component_graph()
        }

    async def stop(self):
        await self._runtime.stop()
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "operational" if self.running else "stopped",
            "running": self.running,
            "mode": self.config.mode,
            "component_count": len(self.modules),
            "canonical_runtime": "ModularMonolithRuntime",
        }
