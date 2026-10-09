#!/usr/bin/env python
"""Canonical MT5 *demo* runner — live market feed, demo-only execution.

Drives ``ModularMonolithRuntime`` with ``execution_mode="mt5_demo"``. The
adapter refuses any non-DEMO account, resolves credentials through the
canonical credential provider (MT5_LOGIN / MT5_PASSWORD / MT5_SERVER), and
never falls back to paper execution.

Sources:
  --replay N     closed M15 bars from the terminal (validates the full
                 pipeline on real recent market data)
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


async def run(args: argparse.Namespace) -> int:
    from trading_bot.foundation.runtime import ModularMonolithRuntime
    from trading_bot.interfaces.control import ControlChannel, OperatorConsole

    state_dir = Path(args.state_dir)
    channel = ControlChannel(state_dir / "control")

    runtime = ModularMonolithRuntime({
        "execution_mode": "mt5_demo",
        "symbol": args.symbol,
        "account_id": "mt5_demo",
        "trading_state_path": str(state_dir / "trading_state.db"),
        "decision_log_path": str(state_dir / "decision_log.jsonl"),
        "strategy_id": args.strategy_id,
        "initial_equity": args.initial_equity,
        "mt5": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "account_currency": "USD",
            "terminal_path": args.terminal_path,
            "auto_approve": args.auto_approve,
        },
    })
    await runtime.start()  # connects + validates demo account inside start()
    console = OperatorConsole(runtime.bot)
    await console.restore_state()

    adapter = runtime.bot.execution_service.adapter
    client = adapter._client
    tf = getattr(client, "TIMEFRAME_M15")

    if args.dashboard_port:
        serve_dashboard(state_dir, args.dashboard_port)

    def tick_mark() -> None:
        tick = client.symbol_info_tick(args.symbol)
        if tick is not None:
            console.last_price[args.symbol] = (
                float(tick.bid) + float(tick.ask)) / 2.0

    processed = 0
    try:
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
                publish_snapshot(state_dir, _snapshot(processed, console, args))
        else:  # follow: poll for each newly closed M15 bar
            # Warm-up: feed the last N closed bars first so derived
            # features (volatility/trend — needed by the evidence gate
            # after ~21 observations) exist before the first live bar.
            warm = _closed_bars(client, args.symbol, tf, args.warmup)
            last_bar_time = 0
            if warm is not None and len(warm):
                logger.info("follow warm-up: %d closed bars", len(warm))
                for bar in warm:
                    obs = _bar_to_obs(args.symbol, bar, adapter)
                    tick_mark()
                    await runtime.bot.run_cycle(obs)
                    publish_snapshot(state_dir,
                                     _snapshot(processed, console, args))
                last_bar_time = int(warm[-1]["time"])
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
                    publish_snapshot(state_dir,
                                     _snapshot(processed, console, args))
                await asyncio.sleep(max(args.interval, 5.0))
    finally:
        publish_snapshot(state_dir, _snapshot(processed, console, args))
        await runtime.stop()
    logger.info("demo runner finished: %d cycles processed", processed)
    return 0


def _snapshot(processed: int, console, args) -> Dict[str, Any]:
    return {
        "as_of": time.time(),
        "cycles": processed,
        "control": console.control_state(),
        "mode": "mt5_demo",
        "symbol": args.symbol,
        "account_login": getattr(
            getattr(console.bot.execution_service, "adapter", None),
            "account_login", None),
        "account_mode": getattr(
            getattr(console.bot.execution_service, "adapter", None),
            "account_mode", None),
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
    parser.add_argument("--terminal-path", default=None)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0)
    parser.add_argument("--strategy-id", default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
