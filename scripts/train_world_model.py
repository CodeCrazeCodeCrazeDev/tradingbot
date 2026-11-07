"""Train WorldModelV2 (AMT stage) on market_data.db.

Self-supervised next-latent prediction on real OHLCV windows, plus a
jointly-trained observable decoder (next-bar range and |return|) so the
encoder is shaped to carry economically decodable information — not just
self-consistent latents.

Save gate (all must hold on the chronological held-out tail):
  1. latent skill: model_cos - persistence_cos > 0   (original check)
  2. decoder next-range R^2 >= raw-feature ridge R^2 on the same split —
     the latent must carry at least as much observable signal as the bar's
     own features. A trained flag without measured skill would be a lie.

Off-grid rows (spliced second-feed artifacts with fractional-second or
non-M15-aligned timestamps) are dropped in load_features — they produced
fake +-6.7% alternating returns in the June 2026 segment.
"""

import argparse
import json
import math
import re
import sqlite3
import subprocess
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)  # OpenMP threading deadlocks observed on this host

import torch.nn as nn  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import torch.optim as optim  # noqa: E402

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from trading_bot.world_model.v2_training import WorldModelSpecialistTrainer  # noqa: E402

_TF_MIN = {"M": 1, "H": 60, "D": 1440}


def grid_minutes(timeframe: str) -> int:
    m = re.match(r"^([MHD])(\d+)$", timeframe.upper())
    if not m:
        raise ValueError(f"unrecognized timeframe {timeframe!r}")
    return _TF_MIN[m.group(1)] * int(m.group(2))


def on_grid(ts: str, step_min: int) -> bool:
    m = re.search(r"T(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", ts)
    if m is None:
        return False
    h, mi, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return sec == 0.0 and (h * 60 + mi) % step_min == 0


def load_features(db: str, symbol: str, timeframe: str, limit: int):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT timestamp, open, high, low, close, volume FROM market_data "
        "WHERE symbol=? AND timeframe=? ORDER BY timestamp DESC LIMIT ?",
        (symbol, timeframe, limit)).fetchall()[::-1]
    con.close()
    step = grid_minutes(timeframe)
    rows = [r for r in rows if on_grid(str(r[0]), step)]
    if len(rows) < 100:
        raise SystemExit(f"insufficient bars: {len(rows)}")
    c = np.array([r[4] for r in rows], dtype=np.float64)
    h = np.array([r[2] for r in rows], dtype=np.float64)
    lo = np.array([r[3] for r in rows], dtype=np.float64)
    v = np.array([r[5] for r in rows], dtype=np.float64)
    ts = np.array([r[0] for r in rows], dtype=object)

    ret = np.diff(np.log(c), prepend=np.log(c[0]))
    rng = (h - lo) / np.maximum(c, 1e-12)
    vol_z = (v - v.mean()) / (v.std() + 1e-9)
    mom8 = np.concatenate([np.zeros(8), np.log(c[8:] / c[:-8])])
    roll_std = np.array([ret[max(0, i - 20):i + 1].std() for i in range(len(ret))])
    try:
        from datetime import datetime
        hour = np.array([datetime.fromisoformat(str(t).replace("Z", "+00:00")).hour
                         for t in ts], dtype=np.float64)
    except Exception:
        hour = np.zeros(len(c))
    return rows, ret, rng, vol_z, mom8, roll_std, hour


def to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, i):
    """Rebuild the observation dict a live cycle would produce, so the
    trained featurizer sees the same distribution as encode()."""
    r = rows[i]
    ts = str(r[0])
    try:
        from datetime import datetime
        h = datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
    except Exception:
        h = 0
    return {
        "timestamp": ts, "symbol": "EURUSD",
        "open": r[1], "high": r[2], "low": r[3], "close": r[4],
        "price": r[4], "volume": r[5],
        "returns": ret[i], "log_returns": ret[i],
        "volatility": roll_std[i], "volume_ratio": vol_z[i],
        "momentum": mom8[i], "session_hour": hour[i],
        "hour_sin": math.sin(h / 24 * 2 * math.pi),
        "hour_cos": math.cos(h / 24 * 2 * math.pi),
        "high_24h": r[2], "low_24h": r[3],
        "uncertainty": 0.2, "rsi": 50.0, "atr": rng[i],
        "trend": "FLAT", "regime": "FLAT",
    }


def build_decoder(latent_dim: int) -> nn.Module:
    """Observable-space head: context latent -> [next_range, next_|ret|]
    (targets standardized on train-split stats)."""
    return nn.Sequential(
        nn.Linear(latent_dim, 64), nn.GELU(), nn.Linear(64, 2))


def ridge_fit_np(X, Y, lam=1.0):
    mu, sd = X.mean(0, keepdims=True), X.std(0, keepdims=True) + 1e-9
    Xs = (X - mu) / sd
    W = np.linalg.solve(Xs.T @ Xs + lam * np.eye(Xs.shape[1]), Xs.T @ Y)
    return mu, sd, W


