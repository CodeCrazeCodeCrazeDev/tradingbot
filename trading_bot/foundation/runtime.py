"""Public modular-monolith application boundary for AlphaAlgo."""

from __future__ import annotations

from typing import Any, Dict, Iterator, Optional

from trading_bot.unified_bot import UnifiedTradingBot


class ModularMonolithRuntime:
    """Stable application boundary; delegates decisions to the canonical bot."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.bot = UnifiedTradingBot(config or {})
        self.read_model = None
        self.dashboard_adapter = None
        self.reporting_adapter = None
        self.notification_adapter = None

    @property
    def running(self) -> bool:
        return self.bot.running

    async def start(self) -> None:
        await self.bot.start()
        await self._register_interface_projections()

    async def _register_interface_projections(self) -> None:
        """Register read-only projections in the canonical component graph."""
        from trading_bot.core.unified_registry import registry
        from trading_bot.interfaces.adapters import (
            DashboardRuntimeAdapter,
            NotificationRuntimeAdapter,
            ReportingRuntimeAdapter,
        )
        from trading_bot.interfaces.read_models import ModularMonolithReadModel

        self.read_model = ModularMonolithReadModel(self)
        self.dashboard_adapter = DashboardRuntimeAdapter(self.read_model)
        self.reporting_adapter = ReportingRuntimeAdapter(self.read_model)
        self.notification_adapter = NotificationRuntimeAdapter(self.read_model)

        components = {
            "read_model": self.read_model,
            "dashboard_adapter": self.dashboard_adapter,
            "reporting_adapter": self.reporting_adapter,
            "notification_adapter": self.notification_adapter,
        }
        metadata = {"read_only": True, "capital_path": "none"}
        for name, component in components.items():
            registry.register(
                f"interface_{name}",
                component,
                "Interface",
                dependencies=["trading_repository"],
                metadata=metadata,
                overwrite=True,
            )

    async def run(
        self,
        observations: Iterator[Dict[str, Any]],
        cycles: int = 0,
        interval: float = 1.0,
    ) -> None:
        await self.start()
        await self.bot.run(observations, cycles=cycles, interval=interval)

    async def stop(self) -> None:
        await self.bot.stop()

    def component_graph(self) -> list:
        return self.bot.component_graph()

    async def health_check(self) -> Dict[str, Any]:
        return await self.bot.health_check()
