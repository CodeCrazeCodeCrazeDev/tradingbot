#!/usr/bin/env python
"""Keyless limit-order-book snapshot collector -> lob_data.db.

Fulfils the §L5 data-capability gap: ~20/43 anchored-but-unextracted
scout records are microstructure methods (order-flow imbalance, queue
imbalance, market impact). OHLCV cannot evaluate them; top-of-book
snapshots can.

Sources (all public, no credentials):

- Binance USDⓈ-M ``fapi/v1/depth?limit=20`` — current book snapshot
  (bids/asks price+qty). No historical endpoint exists: this builds a
  time series FORWARD, one snapshot per symbol per run.
- Hyperliquid ``api.hyperliquid.xyz/info`` ``l2Book`` — same shape via
  keyless POST (levels[0]=bids, levels[1]=asks of {px,sz,n}).

Each row stores the RAW top-20 levels as JSON so future methods can
recompute features at any depth band without recollecting — snapshots
are the scarce resource. Convenience aggregates (mid, spread_bps,
10bps-band depth imbalance) are precomputed alongside.

Nothing is synthesized: a venue that fails is reported and skipped.
Re-runs are append-safe (PRIMARY KEY on source+symbol+ts).

Cadence matters: run periodically (e.g. every 15–60 min) — evaluators
need a few hundred snapshots per series before verdicts are possible.
Early runs honestly report ``insufficient_snapshots``.

Usage:
    python scripts/collect_lob.py                     # all sources
    python scripts/collect_lob.py --sources binance
    python scripts/collect_lob.py --loop 60 --count 30  # 30 runs, 60s apart
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
DB = ROOT / "lob_data.db"

_UA = {"User-Agent": "alphaalgo-lob-collector/1.0"}
_FAPI = "https://fapi.binance.com"
_HL_INFO = "https://api.hyperliquid.xyz/info"

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DEFAULT_HL_COINS = ("BTC", "ETH", "SOL")
LEVELS = 20
BAND_BPS = 10.0  # canonical stored imbalance band

SCHEMA = """
CREATE TABLE IF NOT EXISTS lob_snapshots (
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    ts INTEGER NOT NULL,            -- ms epoch (venue time if given)
    best_bid REAL, best_ask REAL, mid REAL, spread_bps REAL,
    bid_depth_10bps REAL, ask_depth_10bps REAL, imbalance_10bps REAL,
    levels INTEGER,
    book_json TEXT,               -- {"bids":[[px,qty]..],"asks":[[px,qty]..]}
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


def _fetched_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_ms() -> int:
    return int(time.time() * 1000)


def depth_in_band(levels: list, mid: float, side: str,
                  band_bps: float) -> float:
    """Total qty within band_bps of mid. side='bid'|'ask'."""
    if not mid:
        return 0.0
    lo, hi = mid * (1 - band_bps / 1e4), mid * (1 + band_bps / 1e4)
    tot = 0.0
    for px, qty in levels:
        if side == "bid" and px >= lo and px <= mid:
            tot += qty
        elif side == "ask" and px <= hi and px >= mid:
            tot += qty
    return tot


def aggregates(bids: list, asks: list):
    """(mid, spread_bps, bid_d, ask_d, imb) or None if book is empty."""
    if not bids or not asks:
        return None
    bb, ba = bids[0][0], asks[0][0]
    if bb <= 0 or ba <= bb:
        return None
    mid = (bb + ba) / 2
    spread_bps = (ba - bb) / mid * 1e4
    bd = depth_in_band(bids, mid, "bid", BAND_BPS)
    ad = depth_in_band(asks, mid, "ask", BAND_BPS)
    imb = (bd - ad) / (bd + ad) if (bd + ad) > 0 else 0.0
    return mid, spread_bps, bd, ad, imb


def insert_snapshot(con, source: str, symbol: str, ts: int,
                    bids: list, asks: list) -> bool:
    agg = aggregates(bids, asks)
    if agg is None:
        return False
    mid, spread_bps, bd, ad, imb = agg
    con.execute(
        "INSERT OR REPLACE INTO lob_snapshots VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (source, symbol, int(ts), bids[0][0], asks[0][0], mid,
         spread_bps, bd, ad, imb, max(len(bids), len(asks)),
         json.dumps({"bids": bids, "asks": asks}), _fetched_at()))
    return True


