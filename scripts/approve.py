#!/usr/bin/env python3
"""Operator CLI for the human approval gate (trading_bot.human_layer).

The running bot persists pending approval requests as
``human_layer/request_<id>.json`` and polls ``human_layer/decision_<id>.json``
while waiting. This tool lists pending requests and writes decision files so
a human can approve/reject STANDARD/CRITICAL actions in live mode.

Usage:
    python scripts/approve.py list
    python scripts/approve.py approve <request_id> [--approver NAME] [--reason TEXT]
    python scripts/approve.py reject <request_id> --reason TEXT [--approver NAME]

Options:
    --storage PATH   Override the approval storage dir (default: human_layer/)
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

STORAGE = Path("human_layer")


def _requests(storage: Path) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted(storage.glob("request_*.json")):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def cmd_list(storage: Path) -> int:
    pending = [
        (p, r) for p, r in _requests(storage) if r.get("status") == "pending"
    ]
    if not pending:
        print("No pending approval requests.")
        return 0
    print(f"{len(pending)} pending request(s):\n")
    for _, r in pending:
        print(f"  {r['request_id']}")
        print(f"    action: {r.get('action')}   level: {r.get('level')}")
        print(f"    description: {r.get('description')}")
        print(f"    risk: {r.get('risk_assessment')}   created: {r.get('created_at')}")
        details = r.get("details") or {}
        if details:
            print(f"    details: {json.dumps(details)[:200]}")
        print()
    return 0


def cmd_decide(storage: Path, request_id: str, status: str, approver: str, reason: str) -> int:
    req = storage / f"request_{request_id}.json"
    if not req.exists():
        # allow prefix match — request ids are UUIDs
        matches = [p for p, r in _requests(storage) if r.get("request_id", "").startswith(request_id)]
        if len(matches) == 1:
            req = matches[0]
            request_id = json.loads(req.read_text(encoding="utf-8"))["request_id"]
        else:
            print(f"error: request '{request_id}' not found ({len(matches)} prefix matches)", file=sys.stderr)
            return 2
    decision = {
        "request_id": request_id,
        "status": status,
        "approver": approver,
        "reason": reason,
    }
    (storage / f"decision_{request_id}.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )
    print(f"{status.upper()}: {request_id} (decision file written — gate polls ~1s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--storage", default=str(STORAGE), help="approval storage dir (default: human_layer/)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list pending requests")
    ap = sub.add_parser("approve", help="approve a request")
    ap.add_argument("request_id")
    ap.add_argument("--approver", default=getpass.getuser())
    ap.add_argument("--reason", default="approved via scripts/approve.py")
    rj = sub.add_parser("reject", help="reject a request")
    rj.add_argument("request_id")
    rj.add_argument("--approver", default=getpass.getuser())
    rj.add_argument("--reason", required=True)
    args = parser.parse_args()

    storage = Path(args.storage)
    storage.mkdir(parents=True, exist_ok=True)
    if args.cmd == "list":
        return cmd_list(storage)
    if args.cmd == "approve":
        return cmd_decide(storage, args.request_id, "approved", args.approver, args.reason)
    return cmd_decide(storage, args.request_id, "rejected", args.approver, args.reason)


if __name__ == "__main__":
    raise SystemExit(main())
