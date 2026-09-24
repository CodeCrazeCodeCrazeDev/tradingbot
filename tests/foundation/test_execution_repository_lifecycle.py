"""Repository-backed order lifecycle and reconciliation tests."""

from types import SimpleNamespace

import pytest

from trading_bot.execution.service import CanonicalExecutionService, LegacyBrokerAdapter
from trading_bot.foundation import (
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioSnapshot,
    Position,
)
from trading_bot.persistence.repositories import SqliteTradingRepository


def make_order(order_id="order-lifecycle"):
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1.0,
        price=1.1,
        client_order_id=order_id,
        decision_id="decision-lifecycle",
    )


@pytest.mark.asyncio
async def test_paper_order_lifecycle_is_authoritative_and_reconcilable(tmp_path) -> None:
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(repository=repository)
    report = await service.submit(make_order())
    snapshot = await repository.snapshot("account-1")

    assert report.status is OrderStatus.FILLED
    assert await service.status("order-lifecycle") is OrderStatus.FILLED
    assert (await repository.reconcile(snapshot)).matched is True

    mismatch = PortfolioSnapshot(
        "account-1",
        10000,
        10000,
        positions=[Position(make_order().instrument, 2.0, 1.1)],
    )
    result = await service.reconcile(mismatch)
    assert result.matched is False
    assert "EURUSD" in result.position_differences
    repository.close()


@pytest.mark.asyncio
async def test_legacy_broker_positions_are_normalized_for_reconciliation(tmp_path) -> None:
    class OldStyleBroker:
        async def place_order(self, symbol, side, type, quantity):
            return SimpleNamespace(
                client_order_id="old-filled",
                status="FILLED",
                filled_quantity=quantity,
                filled_price=1.1,
                commission=0.0,
            )

        async def get_positions(self):
            return [SimpleNamespace(symbol="EURUSD", quantity=1.0, entry_price=1.1)]

    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    adapter = LegacyBrokerAdapter(OldStyleBroker(), venue_id="old")
    service = CanonicalExecutionService(adapter=adapter, mode="testnet", repository=repository)
    await service.submit(make_order("old-1"))
    expected = PortfolioSnapshot(
        "account-1", 10000, 10000,
        positions=[Position(make_order().instrument, 1.0, 1.1)],
    )

    result = await service.reconcile(expected)

    assert result.matched is True
    repository.close()


@pytest.mark.asyncio
async def test_legacy_adapter_cancel_is_persisted(tmp_path) -> None:
    class PendingBroker:
        async def place_order(self, symbol, side, type, quantity):
            return SimpleNamespace(
                client_order_id="venue-pending",
                status="PENDING",
                filled_quantity=0.0,
                filled_price=None,
                commission=0.0,
            )

        async def cancel_order(self, symbol, order_id):
            return True

        async def get_positions(self):
            return []

    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(
        adapter=LegacyBrokerAdapter(PendingBroker(), venue_id="fake"),
        mode="testnet",
        repository=repository,
    )
    await service.submit(make_order("pending-1"))

    assert await service.cancel("pending-1") is True
    assert await service.status("pending-1") is OrderStatus.CANCELLED
    row = repository._connection.execute(
        "SELECT status FROM orders WHERE client_order_id=?", ("pending-1",)
    ).fetchone()
    assert row["status"] == "cancelled"
    repository.close()
