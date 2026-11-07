#!/usr/bin/env python
"""Canonical cTrader *demo* runner — live market feed, demo-only execution.

Drives ``ModularMonolithRuntime`` with ``execution_mode="ctrader_demo"``.
The adapter hard-pins the demo endpoint, verifies the account's ``isLive``
flag is false, resolves credentials through the canonical credential
provider (CTRADER_CLIENT_ID / CTRADER_CLIENT_SECRET / CTRADER_ACCESS_TOKEN /
CTRADER_ACCOUNT_ID), and never falls back to paper execution.

Sources:
  --replay N     last N closed M15 trendbars through a non-executing
                 analysis runtime (real market data; paper boundary only)
  --follow       poll for each new closed M15 trendbar (the soak mode;
                 drains operator controls between polls)

Usage (hermes interpreter, ctrader-open-api installed, creds provisioned):
    python scripts/ctrader_demo_runner.py --replay 40
    python scripts/ctrader_demo_runner.py --follow --dashboard-port 8080
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.paper_runner import publish_snapshot, serve_dashboard  # noqa: E402
from scripts.mt5_demo_runner import _seed_warmup  # noqa: E402

logger = logging.getLogger("ctrader_demo_runner")

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "ctrader_demo"
M15_MS = 15 * 60 * 1000


def _closed_boundary_ms() -> int:
    """Start (ms) of the still-forming M15 bar — only bars strictly before
    this boundary are closed."""
    return int(time.time() * 1000) // M15_MS * M15_MS


async def _trendbars(adapter: Any, n: int,
                     to_ms: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch up to ``n`` closed M15 trendbars for the configured symbol.

    ``to_ms`` defaults to the current bar's open so the forming bar is
    never returned. Encoding per Open API: ``low`` is absolute price *
    10**digits; ``deltaOpen``/``deltaClose``/``deltaHigh`` are positive
    offsets from ``low`` in the same scale.
    """
    from trading_bot.brokers.ctrader_demo import _messages

    if adapter._symbol_id is None:
        return []
    msgs = _messages()
    to_ms = int(to_ms if to_ms is not None else _closed_boundary_ms())
    req = msgs.ProtoOAGetTrendbarsReq()
    req.ctidTraderAccountId = adapter.ctid_trader_account_id
    req.symbolId = adapter._symbol_id
    req.period = 7  # ProtoOATrendbarPeriod.M15
    req.toTimestamp = to_ms
    req.fromTimestamp = to_ms - max(n, 1) * M15_MS * 2
    req.count = int(n)
    res = await adapter._request(req)
    scale = 10 ** adapter._digits
    bars = []
    for tb in getattr(res, "trendbar", ()):
        low = float(getattr(tb, "low", 0.0)) / scale
        bars.append({
            "time": int(getattr(tb, "utcTimestampInMinutes", 0)) * 60,
            "open": (float(getattr(tb, "low", 0.0))
                     + float(getattr(tb, "deltaOpen", 0.0))) / scale,
            "high": (float(getattr(tb, "low", 0.0))
                     + float(getattr(tb, "deltaHigh", 0.0))) / scale,
            "low": low,
            "close": (float(getattr(tb, "low", 0.0))
                      + float(getattr(tb, "deltaClose", 0.0))) / scale,
            "volume": float(getattr(tb, "volume", 0.0)),
        })
    bars.sort(key=lambda b: b["time"])
    return bars


