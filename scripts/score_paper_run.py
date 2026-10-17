#!/usr/bin/env python
"""Score a prospective paper run against frozen baselines.

Reads a paper_runner state-dir (decision_log.jsonl + market_history.json)
and the source bars, projects the CSC's position stream onto per-bar
returns, and runs compare_candidate_vs_baseline vs always_long and frozen
momentum. Diagnostic evidence only — never promotion.

    python scripts/score_paper_run.py --state-dir var/paper_run_p3 \
        --skip 60000
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from trading_bot.evaluation.frozen_baseline import (  # noqa: E402
    compare_candidate_vs_baseline)


def load_source_bars(symbol: str, timeframe: str, skip: int):
    con = sqlite3.connect(
        f"file:{PROJECT_ROOT / 'market_data.db'}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp, close FROM market_data "
            "WHERE symbol=? AND timeframe=? ORDER BY timestamp ASC",
            (symbol, timeframe)).fetchall()
    finally:
        con.close()
    return rows[skip:]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--timeframe", default="M15")
    p.add_argument("--skip", type=int, default=60000,
                   help="bars skipped before the run's first bar")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--min-decisions", type=int, default=20)
    args = p.parse_args(argv)

    log = args.state_dir / "decision_log.jsonl"
    if not log.exists():
        print(f"no decision log at {log}")
        return 1
    decisions = [json.loads(l) for l in log.read_text().splitlines()
                 if l.strip()]
    if not decisions:
        print("decision log is empty — run still warming up")
        return 1

    bars = load_source_bars(args.symbol, args.timeframe, args.skip)
    closes = [float(r[1]) for r in bars[:len(decisions) + 2]]
    rets = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]

    # Project decisions onto positions: hold preserves, abstain holds.
    pos, positions = 0.0, []
    for d in decisions[:len(rets)]:
        outcome = str(d.get("outcome") or "")
        action = str(d.get("action") or "")
        if outcome == "TRADE_APPROVED":
            pos = 1.0 if action == "BUY" else -1.0 if action == "SELL" else pos
        positions.append(pos)

    n = min(len(positions), len(rets))
    positions, rets = positions[:n], rets[:n]
    ma = 10
    momentum = [1.0 if closes[i] >= np.mean(closes[max(0, i - ma):i])
                else -1.0 for i in range(1, len(closes))][:n]

    report = {
        "decisions_scored": len(decisions), "paired_bars": n,
        "vs_always_long": compare_candidate_vs_baseline(
            positions, [1.0] * n, rets, cost_bps=args.cost_bps,
            min_decisions=args.min_decisions),
        "vs_frozen_momentum": compare_candidate_vs_baseline(
            positions, momentum, rets, cost_bps=args.cost_bps,
            min_decisions=args.min_decisions),
    }
    out = args.state_dir / "baseline_score.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    for k, v in report.items():
        if isinstance(v, dict) and "verdict" in v:
            c, b = v["candidate"], v["baseline"]
            print(f"{k}: {v['verdict']} | csc_net={c['total_net']:+.6f} "
                  f"base_net={b['total_net']:+.6f} edge={v.get('net_edge', 0):+.6f}")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
