"""Shadow-mode economic evaluation of the rv-blend forecaster.

Question: does forecast vol-EXPANSION actually precede the conditions
that hurt trades? Decision-agnostic — no bot trades needed.

For every bar in the held-out tail (the same region the save gate
measured on), the live RVBlendForecaster runtime produces vol_mult
forecasts; we then measure, per forecast decile:

  - realized rv16 (calibration: does higher forecast -> higher realized vol?)
  - max adverse excursion over the next 16 bars for a hypothetical unit
    position, long and short (trade-condition proxy)
  - |ret|>0.5% big-move rate (event capture / lift vs base rate)
  - 15bps stop-hit rate within 16 bars (would a tight stop survive?)

If expansion forecasts map monotonically to adverse outcomes, an
"abstain when forecast vol-expansion" rule has measurable support —
reported as fraction of bars flagged vs fraction of adverse-excursion
mass covered.

Runs the REAL runtime (trading_bot.world_model.rv_forecaster) — same
code path the paper runner uses, just fed from the DB instead of a
live/replay source. Read-only; writes var/rv_shadow_eval.json.
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

from trading_bot.world_model.rv_forecaster import RVBlendForecaster  # noqa: E402
from train_world_model import load_features  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--bars", type=int, default=30000)
    ap.add_argument("--eval-bars", type=int, default=9000,
                    help="chronological tail used for evaluation")
    ap.add_argument("--ckpt", default="var/rv_blend_forecaster.pt")
    ap.add_argument("--horizon", type=int, default=16)
    ap.add_argument("--stop-bps", type=float, default=15.0)
    ap.add_argument("--out", default="var/rv_shadow_eval.json")
    args = ap.parse_args()

    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, args.bars)
    n = len(rows)
    tail_lo = n - args.eval_bars
    warm_lo = max(0, tail_lo - 96)
    print(f"n={n} eval tail=[{tail_lo},{n}) warm from {warm_lo}", flush=True)

    fc = RVBlendForecaster(args.ckpt, timeframe=args.timeframe)

    preds = []        # (i, log_ratio[h], vol_mult[h]) per forecast bar i
    for i in range(warm_lo, n):
        r = rows[i]
        obs = {"symbol": args.symbol, "timestamp": str(r[0]),
               "broker_timestamp": str(r[0]),
               "open": r[1], "high": r[2], "low": r[3], "close": r[4],
               "volume": r[5], "price": r[4]}
        out = fc.update(obs)
        if i >= tail_lo and out and out.get("ready"):
            preds.append((i,
                          [out["log_ratio"][f"rv{h}"] for h in fc.horizons],
                          [out["vol_mult"][f"rv{h}"] for h in fc.horizons]))
        if (i - warm_lo + 1) % 3000 == 0:
            print(f"  streamed {i - warm_lo + 1}/{n - warm_lo} "
                  f"(forecasts: {len(preds)})", flush=True)

    print(f"forecasts collected: {len(preds)} "
          f"(skipped off-grid: {fc.n_skipped_offgrid})", flush=True)

    idx = np.array([p[0] for p in preds])
    log_ratio = np.array([p[1] for p in preds])          # [N,3]
    vol_mult = np.array([p[2] for p in preds])           # [N,3]

    c = np.array([r[4] for r in rows], dtype=np.float64)
    hh = np.array([r[2] for r in rows], dtype=np.float64)
    ll = np.array([r[3] for r in rows], dtype=np.float64)
    absret = np.abs(ret)
    H = args.horizon

    # realized outcomes per forecast bar
    def fut_mean_absret(i, h):
        return absret[i + 1:i + 1 + h].mean() if i + 1 + h <= n else np.nan

    realized_rv = np.array([[fut_mean_absret(i, h) for h in (4, 8, 16)]
                            for i in idx])
    mae_long = np.array([
        (c[i] - ll[i + 1:i + 1 + H].min()) / c[i] if i + 1 + H <= n else np.nan
        for i in idx])
    mae_short = np.array([
        (hh[i + 1:i + 1 + H].max() - c[i]) / c[i] if i + 1 + H <= n else np.nan
        for i in idx])
    big_move = np.array([
        bool((np.abs(ret[i + 1:i + 1 + H]) > 5e-3).any())
        if i + 1 + H <= n else np.nan for i in idx])
    stop_hit = np.array([
        bool(((c[i] - ll[i + 1:i + 1 + H]) / c[i] > args.stop_bps / 1e4).any()
             or ((hh[i + 1:i + 1 + H] - c[i]) / c[i] > args.stop_bps / 1e4).any())
        if i + 1 + H <= n else np.nan for i in idx])

    valid = ~np.isnan(realized_rv[:, -1])
    idx, log_ratio, vol_mult = idx[valid], log_ratio[valid], vol_mult[valid]
    realized_rv, mae_long, mae_short = (realized_rv[valid], mae_long[valid],
                                      mae_short[valid])
    big_move, stop_hit = big_move[valid].astype(float), stop_hit[valid].astype(float)
    print(f"valid eval bars: {len(idx)}", flush=True)

    # ---- decile table on rv16 log-ratio forecast ----
    k16 = 2  # column for rv16
    qs = np.quantile(log_ratio[:, k16], np.linspace(0, 1, 11))
    dec = np.clip(np.digitize(log_ratio[:, k16], qs[1:-1]), 0, 9)
    table = []
    for d in range(10):
        m = dec == d
        if not m.any():
            continue
        table.append({
            "decile": d + 1,
            "n": int(m.sum()),
            "log_ratio_mean": float(log_ratio[m, k16].mean()),
            "vol_mult_mean": float(vol_mult[m, k16].mean()),
            "realized_rv16_mean": float(realized_rv[m, -1].mean()),
            "mae_long_bps_mean": float(mae_long[m].mean() * 1e4),
            "mae_short_bps_mean": float(mae_short[m].mean() * 1e4),
            "big_move_rate": float(big_move[m].mean()),
            "stop_hit_rate": float(stop_hit[m].mean()),
        })
    for row in table:
        print(f"  d{row['decile']:2d} n={row['n']:4d} mult={row['vol_mult_mean']:.3f} "
              f"rv16={row['realized_rv16_mean']*1e4:5.2f}bps "
              f"maeL={row['mae_long_bps_mean']:5.1f} maeS={row['mae_short_bps_mean']:5.1f} "
              f"big={row['big_move_rate']:.3f} stop={row['stop_hit_rate']:.3f}",
              flush=True)

    # ---- abstention-rule economics ----
    # For candidate thresholds on log_ratio_16: fraction of bars flagged
    # vs share of total adverse-excursion mass and big moves covered.
    total_mae = mae_long.sum() + mae_short.sum()
    total_big = big_move.sum()
    total_stop = stop_hit.sum()
    rules = []
    for q in (0.5, 0.6, 0.7, 0.8, 0.9):
        thr = float(np.quantile(log_ratio[:, k16], q))
        flag = log_ratio[:, k16] > thr
        rules.append({
            "quantile": q, "log_ratio_thr": thr,
            "bars_flagged": float(flag.mean()),
            "mae_mass_covered": float(
                (mae_long[flag].sum() + mae_short[flag].sum()) / total_mae),
            "big_moves_covered": float(big_move[flag].sum() / total_big)
            if total_big else None,
            "stop_hits_covered": float(stop_hit[flag].sum() / total_stop)
            if total_stop else None,
            "big_move_rate_flagged": float(big_move[flag].mean()),
            "big_move_rate_rest": float(big_move[~flag].mean()),
        })
        r = rules[-1]
        print(f"  skip q>{q}: flag {r['bars_flagged']*100:.0f}% bars, "
              f"covers {r['mae_mass_covered']*100:.0f}% mae, "
              f"{(r['big_moves_covered'] or 0)*100:.0f}% big moves, "
              f"big-rate {r['big_move_rate_flagged']:.3f} vs "
              f"{r['big_move_rate_rest']:.3f}", flush=True)

    report = {
        "config": vars(args), "n_bars": n, "eval_tail": [int(tail_lo), n],
        "n_forecasts": int(len(idx)),
        "skipped_offgrid": fc.n_skipped_offgrid,
        "deciles_rv16": table,
        "abstention_rules": rules,
        "summary": {
            "corr_logratio16_realized": float(
                np.corrcoef(log_ratio[:, k16], realized_rv[:, -1])[0, 1]),
            "big_move_base_rate": float(big_move.mean()),
            "stop_hit_base_rate": float(stop_hit.mean()),
        },
    }
    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"-> wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
