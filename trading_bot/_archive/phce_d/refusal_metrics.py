"""
PHCE-D Module 12: Refusal and Abstention Quality Metrics

P0 #8: The system's main job is refusing bad trades, so measure refusal quality.
Without this, NO_TRADE can become lazy over-filtering.

Metrics:
- Refusal precision: rejected trades that would have lost
- Refusal recall: losing trades correctly rejected
- False abstention rate: rejected trades that would have won
- Abstention cost: opportunity cost from missed winners
- Needs-more-evidence resolution rate: how often uncertainty later resolves cleanly
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

from .core_types import (
    DecisionAuditRecord,
    DecisionOutput,
    RefusalMetrics,
)

logger = logging.getLogger(__name__)


@dataclass
class OutcomeObservation:
    """Record of an actual outcome for a decision that was made or refused."""
    decision_id: str
    phce_d_output: DecisionOutput
    actual_return_bps: float  # Realized return in bps (positive = win)
    would_have_won: bool  # If PHCE-D refused, would the trade have won?
    timestamp: float


class RefusalQualityTracker:
    """
    Module 12: Refusal and Abstention Quality Metrics

    Measures whether the system's refusals are correct or lazy over-filtering.

    Key insight: NO_TRADE can become lazy over-filtering if not measured.
    The system must demonstrate that its refusals are precision-targeted,
    not just safe conservatism.

    Metrics:
    - Refusal precision: Of rejected/refused trades, how many would have lost?
    - Refusal recall: Of all losing trades, how many did we correctly reject?
    - False abstention rate: Of rejected trades, how many would have won?
    - Abstention cost: Opportunity cost from missed winners
    - Needs-more-evidence resolution rate: How often does NEEDS_MORE_EVIDENCE
      later resolve to a clear action?
    """

    def __init__(
        self,
        window_size: int = 200,
        winning_threshold_bps: float = 0.0,  # >0 means trade was profitable
    ):
        self.window_size = window_size
        self.winning_threshold = winning_threshold_bps

        # Rolling observations
        self._observations: Deque[OutcomeObservation] = deque(maxlen=window_size)

        # Needs-more-evidence tracking
        self._nme_decisions: Dict[str, Dict[str, Any]] = {}  # decision_id → tracking
        self._nme_resolutions: Deque[bool] = deque(maxlen=100)

        # Statistics
        self.total_observations = 0
        self.total_refusals = 0
        self.total_approvals = 0

    def record_outcome(
        self,
        decision_id: str,
        phce_d_output: DecisionOutput,
        actual_return_bps: float,
        timestamp: Optional[float] = None,
    ) -> RefusalMetrics:
        """
        Record the actual outcome of a decision for quality tracking.

        Args:
            decision_id: The PHCE-D decision ID
            phce_d_output: What PHCE-D decided
            actual_return_bps: What actually happened (in bps)
            timestamp: When the outcome was observed

        Returns:
            Updated RefusalMetrics
        """
        timestamp = timestamp or time.time()
        would_have_won = actual_return_bps > self.winning_threshold

        obs = OutcomeObservation(
            decision_id=decision_id,
            phce_d_output=phce_d_output,
            actual_return_bps=actual_return_bps,
            would_have_won=would_have_won,
            timestamp=timestamp,
        )
        self._observations.append(obs)
        self.total_observations += 1

        if phce_d_output in DecisionOutput.abstention():
            self.total_refusals += 1
        else:
            self.total_approvals += 1

        return self.compute_metrics()

    def record_nme_resolution(
        self,
        original_decision_id: str,
        resolved_output: DecisionOutput,
    ) -> None:
        """
        Record that a NEEDS_MORE_EVIDENCE decision later resolved.

        Clean resolution = resolved to a clear action (BUY/SELL/REJECTED)
        Unclean resolution = resolved to another ambiguous state
        """
        clean_resolutions = {DecisionOutput.BUY, DecisionOutput.SELL,
                             DecisionOutput.REJECTED, DecisionOutput.NO_TRADE}
        resolved_cleanly = resolved_output in clean_resolutions
        self._nme_resolutions.append(resolved_cleanly)

    def compute_metrics(self) -> RefusalMetrics:
        """
        Compute refusal quality metrics from the rolling window.

        Returns:
            RefusalMetrics with all quality measurements
        """
        if not self._observations:
            return RefusalMetrics()

        obs_list = list(self._observations)

        # Separate refusals and approvals
        refusals = [o for o in obs_list if o.phce_d_output in DecisionOutput.abstention()]
        approvals = [o for o in obs_list if o.phce_d_output in DecisionOutput.trade_positive()]

        # Refusal precision: of refusals, how many would have lost?
        if refusals:
            correct_refusals = sum(1 for o in refusals if not o.would_have_won)
            refusal_precision = correct_refusals / len(refusals)
        else:
            refusal_precision = 0.0

        # Refusal recall: of all losing trades, how many did we correctly reject?
        all_losing = [o for o in obs_list if not o.would_have_won]
        if all_losing:
            correctly_rejected_losers = sum(
                1 for o in all_losing
                if o.phce_d_output in DecisionOutput.abstention()
            )
            refusal_recall = correctly_rejected_losers / len(all_losing)
        else:
            refusal_recall = 1.0  # No losers to miss

        # False abstention rate: of refusals, how many would have won?
        if refusals:
            false_abstentions = sum(1 for o in refusals if o.would_have_won)
            false_abstention_rate = false_abstentions / len(refusals)
        else:
            false_abstention_rate = 0.0

        # Abstention cost: opportunity cost from missed winners
        missed_winners = [o for o in refusals if o.would_have_won]
        abstention_cost = sum(o.actual_return_bps for o in missed_winners)

        # Needs-more-evidence resolution rate
        if self._nme_resolutions:
            nme_resolution_rate = sum(1 for r in self._nme_resolutions if r) / len(self._nme_resolutions)
        else:
            nme_resolution_rate = 0.0

        return RefusalMetrics(
            refusal_precision=refusal_precision,
            refusal_recall=refusal_recall,
            false_abstention_rate=false_abstention_rate,
            abstention_cost=abstention_cost,
            needs_evidence_resolution_rate=nme_resolution_rate,
            total_refusals=len(refusals),
            total_approvals=len(approvals),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return refusal quality statistics."""
        metrics = self.compute_metrics()
        return {
            "total_observations": self.total_observations,
            "total_refusals": self.total_refusals,
            "total_approvals": self.total_approvals,
            "refusal_precision": metrics.refusal_precision,
            "refusal_recall": metrics.refusal_recall,
            "false_abstention_rate": metrics.false_abstention_rate,
            "abstention_cost_bps": metrics.abstention_cost,
            "nme_resolution_rate": metrics.needs_evidence_resolution_rate,
            "warning": (
                "NO_TRADE may be lazy over-filtering"
                if metrics.refusal_precision < 0.5 and self.total_refusals > 20
                else None
            ),
        }
