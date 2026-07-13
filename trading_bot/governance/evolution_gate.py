"""
Evolution Gate - UCA V5 Governance
==================================

Monotone-safe gate for recursive agent self-evolution.
Implements EKSFT (Entropy-KL Selective Fine-Tuning) and RSEA principles.
"""

import logging
import math
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EvolutionGate:
    """
    RSEA: Recursive Self-Evolving Agents Gate.
    Enforces the 'Monotone-Safe' update rule and EKSFT masking.
    """

    def __init__(self, validation_engine: Any = None, improvement_threshold: float = 0.05):
        self.validation_engine = validation_engine
        self.threshold = improvement_threshold
        self.evolution_history = []
        logger.info("EvolutionGate V5: Monotone-Safe & EKSFT enabled")

    def validate_evolution(self, candidate_id: str, candidate_config: Dict[str, Any], baseline_config: Dict[str, Any]) -> bool:
        """
        Gate: Only commit a rewrite if it improves on a held-out validation set.
        Implements Monotone-Safe Contraction Mapping.
        """
        logger.info(f"EvolutionGate: Validating candidate {candidate_id}")

        if not self.validation_engine:
            logger.warning("No validation engine available. Defaulting to REJECT for safety.")
            return False

        # 1. Run baseline on validation set
        baseline_perf = self.validation_engine.run_benchmark(baseline_config)

        # 2. Run candidate on validation set
        candidate_perf = self.validation_engine.run_benchmark(candidate_config)

        # 3. Monotone-Safe Check: candidate > baseline + epsilon
        # Ensures genuine improvement (arXiv:2606.28374)
        gain = candidate_perf - baseline_perf
        is_safe = gain >= self.threshold

        if is_safe:
            logger.info(f"EvolutionGate: Candidate {candidate_id} APPROVED. Gain: {gain:.4f}")
            self._log_evolution(candidate_id, gain, "COMMITTED")
            return True
        else:
            logger.warning(f"EvolutionGate: Candidate {candidate_id} REJECTED. Gain: {gain:.4f} < {self.threshold}")
            self._log_evolution(candidate_id, gain, "REJECTED")
            return False

    def apply_eksft_masking(self, tokens: List[str], entropy_scores: List[float], kl_divergence: List[float],
                           tau_h: float = 2.0, tau_kl: float = 0.5) -> List[int]:
        """
        EKSFT (Entropy-KL Selective Fine-Tuning): Identify tokens to mask.
        arXiv:2605.29303
        """
        masks = []
        for h, kl in zip(entropy_scores, kl_divergence):
            # Mask if high uncertainty OR high distribution shift
            if h > tau_h or kl > tau_kl:
                masks.append(1) # Masked
            else:
                masks.append(0) # Unmasked

        logger.debug(f"EKSFT: Masked {sum(masks)}/{len(tokens)} tokens")
        return masks

    def _log_evolution(self, candidate_id: str, gain: float, status: str):
        self.evolution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "candidate_id": candidate_id,
            "gain": gain,
            "status": status
        })

    def get_evolution_report(self) -> List[Dict[str, Any]]:
        return self.evolution_history.copy()
