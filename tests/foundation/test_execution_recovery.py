"""Execution durability/recovery boundary tests.

Covers the invariants that make the canonical paper path crash-consistent:

* terminal (timed-out) LogAct actions are never re-opened for dispatch —
  a decision that already reported TIMED_OUT must not execute later;
* orders persisted in a non-terminal state are reconciled at startup via
  broker lookup (``adapter.get_order``) — never by resubmission;
* a redelivered submission for a durable client_order_id is deduplicated
  from the persisted record, not from in-memory caches;
* a hung broker submit resolves to a durable UNKNOWN report so the next
  recovery pass can reconcile it;
* every submission attempt, broker response, recovery and reconciliation
  leaves an ``audit_events`` row;
* the repository runs WAL + FULL synchronous for crash durability.
"""

import asyncio
from dataclasses import dataclass

import pytest

from trading_bot.core.execution_bridge import PaperExecutionBridge
from trading_bot.core.unified_event_bus import (
    ActionStatus,
    EventPriority,
    LogAction,
    UnifiedDecisionBus,
)
from trading_bot.data.normalizer import MarketDataNormalizer
from trading_bot.execution.recovery import ExecutionReconciler
from trading_bot.execution.service import CanonicalExecutionService, PaperBrokerAdapter
from trading_bot.foundation import DataQuality
from trading_bot.foundation.contracts import (
    ExecutionReport,
    Fill,
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)
from trading_bot.persistence.repositories import SqliteTradingRepository


def make_order(order_id="recovery-order", price=1.1, quantity=1.0):
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        client_order_id=order_id,
        decision_id="decision-recovery",
    )


@dataclass
class _Action:
    payload: dict
    action_id: str = "action-recovery"
    voter_reports: dict = None

    def __post_init__(self):
        if self.voter_reports is None:
            self.voter_reports = {}


def _payload(trade_id, **overrides):
    payload = {
        "trade_id": trade_id,
        "symbol": "EURUSD",
        "action": "BUY",
        "quantity": 1.0,
        "price": 1.1,
    }
    payload.update(overrides)
    return payload


class SpyPaperAdapter(PaperBrokerAdapter):
    """Paper adapter that counts venue submissions."""

    def __init__(self):
        super().__init__()
        self.submit_calls = 0
        self.lookup_calls = 0

    async def submit_order(self, order):
        self.submit_calls += 1
        return await super().submit_order(order)

    async def get_order(self, client_order_id):
        self.lookup_calls += 1
        return await super().get_order(client_order_id)


# --------------------------------------------------------------------------
# Repository durability + read surface
# --------------------------------------------------------------------------


