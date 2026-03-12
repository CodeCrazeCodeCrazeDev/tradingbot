"""
Dark Pool Iceberg Order Optimizer

Optimizes large order execution through dark pools using iceberg strategy.
Minimizes market impact and information leakage.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


@dataclass
class IcebergOrder:
    """Iceberg order specification"""
    order_id: str
    symbol: str
    side: str  # BUY or SELL
    total_quantity: int
    display_quantity: int
    min_fill_quantity: int
    max_participation_rate: float
    urgency: str  # LOW, MEDIUM, HIGH
    dark_pool_preference: List[str]
    time_limit: Optional[datetime] = None


@dataclass
class OrderSlice:
    """Individual slice of iceberg order"""
    slice_id: str
    parent_order_id: str
    quantity: int
    venue: str
    price_limit: Optional[float]
    timestamp: datetime
    status: str  # PENDING, FILLED, CANCELLED


class IcebergSlicingAlgorithm:
    """
    Intelligent Iceberg Order Slicing
    
    Determines optimal slice sizes and timing for minimal market impact.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Slicing parameters
        self.min_slice_ratio = self.config.get('min_slice_ratio', 0.05)
        self.max_slice_ratio = self.config.get('max_slice_ratio', 0.20)
        self.randomization_factor = self.config.get('randomization_factor', 0.15)
    
    def calculate_slices(
        self,
        order: IcebergOrder,
        market_volume: float,
        volatility: float
    ) -> List[int]:
        """
        Calculate optimal slice sizes
        
        Args:
            order: Iceberg order
            market_volume: Current market volume
            volatility: Market volatility
            
        Returns:
            List of slice sizes
        """
        total_qty = order.total_quantity
        
        # Base slice size from participation rate
        avg_slice_size = int(market_volume * order.max_participation_rate)
        
        # Adjust for urgency
        urgency_multipliers = {
            'LOW': 0.5,
            'MEDIUM': 1.0,
            'HIGH': 1.5
        }
        multiplier = urgency_multipliers.get(order.urgency, 1.0)
        avg_slice_size = int(avg_slice_size * multiplier)
        
        # Ensure within bounds
        min_size = max(order.min_fill_quantity, int(total_qty * self.min_slice_ratio))
        max_size = int(total_qty * self.max_slice_ratio)
        avg_slice_size = np.clip(avg_slice_size, min_size, max_size)
        
        # Generate slices with randomization
        slices = []
        remaining = total_qty
        
        while remaining > 0:
            # Add randomization to avoid detection
            randomization = np.random.uniform(
                1 - self.randomization_factor,
                1 + self.randomization_factor
            )
            slice_size = int(avg_slice_size * randomization)
            
            # Ensure minimum size
            slice_size = max(min_size, min(slice_size, remaining))
            
            slices.append(slice_size)
            remaining -= slice_size
        
        logger.info(f"Generated {len(slices)} slices for order {order.order_id}")
        
        return slices
    
    def calculate_timing(
        self,
        num_slices: int,
        time_limit: Optional[datetime],
        volatility: float
    ) -> List[float]:
        """
        Calculate optimal timing between slices
        
        Args:
            num_slices: Number of slices
            time_limit: Time limit for order
            volatility: Market volatility
            
        Returns:
            List of delays (in seconds) between slices
        """
        if time_limit:
            total_time = (time_limit - datetime.now()).total_seconds()
            avg_delay = total_time / num_slices
        else:
            # Base delay on volatility (higher vol = longer delays)
            avg_delay = 30 + volatility * 100
        
        # Add randomization
        delays = []
        for _ in range(num_slices - 1):
            randomization = np.random.uniform(0.7, 1.3)
            delay = avg_delay * randomization
            delays.append(delay)
        
        return delays


