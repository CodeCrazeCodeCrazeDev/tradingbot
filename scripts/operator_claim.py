#!/usr/bin/env python
"""Operator-directed claims: vetted text -> spec -> gate -> record.

The scout trust gate rejects ~100% of web sources by design — correct
for untrusted input. But the OPERATOR is the trust root: a claim the
operator submits directly has already passed the trust decision a
human would make. This script runs the same extract->compile->
gate path on operator-supplied text and writes standard
method_candidates records the analyst consumes — no trust gate,
because trust was established by the submitter, not the web.

Honest limits: extraction is the same mechanical mapper (anchored
finance text only); claims outside the family space return [] and
are reported, never forced. Advisory only — records feed the
analyst queue; promotion still needs signed authorization.

Usage:
    python scripts/operator_claim.py --text "10-period momentum on
        forex: go long when price rises >15bps over 10 bars..."
    python scripts/operator_claim.py --file claim.txt \
        --datasets 'market_data.db:EURUSD:M15;fx_data.db:GBPUSD:D1'
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from autonomous_cycle import (  # noqa: E402
    eval_spec_on_datasets, parse_datasets)
from trading_bot.core.csc.research.spec_extractor import (  # noqa: E402
    extract_specs)


def _record_for(spec_dict, dspec, ds_result):
    """Shape one dataset eval into the method_candidates contract
    analyst_review.collect() consumes."""
    db, sym, tf = dspec
    verdict = ds_result.get("verdict")
    if verdict not in ("candidate", "rejected"):
        return None  # needs_pair / load_error / insufficient — not a verdict
    return {
        "spec": spec_dict,
        "dataset": {"db": db, "symbol": sym, "timeframe": tf},
        "gate": {"verdict": verdict},
        "verdict": {
            "dataset": ds_result.get("dataset"),
            "eval_window": None,
            "cost_bps": ds_result.get("cost_bps"),
            "verdict": verdict,
            "overall": ds_result.get("overall"),
            "segments": ds_result.get("segments"),
            "meta": {"origin": "operator_claim"},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None, help="claim text inline")
    ap.add_argument("--file", default=None, help="path to claim text")
    ap.add_argument("--datasets",
                    default="market_data.db:EURUSD:M15",
                    help="; separated db:symbol:timeframe")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--cost-floor-bps", type=float, default=5.0)
    ap.add_argument("--margin-bps", type=float, default=0.0)
    ap.add_argument("--out-dir", default="var/method_candidates")
    args = ap.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8",
                                         errors="replace")
    elif args.text:
        text = args.text
    else:
        ap.error("--text or --file required")

    raw_specs = extract_specs(text)
    if not raw_specs:
        print("no specs extracted — claim lacks a finance anchor or "
              "maps to no allow-listed family (honest empty)")
        return 0
    import dataclasses
    specs = [dataclasses.asdict(s) if dataclasses.is_dataclass(s)
             else dict(s) for s in raw_specs]
    print(f"extracted {len(specs)} spec(s) "
          f"({[s.get('family') for s in specs]})")

    datasets = parse_datasets(args.datasets)
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for sd in specs:
        sid = sd.get("spec_id") or "operator_claim"
        results = eval_spec_on_datasets(
            sd, datasets, args.horizon, args.cost_floor_bps,
            args.segments, args.margin_bps)
        for dspec, dres in zip(datasets, results):
            rec = _record_for(sd, dspec, dres)
            if rec is None:
                print(f"  {sid} on {dres.get('dataset')}: "
                      f"{dres.get('status') or dres.get('verdict')} "
                      "— no verdict written")
                continue
            h = hashlib.sha256(
                json.dumps(sd, sort_keys=True,
                           default=str).encode()).hexdigest()[:8]
            out = out_dir / f"{sid}__{dspec[1]}_{dspec[2]}_{h}.json"
            out.write_text(json.dumps(rec, indent=2, default=str))
            wrote += 1
            ov = (rec["verdict"].get("overall") or {})
            print(f"  {sid} [{sd.get('family')}] on "
                  f"{dspec[1]}/{dspec[2]}: {rec['verdict']['verdict']} "
                  f"mean={ov.get('mean_net_bps')} "
                  f"lcb={ov.get('lcb5_net_bps')} -> {out.name}")
    print(f"wrote {wrote} candidate record(s) -> {args.out_dir}")
    print("next: scripts/analyst_review.py classifies them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
