"""
Multi-Agent Scientific Debate and Consensus Engine for Research OS.
Coordinates specialized reviewer agents, aggregates opinions, and derives a Bayesian-weighted consensus.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import logging

from trading_bot.research.core.interfaces import ReviewerOpinion, HypothesisObject
from trading_bot.research.marketplace.agents import (
    StatisticianReviewer,
    EconometricianReviewer,
    PortfolioManagerReviewer,
    RiskManagerReviewer,
    ExecutionSpecialistReviewer,
    SkepticalReviewer
)

logger = logging.getLogger(__name__)


class ScientificDebateEngine:
    """
    Coordinates multi-agent debate tournaments over quantitative research proposals.
    Governance depends on aggregated consensus evidence rather than a single checklist.
    """

    def __init__(self):
        # Instantiate standard panel of experts
        self.reviewers = [
            StatisticianReviewer(),
            EconometricianReviewer(),
            PortfolioManagerReviewer(),
            RiskManagerReviewer(),
            ExecutionSpecialistReviewer(),
            SkepticalReviewer()
        ]

    def conduct_debate(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> Tuple[bool, float, List[ReviewerOpinion], str]:
        """
        Runs the debate.
        Returns:
          - is_promoted (bool)
          - consensus_score (float, 0 to 1)
          - opinions (list of ReviewerOpinion)
          - debate_summary (str)
        """
        opinions = []
        approved_weight = 0.0
        total_weight = 0.0
        objections_count = 0

        logger.info(f"[*] Convening quantitative review board for hypothesis '{hypothesis.hypothesis_id}'")

        for reviewer in self.reviewers:
            try:
                opinion = reviewer.critique(hypothesis, backtest_results)
                opinions.append(opinion)

                # We weight reviews by the reviewer's self-assessed confidence
                weight = opinion.confidence
                total_weight += weight
                if opinion.is_approved:
                    approved_weight += weight

                objections_count += len(opinion.objections)

                status_str = "APPROVED" if opinion.is_approved else "REJECTED"
                logger.info(f"  -> Reviewer {reviewer.name} ({reviewer.persona}): {status_str} (Confidence: {opinion.confidence:.2f})")
            except Exception as e:
                logger.error(f"Error during critique by reviewer '{reviewer.name}': {e}")

        # Calculate Bayesian Consensus Score
        consensus_score = float(approved_weight / total_weight) if total_weight > 0 else 0.0

        # Promotion Condition:
        # Consensus score must exceed 0.70 AND there must be no critical blocker objections (e.g. Risk objections)
        risk_approved = True
        for op in opinions:
            if op.persona == "Risk Manager" and not op.is_approved:
                risk_approved = False

        is_promoted = (consensus_score >= 0.70) and risk_approved

        # Rationale compilation
        objections_summary = []
        for op in opinions:
            for obj in op.objections:
                objections_summary.append(f"[{op.persona}] {obj}")

        summary_msg = (
            f"Consensus Score: {consensus_score:.2%} | Total Objections: {objections_count} | "
            f"Risk Gate: {'PASSED' if risk_approved else 'BLOCKED'}\n"
        )
        if objections_summary:
            summary_msg += "Critical objections raised:\n  - " + "\n  - ".join(objections_summary)
        else:
            summary_msg += "Scientific panel raised no outstanding objections."

        return is_promoted, consensus_score, opinions, summary_msg
