"""
Advanced Execution Algorithms - Production-Ready Implementation

Complete implementation of institutional-grade execution algorithms:
- TWAP (Time-Weighted Average Price)
- VWAP (Volume-Weighted Average Price)
- Iceberg Orders
- Smart Order Routing
- Implementation Shortfall
- POV (Percentage of Volume)
- Adaptive Execution
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ExecutionAlgorithm(Enum):
    """Execution algorithm types"""
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    POV = "pov"
    IMPLEMENTATION_SHORTFALL = "is"
    ADAPTIVE = "adaptive"
    SNIPER = "sniper"
    GUERRILLA = "guerrilla"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class SliceOrder:
    """Individual slice of a parent order"""
    slice_id: str
    parent_id: str
    symbol: str
    side: OrderSide
    quantity: float
    target_price: Optional[float]
    scheduled_time: datetime
    executed: bool = False
    executed_quantity: float = 0.0
    executed_price: float = 0.0
    executed_time: Optional[datetime] = None
    order_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'slice_id': self.slice_id,
            'parent_id': self.parent_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'target_price': self.target_price,
            'scheduled_time': self.scheduled_time.isoformat(),
            'executed': self.executed,
            'executed_quantity': self.executed_quantity,
            'executed_price': self.executed_price
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan for an order"""
    plan_id: str
    symbol: str
    side: OrderSide
    total_quantity: float
    algorithm: ExecutionAlgorithm
    start_time: datetime
    end_time: datetime
    slices: List[SliceOrder] = field(default_factory=list)
    
    # Execution state
    executed_quantity: float = 0.0
    average_price: float = 0.0
    status: str = "pending"
    
    # Metrics
    arrival_price: float = 0.0
    slippage_bps: float = 0.0
    participation_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'plan_id': self.plan_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'total_quantity': self.total_quantity,
            'algorithm': self.algorithm.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'executed_quantity': self.executed_quantity,
            'average_price': self.average_price,
            'status': self.status,
            'slippage_bps': self.slippage_bps,
            'slices': [s.to_dict() for s in self.slices]
        }


class TWAPExecutor:
    """
    Time-Weighted Average Price execution.
    
    Splits order into equal slices executed at regular intervals.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_slice_size = self.config.get('min_slice_size', 1000)
        self.randomize_timing = self.config.get('randomize_timing', True)
        self.timing_variance = self.config.get('timing_variance', 0.2)  # 20% variance
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        duration_minutes: int,
        num_slices: Optional[int] = None,
        start_time: Optional[datetime] = None
    ) -> ExecutionPlan:
        """Create TWAP execution plan"""
        start_time = start_time or datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Calculate number of slices
        if num_slices is None:
            num_slices = max(1, int(quantity / self.min_slice_size))
            num_slices = min(num_slices, duration_minutes)  # At most 1 per minute
        
        slice_quantity = quantity / num_slices
        interval = timedelta(minutes=duration_minutes / num_slices)
        
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.TWAP,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create slices
        for i in range(num_slices):
            scheduled_time = start_time + interval * i
            
            # Add randomization
            if self.randomize_timing and i > 0:
                variance_seconds = interval.total_seconds() * self.timing_variance
                offset = random.uniform(-variance_seconds, variance_seconds)
                scheduled_time += timedelta(seconds=offset)
            
            slice_order = SliceOrder(
                slice_id=f"{plan.plan_id}_{i}",
                parent_id=plan.plan_id,
                symbol=symbol,
                side=side,
                quantity=slice_quantity,
                target_price=None,
                scheduled_time=scheduled_time
            )
            plan.slices.append(slice_order)
        
        logger.info(f"TWAP plan created: {num_slices} slices over {duration_minutes} minutes")
        return plan


class VWAPExecutor:
    """
    Volume-Weighted Average Price execution.
    
    Executes order proportionally to historical volume profile.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_slice_size = self.config.get('min_slice_size', 1000)
        
        # Default intraday volume profile (hourly buckets)
        self.default_volume_profile = [
            0.08, 0.07, 0.06, 0.05, 0.05, 0.05,  # 00:00 - 05:00
            0.06, 0.08, 0.10, 0.08, 0.06, 0.05,  # 06:00 - 11:00
            0.04, 0.04, 0.05, 0.06, 0.07, 0.08,  # 12:00 - 17:00
            0.06, 0.05, 0.04, 0.03, 0.02, 0.02   # 18:00 - 23:00
        ]
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        duration_minutes: int,
        volume_profile: Optional[List[float]] = None,
        start_time: Optional[datetime] = None
    ) -> ExecutionPlan:
        """Create VWAP execution plan"""
        start_time = start_time or datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Use provided or default volume profile
        profile = volume_profile or self.default_volume_profile
        
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.VWAP,
            start_time=start_time,
            end_time=end_time
        )
        
        # Calculate slices based on volume profile
        num_intervals = min(duration_minutes, 60)  # Max 60 slices
        interval = timedelta(minutes=duration_minutes / num_intervals)
        
        # Get relevant portion of volume profile
        start_hour = start_time.hour
        profile_weights = []
        
        for i in range(num_intervals):
            current_time = start_time + interval * i
            hour = current_time.hour
            profile_weights.append(profile[hour % 24])
        
        # Normalize weights
        total_weight = sum(profile_weights)
        normalized_weights = [w / total_weight for w in profile_weights]
        
        # Create slices
        for i, weight in enumerate(normalized_weights):
            slice_quantity = quantity * weight
            
            if slice_quantity < self.min_slice_size:
                continue
            
            scheduled_time = start_time + interval * i
            
            slice_order = SliceOrder(
                slice_id=f"{plan.plan_id}_{i}",
                parent_id=plan.plan_id,
                symbol=symbol,
                side=side,
                quantity=slice_quantity,
                target_price=None,
                scheduled_time=scheduled_time
            )
            plan.slices.append(slice_order)
        
        logger.info(f"VWAP plan created: {len(plan.slices)} slices based on volume profile")
        return plan


