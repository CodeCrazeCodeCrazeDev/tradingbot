"""Formal research-question formation.

Vague observations become falsifiable questions only after scope,
assumptions, competing explanations, and falsification criteria are made
explicit. Questions are generated from the uncertainty map — the system
asks "what do we most consequentially not know?" first.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from trading_bot.core.governance.determinism import determinism as _determinism

from .state import UncertaintyEntry, UncertaintyMap


@dataclass
class ResearchQuestion:
    """A question is a contract-shaped object — testable or it doesn't
    enter the pipeline."""
    question_id: str
    objective: str
    topic: str
    scope: str = ""
    assumptions: List[str] = field(default_factory=list)
    known_evidence: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    competing_explanations: List[str] = field(default_factory=list)
    success_criteria: str = ""
    falsification_criteria: List[str] = field(default_factory=list)
    resource_budget: Dict[str, float] = field(default_factory=dict)
    risk_level: str = "low"          # low | medium | high
    priority: float = 0.0
    created_at: float = field(default_factory=time.time)


def formalize(entry: UncertaintyEntry) -> ResearchQuestion:
    """Turn an uncertainty-map cell into a falsifiable question."""
    scope = {
        "unexplained": "Determine the mechanism behind the anomaly and "
                       "whether it is decision-relevant.",
        "contradictory": "Identify which measurement conditions flip the "
                         "result — datasets, regimes, implementations.",
        "unvalidated_assumption": "Obtain the first measured evidence for "
                                  "or against the assumption.",
    }.get(entry.state, "Characterize the uncertainty's size and source.")

    falsifiers = [
        "The effect disappears on a disjoint out-of-sample slice.",
        "The effect is fully explained by transaction cost or leakage.",
        "An alternative explanation fits the same evidence as well or "
        "better.",
        "The effect fails to replicate under a different implementation.",
    ]
    risk = ("high" if entry.consequence >= 0.8 else
            "medium" if entry.consequence >= 0.5 else "low")
    return ResearchQuestion(
        question_id=_determinism.get_uuid(),
        objective=f"Resolve uncertainty on '{entry.topic}'",
        topic=entry.topic,
        scope=scope,
        assumptions=[f"Entry state '{entry.state}' reflects actual "
                     f"knowledge, not stale data."],
        known_evidence=list(entry.evidence_refs),
        unknowns=[f"true value of {entry.topic}",
                  "boundary conditions under which the belief holds"],
        competing_explanations=(
            ["regime dependence", "measurement artifact",
             "sample-size coincidence"] if entry.state in (
                 "unexplained", "contradictory") else []),
        success_criteria=(
            "Verified evidence graph passes the adversarial swarm; "
            "outcome measurable against the falsification criteria."),
        falsification_criteria=falsifiers,
        resource_budget={"observations": 60, "max_rsi_cycles": 0},
        risk_level=risk,
        priority=entry.priority)


def generate_questions(uncertainty_map: UncertaintyMap, n: int = 5
                       ) -> List[ResearchQuestion]:
    """The VoI engine ranks; the generator formalizes the top entries."""
    return [formalize(e) for e in uncertainty_map.top_questions(n)]
