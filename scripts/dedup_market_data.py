#!/usr/bin/env python
"""Dedup market_data rows on (symbol,timeframe,timestamp).

hl_data.db crypto series carry ~67% duplicate timestamps from
overlapping sync windows (data_quality_audit finding). Default is
--dry-run; pass --apply to delete duplicates, keeping the row with
the smallest id (earliest write) per key. Prints per-db counts.

Usage:
    python scripts/dedup_market_data.py            # dry run
    python scripts/dedup_market_data.py --apply    # execute
    python scripts/dedup_market_data.py hl_data.db --apply
"""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def dedup_db(path: Path, apply: bool) -> int:
    con = sqlite3.connect(str(path))
    try:
        n = con.execute(
            "select count(*) from (select 1 from market_data "
            "group by symbol,timeframe,timestamp "
            "having count(*)>1)").fetchone()[0]
        total_dup = con.execute(
            "select coalesce(sum(c-1),0) from (select count(*) c "
            "from market_data group by symbol,timeframe,timestamp "
            "having c>1)").fetchone()[0]
        if apply and total_dup:
            con.execute(
                "delete from market_data where id not in ("
                "select min(id) from market_data "
                "group by symbol,timeframe,timestamp)")
            con.commit()
        con.close()
        return total_dup, n
    except sqlite3.Error as e:
        con.close()
        print(f"{path.name}: {e}")
        return 0, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dbs", nargs="*", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    paths = ([ROOT / d for d in args.dbs] if args.dbs
             else sorted(ROOT.glob("*.db")))
    mode = "APPLY" if args.apply else "dry-run"
    for p in paths:
        if not p.exists():
            continue
        dup_rows, dup_keys = dedup_db(p, args.apply)
        if dup_rows or dup_keys:
            print(f"{mode} {p.name}: {dup_rows} duplicate rows "
                  f"across {dup_keys} keys")
    if not args.apply:
        print("dry-run only — rerun with --apply to delete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
