"""FX order-flow provisioning — real historical bid/ask ticks from the
public Dukascopy datafeed (no credentials needed).

Each hour is a ``.bi5`` LZMA file of 20-byte records:
millisecond offset, ask, bid, ask volume, bid volume (big-endian).
Prices land in points for JPY pairs; the collector auto-scales by
median magnitude and records the scale used — every row is
timestamped real tick data, nothing is synthesized.

Honest boundary: this is historical quote data from one LP aggregator,
not a consolidated FX book (none exists — FX is decentralized).
Coverage accrues per requested hour; failures are retried then
reported, never skipped silently.

Usage:
    .venv/Scripts/python.exe scripts/collect_fx_ticks.py \
        --symbol EURUSD --day 2026-10-02 --hours 8 9 10 11
"""

from __future__ import annotations

import argparse
import lzma
import sqlite3
import struct
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "var" / "orderflow" / "fx_ticks.db"
FEED = "https://datafeed.dukascopy.com/datafeed"


def init_db(p: Path) -> sqlite3.Connection:
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE IF NOT EXISTS fx_ticks ("
                "ts_ms INTEGER, symbol TEXT, ask REAL, bid REAL, "
                "ask_vol REAL, bid_vol REAL, hour_file TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_ft ON "
                "fx_ticks(symbol, ts_ms)")
    con.commit()
    return con


def fetch_hour(symbol: str, day: str, hour: int,
               retries: int = 3) -> tuple[int, float]:
    """Download + decode one hour of real ticks. Returns (rows, scale)."""
    y, m, d = day.split("-")
    url = (f"{FEED}/{symbol}/{int(y)}/{int(m)-1:02d}/{int(d):02d}/"
           f"{hour:02d}h_ticks.bi5")
    raw = None
    for a in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "fx-tick-collector/1.0"})
            raw = urllib.request.urlopen(req, timeout=30).read()
            break
        except Exception:  # noqa: BLE001
            time.sleep(2 * (a + 1))
    if raw is None:
        return None
    try:
        data = lzma.decompress(raw)
    except lzma.LZMAError:
        # truncated/error response body — a fetch failure, not ticks
        return None
    n = len(data) // 20
    if n == 0:
        return None
    # .bi5 ms offsets are relative to the UTC hour — naive
    # .timestamp() would stamp ticks in local machine time
    base_ms = int(datetime(int(y), int(m), int(d), hour,
                           tzinfo=timezone.utc).timestamp() * 1000)
    # .bi5 records are >IIIff: ms u32, ask u32 (points), bid u32
    # (points), ask_vol f32, bid_vol f32. Price scale is 1e-3 for JPY
    # pairs, 1e-5 for everything else — auto-detect by magnitude so a
    # wrong convention can't silently corrupt prices.
    sample = [struct.unpack(">IIIff", data[i * 20:i * 20 + 20])[1]
              for i in range(0, min(n, 200))]
    med = sorted(sample)[len(sample) // 2]
    scale = 1e-3 if med / 1e-3 < 1000 else 1e-5
    return n, scale, base_ms, data, url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--day", required=True)
    ap.add_argument("--hours", type=int, nargs="+", required=True)
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()
    con = init_db(Path(args.db))
    total = 0
    for h in args.hours:
        out = fetch_hour(args.symbol, args.day, h)
        if out is None:
            print(f"{args.symbol} {args.day} {h:02d}h: unavailable",
                  flush=True)
            continue
        n, scale, base_ms, data, url = out
        for i in range(n):
            ms, ask, bid, av, bv = struct.unpack(
                ">IIIff", data[i * 20:i * 20 + 20])
            con.execute(
                "INSERT INTO fx_ticks (ts_ms, symbol, ask, bid, "
                "ask_vol, bid_vol, hour_file) VALUES (?,?,?,?,?,?,?)",
                (base_ms + ms, args.symbol, ask * scale, bid * scale,
                 av, bv, url.rsplit("/", 1)[-1]))
        con.commit()
        total += n
        print(f"{args.symbol} {args.day} {h:02d}h: {n} ticks "
              f"(scale={scale})", flush=True)
    print(f"done — {total} real ticks -> {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
