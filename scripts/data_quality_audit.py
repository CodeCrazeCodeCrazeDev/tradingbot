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
  extreme_ret   |close-to-close return| > max(MIN_ABS,
                EWMA_K * rolling sigma) — vol-normalized so genuine
                crypto spikes don't flag as splices
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
# extreme_ret is vol-normalized: a return is anomalous when it
# exceeds K local sigmas (EWMA of past returns, so the spike can't
# inflate its own threshold) with a sanity floor below which nothing
# is ever flagged and a cap so dead-calm series can't produce
# absurd thresholds. Fixed bps thresholds can't work across FX M15
# (sigma ~0.04%) and DOGE 15m (sigma ~0.8%) simultaneously.
EXTREME_K = 8.0          # sigma multiple
EXTREME_MIN_ABS = 0.002  # 20bps — never flag smaller moves
EXTREME_CAP = 0.15       # never require >15% for intraday-ish bars
EWMA_LAMBDA = 0.94       # RiskMetrics decay


def _parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _extreme_threshold(var):
    """bps-fraction threshold from EWMA variance of past returns."""
    sigma = var ** 0.5 if var and var > 0 else 0.0
    return min(EXTREME_CAP, max(EXTREME_MIN_ABS,
                                EXTREME_K * sigma))


def audit_series(rows, tf):
    """rows: [(timestamp, close)] ordered by timestamp."""
    tf_min = TF_MINUTES.get(tf)
    # minute-modulus alignment only applies intraday — daily/weekly
    # bars legitimately sit at session times, not midnight-UTC grid
    grid_check = bool(tf_min and tf_min < 1440)
    out = {"rows": len(rows), "off_grid": 0, "non_monotonic": 0,
           "extreme_ret": 0, "dup_ts": 0}
    prev_dt, prev_close = None, None
    var = None          # EWMA variance of returns (pre-return state)
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
            ret = close / prev_close - 1.0
            if abs(ret) > _extreme_threshold(var):
                out["extreme_ret"] += 1
            var = (ret * ret if var is None
                   else EWMA_LAMBDA * var + (1 - EWMA_LAMBDA) * ret * ret)
        prev_close = close or prev_close
    return out


def audit_db(path: Path):
    entry = {"db": path.name, "series": [], "error": None}
    try:
        con = sqlite3.connect(str(path))
        tabs = [r[0] for r in con.execute(
            "select name from sqlite_master where type='table'")]
        if "lob_snapshots" in tabs:
            # ms-epoch ts, irregular cadence — off_grid does not apply;
            # structural flags only (dup_ts/non_monotonic) + extreme_ret
            for src, sym in con.execute(
                    "select source,symbol from lob_snapshots "
                    "group by source,symbol").fetchall():
                rows = con.execute(
                    "select ts,mid from lob_snapshots where source=? "
                    "and symbol=? order by rowid", (src, sym)).fetchall()
                q = {"rows": len(rows), "off_grid": 0,
                     "non_monotonic": 0, "extreme_ret": 0, "dup_ts": 0}
                prev_t, prev_mid, seen = None, None, set()
                var = None
                for t, mid in rows:
                    if t in seen:
                        q["dup_ts"] += 1
                    seen.add(t)
                    if prev_t is not None and t < prev_t:
                        q["non_monotonic"] += 1
                    prev_t = t
                    if prev_mid and mid:
                        ret = mid / prev_mid - 1.0
                        if abs(ret) > _extreme_threshold(var):
                            q["extreme_ret"] += 1
                        var = (ret * ret if var is None else
                               EWMA_LAMBDA * var
                               + (1 - EWMA_LAMBDA) * ret * ret)
                    prev_mid = mid or prev_mid
                q.update({"symbol": f"{src}:{sym}",
                          "timeframe": "snap"})
                entry["series"].append(q)
            con.close()
            return entry
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
