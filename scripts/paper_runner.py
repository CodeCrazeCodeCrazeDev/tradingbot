#!/usr/bin/env python
"""Canonical offline paper-trading runner.

Drives ``ModularMonolithRuntime`` (paper mode only — never a broker) over a
synthetic or read-only market_data.db feed. Between every cycle it drains the
operator control channel so a separate ``operator_cli.py`` process can pause,
resume, flatten, cancel-all or emergency-stop the live bot. A JSON snapshot
is published each cycle for the read-only dashboard; ``--dashboard-port``
serves it over localhost GET-only (no mutation surface exists on that server).

Usage:
    python scripts/paper_runner.py --source synthetic --cycles 200
    python scripts/paper_runner.py --source db --symbol EURUSD --interval 0.5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("paper_runner")

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "paper"


def db_observations(db_path: Path, symbol: str) -> Iterator[Dict[str, Any]]:
    """Replay market_data.db rows read-only as raw observations."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        for ts, o, h, l, c, v in con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? ORDER BY timestamp ASC",
            (symbol,),
        ):
            yield {"symbol": symbol, "timestamp": ts, "open": o, "high": h,
                   "low": l, "close": c, "volume": v, "price": c}
    finally:
        con.close()


def synthetic_observations(symbol: str, n_bars: int, seed: int
                           ) -> Iterator[Dict[str, Any]]:
    from trading_bot.evaluation.synthetic_market import (
        RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec)

    spec = SyntheticMarketSpec(
        seed=seed, instruments=(symbol,),
        regimes=(RegimeSpec("mean_revert", n_bars, vol=0.0002,
                            sine_amp=0.01, sine_period=8),))
    frames = SyntheticMarketGenerator(spec).generate()
    frame = frames[symbol]
    for row in frame.to_dict("records"):
        yield {**row, "symbol": symbol, "price": row.get("close")}


def publish_snapshot(state_dir: Path, snapshot: Dict[str, Any]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp = state_dir / ".snapshot.tmp"
    tmp.write_text(json.dumps(snapshot, default=str), encoding="utf-8")
    tmp.replace(state_dir / "snapshot.json")


def serve_dashboard(state_dir: Path, port: int) -> None:
    """GET-only snapshot server; there is no request body to mutate with."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    snapshot_path = state_dir / "snapshot.json"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - stdlib hook name
            if self.path.rstrip("/") not in ("", "/snapshot", "/snapshot.json"):
                self.send_error(404)
                return
            try:
                body = snapshot_path.read_bytes()
            except OSError:
                body = b'{"status": "no snapshot published yet"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence per-request logging
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("read-only dashboard on http://127.0.0.1:%d/", port)


async def run(args: argparse.Namespace) -> int:
    from trading_bot.foundation.runtime import ModularMonolithRuntime
    from trading_bot.interfaces.control import ControlChannel, OperatorConsole

    state_dir = Path(args.state_dir)
    channel = ControlChannel(state_dir / "control")

    runtime = ModularMonolithRuntime({
        "execution_mode": "paper",
        "symbol": args.symbol,
        "account_id": "paper",
        "trading_state_path": str(state_dir / "trading_state.db"),
        "decision_log_path": str(state_dir / "decision_log.jsonl"),
        "strategy_id": args.strategy_id,
    })
    await runtime.start()
    console = OperatorConsole(runtime.bot)
    await console.restore_state()  # paused/emergency flags survive restart

    # Seed the derived-feature windows from the durable history file so a
    # restart does not re-lock directional decisions for a warmup period.
    history_path = state_dir / "market_history.json"
    history: list = []
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))[-64:]
    except (OSError, json.JSONDecodeError):
        history = []
    if history:
        csc = getattr(runtime.bot, "csc", None)
        if csc is not None:
            csc.seed_observation_history(args.symbol, history)
        runtime.bot._price_window.extend(
            float(c) for c in history if isinstance(c, (int, float)))
        logger.info("seeded %d historical closes into feature windows",
                    len(history))

    if args.dashboard_port:
        serve_dashboard(state_dir, args.dashboard_port)

    if args.source == "db":
        source = db_observations(PROJECT_ROOT / "market_data.db", args.symbol)
    else:
        source = synthetic_observations(args.symbol, args.cycles or 200,
                                        args.seed)

    processed = 0
    emergency = False
    try:
        for obs in source:
            for command in channel.drain():
                outcome = await console.apply(command)
                logger.info("operator command %s -> %s",
                            command.get("action"), outcome)
                if command.get("action") == "emergency_stop":
                    emergency = True
            price = obs.get("price", obs.get("close"))
            if price is not None:
                symbol = str(obs.get("symbol") or args.symbol)
                console.last_price[symbol] = float(price)
                # Feed the venue mark so resting/limit/delayed orders can
                # fill on this bar — fills never use a mark older than the
                # bar that produced them.
                adapter = getattr(
                    getattr(runtime.bot, "execution_service", None),
                    "adapter", None)
                if hasattr(adapter, "on_mark"):
                    adapter.on_mark(symbol, float(price))
                history.append(float(price))
                history = history[-64:]
                try:
                    tmp = history_path.with_suffix(".tmp")
                    tmp.write_text(json.dumps(history), encoding="utf-8")
                    tmp.replace(history_path)
                except OSError:
                    logger.warning("market history persistence failed")
            if not emergency:
                await runtime.bot.run_cycle(obs)
                processed += 1
            publish_snapshot(state_dir, {
                "as_of": time.time(),
                "cycles": processed,
                "control": console.control_state(),
                "mode": "paper",
                "symbol": args.symbol,
            })
            if args.cycles and processed >= args.cycles:
                break
            if args.interval > 0:
                await asyncio.sleep(args.interval)
    finally:
        await runtime.stop()
    logger.info("runner finished: %d cycles processed", processed)
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("synthetic", "db"),
                        default="synthetic")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--interval", type=float, default=0.0,
                        help="seconds between cycles (0 = as fast as possible)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0,
                        help="serve the read-only snapshot on 127.0.0.1:PORT")
    parser.add_argument("--strategy-id", default=None,
                        help="optional registered strategy capability id")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
