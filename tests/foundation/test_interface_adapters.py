"""Tests for read-only dashboard/reporting/notification adapters."""

import pytest

from trading_bot.interfaces.adapters import (
    DashboardRuntimeAdapter,
    NotificationRuntimeAdapter,
    ReportingRuntimeAdapter,
)
from trading_bot.interfaces.read_models import ModularMonolithReadModel


class Runtime:
    running = True
    bot = type("Bot", (), {"execution_mode": "paper", "trading_repository": None})()

    def component_graph(self):
        return [{"name": "csc"}]

    async def health_check(self):
        return {"running": True, "components": {"csc": {"status": "running"}}}


@pytest.mark.asyncio
async def test_interface_adapters_are_read_only_projections() -> None:
    read_model = ModularMonolithReadModel(Runtime())

    dashboard = await DashboardRuntimeAdapter(read_model).snapshot()
    report = await ReportingRuntimeAdapter(read_model).report()
    notification = await NotificationRuntimeAdapter(read_model).health_alert()

    assert dashboard["status"]["running"] is True
    assert report["position_count"] == 0
    assert notification["event_type"] == "alphaalgo.health"
    assert notification["read_only"] is True
