"""
Strategy Sub-package for Research OS.
Translates alpha signals into executable ResearchStrategy objects and registries.
"""

from .synthesizer import StandardResearchStrategy, StrategySynthesizer
from .registry import StandardStrategyRegistry

__all__ = [
    'StandardResearchStrategy',
    'StrategySynthesizer',
    'StandardStrategyRegistry'
]