def _bar_to_obs(symbol: str, bar: Dict[str, Any], adapter: Any,
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    obs = {
        "symbol": symbol,
        "timestamp": datetime.fromtimestamp(
            bar["time"], tz=timezone.utc).isoformat()
        if bar.get("time") else datetime.now(timezone.utc).isoformat(),
        "open": float(bar["open"]),
        "high": float(bar["high"]),
        "low": float(bar["low"]),
        "close": float(bar["close"]),
        "volume": float(bar["volume"]),
        "price": float(bar["close"]),
        # Venue spec (in lots) so the risk gate evaluates real margin-FX
        # notional, not synthetic-unit quantities.
        "venue": adapter.venue_id,
        "contract_size": adapter._lot_size,
        "volume_step": adapter._volume_step / adapter._lot_size
        if adapter._lot_size else 0.0,
        "volume_min": adapter._volume_min / adapter._lot_size
        if adapter._lot_size else 0.0,
    }
    if extra:
        obs.update(extra)
    return obs


def _quote_extra(adapter: Any) -> Dict[str, Any]:
    """Live bid/ask from the subscribed spot feed — point-in-time correct
    in follow mode only. Never attach to historical replay bars."""
    if adapter._symbol_id is None:
        return {}
    q = adapter.latest_quote(adapter._symbol_id)
    if not q or not q.get("bid") or not q.get("ask"):
        return {}
    bid, ask = float(q["bid"]), float(q["ask"])
    mid = (bid + ask) / 2.0
    return {"bid": bid, "ask": ask,
            "mark_price": mid,
            "spread_bps": (ask - bid) / mid * 1e4 if mid else None,
            "quote_time": q.get("ts")}


def _ctrader_config(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "account_currency": str(
            getattr(args, "account_currency", "USD")).upper(),
        "auto_approve": args.auto_approve,
    }


def _runtime_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Runtime config for live-follow vs non-executing historical replay.

    Replay bars are real market data, but they cannot justify a live/demo
    order. The replay runtime therefore uses analysis mode and a paper
    execution boundary while a separate cTrader adapter supplies bars
    only — see mt5_demo_runner for the same construction.
    """
    replay = bool(args.replay)
    return {
        "execution_mode": "analysis" if replay else "ctrader_demo",
        "symbol": args.symbol,
        "account_id": "ctrader_replay" if replay else "ctrader_demo",
        "trading_state_path": str(Path(args.state_dir) / "trading_state.db"),
        "decision_log_path": str(Path(args.state_dir) / "decision_log.jsonl"),
        "strategy_id": args.strategy_id,
        "initial_equity": args.initial_equity,
        "trading_enabled": True,
        "ctrader": _ctrader_config(args),
        "cognitive_assembly": {
            "enabled": True,
            "research_interval": args.research_interval,
            "discover_advisors": False,
        },
    }


async def _connect_feed_adapter(args: argparse.Namespace) -> Any:
    """Connect cTrader for market data without attaching it to the
    runtime's execution service."""
    from trading_bot.brokers.ctrader_demo import CTraderDemoAdapter

    adapter = CTraderDemoAdapter(config=_ctrader_config(args))
    await adapter.connect()
    return adapter


async def run(args: argparse.Namespace) -> int:
    from trading_bot.foundation.runtime import ModularMonolithRuntime
    from trading_bot.interfaces.control import ControlChannel, OperatorConsole

    state_dir = Path(args.state_dir)
    channel = ControlChannel(state_dir / "control")

    runtime = ModularMonolithRuntime(_runtime_config(args))
    console = None
    feed_adapter = None
    adapter = None
    processed = 0
    try:
        await runtime.start()
        console = OperatorConsole(runtime.bot)
        await console.restore_state()

        # Restore open positions from the prior session — without this a
        # restart orphans persisted fills: the ledger holds exposure the
        # CSC forgot, so those positions never settle and never score
        # their predictions (self_state then reports phantom exposure).
        csc0 = getattr(runtime.bot, "csc", None)
        pos_state_path = state_dir / "open_positions.json"
        if (csc0 is not None and hasattr(csc0, "import_open_positions")
                and pos_state_path.exists()):
            try:
                n = csc0.import_open_positions(json.loads(
                    pos_state_path.read_text(encoding="utf-8")))
                if n:
                    logger.info("restored %d open positions", n)
            except Exception as exc:
                logger.warning("open-position restore failed: %s", exc)

        if args.strategy_id:
            from trading_bot.strategies.adapter import (
                build_builtin_strategy)
            runtime.bot.register_strategy_adapter(
                build_builtin_strategy(args.strategy_id))
            logger.info("strategy_signals fed by %s", args.strategy_id)

        if args.replay:
            paper_adapter = getattr(
                runtime.bot.execution_service, "adapter", None)
            for attr, val in (("spread_bps", args.paper_spread_bps),
                              ("slippage_bps", args.paper_slippage_bps),
                              ("commission_per_unit",
                               args.paper_commission)):
                if hasattr(paper_adapter, attr):
                    setattr(paper_adapter, attr, val)
            logger.info(
                "replay paper cost model: spread=%.2fbps slip=%.2fbps "
                "comm=%.4f/unit", args.paper_spread_bps,
                args.paper_slippage_bps, args.paper_commission)
            # Historical bars must never reach a venue adapter through the
            # execution service. Connect cTrader separately for data only.
            feed_adapter = await _connect_feed_adapter(args)
            adapter = feed_adapter
        else:
            adapter = runtime.bot.execution_service.adapter
            # Spot subscription feeds the fresh-quote fields; advisory and
            # risk keep working off the bar close either way.
            try:
                await adapter.subscribe_spots([adapter._symbol_id])
            except Exception as exc:
                logger.warning("spot subscribe failed (quote fields will "
                               "be absent): %s", exc)

        if args.dashboard_port:
            serve_dashboard(state_dir, args.dashboard_port)

        if args.replay:
            # Seed derived-feature windows from closed bars before the
            # replay window — real older history, no lookahead.
            if args.warmup:
                warm = await _trendbars(adapter, args.replay + args.warmup)
                if len(warm) > args.replay:
                    seeded = await _seed_warmup(
                        runtime, args.symbol,
                        warm[:len(warm) - args.replay])
                    logger.info("replay warm-up: seeded %d closed bars "
                                "from before the replay window", seeded)
            bars = await _trendbars(adapter, args.replay)
            for bar in bars:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                obs = _bar_to_obs(args.symbol, bar, adapter)
                await runtime.bot.run_cycle(obs)
                processed += 1
                publish_snapshot(state_dir, _snapshot(
                    processed, console, args, runtime, adapter))
        else:  # follow: poll for each newly closed M15 bar
            warm = await _trendbars(adapter, args.warmup)
            if warm:
                seeded = await _seed_warmup(runtime, args.symbol, warm)
                logger.info("follow warm-up: seeded %d closed bars", seeded)
                last_bar_time = int(warm[-1]["time"])
            else:
                last_bar_time = 0

            quiet_polls = 0
            quiet_logged = False
            publish_snapshot(state_dir, _snapshot(
                processed, console, args, runtime, adapter))
            while not args.cycles or processed < args.cycles:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                bars = await _trendbars(adapter, 1)
                if bars and int(bars[-1]["time"]) != last_bar_time:
                    last_bar_time = int(bars[-1]["time"])
                    obs = _bar_to_obs(
                        args.symbol, bars[-1], adapter,
                        _quote_extra(adapter))
                    await runtime.bot.run_cycle(obs)
                    processed += 1
                    quiet_polls = 0
                    quiet_logged = False
                    publish_snapshot(state_dir, _snapshot(
                        processed, console, args, runtime, adapter))
                else:
                    quiet_polls += 1
                    now = datetime.now(timezone.utc)
                    fx_quiet = (now.weekday() == 5
                                or (now.weekday() == 6 and now.hour < 22)
                                or (now.weekday() == 4 and now.hour >= 22))
                    if quiet_polls >= 3 and not quiet_logged:
                        quiet_logged = True
                        logger.info(
                            "FX market closed (weekend) - polling at "
                            "reduced cadence" if fx_quiet else
                            "no new bars after %d polls - continuing to "
                            "poll", quiet_polls)
                    await asyncio.sleep(
                        max(args.interval * 6.0, 60.0)
                        if fx_quiet and quiet_polls >= 3
                        else max(args.interval, 5.0))
                    continue
                await asyncio.sleep(max(args.interval, 5.0))
    finally:
        if console is not None:
            publish_snapshot(state_dir, _snapshot(
                processed, console, args, runtime, adapter))
        # Persist open positions so a restart keeps tracking them — atomic
        # temp+replace; a crashed write must not corrupt prior state.
        csc1 = getattr(getattr(runtime, "bot", None), "csc", None)
        if csc1 is not None and hasattr(csc1, "export_open_positions"):
            try:
                pos_state_path = state_dir / "open_positions.json"
                tmp = pos_state_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(
                    csc1.export_open_positions(), default=str),
                    encoding="utf-8")
                tmp.replace(pos_state_path)
            except Exception as exc:
                logger.warning("open-position export failed: %s", exc)
        if feed_adapter is not None:
            await feed_adapter.disconnect()
        await runtime.stop()
    logger.info("demo runner finished: %d cycles processed", processed)
    return 0


