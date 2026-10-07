#!/usr/bin/env python
"""Local operator CLI for a running paper_runner / canonical runtime.

Commands write to the control channel the runner drains between cycles:

    python scripts/operator_cli.py pause
    python scripts/operator_cli.py resume
    python scripts/operator_cli.py flatten
    python scripts/operator_cli.py cancel-all
    python scripts/operator_cli.py estop --reason "fat finger check"
    python scripts/operator_cli.py status          # read snapshot
    python scripts/operator_cli.py positions       # read snapshot positions
    python scripts/operator_cli.py explain TRADE_ID  # durable decision trail

Mutating commands can only restrict or unwind exposure — this surface has
no order-entry capability by design. ``status``/``positions`` read the
published snapshot file; ``explain`` opens the durable state db read-only
and prints the audit trail for one trade_id. None of them can trade.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_STATE_DIR = PROJECT_ROOT / "var" / "paper"

COMMAND_MAP = {
    "pause": "pause",
    "resume": "resume",
    "estop": "emergency_stop",
    "reset-emergency": "reset_emergency",
    "flatten": "flatten",
    "cancel-all": "cancel_all",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--user", default="operator")
    parser.add_argument("--reason", default="")
    parser.add_argument("command",
                        choices=list(COMMAND_MAP) + ["status", "positions",
                                                     "explain"])
    parser.add_argument("trade_id", nargs="?", default=None,
                        help="required by 'explain'")
    args = parser.parse_args(argv)

    state_dir = Path(args.state_dir)
    if args.command == "explain":
        if not args.trade_id:
            print("usage: operator_cli.py explain TRADE_ID")
            return 2
        db_path = state_dir / "trading_state.db"
        if not db_path.exists():
            print(f"no state db at {db_path} — has the runner produced a "
                  "decision yet?")
            return 2
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT event_type, actor, action, outcome, event_json, "
                "occurred_at FROM audit_events WHERE correlation_id=? "
                "ORDER BY occurred_at ASC", (args.trade_id,)).fetchall()
        except sqlite3.OperationalError as exc:
            print(f"audit read failed: {exc}")
            return 2
        finally:
            con.close()
        if not rows:
            print(f"no audit trail for trade_id={args.trade_id}")
            return 1
        for etype, actor, action, outcome, event_json, occurred in rows:
            print(f"{occurred}  {etype:18} {action:22} -> {outcome}")
            try:
                details = json.loads(event_json).get("details")
                if details:
                    print(f"    {json.dumps(details, default=str)}")
            except (json.JSONDecodeError, AttributeError):
                pass
        return 0
    if args.command in ("status", "positions"):
        snapshot_path = state_dir / "snapshot.json"
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print(f"no snapshot at {snapshot_path} — is the runner up?")
            return 2
        if args.command == "positions":
            print(json.dumps(snapshot.get("positions", []), indent=2,
                             default=str))
        else:
            print(json.dumps(snapshot, indent=2, default=str))
        return 0

    from trading_bot.interfaces.control import ControlChannel

    channel = ControlChannel(state_dir / "control")
    command = channel.send(COMMAND_MAP[args.command], user=args.user,
                           reason=args.reason)
    print(f"queued {args.command} (id={command['id'][:8]}) for next cycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
