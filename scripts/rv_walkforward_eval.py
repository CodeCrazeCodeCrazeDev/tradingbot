"""Multi-fold walk-forward evaluation of realized-vol forecasts.

The single 70/30 chronological split used by train_rv_forecaster.py is
one regime boundary — a passing gate can still be an adjacent-regime
artifact (the +0.32 range R2 that did not transfer was exactly that).
This harness re-judges the same task the way edge_gate.py judges rules:
contiguous expanding-window folds, an embargo of S + H bars between
train and eval so no target window straddles the boundary, and the
same metrics per fold so temporal instability is visible.

Per fold it reports, for each horizon H in {4,8,16} (ratio space:
log(rv_H / trailing-21 mean|ret|), persistence = 0):
  * ridge_r2 / ridge_corr  — raw-feature ridge REFIT on that fold's
    train region (the honest "is there transferable linear signal here")
  * ckpt_r2 / ckpt_corr    — the saved blend artifact (GRU + stored
    ridge, fixed 50/50) applied untouched. Marked in_sample for folds
    inside the checkpoint's own train region (EURUSD only — other
    symbols were never in its training set and are pure transfer tests).

Verdict per horizon/series: mean fold R2, fraction of folds with R2 > 0,
min fold R2. A claim "transfers" only if it is positive on most folds.

Hermes env only (needs torch): keeps the single-thread guard.
"""

import argparse
import json
import subprocess
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)  # OpenMP threading deadlocks observed on this host

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from train_world_model import load_features, to_obs  # noqa: E402
from train_world_model import ridge_fit_np, ridge_pred_np  # noqa: E402
from train_rv_forecaster import GRUForecaster, HORIZONS, realized_vol  # noqa: E402


def featurize(rows, ret, rng, vol_z, mom8, roll_std, hour):
    featurizer = WorldModelV2(asset_dims={"FX": 64, "Equities": 128},
                              latent_dim=256)
    out = []
    for i in range(len(rows)):
        out.append(featurizer._obs_to_features(
            to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, i)))
        if (i + 1) % 10000 == 0:
            print(f"  featurized {i + 1}/{len(rows)}", flush=True)
    return torch.stack(out).float()


def ratio_targets(absret):
    """y[j, k] = log(rv_H[j] / roll21|ret|[j-1]); persistence = 0."""
    n = len(absret)
    H = max(HORIZONS)
    rv = np.stack([realized_vol(absret, h)[:n - H + 1]
                   for h in HORIZONS], axis=1)
    c = np.cumsum(np.concatenate([[0.0], absret]))
    roll = np.concatenate([np.full(20, np.nan), (c[21:] - c[:-21]) / 21.0])
    denom = np.concatenate([[np.nan], roll])[:len(rv), None]
    return np.log(np.maximum(rv, 1e-9) / np.maximum(denom, 1e-9))


def r2(pred, y):
    mse_b = float(np.mean(y ** 2))  # persistence = 0 in ratio space
    return 1.0 - float(np.mean((pred - y) ** 2)) / mse_b if mse_b else float("nan")


def _pinball(y, pred, tau):
    d = y - pred
    return float(np.mean(np.maximum(tau * d, (tau - 1.0) * d)))


def eval_quantiles(args, X_tr, y_tr, X_ev, y_ev, hi, hrec):
    """GBM pinball-regression vs the constant train-quantile baseline.

    skill = 1 - model_pinball/const_pinball (>0 = heteroscedastic
    information the unconditional quantile misses); coverage should
    approximate tau. Hermes-only import — sklearn lives there, not .venv.
    """
    from sklearn.ensemble import GradientBoostingRegressor
    for tau in args.quantiles:
        g = GradientBoostingRegressor(loss="quantile", alpha=tau,
                                      n_estimators=150, max_depth=2,
                                      learning_rate=0.05, random_state=0)
        g.fit(X_tr, y_tr[:, hi])
        qp = g.predict(X_ev)
        q_const = float(np.quantile(y_tr[:, hi], tau))
        pin_m, pin_b = _pinball(y_ev[:, hi], qp, tau), \
            _pinball(y_ev[:, hi], q_const, tau)
        tag = f"q{int(round(tau * 100))}"
        hrec[f"{tag}_skill"] = (1.0 - pin_m / pin_b) if pin_b else float("nan")
        hrec[f"{tag}_coverage"] = float(np.mean(y_ev[:, hi] <= qp))


