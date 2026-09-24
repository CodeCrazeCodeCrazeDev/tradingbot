"""Tests for authoritative typed trading-state persistence."""

from datetime import datetime, timezone

import pytest

from trading_bot.foundation import (
    AuditEvent,
    ExecutionReport,
    Fill,
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


def make_order() -> OrderRequest:
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=2.0,
        price=1.1,
        client_order_id="order-1",
        decision_id="decision-1",
    )


@pytest.mark.asyncio
async def test_repository_persists_execution_and_rebuilds_position(tmp_path) -> None:
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    order = make_order()
    fill = Fill(
        client_order_id="order-1",
        venue_order_id="venue-1",
        instrument=order.instrument,
        side=order.side,
        quantity=2.0,
        price=1.1,
    )
    report = ExecutionReport(
        client_order_id="order-1",
        status=OrderStatus.FILLED,
        fills=[fill],
    )

    await repository.record_execution(order, report)
    await repository.record_execution(order, report)
    snapshot = await repository.snapshot("account-1")

    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].quantity == 2.0
    assert snapshot.positions[0].instrument.symbol == "EURUSD"

    reconciliation = await repository.reconcile(snapshot)
    assert reconciliation.matched is True
    repository.close()


@pytest.mark.asyncio
async def test_repository_audits_and_detects_position_mismatch(tmp_path) -> None:
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    event = AuditEvent(
        event_type="TEST",
        actor="test",
        action="persist",
        outcome="accepted",
        correlation_id="corr-1",
        occurred_at=datetime.now(timezone.utc),
    )
    audit_id = await repository.record_audit_event(event)
    assert audit_id

    expected = PortfolioSnapshot(
        account_id="account-1",
        equity=1000,
        cash=1000,
        positions=[
            # No fill exists for this expected position.
            Position(Instrument("EURUSD", InstrumentType.FX, "paper"), 1.0, 1.1)
        ],
    )
    reconciliation = await repository.reconcile(expected)

    assert reconciliation.matched is False
    assert "EURUSD" in reconciliation.position_differences
    repository.close()
