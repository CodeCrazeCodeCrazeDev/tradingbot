"""Order-flow collector — provisions the one data class the
falsification baseline proved absent.

Pulls real Binance public endpoints (no API key needed):

- ``/api/v3/depth`` — top-N order-book snapshots (bids + asks)
- ``/api/v3/aggTrades`` — real executed trades since the last poll
  (incremental via ``fromId``, deduplicated on aggregate trade id)

Writes ``var/orderflow/orderflow.db``. Bounded by design: run N cycles
then exit — schedule it (cron/Task Scheduler) to accrue coverage.
Honest boundary: public APIs serve no order-book *history*, so depth
coverage starts accruing from first run; nothing is backfilled or
simulated.

Usage:
    .venv/Scripts/python.exe scripts/collect_orderflow.py \
        --symbols BTCUSDT ETHUSDT --cycles 5 --interval 10 --depth 20
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "var" / "orderflow"
DB_PATH = DB_DIR / "orderflow.db"
BASE = "https://api.binance.com/api/v3"


def init_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS book_snapshots ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, "
        "symbol TEXT, last_update_id INTEGER, "
        "bids_json TEXT, asks_json TEXT)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS agg_trades ("
        "agg_id INTEGER PRIMARY KEY, ts_ms INTEGER, symbol TEXT, "
        "price REAL, qty REAL, is_buyer_maker INTEGER)")
    con.commit()
    return con


def _get(url: str) -> object:
    req = urllib.request.Request(
        url, headers={"User-Agent": "orderflow-collector/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def snapshot_book(con: sqlite3.Connection, symbol: str,
                  depth: int) -> int:
    d = _get(f"{BASE}/depth?symbol={symbol}&limit={depth}")
    con.execute(
        "INSERT INTO book_snapshots (ts_ms, symbol, last_update_id, "
        "bids_json, asks_json) VALUES (?,?,?,?,?)",
        (d.get("T") or int(time.time() * 1000), symbol,
         d["lastUpdateId"], json.dumps(d["bids"]),
         json.dumps(d["asks"])))
    return 1


def collect_trades(con: sqlite3.Connection, symbol: str) -> int:
    row = con.execute(
        "SELECT MAX(agg_id) FROM agg_trades WHERE symbol=?",
        (symbol,)).fetchone()
    last = row[0]
    url = f"{BASE}/aggTrades?symbol={symbol}&limit=500"
    if last:
        url += f"&fromId={last + 1}"
    trades = _get(url)
    n = 0
    for t in trades:
        con.execute(
            "INSERT OR IGNORE INTO agg_trades (agg_id, ts_ms, symbol, "
            "price, qty, is_buyer_maker) VALUES (?,?,?,?,?,?)",
            (t["a"], t["T"], symbol, t["p"], t["q"],
             1 if t["m"] else 0))
        n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT"])
    ap.add_argument("--cycles", type=int, default=5)
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()
    con = init_db(Path(args.db))
    total_books = total_trades = 0
    try:
        for cyc in range(1, args.cycles + 1):
            for sym in args.symbols:
                total_books += snapshot_book(con, sym, args.depth)
                total_trades += collect_trades(con, sym)
            con.commit()
            print(f"cycle {cyc}/{args.cycles}: books={total_books} "
                  f"trades={total_trades}", flush=True)
            if cyc < args.cycles:
                time.sleep(args.interval)
    finally:
        con.close()
    print(f"done — {args.db}: {total_books} book snapshots, "
          f"{total_trades} agg trades")
    return 0


if __name__ == "__main__":
    sys.exit(main())
