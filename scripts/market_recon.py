"""Decompose a market window into structural drivers. Bar-level first pass:
drift, vol regime, vol clustering, return autocorrelation, concentration.
Layers available surfaces (bookTicker1s, bookDepth, metrics) when present
for the same symbol/dates under var/l2data.

Usage:
  python scripts/market_recon.py --db market_data.db --symbol EURUSD \
      --timeframe M15 --t0 2026-10-01 --t1 2026-11-01 [--baseline-bars 500]
"""
import argparse
import sqlite3
from pathlib import Path

import numpy as np

L2 = Path("var/l2data")


def load_bars(db, sym, tf):
    con = sqlite3.connect(db)
    rows = con.execute(
        "select timestamp,open,high,low,close,volume from market_data "
        "where symbol=? and timeframe=? order by timestamp", (sym, tf)
    ).fetchall()
    con.close()
    ts = np.array([r[0] for r in rows], dtype="datetime64[ms]")
    o = np.array([r[1] for r in rows])
    h = np.array([r[2] for r in rows])
    l = np.array([r[3] for r in rows])
    c = np.array([r[4] for r in rows])
    v = np.array([r[5] for r in rows])
    return ts, o, h, l, c, v


def stats(ts, c, v, label):
    ret = np.diff(np.log(c)) * 1e4
    aret = np.abs(ret)
    print(f"\n== {label} ({len(c)} bars, {ts[0]} -> {ts[-1]}) ==")
    print(f"drift      : {ret.mean():+.3f} bps/bar  ({(c[-1]/c[0]-1)*1e4:+.1f} bps total)")
    print(f"vol        : {aret.mean():.3f} mean|ret|  {ret.std():.3f} sd bps/bar")
    ac1 = np.corrcoef(ret[1:], ret[:-1])[0, 1] if len(ret) > 4 else np.nan
    vac1 = np.corrcoef(aret[1:], aret[:-1])[0, 1] if len(aret) > 4 else np.nan
    print(f"ret ac1    : {ac1:+.3f}   |ret| ac1: {vac1:+.3f}  (vol clustering)")
    # concentration: top-decile bar share of total |move|
    q = np.quantile(aret, 0.9)
    share = aret[aret >= q].sum() / aret.sum() if aret.sum() else np.nan
    print(f"conc.      : top-decile bars = {share*100:.0f}% of total |move|")
    # episode clustering of extreme moves
    big = np.where(aret >= np.quantile(aret, 0.95))[0]
    gaps = np.diff(big) if len(big) > 1 else np.array([10])
    print(f"episodes   : {len(big)} p95+ bars, median gap {np.median(gaps) if len(gaps) else 'n/a'} bars")
    if v is not None and (v > 0).any():
        qv = np.quantile(v, 0.9)
        m = (v >= qv)[1:]
        print(f"volume     : top-decile bars ret {ret[m].mean() if m.any() else 0:+.2f} vs all {ret.mean():+.2f} bps")


def layer_l2(sym):
    files = sorted(L2.glob(f"{sym}*"))
    if not files:
        print("\nL2 surfaces: none cached for", sym)
        return
    print("\nL2 surfaces present:")
    for f in files:
        print("  ", f.name, f"{f.stat().st_size/1e6:.1f}MB")
    for f in files:
        if "bookTicker1s" in f.name:
            a = np.genfromtxt(f, delimiter=",", names=True)
            spr = (a["ask"] - a["bid"]) / ((a["ask"] + a["bid"]) / 2) * 1e4
            mimb = ((a["ask"] * a["bid_qty"] + a["bid"] * a["ask_qty"])
                    / (a["bid_qty"] + a["ask_qty"])
                    - (a["ask"] + a["bid"]) / 2) / ((a["ask"] + a["bid"]) / 2) * 1e4
            print(f"    {f.name}: n={len(a)} median spread {np.median(spr):.3f}bps "
                  f"imb mean {mimb.mean():+.3f} sd {mimb.std():.3f}")
        elif "bookDepth" in f.name or "metrics" in f.name:
            print(f"    {f.name}: (present — see edge_research H5/H6)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--t0", default="")
    ap.add_argument("--t1", default="")
    ap.add_argument("--baseline-bars", type=int, default=0,
                    help="compare the window to N bars preceding t0")
    a = ap.parse_args()
    ts, o, h, l, c, v = load_bars(a.db, a.symbol, a.timeframe)
    if not len(ts):
        print("no rows for", a.symbol, a.timeframe, "in", a.db)
        return
    if a.t0 or a.t1:
        t0 = np.datetime64(a.t0) if a.t0 else ts[0]
        t1 = np.datetime64(a.t1) if a.t1 else ts[-1]
        m = (ts >= t0) & (ts <= t1)
        print(f"window {t0} -> {t1}: {m.sum()} bars")
        if m.sum() < 3:
            print("not enough bars in window")
            return
        stats(ts[m], c[m], v[m], "event window")
        if a.baseline_bars and m.any():
            i0 = np.argmax(m)
            bm = np.zeros_like(m)
            bm[max(0, i0 - a.baseline_bars):i0] = True
            if bm.sum():
                stats(ts[bm], c[bm], v[bm], "baseline (preceding)")
    else:
        stats(ts, c, v, "full series")
    layer_l2(a.symbol)


if __name__ == "__main__":
    main()
