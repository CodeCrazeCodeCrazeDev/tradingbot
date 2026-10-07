"""Operator control surface: pause/resume/estop via the human gate,
flatten/cancel via the canonical execution service, channel quarantine."""

from __future__ import annotations

import json
import types

import pytest

from trading_bot.execution.service import (
    CanonicalExecutionService, PaperBrokerAdapter)
from trading_bot.foundation.contracts import (
    Instrument, InstrumentType, OrderRequest, OrderSide, OrderType,
    OrderStatus)
from trading_bot.interfaces.control import (
    CONTROL_ACTIONS, ControlChannel, OperatorConsole)


@pytest.fixture()
def override():
    from trading_bot.human_layer import override as override_mod
    ov = override_mod.get_manual_override()
    ov._trading_paused = False
    ov.emergency_stop._triggered = False
    ov.emergency_stop._trigger_reason = None
    ov._blocked_signals.clear()
    yield ov
    ov._trading_paused = False
    ov.emergency_stop._triggered = False


def _bot_with_paper():
    service = CanonicalExecutionService(adapter=PaperBrokerAdapter())
    return types.SimpleNamespace(
        config={}, execution_service=service, trading_repository=None)


def _paper_order(cid="o-1", side=OrderSide.BUY, qty=0.1):
    return OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper"),
        side=side, order_type=OrderType.MARKET, quantity=qty,
        client_order_id=cid, decision_id="d", price=1.10)


def test_channel_roundtrip_and_unknown_rejected(tmp_path):
    channel = ControlChannel(tmp_path / "control")
    channel.send("pause", user="ops")
    channel.send("flatten", user="ops", reason="check")
    drained = channel.drain()
    assert [c["action"] for c in drained] == ["pause", "flatten"]
    assert channel.drain() == []
    with pytest.raises(ValueError):
        channel.send("buy_market")        # no order-entry surface exists


def test_channel_quarantines_malformed(tmp_path):
    channel = ControlChannel(tmp_path / "control")
    bad = channel.dir / "cmd-1.000000-bad.json"
    bad.write_text("{not json")
    good = channel.send("pause")
    drained = channel.drain()
    assert [c["id"] for c in drained] == [good["id"]]
    assert not bad.exists()
    assert bad.with_suffix(".bad").exists()


async def test_pause_resume_roundtrip(override):
    console = OperatorConsole(_bot_with_paper())
    assert override.is_trading_allowed()
    out = await console.apply({"action": "pause", "user": "t"})
    assert out["applied"] and not override.is_trading_allowed()
    out = await console.apply({"action": "resume", "user": "t"})
    assert out["applied"] and override.is_trading_allowed()
    # history recorded
    assert override.get_history()[-2:][0]["action"] == "pause_trading"


async def test_emergency_stop_blocks_resume(override):
    console = OperatorConsole(_bot_with_paper())
    out = await console.apply({"action": "emergency_stop", "user": "t",
                               "reason": "ops check"})
    assert out["applied"]
    assert not override.is_trading_allowed()
    out = await console.apply({"action": "resume", "user": "t"})
    assert not out["applied"]                  # ManualOverride refuses


async def test_flatten_closes_positions_via_execution_service(override):
    bot = _bot_with_paper()
    service = bot.execution_service
    await service.adapter.connect()
    await service.submit(_paper_order())
    assert service.adapter._positions["EURUSD"].quantity == 0.1

    console = OperatorConsole(bot)
    console.last_price["EURUSD"] = 1.09
    out = await console.apply({"action": "flatten", "user": "t"})
    assert out["applied"], out
    assert service.adapter._positions["EURUSD"].quantity == 0.0


async def test_cancel_all_no_pending_is_safe(override):
    console = OperatorConsole(_bot_with_paper())
    out = await console.apply({"action": "cancel_all", "user": "t"})
    assert out["applied"]


async def test_no_order_entry_actions_exist(override):
    """The control surface can only restrict/unwind, never open exposure."""
    for forbidden in ("buy", "sell", "submit_order", "place_order"):
        assert forbidden not in CONTROL_ACTIONS


def _bot_with_repo(tmp_path):
    from trading_bot.persistence.repositories import SqliteTradingRepository
    service = CanonicalExecutionService(adapter=PaperBrokerAdapter())
    return types.SimpleNamespace(
        config={}, execution_service=service,
        trading_repository=SqliteTradingRepository(str(tmp_path / "s.db")))


async def test_reset_emergency_clears_flag(override):
    console = OperatorConsole(_bot_with_paper())
    await console.apply({"action": "emergency_stop", "user": "t"})
    assert not override.is_trading_allowed()
    out = await console.apply({"action": "reset_emergency", "user": "t"})
    assert out["applied"]
    assert override.is_trading_allowed()


async def test_pause_persists_and_restores_across_restart(tmp_path, override):
    bot = _bot_with_repo(tmp_path)
    console = OperatorConsole(bot)
    out = await console.apply({"action": "pause", "user": "t"})
    assert out["applied"]

    # New console over the same repository = simulated process restart.
    override._trading_paused = False  # restart loses in-memory flags
    console2 = OperatorConsole(bot)
    await console2.restore_state()
    assert not override.is_trading_allowed()


async def test_emergency_persists_and_restores_across_restart(tmp_path, override):
    bot = _bot_with_repo(tmp_path)
    console = OperatorConsole(bot)
    await console.apply({"action": "emergency_stop", "user": "t"})

    override.emergency_stop._triggered = False  # restart loses the flag
    console2 = OperatorConsole(bot)
    await console2.restore_state()
    assert override.emergency_stop.is_triggered
    assert not override.is_trading_allowed()
