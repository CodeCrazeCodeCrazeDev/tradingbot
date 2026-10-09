#!/usr/bin/env python
"""Canonical MT5 *demo* runner — live market feed, demo-only execution.

Drives ``ModularMonolithRuntime`` with ``execution_mode="mt5_demo"``. The
adapter refuses any non-DEMO account, resolves credentials through the
canonical credential provider (MT5_LOGIN / MT5_PASSWORD / MT5_SERVER), and
never falls back to paper execution.

Sources:
  --replay N     closed M15 bars from the terminal through a non-executing
                 analysis runtime (real market data; paper boundary only)
  --follow       poll the terminal for each new closed M15 bar (the soak
                 mode; drains operator controls between polls)

Usage (hermes interpreter, credentials in env):
    python scripts/mt5_demo_runner.py --replay 40
    python scripts/mt5_demo_runner.py --follow --dashboard-port 8080
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
from typing import Any, Dict, Iterator, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.paper_runner import publish_snapshot, serve_dashboard  # noqa: E402

logger = logging.getLogger("mt5_demo_runner")

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "mt5_demo"


def _bar_to_obs(symbol: str, bar: Any, adapter: Any) -> Dict[str, Any]:
    names = getattr(getattr(bar, "dtype", None), "names", ()) or ()
    ts = int(bar["time"]) if "time" in names else 0
    volume = float(bar["tick_volume"]) if "tick_volume" in names else 0.0
    return {
        "symbol": symbol,
        "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        if ts else datetime.now(timezone.utc).isoformat(),
        "open": float(bar["open"]),
        "high": float(bar["high"]),
        "low": float(bar["low"]),
        "close": float(bar["close"]),
        "volume": volume,
        "price": float(bar["close"]),
        # Venue spec so the risk gate evaluates real margin-FX notional,
        # not synthetic-unit quantities.
        "venue": adapter.venue_id,
        "contract_size": adapter._contract_size,
        "volume_step": adapter._volume_step,
        "volume_min": adapter._volume_min,
    }


def _closed_bars(client: Any, symbol: str, timeframe_const: int, n: int):
    """Closed bars only — position 0 is the still-forming bar."""
    return client.copy_rates_from_pos(symbol, timeframe_const, 1, n)


def _mt5_config(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "account_currency": "USD",
        "terminal_path": args.terminal_path,
        "auto_approve": args.auto_approve,
        # Explicit operator opt-in: attach to the terminal's already-open
        # session when rotated creds aren't provisioned. DEMO-only
        # account validation still applies in the adapter.
        "current_session": args.current_session,
    }


def _runtime_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Runtime config for live-follow vs non-executing historical replay.

    Replay bars are real market data, but they cannot justify a live/demo
    order. The replay runtime therefore uses analysis mode and a paper
    execution boundary while a separate MT5 adapter supplies bars only.

    trading_enabled stays on in replay: execution_mode="analysis" maps to
    CanonicalExecutionService(mode="paper") with NO venue adapter attached,
    so approvals can only produce paper fills labeled venue=paper. Those
    paper fills settle on subsequent real bars and produce DECISION_OUTCOME
    rows — the honest measurement feed for advisor reliability scoring and
    research signals, without which the learning loop has nothing to
    learn from.
    """
    replay = bool(args.replay)
    return {
        "execution_mode": "analysis" if replay else "mt5_demo",
        "symbol": args.symbol,
        "account_id": "mt5_replay" if replay else "mt5_demo",
        "trading_state_path": str(Path(args.state_dir) / "trading_state.db"),
        "decision_log_path": str(Path(args.state_dir) / "decision_log.jsonl"),
        "strategy_id": args.strategy_id,
        "initial_equity": args.initial_equity,
        "trading_enabled": True,
        "mt5": _mt5_config(args),
        "cognitive_assembly": {
            "enabled": True,
            "research_interval": args.research_interval,
            "discover_advisors": False,
        },
    }


async def _connect_feed_adapter(args: argparse.Namespace) -> Any:
    """Connect the MT5 terminal for market data without attaching it to the
    runtime's execution service."""
    from trading_bot.brokers.mt5_demo import MT5DemoAdapter

    adapter = MT5DemoAdapter(config=_mt5_config(args))
    await adapter.connect()
    return adapter


