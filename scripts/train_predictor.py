#!/usr/bin/env python
"""Offline forward-return predictor — the deep-learning on-ramp.

Trains a ridge regression on enriched bar features to predict the
next-horizon return, then proves/disproves it through the SAME gate
machinery the live system uses (chronological split, embargo,
block-bootstrap 5% LCB, net-of-cost). Promotion rule: only if the
model's directional trades beat the cost floor does it earn a
checkpoint — the checkpoint then loads as an ADVISORY predictor,
never direct authority.

Pure numpy — no sklearn dependency. .venv-safe.

    python scripts/train_predictor.py --db-path binance_data.db \
        --symbol BTC --timeframe 15m --horizon 4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import (  # noqa: E402
    block_bootstrap_lcb, load_bars, roll_spread_bps)

FEATS = ("ret1", "ret5", "ret10", "rsi14", "vol20", "er10",
         "autocorr20", "zscore20")


def build_xy(closes, horizon):
    n = len(closes)
    X, y, idx = [], [], []
    for i in range(120, n - horizon):
        c = closes
        r = np.diff(np.log(c[i - 20:i + 1]))
        r1 = (c[i] - c[i - 1]) / c[i - 1]
        r5 = (c[i] - c[i - 5]) / c[i - 5]
        r10 = (c[i] - c[i - 10]) / c[i - 10]
        d = np.diff(c[i - 14:i + 1])
        g, l = d[d > 0].sum(), -d[d < 0].sum()
        rsi = 100.0 if l == 0 else 100.0 - 100.0 / (1.0 + g / l)
        vol = float(np.std(r))
        net = c[i] - c[i - 10]
        path = np.abs(np.diff(c[i - 10:i + 1])).sum()
        er = abs(net) / path if path > 0 else 0.0
        ac = float(np.corrcoef(r[:-1], r[1:])[0, 1]) if np.std(r) > 0 else 0.0
        m, s = np.mean(c[i - 19:i + 1]), np.std(c[i - 19:i + 1])
        z = (c[i] - m) / s if s > 0 else 0.0
        X.append([r1, r5, r10, rsi / 100.0, vol * 1e3, er, ac, z])
        y.append((c[i + horizon] - c[i]) / c[i] * 1e4)  # fwd bps
        idx.append(i)
    return np.asarray(X), np.asarray(y), idx


def ridge_fit(X, y, lam=10.0):
    xm, xs = X.mean(0), X.std(0) + 1e-12
    Xs = (X - xm) / xs
    Xb = np.hstack([Xs, np.ones((len(Xs), 1))])
    w = np.linalg.solve(Xb.T @ Xb + lam * np.eye(Xb.shape[1]),
                        Xb.T @ y)
    return w, xm, xs


def ridge_pred(X, w, xm, xs):
    Xs = (X - xm) / xs
    return np.hstack([Xs, np.ones((len(Xs), 1))]) @ w


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default="binance_data.db")
    ap.add_argument("--symbol", default="BTC")
    ap.add_argument("--timeframe", default="15m")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--eval-frac", type=float, default=0.40)
    ap.add_argument("--signal-bps", type=float, default=1.0,
                    help="trade when |predicted fwd bps| exceeds this")
    ap.add_argument("--margin", type=float, default=2.0)
    ap.add_argument("--out", default="var/trained_predictor.json")
    args = ap.parse_args()

    ts, bars = load_bars(ROOT / args.db_path, args.symbol,
                         args.timeframe)
    closes = bars[:, 3]
    X, y, idx = build_xy(closes, args.horizon)
    n = len(y)
    if n < 300:
        print(f"insufficient samples: {n}")
        return 2

    disc = int(n * (1.0 - args.eval_frac)) - args.embargo
    cost = max(roll_spread_bps(closes) or 0.0, 5.0)
    w, xm, xs = ridge_fit(X[:disc], y[:disc])
    pred = ridge_pred(X, w, xm, xs)

    # OOS quality
    ic = float(np.corrcoef(pred[disc:], y[disc:])[0, 1])
    # trade rule: sign(pred) when |pred| > signal floor
    net = []
    for j in range(disc, n):
        if abs(pred[j]) > args.signal_bps:
            net.append(np.sign(pred[j]) * y[j] - cost)
    net = np.asarray(net)
    mean_b = lcb = None
    status = "insufficient_evidence"
    if len(net) >= 30:
        mean_b, lcb = block_bootstrap_lcb(net)
        status = ("candidate_edge" if lcb > args.margin else "no_edge")

    # baseline comparison: sign-only follower on same eval window
    base = []
    for j in range(disc, n):
        r5 = X[j, 1]
        if abs(r5) > 0.001:
            base.append(np.sign(r5) * y[j] - cost)
    bm = bl = None
    if len(base) >= 30:
        bm, bl = block_bootstrap_lcb(np.asarray(base))

    report = {"generated_at": time.time(),
              "symbol": args.symbol, "timeframe": args.timeframe,
              "horizon": args.horizon, "cost_bps": cost,
              "features": FEATS, "train_n": disc, "eval_n": n - disc,
              "oos_ic": round(ic, 4),
              "model": {"trades": len(net), "mean_bps": mean_b,
                        "lcb5_bps": lcb, "status": status},
              "baseline_momentum": {"trades": len(base),
                                    "mean_bps": bm, "lcb5_bps": bl},
              "verdict": ("qualified_offline" if status ==
                          "candidate_edge" and lcb > (bl or -999)
                          else "rejected")}
    rp = ROOT / args.out
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=2))
    # checkpoint only survives if qualified — unearned weights get
    # no checkpoint, mirroring the live honesty rule.
    if report["verdict"] == "qualified_offline":
        np.savez_compressed(
            ROOT / "var" / "predictor_ckpt.npz",
            w=w, xm=xm, xs=xs, feats=list(FEATS),
            horizon=args.horizon, signal_bps=args.signal_bps)
        print("checkpoint saved -> var/predictor_ckpt.npz")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
