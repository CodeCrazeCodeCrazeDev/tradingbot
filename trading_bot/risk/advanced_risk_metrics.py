"""
Advanced risk metrics: VaR, CVaR, HRP, stress testing.
Institutional-grade risk management implementation.
"""

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import minimize
from scipy.cluster.hierarchy import linkage, dendrogram
from typing import Dict, List, Optional, Tuple
from loguru import logger
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class AdvancedRiskMetrics:
    """Comprehensive risk metrics for portfolio management."""
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence: float = 0.95, 
                     method: str = 'historical') -> float:
        """
        Calculate Value at Risk.
        
        Args:
            returns: Array of returns
            confidence: Confidence level (e.g., 0.95 for 95%)
            method: 'historical', 'parametric', or 'monte_carlo'
            
        Returns:
            VaR value (negative number indicating loss)
        """
        if len(returns) == 0:
            return 0.0
        
        if method == 'historical':
            var = np.percentile(returns, (1 - confidence) * 100)
            
        elif method == 'parametric':
            mean = np.mean(returns)
            std = np.std(returns)
            var = mean - stats.norm.ppf(confidence) * std
            
        elif method == 'monte_carlo':
            var = AdvancedRiskMetrics._monte_carlo_var(returns, confidence)
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return var
    
    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            CVaR value (average loss beyond VaR)
        """
        if len(returns) == 0:
            return 0.0
        
        var = AdvancedRiskMetrics.calculate_var(returns, confidence, 'historical')
        cvar = returns[returns <= var].mean()
        
        return cvar if not np.isnan(cvar) else var
    
    @staticmethod
    def _monte_carlo_var(returns: np.ndarray, confidence: float, 
                        n_simulations: int = 10000) -> float:
        """Monte Carlo VaR simulation."""
        mean = np.mean(returns)
        std = np.std(returns)
        
        simulated_returns = np.random.normal(mean, std, n_simulations)
        var = np.percentile(simulated_returns, (1 - confidence) * 100)
        
        return var
    
    @staticmethod
    def calculate_portfolio_var(positions: Dict[str, float], 
                               returns_matrix: pd.DataFrame,
                               confidence: float = 0.95) -> float:
        """
        Calculate portfolio VaR considering correlations.
        
        Args:
            positions: Dict of {symbol: position_value}
            returns_matrix: DataFrame with returns for each symbol
            confidence: Confidence level
            
        Returns:
            Portfolio VaR
        """
        # Get weights
        total_value = sum(positions.values())
        weights = np.array([positions.get(sym, 0) / total_value 
                           for sym in returns_matrix.columns])
        
        # Calculate portfolio returns
        portfolio_returns = (returns_matrix * weights).sum(axis=1)
        
        # Calculate VaR
        var = AdvancedRiskMetrics.calculate_var(portfolio_returns.values, confidence)
        
        return var * total_value
    
    @staticmethod
    def stress_test(positions: Dict[str, float], 
                   scenarios: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Run stress tests on portfolio.
        
        Args:
            positions: Dict of {symbol: position_value}
            scenarios: Dict of {scenario_name: {symbol: shock_pct}}
            
        Returns:
            Dict of {scenario_name: portfolio_loss}
        """
        results = {}
        
        for scenario_name, shocks in scenarios.items():
            portfolio_loss = 0
            
            for symbol, position_value in positions.items():
                shock = shocks.get(symbol, 0)
                loss = position_value * shock
                portfolio_loss += loss
            
            results[scenario_name] = portfolio_loss
        
        logger.info(f"Stress test completed: {len(scenarios)} scenarios")
        return results
    
    @staticmethod
    def hierarchical_risk_parity(returns: pd.DataFrame) -> np.ndarray:
        """
        Calculate Hierarchical Risk Parity portfolio weights.
        
        Args:
            returns: DataFrame with returns for each asset
            
        Returns:
            Array of optimal weights
        """
        # Calculate correlation matrix
        corr = returns.corr()
        
        # Convert correlation to distance
        dist = np.sqrt((1 - corr) / 2)
        
        # Hierarchical clustering
        link = linkage(dist, method='single')
        
        # Get quasi-diagonalization order
        sort_ix = AdvancedRiskMetrics._get_quasi_diag(link)
        
        # Recursive bisection
        weights = AdvancedRiskMetrics._recursive_bisection(
            returns.iloc[:, sort_ix].cov()
        )
        
        # Reorder weights
        weights_ordered = np.zeros(len(weights))
        for i, ix in enumerate(sort_ix):
            weights_ordered[ix] = weights[i]
        
        return weights_ordered
    
    @staticmethod
    def _get_quasi_diag(link: np.ndarray) -> List[int]:
        """Get quasi-diagonal order from linkage matrix."""
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
            sort_ix = pd.concat([sort_ix, df0]).sort_index()
            sort_ix.index = range(sort_ix.shape[0])
        
        return sort_ix.tolist()
    
    @staticmethod
    def _recursive_bisection(cov: pd.DataFrame, sort_ix: Optional[List] = None) -> np.ndarray:
        """Recursive bisection for HRP."""
        if sort_ix is None:
            sort_ix = list(range(cov.shape[0]))
        
        weights = pd.Series(1.0, index=sort_ix)
        clusters = [sort_ix]
        
        while len(clusters) > 0:
            clusters = [cluster[start:end] 
                       for cluster in clusters 
                       for start, end in ((0, len(cluster) // 2), 
                                         (len(cluster) // 2, len(cluster)))
                       if len(cluster) > 1]
            
            for i in range(0, len(clusters), 2):
                cluster0 = clusters[i]
                cluster1 = clusters[i + 1] if i + 1 < len(clusters) else []
                
                if len(cluster1) == 0:
                    continue
                
                # Calculate cluster variances
                cov0 = cov.iloc[cluster0, cluster0]
                cov1 = cov.iloc[cluster1, cluster1]
                
                ivp0 = 1.0 / np.diag(cov0).sum()
                ivp1 = 1.0 / np.diag(cov1).sum()
                
                # Allocate weight
                alpha = ivp0 / (ivp0 + ivp1)
                
                weights[cluster0] *= alpha
                weights[cluster1] *= (1 - alpha)
        
        return weights.values
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion for position sizing.
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive)
            
        Returns:
            Optimal fraction of capital to risk
        """
        if avg_loss == 0:
            return 0.0
        
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Apply half-Kelly for safety
        kelly = max(0, kelly * 0.5)
        
        return kelly
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0,
                              periods_per_year: int = 252) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / periods_per_year
        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        sharpe_annualized = sharpe * np.sqrt(periods_per_year)
        
        return sharpe_annualized
    
    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.0,
                               periods_per_year: int = 252) -> float:
        """Calculate annualized Sortino ratio (downside deviation)."""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0
        
        sortino = np.mean(excess_returns) / downside_std
        sortino_annualized = sortino * np.sqrt(periods_per_year)
        
        return sortino_annualized
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: np.ndarray) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown.
        
        Returns:
            (max_drawdown_pct, start_idx, end_idx)
        """
        if len(equity_curve) == 0:
            return 0.0, 0, 0
        
        cummax = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - cummax) / cummax
        
        max_dd = drawdown.min()
        end_idx = drawdown.argmin()
        start_idx = equity_curve[:end_idx].argmax()
        
        return abs(max_dd) * 100, start_idx, end_idx
    
    @staticmethod
    def calculate_calmar_ratio(returns: np.ndarray, 
                              periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        if len(returns) == 0:
            return 0.0
        
        annual_return = np.mean(returns) * periods_per_year
        equity_curve = np.cumprod(1 + returns)
        max_dd, _, _ = AdvancedRiskMetrics.calculate_max_drawdown(equity_curve)
        
        if max_dd == 0:
            return float('inf')
        
        return annual_return / (max_dd / 100)


class RiskMonitor:
    """Real-time risk monitoring system."""
    
    def __init__(self, max_var: float = 0.05, max_drawdown: float = 0.20):
        self.max_var = max_var
        self.max_drawdown = max_drawdown
        self.alerts = []
        
    def check_risk_limits(self, portfolio_value: float, 
                         returns: np.ndarray) -> Dict[str, bool]:
        """Check if risk limits are breached."""
        alerts = {}
        
        # VaR check
        var_95 = AdvancedRiskMetrics.calculate_var(returns, 0.95)
        var_pct = abs(var_95)
        
        if var_pct > self.max_var:
            alerts['var_breach'] = True
            logger.warning(f"VaR breach: {var_pct:.2%} > {self.max_var:.2%}")
        
        # Drawdown check
        equity_curve = portfolio_value * np.cumprod(1 + returns)
        max_dd, _, _ = AdvancedRiskMetrics.calculate_max_drawdown(equity_curve)
        
        if max_dd / 100 > self.max_drawdown:
            alerts['drawdown_breach'] = True
            logger.warning(f"Drawdown breach: {max_dd:.2%} > {self.max_drawdown:.2%}")
        
        return alerts
    
    def get_risk_report(self, returns: np.ndarray, 
                       portfolio_value: float) -> Dict:
        """Generate comprehensive risk report."""
        return {
            'var_95': AdvancedRiskMetrics.calculate_var(returns, 0.95),
            'cvar_95': AdvancedRiskMetrics.calculate_cvar(returns, 0.95),
            'var_99': AdvancedRiskMetrics.calculate_var(returns, 0.99),
            'cvar_99': AdvancedRiskMetrics.calculate_cvar(returns, 0.99),
            'sharpe': AdvancedRiskMetrics.calculate_sharpe_ratio(returns),
            'sortino': AdvancedRiskMetrics.calculate_sortino_ratio(returns),
            'max_drawdown': AdvancedRiskMetrics.calculate_max_drawdown(
                portfolio_value * np.cumprod(1 + returns)
            )[0],
            'calmar': AdvancedRiskMetrics.calculate_calmar_ratio(returns)
        }
