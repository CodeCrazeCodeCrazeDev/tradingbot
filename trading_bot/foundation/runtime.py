"""Public modular-monolith application boundary for AlphaAlgo."""

from __future__ import annotations

from typing import Any, Dict, Iterator, Optional

from trading_bot.unified_bot import UnifiedTradingBot


class ModularMonolithRuntime:
    """Stable application boundary; delegates decisions to the canonical bot."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.bot = UnifiedTradingBot(config or {})

    @property
    def running(self) -> bool:
        return self.bot.running

    async def start(self) -> None:
        await self.bot.start()

    async def run(
        self,
        observations: Iterator[Dict[str, Any]],
        cycles: int = 0,
        interval: float = 1.0,
    ) -> None:
        await self.bot.run(observations, cycles=cycles, interval=interval)

    async def stop(self) -> None:
        await self.bot.stop()

    def component_graph(self) -> list:
        return self.bot.component_graph()

    async def health_check(self) -> Dict[str, Any]:
        return await self.bot.health_check()
