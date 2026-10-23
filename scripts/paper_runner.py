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
from typing import Any, Dict, Iterator, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("paper_runner")

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "paper"


def _load_htf_bars(db_path: Path, symbol: str, timeframe: str
                   ) -> List[Tuple[str, float]]:
    """All (timestamp, close) rows for a second timeframe — loaded once so
    the M15 replay can attach point-in-time higher-timeframe context."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return con.execute(
            "SELECT timestamp, close FROM market_data "
            "WHERE symbol=? AND timeframe=? ORDER BY timestamp ASC",
            (symbol, timeframe)).fetchall()
    finally:
        con.close()


def db_observations(db_path: Path, symbol: str, timeframe: str,
                    skip: int = 0, htf_timeframe: str = ""
                    ) -> Iterator[Dict[str, Any]]:
    """Replay market_data.db rows read-only as raw observations.

    timeframe must be filtered — the table holds M15+H1 rows for the same
    symbol; sorting all of them by timestamp interleaves cadences and
    silently corrupts return/volatility features at every seam.
    ``skip`` drops the first N matching bars so parallel runs can cover
    disjoint historical windows.

    ``htf_timeframe`` (e.g. "H1") attaches point-in-time higher-timeframe
    context to each obs: htf_close, htf_rsi14, htf_trend (return over the
    last 10 completed higher-TF bars). Only bars CLOSED at or before the
    current timestamp are used — no lookahead.
    """
    htf = _load_htf_bars(db_path, symbol, htf_timeframe) \
        if htf_timeframe else []
    htf_idx = 0          # next htf bar not yet released
    htf_closes: List[float] = []  # released closes, in order

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        for ts, o, h, l, c, v in con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp ASC",
            (symbol, timeframe),
        ):
            if skip > 0:
                skip -= 1
                continue
            obs = {"symbol": symbol, "timestamp": ts, "open": o, "high": h,
                   "low": l, "close": c, "volume": v, "price": c}
            while htf_idx < len(htf) and htf[htf_idx][0] <= ts:
                htf_closes.append(htf[htf_idx][1])
                htf_idx += 1
            if htf_closes:
                obs["htf_close"] = htf_closes[-1]
                obs["htf_bars"] = len(htf_closes)
                if len(htf_closes) > 10:
                    obs["htf_trend"] = (
                        (htf_closes[-1] - htf_closes[-11])
                        / htf_closes[-11])
                if len(htf_closes) > 14:
                    ds = [htf_closes[i] - htf_closes[i - 1]
                          for i in range(len(htf_closes) - 14,
                                         len(htf_closes))]
                    gains = sum(d for d in ds if d > 0)
                    losses = -sum(d for d in ds if d < 0)
                    obs["htf_rsi14"] = (
                        100.0 - 100.0 / (1.0 + gains / losses)
                        if losses > 0 else 100.0)
            yield obs
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
    target = state_dir / "snapshot.json"
    for _ in range(3):
        try:
            tmp.replace(target)
            return
        except OSError:
            # Windows AV/indexer/readers can hold the target briefly.
            time.sleep(0.2)
    # Last resort: overwrite in place (loses atomicity, keeps the run).
    target.write_text(tmp.read_text(encoding="utf-8"), encoding="utf-8")
    tmp.unlink(missing_ok=True)


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

    if args.strategy_id:
        # Register before start so the first enriched cycle already sees
        # strategy_signals; the registry is otherwise empty and the
        # strategy_id config string would resolve to [] forever.
        from trading_bot.strategies.adapter import build_builtin_strategy
        _builtin_strategy = build_builtin_strategy(args.strategy_id)
    else:
        _builtin_strategy = None

    runtime = ModularMonolithRuntime({
        "execution_mode": "paper",
        "symbol": args.symbol,
        "account_id": "paper",
        "trading_state_path": str(state_dir / "trading_state.db"),
        "decision_log_path": str(state_dir / "decision_log.jsonl"),
        # Live-dims world model (FX=64 / latent 256); load is advisory-only —
        # a dim mismatch warns and falls back to scaffold weights, never dies.
        "world_model_checkpoint": str(PROJECT_ROOT / "var" / "world_model_v2.pt"),
        "strategy_id": args.strategy_id,
        "cognitive_assembly": {
            "enabled": True,
            "research_interval": args.research_interval,
            "discover_advisors": args.discover_advisors,
        },
    })
    await runtime.start()
    if _builtin_strategy is not None:
        runtime.bot.register_strategy_adapter(_builtin_strategy)
        logger.info("strategy_signals fed by %s", args.strategy_id)
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
    csc = getattr(runtime.bot, "csc", None)
    if csc is not None:
        # Position closes must hit the ledger, not just CSC bookkeeping —
        # wire the canonical execution service so horizon/adverse/reversal
        # exits submit real opposing orders.
        csc.configure_execution_service(runtime.bot.execution_service)
        # Swarm knowledge base persists beside the run state — learned
        # node skill and patterns survive restarts.
        csc.configure_swarm_state(
            str(Path(args.state_dir) / "swarm_kb.json"))
        # Self-wiring inventory likewise — measured node states persist.
        csc.configure_self_wiring_state(
            str(Path(args.state_dir) / "self_wiring.json"))
        # Session-gate self-validation: the bot must verify its own
        # safety chain before the first real observation — the probe
        # can never dispatch an order. Fails closed unless --no-preflight.
        if not getattr(args, "no_preflight", False):
            try:
                report = await csc.preflight_self_check()
            except Exception as exc:  # noqa: BLE001
                report = {"all_passed": False,
                          "blocking": [f"preflight_error:{exc}"]}
            if not report.get("all_passed"):
                logger.error(
                    "preflight self-check FAILED: %s — refusing to run",
                    report.get("blocking"))
                return 2
            logger.info("preflight self-check passed (%d checks)",
                        len(report.get("checks", [])))
    if args.decision_stride > 1 and csc is not None:
        csc._decision_stride = args.decision_stride
        logger.info("decision_stride=%d applied to CSC (cadenced decisions)",
                    args.decision_stride)
    if history:
        if csc is not None:
            csc.seed_observation_history(args.symbol, history)
            # Advisory services keep internal bar windows — replay the same
            # closes through them so they emit from cycle 1 instead of
            # reporting 'warming' for 50-70 live cycles.
            if hasattr(csc, "seed_advisory_history"):
                try:
                    await csc.seed_advisory_history([
                        {"symbol": args.symbol, "close": float(c),
                         "price": float(c), "volume": 0.0}
                        for c in history if isinstance(c, (int, float))])
                except Exception:  # noqa: BLE001
                    pass
        runtime.bot._price_window.extend(
            float(c) for c in history if isinstance(c, (int, float)))
        logger.info("seeded %d historical closes into feature windows",
                    len(history))
        # Restore open positions from the prior session — without this a
        # restart orphans persisted fills: ledger holds exposure the CSC
        # forgot, so it never settles and never scores those predictions.
        pos_state_path = state_dir / "open_positions.json"
        if pos_state_path.exists():
            try:
                n = csc.import_open_positions(json.loads(
                    pos_state_path.read_text(encoding="utf-8")))
                if n:
                    logger.info("restored %d open positions", n)
            except Exception as exc:
                logger.warning("open-position restore failed: %s", exc)

    # Honest fill costs: paper fills at raw bar price would overstate every
    # edge the outcome scorer learns from. Defaults are the measured
    # MetaQuotes-Demo EURUSD figures (spread ~2bps, slip ~1.25bps from the
    # real fill on 2026-10-07); commission 0 matches that venue.
    adapter = getattr(
        getattr(runtime.bot, "execution_service", None), "adapter", None)
    for attr, val in (("spread_bps", args.spread_bps),
                      ("slippage_bps", args.slippage_bps),
                      ("commission_per_unit", args.commission),
                      ("market_data_source", args.source)):
        if adapter is not None and hasattr(adapter, attr):
            setattr(adapter, attr, val)
    if adapter is not None:
        logger.info("paper cost model: spread=%.2fbps slip=%.2fbps comm=%.4f",
                    args.spread_bps, args.slippage_bps, args.commission)

    from trading_bot.execution.paper_feedback import PaperSettlementFeedback
    feedback = PaperSettlementFeedback(
        runtime.bot.execution_service.repository, csc) if csc is not None else None
    feedback_status = {}

    async def sync_economic_feedback():
        if feedback is None:
            return {}
        try:
            return await feedback.sync()
        except Exception as exc:
            # Missing or conflicting receipts must never become positive
            # reward; retain the durable fills for investigation/replay.
            logger.error("paper settlement feedback unavailable: %s", exc)
            return {"status": "unavailable", "reason": str(exc)}

    feedback_status = await sync_economic_feedback()

    if args.dashboard_port:
        serve_dashboard(state_dir, args.dashboard_port)

    if args.source == "db":
        source = db_observations(PROJECT_ROOT / "market_data.db",
                                 args.symbol, args.timeframe, args.skip,
                                 args.htf_timeframe)
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
            feedback_status = await sync_economic_feedback()
            publish_snapshot(state_dir, {
                "as_of": time.time(),
                "cycles": processed,
                "control": console.control_state(),
                "mode": "paper",
                # Data provenance: 'paper' mode alone is ambiguous —
                # synthetic bars and real market_data.db replay produce
                # identical-looking snapshots without the source label.
                "data_source": args.source,
                "economic_rewards": feedback_status,
                "data_timeframe": args.timeframe if args.source == "db"
                else None,
                "symbol": args.symbol,
                # Read-only advisory standing — which advisors contribute
                # and their measured weight/precision per regime.
                "advisors": csc.advisory_report() if csc is not None
                and hasattr(csc, "advisory_report") else None,
                # Ordered stage-funnel counts — where each observation's
                # decision terminated (verification veto, net-cost,
                # governance, consensus) or abstained.
                "funnel": csc.funnel_report() if csc is not None
                and hasattr(csc, "funnel_report") else None,
                # Read-only AI-stack planes (state/evidence/selection)
                # — one-line summaries per DOCS/CANONICAL_RUNTIME_DATAFLOW §4.
                "ai_stack": runtime.ai_stack.explain()
                if getattr(runtime, "ai_stack", None) is not None else None,
            })
            if args.cycles and processed >= args.cycles:
                break
            if args.interval > 0:
                await asyncio.sleep(args.interval)
    finally:
        # Settle every open position at last marks and persist the
        # remainder — kills are instant, so anything still open here
        # would otherwise vanish from CSC bookkeeping while its fills
        # stay in the ledger (orphan exposure).
        if csc is not None:
            try:
                marks = {s: p for s, p in console.last_price.items()
                         if isinstance(p, (int, float)) and p > 0}
                realized = await csc.close_all_positions(marks)
                if realized:
                    logger.info("end-of-run forecast flush settled: %s",
                                list(realized))
                tmp = (state_dir / "open_positions.json")
                tmp.write_text(json.dumps(
                    csc.export_open_positions(), default=str),
                    encoding="utf-8")
            except Exception as exc:
                logger.warning("position flush/persist failed: %s", exc)
        await sync_economic_feedback()
        await runtime.stop()
    logger.info("runner finished: %d cycles processed", processed)
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("synthetic", "db"),
                        default="synthetic")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="M15",
                        help="db source only: market_data.db holds M15+H1; "
                             "unfiltered replay interleaves cadences")
    parser.add_argument("--skip", type=int, default=0,
                        help="db source only: drop the first N bars of the "
                             "filtered timeframe (segments parallel runs)")
    parser.add_argument("--htf-timeframe", default="",
                        help="db source only: attach point-in-time higher-"
                             "timeframe context (htf_close/htf_trend/htf_rsi14) "
                             "from this timeframe's closed bars — e.g. H1")
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--spread-bps", type=float, default=2.0)
    parser.add_argument("--slippage-bps", type=float, default=1.25)
    parser.add_argument("--commission", type=float, default=0.0)
    parser.add_argument("--interval", type=float, default=0.0,
                        help="seconds between cycles (0 = as fast as possible)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--dashboard-port", type=int, default=0,
                        help="serve the read-only snapshot on 127.0.0.1:PORT")
    parser.add_argument("--research-interval", type=int, default=100,
                        help="observations between automatic research "
                             "cycles (0 disables cycles; the engine "
                             "still ingests forward outcomes)")
    parser.add_argument("--decision-stride", type=int, default=1,
                        help="CSC decides every Nth observation "
                             "(replicated-OOS evidence supports 4+)")
    parser.add_argument("--discover-advisors", action="store_true",
                        help="auto-scan quarantined AI packages for "
                             "observation-callable analyzers and attach "
                             "them as advisory services (probe-gated, "
                             "timeout-bounded; default off)")
    parser.add_argument("--no-preflight", action="store_true",
                        help="skip the session-gate self-check (default: "
                             "runner fails closed on preflight failure)")
    parser.add_argument("--strategy-id", default=None,
                        help="optional registered strategy capability id")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
