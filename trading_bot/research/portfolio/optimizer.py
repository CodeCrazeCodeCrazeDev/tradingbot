"""
Mathematical Portfolio Optimization Subsystem for Research OS.
Implements Hierarchical Risk Parity (HRP), Risk Parity, Kelly Criterion, and CVaR minimization.
"""

from typing import Dict, Any, List
import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.optimize import minimize
import logging

logger = logging.getLogger(__name__)


class PortfolioResearchOptimizer:
    """
    Advanced asset-allocation engine.
    Applies diverse portfolio construction frameworks to synthesize resilient strategy weights.
    """

    def calculate_correlation_matrix(self, returns_matrix: np.ndarray) -> np.ndarray:
        """
        returns_matrix: Shape (N_timesteps, M_assets)
        """
        return np.corrcoef(returns_matrix, rowvar=False)

    def calculate_covariance_matrix(self, returns_matrix: np.ndarray) -> np.ndarray:
        return np.cov(returns_matrix, rowvar=False)

    # 1. RISK PARITY (Equal Risk Contribution Optimization)
    def optimize_risk_parity(self, returns_matrix: np.ndarray) -> np.ndarray:
        cov = self.calculate_covariance_matrix(returns_matrix)
        num_assets = cov.shape[0]

        # Objective: minimize the sum of squared differences of risk contributions
        init_weights = np.ones(num_assets) / num_assets
        bounds = [(0.01, 1.0) for _ in range(num_assets)]
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

        def _risk_contribution_objective(weights):
            portfolio_variance = np.dot(weights.T, np.dot(cov, weights))
            marginal_risk = np.dot(cov, weights)
            risk_contributions = weights * marginal_risk / portfolio_variance
            # Penalize disparity from equal target risk contributions (1 / num_assets)
            target = 1.0 / num_assets
            return np.sum((risk_contributions - target) ** 2)

        res = minimize(_risk_contribution_objective, init_weights, bounds=bounds, constraints=constraints, method='SLSQP')
        if res.success:
            return res.x
        return init_weights

    # 2. HIERARCHICAL RISK PARITY (HRP)
    def optimize_hrp(self, returns_matrix: np.ndarray) -> np.ndarray:
        """
        Executes Hierarchical Risk Parity allocation.
        Uses single-linkage tree clustering to build an intuitive, noise-robust risk hierarchy.
        """
        cov = self.calculate_covariance_matrix(returns_matrix)
        corr = self.calculate_correlation_matrix(returns_matrix)
        num_assets = cov.shape[0]

        if num_assets <= 1:
            return np.ones(num_assets)

        # 1. Hierarchical Tree Clustering
        # Calculate distance metric d(i,j) = sqrt(0.5 * (1 - corr(i,j)))
        dist = np.sqrt(0.5 * (1.0 - np.clip(corr, -1.0, 1.0)))
        linkage = sch.linkage(dist, method='single')

        # 2. Quasi-Diagonalization (order assets by cluster linkage adjacency)
        sorted_indices = sch.leaves_list(linkage)

        # 3. Recursive Bisection weighting
        weights = np.ones(num_assets)
        self._recursive_bisection(cov, sorted_indices, weights)

        return weights

    def _recursive_bisection(self, cov: np.ndarray, sorted_indices: List[int], weights: np.ndarray):
        """Helper to recursively divide weights according to inverse variance of sub-clusters."""
        if len(sorted_indices) <= 1:
            return

        mid = len(sorted_indices) // 2
        left_slice = sorted_indices[:mid]
        right_slice = sorted_indices[mid:]

        # Compute cluster variance
        cov_l = cov[np.ix_(left_slice, left_slice)]
        cov_r = cov[np.ix_(right_slice, right_slice)]

        # Simple inverse-variance allocation across left and right cluster subsets
        w_l = 1.0 / np.trace(cov_l) if np.trace(cov_l) > 0 else 1.0
        w_r = 1.0 / np.trace(cov_r) if np.trace(cov_r) > 0 else 1.0

        allocation_l = w_l / (w_l + w_r)
        allocation_r = 1.0 - allocation_l

        # Scaled sub-weights
        weights[left_slice] *= allocation_l
        weights[right_slice] *= allocation_r

        # Recurse
        self._recursive_bisection(cov, left_slice, weights)
        self._recursive_bisection(cov, right_slice, weights)

    # 3. KELLY CRITERION allocation scaling
    def calculate_kelly_fraction(self, win_rate: float, win_loss_ratio: float) -> float:
        """
        Computes Kelly fraction: f* = p - (q / b)
        where p = win_rate, q = 1 - p, b = average win/loss ratio.
        """
        if win_loss_ratio <= 0:
            return 0.0
        p = win_rate
        q = 1.0 - p
        kelly = p - (q / win_loss_ratio)
        return float(np.clip(kelly, 0.0, 1.0))

    # 4. CONDITIONAL VALUE AT RISK (CVaR) Optimization
    def optimize_minimum_cvar(self, returns_matrix: np.ndarray, alpha: float = 0.05) -> np.ndarray:
        """
        Finds asset weights that minimize the out-of-sample portfolio Conditional Value at Risk (CVaR).
        """
        num_assets = returns_matrix.shape[1]
        init_weights = np.ones(num_assets) / num_assets
        bounds = [(0.0, 1.0) for _ in range(num_assets)]
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

        def _portfolio_cvar(weights):
            port_returns = np.dot(returns_matrix, weights)
            var_thresh = np.percentile(port_returns, alpha * 100)
            tail_returns = port_returns[port_returns <= var_thresh]
            if len(tail_returns) == 0:
                return -var_thresh
            return float(-np.mean(tail_returns))

        res = minimize(_portfolio_cvar, init_weights, bounds=bounds, constraints=constraints, method='SLSQP')
        if res.success:
            return res.x
        return init_weights