def _snapshot(processed: int, console, args, runtime=None,
              adapter=None) -> Dict[str, Any]:
    if adapter is None:
        adapter = getattr(
            getattr(console.bot, "execution_service", None), "adapter", None)
    csc = getattr(getattr(runtime, "bot", None), "csc", None)
    return {
        "as_of": time.time(),
        "cycles": processed,
        "control": console.control_state(),
        "mode": "ctrader_replay" if args.replay else "ctrader_demo",
        "execution_mode": getattr(
            getattr(runtime, "bot", None), "execution_mode", None),
        "symbol": args.symbol,
        "ctid_trader_account_id": getattr(
            adapter, "ctid_trader_account_id", None),
        "account_mode": getattr(adapter, "account_mode", None),
        "advisors": csc.advisory_report() if csc is not None
        and hasattr(csc, "advisory_report") else None,
        "funnel": csc.funnel_report() if csc is not None
        and hasattr(csc, "funnel_report") else None,
        "ai_stack": runtime.ai_stack.explain()
        if getattr(runtime, "ai_stack", None) is not None else None,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--replay", type=int, metavar="N",
                     help="replay the last N closed M15 trendbars")
    src.add_argument("--follow", action="store_true",
                     help="poll for each new closed M15 trendbar "
                          "(soak mode)")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="M15")
    parser.add_argument("--account-currency", default="USD",
                        help="declared deposit currency — the adapter "
                             "fails closed if the account's actual "
                             "currency differs")
    parser.add_argument("--cycles", type=int, default=0,
                        help="cap on bars processed in follow mode (0=forever)")
    parser.add_argument("--interval", type=float, default=15.0,
                        help="poll interval seconds in follow mode (>=5)")
    parser.add_argument("--warmup", type=int, default=30,
                        help="closed bars fed before follow/replay starts "
                             "(derived-feature warm-up; 0 disables)")
    parser.add_argument("--initial-equity", type=float, default=100000.0)
    parser.add_argument("--auto-approve", action="store_true",
                        help="STANDARD approvals auto-pass (demo account "
                             "only; audited). Without it each trade waits "
                             "for an operator decision file.")
    parser.add_argument("--paper-spread-bps", type=float, default=2.0,
                        help="replay paper-fill half-spread model (bps)")
    parser.add_argument("--paper-slippage-bps", type=float, default=1.25,
                        help="replay paper-fill adverse slippage (bps)")
    parser.add_argument("--paper-commission", type=float, default=0.0,
                        help="replay paper-fill commission per unit")
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0)
    parser.add_argument("--strategy-id", default=None)
    parser.add_argument("--research-interval", type=int, default=100,
                        help="observations between automatic research "
                             "cycles (0 disables; evidence still flows)")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
