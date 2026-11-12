"""Expansion sweep — the four follow-up experiments in one honest run.

Each sub-experiment writes into ``var/expansion/sweep_results.json`` as
soon as it finishes, so partial results survive a stop:

A) regime_gated   — measure ret_autocorr per series, then run the
                    matching family only: fade rules where the series
                    mean-reverts, trend rules where it trends. The
                    regime is measured, never assumed.
B) cost_sensitivity — same sealed gate at several COST_BPS values. The
                    override lands in the seal's recorded cost_bps, so
                    each verdict is honestly attributed.
C) venue          — Hyperliquid crypto series (the highest measured
                    structure in the inventory) through the same gate.
D) horizon        — same signal family at horizons 8/24/48 to test
                    whether the edge (if any) lives at a different
                    timescale.

Usage:
    .venv/Scripts/python.exe -u scripts/expansion_sweep.py \
        --experiments regime cost venue horizon --tail-bars 2000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.expansion_foundry_run import load_bars  # noqa: E402
from trading_bot.expansion.scanner import series_stats  # noqa: E402

FADE_SPECS = [
    {"kind": "threshold_rule", "feature": "momentum", "op": ">",
     "direction": "SELL", "name": "fade_momentum_sell"},
    {"kind": "threshold_rule", "feature": "momentum", "op": "<",
     "direction": "BUY", "name": "fade_momentum_buy"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": ">",
     "direction": "SELL", "name": "fade_rsi_sell"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
     "direction": "BUY", "name": "fade_rsi_buy"},
]
TREND_SPECS = [
    {"kind": "threshold_rule", "feature": "momentum", "op": ">",
     "direction": "BUY", "name": "trend_momentum_buy"},
    {"kind": "threshold_rule", "feature": "momentum", "op": "<",
     "direction": "SELL", "name": "trend_momentum_sell"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": ">",
     "direction": "BUY", "name": "trend_rsi_buy"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
     "direction": "SELL", "name": "trend_rsi_sell"},
]
# The strongest GA expressions from the FX run — reused at horizons.
GA_POOL = [
    "zscore(ts_min(ts_min(low)))",
    "ts_rank(zscore(covariance(volume, close, 120)), 10)",
]

OUT = ROOT / "var" / "expansion" / "sweep_results.json"


def _save(key: str, payload: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text())
        except Exception:  # noqa: BLE001
            data = {}
    data[key] = payload
    data["updated_at"] = time.time()
    OUT.write_text(json.dumps(data, indent=2, default=str))
    print(f"[saved:{key}]", json.dumps(payload, default=str)[:900],
          flush=True)


def _specs_with_horizon(family, horizons):
    out = []
    for h in horizons:
        for s in family:
            d = dict(s)
            d["horizon"] = h
            d["name"] = f"{s['name']}_h{h}"
            out.append(d)
    return out


async def exp_regime(csc, foundry, args) -> None:
    for symbol in args.symbols:
        bars, skipped = load_bars(
            ROOT / args.db, symbol, args.timeframe,
            args.tail_bars, args.tf_minutes)
        st = series_stats([b["close"] for b in bars])
        if st is None:
            _save(f"regime:{symbol}", {"status": "insufficient_data"})
            continue
        mean_rev = st["ret_autocorr"] < 0
        family = FADE_SPECS if mean_rev else TREND_SPECS
        rec = await foundry.run_generation(
            csc, bars, specs=family,
            dataset_label=f"{symbol}:{args.timeframe}")
        _save(f"regime:{symbol}", {
            "measured": {"ret_autocorr": st["ret_autocorr"],
                         "sign_persistence": st["sign_persistence"]},
            "regime_family": "fade" if mean_rev else "trend",
            "bars": len(bars), "offgrid_skipped": skipped,
            "candidates": [
                {"name": c["spec"]["name"], "status": c.get("status"),
                 "verdict": c.get("verdict"),
                 "mean_net_bps": c.get("mean_net_bps"),
                 "reason": c.get("reason")}
                for c in rec["candidates"]],
            "validated": rec["validated"], "rejected": rec["rejected"]})


async def exp_cost(csc, foundry, args) -> None:
    from trading_bot.core.csc import model_engineering as me
    symbol = args.cost_symbol
    bars, skipped = load_bars(
        ROOT / args.db, symbol, args.timeframe,
        args.tail_bars, args.tf_minutes)
    for cb in args.costs:
        me.COST_BPS = float(cb)  # recorded in each evaluation's seal
        rec = await foundry.run_generation(
            csc, bars, specs=TREND_SPECS,
            dataset_label=f"{symbol}:{args.timeframe}@cost{cb}")
        _save(f"cost:{symbol}@{cb}bps", {
            "cost_bps": cb, "bars": len(bars),
            "candidates": [
                {"name": c["spec"]["name"], "status": c.get("status"),
                 "verdict": c.get("verdict"),
                 "mean_net_bps": c.get("mean_net_bps"),
                 "holdout_signals": c.get("holdout_signals")}
                for c in rec["candidates"]],
            "validated": rec["validated"], "rejected": rec["rejected"]})
    me.COST_BPS = 3.25


async def exp_venue(csc, foundry, args) -> None:
    for db, symbol, tf, tfmin in args.venue_series:
        bars, skipped = load_bars(
            ROOT / db, symbol, tf, args.tail_bars, tfmin)
        if len(bars) < 500:
            _save(f"venue:{symbol}:{tf}",
                  {"status": "skipped", "bars": len(bars)})
            continue
        st = series_stats([b["close"] for b in bars])
        mean_rev = bool(st and st["ret_autocorr"] < 0)
        family = FADE_SPECS if mean_rev else TREND_SPECS
        rec = await foundry.run_generation(
            csc, bars, specs=family,
            dataset_label=f"{symbol}:{tf}@{db}")
        _save(f"venue:{symbol}:{tf}", {
            "db": db, "bars": len(bars), "offgrid_skipped": skipped,
            "measured": st, "regime_family":
            "fade" if mean_rev else "trend",
            "candidates": [
                {"name": c["spec"]["name"], "status": c.get("status"),
                 "verdict": c.get("verdict"),
                 "mean_net_bps": c.get("mean_net_bps"),
                 "p_gt_0": c.get("p_gt_0")}
                for c in rec["candidates"]],
            "validated": rec["validated"], "rejected": rec["rejected"]})


async def exp_horizon(csc, foundry, args) -> None:
    symbol = args.cost_symbol
    bars, skipped = load_bars(
        ROOT / args.db, symbol, args.timeframe,
        args.tail_bars, args.tf_minutes)
    specs = []
    for h in args.horizons:
        for expr in GA_POOL:
            specs.append({"kind": "ga_expression", "expression": expr,
                          "horizon": h,
                          "name": f"ga_h{h}:{expr[:20]}"})
    rec = await foundry.run_generation(
        csc, bars, specs=specs,
        dataset_label=f"{symbol}:{args.timeframe}:horizon_sweep")
    _save(f"horizon:{symbol}", {
        "bars": len(bars),
        "candidates": [
            {"name": c["spec"]["name"],
             "horizon": c["spec"].get("horizon"),
             "status": c.get("status"), "verdict": c.get("verdict"),
             "mean_net_bps": c.get("mean_net_bps"),
             "holdout_signals": c.get("holdout_signals"),
             "reason": c.get("reason")}
            for c in rec["candidates"]],
        "validated": rec["validated"], "rejected": rec["rejected"]})


async def run(args) -> None:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.expansion.foundry import AgentFoundry
    csc = CognitiveSystemController()
    foundry = AgentFoundry(ROOT / "var" / "expansion" / "foundry.json")
    jobs = {
        "regime": exp_regime, "cost": exp_cost,
        "venue": exp_venue, "horizon": exp_horizon}
    for name in args.experiments:
        print(f"[experiment:{name}] starting", flush=True)
        await jobs[name](csc, foundry, args)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbols", nargs="+",
                    default=["EURUSD", "GBPUSD", "USDJPY"])
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--tf-minutes", type=int, default=15)
    ap.add_argument("--tail-bars", type=int, default=2000)
    ap.add_argument("--cost-symbol", default="EURUSD")
    ap.add_argument("--costs", type=float, nargs="+",
                    default=[0.0, 1.0, 2.0, 3.25])
    ap.add_argument("--horizons", type=int, nargs="+",
                    default=[8, 24, 48])
    ap.add_argument("--venue-series", nargs=4, action="append",
                    metavar=("DB", "SYMBOL", "TF", "TFMIN"),
                    default=[
                        ["hl_data.db", "BTC", "15m", "15"],
                        ["hl_data.db", "ETH", "15m", "15"],
                        ["hl_data.db", "SOL", "15m", "15"],
                        ["hl_data.db", "LTC", "4h", "240"]])
    ap.add_argument("--experiments", nargs="+",
                    default=["regime", "cost", "venue", "horizon"])
    args = ap.parse_args()
    args.venue_series = [
        (d, s, t, int(m)) for d, s, t, m in args.venue_series]
    asyncio.run(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
