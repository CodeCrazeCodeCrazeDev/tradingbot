"""Audited EURUSD baseline edge experiment.

Answers the question the whole session circled: is there a measurable,
cost-adjusted, out-of-sample edge in the data we have — or is the CSC's
abstention correct?

Method (fixed BEFORE evaluation, no tuning on eval data):
  - 3 falsifiable rules, declared below with entry/exit/eligibility
  - chronological split: 60% discovery / 40% evaluation, 20-bar embargo
  - entry at bar-close (signal time) — conservative, no intra-bar fill
  - net return = direction * fwd_return(horizon) - spread - commission
  - spread: flat bps estimate (+ per-bar Roll estimate when available)
  - uncertainty: circular block bootstrap (blocks=8 bars) on the eval
    window net returns -> 5% LCB on mean net bps
  - status emitted: insufficient_evidence / no_edge / candidate_edge

Statuses are honest: ABSTAIN history proves nothing about edge either
way — this measures the SIGNAL, not the pipeline's gate decisions.
"""

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_bars(db_path, symbol, timeframe):
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT timestamp, open, high, low, close, volume "
        "FROM market_data WHERE symbol=? AND timeframe=? "
        "ORDER BY timestamp", (symbol, timeframe)).fetchall()
    con.close()
    arr = np.array([[r[1], r[2], r[3], r[4], r[5] or 0.0]
                    for r in rows], dtype=float)
    ts = [r[0] for r in rows]
    return ts, arr


def roll_spread_bps(closes, window=30):
    """Roll (1984) effective-spread estimate from close covariance."""
    if len(closes) < window:
        return None
    c = np.asarray(closes[-window:], dtype=float)
    d = np.diff(np.log(c))
    cov = float(np.cov(d[:-1], d[1:])[0, 1])
    if cov >= 0 or not math.isfinite(cov):
        return None
    return 2.0 * math.sqrt(-cov) / float(np.mean(c)) * 1e4


# ----------------------------------------------------------------
# Fixed rules — declared before evaluation. Each returns +1/-1/0 at
# bar i (trade on close of bar i, exit at close of bar i+horizon).

def rule_pullback_long(closes, i):
    """Trend-pullback long: price above SMA50, last 3 bars pulled back
    (close[i] < close[i-3]), prior 10-bar trend positive."""
    if i < 60:
        return 0
    sma = np.mean(closes[i - 49:i + 1])
    trend = closes[i - 10] - closes[i - 20]
    pullback = closes[i] < closes[i - 3]
    return 1 if (closes[i] > sma and trend > 0 and pullback) else 0


def rule_momentum(closes, i):
    """Momentum continuation: 5-bar return > +0.15% -> follow long;
    < -0.15% -> follow short."""
    if i < 20:
        return 0
    r = (closes[i] - closes[i - 5]) / closes[i - 5]
    if r > 0.0015:
        return 1
    if r < -0.0015:
        return -1
    return 0


def rule_meanrev(closes, i):
    """Mean reversion: close > upper band (SMA20 + 2*sigma) -> short;
    < lower band -> long."""
    if i < 25:
        return 0
    w = closes[i - 19:i + 1]
    m, s = np.mean(w), np.std(w)
    if s <= 0:
        return 0
    if closes[i] > m + 2 * s:
        return -1
    if closes[i] < m - 2 * s:
        return 1
    return 0


RULES = {"pullback_long": rule_pullback_long,
         "momentum": rule_momentum,
         "meanrev": rule_meanrev}


def block_bootstrap_lcb(returns, block=8, n_boot=2000, seed=7):
    """5% lower confidence bound on the mean of autocorrelated returns
    via circular block bootstrap."""
    x = np.asarray(returns, dtype=float)
    n = len(x)
    if n < block:
        return float(np.mean(x)), float(np.mean(x))
    rng = np.random.RandomState(seed)
    nblocks = int(math.ceil(n / block))
    means = np.empty(n_boot)
    ext = np.concatenate([x, x[:block]])
    for b in range(n_boot):
        idx = rng.randint(0, n, size=nblocks)
        samp = np.concatenate(
            [ext[i:i + block] for i in idx])[:n]
        means[b] = np.mean(samp)
    return float(np.mean(x)), float(np.percentile(means, 5))


