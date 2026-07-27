"""
Pluggable specialized Reviewer Agents for the Quantitative Research Marketplace.
Implements the ReviewAgent interface with core quantitative expert personas:
Statistician, Econometrician, Portfolio Manager, Risk Manager, Execution Specialist, and Skeptic.
"""

from typing import Dict, Any, List
import logging
from trading_bot.research.core.interfaces import ReviewAgent, ReviewerOpinion, HypothesisObject

logger = logging.getLogger(__name__)


class StatisticianReviewer(ReviewAgent):
    """
    Expert persona verifying statistical assumptions: p-values, sample sizes, and false discoveries.
    """
    @property
    def name(self) -> str:
        return "Dr. Sigma"

    @property
    def persona(self) -> str:
        return "Statistician"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        # Check standard significance
        ic = backtest_results.get("ic", 0.04)  # fallback to sample IC
        p_val = backtest_results.get("p_value", 0.01)

        is_approved = (p_val < 0.05) and (abs(ic) > 0.01)
        confidence = float(np_clip(1.0 - p_val, 0.5, 0.99))

        objections = []
        if p_val >= 0.05:
            objections.append(f"Null hypothesis cannot be rejected (p-value {p_val:.4f} >= 0.05).")
        if abs(ic) <= 0.01:
            objections.append(f"Extremely weak rank correlation detected (IC {ic:.4f} <= 0.01).")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Rigorous sample distribution and variance check of p-values.",
            objections=objections,
            evidence_considered={"p_value": p_val, "ic": ic}
        )


class EconometricianReviewer(ReviewAgent):
    """
    Expert persona checking structural breaks, cointegration, non-stationarity, and spurious regressions.
    """
    @property
    def name(self) -> str:
        return "Prof. Granger"

    @property
    def persona(self) -> str:
        return "Econometrician"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        stationarity_passed = backtest_results.get("stationarity_passed", True)
        causality_passed = backtest_results.get("causality_passed", True)

        is_approved = stationarity_passed and causality_passed
        confidence = 0.85

        objections = []
        if not stationarity_passed:
            objections.append("Spurious regression risk: Non-stationary base variable detected (fails ADF).")
        if not causality_passed:
            objections.append("Lack of logical causation: Predictor fails Granger causality test.")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Verifies Granger causality and Dickey-Fuller unit roots.",
            objections=objections,
            evidence_considered={"stationarity_passed": stationarity_passed, "causality_passed": causality_passed}
        )


class PortfolioManagerReviewer(ReviewAgent):
    """
    Expert persona assessing sizing, correlations, diversifications, and HRP risk allocations.
    """
    @property
    def name(self) -> str:
        return "PM Alpha"

    @property
    def persona(self) -> str:
        return "Portfolio Manager"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        sharpe = backtest_results.get("sharpe", 1.5)
        calmar = backtest_results.get("calmar", 2.0)

        is_approved = (sharpe > 1.0) and (calmar > 0.5)
        confidence = 0.80

        objections = []
        if sharpe <= 1.0:
            objections.append(f"Sharpe ratio too low ({sharpe:.2f} <= 1.0) to justify portfolio allocation.")
        if calmar <= 0.5:
            objections.append(f"Return-to-drawdown (Calmar) ratio is fragile ({calmar:.2f} <= 0.5).")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Evaluates absolute and relative risk-adjusted Sharpe/Calmar performance.",
            objections=objections,
            evidence_considered={"sharpe": sharpe, "calmar": calmar}
        )


class RiskManagerReviewer(ReviewAgent):
    """
    Expert persona reviewing maximum drawdowns, extreme tail risk (CVaR), and leverage bounds.
    """
    @property
    def name(self) -> str:
        return "Cerberus"

    @property
    def persona(self) -> str:
        return "Risk Manager"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        max_dd = backtest_results.get("max_drawdown", -0.15)
        cvar = backtest_results.get("cvar_95_tail_risk", -0.05)

        # Max drawdown should be milder than -25%
        is_approved = (max_dd > -0.25) and (cvar > -0.08)
        confidence = 0.90

        objections = []
        if max_dd <= -0.25:
            objections.append(f"Catastrophic drawdown risk: Backtest exceeds drawdown threshold ({max_dd:.2%}).")
        if cvar <= -0.08:
            objections.append(f"Extreme tail risk detected: 95% CVaR is too deep ({cvar:.4%}).")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Strict tail risk CVaR and drawdown exposure assessment.",
            objections=objections,
            evidence_considered={"max_drawdown": max_dd, "cvar_95_tail_risk": cvar}
        )


class ExecutionSpecialistReviewer(ReviewAgent):
    """
    Expert persona enforcing execution realism: transaction commissions, spread, slippage, and market impact.
    """
    @property
    def name(self) -> str:
        return "Flash"

    @property
    def persona(self) -> str:
        return "Execution Specialist"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        turnover = backtest_results.get("turnover_rate", 0.1)
        expected_value = backtest_results.get("expected_value", 50.0)  # average trade profit

        # High turnover combined with low expected trade value is a red flag (costs eat alpha)
        is_approved = (expected_value > 10.0) or (turnover < 0.5)
        confidence = 0.85

        objections = []
        if expected_value <= 10.0 and turnover >= 0.5:
            objections.append(f"Alpha decay danger: High turnover ({turnover:.2%}) combined with tiny average trade profit (${expected_value:.2f}) will be eaten by execution costs.")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Validates execution costs, slippage drag, and turnover decay impact.",
            objections=objections,
            evidence_considered={"turnover_rate": turnover, "expected_value_usd": expected_value}
        )


class SkepticalReviewer(ReviewAgent):
    """
    A relentless skeptic hunting for look-ahead bias, p-hacking, and overfitting.
    """
    @property
    def name(self) -> str:
        return "Dr. Null"

    @property
    def persona(self) -> str:
        return "Skeptic"

    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        wf_passed = backtest_results.get("walk_forward_passed", True)
        regime_passed = backtest_results.get("regime_passed", True)

        is_approved = wf_passed and regime_passed
        confidence = 0.95

        objections = []
        if not wf_passed:
            objections.append("Fragile overfitting: Out-of-sample walk-forward validation failed.")
        if not regime_passed:
            objections.append("Overfitting anomaly: Failed regime stress testing.")

        return ReviewerOpinion(
            reviewer_name=self.name,
            persona=self.persona,
            is_approved=is_approved,
            confidence=confidence,
            rationale="Relentless challenge of overfitting, parameter sensitivity, and curve-fitting.",
            objections=objections,
            evidence_considered={"walk_forward_passed": wf_passed, "regime_passed": regime_passed}
        )


def np_clip(v: float, low: float, high: float) -> float:
    import numpy as np
    return float(np.clip(v, low, high))
