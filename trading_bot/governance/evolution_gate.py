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

    def __init__(self, validation_engine: Any, improvement_threshold: float = 0.05):
        self.validation_engine = validation_engine
        self.threshold = improvement_threshold
        self.evolution_history = []

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any]) -> bool:
        """
        Gate: Only commit a rewrite if it improves on a held-out validation set.
        """
        logger.info(f"EvolutionGate: Validating candidate {candidate_id}")

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

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history
