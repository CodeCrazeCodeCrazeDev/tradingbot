"""Run a real expansion-foundry generation on real market data.

This is the measurable experiment, not a claim: candidate specs are
proposed through ``csc.propose_model`` and fitted/evaluated through the
CSC's sealed holdout gate (``csc.validate_model`` — 70/30 split, net
expectancy after the cost model, bootstrap significance vs zero and vs
buy-and-hold). Whatever verdict comes out is the verdict; nothing is
adjusted to look better.

Off-grid contaminated rows (fractional-second timestamps, minute%15!=0)
are excluded and counted — the same mask the world-model eval uses.

Usage:
    .venv/Scripts/python.exe scripts/expansion_foundry_run.py \
        --symbols EURUSD GBPUSD USDJPY --tail-bars 8000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _off_grid(ts: str, tf_minutes: int) -> bool:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return True
    return bool(dt.microsecond or (dt.minute % tf_minutes) != 0)


def load_bars(db: Path, symbol: str, timeframe: str, tail: int,
              tf_minutes: int) -> tuple[list, int]:
    con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp, open, high, low, close, volume FROM ("
            "SELECT timestamp, open, high, low, close, volume FROM "
            "market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp",
            (symbol, timeframe, tail)).fetchall()
    finally:
        con.close()
    skipped = 0
    bars = []
    for ts, o, h, l, c, v in rows:
        if _off_grid(str(ts), tf_minutes):
            skipped += 1
            continue
        bars.append({"timestamp": ts, "symbol": symbol,
                     "open": o, "high": h, "low": l, "close": c,
                     "volume": v, "price": c, "timeframe": timeframe})
    return bars, skipped


async def run(args) -> dict:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.expansion.foundry import AgentFoundry

    csc = CognitiveSystemController()
    foundry = AgentFoundry(ROOT / "var" / "expansion" / "foundry.json")
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
        rec = await foundry.run_generation(
            csc, bars, dataset_label=f"{symbol}:{args.timeframe}")
        report["symbols"][symbol] = {
            "bars_used": len(bars), "offgrid_skipped": skipped,
            "candidates": [
                {"name": c["spec"].get("name"),
                 "status": c.get("status"),
                 "verdict": c.get("verdict"),
                 "mean_net_bps": c.get("mean_net_bps"),
                 "holdout_signals": c.get("holdout_signals"),
                 "p_gt_0": c.get("p_gt_0"),
                 "reason": c.get("reason")}
                for c in rec["candidates"]],
            "validated": rec["validated"],
            "rejected": rec["rejected"],
        }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--symbols", nargs="+", default=["EURUSD"])
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--tf-minutes", type=int, default=15)
    ap.add_argument("--tail-bars", type=int, default=8000)
    ap.add_argument("--out", default="var/expansion/foundry_real_run.json")
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
