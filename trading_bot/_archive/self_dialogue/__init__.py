"""
Self-Dialogue Engine
====================

Internal reasoning and self-questioning system.

Every major decision undergoes internal dialogue:
1. Hypothesis validation
2. Contrarian analysis
3. Risk assessment
4. Uncertainty quantification

Dialogue is logged for post-hoc analysis and improvement.
"""

from .dialogue_engine import SelfDialogueEngine, DialogueRecord, DialogueTurn
from .hypothesis_debate import HypothesisDebateModule
from .strategy_reflection import StrategyReflectionModule
from .explanation_generator import ExplanationGenerator

__all__ = [
    'SelfDialogueEngine',
    'DialogueRecord',
    'DialogueTurn',
    'HypothesisDebateModule',
    'StrategyReflectionModule',
    'ExplanationGenerator',
]
