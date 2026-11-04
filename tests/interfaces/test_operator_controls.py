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


async def test_unsigned_queued_reset_does_not_clear_flag(override):
    console = OperatorConsole(_bot_with_paper())
    await console.apply({"action": "emergency_stop", "user": "t"})
    assert not override.is_trading_allowed()
    out = await console.apply({"action": "reset_emergency", "user": "t"})
    assert not out["applied"]
    assert not override.is_trading_allowed()
    assert "signed" in out["error"]


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


@pytest.fixture
def reset_case(tmp_path, monkeypatch):
    import sqlite3
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from trading_bot.interfaces import operator_reset as reset
    from trading_bot.persistence.repositories import SqliteTradingRepository

    state = tmp_path / "paper"
    state.mkdir()
    (state / "snapshot.json").write_text(json.dumps({"mode": "paper"}))
    SqliteTradingRepository(str(state / "trading_state.db")).close()
    with sqlite3.connect(state / "trading_state.db") as con:
        con.executemany("INSERT INTO account_state VALUES(?,?,?)", [
            ("control:emergency", "1", "incident-one"),
            ("control:paused", "1", "keep-paused")])
    keys = tmp_path / "keys"
    keys.mkdir()
    monkeypatch.setattr(reset, "key_directory", lambda _: keys)
    key = Ed25519PrivateKey.generate()
    (keys / "operator.pub").write_bytes(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw))
    payload = reset.reset_request(state, "operator-test", "Reviewed paper stop")

    def sign(p=None):
        p = payload if p is None else p
        return {"payload": p, "signature": key.sign(reset.canonical(p)).hex()}

    return state, reset, payload, sign


def test_signed_reset_commits_receipt_and_preserves_pause(reset_case):
    import sqlite3
    state, reset, _, sign = reset_case
    with reset.runner_lock(state):
        receipt = reset.consume_reset(state, sign())
    with sqlite3.connect(state / "trading_state.db") as con:
        controls = dict(con.execute("SELECT key,value FROM account_state"))
        assert controls["control:emergency"] == "0"
        assert controls["control:paused"] == "1"
        row = con.execute("SELECT event_json FROM audit_events").fetchone()
        assert json.loads(row[0]) == receipt
        assert "control:reset_used:" + receipt["correlation_id"] in controls
    with pytest.raises(reset.ResetApprovalError):
        reset.consume_reset(state, sign())


@pytest.mark.parametrize("change", [
    {"action": "resume"}, {"database": "other-state"}, {"mode": "live"},
    {"expires_at": 1}, {"issued_at": float("inf")}, {"nonce": "../bad"},
    {"issued_by": ""}, {"reason": ""}, {"incident": "0" * 64},
])
def test_reset_rejects_invalid_or_wrong_scope_approvals(reset_case, change):
    import sqlite3
    state, reset, payload, sign = reset_case
    with pytest.raises((reset.ResetApprovalError, ValueError)):
        reset.consume_reset(state, sign({**payload, **change}))
    with sqlite3.connect(state / "trading_state.db") as con:
        assert con.execute("SELECT value FROM account_state WHERE key='control:emergency'").fetchone()[0] == "1"
        assert con.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 0


def test_reset_rejects_tampering_and_untrusted_signer(reset_case):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    state, reset, payload, sign = reset_case
    approval = sign()
    approval["payload"] = {**payload, "reason": "changed after signing"}
    with pytest.raises(reset.ResetApprovalError):
        reset.consume_reset(state, approval)
    approval = {"payload": payload, "signature":
                Ed25519PrivateKey.generate().sign(reset.canonical(payload)).hex()}
    with pytest.raises(reset.ResetApprovalError):
        reset.consume_reset(state, approval)


