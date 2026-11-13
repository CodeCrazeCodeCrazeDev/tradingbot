"""Delta-neutral funding carry evaluator.

Sibling to funding_carry_eval.py, which measures the UNHEDGED
funding-signed directional fade (funding income + drift reported
separately). This script measures the actual carry claim: hold a
delta-neutral book — receive |funding| while the spot/perp legs
cancel directional exposure — and report what survives after the
MEASURED cross-venue basis and trading costs.

Position rule per funding interval (t0 -> t1, payment at t1):
  funding_rate(t1) > 0  ->  longs pay shorts  ->  SHORT perp + LONG spot
  funding_rate(t1) < 0  ->  shorts pay longs  ->  LONG perp + SHORT spot
Per-window P&L (bps of perp notional):
  net = |funding_bps| + sign(f) * (spot_ret_bps - perp_ret_bps)
        - rebalance_bps - (cost_bps if position flips else 0)

Honest boundaries, stated in every record:
  * spot leg is a PROXY — binance_data.db symbol closes are treated
    as spot; if they are actually perp klines the measured "basis"
    is a perp-perp venue spread, which still represents real hedge
    risk for a cross-venue book but is not same-venue basis.
  * side selection uses the funding rate printed at t1 — the rate
    is observable shortly before settlement, but exact timing is
    approximated (mild lookahead, bounded by funding-sign
    persistence).
  * costs are fixed bps assumptions, not measured spreads.
  * funding accrues on perp notional; gross book is ~2x that.

Verdicts append to var/methods/ledger.jsonl (same contract as
funding_carry_eval) so analyst_review picks them up unchanged.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FUNDING_DB = ROOT / "funding_data.db"
SPOT_DB = ROOT / "binance_data.db"
PERP_DB = ROOT / "hl_data.db"
OUT = ROOT / "var" / "methods" / "ledger.jsonl"


def load_funding(db: Path, source: str, symbol: str):
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT funding_time, funding_rate FROM funding_rates "
            "WHERE source=? AND symbol=? ORDER BY funding_time",
            (source, symbol)).fetchall()
    finally:
        con.close()
    return [(int(t), float(r)) for t, r in rows]


def load_closes(db: Path, symbol: str, tf: str):
    """-> sorted (epoch_ms, close); same contract as funding_carry_eval."""
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT timestamp, close FROM market_data "
            "WHERE symbol=? AND timeframe=? ORDER BY timestamp",
            (symbol, tf)).fetchall()
    finally:
        con.close()
    out = []
    for ts, c in rows:
        try:
            dt = datetime.fromisoformat(str(ts))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            out.append((int(dt.timestamp() * 1000), float(c)))
        except (ValueError, TypeError):
            continue
    return [(t, c) for t, c in out if c and c > 0]


def nearest_close(series, ts_ms, tol_ms):
    if not series:
        return None
    ts = np.array([t for t, _ in series])
    i = int(np.argmin(np.abs(ts - ts_ms)))
    if abs(int(ts[i]) - ts_ms) <= tol_ms:
        return series[i][1]
    return None


def evaluate(fr, spot, perp, tol_ms, cost_bps, rebalance_bps,
             segments):
    """fr: [(funding_ms, rate)]; returns stats dict or None."""
    funds, hedges, nets, flips, wins = [], [], [], [], []
    prev_sign = 0.0
    for i in range(len(fr) - 1):
        t0 = fr[i][0]
        t1, f1 = fr[i + 1]
        f0 = fr[i][1]
        s0, p0 = nearest_close(spot, t0, tol_ms), \
            nearest_close(perp, t0, tol_ms)
        s1, p1 = nearest_close(spot, t1, tol_ms), \
            nearest_close(perp, t1, tol_ms)
        if not all(v and v > 0 for v in (s0, p0, s1, p1)):
            continue
        spot_ret = math.log(s1 / s0) * 1e4
        perp_ret = math.log(p1 / p0) * 1e4
        side = 1.0 if f1 > 0 else -1.0     # +1 = short perp/long spot
        hedge = side * (spot_ret - perp_ret)
        fund_bps = abs(f1) * 1e4
        flip = side != (1.0 if f0 > 0 else -1.0)
        net = fund_bps + hedge - rebalance_bps \
            - (cost_bps if flip or i == 0 else 0.0)
        funds.append(fund_bps)
        hedges.append(hedge)
        nets.append(net)
        flips.append(bool(flip))
        wins.append(net > 0)
        prev_sign = side
    n = len(nets)
    if n < 10:
        return None
    net = np.asarray(nets)
    seg_means = []
    for s in range(segments):
        chunk = net[int(n * s / segments):int(n * (s + 1) / segments)]
        seg_means.append(round(float(chunk.mean()), 3) if len(chunk)
                         else None)
    sharpe = (net.mean() / net.std() * math.sqrt(n)
              if net.std() > 0 else 0.0)
    return {"windows": n,
            "funding_bps_per_window": round(float(np.mean(funds)), 3),
            "hedge_basis_bps_per_window":
                round(float(np.mean(hedges)), 3),
            "rebalance_bps_per_window": rebalance_bps,
            "cost_bps_per_window": round(cost_bps * float(np.mean(flips)), 3),
            "net_bps_per_window": round(float(net.mean()), 3),
            "net_total_bps": round(float(net.sum()), 1),
            "net_sharpe": round(float(sharpe), 3),
            "hit_rate": round(float(np.mean(wins)), 3),
            "position_flips": int(sum(flips)),
            "segment_means_bps": seg_means,
            "mechanism": "delta-neutral carry — funding income minus "
                         "measured cross-venue basis, net of costs"}


def verdict(stats: dict) -> str:
    segs = [s for s in stats["segment_means_bps"] if s is not None]
    if stats["net_total_bps"] > 0 and stats["net_sharpe"] > 1.0 \
            and sum(1 for s in segs if s > 0) >= (len(segs) + 1) // 2:
        return "PASS"
    if stats["funding_bps_per_window"] > 0 and \
            stats["net_bps_per_window"] <= 0:
        return "MARGINAL"
    return "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--funding-source", default="hyperliquid")
    ap.add_argument("--funding-symbol", default="BTC")
    ap.add_argument("--spot-db", default=str(SPOT_DB))
    ap.add_argument("--spot-symbol", default="BTC")
    ap.add_argument("--perp-db", default=str(PERP_DB))
    ap.add_argument("--perp-symbol", default="BTC")
    ap.add_argument("--tf", default="1h")
    ap.add_argument("--tol-min", type=float, default=30.0)
    ap.add_argument("--cost-bps", type=float, default=1.6,
                    help="round-trip both legs, charged on flips/entry")
    ap.add_argument("--rebalance-bps", type=float, default=0.4,
                    help="per-interval leg-rebalance cost")
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--funding-db", default=str(FUNDING_DB))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    fr = load_funding(Path(args.funding_db), args.funding_source,
                      args.funding_symbol)
    spot = load_closes(Path(args.spot_db), args.spot_symbol, args.tf)
    perp = load_closes(Path(args.perp_db), args.perp_symbol, args.tf)
    rec = {"ts": datetime.now(timezone.utc).isoformat(),
           "spec": {"family": "funding_carry_delta",
                    "funding_source": args.funding_source,
                    "funding_symbol": args.funding_symbol,
                    "spot_symbol": args.spot_symbol,
                    "perp_symbol": args.perp_symbol, "tf": args.tf},
           "cost_bps": args.cost_bps,
           "rebalance_bps": args.rebalance_bps,
           "caveats": ["cross-venue basis: spot leg is a proxy "
                       "(binance_data.db), perp leg is hl_data.db",
                       "spot/perp instrument type unverified",
                       "funding side selection approximates print "
                       "timing (mild lookahead)",
                       "fixed bps costs, not measured spreads"]}
    stats = evaluate(fr, spot, perp, int(args.tol_min * 60_000),
                     args.cost_bps, args.rebalance_bps, args.segments)
    if stats is None:
        rec.update(verdict="REJECTED",
                   reason=f"insufficient aligned windows "
                          f"(funding prints={len(fr)}, "
                          f"spot bars={len(spot)}, perp bars={len(perp)})")
        print(f"REJECTED  {rec['reason']}")
    else:
        v = verdict(stats)
        rec.update(verdict=v, stats=stats)
        print(f"{v:9s} funding_carry_delta {args.funding_symbol} "
              f"fund[{args.funding_source}] vs spot={args.spot_symbol}"
              f" perp={args.perp_symbol}@{args.tf} "
              f"windows={stats['windows']} "
              f"fund={stats['funding_bps_per_window']:+.3f}bps/w "
              f"basis={stats['hedge_basis_bps_per_window']:+.3f}bps/w "
              f"net={stats['net_bps_per_window']:+.3f}bps/w "
              f"total={stats['net_total_bps']:+.1f}bps "
              f"sharpe={stats['net_sharpe']:+.2f} "
              f"flips={stats['position_flips']} "
              f"segs={stats['segment_means_bps']}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"ledger -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
