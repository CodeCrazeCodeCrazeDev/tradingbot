"""
Experimentation Sub-package for Research OS.
Registers, tracks, and manages experimental runs, models, scheduling, and resource prioritisations.
"""

from .registry import StandardExperimentRegistry
from .model_registry import StandardModelRegistry
from .scheduler import (
    SovereignExperimentScheduler,
    FIFOSchedulingPolicy,
    ExpectedInformationGainSchedulingPolicy,
    MultiArmedBanditSchedulingPolicy
)
from .prioritization import (
    BayesianEVIPrioritizationPolicy,
    ResearchEconomicsAllocationOptimizer
)

__all__ = [
    'StandardExperimentRegistry',
    'StandardModelRegistry',
    'SovereignExperimentScheduler',
    'FIFOSchedulingPolicy',
    'ExpectedInformationGainSchedulingPolicy',
    'MultiArmedBanditSchedulingPolicy',
    'BayesianEVIPrioritizationPolicy',
    'ResearchEconomicsAllocationOptimizer'
]
