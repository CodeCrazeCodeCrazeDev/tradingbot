#!/usr/bin/env python
"""Data-discovery scout: finds new market data and measures whether it
carries a tradable signal. Keyless Hyperliquid candles only -- never
trades, never weakens cost or evidence gates.

For each (coin, timeframe) in the grid:
  1. sync candles into --db-path via scripts/hyperliquid_sync.py
  2. run scripts/edge_baseline.py on that exact symbol/timeframe
  3. collect the honest verdict (candidate_edge only when the bootstrap
     lower confidence bound clears the required margin -- a positive
     mean alone is NOT evidence)

Output: a ranked report at var/data_scout.json + a per-combo table.
Verdicts measure THESE THREE RULES on THIS window/cost model only --
not the market as a whole.

    python scripts/data_scout.py
    python scripts/data_scout.py --coins BTC,ETH,SOL --timeframes 5m,15m,1h --days 60
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable] + cmd, cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    return proc.returncode, proc.stdout + proc.stderr


def scout(coins, timeframes, days, db_path, horizon) -> dict:
    report_path = ROOT / "var" / "edge_baseline.json"
    results = []
    for tf in timeframes:
        for coin in coins:
            combo = {"coin": coin, "timeframe": tf}
            print(f"\n=== {coin} {tf} ===", flush=True)
            rc, log = run(["scripts/hyperliquid_sync.py", "--coin", coin,
                           "--timeframe", tf, "--days", str(days),
                           "--db-path", str(db_path)])
            if rc != 0:
                combo["status"] = f"sync_failed rc={rc}"
                print("  " + log.strip().splitlines()[-1][:200])
                results.append(combo)
                continue
            rc, log = run(["scripts/edge_baseline.py", "--db-path",
                           str(db_path), "--symbol", coin,
                           "--timeframe", tf, "--horizon", str(horizon)])
            if rc != 0 or not report_path.exists():
                combo["status"] = f"baseline_failed rc={rc}"
                print("  " + log.strip().splitlines()[-1][:200])
                results.append(combo)
                continue
            r = json.loads(report_path.read_text())
            best = max(
                ((name, ru["lcb5_net_bps"]) for name, ru in
                 r.get("rules", {}).items()
                 if ru.get("lcb5_net_bps") is not None),
                key=lambda kv: kv[1], default=(None, None))
            combo.update({
                "status": "measured",
                "bars": r.get("bars"),
                "eval_window": r.get("eval_window"),
                "cost_bps": r.get("cost_bps"),
                "verdict": r.get("verdict"),
                "best_rule": best[0],
                "best_lcb5_net_bps": best[1],
                "rules": {k: {"status": v["status"],
                              "mean_net_bps": v["mean_net_bps"],
                              "lcb5_net_bps": v["lcb5_net_bps"],
                              "win_rate": v["win_rate"]}
                          for k, v in r.get("rules", {}).items()},
            })
            print(f"  verdict={combo['verdict']} best={combo['best_rule']}"
                  f" lcb5={combo['best_lcb5_net_bps']}", flush=True)
            results.append(combo)
    candidates = [r for r in results if r.get("verdict") == "candidate_edge"]
    measured = [r for r in results if r["status"] == "measured"]
    measured.sort(key=lambda r: (r.get("best_lcb5_net_bps") or -999),
                  reverse=True)
    return {
        "generated_at": time.time(), "grid": {"coins": coins,
        "timeframes": timeframes, "days": days, "horizon": horizon},
        "verdict": ("candidates_found" if candidates
                    else "no_edge_anywhere"),
        "candidates": candidates,
        "ranked": measured,
        "failures": [r for r in results if r["status"] != "measured"],
        "scope": "3 fixed rules, chronological 60/40 split, embargo, "
                 "block bootstrap LCB; not a market-wide proof",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coins", default="BTC,ETH,SOL")
    ap.add_argument("--timeframes", default="15m,1h")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--db-path", default="hl_data.db")
    args = ap.parse_args()
    out = scout([c.strip() for c in args.coins.split(",") if c.strip()],
                [t.strip() for t in args.timeframes.split(",") if t.strip()],
                args.days, args.db_path, args.horizon)
    rp = ROOT / "var" / "data_scout.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(out, indent=2))
    print(f"\n{'='*56}\nVERDICT: {out['verdict']}  report: {rp}")
    print(f"{'combo':<10}{'bars':>6}{'cost':>7}{'best rule':<16}{'lcb5':>8}")
    for r in out["ranked"]:
        print(f"{r['coin']+'/'+r['timeframe']:<10}{r['bars'] or 0:>6}"
              f"{r['cost_bps'] or 0:>7.1f}{str(r['best_rule']):<16}"
              f"{r['best_lcb5_net_bps']:>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
