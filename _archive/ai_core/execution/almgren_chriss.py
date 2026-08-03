"""
Almgren-Chriss Optimal Execution Model

Paper: "Optimal execution of portfolio transactions"
Almgren & Chriss (2001)

Minimizes execution cost considering:
- Market impact (permanent + temporary)
- Timing risk (price volatility)
- Trade-off via risk aversion parameter
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class MarketImpactParams:
    """Market impact model parameters."""
    eta: float = 0.1  # Temporary impact coefficient
    gamma: float = 0.01  # Permanent impact coefficient
    sigma: float = 0.02  # Price volatility
    lambda_risk: float = 1e-6  # Risk aversion parameter


@dataclass
class ExecutionSchedule:
    """Optimal execution schedule."""
    times: np.ndarray  # Time points
    trades: np.ndarray  # Trade sizes at each time
    holdings: np.ndarray  # Remaining holdings
    expected_cost: float  # Expected execution cost
    expected_variance: float  # Variance of cost
    total_shares: float  # Total shares to execute


class AlmgrenChrissExecutor:
    """
    Almgren-Chriss optimal execution.
    
    Solves for optimal trade schedule that minimizes:
    E[cost] + lambda * Var[cost]
    
    where cost includes market impact and timing risk.
    """
    
    def __init__(self, params: Optional[MarketImpactParams] = None):
        try:
            self.params = params or MarketImpactParams()
            logger.info("Almgren-Chriss executor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_optimal_schedule(
        self,
        total_shares: float,
        time_horizon: float,
        num_periods: int,
        initial_price: float = 100.0
    ) -> ExecutionSchedule:
        """
        Compute optimal execution schedule.
        
        Args:
            total_shares: Total number of shares to execute
            time_horizon: Total time to complete execution (in days)
            num_periods: Number of trading periods
            initial_price: Initial asset price
        
        Returns:
            Optimal execution schedule
        """
        try:
            tau = time_horizon / num_periods  # Time per period
        
            # Almgren-Chriss parameters
            eta = self.params.eta
            gamma = self.params.gamma
            sigma = self.params.sigma
            lambda_risk = self.params.lambda_risk
        
            # Compute kappa (decay rate)
            kappa = np.sqrt(lambda_risk * sigma ** 2 / (eta * tau))
        
            # Compute trajectory parameters
            sinh_kappa_T = np.sinh(kappa * time_horizon)
            cosh_kappa_T = np.cosh(kappa * time_horizon)
        
            # Time points
            times = np.linspace(0, time_horizon, num_periods + 1)
        
            # Optimal holdings trajectory
            holdings = np.zeros(num_periods + 1)
            for i, t in enumerate(times):
                holdings[i] = total_shares * np.sinh(kappa * (time_horizon - t)) / sinh_kappa_T
        
            # Optimal trade sizes
            trades = -np.diff(holdings)  # Negative because we're selling
        
            # Expected cost
            # Permanent impact cost
            permanent_cost = gamma * total_shares ** 2 / 2
        
            # Temporary impact cost
            temporary_cost = eta * np.sum(trades ** 2) / tau
        
            # Total expected cost
            expected_cost = permanent_cost + temporary_cost
        
            # Variance of cost
            variance_numerator = 0.5 * sigma ** 2 * total_shares ** 2 * tau
            variance_denominator = sinh_kappa_T ** 2
            expected_variance = variance_numerator * (
                cosh_kappa_T - 1
            ) / variance_denominator
        
            logger.info(
                f"Optimal schedule computed: {num_periods} periods, "
                f"cost={expected_cost:.2f}, variance={expected_variance:.2f}"
            )
        
            return ExecutionSchedule(
                times=times,
                trades=trades,
                holdings=holdings,
                expected_cost=expected_cost,
                expected_variance=expected_variance,
                total_shares=total_shares
            )
        except Exception as e:
            logger.error(f"Error in compute_optimal_schedule: {e}")
            raise
    
    def compute_linear_schedule(
        self,
        total_shares: float,
        time_horizon: float,
        num_periods: int
    ) -> ExecutionSchedule:
        """
        Compute simple linear (TWAP) schedule for comparison.
        
        Args:
            total_shares: Total shares to execute
            time_horizon: Total time
            num_periods: Number of periods
        
        Returns:
            Linear execution schedule
        """
        try:
            tau = time_horizon / num_periods
        
            # Equal-sized trades
            trade_size = total_shares / num_periods
            trades = np.full(num_periods, trade_size)
        
            # Holdings decrease linearly
            holdings = np.linspace(total_shares, 0, num_periods + 1)
        
            # Times
            times = np.linspace(0, time_horizon, num_periods + 1)
        
            # Expected cost
            permanent_cost = self.params.gamma * total_shares ** 2 / 2
            temporary_cost = self.params.eta * np.sum(trades ** 2) / tau
            expected_cost = permanent_cost + temporary_cost
        
            # Variance
            expected_variance = (
                self.params.sigma ** 2 * total_shares ** 2 * time_horizon / 12
            )
        
            return ExecutionSchedule(
                times=times,
                trades=trades,
                holdings=holdings,
                expected_cost=expected_cost,
                expected_variance=expected_variance,
                total_shares=total_shares
            )
        except Exception as e:
            logger.error(f"Error in compute_linear_schedule: {e}")
            raise
    
    def adjust_for_market_conditions(
        self,
        schedule: ExecutionSchedule,
        current_volatility: float,
        current_liquidity: float
    ) -> ExecutionSchedule:
        """
        Adjust schedule based on current market conditions.
        
        Args:
            schedule: Original schedule
            current_volatility: Current market volatility
            current_liquidity: Current market liquidity
        
        Returns:
            Adjusted schedule
        """
        # Volatility adjustment
        try:
            vol_ratio = current_volatility / self.params.sigma
        
            # Liquidity adjustment (inverse relationship)
            liquidity_factor = 1.0 / max(current_liquidity, 0.1)
        
            # Adjust trade sizes
            adjustment_factor = vol_ratio * liquidity_factor
        
            # Slow down if volatility high or liquidity low
            if adjustment_factor > 1.2:
                # Spread trades more evenly
                adjusted_trades = schedule.trades * 0.8
            elif adjustment_factor < 0.8:
                # Can be more aggressive
                adjusted_trades = schedule.trades * 1.2
            else:
                adjusted_trades = schedule.trades.copy()
        
            # Ensure total shares conserved
            adjusted_trades = adjusted_trades * (schedule.total_shares / adjusted_trades.sum())
        
            # Recompute holdings
            adjusted_holdings = np.zeros(len(schedule.holdings))
            adjusted_holdings[0] = schedule.total_shares
            for i in range(len(adjusted_trades)):
                adjusted_holdings[i+1] = adjusted_holdings[i] - adjusted_trades[i]
        
            return ExecutionSchedule(
                times=schedule.times,
                trades=adjusted_trades,
                holdings=adjusted_holdings,
                expected_cost=schedule.expected_cost * adjustment_factor,
                expected_variance=schedule.expected_variance * (adjustment_factor ** 2),
                total_shares=schedule.total_shares
            )
        except Exception as e:
            logger.error(f"Error in adjust_for_market_conditions: {e}")
            raise


class MarketImpactModel:
    """
    Market impact models.
    
    Implements various impact functions:
    - Linear (Almgren-Chriss)
    - Square-root (Gatheral)
    - Power-law
    """
    
    def __init__(self, model_type: str = 'linear'):
        try:
            self.model_type = model_type
            logger.info(f"Market impact model: {model_type}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def permanent_impact(
        self,
        trade_size: float,
        daily_volume: float,
        gamma: float = 0.01
    ) -> float:
        """
        Compute permanent market impact.
        
        Args:
            trade_size: Size of trade
            daily_volume: Average daily volume
            gamma: Impact coefficient
        
        Returns:
            Permanent price impact (in basis points)
        """
        try:
            participation_rate = trade_size / daily_volume
        
            if self.model_type == 'linear':
                return gamma * participation_rate
            elif self.model_type == 'square_root':
                return gamma * np.sqrt(participation_rate)
            elif self.model_type == 'power_law':
                return gamma * (participation_rate ** 0.6)
            else:
                return gamma * participation_rate
        except Exception as e:
            logger.error(f"Error in permanent_impact: {e}")
            raise
    
    def temporary_impact(
        self,
        trade_size: float,
        daily_volume: float,
        eta: float = 0.1
    ) -> float:
        """
        Compute temporary market impact.
        
        Args:
            trade_size: Size of trade
            daily_volume: Average daily volume
            eta: Impact coefficient
        
        Returns:
            Temporary price impact (in basis points)
        """
        try:
            participation_rate = trade_size / daily_volume
        
            if self.model_type == 'linear':
                return eta * participation_rate
            elif self.model_type == 'square_root':
                return eta * np.sqrt(participation_rate)
            elif self.model_type == 'power_law':
                return eta * (participation_rate ** 0.6)
            else:
                return eta * participation_rate
        except Exception as e:
            logger.error(f"Error in temporary_impact: {e}")
            raise
    
    def total_impact(
        self,
        trade_size: float,
        daily_volume: float,
        gamma: float = 0.01,
        eta: float = 0.1
    ) -> float:
        """Compute total market impact."""
        try:
            permanent = self.permanent_impact(trade_size, daily_volume, gamma)
            temporary = self.temporary_impact(trade_size, daily_volume, eta)
            return permanent + temporary
        except Exception as e:
            logger.error(f"Error in total_impact: {e}")
            raise


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("ALMGREN-CHRISS OPTIMAL EXECUTION DEMO")
    print("="*80)
    
    # Create executor
    params = MarketImpactParams(
        eta=0.1,
        gamma=0.01,
        sigma=0.02,
        lambda_risk=1e-6
    )
    executor = AlmgrenChrissExecutor(params)
    
    # Compute optimal schedule
    logger.info("\n[1] Computing optimal execution schedule...")
    schedule = executor.compute_optimal_schedule(
        total_shares=10000,
        time_horizon=1.0,  # 1 day
        num_periods=10,
        initial_price=100.0
    )
    
    logger.info(f"\nOptimal Schedule:")
    logger.info(f"  Expected Cost: ${schedule.expected_cost:.2f}")
    logger.info(f"  Expected Variance: {schedule.expected_variance:.4f}")
    logger.info(f"  Trade sizes: {schedule.trades}")
    logger.info(f"  Holdings: {schedule.holdings}")
    
    # Compare with linear schedule
    logger.info("\n[2] Comparing with linear (TWAP) schedule...")
    linear_schedule = executor.compute_linear_schedule(
        total_shares=10000,
        time_horizon=1.0,
        num_periods=10
    )
    
    logger.info(f"\nLinear Schedule:")
    logger.info(f"  Expected Cost: ${linear_schedule.expected_cost:.2f}")
    logger.info(f"  Expected Variance: {linear_schedule.expected_variance:.4f}")
    
    cost_savings = linear_schedule.expected_cost - schedule.expected_cost
    logger.info(f"\nCost Savings: ${cost_savings:.2f} ({cost_savings/linear_schedule.expected_cost*100:.1f}%)")
    
    # Test market impact model
    logger.info("\n[3] Testing market impact models...")
    impact_model = MarketImpactModel('square_root')
    
    trade_sizes = [1000, 5000, 10000]
    daily_volume = 1000000
    
    for size in trade_sizes:
        impact = impact_model.total_impact(size, daily_volume)
        logger.info(f"  Trade size {size}: {impact*10000:.2f} bps impact")
    
    # Test market condition adjustment
    logger.info("\n[4] Testing market condition adjustment...")
    adjusted_schedule = executor.adjust_for_market_conditions(
        schedule,
        current_volatility=0.03,  # Higher volatility
        current_liquidity=0.5  # Lower liquidity
    )
    
    logger.info(f"\nAdjusted Schedule:")
    logger.info(f"  Expected Cost: ${adjusted_schedule.expected_cost:.2f}")
    logger.info(f"  Trade sizes: {adjusted_schedule.trades}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
