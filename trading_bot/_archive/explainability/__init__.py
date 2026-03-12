"""
Explainability Module
Provides explanations for trading decisions and model predictions
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TradingExplainer:
    """
    Trading Decision Explainer
    
    Provides human-readable explanations for trading decisions
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.explanation_templates = {
            'buy': "Buy signal generated due to {reasons}",
            'sell': "Sell signal generated due to {reasons}",
            'hold': "Hold position due to {reasons}"
        }
        logger.info("Trading explainer initialized")
    
    def explain_decision(self, decision: Dict[str, Any]) -> str:
        """
        Explain a trading decision
        
        Args:
            decision: Trading decision dictionary
            
        Returns:
            Human-readable explanation
        """
        try:
            action = decision.get('action', 'hold')
            confidence = decision.get('confidence', 0.5)
            factors = decision.get('factors', [])
            
            reasons = ", ".join(factors) if factors else "market conditions"
            template = self.explanation_templates.get(action, "Action: {action}")
            
            explanation = template.format(reasons=reasons)
            explanation += f" (Confidence: {confidence:.1%})"
            
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return "Unable to explain decision"
    
    def explain_model_prediction(self, model_name: str, features: Dict, prediction: Any) -> str:
        """Explain model prediction"""
        try:
            feature_str = ", ".join([f"{k}={v:.2f}" for k, v in features.items()])
            return f"Model '{model_name}' predicted {prediction} based on: {feature_str}"
        except Exception as e:
            logger.error(f"Failed to explain prediction: {e}")
            return "Unable to explain prediction"


class FeatureImportanceExplainer:
    """Explains feature importance in models"""
    
    def __init__(self):
        self.feature_scores = {}
        logger.info("Feature importance explainer initialized")
    
    def calculate_importance(self, model: Any, features: List[str]) -> Dict[str, float]:
        """Calculate feature importance"""
        # Placeholder implementation
        return {feature: 0.5 for feature in features}
    
    def explain_top_features(self, n: int = 5) -> str:
        """Explain top N most important features"""
        if not self.feature_scores:
            return "No feature importance data available"
        
        sorted_features = sorted(self.feature_scores.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_features[:n]
        
        explanation = "Top features:\n"
        for feature, score in top_features:
            explanation += f"  - {feature}: {score:.2%}\n"
        
        return explanation


__all__ = ['TradingExplainer', 'FeatureImportanceExplainer']

# Auto-integrated modules
from .xai_module import DecisionExplanation, SHAPExplainer, LIMEExplainer, NaturalLanguageGenerator, ExplainableAI