class IcebergExecutor:
    """
    Iceberg order execution.
    
    Shows only a portion of the total order to the market.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_display_ratio = self.config.get('display_ratio', 0.1)  # 10% visible
        self.min_display_size = self.config.get('min_display_size', 1000)
        self.randomize_size = self.config.get('randomize_size', True)
        self.size_variance = self.config.get('size_variance', 0.3)  # 30% variance
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        display_quantity: Optional[float] = None,
        limit_price: Optional[float] = None
    ) -> ExecutionPlan:
        """Create iceberg execution plan"""
        # Calculate display quantity
        if display_quantity is None:
            display_quantity = max(
                self.min_display_size,
                quantity * self.default_display_ratio
            )
        
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.ICEBERG,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=24)  # Max duration
        )
        
        # Create slices
        remaining = quantity
        slice_num = 0
        
        while remaining > 0:
            # Calculate slice size with optional randomization
            slice_size = min(display_quantity, remaining)
            
            if self.randomize_size and slice_size == display_quantity:
                variance = display_quantity * self.size_variance
                slice_size = max(
                    self.min_display_size,
                    display_quantity + random.uniform(-variance, variance)
                )
                slice_size = min(slice_size, remaining)
            
            slice_order = SliceOrder(
                slice_id=f"{plan.plan_id}_{slice_num}",
                parent_id=plan.plan_id,
                symbol=symbol,
                side=side,
                quantity=slice_size,
                target_price=limit_price,
                scheduled_time=datetime.now()  # Execute when previous fills
            )
            plan.slices.append(slice_order)
            
            remaining -= slice_size
            slice_num += 1
        
        logger.info(f"Iceberg plan created: {len(plan.slices)} hidden slices, "
                   f"display size: {display_quantity}")
        return plan


class POVExecutor:
    """
    Percentage of Volume execution.
    
    Executes as a percentage of market volume.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_participation_rate = self.config.get('participation_rate', 0.1)  # 10%
        self.max_participation_rate = self.config.get('max_participation_rate', 0.25)  # 25%
        self.volume_check_interval = self.config.get('volume_check_interval', 60)  # seconds
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        participation_rate: Optional[float] = None,
        max_duration_minutes: int = 480  # 8 hours max
    ) -> ExecutionPlan:
        """Create POV execution plan"""
        rate = participation_rate or self.default_participation_rate
        rate = min(rate, self.max_participation_rate)
        
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.POV,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=max_duration_minutes),
            participation_rate=rate
        )
        
        # POV doesn't pre-create slices - they're created dynamically
        # based on observed market volume
        
        logger.info(f"POV plan created: {rate*100}% participation rate")
        return plan
    
    def calculate_slice_size(
        self,
        market_volume: float,
        participation_rate: float,
        remaining_quantity: float
    ) -> float:
        """Calculate next slice size based on market volume"""
        target_size = market_volume * participation_rate
        return min(target_size, remaining_quantity)


