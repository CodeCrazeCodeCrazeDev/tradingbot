#!/usr/bin/env python
"""Multi-window cross-venue edge gate (P5).

edge_baseline asks: "does a rule clear bootstrap LCB on ONE eval
window?" This gate asks the promotion question: "does it clear LCB on
EVERY walk-forward segment AND on at least --min-venues independent
venues?" A candidate that only wins one window or one exchange's bars
is selection noise, not edge — this is the gate that keeps a lucky
window from ever reaching promotion.

Usage:
    python scripts/edge_gate.py \
        --combos "binance_data.db:BTC:15m,hl_data.db:BTC:15m" \
        --segments 3 --min-venues 2 --horizon 4
    python scripts/edge_gate.py --grid BTC,ETH,SOL --timeframes 15m,1h \
        --venues hl_data.db,binance_data.db
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import (  # noqa: E402
    RULES, block_bootstrap_lcb, evaluate, load_bars, quarantine_flags,
    roll_spread_bps)
from scripts.edge_hypotheses import HYPOTHESES  # noqa: E402

ALL_RULES = dict(RULES)
ALL_RULES.update(HYPOTHESES)


def segment_eval(closes, fn, horizon, seg_start, seg_end, cost_bps):
    _, net = evaluate(closes, fn, horizon, seg_start, seg_end, cost_bps)
    if len(net) < 30:
        return {"status": "insufficient_evidence", "trades": len(net),
                "lcb5_net_bps": None, "mean_net_bps": None}
    mean_b, lcb = block_bootstrap_lcb(net)
    return {"status": "evaluated", "trades": len(net),
            "mean_net_bps": round(mean_b, 3),
            "lcb5_net_bps": round(lcb, 3)}


def gate_combo(db_path: Path, symbol: str, timeframe: str,
               segments: int, horizon: int, margin: float,
               eval_frac: float, embargo: int) -> dict:
    qf = quarantine_flags(db_path, symbol, timeframe)
    if qf and qf["quarantined"]:
        return {"status": "quarantined", "flags": qf["flags"],
                "reason": "data_quality flags — repair is operator-gated",
                "rules": {}}
    ts, bars = load_bars(db_path, symbol, timeframe)
    closes = bars[:, 3]
    n = len(closes)
    roll = roll_spread_bps(closes)
    cost_bps = max(roll or 0.0, 5.0)

    eval_n = int(n * eval_frac)
    if eval_n < segments * 40:
        return {"status": "insufficient_bars", "bars": n,
            "rules": {}}
    seg_len = (eval_n - embargo) // segments
    bounds = [(n - eval_n + embargo + k * seg_len,
               n - eval_n + embargo + (k + 1) * seg_len)
              for k in range(segments)]
    out_rules = {}
    for name, fn in ALL_RULES.items():
        segs = [segment_eval(closes, fn, horizon, a, b, cost_bps)
                for a, b in bounds]
        evaluated = [s for s in segs if s["status"] == "evaluated"]
        # Gate: every evaluated segment must clear the margin, and at
        # least half the segments must be evaluable at all.
        passes = (len(evaluated) >= max(1, segments // 2)
                  and len(evaluated) == len(segs)
                  and all(s["lcb5_net_bps"] > margin for s in evaluated))
        out_rules[name] = {
            "verdict": "pass" if passes else "fail",
            "segments": segs}
    return {"status": "evaluated", "bars": n,
            "eval_window": [ts[n - eval_n + embargo], ts[-1]],
            "cost_bps": cost_bps, "rules": out_rules}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combos", default="",
                    help="db:symbol:timeframe list, comma separated")
    ap.add_argument("--grid", default="",
                    help="coins list — pairs with --venues/--timeframes")
    ap.add_argument("--venues", default="hl_data.db,binance_data.db")
    ap.add_argument("--timeframes", default="15m")
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--min-venues", type=int, default=2)
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--eval-frac", type=float, default=0.45,
                    help="tail fraction used for walk-forward segments")
    ap.add_argument("--required-margin-bps", type=float, default=2.0)
    ap.add_argument("--out", default="var/edge_gate.json")
    args = ap.parse_args()

    combos = []
    if args.combos:
        for c in args.combos.split(","):
            db, sym, tf = c.strip().split(":")
            combos.append((db, sym, tf))
    for coin in [c.strip() for c in args.grid.split(",") if c.strip()]:
        for db in [d.strip() for d in args.venues.split(",") if d.strip()]:
            for tf in [t.strip() for t in args.timeframes.split(",")
                       if t.strip()]:
                combos.append((db, coin, tf))
    if not combos:
        print("no combos — pass --combos or --grid")
        return 2

    by_rule: dict = {}
    venue_hits: dict = {}
    for db, sym, tf in combos:
        key = f"{sym}:{tf}"
        dbp = ROOT / db
        label = f"{db}:{sym}:{tf}"
        try:
            res = gate_combo(dbp, sym, tf, args.segments, args.horizon,
                             args.required_margin_bps, args.eval_frac,
                             args.embargo)
        except Exception as exc:  # noqa: BLE001
            res = {"status": f"error:{exc}", "rules": {}}
        print(f"{label:<38} {res.get('status')} "
              f"bars={res.get('bars')}")
        if res.get("status") != "evaluated":
            continue
        venue_hits.setdefault(key, []).append(db)
        for name, r in res["rules"].items():
            entry = by_rule.setdefault(name, {}).setdefault(
                key, {"venues_passed": 0, "venues_evaluated": 0,
                      "detail": {}})
            entry["venues_evaluated"] += 1
            if r["verdict"] == "pass":
                entry["venues_passed"] += 1
            entry["detail"][db] = r["verdict"]

    promoted = {}
    for name, combos_ in by_rule.items():
        for key, e in combos_.items():
            ok = (e["venues_evaluated"] >= args.min_venues
                  and e["venues_passed"] >= args.min_venues)
            promoted[f"{name}@{key}"] = {
                "verdict": ("qualified_candidate" if ok else "rejected"),
                "venues_passed": e["venues_passed"],
                "venues_evaluated": e["venues_evaluated"],
                "detail": e["detail"]}

    report = {"generated_at": time.time(),
              "gate": {"segments": args.segments,
                       "min_venues": args.min_venues,
                       "margin_bps": args.required_margin_bps,
                       "horizon": args.horizon,
                       "eval_frac": args.eval_frac,
                       "embargo": args.embargo},
              "candidates": promoted}
    rp = ROOT / args.out
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=2))
    n_q = sum(1 for v in promoted.values()
              if v["verdict"] == "qualified_candidate")
    print(f"\nqualified candidates: {n_q}  report: {rp}")
    for k, v in sorted(promoted.items(),
                       key=lambda kv: -kv[1]["venues_passed"]):
        print(f"  {k:<40} {v['verdict']:<22} "
              f"{v['venues_passed']}/{v['venues_evaluated']} venues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
