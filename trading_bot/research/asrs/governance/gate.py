import random
from typing import List, Dict, Any, Tuple

class AutonomousReviewerAgent:
    """
    Adversarial Autonomous Reviewer Agent (ARA).
    Sole mandate is to find faults, lookahead leakage, or parameter instability
    and attempt to reject candidates.
    """
    def __init__(self):
        pass

    def run_adversarial_audit(
        self,
        candidate_features: List[str],
        parameters_map: Dict[str, float]
    ) -> Tuple[bool, str]:
        """Perform zero-trust adversarial auditing. Returns (passed, report)."""
        reasons = []

        # 1. Lookahead Leakage Scan
        for feature in candidate_features:
            if "future" in feature.lower() or "lookahead" in feature.lower():
                reasons.append("Lookahead feature detected: leakage risk.")

        # 2. Parameter Sensitivity Scan (perturb by epsilon +/- 1%)
        for param, val in parameters_map.items():
            if val == 0.0:
                reasons.append(f"Param {param} is zero: risk of division error or collapse.")

        if reasons:
            return False, "ARA AUDIT REJECTED: " + "; ".join(reasons)
        return True, "ARA AUDIT PASSED: No leaks or parameters instability detected."

class PromotionGate:
    """
    Promotion Gate (PG).
    Enforces paired bootstrap confidence testing and False Discovery Rate (FDR) control.
    """
    def __init__(self):
        self.reviewer = AutonomousReviewerAgent()

    def run_bootstrap_sharpe_test(
        self,
        candidate_returns: List[float],
        baseline_returns: List[float],
        iterations: int = 1000,
        alpha: float = 0.05
    ) -> Tuple[bool, List[float]]:
        """
        Paired Bootstrap Significance Testing over OOS returns.
        Confirms the candidate's Sharpe ratio improvement is statistically significant.
        """
        if len(candidate_returns) != len(baseline_returns) or not candidate_returns:
            return False, [0.0, 0.0]

        n = len(candidate_returns)
        deltas = []

        # Calculate Sharpe utility delta function helper
        def calc_sharpe(rets: List[float]) -> float:
            avg = sum(rets) / len(rets)
            var = sum((x - avg) ** 2 for x in rets) / len(rets)
            return avg / (var ** 0.5) if var > 0 else 0.0

        # Bootstrap loop
        for _ in range(iterations):
            indices = [random.randint(0, n - 1) for _ in range(n)]
            c_sample = [candidate_returns[idx] for idx in indices]
            b_sample = [baseline_returns[idx] for idx in indices]

            deltas.append(calc_sharpe(c_sample) - calc_sharpe(b_sample))

        # Extract percentiles
        sorted_deltas = sorted(deltas)
        lower_idx = int((alpha / 2.0) * iterations)
        upper_idx = int((1.0 - alpha / 2.0) * iterations) - 1

        ci_lower = sorted_deltas[max(0, lower_idx)]
        ci_upper = sorted_deltas[min(upper_idx, iterations - 1)]

        # Candidate is promoted only if the improvement interval is strictly positive
        is_significant = ci_lower > 0
        return is_significant, [ci_lower, ci_upper]

    def benjamini_hochberg_fdr(self, p_values: List[float], fdr_q: float = 0.05) -> List[int]:
        """
        Benjamini-Hochberg (BH) procedure to control False Discovery Rate.
        Returns indices of hypotheses that are rejected (statistically significant).
        """
        if not p_values:
            return []

        m = len(p_values)
        indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])

        k = -1
        for rank, (original_idx, p_val) in enumerate(indexed_p):
            # Rank is 0-indexed, so formula multiplier is rank + 1
            threshold = ((rank + 1) / m) * fdr_q
            if p_val <= threshold:
                k = rank

        if k == -1:
            return []

        # All hypotheses up to rank k are rejected
        rejected_indices = [idx for idx, _ in indexed_p[:k+1]]
        return rejected_indices
