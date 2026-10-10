#!/usr/bin/env python
"""Calibration report — the honest "is there edge" answer.

Aggregates DECISION_OUTCOME rows across run state dirs, discounts
shared settlements (N decisions scored on one market move are ONE
independent observation), splits paper vs real-bar sources, and reports
per-advisor precision with sample sizes. Numbers only ever get *more*
accurate as runs accumulate — re-run freely.

    python scripts/calibration_report.py var/dbseg_a var/dbseg_b ...
    python scripts/calibration_report.py --all          # scan var/*

Labels, not hype: 'independent' outcomes exclude correlated shares;
'provisional' below 20 independent outcomes; 'measured' at 20+.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _outcomes(db_path: Path) -> List[Dict[str, Any]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT correlation_id, action, outcome, event_json "
            "FROM audit_events WHERE event_type='DECISION_OUTCOME'"
        ).fetchall()
    finally:
        con.close()
    out = []
    for cid, action, outcome, raw in rows:
        try:
            d = json.loads(raw).get("details", {})
        except Exception:
            d = {}
        out.append({
            "trade_id": cid, "action": action,
            "correct": outcome == "correct",
            "realized_return": d.get("realized_return"),
            "regime": d.get("regime"),
            "confidence": d.get("confidence"),
            "shared": int(d.get("shared_settlement") or 1),
            "advisory_calls": d.get("advisory_calls") or [],
        })
    return out


def _label(n_independent: int) -> str:
    if n_independent == 0:
        return "no_data"
    if n_independent < 20:
        return "provisional"
    return "measured"


def report(state_dirs: List[Path]) -> Dict[str, Any]:
    all_outcomes = []
    per_run = {}
    for d in state_dirs:
        db = d / "trading_state.db"
        if not db.exists():
            continue
        outs = _outcomes(db)
        data_source = "unknown"
        snap = d / "snapshot.json"
        if snap.exists():
            try:
                data_source = (json.loads(snap.read_text())
                               .get("data_source") or "unknown")
            except Exception:
                pass
        for o in outs:
            o["run"] = d.name
            o["data_source"] = data_source
        all_outcomes.extend(outs)
        n_ind = sum(1.0 / o["shared"] for o in outs)
        per_run[d.name] = {
            "outcome_rows": len(outs),
            "independent_outcomes": round(n_ind, 2),
            "correct": sum(o["correct"] for o in outs),
            "data_source": data_source,
        }

    # Independent-sample stats: each shared settlement contributes
    # weight 1/N to both correct and total counts.
    def _independent_stats(outs):
        w_tot = sum(1.0 / o["shared"] for o in outs)
        w_ok = sum((1.0 / o["shared"]) for o in outs if o["correct"])
        rets = [o["realized_return"] for o in outs
                if isinstance(o["realized_return"], (int, float))]
        return {
            "independent_outcomes": round(w_tot, 2),
            "weighted_correct": round(w_ok, 2),
            "accuracy": round(w_ok / w_tot, 4) if w_tot else None,
            "mean_realized_return": (
                round(sum(rets) / len(rets), 6) if rets else None),
            "label": _label(int(w_tot)),
        }

    overall = _independent_stats(all_outcomes)
    real = _independent_stats(
        [o for o in all_outcomes if o["data_source"] == "db"])
    synthetic = _independent_stats(
        [o for o in all_outcomes if o["data_source"] == "synthetic"])

    # Per-advisor precision (directional calls scored on shared
    # settlements are likewise discounted).
    adv = defaultdict(lambda: [0.0, 0.0])
    for o in all_outcomes:
        decided = o["action"] in ("BUY", "SELL")
        for call in o["advisory_calls"]:
            d = str(call.get("direction") or "").upper()
            if d not in ("BUY", "SELL"):
                continue
            adv[call.get("capability_id")][1] += 1.0 / o["shared"]
            adv[call.get("capability_id")][0] += (
                (1.0 / o["shared"]) if (d == o["action"]) == o["correct"]
                else 0.0)
    advisors = {
        k: {"weighted_correct": round(ok, 2),
            "weighted_calls": round(tot, 2),
            "precision": round(ok / tot, 4) if tot else None,
            "label": _label(int(tot))}
        for k, (ok, tot) in sorted(
            adv.items(), key=lambda kv: -kv[1][1])
    }

    # Per-regime view.
    by_regime = defaultdict(list)
    for o in all_outcomes:
        by_regime[o.get("regime") or "unknown"].append(o)
    regimes = {r: _independent_stats(v) for r, v in by_regime.items()}

    return {
        "runs": per_run,
        "overall": overall,
        "real_bars_only": real,
        "synthetic_only": synthetic,
        "advisors": advisors,
        "regimes": regimes,
        "verdict": (
            "insufficient data — keep running"
            if overall["independent_outcomes"] < 20 else
            "edge measurable — see per-regime/advisor breakdown"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("state_dirs", nargs="*",
                    help="var/* state dirs with trading_state.db")
    ap.add_argument("--all", action="store_true",
                    help="scan every var/* dir containing a db")
    args = ap.parse_args()
    dirs = ([Path(p) for p in args.state_dirs] if not args.all
            else [d for d in (PROJECT_ROOT / "var").iterdir()
                  if (d / "trading_state.db").exists()])
    r = report(dirs)
    print(json.dumps(r, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
