"""
Black-Litterman Portfolio Optimization.
Combines market equilibrium with investor views.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy.optimize import minimize
from loguru import logger
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class BlackLittermanOptimizer:
    """Black-Litterman portfolio optimization model."""
    
    def __init__(self, risk_aversion: float = 2.5):
        """
        Initialize Black-Litterman optimizer.
        
        Args:
            risk_aversion: Risk aversion parameter (typically 2-4)
        """
        try:
            self.risk_aversion = risk_aversion
            self.market_weights = None
            self.equilibrium_returns = None
        
            logger.info(f"Black-Litterman optimizer initialized (risk_aversion: {risk_aversion})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_equilibrium_returns(self, market_weights: np.ndarray,
                                     cov_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate implied equilibrium returns from market weights.
        
        Args:
            market_weights: Market capitalization weights
            cov_matrix: Covariance matrix of returns
            
        Returns:
            Equilibrium expected returns
        """
        # Reverse optimization: π = λ * Σ * w
        try:
            equilibrium_returns = self.risk_aversion * cov_matrix @ market_weights
        
            self.market_weights = market_weights
            self.equilibrium_returns = equilibrium_returns
        
            logger.info("Equilibrium returns calculated")
            return equilibrium_returns
        except Exception as e:
            logger.error(f"Error in calculate_equilibrium_returns: {e}")
            raise
    
    def incorporate_views(self, P: np.ndarray, Q: np.ndarray, 
                         omega: Optional[np.ndarray] = None,
                         tau: float = 0.05) -> np.ndarray:
        """
        Incorporate investor views into equilibrium returns.
        
        Args:
            P: Pick matrix (views on assets)
            Q: View returns vector
            omega: Uncertainty matrix for views (None for proportional)
            tau: Scaling factor for uncertainty
            
        Returns:
            Posterior expected returns
        """
        try:
            if self.equilibrium_returns is None:
                raise ValueError("Must calculate equilibrium returns first")
        
            # Get covariance matrix
            cov_matrix = self.equilibrium_returns.reshape(-1, 1) @ self.equilibrium_returns.reshape(1, -1)
        
            # Default omega (proportional to view uncertainty)
            if omega is None:
                omega = np.diag(np.diag(P @ (tau * cov_matrix) @ P.T))
        
            # Black-Litterman formula
            # E[R] = [(τΣ)^-1 + P'Ω^-1P]^-1 [(τΣ)^-1 π + P'Ω^-1 Q]
        
            tau_sigma_inv = np.linalg.inv(tau * cov_matrix)
            omega_inv = np.linalg.inv(omega)
        
            # Posterior precision
            posterior_precision = tau_sigma_inv + P.T @ omega_inv @ P
        
            # Posterior mean
            posterior_mean = np.linalg.inv(posterior_precision) @ (
                tau_sigma_inv @ self.equilibrium_returns + P.T @ omega_inv @ Q
            )
        
            logger.info(f"Incorporated {len(Q)} views into returns")
            return posterior_mean
        except Exception as e:
            logger.error(f"Error in incorporate_views: {e}")
            raise
    
    def optimize_portfolio(self, expected_returns: np.ndarray,
                          cov_matrix: np.ndarray,
                          constraints: Optional[Dict] = None) -> np.ndarray:
        """
        Optimize portfolio weights given expected returns.
        
        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            constraints: Portfolio constraints
            
        Returns:
            Optimal weights
        """
        n_assets = len(expected_returns)
        
        # Objective: minimize variance - risk_aversion * return
        def objective(weights):
            try:
                portfolio_return = weights @ expected_returns
                portfolio_variance = weights @ cov_matrix @ weights
                return portfolio_variance - self.risk_aversion * portfolio_return
            except Exception as e:
                logger.error(f"Error in objective: {e}")
                raise
        
        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]
        
        # Bounds
        bounds = [(0, 1) for _ in range(n_assets)]  # Long only
        
        # Add custom constraints
        if constraints:
            if 'max_weight' in constraints:
                bounds = [(0, constraints['max_weight']) for _ in range(n_assets)]
            
            if 'min_weight' in constraints:
                bounds = [(constraints['min_weight'], 1) for _ in range(n_assets)]
        
        # Initial guess (equal weight)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        if result.success:
            logger.success("Portfolio optimization successful")
            return result.x
        else:
            logger.error(f"Optimization failed: {result.message}")
            return x0
    
    def full_optimization(self, market_weights: np.ndarray,
                         returns: pd.DataFrame,
                         views: Optional[List[Dict]] = None) -> Dict:
        """
        Complete Black-Litterman optimization workflow.
        
        Args:
            market_weights: Market cap weights
            returns: Historical returns DataFrame
            views: List of view dictionaries with 'assets', 'return', 'confidence'
            
        Returns:
            Dictionary with optimal weights and statistics
        """
        # Calculate covariance matrix
        try:
            cov_matrix = returns.cov().values
        
            # Calculate equilibrium returns
            eq_returns = self.calculate_equilibrium_returns(market_weights, cov_matrix)
        
            # Incorporate views if provided
            if views:
                P, Q = self._construct_view_matrices(views, returns.columns)
                posterior_returns = self.incorporate_views(P, Q)
            else:
                posterior_returns = eq_returns
        
            # Optimize portfolio
            optimal_weights = self.optimize_portfolio(posterior_returns, cov_matrix)
        
            # Calculate portfolio statistics
            portfolio_return = optimal_weights @ posterior_returns
            portfolio_variance = optimal_weights @ cov_matrix @ optimal_weights
            portfolio_std = np.sqrt(portfolio_variance)
            sharpe = portfolio_return / portfolio_std if portfolio_std > 0 else 0
        
            result = {
                'weights': dict(zip(returns.columns, optimal_weights)),
                'expected_return': float(portfolio_return),
                'volatility': float(portfolio_std),
                'sharpe_ratio': float(sharpe),
                'equilibrium_returns': dict(zip(returns.columns, eq_returns)),
                'posterior_returns': dict(zip(returns.columns, posterior_returns))
            }
        
            logger.success(f"Black-Litterman optimization complete: Sharpe={sharpe:.2f}")
            return result
        except Exception as e:
            logger.error(f"Error in full_optimization: {e}")
            raise
    
    def _construct_view_matrices(self, views: List[Dict], 
                                 asset_names: pd.Index) -> Tuple[np.ndarray, np.ndarray]:
        """Construct P and Q matrices from views."""
        try:
            n_assets = len(asset_names)
            n_views = len(views)
        
            P = np.zeros((n_views, n_assets))
            Q = np.zeros(n_views)
        
            for i, view in enumerate(views):
                # Absolute view: asset will return X%
                if 'asset' in view:
                    asset_idx = asset_names.get_loc(view['asset'])
                    P[i, asset_idx] = 1.0
                    Q[i] = view['return']
            
                # Relative view: asset A will outperform asset B by X%
                elif 'asset_a' in view and 'asset_b' in view:
                    idx_a = asset_names.get_loc(view['asset_a'])
                    idx_b = asset_names.get_loc(view['asset_b'])
                    P[i, idx_a] = 1.0
                    P[i, idx_b] = -1.0
                    Q[i] = view['return']
        
            return P, Q
        except Exception as e:
            logger.error(f"Error in _construct_view_matrices: {e}")
            raise


