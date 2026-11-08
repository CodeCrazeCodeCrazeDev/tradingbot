"""Train GBM quantile heads for the RV-ratio forecast (P50/P80/P95).

Sibling of train_rv_forecaster.py: same featurization, same ratio
targets, same chronological protocol — but predicts quantiles of the
log vol-change factor, which is what position sizing and kill-switch
thresholds consume (a mean forecast cannot bound the tail).

Per fold evidence already exists (scripts/rv_walkforward_eval.py
--quantile): 5/5 folds positive pinball skill at every tau on EURUSD.
This script produces the deployable artifact with its own held-out
gate so a saved model is never an unmeasured claim:

  gate: rv16 pinball skill > 0 at q80 AND q95 on the held-out tail,
        with one-sided coverage: under-coverage > 0.05 below tau fails
        (an upper bound that misses its tail is dangerous), while
        over-coverage up to +0.15 is tolerated — a risk bound that is
        too wide in a low-vol regime errs the right way.

Hermes env only (sklearn + torch). USDJPY needs its own artifact
(--symbol USDJPY --out var/rv_quantile_jpy.joblib) — EURUSD weights
do not transfer there.
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
from train_rv_forecaster import HORIZONS  # noqa: E402
from rv_walkforward_eval import ratio_targets  # noqa: E402


def _pinball(y, pred, tau):
    d = y - pred
    return float(np.mean(np.maximum(tau * d, (tau - 1.0) * d)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--train-frac", type=float, default=0.7)
    ap.add_argument("--quantiles", default="0.5,0.8,0.95")
    ap.add_argument("--out", default="var/rv_quantile_forecaster.joblib")
    args = ap.parse_args()
    taus = [float(t) for t in str(args.quantiles).split(",")]

    from sklearn.ensemble import GradientBoostingRegressor
    import joblib

    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    print(f"bars after grid filter: {len(rows)}", flush=True)

    featurizer = WorldModelV2(asset_dims={"FX": 64, "Equities": 128},
                              latent_dim=256)
    feats = torch.stack([featurizer._obs_to_features(
        to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, i))
        for i in range(len(rows))]).float().numpy()
    n = len(feats)
    S = 32
    y = ratio_targets(np.abs(ret))[:n]
    split = int(n * args.train_frac)
    H = max(HORIZONS)

    j_tr = np.arange(S, split)
    j_ev = np.arange(split, n - H + 1)
    j_tr = j_tr[np.isfinite(y[j_tr]).all(1)]
    j_ev = j_ev[np.isfinite(y[j_ev]).all(1)]
    X_tr, X_ev = feats[j_tr - 1], feats[j_ev - 1]

    models, results = {}, {}
    for hi, hh in enumerate(HORIZONS):
        hres = {}
        for tau in taus:
            g = GradientBoostingRegressor(loss="quantile", alpha=tau,
                                          n_estimators=150, max_depth=2,
                                          learning_rate=0.05,
                                          random_state=0)
            g.fit(X_tr, y[j_tr, hi])
            qp = g.predict(X_ev)
            pin_m = _pinball(y[j_ev, hi], qp, tau)
            pin_b = _pinball(y[j_ev, hi],
                             float(np.quantile(y[j_tr, hi], tau)), tau)
            tag = f"q{int(round(tau * 100))}"
            hres[tag] = {"skill": (1.0 - pin_m / pin_b) if pin_b else
                         float("nan"),
                         "coverage": float(np.mean(y[j_ev, hi] <= qp))}
            models.setdefault(str(hh), {})[tag] = g
            print(f"  rv{hh} {tag}: skill={hres[tag]['skill']:+.4f} "
                  f"coverage={hres[tag]['coverage']:.3f}", flush=True)
        results[f"rv{hh}"] = hres

    r16 = results["rv16"]
    gate = (r16["q80"]["skill"] > 0 and r16["q95"]["skill"] > 0
            and r16["q80"]["coverage"] >= 0.75
            and r16["q80"]["coverage"] <= 0.95
            and r16["q95"]["coverage"] >= 0.90
            and r16["q95"]["coverage"] <= 0.995)
    meta = {"args": vars(args), "horizons": HORIZONS, "quantiles": taus,
            "n_bars": n, "split": split, "results": results}
    try:
        meta["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass

    Path("var").mkdir(exist_ok=True)
    if gate:
        joblib.dump({"models": models, "meta": meta}, args.out)
        print(f"-> saved {args.out}")
    else:
        print("-> NOT saved: gate failed — honest rejection")
    Path(args.out.rsplit(".", 1)[0] + ".train_meta.json").write_text(
        json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
