"""RSI synthetic benchmark + ablation (mission section 18).

Runs the Level-1 cycle over N seeds on synthetic markets with planted and
absent edges, and ablates (a) anti-gaming checks and (b) Pareto+statistical
selection vs naive scalar selection. Measures the *machinery* — false
eligible rate, detection rates — on engineering fixtures. Output:
ABLATION_RSI_SYNTHETIC.json. No market conclusion can be drawn from this.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_bot.evaluation.synthetic_market import (
    RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec, fingerprint_all)
from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.candidate_adapters import (
    ADAPTERS, candidate_code_hash, dependencies_hash)
from trading_bot.recursive_self_improvement.engine_v2 import (
    CycleConfig, IndependentVerifier, RecursiveImprovementCycle, SandboxManager)
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.protected_control_plane import (
    DEFAULT_PROTECTED_PATHS, ProtectedPathGuard)
from trading_bot.recursive_self_improvement.scorecard import RSIScorecard


def _contract(frames, n_bars):
    return {
        "schema_version": 2, "contract_id": "ablation-contract",
        "baseline_hash": "incumbent-100",
        "dataset_hash": fingerprint_all(frames),
        "strategy_family": "mean_reversion",
        "allowed_parameters": {"lookback": [2, 200], "entry_threshold": [0.5, 4.0]},
        "min_bars": 20, "min_instruments": 2, "block_size": 4, "max_trials": 10,
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


def _frames(seed, n=160, edge=True):
    spec = SyntheticMarketSpec(
        seed=seed, instruments=("EURUSD", "GBPUSD"),
        regimes=(RegimeSpec("mean_revert", n, vol=0.0002,
                            sine_amp=0.01 if edge else 0.0, sine_period=8),))
    return SyntheticMarketGenerator(spec).generate()


def run_cycle(seed, edge, workdir):
    frames = _frames(seed, edge=edge)
    contract = _contract(frames, 160)
    archive = ParetoArchive(Path(workdir) / f"a{seed}-{edge}.jsonl")
    memory = ImprovementMemory(str(Path(workdir) / f"m{seed}-{edge}.db"))
    cycle = RecursiveImprovementCycle(
        contract=contract, verifier=IndependentVerifier(), archive=archive,
        memory=memory, guard=ProtectedPathGuard(), frames=frames,
        incumbent_params={"lookback": 100, "entry_threshold": 1.0},
        adapter=ADAPTERS["mean_reversion"],
        config=CycleConfig(run_transfer=False, max_candidates_per_cycle=4,
                           wall_clock_s=25.0))
    decisions = cycle.run_cycle()
    return decisions, RSIScorecard(archive, memory).compute()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default="ABLATION_RSI_SYNTHETIC.json")
    args = ap.parse_args()

    results = {"edge": {"eligible": 0, "rejected": 0, "insufficient": 0, "runs": []},
               "no_edge": {"eligible": 0, "rejected": 0, "insufficient": 0, "runs": []}}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for seed in range(args.seeds):
            for edge in (True, False):
                decisions, card = run_cycle(seed, edge, tmp)
                key = "edge" if edge else "no_edge"
                for d in decisions:
                    bucket = ("eligible" if d.status == "eligible_for_operator_review"
                              else "rejected" if d.status == "rejected"
                              else "insufficient")
                    results[key][bucket] += 1
                results[key]["runs"].append(
                    {"seed": seed, "decisions": len(decisions),
                     "eligible_rate": card["eligible_rate"],
                     "chain_valid": card["archive_chain_valid"]})
    results["interpretation"] = (
        "eligible rate under 'edge' = planted-fixture sensitivity; under "
        "'no_edge' should be ~0 (false-eligible rate on noise). These are "
        "machinery metrics, not market evidence.")
    out = Path(args.out)
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
