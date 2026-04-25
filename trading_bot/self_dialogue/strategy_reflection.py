"""
Strategy Reflection Module
===========================

Reflects on strategy performance and lessons learned.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reflection:
    """Strategy reflection record."""
    decision: str
    outcome: str
    lesson: str
    adaptation: str
    timestamp: datetime


class StrategyReflectionModule:
    """Module for strategy reflection and learning."""
    
    def __init__(self):
        self.reflections: List[Reflection] = []
    
    def reflect(self, decision: str, outcome: str, pnl: float) -> Reflection:
        """Create reflection on strategy decision."""
        if pnl > 0:
            lesson = "Good execution, maintain approach"
            adaptation = "Continue current strategy"
        else:
            lesson = "Improve risk management"
            adaptation = "Reduce position size, tighten stops"
        
        reflection = Reflection(
            decision=decision,
            outcome=outcome,
            lesson=lesson,
            adaptation=adaptation,
            timestamp=datetime.now(),
        )
        
        self.reflections.append(reflection)
        return reflection