def collect_binance(con: sqlite3.Connection, symbols: list[str]) -> dict:
    stats = {"symbols": {}}
    for sym in symbols:
        q = urllib.parse.urlencode({"symbol": sym, "limit": LEVELS})
        r = _get_json(f"{_FAPI}/fapi/v1/depth?{q}")
        ok = False
        if isinstance(r, dict) and r.get("bids") and r.get("asks"):
            bids = [[float(p), float(q2)] for p, q2 in r["bids"]]
            asks = [[float(p), float(q2)] for p, q2 in r["asks"]]
            ok = insert_snapshot(con, "binance", sym, _now_ms(),
                                 bids, asks)
        stats["symbols"][sym] = "ok" if ok else "fetch_failed"
        time.sleep(0.15)
    return stats


def collect_hyperliquid(con: sqlite3.Connection, coins: list[str]) -> dict:
    stats = {"coins": {}}
    for coin in coins:
        r = _get_json(_HL_INFO, payload={"type": "l2Book", "coin": coin})
        ok = False
        if isinstance(r, dict) and r.get("levels"):
            lv = r["levels"]
            if len(lv) == 2 and lv[0] and lv[1]:
                bids = [[float(x["px"]), float(x["sz"])]
                        for x in lv[0][:LEVELS]]
                asks = [[float(x["px"]), float(x["sz"])]
                        for x in lv[1][:LEVELS]]
                ts = int(r.get("time") or _now_ms())
                ok = insert_snapshot(con, "hyperliquid", coin, ts,
                                     bids, asks)
        stats["coins"][coin] = "ok" if ok else "fetch_failed"
        time.sleep(0.15)
    return stats


def load_lob(db: Path, source: str, symbol: str):
    """-> sorted [(ts_ms, mid, spread_bps, book_dict)]."""
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT ts, mid, spread_bps, book_json FROM lob_snapshots "
            "WHERE source=? AND symbol=? ORDER BY ts",
            (source, symbol)).fetchall()
    finally:
        con.close()
    out = []
    for ts, mid, sp, bj in rows:
        try:
            book = json.loads(bj) if bj else {}
        except (TypeError, ValueError):
            book = {}
        out.append((int(ts), float(mid), float(sp or 0.0), book))
    return out


def run_once(con: sqlite3.Connection, sources: list[str],
             symbols: list[str], coins: list[str]) -> dict:
    results = {}
    if "binance" in sources:
        results["binance"] = collect_binance(con, symbols)
    if "hyperliquid" in sources:
        results["hyperliquid"] = collect_hyperliquid(con, coins)
    con.commit()
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", default="binance,hyperliquid")
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                    help="Binance perp symbols")
    ap.add_argument("--hl-coins", default=",".join(DEFAULT_HL_COINS),
                    help="Hyperliquid coin names")
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--loop", type=int, default=0,
                    help="seconds between runs; 0 = single pass")
    ap.add_argument("--count", type=int, default=1,
                    help="runs when --loop set")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.executescript(SCHEMA)
    symbols = [s.strip().upper() for s in args.symbols.split(",")
               if s.strip()]
    coins = [c.strip().upper() for c in args.hl_coins.split(",")
             if c.strip()]
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    runs = args.count if args.loop else 1
    last = {}
    for i in range(runs):
        last = run_once(con, sources, symbols, coins)
        print(json.dumps({"run": i + 1, "of": runs,
                          "sources": last}, default=str))
        if i < runs - 1:
            time.sleep(args.loop)
    n = con.execute("SELECT COUNT(*) FROM lob_snapshots").fetchone()[0]
    con.close()
    print(json.dumps({"db": args.db, "lob_rows": n}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
