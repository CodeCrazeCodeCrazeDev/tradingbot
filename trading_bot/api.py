"""Legacy API manager compatibility facade."""

from __future__ import annotations

import warnings
from typing import Any, Dict, Optional

from trading_bot.foundation.runtime import ModularMonolithRuntime
from trading_bot.interfaces.read_models import ModularMonolithReadModel


class APIManager:
    """One-wave read-only facade over the canonical runtime."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "APIManager is a compatibility facade; use ModularMonolithRuntime and read models.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config: Dict[str, Any] = kwargs.get("config", {})
        self.runtime = ModularMonolithRuntime(self.config)
        self.read_model = ModularMonolithReadModel(self.runtime)
        self.running = False

    async def start(self) -> None:
        await self.runtime.start()
        self.running = True

    async def stop(self) -> None:
        await self.runtime.stop()
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        return {
            **self.read_model.status(),
            "running": self.running,
            "canonical_runtime": "ModularMonolithRuntime",
            "read_only": True,
        }
