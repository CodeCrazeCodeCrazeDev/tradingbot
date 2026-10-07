"""Experiment contracts + value-of-information experiment selection.

Two commitments this module enforces:

1. **Locked contract** — an experiment is an immutable scientific object.
   Once sealed, its parameters hash into ``seal_hash``; attempting to
   mutate a frozen dataclass raises. The seal is recorded *before*
   execution so the contract can't be rewritten to make it pass.

2. **VoI selection** — the question is "which experiment should we run
   next?", never "which can we run?". Score:

       expected_info_gain × decision_relevance × capability_impact
           × replication_value
       ─────────────────────────────────────────────────────────
       compute_cost + time_cost + financial_cost + risk
           + opportunity_cost
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from trading_bot.core.governance.determinism import determinism as _determinism

from .state import ReplicationLevel


@dataclass(frozen=True)
class ExperimentContract:
    """An experiment is locked before it runs. All fields are part of the
    seal — nothing here may be amended post-hoc."""
    contract_id: str
    hypothesis_id: str
    baseline_id: str
    treatment_id: str
    dataset_id: str
    primary_metric: str
    secondary_metrics: tuple = ()
    expected_effect: float = 0.0
    minimum_meaningful_effect: float = 0.0
    alpha: float = 0.05
    power: float = 0.8
    falsification_criteria: tuple = ()
    compute_budget: float = 0.0
    time_budget_s: float = 0.0
    stopping_rule: str = "evaluate_once"
    evaluation_set: str = "oos"
    contamination_policy: str = "reject_on_overlap"
    replication_level: int = int(ReplicationLevel.CONTROLLED_EXPERIMENT)
    sealed_at: float = 0.0
    seal_hash: str = ""

    def seal(self) -> "ExperimentContract":
        """Return a sealed copy — the hash commits every parameter."""
        payload = {k: v for k, v in asdict(self).items()
                   if k not in ("sealed_at", "seal_hash")}
        canon = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(canon.encode()).hexdigest()
        return ExperimentContract(**{**asdict(self),
                                     "sealed_at": time.time(),
                                     "seal_hash": digest})

    def verify_seal(self) -> bool:
        """Recompute the hash over the frozen fields — any tamper fails."""
        payload = {k: v for k, v in asdict(self).items()
                   if k not in ("sealed_at", "seal_hash")}
        canon = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canon.encode()).hexdigest() == self.seal_hash


def make_contract(**kwargs: Any) -> ExperimentContract:
    """Constructor that seals the contract at creation."""
    kwargs.setdefault("contract_id", _determinism.get_uuid())
    return ExperimentContract(**kwargs).seal()


@dataclass
class ExperimentCandidate:
    """A design under consideration for VoI scoring."""
    description: str
    contract: Optional[ExperimentContract]
    expected_info_gain: float     # 0..1 — how much uncertainty it resolves
    decision_relevance: float     # 0..1 — does the answer change a decision
    capability_impact: float      # 0..1 — validated capability if supported
    replication_value: float      # 0..1 — does it replicate prior results
    compute_cost: float = 1.0
    time_cost: float = 1.0
    financial_cost: float = 0.0
    risk_cost: float = 0.0
    opportunity_cost: float = 0.0


class VoIEngine:
    """Ranks candidate experiments by expected knowledge gained per unit
    cost. Deliberately multiplicative on gains (a zero-relevance experiment
    scores zero) and additive on costs."""

    def score(self, c: ExperimentCandidate) -> float:
        gain = (float(c.expected_info_gain)
                * float(c.decision_relevance)
                * float(c.capability_impact)
                * max(0.1, float(c.replication_value)))
        cost = (float(c.compute_cost) + float(c.time_cost)
                + float(c.financial_cost) + float(c.risk_cost)
                + float(c.opportunity_cost))
        return gain / max(cost, 1e-9)

    def rank(self, candidates: List[ExperimentCandidate]
             ) -> List[ExperimentCandidate]:
        return sorted(candidates, key=self.score, reverse=True)

    def select(self, candidates: List[ExperimentCandidate]
               ) -> Optional[ExperimentCandidate]:
        ranked = self.rank(candidates)
        return ranked[0] if ranked else None
