"""Concrete legacy broker adapter bridge tests (paper/mock only)."""

import pytest

from trading_bot.brokers.adapter_bridge import FoundationBrokerAdapter
from trading_bot.brokers.broker_adapter import MockBrokerAdapter
from trading_bot.execution.service import CanonicalExecutionService
from trading_bot.foundation import Instrument, InstrumentType, OrderRequest, OrderSide, OrderType, PortfolioSnapshot, Position
from trading_bot.persistence.repositories import SqliteTradingRepository


def order(order_id="mock-1"):
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "mock"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        price=1.1,
        client_order_id=order_id,
        decision_id="decision-mock",
    )


@pytest.mark.asyncio
async def test_concrete_mock_broker_is_foundation_compatible(tmp_path) -> None:
    legacy = MockBrokerAdapter({"initial_balance": 10000.0, "slippage_bps": 0.0})
    adapter = FoundationBrokerAdapter.from_legacy(legacy, venue_id="mock")
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(adapter=adapter, mode="paper", repository=repository)

    await adapter.connect()
    report = await service.submit(order())
    positions = await adapter.get_positions()
    expected = PortfolioSnapshot(
        "account-1", 10000, 10000,
        positions=[Position(order().instrument, 1.0, 1.1)],
    )
    reconciliation = await service.reconcile(expected)

    assert report.status.value == "filled"
    assert len(positions) == 1
    assert reconciliation.matched is True
    await adapter.disconnect()
    repository.close()
