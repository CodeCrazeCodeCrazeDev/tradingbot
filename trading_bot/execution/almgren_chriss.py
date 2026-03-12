"""
Almgren-Chriss Optimal Execution

Based on: "Optimal execution of portfolio transactions" (2000)
https://www.math.nyu.edu/faculty/chriss/optliq_f.pdf

Computes optimal execution schedule to minimize:
- Market impact cost
- Timing risk (price volatility)
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class ExecutionSchedule:
    """Optimal execution schedule"""
    total_quantity: float
    time_horizon: int  # minutes
    trajectory: List[float]  # Quantity to trade each period
    timestamps: List[int]  # Time in minutes
    expected_cost: float  # Expected execution cost
    expected_variance: float  # Variance of execution cost


class AlmgrenChrissOptimizer:
    """
    Almgren-Chriss optimal execution optimizer
    
    Minimizes: E[Cost] + λ * Var[Cost]
    where λ is risk aversion parameter
    """
    
    def __init__(
        self,
        risk_aversion: float = 0.5,
        permanent_impact: float = 0.1,
        temporary_impact: float = 0.01,
        volatility: float = 0.01
    ):
        """
        Args:
            risk_aversion: Risk aversion parameter (λ)
            permanent_impact: Permanent market impact coefficient
            temporary_impact: Temporary market impact coefficient
            volatility: Price volatility (σ)
        """
        try:
            self.risk_aversion = risk_aversion
            self.permanent_impact = permanent_impact
            self.temporary_impact = temporary_impact
            self.volatility = volatility
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_optimal_trajectory(
        self,
        total_quantity: float,
        time_horizon: int,
        dt: float = 1.0
    ) -> ExecutionSchedule:
        """
        Compute optimal execution trajectory
        
        Args:
            total_quantity: Total quantity to execute (lots)
            time_horizon: Time horizon in minutes
            dt: Time step in minutes
            
        Returns:
            ExecutionSchedule with optimal trajectory
        """
        try:
            n_steps = int(time_horizon / dt)
        
            # Parameters
            gamma = self.permanent_impact
            eta = self.temporary_impact
            sigma = self.volatility
            lambda_risk = self.risk_aversion
        
            # Almgren-Chriss solution
            kappa = np.sqrt(lambda_risk * sigma**2 / eta)
            tau = time_horizon
        
            # Optimal trajectory: x(t) = X * sinh(κ(T-t)) / sinh(κT)
            timestamps = np.linspace(0, tau, n_steps + 1)
        
            if kappa * tau < 1e-6:
                # Linear trajectory for small κτ
                holdings = total_quantity * (1 - timestamps / tau)
            else:
                holdings = total_quantity * np.sinh(kappa * (tau - timestamps)) / np.sinh(kappa * tau)
        
            # Trading trajectory (derivatives)
            trajectory = -np.diff(holdings)
        
            # Ensure non-negative and sum to total
            trajectory = np.maximum(trajectory, 0)
            trajectory = trajectory * (total_quantity / trajectory.sum())
        
            # Expected cost
            expected_cost = self._calculate_expected_cost(
                trajectory, dt, gamma, eta
            )
        
            # Variance
            expected_variance = self._calculate_variance(
                holdings[:-1], dt, sigma
            )
        
            schedule = ExecutionSchedule(
                total_quantity=total_quantity,
                time_horizon=time_horizon,
                trajectory=trajectory.tolist(),
                timestamps=timestamps[:-1].tolist(),
                expected_cost=expected_cost,
                expected_variance=expected_variance
            )
        
            logger.info(
                f"Optimal schedule: {total_quantity:.2f} lots over {time_horizon} min, "
                f"cost: ${expected_cost:.2f}, variance: {expected_variance:.6f}"
            )
        
            return schedule
        except Exception as e:
            logger.error(f"Error in compute_optimal_trajectory: {e}")
            raise
    
    def _calculate_expected_cost(
        self,
        trajectory: np.ndarray,
        dt: float,
        gamma: float,
        eta: float
    ) -> float:
        """Calculate expected execution cost"""
        # Permanent impact cost
        try:
            permanent_cost = gamma * np.sum(trajectory)**2 / 2
        
            # Temporary impact cost
            temporary_cost = eta * np.sum(trajectory**2) * dt
        
            total_cost = permanent_cost + temporary_cost
        
            return total_cost
        except Exception as e:
            logger.error(f"Error in _calculate_expected_cost: {e}")
            raise
    
    def _calculate_variance(
        self,
        holdings: np.ndarray,
        dt: float,
        sigma: float
    ) -> float:
        """Calculate variance of execution cost"""
        # Variance from price volatility
        try:
            variance = sigma**2 * np.sum(holdings**2) * dt
        
            return variance
        except Exception as e:
            logger.error(f"Error in _calculate_variance: {e}")
            raise
    
    def compute_twap_schedule(
        self,
        total_quantity: float,
        time_horizon: int,
        dt: float = 1.0
    ) -> ExecutionSchedule:
        """
        Compute TWAP (Time-Weighted Average Price) schedule
        Simple baseline: equal quantities each period
        
        Args:
            total_quantity: Total quantity to execute
            time_horizon: Time horizon in minutes
            dt: Time step in minutes
            
        Returns:
            TWAP execution schedule
        """
        try:
            n_steps = int(time_horizon / dt)
        
            # Equal quantities
            quantity_per_step = total_quantity / n_steps
            trajectory = [quantity_per_step] * n_steps
            timestamps = list(np.arange(0, time_horizon, dt))
        
            # Calculate costs
            trajectory_array = np.array(trajectory)
            expected_cost = self._calculate_expected_cost(
                trajectory_array, dt,
                self.permanent_impact, self.temporary_impact
            )
        
            holdings = np.array([total_quantity * (1 - i/n_steps) for i in range(n_steps)])
            expected_variance = self._calculate_variance(
                holdings, dt, self.volatility
            )
        
            return ExecutionSchedule(
                total_quantity=total_quantity,
                time_horizon=time_horizon,
                trajectory=trajectory,
                timestamps=timestamps,
                expected_cost=expected_cost,
                expected_variance=expected_variance
            )
        except Exception as e:
            logger.error(f"Error in compute_twap_schedule: {e}")
            raise
    
    def compute_vwap_schedule(
        self,
        total_quantity: float,
        volume_profile: List[float],
        time_horizon: int
    ) -> ExecutionSchedule:
        """
        Compute VWAP (Volume-Weighted Average Price) schedule
        Trade proportional to expected volume
        
        Args:
            total_quantity: Total quantity to execute
            volume_profile: Expected volume for each period
            time_horizon: Time horizon in minutes
            
        Returns:
            VWAP execution schedule
        """
        # Normalize volume profile
        try:
            total_volume = sum(volume_profile)
            volume_weights = [v / total_volume for v in volume_profile]
        
            # Allocate quantity proportional to volume
            trajectory = [total_quantity * w for w in volume_weights]
            timestamps = list(range(len(volume_profile)))
        
            # Calculate costs
            trajectory_array = np.array(trajectory)
            dt = time_horizon / len(volume_profile)
        
            expected_cost = self._calculate_expected_cost(
                trajectory_array, dt,
                self.permanent_impact, self.temporary_impact
            )
        
            # Holdings trajectory
            holdings = np.array([
                total_quantity * (1 - sum(volume_weights[:i])/sum(volume_weights))
                for i in range(len(volume_profile))
            ])
        
            expected_variance = self._calculate_variance(
                holdings, dt, self.volatility
            )
        
            return ExecutionSchedule(
                total_quantity=total_quantity,
                time_horizon=time_horizon,
                trajectory=trajectory,
                timestamps=timestamps,
                expected_cost=expected_cost,
                expected_variance=expected_variance
            )
        except Exception as e:
            logger.error(f"Error in compute_vwap_schedule: {e}")
            raise


def compare_strategies(
    total_quantity: float,
    time_horizon: int,
    optimizer: AlmgrenChrissOptimizer
) -> Dict[str, ExecutionSchedule]:
    """Compare different execution strategies"""
    
    # Optimal Almgren-Chriss
    try:
        optimal = optimizer.compute_optimal_trajectory(total_quantity, time_horizon)
    
        # TWAP baseline
        twap = optimizer.compute_twap_schedule(total_quantity, time_horizon)
    
        # VWAP with sample volume profile (U-shaped)
        n_periods = time_horizon
        volume_profile = [
            1.5 if i < n_periods/4 or i > 3*n_periods/4 else 0.8
            for i in range(n_periods)
        ]
        vwap = optimizer.compute_vwap_schedule(total_quantity, volume_profile, time_horizon)
    
        return {
            'optimal': optimal,
            'twap': twap,
            'vwap': vwap
        }
    except Exception as e:
        logger.error(f"Error in compare_strategies: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create optimizer
    optimizer = AlmgrenChrissOptimizer(
        risk_aversion=0.5,
        permanent_impact=0.1,
        temporary_impact=0.01,
        volatility=0.01
    )
    
    # Compute optimal schedule
    total_quantity = 1.0  # 1 lot
    time_horizon = 10  # 10 minutes
    
    print("\n" + "="*60)
    logger.info("ALMGREN-CHRISS OPTIMAL EXECUTION")
    print("="*60)
    
    # Compare strategies
    strategies = compare_strategies(total_quantity, time_horizon, optimizer)
    
    for name, schedule in strategies.items():
        logger.info(f"\n{name.upper()} Strategy:")
        logger.info(f"  Total quantity: {schedule.total_quantity:.2f} lots")
        logger.info(f"  Time horizon: {schedule.time_horizon} minutes")
        logger.info(f"  Expected cost: ${schedule.expected_cost:.4f}")
        logger.info(f"  Expected variance: {schedule.expected_variance:.6f}")
        logger.info(f"  Trajectory (first 5): {schedule.trajectory[:5]}")
    
    # Calculate savings
    optimal_cost = strategies['optimal'].expected_cost
    twap_cost = strategies['twap'].expected_cost
    savings = ((twap_cost - optimal_cost) / twap_cost) * 100
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Optimal vs TWAP savings: {savings:.2f}%")
    logger.info(f"{'='*60}")
