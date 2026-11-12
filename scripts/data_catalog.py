#!/usr/bin/env python
"""Unified data catalog (M3 of DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md).

Scans market_data-schema sqlite dbs in the repo root and writes
var/data_catalog.json: per (db, symbol, timeframe) -> rows, coverage,
freshness. Collectors/scouts/paper_runner --universe auto should read
this instead of re-scanning. Read-only; honest about empty/failed dbs.

Usage: python scripts/data_catalog.py [--out var/data_catalog.json]
       [--include var/**/*.db]
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def catalog_db(path: Path) -> dict:
    entry = {"path": str(path.relative_to(ROOT)), "series": []}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                              timeout=5)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "market_data" not in tables:
            entry["note"] = "no market_data table"
            con.close()
            return entry
        cols = {c[1] for c in con.execute("PRAGMA table_info(market_data)")}
        if not {"symbol", "timeframe", "timestamp", "close"} <= cols:
            entry["note"] = "market_data schema mismatch"
            con.close()
            return entry
        for sym, tf, n, t0, t1 in con.execute(
                "SELECT symbol, timeframe, COUNT(*), MIN(timestamp), "
                "MAX(timestamp) FROM market_data "
                "GROUP BY symbol, timeframe ORDER BY symbol, timeframe"):
            entry["series"].append({
                "symbol": sym, "timeframe": tf, "rows": n,
                "first_ts": t0, "last_ts": t1})
        con.close()
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry


def catalog_macro(path: Path) -> dict:
    """macro_data.db gets series-level catalog (not OHLC)."""
    entry = {"path": str(path.relative_to(ROOT)),
             "kind": "macro_series", "series": []}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                              timeout=5)
        if "macro_series" not in {
                r[0] for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}:
            con.close()
            return entry
        for name, n, d0, d1 in con.execute(
                "SELECT series, COUNT(*), MIN(date), MAX(date) "
                "FROM macro_series GROUP BY series ORDER BY series"):
            entry["series"].append({"series": name, "rows": n,
                                    "first_date": d0, "last_date": d1})
        con.close()
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="var/data_catalog.json")
    ap.add_argument("--globs", nargs="*", default=None,
                    help="db globs relative to root (default: *.db)")
    args = ap.parse_args()

    pats = args.globs or ["*.db"]
    dbs = []
    for p in pats:
        dbs.extend(sorted(ROOT.glob(p)))
    dbs = [d for d in dbs if d.is_file()]

    catalog = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "dbs": []}
    for db in dbs:
        if db.name == "macro_data.db":
            catalog["dbs"].append(catalog_macro(db))
        else:
            catalog["dbs"].append(catalog_db(db))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2))
    n_series = sum(len(d.get("series", [])) for d in catalog["dbs"])
    n_rows = sum(s.get("rows", 0) for d in catalog["dbs"]
                 for s in d.get("series", []))
    print(f"catalog -> {out}  ({len(catalog['dbs'])} dbs, "
          f"{n_series} series, {n_rows:,} rows)")
    for d in catalog["dbs"]:
        err = d.get("error") or d.get("note")
        tag = f"  [{err}]" if err else ""
        print(f"  {d['path']}: {len(d.get('series', []))} series{tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
