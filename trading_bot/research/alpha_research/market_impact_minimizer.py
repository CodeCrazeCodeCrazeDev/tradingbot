"""
Market Impact Minimizer
=======================
Advanced order execution to minimize market footprint.

Features:
- Micro-sized child order splitting
- Poisson process timing randomization
- Pseudo-human execution patterns
- Liquidity pocket trading
- Unpredictable interval execution
- Spread-optimized routing

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.special import factorial
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExecutionStyle(Enum):
    """Execution style patterns"""
    AGGRESSIVE = auto()
    PASSIVE = auto()
    NEUTRAL = auto()
    HUMAN_LIKE = auto()
    STEALTH = auto()


class TimingMode(Enum):
    """Order timing modes"""
    POISSON = auto()
    UNIFORM_RANDOM = auto()
    CLUSTERED = auto()
    SPREAD_TRIGGERED = auto()
    LIQUIDITY_TRIGGERED = auto()


@dataclass
class ChildOrder:
    """Individual child order"""
    order_id: str
    parent_id: str
    sequence: int
    
    # Order details
    symbol: str
    side: str
    quantity: float
    price_limit: Optional[float] = None
    
    # Timing
    scheduled_time: datetime = field(default_factory=datetime.now)
    executed_time: Optional[datetime] = None
    
    # Execution
    status: str = "pending"  # pending, sent, filled, cancelled
    fill_price: float = 0.0
    fill_quantity: float = 0.0
    slippage_bps: float = 0.0


@dataclass
class ExecutionPlan:
    """Complete execution plan"""
    plan_id: str
    symbol: str
    side: str
    total_quantity: float
    
    # Strategy
    execution_style: ExecutionStyle = ExecutionStyle.STEALTH
    timing_mode: TimingMode = TimingMode.POISSON
    
    # Parameters
    num_slices: int = 10
    duration_seconds: int = 300
    min_slice_interval_ms: int = 100
    max_slice_interval_ms: int = 5000
    
    # Child orders
    child_orders: List[ChildOrder] = field(default_factory=list)
    
    # Progress
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    total_slippage_bps: float = 0.0
    
    # Constraints
    max_spread_bps: float = 10.0
    min_liquidity: float = 1000.0


@dataclass
class LiquidityPocket:
    """Detected liquidity pocket"""
    price_level: float
    available_size: float
    side: str
    confidence: float
    time_detected: datetime
    expected_duration_ms: int = 1000


class PoissonTimer:
    """Poisson process timer for randomized execution"""
    
    def __init__(self, lambda_rate: float = 1.0):
        """
        Args:
            lambda_rate: Average events per second
        """
        self.lambda_rate = lambda_rate
        self.last_event_time = datetime.now()
        
    def get_next_interval_ms(self) -> int:
        """Get next interval using exponential distribution"""
        # Exponential distribution for inter-arrival times
        interval_seconds = np.random.exponential(1.0 / self.lambda_rate)
        return int(interval_seconds * 1000)
    
    def generate_schedule(
        self,
        num_events: int,
        total_duration_ms: int
    ) -> List[int]:
        """Generate schedule of event times"""
        
        # Adjust lambda to fit duration
        adjusted_lambda = num_events / (total_duration_ms / 1000)
        
        intervals = []
        current_time = 0
        
        for _ in range(num_events):
            interval = int(np.random.exponential(1.0 / adjusted_lambda) * 1000)
            interval = max(50, min(interval, total_duration_ms // num_events * 3))
            current_time += interval
            intervals.append(current_time)
        
        # Normalize to fit within duration
        if intervals and intervals[-1] > 0:
            scale = total_duration_ms / intervals[-1]
            intervals = [int(t * scale * 0.95) for t in intervals]
        
        return intervals


class HumanPatternGenerator:
    """Generate pseudo-human execution patterns"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Human behavior parameters
        self.hesitation_prob = 0.15  # Probability of hesitation
        self.burst_prob = 0.1  # Probability of burst activity
        self.fatigue_factor = 0.02  # Slowdown over time
        
    def generate_human_timing(
        self,
        num_orders: int,
        base_interval_ms: int
    ) -> List[int]:
        """Generate human-like timing pattern"""
        
        timings = []
        current_time = 0
        
        for i in range(num_orders):
            # Base interval with noise
            interval = base_interval_ms * (0.5 + np.random.random())
            
            # Hesitation (longer pause)
            if np.random.random() < self.hesitation_prob:
                interval *= (2 + np.random.random() * 3)
            
            # Burst (quick succession)
            if np.random.random() < self.burst_prob:
                interval *= 0.2
            
            # Fatigue (gradual slowdown)
            fatigue = 1 + self.fatigue_factor * i
            interval *= fatigue
            
            # Add micro-jitter
            jitter = np.random.normal(0, interval * 0.1)
            interval = max(50, interval + jitter)
            
            current_time += int(interval)
            timings.append(current_time)
        
        return timings
    
    def generate_human_sizes(
        self,
        total_quantity: float,
        num_orders: int
    ) -> List[float]:
        """Generate human-like order sizes"""
        
        sizes = []
        remaining = total_quantity
        
        for i in range(num_orders - 1):
            # Humans tend to use round numbers
            avg_size = remaining / (num_orders - i)
            
            # Add variability
            size = avg_size * (0.5 + np.random.random())
            
            # Round to human-friendly numbers
            size = self._round_to_human_number(size)
            
            size = min(size, remaining * 0.5)  # Don't take more than half
            sizes.append(size)
            remaining -= size
        
        sizes.append(remaining)  # Last order gets remainder
        
        # Shuffle to avoid pattern
        random.shuffle(sizes)
        
        return sizes
    
    def _round_to_human_number(self, value: float) -> float:
        """Round to human-friendly number"""
        
        if value < 10:
            return round(value, 1)
        elif value < 100:
            return round(value / 5) * 5
        elif value < 1000:
            return round(value / 10) * 10
        elif value < 10000:
            return round(value / 100) * 100
        else:
            return round(value / 1000) * 1000


