"""
from pathlib import Path
Monte Carlo Simulation for Trading Risk Management
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
import matplotlib.pyplot as plt
try:
    from scipy import stats
except ImportError:
    scipy = None
import seaborn as sns
from datetime import datetime, timedelta
import pathlib
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    expected_return: float
    median_return: float
    worst_case: float
    best_case: float
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional Value at Risk (95%)
    max_drawdown: float
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    percentiles: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'expected_return': self.expected_return,
            'median_return': self.median_return,
            'worst_case': self.worst_case,
            'best_case': self.best_case,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'percentiles': self.percentiles
        }


class MonteCarloSimulator:
    """
    Advanced Monte Carlo simulation for trading risk management
    
    Features:
    - Portfolio simulation with correlations
    - Drawdown analysis
    - Value at Risk (VaR) calculation
    - Conditional Value at Risk (CVaR)
    - Stress testing
    - Scenario analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Simulation parameters
        self.num_simulations = self.config.get('num_simulations', 10000)
        self.time_horizon = self.config.get('time_horizon', 252)  # Trading days
        self.confidence_level = self.config.get('confidence_level', 0.95)
        
        # Risk-free rate for Sharpe ratio
        self.risk_free_rate = self.config.get('risk_free_rate', 0.02)  # 2%
        
        logger.info("Monte Carlo Simulator initialized")
    
    def simulate_returns(self, mean_return: float, volatility: float, 
                        distribution: str = 'normal') -> np.ndarray:
        """
        Simulate daily returns
        
        Args:
            mean_return: Expected daily return
            volatility: Daily volatility
            distribution: Return distribution ('normal', 't', 'skewed')
            
        Returns:
            Array of simulated returns
        """
        if distribution == 'normal':
            # Normal distribution
            returns = np.random.normal(mean_return, volatility, 
                                      (self.num_simulations, self.time_horizon))
        elif distribution == 't':
            # Student's t-distribution (fatter tails)
            df = self.config.get('t_distribution_df', 5)  # Degrees of freedom
            returns = stats.t.rvs(df, loc=mean_return, scale=volatility, 
                                 size=(self.num_simulations, self.time_horizon))
        elif distribution == 'skewed':
            # Skewed normal distribution
            skew = self.config.get('skew_parameter', -0.5)  # Negative skew common in markets
            returns = stats.skewnorm.rvs(skew, loc=mean_return, scale=volatility, 
                                        size=(self.num_simulations, self.time_horizon))
        else:
            logger.warning(f"Unknown distribution: {distribution}, using normal")
            returns = np.random.normal(mean_return, volatility, 
                                      (self.num_simulations, self.time_horizon))
        
        return returns
    
    def simulate_portfolio(self, assets: List[Dict[str, Any]], 
                         weights: Optional[List[float]] = None) -> MonteCarloResult:
        """
        Simulate portfolio performance
        
        Args:
            assets: List of assets with 'mean_return', 'volatility', and 'correlation' fields
            weights: Portfolio weights (if None, equal weights are used)
            
        Returns:
            MonteCarloResult with simulation statistics
        """
        num_assets = len(assets)
        
        if num_assets == 0:
            logger.warning("No assets provided for simulation")
            return self._empty_result()
        
        # Use equal weights if not provided
        if weights is None:
            weights = [1.0 / num_assets] * num_assets
        
        # Ensure weights sum to 1
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        
        # Extract parameters
        means = np.array([asset.get('mean_return', 0) for asset in assets])
        vols = np.array([asset.get('volatility', 0.01) for asset in assets])
        
        # Build correlation matrix
        corr_matrix = np.ones((num_assets, num_assets))
        for i in range(num_assets):
            for j in range(i+1, num_assets):
                corr = assets[i].get('correlation', {}).get(assets[j].get('ticker', ''), 0)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
        
        # Build covariance matrix
        cov_matrix = np.outer(vols, vols) * corr_matrix
        
        # Generate correlated returns
        try:
            # Cholesky decomposition for correlated random variables
            L = np.linalg.cholesky(cov_matrix)
            
            # Generate uncorrelated random variables
            uncorrelated = np.random.normal(0, 1, (self.num_simulations, self.time_horizon, num_assets))
            
            # Transform to correlated variables
            Z = np.zeros_like(uncorrelated)
            for i in range(self.num_simulations):
                for j in range(self.time_horizon):
                    Z[i, j, :] = means + np.dot(L, uncorrelated[i, j, :])
            
            # Calculate portfolio returns
            portfolio_returns = np.zeros((self.num_simulations, self.time_horizon))
            for i in range(self.num_simulations):
                for j in range(self.time_horizon):
                    portfolio_returns[i, j] = np.sum(weights * Z[i, j, :])
            
        except np.linalg.LinAlgError:
            logger.warning("Correlation matrix is not positive definite, using uncorrelated simulation")
            
            # Fall back to uncorrelated simulation
            asset_returns = [
                self.simulate_returns(asset.get('mean_return', 0), asset.get('volatility', 0.01))
                for asset in assets
            ]
            
            # Calculate portfolio returns
            portfolio_returns = np.zeros((self.num_simulations, self.time_horizon))
            for i in range(num_assets):
                portfolio_returns += weights[i] * asset_returns[i]
        
        # Calculate equity curves
        equity_curves = np.cumprod(1 + portfolio_returns, axis=1)
        
        # Calculate statistics
        final_values = equity_curves[:, -1]
        
        # Calculate returns
        total_returns = final_values - 1
        
        # Calculate drawdowns
        max_drawdowns = self._calculate_drawdowns(equity_curves)
        
        # Calculate VaR and CVaR
        var_95 = np.percentile(total_returns, 5)  # 95% VaR
        cvar_95 = np.mean(total_returns[total_returns <= var_95])  # 95% CVaR
        
        # Calculate win rate
        win_rate = np.mean(total_returns > 0)
        
        # Calculate Sharpe ratio
        excess_return = np.mean(total_returns) - self.risk_free_rate
        sharpe_ratio = excess_return / np.std(total_returns) if np.std(total_returns) > 0 else 0
        
        # Calculate Sortino ratio (downside risk)
        downside_returns = total_returns[total_returns < 0]
        downside_risk = np.std(downside_returns) if len(downside_returns) > 0 else 0.001
        sortino_ratio = excess_return / downside_risk if downside_risk > 0 else 0
        
        # Calculate percentiles
        percentiles = {
            '1%': np.percentile(total_returns, 1),
            '5%': np.percentile(total_returns, 5),
            '10%': np.percentile(total_returns, 10),
            '25%': np.percentile(total_returns, 25),
            '50%': np.percentile(total_returns, 50),
            '75%': np.percentile(total_returns, 75),
            '90%': np.percentile(total_returns, 90),
            '95%': np.percentile(total_returns, 95),
            '99%': np.percentile(total_returns, 99)
        }
        
        # Create result
        result = MonteCarloResult(
            expected_return=np.mean(total_returns),
            median_return=np.median(total_returns),
            worst_case=np.min(total_returns),
            best_case=np.max(total_returns),
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=np.mean(max_drawdowns),
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            percentiles=percentiles
        )
        
        # Store equity curves for plotting
        self.last_equity_curves = equity_curves[:100]  # Store first 100 curves
        
        return result
    
    def _calculate_drawdowns(self, equity_curves: np.ndarray) -> np.ndarray:
        """Calculate maximum drawdown for each simulation"""
        max_drawdowns = np.zeros(equity_curves.shape[0])
        
        for i in range(equity_curves.shape[0]):
            # Calculate running maximum
            running_max = np.maximum.accumulate(equity_curves[i])
            
            # Calculate drawdowns
            drawdowns = (running_max - equity_curves[i]) / running_max
            
            # Get maximum drawdown
            max_drawdowns[i] = np.max(drawdowns)
        
        return max_drawdowns
    
    def _empty_result(self) -> MonteCarloResult:
        """Return empty result when simulation fails"""
        return MonteCarloResult(
            expected_return=0.0,
            median_return=0.0,
            worst_case=0.0,
            best_case=0.0,
            var_95=0.0,
            cvar_95=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            percentiles={
                '1%': 0.0, '5%': 0.0, '10%': 0.0, '25%': 0.0, '50%': 0.0,
                '75%': 0.0, '90%': 0.0, '95%': 0.0, '99%': 0.0
            }
        )
    
    def simulate_from_history(self, returns: List[float], 
                            bootstrap: bool = True) -> MonteCarloResult:
        """
        Simulate future performance based on historical returns
        
        Args:
            returns: Historical returns
            bootstrap: Whether to use bootstrap resampling (True) or fit distribution (False)
            
        Returns:
            MonteCarloResult with simulation statistics
        """
        if not returns:
            logger.warning("No historical returns provided")
            return self._empty_result()
        
        returns_array = np.array(returns)
        
        if bootstrap:
            # Bootstrap resampling
            simulated_returns = np.zeros((self.num_simulations, self.time_horizon))
            
            for i in range(self.num_simulations):
                # Resample with replacement
                simulated_returns[i] = np.random.choice(
                    returns_array, size=self.time_horizon, replace=True
                )
        else:
            # Fit distribution
            mean_return = np.mean(returns_array)
            volatility = np.std(returns_array)
            
            # Check for skewness and kurtosis
            skewness = stats.skew(returns_array)
            kurtosis = stats.kurtosis(returns_array)
            
            if abs(kurtosis) > 1:
                # Fat tails, use t-distribution
                df, loc, scale = stats.t.fit(returns_array)
                simulated_returns = stats.t.rvs(
                    df, loc=loc, scale=scale, 
                    size=(self.num_simulations, self.time_horizon)
                )
            elif abs(skewness) > 0.5:
                # Skewed, use skewed normal
                a, loc, scale = stats.skewnorm.fit(returns_array)
                simulated_returns = stats.skewnorm.rvs(
                    a, loc=loc, scale=scale, 
                    size=(self.num_simulations, self.time_horizon)
                )
            else:
                # Normal distribution
                simulated_returns = np.random.normal(
                    mean_return, volatility, 
                    (self.num_simulations, self.time_horizon)
                )
        
        # Calculate equity curves
        equity_curves = np.cumprod(1 + simulated_returns, axis=1)
        
        # Calculate statistics
        final_values = equity_curves[:, -1]
        
        # Calculate returns
        total_returns = final_values - 1
        
        # Calculate drawdowns
        max_drawdowns = self._calculate_drawdowns(equity_curves)
        
        # Calculate VaR and CVaR
        var_95 = np.percentile(total_returns, 5)  # 95% VaR
        cvar_95 = np.mean(total_returns[total_returns <= var_95])  # 95% CVaR
        
        # Calculate win rate
        win_rate = np.mean(total_returns > 0)
        
        # Calculate Sharpe ratio
        excess_return = np.mean(total_returns) - self.risk_free_rate
        sharpe_ratio = excess_return / np.std(total_returns) if np.std(total_returns) > 0 else 0
        
        # Calculate Sortino ratio (downside risk)
        downside_returns = total_returns[total_returns < 0]
        downside_risk = np.std(downside_returns) if len(downside_returns) > 0 else 0.001
        sortino_ratio = excess_return / downside_risk if downside_risk > 0 else 0
        
        # Calculate percentiles
        percentiles = {
            '1%': np.percentile(total_returns, 1),
            '5%': np.percentile(total_returns, 5),
            '10%': np.percentile(total_returns, 10),
            '25%': np.percentile(total_returns, 25),
            '50%': np.percentile(total_returns, 50),
            '75%': np.percentile(total_returns, 75),
            '90%': np.percentile(total_returns, 90),
            '95%': np.percentile(total_returns, 95),
            '99%': np.percentile(total_returns, 99)
        }
        
        # Create result
        result = MonteCarloResult(
            expected_return=np.mean(total_returns),
            median_return=np.median(total_returns),
            worst_case=np.min(total_returns),
            best_case=np.max(total_returns),
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=np.mean(max_drawdowns),
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            percentiles=percentiles
        )
        
        # Store equity curves for plotting
        self.last_equity_curves = equity_curves[:100]  # Store first 100 curves
        
        return result
    
    def stress_test(self, assets: List[Dict[str, Any]], 
                  weights: Optional[List[float]] = None,
                  scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, MonteCarloResult]:
        """
        Perform stress testing on portfolio
        
        Args:
            assets: List of assets with 'mean_return', 'volatility', and 'correlation' fields
            weights: Portfolio weights (if None, equal weights are used)
            scenarios: List of stress scenarios to test
            
        Returns:
            Dictionary of scenario names to MonteCarloResult
        """
        if not scenarios:
            # Default stress scenarios
            scenarios = [
                {
                    'name': 'Market Crash',
                    'return_shock': -0.3,  # -30% return shock
                    'volatility_multiplier': 2.0,  # Double volatility
                    'correlation_increase': 0.3  # Correlations increase by 0.3
                },
                {
                    'name': 'Recession',
                    'return_shock': -0.15,  # -15% return shock
                    'volatility_multiplier': 1.5,  # 50% more volatility
                    'correlation_increase': 0.2  # Correlations increase by 0.2
                },
                {
                    'name': 'Sector Rotation',
                    'return_shock': -0.05,  # -5% return shock
                    'volatility_multiplier': 1.2,  # 20% more volatility
                    'correlation_increase': -0.1  # Correlations decrease by 0.1
                }
            ]
        
        results = {}
        
        # Run base case
        base_result = self.simulate_portfolio(assets, weights)
        results['Base Case'] = base_result
        
        # Run stress scenarios
        for scenario in scenarios:
            # Apply scenario adjustments
            stressed_assets = []
            
            for asset in assets:
                stressed_asset = asset.copy()
                
                # Apply return shock
                stressed_asset['mean_return'] = asset.get('mean_return', 0) + scenario.get('return_shock', 0)
                
                # Apply volatility multiplier
                stressed_asset['volatility'] = asset.get('volatility', 0.01) * scenario.get('volatility_multiplier', 1.0)
                
                # Apply correlation adjustment
                if 'correlation' in asset:
                    stressed_correlation = {}
                    for ticker, corr in asset['correlation'].items():
                        new_corr = corr + scenario.get('correlation_increase', 0)
                        # Ensure correlation is between -1 and 1
                        new_corr = max(-1.0, min(1.0, new_corr))
                        stressed_correlation[ticker] = new_corr
                    stressed_asset['correlation'] = stressed_correlation
                
                stressed_assets.append(stressed_asset)
            
            # Run simulation with stressed assets
            scenario_result = self.simulate_portfolio(stressed_assets, weights)
            results[scenario['name']] = scenario_result
        
        return results
    
    def plot_simulation_results(self, title: str = "Monte Carlo Simulation",
                              save_path: Optional[str] = None):
        """
        Plot Monte Carlo simulation results
        
        Args:
            title: Plot title
            save_path: Path to save plot, if None, plot is displayed
        """
        if not hasattr(self, 'last_equity_curves') or self.last_equity_curves is None:
            logger.warning("No simulation results to plot")
            return
        
        equity_curves = self.last_equity_curves
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot equity curves
        for i in range(min(100, len(equity_curves))):
            ax1.plot(equity_curves[i], alpha=0.1, color='blue')
        
        # Plot median curve
        median_curve = np.median(equity_curves, axis=0)
        ax1.plot(median_curve, linewidth=2, color='red', label='Median')
        
        # Plot percentiles
        percentile_5 = np.percentile(equity_curves, 5, axis=0)
        percentile_95 = np.percentile(equity_curves, 95, axis=0)
        
        ax1.plot(percentile_5, linewidth=1.5, color='orange', linestyle='--', label='5th Percentile')
        ax1.plot(percentile_95, linewidth=1.5, color='green', linestyle='--', label='95th Percentile')
        
        # Add labels and title
        ax1.set_ylabel('Portfolio Value (Multiple of Initial)')
        ax1.set_title(title)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot histogram of final values
        final_values = equity_curves[:, -1]
        sns.histplot(final_values, kde=True, ax=ax2)
        ax2.axvline(np.median(final_values), color='red', linestyle='-', label='Median')
        ax2.axvline(np.percentile(final_values, 5), color='orange', linestyle='--', label='5th Percentile')
        ax2.set_xlabel('Final Portfolio Value')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved Monte Carlo simulation plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