def ridge_pred_np(model_r, X):
    mu, sd, W = model_r
    return ((X - mu) / sd) @ W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--seq", type=int, default=32)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--latent", type=int, default=256)
    ap.add_argument("--fx-dim", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--dec-w", type=float, default=0.5,
                    help="weight of the observable decoder loss")
    ap.add_argument("--eval-windows", type=int, default=1024)
    ap.add_argument("--out", default="var/world_model_v2.pt")
    args = ap.parse_args()

    torch.manual_seed(0)
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    print(f"bars after grid filter: {len(rows)}", flush=True)

    model = WorldModelV2(asset_dims={"FX": args.fx_dim, "Equities": 128},
                         latent_dim=args.latent)
    dec = build_decoder(args.latent)
    opt_dec = optim.AdamW(dec.parameters(), lr=args.lr)

    # Featurize every bar through the model's own encode() path so the
    # training distribution exactly matches what the live pipeline feeds.
    feat_list = []
    for i in range(len(rows)):
        feat_list.append(model._obs_to_features(
            to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, i)))
        if (i + 1) % 5000 == 0:
            print(f"  featurized {i + 1}/{len(rows)}", flush=True)
    feats = torch.stack(feat_list).float()

    n = len(feats)
    split = int(n * 0.7)
    train, held = feats[:split], feats[split:]
    S = args.seq

    absret = np.abs(ret)
    # decoder targets for window starting at local index i: bar i+S
    # (same bar the AMT target encodes). Normalized on train stats.
    y_all = np.stack([rng, absret], axis=1)
    y_tr = y_all[S:split]
    y_mu, y_sd = y_tr.mean(0), y_tr.std(0) + 1e-12
    y_n = (y_all - y_mu) / y_sd

    def sample(src, bs):
        idx = torch.randint(0, len(src) - S - 1, (bs,))
        return idx, torch.stack([src[i:i + S + 1] for i in idx])

    trainer = WorldModelSpecialistTrainer(model, lr=args.lr)

    for step in range(1, args.steps + 1):
        idx, win = sample(train, args.batch)
        yb = torch.tensor(y_n[idx.numpy() + S], dtype=torch.float32)

        def dec_loss(z_last, _yb=yb):
            return args.dec_w * F.mse_loss(dec(z_last), _yb)

        loss = trainer.train_amt_step({"FX": win}, extra_loss_fn=dec_loss)
        opt_dec.step()
        opt_dec.zero_grad()
        if step % 20 == 0:
            print(f"step {step:4d}  pred_mse={loss:.6f}", flush=True)

    # ---- held-out evaluation ----
    g = torch.Generator().manual_seed(0)
    ev_idx = torch.randint(0, len(held) - S - 1, (args.eval_windows,),
                           generator=g)
    ev = trainer.eval_amt({"FX": torch.stack(
        [held[i:i + S + 1] for i in ev_idx])})
    skill = ev["model_cos"] - ev["persistence_cos"]

    # decoder predictions on the same held-out windows
    with torch.no_grad():
        ctx = torch.stack([held[i:i + S] for i in ev_idx])
        z_last = model.encoder({"FX": ctx})[:, -1, :]
        pred_n = dec(z_last).numpy()
    pred = pred_n * y_sd + y_mu
    gidx = split + ev_idx.numpy() + S          # global target bar index
    y_true = y_all[gidx]
    y_base = np.stack([rng[gidx - 1], roll_std[gidx - 1]], axis=1)

    def r2(p, y, b):
        mse_b = float(np.mean((b - y) ** 2))
        return 1.0 - float(np.mean((p - y) ** 2)) / mse_b if mse_b else float("nan")

    dec_r2_range = r2(pred[:, 0], y_true[:, 0], y_base[:, 0])
    dec_r2_absret = r2(pred[:, 1], y_true[:, 1], y_base[:, 1])

    # raw-feature ridge reference: same protocol — fit on train split,
    # predict the same held-out targets from the last context bar.
    tr_idx = torch.randint(0, split - S - 1, (20000,), generator=g).numpy()
    Xr_tr = feats[tr_idx + S - 1].numpy()
    Xr_ev = feats[split + ev_idx.numpy() + S - 1].numpy()
    raw_r2 = {}
    for k, name in ((0, "range"), (1, "absret")):
        mr = ridge_fit_np(Xr_tr, y_all[tr_idx + S, k])
        raw_r2[name] = r2(ridge_pred_np(mr, Xr_ev), y_true[:, k],
                          y_base[:, k])

    print(f"\nheld-out: model_cos={ev['model_cos']:.4f} "
          f"persistence_cos={ev['persistence_cos']:.4f} "
          f"mse={ev['mse']:.6f} skill={skill:+.4f}")
    print(f"decoder R2: range={dec_r2_range:+.4f} absret={dec_r2_absret:+.4f} "
          f"| raw-ridge R2: range={raw_r2['range']:+.4f} "
          f"absret={raw_r2['absret']:+.4f}")

    meta = {
        "args": vars(args), "n_bars": n, "split": split,
        "y_mean": y_mu.tolist(), "y_std": y_sd.tolist(),
        "latent_skill": skill, "model_cos": ev["model_cos"],
        "persistence_cos": ev["persistence_cos"], "mse": ev["mse"],
        "dec_r2_range": dec_r2_range, "dec_r2_absret": dec_r2_absret,
        "raw_r2": raw_r2,
    }
    try:
        meta["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=Path(__file__).resolve().parent.parent
        ).stdout.strip()
    except Exception:
        pass

    Path("var").mkdir(exist_ok=True)
    gate = skill > 0 and dec_r2_range >= raw_r2["range"]
    if gate:
        model.save(args.out)
        dec_path = args.out.replace(".pt", ".dec.pt")
        torch.save({"state_dict": dec.state_dict(),
                    "y_mean": y_mu.tolist(), "y_std": y_sd.tolist()},
                   dec_path)
        print(f"-> saved {args.out} + {dec_path} (trained=True on load)")
    else:
        print("-> NOT saved: gate failed "
              f"(skill>0: {skill > 0}, dec_range {dec_r2_range:+.4f} "
              f">= raw {raw_r2['range']:+.4f}: "
              f"{dec_r2_range >= raw_r2['range']}) — honest rejection")
    Path(args.out.replace(".pt", ".train_meta.json")).write_text(
        json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
