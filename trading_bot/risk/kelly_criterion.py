"""
from pathlib import Path
Kelly Criterion Implementation for Optimal Position Sizing
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
try:
    from scipy import stats
except ImportError:
    scipy = None
import matplotlib.pyplot as plt
from dataclasses import field
import pathlib
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class KellyResult:
    """Results from Kelly criterion calculation"""
    optimal_fraction: float
    half_kelly: float
    quarter_kelly: float
    expected_return: float
    win_rate: float
    win_loss_ratio: float
    risk_of_ruin: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'optimal_fraction': self.optimal_fraction,
            'half_kelly': self.half_kelly,
            'quarter_kelly': self.quarter_kelly,
            'expected_return': self.expected_return,
            'win_rate': self.win_rate,
            'win_loss_ratio': self.win_loss_ratio,
            'risk_of_ruin': self.risk_of_ruin
        }


class KellyCriterion:
    """
    Advanced Kelly Criterion implementation for optimal position sizing
    
    Features:
    - Classical Kelly formula
    - Fractional Kelly for risk reduction
    - Multi-asset Kelly optimization
    - Risk of ruin calculation
    - Monte Carlo simulation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Default Kelly fraction (for risk management)
        self.default_fraction = self.config.get('default_fraction', 0.5)  # Half Kelly by default
        
        # Maximum allowed Kelly fraction (safety limit)
        self.max_fraction = self.config.get('max_fraction', 0.2)  # 20% max position size
        
        # Minimum required win rate for Kelly calculation
        self.min_win_rate = self.config.get('min_win_rate', 0.4)
        
        # Minimum required edge for Kelly calculation
        self.min_edge = self.config.get('min_edge', 0.05)  # 5% edge
        
        logger.info("Kelly Criterion module initialized")
    
    def calculate_kelly(self, win_rate: float, win_loss_ratio: float) -> KellyResult:
        """
        Calculate Kelly criterion for optimal position sizing
        
        Args:
            win_rate: Probability of winning (0.0 to 1.0)
            win_loss_ratio: Ratio of average win to average loss
            
        Returns:
            KellyResult with optimal fraction and related metrics
        """
        # Validate inputs
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"Invalid win rate: {win_rate}, using default")
            win_rate = 0.5
        
        if win_loss_ratio <= 0:
            logger.warning(f"Invalid win/loss ratio: {win_loss_ratio}, using default")
            win_loss_ratio = 1.0
        
        # Calculate Kelly fraction: f* = p - (1-p)/R
        # Where p = win rate, R = win/loss ratio
        kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
        
        # Calculate expected return
        expected_return = win_rate * win_loss_ratio - (1 - win_rate)
        
        # Apply safety limits
        if kelly_fraction < 0:
            kelly_fraction = 0
        
        if kelly_fraction > self.max_fraction:
            logger.info(f"Kelly fraction {kelly_fraction:.2f} exceeds maximum, limiting to {self.max_fraction}")
            kelly_fraction = self.max_fraction
        
        # Calculate risk of ruin
        risk_of_ruin = self._calculate_risk_of_ruin(win_rate, win_loss_ratio, kelly_fraction)
        
        # Create result
        result = KellyResult(
            optimal_fraction=kelly_fraction,
            half_kelly=kelly_fraction / 2,
            quarter_kelly=kelly_fraction / 4,
            expected_return=expected_return,
            win_rate=win_rate,
            win_loss_ratio=win_loss_ratio,
            risk_of_ruin=risk_of_ruin
        )
        
        return result
    
    def calculate_kelly_from_history(self, trade_history: List[Dict[str, Any]]) -> KellyResult:
        """
        Calculate Kelly criterion from trade history
        
        Args:
            trade_history: List of trade results with 'profit' field
            
        Returns:
            KellyResult with optimal fraction and related metrics
        """
        if not trade_history:
            logger.warning("Empty trade history, using default values")
            return KellyResult(
                optimal_fraction=0,
                half_kelly=0,
                quarter_kelly=0,
                expected_return=0,
                win_rate=0,
                win_loss_ratio=0,
                risk_of_ruin=1.0
            )
        
        # Extract profits
        profits = [trade.get('profit', 0) for trade in trade_history]
        
        # Calculate win rate
        wins = sum(1 for p in profits if p > 0)
        win_rate = wins / len(profits) if len(profits) > 0 else 0
        
        # Calculate average win and loss
        avg_win = np.mean([p for p in profits if p > 0]) if any(p > 0 for p in profits) else 0
        avg_loss = abs(np.mean([p for p in profits if p < 0])) if any(p < 0 for p in profits) else 1
        
        # Calculate win/loss ratio
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
        
        # Calculate Kelly
        return self.calculate_kelly(win_rate, win_loss_ratio)
    
    def _calculate_risk_of_ruin(self, win_rate: float, win_loss_ratio: float, 
                              fraction: float, num_trades: int = 1000) -> float:
        """
        Calculate risk of ruin using simulation
        
        Args:
            win_rate: Probability of winning
            win_loss_ratio: Ratio of average win to average loss
            fraction: Kelly fraction to use
            num_trades: Number of trades to simulate
            
        Returns:
            Probability of ruin (0.0 to 1.0)
        """
        # Run Monte Carlo simulation
        num_simulations = 1000
        ruin_count = 0
        
        for _ in range(num_simulations):
            # Start with 1.0 (100%) capital
            capital = 1.0
            
            for _ in range(num_trades):
                # Simulate trade
                if np.random.random() < win_rate:
                    # Win
                    capital *= (1 + fraction * win_loss_ratio)
                else:
                    # Loss
                    capital *= (1 - fraction)
                
                # Check for ruin (less than 10% of initial capital)
                if capital < 0.1:
                    ruin_count += 1
                    break
        
        return ruin_count / num_simulations
    
    def optimize_portfolio_kelly(self, assets: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Optimize Kelly fractions for a portfolio of assets
        
        Args:
            assets: List of assets with 'win_rate', 'win_loss_ratio', and 'correlation' fields
            
        Returns:
            Dictionary of optimal fractions by asset
        """
        # Simple implementation for uncorrelated assets
        # In a real system, this would use matrix calculations for correlated assets
        
        total_kelly = 0
        fractions = {}
        
        for asset in assets:
            ticker = asset.get('ticker', 'unknown')
            win_rate = asset.get('win_rate', 0.5)
            win_loss_ratio = asset.get('win_loss_ratio', 1.0)
            
            # Calculate individual Kelly
            kelly_result = self.calculate_kelly(win_rate, win_loss_ratio)
            
            # Store fraction
            fractions[ticker] = kelly_result.optimal_fraction
            total_kelly += kelly_result.optimal_fraction
        
        # Normalize if total exceeds maximum
        if total_kelly > self.max_fraction:
            scale_factor = self.max_fraction / total_kelly
            for ticker in fractions:
                fractions[ticker] *= scale_factor
        
        return fractions
    
    def simulate_kelly_performance(self, win_rate: float, win_loss_ratio: float, 
                                 kelly_fraction: float, num_trades: int = 1000, 
                                 num_simulations: int = 100) -> Dict[str, Any]:
        """
        Simulate performance using Kelly criterion
        
        Args:
            win_rate: Probability of winning
            win_loss_ratio: Ratio of average win to average loss
            kelly_fraction: Kelly fraction to use
            num_trades: Number of trades to simulate
            num_simulations: Number of simulations to run
            
        Returns:
            Simulation results
        """
        # Store results
        final_capitals = []
        equity_curves = []
        max_drawdowns = []
        
        for _ in range(num_simulations):
            # Start with 1.0 (100%) capital
            capital = 1.0
            equity_curve = [capital]
            peak_capital = capital
            max_drawdown = 0
            
            for _ in range(num_trades):
                # Simulate trade
                if np.random.random() < win_rate:
                    # Win
                    capital *= (1 + kelly_fraction * win_loss_ratio)
                else:
                    # Loss
                    capital *= (1 - kelly_fraction)
                
                # Update equity curve
                equity_curve.append(capital)
                
                # Update peak and drawdown
                if capital > peak_capital:
                    peak_capital = capital
                
                drawdown = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            final_capitals.append(capital)
            equity_curves.append(equity_curve)
            max_drawdowns.append(max_drawdown)
        
        # Calculate statistics
        mean_final = np.mean(final_capitals)
        median_final = np.median(final_capitals)
        min_final = np.min(final_capitals)
        max_final = np.max(final_capitals)
        
        mean_drawdown = np.mean(max_drawdowns)
        median_drawdown = np.median(max_drawdowns)
        max_drawdown = np.max(max_drawdowns)
        
        # Calculate percentiles
        percentiles = {
            '5%': np.percentile(final_capitals, 5),
            '25%': np.percentile(final_capitals, 25),
            '50%': np.percentile(final_capitals, 50),
            '75%': np.percentile(final_capitals, 75),
            '95%': np.percentile(final_capitals, 95)
        }
        
        return {
            'mean_final_capital': mean_final,
            'median_final_capital': median_final,
            'min_final_capital': min_final,
            'max_final_capital': max_final,
            'mean_max_drawdown': mean_drawdown,
            'median_max_drawdown': median_drawdown,
            'max_max_drawdown': max_drawdown,
            'percentiles': percentiles,
            'equity_curves': equity_curves[:10]  # Return first 10 curves for plotting
        }
    
    def plot_kelly_simulation(self, simulation_results: Dict[str, Any], 
                            title: str = "Kelly Criterion Simulation",
                            save_path: Optional[str] = None):
        """
        Plot Kelly simulation results
        
        Args:
            simulation_results: Results from simulate_kelly_performance
            title: Plot title
            save_path: Path to save plot, if None, plot is displayed
        """
        equity_curves = simulation_results.get('equity_curves', [])
        
        if not equity_curves:
            logger.warning("No equity curves to plot")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Plot equity curves
        for i, curve in enumerate(equity_curves):
            plt.plot(curve, alpha=0.3, color='blue')
        
        # Plot median curve
        median_curve = np.median(np.array(equity_curves), axis=0)
        plt.plot(median_curve, linewidth=2, color='red', label='Median')
        
        # Add labels and title
        plt.xlabel('Number of Trades')
        plt.ylabel('Capital (Multiple of Initial)')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add statistics
        stats_text = (
            f"Mean Final Capital: {simulation_results['mean_final_capital']:.2f}x\n"
            f"Median Final Capital: {simulation_results['median_final_capital']:.2f}x\n"
            f"Max Drawdown: {simulation_results['max_max_drawdown']:.2%}\n"
            f"5th Percentile: {simulation_results['percentiles']['5%']:.2f}x\n"
            f"95th Percentile: {simulation_results['percentiles']['95%']:.2f}x"
        )
        
        plt.figtext(0.15, 0.15, stats_text, bbox=dict(facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved Kelly simulation plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
