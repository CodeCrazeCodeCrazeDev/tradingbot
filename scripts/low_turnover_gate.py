#!/usr/bin/env python
"""Low-turnover anomaly gate — the cost math finally matches.

Every prior falsification traded daily-or-faster where 5bps/trade
dominates. At monthly/weekly horizons cost is ~5bps ONCE per
rebalance — anomalies that were sub-cost intraday may clear here.

Three hypothesis classes on us_stocks.db D1 bars (17 symbols,
2012->2026):

  A) 12-1 month cross-sectional momentum — rank by return over
     months [t-12, t-2] (skip most recent), long top-5 / short
     bottom-5 equal-weight, monthly rebalance. Turnover cost charged
     on weight changes (x2 legs).

  B) index-ETF pairs z-fade — SPY/QQQ, SPY/DIA, QQQ/IWM weekly closes,
     spread=log(a)-log(b), z over 26w window; pos=-sign(z) when
     |z|>1.5 else flat, weekly rebalance, cost x2 legs on changes.

  C) overnight anomaly by weekday / turn-of-month — overnight_bps
     conditioned on weekday of the session and ToM window (last3+first3
     trading days of month); long-overnight only on qualifying days.

Verdicts: chronological 60/40, OOS tail in 3 contiguous segments,
block-bootstrap LCB5 — candidate needs EVERY segment LCB>0 & mean>0.

Usage: python scripts/low_turnover_gate.py \
    --db us_stocks.db --out var/low_turnover_gate.json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402

COST_BPS = 5.0
TOP_K, BOT_K = 5, 5
Z_ENTRY = 1.5
Z_WINDOW_W = 26


def load_daily(db: str):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT symbol, timestamp, open, close FROM market_data "
        "WHERE timeframe='D1' ORDER BY symbol, timestamp").fetchall()
    con.close()
    out = {}
    for sym, ts, o, c in rows:
        out.setdefault(sym, []).append((ts, float(o), float(c)))
    return {s: (np.array([r[0] for r in v]),
                np.array([r[1] for r in v]),
                np.array([r[2] for r in v])) for s, v in out.items()}


def verdict(pnl, n_segments=3):
    pnl = np.asarray(pnl, dtype=float)
    n = len(pnl)
    if n < 24:
        return {"status": "insufficient_evidence", "n": int(n)}
    split = int(n * 0.6)
    ev = pnl[split:]
    if len(ev) < 10:
        return {"status": "insufficient_eval", "n": int(len(ev))}
    m, l = block_bootstrap_lcb(ev)
    seg_n = max(1, len(ev) // n_segments)
    segs = []
    for k in range(n_segments):
        a, b = k * seg_n, (k + 1) * seg_n if k < n_segments - 1 \
            else len(ev)
        if b - a < 4:
            segs.append({"status": "thin"})
            continue
        ms, ls = block_bootstrap_lcb(ev[a:b])
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    ok = (len([s for s in segs if "lcb5" in s]) == 3
          and all(s["lcb5"] > 0 for s in segs if "lcb5" in s) and m > 0)
    return {"n": int(n), "mean_bps": round(m, 3), "lcb5": round(l, 3),
            "segments": segs,
            "verdict": "candidate" if ok else "rejected"}


def monthly_momentum(data, cost_bps):
    """12-1 momentum, top5 long / bottom5 short, monthly rebalance.
    Returns monthly net-bps series."""
    # month index per bar: YYYYMM from timestamp
    series = {}
    for sym, (ts, o, c) in data.items():
        months = np.array([int(str(t)[:7].replace("-", "")) for t in ts])
        # last close per month
        um, inv = np.unique(months, return_inverse=True)
        mc = np.full(len(um), np.nan)
        mc[inv] = c  # last write wins per month (ordered input)
        series[sym] = (um, mc)
    all_months = sorted(set().union(*[set(s[0]) for s in
                                      series.values()]))
    midx = {m: i for i, m in enumerate(all_months)}
    T = len(all_months)
    # close matrix sym x month (ffill)
    syms = sorted(series)
    C = np.full((len(syms), T), np.nan)
    for si, s in enumerate(syms):
        um, mc = series[s]
        for m, v in zip(um, mc):
            C[si, midx[m]] = v
    for si in range(len(syms)):
        for t in range(1, T):
            if np.isnan(C[si, t]):
                C[si, t] = C[si, t - 1]
    # momentum at month-end t: return over months t-12..t-2 (skip t-1)
    pnl = []
    prev_w = np.zeros(len(syms))
    for t in range(13, T - 1):
        mom = np.full(len(syms), np.nan)
        for si in range(len(syms)):
            if np.isfinite(C[si, t - 2]) and np.isfinite(C[si, t - 12]):
                mom[si] = C[si, t - 2] / C[si, t - 12] - 1.0
        ok = np.isfinite(mom)
        if ok.sum() < 2 * TOP_K:
            continue
        order = np.argsort(np.where(ok, mom, -np.inf))
        w = np.zeros(len(syms))
        shorts = order[:BOT_K]
        longs = order[-TOP_K:]
        valid_l = [i for i in longs if ok[i]]
        valid_s = [i for i in shorts if ok[i]]
        if len(valid_l) < TOP_K or len(valid_s) < BOT_K:
            continue
        w[valid_l] = 1.0 / TOP_K
        w[valid_s] = -1.0 / BOT_K
        # next-month return per symbol
        r_next = C[:, t] / C[:, t - 1] - 1.0  # month t-1 -> t? see note
        # position decided at end of month t-1 earns month t return:
        # C[:,t]/C[:,t-1] is the return DURING month t vs t-1 close.
        gross = float(np.nansum(w * r_next)) * 1e4
        turnover = float(np.sum(np.abs(w - prev_w)))
        cost = turnover * cost_bps
        pnl.append(gross - cost)
        prev_w = w
    return np.array(pnl)


def pairs_z_fade(data, pairs, cost_bps):
    """Weekly log-spread z-score fade on index ETFs."""
    # resample D1 -> weekly last close
    wk = {}
    for sym in set(sum(([a, b] for a, b in pairs), [])):
        if sym not in data:
            continue
        ts, o, c = data[sym]
        # ISO week key
        wkey = np.array([f"{str(t)[:4]}-W{int(__import__('datetime').datetime.fromisoformat(str(t).replace('Z','+00:00')).isocalendar().week):02d}"
                         for t in ts])
        uw, inv = np.unique(wkey, return_inverse=True)
        wc = np.full(len(uw), np.nan)
        wc[inv] = c
        wk[sym] = wc
    out = {}
    for a, b in pairs:
        if a not in wk or b not in wk:
            continue
        n = min(len(wk[a]), len(wk[b]))
        ca, cb = wk[a][:n], wk[b][:n]
        ok = np.isfinite(ca) & np.isfinite(cb)
        ca, cb = ca[ok], cb[ok]
        if len(ca) < Z_WINDOW_W + 20:
            continue
        spread = np.log(ca) - np.log(cb)
        pos = np.zeros(len(ca))
        for i in range(Z_WINDOW_W, len(ca)):
            w = spread[i - Z_WINDOW_W:i]
            m, s = float(np.mean(w)), float(np.std(w))
            if s <= 0:
                continue
            z = (spread[i] - m) / s
            pos[i] = -1.0 if z > Z_ENTRY else (1.0 if z < -Z_ENTRY else 0.0)
        # weekly spread return i-1 -> i earned by pos[i-1]? pos at week
        # i close earns next week: shift pos back one
        pos_earn = np.concatenate([[0.0], pos[:-1]])
        spr_ret = np.diff(spread)
        spr_ret = np.concatenate([[0.0], spr_ret])
        dpos = np.abs(np.diff(np.concatenate([[0.0], pos_earn])))
        pnl = pos_earn * spr_ret * 1e4 - dpos * cost_bps * 2.0
        out[f"{a}/{b}"] = verdict(pnl[Z_WINDOW_W:])
    return out


def overnight_conditioned(data, cost_bps):
    """Overnight returns conditioned on weekday + turn-of-month."""
    import datetime as _dt
    groups = {}
    for sym, (ts, o, c) in data.items():
        for i in range(1, len(ts)):
            on = (o[i] / c[i - 1] - 1.0) * 1e4 - cost_bps
            d = _dt.datetime.fromisoformat(
                str(ts[i]).replace("Z", "+00:00"))
            wd = d.weekday()
            day_of_month = d.day
            # approximate ToM: first 3 or last 3 calendar days
            import calendar as _cal
            last_day = _cal.monthrange(d.year, d.month)[1]
            tom = day_of_month <= 3 or day_of_month >= last_day - 2
            groups.setdefault(f"wd{wd}", []).append(on)
            groups.setdefault("tom" if tom else "not_tom",
                              []).append(on)
    return {k: verdict(np.array(v)) for k, v in groups.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="us_stocks.db")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/low_turnover_gate.json")
    args = ap.parse_args()

    data = load_daily(args.db)
    print(f"loaded {len(data)} symbols")
    report = {"gate": {"db": args.db, "cost_bps": args.cost_bps,
                       "top_k": TOP_K, "bot_k": BOT_K,
                       "z_entry": Z_ENTRY, "z_window_w": Z_WINDOW_W},
              "monthly_momentum_12_1": {},
              "pairs_z_fade": {},
              "overnight_conditioned": {}}

    pm = monthly_momentum(data, args.cost_bps)
    report["monthly_momentum_12_1"] = verdict(pm)
    r = report["monthly_momentum_12_1"]
    print(f"[12-1 mom L/S] n={r.get('n')} mean={r.get('mean_bps')} "
          f"lcb={r.get('lcb5')} -> {r.get('verdict', r.get('status'))}",
          flush=True)

    pairs = [("SPY", "QQQ"), ("SPY", "DIA"), ("QQQ", "IWM"),
             ("SPY", "IWM")]
    pz = pairs_z_fade(data, pairs, args.cost_bps)
    report["pairs_z_fade"] = pz
    for k, v in pz.items():
        print(f"[pair {k}] mean={v.get('mean_bps')} "
              f"lcb={v.get('lcb5')} -> "
              f"{v.get('verdict', v.get('status'))}", flush=True)

    oc = overnight_conditioned(data, args.cost_bps)
    report["overnight_conditioned"] = oc
    for k in sorted(oc):
        v = oc[k]
        print(f"[on {k}] n={v.get('n')} mean={v.get('mean_bps')} "
              f"lcb={v.get('lcb5')} -> "
              f"{v.get('verdict', v.get('status'))}", flush=True)

    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    cands = []
    if report["monthly_momentum_12_1"].get("verdict") == "candidate":
        cands.append("12-1 momentum L/S")
    cands += [f"pair {k}" for k, v in pz.items()
              if v.get("verdict") == "candidate"]
    cands += [f"overnight {k}" for k, v in oc.items()
              if v.get("verdict") == "candidate"]
    for c in cands:
        print(f"  CANDIDATE: {c}")
    if not cands:
        print("  no low-turnover candidates — honest null")
    return 0


if __name__ == "__main__":
    sys.exit(main())
