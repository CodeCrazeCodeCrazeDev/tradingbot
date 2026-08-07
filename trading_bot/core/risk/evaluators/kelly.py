import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class KellyEvaluator(IRiskEvaluator):
    """Kelly Criterion Evaluator with Uncertainty Adjustment."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        # Mock Kelly logic using uncertainty adjustment
        win_rate = params.get("win_rate", 0.5)
        win_loss_ratio = params.get("win_loss_ratio", 1.5)
        uncertainty = context.get("model_uncertainty", 0.2)

        # Kelly: f* = (bp - q) / b where b is odds (win_loss_ratio)
        kelly_fraction = (win_loss_ratio * win_rate - (1 - win_rate)) / win_loss_ratio

        # Uncertainty adjustment: shrink toward zero based on uncertainty
        adjusted_size = max(0, kelly_fraction * (1 - uncertainty))

        return RiskResult(
            evaluator_name="KellyEvaluator",
            approved=adjusted_size > 0,
            risk_score=uncertainty,
            confidence=1 - uncertainty,
            recommended_position_size=adjusted_size,
            evidence={"raw_kelly": kelly_fraction, "uncertainty": uncertainty}
        )
