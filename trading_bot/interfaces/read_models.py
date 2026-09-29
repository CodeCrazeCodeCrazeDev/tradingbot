"""Read-only projections for API, CLI, dashboards, and operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from trading_bot.foundation.runtime import ModularMonolithRuntime


class ModularMonolithReadModel:
    """Expose runtime state without importing domain authorities directly."""

    def __init__(self, runtime: ModularMonolithRuntime):
        self.runtime = runtime

    def component_graph(self) -> list:
        return self.runtime.component_graph()

    async def health(self) -> Dict[str, Any]:
        return await self.runtime.health_check()

    async def portfolio(self, account_id: str = "runtime") -> Dict[str, Any]:
        repository = self.runtime.bot.trading_repository
        if repository is None:
            return {"account_id": account_id, "positions": [], "available": False}
        snapshot = await repository.snapshot(account_id)
        return snapshot.to_dict()

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.runtime.running,
            "component_count": len(self.component_graph()),
            "mode": self.runtime.bot.execution_mode,
        }

    async def dashboard_snapshot(self, account_id: str = "runtime") -> Dict[str, Any]:
        """Read-only projection for dashboards; no domain authority is exposed."""
        return {
            "status": self.status(),
            "health": await self.health(),
            "portfolio": await self.portfolio(account_id),
        }

    async def report_snapshot(self, account_id: str = "runtime") -> Dict[str, Any]:
        """Read-only projection for reporting and notifications."""
        snapshot = await self.portfolio(account_id)
        return {
            "account_id": account_id,
            "mode": self.runtime.bot.execution_mode,
            "component_count": len(self.component_graph()),
            "position_count": len(snapshot.get("positions", [])),
            "positions": snapshot.get("positions", []),
        }
