#!/usr/bin/env python
"""Keyless perpetual funding-rate + mark/index ingestion -> funding_data.db.

Fulfils the open ``scout_claims`` data request (var/data_requests.json):
funding-carry specs need real perp funding history and mark/index to
test carry/fade claims — neither is in any local db today.

Sources (all public, no credentials):

- Binance USDⓈ-M ``fapi/v1/fundingRate`` — settled funding prints,
  paginated backwards by ``startTime`` (max 1000/call, ~3/day/symbol).
- Binance ``fapi/v1/premiumIndex`` — current mark/index/lastFundingRate
  snapshot (point-in-time, one row per run per symbol).
- Hyperliquid ``api.hyperliquid.xyz/info`` ``fundingHistory`` — hourly
  funding prints for HIP-3 style perps (keyless POST).

Nothing is synthesized: a source that fails is reported and skipped,
never back-filled with estimates. Re-runs are idempotent
(INSERT OR REPLACE on the natural key).

Usage:
    python scripts/collect_funding.py                      # all sources
    python scripts/collect_funding.py --sources binance --days 30
    python scripts/collect_funding.py --symbols BTCUSDT,ETHUSDT
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "funding_data.db"

_UA = {"User-Agent": "alphaalgo-funding-collector/1.0"}
_FAPI = "https://fapi.binance.com"
_HL_INFO = "https://api.hyperliquid.xyz/info"

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

SCHEMA = """
CREATE TABLE IF NOT EXISTS funding_rates (
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    funding_time INTEGER NOT NULL,   -- ms epoch of the funding event
    funding_rate REAL NOT NULL,      -- decimal (0.0001 = 1bp)
    mark_price REAL,
    index_price REAL,
    premium REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (source, symbol, funding_time)
);
CREATE TABLE IF NOT EXISTS premium_snapshots (
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    ts INTEGER NOT NULL,             -- ms epoch of the snapshot
    mark_price REAL,
    index_price REAL,
    last_funding_rate REAL,
    next_funding_time INTEGER,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (source, symbol, ts)
);
"""


def _get_json(url: str, payload: dict | None = None,
              timeout: float = 20.0):
    try:
        if payload is None:
            req = urllib.request.Request(url, headers=_UA)
        else:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(),
                headers={**_UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 — report, never fabricate
        print(f"  fetch failed {url[:80]}: {type(e).__name__}: {e}",
              file=sys.stderr)
        return None


def _now_ms() -> int:
    return int(time.time() * 1000)


def _fetched_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def collect_binance(con: sqlite3.Connection, symbols: list[str],
                     days: int) -> dict:
    """ fundingRate history (paginated) + premiumIndex snapshot."""
    stats = {"symbols": {}, "prints": 0, "snapshots": 0}
    start_ms = _now_ms() - days * 86_400_000
    for sym in symbols:
        got = 0
        cursor = start_ms
        # Page forward: fundingRate returns ascending from startTime;
        # step cursor past the newest print each call.
        for _ in range(40):  # hard bound: 40k prints/symbol max
            q = urllib.parse.urlencode(
                {"symbol": sym, "startTime": cursor, "limit": 1000})
            rows = _get_json(f"{_FAPI}/fapi/v1/fundingRate?{q}")
            if not rows:
                break
            for r in rows:
                con.execute(
                    "INSERT OR REPLACE INTO funding_rates VALUES "
                    "(?,?,?,?,?,?,?,?)",
                    ("binance", sym, int(r["fundingTime"]),
                     float(r["fundingRate"]), None, None, None,
                     _fetched_at()))
                got += 1
            cursor = int(rows[-1]["fundingTime"]) + 1
            if len(rows) < 1000:
                break
            time.sleep(0.15)  # be polite to the public endpoint
        stats["prints"] += got
        stats["symbols"][sym] = got

        pi = _get_json(f"{_FAPI}/fapi/v1/premiumIndex?"
                       + urllib.parse.urlencode({"symbol": sym}))
        if isinstance(pi, dict) and pi.get("symbol"):
            con.execute(
                "INSERT OR REPLACE INTO premium_snapshots VALUES "
                "(?,?,?,?,?,?,?,?)",
                ("binance", sym, _now_ms(),
                 num(pi.get("markPrice")),
                 num(pi.get("indexPrice")),
                 num(pi.get("lastFundingRate")),
                 int(pi["nextFundingTime"])
                 if pi.get("nextFundingTime") else None,
                 _fetched_at()))
            stats["snapshots"] += 1
        time.sleep(0.15)
    return stats


def collect_hyperliquid(con: sqlite3.Connection, coins: list[str],
                         days: int) -> dict:
    """ fundingHistory prints; coin names are bare (BTC not BTCUSDT)."""
    stats = {"coins": {}, "prints": 0}
    start_ms = _now_ms() - days * 86_400_000
    for coin in coins:
        rows = _get_json(_HL_INFO, payload={
            "type": "fundingHistory", "coin": coin,
            "startTime": start_ms})
        got = 0
        if isinstance(rows, list):
            for r in rows:
                con.execute(
                    "INSERT OR REPLACE INTO funding_rates VALUES "
                    "(?,?,?,?,?,?,?,?)",
                    ("hyperliquid", coin, int(r["time"]),
                     float(r["fundingRate"]),
                     None, None, num(r.get("premium")),
                     _fetched_at()))
                got += 1
        stats["prints"] += got
        stats["coins"][coin] = got if isinstance(rows, list) else "fetch_failed"
        time.sleep(0.15)
    return stats


def num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", default="binance,hyperliquid")
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                    help="Binance perp symbols")
    ap.add_argument("--hl-coins", default="BTC,ETH,SOL",
                    help="Hyperliquid coin names")
    ap.add_argument("--days", type=int, default=30,
                    help="history window to (re)fetch")
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.executescript(SCHEMA)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    coins = [c.strip().upper() for c in args.hl_coins.split(",") if c.strip()]
    results = {}
    if "binance" in args.sources:
        results["binance"] = collect_binance(con, symbols, args.days)
    if "hyperliquid" in args.sources:
        results["hyperliquid"] = collect_hyperliquid(con, coins, args.days)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM funding_rates").fetchone()[0]
    con.close()
    print(json.dumps({"db": args.db, "funding_rows": n,
                      "sources": results}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
