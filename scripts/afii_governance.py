#!/usr/bin/env python
"""AFII governance kernel — deterministic authority over intelligence.

The AFII principle: AI proposes and evaluates; a DETERMINISTIC policy
engine authorizes; independent monitors can halt. This module is the
authorize+halt half — it contains no learned components and grants no
authority to itself.

Layering (institution -> AFII):
  var/authority.json        subsystem-internal autonomy table
                            (AlphaAlgo's own action classes)
  var/afii/governance.json  AFII-level registry: named SUBSYSTEMS with
                            permissions, risk budgets, status. Today
                            AlphaAlgo is the only active subsystem;
                            AEAN registers when it produces evidence.
  var/afii/HALT             independent monitor halt — existence of
                            this file pauses every gated stage in the
                            autonomous cycle. Any monitor/operator may
                            create it; only an operator removes it.
  var/afii/capital_ledger.jsonl
                            typed capital records: allocation,
                            obligation, reserve, release — append-only.
                            Balances are DERIVED, never stored.

Usage:
    python scripts/afii_governance.py status
    python scripts/afii_governance.py auth alphaalgo spec_evaluation 2
    python scripts/afii_governance.py halt --reason "spread anomaly"
    python scripts/afii_governance.py unhalt   # operator action
    python scripts/afii_governance.py record allocation alphaalgo \
        --amount 0 --unit bps --evidence "probe budget"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AFII = ROOT / "var" / "afii"
GOVERNANCE = AFII / "governance.json"
HALT = AFII / "HALT"
CAPITAL = AFII / "capital_ledger.jsonl"

DEFAULT_GOVERNANCE = {
    "version": 1,
    "note": "AFII authority registry. Subsystems propose; this file "
            "authorizes. Level scale matches var/authority.json: "
            "L0 observe, L1 draft, L2 sandboxed eval, L3 bounded live "
            "(operator-earned), L4 broad (measured record + consent). "
            "Edits here ARE operator acts — log them to decisions.",
    "subsystems": {
        "alphaalgo": {
            "domain": "market intelligence + method evaluation",
            "status": "active",
            "max_level": 2,
            "risk_budget_bps": 0,
            "permissions": [
                "spec_evaluation", "collection", "genome_proposal",
                "research_eval", "journal", "lob_collect",
            ],
            "denied": ["method_promotion", "data_repair",
                       "external_action", "capital_allocation"],
            "evidence": [
                "var/decisions.jsonl",
                "var/methods/ledger.jsonl",
                "var/autonomous_cycle/reports",
            ],
        },
        "aean": {
            "domain": "economic reasoning + venture operations",
            "status": "registered",
            "max_level": 0,
            "risk_budget_bps": 0,
            "permissions": [],
            "denied": ["all — registered, not yet producing "
                       "measured evidence under this governance"],
            "evidence": [
                "C:\\Users\\peterson\\aean\\docs\\PLAN_STATUS.md",
                "C:\\Users\\peterson\\aean\\docs\\"
                "56_GATE_A_TECHNICAL_EVIDENCE_V1.md",
                "C:\\Users\\peterson\\aean\\data\\bakeoff_results.json",
            ],
        },
    },
    "evidence_rule": "Activation above L0 requires resolvable measured-"
                     "evidence links AND an operator signature — the "
                     "kernel checks links exist; it never judges quality.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_governance() -> dict:
    if not GOVERNANCE.exists():
        AFII.mkdir(parents=True, exist_ok=True)
        GOVERNANCE.write_text(json.dumps(DEFAULT_GOVERNANCE, indent=2))
    return json.loads(GOVERNANCE.read_text(encoding="utf-8"))


def halted() -> dict | None:
    """Independent monitor surface: HALT file present => halted."""
    if not HALT.exists():
        return None
    try:
        return json.loads(HALT.read_text(encoding="utf-8"))
    except Exception:
        return {"reason": "HALT file present (unreadable body)"}


def check_authorization(subsystem: str, action_class: str,
                        implied_level: int) -> dict:
    """Deterministic policy: subsystem active + class permitted +
    implied level within max_level -> authorized. Anything else is a
    denial with a reason — never an exception path."""
    if halted() is not None:
        return {"authorized": False, "reason": "AFII halt active"}
    gov = load_governance()
    sub = gov.get("subsystems", {}).get(subsystem)
    if sub is None:
        return {"authorized": False,
                "reason": f"subsystem {subsystem!r} not registered"}
    if sub.get("status") != "active":
        ev = verify_evidence(subsystem).get(subsystem, {})
        return {"authorized": False,
                "reason": f"subsystem {subsystem!r} status="
                          f"{sub.get('status')!r}; evidence resolvable "
                          f"{ev.get('resolvable', '0/0')} — activation "
                          "needs measured links + operator signature"}
    if action_class in sub.get("denied", []):
        return {"authorized": False,
                "reason": f"{action_class!r} denied for {subsystem}"}
    if action_class not in sub.get("permissions", []):
        return {"authorized": False,
                "reason": f"{action_class!r} not in permissions"}
    if implied_level > int(sub.get("max_level", 0)):
        return {"authorized": False,
                "reason": f"implied L{implied_level} exceeds max_level "
                          f"L{sub.get('max_level')} — operator gate"}
    return {"authorized": True,
            "reason": f"within L{sub.get('max_level')} authority"}


def halt(reason: str, by: str = "monitor") -> dict:
    AFII.mkdir(parents=True, exist_ok=True)
    rec = {"halted_at": _now(), "by": by, "reason": reason}
    HALT.write_text(json.dumps(rec, indent=2))
    return rec


def unhalt() -> bool:
    if HALT.exists():
        HALT.unlink()
        return True
    return False


def record_capital(subsystem: str, kind: str, amount: float,
                   unit: str, evidence: str) -> dict:
    """Append a typed capital record. kinds: allocation (budget
    assigned), obligation (committed liability), reserve (held back),
    release (freed). Balances are derived by summing, never stored."""
    AFII.mkdir(parents=True, exist_ok=True)
    if kind not in ("allocation", "obligation", "reserve", "release"):
        raise ValueError(f"bad capital kind {kind!r}")
    rec = {"ts": _now(), "subsystem": subsystem, "kind": kind,
           "amount": float(amount), "unit": unit,
           "evidence": evidence[:200]}
    with CAPITAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def verify_evidence(subsystem: str | None = None) -> dict:
    """Resolve each subsystem's declared evidence links. Reports
    exists/missing/mtime per link — the kernel CHECKS linkage, it
    never pretends to judge the evidence itself."""
    gov = load_governance()
    out = {}
    for name, sub in gov.get("subsystems", {}).items():
        if subsystem and name != subsystem:
            continue
        links = []
        for p in sub.get("evidence", []):
            path = Path(p)
            if not path.is_absolute():
                path = ROOT / p
            links.append({
                "path": p,
                "exists": path.exists(),
                "mtime": (datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc)
                    .isoformat(timespec="seconds")
                    if path.exists() else None)})
        n_ok = sum(1 for l in links if l["exists"])
        out[name] = {"links": links,
                     "resolvable": f"{n_ok}/{len(links)}"}
    return out


def capital_position(subsystem: str | None = None) -> dict:
    """Derived balances per subsystem: allocated - obligations -
    reserves + releases = available headroom."""
    pos: dict[str, dict] = {}
    if CAPITAL.exists():
        for line in CAPITAL.read_text(
                encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if subsystem and r.get("subsystem") != subsystem:
                continue
            p = pos.setdefault(r.get("subsystem"), {
                k: 0.0 for k in
                ("allocation", "obligation", "reserve", "release")})
            k = r.get("kind")
            if k in p:
                p[k] += float(r.get("amount") or 0.0)
    for p in pos.values():
        p["available"] = round(
            p["allocation"] - p["obligation"] - p["reserve"]
            + p["release"], 6)
    return pos


def status() -> dict:
    gov = load_governance()
    return {
        "halt": halted(),
        "subsystems": {k: {"status": v.get("status"),
                           "max_level": v.get("max_level"),
                           "risk_budget_bps": v.get("risk_budget_bps")}
                       for k, v in gov.get("subsystems", {}).items()},
        "capital": capital_position(),
        "evidence": {k: v["resolvable"]
                     for k, v in verify_evidence().items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    ve = sub.add_parser("verify")
    ve.add_argument("subsystem", nargs="?")
    au = sub.add_parser("auth")
    au.add_argument("subsystem")
    au.add_argument("action_class")
    au.add_argument("implied_level", type=int)
    ha = sub.add_parser("halt")
    ha.add_argument("--reason", default="manual halt")
    sub.add_parser("unhalt")
    rc = sub.add_parser("record")
    rc.add_argument("kind", choices=["allocation", "obligation",
                                     "reserve", "release"])
    rc.add_argument("subsystem")
    rc.add_argument("--amount", type=float, required=True)
    rc.add_argument("--unit", default="bps")
    rc.add_argument("--evidence", default="")
    args = ap.parse_args()

    if args.cmd == "status":
        print(json.dumps(status(), indent=2))
    elif args.cmd == "verify":
        print(json.dumps(verify_evidence(args.subsystem), indent=2))
    elif args.cmd == "auth":
        print(json.dumps(check_authorization(
            args.subsystem, args.action_class,
            args.implied_level), indent=2))
    elif args.cmd == "halt":
        print(json.dumps(halt(args.reason), indent=2))
    elif args.cmd == "unhalt":
        print(json.dumps({"removed": unhalt()}))
    elif args.cmd == "record":
        print(json.dumps(record_capital(
            args.subsystem, args.kind, args.amount, args.unit,
            args.evidence), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