class LiquidityPocketDetector:
    """Detect liquidity pockets in order book"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pocket_history: deque = deque(maxlen=100)
        
    def detect_pockets(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        mid_price: float
    ) -> List[LiquidityPocket]:
        """Detect liquidity pockets in order book"""
        
        pockets = []
        
        # Analyze bid side
        bid_pockets = self._find_depth_concentrations(bids, 'bid', mid_price)
        pockets.extend(bid_pockets)
        
        # Analyze ask side
        ask_pockets = self._find_depth_concentrations(asks, 'ask', mid_price)
        pockets.extend(ask_pockets)
        
        # Store in history
        for pocket in pockets:
            self.pocket_history.append(pocket)
        
        return pockets
    
    def _find_depth_concentrations(
        self,
        levels: List[Tuple[float, float]],
        side: str,
        mid_price: float
    ) -> List[LiquidityPocket]:
        """Find concentrations of liquidity"""
        
        if not levels:
            return []
        
        pockets = []
        
        # Calculate average depth
        sizes = [level[1] for level in levels[:10]]
        if not sizes:
            return []
        
        avg_size = np.mean(sizes)
        std_size = np.std(sizes) + 1
        
        # Find levels with above-average liquidity
        for price, size in levels[:10]:
            if size > avg_size + std_size:
                # Calculate confidence based on size and distance from mid
                distance = abs(price - mid_price) / mid_price
                size_score = (size - avg_size) / std_size
                confidence = min(size_score / 3, 1.0) * (1 - distance * 10)
                
                if confidence > 0.3:
                    pockets.append(LiquidityPocket(
                        price_level=price,
                        available_size=size,
                        side=side,
                        confidence=confidence,
                        time_detected=datetime.now(),
                        expected_duration_ms=int(1000 + size / avg_size * 500)
                    ))
        
        return pockets
    
    def get_best_pocket(
        self,
        side: str,
        min_size: float
    ) -> Optional[LiquidityPocket]:
        """Get best liquidity pocket for execution"""
        
        valid_pockets = [
            p for p in self.pocket_history
            if p.side == side and p.available_size >= min_size
            and (datetime.now() - p.time_detected).total_seconds() * 1000 < p.expected_duration_ms
        ]
        
        if not valid_pockets:
            return None
        
        # Sort by confidence
        valid_pockets.sort(key=lambda p: p.confidence, reverse=True)
        
        return valid_pockets[0]


class SpreadMonitor:
    """Monitor spread for optimal execution timing"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.spread_history: deque = deque(maxlen=1000)
        self.tight_spread_threshold = 0.0
        
    def update(self, bid: float, ask: float):
        """Update spread history"""
        
        spread = ask - bid
        spread_bps = (spread / ((bid + ask) / 2)) * 10000
        
        self.spread_history.append({
            'timestamp': datetime.now(),
            'spread': spread,
            'spread_bps': spread_bps,
            'bid': bid,
            'ask': ask
        })
        
        # Update threshold
        if len(self.spread_history) > 50:
            spreads = [s['spread_bps'] for s in self.spread_history]
            self.tight_spread_threshold = np.percentile(spreads, 25)
    
    def is_spread_tight(self) -> bool:
        """Check if current spread is tight"""
        
        if not self.spread_history:
            return False
        
        current = self.spread_history[-1]['spread_bps']
        return current <= self.tight_spread_threshold
    
    def get_spread_percentile(self) -> float:
        """Get current spread percentile"""
        
        if len(self.spread_history) < 10:
            return 0.5
        
        current = self.spread_history[-1]['spread_bps']
        spreads = [s['spread_bps'] for s in self.spread_history]
        
        return stats.percentileofscore(spreads, current) / 100 if SCIPY_AVAILABLE else 0.5
    
    def wait_for_tight_spread(
        self,
        max_wait_ms: int = 5000
    ) -> bool:
        """Wait for spread to tighten"""
        
        # This would be called in async context
        # Returns True if spread became tight
        return self.is_spread_tight()


