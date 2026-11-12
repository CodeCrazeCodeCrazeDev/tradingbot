#!/usr/bin/env python
"""Data-quality audit — the 'verifies data' leg of AFI made visible.

Every gate eval trusts load_bars() blindly; market_data.db is known
to carry off-grid spliced rows (fractional-second timestamps,
+-6.7% fake returns, AGENTS.md world-model notes). This audit scans
each (db, symbol, timeframe) series for the contamination classes
that corrupt verdicts:

  off_grid      timestamp not on the timeframe boundary
                (fractional seconds or minute % tf_minutes != 0)
  non_monotonic timestamp order violations
  extreme_ret   |close-to-close return| > 0.5% (news/gap vs splice)
  dup_ts        duplicate timestamps

Output: var/data_quality.json + console summary, worst series first.
Read-only; runs under .venv (stdlib+sqlite only).
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60,
              "H4": 240, "D1": 1440, "W1": 10080,
              "1m": 1, "5m": 5, "15m": 15, "30m": 30,
              "1h": 60, "4h": 240, "1d": 1440}
# extreme-return threshold scales with bar size AND asset vol: 0.5%
# is anomalous on EURUSD M15 but ordinary on crypto 15m (DOGE 1h
# legitimately prints 1339 of them, max 7%). 5% intraday flags only
# genuine spikes/splices; daily/weekly unchanged.
EXTREME_RET_BY_TF = {"intraday": 0.05, "daily": 0.05,
                     "weekly": 0.10}


def _parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def audit_series(rows, tf):
    """rows: [(timestamp, close)] ordered by timestamp."""
    tf_min = TF_MINUTES.get(tf)
    # minute-modulus alignment only applies intraday — daily/weekly
    # bars legitimately sit at session times, not midnight-UTC grid
    grid_check = bool(tf_min and tf_min < 1440)
    extreme = (EXTREME_RET_BY_TF["daily"] if tf_min and tf_min >= 1440
               else EXTREME_RET_BY_TF["weekly"] if tf_min and tf_min >= 10080
               else EXTREME_RET_BY_TF["intraday"])
    out = {"rows": len(rows), "off_grid": 0, "non_monotonic": 0,
           "extreme_ret": 0, "dup_ts": 0}
    prev_dt, prev_close = None, None
    seen = set()
    for raw, close in rows:
        if raw in seen:
            out["dup_ts"] += 1
        seen.add(raw)
        dt = _parse_ts(raw)
        if dt is None:
            out["off_grid"] += 1
        else:
            if (dt.second or dt.microsecond
                    or (grid_check
                        and (dt.hour * 60 + dt.minute) % tf_min)):
                out["off_grid"] += 1
            if prev_dt and dt < prev_dt:
                out["non_monotonic"] += 1
            prev_dt = dt
        if prev_close and close:
            ret = abs(close / prev_close - 1.0)
            if ret > extreme:
                out["extreme_ret"] += 1
        prev_close = close or prev_close
    return out


def audit_db(path: Path):
    entry = {"db": path.name, "series": [], "error": None}
    try:
        con = sqlite3.connect(str(path))
        tabs = [r[0] for r in con.execute(
            "select name from sqlite_master where type='table'")]
        if "market_data" not in tabs:
            entry["error"] = "no market_data table"
            con.close()
            return entry
        groups = con.execute(
            "select symbol,timeframe from market_data "
            "group by symbol,timeframe").fetchall()
        for sym, tf in groups:
            rows = con.execute(
                "select timestamp,close from market_data "
                "where symbol=? and timeframe=? order by timestamp",
                (sym, tf)).fetchall()
            q = audit_series(rows, tf)
            q.update({"symbol": sym, "timeframe": tf})
            entry["series"].append(q)
        con.close()
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry


def main():
    dbs = sorted(ROOT.glob("*.db"))
    catalog = {"generated": datetime.now().isoformat(
        timespec="seconds"), "dbs": []}
    for db in dbs:
        e = audit_db(db)
        if e["series"] or e["error"]:
            catalog["dbs"].append(e)
            print(f"{e['db']}: {len(e['series'])} series"
                  + (f" [{e['error']}]" if e["error"] else ""))
    out = ROOT / "var" / "data_quality.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2))
    print(f"-> {out}")

    # worst offenders: any contamination class nonzero
    flagged = []
    for d in catalog["dbs"]:
        for s in d["series"]:
            bad = {k: s[k] for k in
                   ("off_grid", "non_monotonic", "extreme_ret",
                    "dup_ts") if s[k]}
            if bad:
                flagged.append((d["db"], s["symbol"], s["timeframe"],
                                s["rows"], bad))
    flagged.sort(key=lambda x: -sum(x[4].values()))
    print(f"\nflagged series: {len(flagged)}")
    for db, sym, tf, n, bad in flagged[:15]:
        print(f"  {db}:{sym}:{tf} rows={n} {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
