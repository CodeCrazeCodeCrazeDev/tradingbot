"""
Skill #100: Explainability Engine
=================================

Explains trading decisions in human-readable format.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class Explanation:
    """Decision explanation."""
    factor: str
    contribution: float
    description: str


@dataclass
class ExplainabilityResult:
    """Explainability result."""
    decision: str
    confidence: float
    explanations: List[Explanation]
    summary: str
    trading_signal: str


class ExplainabilityEngine:
    """Explains trading decisions."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("ExplainabilityEngine initialized")
    
    def explain(self, decision: str, factors: Dict[str, float]) -> ExplainabilityResult:
        """Explain a trading decision."""
        explanations = []
        
        # Sort factors by absolute contribution
        sorted_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)
        
        for factor, contribution in sorted_factors[:5]:
            direction = "positive" if contribution > 0 else "negative"
            explanations.append(Explanation(
                factor=factor, contribution=contribution,
                description=f"{factor} had a {direction} impact of {abs(contribution):.2f}"
            ))
        
        # Calculate confidence
        total_contribution = sum(abs(v) for v in factors.values())
        top_contribution = sum(abs(e.contribution) for e in explanations)
        confidence = top_contribution / (total_contribution + 1e-10)
        
        # Generate summary
        top_factors = [e.factor for e in explanations[:3]]
        summary = f"Decision '{decision}' was primarily driven by: {', '.join(top_factors)}"
        
        return ExplainabilityResult(
            decision=decision, confidence=confidence, explanations=explanations,
            summary=summary, trading_signal=f"EXPLAINED: {decision} ({confidence:.0%} confidence)"
        )
    
    def explain_model(self, model_name: str, feature_importance: Dict[str, float]) -> ExplainabilityResult:
        """Explain model predictions."""
        return self.explain(f"Model: {model_name}", feature_importance)
