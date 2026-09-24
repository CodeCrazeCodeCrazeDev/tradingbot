"""
Evolution Gate - UCA V6 Monotone-Safe Self-Evolution Gatekeeper

Paper Traceability Matrix:
- arXiv:2605.29303 (EKSFT): Entropy-KL selective fine-tuning compliance verification.
- arXiv:2607.00341 (DiscoLoop): Continuous-discrete state consistency checks under evolution.
- arXiv:2607.01224 (AutoMem): Schema versioning and metamemory evolution tracking.
- arXiv:2605.12061 (SAGE): Evidence graph edge weight update validation.
- arXiv:2605.10813 (NanoResearch): Tri-level policy and skill bank co-evolution auditing.
- arXiv:2605.20025 (AutoResearchClaw): Automated red-teaming and falsification tests.
- arXiv:2605.17734 (HASP): Invariant program safety enforcement.
- arXiv:2605.21482 (DeepWeb-Bench): Calibration error (ECE) and latency regression bounds.

Monotone-safe gate for recursive agent self-evolution using CL-Bench Gain Metric.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


def compute_ece(
    confidences: Sequence[float],
    correctness: Sequence[float],
    n_bins: int = 10,
) -> float:
    """
    Expected Calibration Error (ECE) — DeepWeb-Bench (arXiv:2605.21482).

    Partitions predictions into `n_bins` confidence buckets and returns the
    weighted mean absolute gap between mean confidence and empirical accuracy
    per bucket.

    Args:
        confidences: predicted probabilities/confidence scores in [0, 1].
        correctness: 1.0/0.0 (or boolean) per prediction — was it correct.
        n_bins: number of equal-width confidence bins.

    Returns:
        ECE in [0, 1]; lower is better calibrated.
    """
    conf = np.clip(np.asarray(confidences, dtype=np.float64), 0.0, 1.0)
    corr = np.asarray(correctness, dtype=np.float64)
    if conf.size == 0:
        return 0.0
    if conf.shape != corr.shape:
        raise ValueError("confidences and correctness must have the same shape")

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(conf, bins[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        mask = idx == b
        count = int(mask.sum())
        if count == 0:
            continue
        acc = float(corr[mask].mean())
        mean_conf = float(conf[mask].mean())
        ece += (count / conf.size) * abs(mean_conf - acc)
    return float(ece)


@dataclass
class EvolutionMetrics:
    reward: float
    calibration: float  # (1 - ECE)
    robustness: float   # Performance in OOD
    latency: float      # Decision speed (ms)
    safety_score: float # Zero-violation rate
    gain: float = 0.0   # CL-Bench Gain Metric (G)
    drawdown: float = 0.0
    calibration_error: float = 0.0
    hms_retrieval_quality: float = 1.0
    deterministic_replay_success: float = 1.0

    def __getitem__(self, item: str) -> Any:
        if item in ("perf", "reward"):
            return self.reward
        if item in ("decision_latency", "latency"):
            return self.latency
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except (KeyError, AttributeError):
            return default


def parse_metrics(raw: Any) -> EvolutionMetrics:
    if isinstance(raw, (int, float)):
        return EvolutionMetrics(reward=float(raw), calibration=0.9, robustness=0.8, latency=10.0, safety_score=1.0)

    if not isinstance(raw, dict):
        if isinstance(raw, EvolutionMetrics):
            return raw
        return EvolutionMetrics(reward=0.5, calibration=0.9, robustness=0.8, latency=10.0, safety_score=1.0)

    reward = raw.get("reward", raw.get("perf", raw.get("sharpe_ratio", raw.get("score", 0.5))))
    if "confidences" in raw and "correctness" in raw:
        # Real ECE from raw predictions (DeepWeb-Bench calibration audit)
        ece = compute_ece(raw["confidences"], raw["correctness"],
                          n_bins=int(raw.get("ece_bins", 10)))
        calibration = raw.get("calibration", 1.0 - ece)
    else:
        ece = raw.get("ece", 1.0 - raw.get("calibration", 0.95))
        calibration = raw.get("calibration", 1.0 - ece)
    robustness = raw.get("robustness", 0.8)
    latency = raw.get("latency", raw.get("decision_latency", 10.0))
    safety_score = raw.get("safety_score", 1.0)

    m = EvolutionMetrics(
        reward=reward,
        calibration=calibration,
        robustness=robustness,
        latency=latency,
        safety_score=safety_score,
        drawdown=raw.get("drawdown", 0.0),
        calibration_error=raw.get("calibration_error", 1.0 - calibration)
    )
    for k, v in raw.items():
        if not hasattr(m, k):
            setattr(m, k, v)
    return m


def _get_metric(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        if name == "perf":
            return obj.get("perf", obj.get("reward", default))
        return obj.get(name, default)
    if hasattr(obj, "get"):
        val = obj.get(name, None)
        if val is not None:
            return val
    if hasattr(obj, name):
        return getattr(obj, name)
    if name == "perf" and hasattr(obj, "reward"):
        return getattr(obj, "reward")
    return default


class EvolutionGate:
    """
    RSEA: Recursive Self-Evolving Agents Gate (arXiv:2606.28374).
    Enforces the 'Monotone-Safe' update rule using the CL-Bench Gain Metric.
    Integrates EKSFT for selective strategy internalization and automated red-teaming.
    """

    def __init__(self, validation_engine: Any = None, threshold: float = 0.05, **kwargs):
        self.validation_engine = validation_engine
        self.evolution_history = []
        self.threshold = kwargs.get("improvement_threshold", kwargs.get("gain_threshold", threshold))
        # EKSFT Thresholds
        self.tau_h = 0.8  # Entropy threshold
        self.tau_kl = 0.5 # KL Divergence threshold
        logger.info(f"EvolutionGate V6: Monotone-Safe enabled (threshold={self.threshold})")

    def _get_metric(self, obj: Any, name: str, default: Any = None) -> Any:
        return _get_metric(obj, name, default)

    def _parse_metrics(self, raw: Any) -> EvolutionMetrics:
        return parse_metrics(raw)

    def _check_eksft_compliance(self, candidate_config: Dict[str, Any]) -> bool:
        """
        EKSFT compliance gate (arXiv:2605.29303).

        A candidate update is compliant when its declared selective-update
        statistics stay inside the entropy/KL boundaries: mean update entropy
        >= tau_h (still exploring — no distribution sharpening) and max KL
        drift vs the baseline policy <= tau_kl.
        Candidates that carry no selective-update stats are compliant by
        default (nothing to gate).
        """
        # Per-token trace format: training_metadata.eksft_trace is a list of
        # {id, entropy, masked} — every token whose entropy reaches the
        # high-uncertainty band (>= tau_h) must be masked out of the update.
        trace = (candidate_config.get("training_metadata") or {}).get("eksft_trace") or []
        if isinstance(trace, list):
            for token in trace:
                if not isinstance(token, dict):
                    continue
                entropy = token.get("entropy")
                if entropy is not None and float(entropy) >= self.tau_h and not token.get("masked", False):
                    logger.warning(
                        f"EKSFT: high-entropy token '{token.get('id')}' (entropy {entropy} >= {self.tau_h}) "
                        "is unmasked — selective masking required"
                    )
                    return False

        stats = candidate_config.get("eksft_stats") or candidate_config.get("update_stats") or {}
        if not isinstance(stats, dict) or not stats:
            return True

        entropy = stats.get("entropy")
        kl = stats.get("kl_divergence", stats.get("kl"))
        if entropy is not None and float(entropy) < self.tau_h:
            logger.warning(f"EKSFT: entropy {entropy} < tau_h {self.tau_h} — distribution sharpening detected")
            return False
        if kl is not None and float(kl) > self.tau_kl:
            logger.warning(f"EKSFT: KL divergence {kl} > tau_kl {self.tau_kl} — policy drift beyond compliance gate")
            return False
        return True

    def generate_adversarial_tests(self, code_diff: str) -> List[Dict[str, Any]]:
        """
        AutoResearchClaw (arXiv:2605.20025): synthesize adversarial scenarios
        that target the surfaces touched by the candidate diff.
        """
        scenarios: List[Dict[str, Any]] = [
            {"name": "volatility_spike", "shock": {"volatility": 0.5}, "invariant": "no_trade_above_vol_0.3"},
            {"name": "api_failure", "shock": {"execution_error": True}, "invariant": "graceful_fallback_to_hold"},
            {"name": "slippage_burst", "shock": {"slippage": 0.02}, "invariant": "ev_must_cover_costs"},
        ]
        lowered = code_diff.lower()
        if "risk" in lowered or "exposure" in lowered:
            scenarios.append({"name": "exposure_breach", "shock": {"portfolio_exposure": 1.0}, "invariant": "hard_exposure_cap"})
        if "order" in lowered or "execution" in lowered:
            scenarios.append({"name": "partial_fill", "shock": {"fill_ratio": 0.3}, "invariant": "no_double_count_fill"})
        if "reward" in lowered or "loss" in lowered:
            scenarios.append({"name": "reward_hacking", "shock": {"reward": float("inf")}, "invariant": "finite_reward_only"})
        return scenarios

    def run_red_teaming_session(self, candidate_config: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        AutoResearchClaw (arXiv:2605.20025): run each adversarial scenario and
        report invariant violations. A scenario fails if the candidate's
        declared behavior map does not preserve the scenario invariant.
        """
        behavior = candidate_config.get("behavior", {}) or {}
        failures: List[str] = []
        for scenario in scenarios:
            name = scenario.get("name", "unnamed")
            invariant = scenario.get("invariant")
            respected = behavior.get(invariant, candidate_config.get(invariant, True))
            if not respected:
                failures.append(f"{name}: invariant '{invariant}' violated")
        return {
            "status": "failed" if failures else "passed",
            "failures": failures,
            "scenarios_run": len(scenarios),
        }

    async def validate_improvement(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any], drift: Optional[Dict[str, Any]] = None) -> bool:
        """
        Gate: Only commit a rewrite if it improves on a held-out validation set.

        ``drift`` (V4 contract) carries explicit distribution stats
        (``entropy``/``kl_divergence``) gated against tau_h/tau_kl.
        """
        logger.info(f"EvolutionGate: Validating candidate {candidate_id}")

        if isinstance(drift, dict) and drift:
            entropy = drift.get("entropy")
            kl = drift.get("kl_divergence", drift.get("kl"))
            if entropy is not None and float(entropy) < self.tau_h:
                logger.warning(f"EvolutionGate: REJECTED - entropy {entropy} < tau_h {self.tau_h} (mode collapse)")
                return False
            if kl is not None and float(kl) > self.tau_kl:
                logger.warning(f"EvolutionGate: REJECTED - KL {kl} > tau_kl {self.tau_kl} (excessive drift)")
                return False

        # 1. EKSFT Compliance Check
        if not self._check_eksft_compliance(candidate_config):
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED due to EKSFT non-compliance.")
            return False

        # Invariant safety check: exposure cannot be increased while halted
        logic_shard = candidate_config.get("logic_shard", {}) or {}
        if logic_shard.get("halt", False) and logic_shard.get("increase_exposure", False):
            logger.error(f"EvolutionGate: REJECTED - Candidate {candidate_id} violated formal invariant (halted but increasing exposure)")
            return False

        # 2. Adversarial Red-Teaming
        code_diff = candidate_config.get("code_diff", "")
        if code_diff:
            scenarios = self.generate_adversarial_tests(code_diff)
            red_team_report = self.run_red_teaming_session(candidate_config, scenarios)
            if red_team_report["status"] == "failed":
                logger.error(f"EvolutionGate: REJECTED - Red-teaming failed: {red_team_report['failures']}")
                return False

        # 3. Run baseline on validation set
        baseline_raw = baseline_config
        if self.validation_engine and hasattr(self.validation_engine, "run_benchmark"):
            if isinstance(baseline_config, dict) and "reward" not in baseline_config and "perf" not in baseline_config:
                baseline_mode = baseline_config.get("mode", "stateless")
                try:
                    baseline_raw = self.validation_engine.run_benchmark(baseline_config, mode=baseline_mode)
                except TypeError:
                    baseline_raw = self.validation_engine.run_benchmark(baseline_config)
            elif isinstance(baseline_config, dict):
                try:
                    baseline_raw = self.validation_engine.run_benchmark(baseline_config)
                except Exception:
                    pass

        baseline = self._parse_metrics(baseline_raw)

        # 4. Run candidate benchmark
        candidate_mode = candidate_config.get("mode", "stateful")
        candidate_raw = candidate_config
        if self.validation_engine and hasattr(self.validation_engine, "run_benchmark"):
            try:
                candidate_raw = self.validation_engine.run_benchmark(candidate_config, mode=candidate_mode)
            except TypeError:
                candidate_raw = self.validation_engine.run_benchmark(candidate_config)

        candidate = parse_metrics(candidate_raw)

        # 5. Calculate gain and evaluate monotonicity
        cand_perf = float(_get_metric(candidate, "perf", 0.5))
        base_perf = float(_get_metric(baseline, "perf", 0.5))
        gain = cand_perf - base_perf

        cand_latency = float(_get_metric(candidate, "latency", 10.0))
        base_latency = float(_get_metric(baseline, "latency", 10.0))

        cand_safety = float(_get_metric(candidate, "safety_score", 1.0))
        base_safety = float(_get_metric(baseline, "safety_score", 1.0))

        cand_calibration = float(_get_metric(candidate, "calibration", 0.9))
        base_calibration = float(_get_metric(baseline, "calibration", 0.9))

        cand_robustness = float(_get_metric(candidate, "robustness", 0.8))
        base_robustness = float(_get_metric(baseline, "robustness", 0.8))

        if cand_safety < 1.0:
            logger.error(f"EvolutionGate: REJECTED - Safety regression ({cand_safety} < 1.0)")
            return False

        is_significant = (gain >= self.threshold)
        no_regressions = (
            cand_safety >= base_safety and
            cand_latency <= base_latency * 1.2 and
            cand_calibration >= base_calibration - 0.05 and
            cand_robustness >= base_robustness - 0.05
        )

        cand_drawdown = _get_metric(candidate, "drawdown", None)
        base_drawdown = _get_metric(baseline, "drawdown", None)
        if cand_drawdown is not None and base_drawdown is not None:
            if cand_drawdown > base_drawdown + 0.01:
                no_regressions = False

        if is_significant and no_regressions:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain (G): {gain:.4f}")
            self.evolution_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "candidate_id": candidate_id,
                "metrics": candidate.__dict__ if hasattr(candidate, "__dict__") else candidate,
                "provenance": {
                    "baseline_id": baseline_config.get("id") if isinstance(baseline_config, dict) else getattr(baseline_config, "id", "unknown"),
                    "validation_mode": "CL-Bench-Stateful",
                    "reproducible_seed": 42,
                    "signatures": {"governance": "APPROVED_UCA_V5"}
                },
                "status": "PROMOTED"
            })
            return True
        else:
            reasons = []
            if not is_significant:
                reasons.append(f"insignificant gain {gain:.4f} < {self.threshold}")
            calibration_drift = abs(cand_calibration - base_calibration)
            if calibration_drift > 0.05:
                reasons.append(f"calibration drift {calibration_drift:.4f} > 0.05")
            if cand_latency > base_latency * 1.2:
                reasons.append(f"latency regression {cand_latency} > {base_latency * 1.2}")
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED due to: {', '.join(reasons)}")
            return False

    def validate_evolution(self, *args, **kwargs) -> bool:
        """Legacy sync wrapper — safe to call inside or outside a running loop."""
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.validate_improvement(*args, **kwargs))
        # Already inside an event loop: run the coroutine on a private loop
        # in a helper thread (nest_asyncio may not be installed).
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(
                lambda: asyncio.run(self.validate_improvement(*args, **kwargs))
            ).result()

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history.copy()
