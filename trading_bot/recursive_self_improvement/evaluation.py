import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class EvaluationEngine:
    """
    Measures and validates improvements across multiple dimensions.
    Ensures that improvements are statistically significant and robust.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_confidence = self.config.get("min_confidence", 0.95)
        self.min_improvement_threshold = self.config.get("min_improvement", 0.02)

    def evaluate_improvement(self, baseline_metrics: Dict[str, float], candidate_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare baseline vs candidate performance.
        Returns a detailed evaluation report.
        """
        report = {
            "is_improved": False,
            "confidence_score": 0.0,
            "improvements": {},
            "regressions": [],
            "overall_score": 0.0,
            "recommendation": "reject"
        }

        # Calculate delta for each metric
        total_delta = 0.0
        for metric, baseline_val in baseline_metrics.items():
            if metric in candidate_metrics:
                candidate_val = candidate_metrics[metric]
                delta = (candidate_val - baseline_val) / abs(baseline_val) if baseline_val != 0 else 0
                report["improvements"][metric] = delta

                # Weight based on metric importance (simplified)
                weight = 1.0
                if "sharpe" in metric.lower(): weight = 2.0
                if "pnl" in metric.lower(): weight = 1.5
                if "drawdown" in metric.lower():
                    weight = 2.0
                    delta = -delta # Lower drawdown is better

                total_delta += delta * weight

                if delta < -0.05: # Regression threshold
                    report["regressions"].append(metric)

        # Overall score (normalized improvement)
        report["overall_score"] = total_delta

        # Decision logic
        if total_delta > self.min_improvement_threshold and not report["regressions"]:
            report["is_improved"] = True
            report["recommendation"] = "approve"
        elif total_delta > 0 and len(report["regressions"]) < 2:
            report["recommendation"] = "needs_further_testing"

        return report

    def assess_robustness(self, regime_results: Dict[str, Dict[str, float]]) -> float:
        """
        Assess how well an improvement performs across different market regimes.
        Returns a robustness score (0.0 to 1.0).
        """
        if not regime_results:
            return 0.0

        scores = []
        for regime, metrics in regime_results.items():
            # Calculate a basic performance score for each regime
            sharpe = metrics.get("sharpe_ratio", 0)
            win_rate = metrics.get("win_rate", 0)
            scores.append(sharpe * win_rate)

        if not scores:
            return 0.0

        # Robustness is inversely proportional to variance across regimes
        avg_score = np.mean(scores)
        std_score = np.std(scores)

        robustness = 1.0 - (std_score / abs(avg_score)) if avg_score != 0 else 0
        return max(0.0, min(1.0, robustness))

    def run_statistical_check(self, baseline_samples: List[float], candidate_samples: List[float]) -> Dict[str, Any]:
        """
        Perform t-test or similar to check for statistical significance.
        """
        from scipy import stats

        if len(baseline_samples) < 2 or len(candidate_samples) < 2:
            return {"significant": False, "p_value": 1.0}

        t_stat, p_value = stats.ttest_ind(candidate_samples, baseline_samples)

        return {
            "significant": p_value < (1 - self.min_confidence),
            "p_value": p_value,
            "t_stat": t_stat
        }
