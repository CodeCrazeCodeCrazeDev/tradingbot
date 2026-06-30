"""
Improvement Gatekeeper - Phase 3 Safety Architecture
Deterministic validation of all autonomous system upgrades.
"""

import logging
from typing import Any, Dict, List, Optional
from .registry import ImprovementRecord

logger = logging.getLogger(__name__)

class ImprovementGatekeeper:
    """
    Enforces quality gates before any 'keep' decision is finalized.
    """
    def __init__(self, max_complexity: int = 15, min_fitness_gain: float = 0.05):
        self.max_complexity = max_complexity
        self.min_fitness_gain = min_fitness_gain

    async def validate_improvement(self, record: ImprovementRecord) -> bool:
        """
        Runs a suite of checks on the improvement record.
        Returns True if the improvement is safe and performant.
        """
        logger.info(f"Gatekeeper validating improvement: {record.change_id}")

        # 1. Performance Check
        gain = self._calculate_gain(record.metrics_before, record.metrics_after)
        if gain < self.min_fitness_gain and record.result != "reject":
            logger.warning(f"Rejecting {record.change_id}: Insufficient gain ({gain:.2%})")
            return False

        # 2. Complexity Check
        complexity = record.metrics_after.get("complexity", 0)
        if complexity > self.max_complexity:
            logger.warning(f"Rejecting {record.change_id}: Complexity threshold exceeded ({complexity})")
            return False

        # 3. Layer Specific Validation
        if record.layer == "Architecture":
            if record.metrics_after.get("latency", 0) > record.metrics_before.get("latency", 100) * 1.2:
                logger.warning(f"Rejecting {record.change_id}: Latency degradation too high")
                return False

        logger.info(f"✅ Improvement {record.change_id} passed all gates.")
        return True

    def _calculate_gain(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        # Simplified gain calculation
        b = before.get("sharpe", before.get("accuracy", 1.0))
        a = after.get("sharpe", after.get("accuracy", 1.0))
        return (a - b) / (abs(b) + 1e-6)
