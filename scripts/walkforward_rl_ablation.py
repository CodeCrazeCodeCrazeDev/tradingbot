#!/usr/bin/env python
"""Chronological walk-forward ablation: does the RL advisor cohort add
measured value?

Three arms over disjoint OOS windows of real bars:
  A. momentum          — frozen sign(close - MA) baseline, no CSC.
  B. csc_no_rl         — CognitiveSystemController, RL factories
                         excluded via TB_DISABLED_ADVISORS.
  C. csc_with_rl       — full measured advisory set (RL included).

Honesty constraints (same as csc_oos_benchmark):
  * Chronological splits only — every feature derives from prior bars.
  * Fresh CSC singleton per (arm, window) — no cross-window state leak.
  * Round-trip cost model: spread + slippage + commission per unit of
    position turnover (see --cost-bps). Simulated fills omit queue
    position, partial fills and latency effects; results are an upper
    bound on live performance (cf. paper-trading limitations).
  * Uncertainty: per-window net deltas, paired across arms; report
    mean +/- standard error — no point estimates presented as proof.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RL_ADVISORS = (
    "rl_adaptive_decision", "rl_adaptive_spread", "rl_analysis_lens",
    "rl_alpha_search", "mm_adaptive_spread", "rl_adaptive_objectives",
    "rl_distributional",
)


def load_bars(db_path: Path, symbol: str, timeframe: str = "M15"):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp ASC", (symbol, timeframe)).fetchall()
    finally:
        con.close()


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    diffs = np.diff(closes[-(period + 1):])
    gains = np.where(diffs > 0, diffs, 0.0).mean()
    losses = np.where(diffs < 0, -diffs, 0.0).mean()
    return 100.0 if losses == 0 else 100.0 - 100.0 / (1.0 + gains / losses)


def causal_observation(row, closes_history, symbol, cost_bps):
    ts, o, h, l, c, v = row
    obs = {"symbol": symbol, "timestamp": ts, "open": o, "high": h,
           "low": l, "close": c, "price": c, "volume": v,
           "cost_bps": cost_bps}
    if len(closes_history) >= 20:
        rets = np.diff(closes_history[-21:]) / np.asarray(
            closes_history[-21:-1])
        obs["volatility"] = float(np.std(rets))
        ma20 = float(np.mean(closes_history[-20:]))
        obs["trend"] = ("BULLISH" if c > ma20 * 1.0005 else
                        "BEARISH" if c < ma20 * 0.9995 else "NEUTRAL")
    obs["rsi"] = rsi(closes_history)
    return obs


def momentum_positions(rows, context_end, end, lookback):
    hist = [float(r[4]) for r in rows[:context_end]]
    out = []
    for r in rows[context_end:end]:
        hist.append(float(r[4]))
        w = hist[-(lookback + 1):]
        out.append(1.0 if w[-1] >= float(np.mean(w[:-1])) else -1.0)
    return out[1:]


async def replay_csc(rows, context_end, test_rows, args, disable_rl):
    """Replay one window; returns the position series (len == bars-1)."""
    if disable_rl:
        os.environ["TB_DISABLED_ADVISORS"] = ",".join(RL_ADVISORS)
    else:
        os.environ.pop("TB_DISABLED_ADVISORS", None)

    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.core.csc.assembly import build_cognitive_system
    from trading_bot.core.unified_event_bus import (
        ActionStatus, UnifiedDecisionBus, decision_bus)

    UnifiedDecisionBus.reset()
    bus = UnifiedDecisionBus()
    bus._log_path = None

    async def _exec_stub(action):
        action.status = ActionStatus.EXECUTED
        return {"status": "filled"}
    bus.subscribe("TRADE_EXECUTION", _exec_stub,
                  subscriber_id="wf_ablation")
    await bus.start()

    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(
        position_horizon=args.position_horizon,
        decision_stride=args.stride)
    build_cognitive_system(csc, advisory_brain=True,
                           discover_advisors=False)

    hist = [float(r[4]) for r in rows[:context_end]]
    pos = 0.0
    positions = []
    for row in test_rows:
        obs = causal_observation(row, hist, args.symbol,
                                 args.controller_cost_bps)
        hist.append(float(row[4]))
        try:
            decision = await asyncio.wait_for(
                csc.process_market_observation(obs), timeout=30.0)
        except Exception as exc:
            print(f"  cycle error @{obs['timestamp']}: {exc}",
                  file=sys.stderr)
            decision = None
        outcome = getattr(decision, "outcome", None)
        oname = getattr(outcome, "name", str(outcome))
        action = None
        if decision is not None:
            pend = getattr(csc, "_pending_predictions", {}).get(
                getattr(decision, "trade_id", ""), {})
            action = pend.get("action")
        if oname == "TRADE_APPROVED" and action == "BUY":
            pos = 1.0
        elif oname == "TRADE_APPROVED" and action == "SELL":
            pos = -1.0
        positions.append(pos)
    try:
        await csc.close_all_positions(
            {args.symbol: float(test_rows[-1][4])})
        await bus.stop()
    except Exception:
        pass
    UnifiedDecisionBus.reset()
    return positions[1:]


def apply_exec_lag(positions, lag):
    """Decision->fill latency: replay fills at decision-bar close; a
    real order fills later. Shifting the position series by `lag`
    bars is the honest model — you get the move from fill, not
    decision."""
    if lag <= 0:
        return list(positions)
    return list(positions[:1]) * lag + list(positions[:-lag])


def exit_efficiency(positions, rets, horizon=8):
    """Score exit timing: for each closed position run, fraction of
    the max attainable forward move actually captured. 1.0 = perfect
    exits; negative = exits cost more than they saved."""
    pos = list(positions)
    r = list(rets)
    effs = []
    i = 0
    n = len(pos)
    while i < n:
        if pos[i] == 0:
            i += 1
            continue
        j = i
        while j < n and pos[j] == pos[i]:
            j += 1
        side = pos[i]
        realized = sum(r[k] * side for k in range(i + 1, min(j + 1, len(r))))
        # best attainable over next `horizon` bars from exit bar
        future = [sum(r[k] * side for k in range(j + 1, min(j + 1 + h, len(r))))
                  for h in range(1, horizon + 1) if j + 1 + h <= len(r)]
        best = max(future) if future else realized
        denom = abs(best) if abs(best) > 1e-9 else 1e-9
        effs.append(realized / denom)
        i = j
    return float(np.mean(effs)) if effs else 0.0


def score(positions, rets, cost_bps):
    """Net/gross/dd/turnover/Sharpe — mirrors score_side semantics."""
    pos = np.asarray(positions, dtype=float)
    r = np.asarray(rets, dtype=float)
    gross = pos * r
    turn = np.abs(np.diff(np.concatenate([[0.0], pos])))
    costs = turn * cost_bps / 1e4
    net = gross - costs
    eq = np.cumsum(net)
    peak = np.maximum.accumulate(np.maximum(eq, 0.0))
    dd = float(np.max(peak - eq)) if len(eq) else 0.0
    sd = float(np.std(net))
    sharpe = float(np.mean(net) / sd * math.sqrt(len(net))) \
        if sd > 0 else 0.0
    return {
        "total_gross": float(np.sum(gross)),
        "total_net": float(np.sum(net)),
        "cost_paid": float(np.sum(costs)),
        "turnover": float(np.sum(turn)),
        "max_drawdown": dd,
        "win_rate": float(np.mean(net > 0)) if len(net) else 0.0,
        "sharpe_like": sharpe,
        "n_bars": int(len(net)),
    }


async def main_async(args):
    rows = load_bars(PROJECT_ROOT / "market_data.db", args.symbol,
                     args.timeframe)
    # Data cutoff: pin the eval horizon — a live feed keeps appending
    # rows, and two runs on different days must not see different data.
    if args.data_cutoff:
        rows = [r for r in rows if str(r[0]) <= args.data_cutoff]
    n = len(rows)
    if args.spread_windows:
        # Regime-stratified windows across the whole series instead of
        # a contiguous tail — contiguous windows all sample the same
        # vol regime and don't generalize.
        stride = n // (args.windows + 1)
        starts = [stride * (w + 1) - args.window_bars // 2
                  for w in range(args.windows)]
    else:
        span = min(n // 5, args.windows * args.window_bars)
        pool_start = n - span
        starts = [pool_start + w * (span // args.windows)
                  for w in range(args.windows)]

    rets_by_window, arms = [], {"momentum": [], "csc_no_rl": [],
                                "csc_with_rl": []}
    for w in range(args.windows):
        # Purged embargo: skip embargo_bars between context and the test
        # window so serial correlation cannot leak regime information
        # across the boundary.
        start = max(0, starts[w]) + args.embargo_bars
        if args.spread_windows:
            end = min(start + args.window_bars,
                      starts[w + 1] if w + 1 < len(starts) else n)
        else:
            span = min(n // 5, args.windows * args.window_bars)
            pool_start = n - span
            end = min(start + args.window_bars,
                      pool_start + (w + 1) * (span // args.windows))
        test_rows = rows[start:end]
        rets = [float(test_rows[i][4]) / float(test_rows[i - 1][4]) - 1.0
                for i in range(1, len(test_rows))]
        rets_by_window.append(rets)
        label = (f"window {w} {rows[start][0][:10]}.."
                 f"{rows[end-1][0][:10]} ({len(test_rows)} bars)")
        print(f"== {label}")

        t0 = time.time()
        mp = momentum_positions(rows, start, end,
                                args.momentum_lookback)
        mp = apply_exec_lag(mp, args.exec_lag_bars)
        s = score(mp, rets, args.cost_bps)
        s["exit_efficiency"] = exit_efficiency(mp, rets)
        arms["momentum"].append(s)
        print(f"   momentum    net={arms['momentum'][-1]['total_net']:+.6f} "
              f"[{time.time()-t0:.0f}s]")

        t0 = time.time()
        p = await replay_csc(rows, start, test_rows, args,
                             disable_rl=True)
        p = apply_exec_lag(p, args.exec_lag_bars)
        s = score(p, rets, args.cost_bps)
        s["exit_efficiency"] = exit_efficiency(p, rets)
        arms["csc_no_rl"].append(s)
        print(f"   csc_no_rl   net={arms['csc_no_rl'][-1]['total_net']:+.6f} "
              f"[{time.time()-t0:.0f}s]")

        t0 = time.time()
        p = await replay_csc(rows, start, test_rows, args,
                             disable_rl=False)
        p = apply_exec_lag(p, args.exec_lag_bars)
        s = score(p, rets, args.cost_bps)
        s["exit_efficiency"] = exit_efficiency(p, rets)
        arms["csc_with_rl"].append(s)
        print(f"   csc_with_rl net={arms['csc_with_rl'][-1]['total_net']:+.6f} "
              f"[{time.time()-t0:.0f}s]")

    # Uncertainty: paired per-window deltas, mean ± SE.
    def paired(a, b):
        d = [x["total_net"] - y["total_net"]
             for x, y in zip(a, b)]
        m = float(np.mean(d))
        se = float(np.std(d) / math.sqrt(len(d))) if len(d) > 1 else 0.0
        return {"delta_mean": m, "delta_se": se,
                "per_window": d, "wins": sum(1 for x in d if x > 0)}

    report = {
        "symbol": args.symbol, "timeframe": args.timeframe,
        "cost_bps_round_trip_equiv": args.cost_bps,
        "windows": args.windows, "window_bars": args.window_bars,
        "cost_model_note": (
            "Per-unit-turnover bps charge covering spread+slippage+"
            "commission. Simulated fills omit queue position, partials "
            "and latency — treat as upper bound on live."),
        "arms": arms,
        "paired_deltas": {
            "csc_with_rl - momentum":
                paired(arms["csc_with_rl"], arms["momentum"]),
            "csc_no_rl - momentum":
                paired(arms["csc_no_rl"], arms["momentum"]),
            "csc_with_rl - csc_no_rl":
                paired(arms["csc_with_rl"], arms["csc_no_rl"]),
        },
    }
    out = PROJECT_ROOT / "var" / "reports" / "walkforward_rl_ablation.json"
    out.write_text(json.dumps(report, indent=2, default=str))

    print("\n=== paired deltas (mean ± SE, per-window) ===")
    for k, v in report["paired_deltas"].items():
        print(f"  {k:28s} {v['delta_mean']:+.6f} ± {v['delta_se']:.6f} "
              f"wins={v['wins']}/{len(v['per_window'])}")
    print(f"wrote {out}")
    return 0


def main():
    # Run-scoped RL checkpoints: the with-RL arm must learn within a
    # run (chronological transfer across windows is legitimate) but
    # must NOT inherit Q from previous invocations — otherwise two
    # runs of the same script produce different results.
    os.environ.setdefault(
        "TB_RL_STATE_DIR",
        str(PROJECT_ROOT / "var" / "rl_ablation_state"))
    import shutil
    shutil.rmtree(os.environ["TB_RL_STATE_DIR"], ignore_errors=True)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--timeframe", default="M15")
    p.add_argument("--windows", type=int, default=3)
    p.add_argument("--window-bars", type=int, default=800)
    p.add_argument("--cost-bps", type=float, default=5.0,
                   help="round-trip-equivalent cost per unit turnover")
    p.add_argument("--controller-cost-bps", type=float, default=5.0)
    p.add_argument("--momentum-lookback", type=int, default=10)
    p.add_argument("--data-cutoff", default="",
                   help="ISO timestamp; bars after this are excluded "
                        "(pins eval against a growing feed)")
    p.add_argument("--spread-windows", action="store_true",
                   help="regime-stratified windows across the series "
                        "instead of a contiguous tail")
    p.add_argument("--embargo-bars", type=int, default=20,
                   help="purged gap between context end and window start")
    p.add_argument("--exec-lag-bars", type=int, default=1,
                   help="bars between decision and modeled fill")
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--position-horizon", type=int, default=8)
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
