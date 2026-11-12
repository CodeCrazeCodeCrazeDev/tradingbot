#!/usr/bin/env python
"""Regime-conditional verdict — judge a claim WHERE it claims.

Global verdicts average across vol regimes and can kill a claim that
only works in one. The verified rv16 blend forecast
(var/rv_blend_forecaster.pt) splits decision bars into forecast-vol
terciles; this script re-runs the exact evaluate() per-trade math
(net = s*fwd_bps - cost) and buckets trades by regime.

Per regime: n_trades, mean, LCB5, split-half sign consistency.
Unregimed trades (no forecast coverage) reported separately —
honest, never silently dropped.

HERMES ENV ONLY (torch + WorldModelV2 featurizer):
    %LOCALAPPDATA%/hermes/hermes-agent/venv/Scripts/python.exe \
        scripts/regime_split_eval.py --db market_data.db \
        --symbol EURUSD --timeframe M15 --spec-file spec.json
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from scripts.edge_baseline import (  # noqa: E402
    block_bootstrap_lcb, load_bars, roll_spread_bps)
from scripts.method_candidate import verdict_from_pnl  # noqa: E402
from trading_bot.core.csc.research.method_spec import (  # noqa: E402
    compile_rule, spec_from_dict)
from train_world_model import load_features, ridge_pred_np  # noqa: E402
from train_rv_forecaster import (  # noqa: E402
    GRUForecaster, HORIZONS)
from rv_walkforward_eval import featurize  # noqa: E402

SEQ = 60
COST_FLOOR_BPS = 5.0
EVAL_FRAC = 0.40
EMBARGO = 20


def build_regime(db, symbol, timeframe, bars_n, ckpt):
    """rv16 blend forecast -> per-decision-bar tercile (0/1/2, -1 none).
    Mirrors vol_regime_gate.py's verified pipeline."""
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        db, symbol, timeframe, bars_n)
    n = len(rows)
    closes = np.array([r[4] for r in rows], dtype=float)
    feats = featurize(rows, ret, rng, vol_z, mom8, roll_std, hour).numpy()
    p = torch.load(ckpt, map_location="cpu", weights_only=False)
    net = GRUForecaster(
        in_dim=p["state_dict"]["gru.weight_ih_l0"].shape[1],
        hidden=p["state_dict"]["gru.weight_hh_l0"].shape[1])
    net.load_state_dict(p["state_dict"])
    net.eval()
    rdg = {k: tuple(np.array(m) for m in v)
           for k, v in p["ridge"].items()}
    y_mu, y_sd = np.array(p["y_mean"]), np.array(p["y_std"])
    bw = p.get("blend_w", 0.5)

    j_all = np.arange(SEQ, n - max(HORIZONS))
    preds = np.empty((len(j_all), len(HORIZONS)))
    with torch.no_grad():
        for a in range(0, len(j_all), 4096):
            js = j_all[a:a + 4096]
            w = torch.tensor(
                feats[np.stack([np.arange(j - SEQ, j) for j in js])])
            preds[a:a + len(js)] = net(w).numpy()
    gru_p = preds * y_sd + y_mu
    rp = np.stack([ridge_pred_np(rdg[str(h)], feats[j_all - 1])
                   for h in HORIZONS], axis=1)
    bp = bw * gru_p + (1 - bw) * rp
    rv16_ratio = np.exp(bp[:, 2])

    cut = int(len(j_all) * 0.6)
    q1, q2 = np.quantile(rv16_ratio[:cut], [1 / 3, 2 / 3])
    regime = np.full(n, -1, dtype=int)
    for k, j in enumerate(j_all):
        t = j - 1
        if 0 <= t < n:
            regime[t] = (0 if rv16_ratio[k] <= q1
                         else 2 if rv16_ratio[k] > q2 else 1)
    return closes, regime


def regime_verdict(closes, rule_fn, regime, horizon, cost_bps,
                   n_segments=3):
    """evaluate() per-trade math, bucketed by decision-bar regime."""
    n = len(closes)
    disc_end = int(n * (1.0 - EVAL_FRAC))
    eval_start = disc_end + EMBARGO
    eval_end = n
    buckets = {-1: [], 0: [], 1: [], 2: []}
    for i in range(eval_start, min(eval_end, n - horizon)):
        s = rule_fn(closes, i)
        if s == 0:
            continue
        fwd = (closes[i + horizon] - closes[i]) / closes[i] * 1e4
        net = s * fwd - cost_bps
        buckets[int(regime[i])].append(net)

    names = {-1: "unregimed", 0: "low_fvol", 1: "mid_fvol",
             2: "high_fvol"}
    out = {}
    all_net = []
    for tag in (-1, 0, 1, 2):
        nets = np.asarray(buckets[tag], dtype=float)
        all_net.extend(nets.tolist())
        rec = {"trades": int(len(nets))}
        if len(nets) >= 30:
            m, l = block_bootstrap_lcb(nets)
            h = len(nets) // 2
            rec.update({"mean_net_bps": round(m, 3),
                        "lcb5_net_bps": round(l, 3),
                        "h1_mean": round(float(np.mean(nets[:h])), 3),
                        "h2_mean": round(float(np.mean(nets[h:])), 3)})
        else:
            rec["status"] = "insufficient_evidence"
        out[names[tag]] = rec
    if len(all_net) >= 30:
        m, l = block_bootstrap_lcb(np.asarray(all_net))
        out["global"] = {"trades": len(all_net),
                         "mean_net_bps": round(m, 3),
                         "lcb5_net_bps": round(l, 3)}
    return {"eval_window": [eval_start, eval_end],
            "horizon": horizon, "cost_bps": round(cost_bps, 2),
            "regimes": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--spec-file", required=True,
                    help="MethodSpec JSON (spec_from_dict shape)")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--cost-bps", type=float, default=COST_FLOOR_BPS)
    ap.add_argument("--ckpt", default="var/rv_blend_forecaster.pt")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    spec = spec_from_dict(json.loads(
        Path(args.spec_file).read_text()))
    rule_fn = compile_rule(spec)

    closes, regime = build_regime(args.db, args.symbol, args.timeframe,
                                  args.bars, args.ckpt)
    n = len(closes)
    print(f"[{args.symbol}] {n} bars; regime coverage "
          f"{int((regime >= 0).sum())}/{n}", flush=True)

    cost = max(roll_spread_bps(closes) or 0.0, args.cost_bps)
    res = regime_verdict(closes, rule_fn, regime, args.horizon, cost)
    res["spec_id"] = spec.spec_id
    res["family"] = spec.family
    res["dataset"] = f"{args.db}:{args.symbol}:{args.timeframe}"

    print(f"spec={spec.spec_id} family={spec.family} "
          f"horizon={args.horizon} cost={cost:.2f}bps")
    for name, rec in res["regimes"].items():
        if "mean_net_bps" in rec:
            extra = (f" h1={rec['h1_mean']:+.2f} "
                     f"h2={rec['h2_mean']:+.2f}"
                     if "h1_mean" in rec else "")
            print(f"  {name:10s} n={rec['trades']:5d} "
                  f"mean={rec['mean_net_bps']:+.2f} "
                  f"lcb={rec['lcb5_net_bps']:+.2f}{extra}")
        else:
            print(f"  {name:10s} n={rec['trades']:5d} "
                  f"({rec.get('status', 'thin')})")

    out = args.out or f"var/regime_split_{spec.spec_id}.json"
    Path(out).parent.mkdir(exist_ok=True)
    Path(out).write_text(json.dumps(res, indent=2))
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
