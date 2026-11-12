#!/usr/bin/env python
"""Venue-level replication gate for the daily rates-momentum signal.

scripts/macro_rates_gate.py found the first gated directional
candidates in the repo — but on ECB/Fed *fixing* series, single
source, same-day yield alignment. This script re-judges the identical
claim on tradeable venue D1 bars:

  - spot leg: market_data-schema D1 bars (fx_data.db Yahoo composite,
    or any collector db — pass several --db for cross-venue)
  - signal leg: unchanged — us_ust_2y/us_ust_10y/us_sofr momentum from
    macro_data.db (yields are inherently single-source macro data)
  - lookahead: position over venue bar dated D is decided by yield
    changes through date D-LAG. --yield-lag 1 (default) uses yields
    strictly before the bar date — bulletproof against the
    published_at=23:59UTC timing ambiguity; lag 0 reproduces the
    original gate's same-day convention as a sensitivity.
    NOTE: this script's alignment is also one bar STRICTER than
    macro_rates_gate's — there pos[t] appears to consume the yield
    print dated t+1 to earn the spot[t]->spot[t+1] return (the yield
    publishes ~23:59 UTC, after the ~14:00-16:00 UTC fixing), a
    possible same-day lookahead in the original result. The venue
    gate decides at bar k using yields <= date_k - lag and earns
    close[k]->close[k+1]; if the signal only survives lag=0 the
    original finding was likely a timing artifact.
  - cost: flat COST_BPS on position changes (no spread data on Yahoo
    composite; --cost-bps sweeps sensitivity). Dukascopy/MT5 D1
    replication with measured spread is the follow-up.
  - verdict per venue: every evaluated OOS segment LCB5 > 0 and
    mean > 0 (same rule as macro_rates_gate). Cross-venue candidate
    must pass on EVERY --db venue — edge_gate's all-segments /
    min-venues philosophy applied to the daily channel.

Usage:
    python scripts/macro_rates_venue_gate.py \
        --dbs fx_data.db --macro-db macro_data.db \
        --out var/macro_rates_venue_gate.json
"""

import argparse
import datetime as dt
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402
from scripts.macro_rates_gate import (  # noqa: E402
    PAIRS, YIELDS, WINDOWS, THRESHOLDS, COST_BPS, load_series)


def venue_panel(db_path: str, pair: str):
    """D1 closes for `pair` from a market_data-schema db."""
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT timestamp, close FROM market_data "
        "WHERE symbol=? AND timeframe='D1' ORDER BY timestamp",
        (pair,)).fetchall()
    con.close()
    if not rows:
        return None
    dates = [r[0][:10] for r in rows]
    closes = np.array([r[1] for r in rows], dtype=float)
    keep = np.isfinite(closes) & (closes > 0)
    return dates, closes, keep


def yield_panel_on_dates(macro_con, dates, lag, pair):
    """Yield series reindexed onto venue dates, lookahead-safe.

    For each venue bar date d, the usable yield set is
    {yield_date <= d - lag days} (calendar subtraction; yields do not
    print on weekends, so a Monday bar with lag=1 sees Friday's
    print). Each panel slot gets the latest yield value at or before
    that cutoff — ffill across non-yield days. NaN before the first
    yield observation.
    """
    out = {}
    for y in YIELDS:
        m = load_series(macro_con, y)
        ys = sorted(m)
        vals = []
        j = 0
        yd = [dt.date.fromisoformat(d) for d in dates]
        ydates = [dt.date.fromisoformat(d) for d in ys]
        for d in yd:
            cutoff = d - dt.timedelta(days=lag)
            while j < len(ys) and ydates[j] <= cutoff:
                j += 1
            # j-1 is latest yield date <= cutoff
            vals.append(m[ys[j - 1]] if j > 0 else np.nan)
        out[y] = np.array(vals, dtype=float)
    spec = PAIRS[pair]
    if spec["diff"]:
        a = load_series(macro_con, spec["diff"][0])
        b = load_series(macro_con, spec["diff"][1])
        common = sorted(set(a) & set(b))
        amap = {d: a[d] - b[d] for d in common}
        vals, j = [], 0
        cdates = sorted(amap)
        cdates_d = [dt.date.fromisoformat(d) for d in cdates]
        for ds in [dt.date.fromisoformat(d) for d in dates]:
            cutoff = ds - dt.timedelta(days=lag)
            while j < len(cdates) and cdates_d[j] <= cutoff:
                j += 1
            vals.append(amap[cdates[j - 1]] if j > 0 else np.nan)
        out["diff10"] = np.array(vals, dtype=float)
    return out


