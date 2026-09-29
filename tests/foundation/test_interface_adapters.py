"""Tests for read-only dashboard/reporting/notification adapters."""

import warnings

import pytest

from trading_bot.interfaces.adapters import (
    DashboardRuntimeAdapter,
    NotificationRuntimeAdapter,
    ReportingRuntimeAdapter,
)
from trading_bot.foundation.runtime import ModularMonolithRuntime
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


@pytest.mark.asyncio
async def test_runtime_registers_interface_projections_as_read_only() -> None:
    runtime = ModularMonolithRuntime({"mode": "paper"})

    async def start_without_side_effects() -> None:
        runtime.bot.running = True

    runtime.bot.start = start_without_side_effects
    await runtime.start()

    graph = {component["name"]: component for component in runtime.component_graph()}
    for name in (
        "interface_read_model",
        "interface_dashboard_adapter",
        "interface_reporting_adapter",
        "interface_notification_adapter",
    ):
        assert graph[name]["type"] == "Interface"
        assert graph[name]["metadata"]["read_only"] is True
        assert graph[name]["metadata"]["capital_path"] == "none"
        assert graph[name]["dependencies"] == ["trading_repository"]


@pytest.mark.asyncio
async def test_unified_main_facade_delegates_to_canonical_runtime() -> None:
    from trading_bot.unified_main import UnifiedTradingSystem

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        system = UnifiedTradingSystem({"mode": "paper"})

    calls = []

    async def fake_run(observations, cycles=0, interval=1.0):
        calls.append((list(observations), cycles, interval))

    async def fake_start() -> None:
        system.runtime.bot.running = True

    system.runtime.bot.start = fake_start
    system.runtime.bot.run = fake_run
    await system.run(iter([{"symbol": "EURUSD", "price": 1.1}]), cycles=1, interval=0)

    assert calls == [([{"symbol": "EURUSD", "price": 1.1}], 1, 0)]
    assert any(item.category is DeprecationWarning for item in captured)
