"""Reassess archived RSI candidates on the most recent data window.

Algory's REASSESS analog: strategies that earned
``eligible_for_operator_review`` are re-simulated on the tail of the
evaluation frames — data that arrived *after* their promotion evidence —
and classified:

    HOLDING    recent per-bar edge is consistent with the archived edge
    DECAYED    recent edge collapsed (ratio below --decay-ratio, or the
               candidate is net-negative on a sufficient sample)
    TOO_EARLY  fewer than --min-bars recent observations — no verdict
    NO_VERDICT replay failed or the record lacks candidate parameters

This is diagnostic only: it never promotes, demotes, or deploys anything.
Results append to ``<work-dir>/reassess.jsonl`` for audit.

    python scripts/rsi_reassess.py --work-dir var/rsi_sleep \
        --db market_data.db --instruments EURUSD
    python scripts/rsi_reassess.py --work-dir var/rsi_sleep --recent-bars 40
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.evaluation.synthetic_market import (  # noqa: E402
    RegimeSpec, SqliteSource, SyntheticMarketGenerator, SyntheticMarketSpec)
from trading_bot.recursive_self_improvement.archive import ParetoArchive  # noqa: E402
from trading_bot.recursive_self_improvement.candidate_adapters import (  # noqa: E402
    ADAPTERS)
from trading_bot.recursive_self_improvement.robustness_gates import (  # noqa: E402
    candidate_series, net_return_of)


def _frames(args) -> Dict[str, Any]:
    if args.db:
        return SqliteSource(args.db, args.instruments).load()
    spec = SyntheticMarketSpec(
        seed=args.seed, instruments=tuple(args.instruments),
        regimes=(RegimeSpec("mean_revert", args.bars, vol=0.0002,
                            sine_amp=0.01, sine_period=8),))
    return SyntheticMarketGenerator(spec).generate()


def _recent_series(out: Mapping[str, Any], n: int):
    """Last ``n`` cross-sectional mean candidate nets from a replay."""
    timeline, series = candidate_series({"bars": out.get("bars") or []})
    return series[-n:] if n > 0 else series


def _edge_series(out: Mapping[str, Any]) -> List[float]:
    """Per-timestamp cross-sectional mean of (candidate_net - baseline_net).

    This is the *relative* edge series — what actually decays when a
    strategy's edge erodes, independent of market drift.
    """
    grouped: Dict[str, Dict[Any, Tuple[float, float]]] = {}
    for row in out.get("bars") or []:
        if not isinstance(row, dict):
            continue
        sym, ts = row.get("symbol"), row.get("timestamp")
        cn, bn = row.get("candidate_net"), row.get("baseline_net")
        if (isinstance(sym, str) and isinstance(ts, (int, float))
                and isinstance(cn, (int, float)) and isinstance(bn, (int, float))):
            grouped.setdefault(sym, {})[ts] = (float(cn), float(bn))
    if not grouped:
        return []
    timeline = sorted(next(iter(grouped.values())))
    series = []
    for t in timeline:
        diffs = [grouped[s][t][0] - grouped[s][t][1]
                 for s in grouped if t in grouped[s]]
        if diffs:
            series.append(sum(diffs) / len(diffs))
    return series


def reassess_record(rec: Mapping[str, Any], frames: Mapping[str, Any],
                    *, recent_bars: int, cost_bps: float,
                    decay_ratio: float, min_bars: int) -> Dict[str, Any]:
    """Replay one archived candidate on the recent window and classify."""
    from trading_bot.evaluation.runner import PairedFamilyReplay

    extra = rec.get("extra") or {}
    params = extra.get("candidate_parameters") or {}
    family = rec.get("strategy_family")
    base = {"genome_id": rec.get("genome_id"),
            "role": rec.get("role"),
            "strategy_family": family,
            "verdict_archived": rec.get("verdict")}
    if not params or family not in ADAPTERS:
        return {**base, "verdict": "NO_VERDICT",
                "reason": "missing candidate_parameters or unknown family"}
    adapter = ADAPTERS[family]
    incumbent = extra.get("incumbent_params")
    try:
        runner = PairedFamilyReplay(adapter, cost_bps=cost_bps,
                                    fraction=0.01)
        if incumbent:
            # True candidate-vs-baseline edge: replay the archived
            # incumbent against the archived candidate on recent data.
            out = runner.run(dict(frames), baseline_params=dict(incumbent),
                             candidate_params=dict(params))
            mode = "relative"
        else:
            # Legacy records predate incumbent_params storage: replay the
            # candidate against itself and fall back to absolute decay.
            out = runner.run(dict(frames), baseline_params=dict(params),
                             candidate_params=dict(params))
            mode = "absolute"
    except Exception as exc:  # noqa: BLE001 - per-record isolation
        return {**base, "verdict": "NO_VERDICT", "reason": str(exc)}

    if mode == "relative":
        edge = _edge_series(out)
        recent = edge[-recent_bars:] if recent_bars > 0 else edge
        n = len(recent)
        if n < min_bars:
            return {**base, "verdict": "TOO_EARLY", "mode": mode,
                    "reason": f"only {n} recent bars (< {min_bars})",
                    "n_recent": n}
        recent_edge_mean = sum(recent) / n
        recent_net = net_return_of(recent)
        mv = rec.get("metric_vector") or {}
        arch_edge = mv.get("paired_mean_diff")
        ratio = (recent_edge_mean / arch_edge
                 if isinstance(arch_edge, (int, float)) and arch_edge else None)
        result = {**base, "verdict": "HOLDING", "mode": mode,
                  "n_recent": n, "recent_edge_mean": recent_edge_mean,
                  "recent_net_return": recent_net,
                  "archived_edge_mean": arch_edge, "decay_ratio": ratio}
        if recent_edge_mean <= 0 or (ratio is not None and ratio < decay_ratio):
            result["verdict"] = "DECAYED"
            result["reason"] = (
                "recent edge non-positive"
                if recent_edge_mean <= 0 else
                f"edge ratio {ratio:.2f} < {decay_ratio}")
        return result

    recent = _recent_series(out, recent_bars)
    n = len(recent)
    if n < min_bars:
        return {**base, "verdict": "TOO_EARLY", "mode": mode,
                "reason": f"only {n} recent bars (< {min_bars})",
                "n_recent": n}
    recent_net = net_return_of(recent)
    recent_mean = sum(recent) / n

    mv = rec.get("metric_vector") or {}
    arch_net = mv.get("candidate_net_return")
    arch_bars = mv.get("candidate_n_bars") or mv.get("n_bars")
    arch_mean = (arch_net / arch_bars
                 if isinstance(arch_net, (int, float))
                 and isinstance(arch_bars, (int, float)) and arch_bars
                 else None)
    ratio = (recent_mean / arch_mean
             if arch_mean not in (None, 0) else None)

    result = {**base, "verdict": "HOLDING", "mode": mode,
              "n_recent": n, "recent_net_return": recent_net,
              "recent_mean_net": recent_mean,
              "archived_mean_net": arch_mean, "decay_ratio": ratio}
    if recent_mean <= 0 or (ratio is not None and ratio < decay_ratio):
        result["verdict"] = "DECAYED"
        result["reason"] = (
            "recent per-bar edge non-positive"
            if recent_mean <= 0 else
            f"edge ratio {ratio:.2f} < {decay_ratio}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", default="var/rsi_sleep",
                    help="archive/memory state directory holding archive.jsonl")
    ap.add_argument("--db", default=None, help="market_data.db for frames")
    ap.add_argument("--instruments", nargs="+", default=["EURUSD", "GBPUSD"])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--bars", type=int, default=160)
    ap.add_argument("--recent-bars", type=int, default=40,
                    help="tail window treated as post-training data")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    ap.add_argument("--decay-ratio", type=float, default=0.3,
                    help="recent/archived per-bar edge ratio below which a "
                         "candidate is DECAYED")
    ap.add_argument("--min-bars", type=int, default=20,
                    help="minimum recent observations for a verdict")
    ap.add_argument("--all-records", action="store_true",
                    help="reassess every record, not just live members")
    ap.add_argument("--interval", type=float, default=0.0,
                    help="seconds between reassessment sweeps (0 = once)")
    args = ap.parse_args()

    work = Path(args.work_dir)
    archive_path = work / "archive.jsonl"
    if not archive_path.exists():
        print(f"no archive at {archive_path}", file=sys.stderr)
        return 2
    archive = ParetoArchive(archive_path)
    frames = _frames(args)

    while True:
        if args.all_records:
            records = [r for r in archive.records if r.get("kind") == "record"]
        else:
            live = archive.live_members()
            records = [r for r in live
                       if r.get("verdict") == "eligible_for_operator_review"]
        results = [reassess_record(
            r, frames, recent_bars=args.recent_bars,
            cost_bps=args.cost_bps, decay_ratio=args.decay_ratio,
            min_bars=args.min_bars) for r in records]

        out_path = work / "reassess.jsonl"
        ts = time.time()
        with out_path.open("a", encoding="utf-8") as fh:
            for res in results:
                fh.write(json.dumps({"ts": ts, **res}, default=str) + "\n")
        summary = {v: sum(1 for r in results if r["verdict"] == v)
                   for v in ("HOLDING", "DECAYED", "TOO_EARLY", "NO_VERDICT")}
        print(json.dumps({"reassessed": len(results), "summary": summary,
                          "results": results}, indent=2, default=str))
        if args.interval <= 0:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
