import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class CorrelationEvaluator(IRiskEvaluator):
    """Correlation and Concentration Risk Evaluator."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        asset_correlation = context.get("asset_correlation", 0.5)
        sector_exposure = context.get("sector_exposure", 0.2)

        # Max sector concentration 30%
        # Max average correlation 0.7

        reasons = []
        if sector_exposure > 0.3:
            reasons.append(f"Sector exposure {sector_exposure:.2%} > 30%")
        if asset_correlation > 0.7:
            reasons.append(f"Asset correlation {asset_correlation:.2f} > 0.7")

        approved = len(reasons) == 0

        return RiskResult(
            evaluator_name="CorrelationEvaluator",
            approved=approved,
            risk_score=max(sector_exposure/0.3, asset_correlation/0.7),
            confidence=0.8,
            violated_constraints=reasons,
            evidence={"correlation": asset_correlation, "sector_exposure": sector_exposure}
        )
