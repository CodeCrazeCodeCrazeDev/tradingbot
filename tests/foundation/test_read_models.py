"""Tests for read-only modular-monolith interface projections."""

import pytest

from trading_bot.foundation.contracts import PortfolioSnapshot
from trading_bot.interfaces.read_models import ModularMonolithReadModel


class Repository:
    async def snapshot(self, account_id):
        return PortfolioSnapshot(account_id, 1000, 1000)


class Runtime:
    running = True
    bot = type("Bot", (), {"execution_mode": "paper", "trading_repository": Repository()})()

    def component_graph(self):
        return [{"name": "csc", "type": "Controller"}]

    async def health_check(self):
        return {"running": True, "components": {"csc": {"status": "running"}}}


@pytest.mark.asyncio
async def test_read_model_exposes_health_graph_and_portfolio() -> None:
    read_model = ModularMonolithReadModel(Runtime())

    assert read_model.status()["component_count"] == 1
    assert read_model.component_graph()[0]["name"] == "csc"
    assert (await read_model.health())["running"] is True
    assert (await read_model.portfolio())["account_id"] == "runtime"
    dashboard = await read_model.dashboard_snapshot()
    assert dashboard["status"]["mode"] == "paper"
    report = await read_model.report_snapshot()
    assert report["position_count"] == 0
