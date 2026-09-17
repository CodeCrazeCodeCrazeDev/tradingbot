"""
Hypothesis Generator for Research OS.
Translates unstructured or semi-structured research ideas and papers into testable, regime-aware Hypotheses.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from trading_bot.research.core.interfaces import HypothesisObject, ResearchPaper


class HypothesisGenerator:
    """
    Translates research papers, claims, or market beliefs into structured,
    empirically testable HypothesisObjects.
    """

    def generate_from_paper(self, paper: ResearchPaper, market: str = "EURUSD", timeframe: str = "15m") -> HypothesisObject:
        """
        Derives a testable quantitative hypothesis from a scientific paper's content.
        """
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:8]}"

        # Determine expected mechanism and assumptions based on paper provider or properties
        category = paper.category.lower()

        if "microstructure" in category or "vpin" in paper.paper_id:
            assumptions = [
                "Order flow imbalance is highly predictive of short-term price pressure.",
                "Liquidity providers adjust spreads asymmetrically in response to toxic order flow."
            ]
            expected_mechanism = (
                "High Volume-Synchronized Probability of Toxicity (VPIN) signals "
                "heightened inventory risk, triggering a rapid reversion in short-term quotes."
            )
            measurable_prediction = (
                "When VPIN exceeds its 90th percentile, 15-minute forward returns "
                "will revert within 3 periods with a t-statistic absolute value > 2.0."
            )
            failure_conditions = [
                "The correlation between high VPIN and subsequent returns is statistically indistinguishable from zero.",
                "Trading costs/spreads fully consume the premium."
            ]
        elif "active_inference" in category or "logact" in paper.paper_id:
            assumptions = [
                "The market behaves as a dynamic, non-stationary agent seeking to minimize free energy.",
                "Policy transitions can be modeled as active inference actions."
            ]
            expected_mechanism = (
                "The self-proposed transformation (RSEA) manages risk exposure by dynamically "
                "re-calibrating subjective transition probabilities under regime volatility."
            )
            measurable_prediction = (
                "Active inference-driven dynamic hedging reduces maximum drawdowns by "
                "at least 15% relative to a static equal-weight strategy during high-volatility regimes."
            )
            failure_conditions = [
                "Dynamic policy adaptation incurs excessive transaction turnover.",
                "Subjective beliefs suffer from extreme over-fitting to short-term trends."
            ]
        elif "portfolio" in category or "hrp" in paper.paper_id:
            assumptions = [
                "Asset covariance matrices exhibit stable hierarchical cluster structures.",
                "Optimal transport metrics are robust to sample out-of-sample noise."
            ]
            expected_mechanism = (
                "Wasserstein distances between historical and live portfolios yield "
                "stable, noise-resistant risk parity allocations without matrix inversion."
            )
            measurable_prediction = (
                "Hierarchical Risk Parity using Wasserstein distances achieves a 10% "
                "lower out-of-sample portfolio volatility compared to traditional risk parity."
            )
            failure_conditions = [
                "Hierarchical cluster boundaries dissolve during high-correlation market shocks.",
                "Out-of-sample tracking error exceeds 5% annualized."
            ]
        else:
            # General baseline
            assumptions = [
                "Price movements exhibit statistically significant, non-random autocorrelation during high liquidity hours.",
                "Market inefficiencies are periodically exploitable."
            ]
            expected_mechanism = f"Exploit anomalies and information structural delays referenced in '{paper.title}'."
            measurable_prediction = "The generated alpha signal has a positive Information Coefficient (IC > 0.02) over a 252-day walk-forward window."
            failure_conditions = [
                "Signal decay occurs faster than execution latency.",
                "Predictive power drops below p-value threshold of 0.05."
            ]

        return HypothesisObject(
            hypothesis_id=hypothesis_id,
            description=f"Empirical test of: {paper.title}",
            assumptions=assumptions,
            market=market,
            timeframe=timeframe,
            expected_mechanism=expected_mechanism,
            measurable_prediction=measurable_prediction,
            failure_conditions=failure_conditions,
            lineage_paper_id=paper.paper_id,
            status="draft",
            metadata={
                "source_paper_title": paper.title,
                "generated_by": "HypothesisGeneratorV1",
                "original_category": paper.category
            }
        )

    def generate_custom(
        self,
        description: str,
        assumptions: List[str],
        market: str,
        timeframe: str,
        expected_mechanism: str,
        measurable_prediction: str,
        failure_conditions: List[str],
        lineage_paper_id: Optional[str] = None
    ) -> HypothesisObject:
        """Manually generate a well-formed testable HypothesisObject."""
        return HypothesisObject(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            description=description,
            assumptions=assumptions,
            market=market,
            timeframe=timeframe,
            expected_mechanism=expected_mechanism,
            measurable_prediction=measurable_prediction,
            failure_conditions=failure_conditions,
            lineage_paper_id=lineage_paper_id,
            status="draft"
        )
