#!/usr/bin/env python
"""Low-turnover anomaly gate — the cost regime everything else lacked.

Every prior falsification ran at daily-or-faster turnover where 5bps
per trade dominates. This gate tests hypotheses whose natural
frequency is weekly-to-monthly, where the same 5bps is amortized:

  A) 12-1 month cross-sectional momentum (equities): each month-end,
     rank symbols by return over months [t-12, t-2] (skip most recent
     month — the reversal month); long top quintile, short bottom
     quintile, equal weight. Monthly rebalance; cost charged on
     actual weight changes.

  B) Index-ETF pairs via the stat_arb machinery on D1 closes:
     SPY/QQQ, SPY/DIA, QQQ/IWM, DIA/IWM — spread z-score fade; the
     gate charges cost on ACTUAL position changes, so if the signal
     holds for weeks the cost is honestly amortized (no hand-tuned
     holding period).

  C) Turn-of-month effect: mean daily return on last-trading-day +
     first-3-days vs all other days, per symbol and portfolio.
     Descriptive anomaly check (no strategy claim unless it clears).

Verdicts reuse the segmented all-LCB philosophy on per-period net
bps. Usage: python scripts/low_turnover_gate.py --db us_stocks.db
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
from trading_bot.core.csc.research.method_spec import (  # noqa: E402
    PAIR_FAMILIES, align_pair, compile_rule, pair_pnl_bps,
    spec_from_dict)
from scripts.method_candidate import verdict_from_pnl  # noqa: E402

COST_BPS = 5.0
PAIRS = [("SPY", "QQQ"), ("SPY", "DIA"), ("QQQ", "IWM"), ("DIA", "IWM")]


def load_all_daily(db):
    con = sqlite3.connect(db)
    out = {}
    for sym, tf in con.execute(
            "SELECT DISTINCT symbol, timeframe FROM market_data "
            "WHERE timeframe='D1'"):
        rows = con.execute(
            "SELECT timestamp, open, close FROM market_data "
            "WHERE symbol=? AND timeframe='D1' ORDER BY timestamp",
            (sym,)).fetchall()
        out[sym] = ([r[0] for r in rows],
                    np.array([r[1] for r in rows]),
                    np.array([r[2] for r in rows]))
    con.close()
    return out


def month_ends(ts_list):
    """Indices of last trading day per calendar month."""
    ends = {}
    for i, t in enumerate(ts_list):
        ends[t[:7]] = i
    return sorted(ends.values())


def momentum_12_1(closes_by_sym):
    """Long-short quintile spread, monthly. Returns per-month net bps
    series (already cost-adjusted on weight turnover)."""
    # align on the exact shared calendar: keep only symbols whose
    # date set equals the reference's (META is missing interior bars —
    # positional indexing would silently misalign returns)
    date_close = {}
    for s, (ts, o, c) in closes_by_sym.items():
        date_close[s] = {t[:10]: float(c[i])
                         for i, t in enumerate(ts)}
    ref_dates = sorted(date_close[max(
        date_close, key=lambda s: len(date_close[s]))])
    ref_set = set(ref_dates)
    data = {}
    for s, dc in date_close.items():
        if set(dc) == ref_set:
            data[s] = np.array([dc[d] for d in ref_dates])
    dropped = sorted(set(closes_by_sym) - set(data))
    if dropped:
        print(f"  momentum universe dropped (calendar mismatch): "
              f"{dropped}")
    syms = sorted(data)
    ts_ref = [f"{d}T00:00:00+00:00" for d in ref_dates]
    ends = month_ends(ts_ref)
    # need ~13 months history before first signal
    rets_m = {}
    for s in syms:
        c = data[s]
        # daily log returns -> monthly compound via resample on ends
        rets_m[s] = np.diff(np.log(c), prepend=np.log(c[0]))
    pnl = []
    prev_w = {s: 0.0 for s in syms}
    months = []
    for k in range(13, len(ends) - 1):
        e_now, e_prev = ends[k], ends[k - 1]
        # momentum window: months [k-12, k-2] -> daily bars between
        # month-end indices ends[k-12]..ends[k-2]
        a, b = ends[k - 12], ends[k - 2]
        if b <= a:
            continue
        scores = {}
        for s in syms:
            c = data[s]
            if b >= len(c) or a >= len(c):
                continue
            scores[s] = float(np.log(c[b] / c[a]))
        if len(scores) < 6:
            continue
        ranked = sorted(scores, key=scores.get)
        q = max(1, len(ranked) // 5)
        losers, winners = ranked[:q], ranked[-q:]
        # next-month return: ends[k] -> ends[k+1]
        e_next = ends[k + 1]
        r_next = {s: float(np.log(data[s][e_next] / data[s][e_now]))
                  for s in scores}
        gross = (np.mean([r_next[s] for s in winners])
                 - np.mean([r_next[s] for s in losers])) * 1e4
        # turnover cost: weight changes on both legs
        w = {s: 0.0 for s in syms}
        for s in winners:
            w[s] = 1.0 / len(winners)
        for s in losers:
            w[s] = -1.0 / len(losers)
        turn = sum(abs(w[s] - prev_w[s]) for s in syms)
        cost = turn * COST_BPS / 2.0  # per-unit-notional approx
        pnl.append(gross - cost)
        prev_w = w
        months.append(ts_ref[e_now][:7])
    return np.array(pnl), months


def pairs_low_turnover(data):
    """stat_arb z-fade on D1 closes; gate charges actual turnover."""
    out = {}
    for a_sym, b_sym in PAIRS:
        if a_sym not in data or b_sym not in data:
            continue
        a_ts, a_o, a_c = data[a_sym]
        b_ts, b_o, b_c = data[b_sym]
        a_al, b_al = align_pair(a_ts, a_c, b_ts, b_c)
        if len(a_al) < 500:
            continue
        spec = spec_from_dict({
            "spec_id": f"lt_{a_sym}_{b_sym}",
            "hypothesis": f"{a_sym}/{b_sym} spread z-fade",
            "family": "stat_arb",
            "params": {"window": 60, "z": 2.0, "hedge": 1.0},
            "pair": {"db": "us_stocks.db", "symbol": b_sym,
                     "timeframe": "D1"}})
        try:
            rule2 = compile_rule(spec)
        except Exception as e:
            out[f"{a_sym}/{b_sym}"] = {"status": f"spec_error:{e}"}
            continue
        # per-leg cost x2 already inside pair_pnl_bps at COST_BPS
        pnl = pair_pnl_bps(rule2, a_al, b_al, 1.0, COST_BPS)
        out[f"{a_sym}/{b_sym}"] = {
            "aligned_days": len(a_al),
            "verdict": verdict_from_pnl(pnl, 3, 0.4, 20, 0.0,
                                        label=f"{a_sym}/{b_sym}")}
    return out


def turn_of_month(data):
    """Mean daily log-return on ToM days vs others; portfolio = mean
    across symbols of per-day returns aligned by date."""
    by_date = {}
    for s, (ts, o, c) in data.items():
        for i in range(1, len(c)):
            d = ts[i][:10]
            by_date.setdefault(d, {})[s] = float(
                np.log(c[i] / c[i - 1]))
    dates = sorted(by_date)
    # mark ToM: last trading day of month + first 3 of next month
    month_last = {}
    for d in dates:
        month_last[d[:7]] = d
    tom = set()
    for m, last in month_last.items():
        # last trading day itself + first 3 dates of NEXT month
        nxt = sorted(x for x in dates if x[:7] > m)[:3]
        tom.add(last)
        tom.update(nxt)
    tom_rets, oth_rets = [], []
    for d in dates:
        rets = list(by_date[d].values())
        if not rets:
            continue
        (tom_rets if d in tom else oth_rets).append(float(np.mean(rets)))
    def stats(x):
        x = np.array(x) * 1e4
        return {"n": len(x), "mean_bps": round(float(x.mean()), 2),
                "lcb5": round(block_bootstrap_lcb(x)[1], 2)} \
            if len(x) >= 30 else {"n": len(x), "status": "thin"}
    return {"tom_days": stats(tom_rets), "other_days": stats(oth_rets),
            "n_tom": len(tom)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="us_stocks.db")
    ap.add_argument("--out", default="var/low_turnover_gate.json")
    args = ap.parse_args()

    data = load_all_daily(args.db)
    print(f"symbols: {sorted(data)}")

    report = {"gate": {"db": args.db, "cost_bps": COST_BPS},
              "momentum_12_1": {}, "index_pairs": {},
              "turn_of_month": {}}

    # A) momentum on the broad universe (ex-ETFs: use all, ETFs are
    # legitimate momentum candidates too)
    pnl, months = momentum_12_1(data)
    if len(pnl) >= 30:
        v = verdict_from_pnl(pnl, 3, 0.4, 0, 0.0,
                             label="xs_momentum_12_1")
        report["momentum_12_1"] = {
            "months": len(months), "span": [months[0], months[-1]],
            "verdict": v}
        print(f"[momentum_12_1] months={len(months)} "
              f"mean={v['overall'].get('mean_net_bps')} "
              f"lcb={v['overall'].get('lcb5_net_bps')} "
              f"-> {v['verdict']}", flush=True)
    else:
        report["momentum_12_1"] = {"status": "insufficient",
                                   "months": len(pnl)}
        print("[momentum_12_1] insufficient history")

    # B) index pairs
    for k, v in pairs_low_turnover(data).items():
        report["index_pairs"][k] = v
        vv = v.get("verdict", {})
        print(f"[{k}] aligned={v.get('aligned_days')} "
              f"mean={vv.get('overall', {}).get('mean_net_bps')} "
              f"lcb={vv.get('overall', {}).get('lcb5_net_bps')} "
              f"-> {vv.get('verdict', v.get('status'))}", flush=True)

    # C) turn-of-month
    report["turn_of_month"] = turn_of_month(data)
    t = report["turn_of_month"]
    print(f"[ToM] tom n={t['tom_days'].get('n')} "
          f"mean={t['tom_days'].get('mean_bps')}bps vs "
          f"other={t['other_days'].get('mean_bps')}bps", flush=True)

    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
