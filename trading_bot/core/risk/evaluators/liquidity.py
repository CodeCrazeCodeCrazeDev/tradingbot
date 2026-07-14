import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class LiquidityEvaluator(IRiskEvaluator):
    """Liquidity-Adjusted Risk Evaluator."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        adv = context.get("average_daily_volume", 10000000)
        order_size = params.get("exposure", 0.0)

        # Limit order size to 1% of ADV
        participation_rate = order_size / adv if adv > 0 else 1.0
        approved = participation_rate < 0.01

        return RiskResult(
            evaluator_name="LiquidityEvaluator",
            approved=approved,
            risk_score=participation_rate / 0.01 if participation_rate < 0.01 else 1.0,
            confidence=0.8,
            violated_constraints=[] if approved else [f"Participation rate {participation_rate:.4f} > 1%"],
            evidence={"participation_rate": participation_rate, "adv": adv}
        )
