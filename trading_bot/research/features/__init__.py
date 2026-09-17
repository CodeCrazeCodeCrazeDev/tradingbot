"""
Feature Engineering Sub-package for Research OS.
Handles quantitative feature mining, selection scoring, and features registry tracking.
"""

from .engine import FeatureDiscoveryEngine
from .registry import StandardFeatureRegistry

__all__ = [
    'FeatureDiscoveryEngine',
    'StandardFeatureRegistry'
]