class DarkPoolRouter:
    """
    Dark Pool Routing Optimizer
    
    Routes order slices to optimal dark pools based on fill probability.
    """
    
    def __init__(self):
        # Dark pool characteristics
        self.dark_pools = {
            'POSIT': {
                'fill_rate': 0.65,
                'avg_size': 50000,
                'latency_ms': 10,
                'fee_bps': 0.5
            },
            'Liquidnet': {
                'fill_rate': 0.70,
                'avg_size': 100000,
                'latency_ms': 15,
                'fee_bps': 0.3
            },
            'Crossfinder': {
                'fill_rate': 0.60,
                'avg_size': 30000,
                'latency_ms': 8,
                'fee_bps': 0.6
            },
            'Sigma_X': {
                'fill_rate': 0.55,
                'avg_size': 40000,
                'latency_ms': 12,
                'fee_bps': 0.5
            },
            'IEX': {
                'fill_rate': 0.50,
                'avg_size': 20000,
                'latency_ms': 5,
                'fee_bps': 0.9
            }
        }
    
    def select_venue(
        self,
        slice_size: int,
        symbol: str,
        preferences: List[str]
    ) -> str:
        """
        Select optimal dark pool for slice
        
        Args:
            slice_size: Size of order slice
            symbol: Trading symbol
            preferences: Preferred dark pools
            
        Returns:
            Selected dark pool name
        """
        # Score each dark pool
        scores = {}
        
        for pool, chars in self.dark_pools.items():
            # Skip if not in preferences
            if preferences and pool not in preferences:
                continue
            
            # Size match score (prefer pools with similar avg size)
            size_ratio = min(slice_size, chars['avg_size']) / max(slice_size, chars['avg_size'])
            size_score = size_ratio
            
            # Fill rate score
            fill_score = chars['fill_rate']
            
            # Cost score (lower is better)
            cost_score = 1 - (chars['fee_bps'] / 10)
            
            # Latency score (lower is better)
            latency_score = 1 - (chars['latency_ms'] / 100)
            
            # Combined score
            total_score = (
                size_score * 0.3 +
                fill_score * 0.4 +
                cost_score * 0.2 +
                latency_score * 0.1
            )
            
            scores[pool] = total_score
        
        # Select best venue
        if scores:
            best_venue = max(scores, key=scores.get)
            logger.debug(f"Selected {best_venue} for slice (score: {scores[best_venue]:.2f})")
            return best_venue
        else:
            # Fallback to first preference or POSIT
            return preferences[0] if preferences else 'POSIT'


class MarketImpactModel:
    """
    Market Impact Estimation
    
    Estimates price impact of order execution.
    """
    
    def estimate_impact(
        self,
        quantity: int,
        avg_daily_volume: float,
        volatility: float,
        spread: float
    ) -> float:
        """
        Estimate market impact in bps
        
        Uses square-root model: Impact ~ sqrt(quantity/volume)
        
        Args:
            quantity: Order quantity
            avg_daily_volume: Average daily volume
            volatility: Daily volatility
            spread: Bid-ask spread
            
        Returns:
            Estimated impact in bps
        """
        # Participation rate
        participation = quantity / avg_daily_volume
        
        # Square-root impact
        temporary_impact = volatility * np.sqrt(participation) * 10000  # bps
        
        # Permanent impact (smaller)
        permanent_impact = temporary_impact * 0.3
        
        # Spread cost
        spread_cost = spread * 10000 / 2  # Half spread in bps
        
        total_impact = temporary_impact + permanent_impact + spread_cost
        
        return total_impact


