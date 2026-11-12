#!/usr/bin/env python
"""Operator intel surface (M4 of DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md).

One status view merging the L2 audit outputs that today live as
separate tools: scout ledgers (ECIE gate outcomes), autonomous-cycle
daily reports, method-candidate verdicts, and the data catalog.
Read-only; prints to stdout and refreshes var/intel_report.md.

Usage: python scripts/intel_report.py [--state var/autonomous_cycle]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tail_jsonl(path: Path, n: int):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8",
                           errors="replace").splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="var/autonomous_cycle")
    ap.add_argument("--ledger-glob", default="var/ecie/scout_ledger*.jsonl")
    ap.add_argument("--cand-dir", default="var/method_candidates")
    ap.add_argument("--catalog", default="var/data_catalog.json")
    args = ap.parse_args()

    lines = [f"# Intel report — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z",
             ""]

    # --- scout ledgers ---
    ledgers = sorted(ROOT.glob(args.ledger_glob))
    lines.append("## Scout ledgers")
    if not ledgers:
        lines.append("- none found")
    for lp in ledgers:
        recs = tail_jsonl(lp, 200)
        finals = {}
        specs = 0
        for r in recs:
            f = r.get("final", "?")
            finals[f] = finals.get(f, 0) + 1
            specs += len(r.get("method_specs") or [])
        lines.append(f"- `{lp}`: {len(recs)} recent rows, "
                     f"{specs} method_specs, finals={finals}")
    lines.append("")

    # --- cycle reports ---
    rep_dir = ROOT / args.state / "reports"
    lines.append("## Autonomous cycles")
    reps = sorted(rep_dir.glob("*.md")) if rep_dir.exists() else []
    if not reps:
        lines.append("- no reports yet")
    for rp in reps[-3:]:
        txt = rp.read_text(encoding="utf-8", errors="replace")
        cand = [l for l in txt.splitlines() if "candidates:" in l]
        lines.append(f"- `{rp.name}`: "
                     f"{cand[-1].strip() if cand else '?'}")
    cyc_dir = ROOT / args.state / "cycles"
    n_cycles = len(list(cyc_dir.glob("*.json"))) if cyc_dir.exists() else 0
    lines.append(f"- cycle artifacts: {n_cycles}")
    lines.append("")

    # --- method candidates ---
    cand_dir = ROOT / args.cand_dir
    lines.append("## Method candidates")
    cands = sorted(cand_dir.glob("*.json")) if cand_dir.exists() else []
    if not cands:
        lines.append("- none evaluated yet")
    for cp in cands[-10:]:
        try:
            r = json.loads(cp.read_text())
            v = r.get("verdict", {})
            ov = v.get("overall") or {}
            lines.append(
                f"- `{r.get('spec', {}).get('spec_id')}` "
                f"[{r.get('spec', {}).get('family')}] "
                f"{v.get('verdict')} mean={ov.get('mean_net_bps')} "
                f"lcb5={ov.get('lcb5_net_bps')} "
                f"on {r.get('dataset', {}).get('symbol')}/"
                f"{r.get('dataset', {}).get('timeframe')}")
        except Exception:
            lines.append(f"- `{cp.name}`: unreadable")
    lines.append("")

    # --- claims funnel: text -> spec -> eval -> verdict -> class ---
    lines.append("## Claims funnel")
    n_recs = n_specs = 0
    for lp in ledgers:
        for r in tail_jsonl(lp, 500):
            n_recs += 1
            n_specs += len(r.get("method_specs") or [])
    lines.append(f"- scout records: {n_recs} -> method_specs: {n_specs}")
    n_evals = n_cand = 0
    vdist = {}
    if cyc_dir.is_dir():
        for cf in cyc_dir.glob("*.json"):
            try:
                cyc = json.loads(cf.read_text())
            except Exception:
                continue
            for e in cyc.get("evals", []):
                n_evals += 1
                for d in e.get("datasets", []):
                    v = d.get("verdict") or d.get("status") or "?"
                    vdist[v] = vdist.get(v, 0) + 1
                    if v == "candidate":
                        n_cand += 1
    lines.append(f"- evals: {n_evals} -> dataset verdicts: {vdist}")
    lines.append(f"- candidate verdicts: {n_cand} "
                 "(pre-replication; unreplicated marked separately)")
    lines.append("")

    # --- analyst queue ---
    aq_path = ROOT / "var" / "analyst_queue.json"
    lines.append("## Analyst queue")
    if aq_path.exists():
        try:
            aq = json.loads(aq_path.read_text())
            counts = aq.get("counts", {})
            lines.append(f"- generated {aq.get('generated')}: "
                         + ", ".join(f"{k}={v}" for k, v in
                                     sorted(counts.items())))
            for al in (aq.get("alerts") or [])[:8]:
                lines.append(f"- ALERT: {al}")
            live = [s for s in aq.get("specs", [])
                    if s.get("classification") != "DEAD"]
            if not live:
                lines.append("- no live signals (all DEAD)")
            for s in live[:10]:
                lines.append(
                    f"- **{s.get('classification')}** "
                    f"`{s.get('spec_id')}` ({s.get('family')}): "
                    f"{'; '.join(s.get('reasons') or ['-'])[:140]}")
        except Exception:
            lines.append("- unreadable")
    else:
        lines.append("- not built — run scripts/analyst_review.py")
    lines.append("")

    # --- data/spec requests ---
    dr_path = ROOT / "var" / "data_requests.json"
    lines.append("## Data/spec requests")
    if dr_path.exists():
        try:
            dr = json.loads(dr_path.read_text())
            reqs = dr.get("requests", {})
            kinds = {}
            for r in reqs.values():
                kinds[r.get("kind")] = kinds.get(r.get("kind"), 0) + 1
            lines.append(f"- {len(reqs)} open requests ({kinds})")
            for r in sorted(reqs.values(),
                            key=lambda x: -x.get("count", 0))[:8]:
                lines.append(
                    f"- [{r.get('kind')}] `{r.get('spec_id')}` needs "
                    f"{r.get('need')} (x{r.get('count')})")
        except Exception:
            lines.append("- unreadable")
    else:
        lines.append("- none filed yet")
    lines.append("")

    # --- data catalog ---
    cat_path = ROOT / args.catalog
    lines.append("## Data catalog")
    if cat_path.exists():
        cat = json.loads(cat_path.read_text())
        lines.append(f"- generated {cat.get('generated_at')}")
        for d in cat.get("dbs", []):
            n = len(d.get("series", []))
            rows = sum(s.get("rows", 0) for s in d.get("series", []))
            err = d.get("error") or d.get("note")
            tag = f" [{err}]" if err else ""
            lines.append(f"- `{d['path']}`: {n} series, {rows:,} rows{tag}")
    else:
        lines.append("- not built — run scripts/data_catalog.py")
    lines.append("")
    lines.append("promotion_eligible: false everywhere — "
                 "operator signature required for any deployment")

    out = "\n".join(lines)
    print(out)
    (ROOT / "var" / "intel_report.md").write_text(out + "\n",
                                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