class OrderSlicer:
    """Slice orders into optimal child orders"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def slice_order(
        self,
        total_quantity: float,
        adv: float,
        volatility: float,
        execution_style: ExecutionStyle
    ) -> Tuple[int, List[float]]:
        """Determine optimal slicing"""
        
        # Calculate participation rate
        participation = total_quantity / adv if adv > 0 else 0.01
        
        # Base number of slices
        if participation < 0.01:
            base_slices = 5
        elif participation < 0.05:
            base_slices = 10
        elif participation < 0.1:
            base_slices = 20
        else:
            base_slices = 50
        
        # Adjust for volatility
        vol_factor = 1 + volatility * 10
        num_slices = int(base_slices * vol_factor)
        
        # Adjust for execution style
        if execution_style == ExecutionStyle.STEALTH:
            num_slices = int(num_slices * 1.5)
        elif execution_style == ExecutionStyle.AGGRESSIVE:
            num_slices = max(3, num_slices // 2)
        
        num_slices = max(3, min(num_slices, 100))
        
        # Generate sizes
        if execution_style == ExecutionStyle.HUMAN_LIKE:
            generator = HumanPatternGenerator()
            sizes = generator.generate_human_sizes(total_quantity, num_slices)
        else:
            # Uniform with noise
            base_size = total_quantity / num_slices
            sizes = [base_size * (0.7 + np.random.random() * 0.6) for _ in range(num_slices)]
            
            # Normalize
            total = sum(sizes)
            sizes = [s * total_quantity / total for s in sizes]
        
        return num_slices, sizes


class MarketImpactMinimizer:
    """
    Complete Market Impact Minimizer.
    
    Features:
    - Micro-sized child order splitting
    - Poisson process timing randomization
    - Pseudo-human execution patterns
    - Liquidity pocket trading
    - Unpredictable interval execution
    - Spread-optimized routing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.poisson_timer = PoissonTimer()
        self.human_generator = HumanPatternGenerator()
        self.pocket_detector = LiquidityPocketDetector()
        self.spread_monitor = SpreadMonitor()
        self.order_slicer = OrderSlicer()
        
        # Active plans
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.completed_plans: List[ExecutionPlan] = []
        
        # Statistics
        self.total_orders_executed = 0
        self.avg_slippage_bps = 0.0
        
        logger.info("MarketImpactMinimizer initialized")
    
    def create_execution_plan(
        self,
        symbol: str,
        side: str,
        quantity: float,
        adv: float,
        volatility: float,
        duration_seconds: int = 300,
        execution_style: ExecutionStyle = ExecutionStyle.STEALTH,
        timing_mode: TimingMode = TimingMode.POISSON
    ) -> ExecutionPlan:
        """Create an execution plan"""
        
        import uuid
        plan_id = str(uuid.uuid4())[:8]
        
        # Determine slicing
        num_slices, sizes = self.order_slicer.slice_order(
            quantity, adv, volatility, execution_style
        )
        
        # Generate timing
        duration_ms = duration_seconds * 1000
        
        if timing_mode == TimingMode.POISSON:
            timings = self.poisson_timer.generate_schedule(num_slices, duration_ms)
        elif timing_mode == TimingMode.UNIFORM_RANDOM:
            timings = sorted([random.randint(0, duration_ms) for _ in range(num_slices)])
        else:  # HUMAN_LIKE or others
            base_interval = duration_ms // num_slices
            timings = self.human_generator.generate_human_timing(num_slices, base_interval)
        
        # Create child orders
        child_orders = []
        start_time = datetime.now()
        
        for i, (size, timing) in enumerate(zip(sizes, timings)):
            child = ChildOrder(
                order_id=f"{plan_id}_{i}",
                parent_id=plan_id,
                sequence=i,
                symbol=symbol,
                side=side,
                quantity=size,
                scheduled_time=start_time + timedelta(milliseconds=timing)
            )
            child_orders.append(child)
        
        # Create plan
        plan = ExecutionPlan(
            plan_id=plan_id,
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            execution_style=execution_style,
            timing_mode=timing_mode,
            num_slices=num_slices,
            duration_seconds=duration_seconds,
            child_orders=child_orders
        )
        
        self.active_plans[plan_id] = plan
        
        logger.info(f"Created execution plan {plan_id}: {num_slices} slices over {duration_seconds}s")
        
        return plan
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        order_book_feed: Any,
        execute_order_func: Any
    ) -> ExecutionPlan:
        """Execute an execution plan"""
        
        logger.info(f"Starting execution of plan {plan.plan_id}")
        
        for child in plan.child_orders:
            # Wait until scheduled time
            wait_time = (child.scheduled_time - datetime.now()).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Check spread
            if plan.execution_style == ExecutionStyle.STEALTH:
                # Wait for tight spread
                spread_wait = 0
                while not self.spread_monitor.is_spread_tight() and spread_wait < 5:
                    await asyncio.sleep(0.1)
                    spread_wait += 0.1
            
            # Check for liquidity pocket
            pocket = self.pocket_detector.get_best_pocket(
                'ask' if child.side == 'buy' else 'bid',
                child.quantity
            )
            
            if pocket:
                child.price_limit = pocket.price_level
            
            # Execute
            try:
                result = await execute_order_func(
                    symbol=child.symbol,
                    side=child.side,
                    quantity=child.quantity,
                    price_limit=child.price_limit
                )
                
                child.status = 'filled'
                child.executed_time = datetime.now()
                child.fill_price = result.get('price', 0)
                child.fill_quantity = result.get('quantity', child.quantity)
                
                # Update plan progress
                plan.filled_quantity += child.fill_quantity
                
            except Exception as e:
                logger.error(f"Child order {child.order_id} failed: {e}")
                child.status = 'failed'
        
        # Calculate final stats
        if plan.filled_quantity > 0:
            filled_orders = [c for c in plan.child_orders if c.status == 'filled']
            if filled_orders:
                total_value = sum(c.fill_price * c.fill_quantity for c in filled_orders)
                plan.avg_fill_price = total_value / plan.filled_quantity
        
        # Move to completed
        del self.active_plans[plan.plan_id]
        self.completed_plans.append(plan)
        
        logger.info(f"Completed plan {plan.plan_id}: filled {plan.filled_quantity}/{plan.total_quantity}")
        
        return plan
    
    def update_order_book(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]]
    ):
        """Update with new order book data"""
        
        if bids and asks:
            mid_price = (bids[0][0] + asks[0][0]) / 2
            self.pocket_detector.detect_pockets(bids, asks, mid_price)
            self.spread_monitor.update(bids[0][0], asks[0][0])
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        
        if not self.completed_plans:
            return {'total_plans': 0}
        
        total_slippage = sum(p.total_slippage_bps for p in self.completed_plans)
        fill_rates = [p.filled_quantity / p.total_quantity for p in self.completed_plans]
        
        return {
            'total_plans': len(self.completed_plans),
            'active_plans': len(self.active_plans),
            'avg_slippage_bps': total_slippage / len(self.completed_plans),
            'avg_fill_rate': np.mean(fill_rates),
            'total_volume': sum(p.filled_quantity for p in self.completed_plans)
        }


# Factory function
def create_impact_minimizer(config: Optional[Dict] = None) -> MarketImpactMinimizer:
    """Create and return a MarketImpactMinimizer instance"""
    return MarketImpactMinimizer(config)
