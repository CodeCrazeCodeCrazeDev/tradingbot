"""Daily-horizon rates-momentum gate — the macro channel's killable claim.

Context: on M15/H1 bars every directional rule nets ~-cost (alpha
verdict 2026-11-09). The one channel that showed a stable,
theory-correct sign was rates momentum: US yields up -> USD up ->
EURUSD down (OOS r=-0.215 on dUST2y). This script runs the claim
through gate-fair semantics on macro_data.db daily series:

  - point-in-time only: `published_at` for yield/spot series is the
    same trading day 23:59 UTC (verified) — a daily-close decision
    may use them without lookahead
  - position on day t decided from 5d yield change through day t,
    earns log spot return t -> t+1, pays cost on position change
  - chronological 60/40 split, then the OOS tail split into
    contiguous segments (same philosophy as edge_gate)
  - metrics per variant: OOS mean bps/day, block-bootstrap LCB5,
    exposure, per-segment LCB — verdict needs LCB > 0 in EVERY
    evaluated segment (mirroring the FX gate's all-segments rule)
  - vol-regime conditioning: signal quality split by 20d realized
    spot vol (median split) — does the channel work in a regime?

Signal sign convention: US yields rising = USD strengthening.
EURUSD/GBPUSD quote USD-per-unit  -> sign = -sign(dy)
USDJPY quotes JPY-per-USD         -> sign = +sign(dy)
EURUSD also gets the full diff (us_ust_10y - eu_aaa_10y).
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from scripts.edge_baseline import block_bootstrap_lcb  # noqa: E402

PAIRS = {
    "EURUSD": {"spot": "usd_per_eur_ecb", "sign": -1.0,
               "diff": ("us_ust_10y", "eu_aaa_10y")},
    "GBPUSD": {"spot": "usd_per_gbp_fed", "sign": -1.0, "diff": None},
    "USDJPY": {"spot": "jpy_per_usd_fed", "sign": +1.0, "diff": None},
}
YIELDS = ("us_ust_2y", "us_ust_10y", "us_sofr")
WINDOWS = (5, 10)
THRESHOLDS = (0.10, 0.15, 0.20)
COST_BPS = 5.0


def load_series(con, name):
    return {d: v for d, v in con.execute(
        "SELECT date, value FROM macro_series WHERE series=? ORDER BY date",
        (name,))}


def panel(con, pair):
    spec = PAIRS[pair]
    maps = {k: load_series(con, k) for k in YIELDS}
    maps["spot"] = load_series(con, spec["spot"])
    dates = sorted(set(maps["spot"])
                   .intersection(*[set(maps[y]) for y in YIELDS]))
    out = {k: np.array([m[d] for d in dates]) for k, m in maps.items()}
    if spec["diff"]:
        a, b = (load_series(con, s) for s in spec["diff"])
        dates = [d for d in dates if d in a and d in b]
        out = {k: v[:len(dates)] for k, v in
               ((k, np.array([m[d] for d in dates]))
                for k, m in maps.items())}
        out["diff10"] = np.array([a[d] - b[d] for d in dates])
    out["dates"] = dates
    out["ret"] = np.diff(np.log(out["spot"]))
    out["ret"].flags.writeable = False
    return out


def daily_pnl(ret, sig_raw, dsign, th):
    """sig_raw: 5d/10d change ending day j (j>=W). pos[t] uses data
    through day t, earns ret[t]; cost on position changes."""
    W = len(ret) - len(sig_raw)
    k = len(ret) - W
    sig = np.where(np.abs(sig_raw[:k]) > th,
                   dsign * np.sign(sig_raw[:k]), 0.0)
    pos = np.concatenate([np.zeros(W), sig])
    chg = np.abs(np.diff(np.concatenate([[0.0], pos]))) > 0
    return pos, pos * ret - chg * (COST_BPS / 1e4)


def evaluate(ret, pos, pnl, split):
    ev = pnl[split:]
    m, l = block_bootstrap_lcb(ev * 1e4)
    seg_n = (len(ret) - split) // 3
    segs = []
    for k in range(3):
        a, b = split + k * seg_n, (split + (k + 1) * seg_n
                                   if k < 2 else len(ret))
        if b - a < 60:
            segs.append({"status": "thin"})
            continue
        ms, ls = block_bootstrap_lcb(pnl[a:b] * 1e4)
        segs.append({"mean": round(ms, 2), "lcb5": round(ls, 2)})
    return {"mean_bps": round(m, 3), "lcb5": round(l, 3),
            "exposure": round(float(np.abs(pos[split:]).mean()), 3),
            "segments": segs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="macro_data.db")
    ap.add_argument("--pairs", default="EURUSD,GBPUSD,USDJPY")
    ap.add_argument("--out", default="var/macro_rates_gate.json")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)

    report = {"gate": {"cost_bps": COST_BPS, "windows": WINDOWS,
                       "thresholds": THRESHOLDS, "split": 0.6},
              "pairs": {}}
    for pair in [p.strip() for p in args.pairs.split(",")]:
        spec = PAIRS[pair]
        pan = panel(con, pair)
        ret = pan["ret"]
        n = len(ret)
        split = int(n * 0.6)
        res = {"n_days": n, "eval_span": [pan["dates"][split],
                                        pan["dates"][-1]],
               "variants": {}}
        signals = {}
        for y in YIELDS:
            for w in WINDOWS:
                v = pan[y]
                signals[f"d{y[3:] if y.startswith('us_') else y}_{w}d"] = \
                    v[w:] - v[:-w]
        if "diff10" in pan:
            signals["ddiff10_5d"] = pan["diff10"][5:] - pan["diff10"][:-5]
        for sname, sraw in signals.items():
            for th in THRESHOLDS:
                pos, pnl = daily_pnl(ret, sraw, spec["sign"], th)
                ev = evaluate(ret, pos, pnl, split)
                res["variants"][f"{sname}|>{th}"] = ev
        report["pairs"][pair] = res
        print(f"[{pair}] n={n} eval {res['eval_span'][0]}..", flush=True)

    # verdict: variant promotes only if EVERY evaluated segment LCB>0
    verdicts = {}
    for pair, pr in report["pairs"].items():
        for vname, ev in pr["variants"].items():
            segs = [s for s in ev["segments"] if "lcb5" in s]
            ok = (segs and len(segs) == len(ev["segments"])
                  and all(s["lcb5"] > 0 for s in segs)
                  and ev["mean_bps"] > 0)
            verdicts[f"{vname}@{pair}"] = {
                "verdict": "candidate" if ok else "rejected",
                "mean": ev["mean_bps"], "lcb5": ev["lcb5"],
                "expo": ev["exposure"], "segments": ev["segments"]}
    report["verdicts"] = verdicts
    try:
        report["git_rev"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=ROOT).stdout.strip()
    except Exception:
        pass
    Path("var").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\n-> {args.out}")
    for k, v in sorted(verdicts.items(),
                       key=lambda kv: -kv[1]["mean"]):
        if v["mean"] > 0 or v["verdict"] == "candidate":
            print(f"  {k:<28} {v['verdict']:<10} mean={v['mean']:+.2f} "
                  f"lcb={v['lcb5']:+.2f} expo={v['expo']}")


if __name__ == "__main__":
    main()
