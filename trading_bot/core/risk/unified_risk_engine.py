import logging
import asyncio
from typing import Any, Dict, List, Optional
from .interfaces import IRiskEvaluator, RiskResult
from .evaluators.kelly import KellyEvaluator
from .evaluators.var import VaREvaluator
from .evaluators.cvar import CVaREvaluator
from .evaluators.ood import OODEvaluator
from .evaluators.liquidity import LiquidityEvaluator
from .evaluators.drawdown import DrawdownEvaluator
from .evaluators.correlation import CorrelationEvaluator
from .evaluators.execution import ExecutionRiskEvaluator
from .evaluators.model_risk import ModelRiskEvaluator

logger = logging.getLogger(__name__)

class UnifiedRiskEngine:
    """
    Compositional Risk Engine - Authoritative singleton for AlphaAlgo UCA V5.
    Orchestrates specialized evaluators for VaR, Kelly, OOD, Liquidity, Drawdown, etc.
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UnifiedRiskEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.evaluators: List[IRiskEvaluator] = [
            KellyEvaluator(),
            VaREvaluator(),
            CVaREvaluator(),
            OODEvaluator(),
            LiquidityEvaluator(),
            DrawdownEvaluator(),
            CorrelationEvaluator(),
            ExecutionRiskEvaluator(),
            ModelRiskEvaluator()
        ]
        self._initialized = True
        logger.info("UnifiedRiskEngine initialized with institutional compositional evaluators")

    async def evaluate_risk(self, params: Dict[str, Any], context: Dict[str, Any]) -> RiskResult:
        """Runs all evaluators and aggregates results."""
        logger.info("UnifiedRiskEngine: Starting institutional risk evaluation")

        tasks = [e.evaluate(params, context) for e in self.evaluators]
        results = await asyncio.gather(*tasks)

        # Aggregation Logic
        all_approved = all(r.approved for r in results)
        max_risk_score = max((r.risk_score for r in results), default=0.0)
        violated = [c for r in results for c in r.violated_constraints]

        # Find minimum recommended size among all evaluators
        sizes = [r.recommended_position_size for r in results if r.recommended_position_size is not None]
        final_size = min(sizes) if sizes else None

        # Unified confidence (minimum of all evaluators)
        min_confidence = min((r.confidence for r in results), default=0.0)

        aggregate_result = RiskResult(
            evaluator_name="UnifiedRiskEngine",
            approved=all_approved,
            risk_score=max_risk_score,
            confidence=min_confidence,
            violated_constraints=violated,
            recommended_position_size=final_size,
            evidence={r.evaluator_name: r.evidence for r in results},
            emergency_stop=any(r.emergency_stop for r in results)
        )

        if not all_approved:
            logger.warning(f"Risk Evaluation REJECTED: {violated}")

        return aggregate_result

# Global Access Point
risk_engine = UnifiedRiskEngine()
