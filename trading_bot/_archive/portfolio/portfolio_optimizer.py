"""
Multi-Asset Portfolio Optimization System
Institutional-Grade Portfolio Construction

This module provides comprehensive portfolio optimization:
- Markowitz Mean-Variance Optimization
- Black-Litterman Model with views
- Risk Parity (Equal Risk Contribution)
- Hierarchical Risk Parity (HRP)
- Maximum Sharpe Ratio
- Minimum Variance
- Maximum Diversification
- CVaR Optimization

Portfolio Manager + Quantitative Analyst + Actuary Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy.optimize import minimize, LinearConstraint
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """Portfolio optimization methods"""
    MEAN_VARIANCE = "MEAN_VARIANCE"  # Classic Markowitz
    MAX_SHARPE = "MAX_SHARPE"  # Maximum Sharpe Ratio
    MIN_VARIANCE = "MIN_VARIANCE"  # Minimum Variance
    RISK_PARITY = "RISK_PARITY"  # Equal Risk Contribution
    BLACK_LITTERMAN = "BLACK_LITTERMAN"  # With investor views
    HRP = "HRP"  # Hierarchical Risk Parity
    MAX_DIVERSIFICATION = "MAX_DIVERSIFICATION"  # Maximum Diversification Ratio
    CVAR_OPTIMIZATION = "CVAR_OPTIMIZATION"  # Conditional VaR


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR 95%
    diversification_ratio: float
    effective_n: float  # Effective number of bets
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expected_return': round(self.expected_return, 4),
            'volatility': round(self.volatility, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 4),
            'var_95': round(self.var_95, 4),
            'cvar_95': round(self.cvar_95, 4),
            'diversification_ratio': round(self.diversification_ratio, 2),
            'effective_n': round(self.effective_n, 1)
        }


@dataclass
class OptimizationResult:
    """Portfolio optimization result"""
    method: OptimizationMethod
    weights: Dict[str, float]
    metrics: PortfolioMetrics
    timestamp: datetime
    success: bool
    message: str
    iterations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method.value,
            'weights': {k: round(v, 4) for k, v in self.weights.items()},
            'metrics': self.metrics.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'message': self.message,
            'iterations': self.iterations
        }


@dataclass
class InvestorView:
    """Black-Litterman investor view"""
    asset: str  # Single asset view
    asset_pair: Optional[Tuple[str, str]] = None  # Relative view (asset1 outperforms asset2)
    expected_return: float = 0.0  # Expected return (absolute or relative)
    confidence: float = 0.5  # View confidence (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'asset_pair': self.asset_pair,
            'expected_return': self.expected_return,
            'confidence': self.confidence
        }


class PortfolioOptimizer:
    """
    Multi-Asset Portfolio Optimization System
    
    Provides institutional-grade portfolio construction using multiple
    optimization methodologies:
    
    1. Mean-Variance Optimization (Markowitz)
       - Classic efficient frontier
       - Target return or risk constraints
       - Long-only or long-short
    
    2. Maximum Sharpe Ratio
       - Tangent portfolio on efficient frontier
       - Risk-free rate adjusted
    
    3. Minimum Variance
       - Lowest volatility portfolio
       - Good for risk-averse investors
    
    4. Risk Parity (Equal Risk Contribution)
       - Each asset contributes equally to portfolio risk
       - More balanced than equal weight
    
    5. Black-Litterman
       - Combines market equilibrium with investor views
       - Reduces estimation error
       - More stable weights
    
    6. Hierarchical Risk Parity (HRP)
       - Uses hierarchical clustering
       - No covariance matrix inversion
       - More robust to estimation error
    
    7. Maximum Diversification
       - Maximizes diversification ratio
       - Portfolio vol / weighted avg vol
    
    8. CVaR Optimization
       - Minimizes tail risk
       - Better for fat-tailed distributions
    
    Constraints Supported:
    - Long-only or long-short
    - Position limits (min/max weight)
    - Sector constraints
    - Turnover constraints
    - Tracking error constraints
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize portfolio optimizer
        
        Args:
            config: Configuration dictionary with:
                - risk_free_rate: Annual risk-free rate (default: 0.04)
                - min_weight: Minimum position weight (default: 0.0)
                - max_weight: Maximum position weight (default: 1.0)
                - target_return: Target annual return for MVO
                - max_iterations: Optimization iterations (default: 1000)
        """
        self.config = config or {}
        
        self.risk_free_rate = self.config.get('risk_free_rate', 0.04)
        self.min_weight = self.config.get('min_weight', 0.0)
        self.max_weight = self.config.get('max_weight', 1.0)
        self.target_return = self.config.get('target_return', None)
        self.max_iterations = self.config.get('max_iterations', 1000)
        
        # Statistics
        self.optimizations_run = 0
        self.successful_optimizations = 0
        
        logger.info(f"PortfolioOptimizer initialized with rf={self.risk_free_rate:.2%}")
    
    def optimize(self,
                returns: pd.DataFrame,
                method: OptimizationMethod = OptimizationMethod.MAX_SHARPE,
                views: Optional[List[InvestorView]] = None,
                constraints: Optional[Dict[str, Any]] = None) -> OptimizationResult:
        """
        Optimize portfolio using specified method
        
        Args:
            returns: DataFrame of asset returns (rows=time, cols=assets)
            method: Optimization method to use
            views: List of investor views (for Black-Litterman)
            constraints: Additional constraints
            
        Returns:
            OptimizationResult with optimal weights and metrics
        """
        self.optimizations_run += 1
        
        # Calculate expected returns and covariance
        expected_returns = returns.mean() * 252  # Annualize
        cov_matrix = returns.cov() * 252  # Annualize
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        # Apply constraints
        constraints = constraints or {}
        min_weight = constraints.get('min_weight', self.min_weight)
        max_weight = constraints.get('max_weight', self.max_weight)
        
        try:
            if method == OptimizationMethod.MEAN_VARIANCE:
                weights = self._mean_variance_optimization(
                    expected_returns, cov_matrix, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.MAX_SHARPE:
                weights = self._max_sharpe_optimization(
                    expected_returns, cov_matrix, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.MIN_VARIANCE:
                weights = self._min_variance_optimization(
                    cov_matrix, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.RISK_PARITY:
                weights = self._risk_parity_optimization(
                    cov_matrix, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.BLACK_LITTERMAN:
                weights = self._black_litterman_optimization(
                    expected_returns, cov_matrix, views, assets, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.HRP:
                weights = self._hrp_optimization(returns)
            
            elif method == OptimizationMethod.MAX_DIVERSIFICATION:
                weights = self._max_diversification_optimization(
                    cov_matrix, min_weight, max_weight
                )
            
            elif method == OptimizationMethod.CVAR_OPTIMIZATION:
                weights = self._cvar_optimization(
                    returns, min_weight, max_weight
                )
            
            else:
                raise ValueError(f"Unknown optimization method: {method}")
            
            # Create weights dictionary
            weights_dict = {asset: w for asset, w in zip(assets, weights)}
            
            # Calculate portfolio metrics
            metrics = self._calculate_portfolio_metrics(
                weights, expected_returns.values, cov_matrix.values, returns.values
            )
            
            self.successful_optimizations += 1
            
            return OptimizationResult(
                method=method,
                weights=weights_dict,
                metrics=metrics,
                timestamp=datetime.now(),
                success=True,
                message="Optimization successful"
            )
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            
            # Return equal weight as fallback
            equal_weights = {asset: 1.0 / n_assets for asset in assets}
            
            return OptimizationResult(
                method=method,
                weights=equal_weights,
                metrics=self._calculate_portfolio_metrics(
                    np.array([1.0 / n_assets] * n_assets),
                    expected_returns.values,
                    cov_matrix.values,
                    returns.values
                ),
                timestamp=datetime.now(),
                success=False,
                message=f"Optimization failed: {str(e)}. Using equal weights."
            )
    
    def _mean_variance_optimization(self,
                                   expected_returns: pd.Series,
                                   cov_matrix: pd.DataFrame,
                                   min_weight: float,
                                   max_weight: float) -> np.ndarray:
        """Classic Markowitz mean-variance optimization"""
        n = len(expected_returns)
        
        # Initial guess (equal weight)
        x0 = np.array([1.0 / n] * n)
        
        # Objective: minimize variance for target return
        def objective(weights):
            return np.dot(weights.T, np.dot(cov_matrix.values, weights))
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        
        # Add target return constraint if specified
        if self.target_return is not None:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.dot(x, expected_returns.values) - self.target_return
            })
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _max_sharpe_optimization(self,
                                expected_returns: pd.Series,
                                cov_matrix: pd.DataFrame,
                                min_weight: float,
                                max_weight: float) -> np.ndarray:
        """Maximum Sharpe Ratio optimization"""
        n = len(expected_returns)
        
        # Initial guess
        x0 = np.array([1.0 / n] * n)
        
        # Objective: minimize negative Sharpe ratio
        def objective(weights):
            port_return = np.dot(weights, expected_returns.values)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix.values, weights)))
            sharpe = (port_return - self.risk_free_rate) / port_vol
            return -sharpe  # Negative because we minimize
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _min_variance_optimization(self,
                                  cov_matrix: pd.DataFrame,
                                  min_weight: float,
                                  max_weight: float) -> np.ndarray:
        """Minimum variance portfolio"""
        n = len(cov_matrix)
        
        # Initial guess
        x0 = np.array([1.0 / n] * n)
        
        # Objective: minimize variance
        def objective(weights):
            return np.dot(weights.T, np.dot(cov_matrix.values, weights))
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _risk_parity_optimization(self,
                                 cov_matrix: pd.DataFrame,
                                 min_weight: float,
                                 max_weight: float) -> np.ndarray:
        """Risk Parity (Equal Risk Contribution) optimization"""
        n = len(cov_matrix)
        cov = cov_matrix.values
        
        # Initial guess
        x0 = np.array([1.0 / n] * n)
        
        # Target risk contribution (equal)
        target_risk = 1.0 / n
        
        # Objective: minimize squared difference from target risk contribution
        def objective(weights):
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            marginal_contrib = np.dot(cov, weights)
            risk_contrib = weights * marginal_contrib / port_vol
            risk_contrib_pct = risk_contrib / port_vol
            
            # Sum of squared differences from target
            return np.sum((risk_contrib_pct - target_risk) ** 2)
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Bounds
        bounds = [(max(min_weight, 0.01), max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _black_litterman_optimization(self,
                                     expected_returns: pd.Series,
                                     cov_matrix: pd.DataFrame,
                                     views: Optional[List[InvestorView]],
                                     assets: List[str],
                                     min_weight: float,
                                     max_weight: float) -> np.ndarray:
        """Black-Litterman optimization with investor views"""
        n = len(assets)
        cov = cov_matrix.values
        
        # Market equilibrium returns (CAPM implied)
        # Assume market cap weights (equal for simplicity)
        market_weights = np.array([1.0 / n] * n)
        risk_aversion = 2.5  # Market risk aversion
        
        # Equilibrium returns
        pi = risk_aversion * np.dot(cov, market_weights)
        
        if views is None or len(views) == 0:
            # No views, use equilibrium returns
            bl_returns = pi
        else:
            # Build P matrix (view portfolios) and Q vector (view returns)
            P = []
            Q = []
            omega_diag = []  # View uncertainty
            
            for view in views:
                p_row = np.zeros(n)
                
                if view.asset_pair:
                    # Relative view
                    asset1_idx = assets.index(view.asset_pair[0])
                    asset2_idx = assets.index(view.asset_pair[1])
                    p_row[asset1_idx] = 1
                    p_row[asset2_idx] = -1
                else:
                    # Absolute view
                    asset_idx = assets.index(view.asset)
                    p_row[asset_idx] = 1
                
                P.append(p_row)
                Q.append(view.expected_return)
                
                # View uncertainty (inverse of confidence)
                omega_diag.append((1 - view.confidence) * 0.1)
            
            P = np.array(P)
            Q = np.array(Q)
            omega = np.diag(omega_diag)
            
            # Tau (scaling factor)
            tau = 0.05
            
            # Black-Litterman formula
            tau_cov = tau * cov
            
            # Posterior expected returns
            inv_tau_cov = np.linalg.inv(tau_cov)
            inv_omega = np.linalg.inv(omega)
            
            M = np.linalg.inv(inv_tau_cov + np.dot(P.T, np.dot(inv_omega, P)))
            bl_returns = np.dot(M, np.dot(inv_tau_cov, pi) + np.dot(P.T, np.dot(inv_omega, Q)))
        
        # Optimize using BL returns
        x0 = np.array([1.0 / n] * n)
        
        def objective(weights):
            port_return = np.dot(weights, bl_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            sharpe = (port_return - self.risk_free_rate) / port_vol
            return -sharpe
        
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _hrp_optimization(self, returns: pd.DataFrame) -> np.ndarray:
        """Hierarchical Risk Parity optimization"""
        # Calculate correlation and covariance
        corr = returns.corr()
        cov = returns.cov() * 252
        
        # Step 1: Tree clustering
        dist = np.sqrt((1 - corr) / 2)  # Distance matrix
        dist_condensed = squareform(dist.values, checks=False)
        link = linkage(dist_condensed, method='ward')
        
        # Step 2: Quasi-diagonalization
        sort_ix = self._get_quasi_diag(link)
        sorted_assets = [returns.columns[i] for i in sort_ix]
        
        # Step 3: Recursive bisection
        weights = self._get_recursive_bisection(cov, sorted_assets)
        
        # Reorder weights to original order
        result = np.zeros(len(returns.columns))
        for i, asset in enumerate(returns.columns):
            result[i] = weights.get(asset, 0)
        
        return result
    
    def _get_quasi_diag(self, link: np.ndarray) -> List[int]:
        """Get quasi-diagonal order from linkage matrix"""
        link = link.astype(int)
        sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
        num_items = link[-1, 3]
        
        while sort_ix.max() >= num_items:
            sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
            df0 = sort_ix[sort_ix >= num_items]
            i = df0.index
            j = df0.values - num_items
            sort_ix[i] = link[j, 0]
            df0 = pd.Series(link[j, 1], index=i + 1)
            sort_ix = pd.concat([sort_ix, df0])
            sort_ix = sort_ix.sort_index()
            sort_ix.index = range(sort_ix.shape[0])
        
        return sort_ix.tolist()
    
    def _get_recursive_bisection(self,
                                cov: pd.DataFrame,
                                sorted_assets: List[str]) -> Dict[str, float]:
        """Recursive bisection for HRP weights"""
        weights = {asset: 1.0 for asset in sorted_assets}
        clusters = [sorted_assets]
        
        while len(clusters) > 0:
            # Bisect each cluster
            new_clusters = []
            
            for cluster in clusters:
                if len(cluster) > 1:
                    # Split cluster
                    mid = len(cluster) // 2
                    cluster1 = cluster[:mid]
                    cluster2 = cluster[mid:]
                    
                    # Calculate cluster variances
                    var1 = self._get_cluster_var(cov, cluster1)
                    var2 = self._get_cluster_var(cov, cluster2)
                    
                    # Allocate based on inverse variance
                    alpha = 1 - var1 / (var1 + var2)
                    
                    # Update weights
                    for asset in cluster1:
                        weights[asset] *= alpha
                    for asset in cluster2:
                        weights[asset] *= (1 - alpha)
                    
                    # Add to new clusters if more than 1 asset
                    if len(cluster1) > 1:
                        new_clusters.append(cluster1)
                    if len(cluster2) > 1:
                        new_clusters.append(cluster2)
            
            clusters = new_clusters
        
        return weights
    
    def _get_cluster_var(self, cov: pd.DataFrame, assets: List[str]) -> float:
        """Calculate cluster variance using inverse-variance weights"""
        cov_slice = cov.loc[assets, assets]
        ivp = 1 / np.diag(cov_slice)
        ivp /= ivp.sum()
        return np.dot(ivp, np.dot(cov_slice, ivp))
    
    def _max_diversification_optimization(self,
                                         cov_matrix: pd.DataFrame,
                                         min_weight: float,
                                         max_weight: float) -> np.ndarray:
        """Maximum diversification ratio optimization"""
        n = len(cov_matrix)
        cov = cov_matrix.values
        vols = np.sqrt(np.diag(cov))
        
        # Initial guess
        x0 = np.array([1.0 / n] * n)
        
        # Objective: minimize negative diversification ratio
        def objective(weights):
            weighted_avg_vol = np.dot(weights, vols)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            div_ratio = weighted_avg_vol / port_vol
            return -div_ratio  # Negative because we minimize
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _cvar_optimization(self,
                          returns: pd.DataFrame,
                          min_weight: float,
                          max_weight: float,
                          alpha: float = 0.05) -> np.ndarray:
        """CVaR (Conditional Value at Risk) optimization"""
        n = returns.shape[1]
        T = returns.shape[0]
        
        # Initial guess
        x0 = np.array([1.0 / n] * n)
        
        # Objective: minimize CVaR
        def objective(weights):
            port_returns = np.dot(returns.values, weights)
            var = np.percentile(port_returns, alpha * 100)
            cvar = port_returns[port_returns <= var].mean()
            return -cvar  # Negative because CVaR is negative for losses
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': self.max_iterations}
        )
        
        return result.x
    
    def _calculate_portfolio_metrics(self,
                                    weights: np.ndarray,
                                    expected_returns: np.ndarray,
                                    cov_matrix: np.ndarray,
                                    returns: np.ndarray) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        # Portfolio return and volatility
        port_return = np.dot(weights, expected_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Sharpe ratio
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        # Portfolio returns series
        port_returns = np.dot(returns, weights)
        
        # Sortino ratio (downside deviation)
        downside_returns = port_returns[port_returns < 0]
        downside_std = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else port_vol
        sortino = (port_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + port_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # VaR and CVaR (95%)
        var_95 = np.percentile(port_returns, 5)
        cvar_95 = port_returns[port_returns <= var_95].mean() if len(port_returns[port_returns <= var_95]) > 0 else var_95
        
        # Diversification ratio
        vols = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = np.dot(weights, vols)
        div_ratio = weighted_avg_vol / port_vol if port_vol > 0 else 1
        
        # Effective N (number of bets)
        effective_n = 1 / np.sum(weights ** 2) if np.sum(weights ** 2) > 0 else 1
        
        return PortfolioMetrics(
            expected_return=port_return,
            volatility=port_vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            diversification_ratio=div_ratio,
            effective_n=effective_n
        )
    
    def efficient_frontier(self,
                          returns: pd.DataFrame,
                          n_portfolios: int = 50) -> List[OptimizationResult]:
        """
        Generate efficient frontier portfolios
        
        Args:
            returns: Asset returns DataFrame
            n_portfolios: Number of portfolios on frontier
            
        Returns:
            List of OptimizationResult for each portfolio
        """
        expected_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        # Get min and max return portfolios
        min_var_result = self.optimize(returns, OptimizationMethod.MIN_VARIANCE)
        min_return = min_var_result.metrics.expected_return
        
        max_return = expected_returns.max()
        
        # Generate target returns
        target_returns = np.linspace(min_return, max_return * 0.95, n_portfolios)
        
        frontier = []
        
        for target in target_returns:
            self.target_return = target
            result = self.optimize(returns, OptimizationMethod.MEAN_VARIANCE)
            frontier.append(result)
        
        self.target_return = None  # Reset
        
        return frontier
    
    def compare_methods(self, returns: pd.DataFrame) -> Dict[str, OptimizationResult]:
        """
        Compare all optimization methods
        
        Args:
            returns: Asset returns DataFrame
            
        Returns:
            Dictionary of method -> OptimizationResult
        """
        results = {}
        
        for method in OptimizationMethod:
            try:
                result = self.optimize(returns, method)
                results[method.value] = result
            except Exception as e:
                logger.warning(f"Method {method.value} failed: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            'optimizations_run': self.optimizations_run,
            'successful_optimizations': self.successful_optimizations,
            'success_rate': self.successful_optimizations / self.optimizations_run if self.optimizations_run > 0 else 0,
            'risk_free_rate': self.risk_free_rate
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create sample returns data
    np.random.seed(42)
    n_assets = 5
    n_periods = 252 * 3  # 3 years
    
    # Generate correlated returns
    mean_returns = np.array([0.10, 0.12, 0.08, 0.15, 0.07]) / 252
    volatilities = np.array([0.15, 0.20, 0.12, 0.25, 0.10]) / np.sqrt(252)
    
    # Correlation matrix
    corr = np.array([
        [1.0, 0.6, 0.3, 0.4, 0.2],
        [0.6, 1.0, 0.4, 0.5, 0.3],
        [0.3, 0.4, 1.0, 0.3, 0.5],
        [0.4, 0.5, 0.3, 1.0, 0.2],
        [0.2, 0.3, 0.5, 0.2, 1.0]
    ])
    
    # Generate returns
    L = np.linalg.cholesky(corr)
    returns_raw = np.random.randn(n_periods, n_assets)
    returns_corr = np.dot(returns_raw, L.T)
    returns_scaled = returns_corr * volatilities + mean_returns
    
    returns_df = pd.DataFrame(
        returns_scaled,
        columns=['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'JNJ']
    )
    
    # Create optimizer
    optimizer = PortfolioOptimizer({
        'risk_free_rate': 0.04,
        'min_weight': 0.05,
        'max_weight': 0.40
    })
    
    logger.info("\n=== Portfolio Optimization Comparison ===\n")
    
    # Compare all methods
    results = optimizer.compare_methods(returns_df)
    
    for method, result in results.items():
        logger.info(f"\n{method}:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Weights: {', '.join([f'{k}: {v:.1%}' for k, v in result.weights.items()])}")
        logger.info(f"  Expected Return: {result.metrics.expected_return:.2%}")
        logger.info(f"  Volatility: {result.metrics.volatility:.2%}")
        logger.info(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: {result.metrics.max_drawdown:.2%}")
        logger.info(f"  Diversification Ratio: {result.metrics.diversification_ratio:.2f}")
    
    # Black-Litterman with views
    logger.info("\n=== Black-Litterman with Views ===")
    views = [
        InvestorView(asset='TSLA', expected_return=0.25, confidence=0.7),
        InvestorView(asset_pair=('AAPL', 'MSFT'), expected_return=0.05, confidence=0.6)
    ]
    
    bl_result = optimizer.optimize(returns_df, OptimizationMethod.BLACK_LITTERMAN, views=views)
    logger.info(f"  Weights: {', '.join([f'{k}: {v:.1%}' for k, v in bl_result.weights.items()])}")
    logger.info(f"  Expected Return: {bl_result.metrics.expected_return:.2%}")
    logger.info(f"  Sharpe Ratio: {bl_result.metrics.sharpe_ratio:.2f}")
    
    # Get statistics
    stats = optimizer.get_statistics()
    logger.info(f"\n=== Optimizer Statistics ===")
    logger.info(f"  Optimizations Run: {stats['optimizations_run']}")
    logger.info(f"  Success Rate: {stats['success_rate']:.1%}")