def build_signals(ypanel, pair):
    """Same signal definitions as macro_rates_gate.main."""
    signals = {}
    for y in YIELDS:
        v = ypanel[y]
        for w in WINDOWS:
            signals[f"d{y[3:] if y.startswith('us_') else y}_{w}d"] = \
                v[w:] - v[:-w]
    if "diff10" in ypanel:
        signals["ddiff10_5d"] = ypanel["diff10"][5:] - ypanel["diff10"][:-5]
    return signals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dbs", default="fx_data.db",
                    help="comma-separated market_data-schema dbs; each is "
                         "an independent venue leg")
    ap.add_argument("--macro-db", default="macro_data.db")
    ap.add_argument("--pairs", default="EURUSD,GBPUSD,USDJPY")
    ap.add_argument("--yield-lag", type=int, default=1,
                    help="yield observations usable through venue_date-lag "
                         "(1 = strictly before bar date; 0 = same-day, "
                         "original-gate convention)")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/macro_rates_venue_gate.json")
    args = ap.parse_args()
    cost_bps = args.cost_bps

    macro_con = sqlite3.connect(args.macro_db)
    venues = [d.strip() for d in args.dbs.split(",")]
    report = {"gate": {"cost_bps": cost_bps, "yield_lag": args.yield_lag,
                       "windows": WINDOWS, "thresholds": THRESHOLDS,
                       "venues": venues},
              "venue_results": {}, "cross_venue": {}}

    for pair in [p.strip() for p in args.pairs.split(",")]:
        per_venue = {}
        for db in venues:
            vp = venue_panel(db, pair)
            if vp is None:
                per_venue[db] = {"status": "no_d1_bars"}
                continue
            dates, closes, keep = vp
            # drop bad rows, keep date alignment
            idx = np.where(keep)[0]
            dates = [dates[i] for i in idx]
            closes = closes[idx]
            ypanel = yield_panel_on_dates(macro_con, dates,
                                          args.yield_lag, pair)
            signals = build_signals(ypanel, pair)
            res = simulate_weighted(closes, dates, signals, pair,
                                    cost_bps)
            res["db"] = db
            per_venue[db] = res
            print(f"[{pair}@{db}] bars={res['n_bars']} "
                  f"eval {res['eval_span'][0]}..{res['eval_span'][1]}",
                  flush=True)
        report["venue_results"][pair] = per_venue

        # cross-venue verdict: candidate only if EVERY venue with data
        # marks it candidate
        cv = {}
        vnames = set()
        for db, res in per_venue.items():
            if "variants" in res:
                vnames.update(res["variants"])
        for vn in sorted(vnames):
            oks, details = True, {}
            for db, res in per_venue.items():
                if "variants" not in res or vn not in res["variants"]:
                    continue
                ev = res["variants"][vn]
                segs = [s for s in ev.get("segments", [])
                        if "lcb5" in s]
                ok = (segs and len(segs) == len(ev.get("segments", []))
                      and all(s["lcb5"] > 0 for s in segs)
                      and ev.get("mean_bps", -1) > 0)
                details[db] = {"verdict": "candidate" if ok else "rejected",
                               "mean": ev.get("mean_bps"),
                               "lcb5": ev.get("lcb5")}
                oks = oks and ok
            if details:
                cv[vn] = {"cross_venue": "candidate" if oks else "rejected",
                          "venues": details}
        report["cross_venue"][pair] = cv

    try:
        report["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass
    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\n-> {args.out}")
    for pair, cvs in report["cross_venue"].items():
        for vn, v in cvs.items():
            if v["cross_venue"] == "candidate":
                print(f"  CANDIDATE {vn}@{pair}: {v['venues']}")


def simulate_weighted(closes, dates, signals, pair, cost_bps):
    """Align each signal series to venue bars by right edge.

    signals[s] has length len(panel) - w (window warmup). Both the
    yield panel and venue bars are ordered on the same dates after
    reindexing, so signal element j corresponds to venue bar index
    j + w. We therefore evaluate each signal on the venue bar range
    [w, n) — the signal's last element pairs with the last bar.
    """
    ret = np.diff(np.log(closes))
    n = len(closes)
    split = int(n * 0.6)
    res = {"n_bars": n, "eval_span": [dates[split], dates[-1]],
           "variants": {}}
    dsign = PAIRS[pair]["sign"]
    for sname, sraw_full in signals.items():
        # recover warmup w from series length vs panel length is not
        # stored; infer per-window: signal len = panel_len - w and
        # panel_len == n. So w = n - len(sraw_full).
        w = n - len(sraw_full)
        sraw = sraw_full  # element j -> venue bar index j + w
        for th in THRESHOLDS:
            # position for bar i uses signal element i - w
            pos = np.zeros(n - 1)
            valid = np.abs(sraw[:n - 1 - w]) > th
            pos[w:n - 1] = np.where(valid,
                                    dsign * np.sign(sraw[:n - 1 - w]),
                                    0.0)
            chg = np.abs(np.diff(np.concatenate([[0.0], pos]))) > 0
            pnl = pos * ret - chg * (cost_bps / 1e4)
            ev = pnl[split - 1:]
            if len(ev) < 60:
                res["variants"][f"{sname}|>{th}"] = {
                    "status": "thin", "n": len(ev)}
                continue
            m, l = block_bootstrap_lcb(ev * 1e4)
            seg_n = len(ev) // 3
            segs = []
            for k in range(3):
                a, b = k * seg_n, (k + 1) * seg_n if k < 2 else len(ev)
                if b - a < 60:
                    segs.append({"status": "thin"})
                    continue
                ms, ls = block_bootstrap_lcb(
                    pnl[split - 1 + a: split - 1 + b] * 1e4)
                segs.append({"mean": round(ms, 2),
                             "lcb5": round(ls, 2)})
            res["variants"][f"{sname}|>{th}"] = {
                "mean_bps": round(m, 3), "lcb5": round(l, 3),
                "exposure": round(float(np.abs(pos[split - 1:]).mean()), 3),
                "segments": segs}
    return res


if __name__ == "__main__":
    main()
