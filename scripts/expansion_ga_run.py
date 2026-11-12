"""GA alpha-mining experiment on real market data.

``propose_alpha_generation`` breeds expression candidates through the
quarantined apex_fi GeneticAlphaSearch; only expressions the safe
evaluator can compute become ``ga_expression`` proposals. Then
``validate_alpha_generation`` runs each through the sealed holdout gate
and applies Benjamini-Hochberg FDR control across the batch — most
apparent wins in a generation sweep are luck, and the FDR gate exists
to say so honestly.

Same off-grid exclusion as the foundry run. Whatever survives (or
doesn't) is the measured result.

Usage:
    .venv/Scripts/python.exe scripts/expansion_ga_run.py \
        --symbols EURUSD GBPUSD USDJPY --tail-bars 4000 --n-proposals 15
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


async def run(args) -> dict:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.core.csc.model_engineering import (
        propose_alpha_generation, validate_alpha_generation)

    csc = CognitiveSystemController()
    report = {"symbols": {}, "generated_at": time.time(),
              "n_proposals": args.n_proposals,
              "population_size": args.population}
    for symbol in args.symbols:
        bars, skipped = load_bars(
            ROOT / args.db, symbol, args.timeframe,
            args.tail_bars, args.tf_minutes)
        if len(bars) < 500:
            report["symbols"][symbol] = {
                "status": "skipped",
                "reason": f"only {len(bars)} clean bars"}
            continue
        try:
            proposed = await propose_alpha_generation(
                csc, n_proposals=args.n_proposals,
                population_size=args.population)
        except Exception as exc:  # noqa: BLE001
            report["symbols"][symbol] = {
                "status": "error", "reason": str(exc)[:200]}
            continue
        if not proposed:
            report["symbols"][symbol] = {
                "status": "no_proposals",
                "bars_used": len(bars), "offgrid_skipped": skipped}
            continue
        verdict = await validate_alpha_generation(csc, proposed, bars)
        detail = []
        for r in verdict["candidates"]:
            c = csc._engineered_models.get(r["candidate_id"])
            val = getattr(c, "validation", {}) if c is not None else {}
            detail.append({
                "name": getattr(c, "name", "?") if c is not None
                        else "?",
                "expression": (getattr(c, "spec", {}) or {}).get(
                    "expression") if c is not None else None,
                "status": r.get("status"),
                "p_le_0": r.get("p_le_0"),
                "fdr_survived": r.get("fdr_survived"),
                "mean_net_bps": val.get("mean_net_bps"),
                "holdout_signals": val.get("holdout_signals"),
                "verdict": getattr(c, "verdict", None)
                if c is not None else None,
            })
        report["symbols"][symbol] = {
            "bars_used": len(bars), "offgrid_skipped": skipped,
            "proposed": len(proposed),
            "fdr_validated": verdict["validated"],
            "candidates": detail,
        }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbols", nargs="+", default=["EURUSD"])
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--tf-minutes", type=int, default=15)
    ap.add_argument("--tail-bars", type=int, default=4000)
    ap.add_argument("--n-proposals", type=int, default=15)
    ap.add_argument("--population", type=int, default=150)
    ap.add_argument("--out", default="var/expansion/ga_real_run.json")
    args = ap.parse_args()
    report = asyncio.run(run(args))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        try:
            prev = json.loads(out.read_text())
            report["symbols"] = {**prev.get("symbols", {}),
                                 **report["symbols"]}
        except Exception:  # noqa: BLE001
            pass
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
