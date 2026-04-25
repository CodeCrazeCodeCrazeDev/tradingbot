"""
Explanation Generator
=====================

Generates human-readable explanations for decisions.
"""

from typing import Dict, Any


class ExplanationGenerator:
    """Generates explanations for AI decisions."""
    
    def __init__(self):
        pass
    
    def generate(self, 
                decision: str,
                factors: Dict[str, Any],
                confidence: float) -> str:
        """Generate explanation for decision."""
        explanation = f"Decision: {decision}\n\n"
        explanation += "Key factors:\n"
        
        for factor, value in factors.items():
            explanation += f"- {factor}: {value}\n"
        
        explanation += f"\nConfidence: {confidence:.0%}\n"
        
        if confidence > 0.8:
            explanation += "High confidence based on strong evidence."
        elif confidence > 0.6:
            explanation += "Moderate confidence with some uncertainty."
        else:
            explanation += "Low confidence - proceed with caution."
        
        return explanation
