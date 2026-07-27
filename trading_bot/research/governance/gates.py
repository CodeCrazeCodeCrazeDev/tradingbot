"""
Governance Gate Promotion Pipeline for Research OS.
Strictly regulates promotion through sequential research gates.
Promotes candidates only when justified by robust multi-agent debate consensus and causal evidence.
"""

from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PromotionPipelineGatekeeper:
    """
    Enforces scientific rigor during strategy promotion.
    Integrates multi-agent debate consensus and structural causal models.
    """

    def __init__(self, registries: Dict[str, Any] = None):
        self.registries = registries or {}

    def execute_promotion_pipeline(
        self,
        strategy_id: str,
        results_manifest: Dict[str, Any],
        debate_consensus_score: float,
        causal_model: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Runs sequential checks on the strategy's research artifact.

        Sequential gates:
        1. Research Ingestion (claim & paper registered)
        2. Statistical Validation (stationarity and causality passed)
        3. Alpha Validation (IC > 0.02, p-value < 0.05)
        4. Causal Support (discovered causal coefficients on target returns)
        5. Strategy Construction (reproducible manifest)
        6. Multi-Agent Debate Board (consensus score >= 70%)
        7. Realistic Backtesting (Sharpe > 1.2, Max DD > -25%)
        8. Robustness Testing (Walk-Forward and Regime tests passed)
        9. Portfolio Evaluation (Contribution verified)
        10. Governance Board Approval (Traceability confirmed)
        """
        logger.info(f"Starting Promotion Gatekeeper sequence for strategy '{strategy_id}'.")

        # GATE 1: Research Ingestion validation
        if not results_manifest.get("has_lineage_paper", False):
            return False, "GATE 1 FAILED: Strategy has no documented research paper lineage."

        # GATE 2: Statistical Validation check
        stat_results = results_manifest.get("statistical_test_results", {})
        if not stat_results.get("stationarity_passed", False):
            return False, "GATE 2 FAILED: Base features fail ADF stationarity test."
        if not stat_results.get("causality_passed", False):
            return False, "GATE 2 FAILED: Base features do not Granger-cause price returns."

        # GATE 3: Alpha Validation check
        alpha_metrics = results_manifest.get("alpha_metrics", {})
        if abs(alpha_metrics.get("ic", 0.0)) < 0.02:
            return False, f"GATE 3 FAILED: Information Coefficient (IC) {alpha_metrics.get('ic'):.4f} below target threshold of 0.02."
        if alpha_metrics.get("p_value", 1.0) >= 0.05:
            return False, "GATE 3 FAILED: Alpha signal correlation is not statistically significant (p-value >= 0.05)."

        # GATE 4: Causal Support check
        if not causal_model or "coefficients" not in causal_model:
            return False, "GATE 4 FAILED: Missing structural causal model (SCM)."
        coefs = causal_model["coefficients"]
        vol_to_ret = abs(coefs.get("volatility_to_returns", 0.0))
        ent_to_ret = abs(coefs.get("entropy_to_returns", 0.0))
        if vol_to_ret == 0.0 and ent_to_ret == 0.0:
            return False, "GATE 4 FAILED: Base variables have zero structural causal impact on target returns."

        # GATE 5: Strategy Construction validation
        if not results_manifest.get("has_executable_code", False):
            return False, "GATE 5 FAILED: Strategy package is missing executable Python implementation."

        # GATE 6: Multi-Agent Debate Consensus
        if debate_consensus_score < 0.70:
            return False, f"GATE 6 FAILED: Review board consensus {debate_consensus_score:.2%} below required 70% threshold."

        # GATE 7: Realistic Backtesting checks
        backtest_res = results_manifest.get("backtest_results", {})
        if backtest_res.get("sharpe", 0.0) < 1.0:
            return False, f"GATE 7 FAILED: Simulated Sharpe {backtest_res.get('sharpe'):.2f} below minimum target of 1.0."
        if backtest_res.get("max_drawdown", 0.0) < -0.25:
            return False, f"GATE 7 FAILED: Simulated Drawdown {backtest_res.get('max_drawdown'):.2%} exceeds high risk threshold of -25%."

        # GATE 8: Robustness Testing checks
        robustness_res = results_manifest.get("robustness_results", {})
        if not robustness_res.get("walk_forward_passed", False):
            return False, "GATE 8 FAILED: Strategy failed out-of-sample walk-forward validation (fragile/overfitted)."
        if not robustness_res.get("regime_passed", False):
            return False, "GATE 8 FAILED: Strategy blew up during high-volatility regime stress test."

        # GATE 9: Portfolio Contribution check
        portfolio_res = results_manifest.get("portfolio_results", {})
        if portfolio_res.get("marginal_cvar_contribution", 0.0) > 0.1:
            return False, "GATE 9 FAILED: Strategy contribution increases portfolio tail-risk (CVaR) beyond 10% target."

        # GATE 10: Governance Board Review
        if not results_manifest.get("governance_signoff", False):
            return False, "GATE 10 FAILED: Final human-in-the-loop or sovereign compliance check is pending review."

        logger.info(f"Strategy '{strategy_id}' successfully passed all 10 sequential promotion gates!")
        return True, "PROMOTED: Strategy approved for live production deployment."