class ImplementationShortfallExecutor:
    """
    Implementation Shortfall (Arrival Price) execution.
    
    Minimizes the difference between execution price and arrival price.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.urgency_factor = self.config.get('urgency_factor', 0.5)  # 0-1
        self.risk_aversion = self.config.get('risk_aversion', 0.5)  # 0-1
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        arrival_price: float,
        volatility: float,
        expected_volume: float,
        duration_minutes: int = 60
    ) -> ExecutionPlan:
        """Create Implementation Shortfall execution plan"""
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.IMPLEMENTATION_SHORTFALL,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=duration_minutes),
            arrival_price=arrival_price
        )
        
        # Almgren-Chriss optimal execution
        # Trade-off between market impact and timing risk
        
        # Calculate optimal trajectory
        num_intervals = min(duration_minutes, 30)
        
        if NUMPY_AVAILABLE:
            # Optimal execution uses exponential decay
            decay_rate = self.urgency_factor * 2
            times = np.linspace(0, 1, num_intervals)
            weights = np.exp(-decay_rate * times)
            weights = weights / weights.sum()
        else:
            # Simple linear decay
            weights = [(num_intervals - i) for i in range(num_intervals)]
            total = sum(weights)
            weights = [w / total for w in weights]
        
        interval = timedelta(minutes=duration_minutes / num_intervals)
        
        for i, weight in enumerate(weights):
            slice_quantity = quantity * weight
            scheduled_time = plan.start_time + interval * i
            
            slice_order = SliceOrder(
                slice_id=f"{plan.plan_id}_{i}",
                parent_id=plan.plan_id,
                symbol=symbol,
                side=side,
                quantity=slice_quantity,
                target_price=None,
                scheduled_time=scheduled_time
            )
            plan.slices.append(slice_order)
        
        logger.info(f"IS plan created: {len(plan.slices)} slices, "
                   f"urgency: {self.urgency_factor}")
        return plan


class AdaptiveExecutor:
    """
    Adaptive execution algorithm.
    
    Dynamically adjusts execution based on market conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.aggression_level = self.config.get('aggression_level', 0.5)
        self.spread_threshold = self.config.get('spread_threshold', 0.001)  # 10 bps
        self.volume_threshold = self.config.get('volume_threshold', 0.8)
    
    def create_plan(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        duration_minutes: int = 60
    ) -> ExecutionPlan:
        """Create adaptive execution plan"""
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            algorithm=ExecutionAlgorithm.ADAPTIVE,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=duration_minutes)
        )
        
        # Adaptive doesn't pre-create slices
        # Slices are created dynamically based on market conditions
        
        logger.info(f"Adaptive plan created: aggression {self.aggression_level}")
        return plan
    
    def calculate_next_action(
        self,
        remaining_quantity: float,
        current_spread: float,
        current_volume: float,
        avg_volume: float,
        time_remaining: float
    ) -> Dict[str, Any]:
        """Calculate next execution action based on market conditions"""
        # Spread analysis
        spread_favorable = current_spread < self.spread_threshold
        
        # Volume analysis
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        volume_favorable = volume_ratio > self.volume_threshold
        
        # Time pressure
        time_pressure = 1 - time_remaining
        
        # Calculate aggression
        aggression = self.aggression_level
        
        if spread_favorable:
            aggression += 0.2
        if volume_favorable:
            aggression += 0.1
        
        aggression += time_pressure * 0.3
        aggression = min(1.0, aggression)
        
        # Calculate slice size
        base_size = remaining_quantity * 0.1
        slice_size = base_size * (1 + aggression)
        
        return {
            'action': 'execute',
            'quantity': min(slice_size, remaining_quantity),
            'aggression': aggression,
            'use_limit': not spread_favorable,
            'reason': f"spread_ok={spread_favorable}, volume_ok={volume_favorable}"
        }


