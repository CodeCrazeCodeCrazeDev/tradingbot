"""Run one RSI "sleep phase": consolidate + dream + gated cycle.

Adapted from the Sleep paradigm (arXiv:2606.03979) — offline memory
consolidation and synthetic-scenario rehearsal, run while the trading
runtime is quiescent:

    # Standalone against synthetic frames (runner already stopped):
    python scripts/rsi_sleep_cycle.py --work-dir var/rsi_sleep

    # Against a live paper runner: wires pause/resume through the
    # operator ControlChannel and refuses to start while trading is
    # awake but unpausable.
    python scripts/rsi_sleep_cycle.py --work-dir var/rsi_sleep \
        --state-dir var/paper_run

    # Real-data evaluation frames, synthetic dreams:
    python scripts/rsi_sleep_cycle.py --db market_data.db --instruments EURUSD

Dream output is diagnostic only: synthetic rehearsal evidence cannot
promote anything — deployment stages still require a signed
OperatorAuthorization. Exit code is nonzero if the evidence ledger
fails verification or the runtime could not be quiesced.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.evaluation.synthetic_market import (
    RegimeSpec, SqliteSource, SyntheticMarketGenerator, SyntheticMarketSpec,
    fingerprint_all)
from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.candidate_adapters import (
    ADAPTERS, candidate_code_hash, dependencies_hash)
from trading_bot.recursive_self_improvement.engine_v2 import (
    CycleConfig, IndependentVerifier, RecursiveImprovementCycle)
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.protected_control_plane import (
    DEFAULT_PROTECTED_PATHS, ProtectedPathGuard)
from trading_bot.recursive_self_improvement.sleep_cycle import (
    SleepPhaseConfig, SleepPhaseRunner, SleepQuiesceError,
    channel_sleep_controller)


def _frames(args):
    if args.db:
        return SqliteSource(args.db, args.instruments).load()
    spec = SyntheticMarketSpec(
        seed=args.seed, instruments=tuple(args.instruments),
        regimes=(RegimeSpec("mean_revert", args.bars, vol=0.0002,
                            sine_amp=0.01, sine_period=8),))
    return SyntheticMarketGenerator(spec).generate()


def _contract(frames, n_bars, family):
    return {
        "schema_version": 2, "contract_id": "rsi-sleep-contract",
        "baseline_hash": "incumbent-mr-100",
        "dataset_hash": fingerprint_all(frames),
        "strategy_family": family,
        "allowed_parameters": {"lookback": [2, 200], "entry_threshold": [0.5, 4.0]},
        "min_bars": 20, "min_instruments": max(1, len(frames)),
        "block_size": 4, "max_trials": 10,
        "minimum_net_gain": 1e-6, "economic_materiality_min": 1e-6,
        "max_drawdown": 0.5, "max_drawdown_regression": 0.05,
        "confidence": 0.95, "min_cost_bps": 1.0, "max_cost_bps": 10.0,
        "max_latency_ms": 60000.0, "max_exposure": 0.05,
        "max_cvar_95": 0.5, "max_turnover": 20.0,
        "cost_model_id": "synthetic-costs-v1",
        "code_hash": candidate_code_hash(),
        "dependencies_hash": dependencies_hash(),
        "metric_directions": {"net_return": "max", "max_drawdown": "min",
                              "cvar_95": "min", "turnover": "min"},
        "pareto_objectives": ["net_return", "max_drawdown", "cvar_95", "turnover"],
        "regression_budgets": {"sharpe": 5.0, "turnover": 50.0},
        "regime_panel": ["trend", "mean_revert"],
        "holdout_query_budget": 10, "max_recursion_depth": 1,
        "protected_paths": list(DEFAULT_PROTECTED_PATHS),
        "seeds": [7], "cost_multipliers": [1.0, 1.5],
        "train_end": -30, "validation_start": -20, "validation_end": -10,
        "holdout_start": 0, "holdout_end": float(n_bars),
        "expiry": 4102444800.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", default="var/rsi_sleep",
                    help="archive/memory/verifier-key state directory")
    ap.add_argument("--state-dir", default=None,
                    help="live runner state dir; wires pause/resume through "
                         "the operator ControlChannel (sleep pauses trading)")
    ap.add_argument("--db", default=None, help="market_data.db for eval frames")
    ap.add_argument("--instruments", nargs="+", default=["EURUSD", "GBPUSD"])
    ap.add_argument("--family", default="mean_reversion",
                    choices=sorted(ADAPTERS))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--bars", type=int, default=160)
    ap.add_argument("--dreams", type=int, default=6)
    ap.add_argument("--dream-bars", type=int, default=160)
    ap.add_argument("--no-gated", action="store_true",
                    help="skip the gated improvement cycle")
    ap.add_argument("--no-consolidate", action="store_true")
    ap.add_argument("--max-experiment-rows", type=int, default=500)
    ap.add_argument("--quiesce-timeout", type=float, default=600.0,
                    help="seconds to wait for the runtime to drain the "
                         "pause command and report control:paused=1; the "
                         "channel only drains mid-cycle, so this must "
                         "outlast one runner cycle")
    ap.add_argument("--every-cycles", type=int, default=0,
                    help="repeat the sleep phase every N runner cycles "
                         "(needs --state-dir; polls snapshot.json)")
    ap.add_argument("--every-seconds", type=float, default=0.0,
                    help="repeat the sleep phase every N seconds "
                         "(wall-clock fallback when no runner snapshot "
                         "is available)")
    ap.add_argument("--max-sleeps", type=int, default=0,
                    help="stop after N sleep phases (0 = run until "
                         "interrupted)")
    ap.add_argument("--sandbox-backend", default="thread",
                    choices=["thread", "subprocess"],
                    help="'subprocess' is the isolation-correct backend; "
                         "'thread' is faster for offline engineering runs")
    args = ap.parse_args()

    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    frames = _frames(args)
    n_bars = len(next(iter(frames.values())))
    contract = _contract(frames, n_bars, args.family)

    # Provisioned verifier custody (file outside repo trust boundary is the
    # operator's job in production; a work-dir key is the offline equivalent).
    key_path = work / "sleep_verifier.pem"
    if not key_path.exists():
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey)
        IndependentVerifier(
            private_key=Ed25519PrivateKey.generate()
        ).export_private_key(str(key_path))
    verifier = IndependentVerifier(key_path=str(key_path))

    archive = ParetoArchive(work / "archive.jsonl")
    memory = ImprovementMemory(str(work / "memory.db"))
    incumbent = ({"lookback": 100, "entry_threshold": 1.0}
                 if args.family == "mean_reversion"
                 else {"fast_period": 10, "slow_period": 50}
                 if args.family == "momentum"
                 else {"lookback": 60})
    cycle = RecursiveImprovementCycle(
        contract=contract, verifier=verifier, archive=archive, memory=memory,
        guard=ProtectedPathGuard(), frames=frames,
        incumbent_params=incumbent, adapter=ADAPTERS[args.family],
        config=CycleConfig(run_transfer=False, max_candidates_per_cycle=4,
                           sandbox_backend=args.sandbox_backend))

    wiring = {}
    if args.state_dir:
        ctl = channel_sleep_controller(args.state_dir)
        wiring = {"pause_fn": ctl.pause, "resume_fn": ctl.resume,
                  "is_active_fn": ctl.is_active}
    runner = SleepPhaseRunner(
        cycle=cycle, **wiring,
        config=SleepPhaseConfig(
            n_dream_scenarios=args.dreams, dream_bars=args.dream_bars,
            run_gated_cycle=not args.no_gated,
            consolidate=not args.no_consolidate,
            max_experiment_rows=args.max_experiment_rows,
            quiesce_timeout_s=args.quiesce_timeout))

    def _cycles_now() -> float:
        """Runner's published cycle count; -1 when no fresh snapshot."""
        if not args.state_dir:
            return -1
        try:
            snap = json.loads(
                (Path(args.state_dir) / "snapshot.json").read_text(
                    encoding="utf-8"))
            return float(snap.get("cycles", -1))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return -1

    periodic = args.every_cycles > 0 or args.every_seconds > 0
    slept = 0
    rc = 0
    try:
        while True:
            try:
                report = runner.run_sleep()
            except SleepQuiesceError as exc:
                print(f"sleep phase refused: {exc}", file=sys.stderr)
                return 2
            slept += 1
            print(json.dumps(_report_json(report), indent=2, default=str))
            if not report.ledger_ok:
                rc = 3
            if not periodic or (args.max_sleeps and slept >= args.max_sleeps):
                return rc
            # Periodic window: wait until the runner's cycle count has
            # advanced by --every-cycles since this sleep, or the
            # --every-seconds wall clock elapses.
            mark = _cycles_now()
            deadline = (time.monotonic() + args.every_seconds
                        if args.every_seconds > 0 else None)
            while True:
                time.sleep(10)
                if args.every_cycles > 0:
                    now = _cycles_now()
                    if now >= 0 and mark >= 0 \
                            and now - mark >= args.every_cycles:
                        break
                elif deadline is not None and time.monotonic() >= deadline:
                    break
    except KeyboardInterrupt:
        print(f"sleep scheduler stopped after {slept} sleep phase(s)",
              file=sys.stderr)
        return rc


def _report_json(report) -> dict:
    return {
        "paused_here": report.paused_here,
        "consolidation": asdict(report.consolidation)
        if report.consolidation else None,
        "dreams_generated": report.dreams_generated,
        "dreams_kept": report.dreams_kept,
        "top_dreams": [
            {"label": s.label, "regime": s.regime, "power": s.power,
             "best_probe": dict(s.best_probe)}
            for s in report.top_dreams],
        "recombinations": report.recombinations,
        "decisions": [{"genome_id": d.genome_id, "status": d.status,
                       "reason": d.reason} for d in report.decisions],
        "ledger_ok": report.ledger_ok,
        "notes": report.notes,
        "interpretation": (
            "dream/recombination output is diagnostic only and cannot "
            "promote; 'decisions' come from the gated paired-replay cycle "
            "and at most reach eligible_for_operator_review."),
    }


if __name__ == "__main__":
    sys.exit(main())
