#!/usr/bin/env python
"""Funding-carry evaluation on LOCAL collected data — no network.

First consumer of funding_data.db (scripts/collect_funding.py): joins
settled funding prints to aligned price closes and scores the carry
trade — hold the perp AGAINST the crowded side each funding window,
earn |funding|, pay drift + costs.

Honest boundaries, stated in every record:
- Price leg is the SPOT close from binance_data.db market_data, used
  as a perp proxy — the basis between spot and perp is NOT measured
  here (premiumIndex snapshots carry mark/index but only ~1/run).
- Cost model: fixed --cost-bps per window round-trip (default 1.6,
  taker estimate from edge_research H2) — not the measured-spread
  model method_candidate uses.
- Funding is credited at |rate| to the anti-crowded side; drift is
  the signed spot move over the same window.

Verdicts append to var/methods/ledger.jsonl (same contract as
method_eval): PASS / MARGINAL / FAIL / REJECTED. Advisory only.

    .venv/Scripts/python.exe scripts/funding_carry_eval.py \
        --symbol BTCUSDT --price-symbol BTC --tf 15m
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FUNDING_DB = ROOT / "funding_data.db"
PRICE_DB = ROOT / "binance_data.db"
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
    """-> sorted (epoch_ms, close) for the requested series."""
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
    """Closest bar close within tol_ms — else None (never fabricate)."""
    if not series:
        return None
    ts = np.array([t for t, _ in series])
    i = int(np.argmin(np.abs(ts - ts_ms)))
    if abs(int(ts[i]) - ts_ms) <= tol_ms:
        return series[i][1]
    return None


def evaluate(fr, series, tol_ms, cost_bps, segments):
    """fr: [(funding_ms, rate)]; returns stats dict or None.

    DECOMPOSITION IS THE POINT: this is a single-leg, UNHEDGED
    funding-signed directional strategy — funding income and drift
    are reported separately because they are different mechanisms.
    A delta-neutral carry (perp vs spot) cannot be constructed from
    spot closes alone; what is measured here is "does fading the
    crowded side earn funding plus avoid adverse drift", NOT pure
    carry yield."""
    drifts, carries, nets, wins = [], [], [], []
    for i in range(len(fr) - 1):
        t0, f = fr[i]
        t1 = fr[i + 1][0]
        p0 = nearest_close(series, t0, tol_ms)
        p1 = nearest_close(series, t1, tol_ms)
        if not p0 or not p1:
            continue
        drift = math.log(p1 / p0)
        pos = -1.0 if f > 0 else 1.0      # short when funding positive
        signed_drift = drift * pos * 1e4  # bps earned by the position
        fund_bps = abs(f) * 1e4
        nets.append(fund_bps + signed_drift - cost_bps)
        drifts.append(signed_drift)
        carries.append(fund_bps)
        wins.append(nets[-1] > 0)
    n = len(nets)
    if n < 10:
        return None
    net = np.asarray(nets)
    drift_a = np.asarray(drifts)
    # chronological segments — a carry edge that only exists in one
    # regime is reported, not hidden
    seg_means = []
    for s in range(segments):
        chunk = net[int(n * s / segments):int(n * (s + 1) / segments)]
        seg_means.append(round(float(chunk.mean()), 3) if len(chunk) else None)
    sharpe = (net.mean() / net.std() * math.sqrt(n)
              if net.std() > 0 else 0.0)
    return {"windows": n,
            "funding_bps_per_window": round(float(np.mean(carries)), 3),
            "drift_bps_per_window": round(float(drift_a.mean()), 3),
            "cost_bps_per_window": cost_bps,
            "net_bps_per_window": round(float(net.mean()), 3),
            "net_total_bps": round(float(net.sum()), 1),
            "net_sharpe": round(float(sharpe), 3),
            "hit_rate": round(float(np.mean(wins)), 3),
            "segment_means_bps": seg_means,
            "mechanism": "unhedged funding-signed directional — "
                         "NOT delta-neutral carry"}


def verdict(stats: dict) -> str:
    """PASS requires the UNHEDGED strategy to clear cost+sharpe+segment
    gates — the record's decomposition shows how much of that is
    funding income vs directional drift. A PASS here means 'the
    funding-signed fade earned net of costs', never 'delta-neutral
    carry worked'."""
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
    ap.add_argument("--source", default="binance")
    ap.add_argument("--symbol", default="BTCUSDT",
                    help="funding_rates.symbol")
    ap.add_argument("--price-symbol", default="BTC",
                    help="market_data.symbol price leg")
    ap.add_argument("--tf", default="15m")
    ap.add_argument("--tol-min", type=float, default=30.0,
                    help="max bar-distance for timestamp alignment")
    ap.add_argument("--cost-bps", type=float, default=1.6)
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--funding-db", default=str(FUNDING_DB))
    ap.add_argument("--price-db", default=str(PRICE_DB))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    fr = load_funding(Path(args.funding_db), args.source, args.symbol)
    series = load_closes(Path(args.price_db), args.price_symbol, args.tf)
    rec = {"ts": datetime.now(timezone.utc).isoformat(),
           "spec": {"family": "funding_fade", "symbol": args.symbol,
                    "price_symbol": args.price_symbol, "tf": args.tf,
                    "source": args.source},
           "cost_bps": args.cost_bps,
           "caveats": ["spot closes as perp proxy — basis unmeasured",
                       "fixed per-window cost, not measured spread"]}
    stats = evaluate(fr, series, int(args.tol_min * 60_000),
                     args.cost_bps, args.segments)
    if stats is None:
        rec.update(verdict="REJECTED",
                   reason=f"insufficient aligned windows "
                          f"(funding prints={len(fr)}, bars={len(series)})")
        print(f"REJECTED  {rec['reason']}")
    else:
        v = verdict(stats)
        rec.update(verdict=v, stats=stats)
        print(f"{v:9s} funding_fade {args.symbol} vs {args.price_symbol}"
              f"@{args.tf} windows={stats['windows']} "
              f"fund={stats['funding_bps_per_window']:+.3f}bps/w "
              f"drift={stats['drift_bps_per_window']:+.3f}bps/w "
              f"net={stats['net_bps_per_window']:+.3f}bps/w "
              f"total={stats['net_total_bps']:+.1f}bps "
              f"sharpe={stats['net_sharpe']:+.2f} "
              f"segs={stats['segment_means_bps']}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"ledger -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
