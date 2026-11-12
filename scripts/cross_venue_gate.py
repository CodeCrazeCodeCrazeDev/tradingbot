#!/usr/bin/env python
"""Cross-venue lead-lag gate: does Binance taker imbalance predict
Kraken/HL next-bar returns net of cost?

Alignment (lookahead-safe): taker bar i aggregates trades over
[t_i, t_i+15m) and completes exactly when laggard bar i closes.
Position set at laggard close[i] = sign(imb_i) earns
close[i]->close[i+1]. Same-index pairing on shared 15m timestamps.

imb = (taker_buy - (vol - taker_buy)) / vol = 2*buy/vol - 1.

Verdict per (symbol, laggard venue, threshold): chronological 60/40,
OOS tail in 3 contiguous segments, block-bootstrap LCB5 — candidate
only if EVERY segment LCB>0 and mean>0 (edge_gate philosophy).
Cost: flat COST_BPS (no spread columns on these dbs — honest floor).

Usage:
  python scripts/cross_venue_gate.py --symbols BTC,ETH \
      --laggards hl_data.db,kraken_data.db --out var/cross_venue_gate.json
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
THRESHOLDS = (0.0, 0.1, 0.2)


def load_taker_imb(db: str, symbol: str, tf_min: int = 15):
    """{timestamp: imbalance} from taker_<SYM> (15m bars)."""
    con = sqlite3.connect(db)
    tbl = f"taker_{symbol}"
    try:
        rows = con.execute(
            f"SELECT ts, taker_buy, vol FROM {tbl} ORDER BY ts").fetchall()
    except sqlite3.OperationalError:
        con.close()
        return None
    con.close()
    out = {}
    for ts, buy, vol in rows:
        if vol and vol > 0:
            out[ts] = (2.0 * buy / vol) - 1.0
    return out


def load_closes(db: str, symbol: str, timeframe: str):
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT timestamp, close FROM market_data "
        "WHERE symbol=? AND timeframe=? ORDER BY timestamp",
        (symbol, timeframe)).fetchall()
    con.close()
    return [r[0] for r in rows], np.array([r[1] for r in rows])


def eval_variant(closes, imb_on_ts, ts_list, th, cost_bps):
    """pos[i]=sign(imb) if |imb|>th, earns ret[i]=c[i+1]/c[i]-1."""
    n = len(closes)
    pos = np.zeros(n - 1)
    for i in range(n - 1):
        imb = imb_on_ts.get(ts_list[i])
        if imb is not None and abs(imb) > th:
            pos[i] = 1.0 if imb > 0 else -1.0
    ret = closes[1:] / closes[:-1] - 1.0
    chg = np.abs(np.diff(np.concatenate([[0.0], pos]))) > 0
    pnl = pos * ret - chg * (cost_bps / 1e4)
    split = int((n - 1) * 0.6)
    ev = pnl[split:]
    if len(ev) < 90:
        return {"status": "thin", "n": len(ev)}
    m, l = block_bootstrap_lcb(ev * 1e4)
    seg_n = len(ev) // 3
    segs = []
    for k in range(3):
        a, b = k * seg_n, (k + 1) * seg_n if k < 2 else len(ev)
        if b - a < 30:
            segs.append({"status": "thin"})
            continue
        ms, ls = block_bootstrap_lcb(pnl[split + a: split + b] * 1e4)
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    ok = all("lcb5" in s and s["lcb5"] > 0 for s in segs) \
        and len([s for s in segs if "lcb5" in s]) == 3 and m > 0
    return {"mean_bps": round(m, 3), "lcb5": round(l, 3),
            "exposure": round(float(np.abs(pos[split:]).mean()), 3),
            "segments": segs,
            "verdict": "candidate" if ok else "rejected"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leader-db", default="binance_data.db")
    ap.add_argument("--laggards", default="hl_data.db,kraken_data.db")
    ap.add_argument("--symbols", default="BTC,ETH")
    ap.add_argument("--timeframe", default="15m")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/cross_venue_gate.json")
    args = ap.parse_args()

    report = {"gate": {"cost_bps": args.cost_bps,
                       "leader": args.leader_db,
                       "thresholds": THRESHOLDS},
              "pairs": {}}
    for sym in [s.strip() for s in args.symbols.split(",")]:
        imb = load_taker_imb(args.leader_db, sym)
        if imb is None:
            print(f"[{sym}] no taker table on leader — skip")
            continue
        for ldb in [d.strip() for d in args.laggards.split(",")]:
            ts, closes = load_closes(ldb, sym, args.timeframe)
            if len(closes) < 200:
                print(f"[{sym}@{ldb}] only {len(closes)} bars — skip")
                continue
            imb_on_ts = {t: imb[t] for t in ts if t in imb}
            coverage = len(imb_on_ts) / max(1, len(ts) - 1)
            res = {"bars": len(closes), "imb_coverage": round(coverage, 3),
                   "variants": {}}
            for th in THRESHOLDS:
                res["variants"][f"imb|>{th}"] = eval_variant(
                    closes, imb_on_ts, ts, th, args.cost_bps)
            report["pairs"][f"{sym}@{ldb}"] = res
            best = max(res["variants"].items(),
                       key=lambda kv: kv[1].get("mean_bps", -999))
            print(f"[{sym}@{ldb}] bars={len(closes)} "
                  f"cov={coverage:.0%} best={best[0]} "
                  f"mean={best[1].get('mean_bps')} "
                  f"lcb={best[1].get('lcb5')} "
                  f"-> {best[1].get('verdict')}", flush=True)

    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    cands = [(k, vn) for k, p in report["pairs"].items()
             for vn, v in p["variants"].items()
             if v.get("verdict") == "candidate"]
    for k, vn in cands:
        print(f"  CANDIDATE {vn} on {k}")
    if not cands:
        print("  no cross-venue candidates — honest null result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
