"""Adversarial Verdict Engine for the CDS.

Synthesizes disagreements between specialist adversarial reviewers
rather than simple majority voting.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from .reviewers.specialists import ReviewerOutput, BullReviewer, BearReviewer, RiskReviewer


class FinalVerdictOutcome(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ABSTAINED = "ABSTAINED"
    RESIZED = "RESIZED"


@dataclass
class FinalVerdict:
    outcome: FinalVerdictOutcome
    belief_score: float
    uncertainty: float
    explanation: str
    reviewer_verdicts: List[ReviewerOutput]
    synthesis_logic: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class VerdictEngine:
    """Synthesizes structured debate from specialist reviewers."""

    def __init__(self, reviewers: Optional[List[Any]] = None):
        self.reviewers = reviewers or [
            BullReviewer(),
            BearReviewer(),
            RiskReviewer()
        ]
        self.logger = logging.getLogger("cds.verdict_engine")

    async def synthesize(
        self,
        hypothesis: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> FinalVerdict:
        """Run the adversarial debate and synthesize the final verdict."""

        # 1. Run all reviewers in parallel
        tasks = [reviewer.review(hypothesis, evidence) for reviewer in self.reviewers]
        raw_results = await asyncio.gather(*tasks)
        results = [asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in raw_results]

        # 2. Extract Disagreements
        approvals = [r for r in results if r['verdict'] == "APPROVE"]
        rejections = [r for r in results if r['verdict'] == "REJECT"]
        cautions = [r for r in results if r['verdict'] == "CAUTION"]

        # 3. Calculate Synthesis
        # Principle: synthesis should weigh rejections and risk concerns higher than approvals.

        total_confidence = sum(r['confidence'] for r in results)
        if total_confidence == 0:
            return self._abstain("Zero confidence from all reviewers")

        # Weighted belief score
        weighted_score = sum(
            (1.0 if r['verdict'] == "APPROVE" else 0.0 if r['verdict'] == "REJECT" else 0.5) * r['confidence']
            for r in results
        ) / total_confidence

        # Uncertainty synthesis (average + disagreement penalty)
        avg_uncertainty = sum(r['uncertainty'] for r in results) / len(results)
        disagreement_penalty = (len(rejections) * 0.2) if approvals else 0.0
        final_uncertainty = min(1.0, avg_uncertainty + disagreement_penalty)

        # 4. Final Decision Logic
        outcome = FinalVerdictOutcome.APPROVED
        explanation = "Debate synthesized: Consensus reached on directional edge."

        if rejections:
            outcome = FinalVerdictOutcome.REJECTED
            explanation = f"REJECTED: {len(rejections)} reviewers raised critical objections. Objections: " + \
                          "; ".join([r['reasoning'] for r in rejections])
        elif final_uncertainty > 0.6:
            outcome = FinalVerdictOutcome.ABSTAINED
            explanation = f"ABSTAINED: High disagreement/uncertainty ({final_uncertainty:.2f})."
        elif weighted_score < 0.6:
            outcome = FinalVerdictOutcome.RESIZED
            explanation = f"RESIZED: Moderate confidence ({weighted_score:.2f}); reducing exposure."

        return FinalVerdict(
            outcome=outcome,
            belief_score=round(weighted_score, 4),
            uncertainty=round(final_uncertainty, 4),
            explanation=explanation,
            reviewer_verdicts=results,
            synthesis_logic="Weighted Bayesian Synthesis with Disagreement Penalty",
            metadata={"num_reviewers": len(results)}
        )

    def _abstain(self, reason: str) -> FinalVerdict:
        return FinalVerdict(
            outcome=FinalVerdictOutcome.ABSTAINED,
            belief_score=0.0,
            uncertainty=1.0,
            explanation=reason,
            reviewer_verdicts=[],
            synthesis_logic="Default Abstention"
        )
