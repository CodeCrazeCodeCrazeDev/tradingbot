#!/usr/bin/env python
"""Overnight/intraday decomposition gate — first EQUITY hypothesis.

Different microstructure from FX/crypto: equity returns decompose
into overnight (prev_close -> open) and intraday (open -> close)
components, and the literature's well-known anomaly is that equity
premia concentrate overnight while intraday is flat-to-negative.
FX has no close/open gap structure — this class is untestable there.

Per symbol, per day t (needs consecutive sessions):
  overnight_bps = open[t]/close[t-1] - 1   (gap component)
  intraday_bps  = close[t]/open[t] - 1     (session component)

Strategies (one round trip per day each, COST_BPS charged once):
  long_overnight   +1 * overnight_bps - cost
  long_intraday    +1 * intraday_bps  - cost
  short_overnight  -1 * overnight_bps - cost
  short_intraday   -1 * intraday_bps  - cost
  long_both        overnight+intraday - 2*cost  (always-invested ref)

Verdict per (symbol, strategy): chronological 60/40 on DAYS,
OOS tail in 3 contiguous segments, block-bootstrap LCB5 — candidate
only if EVERY segment LCB>0 and mean>0. Also reports the
cross-sectional equal-weight portfolio verdict (the anomaly claim
is about the broad market, not one ticker).

Usage: python scripts/overnight_intraday_gate.py \
    --db us_stocks.db --out var/overnight_intraday_gate.json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402

COST_BPS = 5.0
STRATEGIES = ("long_overnight", "long_intraday",
              "short_overnight", "short_intraday", "long_both")


def load_daily(db: str, symbol: str):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT timestamp, open, high, low, close, volume "
        "FROM market_data WHERE symbol=? AND timeframe='D1' "
        "ORDER BY timestamp", (symbol,)).fetchall()
    con.close()
    if len(rows) < 100:
        return None
    ts = [r[0] for r in rows]
    o = np.array([r[1] for r in rows])
    c = np.array([r[4] for r in rows])
    return ts, o, c


def day_pnl(o, c, cost_bps):
    """Per-day bps arrays for each strategy. Day t uses bars t-1,t."""
    on = (o[1:] / c[:-1] - 1.0) * 1e4     # overnight t-1 close -> t open
    idi = (c[1:] / o[1:] - 1.0) * 1e4    # intraday t open -> t close
    out = {
        "long_overnight": on - cost_bps,
        "long_intraday": idi - cost_bps,
        "short_overnight": -on - cost_bps,
        "short_intraday": -idi - cost_bps,
        "long_both": on + idi - 2 * cost_bps,
    }
    return out, on, idi


def verdict(pnl, n_segments=3):
    n = len(pnl)
    if n < 60:
        return {"status": "insufficient_evidence", "n": n}
    split = int(n * 0.6)
    ev = pnl[split:]
    if len(ev) < 30:
        return {"status": "insufficient_eval", "n": len(ev)}
    m, l = block_bootstrap_lcb(ev)
    seg_n = max(1, len(ev) // n_segments)
    segs = []
    for k in range(n_segments):
        a, b = k * seg_n, (k + 1) * seg_n if k < n_segments - 1 \
            else len(ev)
        if b - a < 10:
            segs.append({"status": "thin"})
            continue
        ms, ls = block_bootstrap_lcb(ev[a:b])
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    ok = (len([s for s in segs if "lcb5" in s]) == 3
          and all(s["lcb5"] > 0 for s in segs if "lcb5" in s) and m > 0)
    return {"n": n, "mean_bps": round(m, 3), "lcb5": round(l, 3),
            "segments": segs,
            "verdict": "candidate" if ok else "rejected"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="us_stocks.db")
    ap.add_argument("--symbols", default=None,
                    help="comma list; default = all 1d symbols in db")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/overnight_intraday_gate.json")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        symbols = [r[0] for r in con.execute(
            "SELECT DISTINCT symbol FROM market_data "
            "WHERE timeframe='D1' ORDER BY symbol")]
    con.close()
    print(f"symbols: {symbols}")

    report = {"gate": {"db": args.db, "cost_bps": args.cost_bps,
                       "strategies": STRATEGIES},
              "per_symbol": {}, "portfolio": {}}
    port_pnl = {s: [] for s in STRATEGIES}
    n_days_ref = None

    for sym in symbols:
        got = load_daily(args.db, sym)
        if got is None:
            print(f"[{sym}] <100 daily bars — skip")
            continue
        ts, o, c = got
        pnls, on, idi = day_pnl(o, c, args.cost_bps)
        report["per_symbol"][sym] = {
            "days": len(on),
            "first": ts[1], "last": ts[-1],
            "mean_overnight_bps": round(float(np.mean(on)), 2),
            "mean_intraday_bps": round(float(np.mean(idi)), 2),
            "strategies": {s: verdict(pnls[s]) for s in STRATEGIES}}
        for s in STRATEGIES:
            port_pnl[s].append(pnls[s])
        n_days_ref = len(on)
        mo = float(np.mean(on))
        mi = float(np.mean(idi))
        print(f"[{sym}] days={len(on)} on={mo:+.1f}bps "
              f"id={mi:+.1f}bps", flush=True)

    # equal-weight cross-sectional portfolio (aligned on day count —
    # all series share the trading calendar, lengths may differ by a
    # few days; truncate to min length)
    minlen = min(len(arr) for s in STRATEGIES for arr in port_pnl[s]) \
        if any(port_pnl[s] for s in STRATEGIES) else 0
    if minlen > 60:
        for s in STRATEGIES:
            arrs = [np.asarray(v)[:minlen] for v in port_pnl[s]]
            port = np.mean(arrs, axis=0)
            report["portfolio"][s] = verdict(port)
            r = report["portfolio"][s]
            print(f"[PORTFOLIO {s}] mean={r.get('mean_bps')} "
                  f"lcb={r.get('lcb5')} -> "
                  f"{r.get('verdict', r.get('status'))}", flush=True)

    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    cands = [(k, s) for k, p in report["per_symbol"].items()
             for s, v in p["strategies"].items()
             if v.get("verdict") == "candidate"]
    cands += [("PORTFOLIO", s) for s, v in
              report["portfolio"].items()
              if v.get("verdict") == "candidate"]
    for k, s in cands:
        print(f"  CANDIDATE {s} on {k}")
    if not cands:
        print("  no overnight/intraday candidates — honest null")
    return 0


if __name__ == "__main__":
    sys.exit(main())