class SmartOrderRouter:
    """
    Smart Order Router for multi-venue execution.
    
    Routes orders to optimal venues based on:
    - Best price
    - Liquidity
    - Latency
    - Fees
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.venues: Dict[str, Dict] = {}
        self.venue_stats: Dict[str, Dict] = {}
    
    def register_venue(
        self,
        venue_id: str,
        broker,
        priority: int = 1,
        fee_bps: float = 0.0
    ):
        """Register a trading venue"""
        self.venues[venue_id] = {
            'broker': broker,
            'priority': priority,
            'fee_bps': fee_bps,
            'enabled': True
        }
        self.venue_stats[venue_id] = {
            'orders': 0,
            'fills': 0,
            'avg_latency_ms': 0,
            'avg_slippage_bps': 0
        }
        logger.info(f"Venue registered: {venue_id}")
    
    def get_best_venue(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        quotes: Optional[Dict[str, Dict]] = None
    ) -> Optional[str]:
        """Get best venue for order"""
        if not self.venues:
            return None
        
        best_venue = None
        best_score = float('-inf')
        
        for venue_id, venue in self.venues.items():
            if not venue['enabled']:
                continue
            
            score = 0
            
            # Priority score
            score += venue['priority'] * 10
            
            # Fee score (lower is better)
            score -= venue['fee_bps']
            
            # Quote score
            if quotes and venue_id in quotes:
                quote = quotes[venue_id]
                if side == OrderSide.BUY:
                    # Lower ask is better
                    score -= quote.get('ask', 0) * 1000
                else:
                    # Higher bid is better
                    score += quote.get('bid', 0) * 1000
            
            # Historical performance
            stats = self.venue_stats.get(venue_id, {})
            fill_rate = stats.get('fills', 0) / max(stats.get('orders', 1), 1)
            score += fill_rate * 5
            score -= stats.get('avg_slippage_bps', 0)
            
            if score > best_score:
                best_score = score
                best_venue = venue_id
        
        return best_venue
    
    async def route_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        **kwargs
    ) -> Optional[Dict]:
        """Route order to best venue"""
        venue_id = self.get_best_venue(symbol, side, quantity)
        
        if not venue_id:
            logger.error("No available venue for order")
            return None
        
        venue = self.venues[venue_id]
        broker = venue['broker']
        
        try:
            start_time = time.time()
            
            response = await broker.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Update stats
            stats = self.venue_stats[venue_id]
            stats['orders'] += 1
            if response and response.success:
                stats['fills'] += 1
            
            # Update latency (exponential moving average)
            stats['avg_latency_ms'] = 0.9 * stats['avg_latency_ms'] + 0.1 * latency_ms
            
            return {
                'venue': venue_id,
                'response': response,
                'latency_ms': latency_ms
            }
            
        except Exception as e:
            logger.error(f"Order routing failed on {venue_id}: {e}")
            return None
    
    def get_venue_stats(self) -> Dict[str, Dict]:
        """Get venue statistics"""
        return self.venue_stats


class ExecutionEngine:
    """
    Main execution engine coordinating all algorithms.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize executors
        self.twap = TWAPExecutor(self.config.get('twap', {}))
        self.vwap = VWAPExecutor(self.config.get('vwap', {}))
        self.iceberg = IcebergExecutor(self.config.get('iceberg', {}))
        self.pov = POVExecutor(self.config.get('pov', {}))
        self.is_executor = ImplementationShortfallExecutor(self.config.get('is', {}))
        self.adaptive = AdaptiveExecutor(self.config.get('adaptive', {}))
        self.router = SmartOrderRouter(self.config.get('router', {}))
        
        # Active plans
        self.active_plans: Dict[str, ExecutionPlan] = {}
        
        # Callbacks
        self.on_slice_executed: Optional[Callable] = None
        self.on_plan_completed: Optional[Callable] = None
        
        # Running state
        self._running = False
        self._execution_task: Optional[asyncio.Task] = None
        
        logger.info("ExecutionEngine initialized")
    
    def create_plan(
        self,
        algorithm: ExecutionAlgorithm,
        symbol: str,
        side: OrderSide,
        quantity: float,
        **kwargs
    ) -> ExecutionPlan:
        """Create execution plan using specified algorithm"""
        if algorithm == ExecutionAlgorithm.TWAP:
            plan = self.twap.create_plan(symbol, side, quantity, **kwargs)
        elif algorithm == ExecutionAlgorithm.VWAP:
            plan = self.vwap.create_plan(symbol, side, quantity, **kwargs)
        elif algorithm == ExecutionAlgorithm.ICEBERG:
            plan = self.iceberg.create_plan(symbol, side, quantity, **kwargs)
        elif algorithm == ExecutionAlgorithm.POV:
            plan = self.pov.create_plan(symbol, side, quantity, **kwargs)
        elif algorithm == ExecutionAlgorithm.IMPLEMENTATION_SHORTFALL:
            plan = self.is_executor.create_plan(symbol, side, quantity, **kwargs)
        elif algorithm == ExecutionAlgorithm.ADAPTIVE:
            plan = self.adaptive.create_plan(symbol, side, quantity, **kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.active_plans[plan.plan_id] = plan
        return plan
    
    async def start(self):
        """Start execution engine"""
        self._running = True
        self._execution_task = asyncio.create_task(self._execution_loop())
        logger.info("ExecutionEngine started")
    
    async def stop(self):
        """Stop execution engine"""
        self._running = False
        if self._execution_task:
            self._execution_task.cancel()
        logger.info("ExecutionEngine stopped")
    
    async def _execution_loop(self):
        """Main execution loop"""
        while self._running:
            try:
                now = datetime.now()
                
                for plan_id, plan in list(self.active_plans.items()):
                    if plan.status == "completed":
                        continue
                    
                    # Check for slices to execute
                    for slice_order in plan.slices:
                        if slice_order.executed:
                            continue
                        
                        if slice_order.scheduled_time <= now:
                            await self._execute_slice(plan, slice_order)
                    
                    # Check if plan is complete
                    if all(s.executed for s in plan.slices):
                        plan.status = "completed"
                        
                        if self.on_plan_completed:
                            await self._safe_callback(self.on_plan_completed, plan)
                
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Execution loop error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_slice(self, plan: ExecutionPlan, slice_order: SliceOrder):
        """Execute a single slice"""
        try:
            result = await self.router.route_order(
                symbol=slice_order.symbol,
                side=slice_order.side,
                quantity=slice_order.quantity,
                price=slice_order.target_price
            )
            
            if result and result['response'] and result['response'].success:
                response = result['response']
                
                slice_order.executed = True
                slice_order.executed_quantity = response.filled_quantity
                slice_order.executed_price = response.average_fill_price
                slice_order.executed_time = datetime.now()
                slice_order.order_id = response.order_id
                
                # Update plan totals
                plan.executed_quantity += response.filled_quantity
                
                # Update average price
                if plan.executed_quantity > 0:
                    total_value = (plan.average_price * (plan.executed_quantity - response.filled_quantity) +
                                  response.average_fill_price * response.filled_quantity)
                    plan.average_price = total_value / plan.executed_quantity
                
                # Calculate slippage
                if plan.arrival_price > 0:
                    plan.slippage_bps = abs(plan.average_price - plan.arrival_price) / plan.arrival_price * 10000
                
                logger.info(f"Slice executed: {slice_order.slice_id}, "
                           f"qty: {response.filled_quantity}, price: {response.average_fill_price}")
                
                if self.on_slice_executed:
                    await self._safe_callback(self.on_slice_executed, plan, slice_order)
            else:
                logger.warning(f"Slice execution failed: {slice_order.slice_id}")
                
        except Exception as e:
            logger.error(f"Slice execution error: {e}")
    
    async def _safe_callback(self, callback: Callable, *args):
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"Callback error: {e}")
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID"""
        return self.active_plans.get(plan_id)
    
    def cancel_plan(self, plan_id: str) -> bool:
        """Cancel execution plan"""
        plan = self.active_plans.get(plan_id)
        if plan:
            plan.status = "cancelled"
            return True
        return False
    
    def get_active_plans(self) -> List[ExecutionPlan]:
        """Get all active plans"""
        return [p for p in self.active_plans.values() if p.status not in ["completed", "cancelled"]]


# Export
__all__ = [
    'ExecutionEngine',
    'ExecutionAlgorithm',
    'ExecutionPlan',
    'SliceOrder',
    'TWAPExecutor',
    'VWAPExecutor',
    'IcebergExecutor',
    'POVExecutor',
    'ImplementationShortfallExecutor',
    'AdaptiveExecutor',
    'SmartOrderRouter',
    'OrderSide'
]
