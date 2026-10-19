"""Bridge between the HMS reflective stores and the Level-1 RSI cycle.

This module is what makes the improvement loop *recursive* against the live
system's own history:

    CSC failures  -->  HMS FailureMemory  -->  PerformanceGaps
        -->  RecursiveImprovementCycle.run_cycle(gaps=...)
        -->  PromotionDecisions  -->  HMS SelfImprovementMemory
        -->  recalled as lessons by the CSC evidence plane

Authority boundary: the bridge moves *evidence* in both directions. It never
promotes a candidate — that stays behind the signed ``OperatorAuthorization``
at the ``PromotionLadder`` — and it never touches the decision path.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .engine_v2 import PerformanceGap
from .improvement_genome import PromotionDecision

logger = logging.getLogger(__name__)

# Failure-kind -> (gap kind, metric) mapping. Gap kinds are the closed set
# ObservationEngine emits so RootCauseEngine attribution stays coherent:
#   cold_start | below_hurdle | tail_risk | cost_drag | inactivity
_FAILURE_TO_GAP = {
    "prediction_incorrect": ("below_hurdle", "directional_precision"),
    "decision_rejected": ("inactivity", "approval_rate"),
    "execution_fault": ("cost_drag", "realized_cost"),
    "verification_failed": ("below_hurdle", "verification_pass_rate"),
    "advisor_error": ("inactivity", "advisor_availability"),
    "other": ("below_hurdle", "net_return"),
}


def gaps_from_failure_summary(
    summary: Mapping[str, Any],
    *,
    min_count: int = 3,
) -> List[PerformanceGap]:
    """Translate an HMS ``failure_summary()`` into PerformanceGaps.

    A failure kind only becomes a gap once it recurs ``min_count`` times —
    a single bad call is noise, a repeated failure mode is a diagnosable
    weakness. Severity scales with count and saturates at 1.0.
    """
    gaps: List[PerformanceGap] = []
    by_kind = dict(summary.get("by_kind") or {})
    by_regime = dict(summary.get("by_regime") or {})
    for kind, count in by_kind.items():
        if count < min_count:
            continue
        gap_kind, metric = _FAILURE_TO_GAP.get(
            str(kind), ("below_hurdle", "net_return"))
        regime = max(by_regime, key=by_regime.get) if by_regime else "all"
        gaps.append(PerformanceGap(
            kind=gap_kind,
            metric=metric,
            regime=regime,
            severity=min(1.0, count / 20.0),
            evidence={"failure_kind": kind, "failure_count": count,
                      "source": "hms_failure_memory"}))
    return gaps


def decisions_to_lessons(
    decisions: Iterable[PromotionDecision],
) -> List[Dict[str, Any]]:
    """Shape PromotionDecisions into self-improvement memory records."""
    records: List[Dict[str, Any]] = []
    for decision in decisions or []:
        status = str(getattr(decision, "status", "") or "")
        reason = str(getattr(decision, "reason", "") or "")
        genome_id = str(getattr(decision, "genome_id", "") or "")
        evidence = getattr(decision, "evidence", {}) or {}
        domain = str(
            (evidence.get("genome") or {}).get("domain")
            or evidence.get("domain")
            or "trading_policy")
        records.append({
            "record_type": "decision",
            "domain": domain,
            "summary": f"{genome_id}: {status} — {reason}",
            "status": status,
            "genome_id": genome_id or None,
            "evidence": {
                "verdict": dict(evidence) if isinstance(evidence, Mapping)
                           else {},
            },
        })
        # A rejected-with-reason verdict is a generalized lesson the next
        # cycle (and the evidence plane) should not relearn the hard way.
        if status in ("rejected", "insufficient_evidence") and reason:
            records.append({
                "record_type": "lesson",
                "domain": domain,
                "summary": f"{genome_id} failed: {reason}",
                "status": status,
                "genome_id": genome_id or None,
                "evidence": {"learned_from": "promotion_decision"},
            })
    return records


class RSIHMSBridge:
    """Couples the canonical RSI cycle to HMS reflective memory.

    ``observe_gaps`` reads the HMS failure aggregates; ``mirror_decisions``
    writes the cycle's verdicts and lessons back. The caller still owns
    *when* a cycle runs — the bridge never starts one by itself.
    """

    def __init__(self, hms: Any, memory: Any = None) -> None:
        self.hms = hms
        self.memory = memory  # durable ImprovementMemory ledger (optional)

    def observe_gaps(self, *, min_count: int = 3) -> List[PerformanceGap]:
        """Failure memory -> PerformanceGaps for run_cycle(gaps=...)."""
        summary_fn = getattr(self.hms, "failure_summary", None)
        if summary_fn is None:
            return []
        try:
            summary = summary_fn()
        except Exception as exc:  # noqa: BLE001
            logger.warning("RSI-HMS bridge: failure summary failed: %s", exc)
            return []
        return gaps_from_failure_summary(summary, min_count=min_count)

    def mirror_decisions(
        self, decisions: Iterable[PromotionDecision]
    ) -> List[str]:
        """Write cycle decisions (and derived lessons) into HMS + the
        durable RSI ledger. Returns the HMS record ids written."""
        record_fn = getattr(self.hms, "record_improvement", None)
        if record_fn is None:
            return []
        ids: List[str] = []
        for rec in decisions_to_lessons(decisions):
            try:
                ids.append(record_fn(**rec))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "RSI-HMS bridge: improvement record failed: %s", exc)
        return ids

    def run_observed_cycle(self, cycle: Any, *, min_count: int = 3
                           ) -> List[PromotionDecision]:
        """Run one ``RecursiveImprovementCycle`` seeded from live failure
        memory, then mirror every decision back into HMS. Operator-invoked —
        the trading loop never calls this on its own."""
        gaps = self.observe_gaps(min_count=min_count)
        decisions = cycle.run_cycle(gaps=gaps or None)
        self.mirror_decisions(decisions)
        return decisions
