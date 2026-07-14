import logging
import numpy as np
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class CVaREvaluator(IRiskEvaluator):
    """Conditional Value at Risk (CVaR) / Expected Shortfall Evaluator."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        exposure = params.get("exposure", 0.0)
        volatility = context.get("market_volatility", 0.2)
        confidence_level = 0.95

        # Simple Gaussian CVaR approximation: ES = mu + sigma * (phi(Phi^-1(alpha)) / (1-alpha))
        # For mu=0: ES = sigma * (pdf(z_alpha) / (1-alpha))
        z_alpha = 1.645 # 95%
        pdf_z = 0.103 # approx pdf(1.645)
        cvar_factor = pdf_z / (1 - confidence_level)

        cvar_value = exposure * volatility * cvar_factor
        limit = 0.08 * context.get("portfolio_equity", 1000000) # ES limit is usually higher than VaR

        approved = cvar_value < limit

        return RiskResult(
            evaluator_name="CVaREvaluator",
            approved=approved,
            risk_score=cvar_value / limit if limit > 0 else 1.0,
            confidence=0.85,
            violated_constraints=[] if approved else [f"CVaR {cvar_value:.2f} exceeds limit {limit:.2f}"],
            evidence={"cvar_value": cvar_value, "limit": limit}
        )