def _seed_warmup(runtime: Any, symbol: str, bars: Any) -> int:
    """Seed derived-feature windows from closed bars without decision cycles."""
    closes = [float(bar["close"]) for bar in (bars or [])
              if float(bar["close"]) > 0]
    csc = getattr(runtime.bot, "csc", None)
    if csc is not None and hasattr(csc, "seed_observation_history"):
        csc.seed_observation_history(symbol, closes)
    window = getattr(runtime.bot, "_price_window", None)
    if window is not None:
        window.extend(closes)
    return len(closes)


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

        if args.strategy_id:
            # --strategy-id is a registered-capability name, not just a
            # config string: without registration the registry is empty
            # and obs['strategy_signals'] silently stays []. Only
            # allow-listed families are feedable on a single symbol.
            from trading_bot.strategies.adapter import (
                build_builtin_strategy)
            runtime.bot.register_strategy_adapter(
                build_builtin_strategy(args.strategy_id))
            logger.info("strategy_signals fed by %s", args.strategy_id)

        if args.replay:
            # Honest paper-fill frictions: zero-cost fills overstate edge
            # and would teach the reliability tracker a fantasy. Values
            # measured on this venue: ~1.25bps realized slippage on the
            # recorded MT5 demo fill; EURUSD demo spread ~2bps;
            # MetaQuotes-Demo is commission-free.
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

        if args.replay:
            # Historical bars must never reach a venue adapter through the
            # execution service. Connect MT5 separately for data only.
            feed_adapter = await _connect_feed_adapter(args)
            adapter = feed_adapter
        else:
            adapter = runtime.bot.execution_service.adapter
        client = adapter._client
        tf = getattr(client, "TIMEFRAME_M15")

        if args.dashboard_port:
            serve_dashboard(state_dir, args.dashboard_port)

        def tick_mark() -> None:
            tick = client.symbol_info_tick(args.symbol)
            if tick is not None and console is not None:
                console.last_price[args.symbol] = (
                    float(tick.bid) + float(tick.ask)) / 2.0

        if args.replay:
            bars = _closed_bars(client, args.symbol, tf, args.replay)
            for bar in bars:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                obs = _bar_to_obs(args.symbol, bar, adapter)
                tick_mark()
                await runtime.bot.run_cycle(obs)
                processed += 1
                publish_snapshot(state_dir, _snapshot(
                    processed, console, args, runtime, adapter))
        else:  # follow: poll for each newly closed M15 bar
            # Seed only the causal feature windows. Warm-up must not run
            # decisions through the live demo execution path.
            warm = _closed_bars(client, args.symbol, tf, args.warmup)
            last_bar_time = 0
            if warm is not None and len(warm):
                seeded = _seed_warmup(runtime, args.symbol, warm)
                logger.info("follow warm-up: seeded %d closed bars", seeded)
                last_bar_time = int(warm[-1]["time"])
                publish_snapshot(state_dir, _snapshot(
                    processed, console, args, runtime, adapter))
            while not args.cycles or processed < args.cycles:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                tick_mark()
                bars = _closed_bars(client, args.symbol, tf, 1)
                if bars is not None and len(bars) and int(bars[0]["time"]) != last_bar_time:
                    last_bar_time = int(bars[0]["time"])
                    obs = _bar_to_obs(args.symbol, bars[0], adapter)
                    await runtime.bot.run_cycle(obs)
                    processed += 1
                    publish_snapshot(state_dir, _snapshot(
                        processed, console, args, runtime, adapter))
                await asyncio.sleep(max(args.interval, 5.0))
    finally:
        if console is not None:
            publish_snapshot(state_dir, _snapshot(
                processed, console, args, runtime, adapter))
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
        "mode": "mt5_replay" if args.replay else "mt5_demo",
        "execution_mode": getattr(
            getattr(runtime, "bot", None), "execution_mode", None),
        "symbol": args.symbol,
        "account_login": getattr(adapter, "account_login", None),
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
                     help="replay the last N closed M15 bars")
    src.add_argument("--follow", action="store_true",
                     help="poll for each new closed M15 bar (soak mode)")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="M15")
    parser.add_argument("--cycles", type=int, default=0,
                        help="cap on bars processed in follow mode (0=forever)")
    parser.add_argument("--interval", type=float, default=15.0,
                        help="poll interval seconds in follow mode (>=5)")
    parser.add_argument("--warmup", type=int, default=30,
                        help="closed bars fed before follow mode starts "
                             "(derived-feature warm-up; 0 disables)")
    parser.add_argument("--initial-equity", type=float, default=100000.0)
    parser.add_argument("--auto-approve", action="store_true",
                        help="STANDARD approvals auto-pass (demo account only; "
                             "audited). Without it each trade waits for an "
                             "operator decision file.")
    parser.add_argument("--paper-spread-bps", type=float, default=2.0,
                        help="replay paper-fill half-spread model (bps)")
    parser.add_argument("--paper-slippage-bps", type=float, default=1.25,
                        help="replay paper-fill adverse slippage (bps); "
                             "measured ~1.25bps on the recorded MT5 demo fill")
    parser.add_argument("--paper-commission", type=float, default=0.0,
                        help="replay paper-fill commission per unit "
                             "(MetaQuotes-Demo is commission-free)")
    parser.add_argument("--current-session", action="store_true",
                        help="attach to the terminal's current session when "
                             "MT5_LOGIN/MT5_PASSWORD/MT5_SERVER are not set; "
                             "DEMO-only validation still enforced")
    parser.add_argument("--terminal-path", default=None)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0)
    parser.add_argument("--strategy-id", default=None)
    parser.add_argument("--research-interval", type=int, default=100,
                        help="observations between automatic research cycles "
                             "(0 disables cycles; evidence still flows)")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
