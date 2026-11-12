"""Unified data catalog — var/data_catalog.json (M3).

One file describing every data resource the system owns:

- OHLCV stores (root *.db with a market_data table): symbol x timeframe
  x row counts x coverage range — the same shape DataResourceInventory
  produces, so OpportunityScanner consumes the file directly and
  --universe auto can rank WITHOUT re-probing every DB.
- Non-OHLCV stores (orderflow depth/trades, fx ticks, collected CSVs):
  tagged kind= and table/row detail — visible in the catalog but
  skipped by scanner consumers that only understand market_data.

Refreshed on demand and once per autonomous_cycle. Read-only probes.

    .venv/Scripts/python.exe scripts/build_catalog.py          # write
    .venv/Scripts/python.exe scripts/build_catalog.py --print  # view
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "var" / "data_catalog.json"

REQUIRED = {"timestamp", "symbol", "timeframe", "close"}


def probe_ohlcv(path: Path) -> dict | None:
    """market_data-schema probe → scanner-compatible source entry."""
    try:
        con = sqlite3.connect(
            path.resolve().as_uri() + "?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "market_data" not in tables:
            return None
        cols = {c[1] for c in con.execute(
            'PRAGMA table_info("market_data")')}
        if not REQUIRED <= cols:
            return None
        series = [{"symbol": s, "timeframe": t, "rows": n,
                   "first": str(a), "last": str(b)}
                  for s, t, n, a, b in con.execute(
                      "SELECT symbol, timeframe, COUNT(*), "
                      "MIN(timestamp), MAX(timestamp) FROM market_data "
                      "GROUP BY symbol, timeframe")]
        return {"path": str(path), "kind": "ohlcv",
                "size_bytes": path.stat().st_size,
                "series": series,
                "total_rows": sum(e["rows"] for e in series)}
    except sqlite3.Error:
        return None
    finally:
        con.close()


def probe_generic_db(path: Path, kind: str) -> dict | None:
    """Any other SQLite: table names + row counts + ts range if found."""
    try:
        con = sqlite3.connect(
            path.resolve().as_uri() + "?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {}
        for (name,) in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"):
            try:
                n = con.execute(f'SELECT COUNT(*) FROM "{name}"'
                                ).fetchone()[0]
            except sqlite3.Error:
                n = -1
            cols = [c[1] for c in con.execute(
                f'PRAGMA table_info("{name}")')]
            tables[name] = {"rows": n, "columns": cols[:12]}
        if not any(t["rows"] > 0 for t in tables.values()):
            return None
        return {"path": str(path), "kind": kind,
                "size_bytes": path.stat().st_size,
                "tables": tables,
                "total_rows": sum(max(t["rows"], 0)
                                  for t in tables.values())}
    finally:
        con.close()


def probe_csv_trades(path: Path) -> dict:
    n = sum(1 for _ in path.open("rb"))
    return {"path": str(path), "kind": "csv_trades", "rows": n,
            "size_bytes": path.stat().st_size,
            "note": "aggTrades schema: id,price,qty,first,last,ts,"
                    "isBuyerMaker,isBestMatch"}


def build() -> dict:
    cat = {"generated_at": time.time(),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                         time.gmtime()),
           "sources": {}}

    for db in sorted(ROOT.glob("*.db")):
        ent = probe_ohlcv(db) or probe_generic_db(db, "sqlite_other")
        cat["sources"][db.name] = (
            ent if ent else {"status": "unusable"})

    # collected stores under var/
    of = ROOT / "var" / "orderflow" / "orderflow.db"
    if of.exists():
        e = probe_generic_db(of, "orderflow")
        if e:
            cat["sources"]["var/orderflow/orderflow.db"] = e
    fx = ROOT / "var" / "orderflow" / "fx_ticks.db"
    if fx.exists():
        e = probe_generic_db(fx, "fx_ticks")
        if e:
            cat["sources"]["var/orderflow/fx_ticks.db"] = e
    for f in sorted((ROOT / "var" / "data_scout").glob("*.csv")):
        cat["sources"][f"var/data_scout/{f.name}"] = probe_csv_trades(f)

    cat["series_total"] = sum(len(s.get("series", ()))
                              for s in cat["sources"].values())
    cat["rows_total"] = sum(s.get("total_rows", s.get("rows", 0))
                            for s in cat["sources"].values())
    return cat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    cat = build()
    if args.print:
        print(f"generated {cat['generated_utc']}")
        for name, s in cat["sources"].items():
            if "series" in s:
                kinds = f"{len(s['series'])} series"
            elif "tables" in s:
                kinds = f"tables={list(s['tables'])}"
            else:
                kinds = s.get("status", "?")
            print(f"  {name:44s} {s.get('kind','-'):12s} "
                  f"{s.get('total_rows', s.get('rows', 0)):>10} rows  "
                  f"{kinds}")
        print(f"\n{cat['series_total']} OHLCV series, "
              f"{cat['rows_total']} total rows")
        return 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cat, indent=1))
    print(f"catalog -> {out}  ({cat['series_total']} OHLCV series, "
          f"{cat['rows_total']} rows, "
          f"{len(cat['sources'])} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
