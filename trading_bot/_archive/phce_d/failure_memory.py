"""
PHCE-D Module 14: Feedback Loop and Failure Memory

Append-only failure memory with hard restrictions:
- Feedback loop MAY recommend
- Feedback loop MAY NOT deploy
- No automatic threshold modification
- No automatic re-promotion
- No self-tuning into more trade approvals

Good:
- Append-only failure memory
- Threshold recalibration recommendations
- Hypothesis-family failure patterns

Dangerous (forbidden):
- Automatic threshold modification
- Automatic re-promotion
- Self-tuning into more trade approvals
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Set

from .core_types import (
    DecisionAuditRecord,
    DecisionOutput,
    Hypothesis,
    HypothesisStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class FailureRecord:
    """A single failure record — append-only, never modified."""
    record_id: str
    timestamp: float
    hypothesis_id: str
    hypothesis_name: str
    decision_id: str
    failure_type: str  # "verification_failed", "cost_killed", "gateway_rejected", "paper_trade_failed", "drift_detected"
    failure_details: str
    edge_before_cost_bps: float
    edge_after_cost_bps: float
    output_class: DecisionOutput
    regime_at_failure: str
    # Recommendation (MAY recommend, MAY NOT deploy)
    recommendation: str
    recommendation_type: str  # "threshold_recalibration", "hypothesis_retirement", "feature_review", "regime_review"
    deployed: bool = False  # Always False — recommendations are never auto-deployed


@dataclass
class FailurePattern:
    """A recurring failure pattern detected across multiple records."""
    pattern_id: str
    pattern_name: str
    failure_type: str
    occurrence_count: int
    affected_hypotheses: Set[str]
    common_regime: str
    recommendation: str
    severity: float  # 0-1


class FailureMemory:
    """
    Module 14: Feedback Loop and Failure Memory

    Append-only failure memory that records what went wrong and why.

    Hard restrictions:
    - MAY recommend threshold recalibrations
    - MAY NOT deploy any changes automatically
    - MAY NOT re-promote retired hypotheses
    - MAY NOT self-tune into more trade approvals

    The feedback loop is a diagnostic tool, not an autopilot.
    """

    def __init__(
        self,
        max_records: int = 10000,
        pattern_detection_min_occurrences: int = 3,
    ):
        self.max_records = max_records
        self.pattern_min = pattern_detection_min_occurrences

        # Append-only records
        self._records: Deque[FailureRecord] = deque(maxlen=max_records)

        # Pattern tracking
        self._patterns: Dict[str, FailurePattern] = {}
        self._failure_type_counts: Dict[str, int] = defaultdict(int)
        self._hypothesis_failure_counts: Dict[str, int] = defaultdict(int)

        # Statistics
        self.total_records = 0
        self.total_recommendations = 0
        self.total_deployed = 0  # Should always be 0

    def record_failure(
        self,
        hypothesis: Hypothesis,
        decision_id: str,
        failure_type: str,
        failure_details: str,
        edge_before_cost_bps: float,
        edge_after_cost_bps: float,
        output_class: DecisionOutput,
        regime_at_failure: str = "",
        recommendation: str = "",
        recommendation_type: str = "",
    ) -> FailureRecord:
        """
        Record a failure — append-only, never modified after creation.

        Args:
            hypothesis: The hypothesis that failed
            decision_id: The decision audit record ID
            failure_type: Category of failure
            failure_details: Human-readable description
            edge_before_cost_bps: Edge before cost adjustment
            edge_after_cost_bps: Edge after cost adjustment
            output_class: The decision output that resulted
            regime_at_failure: Regime at time of failure
            recommendation: What should be considered (not auto-deployed)
            recommendation_type: Category of recommendation

        Returns:
            The created FailureRecord (never to be modified)
        """
        now = time.time()
        record_id = hashlib.sha256(
            f"{decision_id}:{failure_type}:{now}".encode()
        ).hexdigest()[:16]

        record = FailureRecord(
            record_id=record_id,
            timestamp=now,
            hypothesis_id=hypothesis.hypothesis_id,
            hypothesis_name=hypothesis.name,
            decision_id=decision_id,
            failure_type=failure_type,
            failure_details=failure_details,
            edge_before_cost_bps=edge_before_cost_bps,
            edge_after_cost_bps=edge_after_cost_bps,
            output_class=output_class,
            regime_at_failure=regime_at_failure,
            recommendation=recommendation,
            recommendation_type=recommendation_type,
            deployed=False,  # NEVER auto-deployed
        )

        self._records.append(record)
        self.total_records += 1

        # Update tracking
        self._failure_type_counts[failure_type] += 1
        self._hypothesis_failure_counts[hypothesis.hypothesis_id] += 1

        if recommendation:
            self.total_recommendations += 1

        # Check for patterns
        self._detect_patterns()

        logger.info(
            f"Failure recorded: {failure_type} for {hypothesis.name} "
            f"edge_before={edge_before_cost_bps:.1f}bps "
            f"edge_after={edge_after_cost_bps:.1f}bps"
        )

        return record

    def get_recommendations(
        self,
        hypothesis_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pending recommendations — for human review only.
        These are NEVER auto-deployed.

        Args:
            hypothesis_id: Filter by hypothesis, or None for all

        Returns:
            List of recommendation dicts for human review
        """
        recommendations = []
        for record in self._records:
            if record.recommendation and not record.deployed:
                if hypothesis_id is None or record.hypothesis_id == hypothesis_id:
                    recommendations.append({
                        "record_id": record.record_id,
                        "hypothesis_id": record.hypothesis_id,
                        "hypothesis_name": record.hypothesis_name,
                        "failure_type": record.failure_type,
                        "recommendation": record.recommendation,
                        "recommendation_type": record.recommendation_type,
                        "timestamp": record.timestamp,
                        "deployed": record.deployed,
                        "warning": "RECOMMENDATION ONLY — DO NOT AUTO-DEPLOY",
                    })
        return recommendations

    def mark_recommendation_deployed(
        self,
        record_id: str,
        deployed_by: str,
    ) -> bool:
        """
        Mark a recommendation as deployed by a human.
        This requires explicit human action — no automation.

        Args:
            record_id: The failure record ID
            deployed_by: Human who approved the deployment

        Returns:
            True if successfully marked
        """
        for record in self._records:
            if record.record_id == record_id:
                record.deployed = True
                self.total_deployed += 1
                logger.info(
                    f"Recommendation {record_id} deployed by {deployed_by}"
                )
                return True
        return False

    def get_failure_patterns(self) -> List[FailurePattern]:
        """Get detected failure patterns."""
        return list(self._patterns.values())

    def get_hypothesis_failure_summary(
        self,
        hypothesis_id: str,
    ) -> Dict[str, Any]:
        """Get failure summary for a specific hypothesis."""
        records = [r for r in self._records if r.hypothesis_id == hypothesis_id]
        if not records:
            return {"hypothesis_id": hypothesis_id, "total_failures": 0}

        by_type: Dict[str, int] = defaultdict(int)
        for r in records:
            by_type[r.failure_type] += 1

        return {
            "hypothesis_id": hypothesis_id,
            "total_failures": len(records),
            "by_type": dict(by_type),
            "most_recent": max(records, key=lambda r: r.timestamp).failure_type,
            "should_retire": len(records) >= 5,  # Heuristic: 5+ failures → retire
        }

    def _detect_patterns(self) -> None:
        """Detect recurring failure patterns across records."""
        # Group by failure type + regime
        groups: Dict[str, List[FailureRecord]] = defaultdict(list)
        for record in self._records:
            key = f"{record.failure_type}:{record.regime_at_failure}"
            groups[key].append(record)

        for key, group in groups.items():
            if len(group) < self.pattern_min:
                continue

            failure_type, regime = key.split(":", 1)
            pattern_id = hashlib.sha256(key.encode()).hexdigest()[:12]

            affected = {r.hypothesis_id for r in group}
            severity = min(1.0, len(group) / 20.0)

            recommendation = self._generate_pattern_recommendation(failure_type, len(group))

            pattern = FailurePattern(
                pattern_id=pattern_id,
                pattern_name=f"recurring_{failure_type}_in_{regime or 'unknown_regime'}",
                failure_type=failure_type,
                occurrence_count=len(group),
                affected_hypotheses=affected,
                common_regime=regime,
                recommendation=recommendation,
                severity=severity,
            )
            self._patterns[pattern_id] = pattern

    def _generate_pattern_recommendation(
        self,
        failure_type: str,
        count: int,
    ) -> str:
        """Generate a recommendation for a failure pattern."""
        recommendations = {
            "verification_failed": "Consider tightening verification thresholds or retiring affected hypothesis family",
            "cost_killed": "Transaction cost model may be too conservative, or edge is genuinely insufficient — do NOT lower cost estimates",
            "gateway_rejected": "Review gateway thresholds — but do NOT loosen them without human approval and calibration evidence",
            "paper_trade_failed": "Hypothesis does not survive realistic execution — retire it",
            "drift_detected": "Regime has shifted — consider suspending affected hypotheses until conditions stabilize",
        }
        base = recommendations.get(failure_type, "Review failure pattern and consider hypothesis retirement")
        return f"{base} (pattern observed {count} times)"

    def get_stats(self) -> Dict[str, Any]:
        """Return failure memory statistics."""
        return {
            "total_records": self.total_records,
            "total_recommendations": self.total_recommendations,
            "total_deployed": self.total_deployed,
            "deployed_rate": self.total_deployed / max(1, self.total_recommendations),
            "failure_type_counts": dict(self._failure_type_counts),
            "pattern_count": len(self._patterns),
            "warning": "Recommendations are NEVER auto-deployed" if self.total_deployed == 0 else None,
        }
