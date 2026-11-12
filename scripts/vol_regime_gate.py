#!/usr/bin/env python
"""Vol-regime monetization gate — last untested edge channel.

Question: the rv16 blend forecast is the only VERIFIED transferable
skill (walk-forward R2 +0.43 EURUSD, zero-shot GBPUSD). Can it
MONETIZE? Not direction — vol forecasts don't point anywhere. Three
structures, all bounded, all net of turnover cost:

  mom_flat / mom_high / mom_low   — momentum(10,15bps) unconditional
                                  vs gated to forecast-vol terciles
  mr_low / mr_high                — meanrev(20,2sd) gated likewise
  regime_switch                   — momentum in high-fvol tercile,
                                  meanrev in low-fvol (the hypothesis:
                                  vol regime selects which anomaly pays)
  invvol_size                     — momentum sized ~1/fvol_hat

Forecasts: blend checkpoint var/rv_blend_forecaster.pt (GRU+ridge,
log(rv16/roll21|ret|) target), inference identical to
rv_walkforward_eval.py — window S=32 feats -> net -> blend. Regime
terciles fixed on the first 60% of the forecast range, applied to the
last 40% (already OOS for the checkpoint); inside eval: 60/40 split,
3 contiguous segments, block-bootstrap LCB5. Candidate needs every
segment LCB>0 AND mean>0 — same gate philosophy as every other script.

HERMES ENV ONLY (torch + the WorldModelV2 featurizer):
  %LOCALAPPDATA%/hermes/hermes-agent/venv/Scripts/python.exe \
      scripts/vol_regime_gate.py --out var/vol_regime_gate.json
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)

from edge_baseline import block_bootstrap_lcb  # noqa: E402
from train_world_model import load_features  # noqa: E402
from train_rv_forecaster import GRUForecaster, HORIZONS, realized_vol  # noqa: E402
from rv_walkforward_eval import featurize, ratio_targets  # noqa: E402
from train_world_model import ridge_pred_np  # noqa: E402

COST_BPS = 5.0
SEQ = 32


def mom_rule(closes, i, lookback=10, th_bps=15.0):
    if i < lookback:
        return 0.0
    base = closes[i - lookback]
    if base <= 0:
        return 0.0
    r = (closes[i] - base) / base * 1e4
    if r > th_bps:
        return 1.0
    if r < -th_bps:
        return -1.0
    return 0.0


def mr_rule(closes, i, window=20, z=2.0):
    if i < window:
        return 0.0
    w = closes[i - window + 1:i + 1]
    m, s = float(np.mean(w)), float(np.std(w))
    if s <= 0:
        return 0.0
    dev = (closes[i] - m) / s
    if dev > z:
        return -1.0
    if dev < -z:
        return 1.0
    return 0.0


def pnl_series(pos, ret_bps, cost_bps):
    """pos[t] earns ret[t->t+1]; charge cost on position changes."""
    pos = np.asarray(pos, dtype=float)
    dpos = np.abs(np.diff(np.concatenate([[0.0], pos])))
    return pos * ret_bps - dpos * cost_bps


def gate_metrics(pnl):
    n = len(pnl)
    if n < 300:
        return {"status": "insufficient", "n": n}
    split = int(n * 0.6)
    ev = pnl[split:]
    if len(ev) < 200:
        return {"status": "insufficient_eval", "n": len(ev)}
    m, l = block_bootstrap_lcb(ev)
    seg_n = len(ev) // 3
    segs = []
    for k in range(3):
        a, b = k * seg_n, (k + 1) * seg_n if k < 2 else len(ev)
        ms, ls = block_bootstrap_lcb(ev[a:b])
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    ok = all(s["lcb5"] > 0 for s in segs) and m > 0
    return {"n": n, "eval_n": len(ev), "mean_bps": round(m, 3),
            "lcb5": round(l, 3), "segments": segs,
            "verdict": "candidate" if ok else "rejected"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--ckpt", default="var/rv_blend_forecaster.pt")
    ap.add_argument("--cost-bps", type=float, default=COST_BPS)
    ap.add_argument("--out", default="var/vol_regime_gate.json")
    args = ap.parse_args()

    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    closes = np.array([r[4] for r in rows], dtype=float)
    n = len(closes)
    print(f"[{args.symbol}] {n} bars {rows[0][0]}..{rows[-1][0]}",
          flush=True)

    feats = featurize(rows, ret, rng, vol_z, mom8, roll_std, hour).numpy()
    p = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    net = GRUForecaster(
        in_dim=p["state_dict"]["gru.weight_ih_l0"].shape[1],
        hidden=p["state_dict"]["gru.weight_hh_l0"].shape[1])
    net.load_state_dict(p["state_dict"])
    net.eval()
    rdg = {k: tuple(np.array(m) for m in v)
           for k, v in p["ridge"].items()}
    y_mu, y_sd = np.array(p["y_mean"]), np.array(p["y_std"])
    bw = p.get("blend_w", 0.5)

    # forecast rv16 log-ratio for every eligible target-start j:
    # feats[j-1] window -> net; ridge on feats[j-1]; blend bw
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
    rv16_ratio = np.exp(bp[:, 2])          # predicted rv16/roll ratio

    # decision bar t uses forecast whose target starts at t+1:
    # pred index k corresponds to j_all[k] = j -> regime[t=j-1]
    reg_j = rv16_ratio                     # indexed by position in j_all
    t_of_j = j_all - 1                     # decision bar for that forecast

    # split forecast range 60/40 -> terciles on first 60%
    cut = int(len(j_all) * 0.6)
    tr_vals = reg_j[:cut]
    q1, q2 = np.quantile(tr_vals, [1 / 3, 2 / 3])
    regime = np.full(n, -1, dtype=int)     # 0 low, 1 mid, 2 high fvol
    for k, j in enumerate(j_all):
        t = j - 1
        if t < 0 or t >= n:
            continue
        regime[t] = 0 if reg_j[k] <= q1 else (2 if reg_j[k] > q2 else 1)

    # eval region: last 40% of forecast range -> decision bars
    eval_t = t_of_j[cut:]
    eval_mask = np.zeros(n, dtype=bool)
    eval_mask[eval_t] = True
    idx = np.where(eval_mask)[0]
    idx = idx[(idx >= 60) & (idx < n - 2)]
    print(f"eval bars: {len(idx)}  regimes: "
          f"{np.bincount(regime[idx][regime[idx] >= 0])}", flush=True)

    ret_bps = np.diff(closes) / closes[:-1] * 1e4   # ret[t->t+1] at t
    ret_bps = np.concatenate([ret_bps, [0.0]])

    # precompute rule signals over all bars
    mom_sig = np.array([mom_rule(closes, i) for i in range(n)])
    mr_sig = np.array([mr_rule(closes, i) for i in range(n)])

    results = {}

    def pos_for(sig, gate=None, scale=None):
        pos = np.zeros(n)
        for i in idx:
            if gate is None or gate(i):
                s = sig[i]
                if scale is not None:
                    s = s * scale(i)
                pos[i] = s
        return pos

    def add(name, pos):
        pnl = pnl_series(pos, ret_bps, args.cost_bps)
        results[name] = gate_metrics(pnl[idx])
        r = results[name]
        print(f"{name:16s} mean={r.get('mean_bps')} lcb={r.get('lcb5')} "
              f"-> {r.get('verdict', r.get('status'))}", flush=True)

    add("mom_flat", pos_for(mom_sig))
    add("mom_highvol", pos_for(mom_sig, lambda i: regime[i] == 2))
    add("mom_lowvol", pos_for(mom_sig, lambda i: regime[i] == 0))
    add("mr_lowvol", pos_for(mr_sig, lambda i: regime[i] == 0))
    add("mr_highvol", pos_for(mr_sig, lambda i: regime[i] == 2))

    pos = np.zeros(n)
    for i in idx:
        if regime[i] == 2:
            pos[i] = mom_sig[i]
        elif regime[i] == 0:
            pos[i] = mr_sig[i]
    add("regime_switch", pos)

    med = float(np.median(reg_j[reg_j > 0]))
    def invvol_scale(i):
        # regime index -> forecast value via nearest j (t=i -> j=i+1)
        j = i + 1
        k = j - SEQ  # position in j_all only if j in range; fallback med
        if 0 <= k < len(reg_j) and j_all[k] == j:
            fv = reg_j[k]
        else:
            fv = med
        return float(np.clip(med / max(fv, 1e-6), 0.25, 1.5))

    add("invvol_size", pos_for(mom_sig, None, invvol_scale))

    report = {
        "gate": {"symbol": args.symbol, "timeframe": args.timeframe,
                 "bars": n, "cost_bps": args.cost_bps,
                 "ckpt": args.ckpt, "seq": SEQ,
                 "regime_terciles": [float(q1), float(q2)],
                 "forecast_range": [str(rows[j_all[0]][0]),
                                    str(rows[j_all[-1]][0])]},
        "structures": results,
        "note": "regime terciles fixed on first 60% of forecast range; "
                "eval = last 40% (checkpoint-OOS); positions per-bar, "
                "cost on turnover; candidate needs all-segment LCB>0",
    }
    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> {args.out}")
    cands = [k for k, v in results.items() if v.get("verdict") == "candidate"]
    print("CANDIDATES:", cands if cands else "none — honest null")
    return 0


if __name__ == "__main__":
    sys.exit(main())
