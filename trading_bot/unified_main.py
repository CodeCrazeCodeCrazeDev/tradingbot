"""Compatibility facade for the former standalone unified entry point.

`UnifiedTradingSystem` previously owned a second lifecycle and trading loop.
It now delegates all lifecycle and observation processing to
`ModularMonolithRuntime`; no code in this module may create a parallel decision,
risk, execution, or broker authority.
"""

from __future__ import annotations

import asyncio
import logging
import warnings
from typing import Any, Dict, Iterator, Optional

from trading_bot.foundation.runtime import ModularMonolithRuntime
from trading_bot.interfaces.read_models import ModularMonolithReadModel

logger = logging.getLogger(__name__)


class UnifiedTradingSystem:
    """One-wave compatibility facade over the canonical runtime."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        warnings.warn(
            "UnifiedTradingSystem is a compatibility facade; use "
            "ModularMonolithRuntime or python main.py instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config or {}
        self.runtime = ModularMonolithRuntime(self.config)
        self.read_model = ModularMonolithReadModel(self.runtime)

    @property
    def running(self) -> bool:
        return self.runtime.running

    async def start(self) -> None:
        await self.runtime.start()

    async def stop(self) -> None:
        await self.runtime.stop()

    async def run(
        self,
        observations: Optional[Iterator[Dict[str, Any]]] = None,
        cycles: int = 0,
        interval: float = 1.0,
    ) -> None:
        """Delegate observation processing to the canonical runtime."""
        source = observations if observations is not None else self.config.get("observations", ())
        await self.runtime.run(iter(source), cycles=cycles, interval=interval)

    def get_status(self) -> Dict[str, Any]:
        """Return a read-only compatibility status projection."""
        status = self.read_model.status()
        status.update({
            "status": "running" if self.running else "stopped",
            "trading_mode": self.runtime.bot.execution_mode,
            "canonical_runtime": "ModularMonolithRuntime",
            "trading_allowed": self.runtime.bot.trading_allowed(),
        })
        return status

    async def health(self) -> Dict[str, Any]:
        return await self.read_model.health()

    async def portfolio(self, account_id: str = "runtime") -> Dict[str, Any]:
        return await self.read_model.portfolio(account_id)

    def get_constraints(self) -> Dict[str, Any]:
        """Read constraints from the runtime's evolution capability when wired."""
        evolution = self.runtime.bot.layers.get("evolution", {})
        reward_model = evolution.get("reward_model")
        constraints = getattr(reward_model, "get_constraints_dict", None)
        if callable(constraints):
            return constraints()
        return {}

    def _approval_gate(self) -> Any:
        human = self.runtime.bot.layers.get("human", {})
        return human.get("approval_gate")

    async def request_approval(self, action: str, description: str, details: Dict[str, Any]) -> bool:
        """Delegate to the canonical human gate; fail closed when unavailable."""
        gate = self._approval_gate()
        request = getattr(gate, "request_approval", None)
        if not callable(request):
            logger.warning("UnifiedTradingSystem: human approval gate unavailable")
            return False
        result = request(action, description, details)
        if hasattr(result, "__await__"):
            result = await result
        return bool(result)

    def approve_request(self, request_id: str, approver: str) -> bool:
        gate = self._approval_gate()
        approve = getattr(gate, "approve", None)
        if not callable(approve):
            return False
        return bool(approve(request_id, approver))

    def reject_request(self, request_id: str, reason: str) -> bool:
        gate = self._approval_gate()
        reject = getattr(gate, "reject", None)
        if not callable(reject):
            return False
        return bool(reject(request_id, reason))


async def main(config: Optional[Dict[str, Any]] = None) -> None:
    """Run the compatibility facade against configured observations."""
    system = UnifiedTradingSystem(config)
    await system.run()


def run(config: Optional[Dict[str, Any]] = None) -> None:
    """Synchronous compatibility entry point."""
    try:
        asyncio.run(main(config))
    except KeyboardInterrupt:
        logger.info("Shutdown requested")


def __getattr__(name: str) -> Any:
    """Preserve lazy legacy imports without initializing the removed system."""
    if name in {"TradingMode", "SystemStatus", "HealthStatus", "EventBus", "EventType", "create_system_event"}:
        from . import core_api
        return getattr(core_api, name)
    raise AttributeError(name)


__all__ = [
    "UnifiedTradingSystem",
    "main",
    "run",
    "TradingMode",
    "SystemStatus",
    "HealthStatus",
    "EventBus",
    "EventType",
    "create_system_event",
]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    print(
        "DEPRECATED: unified_main.py standalone entry is superseded by the "
        "modular-monolith runtime.\nUse `python main.py`; redirecting to the "
        "canonical entry point..."
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from main import main as _unified_main
    asyncio.run(_unified_main())
