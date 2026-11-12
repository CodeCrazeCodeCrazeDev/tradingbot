"""Dump the research knowledge-graph claim ledger from a run's audit trail.

Read-only: replays RESEARCH_KG (nodes/edges) and RESEARCH (questions,
verdicts) audit events from <state-dir>/trading_state.db and prints a
human-readable ledger — what the research engine asked, what it found,
and which claims stand, fell, or replicated.

Usage:
    .venv/Scripts/python.exe scripts/research_ledger.py \
        --state-dir var/paper_fx
    .venv/Scripts/python.exe scripts/research_ledger.py \
        --state-dir var/paper_fx --edges --limit 50
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def load_events(db_path: Path):
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT occurred_at, event_type, action, outcome, "
            "correlation_id, event_json FROM audit_events "
            "WHERE event_type IN ('RESEARCH', 'RESEARCH_KG') "
            "ORDER BY occurred_at").fetchall()
    finally:
        con.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--edges", action="store_true",
                    help="also print KG edge rows")
    ap.add_argument("--limit", type=int, default=30,
                    help="max questions/claims to print (newest first)")
    args = ap.parse_args()

    db_path = Path(args.state_dir) / "trading_state.db"
    if not db_path.exists():
        print(f"no audit db at {db_path}")
        return 1

    rows = load_events(db_path)
    nodes, edges, investigations, cycles = [], [], [], []
    for occurred_at, etype, action, outcome, cid, raw in rows:
        try:
            details = json.loads(raw).get("details", {})
        except (json.JSONDecodeError, TypeError):
            details = {}
        if etype == "RESEARCH_KG" and action == "KG_NODE":
            nodes.append((occurred_at, details))
        elif etype == "RESEARCH_KG" and action == "KG_EDGE":
            edges.append((occurred_at, details))
        elif etype == "RESEARCH" and action == "investigate":
            investigations.append((occurred_at, outcome, details))
        elif etype == "RESEARCH" and action == "cycle":
            cycles.append((occurred_at, details))

    print(f"state-dir: {args.state_dir}")
    print(f"KG nodes: {len(nodes)} | KG edges: {len(edges)} | "
          f"investigations: {len(investigations)} | cycles: {len(cycles)}")

    # Verdict tally across all investigations
    tally = {}
    for _, outcome, _ in investigations:
        tally[outcome] = tally.get(outcome, 0) + 1
    if tally:
        print("verdicts:", dict(sorted(tally.items(),
                                     key=lambda kv: -kv[1])))

    print("\n--- investigations (newest first) ---")
    for occurred_at, outcome, d in investigations[-args.limit:][::-1]:
        conf = d.get("composite_confidence")
        conf_s = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "?"
        print(f"[{occurred_at[:19]}] {outcome:14s} conf={conf_s}  "
              f"{str(d.get('question'))[:100]}")
        ext = d.get("external_evidence")
        if isinstance(ext, dict):
            srcs = ext.get("sources") or []
            print(f"    internet: {ext.get('status')} ({len(srcs)} sources)"
                  + (f" reason={ext.get('reason')}"
                     if ext.get("reason") else ""))
            for s in srcs[:3]:
                print(f"      [{s.get('source')}] "
                      f"{str(s.get('title'))[:80]}")

    if args.edges:
        print("\n--- KG edges (newest first) ---")
        for occurred_at, d in edges[-args.limit:][::-1]:
            print(f"[{occurred_at[:19]}] {d.get('src')} "
                  f"-[{d.get('relation')}]-> {d.get('dst')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
