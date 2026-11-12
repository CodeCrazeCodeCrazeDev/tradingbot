"""Train a small GRU realized-volatility forecaster at multiple horizons.

Targets: rv_H[i] = mean(|log ret|) over bars i..i+H-1 for H in {4,8,16}
— the forward-looking realized vol the model must anticipate. Longer
horizons smooth idiosyncratic noise and expose exploitable structure
(vol mean-reversion, intraday seasonality via hour_sin/hour_cos) that
a next-bar point forecast cannot see.

Baseline per horizon: rolling 21-bar mean|ret| at the last context bar
(vol-level persistence — matched units). Reference: raw-feature ridge
fit on the same train split (it keeps hour_sin/hour_cos, so linear
seasonality is available to the baseline too).

Save gate: rv16 R2 > 0 AND > raw-feature ridge rv16 R2 on the same
held-out tail. Shares the filtered load_features/on_grid path with
train_world_model.py — spliced off-grid rows are dropped there.
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

import torch.nn as nn  # noqa: E402
import torch.optim as optim  # noqa: E402

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from train_world_model import load_features, to_obs  # noqa: E402
from train_world_model import ridge_fit_np, ridge_pred_np  # noqa: E402

HORIZONS = (4, 8, 16)


class GRUForecaster(nn.Module):
    def __init__(self, in_dim: int = 64, hidden: int = 64,
                 out_dim: int = len(HORIZONS)):
        super().__init__()
        self.gru = nn.GRU(in_dim, hidden, batch_first=True)
        self.head = nn.Linear(hidden, out_dim)

    def forward(self, x):
        h, _ = self.gru(x)
        return self.head(h[:, -1, :])


def realized_vol(absret, H):
    """rv[i] = mean |ret| over bars i..i+H-1. Valid for i <= n-H."""
    c = np.cumsum(np.concatenate([[0.0], absret]))
    return (c[H:] - c[:-H]) / H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--seq", type=int, default=32)
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--eval-windows", type=int, default=2048)
    ap.add_argument("--ratio", action="store_true",
                    help="target log(rv/rolling-mean|ret|) — vol-change "
                         "factor; persistence becomes the zero forecast")
    ap.add_argument("--blend", action="store_true",
                    help="candidate = fixed 50/50 mean of GRU and ridge "
                         "predictions (declared a priori, not fitted)")
    ap.add_argument("--blend-w", type=float, default=0.5,
                    help="GRU weight in the ridge blend (1-w = ridge)")
    ap.add_argument("--ablate", default="none",
                    help="comma list of obs signals to zero before "
                         "featurization: hour,mom8,vol_z,rng,"
                         "roll_std (ret excluded — it feeds the rv "
                         "targets); presets: price_only,vol_only")
    ap.add_argument("--out", default="var/rv_forecaster.pt")
    args = ap.parse_args()

    torch.manual_seed(0)
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    print(f"bars after grid filter: {len(rows)}", flush=True)

    # Feature ablation (model-engineering search): zero selected
    # derived-signal arrays BEFORE featurization. ret is excluded —
    # absret feeds the rv targets, so ablating it would corrupt y.
    _ABLATE_PRESETS = {
        "price_only": ["rng", "vol_z", "mom8", "roll_std", "hour"],
        "vol_only": ["mom8", "hour"],
    }
    _ABLATE_VARS = {"rng": rng, "vol_z": vol_z, "mom8": mom8,
                    "roll_std": roll_std, "hour": hour}
    _abl = args.ablate.split(",") if args.ablate != "none" else []
    for _p in _abl:
        _abl += _ABLATE_PRESETS.get(_p.strip(), [])
    for _name in dict.fromkeys(_abl):
        _v = _ABLATE_VARS.get(_name.strip())
        if _v is not None:
            _v[:] = 0.0
    if _abl:
        print(f"ablated features: {sorted(set(_abl))}", flush=True)

    featurizer = WorldModelV2(asset_dims={"FX": 64, "Equities": 128},
                              latent_dim=256)
    feat_list = []
    for i in range(len(rows)):
        feat_list.append(featurizer._obs_to_features(
            to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, i)))
        if (i + 1) % 10000 == 0:
            print(f"  featurized {i + 1}/{len(rows)}", flush=True)
    feats = torch.stack(feat_list).float()

    n = len(feats)
    split = int(n * 0.7)
    train, held = feats[:split], feats[split:]
    S = args.seq
    H = max(HORIZONS)

    absret = np.abs(ret)
    rv = np.stack([realized_vol(absret, h)[:n - H + 1]
                   for h in HORIZONS], axis=1)
    # rv[j, k] = mean|ret| over j..j+HORIZONS[k]-1; all valid to n-H
    y_all = rv
    # trailing rolling-mean|ret| baseline (21 bars), matched units
    c = np.cumsum(np.concatenate([[0.0], absret]))
    roll_absret = (c[21:] - c[:-21]) / 21.0
    roll_absret = np.concatenate(
        [np.full(20, np.nan), roll_absret])  # first 20 undefined

    if args.ratio:
        # log vol-change factor vs current level; baseline = 0.
        # denom[j] = rolling mean|ret| ending at bar j-1 (pre-window).
        denom = np.concatenate([[np.nan], roll_absret])[:len(y_all), None]
        y_all = np.log(np.maximum(y_all, 1e-9) /
                       np.maximum(denom, 1e-9))
        print("targets: log(rv / rolling-mean|ret|)", flush=True)

    y_tr = y_all[S:split]
    y_mu, y_sd = y_tr.mean(0), y_tr.std(0) + 1e-12
    y_n = (y_all - y_mu) / y_sd

    net = GRUForecaster(in_dim=feats.shape[1], hidden=args.hidden)
    n_params = sum(p.numel() for p in net.parameters())
    opt = optim.AdamW(net.parameters(), lr=args.lr)
    print(f"model params: {n_params}", flush=True)

    max_i = len(train) - S - H - 1
    for step in range(1, args.steps + 1):
        idx = torch.randint(0, max_i, (args.batch,))
        win = torch.stack([train[i:i + S] for i in idx])
        yb = torch.tensor(y_n[idx.numpy() + S], dtype=torch.float32)
        net.train()
        loss = torch.nn.functional.mse_loss(net(win), yb)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
        opt.step()
        if step % 100 == 0:
            print(f"step {step:4d}  mse={loss.item():.6f}", flush=True)

    # ---- held-out evaluation ----
    net.eval()
    g = torch.Generator().manual_seed(0)
    ev_hi = len(held) - S - H - 1
    ev_idx = torch.randint(0, ev_hi, (args.eval_windows,), generator=g)
    gidx = split + ev_idx.numpy() + S          # global target-start bar
    with torch.no_grad():
        win = torch.stack([held[i:i + S] for i in ev_idx])
        pred = net(win).numpy() * y_sd + y_mu
    y_true = y_all[gidx]                        # rv starting at gidx
    if args.ratio:
        y_base = np.zeros_like(y_true)          # persistence = no change
    else:
        y_base = np.repeat(roll_absret[gidx - 1][:, None], 3, axis=1)

    def r2(p, y, b):
        mse_b = float(np.mean((b - y) ** 2))
        return 1.0 - float(np.mean((p - y) ** 2)) / mse_b if mse_b else float("nan")

    res = {}
    for k, hh in enumerate(HORIZONS):
        res[f"rv{hh}"] = {
            "r2": r2(pred[:, k], y_true[:, k], y_base[:, k]),
            "corr": float(np.corrcoef(pred[:, k], y_true[:, k])[0, 1]),
        }

    # raw-feature ridge reference per horizon (last context bar -> target)
    tr_idx = torch.randint(0, max_i, (20000,), generator=g).numpy()
    Xr_tr = feats[tr_idx + S - 1].numpy()
    Xr_ev = feats[split + ev_idx.numpy() + S - 1].numpy()
    ridge_models = {}
    ridge_pred = np.zeros_like(pred)
    for k, hh in enumerate(HORIZONS):
        mr = ridge_fit_np(Xr_tr, y_all[tr_idx + S, k])
        ridge_models[hh] = mr
        ridge_pred[:, k] = ridge_pred_np(mr, Xr_ev)
        res[f"rv{hh}"]["raw_r2"] = r2(ridge_pred[:, k],
                                      y_true[:, k], y_base[:, k])
        print(f"  rv{hh}: gru_r2={res[f'rv{hh}']['r2']:+.4f} "
              f"corr={res[f'rv{hh}']['corr']:+.4f} "
              f"raw_r2={res[f'rv{hh}']['raw_r2']:+.4f}", flush=True)

    if args.blend:
        bpred = 0.5 * (pred + ridge_pred)
        for k, hh in enumerate(HORIZONS):
            res[f"rv{hh}"]["blend_r2"] = r2(bpred[:, k],
                                            y_true[:, k], y_base[:, k])
            res[f"rv{hh}"]["blend_corr"] = float(
                np.corrcoef(bpred[:, k], y_true[:, k])[0, 1])
            print(f"  rv{hh} blend: r2={res[f'rv{hh}']['blend_r2']:+.4f} "
                  f"corr={res[f'rv{hh}']['blend_corr']:+.4f}", flush=True)

    meta = {
        "args": vars(args), "horizons": HORIZONS, "n_bars": n,
        "split": split, "n_params": n_params,
        "y_mean": y_mu.tolist(), "y_std": y_sd.tolist(), "results": res,
    }
    try:
        meta["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass

    Path("var").mkdir(exist_ok=True)
    r16 = res["rv16"]
    cand = r16["blend_r2"] if args.blend else r16["r2"]
    gate = cand > 0 and cand > r16["raw_r2"]
    if gate:
        payload = {"state_dict": net.state_dict(), "args": vars(args),
                   "horizons": HORIZONS,
                   "y_mean": y_mu.tolist(), "y_std": y_sd.tolist()}
        if args.blend:
            payload["blend_w"] = float(args.blend_w)
            payload["ridge"] = {str(h): ([m.tolist() for m in mr]
                                         if isinstance(mr, tuple) else mr)
                                for h, mr in ridge_models.items()}
        torch.save(payload, args.out)
        print(f"-> saved {args.out}")
    else:
        print("-> NOT saved: gate failed "
              f"(rv16 candidate R2 {cand:+.4f} must be > 0 and > raw "
              f"{r16['raw_r2']:+.4f}) — honest rejection")
    Path(args.out.replace(".pt", ".train_meta.json")).write_text(
        json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
