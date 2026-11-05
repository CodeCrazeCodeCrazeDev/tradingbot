#!/usr/bin/env python
"""Cross-asset lead-lag edge gate.

Hypothesis: a large leader-coin move at bar t predicts the follower's
move at t+horizon — crypto majors co-move and BTC leads. Falsifiable:
if lead-lag carried no signal, leader-conditioned follower returns are
cost-covered noise. Same machinery as edge_baseline/edge_gate:
chronological walk-forward segments, entry at close, net-of-cost,
block-bootstrap 5% LCB, >=2-venue requirement.

    python scripts/edge_leadlag.py --leader BTC \
        --followers ETH,SOL,XRP,DOGE,LTC --timeframes 15m \
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
    block_bootstrap_lcb, load_bars, roll_spread_bps)


def aligned_pair(db_path: Path, leader: str, follower: str,
                 timeframe: str):
    """Intersect leader/follower timestamps -> two aligned close arrays."""
    ts_l, bars_l = load_bars(db_path, leader, timeframe)
    ts_f, bars_f = load_bars(db_path, follower, timeframe)
    cl = {t: c for t, c in zip(ts_l, bars_l[:, 3])}
    cf = {t: c for t, c in zip(ts_f, bars_f[:, 3])}
    common = sorted(set(cl) & set(cf))
    return (common,
            np.asarray([cl[t] for t in common]),
            np.asarray([cf[t] for t in common]))


def leadlag_eval(leader_cl, follower_cl, horizon, seg_start, seg_end,
                 cost_bps, thresh):
    """signal = sign(leader 1-bar return) when |ret| > thresh;
    trade follower for horizon bars, net of cost."""
    net = []
    for i in range(max(seg_start, 1), min(seg_end,
                                         len(follower_cl) - horizon)):
        lr = (leader_cl[i] - leader_cl[i - 1]) / leader_cl[i - 1]
        if abs(lr) <= thresh:
            continue
        s = 1.0 if lr > 0 else -1.0
        fwd = ((follower_cl[i + horizon] - follower_cl[i])
               / follower_cl[i] * 1e4)
        net.append(s * fwd - cost_bps)
    net = np.asarray(net)
    if len(net) < 30:
        return {"status": "insufficient_evidence", "trades": len(net),
                "lcb5_net_bps": None, "mean_net_bps": None}
    mean_b, lcb = block_bootstrap_lcb(net)
    return {"status": "evaluated", "trades": len(net),
            "mean_net_bps": round(mean_b, 3), "lcb5_net_bps": round(lcb, 3)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--leader", default="BTC")
    ap.add_argument("--followers", default="ETH,SOL,XRP,DOGE,LTC")
    ap.add_argument("--timeframes", default="15m")
    ap.add_argument("--venues", default="hl_data.db,binance_data.db")
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--min-venues", type=int, default=2)
    ap.add_argument("--horizon", type=int, default=1)
    ap.add_argument("--thresh", type=float, default=0.0015,
                    help="leader 1-bar return threshold (fraction)")
    ap.add_argument("--margin", type=float, default=2.0)
    ap.add_argument("--eval-frac", type=float, default=0.45)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--out", default="var/edge_leadlag.json")
    args = ap.parse_args()

    results = {}
    for fol in [f.strip() for f in args.followers.split(",") if f.strip()]:
        for tf in [t.strip() for t in args.timeframes.split(",")
                   if t.strip()]:
            key = f"{args.leader}->{fol}:{tf}"
            passed = evaluated = 0
            detail = {}
            for db in [d.strip() for d in args.venues.split(",")
                       if d.strip()]:
                common, cl, cf = aligned_pair(ROOT / db, args.leader,
                                             fol, tf)
                n = len(common)
                if n < 200:
                    detail[db] = {"status": "insufficient_bars",
                                  "bars": n}
                    continue
                cost = max(roll_spread_bps(cf) or 0.0, 5.0)
                eval_n = int(n * args.eval_frac)
                seg_len = (eval_n - args.embargo) // args.segments
                segs = [leadlag_eval(
                            cl, cf, args.horizon,
                            n - eval_n + args.embargo + k * seg_len,
                            n - eval_n + args.embargo + (k + 1) * seg_len,
                            cost, args.thresh)
                        for k in range(args.segments)]
                ev = [s for s in segs if s["status"] == "evaluated"]
                ok = (len(ev) == len(segs)
                      and all(s["lcb5_net_bps"] > args.margin
                              for s in ev))
                evaluated += 1
                passed += int(ok)
                detail[db] = {"bars": n, "verdict": "pass" if ok else "fail",
                              "segments": segs}
                print(f"{key:<22}{db:<18}{'PASS' if ok else 'fail':<5}"
                      f" {[s['lcb5_net_bps'] for s in segs]}")
            results[key] = {
                "verdict": ("qualified_candidate"
                            if (evaluated >= args.min_venues
                                and passed >= args.min_venues)
                            else "rejected"),
                "venues_passed": passed,
                "venues_evaluated": evaluated,
                "detail": detail}

    report = {"generated_at": time.time(),
              "gate": {"leader": args.leader, "horizon": args.horizon,
                       "thresh": args.thresh, "segments": args.segments,
                       "min_venues": args.min_venues,
                       "margin": args.margin},
              "candidates": results}
    rp = ROOT / args.out
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=2))
    n_q = sum(1 for v in results.values()
              if v["verdict"] == "qualified_candidate")
    print(f"\nqualified: {n_q}  report: {rp}")
    for k, v in sorted(results.items(),
                       key=lambda kv: -kv[1]["venues_passed"]):
        print(f"  {k:<22} {v['verdict']:<22} "
              f"{v['venues_passed']}/{v['venues_evaluated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