class ViewGenerator:
    """Generate views for Black-Litterman model."""
    
    @staticmethod
    def momentum_view(returns: pd.DataFrame, lookback: int = 20,
                     confidence: float = 0.5) -> List[Dict]:
        """Generate views based on momentum."""
        try:
            recent_returns = returns.iloc[-lookback:].mean()
            views = []
        
            # Top performer view
            best_asset = recent_returns.idxmax()
            views.append({
                'asset': best_asset,
                'return': recent_returns[best_asset] * 1.5,  # Expect continuation
                'confidence': confidence
            })
        
            return views
        except Exception as e:
            logger.error(f"Error in momentum_view: {e}")
            raise
    
    @staticmethod
    def mean_reversion_view(returns: pd.DataFrame, lookback: int = 60,
                           confidence: float = 0.5) -> List[Dict]:
        """Generate views based on mean reversion."""
        try:
            recent_returns = returns.iloc[-lookback:].mean()
            long_term_mean = returns.mean()
        
            views = []
        
            # Assets far from mean
            deviation = recent_returns - long_term_mean
            extreme_asset = deviation.abs().idxmax()
        
            if deviation[extreme_asset] > 0:
                # Overperformed, expect reversion
                expected_return = long_term_mean[extreme_asset]
            else:
                # Underperformed, expect bounce
                expected_return = long_term_mean[extreme_asset] * 1.2
        
            views.append({
                'asset': extreme_asset,
                'return': expected_return,
                'confidence': confidence
            })
        
            return views
        except Exception as e:
            logger.error(f"Error in mean_reversion_view: {e}")
            raise