def test_repository_enables_wal_full_sync_and_busy_timeout(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    journal = repo._connection.execute("PRAGMA journal_mode").fetchone()[0]
    synchronous = repo._connection.execute("PRAGMA synchronous").fetchone()[0]
    busy = repo._connection.execute("PRAGMA busy_timeout").fetchone()[0]
    repo.close()
    assert journal.lower() == "wal"
    assert synchronous == 2  # FULL
    assert busy > 0


@pytest.mark.asyncio
async def test_get_order_and_list_orders_roundtrip(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    order = make_order("persisted-1")
    await repo.record_order(order, OrderStatus.SUBMITTED)
    await repo.record_order(make_order("persisted-2"), OrderStatus.FILLED)

    row = await repo.get_order("persisted-1")
    assert row["status"] == "submitted"
    assert row["decision_id"] == "decision-recovery"

    pending = await repo.list_orders(statuses=["submitted", "unknown"])
    assert [r["client_order_id"] for r in pending] == ["persisted-1"]
    everything = await repo.list_orders()
    assert {r["client_order_id"] for r in everything} == {"persisted-1", "persisted-2"}

    decoded = repo.decode_order(row["order_json"])
    assert decoded.client_order_id == "persisted-1"
    assert decoded.side is OrderSide.BUY
    assert decoded.instrument.symbol == "EURUSD"
    repo.close()


@pytest.mark.asyncio
async def test_repository_decode_report_roundtrip(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    order = make_order("decode-1")
    service = CanonicalExecutionService(repository=repo)
    report = await service.submit(order)

    row = await repo.get_order("decode-1")
    decoded = repo.decode_report(row["report_json"])
    assert decoded.status is OrderStatus.FILLED
    assert decoded.fills[0].price == report.fills[0].price
    repo.close()


# --------------------------------------------------------------------------
# Durable recovery — broker lookup, never resubmit
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recovery_reconciles_unknown_order_via_broker_lookup(tmp_path) -> None:
    """A crash between record_order and the venue reply leaves 'submitted'
    durable state. Recovery must ask the venue — not resubmit."""
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    order = make_order("orphan-1")
    await repo.record_order(order, OrderStatus.SUBMITTED)

    adapter = SpyPaperAdapter()  # venue never saw the order
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    reconciler = ExecutionReconciler(service, repo)

    report = await reconciler.recover_pending_orders()

    assert adapter.submit_calls == 0  # never resubmitted
    assert adapter.lookup_calls == 1
    assert report["recovered"][0]["outcome"] == "unknown"
    row = await repo.get_order("orphan-1")
    assert row["status"] == "unknown"

    audits = repo._connection.execute(
        "SELECT action, outcome FROM audit_events WHERE correlation_id='orphan-1'"
    ).fetchall()
    assert any(r["action"] == "order_recovery" for r in audits)
    repo.close()


@pytest.mark.asyncio
async def test_recovery_restores_fill_the_venue_confirms(tmp_path) -> None:
    """Venue-side fill the crash dropped: recovery persists it and the
    position ledger catches up."""

    class VenueKnowsOrder(PaperBrokerAdapter):
        async def get_order(self, client_order_id):
            inst = Instrument("EURUSD", InstrumentType.FX, "paper")
            fill = Fill(client_order_id, "venue-1", inst, OrderSide.BUY, 1.0, 1.1)
            return ExecutionReport(
                client_order_id=client_order_id,
                status=OrderStatus.FILLED,
                fills=[fill],
            )

    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    await repo.record_order(make_order("found-1"), OrderStatus.SUBMITTED)

    adapter = VenueKnowsOrder()
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    reconciler = ExecutionReconciler(service, repo)

    await reconciler.recover_pending_orders()

    row = await repo.get_order("found-1")
    assert row["status"] == "filled"
    snapshot = await repo.snapshot("runtime")
    assert snapshot.positions[0].quantity == 1.0
    repo.close()


@pytest.mark.asyncio
async def test_recovery_leaves_terminal_orders_untouched(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    adapter = SpyPaperAdapter()
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    await service.submit(make_order("already-filled"))

    adapter.submit_calls = 0
    adapter.lookup_calls = 0
    reconciler = ExecutionReconciler(service, repo)
    report = await reconciler.recover_pending_orders()

    assert report["count"] == 0
    assert adapter.submit_calls == 0 and adapter.lookup_calls == 0
    repo.close()


@pytest.mark.asyncio
async def test_recovery_lookup_failure_is_audited_not_fatal(tmp_path) -> None:
    class DeafVenue(PaperBrokerAdapter):
        async def get_order(self, client_order_id):
            raise ConnectionError("venue unreachable")

    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    await repo.record_order(make_order("deaf-1"), OrderStatus.SUBMITTED)

    service = CanonicalExecutionService(adapter=DeafVenue(), repository=repo)
    report = await ExecutionReconciler(service, repo).recover_pending_orders()

    assert report["recovered"][0]["outcome"] == "lookup_failed"
    assert (await repo.get_order("deaf-1"))["status"] == "submitted"
    audits = repo._connection.execute(
        "SELECT outcome FROM audit_events WHERE correlation_id='deaf-1'"
    ).fetchall()
    assert any(r["outcome"] == "lookup_failed" for r in audits)
    repo.close()


# --------------------------------------------------------------------------
# Bridge-level durable idempotency + submit timeout
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bridge_dedup_uses_durable_record_after_restart(tmp_path) -> None:
    """First process fills the order; a restarted bridge seeing the same
    trade_id must dedup from the persisted row, not memory."""
    path = str(tmp_path / "state.db")
    repo = SqliteTradingRepository(path)
    service = CanonicalExecutionService(repository=repo)
    bridge = PaperExecutionBridge(execution_service=service)
    result = await bridge.execute(_Action(_payload("restart-trade")))
    assert result["status"] == "filled"
    repo.close()

    # New process state: fresh adapter (no _reports), fresh bridge — but the
    # same durable store.
    repo2 = SqliteTradingRepository(path)
    adapter2 = SpyPaperAdapter()
    service2 = CanonicalExecutionService(adapter=adapter2, repository=repo2)
    bridge2 = PaperExecutionBridge(execution_service=service2)
    result2 = await bridge2.execute(_Action(_payload("restart-trade")))

    assert result2["status"] == "filled"
    assert adapter2.submit_calls == 0  # durable dedup — never resubmitted
    assert adapter2._positions == {}  # no double fill at the venue either
    repo2.close()


@pytest.mark.asyncio
async def test_bridge_resolves_pending_durable_order_via_lookup(tmp_path) -> None:
    """A persisted non-terminal order is looked up at the venue, not resent."""

    class VenueFills(PaperBrokerAdapter):
        async def get_order(self, client_order_id):
            inst = Instrument("EURUSD", InstrumentType.FX, "paper")
            return ExecutionReport(
                client_order_id=client_order_id,
                status=OrderStatus.FILLED,
                fills=[Fill(client_order_id, "v-9", inst, OrderSide.BUY, 1.0, 1.1)],
            )

    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    await repo.record_order(make_order("pending-x"), OrderStatus.SUBMITTED)

    adapter = VenueFills()
    adapter_submits = []

    async def spy_submit(order):
        adapter_submits.append(order.client_order_id)
        return await PaperBrokerAdapter.submit_order(adapter, order)

    adapter.submit_order = spy_submit  # type: ignore[assignment]
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    bridge = PaperExecutionBridge(execution_service=service)

    result = await bridge.execute(_Action(_payload("pending-x")))

    assert result["status"] == "filled"
    assert adapter_submits == []
    assert (await repo.get_order("pending-x"))["status"] == "filled"
    repo.close()


@pytest.mark.asyncio
async def test_bridge_submit_timeout_records_durable_unknown(tmp_path) -> None:
    """A broker call that hangs past the submit deadline leaves an UNKNOWN
    durable record (reconciled later) — it is never silently retried."""

    class HangingVenue(PaperBrokerAdapter):
        async def submit_order(self, order):
            await asyncio.sleep(30)
            raise AssertionError("should have been cancelled")

    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(adapter=HangingVenue(), repository=repo)
    bridge = PaperExecutionBridge(execution_service=service, submit_timeout=0.05)

    result = await bridge.execute(_Action(_payload("slow-trade")))

    assert result["status"] == "unknown"
    row = await repo.get_order("slow-trade")
    assert row["status"] == "unknown"
    audits = repo._connection.execute(
        "SELECT action, outcome FROM audit_events WHERE correlation_id='slow-trade'"
    ).fetchall()
    assert any(r["outcome"] == "timeout_unknown" for r in audits)
    repo.close()


@pytest.mark.asyncio
async def test_bridge_audit_covers_attempt_and_response(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(repository=repo)
    bridge = PaperExecutionBridge(execution_service=service)

    result = await bridge.execute(_Action(_payload("audit-trade")))
    assert result["status"] == "filled"

    audits = repo._connection.execute(
        "SELECT action, outcome FROM audit_events WHERE correlation_id='audit-trade' ORDER BY rowid"
    ).fetchall()
    actions = [r["action"] for r in audits]
    assert "order_authorized" in actions
    assert "order_submit_attempt" in actions
    assert "order_broker_response" in actions
    outcomes = {r["action"]: r["outcome"] for r in audits}
    assert outcomes["order_broker_response"] == "filled"
    repo.close()


# --------------------------------------------------------------------------
# Position reconciliation + runtime wiring
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reconcile_positions_persists_run_and_audit(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    service = CanonicalExecutionService(repository=repo)
    await service.submit(make_order("recon-fill"))

    reconciler = ExecutionReconciler(service, repo)
    result = await reconciler.reconcile_positions()

    assert result.matched is True
    runs = repo._connection.execute("SELECT venue, matched FROM reconciliation_runs").fetchall()
    assert len(runs) == 1 and runs[0]["matched"] == 1
    audits = repo._connection.execute(
        "SELECT action, outcome FROM audit_events WHERE action='reconcile_positions'"
    ).fetchall()
    assert audits and audits[0]["outcome"] == "matched"
    repo.close()


@pytest.mark.asyncio
async def test_runtime_start_recovers_pending_orders(tmp_path) -> None:
    """Boot path: pending durable orders are reconciled at runtime start and
    the LogAct audit log gets a durable path."""
    from trading_bot.foundation.runtime import ModularMonolithRuntime

    db_path = str(tmp_path / "trading_state.db")
    repo = SqliteTradingRepository(db_path)
    await repo.record_order(make_order("boot-orphan"), OrderStatus.SUBMITTED)

    runtime = ModularMonolithRuntime({"mode": "paper", "trading_state_path": db_path})
    adapter = SpyPaperAdapter()
    runtime.bot.execution_service = CanonicalExecutionService(
        adapter=adapter, repository=repo
    )
    runtime.bot.trading_repository = repo

    async def _noop_start():
        runtime.bot.running = True

    runtime.bot.start = _noop_start
    bus = UnifiedDecisionBus()
    try:
        await runtime.start()
        assert adapter.submit_calls == 0
        assert adapter.lookup_calls == 1
        assert (await repo.get_order("boot-orphan"))["status"] == "unknown"
        # Durable decision-audit path configured next to the state db.
        assert bus._log_path == str(tmp_path / "decision_log.jsonl")
    finally:
        UnifiedDecisionBus({"log_path": None})
    repo.close()


@pytest.mark.asyncio
async def test_runtime_stop_reconciles_positions(tmp_path) -> None:
    from trading_bot.foundation.runtime import ModularMonolithRuntime

    db_path = str(tmp_path / "trading_state.db")
    repo = SqliteTradingRepository(db_path)
    runtime = ModularMonolithRuntime({"mode": "paper", "trading_state_path": db_path})
    runtime.bot.execution_service = CanonicalExecutionService(repository=repo)
    runtime.bot.trading_repository = repo

    async def _noop_start():
        runtime.bot.running = True

    runtime.bot.start = _noop_start
    try:
        await runtime.start()
        await runtime.bot.execution_service.submit(make_order("stop-recon"))
        await runtime.stop()

        probe = SqliteTradingRepository(db_path)
        runs = probe._connection.execute("SELECT matched FROM reconciliation_runs").fetchall()
        assert runs and runs[0]["matched"] == 1
        probe.close()
    finally:
        UnifiedDecisionBus({"log_path": None})


# --------------------------------------------------------------------------
# LogAct: terminal actions never reach voters/dispatch
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bus_never_dispatches_pre_timed_out_action() -> None:
    UnifiedDecisionBus.reset()
    bus = UnifiedDecisionBus()
    bus._log_path = None
    bus._voters.clear()
    bus._subscribers.clear()

    dispatched = []
    voted = []

    async def handler(action):
        dispatched.append(action.action_id)

    async def shield(action):
        voted.append(action.action_id)
        return {"decision": "APPROVED"}

    bus.subscribe("TRADE_EXECUTION", handler)
    bus.register_voter("shield", shield)
    await bus.start()
    try:
        # Enqueue straight onto the queue, already timed out — simulates the
        # caller's wait_for_decision firing while the action still sat queued.
        stale = LogAction(
            action_type="TRADE_EXECUTION",
            payload={"symbol": "EURUSD", "quantity": 1.0},
            agent_id="test",
            priority=EventPriority.CRITICAL,
        )
        stale.status = ActionStatus.TIMED_OUT
        await bus._action_queue.put(
            (-stale.priority.value, stale.timestamp, next(bus._action_seq), stale)
        )
        await asyncio.sleep(0.2)

        assert dispatched == []
        assert voted == []
        assert stale.status is ActionStatus.TIMED_OUT

        # Re-proposing a timed-out action must be refused outright.
        resurrect = LogAction(
            action_type="TRADE_EXECUTION",
            payload={"symbol": "EURUSD", "quantity": 1.0},
            agent_id="test",
        )
        resurrect.status = ActionStatus.TIMED_OUT
        await bus.propose_action(resurrect)
        await asyncio.sleep(0.2)
        assert dispatched == []
        assert resurrect.status is ActionStatus.TIMED_OUT
    finally:
        await bus.stop()
        UnifiedDecisionBus.reset()


@pytest.mark.asyncio
async def test_bus_timeout_during_voting_blocks_dispatch() -> None:
    UnifiedDecisionBus.reset()
    bus = UnifiedDecisionBus()
    bus._log_path = None
    bus._voters.clear()
    bus._subscribers.clear()

    dispatched = []

    async def handler(action):
        dispatched.append(action.action_id)

    async def slow_shield(action):
        await asyncio.sleep(0.3)
        return {"decision": "APPROVED"}

    bus.subscribe("TRADE_EXECUTION", handler)
    bus.register_voter("shield", slow_shield)
    await bus.start()
    try:
        action = LogAction(
            action_type="TRADE_EXECUTION",
            payload={"symbol": "EURUSD", "quantity": 1.0},
            agent_id="test",
            priority=EventPriority.CRITICAL,
        )
        await bus.propose_action(action)
        status = await action.wait_for_decision(timeout=0.05)
        assert status is ActionStatus.TIMED_OUT

        await asyncio.sleep(0.6)  # let the voter finish + any dispatch attempt
        assert dispatched == []
        assert action.status is ActionStatus.TIMED_OUT
    finally:
        await bus.stop()
        UnifiedDecisionBus.reset()


# --------------------------------------------------------------------------
# Observation validation — declared quality honored
# --------------------------------------------------------------------------


def test_normalizer_honors_declared_stale_quality() -> None:
    event = MarketDataNormalizer().normalize(
        {
            "symbol": "EURUSD",
            "timestamp": "2026-01-01T12:00:00Z",
            "price": 1.1,
            "data_quality": "stale",
        },
        source="feed",
    )
    assert event.quality is DataQuality.STALE


def test_normalizer_honors_declared_invalid_and_stale_flag() -> None:
    normalizer = MarketDataNormalizer()
    assert (
        normalizer.normalize(
            {"symbol": "EURUSD", "price": 1.1, "quality": "invalid"}, source="feed"
        ).quality
        is DataQuality.INVALID
    )
    assert (
        normalizer.normalize(
            {"symbol": "EURUSD", "price": 1.1, "stale": True}, source="feed"
        ).quality
        is DataQuality.STALE
    )


def test_normalizer_computed_invalid_beats_declared_valid() -> None:
    """A feed cannot launder malformed data by declaring it 'valid'."""
    event = MarketDataNormalizer().normalize(
        {"symbol": "EURUSD", "price": float("nan"), "data_quality": "valid"},
        source="feed",
    )
    assert event.quality is DataQuality.INVALID


def test_normalizer_optional_staleness_horizon() -> None:
    normalizer = MarketDataNormalizer(max_staleness_seconds=60.0)
    fresh = normalizer.normalize(
        {"symbol": "EURUSD", "price": 1.1}, source="feed"
    )
    assert fresh.quality is DataQuality.VALID

    old = normalizer.normalize(
        {
            "symbol": "EURUSD",
            "timestamp": "2000-01-01T00:00:00Z",
            "price": 1.1,
        },
        source="feed",
    )
    assert old.quality is DataQuality.STALE
