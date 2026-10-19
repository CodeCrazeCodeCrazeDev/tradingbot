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


def fill_reward_report(state_dir: Path) -> dict:
    """Read actual matched-fill feedback without replaying decision indices."""
    db = (state_dir / "trading_state.db").resolve()
    connection = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT event_json FROM audit_events WHERE event_type='PAPER_SETTLEMENT'"
        ).fetchall()
    finally:
        connection.close()
    settlements = [json.loads(row[0])["details"] for row in rows]
    complete = [s for s in settlements if not s["blockers"]]
    currencies = {}
    for s in complete:
        bucket = currencies.setdefault(s["currency"], {
            "entry_notional": 0.0, "gross_pnl": 0.0, "costs": 0.0,
            "net_pnl": 0.0, "baseline_net_pnl": 0.0})
        notional = s["entry_notional"]
        bucket["entry_notional"] += notional
        bucket["gross_pnl"] += notional * s["gross_return"]
        bucket["costs"] += notional * s["cost_return"]
        bucket["net_pnl"] += s["net_pnl"]
        bucket["baseline_net_pnl"] += notional * s["baseline_net_return"]
    for bucket in currencies.values():
        bucket["net_advantage"] = bucket["net_pnl"] - bucket["baseline_net_pnl"]
    return {
        "evidence_class": "diagnostic", "promotion_eligible": False,
        "origin": "paper", "baseline_provenance": "counterfactual",
        "baseline_id": "always_long_same_fills_v1",
        "matched_lots": len(settlements), "costed_lots": len(complete),
        "blocked_lots": len(settlements) - len(complete),
        "opening_decisions": len({s["decision_id"] or s["entry_order_id"]
                                  for s in complete}),
        "market_data_sources": sorted({s.get("market_data_source", "unknown")
                                       for s in complete}),
        "by_currency": currencies,
        "limitations": [
            "Matched lots may be correlated; no significance claim.",
            "Open inventory and mark-only forecast closes are excluded.",
            "Notional and PnL are in quote currency; not account-equity returns.",
        ],
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--timeframe", default="M15")
    p.add_argument("--skip", type=int, default=60000,
                   help="bars skipped before the run's first bar")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--min-decisions", type=int, default=20)
    p.add_argument("--fill-rewards", action="store_true",
                   help="score durable paper fill settlements, without source-bar replay")
    args = p.parse_args(argv)

    if args.fill_rewards:
        report = fill_reward_report(args.state_dir)
        out = args.state_dir / "fill_reward_score.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        print(f"\n-> {out}")
        return 0

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