def eval_symbol(args, symbol, ckpt, ckpt_train_end):
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, symbol, args.timeframe, args.bars)
    print(f"[{symbol}] bars after grid filter: {len(rows)}", flush=True)
    feats = featurize(rows, ret, rng, vol_z, mom8, roll_std, hour).numpy()
    n = len(feats)
    S, H = args.seq, max(HORIZONS)
    y = ratio_targets(np.abs(ret))[:n]
    ts = [str(r[0]) for r in rows]

    eval_start = max(int(n * (1.0 - args.eval_frac)), S + args.min_train)
    seg = (n - eval_start) // args.folds
    folds = []
    for k in range(args.folds):
        e0 = eval_start + k * seg
        e1 = n if k == args.folds - 1 else e0 + seg
        j_ev = np.arange(e0, min(e1, n - H + 1))
        j_tr = np.arange(S, e0 - H)          # embargo: targets end < e0
        j_tr = j_tr[np.isfinite(y[j_tr]).all(1)]
        j_ev = j_ev[np.isfinite(y[j_ev]).all(1)]
        if len(j_ev) < 50:
            continue
        rec = {"fold": k, "eval_span": [ts[e0], ts[min(e1 - 1, n - 1)]],
               "n_eval": int(len(j_ev)), "train_end": ts[e0 - 1],
               "in_sample_ckpt": bool(ckpt_train_end and e0 < ckpt_train_end),
               "horizons": {}}
        X_tr, X_ev = feats[j_tr - 1], feats[j_ev - 1]
        for hi, hh in enumerate(HORIZONS):
            mr = ridge_fit_np(X_tr, y[j_tr, hi], lam=args.lam)
            rec["horizons"][f"rv{hh}"] = {
                "ridge_r2": r2(ridge_pred_np(mr, X_ev), y[j_ev, hi]),
                "target_var": float(np.mean(y[j_ev, hi] ** 2)),
            }
            if args.quantile:
                eval_quantiles(args, X_tr, y[j_tr], X_ev, y[j_ev],
                               hi, rec["horizons"][f"rv{hh}"])
        if ckpt is not None:
            net, y_mu, y_sd, rdg, bw = ckpt
            preds = []
            with torch.no_grad():
                for a in range(0, len(j_ev), 4096):
                    w = torch.tensor(
                        feats[np.stack([np.arange(j - S, j)
                                        for j in j_ev[a:a + 4096]])])
                    preds.append(net(w).numpy())
            gru_p = np.concatenate(preds) * y_sd + y_mu
            for hi, hh in enumerate(HORIZONS):
                rp = ridge_pred_np(rdg[str(hh)], X_ev)
                bp = bw * gru_p[:, hi] + (1 - bw) * rp
                rec["horizons"][f"rv{hh}"].update({
                    "ckpt_r2": r2(bp, y[j_ev, hi]),
                    "ckpt_corr": float(np.corrcoef(bp, y[j_ev, hi])[0, 1]),
                })
        folds.append(rec)
        print(f"  fold {k}: {rec['eval_span'][0][:10]}.. "
              f"ridge rv16 r2={rec['horizons']['rv16']['ridge_r2']:+.3f}"
              + (f"  ckpt={rec['horizons']['rv16'].get('ckpt_r2', 0):+.3f}"
                 if ckpt else ""), flush=True)

    summary = {}
    for hi, hh in enumerate(HORIZONS):
        keys = {"ridge_r2", "ckpt_r2"}
        for f in folds:
            keys.update(k for k in f["horizons"][f"rv{hh}"]
                        if k.startswith("q") and k.endswith(
                            ("_skill", "_coverage")))
        for key in sorted(keys):
            vals = [f["horizons"][f"rv{hh}"].get(key) for f in folds]
            vals = [v for v in vals if v is not None]
            if vals:
                entry = {
                    "mean": float(np.mean(vals)),
                    "min": float(np.min(vals)),
                    "folds_positive": f"{sum(v > 0 for v in vals)}/{len(vals)}",
                }
                if key.endswith("_coverage"):
                    tau = float(key[1:3]) / 100.0
                    entry["target_coverage"] = tau
                summary[f"rv{hh}.{key}"] = entry
    return {"n_bars": n, "folds": folds, "summary": summary}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbols", default="EURUSD,GBPUSD,USDJPY")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--seq", type=int, default=32)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--eval-frac", type=float, default=0.35,
                    help="tail fraction carved into contiguous eval folds")
    ap.add_argument("--min-train", type=int, default=5000)
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--ckpt", default="var/rv_blend_forecaster.pt")
    ap.add_argument("--quantile", action="store_true",
                    help="also fit GBM quantile regressors per fold "
                         "(hermes env — sklearn)")
    ap.add_argument("--quantiles", default="0.5,0.8,0.95")
    ap.add_argument("--out", default="var/rv_walkforward.json")
    args = ap.parse_args()
    args.quantiles = [float(t) for t in str(args.quantiles).split(",")]

    ckpt, ckpt_train_end = None, None
    if args.ckpt and Path(args.ckpt).exists():
        p = torch.load(args.ckpt, map_location="cpu", weights_only=False)
        net = GRUForecaster(in_dim=p["state_dict"]["gru.weight_ih_l0"]
                            .shape[1], hidden=args_hidden(p))
        net.load_state_dict(p["state_dict"])
        net.eval()
        rdg = {k: tuple(np.array(m) for m in v) for k, v in p["ridge"].items()}
        ckpt = (net, np.array(p["y_mean"]), np.array(p["y_std"]),
                rdg, p.get("blend_w", 0.5))
        meta_p = Path(args.ckpt.replace(".pt", ".train_meta.json"))
        if meta_p.exists():
            ckpt_train_end = json.loads(meta_p.read_text()).get("split")
        print(f"ckpt loaded (train_end={ckpt_train_end})", flush=True)

    report = {"args": vars(args), "horizons": HORIZONS, "symbols": {}}
    for sym in args.symbols.split(","):
        report["symbols"][sym] = eval_symbol(
            args, sym.strip(), ckpt, ckpt_train_end if sym.strip() == "EURUSD"
            else None)
    try:
        report["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass
    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> wrote {args.out}")
    for sym, s in report["symbols"].items():
        print(sym, json.dumps(s["summary"], indent=2))


def args_hidden(p):
    return p["state_dict"]["gru.weight_hh_l0"].shape[1]


if __name__ == "__main__":
    main()
