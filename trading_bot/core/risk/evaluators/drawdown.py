import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class DrawdownEvaluator(IRiskEvaluator):
    """Portfolio Drawdown Evaluator."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        current_drawdown = context.get("current_drawdown", 0.0)
        max_limit = 0.15 # 15% Max drawdown

        approved = current_drawdown < max_limit

        return RiskResult(
            evaluator_name="DrawdownEvaluator",
            approved=approved,
            risk_score=current_drawdown / max_limit,
            confidence=0.95,
            violated_constraints=[] if approved else [f"Drawdown {current_drawdown:.2%} > limit {max_limit:.2%}"],
            evidence={"current_drawdown": current_drawdown}
        )