def test_reset_rejects_consumed_nonce_even_for_repeated_incident(reset_case):
    import sqlite3
    state, reset, _, sign = reset_case
    reset.consume_reset(state, sign())
    # Replaying a restored old incident must not allow reuse of the nonce.
    with sqlite3.connect(state / "trading_state.db") as con:
        con.execute("UPDATE account_state SET value='1',updated_at='incident-one' WHERE key='control:emergency'")
    with pytest.raises(reset.ResetApprovalError, match="consumed"):
        reset.consume_reset(state, sign())


def test_reset_rolls_back_if_audit_cannot_be_written(reset_case):
    import sqlite3
    state, reset, _, sign = reset_case
    with sqlite3.connect(state / "trading_state.db") as con:
        con.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON audit_events "
                    "BEGIN SELECT RAISE(ABORT, 'audit unavailable'); END")
    with pytest.raises(sqlite3.DatabaseError):
        reset.consume_reset(state, sign())
    with sqlite3.connect(state / "trading_state.db") as con:
        controls = dict(con.execute("SELECT key,value FROM account_state"))
        assert controls["control:emergency"] == "1"
        assert not any(k.startswith("control:reset_used:") for k in controls)


def test_reset_requires_stopped_paper_state_and_no_queued_commands(reset_case):
    state, reset, _, sign = reset_case
    with reset.runner_lock(state):
        with pytest.raises(reset.ResetApprovalError, match="active"):
            with reset.runner_lock(state):
                pass
    # Crash/release leaves no permanent lock.
    with reset.runner_lock(state):
        pass
    (state / "snapshot.json").write_text(json.dumps({"mode": "live"}))
    with pytest.raises(reset.ResetApprovalError, match="paper"):
        reset.consume_reset(state, sign())
    (state / "snapshot.json").write_text(json.dumps({"mode": "paper"}))
    ControlChannel(state / "control").send("emergency_stop")
    with pytest.raises(reset.ResetApprovalError, match="Pending"):
        reset.consume_reset(state, sign())


def test_cli_rejects_unsigned_reset_before_queuing(reset_case):
    from scripts.operator_cli import main
    state, _, _, _ = reset_case
    assert main(["--state-dir", str(state), "reset-emergency"]) == 2
    assert not list((state / "control").glob("cmd-*.json"))


def test_cli_applies_external_signed_reset(reset_case, tmp_path):
    from scripts.operator_cli import main
    state, _, _, sign = reset_case
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps(sign()))
    assert main(["--state-dir", str(state), "reset-emergency",
                 "--approval-file", str(approval)]) == 0


def test_interactive_reset_decline_does_not_enroll_key(reset_case, monkeypatch):
    import sys
    state, reset, payload, _ = reset_case
    public = reset.key_directory(state) / "operator.pub"
    public.unlink()
    monkeypatch.setattr(sys, "stdin", types.SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", lambda _: "no")
    with pytest.raises(reset.ResetApprovalError, match="cancelled"):
        reset.sign_interactively(state, payload)
    assert not public.exists()
    assert not (public.parent / "operator.dpapi").exists()


def test_interactive_reset_requires_terminal(reset_case, monkeypatch):
    import sys
    state, reset, payload, _ = reset_case
    monkeypatch.setattr(sys, "stdin", types.SimpleNamespace(isatty=lambda: False))
    with pytest.raises(reset.ResetApprovalError, match="interactive"):
        reset.sign_interactively(state, payload)


def test_interactive_dpapi_enrollment_and_signing_in_temporary_custody(reset_case, monkeypatch):
    import sys
    if sys.platform != "win32":
        pytest.skip("Windows DPAPI custody")
    state, reset, payload, _ = reset_case
    public = reset.key_directory(state) / "operator.pub"
    public.unlink()
    monkeypatch.setattr(sys, "stdin", types.SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", lambda _: "RESET PAPER")
    approval = reset.sign_interactively(state, payload)
    assert (public.parent / "operator.dpapi").read_bytes().startswith(b"DPAPI\x01")
    assert reset.consume_reset(state, approval)["outcome"] == "applied"
