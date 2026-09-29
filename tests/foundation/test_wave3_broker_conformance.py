"""Wave-3 broker/venue conformance gate: submit/cancel/status/reconcile.

Covers the boundary contract for BrokerAdapter implementations behind
CanonicalExecutionService, using mock/paper adapters only. No live broker
connections are made; capital-flagged ``brokers/*`` modules are exercised
only through the typed foundation bridge.
"""

import json
from pathlib import Path

import pytest

from trading_bot.brokers.adapter_bridge import FoundationBrokerAdapter
from trading_bot.brokers.broker_adapter import MockBrokerAdapter
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

ROOT = Path(__file__).resolve().parents[2]


def order(order_id: str = "mock-1") -> OrderRequest:
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "mock"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        price=1.1,
        client_order_id=order_id,
        decision_id="decision-mock",
    )


async def _service(tmp_path):
    legacy = MockBrokerAdapter({"initial_balance": 10000.0, "slippage_bps": 0.0})
    adapter = FoundationBrokerAdapter.from_legacy(legacy, venue_id="mock")
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(adapter=adapter, mode="paper", repository=repository)
    await adapter.connect()
    return service, adapter, repository


@pytest.mark.asyncio
async def test_submit_is_idempotent_and_records_fill(tmp_path) -> None:
    service, adapter, repository = await _service(tmp_path)
    first = await service.submit(order("idem-1"))
    second = await service.submit(order("idem-1"))

    assert first is second  # repeated intent returns the cached report
    assert first.status is OrderStatus.FILLED
    assert len(first.fills) == 1
    await adapter.disconnect()
    repository.close()


@pytest.mark.asyncio
async def test_cancel_fails_closed_when_venue_cannot_identify_order(tmp_path) -> None:
    """CanonicalExecutionService surfaces the broker's own cancel verdict;
    it never reports success the venue did not confirm."""
    service, adapter, repository = await _service(tmp_path)
    await service.submit(order("cancel-1"))

    # The mock venue never saw our client id -> cannot cancel -> False,
    # and the cached report must not be mutated to CANCELLED.
    assert await service.cancel("cancel-1") is False
    assert await service.status("cancel-1") is OrderStatus.FILLED
    assert await service.cancel("never-submitted") is False
    await adapter.disconnect()
    repository.close()


@pytest.mark.asyncio
async def test_mock_broker_cancels_pending_venue_order_only() -> None:
    """Venue-level honesty: pending orders cancel; filled/unknown ids do not."""
    from trading_bot.brokers import broker_adapter as legacy_module

    legacy = MockBrokerAdapter({"initial_balance": 10000.0, "slippage_bps": 0.0})
    await legacy.connect()

    pending = await legacy.place_order(
        symbol="EURUSD",
        side=legacy_module.OrderSide.BUY,
        order_type=legacy_module.OrderType.LIMIT,
        quantity=1.0,
        price=1.05,
    )
    assert pending.status == legacy_module.OrderStatus.PENDING
    assert await legacy.cancel_order(pending.order_id) is True
    assert (await legacy.get_order_status(pending.order_id)).status == (
        legacy_module.OrderStatus.CANCELLED
    )
    # Unknown id fails closed instead of the old always-True stub.
    assert await legacy.cancel_order("BOGUS_ID") is False
    await legacy.disconnect()


@pytest.mark.asyncio
async def test_status_for_unknown_order_is_unknown_not_success(tmp_path) -> None:
    service, adapter, repository = await _service(tmp_path)
    assert await service.status("ghost-order") is OrderStatus.UNKNOWN
    await adapter.disconnect()
    repository.close()


@pytest.mark.asyncio
async def test_reconcile_reports_mismatch_instead_of_success(tmp_path) -> None:
    service, adapter, repository = await _service(tmp_path)
    await service.submit(order("recon-1"))

    # Expected state deliberately wrong: venue holds EURUSD, repo expects GBPUSD.
    wrong = PortfolioSnapshot(
        "account-1", 10000, 10000,
        positions=[Position(Instrument("GBPUSD", InstrumentType.FX, "mock"), 1.0, 1.3)],
    )
    result = await service.reconcile(wrong)

    assert result.matched is False
    assert set(result.position_differences) == {"EURUSD", "GBPUSD"}
    await adapter.disconnect()
    repository.close()


@pytest.mark.asyncio
async def test_broker_without_positions_cannot_reconcile_as_success() -> None:
    class BlindBroker:
        async def place_order(self, **kwargs):
            raise RuntimeError("should not be called")

    adapter = LegacyBrokerAdapter(BlindBroker(), venue_id="blind")
    result = await adapter.reconcile(None)

    assert result.matched is False
    assert result.position_differences


@pytest.mark.asyncio
async def test_submit_failure_propagates_and_caches_nothing(tmp_path) -> None:
    class FailingBroker:
        calls = 0

        async def place_order(self, **kwargs):
            self.calls += 1
            raise ConnectionError("venue unreachable")

    broker = FailingBroker()
    adapter = LegacyBrokerAdapter(broker, venue_id="failing")
    repository = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(adapter=adapter, mode="paper", repository=repository)

    with pytest.raises(ConnectionError):
        await service.submit(order("fail-1"))
    assert service._reports.get("fail-1") is None
    # A retry must reach the venue again — no fake success was recorded.
    with pytest.raises(ConnectionError):
        await service.submit(order("fail-1"))
    assert broker.calls == 2
    repository.close()


@pytest.mark.asyncio
async def test_non_paper_mode_requires_explicit_adapter() -> None:
    with pytest.raises(ValueError):
        CanonicalExecutionService(mode="live")


def test_wave3_reachable_modules_are_declared_boundaries_only() -> None:
    """No wave-3 broker/execution module may be runtime-reachable with a
    capital or loop flag unless it is the declared boundary interface."""
    manifest = json.loads(
        (ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json").read_text(encoding="utf-8")
    )
    allowed_reachable = {"trading_bot/broker/broker_interface.py"}
    violations = [
        r["path"]
        for r in manifest["modules"]
        if r["migration_wave"] == 3
        and r["runtime_reachable"]
        and r["path"] not in allowed_reachable
    ]
    assert violations == [], f"unexpected reachable wave-3 modules: {violations}"
