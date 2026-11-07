"""Train a small GRU volatility forecaster on raw features.

Direct observable-space objective — no latent bottleneck: a 32-bar
window of the same 64-dim featurization the world model consumed
predicts [next-bar range, next-bar |log return|]. Targets standardized
on train-split stats.

Save gate (all must hold on the chronological held-out tail):
  1. range R2 > 0 vs persistence baseline (next range = current range)
  2. range R2 > raw-feature ridge R2 fit on the same train split —
     the GRU sees strictly more information (32 bars) than the ridge
     (last bar); failing to beat it means temporal context adds nothing.

Shares load_features/on_grid with train_world_model.py — spliced
off-grid rows are dropped there.
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


class GRUForecaster(nn.Module):
    def __init__(self, in_dim: int = 64, hidden: int = 64):
        super().__init__()
        self.gru = nn.GRU(in_dim, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 2)  # [next_range, next_|ret|]

    def forward(self, x):
        h, _ = self.gru(x)
        return self.head(h[:, -1, :])


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
    ap.add_argument("--out", default="var/vol_forecaster.pt")
    args = ap.parse_args()

    torch.manual_seed(0)
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    print(f"bars after grid filter: {len(rows)}", flush=True)

    # featurize identically to the world-model pipeline
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

    absret = np.abs(ret)
    y_all = np.stack([rng, absret], axis=1)
    y_tr = y_all[S:split]
    y_mu, y_sd = y_tr.mean(0), y_tr.std(0) + 1e-12
    y_n = (y_all - y_mu) / y_sd

    net = GRUForecaster(in_dim=feats.shape[1], hidden=args.hidden)
    n_params = sum(p.numel() for p in net.parameters())
    opt = optim.AdamW(net.parameters(), lr=args.lr)
    print(f"model params: {n_params}", flush=True)

    for step in range(1, args.steps + 1):
        idx = torch.randint(0, len(train) - S - 1, (args.batch,))
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
    ev_idx = torch.randint(0, len(held) - S - 1, (args.eval_windows,),
                           generator=g)
    gidx = split + ev_idx.numpy() + S
    with torch.no_grad():
        win = torch.stack([held[i:i + S] for i in ev_idx])
        pred = net(win).numpy() * y_sd + y_mu
    y_true = y_all[gidx]
    y_base = np.stack([rng[gidx - 1], roll_std[gidx - 1]], axis=1)

    def r2(p, y, b):
        mse_b = float(np.mean((b - y) ** 2))
        return 1.0 - float(np.mean((p - y) ** 2)) / mse_b if mse_b else float("nan")

    r2_range = r2(pred[:, 0], y_true[:, 0], y_base[:, 0])
    r2_absret = r2(pred[:, 1], y_true[:, 1], y_base[:, 1])

    # raw-feature ridge reference (no temporal context): last bar -> target
    tr_idx = torch.randint(0, split - S - 1, (20000,), generator=g).numpy()
    Xr_tr = feats[tr_idx + S - 1].numpy()
    Xr_ev = feats[split + ev_idx.numpy() + S - 1].numpy()
    raw_r2 = {}
    for k, name in ((0, "range"), (1, "absret")):
        mr = ridge_fit_np(Xr_tr, y_all[tr_idx + S, k])
        raw_r2[name] = r2(ridge_pred_np(mr, Xr_ev), y_true[:, k],
                          y_base[:, k])

    print(f"\nheld-out: gru R2 range={r2_range:+.4f} absret={r2_absret:+.4f} "
          f"| raw-ridge R2 range={raw_r2['range']:+.4f} "
          f"absret={raw_r2['absret']:+.4f}")

    meta = {
        "args": vars(args), "n_bars": n, "split": split,
        "n_params": n_params,
        "y_mean": y_mu.tolist(), "y_std": y_sd.tolist(),
        "r2_range": r2_range, "r2_absret": r2_absret, "raw_r2": raw_r2,
    }
    try:
        meta["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass

    Path("var").mkdir(exist_ok=True)
    gate = r2_range > 0 and r2_range > raw_r2["range"]
    if gate:
        torch.save({"state_dict": net.state_dict(), "args": vars(args),
                    "y_mean": y_mu.tolist(), "y_std": y_sd.tolist()},
                   args.out)
        print(f"-> saved {args.out}")
    else:
        print("-> NOT saved: gate failed "
              f"(range R2 {r2_range:+.4f} must be > 0 and > raw "
              f"{raw_r2['range']:+.4f}) — honest rejection")
    Path(args.out.replace(".pt", ".train_meta.json")).write_text(
        json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
