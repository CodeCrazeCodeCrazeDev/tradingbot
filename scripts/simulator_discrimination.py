"""Simulator discrimination test: can the CSC's counterfactual
simulator tell a good trade from a bad one?

Method: replay real LSE EURUSD bars through the three fixed rules;
for every signal, build the SAME MarketState the CSC's hypothesis
generator builds (trend from momentum, |mom|/0.005 strength,
volatility percentile, uncertainty) and run the REAL
CounterfactualSimulator — then compare predicted expected_value
against the realized net outcome (direction * fwd_return - cost).

Discrimination metrics:
  - Spearman rank corr (predicted EV vs realized net bps)
  - mean net bps of EV>0 cohort vs EV<=0 cohort
  - precision@top-quartile-EV vs base rate
Verdicts:
  discriminates  — EV>0 cohort net-positive AND beats EV<=0 by margin
  no_discrimination — cohorts statistically identical
"""

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.cognition.state.contracts import MarketState
from trading_bot.cognition.simulation.contracts import (
    SimulationRequest)
from trading_bot.cognition.simulation.engine import CounterfactualSimulator

from scripts.edge_baseline import (
    RULES, load_bars, roll_spread_bps)


def _market_state(closes, i, symbol, timeframe):
    """Mirror hypothesis._build_market_state on bar i."""
    mom = (closes[i] - closes[i - 20]) / closes[i - 20] \
        if i >= 20 else 0.0
    trend = "BULLISH" if mom > 0.0005 else \
        ("BEARISH" if mom < -0.0005 else "NEUTRAL")
    ts = min(1.0, abs(mom) / 0.005)
    # realized vol percentile over trailing 64 bars of |returns|
    if i >= 64:
        r = np.diff(np.log(closes[i - 63:i + 1]))
        vol = float(np.std(r))
        hist = np.array([np.std(np.diff(np.log(closes[j - 20:j + 1])))
                         for j in range(i - 63, i)])
        vp = float(np.mean(hist <= vol)) if len(hist) else 0.5
    else:
        vol, vp = 0.0, 0.5
    return MarketState(
        timestamp=0.0, instrument=symbol,
        primary_timeframe=timeframe,
        trend_direction=trend, trend_strength=float(ts),
        volatility_percentile=vp, uncertainty=0.2)


