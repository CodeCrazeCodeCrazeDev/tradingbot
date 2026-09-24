"""Tests for the canonical idempotent execution boundary."""

from types import SimpleNamespace

import pytest

from trading_bot.execution.service import CanonicalExecutionService, LegacyBrokerAdapter
from trading_bot.foundation import Instrument, InstrumentType, OrderRequest, OrderSide, OrderStatus, OrderType


def make_order(client_order_id: str = "order-1", price: float = 100.0) -> OrderRequest:
    instrument = Instrument("AAPL", InstrumentType.EQUITY, "paper")
    return OrderRequest(
        instrument=instrument,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=2,
        price=price,
        client_order_id=client_order_id,
        decision_id="decision-1",
    )


@pytest.mark.asyncio
async def test_paper_execution_is_filled_and_idempotent() -> None:
    service = CanonicalExecutionService()

    first = await service.submit(make_order())
    second = await service.submit(make_order())

    assert first.status is OrderStatus.FILLED
    assert first is second
    assert (await service.status("order-1")) is OrderStatus.FILLED
    assert len(await service.adapter.get_positions()) == 1


@pytest.mark.asyncio
async def test_paper_execution_rejects_missing_reference_price() -> None:
    service = CanonicalExecutionService()
    order = make_order(price=100.0)
    order = OrderRequest(
        instrument=order.instrument,
        side=order.side,
        order_type=order.order_type,
        quantity=order.quantity,
        client_order_id=order.client_order_id,
        decision_id=order.decision_id,
    )

    report = await service.submit(order)

    assert report.status is OrderStatus.REJECTED
    assert "price" in (report.error or "")


def test_non_paper_execution_requires_explicit_adapter() -> None:
    with pytest.raises(ValueError, match="broker adapter"):
        CanonicalExecutionService(mode="live")


@pytest.mark.asyncio
async def test_legacy_broker_adapter_converts_order_contract() -> None:
    class FakeBroker:
        async def place_order(self, symbol, side, type, quantity):
            return SimpleNamespace(
                client_order_id="venue-order-1",
                status="FILLED",
                filled_quantity=quantity,
                filled_price=101.0,
                commission=0.1,
            )

    service = CanonicalExecutionService(
        adapter=LegacyBrokerAdapter(FakeBroker(), venue_id="fake"),
        mode="live",
    )
    report = await service.submit(make_order())

    assert report.status is OrderStatus.FILLED
    assert report.fills[0].price == 101.0
    assert report.fills[0].commission == 0.1
