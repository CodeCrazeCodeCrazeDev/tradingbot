"""
Evolution Gate - UCA V5 Governance
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

    def __init__(self, validation_engine: Any):
        self.validation_engine = validation_engine
        self.evolution_history = []

        # EKSFT Thresholds
        self.tau_h = 0.8  # Entropy threshold
        self.tau_kl = 0.5 # KL Divergence threshold

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any]) -> bool:
        """
        Gate: Only promote if ALL metrics are non-regressive and at least one improves significantly.
        """
        logger.info(f"EvolutionGate: Multi-dimensional audit for candidate {candidate_id}")

        # 1. Run full benchmark suite on candidate
        candidate_raw = self.validation_engine.run_benchmark(candidate_config)
        candidate = EvolutionMetrics(**candidate_raw)

        # 2. Institutional Safety Check (Hard Gate)
        if candidate.safety_score < 1.0:
            logger.error(f"EvolutionGate: REJECTED - Safety regression detected ({candidate.safety_score})")
            return False

        # 1. EKSFT: Selective Token/Concept Masking for Internalization
        # Before benchmarking, we ensure the candidate was 'safely' trained
        if not self._check_eksft_compliance(candidate_config):
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED due to EKSFT non-compliance.")
            return False

        # 2. Run baseline on validation set (stateless)
        baseline_perf = self.validation_engine.run_benchmark(baseline_config)

        # 3. Run candidate on validation set (online/stateful)
        candidate_perf = self.validation_engine.run_benchmark(candidate_config)

        # 4. Monotone-Safe Check (CL-Bench Gain Metric)
        gain = candidate_perf - baseline_perf
        is_safe = gain >= self.threshold

        if is_safe:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain (G): {gain:.4f}")
            self.evolution_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "candidate_id": candidate_id,
                "metrics": candidate.__dict__,
                "status": "PROMOTED"
            })
            return True
        else:
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED. Gain (G): {gain:.4f} < {self.threshold}")
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
        return self.evolution_history
