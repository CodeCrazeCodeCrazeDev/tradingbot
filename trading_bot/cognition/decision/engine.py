"""Decision Intelligence Engine with ABSTAIN support and Rigid Risk Gatekeeper."""

import logging
from typing import Dict, Any, Optional, List
from trading_bot.cognition.state.contracts import MarketState
from trading_bot.cognition.verification.contracts import AdversarialAttackReport
from .contracts import CognitiveAction, DecisionProposal, RiskGateResult

logger = logging.getLogger("alphaalgo.cognition.decision")


class DecisionIntelligenceEngine:
    """Synthesizes observations, state, simulations, and adversarial attacks into a DecisionProposal."""

    def synthesize_decision(
        self,
        decision_id: str,
        market_state: MarketState,
        simulation_result: Optional[Any] = None,
        adversarial_report: Optional[AdversarialAttackReport] = None,
        raw_signal: str = "NEUTRAL"
    ) -> DecisionProposal:
        # Check abstention triggers
        data_quality = getattr(market_state, "data_quality_score", 1.0)
        uncertainty = getattr(market_state, "uncertainty", 0.20)

        # 1. First-class ABSTAIN trigger conditions
        if data_quality < 0.80:
            return DecisionProposal(
                decision_id=decision_id,
                action=CognitiveAction.ABSTAIN,
                instrument=market_state.instrument,
                uncertainty=uncertainty,
                confidence=0.0,
                supporting_evidence=[],
                contradicting_evidence=[f"Data quality too low ({data_quality:.2f})"],
                invalidation_conditions=["Data quality restored above 0.80"]
            )

        if uncertainty > 0.45:
            return DecisionProposal(
                decision_id=decision_id,
                action=CognitiveAction.ABSTAIN,
                instrument=market_state.instrument,
                uncertainty=uncertainty,
                confidence=0.0,
                supporting_evidence=[],
                contradicting_evidence=[f"Excessive epistemic uncertainty ({uncertainty:.2f})"],
                invalidation_conditions=["Uncertainty drops below 0.45"]
            )

        if adversarial_report and not adversarial_report.attack_passed:
            return DecisionProposal(
                decision_id=decision_id,
                action=CognitiveAction.ABSTAIN,
                instrument=market_state.instrument,
                uncertainty=uncertainty,
                confidence=0.0,
                supporting_evidence=[],
                contradicting_evidence=adversarial_report.vulnerabilities_found,
                invalidation_conditions=["Adversarial vulnerabilities remediated"]
            )

        # 2. Derive trade proposal if signals align
        trend_dir = getattr(market_state, "trend_direction", "NEUTRAL")
        if raw_signal == "BUY" and trend_dir == "BULLISH":
            action = CognitiveAction.BUY
            direction = "LONG"
        elif raw_signal == "SELL" and trend_dir == "BEARISH":
            action = CognitiveAction.SELL
            direction = "SHORT"
        else:
            action = CognitiveAction.WAIT
            direction = None

        ev = simulation_result.expected_value if simulation_result else 0.0
        win_p = simulation_result.win_probability if simulation_result else 0.50

        return DecisionProposal(
            decision_id=decision_id,
            action=action,
            instrument=market_state.instrument,
            direction=direction,
            proposed_position_size=1.0 if action in (CognitiveAction.BUY, CognitiveAction.SELL) else 0.0,
            expected_value=ev,
            uncertainty=uncertainty,
            confidence=round(win_p * (1.0 - uncertainty), 4),
            calibrated_probability=round(win_p, 4),
            regime=market_state.get_dominant_regime() if hasattr(market_state, "get_dominant_regime") else "transitional",
            supporting_evidence=[f"Trend direction is {trend_dir}"],
            contradicting_evidence=[],
            invalidation_conditions=["Market structure break"]
        )


class RiskGatekeeper:
    """Rigid non-bypassable Risk Gatekeeper with final authority over execution."""

    def __init__(self, max_position_size: float = 5.0, max_daily_drawdown_pct: float = 0.03):
        self.max_position_size = max_position_size
        self.max_daily_drawdown_pct = max_daily_drawdown_pct

    def evaluate_proposal(self, proposal: DecisionProposal, current_daily_drawdown_pct: float = 0.0) -> RiskGateResult:
        violations = []

        # 1. Action is ABSTAIN or WAIT
        if proposal.action in (CognitiveAction.ABSTAIN, CognitiveAction.WAIT, CognitiveAction.HOLD):
            return RiskGateResult(
                proposal_id=proposal.decision_id,
                authorized=True,
                authorized_action=proposal.action,
                authorized_size=0.0,
                rejection_reason=None
            )

        # 2. Max Daily Drawdown Gate
        if current_daily_drawdown_pct >= self.max_daily_drawdown_pct:
            violations.append(f"Daily drawdown limit reached ({current_daily_drawdown_pct:.2%} >= {self.max_daily_drawdown_pct:.2%})")

        # 3. Position Size Limit Gate
        if proposal.proposed_position_size > self.max_position_size:
            violations.append(f"Position size {proposal.proposed_position_size:.2f} exceeds max allowed {self.max_position_size:.2f}")

        # 4. Stop Loss Mandatory Check
        if proposal.action in (CognitiveAction.BUY, CognitiveAction.SELL) and proposal.stop_loss is None:
            # Enforce stop-loss requirement or default risk cap
            violations.append("Mandatory Stop-Loss requirement missing from proposal")

        if violations:
            logger.warning(f"RiskGatekeeper VETOED decision proposal '{proposal.decision_id}': {violations}")
            return RiskGateResult(
                proposal_id=proposal.decision_id,
                authorized=False,
                authorized_action=CognitiveAction.ABSTAIN,
                authorized_size=0.0,
                rejection_reason="Hard Risk Limits Violated",
                hard_limit_violations=violations
            )

        return RiskGateResult(
            proposal_id=proposal.decision_id,
            authorized=True,
            authorized_action=proposal.action,
            authorized_size=proposal.proposed_position_size,
            rejection_reason=None
        )
