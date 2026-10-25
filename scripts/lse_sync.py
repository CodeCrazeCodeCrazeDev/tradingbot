"""Download OHLCV candles from London Strategic Edge into a local
SQLite store shaped exactly like market_data.db so the canonical
paper_runner can replay them read-only.

Requires the lse-data package (pip install lse-data) and a free API
key via LSE_API_KEY env var or --api-key. Provenance is kept clean by
writing to a dedicated lse_data.db rather than mixing into the MT5
store; pass --db-path lse_data.db to paper_runner to replay it.

    python scripts/lse_sync.py --symbol EURUSD --timeframe 15m \
        --start 2026-09-01 --end 2026-10-20

Timestamps are written as UTC ISO (LSE returns epoch/UTC). Volume is
whatever the venue reports — tick count for FX, shares/contracts for
equities/futures.
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_TF_MAP = {
    "1m": "M1", "3m": "M3", "5m": "M5", "15m": "M15", "30m": "M30",
    "1h": "H1", "4h": "H4", "1d": "D1", "1w": "W1", "1mo": "MO1",
    "1s": "S1", "5s": "S5", "15s": "S15", "30s": "S30",
}

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


def _norm_ts(raw) -> str:
    """LSE rows carry 'timestamp'/'time'/'t' as epoch s/ms or ISO."""
    from datetime import datetime, timezone
    if isinstance(raw, (int, float)):
        v = float(raw)
        if v > 1e12:
            v /= 1000.0
        return datetime.fromtimestamp(
            v, tz=timezone.utc).isoformat()
    s = str(raw).replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _norm_row(row: dict) -> tuple:
    """Map an LSE candle dict -> (ts, o, h, l, c, v). Raises on junk."""
    ts = row.get("timestamp", row.get("time", row.get("t")))
    o = row.get("open", row.get("o"))
    h = row.get("high", row.get("h"))
    l = row.get("low", row.get("l"))
    c = row.get("close", row.get("c"))
    v = row.get("volume", row.get("v", 0))
    if ts is None or c is None:
        raise ValueError(f"unrecognized row shape: {sorted(row)}")
    return (_norm_ts(ts), float(o), float(h), float(l),
            float(c), float(v or 0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbol", required=True,
                    help="LSE symbol, e.g. EURUSD, BTC/USD, AAPL")
    ap.add_argument("--timeframe", default="15m",
                    help="LSE tf: 1s..1mo (mapped to M15/H1/... internally)")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--api-key", default=os.environ.get("LSE_API_KEY"))
    ap.add_argument("--db-path", default=str(PROJECT_ROOT / "lse_data.db"))
    ap.add_argument("--market", default="forex",
                    help="LSE market collection for candles")
    args = ap.parse_args()

    if not args.api_key:
        print("LSE_API_KEY not set — register free at "
              "londonstrategicedge.com/api", file=sys.stderr)
        return 2

    from lse import LSE
    client = LSE(api_key=args.api_key)
    rows = client.candles(args.symbol, args.timeframe,
                          start=args.start, end=args.end)
    print(f"lse candles({args.symbol} {args.timeframe} "
          f"{args.start}..{args.end}): {len(rows)} rows")

    tf = _TF_MAP.get(args.timeframe, args.timeframe.upper())
    # Symbol stored canonically: 'EURUSD', 'BTC/USD' -> 'BTCUSD'
    sym = args.symbol.replace("/", "").upper()

    db = Path(args.db_path)
    con = sqlite3.connect(str(db))
    try:
        con.executescript(_SCHEMA)
        ins = skip = 0
        for r in rows:
            try:
                ts, o, h, l, c, v = _norm_row(r)
            except (ValueError, TypeError):
                skip += 1
                continue
            con.execute(
                "INSERT INTO market_data"
                " (timestamp, symbol, timeframe, open, high, low,"
                "  close, volume) VALUES (?,?,?,?,?,?,?,?)",
                (ts, sym, tf, o, h, l, c, v))
            ins += 1
        con.commit()
    finally:
        con.close()
    print(f"inserted {ins} bars into {db.name} "
          f"(skipped {skip} unparseable); symbol={sym} tf={tf}")
    print(f"replay with: python scripts/paper_runner.py --source db "
          f"--db-path {db.name} --symbol {sym} --timeframe {tf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
