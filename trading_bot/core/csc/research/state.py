"""Uncertainty map + confidence profiles — the loop begins with
uncertainty, not problems.

Research priority comes from *where consequential uncertainty lives*, not
from what is fashionable to investigate. The map is updated from real
signals: reliability metrics, outcome records, verifier veto patterns,
and explicitly registered assumptions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional


class EvidenceTier(IntEnum):
    """Evidence hierarchy — not all evidence has equal weight. A claim's
    confidence is bounded by the strongest tier supporting it."""
    THEORETICAL = 0        # argument, hypothesis
    SIMULATION = 1         # counterfactual model output
    CONTROLLED = 2         # controlled experiment on real data
    REPLICATION = 3        # repeated controlled result
    INDEPENDENT = 4        # different implementation/dataset
    OOD_VALIDATED = 5      # held up under distribution shift
    REAL_WORLD = 6         # forward-tested live outcome


class ReplicationLevel(IntEnum):
    """Replication ladder. Required level scales with claim strength ×
    deployment consequence — not every claim needs Level 8."""
    SIMULATION = 0
    CONTROLLED_EXPERIMENT = 1
    INDEPENDENT_REPRODUCTION = 2
    DIFFERENT_IMPLEMENTATION = 3
    DIFFERENT_DATASET = 4
    DISTRIBUTION_SHIFT = 5
    ADVERSARIAL = 6
    REAL_WORLD_FORWARD = 7
    LONG_HORIZON = 8


@dataclass
class ConfidenceProfile:
    """A claim's confidence is a profile, never TRUE/FALSE."""
    n_experiments: int = 0
    n_replications: int = 0
    effect_estimate: float = 0.0
    ci_low: float = 0.0
    ci_high: float = 0.0
    ood_effect: Optional[float] = None
    adversarial_effect: Optional[float] = None
    replication_ratio: float = 0.0
    max_tier: EvidenceTier = EvidenceTier.THEORETICAL
    real_world_venues: List[str] = field(default_factory=list)
    level: str = "NONE"    # NONE/LOW/MODERATE/HIGH

    @property
    def paper_only_real_world(self) -> bool:
        return bool(self.real_world_venues) and all(
            v == "paper" for v in self.real_world_venues)

    def compute_level(self) -> str:
        """Honest level: replication and OOD evidence dominate. Paper-venue
        forward results are real evidence but not live-capital evidence —
        a claim supported only by paper real-world data caps at MODERATE."""
        if (self.n_replications >= 2 and self.replication_ratio >= 0.6
                and self.max_tier >= EvidenceTier.REPLICATION
                and not self.paper_only_real_world):
            self.level = "HIGH"
        elif self.n_experiments >= 1 and self.max_tier >= EvidenceTier.CONTROLLED:
            self.level = "MODERATE" if self.replication_ratio >= 0.5 else "LOW"
        else:
            self.level = "LOW" if self.n_experiments else "NONE"
        return self.level


@dataclass
class UncertaintyEntry:
    """One cell of the uncertainty map — a thing the system believes or
    doesn't know, weighted by how much getting it wrong matters."""
    topic: str
    state: str  # known_confident | known_uncertain | unknown_consequential
                # | unknown_inconsequential | contradictory | unexplained |
                # unvalidated_assumption
    confidence: float = 0.5
    consequence: float = 0.5   # decision impact if wrong
    evidence_refs: List[str] = field(default_factory=list)
    contradiction_refs: List[str] = field(default_factory=list)
    last_updated: float = 0.0

    @property
    def priority(self) -> float:
        """Priority = consequence × uncertainty + contradiction pressure."""
        contradiction_bonus = 0.3 if self.state == "contradictory" else 0.0
        return float(self.consequence) * (1.0 - float(self.confidence)) \
            + contradiction_bonus


class UncertaintyMap:
    """The persistent map of what the system does and doesn't know.

    Entries are seeded by observation statistics (precision collapse in a
    regime → known_uncertain), unexplained anomalies (veto spikes, surprise
    spikes → unexplained), and explicit assumptions any component flags."""

    def __init__(self) -> None:
        self._entries: Dict[str, UncertaintyEntry] = {}

    def register(self, entry: UncertaintyEntry) -> UncertaintyEntry:
        self._entries[entry.topic] = entry
        return entry

    def update_from_reliability(
        self, reliability: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> None:
        """Convert per-agent/regime reliability metrics into map entries.

        A regime whose precision collapses below 0.5 is known_uncertain;
        one with < 3 total predictions is an unvalidated assumption; one
        with precision >= 0.7 over >= 10 predictions is known_confident."""
        for agent, regimes in (reliability or {}).items():
            for regime, m in regimes.items():
                # Metrics may be ReliabilityMetrics objects or plain dicts.
                if isinstance(m, dict):
                    total = m.get("total_predictions", 0)
                    precision = m.get("precision", 0.5)
                else:
                    total = getattr(m, "total_predictions", 0)
                    precision = getattr(m, "precision", 0.5)
                topic = f"predictive:{agent}:{regime}"
                if total < 3:
                    state, conf = "unvalidated_assumption", 0.4
                elif precision >= 0.7:
                    state, conf = "known_confident", min(0.9, precision)
                elif precision >= 0.5:
                    state, conf = "known_uncertain", precision
                else:
                    state, conf = "known_uncertain", max(0.1, precision)
                # consequence scales with how often this regime appears
                consequence = min(1.0, 0.3 + total / 50.0)
                existing = self._entries.get(topic)
                refs = (existing.evidence_refs if existing else [])
                self.register(UncertaintyEntry(
                    topic=topic, state=state, confidence=conf,
                    consequence=consequence, evidence_refs=refs))

    def register_unexplained(self, topic: str, consequence: float = 0.6,
                             ref: Optional[str] = None) -> UncertaintyEntry:
        entry = self._entries.get(topic)
        if entry is None:
            entry = UncertaintyEntry(
                topic=topic, state="unexplained", confidence=0.2,
                consequence=consequence)
        if ref:
            entry.evidence_refs.append(ref)
        self._entries[topic] = entry
        return entry

    def register_contradiction(self, topic: str, refs: List[str],
                               consequence: float = 0.7
                               ) -> UncertaintyEntry:
        entry = self._entries.get(topic)
        if entry is None:
            entry = UncertaintyEntry(topic=topic, state="contradictory")
        entry.state = "contradictory"
        entry.confidence = min(entry.confidence, 0.4)
        entry.consequence = max(entry.consequence, consequence)
        entry.contradiction_refs.extend(refs)
        self._entries[topic] = entry
        return entry

    def resolve(self, topic: str, confidence: float,
                evidence_ref: Optional[str] = None) -> None:
        """A research report closes or tightens an entry — never deletes
        history, it moves the belief."""
        entry = self._entries.get(topic)
        if entry is None:
            return
        entry.confidence = confidence
        entry.state = ("known_confident" if confidence >= 0.7
                       else "known_uncertain")
        if evidence_ref:
            entry.evidence_refs.append(evidence_ref)

    def top_questions(self, n: int = 5) -> List[UncertaintyEntry]:
        return sorted(self._entries.values(),
                      key=lambda e: e.priority, reverse=True)[:n]

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            t: {"state": e.state, "confidence": round(e.confidence, 3),
                "consequence": e.consequence, "priority": round(e.priority, 3),
                "evidence_refs": len(e.evidence_refs)}
            for t, e in self._entries.items()}
