"""
from pathlib import Path
Market Impact Modeling for Large Orders
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
import pathlib
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class MarketImpactParams:
    """Market impact model parameters"""
    permanent_impact: float  # Permanent price impact coefficient
    temporary_impact: float  # Temporary price impact coefficient
    decay_rate: float        # Decay rate of temporary impact
    volatility: float        # Market volatility
    spread: float            # Bid-ask spread
    adv_percentage: float    # Average daily volume percentage threshold for large orders
    
    @classmethod
    def default(cls, asset_type: str = 'equity'):
        """
        Get default parameters based on asset type
        
        Args:
            asset_type: Type of asset (equity, futures, crypto, forex)
            
        Returns:
            MarketImpactParams with default values
        """
        try:
            if asset_type == 'equity':
                return cls(
                    permanent_impact=0.1,
                    temporary_impact=0.3,
                    decay_rate=0.2,
                    volatility=0.01,
                    spread=0.01,
                    adv_percentage=0.03  # 3% of ADV is considered large
                )
            elif asset_type == 'futures':
                return cls(
                    permanent_impact=0.08,
                    temporary_impact=0.25,
                    decay_rate=0.15,
                    volatility=0.015,
                    spread=0.005,
                    adv_percentage=0.05  # 5% of ADV is considered large
                )
            elif asset_type == 'crypto':
                return cls(
                    permanent_impact=0.15,
                    temporary_impact=0.4,
                    decay_rate=0.3,
                    volatility=0.03,
                    spread=0.001,
                    adv_percentage=0.02  # 2% of ADV is considered large
                )
            elif asset_type == 'forex':
                return cls(
                    permanent_impact=0.05,
                    temporary_impact=0.15,
                    decay_rate=0.1,
                    volatility=0.005,
                    spread=0.0001,
                    adv_percentage=0.1  # 10% of ADV is considered large
                )
            else:
                # Default parameters
                return cls(
                    permanent_impact=0.1,
                    temporary_impact=0.3,
                    decay_rate=0.2,
                    volatility=0.01,
                    spread=0.01,
                    adv_percentage=0.03
                )
        except Exception as e:
            logger.error(f"Error in default: {e}")
            raise


@dataclass
class ExecutionResult:
    """Result of order execution with market impact"""
    order_size: float
    initial_price: float
    executed_price: float
    slippage: float
    slippage_bps: float
    market_impact: float
    market_impact_bps: float
    execution_time: float
    participation_rate: float
    cost_breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'order_size': self.order_size,
            'initial_price': self.initial_price,
            'executed_price': self.executed_price,
            'slippage': self.slippage,
            'slippage_bps': self.slippage_bps,
            'market_impact': self.market_impact,
            'market_impact_bps': self.market_impact_bps,
            'execution_time': self.execution_time,
            'participation_rate': self.participation_rate,
            'cost_breakdown': self.cost_breakdown
        }


class MarketImpactModel:
    """
    Market impact model for large orders
    
    Features:
    - Temporary and permanent price impact
    - Order book dynamics
    - Optimal execution strategies
    - Cost estimation
    - Liquidity analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Asset type
            self.asset_type = self.config.get('asset_type', 'equity')
        
            # Market impact parameters
            self.params = self.config.get('params', MarketImpactParams.default(self.asset_type))
        
            # Market data
            self.market_data = {}
        
            logger.info(f"Market Impact Model initialized for {self.asset_type}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_market_impact(self, symbol: str, order_size: float, 
                             side: str, market_data: Dict[str, Any],
                             participation_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Estimate market impact for a large order
        
        Args:
            symbol: Symbol to trade
            order_size: Order size in base units
            side: Order side ('buy' or 'sell')
            market_data: Market data including price, volume, volatility
            participation_rate: Participation rate (0.0 to 1.0)
            
        Returns:
            Dictionary with market impact estimates
        """
        # Extract market data
        try:
            price = market_data.get('price', 100.0)
            adv = market_data.get('adv', 1000000.0)  # Average daily volume
            volatility = market_data.get('volatility', self.params.volatility)
            spread = market_data.get('spread', self.params.spread)
        
            # Calculate order value
            order_value = order_size * price
        
            # Check if this is a large order
            order_adv_pct = order_size / adv
            is_large_order = order_adv_pct > self.params.adv_percentage
        
            # Default participation rate if not provided
            if participation_rate is None:
                if is_large_order:
                    # Lower participation rate for large orders
                    participation_rate = min(0.2, 5.0 / (order_adv_pct * 100))
                else:
                    participation_rate = 0.3
        
            # Ensure participation rate is within bounds
            participation_rate = max(0.01, min(0.5, participation_rate))
        
            # Estimate execution time (in hours)
            execution_time = order_size / (adv * participation_rate)
        
            # Calculate market impact components
            permanent_impact = self._calculate_permanent_impact(
                order_size, price, adv, volatility, side
            )
        
            temporary_impact = self._calculate_temporary_impact(
                order_size, price, adv, volatility, spread, participation_rate, side
            )
        
            # Total market impact
            total_impact = permanent_impact + temporary_impact
        
            # Calculate slippage
            slippage = total_impact * order_size
            slippage_bps = (total_impact / price) * 10000  # Basis points
        
            # Calculate executed price
            if side == 'buy':
                executed_price = price + total_impact
            else:
                executed_price = price - total_impact
        
            # Cost breakdown
            cost_breakdown = {
                'permanent_impact': permanent_impact * order_size,
                'temporary_impact': temporary_impact * order_size,
                'spread_cost': (spread / 2) * order_size,
                'total_cost': slippage
            }
        
            # Create result
            result = ExecutionResult(
                order_size=order_size,
                initial_price=price,
                executed_price=executed_price,
                slippage=slippage,
                slippage_bps=slippage_bps,
                market_impact=total_impact,
                market_impact_bps=(total_impact / price) * 10000,
                execution_time=execution_time,
                participation_rate=participation_rate,
                cost_breakdown=cost_breakdown
            )
        
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error in estimate_market_impact: {e}")
            raise
    
    def _calculate_permanent_impact(self, order_size: float, price: float, 
                                  adv: float, volatility: float, side: str) -> float:
        """
        Calculate permanent price impact
        
        Args:
            order_size: Order size in base units
            price: Current price
            adv: Average daily volume
            volatility: Market volatility
            side: Order side ('buy' or 'sell')
            
        Returns:
            Permanent price impact per unit
        """
        # Square-root model for permanent impact
        try:
            impact_coefficient = self.params.permanent_impact * volatility
        
            # Calculate impact
            impact = impact_coefficient * price * np.sqrt(order_size / adv)
        
            # Adjust for side
            if side == 'sell':
                impact = -impact
        
            return abs(impact)
        except Exception as e:
            logger.error(f"Error in _calculate_permanent_impact: {e}")
            raise
    
    def _calculate_temporary_impact(self, order_size: float, price: float, 
                                  adv: float, volatility: float, spread: float,
                                  participation_rate: float, side: str) -> float:
        """
        Calculate temporary price impact
        
        Args:
            order_size: Order size in base units
            price: Current price
            adv: Average daily volume
            volatility: Market volatility
            spread: Bid-ask spread
            participation_rate: Participation rate
            side: Order side ('buy' or 'sell')
            
        Returns:
            Temporary price impact per unit
        """
        # Power-law model for temporary impact
        try:
            impact_coefficient = self.params.temporary_impact * volatility
        
            # Calculate impact
            impact = impact_coefficient * price * np.power(order_size / adv, 0.6) * np.power(participation_rate, 0.4)
        
            # Add half spread
            impact += spread / 2
        
            # Adjust for side
            if side == 'sell':
                impact = -impact
        
            return abs(impact)
        except Exception as e:
            logger.error(f"Error in _calculate_temporary_impact: {e}")
            raise
    
    def optimize_execution(self, symbol: str, order_size: float, 
                         side: str, market_data: Dict[str, Any],
                         time_horizon: float = 1.0) -> Dict[str, Any]:
        """
        Optimize execution strategy for a large order
        
        Args:
            symbol: Symbol to trade
            order_size: Order size in base units
            side: Order side ('buy' or 'sell')
            market_data: Market data including price, volume, volatility
            time_horizon: Time horizon for execution in hours
            
        Returns:
            Dictionary with optimized execution strategy
        """
        # Extract market data
        price = market_data.get('price', 100.0)
        adv = market_data.get('adv', 1000000.0)  # Average daily volume
        volatility = market_data.get('volatility', self.params.volatility)
        spread = market_data.get('spread', self.params.spread)
        
        # Calculate trading volume during time horizon
        trading_volume = adv * (time_horizon / 24.0)
        
        # Define objective function for optimization
        def objective(x):
            # x is the vector of participation rates
            
            # Ensure participation rates are valid
            try:
                x = np.clip(x, 0.01, 0.5)
            
                # Number of chunks
                n = len(x)
            
                # Size of each chunk
                chunk_sizes = np.ones(n) * (order_size / n)
            
                # Calculate execution time for each chunk
                execution_times = chunk_sizes / (adv * x)
            
                # Calculate market impact for each chunk
                impacts = []
                for i in range(n):
                    perm_impact = self._calculate_permanent_impact(
                        chunk_sizes[i], price, adv, volatility, side
                    )
                
                    temp_impact = self._calculate_temporary_impact(
                        chunk_sizes[i], price, adv, volatility, spread, x[i], side
                    )
                
                    impacts.append(perm_impact + temp_impact)
            
                # Calculate total cost
                total_cost = sum(impacts[i] * chunk_sizes[i] for i in range(n))
            
                # Add penalty for exceeding time horizon
                if sum(execution_times) > time_horizon:
                    total_cost += 1000000 * (sum(execution_times) - time_horizon)
            
                return total_cost
            except Exception as e:
                logger.error(f"Error in objective: {e}")
                raise
        
        # Initial guess: uniform participation rate
        n_chunks = 5  # Number of chunks to split the order
        initial_guess = np.ones(n_chunks) * 0.2
        
        # Constraints: sum of chunk sizes equals order size
        constraints = []
        
        # Bounds: participation rate between 1% and 50%
        bounds = [(0.01, 0.5) for _ in range(n_chunks)]
        
        # Run optimization
        result = minimize(
            objective,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        # Extract optimized participation rates
        participation_rates = np.clip(result.x, 0.01, 0.5)
        
        # Calculate chunk sizes
        chunk_sizes = np.ones(n_chunks) * (order_size / n_chunks)
        
        # Calculate execution times
        execution_times = chunk_sizes / (adv * participation_rates)
        
        # Calculate impacts
        impacts = []
        executed_prices = []
        
        for i in range(n_chunks):
            perm_impact = self._calculate_permanent_impact(
                chunk_sizes[i], price, adv, volatility, side
            )
            
            temp_impact = self._calculate_temporary_impact(
                chunk_sizes[i], price, adv, volatility, spread, participation_rates[i], side
            )
            
            total_impact = perm_impact + temp_impact
            impacts.append(total_impact)
            
            if side == 'buy':
                executed_prices.append(price + total_impact)
            else:
                executed_prices.append(price - total_impact)
        
        # Calculate average executed price
        avg_executed_price = sum(executed_prices[i] * chunk_sizes[i] for i in range(n_chunks)) / order_size
        
        # Calculate slippage
        slippage = (avg_executed_price - price) * order_size if side == 'buy' else (price - avg_executed_price) * order_size
        slippage_bps = abs((avg_executed_price - price) / price) * 10000
        
        # Create execution schedule
        execution_schedule = []
        current_time = 0.0
        
        for i in range(n_chunks):
            execution_schedule.append({
                'chunk': i + 1,
                'size': float(chunk_sizes[i]),
                'participation_rate': float(participation_rates[i]),
                'execution_time': float(execution_times[i]),
                'start_time': float(current_time),
                'end_time': float(current_time + execution_times[i]),
                'impact': float(impacts[i]),
                'executed_price': float(executed_prices[i])
            })
            
            current_time += execution_times[i]
        
        # Create result
        result = {
            'symbol': symbol,
            'order_size': order_size,
            'side': side,
            'initial_price': price,
            'avg_executed_price': float(avg_executed_price),
            'slippage': float(slippage),
            'slippage_bps': float(slippage_bps),
            'total_execution_time': float(sum(execution_times)),
            'execution_schedule': execution_schedule
        }
        
        return result
    
    def simulate_market_impact(self, symbol: str, order_size: float, 
                             side: str, market_data: Dict[str, Any],
                             num_simulations: int = 100) -> Dict[str, Any]:
        """
        Simulate market impact with Monte Carlo simulation
        
        Args:
            symbol: Symbol to trade
            order_size: Order size in base units
            side: Order side ('buy' or 'sell')
            market_data: Market data including price, volume, volatility
            num_simulations: Number of Monte Carlo simulations
            
        Returns:
            Dictionary with simulation results
        """
        # Extract market data
        try:
            price = market_data.get('price', 100.0)
            adv = market_data.get('adv', 1000000.0)  # Average daily volume
            volatility = market_data.get('volatility', self.params.volatility)
            spread = market_data.get('spread', self.params.spread)
        
            # Optimize execution
            optimized = self.optimize_execution(symbol, order_size, side, market_data)
        
            # Extract execution schedule
            schedule = optimized['execution_schedule']
        
            # Run simulations
            simulation_results = []
        
            for _ in range(num_simulations):
                # Simulate price path
                price_path = [price]
                current_price = price
            
                for chunk in schedule:
                    # Random price movement due to market volatility
                    price_change = np.random.normal(0, volatility * np.sqrt(chunk['execution_time'])) * current_price
                
                    # Add market impact
                    if side == 'buy':
                        price_change += chunk['impact']
                    else:
                        price_change -= chunk['impact']
                
                    # Update price
                    current_price += price_change
                    price_path.append(current_price)
            
                # Calculate executed price
                executed_prices = []
            
                for i, chunk in enumerate(schedule):
                    # Use average of start and end price for execution
                    chunk_price = (price_path[i] + price_path[i + 1]) / 2
                    executed_prices.append(chunk_price)
            
                # Calculate average executed price
                avg_executed_price = sum(executed_prices[i] * schedule[i]['size'] for i in range(len(schedule))) / order_size
            
                # Calculate slippage
                slippage = (avg_executed_price - price) * order_size if side == 'buy' else (price - avg_executed_price) * order_size
                slippage_bps = abs((avg_executed_price - price) / price) * 10000
            
                # Store result
                simulation_results.append({
                    'avg_executed_price': avg_executed_price,
                    'slippage': slippage,
                    'slippage_bps': slippage_bps,
                    'price_path': price_path
                })
        
            # Calculate statistics
            slippages = [result['slippage'] for result in simulation_results]
            slippage_bps_values = [result['slippage_bps'] for result in simulation_results]
        
            stats = {
                'mean_slippage': float(np.mean(slippages)),
                'median_slippage': float(np.median(slippages)),
                'std_slippage': float(np.std(slippages)),
                'min_slippage': float(np.min(slippages)),
                'max_slippage': float(np.max(slippages)),
                'mean_slippage_bps': float(np.mean(slippage_bps_values)),
                'median_slippage_bps': float(np.median(slippage_bps_values)),
                'std_slippage_bps': float(np.std(slippage_bps_values)),
                'var_95': float(np.percentile(slippages, 95)),
                'var_99': float(np.percentile(slippages, 99)),
                'cvar_95': float(np.mean([s for s in slippages if s > np.percentile(slippages, 95)]))
            }
        
            # Create result
            result = {
                'symbol': symbol,
                'order_size': order_size,
                'side': side,
                'initial_price': price,
                'optimized_execution': optimized,
                'simulation_stats': stats,
                'num_simulations': num_simulations
            }
        
            return result
        except Exception as e:
            logger.error(f"Error in simulate_market_impact: {e}")
            raise
    
    def estimate_optimal_size(self, symbol: str, max_impact_bps: float, 
                            side: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate optimal order size given maximum acceptable market impact
        
        Args:
            symbol: Symbol to trade
            max_impact_bps: Maximum acceptable market impact in basis points
            side: Order side ('buy' or 'sell')
            market_data: Market data including price, volume, volatility
            
        Returns:
            Dictionary with optimal order size and impact estimates
        """
        # Extract market data
        price = market_data.get('price', 100.0)
        adv = market_data.get('adv', 1000000.0)  # Average daily volume
        volatility = market_data.get('volatility', self.params.volatility)
        spread = market_data.get('spread', self.params.spread)
        
        # Convert max impact from basis points to absolute
        max_impact = (max_impact_bps / 10000) * price
        
        # Define objective function for optimization
        def objective(order_size):
            # Calculate market impact
            try:
                perm_impact = self._calculate_permanent_impact(
                    order_size, price, adv, volatility, side
                )
            
                temp_impact = self._calculate_temporary_impact(
                    order_size, price, adv, volatility, spread, 0.2, side
                )
            
                total_impact = perm_impact + temp_impact
            
                # Return difference from max impact
                return abs(total_impact - max_impact)
            except Exception as e:
                logger.error(f"Error in objective: {e}")
                raise
        
        # Initial guess
        initial_guess = adv * 0.01
        
        # Run optimization
        result = minimize(
            objective,
            initial_guess,
            method='BFGS'
        )
        
        # Extract optimal order size
        optimal_size = max(0, result.x[0])
        
        # Calculate market impact for optimal size
        impact_result = self.estimate_market_impact(
            symbol, optimal_size, side, market_data
        )
        
        # Create result
        result = {
            'symbol': symbol,
            'max_impact_bps': max_impact_bps,
            'side': side,
            'optimal_size': float(optimal_size),
            'optimal_size_pct_adv': float(optimal_size / adv),
            'estimated_impact': impact_result
        }
        
        return result
    
    def plot_market_impact(self, symbol: str, market_data: Dict[str, Any], 
                         max_size_pct: float = 0.2, side: str = 'buy',
                         save_path: Optional[str] = None):
        """
        Plot market impact curve
        
        Args:
            symbol: Symbol to analyze
            market_data: Market data including price, volume, volatility
            max_size_pct: Maximum order size as percentage of ADV
            side: Order side ('buy' or 'sell')
            save_path: Path to save plot
        """
        # Extract market data
        try:
            price = market_data.get('price', 100.0)
            adv = market_data.get('adv', 1000000.0)  # Average daily volume
        
            # Generate order sizes
            sizes = np.linspace(0, adv * max_size_pct, 50)
        
            # Calculate market impact for each size
            impacts = []
        
            for size in sizes:
                result = self.estimate_market_impact(symbol, size, side, market_data)
                impacts.append(result['market_impact_bps'])
        
            # Create plot
            plt.figure(figsize=(12, 8))
        
            # Plot market impact curve
            plt.plot(sizes / adv, impacts, 'b-', linewidth=2)
        
            # Add reference lines
            plt.axhline(y=10, color='r', linestyle='--', alpha=0.7, label='10 bps')
            plt.axhline(y=20, color='orange', linestyle='--', alpha=0.7, label='20 bps')
            plt.axhline(y=50, color='purple', linestyle='--', alpha=0.7, label='50 bps')
        
            # Add labels and title
            plt.xlabel('Order Size (% of ADV)')
            plt.ylabel('Market Impact (bps)')
            plt.title(f'Market Impact Curve for {symbol} ({side.capitalize()} Orders)')
            plt.grid(True, alpha=0.3)
            plt.legend()
        
            # Format x-axis as percentage
            plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1%}'))
        
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Market impact plot saved to {save_path}")
            else:
                plt.show()
        
            plt.close()
        except Exception as e:
            logger.error(f"Error in plot_market_impact: {e}")
            raise
    
    def plot_optimal_execution(self, optimized_result: Dict[str, Any], 
                             save_path: Optional[str] = None):
        """
        Plot optimal execution schedule
        
        Args:
            optimized_result: Result from optimize_execution
            save_path: Path to save plot
        """
        # Extract data
        try:
            symbol = optimized_result['symbol']
            order_size = optimized_result['order_size']
            side = optimized_result['side']
            schedule = optimized_result['execution_schedule']
        
            # Extract schedule data
            chunks = [chunk['chunk'] for chunk in schedule]
            sizes = [chunk['size'] for chunk in schedule]
            rates = [chunk['participation_rate'] for chunk in schedule]
            times = [chunk['execution_time'] for chunk in schedule]
            prices = [chunk['executed_price'] for chunk in schedule]
        
            # Create figure with subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
            # Plot chunk sizes
            ax1.bar(chunks, sizes, color='blue', alpha=0.7)
            ax1.set_ylabel('Chunk Size')
            ax1.set_title(f'Optimal Execution Schedule for {symbol} ({side.capitalize()}, {order_size:,.0f} units)')
            ax1.grid(True, alpha=0.3)
        
            # Plot participation rates
            ax2.bar(chunks, rates, color='green', alpha=0.7)
            ax2.set_ylabel('Participation Rate')
            ax2.grid(True, alpha=0.3)
        
            # Plot execution times
            ax3.bar(chunks, times, color='orange', alpha=0.7)
            ax3.set_xlabel('Execution Chunk')
            ax3.set_ylabel('Execution Time (hours)')
            ax3.grid(True, alpha=0.3)
        
            plt.tight_layout()
        
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Execution schedule plot saved to {save_path}")
            else:
                plt.show()
        
            plt.close()
        except Exception as e:
            logger.error(f"Error in plot_optimal_execution: {e}")
            raise
    
    def calculate_impact(self, order_size: float, market_data: dict) -> float:
        """
        Calculate market impact of an order
        
        Args:
            order_size: Size of the order
            market_data: Market data dictionary with avg_volume, volatility, etc.
            
        Returns:
            Estimated market impact in basis points
        """
        # Simple linear impact model
        try:
            avg_volume = market_data.get('avg_volume', 1000000)
            participation_rate = abs(order_size) / avg_volume if avg_volume > 0 else 0
        
            # Impact increases with square root of participation rate
            # Base impact of 10 bps per 1% participation
            impact_bps = 10 * (participation_rate ** 0.5) * 10000
        
            # Adjust for volatility if available
            volatility = market_data.get('volatility', 0.01)
            impact_bps *= (1 + volatility * 10)
        
            return min(impact_bps, 100)  # Cap at 100 bps
        except Exception as e:
            logger.error(f"Error in calculate_impact: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create market impact model
    model = MarketImpactModel()
    
    # Example market data
    market_data = {
        'price': 100.0,
        'adv': 1000000,  # 1 million shares
        'volatility': 0.02,
        'spread': 0.01
    }
    
    # Estimate market impact
    impact = model.estimate_market_impact('AAPL', 50000, 'buy', market_data)
    logger.info(f"Market Impact: {impact['market_impact_bps']:.2f} bps")
    
    # Optimize execution
    optimized = model.optimize_execution('AAPL', 50000, 'buy', market_data)
    logger.info(f"Optimized Execution: {optimized['slippage_bps']:.2f} bps slippage")
    
    # Simulate market impact
    simulation = model.simulate_market_impact('AAPL', 50000, 'buy', market_data, 100)
    logger.info(f"Simulation: Mean Slippage = {simulation['simulation_stats']['mean_slippage_bps']:.2f} bps")
    
    # Estimate optimal size
    optimal = model.estimate_optimal_size('AAPL', 20.0, 'buy', market_data)
    logger.info(f"Optimal Size: {optimal['optimal_size']:,.0f} units ({optimal['optimal_size_pct_adv']:.2%} of ADV)")
    
    # Plot market impact
    model.plot_market_impact('AAPL', market_data)
    
    # Plot optimal execution
    model.plot_optimal_execution(optimized)
