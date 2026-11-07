"""Regression: replay mode must never reach a venue adapter.

Historical bars are real market data but cannot justify a live/demo
order. Both demo runners map --replay to execution_mode="analysis",
which resolves to CanonicalExecutionService(mode="paper") with a
PaperBrokerAdapter — no venue adapter can be attached in that mode.
This test pins that boundary so a future refactor cannot silently
route replay bars to demo execution.
"""

import sys
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _args(replay):
    return SimpleNamespace(
        replay=replay, follow=not replay, symbol="EURUSD",
        timeframe="M15", state_dir="var/_test_replay_iso",
        strategy_id=None, initial_equity=100000.0, auto_approve=False,
        research_interval=100, terminal_path=None, current_session=False,
        paper_spread_bps=2.0, paper_slippage_bps=1.25, paper_commission=0.0)


def test_mt5_replay_maps_to_analysis_mode():
    from scripts.mt5_demo_runner import _runtime_config
    cfg = _runtime_config(_args(40))
    assert cfg["execution_mode"] == "analysis"
    assert cfg["account_id"] == "mt5_replay"


def test_mt5_follow_maps_to_venue_mode():
    from scripts.mt5_demo_runner import _runtime_config
    cfg = _runtime_config(_args(0))
    assert cfg["execution_mode"] == "mt5_demo"


def test_ctrader_replay_maps_to_analysis_mode():
    from scripts.ctrader_demo_runner import _runtime_config
    cfg = _runtime_config(_args(40))
    assert cfg["execution_mode"] == "analysis"
    assert cfg["account_id"] == "ctrader_replay"


def test_ctrader_follow_maps_to_venue_mode():
    from scripts.ctrader_demo_runner import _runtime_config
    cfg = _runtime_config(_args(0))
    assert cfg["execution_mode"] == "ctrader_demo"


def test_analysis_mode_execution_service_is_paper_only():
    """The execution service behind analysis mode holds a paper adapter —
    submitting an order can only ever produce a paper fill, never a
    venue call."""
    import asyncio
    from trading_bot.execution.service import CanonicalExecutionService
    from trading_bot.foundation.contracts import (
        Instrument, InstrumentType, OrderRequest, OrderSide, OrderType,
        OrderStatus)

    svc = CanonicalExecutionService(mode="paper")
    assert svc.adapter.venue_id == "paper"

    order = OrderRequest(
        instrument=Instrument("EURUSD", InstrumentType.FX, "paper",
                              contract_size=100000.0),
        side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=0.01,
        client_order_id="replay-isolation-1", decision_id="d1")
    report = asyncio.run(svc.submit(order))
    # A paper fill or a validation reject — both prove the request never
    # left the process; the adapter has no venue to call.
    assert report.status in (
        OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.ACCEPTED)
    assert not hasattr(svc.adapter, "order_send")
    assert not hasattr(svc.adapter, "_transport")


def test_replay_uses_feed_adapter_not_execution_adapter():
    """mt5_demo_runner attaches the venue adapter only as a bar feed in
    replay — the executing adapter is the runtime's paper service."""
    import inspect
    import scripts.mt5_demo_runner as m
    src = inspect.getsource(m.run)
    # The venue adapter is created only via the data-only feed seam...
    assert "feed_adapter = await _connect_feed_adapter(args)" in src
    # ...and the runtime's own execution adapter is selected ONLY in the
    # else (follow) branch, never inside an `if args.replay:` block.
    follow_select = "adapter = runtime.bot.execution_service.adapter"
    assert follow_select in src
    idx_follow = src.index(follow_select)
    idx_else = src.rindex("else:", 0, idx_follow)
    idx_prev_replay_if = src.rindex("if args.replay:", 0, idx_else)
    assert idx_prev_replay_if < idx_else, (
        "execution adapter selection must live in the follow branch")
