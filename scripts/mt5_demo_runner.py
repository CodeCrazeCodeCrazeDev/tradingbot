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


def _bar_to_obs(symbol: str, bar: Any, adapter: Any,
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    names = getattr(getattr(bar, "dtype", None), "names", ()) or ()
    ts = int(bar["time"]) if "time" in names else 0
    volume = float(bar["tick_volume"]) if "tick_volume" in names else 0.0
    obs = {
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
    if extra:
        obs.update(extra)
    return obs


def _closed_bars(client: Any, symbol: str, timeframe_const: int, n: int):
    """Closed bars only — position 0 is the still-forming bar."""
    return client.copy_rates_from_pos(symbol, timeframe_const, 1, n)


def _quote_extra(client: Any, symbol: str) -> Dict[str, Any]:
    """Live bid/ask for a freshly-closed bar — point-in-time correct in
    follow mode only. Never attach to historical replay bars."""
    tick = client.symbol_info_tick(symbol)
    if tick is None:
        return {}
    bid, ask = float(tick.bid), float(tick.ask)
    mid = (bid + ask) / 2.0
    return {"bid": bid, "ask": ask,
            "spread_bps": (ask - bid) / mid * 1e4 if mid else None,
            "quote_time": int(getattr(tick, "time", 0))}


def _peer_extra(peer_closes: "deque") -> Dict[str, Any]:
    """Latest closed peer-symbol context: close + returns over 1/10 bars.

    peer_closes is appended with only bars whose timestamp <= the current
    obs bar — no lookahead."""
    if len(peer_closes) < 2:
        return {}
    out = {"peer_close": peer_closes[-1]}
    out["peer_return_1"] = (peer_closes[-1] - peer_closes[-2]) \
        / peer_closes[-2] if peer_closes[-2] else None
    if len(peer_closes) > 10:
        out["peer_return_10"] = (peer_closes[-1] - peer_closes[-11]) \
            / peer_closes[-11] if peer_closes[-11] else None
    return out


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


async def _seed_warmup(runtime: Any, symbol: str, bars: Any) -> int:
    """Seed derived-feature windows from closed bars without decision cycles."""
    bar_list = list(bars) if bars is not None else []
    closes = [float(bar["close"]) for bar in bar_list
              if float(bar["close"]) > 0]
    csc = getattr(runtime.bot, "csc", None)
    if csc is not None and hasattr(csc, "seed_observation_history"):
        csc.seed_observation_history(symbol, closes)
    # Advisory services keep their own internal bar windows — replay the
    # same warmup bars through them so they emit from the first live
    # cycle instead of reporting 'warming' for 50-70 real cycles.
    if csc is not None and hasattr(csc, "seed_advisory_history"):
        def _vol(bar: Any) -> float:
            for key in ("tick_volume", "volume"):
                try:
                    return float(bar[key])
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
            return 0.0
        obs_list = [{
            "symbol": symbol,
            "timestamp": float(bar["time"]),
            "open": float(bar["open"]), "high": float(bar["high"]),
            "low": float(bar["low"]), "close": float(bar["close"]),
            "price": float(bar["close"]), "volume": _vol(bar),
        } for bar in bar_list]
        try:
            await csc.seed_advisory_history(obs_list)
        except Exception:  # noqa: BLE001
            pass
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
    l2_feed = None
    mt5_l2 = None
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

        peer_bars = []
        if args.peer_symbol:
            _pb = _closed_bars(
                client, args.peer_symbol, tf, (args.replay or 1500) + 60)
            peer_bars = list(_pb) if _pb is not None else []
            logger.info("peer symbol %s: %d closed bars loaded",
                        args.peer_symbol, len(peer_bars))
        from collections import deque as _deque
        peer_closes = _deque(maxlen=256)
        peer_idx = 0

        if args.replay:
            bars = _closed_bars(client, args.symbol, tf, args.replay)
            for bar in bars:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                extra: Dict[str, Any] = {}
                while (peer_idx < len(peer_bars)
                       and int(peer_bars[peer_idx]["time"])
                       <= int(bar["time"])):
                    peer_closes.append(float(peer_bars[peer_idx]["close"]))
                    peer_idx += 1
                if args.peer_symbol:
                    extra["peer_symbol"] = args.peer_symbol
                    extra.update(_peer_extra(peer_closes))
                obs = _bar_to_obs(args.symbol, bar, adapter, extra)
                tick_mark()
                await runtime.bot.run_cycle(obs)
                processed += 1
                publish_snapshot(state_dir, _snapshot(
                    processed, console, args, runtime, adapter))
        else:  # follow: poll for each newly closed M15 bar
            # Autonomous market selection: --symbols auto lets the bot
            # choose its trading set from real venue data. Scoring reads
            # real closed bars + live spread per candidate; the ranking
            # is re-run every selector.reselect_every polls and the set
            # rotates when the evidence moves.
            selector = None
            active = [args.symbol]
            if args.symbols == "auto":
                from trading_bot.foundation.market_selector import (
                    MarketSelector)
                selector = MarketSelector(
                    reselect_every=args.reselect_interval)

                def _score(sym: str) -> Dict[str, Any]:
                    cand = _closed_bars(client, sym, tf, 120)
                    tick = client.symbol_info_tick(sym)
                    sp = None
                    if tick is not None:
                        mid = (float(tick.bid) + float(tick.ask)) / 2.0
                        sp = ((float(tick.ask) - float(tick.bid)) / mid * 1e4
                              if mid else None)
                    from trading_bot.foundation.market_selector import (
                        score_symbol)
                    return score_symbol(cand, sp)

                active = selector.reselect(
                    _score, top_n=args.max_symbols)
                logger.info("autonomous market selection: %s", active)
            elif args.symbols:
                active = [s.strip().upper() for s in
                          args.symbols.split(",") if s.strip()]

            # cTrader Level-2 feed: real DOM snapshots -> order_book fields.
            l2_feed = None
            if args.ctrader_l2:
                from trading_bot.feeds.ctrader_l2 import CTraderL2Feed
                l2_feed = CTraderL2Feed()
                if not await l2_feed.start(active):
                    logger.warning("ctrader L2 unavailable - order-book "
                                   "adapters keep abstaining")
                    l2_feed = None

            # MT5-native L2 + tape: market_book depth -> order_book fields;
            # trade-flagged ticks -> order_flow. Free on the same terminal
            # connection the runner already owns.
            mt5_l2 = None
            if args.mt5_l2:
                from trading_bot.feeds.mt5_l2 import MT5L2Feed
                mt5_l2 = MT5L2Feed(client)
                book_syms = mt5_l2.start(active)
                if not book_syms:
                    logger.info("mt5 market book not published - lob "
                                "adapters keep abstaining")
                    mt5_l2 = None
                else:
                    logger.info("mt5 L2 feed live for %s", book_syms)

            last_bar_time: Dict[str, int] = {}
            for sym in active:
                # Seed only the causal feature windows. Warm-up must not
                # run decisions through the live demo execution path.
                warm = _closed_bars(client, sym, tf, args.warmup)
                if warm is not None and len(warm):
                    seeded = await _seed_warmup(runtime, sym, warm)
                    logger.info("follow warm-up %s: seeded %d closed bars",
                                sym, seeded)
                    last_bar_time[sym] = int(warm[-1]["time"])
            publish_snapshot(state_dir, _snapshot(
                processed, console, args, runtime, adapter))
            while not args.cycles or processed < args.cycles:
                for command in channel.drain():
                    outcome = await console.apply(command)
                    logger.info("operator command %s -> %s",
                                command.get("action"), outcome)
                tick_mark()
                if selector is not None and selector.needs_reselect():
                    active = selector.reselect(
                        _score, top_n=args.max_symbols)
                    if l2_feed is not None:
                        await l2_feed.stop()
                        l2_feed = CTraderL2Feed()
                        await l2_feed.start(active)
                    if mt5_l2 is not None:
                        mt5_l2.stop()
                        mt5_l2.start(active)
                    for sym in active:
                        last_bar_time.setdefault(sym, 0)
                for sym in active:
                    bars = _closed_bars(client, sym, tf, 1)
                    if (bars is None or not len(bars)
                            or int(bars[0]["time"])
                            == last_bar_time.get(sym)):
                        continue
                    last_bar_time[sym] = int(bars[0]["time"])
                    extra = _quote_extra(client, sym)
                    if l2_feed is not None:
                        extra.update(l2_feed.snapshot(sym))
                    if mt5_l2 is not None:
                        extra.update(mt5_l2.snapshot(sym))
                        extra.update(mt5_l2.tape(sym))
                    if args.peer_symbol:
                        fresh = _closed_bars(client, args.peer_symbol, tf, 60)
                        if fresh is not None and len(fresh):
                            peer_closes.clear()
                            for pb in fresh:
                                peer_closes.append(float(pb["close"]))
                        extra["peer_symbol"] = args.peer_symbol
                        extra.update(_peer_extra(peer_closes))
                    obs = _bar_to_obs(sym, bars[0], adapter, extra)
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
        if l2_feed is not None:
            await l2_feed.stop()
        if mt5_l2 is not None:
            mt5_l2.stop()
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
    parser.add_argument("--symbols", default="",
                        help="follow-mode symbol set: 'auto' lets the bot "
                             "choose from the venue universe scored on real "
                             "bars+spread; comma list fixes the set; empty "
                             "uses --symbol")
    parser.add_argument("--max-symbols", type=int, default=3,
                        help="auto-selection: how many top-scored symbols "
                             "to trade")
    parser.add_argument("--reselect-interval", type=int, default=60,
                        help="auto-selection: polls between re-scoring the "
                             "candidate universe")
    parser.add_argument("--ctrader-l2", action="store_true",
                        help="attach the cTrader Open API depth feed: real "
                             "Level-2 snapshots -> order_book/bids/asks/"
                             "imbalance fields in each observation (needs "
                             "CTRADER_CLIENT_ID/SECRET/ACCESS_TOKEN)")
    parser.add_argument("--mt5-l2", action="store_true",
                        help="subscribe the MT5 Market Book + trade-flagged "
                             "tick tape: real order_book + order_flow "
                             "fields (free on the same terminal feed)")
    parser.add_argument("--peer-symbol", default="",
                        help="attach peer-symbol closed-bar context "
                             "(peer_close/peer_return_1/peer_return_10) "
                             "aligned by timestamp — e.g. GBPUSD")
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