def evaluate(closes, rule_fn, horizon, eval_start, eval_end,
             cost_bps):
    """Signals on eval window only; returns net bps per trade."""
    sigs, net = [], []
    for i in range(eval_start, min(eval_end,
                                   len(closes) - horizon)):
        s = rule_fn(closes, i)
        if s == 0:
            continue
        fwd = (closes[i + horizon] - closes[i]) / closes[i] * 1e4
        sigs.append(i)
        net.append(s * fwd - cost_bps)
    return sigs, np.asarray(net)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default="lse_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--eval-frac", type=float, default=0.40)
    ap.add_argument("--cost-bps", type=float, default=None,
                    help="override; default = max(Roll estimate, 5bps)")
    ap.add_argument("--min-trades", type=int, default=30)
    ap.add_argument("--required-margin-bps", type=float, default=2.0,
                    help="LCB must clear this margin to be a candidate")
    args = ap.parse_args()

    ts, bars = load_bars(args.db_path, args.symbol, args.timeframe)
    closes = bars[:, 3]
    n = len(closes)
    print(f"loaded {n} {args.timeframe} bars {ts[0]} -> {ts[-1]}")

    # cost: Roll estimate over full window, floored at 5bps flat
    roll = roll_spread_bps(closes)
    cost_bps = args.cost_bps
    if cost_bps is None:
        cost_bps = max(roll or 0.0, 5.0)
    print(f"cost model: {cost_bps:.2f} bps/trade "
          f"(Roll estimate: {roll if roll else 'n/a'})")

    # chronological split with embargo — eval window untouched
    disc_end = int(n * (1.0 - args.eval_frac))
    eval_start = disc_end + args.embargo
    eval_end = n
    print(f"discovery: 0..{disc_end} | embargo {args.embargo} bars | "
          f"eval: {eval_start}..{eval_end} "
          f"({eval_end - eval_start} bars, {ts[eval_start]} -> "
          f"{ts[min(eval_end, n - 1)]})")

    out = {"bars": n, "eval_window": [ts[eval_start],
                                     ts[min(eval_end, n - 1)]],
           "cost_bps": cost_bps, "horizon": args.horizon,
           "rules": {}}
    for name, fn in RULES.items():
        sigs, net = evaluate(closes, fn, args.horizon,
                             eval_start, eval_end, cost_bps)
        trades = len(net)
        if trades < args.min_trades:
            status = "insufficient_evidence"
            mean_b = lcb = None
        else:
            mean_b, lcb = block_bootstrap_lcb(net)
            status = ("candidate_edge" if lcb >
                      args.required_margin_bps else "no_edge")
        out["rules"][name] = {
            "status": status, "trades": trades,
            "mean_net_bps": round(mean_b, 3) if mean_b else None,
            "lcb5_net_bps": round(lcb, 3) if lcb else None,
            "win_rate": round(float(np.mean(net > 0)), 3)
            if trades else None,
            "note": "LCB>margin required for candidate_edge — "
                    "mean>0 alone is not evidence"}
        print(f"{name:15s} trades={trades:3d} "
              f"mean={f'{mean_b:6.2f}' if mean_b is not None else '  n/a'}"
              f"bps lcb5={f'{lcb:6.2f}' if lcb is not None else '  n/a'}"
              f"bps win={out['rules'][name]['win_rate']} -> {status}")

    out["verdict"] = ("candidate_edge" if any(
        r["status"] == "candidate_edge"
        for r in out["rules"].values()) else "no_edge_detected")
    print(f"\nVERDICT: {out['verdict']}")
    rp = ROOT / "var" / "edge_baseline.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(out, indent=2))
    print(f"report: {rp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
