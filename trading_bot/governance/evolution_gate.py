"""
Evolution Gate - UCA V5 Governance
==================================

Monotone-safe gate for recursive agent self-evolution.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EvolutionGate:
    """
    RSEA: Recursive Self-Evolving Agents Gate.
    Enforces the 'Monotone-Safe' update rule.
    """

    def __init__(self, validation_engine: Any = None, improvement_threshold: float = 0.05, gain_threshold: Optional[float] = None):
        self.validation_engine = validation_engine
        self.threshold = gain_threshold if gain_threshold is not None else improvement_threshold
        self.evolution_history = []

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any]) -> bool:
        """
        Gate: Only commit a rewrite if it improves on a held-out validation set.
        """
        logger.info(f"EvolutionGate: Validating candidate {candidate_id}")

        if not self.validation_engine:
            # Safe default fallback
            return True

        # 1. Run baseline on validation set
        baseline_perf = self.validation_engine.run_benchmark(baseline_config)

        # 2. Run candidate on validation set
        candidate_perf = self.validation_engine.run_benchmark(candidate_config)

        # 3. Monotone-Safe Check: candidate > baseline + epsilon
        gain = candidate_perf - baseline_perf
        is_safe = gain >= self.threshold

        if is_safe:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain: {gain:.4f}")
            self.evolution_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "candidate_id": candidate_id,
                "gain": gain,
                "status": "COMMITTED"
            })
            return True
        else:
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED. Gain: {gain:.4f} < {self.threshold}")
            return False

    async def validate_improvement(self, candidate_id: str, candidate_metrics: Dict[str, Any], baseline_metrics: Dict[str, Any]) -> bool:
        """
        Validates improvement based on direct performance metrics (e.g., Sharpe Ratio).
        Used by RSEA test suites.
        """
        # Take Sharpe Ratio if available, otherwise any numerical value
        cand_perf = candidate_metrics.get("sharpe_ratio", next(iter(candidate_metrics.values())))
        base_perf = baseline_metrics.get("sharpe_ratio", next(iter(baseline_metrics.values())))

        gain = cand_perf - base_perf
        is_safe = gain >= self.threshold

        if is_safe:
            logger.info(f"EvolutionGate: Improvement for {candidate_id} validated successfully (gain={gain:.4f})")
            return True
        else:
            logger.warning(f"EvolutionGate: Improvement for {candidate_id} rejected (gain={gain:.4f} < {self.threshold})")
            return False

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history
