#!/usr/bin/env python
"""Analyst stage — the judgment layer the hunter lacks.

Scans accumulated hunter artifacts (autonomous_cycle cycles +
method_candidate verdicts), aggregates per spec_id, and applies the
checks previously done by hand: cross-dataset breadth, segment
stability/decay, cost headroom, near-miss classification.

Emits var/analyst_queue.json (machine) + var/analyst_report.md
(operator). Advisory only — classification, never promotion.

Usage: python scripts/analyst_review.py \
    [--cycles var/autonomous_cycle/cycles] \
    [--candidates var/method_candidates] \
    [--out-queue var/analyst_queue.json] \
    [--out-report var/analyst_report.md]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

MIN_HEADROOM_BPS = 1.0   # cost headroom below this = fragile
DECAY_BPS = 3.0          # last-vs-first segment drop flagged as decay


def _seg_stats(ds):
    segs = [s for s in ds.get("segments", []) if s.get("status") == "evaluated"]
    means = [s.get("mean_net_bps") for s in segs]
    lcbs = [s.get("lcb5_net_bps") for s in segs]
    return means, lcbs


def _dataset_record(ds):
    """Normalize a per-dataset verdict dict into analyst fields."""
    overall = ds.get("overall") or {}
    mean = overall.get("mean_net_bps")
    lcb = overall.get("lcb5_net_bps")
    trades = overall.get("trades", 0)
    seg_means, seg_lcbs = _seg_stats(ds)
    decay = None
    if len(seg_means) >= 2 and all(m is not None for m in seg_means):
        decay = round(seg_means[-1] - seg_means[0], 3)
    near_miss = (mean is not None and mean > 0 and lcb is not None
                 and lcb > 0 and ds.get("verdict") != "candidate")
    return {
        "dataset": ds.get("dataset"),
        "verdict": ds.get("verdict"),
        "trades": trades,
        "mean_net_bps": mean,
        "lcb5_net_bps": lcb,
        "seg_means": seg_means,
        "seg_lcbs": seg_lcbs,
        "decay_bps": decay,
        "near_miss": near_miss,
    }


def _aggregate(spec_id, family, hypothesis, records, replicated,
               spec_dict=None):
    tested = len(records)
    cands = [r for r in records if r["verdict"] == "candidate"]
    unrep = [r for r in records if r["verdict"] == "candidate_unreplicated"]
    pos = [r for r in records
           if r["mean_net_bps"] is not None and r["mean_net_bps"] > 0]
    means = [r["mean_net_bps"] for r in records
             if r["mean_net_bps"] is not None]
    headroom = min(means) if means else None
    decaying = [r for r in records
                if r["decay_bps"] is not None and r["decay_bps"] < -DECAY_BPS]
    near = [r for r in records if r["near_miss"]]

    if cands and replicated is True and headroom is not None \
            and headroom > MIN_HEADROOM_BPS:
        klass = "PROMOTE_CANDIDATE"
    elif near or unrep or (pos and len(pos) < tested):
        klass = "WATCH"
    elif not pos:
        klass = "DEAD"
    else:
        klass = "WATCH"

    reasons = []
    if near:
        reasons.append("near-miss: positive mean+LCB but segments failed "
                       f"on {[r['dataset'] for r in near]}")
    if unrep:
        reasons.append("died on replication datasets")
    if decaying:
        reasons.append("decaying: last segment mean "
                       f"{min(r['decay_bps'] for r in decaying):+.1f}bps vs "
                       "first on "
                       f"{[r['dataset'] for r in decaying]}")
    if headroom is not None and headroom <= MIN_HEADROOM_BPS and pos:
        reasons.append(f"fragile: min cost headroom {headroom:+.2f}bps")

    return {
        "spec_id": spec_id,
        "family": family,
        "hypothesis": (hypothesis or "")[:160],
        "spec": spec_dict,
        "params": (spec_dict or {}).get("params"),
        "classification": klass,
        "datasets_tested": tested,
        "datasets_positive": len(pos),
        "candidate_verdicts": len(cands),
        "unreplicated": len(unrep),
        "replicated": replicated,
        "cost_headroom_bps": (round(headroom, 3)
                              if headroom is not None else None),
        "decaying_datasets": [r["dataset"] for r in decaying],
        "near_miss_datasets": [r["dataset"] for r in near],
        "datasets": records,
        "reasons": reasons,
    }


def collect(cycles_dir: Path, cand_dir: Path):
    """spec_id -> {family, hypothesis, replicated, records[]}"""
    specs = defaultdict(lambda: {"family": None, "hypothesis": "",
                                 "replicated": None, "records": {},
                                 "spec_dict": None})
    if cycles_dir.is_dir():
        for f in sorted(cycles_dir.glob("*.json")):
            try:
                cyc = json.loads(f.read_text())
            except Exception:
                continue
            for e in cyc.get("evals", []):
                sid = e.get("spec_id") or (e.get("spec") or {}).get("spec_id")
                if not sid:
                    continue
                s = specs[sid]
                s["family"] = s["family"] or e.get("family")
                s["hypothesis"] = s["hypothesis"] or e.get("hypothesis", "")
                if e.get("replicated") is not None:
                    s["replicated"] = bool(e["replicated"])
                if s["spec_dict"] is None:
                    s["spec_dict"] = e.get("spec")
                for ds in e.get("datasets", []):
                    key = ds.get("dataset") or "?"
                    cb = ds.get("cost_bps")
                    if cb is not None:
                        key = f"{key}@{cb}"
                    s["records"][key] = _dataset_record(ds)
                for ds in (e.get("replication") or {}).get("datasets", []):
                    key = "REPL:" + (ds.get("dataset") or "?")
                    cb = ds.get("cost_bps")
                    if cb is not None:
                        key = f"{key}@{cb}"
                    s["records"][key] = _dataset_record(ds)
    if cand_dir.is_dir():
        for f in sorted(cand_dir.glob("*.json")):
            try:
                m = json.loads(f.read_text())
            except Exception:
                continue
            spec = m.get("spec") or {}
            sid = spec.get("spec_id") or f.stem
            s = specs[sid]
            s["family"] = s["family"] or spec.get("family")
            s["hypothesis"] = s["hypothesis"] or spec.get("hypothesis", "")
            if s["spec_dict"] is None:
                s["spec_dict"] = spec
            ds = dict(m.get("verdict") or {})
            ds["dataset"] = m.get("dataset")
            ds["verdict"] = (m.get("gate") or {}).get("verdict") \
                or ds.get("verdict")
            s["records"][str(m.get("dataset"))] = _dataset_record(ds)
    return specs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", default="var/autonomous_cycle/cycles")
    ap.add_argument("--candidates", default="var/method_candidates")
    ap.add_argument("--out-queue", default="var/analyst_queue.json")
    ap.add_argument("--out-report", default="var/analyst_report.md")
    args = ap.parse_args()

    specs = collect(Path(args.cycles), Path(args.candidates))
    agg = [_aggregate(sid, s["family"], s["hypothesis"],
                      list(s["records"].values()), s["replicated"],
                      s.get("spec_dict"))
           for sid, s in specs.items()]
    order = {"PROMOTE_CANDIDATE": 0, "WATCH": 1, "DEAD": 2}
    agg.sort(key=lambda a: (order.get(a["classification"], 3),
                            -(a["cost_headroom_bps"] or -999)))
    counts = defaultdict(int)
    for a in agg:
        counts[a["classification"]] += 1

    queue = {"generated": __import__("datetime").datetime.now()
             .isoformat(timespec="seconds"),
             "counts": dict(counts), "specs": agg}
    Path(args.out_queue).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_queue).write_text(json.dumps(queue, indent=2,
                                             default=str))

    lines = ["# Analyst review",
             f"generated: {queue['generated']}",
             f"specs tracked: {len(agg)}  "
             + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())),
             ""]
    for a in agg:
        if a["classification"] == "DEAD" and not a["near_miss_datasets"]:
            continue  # keep the report focused on live signals
        lines.append(f"## {a['classification']} — {a['spec_id']} "
                     f"({a['family']})")
        lines.append(f"- hypothesis: {a['hypothesis'][:120]}")
        lines.append(f"- datasets: {a['datasets_positive']}/"
                     f"{a['datasets_tested']} positive, "
                     f"{a['candidate_verdicts']} candidate, "
                     f"{a['unreplicated']} unreplicated, "
                     f"replicated={a['replicated']}")
        lines.append(f"- cost headroom: {a['cost_headroom_bps']}bps")
        for r in a["reasons"]:
            lines.append(f"- {r}")
        lines.append("")
    Path(args.out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_report).write_text("\n".join(lines), encoding="utf-8")

    print(f"analyst: {len(agg)} specs — "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"queue -> {args.out_queue}")
    print(f"report -> {args.out_report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
