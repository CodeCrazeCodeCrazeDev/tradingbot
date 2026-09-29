"""Compatibility facade for the former parallel master trading system.

The previous implementation constructed its own signal, data, security, risk,
execution, and AI authorities. Those paths are superseded by
`ModularMonolithRuntime -> UnifiedTradingBot`; this module preserves the legacy
class/function names only as a one-wave delegation surface.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, Dict, Optional

from trading_bot.foundation.runtime import ModularMonolithRuntime
from trading_bot.interfaces.read_models import ModularMonolithReadModel

logger = logging.getLogger(__name__)


class MasterTradingSystem:
    """One-wave facade over the canonical modular-monolith runtime."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        warnings.warn(
            "MasterTradingSystem is a compatibility facade; use "
            "ModularMonolithRuntime and UnifiedTradingBot instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self.runtime = ModularMonolithRuntime(self.config)
        self.read_model = ModularMonolithReadModel(self.runtime)

    async def start(self) -> None:
        await self.runtime.start()

    async def stop(self) -> None:
        await self.runtime.stop()

    async def execute_complete_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a legacy trade request through the canonical decision path."""
        symbol = signal.get("symbol")
        price = signal.get("price", signal.get("close"))
        if symbol is None or price is None:
            return {
                "status": "REJECTED",
                "reason": "Missing symbol/price for canonical market observation",
                "canonical_runtime": "ModularMonolithRuntime",
            }

        await self.runtime.start()
        observation = dict(signal)
        observation["symbol"] = symbol
        observation["price"] = price
        decision = await self.runtime.bot.run_cycle(observation)
        if decision is None:
            return {
                "status": "REJECTED",
                "reason": "Canonical runtime produced no executable decision",
                "canonical_runtime": "ModularMonolithRuntime",
            }
        return {
            "status": "DELEGATED",
            "decision": getattr(decision, "to_dict", lambda: decision)(),
            "canonical_runtime": "ModularMonolithRuntime",
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Return the canonical runtime status instead of fabricated completeness."""
        status = self.read_model.status()
        status.update({
            "status": "running" if self.runtime.running else "stopped",
            "canonical_runtime": "ModularMonolithRuntime",
            "read_only": True,
        })
        return status


def create_master_system(config: Optional[Dict[str, Any]] = None) -> MasterTradingSystem:
    """Create the compatibility facade."""
    return MasterTradingSystem(config)


__all__ = ["MasterTradingSystem", "create_master_system"]
