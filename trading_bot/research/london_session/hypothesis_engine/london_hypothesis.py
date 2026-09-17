"""
Hypothesis Engine & Configurable Promotion Policy for London Session Subsystem.
Models hypotheses, predictions, statistical tests, and promotion policies.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger("AlphaAlgo.LondonHypothesisEngine")


@dataclass
class LondonHypothesis:
    """
    Standardized, falsifiable hypothesis object.
    Matches the structure: Hypothesis -> Features -> Prediction -> Statistical test -> Result.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    economic_rationale: str = ""
    feature_columns: List[str] = field(default_factory=list)
    falsification_tests: List[str] = field(default_factory=list)
    status: str = "Proposed"  # Proposed, Accepted, Rejected, Retired
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PromotionPolicy:
    """
    Configurable Promotion Policy for promoting edges from Candidates to Validated.
    Replaces brittle hardcoded values with rigorous, customizable parameters.
    """
    min_observations: int = 150
    max_pbo: float = 0.15          # Probability of Backtest Overfitting limit
    min_dsr: float = 1.6           # Deflated Sharpe Ratio limit
    max_drawdown: float = 0.15     # Max drawdown threshold
    min_calibration: float = 0.80  # Calibration success rate
    min_expected_return: float = 0.005 # Min return per trade (e.g. 50 pips / 0.5%)
    max_turnover: float = 0.85     # Max turnover target
    max_market_impact: float = 5.0 # Max slippage market impact in pips


class LondonHypothesisEngine:
    """
    Generates and processes falsifiable hypotheses for London session behaviors.
    Runs statistical tests to accept or reject them.
    """

    def __init__(self) -> None:
        self.hypotheses: Dict[str, LondonHypothesis] = {}

    def propose_london_hypothesis(self, name: str, description: str, rationale: str,
                                 features: List[str], falsifications: List[str]) -> LondonHypothesis:
        """Structured proposal of a new falsifiable hypothesis."""
        hyp = LondonHypothesis(
            name=name,
            description=description,
            economic_rationale=rationale,
            feature_columns=features,
            falsification_tests=falsifications
        )
        self.hypotheses[hyp.id] = hyp
        logger.info(f"Proposed London Session Hypothesis: '{name}' (ID: {hyp.id})")
        return hyp

    def falsify_hypothesis_regression(self, hyp: LondonHypothesis, df: pd.DataFrame,
                                     target_col: str = "log_ret", p_value_threshold: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
        """
        Runs a regression/correlation statistical check to falsify the hypothesis.
        If feature coefficients do not achieve statistically significant p-values,
        the hypothesis is rejected.
        """
        # Ensure target and features are present
        cols = hyp.feature_columns + [target_col]
        missing = [col for col in cols if col not in df.columns]
        if missing:
            return False, {"error": f"Missing columns in dataset: {missing}"}

        clean_df = df[cols].dropna()
        if len(clean_df) < 50:
            return False, {"error": "Sample size too small for statistical test (<50 rows)"}

        # Simple multiple regression via numpy least squares
        y = clean_df[target_col].values
        X = clean_df[hyp.feature_columns].values
        # Add intercept
        X_design = np.column_stack([np.ones_like(y), X])

        # Beta estimation
        beta, residuals, rank, s = np.linalg.lstsq(X_design, y, rcond=None)

        # Calculate standard errors of beta
        n = len(y)
        k = X_design.shape[1]
        df_residual = n - k
        if df_residual <= 0:
            return False, {"error": "Degrees of freedom are negative or zero"}

        mse = np.sum((y - X_design.dot(beta))**2) / df_residual
        # Variance-covariance matrix of betas
        try:
            cov_beta = mse * np.linalg.inv(X_design.T.dot(X_design))
            se_beta = np.sqrt(np.diagonal(cov_beta))
        except np.linalg.LinAlgError:
            se_beta = np.ones(k) * 1e-4

        # t-statistics and approximate p-values
        t_stats = beta / (se_beta + 1e-12)
        # Approximate p-value (using standard normal cumulative proxy)
        p_values = 2 * (1 - 0.5 * (1.0 + np.tanh(np.abs(t_stats) / np.sqrt(2.0))))

        # Evaluate if any key features passed the p-value test (excluding intercept)
        significant_features = []
        for i, feat in enumerate(hyp.feature_columns):
            p_val = p_values[i + 1]
            if p_val < p_value_threshold:
                significant_features.append((feat, float(p_val)))

        passed = len(significant_features) > 0
        hyp.status = "Accepted" if passed else "Rejected"

        results = {
            "hypothesis_id": hyp.id,
            "sample_size": n,
            "coefficients": {feat: float(beta[i+1]) for i, feat in enumerate(hyp.feature_columns)},
            "p_values": {feat: float(p_values[i+1]) for i, feat in enumerate(hyp.feature_columns)},
            "significant_features": significant_features,
            "status": hyp.status,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Hypothesis {hyp.id[:12]} falsification complete. Status: {hyp.status}")
        return passed, results