class IcebergOptimizer:
    """
    Integrated Iceberg Order Optimizer
    
    Combines slicing, routing, and impact minimization.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.slicer = IcebergSlicingAlgorithm(config)
        self.router = DarkPoolRouter()
        self.impact_model = MarketImpactModel()
        
        # Execution tracking
        self.active_orders = {}
        self.completed_slices = []
        
        logger.info("Iceberg Optimizer initialized")
    
    async def execute_iceberg_order(
        self,
        order: IcebergOrder,
        market_data: Dict
    ) -> Dict:
        """
        Execute iceberg order with optimal slicing and routing
        
        Args:
            order: Iceberg order specification
            market_data: Current market data
            
        Returns:
            Execution results
        """
        logger.info(f"Executing iceberg order {order.order_id}: "
                   f"{order.side} {order.total_quantity} {order.symbol}")
        
        # Extract market data
        market_volume = market_data.get('avg_daily_volume', 1000000)
        volatility = market_data.get('volatility', 0.02)
        spread = market_data.get('spread', 0.01)
        
        # Calculate slices
        slice_sizes = self.slicer.calculate_slices(order, market_volume, volatility)
        
        # Calculate timing
        delays = self.slicer.calculate_timing(
            len(slice_sizes),
            order.time_limit,
            volatility
        )
        
        # Estimate total impact
        total_impact = self.impact_model.estimate_impact(
            order.total_quantity,
            market_volume,
            volatility,
            spread
        )
        
        logger.info(f"Order split into {len(slice_sizes)} slices, "
                   f"estimated impact: {total_impact:.2f} bps")
        
        # Execute slices
        filled_quantity = 0
        total_cost = 0
        execution_results = []
        
        for i, slice_size in enumerate(slice_sizes):
            # Select venue
            venue = self.router.select_venue(
                slice_size,
                order.symbol,
                order.dark_pool_preference
            )
            
            # Create slice
            slice_order = OrderSlice(
                slice_id=f"{order.order_id}_S{i+1}",
                parent_order_id=order.order_id,
                quantity=slice_size,
                venue=venue,
                price_limit=None,
                timestamp=datetime.now(),
                status='PENDING'
            )
            
            # Execute slice
            result = await self._execute_slice(slice_order, market_data)
            
            execution_results.append(result)
            
            if result['status'] == 'FILLED':
                filled_quantity += result['filled_quantity']
                total_cost += result['cost']
                slice_order.status = 'FILLED'
            else:
                slice_order.status = 'CANCELLED'
            
            self.completed_slices.append(slice_order)
            
            # Wait before next slice (if not last)
            if i < len(slice_sizes) - 1:
                await asyncio.sleep(delays[i])
        
        # Calculate metrics
        fill_rate = filled_quantity / order.total_quantity
        avg_price = total_cost / filled_quantity if filled_quantity > 0 else 0
        
        result = {
            'order_id': order.order_id,
            'status': 'COMPLETED' if fill_rate > 0.95 else 'PARTIAL',
            'total_quantity': order.total_quantity,
            'filled_quantity': filled_quantity,
            'fill_rate': fill_rate,
            'avg_price': avg_price,
            'total_cost': total_cost,
            'estimated_impact_bps': total_impact,
            'num_slices': len(slice_sizes),
            'execution_results': execution_results
        }
        
        logger.info(f"Iceberg order {order.order_id} completed: "
                   f"Fill rate {fill_rate:.1%}, Avg price ${avg_price:.2f}")
        
        return result
    
    async def _execute_slice(
        self,
        slice_order: OrderSlice,
        market_data: Dict
    ) -> Dict:
        """Execute individual order slice"""
        # Simulate dark pool execution
        await asyncio.sleep(0.05)  # Simulate latency
        
        # Get venue characteristics
        venue_chars = self.router.dark_pools.get(slice_order.venue, {})
        fill_rate = venue_chars.get('fill_rate', 0.5)
        
        # Determine if filled (probabilistic)
        is_filled = np.random.random() < fill_rate
        
        if is_filled:
            # Simulate fill
            mid_price = market_data.get('mid_price', 100.0)
            spread = market_data.get('spread', 0.01)
            
            # Fill at mid price (dark pool advantage)
            fill_price = mid_price + np.random.uniform(-spread/4, spread/4)
            filled_qty = slice_order.quantity
            
            result = {
                'slice_id': slice_order.slice_id,
                'venue': slice_order.venue,
                'status': 'FILLED',
                'filled_quantity': filled_qty,
                'fill_price': fill_price,
                'cost': fill_price * filled_qty,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Slice {slice_order.slice_id} filled on {slice_order.venue}: "
                        f"{filled_qty} @ ${fill_price:.2f}")
        else:
            result = {
                'slice_id': slice_order.slice_id,
                'venue': slice_order.venue,
                'status': 'UNFILLED',
                'filled_quantity': 0,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Slice {slice_order.slice_id} not filled on {slice_order.venue}")
        
        return result


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        optimizer = IcebergOptimizer()
        
        # Create iceberg order
        order = IcebergOrder(
            order_id="ICE_001",
            symbol="AAPL",
            side="BUY",
            total_quantity=100000,
            display_quantity=5000,
            min_fill_quantity=1000,
            max_participation_rate=0.05,
            urgency="MEDIUM",
            dark_pool_preference=['Liquidnet', 'POSIT', 'Crossfinder'],
            time_limit=datetime.now() + timedelta(hours=2)
        )
        
        # Market data
        market_data = {
            'mid_price': 150.0,
            'spread': 0.02,
            'avg_daily_volume': 50000000,
            'volatility': 0.025
        }
        
        print("\n" + "=" * 80)
        logger.info("ICEBERG ORDER OPTIMIZER DEMO")
        logger.info("=" * 80 + "\n")
        
        logger.info(f"Order: {order.side} {order.total_quantity:,} {order.symbol}")
        logger.info(f"Urgency: {order.urgency}")
        logger.info(f"Max Participation: {order.max_participation_rate:.1%}")
        logger.info(f"Preferred Venues: {', '.join(order.dark_pool_preference)}\n")
        
        # Execute
        result = await optimizer.execute_iceberg_order(order, market_data)
        
        logger.info("\nExecution Results:")
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Fill Rate: {result['fill_rate']:.1%}")
        logger.info(f"  Filled: {result['filled_quantity']:,} / {result['total_quantity']:,}")
        logger.info(f"  Avg Price: ${result['avg_price']:.2f}")
        logger.info(f"  Total Cost: ${result['total_cost']:,.2f}")
        logger.info(f"  Estimated Impact: {result['estimated_impact_bps']:.2f} bps")
        logger.info(f"  Number of Slices: {result['num_slices']}")
        
        logger.info("\n" + "=" * 80 + "\n")
    
    asyncio.run(main())
