"""
Marketplace and Scientific Review Panel Sub-package for Research OS.
Enforces multi-agent debate and Bayesian consensus voting across specialized expert personas.
"""

from .agents import (
    StatisticianReviewer,
    EconometricianReviewer,
    PortfolioManagerReviewer,
    RiskManagerReviewer,
    ExecutionSpecialistReviewer,
    SkepticalReviewer
)
from .debate import ScientificDebateEngine

__all__ = [
    'StatisticianReviewer',
    'EconometricianReviewer',
    'PortfolioManagerReviewer',
    'RiskManagerReviewer',
    'ExecutionSpecialistReviewer',
    'SkepticalReviewer',
    'ScientificDebateEngine'
]
