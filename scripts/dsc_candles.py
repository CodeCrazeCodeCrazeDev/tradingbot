#!/usr/bin/env python
"""Dukascopy tick feed -> mid-price candles + measured spreads.

Second FX venue for the cross-venue edge gate: MT5 bars alone cannot
satisfy edge_gate's >=2-venue requirement, and close-only bars cannot
measure the real spread an entry pays. This syncs the public .bi5 tick
feed (same decoder as scripts/collect_fx_ticks.py), aggregates mid-
price OHLC per timeframe into the canonical market_data schema, and
records per-candle measured spread stats (mean/p90 in bps) that
edge_features.py uses as the cost model.

Honest boundary: one LP aggregator's feed, mid-price candles (neither
side is executable), volume column = tick count not contracts. Ticks
are aggregated in memory and not persisted — disk stays bounded.

Usage:
    python scripts/dsc_candles.py --symbol EURUSD --days 30 \
        --timeframes M15,H1
    python scripts/edge_gate.py --combos \
        "market_data.db:EURUSD:M15,dsc_data.db:EURUSD:M15"
"""

from __future__ import annotations

import argparse
import sqlite3
import struct
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.collect_fx_ticks import fetch_hour  # noqa: E402

DB = ROOT / "dsc_data.db"
TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30,
              "H1": 60, "H4": 240, "D1": 1440}


def init_db(p: Path) -> sqlite3.Connection:
    con = sqlite3.connect(p)
    con.execute(
        "CREATE TABLE IF NOT EXISTS market_data ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, "
        "symbol TEXT, timeframe TEXT, open REAL, high REAL, "
        "low REAL, close REAL, volume REAL)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_md ON "
        "market_data(symbol, timeframe, timestamp)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS dsc_spread ("
        "timestamp TEXT, symbol TEXT, timeframe TEXT, "
        "mean_spread_bps REAL, p90_spread_bps REAL, ticks INTEGER, "
        "PRIMARY KEY (symbol, timeframe, timestamp))")
    con.commit()
    return con


class _Bucket:
    __slots__ = ("o", "h", "l", "c", "n", "spreads")

    def __init__(self, mid, spread_bps):
        self.o = self.h = self.l = self.c = mid
        self.n = 1
        self.spreads = [spread_bps]

    def add(self, mid, spread_bps):
        self.h = max(self.h, mid)
        self.l = min(self.l, mid)
        self.c = mid
        self.n += 1
        self.spreads.append(spread_bps)


def aggregate_ticks(data: bytes, n: int, scale: float, base_ms: int,
                    tf_min: int, buckets: dict):
    """Stream 20-byte .bi5 records into candle buckets keyed by
    bucket-open ms. buckets persists across hour files."""
    span_ms = tf_min * 60_000
    for i in range(n):
        ms, ask, bid, _av, _bv = struct.unpack(
            ">IIIff", data[i * 20:i * 20 + 20])
        a, b = ask * scale, bid * scale
        mid = (a + b) / 2.0
        if mid <= 0:
            continue
        spr_bps = max(0.0, (a - b) / mid * 1e4)
        key = (base_ms + ms) // span_ms * span_ms
        bk = buckets.get(key)
        if bk is None:
            buckets[key] = _Bucket(mid, spr_bps)
        else:
            bk.add(mid, spr_bps)


def _p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(0.9 * len(xs)))]


def flush_buckets(con, buckets, symbol, tf_name, min_ticks=5):
    rows = []
    for key_ms, bk in sorted(buckets.items()):
        if bk.n < min_ticks:
            continue
        ts = datetime.fromtimestamp(
            key_ms / 1000.0, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00")
        rows.append((ts, symbol, tf_name, bk.o, bk.h, bk.l, bk.c,
                     float(bk.n),
                     sum(bk.spreads) / len(bk.spreads),
                     _p90(bk.spreads), bk.n))
    for r in rows:
        con.execute(
            "DELETE FROM market_data WHERE symbol=? AND timeframe=? "
            "AND timestamp=?", (r[0], r[1], r[2]))
        con.execute(
            "INSERT INTO market_data (timestamp, symbol, timeframe,"
            " open, high, low, close, volume) "
            "VALUES (?,?,?,?,?,?,?,?)", r[:8])
        con.execute(
            "INSERT OR REPLACE INTO dsc_spread (timestamp, symbol,"
            " timeframe, mean_spread_bps, p90_spread_bps, ticks) "
            "VALUES (?,?,?,?,?,?)",
            (r[0], r[1], r[2], r[8], r[9], r[10]))
    con.commit()
    return len(rows)


def sync(symbol: str, day0: str, days: int, timeframes, db_path: str,
         polite_s: float = 1.0) -> dict:
    con = init_db(Path(db_path))
    report = {"symbol": symbol, "candles": {}, "missing_hours": 0,
              "days_empty": []}
    buckets = {tf: {} for tf in timeframes}
    d0 = datetime.strptime(day0, "%Y-%m-%d").date()
    for k in range(days):
        d = d0 + timedelta(days=k)
        day_str = d.isoformat()
        got = 0
        for hour in range(24):
            out = fetch_hour(symbol, day_str, hour, retries=2)
            if out is None:
                report["missing_hours"] += 1
                continue
            n, scale, base_ms, data, _url = out
            got += 1
            for tf in timeframes:
                aggregate_ticks(data, n, scale, base_ms,
                                TF_MINUTES[tf], buckets[tf])
            time.sleep(polite_s)
        if got == 0:
            report["days_empty"].append(day_str)
            continue
        for tf in timeframes:
            # flush completed buckets; keep the last (possibly partial)
            # bucket in memory so a candle spanning the day seam is not
            # split into two half-rows
            keys = sorted(buckets[tf])
            keep = keys[-1] if keys else None
            done = {kk: v for kk, v in buckets[tf].items()
                    if kk != keep}
            n_rows = flush_buckets(con, done, symbol, tf)
            report["candles"][tf] = (report["candles"].get(tf, 0)
                                     + n_rows)
            buckets[tf] = ({keep: buckets[tf][keep]}
                           if keep is not None else {})
        print(f"{day_str}: {got}/24 hours", flush=True)
    for tf in timeframes:
        report["candles"][tf] = (report["candles"].get(tf, 0) +
                                 flush_buckets(con, buckets[tf],
                                               symbol, tf))
    con.close()
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--end-date", default=None,
                    help="YYYY-MM-DD; default = yesterday UTC (today's "
                         "partial day is never synced)")
    ap.add_argument("--timeframes", default="M15,H1")
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--polite", type=float, default=1.0,
                    help="seconds between hour-file requests — the "
                         "feed 429s aggressive polling")
    args = ap.parse_args()

    end = (datetime.strptime(args.end_date, "%Y-%m-%d").date()
           if args.end_date else
           (datetime.now(timezone.utc).date() - timedelta(days=1)))
    start = end - timedelta(days=args.days - 1)
    tfs = [t.strip().upper() for t in args.timeframes.split(",")]
    bad = [t for t in tfs if t not in TF_MINUTES]
    if bad:
        print(f"unknown timeframes: {bad} (have {sorted(TF_MINUTES)})")
        return 2
    print(f"{args.symbol} {start} -> {end} {tfs} -> {args.db}")
    rep = sync(args.symbol, start.isoformat(), args.days, tfs,
               args.db, polite_s=args.polite)
    print(f"candles: {rep['candles']}  "
          f"missing_hours={rep['missing_hours']}  "
          f"empty_days={len(rep['days_empty'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
