#!/usr/bin/env python
"""Download US-equity OHLCV candles into a local SQLite store shaped
exactly like market_data.db so the canonical paper_runner (and the
OpportunityScanner / rotating universe) can replay them read-only.

Keyless source: Yahoo Finance v8 chart endpoint — no API key, no
credentials stored. Real exchange data; timestamps are UTC epoch, so
no broker-tz de-offset is needed (--broker-tz-offset 0). Yahoo caps
intraday history (15m ~= 60d, 1h ~= 730d, 1d = full) — requests are
honestly bounded by what the endpoint returns.

Writes to us_stocks.db so equity provenance stays distinct.

    python scripts/stock_sync.py --symbols AAPL,MSFT,NVDA --timeframe 15m
    python scripts/stock_sync.py --symbols SPY,QQQ --timeframe 1h --days 300
"""

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"

_TF_MAP = {"1m": "M1", "5m": "M5", "15m": "M15", "30m": "M30",
           "1h": "H1", "4h": "H4", "1d": "D1", "1wk": "W1"}
_RANGE_DAYS = {"1m": 7, "5m": 60, "15m": 60, "30m": 60,
               "1h": 730, "1d": 3650, "1wk": 3650}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open REAL, high REAL, low REAL, close REAL, volume REAL
);
CREATE INDEX IF NOT EXISTS idx_md_st ON market_data(symbol, timeframe, timestamp);
"""


def _fetch_chart(symbol: str, interval: str, days: int) -> dict:
    url = (API.format(sym=symbol)
           + f"?interval={interval}&range={days}d&includePrePost=false")
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _rows(payload: dict, symbol: str, tf: str):
    res = (payload.get("chart") or {}).get("result") or []
    if not res:
        err = (payload.get("chart") or {}).get("error")
        raise SystemExit(f"{symbol}: no chart result ({err})")
    ts = res[0].get("timestamp") or []
    q = ((res[0].get("indicators") or {}).get("quote") or [{}])[0]
    opens, highs, lows = q.get("open") or [], q.get("high") or [], q.get("low") or []
    closes, vols = q.get("close") or [], q.get("volume") or []
    out = []
    for i, t in enumerate(ts):
        try:
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            if o is None or h is None or l is None or c is None:
                continue  # half-formed bar (holidays/market gaps)
            iso = datetime.fromtimestamp(
                t, tz=timezone.utc).isoformat()
            v = vols[i] if i < len(vols) and vols[i] is not None else 0.0
            out.append((iso, symbol, tf, float(o), float(h),
                        float(l), float(c), float(v)))
        except (IndexError, TypeError, ValueError):
            continue
    return out


def _norm_symbol(sym: str) -> str:
    """Yahoo ticker -> canonical instrument name: EURUSD=X->EURUSD,
    JPY=X->USDJPY (yahoo JPY=X is USD/JPY), BTC-USD->BTC."""
    s = sym.upper().replace("/", "")
    if s.endswith("=X"):
        base = s[:-2]
        return f"USD{base}" if len(base) == 3 else base
    if s.endswith("-USD"):
        return s[:-4]
    return s.replace("=", "").replace("-", "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", required=True,
                    help="comma-separated yahoo tickers, e.g. "
                         "AAPL,MSFT or EURUSD=X,JPY=X,BTC-USD")
    ap.add_argument("--timeframe", default="15m",
                    help="yahoo interval: 1m/5m/15m/30m/1h/1d/1wk")
    ap.add_argument("--days", type=int, default=0,
                    help="history window in days (default = endpoint max "
                         "for the interval)")
    ap.add_argument("--db-path",
                    default=str(PROJECT_ROOT / "us_stocks.db"))
    args = ap.parse_args()

    tf = _TF_MAP.get(args.timeframe, args.timeframe.upper())
    days = args.days or _RANGE_DAYS.get(args.timeframe, 60)

    db = Path(args.db_path)
    con = sqlite3.connect(str(db))
    try:
        con.executescript(_SCHEMA)
        total = 0
        for _y in [s.strip() for s in args.symbols.split(",") if s.strip()]:
            sym = _norm_symbol(_y)
            payload = _fetch_chart(_y, args.timeframe, days)
            rows = _rows(payload, sym, tf)
            # Idempotent re-sync: replace the overlapping window rather
            # than duplicating bars.
            if rows:
                con.execute(
                    "DELETE FROM market_data WHERE symbol=? AND "
                    "timeframe=? AND timestamp>=?",
                    (sym, tf, rows[0][0]))
            con.executemany(
                "INSERT INTO market_data (timestamp, symbol, timeframe,"
                " open, high, low, close, volume)"
                " VALUES (?,?,?,?,?,?,?,?)", rows)
            con.commit()
            span = f"{rows[0][0][:10]}..{rows[-1][0][:10]}" if rows else "empty"
            print(f"{sym} {tf}: {len(rows)} bars ({span})")
            total += len(rows)
            time.sleep(1.0)  # polite pacing on a free endpoint
    finally:
        con.close()
    print(f"inserted {total} bars into {db.name}")
    print(f"replay: python scripts/paper_runner.py --source db "
          f"--universe '{db.name}:AAPL,{args.symbols}:M15' "
          f"--broker-tz-offset 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
