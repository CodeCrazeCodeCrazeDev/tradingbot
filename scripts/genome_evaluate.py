#!/usr/bin/env python
"""Genome evaluation bridge — closes proposal -> evidence.

development_assist.py emits ImprovementGenome proposals; this
bridge evaluates each one's declared target condition against
CURRENT artifact state and writes EvaluationEvidence records.
PromotionDecision stays human — evidence only, never promotion.

Checks are cheap state reads (the genome's verify plan is
descriptive; v1 evaluates 'does the target condition still
hold' honestly rather than executing repairs):

  data_intelligence     flags still present in data_quality.json?
  hypothesis_generation spec still WATCH in analyst_queue.json?
  model_architecture    variant still in me_report with failure?
  research_prioritization request still open in data_requests.json?

Output: var/genome_evidence.jsonl (append, dedup by genome_id)
+ var/genome_evaluation_report.json. Advisory-only.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "var"
GENOMES = VAR / "development_genomes.jsonl"
EVIDENCE = VAR / "genome_evidence.jsonl"
REPORT = VAR / "genome_evaluation_report.json"


def _load(name):
    p = VAR / name
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def _genomes():
    if not GENOMES.exists():
        return []
    out = []
    for line in GENOMES.read_text(encoding="utf-8",
                                  errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def _evaluated_ids():
    ids = set()
    if EVIDENCE.exists():
        for line in EVIDENCE.read_text(encoding="utf-8",
                                       errors="replace").splitlines():
            try:
                ids.add(json.loads(line).get("genome_id"))
            except Exception:
                pass
    return ids


def _check(genome: dict) -> dict:
    """Return {holds: bool, detail: str} — does the genome's target
    condition still hold in current artifacts?"""
    dom = genome.get("domain")
    cs = genome.get("change_set") or {}
    meta = genome.get("metadata") or {}
    ev = meta.get("evidence", "")

    if dom == "data_intelligence":
        target = cs.get("target", "")
        _, sym, tf = (target.split(":") + ["", ""])[:3]
        dq = _load("data_quality.json") or {}
        for d in dq.get("dbs", []):
            if d.get("db") != target.split(":")[0]:
                continue
            for s in d.get("series", []):
                if s.get("symbol") == sym and \
                        s.get("timeframe") == tf:
                    bad = {k: s.get(k) for k in
                           ("off_grid", "non_monotonic",
                            "extreme_ret", "dup_ts") if s.get(k)}
                    return {"holds": bool(bad),
                            "detail": f"flags={bad} "
                                      f"(audit may be stale)"}
        return {"holds": False,
                "detail": "series not found in latest audit"}

    if dom == "hypothesis_generation":
        sid = cs.get("spec_id")
        q = _load("analyst_queue.json") or {}
        for s in q.get("specs", []):
            if s.get("spec_id") == sid:
                return {"holds": s.get("classification") == "WATCH",
                        "detail": f"classification="
                                  f"{s.get('classification')}"}
        return {"holds": False, "detail": "spec no longer tracked"}

    if dom == "model_architecture":
        tag = (cs.get("variant") or {}).get("tag") or \
            str(cs.get("variant"))
        me = _load("model_engineering_report.json") or {}
        for v in me.get("variants", []):
            if v.get("tag") == tag or tag in str(v.get("tag")):
                return {"holds": True,
                        "detail": f"status={v.get('status')} "
                                  f"rv16={v.get('rv16_r2')}"}
        return {"holds": False, "detail": "variant not in report"}

    if dom == "research_prioritization":
        need = cs.get("need")
        dr = _load("data_requests.json") or {}
        open_needs = [r.get("need") for r in
                      (dr.get("requests") or {}).values()
                      if r.get("status") != "resolved"]
        return {"holds": any(need and need in str(n)
                             for n in open_needs),
                "detail": f"request_open={need in open_needs}"}

    return {"holds": True, "detail": "no checker for domain"}


def main() -> int:
    genomes = _genomes()
    done = _evaluated_ids()
    EVIDENCE.parent.mkdir(exist_ok=True)
    wrote = 0
    results = []
    with open(EVIDENCE, "a", encoding="utf-8") as f:
        for g in genomes:
            gid = g.get("genome_id")
            if not gid or gid in done:
                continue
            chk = _check(g)
            rec = {
                "genome_id": gid,
                "domain": g.get("domain"),
                "objective": g.get("objective"),
                "evaluated_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"),
                "condition_holds": chk["holds"],
                "detail": chk["detail"],
                "evidence_ref": (g.get("metadata") or {})
                .get("evidence"),
                "promotion_eligible": False,
                "note": "evidence only — PromotionDecision is "
                        "operator-gated"}
            f.write(json.dumps(rec, default=str) + "\n")
            done.add(gid)
            wrote += 1
            results.append(rec)
    report = {"ran_at": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "genomes": len(genomes),
        "evaluated_now": wrote,
        "holds": sum(1 for r in results if r["condition_holds"]),
        "total_evidence":
        sum(1 for _ in open(EVIDENCE, encoding="utf-8"))
        if EVIDENCE.exists() else 0}
    REPORT.write_text(json.dumps(report, indent=2))
    print(f"genome evaluation: {wrote} evaluated "
          f"({report['holds']} conditions still hold) "
          f"-> {EVIDENCE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
