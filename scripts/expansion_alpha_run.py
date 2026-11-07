"""Bounded GA alpha-generation run on real market data.

Pipeline (all inside the canonical gated path):
  propose_alpha_generation  — genetic alpha search proposes expressions;
                              only ones the safe evaluator computes get
                              proposed as ga_expression candidates.
  validate_alpha_generation — each faces the sealed 70/30 holdout with
                              bootstrap significance; Benjamini-Hochberg
                              FDR then re-verdicts survivors — most
                              apparent wins in a sweep are luck.
  evolve_alpha_generation   — (optional) breeds offspring from FDR
                              survivors on a dev slice, re-verifies on a
                              sealed outer tail that never selected them.

Verdicts are whatever the sealed evaluations measure.

Usage:
    .venv/Scripts/python.exe scripts/expansion_alpha_run.py \
        --symbols EURUSD GBPUSD USDJPY --tail-bars 8000 --evolve
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.expansion_foundry_run import load_bars  # noqa: E402


async def run_symbol(csc: Any, symbol: str, bars: list,
                     skipped: int, args) -> dict:
    from trading_bot.core.csc.model_engineering import (
        evolve_alpha_generation, propose_alpha_generation,
        validate_alpha_generation)

    rec: dict = {"bars_used": len(bars), "offgrid_skipped": skipped}
    proposed = await propose_alpha_generation(
        csc, n_proposals=args.n_proposals,
        population_size=args.population)
    rec["proposed"] = len(proposed)
    if not proposed:
        rec["status"] = "no_candidates"
        return rec
    verdict = await validate_alpha_generation(csc, proposed, bars)
    cands = []
    for r in verdict["candidates"]:
        c = csc._engineered_models.get(r["candidate_id"])
        cands.append({
            "candidate_id": r["candidate_id"],
            "name": getattr(c, "name", ""),
            "status": r["status"],
            "verdict": getattr(c, "verdict", None),
            "p_le_0": round(r["p_le_0"], 5),
            "fdr_survived": r.get("fdr_survived"),
            "mean_net_bps": (getattr(c, "validation", {}) or {}).get(
                "mean_net_bps"),
            "holdout_signals": (getattr(c, "validation", {}) or {})
            .get("holdout_signals"),
        })
    rec["gen1"] = {"tested": verdict["tested"],
                   "validated_after_fdr": verdict["validated"],
                   "candidates": cands}
    survivors = [r["candidate_id"] for r in verdict["candidates"]
                 if r.get("fdr_survived")]
    if args.evolve and survivors:
        evo = await evolve_alpha_generation(
            csc, survivors, bars, n_offspring=args.n_offspring)
        rec["gen2"] = {"parents": evo["parents"],
                       "offspring": evo["offspring"],
                       "dev_validated": evo["dev_validated"],
                       "outer_confirmed": evo["outer_confirmed"],
                       "outer": evo["outer"]}
    rec["status"] = "completed"
    return rec


async def run(args) -> dict:
    from trading_bot.core.csc.controller import CognitiveSystemController
    csc = CognitiveSystemController()
    report = {"symbols": {}, "generated_at": __import__("time").time()}
    for symbol in args.symbols:
        bars, skipped = load_bars(
            ROOT / args.db, symbol, args.timeframe,
            args.tail_bars, args.tf_minutes)
        if len(bars) < 500:
            report["symbols"][symbol] = {
                "status": "skipped",
                "reason": f"only {len(bars)} clean bars"}
            continue
        report["symbols"][symbol] = await run_symbol(
            csc, symbol, bars, skipped, args)
        print(f"[{symbol}] proposed={report['symbols'][symbol].get('proposed')} "
              f"gen1_validated={report['symbols'][symbol].get('gen1', {}).get('validated_after_fdr')}",
              flush=True)
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbols", nargs="+", default=["EURUSD"])
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--tf-minutes", type=int, default=15)
    ap.add_argument("--tail-bars", type=int, default=8000)
    ap.add_argument("--n-proposals", type=int, default=20)
    ap.add_argument("--population", type=int, default=200)
    ap.add_argument("--n-offspring", type=int, default=8)
    ap.add_argument("--evolve", action="store_true")
    ap.add_argument("--out", default="var/expansion/alpha_gen_run.json")
    args = ap.parse_args()
    report = asyncio.run(run(args))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
