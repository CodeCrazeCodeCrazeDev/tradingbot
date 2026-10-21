"""Autonomy manager — the organism's operations layer.

Each observation cycle the CSC asks one question about itself: what
should the organism be doing right now? This manager is the auditable
answer. It replaces scattered independent interval hooks with a single
prioritized activity portfolio, health-scaled budgets, and a capability-
expansion ledger that accounts for every agent the organism has grown.

Authority: none over capital. The manager schedules the organism's own
background activities (research, self-questioning, RSI gap reports,
electorate rewiring, capability review) and emits AUTONOMY audit
events. It cannot place orders, change risk, or bypass gates.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Activities in descending priority. At most one *background* activity
# runs per tick — they share the research task slot — while cheap
# in-line activities (rewire check, ledger update) always run.
ACTIVITY_PRIORITY = (
    "self_question",      # a measured weakness outranks exploration
    "research_cycle",     # budgeted uncertainty-driven investigation
    "capability_review",  # proposals -> candidate-ready signals
    "rsi_gap",            # failure-memory gap reporting
    "rewire",             # electorate transitions (handled in-line)
)

_HEALTHY_SCORE = 50      # below this, exploration spend is suspended


@dataclass
class ActivityDecision:
    activity: str
    allowed: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {"activity": self.activity, "allowed": self.allowed,
                "reason": self.reason}


@dataclass
class AutonomyTick:
    cycle: int
    health_score: Optional[float]
    decisions: List[ActivityDecision] = field(default_factory=list)
    capability_pipeline: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "health_score": self.health_score,
            "decisions": [d.to_dict() for d in self.decisions],
            "capability_pipeline": dict(self.capability_pipeline),
        }


class AutonomyManager:
    """Per-cycle operations decision-maker for the organism.

    Reads measured state — self-health, funnel, capability pipeline,
    research task occupancy — and emits an auditable activity plan.
    Intervals remain the rhythm; this manager adds the judgment layer:
    degraded health suspends exploration, a pending measured weakness
    outranks routine research, and every scheduling choice is a record.
    """

    AUDIT_EVERY = 25   # AUTONOMY audit event cadence

    def __init__(self) -> None:
        self.ticks = 0
        self.activity_counts: Dict[str, int] = {}
        self.last_tick: Optional[AutonomyTick] = None

    # -- the per-cycle ops decision -------------------------------------

    def tick(self, csc: Any) -> AutonomyTick:
        seq = int(getattr(csc, "_observation_seq", 0))
        self.ticks += 1

        health = getattr(csc, "_last_self_health", None) or {}
        score = health.get("score")
        degraded = (isinstance(score, (int, float))
                    and score < _HEALTHY_SCORE)

        task = getattr(csc, "_research_cycle_task", None)
        slot_free = task is None or getattr(task, "done", lambda: True)()

        tick = AutonomyTick(cycle=seq,
                            health_score=score if isinstance(
                                score, (int, float)) else None)

        has_weakness = csc._self_question() is not None

        # Priority ordering with reasons — every gate is explicit.
        tick.decisions.append(ActivityDecision(
            "self_question",
            allowed=has_weakness and slot_free and not degraded,
            reason=("measured weakness found" if has_weakness
                    else "no measured weakness")
            + ("" if slot_free else "; research slot busy")
            + ("; health degraded — suspended" if degraded else "")))
        tick.decisions.append(ActivityDecision(
            "research_cycle",
            allowed=slot_free and not degraded,
            reason=("scheduled" if slot_free else "research slot busy")
            + ("; health degraded — suspended" if degraded else "")))
        tick.decisions.append(ActivityDecision(
            "capability_review",
            allowed=True,
            reason="capability proposals audited each tick"))
        tick.decisions.append(ActivityDecision(
            "rsi_gap",
            allowed=True,
            reason="failure-memory reporting stays active"))
        tick.decisions.append(ActivityDecision(
            "rewire", allowed=True,
            reason="electorate evaluation stays active"))

        tick.capability_pipeline = self.capability_ledger(csc)
        self.last_tick = tick
        for d in tick.decisions:
            if d.allowed:
                self.activity_counts[d.activity] = (
                    self.activity_counts.get(d.activity, 0) + 1)
        return tick

    # -- the capability-expansion ledger --------------------------------

    def capability_ledger(self, csc: Any) -> Dict[str, int]:
        """Growth accounting: every engineered candidate and advisory
        node, counted by lifecycle state. The organism's expansion is a
        measurable ledger, not a claim."""
        ledger: Dict[str, int] = {}
        for cand in (getattr(csc, "_engineered_models", {}) or {}).values():
            status = str(getattr(cand, "status", "unknown")).lower()
            ledger[f"candidate_{status}"] = (
                ledger.get(f"candidate_{status}", 0) + 1)
        sup = getattr(csc, "_self_wiring", None)
        if sup is not None:
            for node in sup.nodes.values():
                key = f"node_{node.state.value}"
                ledger[key] = ledger.get(key, 0) + 1
        engine = getattr(csc, "research_engine", None)
        try:
            proposals = engine.capability_proposals() if engine else []
            ledger["capability_proposals"] = len(proposals)
        except Exception:  # noqa: BLE001
            ledger["capability_proposals"] = 0
        return ledger

    # -- transparency ----------------------------------------------------

    def should_audit(self) -> bool:
        return self.ticks % self.AUDIT_EVERY == 0

    def report(self) -> Dict[str, Any]:
        return {
            "ticks": self.ticks,
            "activity_counts": dict(self.activity_counts),
            "last_tick": (self.last_tick.to_dict()
                          if self.last_tick else None),
        }
