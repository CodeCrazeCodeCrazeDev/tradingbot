"""
Advanced risk calculation and portfolio optimization
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Advanced risk calculation for portfolio management.
    Implements VaR, CVaR, correlation analysis, and portfolio optimization.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.returns_history = []
        self.correlation_matrix = None
        
        logger.info("✅ Risk Calculator initialized")
    
    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: Optional[float] = None
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level (default: 0.95)
        
        Returns:
            VaR value
        """
        if confidence_level is None:
            confidence_level = self.confidence_level
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate VaR using historical simulation
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        return abs(var)
    
    def calculate_cvar(
        self,
        returns: np.ndarray,
        confidence_level: Optional[float] = None
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level (default: 0.95)
        
        Returns:
            CVaR value
        """
        if confidence_level is None:
            confidence_level = self.confidence_level
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate VaR threshold
        var = self.calculate_var(returns, confidence_level)
        
        # Calculate CVaR as mean of returns below VaR
        tail_returns = returns[returns <= -var]
        
        if len(tail_returns) == 0:
            return var
        
        cvar = abs(np.mean(tail_returns))
        
        return cvar
    
    def calculate_portfolio_var(
        self,
        positions: Dict[str, Dict],
        returns_data: Dict[str, np.ndarray],
        confidence_level: Optional[float] = None
    ) -> float:
        """
        Calculate portfolio VaR considering correlations.
        
        Args:
            positions: Dictionary of positions {symbol: {'value': float}}
            returns_data: Dictionary of returns {symbol: np.ndarray}
            confidence_level: Confidence level
        
        Returns:
            Portfolio VaR
        """
        if not positions or not returns_data:
            return 0.0
        
        if confidence_level is None:
            confidence_level = self.confidence_level
        
        # Get symbols and weights
        symbols = list(positions.keys())
        total_value = sum(p['value'] for p in positions.values())
        
        if total_value == 0:
            return 0.0
        
        weights = np.array([positions[s]['value'] / total_value for s in symbols])
        
        # Build returns matrix
        min_length = min(len(returns_data[s]) for s in symbols if s in returns_data)
        
        if min_length == 0:
            return 0.0
        
        returns_matrix = np.array([
            returns_data[s][-min_length:] for s in symbols if s in returns_data
        ]).T
        
        # Calculate portfolio returns
        portfolio_returns = returns_matrix @ weights
        
        # Calculate VaR
        var = self.calculate_var(portfolio_returns, confidence_level)
        
        return var * total_value
    
    def calculate_correlation_matrix(
        self,
        returns_data: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Calculate correlation matrix for assets.
        
        Args:
            returns_data: Dictionary of returns {symbol: np.ndarray}
        
        Returns:
            Correlation matrix
        """
        if not returns_data:
            return np.array([])
        
        symbols = list(returns_data.keys())
        
        # Get minimum length
        min_length = min(len(returns_data[s]) for s in symbols)
        
        if min_length < 2:
            return np.eye(len(symbols))
        
        # Build returns matrix
        returns_matrix = np.array([
            returns_data[s][-min_length:] for s in symbols
        ])
        
        # Calculate correlation
        correlation_matrix = np.corrcoef(returns_matrix)
        
        self.correlation_matrix = correlation_matrix
        
        return correlation_matrix
    
    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Annualize returns (assuming daily)
        mean_return = np.mean(returns) * 252
        std_return = np.std(returns) * np.sqrt(252)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return - risk_free_rate) / std_return
        
        return sharpe
    
    def calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sortino ratio (downside deviation).
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Sortino ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Annualize returns
        mean_return = np.mean(returns) * 252
        
        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.std(downside_returns) * np.sqrt(252)
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_return - risk_free_rate) / downside_std
        
        return sortino
    
    def calculate_max_drawdown(self, equity_curve: np.ndarray) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: Array of equity values
        
        Returns:
            Tuple of (max_drawdown, start_idx, end_idx)
        """
        if len(equity_curve) == 0:
            return 0.0, 0, 0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_curve)
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        # Find maximum drawdown
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        
        # Find start of drawdown
        start_idx = np.argmax(running_max[:max_dd_idx + 1])
        
        return abs(max_dd), start_idx, max_dd_idx
    
    def optimize_portfolio_weights(
        self,
        returns_data: Dict[str, np.ndarray],
        method: str = 'sharpe'
    ) -> Dict[str, float]:
        """
        Optimize portfolio weights.
        
        Args:
            returns_data: Dictionary of returns {symbol: np.ndarray}
            method: Optimization method ('sharpe', 'min_variance', 'risk_parity')
        
        Returns:
            Dictionary of optimal weights {symbol: weight}
        """
        if not returns_data:
            return {}
        
        symbols = list(returns_data.keys())
        n_assets = len(symbols)
        
        # Build returns matrix
        min_length = min(len(returns_data[s]) for s in symbols)
        
        if min_length < 2:
            # Equal weights if insufficient data
            equal_weight = 1.0 / n_assets
            return {s: equal_weight for s in symbols}
        
        returns_matrix = np.array([
            returns_data[s][-min_length:] for s in symbols
        ])
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns_matrix)
        
        if method == 'min_variance':
            # Minimum variance portfolio
            inv_cov = np.linalg.inv(cov_matrix)
            ones = np.ones(n_assets)
            weights = inv_cov @ ones / (ones @ inv_cov @ ones)
            
        elif method == 'risk_parity':
            # Risk parity (equal risk contribution)
            inv_vol = 1.0 / np.sqrt(np.diag(cov_matrix))
            weights = inv_vol / np.sum(inv_vol)
            
        else:  # 'sharpe'
            # Maximum Sharpe ratio (simplified)
            mean_returns = np.mean(returns_matrix, axis=1)
            inv_cov = np.linalg.inv(cov_matrix)
            weights = inv_cov @ mean_returns
            weights = weights / np.sum(np.abs(weights))
        
        # Ensure non-negative and normalized
        weights = np.maximum(weights, 0)
        weights = weights / np.sum(weights)
        
        return {symbols[i]: weights[i] for i in range(n_assets)}
    
    def calculate_beta(
        self,
        asset_returns: np.ndarray,
        market_returns: np.ndarray
    ) -> float:
        """
        Calculate beta (market sensitivity).
        
        Args:
            asset_returns: Asset returns
            market_returns: Market returns
        
        Returns:
            Beta value
        """
        if len(asset_returns) == 0 or len(market_returns) == 0:
            return 1.0
        
        # Align lengths
        min_length = min(len(asset_returns), len(market_returns))
        asset_returns = asset_returns[-min_length:]
        market_returns = market_returns[-min_length:]
        
        # Calculate covariance and variance
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        
        return beta
    
    def stress_test(
        self,
        positions: Dict[str, Dict],
        scenarios: List[Dict[str, float]]
    ) -> List[Dict]:
        """
        Perform stress testing on portfolio.
        
        Args:
            positions: Dictionary of positions {symbol: {'value': float}}
            scenarios: List of scenarios {symbol: shock_percentage}
        
        Returns:
            List of stress test results
        """
        results = []
        
        total_value = sum(p['value'] for p in positions.values())
        
        for i, scenario in enumerate(scenarios):
            # Calculate portfolio impact
            portfolio_impact = 0.0
            
            for symbol, position in positions.items():
                if symbol in scenario:
                    shock = scenario[symbol]
                    impact = position['value'] * shock
                    portfolio_impact += impact
            
            impact_pct = portfolio_impact / total_value if total_value > 0 else 0.0
            
            results.append({
                'scenario': i + 1,
                'impact_value': portfolio_impact,
                'impact_percentage': impact_pct,
                'new_value': total_value + portfolio_impact
            })
        
        return results
