import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class VaREvaluator(IRiskEvaluator):
    """Value at Risk (VaR) Evaluator."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        exposure = params.get("exposure", 0.0)
        volatility = context.get("market_volatility", 0.2)
        confidence_level = 1.96  # 95%

        var_value = exposure * volatility * confidence_level
        limit = 0.05 * context.get("portfolio_equity", 1000000)

        approved = var_value < limit

        return RiskResult(
            evaluator_name="VaREvaluator",
            approved=approved,
            risk_score=var_value / limit if limit > 0 else 1.0,
            confidence=0.9,
            violated_constraints=[] if approved else [f"VaR {var_value} exceeds limit {limit}"],
            evidence={"var_value": var_value, "limit": limit}
        )
