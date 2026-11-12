"""Internet capability scout — the real scout->fetch->scan->evaluate slice.

Pulls REAL candidates from GitHub / arXiv / HuggingFace (no fixtures),
feeds each through the full ECIE gate stack (classify -> trust ->
license -> security -> distill -> compile -> governance), and writes
an auditable JSONL ledger. Everything stays advisory: the strongest
verdict a candidate can reach here is a governance *proposal* —
promotion still requires signed operator approval, and nothing enters
the trading path automatically.

Usage:
    .venv/Scripts/python.exe scripts/internet_scout.py \
        --query "order flow imbalance" --sources github,arxiv
    .venv/Scripts/python.exe scripts/internet_scout.py \
        --query "walk forward validation" --out var/ecie/ledger.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.research.ecie.fetchers import FETCHERS
from trading_bot.research.ecie.pipeline import ECIEPipeline
from trading_bot.research.ecie.governance import GovernanceGate
from trading_bot.research.ecie.models import LicenseStatus
from trading_bot.research.orchestration.research_os import ResearchWorkspace


def run_gate_stack(pipeline: ECIEPipeline, governance: GovernanceGate,
                   candidate) -> dict:
    """One candidate through every gate; returns an auditable record."""
    rec = {
        "name": candidate.name,
        "source": candidate.source_type.value,
        "url": candidate.url,
        # description feeds method_eval's spec extractor — keyword
        # mapping needs the actual text, not just the name
        "description": (candidate.description or "")[:300],
        "version": candidate.version_id,
        "license": candidate.license_name,
        "stars": candidate.stars,
        "ts": datetime.now(timezone.utc).isoformat(),
        "gates": {},
        "final": None,
    }

    cat = pipeline.classify_candidate(candidate)
    rec["gates"]["category"] = cat.value

    trust = pipeline.assess_trust_score(candidate)
    rec["gates"]["trust"] = {
        "score": trust.overall_score,
        "level": trust.trust_level.value,
        "acceptable": trust.is_acceptable,
        "signals": {k: v for k, v in trust.signals.items()},
    }

    lic = pipeline.analyze_license(candidate)
    rec["gates"]["license"] = lic.value

    samples = list(candidate.metadata.get("code_samples") or [])
    executable = bool(samples)  # papers/model cards carry no code —
    # the trust gate's has_tests prong is structurally impossible for
    # documents, so they reach governance for its own verdict instead
    rec["gates"]["trust"]["mode"] = "code" if executable else "document"

    sec = pipeline.perform_security_scan(candidate, samples)
    rec["gates"]["security"] = {
        "secure": sec.is_secure,
        "secrets": len(sec.secrets_found),
        "unsafe": sec.unsafe_patterns[:5],
        "malicious": sec.malicious_scripts_detected,
        "scanned_files": len(samples),
    }

    # Early exits — record WHY the candidate stopped here
    if lic == LicenseStatus.FORBIDDEN:
        rec["final"] = "REJECTED_LICENSE"
        return rec
    if not sec.is_secure:
        rec["final"] = "REJECTED_SECURITY"
        return rec
    if executable and not trust.is_acceptable:
        rec["final"] = "REJECTED_TRUST"
        return rec

    pattern = pipeline.distill_pattern(candidate, cat, samples)
    skill = pipeline.compile_skill(pattern)
    proposal = governance.submit_proposal(
        skill, candidate.url, candidate.version_id,
        candidate.license_name, trust, sec, lic)
    ok, verdict = governance.evaluate_promotion(proposal.proposal_id)
    rec["gates"]["proposal"] = proposal.proposal_id
    rec["final"] = verdict

    # M1 extraction seam: distillate text -> bounded MethodSpecs the
    # edge gate can kill. Advisory only — specs enter var ledgers,
    # never the trading path. Import is guarded: spec extraction must
    # never sink a scout run.
    if verdict and "REJECT" not in verdict and verdict != "NO_FETCH":
        try:
            from trading_bot.core.csc.research.spec_extractor import (
                extract_specs)
            specs = extract_specs(
                f"{candidate.name}\n{candidate.description or ''}",
                provenance={"source": candidate.source_type.value,
                            "url": candidate.url,
                            "scout_query_record": rec.get("name")})
            if specs:
                rec["method_specs"] = [
                    {"spec_id": s.spec_id, "family": s.family,
                     "params": s.params, "spec_hash": s.spec_hash,
                     "hypothesis": s.hypothesis[:200]}
                    for s in specs]
        except Exception as e:  # honest skip, recorded
            rec["method_specs_error"] = f"{type(e).__name__}: {e}"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--query", required=True,
                    help="search terms, e.g. 'order flow imbalance'")
    ap.add_argument("--sources", default="github,arxiv",
                    help="comma list: github,arxiv,hf")
    ap.add_argument("--max-results", type=int, default=3,
                    help="per source (each costs several API calls)")
    ap.add_argument("--out", default="var/ecie/scout_ledger.jsonl")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = ECIEPipeline()
    governance = GovernanceGate(ResearchWorkspace())

    all_records = []
    for src in args.sources.split(","):
        fetcher = FETCHERS.get(src.strip())
        if fetcher is None:
            print(f"unknown source {src!r} — skip "
                  f"(valid: {sorted(FETCHERS)})")
            continue
        print(f"\n=== scouting {src} for {args.query!r} ===")
        candidates = fetcher(args.query, args.max_results)
        if not candidates:
            print(f"  [{src}] 0 candidates (fetch failed or no results)")
            all_records.append({
                "source": src, "query": args.query, "final": "NO_FETCH",
                "ts": datetime.now(timezone.utc).isoformat()})
            continue
        for c in candidates:
            rec = run_gate_stack(pipeline, governance, c)
            all_records.append(rec)
            g = rec["gates"]
            print(f"\n  {c.name}")
            print(f"    {c.url}")
            print(f"    category={g.get('category')}  "
                  f"license={g.get('license')}  "
                  f"trust={g.get('trust', {}).get('score')}"
                  f"({g.get('trust', {}).get('level')})  "
                  f"secure={g.get('security', {}).get('secure')}")
            unsafe = g.get("security", {}).get("unsafe") or []
            for u in unsafe[:3]:
                print(f"      ! {u}")
            print(f"    -> {rec['final']}")

    with out_path.open("a", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec) + "\n")

    kept = sum(1 for r in all_records
               if r.get("final") and "REJECT" not in r["final"]
               and r["final"] != "NO_FETCH")
    print(f"\nledger -> {out_path}  "
          f"({len(all_records)} rows, {kept} reached governance)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
