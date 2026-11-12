#!/usr/bin/env python
"""Event-study gate: do scheduled macro releases have exploitable
drift/vol in the 15-60min window after publication?

Different hypothesis class from the falsified continuous signals:
events are discrete, scheduled, and the calendar is real
(macro_data.db news_events: FOMC statements/minutes, NFP rule-seeds,
ALFRED-vintage releases — published_at semantics already honest).

Per event: locate the M15 bar containing ts_utc, measure
  pre  = log return over the 4 bars BEFORE the event bar
  post_h = log return over h bars AFTER (h in HORIZONS)
  drift = sign-consistent follow-through? We test TWO claims:
    A) vol claim: |post_1| + |post_2| exceeds unconditional median
       (event vol premium — monetizable only via sizing, reported
       separately, never a direction claim)
    B) drift claim: post_h mean != 0 with sign stability — the only
       direction-eligible output; evaluated net of COST_BPS on a
       hypothetical always-in-sign-of-surprise position is NOT used
       (no reliable actual-vs-forecast surprise field) — instead we
       test post-event CONTINUATION of the event-bar move:
       pos = sign(event_bar_return) held h bars, net of cost.

Verdict per (impact, pair-group, horizon): 60/40 chronological on
EVENTS, block-bootstrap LCB5 on per-event net bps; candidate needs
LCB>0 in all 3 OOS segments. Honest nulls expected — most event
alpha at retail cost is sub-gate; that IS the measurement.

Usage: python scripts/event_study_gate.py \
    --events-db macro_data.db --bars-db market_data.db \
    --out var/event_study_gate.json
"""

import argparse
import bisect
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402

COST_BPS = 5.0
HORIZONS = (1, 2, 4, 8)
IMPACTS = ("high", "medium")
# currency -> instruments whose price contains that currency leg
CCY_MAP = {"USD": ["EURUSD", "GBPUSD", "USDJPY"],
           "EUR": ["EURUSD"], "GBP": ["GBPUSD"], "JPY": ["USDJPY"]}


def load_events(db: str):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT ts_utc, currency, impact, title FROM news_events "
        "ORDER BY ts_utc").fetchall()
    con.close()
    return rows


def load_bars(db: str, symbol: str, timeframe: str = "M15"):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT timestamp, close FROM market_data "
        "WHERE symbol=? AND timeframe=? ORDER BY timestamp",
        (symbol, timeframe)).fetchall()
    con.close()
    ts = [r[0] for r in rows]
    cl = np.array([r[1] for r in rows])
    return ts, cl


def event_returns(ts, closes, ev_ts):
    """Index of first bar with timestamp >= ev_ts; None if outside."""
    i = bisect.bisect_left(ts, ev_ts)
    if i >= len(ts) - max(HORIZONS) - 1 or i < 5:
        return None
    return i


def evaluate_events(events, bars_by_sym, cost_bps):
    """events: [(ts,currency,impact,title)]; bars_by_sym:
    {symbol: (ts_list, closes)}. Returns per-group metrics."""
    groups = {}
    for ts_utc, ccy, impact, title in events:
        impact = (impact or "").lower()
        if impact not in IMPACTS or ccy not in CCY_MAP:
            continue
        for sym in CCY_MAP[ccy]:
            if sym not in bars_by_sym:
                continue
            ts, cl = bars_by_sym[sym]
            i = event_returns(ts, cl, ts_utc)
            if i is None:
                continue
            ev_bar_ret = cl[i] / cl[i - 1] - 1.0
            rec = {"sym": sym, "impact": impact, "i": i,
                   "ev_ret": ev_bar_ret}
            for h in HORIZONS:
                rec[f"post{h}"] = cl[i + h] / cl[i] - 1.0
            groups.setdefault((impact, sym), []).append(rec)
    return groups


def score_group(recs, h, cost_bps):
    """Continuation strategy: pos=sign(event_bar_ret), earn post_h,
    pay cost once. Per-event net bps."""
    nets = []
    for r in recs:
        if r["ev_ret"] == 0:
            continue
        pos = 1.0 if r["ev_ret"] > 0 else -1.0
        nets.append(pos * r[f"post{h}"] * 1e4 - cost_bps)
    nets = np.array(nets)
    n = len(nets)
    if n < 30:
        return {"status": "insufficient_evidence", "n": n}
    split = int(n * 0.6)
    ev = nets[split:]
    m, l = block_bootstrap_lcb(ev)
    seg_n = max(1, len(ev) // 3)
    segs = []
    for k in range(3):
        a, b = k * seg_n, (k + 1) * seg_n if k < 2 else len(ev)
        if b - a < 10:
            segs.append({"status": "thin"})
            continue
        ms, ls = block_bootstrap_lcb(ev[a:b])
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    ok = (len([s for s in segs if "lcb5" in s]) == 3
          and all(s["lcb5"] > 0 for s in segs if "lcb5" in s) and m > 0)
    return {"n": n, "mean_bps": round(m, 3), "lcb5": round(l, 3),
            "exposure_note": "continuation-of-event-bar direction",
            "segments": segs,
            "verdict": "candidate" if ok else "rejected"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events-db", default="macro_data.db")
    ap.add_argument("--bars-db", default="market_data.db")
    ap.add_argument("--symbols", default="EURUSD,GBPUSD,USDJPY")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/event_study_gate.json")
    args = ap.parse_args()

    events = load_events(args.events_db)
    print(f"events loaded: {len(events)}")
    bars = {}
    for sym in [s.strip() for s in args.symbols.split(",")]:
        bars[sym] = load_bars(args.bars_db, sym)
        print(f"  {sym}: {len(bars[sym][0])} M15 bars")

    groups = evaluate_events(events, bars, args.cost_bps)
    report = {"gate": {"cost_bps": args.cost_bps, "horizons": HORIZONS,
                       "impacts": IMPACTS},
              "n_events": len(events), "groups": {}}
    for (impact, sym), recs in sorted(groups.items()):
        key = f"{impact}:{sym}"
        report["groups"][key] = {
            "n_events": len(recs),
            "horizons": {f"h{h}": score_group(recs, h, args.cost_bps)
                         for h in HORIZONS}}
        for h in HORIZONS:
            s = report["groups"][key]["horizons"][f"h{h}"]
            print(f"[{key} h{h}] n={s.get('n')} "
                  f"mean={s.get('mean_bps')} lcb={s.get('lcb5')} "
                  f"-> {s.get('verdict', s.get('status'))}", flush=True)

    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    cands = [(k, h) for k, g in report["groups"].items()
             for h, s in g["horizons"].items()
             if s.get("verdict") == "candidate"]
    for k, h in cands:
        print(f"  CANDIDATE {k} {h}")
    if not cands:
        print("  no event-study candidates — honest null")
    return 0


if __name__ == "__main__":
    sys.exit(main())
