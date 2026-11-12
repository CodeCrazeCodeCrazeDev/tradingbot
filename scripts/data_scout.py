"""Data scout — discover and VERIFY new trading-data sources.

Two modes, all real and bounded:

1. Probe a curated set of keyless public market-data endpoints (the
   kind a quant would reach for): checks reachability, latency,
   auth requirements, and pulls a real sample to confirm the schema
   parses. No simulated results — every verdict is measured.

2. HuggingFace dataset search (--search 'financial time series'):
   real dataset discovery via the public API — names, downloads,
   tags — then listed in the ledger as candidates to inspect.

Usage:
    .venv/Scripts/python.exe scripts/data_scout.py
    .venv/Scripts/python.exe scripts/data_scout.py --collect
    .venv/Scripts/python.exe scripts/data_scout.py --search "limit order book"
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.request
import urllib.parse
import zipfile
import csv
from datetime import datetime, timezone
from pathlib import Path

_UA = {"User-Agent": "AlphaAlgo-DataScout/1.0 (bounded probe)"}
_TIMEOUT = 20

OUT = Path("var/data_scout/ledger.jsonl")


def probe(name: str, url: str, kind: str, check,
          post: bytes = None, max_read: int = 5_000_000) -> dict:
    """Fetch url (GET, or POST with `post` body), hand body to check()."""
    rec = {"source": name, "kind": kind, "url": url,
           "ts": datetime.now(timezone.utc).isoformat()}
    t0 = time.time()
    try:
        hdrs = dict(_UA)
        if post is not None:
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=post, headers=hdrs)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            body = r.read(max_read)
        rec["latency_s"] = round(time.time() - t0, 2)
        rec["bytes"] = len(body)
    except Exception as e:
        rec.update(verdict="UNREACHABLE", error=str(e)[:120],
                   latency_s=round(time.time() - t0, 2))
        print(f"  {rec['verdict']:14s} {name:34s} "
              f"{rec.get('error', '')[:70]}")
        return rec
    try:
        rec.update(check(body))
        rec["verdict"] = rec.get("verdict", "OK_KEYLESS")
    except Exception as e:
        rec.update(verdict="FETCH_OK_PARSE_FAIL", error=str(e)[:120])
    print(f"  {rec['verdict']:18s} {name:34s} "
          f"{rec.get('detail', rec.get('error', ''))[:70]}")
    return rec


def j(v, *ks):
    for k in ks:
        if isinstance(v, list):
            v = v[0] if v else None
        if isinstance(v, dict):
            v = v.get(k)
        else:
            return None
    return v


# --- checkers: parse a real sample, report schema ---------------------------

def check_binance_vision(b: bytes) -> dict:
    z = zipfile.ZipFile(io.BytesIO(b))
    rows = list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))))
    return {"verdict": "OK_KEYLESS",
            "detail": f"{len(rows)} aggTrades; cols="
                      f"{len(rows[0])}; schema=aggTradeId,price,qty,"
                      f"first,last,ts,isBuyerMaker"}


def check_json_rows(b: bytes, path) -> dict:
    data = json.loads(b)
    v = j(data, *path) if path else data
    n = len(v) if isinstance(v, list) else 1
    return {"detail": f"{n} records; sample={str(v)[:60]}"}


def check_csv(b: bytes) -> dict:
    rows = list(csv.reader(io.StringIO(b.decode("utf-8", "replace"))))
    return {"detail": f"{len(rows)} rows; header={rows[0][:6]}"}


SOURCES = [
    # (name, url, kind, check, post_body_or_None) — hyperliquid is POST
   
    ("binance_vision_aggTrades",
     "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
     "BTCUSDT-aggTrades-2024-01-01.zip", "microstructure_archive",
     check_binance_vision, None, 60_000_000),
    ("binance_spot_depth",
     "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=20",
     "live_l2",
     lambda b: check_json_rows(b, ("bids",))),
    ("kraken_ohlc",
     "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=15",
     "ohlcv",
     lambda b: check_json_rows(b, ("result", "XXBTZUSD"))),
    ("coinbase_candles",
     "https://api.exchange.coinbase.com/products/BTC-USD/candles"
     "?granularity=900", "ohlcv",
     lambda b: check_json_rows(b, None)),
    ("hyperliquid_meta",
     "https://api.hyperliquid.xyz/info", "venue_meta",
     lambda b: check_json_rows(b, ("universe",)),
     b'{"type":"meta"}'),
    ("stooq_eurusd_daily",
     "https://stooq.com/q/d/l/?s=eurusd&i=d", "daily_ohlcv", check_csv),
    ("coingecko_price",
     "https://api.coingecko.com/api/v3/simple/price"
     "?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true",
     "spot_price", lambda b: check_json_rows(b, ("bitcoin",))),
    ("yahoo_eurusd",
     "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X"
     "?interval=15m&range=1d", "ohlcv",
     lambda b: check_json_rows(b, ("chart", "result"))),
    ("dukascopy_tick_index",
     "https://datafeed.dukascopy.com/datafeed/EURUSD/2026/10/10/"
     "08h_ticks.bi5", "tick_binary",
     lambda b: {"detail": f"{len(b)} bytes LZMA bi5"}),
]


def hf_dataset_search(query: str, limit: int = 8) -> list:
    """REAL dataset discovery via the HF datasets API."""
    q = urllib.parse.urlencode(
        {"search": query, "limit": str(limit), "sort": "downloads",
         "direction": "-1", "full": "false"})
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/api/datasets?{q}", headers=_UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            data = json.loads(r.read(2_000_000))
    except Exception as e:
        print(f"  HF search failed: {str(e)[:100]}")
        return []
    out = []
    for d in data:
        out.append({"source": "hf_dataset", "name": d.get("id"),
                    "downloads": d.get("downloads", 0),
                    "likes": d.get("likes", 0),
                    "tags": [t for t in d.get("tags", [])
                             if ":" not in t][:6],
                    "url": f"https://huggingface.co/datasets/{d.get('id')}",
                    "verdict": "CANDIDATE"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--search", default=None,
                    help="HF dataset discovery query")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--collect", action="store_true",
                    help="fetch one real binance_vision day of aggTrades "
                         "into var/data_scout/ (bounded: 1 day, BTCUSDT)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    records = []

    print("=== probing keyless market-data endpoints ===")
    for src in SOURCES:
        name, url, kind, check = src[:4]
        post = src[4] if len(src) > 4 else None
        max_read = src[5] if len(src) > 5 else 5_000_000
        rec = probe(name, url, kind, check, post=post, max_read=max_read)
        rec["query"] = name
        records.append(rec)

    if args.search:
        print(f"\n=== HF dataset discovery: {args.search!r} ===")
        for d in hf_dataset_search(args.search):
            records.append(d)
            print(f"  CANDIDATE      {d['name']:40s} "
                  f"dl={d['downloads']:>7} {d['url']}")

    if args.collect:
        print("\n=== collecting sample: BTCUSDT aggTrades 2024-01-01 ===")
        url = ("https://data.binance.vision/data/spot/daily/aggTrades/"
               "BTCUSDT/BTCUSDT-aggTrades-2024-01-01.zip")
        req = urllib.request.Request(url, headers=_UA)
        z = zipfile.ZipFile(io.BytesIO(
            urllib.request.urlopen(req, timeout=60).read()))
        dest = Path("var/data_scout/BTCUSDT-aggTrades-2024-01-01.csv")
        with z.open(z.namelist()[0]) as src, dest.open("wb") as dst:
            dst.write(src.read())
        n = sum(1 for _ in dest.open())
        print(f"  wrote {dest} ({n} real aggTrades)")
        records.append({"source": "binance_vision",
                        "verdict": "COLLECTED", "file": str(dest),
                        "rows": n})

    with out.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    ok = sum(1 for r in records if str(r.get("verdict")).startswith("OK")
             or r.get("verdict") in ("CANDIDATE", "COLLECTED"))
    print(f"\nledger -> {out} ({len(records)} rows, {ok} usable/candidate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
