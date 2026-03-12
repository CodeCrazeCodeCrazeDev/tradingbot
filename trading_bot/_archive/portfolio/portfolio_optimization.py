"""Portfolio Optimization and Smart Allocation Module

Implements dynamic portfolio rebalancing and smart allocation using Modern Portfolio Theory (MPT) and related methods.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from scipy.optimize import minimize
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)


@dataclass
class AssetAllocation:
    asset: str
    weight: float
    expected_return: float
    volatility: float

class PortfolioOptimizer:
    """Optimizes portfolio allocation for risk-adjusted returns."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_free_rate = self.config.get('risk_free_rate', 0.01)

    def optimize(self, returns: pd.DataFrame) -> List[AssetAllocation]:
        """Optimize portfolio weights using MPT.

        Args:
            returns: DataFrame of asset returns (columns=assets)
        Returns:
            List of AssetAllocation objects
        """
        assets = returns.columns.tolist()
        mean_returns = returns.mean() * 252  # annualized
        cov_matrix = returns.cov() * 252
        num_assets = len(assets)

        def portfolio_performance(weights):
            port_return = np.dot(weights, mean_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
            return -sharpe  # negative for minimization

        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]

        result = minimize(portfolio_performance, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        weights = result.x if result.success else initial_guess

        allocations = [
            AssetAllocation(
                asset=assets[i],
                weight=weights[i],
                expected_return=mean_returns[i],
                volatility=np.sqrt(cov_matrix.iloc[i, i])
            ) for i in range(num_assets)
        ]
        return allocations

    def rebalance(self, current_weights: Dict[str, float], target_allocations: List[AssetAllocation]) -> Dict[str, float]:
        """Calculate trades needed to rebalance portfolio to target allocations."""
        target_weights = {a.asset: a.weight for a in target_allocations}
        trades = {asset: target_weights.get(asset, 0) - current_weights.get(asset, 0) for asset in set(current_weights) | set(target_weights)}
        return trades
