#!/usr/bin/env python
"""Institutional decision journal — the spine an AFI institution needs.

Scans the existing artifact surface and emits TYPED DECISION RECORDS
into ``var/decisions.jsonl`` (append-only, deduped by decision_id).
Each record carries: who proposed it, on what evidence, what outcome
was predicted, under which authority level, and what was eventually
realized — the replayable decision->outcome attribution an institution
is accountable for.

Authority model (``var/authority.json``): autonomy is per action
class, not global. L0 observe/escalate-only, L1 draft proposals,
L2 sandboxed evaluation, L3 bounded live ops (operator-earned).
A record whose implied action exceeds the class level is tagged
``needs_operator`` — nothing in this file grants authority, it only
MAKES VISIBLE where the line is.

Records ingested:
  method_verdict    var/methods/ledger.jsonl     verdict = realized
  spec_candidate    var/analyst_queue.json        classification = status
  genome_proposal   var/development_genomes.jsonl predicted = objective
                    var/genome_evidence.jsonl     realized = latest holds
  data_request      var/data_requests.json        resolved = realized

Usage:
    python scripts/institution_journal.py ingest   # append new records
    python scripts/institution_journal.py report   # institutional view
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "var"
JOURNAL = VAR / "decisions.jsonl"
AUTHORITY = VAR / "authority.json"

# action class -> max autonomy the institution may exercise WITHOUT
# operator signature. Earned, not assumed: raising a level is an
# operator act recorded in this same file.
DEFAULT_AUTHORITY = {
    "levels": {
        "spec_evaluation": 2,    # evaluate candidates on held data
        "collection": 2,         # pull public data into local stores
        "genome_proposal": 1,    # draft bounded improvement proposals
        "research_eval": 2,      # measure live-outcome evidence
        "data_repair": 0,        # destructive fixes — escalate
        "method_promotion": 0,   # promote a method — operator only
        "external_action": 0,    # messages/trades/deploys — operator only
    },
    "scale": {
        "0": "observe + escalate only",
        "1": "draft proposals for operator review",
        "2": "sandboxed evaluation on local data",
        "3": "bounded live operations (operator-earned per class)",
        "4": "broad autonomy (requires measured record + consent)",
    },
    "note": "Raising a level is itself an operator-signed decision "
            "recorded in decisions.jsonl. Levels are never self-granted.",
    "updated": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _authority() -> dict:
    if not AUTHORITY.exists():
        AUTHORITY.write_text(json.dumps(DEFAULT_AUTHORITY, indent=2))
    try:
        return json.loads(AUTHORITY.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_AUTHORITY


def _level(auth: dict, action_class: str) -> int:
    return int(auth.get("levels", {}).get(action_class, 0))


def _decision_id(cls: str, key: str) -> str:
    return hashlib.sha1(f"{cls}|{key}".encode()).hexdigest()[:16]


def _record(cls, domain, actor, proposal, action_class, *,
            implied_level, evidence_refs=None, predicted=None,
            status="proposed", realized=None, key=""):
    lvl = _level(_authority(), action_class)
    return {
        "decision_id": _decision_id(cls, key or proposal[:80]),
        "ts": _now(),
        "class": cls,
        "domain": domain,
        "actor": actor,
        "proposal": proposal,
        "action_class": action_class,
        "authority": {"level": lvl, "implied": implied_level,
                      "needs_operator": implied_level > lvl},
        "evidence_refs": evidence_refs or [],
        "predicted": predicted,
        "status": status,
        "realized": realized,
    }


def _existing_ids() -> set:
    return {r.get("decision_id") for r in _load_jsonl(JOURNAL)}


def ingest() -> dict:
    seen = _existing_ids()
    new = []

    def add(rec):
        if rec["decision_id"] not in seen:
            seen.add(rec["decision_id"])
            new.append(rec)

    # --- method verdicts: evaluated spec records (realized at write) --
    for i, r in enumerate(_load_jsonl(VAR / "methods" / "ledger.jsonl")):
        spec = r.get("spec") or {}
        fam = spec.get("family", "?")
        sym = spec.get("symbol") or spec.get("spec_id") or "?"
        verdict = r.get("verdict")
        add(_record(
            "method_verdict", "method_evaluation", "method_eval",
            f"{fam} on {sym} @ cost {r.get('cost_bps')}",
            "spec_evaluation", implied_level=2,
            evidence_refs=["methods/ledger.jsonl"],
            predicted={"hypothesis": spec.get("hypothesis", "")[:120]},
            status="evaluated",
            realized={"verdict": verdict,
                      "net_bps": (r.get("stats") or {}).get(
                          "net_total_bps"),
                      "mechanism": (r.get("stats") or {}).get(
                          "mechanism")},
            key=f"{fam}|{sym}|{r.get('ts','')[:16]}|{verdict}"))

    # --- analyst queue candidates ----------------------------------
    qpath = VAR / "analyst_queue.json"
    if qpath.exists():
        try:
            queue = json.loads(qpath.read_text(encoding="utf-8"))
        except Exception:
            queue = {}
        for s in queue.get("specs", []):
            add(_record(
                "spec_candidate", "method_evaluation", "analyst",
                f"{s.get('family')}:{s.get('spec_id')} classified "
                f"{s.get('classification')}",
                "spec_evaluation", implied_level=2,
                evidence_refs=["analyst_queue.json"],
                predicted={"headroom_bps": s.get("cost_headroom_bps")},
                status="evaluated" if s.get("classification") == "DEAD"
                else "proposed",
                realized={"classification": s.get("classification"),
                          "datasets_positive": s.get(
                              "datasets_positive")},
                key=f"aq|{s.get('spec_id')}|{s.get('classification')}"))

    # --- development genomes + their evidence outcomes -------------
    latest_hold = {}
    for e in _load_jsonl(VAR / "genome_evidence.jsonl"):
        gid = e.get("genome_id")
        if gid:
            latest_hold[gid] = e
    for g in _load_jsonl(VAR / "development_genomes.jsonl"):
        gid = g.get("genome_id", "?")
        action = (g.get("change_set") or {}).get("action", "?")
        ev = latest_hold.get(gid)
        realized = None
        status = "proposed"
        if ev is not None:
            holds = ev.get("condition_holds", ev.get("holds"))
            realized = {"condition_holds": holds,
                        "checked_at": ev.get("ts") or ev.get(
                            "evaluated_at")}
            status = "evaluated"
        # the PROPOSAL is a draft (allowed); the ACTION it proposes
        # is what authority gates — destructive repair implies live
        # ops, bounded config/analysis changes imply draft level
        destructive = action in ("dedup_or_resync",)
        implied = 3 if destructive else 1
        add(_record(
            "genome_proposal", g.get("domain", "?"),
            "development_assist",
            g.get("objective", "")[:160],
            "data_repair" if destructive else "genome_proposal",
            implied_level=implied,
            evidence_refs=[(g.get("metadata") or {})
                           .get("evidence", "")],
            predicted={"objective": g.get("objective", "")[:160],
                       "verify": (g.get("evaluation_plan") or {})
                       .get("verify")},
            status=status, realized=realized, key=gid))

    # --- data/spec requests -----------------------------------------
    rq = VAR / "data_requests.json"
    if rq.exists():
        try:
            reqs = json.loads(rq.read_text(encoding="utf-8"))
        except Exception:
            reqs = {}
        for k, r in (reqs.get("requests") or {}).items():
            resolved = r.get("status") == "resolved"
            kind = r.get("kind", "data")
            destructive = kind == "data_repair"
            implied = 3 if destructive else 2
            add(_record(
                "data_request", "data_capability",
                r.get("spec_id") or "system",
                f"{kind}: {r.get('need','')[:140]}",
                "data_repair" if destructive else "collection",
                implied_level=implied,
                evidence_refs=["data_requests.json"],
                predicted={"action": r.get("action", "")[:160]},
                status="resolved" if resolved else "proposed",
                realized=({"resolved": r.get("resolution"),
                           "at": r.get("resolved_at")}
                          if resolved else None),
                key=f"req|{k}"))

    if new:
        with JOURNAL.open("a", encoding="utf-8") as f:
            for r in new:
                f.write(json.dumps(r) + "\n")
    return {"new_records": len(new), "journal": str(JOURNAL)}


def report() -> dict:
    recs = _load_jsonl(JOURNAL)
    by_class = {}
    needs_op = 0
    realized_pairs = []
    for r in recs:
        c = by_class.setdefault(r["class"], {"n": 0, "status": {},
                                             "needs_operator": 0})
        c["n"] += 1
        c["status"][r["status"]] = c["status"].get(r["status"], 0) + 1
        if r["authority"]["needs_operator"]:
            c["needs_operator"] += 1
            needs_op += 1
        if r.get("realized") is not None:
            realized_pairs.append(r)
    return {
        "records": len(recs),
        "by_class": by_class,
        "needs_operator_total": needs_op,
        "with_outcome": len(realized_pairs),
        "authority": _authority().get("levels"),
    }


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ingest"
    if cmd == "ingest":
        print(json.dumps(ingest(), indent=2))
    elif cmd == "report":
        print(json.dumps(report(), indent=2))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
