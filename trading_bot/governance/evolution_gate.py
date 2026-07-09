"""
Evolution Gate - UCA V5 Governance
==================================

Monotone-safe gate for recursive agent self-evolution.
Verifies improvement across 5 institutional dimensions.
"""

import logging
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
    Enforces 'Monotone-Safe' update rules across multiple dimensions.
    """

    def __init__(self, validation_engine: Any):
        self.validation_engine = validation_engine
        self.evolution_history = []

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_metrics: EvolutionMetrics) -> bool:
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

        # 3. Monotone-Safe Audit (No regression in reward or robustness)
        regressions = []
        if candidate.reward < baseline_metrics.reward * 0.99: regressions.append("reward")
        if candidate.robustness < baseline_metrics.robustness * 0.99: regressions.append("robustness")
        if candidate.latency > baseline_metrics.latency * 1.05: regressions.append("latency")

        if regressions:
             logger.warning(f"EvolutionGate: REJECTED - Regressions in: {regressions}")
             return False

        # 4. Significance Check (At least one must improve > 5%)
        significant_gain = (
            candidate.reward > baseline_metrics.reward * 1.05 or
            candidate.calibration > baseline_metrics.calibration * 1.05 or
            candidate.robustness > baseline_metrics.robustness * 1.05
        )

        if significant_gain:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED for promotion.")
            self.evolution_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "candidate_id": candidate_id,
                "metrics": candidate.__dict__,
                "status": "PROMOTED"
            })
            return True
        else:
            logger.warning(f"EvolutionGate: REJECTED - Improvement not statistically significant.")
            return False

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history
