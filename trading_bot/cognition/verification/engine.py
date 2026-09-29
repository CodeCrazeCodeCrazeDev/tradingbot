"""Independent Adversarial Subsystem attacking trade conclusions."""

import logging
from typing import Dict, Any, List, Optional
from trading_bot.cognition.state.contracts import MarketState
from .contracts import AdversarialAttackReport

logger = logging.getLogger("alphaalgo.cognition.verification")


class AdversarialSubsystem:
    """Attacks trade hypotheses with opposite incentives to detect flaws, regime destructors, and execution edge erosion."""

    def attack_trade_hypothesis(
        self,
        hypothesis_id: str,
        proposed_action: str,
        market_state: MarketState,
        simulation_result: Optional[Any] = None
    ) -> AdversarialAttackReport:
        vulnerabilities = []
        contradictions = []
        regime_destructors = []
        confidence_penalty = 0.0

        # 1. Contradictory Trend Evidence
        trend_dir = getattr(market_state, "trend_direction", "NEUTRAL")
        if proposed_action == "BUY" and trend_dir == "BEARISH":
            vulnerabilities.append("Proposing BUY directly against prevailing BEARISH trend")
            contradictions.append("Macro timeframe trend is strongly BEARISH")
            confidence_penalty += 0.30
        elif proposed_action == "SELL" and trend_dir == "BULLISH":
            vulnerabilities.append("Proposing SELL directly against prevailing BULLISH trend")
            contradictions.append("Macro timeframe trend is strongly BULLISH")
            confidence_penalty += 0.30

        # 2. Epistemic Uncertainty & Data Quality Check
        uncertainty = getattr(market_state, "uncertainty", 0.20)
        if uncertainty > 0.40:
            vulnerabilities.append(f"High epistemic uncertainty ({uncertainty:.2f}) in market state estimation")
            confidence_penalty += 0.20

        # 3. Regime Destructor Identification
        dominant_regime = market_state.get_dominant_regime() if hasattr(market_state, "get_dominant_regime") else "transitional"
        if dominant_regime == "ranging":
            regime_destructors.append("Mean-reverting ranging regime will cause severe stop-outs for trend-following entries")
        elif dominant_regime == "transitional":
            regime_destructors.append("Regime transition in progress; historical correlations may break down")

        # 4. Simulation Drawdown Attack
        if simulation_result and getattr(simulation_result, "max_drawdown_risk", 0.0) > 0.008:
            vulnerabilities.append("Counterfactual simulator detected excessive max drawdown risk")
            confidence_penalty += 0.25

        # Decision
        attack_passed = len(vulnerabilities) == 0 and confidence_penalty < 0.25
        risk_level = "CRITICAL" if confidence_penalty >= 0.50 else ("HIGH" if confidence_penalty >= 0.25 else "LOW")

        logger.info(f"Adversarial attack on '{hypothesis_id}': Passed={attack_passed}, RiskLevel={risk_level}, Penalty={confidence_penalty:.2f}")

        return AdversarialAttackReport(
            hypothesis_id=hypothesis_id,
            vulnerabilities_found=vulnerabilities,
            contradictory_evidence=contradictions,
            regime_destructors=regime_destructors,
            overfitting_risk_level=risk_level,
            execution_erosion_pips=1.5,
            attack_passed=attack_passed,
            confidence_penalty=round(confidence_penalty, 4)
        )
