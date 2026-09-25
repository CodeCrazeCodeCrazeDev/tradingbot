"""Read-only dashboard, reporting, and notification interface adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .read_models import ModularMonolithReadModel


class DashboardRuntimeAdapter:
    """Dashboard projection adapter; never mutates trading state."""

    def __init__(self, read_model: ModularMonolithReadModel):
        self.read_model = read_model

    async def snapshot(self, account_id: str = "runtime") -> Dict[str, Any]:
        return await self.read_model.dashboard_snapshot(account_id)


class ReportingRuntimeAdapter:
    """Reporting projection adapter over authoritative repository/read models."""

    def __init__(self, read_model: ModularMonolithReadModel):
        self.read_model = read_model

    async def report(self, account_id: str = "runtime") -> Dict[str, Any]:
        return await self.read_model.report_snapshot(account_id)


class NotificationRuntimeAdapter:
    """Build notification payloads from projections without sending orders/actions."""

    def __init__(self, read_model: ModularMonolithReadModel):
        self.read_model = read_model

    async def health_alert(self, account_id: str = "runtime") -> Dict[str, Any]:
        health = await self.read_model.health()
        return {
            "event_type": "alphaalgo.health",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "account_id": account_id,
            "health": health,
            "read_only": True,
        }
