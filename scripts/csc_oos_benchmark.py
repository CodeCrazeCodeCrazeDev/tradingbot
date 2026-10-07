#!/usr/bin/env python
"""CSC out-of-sample benchmark — the first honest "is the brain better than
a frozen baseline" report.

Protocol:
  1. Chronological 70/30 split of market_data.db EURUSD bars.
  2. TEST split only: replay the CognitiveSystemController one observation
     at a time. All features are computed from strictly-prior bars —
     rolling volatility, MA trend, RSI — no lookahead anywhere.
  3. Approved directional decisions become positions (hold preserves);
     ABSTAIN keeps the prior position. Bar returns are close-to-close.
  4. compare_candidate_vs_baseline against frozen baselines:
       * always_long     — the naive buy-and-hold control
       * momentum_k      — frozen sign(close - MA_k) at fixed lookback
  5. Report verdicts to stdout and scripts/../var/reports/csc_oos_report.json.

The expected result on ~300 OOS bars of a single pair is honest: usually
"insufficient_evidence" or "not_superior". That IS the correct output —
the gate exists so the system can say it has no edge, not to manufacture one.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_bars(db_path: Path, symbol: str, timeframe: str = "M15"):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp ASC",
            (symbol, timeframe)).fetchall()
    finally:
        con.close()
    return rows


def rsi(closes, period=14):
    """Causal RSI from strictly-prior closes."""
    if len(closes) < period + 1:
        return 50.0
    diffs = np.diff(closes[-(period + 1):])
    gains = np.where(diffs > 0, diffs, 0.0).mean()
    losses = np.where(diffs < 0, -diffs, 0.0).mean()
    if losses == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + gains / losses)


def causal_observation(row, closes_history, symbol):
    """Build an observation dict whose every feature uses only past data."""
    ts, o, h, l, c, v = row
    obs = {"symbol": symbol, "timestamp": ts, "open": o, "high": h,
           "low": l, "close": c, "price": c, "volume": v}
    if len(closes_history) >= 20:
        rets = np.diff(closes_history[-21:]) / np.asarray(
            closes_history[-21:-1])
        obs["volatility"] = float(np.std(rets))
        ma20 = float(np.mean(closes_history[-20:]))
        # MarketState vocabulary: BULLISH/BEARISH/NEUTRAL.
        obs["trend"] = ("BULLISH" if c > ma20 * 1.0005 else
                        "BEARISH" if c < ma20 * 0.9995 else "NEUTRAL")
    obs["rsi"] = rsi(closes_history)
    return obs


def action_to_position(outcome_name: str, action: str, prev: float) -> float:
    if outcome_name == "TRADE_APPROVED":
        if action == "BUY":
            return 1.0
        if action == "SELL":
            return -1.0
    return prev  # abstain/hold preserves position


async def replay(csc, obs_iter, symbol: str):
    """Drive the CSC over the OOS bars; collect positions + journal."""
    pos = 0.0
    positions, decisions = [], []
    for obs in obs_iter:
        try:
            decision = await csc.process_market_observation(obs)
        except Exception as exc:
            print(f"cycle error @{obs.get('timestamp')}: {exc}",
                  file=sys.stderr)
            decision = None
        outcome = getattr(decision, "outcome", None)
        outcome_name = getattr(outcome, "name", str(outcome))
        action = None
        if decision is not None:
            pending = getattr(csc, "_pending_predictions", {}).get(
                getattr(decision, "trade_id", ""), {})
            action = pending.get("action")
        pos = action_to_position(outcome_name, action or "", pos)
        positions.append(pos)
        decisions.append({
            "ts": obs.get("timestamp"), "outcome": outcome_name,
            "action": action, "position": pos,
        })
    return positions, decisions


async def main_async(args) -> int:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.evaluation.frozen_baseline import (
        compare_candidate_vs_baseline)

    rows = load_bars(PROJECT_ROOT / "market_data.db", args.symbol,
                     args.timeframe)
    n_total = len(rows)
    cut = int(n_total * args.train_frac)
    test_rows = rows[cut:]
    if args.max_bars:
        test_rows = test_rows[:args.max_bars]
    if args.stride > 1:
        # Lower-frequency variant: decide every Nth bar, hold across the
        # skipped ones. Bar returns become N-bar returns — turnover falls,
        # gross edge per decision stays honest.
        test_rows = test_rows[::args.stride]
    closes_hist = [float(r[4]) for r in rows[:cut]]
    print(f"{n_total} bars | train {cut} (context only) | OOS {len(test_rows)}")

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(
        position_horizon=args.position_horizon)

    # The benchmark is evaluation, not execution — but TRADE_EXECUTION
    # fails closed without exactly one executor, so approved decisions
    # would be falsely recorded as rejections. A stub subscriber lets the
    # evaluator see what the CSC actually decided.
    from trading_bot.core.unified_event_bus import (
        ActionStatus, decision_bus)
    await decision_bus.start()

    async def _bench_executor(action):
        action.status = ActionStatus.EXECUTED
        return {"status": "filled"}
    decision_bus.subscribe("TRADE_EXECUTION", _bench_executor,
                           subscriber_id="oos_bench_executor")

    def obs_iter():
        hist = list(closes_hist)
        for row in test_rows:
            obs = causal_observation(row, hist, args.symbol)
            obs["cost_bps"] = args.controller_cost_bps
            hist.append(float(row[4]))
            yield obs

    t0 = time.time()
    positions, decisions = await replay(csc, obs_iter(), args.symbol)
    # End-of-stream accounting: flush any open position at the final mark so
    # every approved decision has a realized outcome.
    await csc.close_all_positions({args.symbol: float(test_rows[-1][4])})
    try:
        await decision_bus.stop()
    except Exception:
        pass
    elapsed = time.time() - t0
    journal = csc.get_decision_journal()

    # Bar returns for the OOS segment (close-to-close, strictly real).
    test_closes = [float(r[4]) for r in test_rows]
    rets = [test_closes[i] / test_closes[i - 1] - 1.0
            for i in range(1, len(test_closes))]
    csc_pos = positions[1:]            # position taken at bar i earns ret[i]
    ma_k = args.momentum_lookback
    momentum_pos = []
    hist_full = [float(r[4]) for r in rows[:cut]]
    for r in test_rows:
        hist_full.append(float(r[4]))
        window = hist_full[-(ma_k + 1):]
        ma = float(np.mean(window[:-1]))
        momentum_pos.append(1.0 if window[-1] >= ma else -1.0)
    momentum_pos = momentum_pos[1:]

    settled = sum(
        m.get("total_predictions", 0)
        for regimes in journal.get("reliability", {}).values()
        for m in regimes.values())
    report = {
        "symbol": args.symbol,
        "oos_bars": len(test_rows),
        "elapsed_s": round(elapsed, 1),
        "settled_outcomes": settled,
        "pending_unsettled": len(journal.get("pending_predictions", {})),
        "reliability": journal.get("reliability", {}),
        "comparisons": {},
    }
    from collections import Counter
    report["outcomes"] = dict(Counter(d["outcome"] for d in decisions))
    report["comparisons"]["vs_always_long"] = compare_candidate_vs_baseline(
        csc_pos, [1.0] * len(rets), rets,
        cost_bps=args.cost_bps, min_decisions=args.min_decisions)
    report["comparisons"]["vs_frozen_momentum"] = compare_candidate_vs_baseline(
        csc_pos, momentum_pos, rets,
        cost_bps=args.cost_bps, min_decisions=args.min_decisions)

    out_dir = PROJECT_ROOT / "var" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "csc_oos_report.json"
    out_path.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({k: report[k] for k in
                      ("oos_bars", "outcomes", "comparisons")},
                     indent=2, default=str))
    print(f"\nreport -> {out_path}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--timeframe", default="M15")
    p.add_argument("--train-frac", type=float, default=0.7)
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--controller-cost-bps", type=float, default=5.0,
                   help="cost assumption the CSC's net-of-cost gate sees "
                        "(independent of the comparator's scoring cost)")
    p.add_argument("--min-decisions", type=int, default=20)
    p.add_argument("--momentum-lookback", type=int, default=10)
    p.add_argument("--stride", type=int, default=1,
                   help="evaluate every Nth OOS bar (lower-frequency variant)")
    p.add_argument("--position-horizon", type=int, default=8,
                   help="max bars a position is held before settlement")
    p.add_argument("--max-bars", type=int, default=0,
                   help="cap OOS bars for a quick smoke run (0 = all)")
    args = p.parse_args(argv)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
