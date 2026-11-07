"""Held-out evaluation of the WorldModelV2 checkpoint.

Two question battery:

1. Latent skill (same protocol as training): does the checkpoint's
   next-latent prediction beat persistence, on data it did not train on,
   and vs a same-seed random-init control?

2. Observable probes (the stronger honesty test): do the learned latents
   carry *economically meaningful* predictive content? A ridge probe is
   fit from latent -> next-bar (return, |return|, range) on the first
   part of the held-out pool and scored on the chronological tail,
   against naive baselines and the same probes fed raw features or
   random-init latents. If raw features match the trained latent, the
   world model adds nothing measurable yet.

Read-only on the DB. Writes a small JSON artifact to var/.
"""

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

torch.set_num_threads(1)  # OpenMP threading deadlocks observed on this host

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from trading_bot.world_model.v2_training import WorldModelSpecialistTrainer  # noqa: E402
from train_world_model import load_features, to_obs  # noqa: E402


def featurize(model, rows, ret, rng, vol_z, mom8, roll_std, hour):
    return torch.stack([
        model._obs_to_features(to_obs(rows, ret, rng, vol_z, mom8,
                                      roll_std, hour, i))
        for i in range(len(rows))]).float()


def windowed_encoder_latents(model, feats, start, end, seq, chunk=256):
    """z_i for i in [start, end): last-step latent of the seq-length
    window ending at bar i — the same object eval_amt's z_ctx[:, -1]."""
    out = []
    with torch.no_grad():
        for lo in range(start, end, chunk):
            hi = min(lo + chunk, end)
            idx = torch.arange(lo, hi)
            w = torch.stack([feats[i - seq + 1:i + 1] for i in idx])
            z = model.encoder({"FX": w})[:, -1, :]
            out.append(z)
    return torch.cat(out)


def off_grid_mask(rows):
    """Bars whose timestamp isn't aligned to the M15 grid and/or carries
    fractional seconds — i.e. spliced second-feed rows, not venue bars."""
    bad = np.zeros(len(rows), dtype=bool)
    for i, r in enumerate(rows):
        t = str(r[0])
        mm = re.search(r"T\d{2}:(\d{2}):(\d{2}(?:\.\d+)?)", t)
        if mm is None or int(mm.group(1)) % 15 != 0 or float(mm.group(2)) != 0.0:
            bad[i] = True
    return bad


def window_ok(bad, W):
    """window_ok[i] = True if bars i..i+W-1 contain no off-grid rows."""
    conv = np.convolve(bad.astype(np.int64), np.ones(W, np.int64), "valid")
    return conv == 0


def latent_eval(model, feats, cand_idx, seq, n_windows, seed=0):
    """Replicates eval_amt on n_windows sampled from candidate starts."""
    g = torch.Generator().manual_seed(seed)
    pick = torch.randint(0, len(cand_idx), (n_windows,), generator=g)
    idx = cand_idx[pick]
    batch = torch.stack([feats[i:i + seq + 1] for i in idx])
    trainer = WorldModelSpecialistTrainer(model)  # only eval used
    return trainer.eval_amt({"FX": batch})


def ridge_fit(X, Y, lam=1.0):
    mu, sd = X.mean(0, keepdims=True), X.std(0, keepdims=True) + 1e-9
    Xs = (X - mu) / sd
    A = Xs.T @ Xs + lam * np.eye(Xs.shape[1])
    W = np.linalg.solve(A, Xs.T @ Y)
    return (mu, sd, W)


