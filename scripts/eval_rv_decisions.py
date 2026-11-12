"""Decision-level shadow measurement for the rv-blend forecaster.

Question: on the trades the bot ACTUALLY took (dbseg_* replay runs),
would an "abstain on elevated forecast vol-mult" rule have avoided
worse-than-average outcomes?

Join path (all offline, honest):
  1. Each segment's market_history.json last-32 closes locates its
     replay end-bar uniquely inside market_data.db.
  2. TRADE_EXECUTION records carry the proposal price — paper fills
     happen at bar close +/- measured costs, so each execution maps to
     a replayed bar via side-aware price matching with a monotonic
     index constraint. Unmatched/ambiguous fills are dropped, honestly.
  3. The blend forecast is recomputed at each matched bar using the
     exact training featurization (WorldModelV2._obs_to_features +
     to_obs), so live and measured numbers are the same object.
  4. Per entry: forward outcome in the trade's direction over the next
     16 bars — signed return, adverse excursion, stop-hit — grouped by
     whether the forecast at entry was "elevated" (log-ratio > median
     of the held-out shadow-eval distribution, matching the abstention
     candidate) or not.

Small-sample caveat is reported: ~150 executions across segments.
Writes var/rv_decision_eval.json.
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
import torch  # noqa: E402

torch.set_num_threads(1)

from trading_bot.world_model.v2_core import WorldModelV2  # noqa: E402
from trading_bot.world_model.rv_forecaster import _on_grid  # noqa: E402
from train_world_model import (load_features, to_obs, grid_minutes,  # noqa: E402
                               ridge_pred_np)
from train_rv_forecaster import GRUForecaster  # noqa: E402


def find_segment_end(db_closes, hist):
    """Unique start index of `hist` close-sequence inside db_closes."""
    h = np.asarray(hist, dtype=np.float64)[-32:]
    cand = np.where(np.isclose(db_closes, h[0], atol=1e-6))[0]
    hits = [i for i in cand
            if i + len(h) <= len(db_closes)
            and np.allclose(db_closes[i:i + len(h)], h, atol=1e-6)]
    return int(hits[0]) + len(h) if len(hits) == 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--segments", default="bcdefgh")
    ap.add_argument("--ckpt", default="var/rv_blend_forecaster.pt")
    ap.add_argument("--shadow-eval", default="var/rv_shadow_eval.json",
                    help="decile stats used for the elevation threshold")
    ap.add_argument("--flag-quantile", type=float, default=0.5,
                    help="forecast log-ratio quantile above which an "
                         "entry counts as flagged (0.5 = the ~all-big-"
                         "moves split from the shadow eval)")
    ap.add_argument("--horizon", type=int, default=16)
    ap.add_argument("--stop-bps", type=float, default=15.0)
    ap.add_argument("--out", default="var/rv_decision_eval.json")
    args = ap.parse_args()

    import sqlite3
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    dbrows = con.execute(
        "SELECT timestamp, open, high, low, close FROM market_data "
        "WHERE symbol=? AND timeframe=? ORDER BY timestamp",
        (args.symbol, args.timeframe)).fetchall()
    db_ts = [str(r[0]) for r in dbrows]
    c_all = np.array([r[4] for r in dbrows], dtype=np.float64)
    h_all = np.array([r[2] for r in dbrows], dtype=np.float64)
    l_all = np.array([r[3] for r in dbrows], dtype=np.float64)
    N = len(c_all)

    step = grid_minutes(args.timeframe)
    on_grid = np.array([_on_grid(t, step) for t in db_ts])
    filt_pos = np.cumsum(on_grid) - 1          # abs idx -> filtered idx

    rows, ret, rng, vol_z, mom8, roll_std, hour = load_features(
        args.db, args.symbol, args.timeframe, N + 1)
    # load_features returns the most recent bars; map filtered idx back
    n_filt = len(rows)
    filt_offset = int(on_grid.sum()) - n_filt  # first loaded filtered pos

    # ---- locate segments ----
    segs = {}
    for seg in args.segments:
        d = Path(f"var/dbseg_{seg}")
        try:
            hist = json.loads((d / "market_history.json").read_text())
            end = find_segment_end(c_all, hist)
            snap = json.loads((d / "snapshot.json").read_text())
            cyc = int(snap.get("cycles", 0))
        except Exception as exc:
            print(f"seg {seg}: anchor failed ({exc})", flush=True)
            continue
        if end is None:
            print(f"seg {seg}: no unique end match", flush=True)
            continue
        lo = max(0, end - 4 * max(cyc, 1))
        segs[seg] = (lo, end)
        print(f"seg {seg}: window [{lo},{end}) cycles={cyc}", flush=True)

    # ---- collect executions ----
    execs = []
    for seg, (lo, hi) in segs.items():
        for line in open(f"var/dbseg_{seg}/decision_log.jsonl"):
            d = json.loads(line)
            if d.get("action_type") != "TRADE_EXECUTION":
                continue
            p = d["payload"]
            execs.append({"seg": seg, "lo": lo, "hi": hi,
                          "action": p["action"], "price": float(p["price"]),
                          "wall": d["timestamp"],
                          "confidence": p.get("confidence"),
                          "expected_return": p.get("expected_return")})
    print(f"executions: {len(execs)}", flush=True)

    # ---- price-match executions to bars (side-aware, monotonic) ----
    # BUY fills pay costs on top of close -> close <= px; SELL vice versa.
    TOL = 8e-4   # ~8bps: covers measured spread+slip costs
    prev_by_seg = {}
    n_matched = 0
    for e in sorted(execs, key=lambda x: (x["seg"], x["wall"])):
        lo, hi = e["lo"], e["hi"]
        prev = prev_by_seg.get(e["seg"], lo)
        px = e["price"]
        if e["action"] == "BUY":      # close in [px*(1-TOL), px*(1+1bp)]
            mask = (c_all >= px * (1 - TOL)) & (c_all <= px * (1 + 1e-4))
        else:                          # close in [px*(1-1bp), px*(1+TOL)]
            mask = (c_all <= px * (1 + TOL)) & (c_all >= px * (1 - 1e-4))
        cand = np.where(mask)[0]
        cand = cand[(cand >= prev) & (cand < hi)]
        if len(cand) == 0:
            e["bar_idx"] = None
            continue
        bi = int(cand[0])             # earliest feasible monotone match
        e["bar_idx"] = bi
        prev_by_seg[e["seg"]] = bi
        n_matched += 1
    print(f"price-matched: {n_matched}/{len(execs)}", flush=True)

    matched = [e for e in execs if e.get("bar_idx") is not None]

    # ---- recompute forecasts at matched bars ----
    blob = torch.load(args.ckpt, weights_only=True)
    hidden = int(blob["args"].get("hidden", 64))
    net = GRUForecaster(in_dim=64, hidden=hidden,
                        out_dim=len(blob["horizons"]))
    net.load_state_dict(blob["state_dict"])
    net.eval()
    y_mu = np.asarray(blob["y_mean"]); y_sd = np.asarray(blob["y_std"])
    blend_w = float(blob.get("blend_w", 0.5))
    ridge = {int(h): (np.asarray(m[0], dtype=np.float64),
                      np.asarray(m[1], dtype=np.float64),
                      np.asarray(m[2], dtype=np.float64))
             for h, m in blob["ridge"].items()}
    horizons = tuple(blob["horizons"])

    featurizer = WorldModelV2(asset_dims={"FX": 64, "Equities": 128},
                              latent_dim=256)
    S = 32
    need = sorted({e["bar_idx"] for e in matched})
    feat_cache = {}

    def feat_at(abs_i):
        fi = filt_pos[abs_i] - filt_offset
        if fi not in feat_cache:
            feat_cache[fi] = featurizer._obs_to_features(
                to_obs(rows, ret, rng, vol_z, mom8, roll_std, hour, fi))
        return feat_cache[fi]

    fc_out = {}
    skipped = set()
    for ai in need:
        if not on_grid[ai]:
            skipped.add(ai)
            continue
        fi = filt_pos[ai] - filt_offset
        win = list(range(ai - S + 1, ai + 1))
        if min(win) < 0 or not all(on_grid[w] for w in win):
            skipped.add(ai)
            continue
        wfeats = torch.stack([feat_at(w) for w in win]).unsqueeze(0)
        with torch.no_grad():
            gp = net(wfeats.float()).numpy()[0] * y_sd + y_mu
        x = feat_at(ai).numpy()
        rp = np.array([float(ridge_pred_np(m, x.reshape(1, -1)).ravel()[0])
                       for h, m in sorted(ridge.items())])
        fc_out[ai] = blend_w * gp + (1 - blend_w) * rp
    print(f"forecasts: {len(fc_out)} (skipped {len(skipped)} off-grid/"
          "contaminated-window bars)", flush=True)

    # ---- forward outcomes per matched execution ----
    H = args.horizon
    stop = args.stop_bps / 1e4
    recs = []
    for e in matched:
        i = e["bar_idx"]
        if i not in fc_out or i + H >= N:
            continue
        d = 1.0 if e["action"] == "BUY" else -1.0
        fwd = d * (c_all[i + H] / c_all[i] - 1.0)
        adverse = max((c_all[i] - l_all[i + 1:i + 1 + H].min()) / c_all[i],
                      0.0) if d > 0 else \
            max((h_all[i + 1:i + 1 + H].max() - c_all[i]) / c_all[i], 0.0)
        favorable = max((h_all[i + 1:i + 1 + H].max() - c_all[i]) / c_all[i],
                        0.0) if d > 0 else \
            max((c_all[i] - l_all[i + 1:i + 1 + H].min()) / c_all[i], 0.0)
        stopped = adverse > stop
        recs.append({"seg": e["seg"], "bar": i, "ts": db_ts[i],
                     "action": e["action"], "price": e["price"],
                     "confidence": e["confidence"],
                     "expected_return": e["expected_return"],
                     "log_ratio": {f"rv{h}": float(v) for h, v in
                                   zip(horizons, fc_out[i])},
                     "fwd_bps": float(fwd * 1e4),
                     "mae_bps": float(adverse * 1e4),
                     "mfe_bps": float(favorable * 1e4),
                     "stopped": bool(stopped)})

    # ---- elevation threshold from the shadow eval distribution ----
    thr = None
    try:
        se = json.loads(Path(args.shadow_eval).read_text())
        dist = [row["log_ratio_mean"] for row in se["deciles_rv16"]]
        # median of the per-decile means approximates the median split
        thr = float(np.quantile(np.array(dist), args.flag_quantile))
    except Exception as exc:
        print(f"shadow-eval threshold unavailable ({exc}) — "
              "using log_ratio>0", flush=True)
        thr = 0.0

    k16 = "rv16"
    flagged = [r for r in recs if r["log_ratio"][k16] > thr]
    calm = [r for r in recs if r["log_ratio"][k16] <= thr]

    def agg(rs):
        if not rs:
            return {"n": 0}
        return {
            "n": len(rs),
            "fwd_bps_mean": float(np.mean([r["fwd_bps"] for r in rs])),
            "fwd_bps_median": float(np.median([r["fwd_bps"] for r in rs])),
            "win_rate": float(np.mean([r["fwd_bps"] > 0 for r in rs])),
            "mae_bps_mean": float(np.mean([r["mae_bps"] for r in rs])),
            "mfe_bps_mean": float(np.mean([r["mfe_bps"] for r in rs])),
            "stop_hit_rate": float(np.mean([r["stopped"] for r in rs])),
            "expected_return_mean": float(np.mean(
                [r["expected_return"] or 0 for r in rs])),
        }

    report = {
        "config": vars(args), "thr_log_ratio16": thr,
        "n_executions": len(execs), "n_matched": n_matched,
        "n_forecasted": len(recs),
        "segments": {s: list(w) for s, w in segs.items()},
        "flagged": agg(flagged), "calm": agg(calm),
        "records": recs,
    }
    Path(args.out).parent.mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nflagged (elevated fcst): {json.dumps(agg(flagged), indent=1)}")
    print(f"calm: {json.dumps(agg(calm), indent=1)}")
    print(f"-> wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
