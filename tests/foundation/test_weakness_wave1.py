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
