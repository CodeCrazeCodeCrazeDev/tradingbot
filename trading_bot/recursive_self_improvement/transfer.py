"""Transfer evaluation (mission section 9): LOCAL / ROBUST / TRANSFERABLE /
SYSTEMIC classification across regimes, instruments, seeds and cost stress.

The caller supplies scenario panels; each is replayed with the same paired
runner the main gate uses, so transfer claims rest on identical mechanics,
not on a weaker secondary simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from trading_bot.evaluation.runner import PairedFamilyReplay
from trading_bot.evaluation.synthetic_market import fingerprint_all

from .metric_registry import direction
from .multi_objective import metric_vector
from .multiplicity import block_bootstrap_lower, bonferroni_alpha, contract_seed


@dataclass(frozen=True)
class Scenario:
    label: str
    regime: str
    cost_multiplier: float
    seed: int
    frames: Mapping[str, Any]


@dataclass
class ScenarioResult:
    label: str
    regime: str
    cost_multiplier: float
    seed: int
    frames_hash: str
    delta_net: float
    ci_lower: Optional[float]
    metrics_b: Dict[str, float]
    metrics_c: Dict[str, float]
    violations: List[str] = field(default_factory=list)


class TransferEvaluator:
    """Runs the paired replay across a scenario panel and classifies transfer."""

    def __init__(self, contract: Mapping[str, Any], adapter: Any,
                 fraction: float = 0.01) -> None:
        self.contract = contract
        self.adapter = adapter
        self.fraction = fraction

    def run_scenario(
        self,
        scenario: Scenario,
        baseline_params: Mapping[str, Any],
        candidate_params: Mapping[str, Any],
    ) -> ScenarioResult:
        cost = float(self.contract["max_cost_bps"]) * scenario.cost_multiplier \
            if scenario.cost_multiplier > 1.0 else float(self.contract["min_cost_bps"])
        cost = max(cost, 1.0)
        runner = PairedFamilyReplay(self.adapter, cost_bps=cost, fraction=self.fraction)
        out = runner.run(dict(scenario.frames),
                         baseline_params=dict(baseline_params),
                         candidate_params=dict(candidate_params))
        bars = out["bars"]
        grouped: Dict[str, Dict[Any, Any]] = {}
        for row in bars:
            grouped.setdefault(row["symbol"], {})[row["timestamp"]] = row
        timeline = sorted(next(iter(grouped.values()))) if grouped else []
        violations: List[str] = []
        if not timeline:
            return ScenarioResult(scenario.label, scenario.regime,
                                  scenario.cost_multiplier, scenario.seed,
                                  fingerprint_all(scenario.frames),
                                  0.0, None, {}, {}, ["empty replay"])
        base_net = [sum(grouped[s][t]["baseline_net"] for s in grouped) / len(grouped) for t in timeline]
        cand_net = [sum(grouped[s][t]["candidate_net"] for s in grouped) / len(grouped) for t in timeline]
        diffs = [c - b for c, b in zip(cand_net, base_net)]
        alpha = bonferroni_alpha(
            int(self.contract.get("max_trials", 1)), float(self.contract["confidence"]))
        lower = block_bootstrap_lower(
            diffs, int(self.contract["block_size"]), alpha,
            contract_seed(dict(self.contract), scenario.label))
        mb = metric_vector(base_net)
        mc = metric_vector(cand_net)
        return ScenarioResult(
            label=scenario.label, regime=scenario.regime,
            cost_multiplier=scenario.cost_multiplier, seed=scenario.seed,
            frames_hash=fingerprint_all(scenario.frames),
            delta_net=sum(diffs) / len(diffs), ci_lower=lower,
            metrics_b=mb, metrics_c=mc, violations=violations,
        )

    def classify(self, results: Sequence[ScenarioResult],
                 selection_regime: str) -> Tuple[str, Dict[str, Any]]:
        """LOCAL -> ROBUST -> TRANSFERABLE -> SYSTEMIC ladder."""
        c = self.contract
        details: Dict[str, Any] = {"scenarios": len(results)}
        by_regime: Dict[str, List[ScenarioResult]] = {}
        for r in results:
            by_regime.setdefault(r.regime, []).append(r)

        def positive(res: ScenarioResult) -> bool:
            return res.ci_lower is not None and res.ci_lower > 0

        sel = [r for r in by_regime.get(selection_regime, [])]
        sel_at_observed = [r for r in sel if r.cost_multiplier == 1.0]
        sel_all_costs = [r for r in sel]
        if not sel_at_observed or not all(positive(r) for r in sel_at_observed):
            details["reason"] = "no significant gain in the selection regime"
            return "LOCAL", details
        # LOCAL or better from here
        cost_mults = sorted({r.cost_multiplier for r in sel_all_costs})
        robust = all(
            any(r.cost_multiplier == m and positive(r) for r in sel)
            for m in cost_mults
        )
        regime_ok = sum(
            1 for regime, rs in by_regime.items()
            if any(positive(r) for r in rs if r.cost_multiplier == 1.0)
        )
        details["regimes_positive"] = regime_ok
        details["regimes_total"] = len(by_regime)
        if not robust:
            details["reason"] = "gain evaporates under cost stress"
            return "LOCAL", details
        transferable = regime_ok * 3 >= len(by_regime) * 2
        if not transferable:
            return "ROBUST", details
        # systemic: no regression-budget breach anywhere
        for r in results:
            for metric, budget in c.get("regression_budgets", {}).items():
                d = direction(metric)
                cv, bv = r.metrics_c.get(metric, 0.0), r.metrics_b.get(metric, 0.0)
                if (d == "max" and cv < bv - budget) or (d == "min" and cv > bv + budget):
                    details["reason"] = f"regression breach on {metric} in {r.label}"
                    return "TRANSFERABLE", details
        return "SYSTEMIC", details
