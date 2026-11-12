"""Cross-instrument feature experiment — the 'different information'
test the price+volume falsification baseline left open.

Each bar is enriched with ``peer_close`` from a synchronized second
symbol (joined on timestamp); the CSC derives ``peer_return`` and
``peer_corr`` from strictly-prior joint history. Specs then exercise
features the entire exhausted family never touched.

Sentiment and order-flow are not tested: ``sentiment_history.db`` is
empty (0 rows) and no bid/ask feed exists in any onboarded source —
there is nothing to evaluate, and none is fabricated.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.expansion_foundry_run import _off_grid  # noqa: E402

PEER_SPECS = [
    {"kind": "threshold_rule", "feature": "peer_return", "op": ">",
     "direction": "BUY", "name": "peer_ret_up_buy"},
    {"kind": "threshold_rule", "feature": "peer_return", "op": ">",
     "direction": "SELL", "name": "peer_ret_up_sell"},
    {"kind": "threshold_rule", "feature": "peer_return", "op": "<",
     "direction": "BUY", "name": "peer_ret_dn_buy"},
    {"kind": "threshold_rule", "feature": "peer_return", "op": "<",
     "direction": "SELL", "name": "peer_ret_dn_sell"},
    {"kind": "threshold_rule", "feature": "peer_corr", "op": ">",
     "direction": "BUY", "name": "peer_corr_hi_buy"},
    {"kind": "threshold_rule", "feature": "peer_corr", "op": "<",
     "direction": "SELL", "name": "peer_corr_lo_sell"},
    {"kind": "ga_expression",
     "expression": "correlation(returns, peer_return, 60)",
     "name": "ga_peer_corr60"},
    {"kind": "ga_expression",
     "expression": "zscore(delta(peer_close))",
     "name": "ga_peer_momentum"},
]


def load_bars_with_peer(db: Path, symbol: str, peer: str,
                        timeframe: str, tail: int,
                        tf_minutes: int) -> tuple[list, int]:
    """Joint bars: symbol's OHLCV + peer's close at the same timestamp.
    Inner join — a bar with no peer tick is dropped, not fabricated."""
    con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        a = {ts: (o, h, l, c, v) for ts, o, h, l, c, v in con.execute(
            "SELECT timestamp, open, high, low, close, volume FROM "
            "market_data WHERE symbol=? AND timeframe=? "
            "ORDER BY timestamp DESC LIMIT ?",
            (symbol, timeframe, tail * 2))}
        b = {ts: c for ts, c, in con.execute(
            "SELECT timestamp, close FROM market_data WHERE symbol=? "
            "AND timeframe=? ORDER BY timestamp DESC LIMIT ?",
            (peer, timeframe, tail * 2))}
    finally:
        con.close()
    skipped = 0
    bars = []
    for ts in sorted(set(a) & set(b)):
        if _off_grid(str(ts), tf_minutes):
            skipped += 1
            continue
        o, h, l, c, v = a[ts]
        bars.append({"timestamp": ts, "symbol": symbol, "open": o,
                     "high": h, "low": l, "close": c, "volume": v,
                     "price": c, "timeframe": timeframe,
                     "peer_close": b[ts]})
    return bars[-tail:], skipped


async def run(args) -> dict:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.expansion.foundry import AgentFoundry
    csc = CognitiveSystemController()
    foundry = AgentFoundry(ROOT / "var" / "expansion" / "foundry.json")
    report = {"pairs": {}, "generated_at": time.time()}
    for symbol, peer in args.pairs:
        bars, skipped = load_bars_with_peer(
            ROOT / args.db, symbol, peer, args.timeframe,
            args.tail_bars, args.tf_minutes)
        if len(bars) < 500:
            report["pairs"][f"{symbol}~{peer}"] = {
                "status": "skipped", "bars": len(bars)}
            continue
        rec = await foundry.run_generation(
            csc, bars, specs=PEER_SPECS,
            dataset_label=f"{symbol}~{peer}:{args.timeframe}")
        report["pairs"][f"{symbol}~{peer}"] = {
            "bars_used": len(bars), "offgrid_skipped": skipped,
            "candidates": [
                {"name": c["spec"]["name"], "status": c.get("status"),
                 "verdict": c.get("verdict"),
                 "mean_net_bps": c.get("mean_net_bps"),
                 "holdout_signals": c.get("holdout_signals"),
                 "p_gt_0": c.get("p_gt_0"),
                 "reason": c.get("reason")}
                for c in rec["candidates"]],
            "validated": rec["validated"], "rejected": rec["rejected"]}
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="market_data.db")
    ap.add_argument("--pairs", nargs=2, action="append",
                    metavar=("SYMBOL", "PEER"),
                    default=[["EURUSD", "GBPUSD"],
                             ["GBPUSD", "EURUSD"]])
    ap.add_argument("--timeframe", default="M15")
    ap.add_argument("--tf-minutes", type=int, default=15)
    ap.add_argument("--tail-bars", type=int, default=2500)
    ap.add_argument("--out", default="var/expansion/peer_real_run.json")
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
