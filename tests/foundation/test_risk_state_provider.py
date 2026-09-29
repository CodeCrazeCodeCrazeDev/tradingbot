"""Tests for repository-derived portfolio state in canonical risk evaluation."""

import pytest

from trading_bot.foundation.contracts import (
    Fill,
    Instrument,
    InstrumentType,
    OrderSide,
)
from trading_bot.persistence.repositories import SqliteTradingRepository
from trading_bot.risk.service import CanonicalRiskService
from trading_bot.risk.state_provider import PortfolioStateProvider


def make_instrument() -> Instrument:
    return Instrument("EURUSD", InstrumentType.FX, "paper")


async def fill(repo: SqliteTradingRepository, order_id: str, side: OrderSide, qty: float, price: float) -> None:
    await repo.record_fill(Fill(
        client_order_id=order_id,
        venue_order_id=f"v-{order_id}",
        instrument=make_instrument(),
        side=side,
        quantity=qty,
        price=price,
    ))


@pytest.mark.asyncio
async def test_provider_derives_cash_equity_and_exposure(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    await fill(repo, "o1", OrderSide.BUY, 1.0, 100.0)
    await fill(repo, "o2", OrderSide.BUY, 1.0, 110.0)
    await fill(repo, "o3", OrderSide.SELL, 1.0, 120.0)

    provider = PortfolioStateProvider(repo, initial_equity=1000.0)
    state = await provider.portfolio_state({"symbol": "EURUSD", "price": 130.0})

    assert state["cash"] == 910.0          # 1000 - 100 - 110 + 120
    assert state["equity"] == 1040.0       # cash + 1.0 * 130 mark
    assert state["open_positions"] == 1
    assert state["daily_pnl"] == pytest.approx(40.0)  # realized 15 + unrealized 25
    assert state["portfolio_exposure"] == pytest.approx(130.0 / 1040.0)


@pytest.mark.asyncio
async def test_evaluate_action_uses_provider_state(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    provider = PortfolioStateProvider(repo, initial_equity=1000.0)
    service = CanonicalRiskService(state_provider=provider)

    result = await service.evaluate_action(
        {"trade_id": "t1", "symbol": "EURUSD", "action": "BUY", "quantity": 0.5, "confidence": 0.9},
        {"symbol": "EURUSD", "price": 100.0, "data_quality": "valid"},
    )

    # Real equity is 1000 with zero open positions — must not be the
    # fabricated 1.0/0.0 defaults.
    assert result.approved is True
    assert result.checks["open_position_limit"] is True


@pytest.mark.asyncio
async def test_evaluate_action_fails_closed_when_provider_fails() -> None:
    class BrokenProvider:
        async def portfolio_state(self, observation):
            raise RuntimeError("repository down")

    service = CanonicalRiskService(state_provider=BrokenProvider())
    result = await service.evaluate_action(
        {"trade_id": "t2", "symbol": "EURUSD", "action": "BUY", "quantity": 0.5},
        {"symbol": "EURUSD", "data_quality": "valid"},
    )

    assert result.approved is False
    assert result.checks["portfolio_state_available"] is False


@pytest.mark.asyncio
async def test_evaluate_action_vetoes_exposure_breach(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    # Build a large position: 2 x 100 = 200 notional vs equity ~1000 -> 20% >> 5% limit
    await fill(repo, "o1", OrderSide.BUY, 2.0, 100.0)
    provider = PortfolioStateProvider(repo, initial_equity=1000.0)
    service = CanonicalRiskService(state_provider=provider)

    result = await service.evaluate_action(
        {"trade_id": "t3", "symbol": "EURUSD", "action": "BUY", "quantity": 0.5},
        {"symbol": "EURUSD", "price": 100.0, "data_quality": "valid"},
    )

    assert result.approved is False
    assert "exposure_limit" in result.reason


@pytest.mark.asyncio
async def test_evaluate_action_without_provider_keeps_dict_compat() -> None:
    service = CanonicalRiskService()
    result = await service.evaluate_action(
        {"trade_id": "t4", "symbol": "EURUSD", "action": "BUY", "quantity": 1.0, "confidence": 0.8},
        {"symbol": "EURUSD", "data_quality": "valid", "exposure": 0.01},
    )
    assert result.approved is True
