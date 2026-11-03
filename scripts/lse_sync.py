"""Download OHLCV candles from London Strategic Edge v3 into a local
SQLite store shaped exactly like market_data.db so the canonical
paper_runner can replay them read-only.

Calls GET https://download.londonstrategicedge.com/v3/candles directly
(format=csv) — the pip `lse-data` client still targets the retired
/vault endpoints, so we use plain HTTPS + X-API-Key. Free key from
londonstrategicedge.com/data via LSE_API_KEY or --api-key.

Writes to a dedicated lse_data.db so LSE provenance stays distinct
from the MT5 store; replay with paper_runner --db-path lse_data.db.
LSE timestamps are UTC — no broker-tz de-offset needed.

    python scripts/lse_sync.py --symbol EURUSD --timeframe 15m \
        --start 2026-08-01 --end 2026-10-24
"""

import argparse
import csv
import io
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API = "https://download.londonstrategicedge.com/v3/candles"

_TF_MAP = {
    "1m": "M1", "3m": "M3", "5m": "M5", "15m": "M15", "30m": "M30",
    "1h": "H1", "4h": "H4", "1d": "D1", "1w": "W1", "1mo": "MO1",
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


def _api_symbol(symbol: str, market: str) -> str:
    """v3 spells forex pairs BASE_QUOTE (EUR_USD). Accept 'EURUSD',
    'EUR/USD' or 'EUR_USD' and emit the API form."""
    s = symbol.upper().replace("/", "_")
    if market == "forex" and "_" not in s and len(s) == 6:
        s = f"{s[:3]}_{s[3:]}"
    return s


def _fetch_csv(api_key: str, market: str, symbol: str,
               timeframe: str, start: str, end: str) -> str:
    qs = (f"market={market}&symbol={_api_symbol(symbol, market)}"
          f"&timeframe={timeframe}"
          f"&from={start}&to={end}&format=csv&data=candles")
    req = urllib.request.Request(
        f"{API}?{qs}", headers={"X-API-Key": api_key,
                                "User-Agent": "lse-sync/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", "replace")
    if body.lstrip().startswith("{"):
        # JSON refusal -> surface the code/message verbatim
        print(f"LSE refused: {body[:400]}", file=sys.stderr)
        sys.exit(1)
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbol", required=True,
                    help="LSE symbol, e.g. EURUSD, BTC/USD, AAPL")
    ap.add_argument("--market", default="forex",
                    help="LSE market folder: forex/crypto/us_stocks/...")
    ap.add_argument("--timeframe", default="15m",
                    help="LSE tf: 1s..1mo (mapped to M15/H1/...)")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--api-key", default=os.environ.get("LSE_API_KEY"))
    ap.add_argument("--db-path", default=str(PROJECT_ROOT / "lse_data.db"))
    args = ap.parse_args()

    if not args.api_key:
        print("LSE_API_KEY not set — register free at "
              "londonstrategicedge.com/data", file=sys.stderr)
        return 2

    body = _fetch_csv(args.api_key, args.market, args.symbol,
                      args.timeframe, args.start, args.end)
    rows = list(csv.DictReader(io.StringIO(body)))
    print(f"lse candles({args.symbol} {args.timeframe} "
          f"{args.start}..{args.end}): {len(rows)} rows")

    tf = _TF_MAP.get(args.timeframe, args.timeframe.upper())
    sym = args.symbol.replace("/", "").upper()

    db = Path(args.db_path)
    con = sqlite3.connect(str(db))
    try:
        con.executescript(_SCHEMA)
        ins = skip = 0
        for r in rows:
            try:
                # v3 CSV: "time","open","high","low","close","volume"
                # (+ optional "trades"). Time is UTC 'YYYY-MM-DD HH:MM:SS'.
                ts = r["time"].strip().replace(" ", "T") + "+00:00"
                # Forex rows report volume=0; 'trades' is the tick
                # count — same semantics as MT5 tick volume.
                vol = float(r.get("volume") or 0) or \
                    float(r.get("trades") or 0)
                con.execute(
                    "INSERT INTO market_data"
                    " (timestamp, symbol, timeframe, open, high, low,"
                    "  close, volume) VALUES (?,?,?,?,?,?,?,?)",
                    (ts, sym, tf, float(r["open"]), float(r["high"]),
                     float(r["low"]), float(r["close"]), vol))
                ins += 1
            except (KeyError, TypeError, ValueError):
                skip += 1
        con.commit()
    finally:
        con.close()
    print(f"inserted {ins} bars into {db.name} "
          f"(skipped {skip} unparseable); symbol={sym} tf={tf}")
    print(f"replay with: python scripts/paper_runner.py --source db "
          f"--db-path {db.name} --symbol {sym} --timeframe {tf} "
          f"--broker-tz-offset 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
