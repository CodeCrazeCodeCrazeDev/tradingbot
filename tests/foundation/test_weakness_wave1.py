"""Wave-1 weakness fixes: failing tests first.

Each test documents a confirmed weakness from WEAKNESS_REGISTER.json and the
expected corrected behavior — loud failures on order paths, fail-closed
evaluation, restricted exec environments, and identifier validation.
"""
import sys
import types

import pytest

from trading_bot.foundation.contracts import (
    Instrument,
    InstrumentType,
    OrderRequest,
    OrderSide,
    OrderType,
)


def _order() -> OrderRequest:
    return OrderRequest(
        client_order_id="w1-1",
        instrument=Instrument(symbol="EURUSD", instrument_type=InstrumentType.FX, venue="paper"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1,
        price=1.10,
        decision_id="d-w1",
    )


class _BareBroker:
    """Broker whose defining module exposes no legacy order enums."""

    async def place_order(self, **kwargs):
        return types.SimpleNamespace(status="filled", filled_quantity=0.1,
                                     filled_price=kwargs.get("price"))


_BareBroker.__module__ = "nonexistent_legacy_broker_module"


@pytest.mark.asyncio
async def test_unresolvable_broker_enums_fail_loudly_not_wrong_side(monkeypatch):
    """If no legacy enum layer resolves, submit must not silently forward the
    canonical enum — a broker that cannot interpret side/type could map the
    order to the wrong side."""
    from trading_bot.execution.service import LegacyBrokerAdapter

    monkeypatch.setitem(sys.modules, "trading_bot.broker.broker_interface", None)
    adapter = LegacyBrokerAdapter(broker=_BareBroker())
    with pytest.raises(RuntimeError, match="legacy order enum"):
        await adapter.submit_order(_order())


@pytest.mark.asyncio
async def test_evolution_gate_rejects_when_baseline_benchmark_fails():
    """A failed baseline benchmark currently leaves baseline_raw = the raw
    config dict, so parse_metrics fabricates baseline perf 0.5 and a candidate
    can 'beat' a benchmark that never ran."""
    from trading_bot.governance.evolution_gate import EvolutionGate

    class FailingEngine:
        def run_benchmark(self, config, **kwargs):
            raise RuntimeError("benchmark crashed")

    gate = EvolutionGate(validation_engine=FailingEngine(), threshold=0.05)
    candidate = {"reward": 0.9, "safety_score": 1.0, "calibration": 0.95,
                 "robustness": 0.9, "latency": 1.0}
    baseline = {"mode": "stateless"}  # triggers run_benchmark path
    result = await gate.validate_improvement("cand-1", candidate, baseline)
    assert result is False


def test_trade_journal_update_rejects_non_schema_columns(tmp_path):
    """update_trade interpolates kwargs as SQL identifiers; a key that is not a
    real column must be rejected before execute, not interpolated raw."""
    from trading_bot.audit.trade_journal import TradeJournal

    journal = TradeJournal(config={"db_path": str(tmp_path / "journal.db")})
    with pytest.raises(ValueError, match="not an updatable trade column"):
        journal.update_trade("t-1", **{"exit_price": 1.0, "pnl = 0; DROP TABLE trades--": 1})


def test_strategy_exec_cannot_reach_real_builtins():
    """exec(code, {}) injects full builtins into the globals dict; validated
    strategy code can then reach open()/eval via __builtins__ despite the AST
    blocklist. The shared exec helper must expose restricted builtins only."""
    from trading_bot.core.security.sandbox import safe_exec_strategy

    code = "def probe():\n    return 'open' in __builtins__"
    namespace = safe_exec_strategy(code)
    assert namespace["probe"]() is False

    code_real = "def probe():\n    return __builtins__['open']"
    namespace = safe_exec_strategy(code_real)
    with pytest.raises(KeyError):
        namespace["probe"]()


@pytest.mark.asyncio
async def test_risk_gate_exception_fails_closed_not_open():
    """unified_ai_brain._validate_risk: a crashing MSOS/risk/circuit-breaker
    subsystem currently falls through `except: pass` to `approved = True` —
    a risk gate that fails open. An errored gate must leave the trade
    unapproved."""
    from types import SimpleNamespace
    from trading_bot.unified_ai_brain import (
        SubsystemCategory, SubsystemInfo, UnifiedAIBrain,
    )

    class ThrowingRisk:
        def validate_trade(self, **kwargs):
            raise RuntimeError("risk subsystem crashed")

    brain = UnifiedAIBrain.__new__(UnifiedAIBrain)
    brain.subsystems = {
        "risk_manager": SubsystemInfo(
            name="risk_manager", category=SubsystemCategory.RISK,
            module_path="x", class_name="ThrowingRisk",
            instance=ThrowingRisk()),
    }
    brain.loaded_subsystems = {"risk_manager"}
    brain.capital = 10_000.0
    brain.config = SimpleNamespace(max_risk_per_trade=0.02)

    result = await brain._validate_risk(
        "EURUSD", {"action": "BUY", "confidence": 0.9, "price": 1.1})
    assert result["approved"] is False
    assert "error" in result["reason"].lower() or "crashed" in result["reason"].lower()


@pytest.mark.asyncio
async def test_clickhouse_database_identifier_is_validated(monkeypatch):
    """The database name is interpolated into CREATE DATABASE; config values
    must pass an identifier check before any client call."""
    from trading_bot.ingestion.storage import ClickHouseWriter

    writer = ClickHouseWriter.__new__(ClickHouseWriter)
    writer.config = types.SimpleNamespace(
        clickhouse_database="db; DROP TABLE x--", clickhouse_host="h",
        clickhouse_port=1, clickhouse_user="u", clickhouse_password="p",
        hot_retention_days=7)
    writer._initialized = False
    with pytest.raises(ValueError, match="invalid ClickHouse identifier"):
        await writer.initialize()


@pytest.mark.asyncio
async def test_shield_missing_confidence_fails_when_floor_set():
    """ImmutableShield defaults a missing confidence field to 1.0, so a
    configured floor can never reject a proposal that omits confidence."""
    from trading_bot.core.immutable_shield import (
        GovernanceDecision, ImmutableShield)

    shield = ImmutableShield()
    old = dict(shield.config)
    try:
        shield.config = {"min_confidence": 0.5}
        report = await shield.validate_action(
            "trade", {"quantity": 1.0}, {})
        assert report.decision is GovernanceDecision.REJECTED
    finally:
        shield.config = old


@pytest.mark.asyncio
async def test_shield_denylist_applies_to_typed_instrument():
    """The symbol denylist only reads dict-form instruments; a typed payload
    carrying the same symbol silently bypasses it."""
    from types import SimpleNamespace
    from trading_bot.core.immutable_shield import (
        GovernanceDecision, ImmutableShield)

    shield = ImmutableShield()
    old = dict(shield.config)
    try:
        shield.config = {"blocked_symbols": ["EURUSD"]}
        report = await shield.validate_action(
            "trade",
            {"quantity": 1.0, "instrument": SimpleNamespace(symbol="EURUSD")},
            {})
        assert report.decision is GovernanceDecision.BLOCKED
    finally:
        shield.config = old


@pytest.mark.asyncio
async def test_shield_string_numeric_exposure_still_gated():
    """A non-float exposure value skips the cap check entirely — string numerics
    from loose callers must be coerced, not ignored."""
    from trading_bot.core.immutable_shield import (
        GovernanceDecision, ImmutableShield)

    shield = ImmutableShield()
    old = dict(shield.config)
    try:
        shield.config = {"max_exposure": 0.05}
        report = await shield.validate_action(
            "trade", {"quantity": 1.0}, {"market": {"exposure": "0.20"}})
        assert report.decision is GovernanceDecision.BLOCKED
    finally:
        shield.config = old


@pytest.mark.asyncio
async def test_legacy_partial_fill_records_fill_quantity():
    """A broker reporting a PARTIALLY_FILLED result produced zero Fill
    objects — executed quantity silently vanished from the report."""
    from trading_bot.foundation.contracts import (
        Instrument, InstrumentType, OrderRequest, OrderSide, OrderType)

    class _Result:
        status = "partial"
        filled_quantity = 0.5
        filled_price = 100.25
        client_order_id = "venue-9"
        commission = 0.4

    class _FakeBroker:
        __module__ = "definitely_missing_broker_mod"
        def place_order(self, **kw):
            return _Result()

    from trading_bot.execution.service import LegacyBrokerAdapter
    adapter = LegacyBrokerAdapter(_FakeBroker())
    inst = Instrument("EURUSD", InstrumentType.FX, "t")
    order = OrderRequest(
        client_order_id="pf-1", instrument=inst,
        side=OrderSide.BUY, order_type=OrderType.MARKET,
        quantity=1.0, price=100.25, decision_id="d1")
    report = await adapter.submit_order(order)
    from trading_bot.foundation.contracts import OrderStatus
    assert report.status is OrderStatus.PARTIALLY_FILLED
    assert len(report.fills) == 1
    assert report.fills[0].quantity == 0.5


@pytest.mark.asyncio
async def test_execution_submit_is_idempotent_for_duplicate_client_ids():
    """Submitting the same client_order_id twice must not reach the adapter
    twice — duplicate submissions are a known real-money hazard."""
    from trading_bot.foundation.contracts import (
        Instrument, InstrumentType, OrderRequest, OrderSide, OrderType)
    from trading_bot.execution.service import (
        CanonicalExecutionService, PaperBrokerAdapter)

    adapter = PaperBrokerAdapter()
    calls = {"n": 0}
    orig = adapter.submit_order
    async def counted(order):
        calls["n"] += 1
        return await orig(order)
    adapter.submit_order = counted
    service = CanonicalExecutionService(adapter=adapter)
    inst = Instrument("EURUSD", InstrumentType.FX, "t")
    order = OrderRequest(
        client_order_id="dup-1", instrument=inst,
        side=OrderSide.BUY, order_type=OrderType.MARKET,
        quantity=0.1, price=1.1, decision_id="d1")
    r1 = await service.submit(order)
    r2 = await service.submit(order)
    assert calls["n"] == 1
    assert r1 is r2


def test_execution_non_paper_mode_requires_adapter():
    from trading_bot.execution.service import CanonicalExecutionService
    import pytest as _pt
    with _pt.raises(ValueError):
        CanonicalExecutionService(adapter=None, mode="live")


@pytest.mark.asyncio
async def test_decision_bus_lifecycle_start_stop_reset():
    """Bus lifecycle: start spawns the processor, stop clears it, reset
    restores empty state without leaking tasks."""
    import asyncio
    from trading_bot.core import unified_event_bus as ueb

    bus = ueb.decision_bus
    voters = dict(bus._voters); log = list(bus._log)
    try:
        ueb.UnifiedDecisionBus.reset()
        await bus.start()
        assert bus._running is True
        assert bus._processor_task is not None and not bus._processor_task.done()
        await bus.stop()
        assert bus._running is False
        assert bus._processor_task is None
        ueb.UnifiedDecisionBus.reset()
        assert not bus._voters and not bus._log
        # A fresh queue bound to no loop must accept a new action cleanly.
        assert bus._action_queue is not None
    finally:
        bus._voters.update(voters)
        bus._log.extend(log)