def _spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    if n < 3:
        return 0.0
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    d = ra - rb
    return 1.0 - 6.0 * float((d * d).sum()) / (n * (n * n - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default="lse_data.db")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--eval-frac", type=float, default=0.40)
    ap.add_argument("--embargo", type=int, default=20)
    ap.add_argument("--mc-paths", type=int, default=32)
    ap.add_argument("--alignment-prior", type=str, default="1.0",
                    help="float in [-1,1] or 'auto' = estimate the sign "
                         "of alignment value from the DISCOVERY window")
    args = ap.parse_args()

    ts, bars = load_bars(args.db_path, args.symbol, args.timeframe)
    closes = bars[:, 3]
    n = len(closes)
    disc_end = int(n * (1.0 - args.eval_frac))
    eval_start, eval_end = disc_end + args.embargo, n
    roll = roll_spread_bps(closes)
    cost_bps = max(roll or 0.0, 5.0)
    print(f"eval {eval_start}..{eval_end} | cost {cost_bps:.1f}bps")

    # alignment_prior: 'auto' measures whether trend-alignment paid on
    # the DISCOVERY window (never the eval window — no leakage). Mean
    # net of aligned trades vs opposed trades on discovery, squashed to
    # [-1,1] by sign + magnitude ratio.
    alignment_prior = 1.0
    if str(args.alignment_prior).lower() == "auto":
        al_net, op_net = [], []
        for name, fn in RULES.items():
            for i in range(64, disc_end - args.horizon):
                s = fn(closes, i)
                if s == 0:
                    continue
                mom = (closes[i] - closes[i - 20]) / closes[i - 20]
                bullish = mom > 0.0005
                bearish = mom < -0.0005
                aligned = (s > 0 and bullish) or (s < 0 and bearish)
                opposed = (s > 0 and bearish) or (s < 0 and bullish)
                net = s * (closes[i + args.horizon] - closes[i]) \
                    / closes[i] * 1e4 - cost_bps
                if aligned:
                    al_net.append(net)
                elif opposed:
                    op_net.append(net)
        ma = float(np.mean(al_net)) if al_net else 0.0
        mo = float(np.mean(op_net)) if op_net else 0.0
        # measured sign: does alignment beat opposition on discovery?
        denom = abs(ma) + abs(mo) or 1.0
        alignment_prior = max(-1.0, min(1.0, (ma - mo) / denom))
        print(f"auto alignment_prior={alignment_prior:.3f} "
              f"(disc: aligned {ma:.2f}bps n={len(al_net)} "
              f"vs opposed {mo:.2f}bps n={len(op_net)})")
    else:
        alignment_prior = float(args.alignment_prior)

    sim = CounterfactualSimulator()
    rows = []
    for name, fn in RULES.items():
        for i in range(eval_start,
                       min(eval_end, n - args.horizon)):
            s = fn(closes, i)
            if s == 0:
                continue
            state = _market_state(closes, i, args.symbol,
                                  args.timeframe)
            action = "BUY" if s > 0 else "SELL"
            try:
                res = sim.simulate(SimulationRequest(
                    request_id=f"{name}:{i}",
                    current_state=state,
                    proposed_action=action,
                    position_size=0.1,
                    monte_carlo_paths=args.mc_paths,
                    scenario_adjustments={
                        "alignment_prior": alignment_prior}))
                ev = float(res.expected_value or 0.0)
                wp = float(res.win_probability or 0.0)
            except Exception as e:
                ev, wp = float("nan"), float("nan")
            fwd = (closes[i + args.horizon] - closes[i]) \
                / closes[i] * 1e4
            net = s * fwd - cost_bps
            rows.append({"rule": name, "bar": i, "action": action,
                         "pred_ev": ev, "pred_wp": wp,
                         "realized_net_bps": net})

    evs = np.array([r["pred_ev"] for r in rows])
    nets = np.array([r["realized_net_bps"] for r in rows])
    valid = np.isfinite(evs)
    evs, nets = evs[valid], nets[valid]
    n_ev = len(evs)
    print(f"simulated {n_ev} candidates "
          f"({len(rows) - n_ev} sim failures dropped)")

    rho = _spearman(evs, nets)
    pos = nets[evs > 0]
    neg = nets[evs <= 0]
    q75 = np.percentile(evs, 75)
    top = nets[evs >= q75]
    base = float(np.mean(nets))
    verdict = ("discriminates"
               if len(pos) and np.mean(pos) > np.mean(neg) + 1.0
               and np.mean(pos) > 0
               else "no_discrimination")

    out = {
        "candidates": n_ev, "eval_window": [eval_start, eval_end],
        "cost_bps": cost_bps,
        "alignment_prior": alignment_prior,
        "spearman_ev_vs_net": round(rho, 4),
        "ev_positive": {"n": int(len(pos)),
                        "mean_net_bps": round(
                            float(np.mean(pos)), 3)
                        if len(pos) else None},
        "ev_nonpositive": {"n": int(len(neg)),
                           "mean_net_bps": round(
                               float(np.mean(neg)), 3)
                           if len(neg) else None},
        "top_quartile_ev": {"n": int(len(top)),
                            "mean_net_bps": round(
                                float(np.mean(top)), 3),
                            "vs_base": round(
                                float(np.mean(top) - base), 3)},
        "base_mean_net_bps": round(base, 3),
        "verdict": verdict,
        "honest_note": "Spearman ~0 + identical cohorts = the sim "
                       "assigns EV without ranking power on this "
                       "data; discrimination requires EV>0 cohort "
                       "to beat EV<=0 AND clear zero."}
    print(json.dumps({k: v for k, v in out.items()
                      if k != "honest_note"}, indent=1))
    print("VERDICT:", verdict)
    rp = ROOT / "var" / "simulator_discrimination.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(out, indent=2))
    print("report:", rp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
