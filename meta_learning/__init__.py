"""
Phase 5: Meta-Learning & Evolution
Quick adaptation and self-modification
"""

from .maml import MAMLPolicy, MAMLMetaLearner
from .evolutionary import (
    TradingStrategy,
    EvolutionaryOptimizer,
    EvolutionaryStrategyOptimizer
)
from .self_rewriting import (
    CodeGenerator,
    SelfRewritingSystem,
    CodeFragment
)

__all__ = [
    'MAMLPolicy',
    'MAMLMetaLearner',
    'TradingStrategy',
    'EvolutionaryOptimizer',
    'EvolutionaryStrategyOptimizer',
    'CodeGenerator',
    'SelfRewritingSystem',
    'CodeFragment'
]
