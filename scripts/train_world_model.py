"""Train WorldModelV2 (AMT stage) on market_data.db.

Self-supervised next-latent prediction on real OHLCV windows. Saves a
checkpoint ONLY if held-out skill beats the persistence baseline —
matching the system's honesty convention: a trained flag without
measured skill would be a lie.
"""

import argparse
import math
import sqlite3
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from trading_bot.world_model.v2_training import WorldModelSpecialistTrainer  # noqa: E402


def load_features(db: str, symbol: str, timeframe: str, limit: int):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT timestamp, open, high, low, close, volume FROM market_data "
        "WHERE symbol=? AND timeframe=? ORDER BY timestamp DESC LIMIT ?",
        (symbol, timeframe, limit)).fetchall()[::-1]
    con.close()
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
    ap.add_argument("--out", default="var/world_model_v2.pt")
    args = ap.parse_args()

    torch.manual_seed(0)
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)

    model = WorldModelV2(asset_dims={"FX": args.fx_dim, "Equities": 128},
                         latent_dim=args.latent)

    # Featurize every bar through the model's own encode() path so the
    # training distribution exactly matches what the live pipeline feeds.
    feats = torch.stack([
        model._obs_to_features(to_obs(rows, ret, rng, vol_z, mom8,
                                      roll_std, hour, i))
        for i in range(len(rows))]).float()

    n = len(feats)
    split = int(n * 0.7)
    train, held = feats[:split], feats[split:]

    trainer = WorldModelSpecialistTrainer(model, lr=args.lr)

    S = args.seq
    def sample(src, bs):
        idx = torch.randint(0, len(src) - S - 1, (bs,))
        return torch.stack([src[i:i + S + 1] for i in idx])

    for step in range(1, args.steps + 1):
        loss = trainer.train_amt_step({"FX": sample(train, args.batch)})
        if step % 100 == 0:
            print(f"step {step:4d}  pred_mse={loss:.6f}", flush=True)

    ev = trainer.eval_amt({"FX": sample(held, 512)})
    skill = ev["model_cos"] - ev["persistence_cos"]
    print(f"\nheld-out: model_cos={ev['model_cos']:.4f} "
          f"persistence_cos={ev['persistence_cos']:.4f} "
          f"mse={ev['mse']:.6f} skill={skill:+.4f}")

    Path("var").mkdir(exist_ok=True)
    if skill > 0:
        model.save(args.out)
        print(f"-> saved {args.out} (trained=True on load)")
    else:
        print("-> NOT saved: no skill over persistence — honest rejection")


if __name__ == "__main__":
    main()
