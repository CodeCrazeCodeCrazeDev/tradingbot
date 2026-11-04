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
    python scripts/operator_cli.py ai              # AI-stack planes summary
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
    parser.add_argument("--interactive", action="store_true",
                        help="review and sign an offline paper emergency reset")
    parser.add_argument("--approval-file",
                        help="externally signed reset JSON; verified against the pinned operator key")
    parser.add_argument("command",
                        choices=list(COMMAND_MAP) + ["status", "positions",
                                                     "explain", "ai",
                                                     "approve-model",
                                                     "list-models"])
    parser.add_argument("trade_id", nargs="?", default=None,
                        help="required by 'explain'; candidate_id for "
                             "'approve-model'")
    args = parser.parse_args(argv)

    state_dir = Path(args.state_dir)
    if args.command == "reset-emergency":
        from trading_bot.interfaces.operator_reset import (
            ResetApprovalError, consume_reset, reset_request,
            runner_lock, sign_interactively)
        if bool(args.interactive) == bool(args.approval_file):
            print("reset-emergency requires exactly one of --interactive or --approval-file; "
                  "the runner must be stopped.")
            return 2
        try:
            with runner_lock(state_dir):
                if args.interactive:
                    request = reset_request(state_dir, args.user, args.reason)
                    approval = sign_interactively(state_dir, request)
                else:
                    approval = json.loads(Path(args.approval_file).read_text(encoding="utf-8"))
                receipt = consume_reset(state_dir, approval)
            print(f"Signed paper reset applied and audited: {receipt['correlation_id']}. "
                  "The runner is still stopped; pause and other gates are unchanged.")
            return 0
        except (ResetApprovalError, OSError, ValueError, sqlite3.Error) as exc:
            print(f"Reset not applied: {exc}")
            return 2
    if args.command == "approve-model":
        # Human gate for engineered models: writes the durable flag the
        # CSC checks before attaching a candidate. Persistent, audited —
        # not a drainable command, since approval is a standing fact.
        if not args.trade_id:
            print("usage: operator_cli.py approve-model CANDIDATE_ID")
            return 2
        db_path = state_dir / "trading_state.db"
        if not db_path.exists():
            print(f"no state db at {db_path}")
            return 2
        import datetime as _dt
        con = sqlite3.connect(str(db_path))
        try:
            con.execute(
                "INSERT INTO account_state(key, value, updated_at) "
                "VALUES (?, 'approved', ?) ON CONFLICT(key) DO UPDATE SET "
                "value='approved', updated_at=excluded.updated_at",
                (f"control:model_approval:{args.trade_id}",
                 _dt.datetime.utcnow().isoformat()))
            import uuid as _uuid
            con.execute(
                "INSERT INTO audit_events(audit_id, event_type, actor, "
                "action, outcome, correlation_id, event_json, occurred_at) "
                "VALUES (?,'operator_control','operator','approve_model',"
                "'applied',?,?,?)",
                (_uuid.uuid4().hex, args.trade_id,
                 json.dumps({"details": {"candidate_id": args.trade_id,
                                         "user": args.user,
                                         "reason": args.reason}}),
                 _dt.datetime.utcnow().isoformat()))
            con.commit()
        finally:
            con.close()
        print(f"model_approval written for candidate {args.trade_id[:12]}")
        return 0
    if args.command == "list-models":
        db_path = state_dir / "trading_state.db"
        if not db_path.exists():
            print(f"no state db at {db_path}")
            return 2
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT correlation_id, action, outcome, occurred_at, "
                "event_json FROM audit_events WHERE event_type LIKE "
                "'MODEL_%' ORDER BY occurred_at").fetchall()
        finally:
            con.close()
        if not rows:
            print("no engineered-model events recorded")
            return 0
        for cid, action, outcome, ts, ej in rows:
            name = ""
            try:
                name = (json.loads(ej).get("details") or {}).get("name", "")
            except (json.JSONDecodeError, AttributeError):
                pass
            print(f"{ts}  {action:12s} {outcome:10s} {name}  {cid}")
        return 0
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
    if args.command in ("status", "positions", "ai"):
        snapshot_path = state_dir / "snapshot.json"
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print(f"no snapshot at {snapshot_path} — is the runner up?")
            return 2
        if args.command == "positions":
            print(json.dumps(snapshot.get("positions", []), indent=2,
                             default=str))
        elif args.command == "ai":
            planes = snapshot.get("ai_stack")
            if not planes:
                print("no ai_stack in snapshot — is the runner up?")
                return 2
            for plane, line in planes.items():
                print(f"{plane:10} {line}")
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
