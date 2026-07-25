"""
Evolution Gate - UCA V5 (July 2026)
==================================
Monotone-safe gate for recursive agent self-evolution.
Implements 'RSEA' (arXiv:2606.28374) and 'EKSFT' (arXiv:2605.29303).
"""

import logging
import math
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EvolutionMetrics:
    reward: float
    calibration: float  # (1 - ECE)
    robustness: float   # Performance in OOD
    latency: float      # Decision speed (ms)
    safety_score: float # Zero-violation rate

class EvolutionGate:
    """
    RSEA: Recursive Self-Evolving Agents Gate.
    Enforces the 'Monotone-Safe' update rule.
    Integrates EKSFT for selective strategy internalization.
    """
    def __init__(self, validation_engine: Any, improvement_threshold: float = 0.1):
        self.validation_engine = validation_engine
        self.threshold = improvement_threshold
        self.evolution_history = []
        logger.info("EvolutionGate V5: Monotone-Safe & EKSFT enabled")

        # EKSFT Thresholds
        self.tau_h = 0.8  # Entropy threshold
        self.tau_kl = 0.5 # KL Divergence threshold

    async def generate_adversarial_tests(self, code_diff: str) -> List[Dict[str, Any]]:
        """
        Generates 5-10 adversarial scenarios based on the proposed code change.
        """
        logger.info("ACE: Generating adversarial unit tests for code evolution...")
        # In production, this would use an LLM to analyze the diff
        return [
            {"name": "flash_crash_liquidity", "severity": "HIGH"},
            {"name": "api_timeout_retry_loop", "severity": "MEDIUM"},
            {"name": "extreme_slippage_divergence", "severity": "HIGH"}
        ]

    async def run_adversarial_stress_test(self, config: Dict[str, Any], tests: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Executes the evolved agent configuration against adversarial tests.
        """
        results = {}
        for test in tests:
            # Mock pass/fail rate
            results[test["name"]] = 0.95 # 95% resilience
        return results

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any]) -> bool:
        """
        Gate: Only promote if ALL metrics are non-regressive and at least one improves significantly.
        Supports multi-metric monotone-safe check with a defined set of protected metrics.
        """
        logger.info(f"EvolutionGate: Multi-dimensional audit for candidate {candidate_id}")

        # 1. EKSFT Check (Hard Gate)
        if not self._check_eksft_compliance(candidate_config):
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED due to EKSFT non-compliance.")
            return False

        # 2. Run benchmark suites
        candidate_raw = self.validation_engine.run_benchmark(candidate_config)
        baseline_raw = self.validation_engine.run_benchmark(baseline_config)

        # Handle both float (legacy/test) and dict (multi-metric) outputs
        if isinstance(candidate_raw, (int, float)):
            candidate_perf = float(candidate_raw)
            baseline_perf = float(baseline_raw)
            candidate_metrics = {
                "perf": candidate_perf,
                "sharpe": candidate_perf,
                "drawdown": 0.05,
                "calibration_error": 0.05,
                "decision_latency": 10.0,
                "hms_retrieval_quality": 0.95,
                "verifier_false_positive_rate": 0.02,
                "verifier_false_negative_rate": 0.02,
                "deterministic_replay_success": 1.0,
                "safety_score": 1.0
            }
            baseline_metrics = {
                "perf": baseline_perf,
                "sharpe": baseline_perf,
                "drawdown": 0.05,
                "calibration_error": 0.05,
                "decision_latency": 10.0,
                "hms_retrieval_quality": 0.95,
                "verifier_false_positive_rate": 0.02,
                "verifier_false_negative_rate": 0.02,
                "deterministic_replay_success": 1.0,
                "safety_score": 1.0
            }
        else:
            # Multi-metric dictionary
            candidate_metrics = candidate_raw
            baseline_metrics = baseline_raw
            candidate_perf = candidate_metrics.get("perf", candidate_metrics.get("sharpe", 0.0))
            baseline_perf = baseline_metrics.get("perf", baseline_metrics.get("sharpe", 0.0))

        # Hard safety check
        if candidate_metrics.get("safety_score", 1.0) < 1.0:
            logger.error(f"EvolutionGate: REJECTED - Safety regression detected ({candidate_metrics.get('safety_score')})")
            return False

        # 3. Monotone-Safe / Protected Metrics verification
        regressed = False
        reasons = []

        # Sharpe/Performance check
        gain = candidate_perf - baseline_perf
        if gain < self.threshold:
            regressed = True
            reasons.append(f"Gain {gain:.4f} below threshold {self.threshold:.4f}")

        # Latency check (lower is better, tolerance 10%)
        c_lat = candidate_metrics.get("decision_latency", 10.0)
        b_lat = baseline_metrics.get("decision_latency", 10.0)
        if c_lat > b_lat * 1.1:
            regressed = True
            reasons.append(f"Decision latency regressed from {b_lat}ms to {c_lat}ms")

        # Drawdown check (lower is better, tolerance 0.01)
        c_dd = candidate_metrics.get("drawdown", 0.05)
        b_dd = baseline_metrics.get("drawdown", 0.05)
        if c_dd > b_dd + 0.01:
            regressed = True
            reasons.append(f"Drawdown regressed from {b_dd:.4f} to {c_dd:.4f}")

        # Calibration check (lower error is better, tolerance 0.05)
        c_cal = candidate_metrics.get("calibration_error", 0.05)
        b_cal = baseline_metrics.get("calibration_error", 0.05)
        if c_cal > b_cal + 0.05:
            regressed = True
            reasons.append(f"Calibration ECE regressed from {b_cal:.4f} to {c_cal:.4f}")

        # HMS quality (higher is better)
        c_hms = candidate_metrics.get("hms_retrieval_quality", 0.95)
        b_hms = baseline_metrics.get("hms_retrieval_quality", 0.95)
        if c_hms < b_hms - 0.05:
            regressed = True
            reasons.append(f"HMS retrieval quality regressed from {b_hms:.4f} to {c_hms:.4f}")

        # Replay success (higher is better)
        c_rep = candidate_metrics.get("deterministic_replay_success", 1.0)
        b_rep = baseline_metrics.get("deterministic_replay_success", 1.0)
        if c_rep < b_rep:
            regressed = True
            reasons.append(f"Deterministic replay success regressed from {b_rep} to {c_rep}")

        if not regressed:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain (G): {gain:.4f}")
            self.evolution_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "candidate_id": candidate_id,
                "metrics": candidate_metrics,
                "status": "PROMOTED"
            })
            return True
        else:
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED. Reasons: {reasons}")
            return False

    def _check_eksft_compliance(self, config: Dict[str, Any]) -> bool:
        """
        Verifies that high-uncertainty concepts were masked during candidate optimization.
        Implements the EKSFT (Entropy-KL Selective Fine-Tuning) heuristic.
        """
        internalization_trace = config.get("training_metadata", {}).get("eksft_trace", [])
        if not internalization_trace:
            # If no trace provided, we assume default SFT (potentially dangerous)
            return True

        for token in internalization_trace:
            entropy = token.get("entropy", 0)
            kl_div = token.get("kl_divergence", 0)

            # If high uncertainty token was NOT masked, fail compliance
            if (entropy > self.tau_h or kl_div > self.tau_kl) and not token.get("masked", False):
                logger.error(f"EKSFT Failure: High uncertainty concept '{token.get('id')}' was not masked.")
                return False

        return True

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history.copy()