def ridge_pred(model_r, X):
    mu, sd, W = model_r
    return ((X - mu) / sd) @ W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--seq", type=int, default=32)
    ap.add_argument("--latent", type=int, default=256)
    ap.add_argument("--fx-dim", type=int, default=64)
    ap.add_argument("--ckpt", default="var/world_model_v2.pt")
    ap.add_argument("--held-tail", type=int, default=9000,
                    help="chronological tail treated as held-out pool")
    ap.add_argument("--eval-windows", type=int, default=384)
    ap.add_argument("--skip-latent", action="store_true",
                    help="skip the slow core-forward latent eval blocks")
    ap.add_argument("--decoder", default=None,
                    help="optional path to a saved .dec.pt — score the "
                         "jointly-trained decoder on the probe test slice")
    ap.add_argument("--out", default="var/world_model_eval.json")
    args = ap.parse_args()

    print("loading features...", flush=True)
    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)

    torch.manual_seed(0)
    model = WorldModelV2(asset_dims={"FX": args.fx_dim, "Equities": 128},
                         latent_dim=args.latent)
    model.load(args.ckpt)
    model.eval()

    torch.manual_seed(0)
    rand_model = WorldModelV2(asset_dims={"FX": args.fx_dim, "Equities": 128},
                              latent_dim=args.latent)
    rand_model.eval()

    print("featurizing bars...", flush=True)
    feats = featurize(model, rows, ret, rng, vol_z, mom8, roll_std, hour)
    n = len(feats)
    S = args.seq
    split = int(n * 0.7)
    tail_lo = n - args.held_tail          # start index of held-out pool

    bad = off_grid_mask(rows)
    wok = window_ok(bad, S + 1)           # len n-S: start i clean if wok[i]
    n_bad = int(bad.sum())
    print(f"n={n} split(70%)={split} held-out pool=[{tail_lo},{n}) "
          f"off_grid_bars={n_bad}", flush=True)

    # ---- 1. latent skill per chronological block, ckpt vs random ----
    blocks = {
        "in_sample_early": (S, min(6000, split - S - 2)),
        "in_sample_late": (max(S, split - 6000), split - S - 2),
        "held_out_tail": (tail_lo, n - S - 2),
    }
    latent_report = {}
    for name, (lo, hi) in blocks.items():
        if args.skip_latent:
            latent_report[name] = {"skipped": "--skip-latent"}
            continue
        cand = np.arange(lo, hi)[wok[lo:hi]]
        if len(cand) == 0:
            latent_report[name] = {"skipped": f"empty range {lo}:{hi}"}
            continue
        latent_report[name] = {"candidates": int(len(cand))}
        ck = latent_eval(model, feats, torch.from_numpy(cand), S,
                         args.eval_windows)
        rn = latent_eval(rand_model, feats, torch.from_numpy(cand), S,
                         args.eval_windows)
        latent_report[name] = {
            "checkpoint": ck,
            "random_init": rn,
            "ckpt_skill": ck["model_cos"] - ck["persistence_cos"],
            "rand_skill": rn["model_cos"] - rn["persistence_cos"],
        }
        print(f"  {name}: ckpt_skill={latent_report[name]['ckpt_skill']:+.4f} "
              f"rand_skill={latent_report[name]['rand_skill']:+.4f} "
              f"(model_cos={ck['model_cos']:.4f} persist={ck['persistence_cos']:.4f})",
              flush=True)

    # ---- collapse diagnostic on held-out latents ----
    z_all = windowed_encoder_latents(model, feats, tail_lo, n - 1, S)
    zdim_std = z_all.std(0)
    sub = z_all[torch.randperm(len(z_all))[:2000]]
    subn = F.normalize(sub, dim=-1)
    pc = subn @ subn.T
    off = pc[~torch.eye(len(sub), dtype=bool)]
    collapse = {
        "latent_dim_std_mean": float(zdim_std.mean()),
        "latent_dim_std_min": float(zdim_std.min()),
        "pairwise_cos_mean": float(off.mean()),
        "pairwise_cos_p95": float(off.quantile(0.95)),
    }
    print(f"  collapse check: dim_std={collapse['latent_dim_std_mean']:.4f} "
          f"pair_cos={collapse['pairwise_cos_mean']:.4f}", flush=True)

    # ---- 2. observable probes on the held-out pool ----
    # i in [tail_lo, n-2]; target bar i+1
    i_lo, i_hi = tail_lo, n - 1
    zc = windowed_encoder_latents(model, feats, i_lo, i_hi, S).numpy()
    zr = windowed_encoder_latents(rand_model, feats, i_lo, i_hi, S).numpy()
    xr = torch.stack([feats[i] for i in range(i_lo, i_hi)]).numpy()

    m = i_hi - i_lo
    cut = i_lo + int(m * 2 / 3)              # chronological probe split
    ok = wok[np.arange(i_lo, i_hi) - S + 1]  # context+target fully on-grid
    tr = (np.arange(m) < cut - i_lo) & ok
    te = (np.arange(m) >= cut - i_lo) & ok
    print(f"  probe indices: fit {int(tr.sum())}/{int((np.arange(m) < cut - i_lo).sum())} "
          f"test {int(te.sum())}/{m - (cut - i_lo)} clean", flush=True)

    t_ret = ret[i_lo + 1:i_hi + 1]           # next-bar log return
    t_abs = np.abs(t_ret)
    t_rng = rng[i_lo + 1:i_hi + 1]
    base_ret = np.zeros(m)                    # naive: no change
    base_abs = roll_std[i_lo:i_hi]            # vol persistence
    base_rng = rng[i_lo:i_hi]                 # range persistence

    probes = {}
    for tname, y, yb in (("next_log_return", t_ret, base_ret),
                         ("next_abs_return", t_abs, base_abs),
                         ("next_range", t_rng, base_rng)):
        reps = {"z_ckpt": (zc, 1.0), "z_rand": (zr, 1.0), "x_raw": (xr, 1.0),
                "z_ckpt_lam1k": (zc, 1000.0), "x_raw_lam1k": (xr, 1000.0)}
        fit = {nm: ridge_fit(rep[tr], y[tr], lam=lam)
               for nm, (rep, lam) in reps.items()}
        res = {}
        for nm, (rep, _lam) in reps.items():
            pred = ridge_pred(fit[nm], rep[te])
            yte, ybte = y[te], yb[te]
            mse = float(np.mean((pred - yte) ** 2))
            mse_b = float(np.mean((ybte - yte) ** 2))
            res[nm] = {
                "mse": mse, "baseline_mse": mse_b,
                "r2_vs_baseline": 1 - mse / mse_b if mse_b > 0 else float("nan"),
                "corr": float(np.corrcoef(pred, yte)[0, 1]),
            }
            if tname == "next_log_return":
                res[nm]["sign_acc"] = float(
                    np.mean(np.sign(pred) == np.sign(yte)))
        res["baseline_only"] = {
            "mse": float(np.mean((yb[te] - y[te]) ** 2))}
        probes[tname] = res
        print(f"  probe {tname}: ckpt_r2={res['z_ckpt']['r2_vs_baseline']:+.4f} "
              f"rand_r2={res['z_rand']['r2_vs_baseline']:+.4f} "
              f"raw_r2={res['x_raw']['r2_vs_baseline']:+.4f}",
              flush=True)

    # ---- optional: score the jointly-trained decoder checkpoint ----
    dec_report = None
    if args.decoder:
        from train_world_model import build_decoder
        try:
            blob = torch.load(args.decoder, weights_only=True)
        except Exception:
            blob = torch.load(args.decoder, weights_only=False)
        dec = build_decoder(args.latent)
        dec.load_state_dict(blob["state_dict"])
        dec.eval()
        ym = np.array(blob["y_mean"]); ys = np.array(blob["y_std"])
        with torch.no_grad():
            pd = dec(torch.from_numpy(zc[te]).float()).numpy() * ys + ym
        dec_report = {}
        for tname, k, y, yb in (("next_range", 0, t_rng, base_rng),
                                ("next_abs_return", 1, t_abs, base_abs)):
            yte, ybte = y[te], yb[te]
            mse = float(np.mean((pd[:, k] - yte) ** 2))
            mse_b = float(np.mean((ybte - yte) ** 2))
            dec_report[tname] = {
                "mse": mse, "baseline_mse": mse_b,
                "r2_vs_baseline": 1 - mse / mse_b if mse_b > 0 else float("nan"),
                "corr": float(np.corrcoef(pd[:, k], yte)[0, 1]),
            }
            print(f"  trained-decoder {tname}: "
                  f"r2={dec_report[tname]['r2_vs_baseline']:+.4f} "
                  f"corr={dec_report[tname]['corr']:+.4f}", flush=True)

    report = {
        "config": vars(args),
        "n_bars": n, "split_70pct": split, "held_pool": [i_lo, i_hi],
        "off_grid_bars": n_bad,
        "off_grid_span": ([str(rows[int(np.argmax(bad))][0]),
                           str(rows[len(rows) - 1 - int(np.argmax(bad[::-1]))][0])]
                          if n_bad else None),
        "probe_fit": [i_lo, cut], "probe_test": [cut, i_hi],
        "latent_skill": latent_report,
        "collapse": collapse,
        "probes": probes,
        "trained_decoder": dec_report,
    }
    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
