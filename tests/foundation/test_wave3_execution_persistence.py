"""Wave-3 boundary tests: strict bridge facade, real repository equity,
credential vault rotation, and audit-failure veto."""

import asyncio
from dataclasses import dataclass

import pytest

from trading_bot.core.execution_bridge import PaperExecutionBridge
from trading_bot.core.unified_event_bus import (
    ActionStatus,
    LogAction,
    UnifiedDecisionBus,
)
from trading_bot.execution.service import CanonicalExecutionService
from trading_bot.foundation.contracts import (
    Fill,
    Instrument,
    InstrumentType,
    OrderSide,
)
from trading_bot.persistence.repositories import SqliteTradingRepository


@dataclass
class _Action:
    payload: dict
    action_id: str = "action-1"


def _trade_payload(**overrides):
    payload = {
        "trade_id": "trade-w3",
        "symbol": "EURUSD",
        "action": "BUY",
        "quantity": 1.0,
        "price": 1.1,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_bridge_fails_closed_without_execution_service(tmp_path) -> None:
    bridge = PaperExecutionBridge(
        persist_path=str(tmp_path / "fills.jsonl"),
        execution_service=None,
    )
    result = await bridge.execute(_Action(_trade_payload()))
    assert result["status"] == "rejected"
    assert result["reason"] == "no_execution_service"
    assert bridge.fills == []
    assert bridge.positions == {}
    # No parallel ledger file may be created.
    assert not (tmp_path / "fills.jsonl").exists()


@pytest.mark.asyncio
async def test_bridge_writes_no_parallel_ledger(tmp_path) -> None:
    ledger = tmp_path / "paper_fills.jsonl"
    bridge = PaperExecutionBridge(
        persist_path=str(ledger),
        execution_service=CanonicalExecutionService(),
    )
    result = await bridge.execute(_Action(_trade_payload()))
    assert result["status"] == "filled"
    # Authoritative record is the typed service + repository; the JSONL
    # side-ledger must not be written.
    assert not ledger.exists()


@pytest.mark.asyncio
async def test_repository_snapshot_derives_real_equity(tmp_path) -> None:
    repo = SqliteTradingRepository(str(tmp_path / "state.db"), initial_equity=1000.0)
    inst = Instrument("EURUSD", InstrumentType.FX, "paper")
    await repo.record_fill(Fill("o1", "v1", inst, OrderSide.BUY, 2.0, 100.0))
    await repo.record_fill(Fill("o2", "v2", inst, OrderSide.SELL, 1.0, 120.0))

    snapshot = await repo.snapshot("runtime")

    assert snapshot.cash == pytest.approx(920.0)  # 1000 - 200 + 120
    assert snapshot.equity == pytest.approx(1020.0)  # cash + 1.0 * 100 cost basis
    assert len(snapshot.positions) == 1


def test_credential_vault_rotate_key_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "pathlib.Path.home", classmethod(lambda cls: tmp_path)
    )
    from trading_bot.security.credential_vault import SecureCredentialVault

    vault = SecureCredentialVault(vault_path=str(tmp_path / ".credentials.enc"))
    vault.store_credential("test_key", "secret-value")
    vault.rotate_key()

    reloaded = SecureCredentialVault(vault_path=str(tmp_path / ".credentials.enc"))
    assert reloaded.get_credential("test_key") == "secret-value"


@pytest.mark.asyncio
async def test_shielded_action_vetoed_when_audit_unwritable(tmp_path) -> None:
    # log_path inside a regular file -> makedirs/open fail -> audit unhealthy.
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    bus = UnifiedDecisionBus(config={"log_path": str(blocker / "audit.jsonl")})
    bus.register_voter(
        "shield",
        lambda action: {"decision": "PASS", "reason": "ok"},
    )
    await bus.start()

    action = LogAction(
        action_type="TRADE_EXECUTION",
        payload={"symbol": "EURUSD", "quantity": 1.0},
        agent_id="test",
    )
    await bus.propose_action(action)
    for _ in range(200):
        if action.status in {ActionStatus.VETOED, ActionStatus.APPROVED,
                             ActionStatus.EXECUTED, ActionStatus.FAILED}:
            break
        await asyncio.sleep(0.01)

    assert action.status == ActionStatus.VETOED
    assert bus._audit_healthy is False
    await bus.stop()
