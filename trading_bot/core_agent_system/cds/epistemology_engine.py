"""Adversarial Epistemology Engine for the CDS.

This engine challenges every belief by asking structured critical questions,
identifying missing info, assumptions, and counterarguments.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import numpy as np

from .evidence_graph import EvidenceGraph, CDSElement, NodeType, RelationType


@dataclass
class EpistemicReport:
    belief_score: float  # 0.0 to 1.0
    uncertainty: float   # 0.0 to 1.0
    confidence_interval: tuple[float, float]
    counterarguments: List[str]
    supporting_evidence_quality: float
    missing_critical_info: List[str]
    assumptions_identified: List[str]
    adversarial_risk_score: float


class EpistemologyEngine:
    """Engine that challenges trading hypotheses using a hybrid mathematical framework."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.critical_questions = [
            "What evidence supports this?",
            "What evidence contradicts this?",
            "What assumptions exist?",
            "How reliable is each source?",
            "What information is missing?",
            "What alternative explanations exist?",
            "What market regime would invalidate this?",
            "What historical failures resemble this situation?",
            "How uncertain is this conclusion?",
            "How would an adversary exploit this reasoning?"
        ]

    def analyze_hypothesis(
        self,
        hypothesis_id: str,
        graph: EvidenceGraph
    ) -> EpistemicReport:
        """Perform a deep epistemic audit of a hypothesis."""

        if hypothesis_id not in graph.elements:
            raise ValueError(f"Hypothesis {hypothesis_id} not found in evidence graph.")

        hypothesis = graph.elements[hypothesis_id]

        # 1. Gather Evidence
        supporting = graph.get_supporting_evidence(hypothesis_id)
        contradicting = graph.get_contradicting_evidence(hypothesis_id)

        # 2. Identify Assumptions and Missing Info
        assumptions = hypothesis.content.get("assumptions", [])
        missing_info = self._detect_missing_info(hypothesis, supporting)

        # 3. Calculate Belief Score (Bayesian-ish)
        belief_score = self._calculate_belief_score(supporting, contradicting)

        # 4. Calculate Uncertainty (Entropy/Dempster-Shafer)
        uncertainty = self._calculate_uncertainty(supporting, contradicting, missing_info)

        # 5. Identify Counterarguments
        counterarguments = [c.content.get("statement", "Unknown contradiction") for c in contradicting]
        if uncertainty > 0.5:
            counterarguments.append(f"High uncertainty detected ({uncertainty:.2f}) due to missing information.")

        # 6. Calculate Confidence Interval
        ci_lower = max(0.0, belief_score - (uncertainty * 0.5))
        ci_upper = min(1.0, belief_score + ((1.0 - belief_score) * 0.2))

        # 7. Adversarial Risk
        adversarial_risk = self._evaluate_adversarial_exploitability(hypothesis, assumptions, uncertainty)

        return EpistemicReport(
            belief_score=round(belief_score, 4),
            uncertainty=round(uncertainty, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            counterarguments=counterarguments,
            supporting_evidence_quality=self._calc_evidence_quality(supporting),
            missing_critical_info=missing_info,
            assumptions_identified=assumptions,
            adversarial_risk_score=round(adversarial_risk, 4)
        )

    def _calculate_belief_score(
        self,
        supporting: List[CDSElement],
        contradicting: List[CDSElement]
    ) -> float:
        """Calculate belief score using weighted support vs contradiction."""
        if not supporting and not contradicting:
            return 0.5

        support_sum = sum(e.confidence for e in supporting)
        contradict_sum = sum(e.confidence for e in contradicting)

        total = support_sum + contradict_sum
        if total == 0:
            return 0.5

        return support_sum / total

    def _calculate_uncertainty(
        self,
        supporting: List[CDSElement],
        contradicting: List[CDSElement],
        missing_info: List[str]
    ) -> float:
        """Calculate uncertainty using Information Theory (Entropy) and missing info penalty."""
        num_evidence = len(supporting) + len(contradicting)
        if num_evidence == 0:
            return 1.0

        # Entropy of the evidence distribution
        support_ratio = len(supporting) / num_evidence
        entropy = 0
        if 0 < support_ratio < 1:
            entropy = -(support_ratio * np.log2(support_ratio) + (1 - support_ratio) * np.log2(1 - support_ratio))

        # Penalty for missing critical info
        missing_penalty = min(0.5, len(missing_info) * 0.1)

        return min(1.0, (entropy / 1.0) * 0.5 + missing_penalty)

    def _detect_missing_info(
        self,
        hypothesis: CDSElement,
        supporting: List[CDSElement]
    ) -> List[str]:
        """Identify missing evidence types required by the hypothesis."""
        required = set(hypothesis.content.get("required_evidence_types", ["market_data", "signal"]))
        provided = {e.metadata.get("evidence_type") for e in supporting}

        missing = list(required - provided)
        return [m for m in missing if m is not None]

    def _calc_evidence_quality(self, supporting: List[CDSElement]) -> float:
        """Measure average confidence and freshness of evidence."""
        if not supporting:
            return 0.0

        now = time.time()
        quality_scores = []
        for e in supporting:
            # Freshness decay (half-life of 5 minutes for this example)
            age = now - e.timestamp
            freshness = np.exp(-age / 300.0)
            quality_scores.append(e.confidence * freshness)

        return float(np.mean(quality_scores))

    def _evaluate_adversarial_exploitability(
        self,
        hypothesis: CDSElement,
        assumptions: List[str],
        uncertainty: float
    ) -> float:
        """How easily could a market adversary exploit this reasoning?"""
        # Exploitable if:
        # 1. High uncertainty.
        # 2. Many unverified assumptions.
        # 3. Predictable directional bias.

        base_risk = 0.2
        assumption_risk = len(assumptions) * 0.1
        uncertainty_risk = uncertainty * 0.4

        return min(1.0, base_risk + assumption_risk + uncertainty_risk)
