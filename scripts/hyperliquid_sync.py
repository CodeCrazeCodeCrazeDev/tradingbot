"""Hyperliquid candle sync — keyless public API, no credentials.

POSTs to https://api.hyperliquid.xyz/info (type=candleSnapshot) and
writes OHLCV into a sqlite table shaped exactly like market_data.db
so paper_runner / edge_baseline can replay it read-only.

    python scripts/hyperliquid_sync.py --coin BTC --timeframe 15m \
        --days 60 --db-path hl_data.db
"""

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

_API = "https://api.hyperliquid.xyz/info"
_TF = {"1m": "1m", "5m": "5m", "15m": "15m",
       "1h": "1h", "4h": "4h", "1d": "1d"}
_TF_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000,
          "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}
_UA = {"User-Agent": "alphaalgo-research/1.0",
       "Content-Type": "application/json"}


def _post(payload: dict, timeout: int = 30) -> bytes:
    req = urllib.request.Request(
        _API, data=json.dumps(payload).encode(),
        headers=_UA, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_candles(coin: str, tf: str, start_ms: int, end_ms: int):
    return json.loads(_post({
        "type": "candleSnapshot",
        "req": {"coin": coin, "interval": tf,
                "startTime": start_ms, "endTime": end_ms}}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coin", default="BTC")
    ap.add_argument("--timeframe", default="15m", choices=list(_TF))
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--db-path", default="hl_data.db")
    ap.add_argument("--symbol", default=None,
                    help="market_data symbol label; default = coin")
    args = ap.parse_args()

    sym = args.symbol or args.coin
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - args.days * 86_400_000

    con = sqlite3.connect(args.db_path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS market_data ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, "
        "symbol TEXT, timeframe TEXT, open REAL, high REAL, "
        "low REAL, close REAL, volume REAL)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_md ON "
        "market_data(symbol, timeframe, timestamp)")

    # paginate: API caps ~5k candles/response
    step_ms = _TF_MS[args.timeframe] * 4999
    cur, total, gaps = start_ms, 0, 0
    prev_ts = None
    while cur < end_ms:
        chunk_end = min(cur + step_ms, end_ms)
        try:
            candles = fetch_candles(args.coin, args.timeframe,
                                    cur, chunk_end)
        except Exception as e:
            print(f"chunk failed at {cur}: {e} — stopping")
            break
        if not candles:
            break
        rows = []
        for c in candles:
            ts_ms = int(c["t"])
            ts = time.strftime("%Y-%m-%dT%H:%M:%S+00:00",
                               time.gmtime(ts_ms / 1000))
            rows.append((ts, sym, args.timeframe,
                         float(c["o"]), float(c["h"]),
                         float(c["l"]), float(c["c"]),
                         float(c.get("v") or 0.0)))
            if prev_ts and ts_ms - prev_ts > _TF_MS[args.timeframe]:
                gaps += 1
            prev_ts = ts_ms
        con.executemany(
            "INSERT OR IGNORE INTO market_data"
            "(timestamp,symbol,timeframe,open,high,low,close,volume)"
            " VALUES(?,?,?,?,?,?,?,?)", rows)
        total += len(rows)
        cur = chunk_end
    con.commit()
    n = con.execute(
        "SELECT COUNT(*) FROM market_data WHERE symbol=? AND timeframe=?",
        (sym, args.timeframe)).fetchone()[0]
    con.close()
    print(f"{sym} {args.timeframe}: fetched {total}, stored {n} "
          f"rows, {gaps} gaps -> {args.db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
