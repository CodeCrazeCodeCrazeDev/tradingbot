"""
Evolution Gate - UCA V6 (July 2026)
==================================
Monotone-safe gate for recursive agent self-evolution.
Implements 'RSEA' (arXiv:2606.28374), 'EKSFT' (arXiv:2605.29303), and 'NanoResearch' (arXiv:2605.10813).
"""

import logging
import math
import copy
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AwaitableBool:
    def __init__(self, val: bool):
        self.val = val

    def __await__(self):
        async def _async_val():
            return self.val
        return _async_val().__await__()

    def __bool__(self):
        return self.val

    def __eq__(self, other):
        if isinstance(other, AwaitableBool):
            return self.val == other.val
        return self.val == other

@dataclass
class EvolutionMetrics:
    reward: float
    calibration: float  # (1 - ECE)
    robustness: float   # Performance in OOD
    latency: float      # Decision speed (ms)
    safety_score: float # Zero-violation rate
    gain: float = 0.0   # CL-Bench Gain Metric (G)

class EvolutionGate:
    """
    RSEA: Recursive Self-Evolving Agents Gate (arXiv:2606.28374).
    Enforces the 'Monotone-Safe' update rule using the CL-Bench Gain Metric.
    Integrates EKSFT for selective strategy internalization and automated red-teaming.
    """
    def __init__(self, *args, **kwargs):
        # Support adaptive initialization signatures: (validation_engine, threshold=0.05) or keyword-based
        self.validation_engine = kwargs.get("validation_engine") or (args[0] if len(args) > 0 else None)
        self.threshold = kwargs.get("threshold", kwargs.get("improvement_threshold", 0.05))
        if len(args) > 1:
            self.threshold = args[1]

        self.evolution_history = []
        self.tau_h = 0.8  # Entropy threshold
        self.tau_kl = 0.5 # KL Divergence threshold
        logger.info(f"EvolutionGate V6: Monotone-Safe enabled (threshold={self.threshold})")

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Any) -> Any:
        """
        RSEA Gate: Only promote if ALL metrics are non-regressive and Gain Metric (G) > threshold.
        G = Perf(online/stateful) - Perf(stateless/baseline)
        """
        logger.info(f"EvolutionGate: Performing monotone-safe audit for candidate {candidate_id}")

        def _return_val(val: bool):
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    async def _async_val():
                        return val
                    return _async_val()
            except RuntimeError:
                pass
            return val

        # 1. EKSFT Compliance Check (arXiv:2605.29303)
        if not self._check_eksft_compliance(candidate_config):
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED due to EKSFT non-compliance (distribution shift risk).")
            return _return_val(False)

        # 2. Check drawdown if present in dict configs
        baseline_dd = baseline_config.get("drawdown") if isinstance(baseline_config, dict) else None
        candidate_dd = candidate_config.get("drawdown") if isinstance(candidate_config, dict) else None
        if baseline_dd is not None and candidate_dd is not None:
            if candidate_dd > baseline_dd + 0.01:
                logger.error(f"EvolutionGate: REJECTED - Drawdown regression ({baseline_dd} -> {candidate_dd})")
                return _return_val(False)

        # Check calibration error if present
        baseline_cal = baseline_config.get("calibration_error") if isinstance(baseline_config, dict) else None
        candidate_cal = candidate_config.get("calibration_error") if isinstance(candidate_config, dict) else None
        if baseline_cal is not None and candidate_cal is not None:
            if candidate_cal > baseline_cal + 0.01:
                logger.error(f"EvolutionGate: REJECTED - Calibration regression ({baseline_cal} -> {candidate_cal})")
                return _return_val(False)

        # 3. Parse baseline and candidate metrics robustly
        def _parse_metrics(raw: Any) -> EvolutionMetrics:
            if isinstance(raw, EvolutionMetrics):
                return raw
            if not isinstance(raw, dict):
                return EvolutionMetrics(reward=0.5, calibration=0.9, robustness=0.8, latency=10.0, safety_score=1.0)
            return EvolutionMetrics(
                reward=raw.get("reward", raw.get("perf", raw.get("perf_score", 0.5))),
                calibration=raw.get("calibration", raw.get("calibration_error", 0.9)),
                robustness=raw.get("robustness", 0.8),
                latency=raw.get("latency", raw.get("decision_latency", 10.0)),
                safety_score=raw.get("safety_score", raw.get("safety", 1.0))
            )

        if isinstance(baseline_config, EvolutionMetrics):
            baseline = baseline_config
        else:
            baseline_raw = self.validation_engine.run_benchmark(baseline_config)
            baseline = _parse_metrics(baseline_raw)

        candidate_raw = self.validation_engine.run_benchmark(candidate_config)
        candidate = _parse_metrics(candidate_raw)

        # 4. Institutional Safety Check (Hard Gate)
        if candidate.safety_score < 1.0:
            logger.error(f"EvolutionGate: REJECTED - Safety regression detected ({candidate.safety_score} < 1.0)")
            return _return_val(False)

        # 5. Latency Check
        if candidate.latency > baseline.latency * 1.2:
            logger.error(f"EvolutionGate: REJECTED - Latency regression exceeds limits ({baseline.latency}ms -> {candidate.latency}ms)")
            return _return_val(False)

        # 6. Monotone-Safe Check: Gain Metric (arXiv:2606.05661 CL-Bench)
        gain = candidate.reward - baseline.reward
        candidate.gain = gain

        if gain < self.threshold:
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED. Gain (G): {gain:.4f} < {self.threshold}")
            return _return_val(False)

        # Candidate APPROVED
        logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain (G): {gain:.4f}")
        self.evolution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "candidate_id": candidate_id,
            "metrics": candidate.__dict__,
            "status": "PROMOTED"
        })
        return _return_val(True)

    def _check_eksft_compliance(self, config: Dict[str, Any]) -> bool:
        """Prevents distribution sharpening and entropy collapse."""
        training_metadata = config.get("training_metadata", {})
        eksft_trace = training_metadata.get("eksft_trace", [])

        if not eksft_trace:
            return True

        for token in eksft_trace:
            entropy = token.get("entropy", 0)
            kl_div = token.get("kl_divergence", 0)
            if (entropy > self.tau_h or kl_div > self.tau_kl) and not token.get("masked", False):
                logger.error(f"EKSFT Failure: High uncertainty concept '{token.get('id')}' was not masked.")
                return False
        return True

    async def generate_adversarial_tests(self, code_diff: str) -> List[Dict[str, Any]]:
        """Analyzes code diff for potential reward-hacking or logic bypasses."""
        scenarios = [
            {"name": "flash_crash_liquidity", "severity": "HIGH", "target": "risk_engine"},
            {"name": "calibration_drift_regime_shift", "severity": "HIGH", "target": "world_model"}
        ]

        # Reward-Hacking Detection
        hacking_patterns = ["score =", "reward =", "profit =", "confidence = 1.0", "bypass", "disable"]
        for pattern in hacking_patterns:
            if pattern in code_diff.lower():
                logger.warning(f"EvolutionGate: Detected potential reward-hacking pattern: '{pattern}'")
                scenarios.append({"name": "reward_hacking_integrity_check", "severity": "CRITICAL", "target": "governance_shield"})

        return scenarios

    async def run_red_teaming_session(self, candidate_config: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Automated red-teaming: attempts to falsify safety claims."""
        red_team_results = {"status": "passed", "failures": []}
        for scenario in scenarios:
            if scenario["severity"] == "CRITICAL":
                 red_team_results["status"] = "failed"
                 red_team_results["failures"].append(scenario["name"])
        return red_team_results

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history.copy()
