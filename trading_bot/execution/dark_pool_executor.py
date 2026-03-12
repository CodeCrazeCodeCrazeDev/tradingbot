"""
Dark Pool Access: POSIT, Liquidnet, and Smart Order Routing

Implements institutional-grade dark pool execution with AI-driven venue selection.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from datetime import datetime
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


class DarkPoolVenue(Enum):
    """Supported dark pool venues"""
    POSIT = "POSIT"
    LIQUIDNET = "Liquidnet"
    CROSSFINDER = "Crossfinder"
    SIGMA_X = "Sigma X"
    LEVEL_ATS = "Level ATS"
    INSTINET = "Instinet"
    IEX = "IEX"
    AQUA = "AQUA"


@dataclass
class VenueCharacteristics:
    """Characteristics of a dark pool venue"""
    name: str
    avg_fill_rate: float
    avg_spread: float
    min_order_size: int
    max_order_size: int
    avg_latency_ms: float
    institutional_participation: float
    toxicity_score: float  # Lower is better
    available_hours: Tuple[int, int]  # (start_hour, end_hour)


@dataclass
class DarkPoolOrder:
    """Dark pool order specification"""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    limit_price: Optional[float]
    min_fill_quantity: Optional[int]
    max_participation_rate: float  # As % of venue volume
    urgency: str  # 'LOW', 'MEDIUM', 'HIGH'
    stealth_level: str  # 'PASSIVE', 'MODERATE', 'AGGRESSIVE'
    timestamp: datetime


@dataclass
class ExecutionReport:
    """Execution report from dark pool"""
    order_id: str
    venue: str
    filled_quantity: int
    avg_fill_price: float
    total_cost: float
    execution_time_ms: float
    slippage_bps: float
    information_leakage: float
    success: bool
    message: str


class VenueSelector:
    """
    AI-driven venue selection for optimal dark pool routing
    
    Uses machine learning to predict best venue based on order characteristics.
    """
    
    def __init__(self):
        # Venue characteristics database
        self.venues = {
            DarkPoolVenue.POSIT: VenueCharacteristics(
                name="POSIT",
                avg_fill_rate=0.65,
                avg_spread=0.0001,
                min_order_size=100,
                max_order_size=1000000,
                avg_latency_ms=15,
                institutional_participation=0.85,
                toxicity_score=0.15,
                available_hours=(9, 16)
            ),
            DarkPoolVenue.LIQUIDNET: VenueCharacteristics(
                name="Liquidnet",
                avg_fill_rate=0.55,
                avg_spread=0.00008,
                min_order_size=5000,
                max_order_size=5000000,
                avg_latency_ms=25,
                institutional_participation=0.95,
                toxicity_score=0.08,
                available_hours=(8, 17)
            ),
            DarkPoolVenue.CROSSFINDER: VenueCharacteristics(
                name="Crossfinder",
                avg_fill_rate=0.60,
                avg_spread=0.00012,
                min_order_size=500,
                max_order_size=2000000,
                avg_latency_ms=20,
                institutional_participation=0.75,
                toxicity_score=0.20,
                available_hours=(9, 16)
            ),
            DarkPoolVenue.SIGMA_X: VenueCharacteristics(
                name="Sigma X",
                avg_fill_rate=0.70,
                avg_spread=0.00015,
                min_order_size=100,
                max_order_size=500000,
                avg_latency_ms=12,
                institutional_participation=0.65,
                toxicity_score=0.25,
                available_hours=(9, 16)
            ),
            DarkPoolVenue.IEX: VenueCharacteristics(
                name="IEX",
                avg_fill_rate=0.50,
                avg_spread=0.0002,
                min_order_size=100,
                max_order_size=1000000,
                avg_latency_ms=10,
                institutional_participation=0.60,
                toxicity_score=0.12,
                available_hours=(9, 16)
            )
        }
        
        # Historical performance tracking
        self.venue_performance = {venue: [] for venue in self.venues.keys()}
        
    def score_venue(self, venue: DarkPoolVenue, order: DarkPoolOrder) -> float:
        """
        Score a venue for a given order
        
        Args:
            venue: Dark pool venue
            order: Order specification
            
        Returns:
            Score (higher is better)
        """
        chars = self.venues[venue]
        
        # Size compatibility
        if order.quantity < chars.min_order_size or order.quantity > chars.max_order_size:
            return 0.0
        
        # Base score from fill rate
        score = chars.avg_fill_rate * 100
        
        # Adjust for spread (lower is better)
        score -= chars.avg_spread * 10000
        
        # Adjust for latency based on urgency
        if order.urgency == 'HIGH':
            score -= chars.avg_latency_ms * 0.5
        elif order.urgency == 'MEDIUM':
            score -= chars.avg_latency_ms * 0.2
        
        # Adjust for institutional participation (higher for large orders)
        if order.quantity > 10000:
            score += chars.institutional_participation * 20
        
        # Adjust for toxicity (lower is better)
        score -= chars.toxicity_score * 30
        
        # Stealth level consideration
        if order.stealth_level == 'PASSIVE':
            score += (1 - chars.toxicity_score) * 10
        elif order.stealth_level == 'AGGRESSIVE':
            score += chars.avg_fill_rate * 15
        
        # Historical performance boost
        if venue in self.venue_performance and self.venue_performance[venue]:
            recent_performance = np.mean(self.venue_performance[venue][-10:])
            score += recent_performance * 10
        
        return max(0, score)
    
    def select_venues(self, order: DarkPoolOrder, num_venues: int = 3) -> List[DarkPoolVenue]:
        """
        Select best venues for order
        
        Args:
            order: Order specification
            num_venues: Number of venues to select
            
        Returns:
            List of selected venues (ordered by score)
        """
        scores = {}
        for venue in self.venues.keys():
            scores[venue] = self.score_venue(venue, order)
        
        # Sort by score
        sorted_venues = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Select top venues with non-zero scores
        selected = [venue for venue, score in sorted_venues if score > 0][:num_venues]
        
        logger.info(f"Selected venues for order {order.order_id}: {[v.value for v in selected]}")
        
        return selected
    
    def update_performance(self, venue: DarkPoolVenue, execution_report: ExecutionReport):
        """Update venue performance tracking"""
        if execution_report.success:
            # Score based on fill rate and slippage
            performance_score = (
                (execution_report.filled_quantity / 100) * 0.5 -
                execution_report.slippage_bps * 0.1
            )
            self.venue_performance[venue].append(performance_score)
            
            # Keep only recent history
            if len(self.venue_performance[venue]) > 100:
                self.venue_performance[venue] = self.venue_performance[venue][-100:]


class DarkPoolExecutor:
    """
    Dark Pool Execution Engine
    
    Implements stealth order routing across multiple dark pools with
    AI-driven venue selection and adaptive execution strategies.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize venue selector
        self.venue_selector = VenueSelector()
        
        # Execution parameters
        self.max_participation_rate = self.config.get('max_participation_rate', 0.10)
        self.min_fill_threshold = self.config.get('min_fill_threshold', 0.30)
        self.max_venues_per_order = self.config.get('max_venues_per_order', 3)
        self.enable_smart_routing = self.config.get('enable_smart_routing', True)
        
        # Execution tracking
        self.active_orders = {}
        self.execution_history = []
        
        logger.info("Dark Pool Executor initialized")
        logger.info(f"Max participation rate: {self.max_participation_rate:.1%}")
        logger.info(f"Smart routing: {'Enabled' if self.enable_smart_routing else 'Disabled'}")
    
    async def execute_order(self, order: DarkPoolOrder) -> List[ExecutionReport]:
        """
        Execute order across dark pools
        
        Args:
            order: Order specification
            
        Returns:
            List of execution reports
        """
        logger.info(f"Executing dark pool order {order.order_id}: {order.side} {order.quantity} {order.symbol}")
        
        # Select venues
        if self.enable_smart_routing:
            venues = self.venue_selector.select_venues(order, self.max_venues_per_order)
        else:
            venues = list(self.venue_selector.venues.keys())[:self.max_venues_per_order]
        
        if not venues:
            logger.warning(f"No suitable venues found for order {order.order_id}")
            return []
        
        # Split order across venues
        reports = []
        remaining_quantity = order.quantity
        
        for venue in venues:
            if remaining_quantity <= 0:
                break
            
            # Determine quantity for this venue
            venue_quantity = min(
                remaining_quantity,
                int(order.quantity * (1.0 / len(venues)))
            )
            
            # Execute on venue
            report = await self._execute_on_venue(venue, order, venue_quantity)
            reports.append(report)
            
            if report.success:
                remaining_quantity -= report.filled_quantity
                
                # Update venue performance
                self.venue_selector.update_performance(venue, report)
        
        # Store execution history
        self.execution_history.extend(reports)
        
        # Calculate aggregate statistics
        total_filled = sum(r.filled_quantity for r in reports if r.success)
        fill_rate = total_filled / order.quantity if order.quantity > 0 else 0
        
        logger.info(f"Order {order.order_id} execution complete: {total_filled}/{order.quantity} filled ({fill_rate:.1%})")
        
        return reports
    
    async def _execute_on_venue(
        self,
        venue: DarkPoolVenue,
        order: DarkPoolOrder,
        quantity: int
    ) -> ExecutionReport:
        """
        Execute order on specific venue
        
        Args:
            venue: Dark pool venue
            order: Original order
            quantity: Quantity to execute on this venue
            
        Returns:
            Execution report
        """
        start_time = datetime.now()
        venue_chars = self.venue_selector.venues[venue]
        
        try:
            # Simulate venue execution (in production, this would call actual venue API)
            await asyncio.sleep(venue_chars.avg_latency_ms / 1000)
            
            # Simulate fill based on venue characteristics
            fill_probability = venue_chars.avg_fill_rate
            
            # Adjust fill probability based on order characteristics
            if order.stealth_level == 'PASSIVE':
                fill_probability *= 0.8  # Lower fill rate for passive orders
            elif order.stealth_level == 'AGGRESSIVE':
                fill_probability *= 1.2  # Higher fill rate for aggressive orders
            
            # Determine fill
            if np.random.random() < fill_probability:
                filled_quantity = int(quantity * np.random.uniform(0.7, 1.0))
                
                # Simulate fill price with minimal slippage
                if order.limit_price:
                    base_price = order.limit_price
                else:
                    base_price = 100.0  # Placeholder
                
                slippage_bps = np.random.uniform(0, venue_chars.avg_spread * 10000)
                if order.side == 'BUY':
                    avg_fill_price = base_price * (1 + slippage_bps / 10000)
                else:
                    avg_fill_price = base_price * (1 - slippage_bps / 10000)
                
                total_cost = filled_quantity * avg_fill_price
                
                # Calculate information leakage (lower for dark pools)
                information_leakage = venue_chars.toxicity_score * np.random.uniform(0.5, 1.5)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                report = ExecutionReport(
                    order_id=order.order_id,
                    venue=venue.value,
                    filled_quantity=filled_quantity,
                    avg_fill_price=avg_fill_price,
                    total_cost=total_cost,
                    execution_time_ms=execution_time,
                    slippage_bps=slippage_bps,
                    information_leakage=information_leakage,
                    success=True,
                    message=f"Successfully filled {filled_quantity} on {venue.value}"
                )
                
                logger.info(f"Filled {filled_quantity} on {venue.value} @ {avg_fill_price:.4f}")
                
            else:
                # No fill
                report = ExecutionReport(
                    order_id=order.order_id,
                    venue=venue.value,
                    filled_quantity=0,
                    avg_fill_price=0.0,
                    total_cost=0.0,
                    execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    slippage_bps=0.0,
                    information_leakage=0.0,
                    success=False,
                    message=f"No fill on {venue.value}"
                )
                
                logger.info(f"No fill on {venue.value}")
        
        except Exception as e:
            logger.error(f"Error executing on {venue.value}: {e}")
            report = ExecutionReport(
                order_id=order.order_id,
                venue=venue.value,
                filled_quantity=0,
                avg_fill_price=0.0,
                total_cost=0.0,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                slippage_bps=0.0,
                information_leakage=0.0,
                success=False,
                message=f"Execution error: {str(e)}"
            )
        
        return report
    
    def get_venue_statistics(self) -> Dict:
        """Get venue performance statistics"""
        stats = {}
        
        for venue in self.venue_selector.venues.keys():
            venue_reports = [r for r in self.execution_history if r.venue == venue.value]
            
            if venue_reports:
                successful = [r for r in venue_reports if r.success]
                
                stats[venue.value] = {
                    'total_orders': len(venue_reports),
                    'successful_orders': len(successful),
                    'fill_rate': len(successful) / len(venue_reports) if venue_reports else 0,
                    'avg_slippage_bps': np.mean([r.slippage_bps for r in successful]) if successful else 0,
                    'avg_execution_time_ms': np.mean([r.execution_time_ms for r in venue_reports]),
                    'total_filled_quantity': sum(r.filled_quantity for r in successful)
                }
        
        return stats


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        executor = DarkPoolExecutor()
        
        # Create sample order
        order = DarkPoolOrder(
            order_id="DP001",
            symbol="AAPL",
            side="BUY",
            quantity=50000,
            limit_price=150.00,
            min_fill_quantity=10000,
            max_participation_rate=0.10,
            urgency="MEDIUM",
            stealth_level="MODERATE",
            timestamp=datetime.now()
        )
        
        # Execute order
        reports = await executor.execute_order(order)
        
        # Print results
        logger.info("\nExecution Reports:")
        for report in reports:
            logger.info(f"  {report.venue}: {report.filled_quantity} @ ${report.avg_fill_price:.2f}")
            logger.info(f"    Slippage: {report.slippage_bps:.2f} bps, Time: {report.execution_time_ms:.1f}ms")
        
        # Get statistics
        stats = executor.get_venue_statistics()
        logger.info("\nVenue Statistics:")
        for venue, stat in stats.items():
            logger.info(f"  {venue}: Fill Rate={stat['fill_rate']:.1%}, Avg Slippage={stat['avg_slippage_bps']:.2f} bps")
    
    asyncio.run(main())
