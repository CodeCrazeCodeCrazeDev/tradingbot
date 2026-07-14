import logging
from typing import Any, Dict
from ..interfaces import IRiskEvaluator, RiskResult

logger = logging.getLogger(__name__)

class OODEvaluator(IRiskEvaluator):
    """Out-of-Distribution (OOD) Detector."""
    async def evaluate(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        novelty_score = context.get("market_novelty", 0.1)
        threshold = 0.8

        approved = novelty_score < threshold

        return RiskResult(
            evaluator_name="OODEvaluator",
            approved=approved,
            risk_score=novelty_score,
            confidence=0.85,
            violated_constraints=[] if approved else ["Market state is OOD"],
            evidence={"novelty_score": novelty_score}
        )
