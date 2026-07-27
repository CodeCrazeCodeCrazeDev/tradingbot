"""
Portfolio Research Sub-package for Research OS.
Performs Hierarchical Risk Parity (HRP), Risk Parity, and CVaR optimization on combined strategies.
"""

from .optimizer import PortfolioResearchOptimizer

__all__ = [
    'PortfolioResearchOptimizer'
]
