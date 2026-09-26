import hashlib
import json
import logging
import math
import random
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

import numpy as np
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

logger = logging.getLogger(__name__)

class EvaluationEngine:
    """
    Measures and validates improvements across multiple dimensions.
    Ensures that improvements are statistically significant and robust.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_confidence = self.config.get("min_confidence", 0.95)
        self.min_improvement_threshold = self.config.get("min_improvement", 0.02)

    def evaluate_improvement(self, baseline_metrics: Dict[str, float], candidate_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare baseline vs candidate performance.
        Returns a detailed evaluation report.
        """
        report = {
            "is_improved": False,
            "confidence_score": 0.0,
            "improvements": {},
            "regressions": [],
            "overall_score": 0.0,
            "recommendation": "reject"
        }

        # Calculate delta for each metric
        total_delta = 0.0
        for metric, baseline_val in baseline_metrics.items():
            if metric in candidate_metrics:
                candidate_val = candidate_metrics[metric]
                delta = (candidate_val - baseline_val) / abs(baseline_val) if baseline_val != 0 else 0
                report["improvements"][metric] = delta

                # Weight based on metric importance (simplified)
                weight = 1.0
                if "sharpe" in metric.lower(): weight = 2.0
                if "pnl" in metric.lower(): weight = 1.5
                if "drawdown" in metric.lower():
                    weight = 2.0
                    delta = -delta # Lower drawdown is better

                total_delta += delta * weight

                if delta < -0.05: # Regression threshold
                    report["regressions"].append(metric)

        # Overall score (normalized improvement)
        report["overall_score"] = total_delta

        # Decision logic
        report["recommendation"] = "diagnostic_only_independent_evidence_required"
        report["promotion_eligible"] = False
        return report

    def assess_robustness(self, regime_results: Dict[str, Dict[str, float]]) -> float:
        """
        Assess how well an improvement performs across different market regimes.
        Returns a robustness score (0.0 to 1.0).
        """
        if not regime_results:
            return 0.0

        scores = []
        for regime, metrics in regime_results.items():
            # Calculate a basic performance score for each regime
            sharpe = metrics.get("sharpe_ratio", 0)
            win_rate = metrics.get("win_rate", 0)
            scores.append(sharpe * win_rate)

        if not scores:
            return 0.0

        # Robustness is inversely proportional to variance across regimes
        avg_score = np.mean(scores)
        std_score = np.std(scores)

        robustness = 1.0 - (std_score / abs(avg_score)) if avg_score != 0 else 0
        return max(0.0, min(1.0, robustness))

    def run_statistical_check(self, baseline_samples: List[float], candidate_samples: List[float]) -> Dict[str, Any]:
        """
        Perform t-test or similar to check for statistical significance.
        """
        from scipy import stats

        if len(baseline_samples) < 2 or len(candidate_samples) < 2:
            return {"significant": False, "p_value": 1.0}

        t_stat, p_value = stats.ttest_ind(candidate_samples, baseline_samples)

        return {
            "significant": p_value < (1 - self.min_confidence),
            "p_value": p_value,
            "t_stat": t_stat
        }

    @staticmethod
    def _canonical(data: Dict[str, Any]) -> bytes:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

    @staticmethod
    def _equity_metrics(returns: List[float]) -> Dict[str, float]:
        equity = peak = 1.0
        drawdown = 0.0
        for ret in returns:
            equity *= 1.0 + ret
            peak = max(peak, equity)
            drawdown = max(drawdown, 1.0 - equity / peak)
        losses = sorted(-x for x in returns if x < 0)
        tail = max(1, math.ceil(len(returns) * 0.05))
        return {"net_return": equity - 1.0, "max_drawdown": drawdown,
                "cvar_95": sum(losses[-tail:]) / tail if losses else 0.0}

    def evaluate_verified(self, genome: Any, contract: Dict[str, Any], contract_signature: str,
                          operator_public_key: Any, report: Dict[str, Any], report_signature: str,
                          verifier_public_key: Any) -> Dict[str, Any]:
        def verdict(status: str, reason: str, **extra: Any) -> Dict[str, Any]:
            return {"status": status, "reason": reason, "promotion_eligible": False, **extra}

        if not isinstance(operator_public_key, Ed25519PublicKey) or not isinstance(verifier_public_key, Ed25519PublicKey):
            return verdict("insufficient_evidence", "operator and verifier trust anchors required")
        if operator_public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) == \
                verifier_public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw):
            return verdict("insufficient_evidence", "operator and verifier must be independent")
        try:
            operator_public_key.verify(bytes.fromhex(contract_signature), self._canonical(contract))
            verifier_public_key.verify(bytes.fromhex(report_signature), self._canonical(report))
        except (ValueError, TypeError, AttributeError, InvalidSignature, OverflowError):
            return verdict("insufficient_evidence", "missing or invalid independent signatures")
        required = ("schema_version", "contract_id", "baseline_hash", "dataset_hash", "allowed_parameters",
                    "min_bars", "min_instruments", "block_size", "max_trials", "minimum_net_gain",
                    "max_drawdown", "max_drawdown_regression", "confidence", "max_cost_bps", "max_latency_ms",
                    "train_end", "validation_start", "validation_end", "holdout_start", "holdout_end",
                    "cost_model_id", "max_exposure", "max_cvar_95", "code_hash",
                    "dependencies_hash", "max_turnover", "expires_at")
        if not isinstance(contract, dict) or not isinstance(report, dict) or any(k not in contract for k in required):
            return verdict("insufficient_evidence", "unsigned or incomplete evaluation contract")
        try:
            if contract["schema_version"] != 1 or report["schema_version"] != 1:
                return verdict("insufficient_evidence", "unsupported evidence schema")
            if (report["contract_id"] != contract["contract_id"] or
                    report["baseline_hash"] != contract["baseline_hash"] or
                    report["dataset_hash"] != contract["dataset_hash"] or
                    report["candidate_hash"] != genome.fingerprint or
                    genome.parent_id != contract["baseline_hash"] or
                    genome.evaluation_plan.get("contract_id") != contract["contract_id"]):
                return verdict("rejected", "contract, baseline, dataset or candidate mismatch")
            if not (contract["train_end"] < contract["validation_start"] <= contract["validation_end"] <
                    contract["holdout_start"] < contract["holdout_end"]):
                return verdict("insufficient_evidence", "chronological split or embargo is invalid")
            now = time.time()
            if (not all(isinstance(v, (int, float)) and math.isfinite(v)
                        for v in (contract["expires_at"], report["issued_at"], report["expires_at"])) or
                    report["issued_at"] > now + 60 or report["issued_at"] > report["expires_at"] or
                    report["expires_at"] > contract["expires_at"] or now >= report["expires_at"]):
                return verdict("insufficient_evidence", "stale or inconsistent verifier attestation")
            if (report["holdout_attested"] is not True or not isinstance(report["verifier_id"], str) or
                    not report["verifier_id"] or not isinstance(report["trial_id"], str) or
                    not report["trial_id"] or not isinstance(report["nonce"], str) or not report["nonce"]):
                return verdict("insufficient_evidence", "independent holdout attestation absent")
            if report["risk_invariants_passed"] is not True:
                return verdict("rejected", "protected runtime risk invariant failed")
            if (report["code_hash"] != contract["code_hash"] or
                    report["dependencies_hash"] != contract["dependencies_hash"]):
                return verdict("rejected", "parameter candidate modified code or dependencies")
            if report["parameter_effect_verified"] is not True:
                return verdict("insufficient_evidence", "strategy parameter effect unverified")
            if report["cost_model_id"] != contract["cost_model_id"] or not contract["cost_model_id"]:
                return verdict("insufficient_evidence", "cost model is not bound to evaluation")
            if (type(report["trial_count"]) is not int or type(contract["max_trials"]) is not int or
                    not 0 < report["trial_count"] <= contract["max_trials"]):
                return verdict("rejected", "trial budget exceeded")
            if (getattr(genome.domain, "value", "") != "alpha_strategy_discovery" or
                    genome.safety_constraints or len(genome.change_set) != 1 or
                    dict(genome.change_set) != report["candidate_parameters"]):
                return verdict("rejected", "candidate outside bounded strategy-parameter scope")
            for key, val in genome.change_set.items():
                bounds = contract["allowed_parameters"].get(key)
                if not bounds or isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or not bounds[0] <= val <= bounds[1]:
                    return verdict("rejected", "protected or out-of-bounds candidate parameter")
            numeric = ("minimum_net_gain", "max_drawdown", "max_drawdown_regression", "confidence",
                       "max_cost_bps", "max_latency_ms", "block_size", "min_bars", "min_instruments",
                       "max_exposure", "max_cvar_95", "max_turnover")
            if any(not isinstance(contract[k], (int, float)) or isinstance(contract[k], bool) or
                   not math.isfinite(contract[k]) for k in numeric):
                return verdict("insufficient_evidence", "nonfinite or missing contract threshold")
            if not (0 < contract["confidence"] < 1 and contract["block_size"] > 0 and
                    contract["min_bars"] >= 2 and contract["min_instruments"] >= 2 and
                    contract["minimum_net_gain"] > 0 and contract["max_drawdown"] >= 0 and
                    contract["max_drawdown_regression"] >= 0 and contract["max_exposure"] > 0 and
                    contract["max_cvar_95"] >= 0 and contract["max_turnover"] >= 0):
                return verdict("insufficient_evidence", "invalid operator-calibrated thresholds")
            if not math.isfinite(report["latency_ms"]) or report["latency_ms"] < 0:
                return verdict("insufficient_evidence", "invalid latency measurement")
            if report["latency_ms"] > contract["max_latency_ms"]:
                return verdict("rejected", "latency limit breached")
            grouped: Dict[str, Dict[Any, Any]] = {}
            for row in report["bars"]:
                if any(not isinstance(row[k], (float, int)) or isinstance(row[k], bool) or
                       not math.isfinite(row[k]) for k in
                       ("baseline_net", "candidate_net", "baseline_gross", "candidate_gross",
                        "baseline_turnover", "candidate_turnover", "cost_bps",
                        "baseline_exposure", "candidate_exposure")):
                    return verdict("insufficient_evidence", "nonfinite paired returns, costs or exposure")
                if row["cost_bps"] <= 0 or row["cost_bps"] > contract["max_cost_bps"]:
                    return verdict("rejected", "cost model missing or exceeds limit")
                for side in ("baseline", "candidate"):
                    turnover = row[f"{side}_turnover"]
                    exposure = row[f"{side}_exposure"]
                    if turnover < 0 or turnover > contract["max_turnover"] or (exposure == 0 and row[f"{side}_gross"] != 0):
                        return verdict("rejected", "return without exposure or turnover limit breached")
                    net = row[f"{side}_gross"] - turnover * row["cost_bps"] / 10000
                    if not math.isclose(row[f"{side}_net"], net, rel_tol=1e-9, abs_tol=1e-12):
                        return verdict("rejected", "net return does not account for declared costs")
                if (abs(row["candidate_exposure"]) > abs(row["baseline_exposure"]) + 1e-12 or
                        abs(row["candidate_exposure"]) > contract["max_exposure"]):
                    return verdict("rejected", "candidate increased or breached capital exposure")
                timestamp, symbol = row["timestamp"], row["symbol"]
                if (not isinstance(symbol, str) or not symbol or
                        not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool) or
                        not math.isfinite(timestamp) or not contract["holdout_start"] <= timestamp < contract["holdout_end"]):
                    return verdict("insufficient_evidence", "invalid instrument or holdout timestamp")
                bucket = grouped.setdefault(symbol, {})
                if timestamp in bucket:
                    return verdict("rejected", "duplicate timestamp in paired evaluation")
                bucket[timestamp] = row
            if len(grouped) < contract["min_instruments"] or any(len(v) < contract["min_bars"] for v in grouped.values()):
                return verdict("insufficient_evidence", "insufficient cross-instrument transfer observations")
            timelines = [set(v) for v in grouped.values()]
            if any(t != timelines[0] for t in timelines):
                return verdict("insufficient_evidence", "candidate and baseline timeline is not aligned")
            series = [([grouped[s][t]["baseline_net"] for s in grouped],
                       [grouped[s][t]["candidate_net"] for s in grouped]) for t in sorted(timelines[0])]
            baseline = [sum(b) / len(b) for b, _ in series]
            candidate = [sum(c) / len(c) for _, c in series]
            if any(r <= -1 for r in baseline + candidate):
                return verdict("rejected", "nonviable equity path")
            metrics_b = self._equity_metrics(baseline)
            metrics_c = self._equity_metrics(candidate)
            delta = {k: metrics_c[k] - metrics_b[k] for k in metrics_b}
            metrics = {f"baseline_{k}": v for k, v in metrics_b.items()}
            metrics.update({f"candidate_{k}": v for k, v in metrics_c.items()})
            instrument_delta = {
                symbol: self._equity_metrics([grouped[symbol][t]["candidate_net"] for t in sorted(timelines[0])])["net_return"]
                - self._equity_metrics([grouped[symbol][t]["baseline_net"] for t in sorted(timelines[0])])["net_return"]
                for symbol in grouped
            }
            metrics["instrument_net_advantage"] = instrument_delta
            if any(value < 0 for value in instrument_delta.values()):
                return verdict("rejected", "candidate regresses on a required instrument", metrics=metrics, delta=delta)
            if candidate == baseline:
                return verdict("rejected", "candidate produced no change", metrics=metrics, delta=delta)
            if (metrics_c["max_drawdown"] > contract["max_drawdown"] or
                    delta["max_drawdown"] > contract["max_drawdown_regression"] or
                    metrics_c["cvar_95"] > contract["max_cvar_95"]):
                return verdict("rejected", "drawdown or tail-risk limit breached", metrics=metrics, delta=delta)
            if delta["net_return"] < contract["minimum_net_gain"] or delta["cvar_95"] > 0:
                return verdict("rejected", "candidate lacks economic gain or is Pareto dominated", metrics=metrics, delta=delta)
            differences = [c - b for c, b in zip(candidate, baseline)]
            block = int(contract["block_size"])
            if len(differences) // block < 5:
                return verdict("insufficient_evidence", "insufficient effective block sample", metrics=metrics, delta=delta)
            rng = random.Random(int(hashlib.sha256(self._canonical(contract)).hexdigest()[:16], 16))
            n = len(differences)
            bootstrap = []
            for _ in range(512):
                draws = []
                while len(draws) < n:
                    start = rng.randrange(n)
                    draws.extend(differences[(start + j) % n] for j in range(block))
                bootstrap.append(sum(draws[:n]) / n)
            bootstrap.sort()
            alpha = (1 - contract["confidence"]) / report["trial_count"]
            lower = bootstrap[max(0, int(alpha * len(bootstrap)))]
            metrics["paired_mean_net_gain_lower_bound"] = lower
            if lower <= 0:
                return verdict("insufficient_evidence", "paired corrected lower confidence bound not positive", metrics=metrics, delta=delta)
            return verdict("eligible_for_operator_review", "independent offline evidence cleared declared gates; no deployment authorized", metrics=metrics, delta=delta)
        except (KeyError, TypeError, ValueError, IndexError, OverflowError):
            return verdict("insufficient_evidence", "malformed or incomplete verified evidence")
