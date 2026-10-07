"""Reconciliation failure must block new entries, not merely log.

The runtime wires ExecutionReconciler into startup/post-run/pre-stop.
When venue-vs-ledger state diverges (or the venue cannot be queried),
the manual-override emergency stop is the fail-closed admission gate —
these tests pin that behavior and reset the singleton afterwards.
"""

from datetime import datetime, timezone

import pytest

from trading_bot.foundation.contracts import ReconciliationResult


def _result(matched: bool, differences=()) -> ReconciliationResult:
    return ReconciliationResult(
        venue="paper", checked_at=datetime.now(timezone.utc),
        matched=matched, position_differences=list(differences))
from trading_bot.foundation.runtime import ModularMonolithRuntime
from trading_bot.human_layer.override import get_manual_override


@pytest.fixture(autouse=True)
def _reset_override_singleton():
    override = get_manual_override()
    yield
    override.emergency_stop.reset("test-cleanup")
    override._trading_paused = False


class _MismatchReconciler:
    async def reconcile_positions(self, account_id=None):
        return _result(False, [{"symbol": "EURUSD", "delta": 0.5}])

    async def recover_pending_orders(self):
        return {"count": 0, "recovered": []}

    async def aclose(self):
        return None


class _RaisingReconciler(_MismatchReconciler):
    async def reconcile_positions(self, account_id=None):
        raise RuntimeError("venue unreachable")


@pytest.mark.asyncio
async def test_mismatched_reconciliation_triggers_emergency_stop() -> None:
    runtime = ModularMonolithRuntime({})
    runtime._reconciler = _MismatchReconciler()
    await runtime._recover_execution_state()
    override = get_manual_override()
    assert override.emergency_stop.is_triggered
    assert not override.is_trading_allowed()


@pytest.mark.asyncio
async def test_failed_reconciliation_triggers_emergency_stop() -> None:
    runtime = ModularMonolithRuntime({})
    runtime._reconciler = _RaisingReconciler()
    await runtime._recover_execution_state()
    override = get_manual_override()
    assert override.emergency_stop.is_triggered
    assert not override.is_trading_allowed()


@pytest.mark.asyncio
async def test_matched_reconciliation_leaves_gate_open() -> None:
    class _Match(_MismatchReconciler):
        async def reconcile_positions(self, account_id=None):
            return _result(True)

    runtime = ModularMonolithRuntime({})
    runtime._reconciler = _Match()
    await runtime._recover_execution_state()
    override = get_manual_override()
    assert not override.emergency_stop.is_triggered
