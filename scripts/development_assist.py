#!/usr/bin/env python
"""Development-assist: the system proposes its own improvements.

Scans the evidence artifacts the AFI stack already produces and
formalizes improvement opportunities as ImprovementGenome
proposals — the human-governed RSI contract ("never executable
code by itself"). The CSC doesn't patch itself; it identifies
what deserves development attention and writes auditable,
bounded proposals for operator review.

Sources -> domains:
  data_quality.json      contaminated series -> DATA_INTELLIGENCE
  analyst_queue.json     WATCH near-misses    -> HYPOTHESIS_GENERATION
  model_engineering_*    failed variants      -> MODEL_ARCHITECTURE
  data_requests.json     open needs           -> RESEARCH_PRIORITIZATION

Output: var/development_genomes.jsonl (append, dedup by
fingerprint) + var/development_assist_report.json. Advisory-only.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
VAR = ROOT / "var"
OUT = VAR / "development_genomes.jsonl"
REPORT = VAR / "development_assist_report.json"
MAX_PER_RUN = 6


def _load(name):
    p = VAR / name
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def _existing_fingerprints() -> set:
    fps = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8",
                                  errors="replace").splitlines():
            try:
                fps.add(json.loads(line).get("fingerprint"))
            except Exception:
                pass
    return fps


def _gen(domain, objective, change_set, eval_plan, evidence_ref,
         safety=None, metadata=None):
    from trading_bot.recursive_self_improvement.improvement_genome \
        import ImprovementDomain, ImprovementGenome
    g = ImprovementGenome(
        domain=ImprovementDomain(domain),
        objective=objective,
        change_set=change_set,
        evaluation_plan=eval_plan,
        safety_constraints=safety or {
            "promotion": "operator_review_required",
            "auto_execute": False},
        metadata={"evidence": evidence_ref,
                  "generated_by": "development_assist",
                  **(metadata or {})})
    d = g.to_dict()
    d["fingerprint"] = g.fingerprint
    return d


def collect_genomes() -> list:
    out = []

    # DATA_INTELLIGENCE: contaminated series found by the audit
    dq = _load("data_quality.json") or {}
    for d in dq.get("dbs", []):
        for s in d.get("series", []):
            bad = {k: s.get(k) for k in
                   ("off_grid", "non_monotonic", "extreme_ret",
                    "dup_ts") if s.get(k)}
            if not bad:
                continue
            out.append(_gen(
                "data_intelligence",
                f"Repair contaminated series {d['db']}:"
                f"{s['symbol']}:{s['timeframe']} "
                f"({', '.join(f'{k}={v}' for k, v in bad.items())})",
                {"action": "dedup_or_resync",
                 "target": f"{d['db']}:{s['symbol']}:{s['timeframe']}",
                 "flags": bad},
                {"verify": "rerun data_quality_audit; flags -> 0"},
                f"data_quality.json#{d['db']}:{s['symbol']}:"
                f"{s['timeframe']}"))

    # HYPOTHESIS_GENERATION: WATCH specs deserve mutation budgets
    q = _load("analyst_queue.json") or {}
    for s in q.get("specs", []):
        if s.get("classification") != "WATCH":
            continue
        out.append(_gen(
            "hypothesis_generation",
            f"Expand mutation neighborhood around WATCH spec "
            f"{s.get('spec_id')} ({s.get('family')}) — near-miss "
            f"with headroom {s.get('cost_headroom_bps')}bps",
            {"action": "raise_mutation_budget_or_widen_grid",
             "spec_id": s.get("spec_id"),
             "current_budget": "--mutation-budget 4"},
            {"verify": "mutation candidates reach candidate verdict"},
            f"analyst_queue.json#{s.get('spec_id')}"))

    # MODEL_ARCHITECTURE: search variants that failed — lessons
    me = _load("model_engineering_report.json") or {}
    for v in me.get("variants", []):
        if v.get("status") == "train_failed" or \
                (v.get("rv16_r2") is not None
                 and v["rv16_r2"] < 0):
            out.append(_gen(
                "model_architecture",
                f"Investigate failed model variant {v.get('tag')}: "
                f"{v.get('status') or 'negative rv16 R2'}",
                {"action": "diagnose_variant",
                 "variant": v.get("variant"),
                 "logs": f"var/me_search/{v.get('tag')}_*.log"},
                {"verify": "variant diagnosis recorded; "
                           "dead ends documented"},
                f"model_engineering_report.json#{v.get('tag')}"))

    # RESEARCH_PRIORITIZATION: open data requests = dev priorities
    dr = _load("data_requests.json") or {}
    for r in (dr.get("requests") or {}).values():
        if (r.get("count") or 0) < 1:
            continue
        out.append(_gen(
            "research_prioritization",
            f"Fulfill open request ({r.get('kind')}): "
            f"{r.get('need')} — seen {r.get('count')}x",
            {"action": r.get("action"),
             "kind": r.get("kind"), "need": r.get("need")},
            {"verify": "request leaves data_requests.json"},
            f"data_requests.json#{r.get('spec_id')}"))
    return out


def main() -> int:
    genomes = collect_genomes()[:MAX_PER_RUN]
    seen = _existing_fingerprints()
    wrote = 0
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        for g in genomes:
            if g["fingerprint"] in seen:
                continue
            f.write(json.dumps(g, default=str) + "\n")
            seen.add(g["fingerprint"])
            wrote += 1
    report = {"ran_at": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "proposed": len(genomes),
        "written": wrote, "total_ledger":
        sum(1 for _ in open(OUT, encoding="utf-8"))
        if OUT.exists() else 0}
    REPORT.write_text(json.dumps(report, indent=2))
    print(f"development assist: {wrote} new genome proposals "
          f"({len(genomes)} candidates) -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
