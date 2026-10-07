"""Paper venue cost/limit/latency model — honest fills, no free rides."""

import pytest

from trading_bot.execution.service import PaperBrokerAdapter
from trading_bot.foundation.contracts import (
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)


def _order(price=1.10, qty=1.0, side=OrderSide.BUY,
           order_type=OrderType.MARKET, cid="o1") -> OrderRequest:
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=side, order_type=order_type, quantity=qty,
        client_order_id=cid, decision_id="d-1", price=price)


@pytest.mark.asyncio
async def test_market_buy_pays_spread_and_slippage() -> None:
    adapter = PaperBrokerAdapter(spread_bps=2.0, slippage_bps=1.0)
    report = await adapter.submit_order(_order(price=1.10))

    assert report.status is OrderStatus.FILLED
    # half-spread 1bps + slippage 1bps = 2bps adverse on a buy
    assert report.fills[0].price == pytest.approx(1.10 * (1 + 2e-4))
    assert report.slippage_bps == pytest.approx(2.0)


@pytest.mark.asyncio
async def test_commission_is_charged() -> None:
    adapter = PaperBrokerAdapter(commission_per_unit=0.5)
    report = await adapter.submit_order(_order(qty=2.0))

    assert report.fills[0].commission == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_limit_order_rests_until_marketable() -> None:
    adapter = PaperBrokerAdapter()
    adapter.on_mark("EURUSD", 1.12)
    report = await adapter.submit_order(
        _order(price=1.10, order_type=OrderType.LIMIT))
    assert report.status is OrderStatus.ACCEPTED
    assert not report.fills

    # Mark never reaches the limit -> still resting.
    adapter.on_mark("EURUSD", 1.11)
    assert (await adapter.get_order("o1")).status is OrderStatus.ACCEPTED

    adapter.on_mark("EURUSD", 1.10)
    filled = await adapter.get_order("o1")
    assert filled.status is OrderStatus.FILLED
    assert filled.fills[0].price <= 1.10  # never worse than the limit


@pytest.mark.asyncio
async def test_cancel_resting_order() -> None:
    adapter = PaperBrokerAdapter()
    adapter.on_mark("EURUSD", 1.12)
    await adapter.submit_order(_order(price=1.10, order_type=OrderType.LIMIT))

    assert await adapter.cancel_order("o1") is True
    adapter.on_mark("EURUSD", 1.05)   # would have filled — must not
    assert (await adapter.get_order("o1")).status is OrderStatus.CANCELLED
    assert await adapter.get_positions() == []


@pytest.mark.asyncio
async def test_latency_cycles_defers_fill_to_next_mark() -> None:
    adapter = PaperBrokerAdapter(latency_cycles=1)
    adapter.on_mark("EURUSD", 1.10)
    report = await adapter.submit_order(_order(price=1.10))
    assert report.status is OrderStatus.ACCEPTED

    adapter.on_mark("EURUSD", 1.20)
    filled = await adapter.get_order("o1")
    assert filled.status is OrderStatus.FILLED
    # Filled against the *new* mark, not the signal-time price.
    assert filled.fills[0].price == pytest.approx(1.20 * (1 + 5e-5))


@pytest.mark.asyncio
async def test_unsupported_order_type_rejected() -> None:
    adapter = PaperBrokerAdapter()
    report = await adapter.submit_order(
        _order(order_type=OrderType.STOP, price=1.10))
    assert report.status is OrderStatus.REJECTED
