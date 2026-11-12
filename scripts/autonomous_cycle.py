#!/usr/bin/env python
"""Autonomous research cycle runner (M2 of
DOCS/AUTONOMOUS_FI_INFRASTRUCTURE.md).

One bounded, advisory pass per invocation:

  1. scout sweep   — optional internet_scout.py subprocess over the
                     day's rotating query (network, bounded timeout)
  2. spec harvest  — new scout ledger records -> extract_specs ->
                     MethodSpecs (allow-listed families only)
  3. gate eval     — each spec compiled + segmented all-LCB eval on
                     the configured datasets (in-process, no CSC)
  4. report        — var/reports/YYYYMMDD.md + var/autonomous_cycle/
                     cycle_*.jsonl — what ran, what stopped where,
                     honest "no edge found yet" lines

Zero authority by construction: this script can only propose and
record. Promotion stays behind signed RSI evaluator /
OperatorAuthorization. Run under .venv; scout subprocess needs
network.

Usage:
    python scripts/autonomous_cycle.py --once \
        --datasets 'market_data.db:EURUSD:M15;fx_data.db:USDJPY:D1' \
        --scout --query "order flow imbalance"
    python scripts/autonomous_cycle.py --interval-hours 24 \
        --max-cycles 7 --state-dir var/autonomous_cycle
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.edge_baseline import load_bars, roll_spread_bps  # noqa: E402
from scripts.method_candidate import segmented_verdict  # noqa: E402
from trading_bot.core.csc.research.method_spec import (  # noqa: E402
    PAIR_FAMILIES, SpecError, compile_rule)
from scripts.method_candidate import pair_eval  # noqa: E402
from trading_bot.core.csc.research.spec_extractor import (  # noqa: E402
    extract_specs)

# finance-disambiguated: bare terms like "momentum crash" pull
# crash-reconstruction papers, not trading methods
DEFAULT_QUERIES = [
    "order flow imbalance forex trading",
    "walk forward validation trading strategy",
    "volatility regime switching financial markets",
    "intraday mean reversion currency",
    "momentum crash equity trading",
    "pairs trading cointegration forex",
    "market microstructure limit order book",
    "event study macro announcement forex",
    "cross sectional momentum stocks",
    "foreign exchange predictability",
]


def parse_datasets(spec: str):
    out = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        db, sym, tf = part.split(":")
        out.append((db, sym, tf))
    return out


HERMES_PY = (Path.home() / "AppData" / "Local" / "hermes"
             / "hermes-agent" / "venv" / "Scripts" / "python.exe")


def _scout_python() -> str:
    """internet_scout needs sklearn (research.features.engine) which
    lives in the hermes env, not .venv. Prefer hermes when present."""
    if HERMES_PY.exists():
        return str(HERMES_PY)
    return sys.executable


def run_scout(query: str, sources: str, out_ledger: Path,
              timeout_s: int) -> dict:
    """Bounded scout subprocess; failure is recorded, never raised."""
    py = _scout_python()
    cmd = [py, str(ROOT / "scripts" / "internet_scout.py"),
           "--query", query, "--sources", sources,
           "--out", str(out_ledger)]
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                           text=True, timeout=timeout_s)
        return {"cmd": " ".join(cmd), "rc": r.returncode,
                "tail": (r.stdout or "")[-800:],
                "err": (r.stderr or "")[-400:]}
    except subprocess.TimeoutExpired:
        return {"cmd": " ".join(cmd), "rc": None,
                "error": f"timeout {timeout_s}s"}
    except Exception as e:
        return {"cmd": " ".join(cmd), "rc": None,
                "error": f"{type(e).__name__}: {e}"}


def harvest_specs(ledger_path: Path, since_offset: int,
                  max_specs: int):
    """New ledger lines -> extracted MethodSpecs. Records carry
    method_specs already when internet_scout ran the extractor;
    we re-derive from description for older rows and dedupe."""
    specs, seen = [], set()
    if not ledger_path.exists():
        return specs
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    for line in lines[since_offset:]:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        for s in rec.get("method_specs") or []:
            key = s.get("spec_hash") or s.get("spec_id")
            if key and key not in seen:
                seen.add(key)
                specs.append({"spec": s, "record": {
                    "name": rec.get("name"), "url": rec.get("url"),
                    "final": rec.get("final")}})
        # fallback: derive from description when the scout predates
        # the extractor wiring
        if not rec.get("method_specs") and rec.get("description"):
            for spec in extract_specs(
                    f"{rec.get('name','')}\n{rec['description']}",
                    provenance={"source": "scout_ledger_fallback",
                                "url": rec.get("url")}):
                key = spec.spec_hash
                if key not in seen:
                    seen.add(key)
                    specs.append({"spec": {
                        "spec_id": spec.spec_id, "family": spec.family,
                        "params": spec.params, "spec_hash": spec.spec_hash,
                        "hypothesis": spec.hypothesis[:200]},
                        "record": {"name": rec.get("name"),
                                   "url": rec.get("url"),
                                   "final": rec.get("final")}})
        if len(specs) >= max_specs:
            break
    return specs[:max_specs]


def eval_spec_on_datasets(spec_dict: dict, datasets, horizon: int,
                          cost_floor: float, segments: int,
                          margin: float) -> list:
    """Compile + segmented eval per dataset; honest per-dataset
    verdicts, no cross-dataset promotion."""
    from trading_bot.core.csc.research.method_spec import (
        MethodSpec, spec_from_dict)
    spec = spec_from_dict({**spec_dict,
                           "provenance": {**(spec_dict.get("provenance")
                                             or {}),
                                          "origin": "autonomous_cycle"}})
    try:
        rule_fn = compile_rule(spec)
    except SpecError as e:
        # PAIR specs harvested without a hedge-leg declaration land
        # here — record as needs_pair, not a hard rejection
        if spec.family in PAIR_FAMILIES and "spec.pair" in str(e):
            return [{"dataset": None, "status": "needs_pair",
                     "reason": str(e)}]
        return [{"dataset": None, "status": "spec_rejected",
                 "reason": str(e)}]
    out = []
    for db, sym, tf in datasets:
        try:
            if spec.family in PAIR_FAMILIES:
                v = pair_eval(spec, rule_fn, spec.pair, db, sym, tf,
                              horizon, cost_floor, segments, 0.40, 20,
                              margin)
                out.append({"dataset": f"{db}:{sym}:{tf}",
                            "bars": v.get("aligned_bars"),
                            "cost_bps": round(cost_floor, 2),
                            "verdict": v.get("verdict", v.get("status")),
                            "overall": v.get("overall"),
                            "segments": v.get("segments")})
                continue
            ts, bars = load_bars(db, sym, tf)
        except Exception as e:
            out.append({"dataset": f"{db}:{sym}:{tf}",
                        "status": "load_error",
                        "reason": f"{type(e).__name__}: {e}"})
            continue
        closes = bars[:, 3]
        if len(closes) < 200:
            out.append({"dataset": f"{db}:{sym}:{tf}",
                        "status": "insufficient_bars",
                        "bars": len(closes)})
            continue
        cost = max(roll_spread_bps(closes) or 0.0, cost_floor)
        v = segmented_verdict(closes, rule_fn, horizon, segments,
                              0.40, 20, cost, margin)
        out.append({"dataset": f"{db}:{sym}:{tf}", "bars": len(closes),
                    "cost_bps": round(cost, 2),
                    "verdict": v["verdict"],
                    "overall": v.get("overall"),
                    "segments": v["segments"]})
    return out


def write_report(state_dir: Path, day: str, cycle: dict) -> Path:
    rdir = state_dir / "reports"
    rdir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Autonomous cycle report — {day}",
        f"generated {cycle['ts']}  cycle#{cycle['cycle']}  "
        f"query={cycle.get('query')!r}",
        "",
        "## Scout",
        f"- ran: {cycle['scout'].get('ran', False)}  "
        f"rc={cycle['scout'].get('rc')}  "
        f"{cycle['scout'].get('error') or cycle['scout'].get('tail','')[:200]}",
        "",
        "## Specs evaluated",
    ]
    if not cycle["evals"]:
        lines.append("- none — no method specs harvested this cycle")
    for e in cycle["evals"]:
        lines.append(f"- `{e['spec_id']}` ({e['family']} {e['params']}) "
                     f"from {e.get('record_name','?')}")
        for d in e["datasets"]:
            if "verdict" in d:
                ov = d.get("overall") or {}
                lines.append(
                    f"    - {d['dataset']}: **{d['verdict']}** "
                    f"mean={ov.get('mean_net_bps')}bps "
                    f"lcb5={ov.get('lcb5_net_bps')}bps "
                    f"trades={ov.get('trades')}")
            else:
                lines.append(f"    - {d.get('dataset')}: {d.get('status')}"
                             f" {d.get('reason','')}")
        if e.get("replication"):
            rep = e["replication"]
            if rep.get("status") == "skipped":
                lines.append(f"    - replication: skipped ({rep['reason']})")
            else:
                rc = [d for d in rep["datasets"]
                      if d.get("verdict") == "candidate"]
                lines.append(
                    f"    - replication@{rep['level']}: "
                    f"{'SURVIVED' if rc else 'FAILED'} "
                    f"({len(rc)}/{len(rep['datasets'])} datasets)")
                for d in rep["datasets"]:
                    ov = d.get("overall") or {}
                    lines.append(
                        f"        - {d.get('dataset')}: "
                        f"{d.get('verdict', d.get('status'))} "
                        f"mean={ov.get('mean_net_bps')}")
    cands = [e for e in cycle["evals"]
             for d in e["datasets"] if d.get("verdict") == "candidate"]
    lines += ["", "## Verdict",
              f"- candidates: {len(cands)}",
              "- promotion_eligible: false for everything above — "
              "operator signature required",
              "- honest line: " + (
                  "edge candidates exist — see segments"
                  if cands else
                  "no edge found yet this cycle")]
    path = rdir / f"{day}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true",
                    help="single cycle then exit (default when "
                         "--interval-hours unset)")
    ap.add_argument("--interval-hours", type=float, default=None)
    ap.add_argument("--max-cycles", type=int, default=1)
    ap.add_argument("--state-dir", default="var/autonomous_cycle")
    ap.add_argument("--query", default=None,
                    help="override today's rotating query")
    ap.add_argument("--queries-file", default=None,
                    help="JSON list of queries; rotates by day")
    ap.add_argument("--sources", default="github,arxiv")
    ap.add_argument("--scout", action="store_true",
                    help="run internet_scout.py this cycle")
    ap.add_argument("--scout-ledger", default="var/ecie/scout_ledger.jsonl")
    ap.add_argument("--scout-timeout", type=int, default=600)
    ap.add_argument("--datasets",
                    default="market_data.db:EURUSD:M15",
                    help="; separated db:symbol:timeframe")
    ap.add_argument("--replication-datasets", default="",
                    help="; separated db:symbol:timeframe evaluated ONLY "
                         "for specs that produced a candidate verdict — "
                         "the DIFFERENT_DATASET replication rung. Empty "
                         "= replication skipped honestly")
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--cost-floor-bps", type=float, default=5.0)
    ap.add_argument("--margin-bps", type=float, default=0.0)
    ap.add_argument("--max-specs", type=int, default=8)
    args = ap.parse_args()

    state = Path(args.state_dir)
    state.mkdir(parents=True, exist_ok=True)
    datasets = parse_datasets(args.datasets)
    repl_datasets = parse_datasets(args.replication_datasets) \
        if args.replication_datasets else []
    queries = DEFAULT_QUERIES
    if args.queries_file:
        try:
            queries = json.loads(
                Path(args.queries_file).read_text())
        except Exception as e:
            print(f"queries-file unreadable: {e} — using defaults")

    cycles_done = 0
    while cycles_done < args.max_cycles:
        now = datetime.now(timezone.utc)
        day = now.strftime("%Y%m%d")
        cycle_no = cycles_done + 1
        query = args.query or queries[
            (now.timetuple().tm_yday + cycles_done) % len(queries)]

        ledger_path = Path(args.scout_ledger)
        offset_before = (len(ledger_path.read_text(
            encoding="utf-8").splitlines())
            if ledger_path.exists() else 0)

        scout = {"ran": False}
        if args.scout:
            scout = run_scout(query, args.sources, ledger_path,
                              args.scout_timeout)
            scout["ran"] = True

        harvested = harvest_specs(ledger_path, offset_before,
                                  args.max_specs)
        evals = []
        for h in harvested:
            sd = h["spec"]
            results = eval_spec_on_datasets(
                sd, datasets, args.horizon, args.cost_floor_bps,
                args.segments, args.margin_bps)
            evals.append({"spec_id": sd.get("spec_id"),
                          "family": sd.get("family"),
                          "params": sd.get("params"),
                          "hypothesis": sd.get("hypothesis", ""),
                          "spec": sd,
                          "record_name": h["record"].get("name"),
                          "datasets": results})

        # M1c replication rung: any spec with a candidate verdict is
        # re-judged on DIFFERENT datasets before the report calls it a
        # candidate. A candidate that dies on replication is marked
        # candidate_unreplicated — it never reaches the report's
        # candidate count.
        for e in evals:
            if not any(d.get("verdict") == "candidate"
                       for d in e["datasets"]):
                continue
            if not repl_datasets:
                e["replication"] = {"status": "skipped",
                                    "reason": "no replication datasets "
                                              "configured"}
                continue
            e["replication"] = {
                "level": "DIFFERENT_DATASET",
                "datasets": eval_spec_on_datasets(
                    e["spec"], repl_datasets, args.horizon,
                    args.cost_floor_bps, args.segments, args.margin_bps)}
            # downgrade: candidate only survives if replication also
            # produced a candidate on at least one replication dataset
            repl_cands = [d for d in e["replication"]["datasets"]
                          if d.get("verdict") == "candidate"]
            e["replicated"] = bool(repl_cands)
            if not repl_cands:
                for d in e["datasets"]:
                    if d.get("verdict") == "candidate":
                        d["verdict"] = "candidate_unreplicated"

        cycle = {"ts": now.isoformat(), "cycle": cycle_no,
                 "query": query, "scout": scout, "evals": evals}
        cdir = state / "cycles"
        cdir.mkdir(exist_ok=True)
        (cdir / f"{day}_{cycle_no}.json").write_text(
            json.dumps(cycle, indent=2, default=str))
        report = write_report(state, day, cycle)
        n_cand = sum(1 for e in evals for d in e["datasets"]
                     if d.get("verdict") == "candidate")
        print(f"cycle {cycle_no}: query={query!r} scout_rc="
              f"{scout.get('rc')} specs={len(evals)} candidates={n_cand}")
        print(f"report -> {report}")

        # Analyst stage: re-judge ALL accumulated hunter artifacts
        # (this cycle + history + method_candidates) into the
        # classification queue. Advisory; failure must not kill the
        # loop.
        try:
            import subprocess
            ar = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "analyst_review.py")],
                cwd=str(ROOT), capture_output=True, text=True, timeout=120)
            if ar.returncode == 0:
                print("analyst -> var/analyst_queue.json")
            else:
                print(f"analyst rc={ar.returncode}: "
                      f"{(ar.stderr or '')[-200:]}")
        except Exception as exc:  # noqa: BLE001
            print(f"analyst skipped: {exc}")
        cycles_done += 1

        if args.interval_hours is None or args.once:
            break
        time.sleep(args.interval_hours * 3600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
