"""
Phase 7: Explainability & Trust
Makes trading decisions transparent and trustworthy
"""

# Try to import with full features, fall back to basic implementation
try:
    from .feature_attribution import FeatureAttributor
    _captum_available = True
except ImportError:
    # Stub implementation without captum
    class FeatureAttributor:
        """Stub implementation of FeatureAttributor"""
        def __init__(self, *args, **kwargs):
            pass
        def attribute(self, *args, **kwargs):
            return {}
    _captum_available = False

from .decision_narrative import DecisionNarrator
from .confidence_scoring import (
    ConfidenceScorer,
    ConfidenceMetrics
)


class ExplainableAI:
    """
    Unified interface for explainable AI features
    """
    def __init__(self):
        self.attributor = FeatureAttributor()
        self.narrator = DecisionNarrator()
        self.confidence_scorer = ConfidenceScorer()
        self.captum_available = _captum_available
    
    def explain_decision(self, decision, features=None):
        """Generate explanation for a trading decision"""
        explanation = {
            'decision': decision,
            'narrative': self.narrator.generate_narrative(decision),
            'confidence': self.confidence_scorer.calculate_confidence(decision)
        }
        
        if features is not None and self.captum_available:
            explanation['attribution'] = self.attributor.attribute(features)
        
        return explanation


__all__ = [
    'FeatureAttributor',
    'DecisionNarrator',
    'ConfidenceScorer',
    'ConfidenceMetrics',
    'ExplainableAI'
]
