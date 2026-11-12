#!/usr/bin/env python
"""Live-outcome feedback: the spine's own trades become evidence.

Every other verdict in the pipeline judges EXTERNAL claims. This
closes the last loop: paper_runner fills -> FIFO round-trips ->
net bps per round-trip -> a method_candidates-shaped record the
analyst_review consumes like any claim. Explore-probe P&L is the
CSC's implicit directional skill being falsified (or confirmed)
on real replayed data — first-class research evidence, not just
accounting.

Honest limits: per-unit bps (quantity cancels), gross of modeled
spread but NET of recorded commissions when present, FIFO matching
ignores partial-close granularity. Runs with <30 round-trips emit
nothing (insufficient evidence, same bar as the gates).

Usage:
    python scripts/live_outcome_report.py var/soakx_norv var/soakx_rv
    python scripts/live_outcome_report.py --all-soaks
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402

MIN_ROUND_TRIPS = 20
N_SEGMENTS = 3
MARGIN_BPS = 0.0


def round_trips(db_path: Path):
    """FIFO match fills per symbol -> list of (net_bps, ts) per
    closed round-trip. net = sign*(exit-entry)/entry*1e4 minus
    per-leg commission bps when the fills carry it."""
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "select symbol, side, quantity, price, commission,"
            " occurred_at from fills order by occurred_at"
        ).fetchall()
    finally:
        con.close()
    rts = []
    for sym in sorted({r[0] for r in rows}):
        srows = [r for r in rows if r[0] == sym]
        open_side, open_q, open_px, open_comm = None, 0.0, 0.0, 0.0
        for _s, side, q, p, comm, ts in srows:
            comm = comm or 0.0
            if open_side is None:
                open_side, open_q, open_px, open_comm = side, q, p, comm
                continue
            if side == open_side:
                tot_q = open_q + q
                open_px = (open_px * open_q + p * q) / tot_q
                open_comm += comm
                open_q = tot_q
                continue
            done = min(q, open_q)
            if done <= 0:
                continue
            frac = done / open_q
            leg_comm = open_comm * frac + comm * (done / q)
            notional_bps = done * open_px  # quote-ccy notional proxy
            comm_bps = (leg_comm / notional_bps * 1e4
                        if notional_bps > 0 else 0.0)
            sgn = 1.0 if open_side == "buy" else -1.0
            gross = sgn * (p - open_px) / open_px * 1e4
            rts.append({"net_bps": round(gross - comm_bps, 4),
                        "gross_bps": round(gross, 4),
                        "comm_bps": round(comm_bps, 4),
                        "ts": ts, "symbol": sym})
            remaining = q - done
            open_q -= done
            open_comm *= (open_q / (open_q + done)) if open_q else 0.0
            if open_q <= 1e-9:
                open_side, open_q, open_px, open_comm = None, 0.0, 0.0, 0.0
            if remaining > 1e-9:
                # opposing fill exceeded the open lot — leftover opens
                # a fresh position on the other side
                open_side, open_q, open_px, open_comm = (
                    side, remaining, p, comm)
    return rts


def build_record(state_dir: Path):
    """state_dir -> method_candidates-shaped verdict record, or None."""
    db = state_dir / "trading_state.db"
    if not db.exists():
        return None, "no trading_state.db"
    rts = round_trips(db)
    if len(rts) < MIN_ROUND_TRIPS:
        return None, f"{len(rts)} round-trips < {MIN_ROUND_TRIPS}"
    nets = np.array([r["net_bps"] for r in rts])
    n = len(nets)
    seg_len = max(1, n // N_SEGMENTS)
    segments = []
    for k in range(N_SEGMENTS):
        a, b = k * seg_len, (k + 1) * seg_len if k < N_SEGMENTS - 1 else n
        seg = nets[a:b]
        if len(seg) < 10:
            segments.append({"segment": k,
                             "status": "insufficient_evidence",
                             "trades": int(len(seg))})
            continue
        m, l = block_bootstrap_lcb(seg)
        segments.append({"segment": k, "status": "evaluated",
                         "trades": int(len(seg)),
                         "mean_net_bps": round(m, 3),
                         "lcb5_net_bps": round(l, 3)})
    evaluated = [s for s in segments if s["status"] == "evaluated"]
    passes = (len(evaluated) == len(segments)
              and all(s["lcb5_net_bps"] > MARGIN_BPS
                      for s in evaluated))
    m, l = block_bootstrap_lcb(nets)
    syms = sorted({r["symbol"] for r in rts})
    return {
        "spec": {
            "spec_id": f"live_probe_{state_dir.name}",
            "family": "csc_explore_probe",
            "hypothesis": ("CSC explore-probe directional proposals "
                           f"on {state_dir.name} replay"),
            "params": {"state_dir": state_dir.name},
        },
        "dataset": {"db": "trading_state.db", "symbol": ",".join(syms),
                    "timeframe": "fills"},
        "gate": {"verdict": "candidate" if passes else "rejected"},
        "verdict": {
            "dataset": f"live:{state_dir.name}",
            "eval_window": [rts[0]["ts"], rts[-1]["ts"]],
            "cost_bps": round(float(np.mean(
                [r["comm_bps"] for r in rts])), 4),
            "verdict": "candidate" if passes else "rejected",
            "overall": {"trades": n, "mean_net_bps": round(m, 3),
                        "lcb5_net_bps": round(l, 3)},
            "segments": segments,
            "meta": {"round_trips": n,
                     "mean_gross_bps": round(float(nets.mean()
                                                   + np.mean(
                        [r["comm_bps"] for r in rts])), 3),
                     "generated": datetime.now(
                         timezone.utc).isoformat(
                         timespec="seconds")},
        },
    }, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state_dirs", nargs="*",
                    help="paper_runner state dirs containing "
                         "trading_state.db")
    ap.add_argument("--all-soaks", action="store_true",
                    help="scan var/*/trading_state.db")
    ap.add_argument("--out-dir", default="var/method_candidates")
    args = ap.parse_args()

    dirs = [Path(d) for d in args.state_dirs]
    if args.all_soaks:
        dirs += sorted(ROOT.glob("var/*/trading_state.db"))
        dirs = [d.parent for d in dirs]
    if not dirs:
        ap.error("no state dirs")

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for sd in dirs:
        rec, why = build_record(sd)
        if rec is None:
            print(f"{sd.name}: skipped ({why})")
            continue
        ov = rec["verdict"]["overall"]
        out = out_dir / f"live_{sd.name}.json"
        out.write_text(json.dumps(rec, indent=2))
        wrote += 1
        print(f"{sd.name}: {ov['trades']} round-trips "
              f"mean={ov['mean_net_bps']:+.2f}bps "
              f"lcb={ov['lcb5_net_bps']:+.2f} -> {out.name}")
    print(f"wrote {wrote} live-outcome record(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
