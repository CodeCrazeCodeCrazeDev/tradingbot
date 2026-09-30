"""Multi-objective v2 evaluator: hard constraints + regression budgets +
Pareto relation + dependence-aware inference.

Ordering follows RSI_EVALUATION_CONTRACT.md: schema/provenance -> sandbox
invariants -> data/causality/cost -> paired rows -> transfer coverage ->
anti-gaming -> hard bounds -> regression budgets -> economic hurdle ->
Pareto -> corrected statistics -> eligible_for_operator_review.
The word "eligible" is as far as this evaluator ever goes — it never
authorizes deployment.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .anti_gaming import check_metric_gaming
from .contracts import ContractError, canonical, contract_hash, validate_contract
from .metric_registry import direction
from .multiplicity import bonferroni_alpha


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def metric_vector(returns: Sequence[float], turnover: float = 0.0,
                  exposures: Sequence[float] = (), directions: Sequence[int] = ()) -> Dict[str, float]:
    """Full objective vector for one side of a paired replay."""
    n = len(returns)
    if n == 0:
        return {"net_return": 0.0}
    equity, peak, max_dd = 1.0, 1.0, 0.0
    dd_dur = cur_dur = 0
    path: List[float] = []
    for r in returns:
        equity *= 1.0 + r
        path.append(equity)
        peak = max(peak, equity)
        dd = 1.0 - equity / peak
        max_dd = max(max_dd, dd)
        cur_dur = cur_dur + 1 if dd > 0 else 0
        dd_dur = max(dd_dur, cur_dur)
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / max(1, n - 1)
    sd = math.sqrt(var)
    downside = [min(r, 0.0) for r in returns]
    dsd = math.sqrt(sum(d * d for d in downside) / n)
    gross_pos = sum(r for r in returns if r > 0)
    gross_neg = -sum(r for r in returns if r < 0)
    losses = sorted(-r for r in returns if r < 0)
    tail = max(1, math.ceil(n * 0.05))
    cvar = sum(losses[-tail:]) / tail if losses else 0.0
    entries = sum(1 for i, d in enumerate(directions)
                  if d != 0 and (i == 0 or directions[i - 1] == 0))
    invested = sum(1 for d in directions if d != 0)
    net_ret = equity - 1.0
    return {
        "net_return": net_ret,
        "sharpe": mean / sd if sd > 0 else 0.0,
        "sortino": mean / dsd if dsd > 0 else 0.0,
        "calmar": net_ret / max_dd if max_dd > 0 else 0.0,
        "expectancy": net_ret / entries if entries else 0.0,
        "profit_factor": min(gross_pos / gross_neg, 999.0) if gross_neg > 0 else (999.0 if gross_pos > 0 else 0.0),
        "max_drawdown": max_dd,
        "drawdown_duration_bars": float(dd_dur),
        "cvar_95": cvar,
        "downside_deviation": dsd,
        "turnover": turnover,
        "exposure_mean": (sum(exposures) / len(exposures)) if exposures else 0.0,
        "exposure_max": max(exposures) if exposures else 0.0,
        "single_bar_max_loss": max((-r for r in returns), default=0.0),
        "n_trades": float(entries),
        "abstain_rate": 1.0 - invested / n if n else 1.0,
        "zero_trade_frac": 1.0 - invested / n if n else 1.0,
        "n_bars": float(n),
    }


def pareto_relation(candidate: Mapping[str, float], baseline: Mapping[str, float],
                    objectives: Sequence[str]) -> str:
    """"dominates" if candidate >= baseline on every objective and > on one."""
    better = worse = False
    for o in objectives:
        d = direction(o)
        c, b = candidate.get(o, 0.0), baseline.get(o, 0.0)
        if (d == "max" and c < b - 1e-12) or (d == "min" and c > b + 1e-12):
            worse = True
        elif (d == "max" and c > b + 1e-12) or (d == "min" and c < b - 1e-12):
            better = True
    if worse and not better:
        return "dominated"
    if better and not worse:
        return "dominates"
    return "incomparable"


class MultiObjectiveEvaluator:
    """Evaluates a signed-or-local paired report under a schema-2 contract."""

    def __init__(self, contract: Mapping[str, Any]) -> None:
        self.contract = validate_contract(dict(contract))
        self.contract_hash = contract_hash(self.contract)

    def _verdict(self, status: str, reason: str, **extra: Any) -> Dict[str, Any]:
        return {"status": status, "reason": reason,
                "promotion_eligible": False, **extra}

    # -- row-level causal/cost validation -------------------------------------
    def _check_rows(self, report: Mapping[str, Any]) -> Tuple[Optional[str], Dict[str, Dict[Any, Any]]]:
        c = self.contract
        grouped: Dict[str, Dict[Any, Any]] = {}
        rows = report.get("bars")
        if not isinstance(rows, list) or not rows:
            return "empty evidence rows", grouped
        for row in rows:
            if not isinstance(row, dict):
                return "malformed row", grouped
            for k in ("baseline_net", "candidate_net", "baseline_gross", "candidate_gross",
                      "baseline_turnover", "candidate_turnover", "cost_bps",
                      "baseline_exposure", "candidate_exposure"):
                if not _finite(row.get(k)):
                    return f"nonfinite {k}", grouped
            cost = row["cost_bps"]
            if cost < c["min_cost_bps"] or cost > c["max_cost_bps"]:
                return "cost outside contracted band", grouped
            for side in ("baseline", "candidate"):
                t, e, g = row[f"{side}_turnover"], row[f"{side}_exposure"], row[f"{side}_gross"]
                if t < 0 or t > c["max_turnover"] or (e == 0 and g != 0):
                    return "return without exposure or turnover breach", grouped
                if not math.isclose(row[f"{side}_net"], g - t * cost / 10000.0,
                                    rel_tol=1e-9, abs_tol=1e-12):
                    return "net does not account for declared costs", grouped
            if row["candidate_exposure"] > c["max_exposure"]:
                return "candidate breached exposure cap", grouped
            ts, sym = row.get("timestamp"), row.get("symbol")
            if (not isinstance(sym, str) or not sym or not _finite(ts)
                    or not c["holdout_start"] <= ts < c["holdout_end"]):
                return "invalid instrument or holdout timestamp", grouped
            bucket = grouped.setdefault(sym, {})
            if ts in bucket:
                return "duplicate timestamp in paired evaluation", grouped
            bucket[ts] = row
        if len(grouped) < c["min_instruments"] or any(
            len(v) < c["min_bars"] for v in grouped.values()
        ):
            return "insufficient cross-instrument transfer observations", grouped
        timelines = [set(v) for v in grouped.values()]
        if any(t != timelines[0] for t in timelines):
            return "candidate and baseline timeline is not aligned", grouped
        return None, grouped

    def _series(self, grouped: Dict[str, Dict[Any, Any]], side: str,
                field: str, timeline: List[Any]) -> List[float]:
        return [sum(grouped[s][t][f"{side}_{field}"] for s in grouped) / len(grouped)
                for t in timeline]

    # -- main gate -------------------------------------------------------------
    def evaluate(self, genome: Any, report: Mapping[str, Any],
                 *, regime_deltas: Optional[Mapping[str, float]] = None,
                 expected_contract_hash: str = "",
                 holdout_queries_used: int = 1,
                 signature: str = "",
                 verifier_public_key: Optional[Any] = None) -> Dict[str, Any]:
        v = self._verdict
        c = self.contract
        try:
            if expected_contract_hash and expected_contract_hash != self.contract_hash:
                return v("rejected", "contract mutated between proposal and evaluation")
            if not isinstance(report, dict) or report.get("schema_version") != 2:
                return v("insufficient_evidence", "unsupported evidence schema")
            if (report.get("contract_id") != c["contract_id"]
                    or report.get("baseline_hash") != c["baseline_hash"]
                    or report.get("dataset_hash") != c["dataset_hash"]):
                return v("rejected", "contract, baseline or dataset mismatch")
            if not report.get("holdout_attested") or not report.get("verifier_id") or not report.get("trial_id"):
                return v("insufficient_evidence", "independent holdout attestation absent")
            # Attestation is a claim; a signature is the proof. When the
            # contract pins the accepted verifier key (verifier_pubkey_hex)
            # the report must verify under exactly that key — this is what
            # makes custody enforceable instead of self-declared. Without a
            # pin, an engine-supplied key is still used to check the report
            # was signed untampered.
            check_key = verifier_public_key
            pinned_hex = c.get("verifier_pubkey_hex")
            if pinned_hex:
                try:
                    check_key = Ed25519PublicKey.from_public_bytes(
                        bytes.fromhex(str(pinned_hex)))
                except (ValueError, TypeError):
                    return v("insufficient_evidence",
                             "operator-pinned verifier key malformed")
            if check_key is not None:
                if not signature:
                    return v("insufficient_evidence",
                             "verifier signature required but absent")
                try:
                    check_key.verify(bytes.fromhex(signature), canonical(report))
                except (ValueError, TypeError, InvalidSignature):
                    return v("insufficient_evidence", "verifier signature invalid")
            if not report.get("risk_invariants_passed"):
                return v("rejected", "protected runtime risk invariant failed")
            if (report.get("code_hash") != c["code_hash"]
                    or report.get("dependencies_hash") != c["dependencies_hash"]):
                return v("rejected", "candidate modified code or dependencies")
            if not report.get("parameter_effect_verified"):
                return v("insufficient_evidence", "parameter effect unverified")
            if report.get("cost_model_id") != c["cost_model_id"]:
                return v("insufficient_evidence", "cost model not bound to evaluation")
            trial_count = report.get("trial_count", 0)
            if not isinstance(trial_count, int) or not 0 < trial_count <= c["max_trials"]:
                return v("rejected", "trial budget exceeded")
            if holdout_queries_used > c["holdout_query_budget"]:
                return v("rejected", "holdout query budget exhausted")
            if genome is not None:
                if (genome.fingerprint != report.get("candidate_hash")
                        or genome.parent_id != c["baseline_hash"]
                        or genome.evaluation_plan.get("contract_id") != c["contract_id"]):
                    return v("rejected", "candidate not bound to report")
                if len(genome.change_set) != 1 or dict(genome.change_set) != report.get("candidate_parameters"):
                    return v("rejected", "candidate parameters not bound to report")
                for key, val in genome.change_set.items():
                    bounds = c["allowed_parameters"].get(key)
                    if (bounds is None or isinstance(val, bool)
                            or not _finite(val) or not bounds[0] <= val <= bounds[1]):
                        return v("rejected", "protected or out-of-bounds candidate parameter")
            latency = report.get("latency_ms")
            if not _finite(latency) or latency < 0:
                return v("insufficient_evidence", "invalid latency measurement")
            if latency > c["max_latency_ms"]:
                return v("rejected", "latency limit breached")

            err, grouped = self._check_rows(report)
            if err:
                return v("insufficient_evidence" if "insufficient" in err or "invalid" in err
                         or "not aligned" in err or "empty" in err or "malformed" in err
                         else "rejected", err)
            timeline = sorted(next(iter(grouped.values())))
            base_net = self._series(grouped, "baseline", "net", timeline)
            cand_net = self._series(grouped, "candidate", "net", timeline)
            if any(r <= -1 for r in base_net + cand_net):
                return v("rejected", "nonviable equity path")
            base_turn = sum(self._series(grouped, "baseline", "turnover", timeline))
            cand_turn = sum(self._series(grouped, "candidate", "turnover", timeline))
            base_exp = self._series(grouped, "baseline", "exposure", timeline)
            cand_exp = self._series(grouped, "candidate", "exposure", timeline)
            base_dir = [int(grouped[next(iter(grouped))][t].get("baseline_direction", 0) or 0) for t in timeline]
            cand_dir = [int(grouped[next(iter(grouped))][t].get("candidate_direction", 0) or 0) for t in timeline]

            metrics_b = metric_vector(base_net, base_turn, base_exp, base_dir)
            metrics_c = metric_vector(cand_net, cand_turn, cand_exp, cand_dir)
            # exposure ceiling: candidate may not lever up beyond incumbent's max
            if metrics_c["exposure_max"] > metrics_b["exposure_max"] + 1e-12:
                return v("rejected", "candidate raised maximum exposure",
                         metrics=None, delta=None)
            metrics_b["gross_return"] = sum(self._series(grouped, "baseline", "gross", timeline))
            metrics_c["gross_return"] = sum(self._series(grouped, "candidate", "gross", timeline))
            delta = {k: metrics_c[k] - metrics_b[k] for k in metrics_b
                     if _finite(metrics_c.get(k)) and _finite(metrics_b.get(k))}
            metrics = {f"baseline_{k}": val for k, val in metrics_b.items()}
            metrics.update({f"candidate_{k}": val for k, val in metrics_c.items()})

            inst_delta = {
                s: (metric_vector([grouped[s][t]["candidate_net"] for t in timeline])["net_return"]
                    - metric_vector([grouped[s][t]["baseline_net"] for t in timeline])["net_return"])
                for s in grouped
            }
            metrics["instrument_net_advantage"] = inst_delta
            if any(val < 0 for val in inst_delta.values()):
                return v("rejected", "candidate regresses on a required instrument",
                         metrics=metrics, delta=delta)
            if cand_net == base_net:
                return v("rejected", "candidate produced no change",
                         metrics=metrics, delta=delta)

            mean_cost = sum(r["cost_bps"] for r in report["bars"]) / len(report["bars"])
            gaming = check_metric_gaming(
                report["bars"], c, metrics_b, metrics_c,
                expected_contract_hash=expected_contract_hash,
                regime_deltas=regime_deltas, mean_cost_bps=mean_cost,
            )
            if gaming:
                return v("rejected", "suspected_metric_gaming: " + "; ".join(gaming),
                         metrics=metrics, delta=delta)

            # hard bounds
            if (metrics_c["max_drawdown"] > c["max_drawdown"]
                    or metrics_c["cvar_95"] > c["max_cvar_95"]
                    or metrics_c["exposure_max"] > c["max_exposure"]
                    or metrics_c["turnover"] > c["max_turnover"]):
                return v("rejected", "hard risk limit breached",
                         metrics=metrics, delta=delta)
            if metrics_c["max_drawdown"] - metrics_b["max_drawdown"] > c["max_drawdown_regression"]:
                return v("rejected", "drawdown regression limit breached",
                         metrics=metrics, delta=delta)

            # regression budgets
            for metric, budget in c["regression_budgets"].items():
                if metric not in metrics_c:
                    continue
                d = direction(metric)
                cval, bval = metrics_c[metric], metrics_b[metric]
                if (d == "max" and cval < bval - budget) or (d == "min" and cval > bval + budget):
                    return v("rejected", f"regression budget exceeded on {metric}",
                             metrics=metrics, delta=delta)

            # economic materiality
            hurdle = max(c["minimum_net_gain"], c["economic_materiality_min"])
            if delta.get("net_return", 0.0) < hurdle:
                return v("rejected", "candidate lacks economically material net gain",
                         metrics=metrics, delta=delta)

            # Pareto
            relation = pareto_relation(metrics_c, metrics_b, c["pareto_objectives"])
            metrics["pareto_relation"] = relation
            if relation == "dominated":
                return v("rejected", "candidate is Pareto dominated",
                         metrics=metrics, delta=delta)

            # corrected paired inference
            diffs = [x - y for x, y in zip(cand_net, base_net)]
            block = int(c["block_size"])
            if len(diffs) // block < 5:
                return v("insufficient_evidence", "insufficient effective block sample",
                         metrics=metrics, delta=delta)
            rng = random.Random(int(hashlib.sha256(
                json.dumps(c, sort_keys=True, default=str).encode()
            ).hexdigest()[:16], 16))
            n = len(diffs)
            bootstrap: List[float] = []
            for _ in range(512):
                draws: List[float] = []
                while len(draws) < n:
                    start = rng.randrange(n)
                    draws.extend(diffs[(start + j) % n] for j in range(block))
                bootstrap.append(sum(draws[:n]) / n)
            bootstrap.sort()
            alpha = bonferroni_alpha(trial_count, c["confidence"])
            lower = bootstrap[max(0, int(alpha * len(bootstrap)))]
            metrics["paired_mean_diff"] = sum(diffs) / n
            metrics["paired_ci_lower"] = lower
            sd = math.sqrt(sum((x - metrics["paired_mean_diff"]) ** 2 for x in diffs) / max(1, n - 1))
            metrics["effect_size"] = metrics["paired_mean_diff"] / sd if sd > 0 else 0.0
            metrics["n_effective"] = float(len(diffs) // block)
            if lower <= 0:
                return v("insufficient_evidence",
                         "paired corrected lower confidence bound not positive",
                         metrics=metrics, delta=delta)
            return v("eligible_for_operator_review",
                     "v2 multi-objective gates cleared; no deployment authorized",
                     metrics=metrics, delta=delta)
        except (KeyError, TypeError, IndexError, OverflowError, ContractError, ValueError) as exc:
            return v("insufficient_evidence", f"malformed or incomplete evidence: {exc}")
