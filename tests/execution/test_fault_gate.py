"""Reduced-scale run of the fault-injection gate (scripts/fault_gate.py).

The full 10,000-event gate runs via ``python scripts/fault_gate.py``; this
pins the same invariants inside the test suite at a cheap event count.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.fault_gate import run_gate  # noqa: E402


async def test_fault_gate_invariants_small_run(tmp_path):
    result = await run_gate(events=400, seed=5, workdir=tmp_path)
    assert result["passed"], result["violations"]


async def test_resubmit_returns_stored_report_post_restart(tmp_path):
    """Durable dedup: after a restart, resubmitting an existing
    client_order_id replays the stored report without touching the venue."""
    import random

    from trading_bot.execution.service import (
        CanonicalExecutionService, PaperBrokerAdapter)
    from trading_bot.foundation.contracts import (
        Instrument, InstrumentType, OrderRequest, OrderSide, OrderType,
        OrderStatus)
    from trading_bot.persistence.repositories import SqliteTradingRepository
    from scripts.fault_gate import InstrumentedPaperAdapter, _order

    db = str(tmp_path / "state.db")
    repo = SqliteTradingRepository(db)
    adapter = InstrumentedPaperAdapter(random.Random(1))
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    order = _order("dup-1", random.Random(2))
    first = await service.submit(order)
    assert first.status == OrderStatus.FILLED
    assert adapter.submits["dup-1"] == 1

    # restart over the same durable file
    repo2 = SqliteTradingRepository(db)
    adapter2 = InstrumentedPaperAdapter(random.Random(3))
    service2 = CanonicalExecutionService(adapter=adapter2, repository=repo2)
    second = await service2.submit(order)
    assert second.status == OrderStatus.FILLED
    assert adapter2.submits["dup-1"] == 0     # venue never saw a retry
    assert second.fills == first.fills


async def test_resubmit_conflicting_params_rejected(tmp_path):
    import random

    from trading_bot.execution.service import (
        CanonicalExecutionService, PaperBrokerAdapter)
    from trading_bot.foundation.contracts import (
        Instrument, InstrumentType, OrderRequest, OrderSide, OrderType,
        OrderStatus)
    from trading_bot.persistence.repositories import SqliteTradingRepository
    from scripts.fault_gate import InstrumentedPaperAdapter

    repo = SqliteTradingRepository(str(tmp_path / "state.db"))
    adapter = InstrumentedPaperAdapter(random.Random(4))
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    inst = Instrument("EURUSD", InstrumentType.FX, "paper")
    await service.submit(OrderRequest(
        instrument=inst, side=OrderSide.BUY, order_type=OrderType.MARKET,
        quantity=0.1, client_order_id="c", decision_id="d", price=1.1))
    conflict = await service.submit(OrderRequest(
        instrument=inst, side=OrderSide.SELL, order_type=OrderType.MARKET,
        quantity=0.5, client_order_id="c", decision_id="d", price=1.1))
    assert conflict.status == OrderStatus.REJECTED
    assert "collision" in conflict.error
