"""
Enhanced Execution Engine with Smart Order Routing

Advanced execution with:
- Smart order routing across venues
- TWAP/VWAP algorithms
- Real-time liquidity monitoring
- Adaptive execution strategies
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategies"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"
    VWAP = "vwap"
    IMPLEMENTATION_SHORTFALL = "implementation_shortfall"
    ADAPTIVE = "adaptive"


class VenueType(Enum):
    """Trading venue types"""
    PRIMARY_EXCHANGE = "primary"
    DARK_POOL = "dark_pool"
    ATS = "ats"
    ECN = "ecn"
    MAKER_TAKER = "maker_taker"


@dataclass
class Venue:
    """Trading venue"""
    name: str
    venue_type: VenueType
    maker_fee_bps: float
    taker_fee_bps: float
    avg_latency_ms: float
    liquidity_score: float  # 0-1
    rebate_eligible: bool
    min_order_size: float
    max_order_size: float


@dataclass
class OrderSlice:
    """Slice of a parent order"""
    slice_id: str
    size: float
    price: float
    venue: str
    scheduled_time: datetime
    execution_strategy: ExecutionStrategy
    urgency: float  # 0-1


@dataclass
class SmartRoutingDecision:
    """Smart routing decision result"""
    primary_venue: str
    backup_venues: List[str]
    execution_strategy: ExecutionStrategy
    expected_cost_bps: float
    expected_fill_time_ms: float
    market_impact_estimate: float
    routing_reasoning: str


class SmartOrderRouter:
    """
    Intelligent order routing across multiple venues.
    
    Optimizes for:
    - Best execution price
    - Lowest fees (maker vs taker)
    - Market impact minimization
    - Fill probability
    - Latency
    """
    
    def __init__(self):
        self.venues: Dict[str, Venue] = {}
        self.venue_performance: Dict[str, deque] = {}
        self._init_default_venues()
        
    def _init_default_venues(self) -> None:
        """Initialize default venue configurations"""
        
        self.venues = {
            'primary': Venue(
                name='Primary Exchange',
                venue_type=VenueType.PRIMARY_EXCHANGE,
                maker_fee_bps=0.1,
                taker_fee_bps=0.2,
                avg_latency_ms=10,
                liquidity_score=0.9,
                rebate_eligible=True,
                min_order_size=1.0,
                max_order_size=100000.0
            ),
            'dark_pool': Venue(
                name='Dark Pool',
                venue_type=VenueType.DARK_POOL,
                maker_fee_bps=0.0,
                taker_fee_bps=0.3,
                avg_latency_ms=15,
                liquidity_score=0.7,
                rebate_eligible=False,
                min_order_size=100.0,
                max_order_size=50000.0
            ),
            'ats': Venue(
                name='Alternative Trading System',
                venue_type=VenueType.ATS,
                maker_fee_bps=0.05,
                taker_fee_bps=0.15,
                avg_latency_ms=20,
                liquidity_score=0.6,
                rebate_eligible=True,
                min_order_size=10.0,
                max_order_size=25000.0
            )
        }
    
    def route_order(
        self,
        symbol: str,
        size: float,
        side: str,
        urgency: float = 0.5,
        market_conditions: Optional[Dict] = None
    ) -> SmartRoutingDecision:
        """
        Determine optimal routing for an order.
        
        Args:
            symbol: Trading symbol
            size: Order size
            side: 'buy' or 'sell'
            urgency: 0-1, higher = faster execution needed
            market_conditions: Current market data
            
        Returns:
            SmartRoutingDecision with optimal routing
        """
        
        market_conditions = market_conditions or {}
        
        # Score each venue
        venue_scores = {}
        for venue_id, venue in self.venues.items():
            score = self._score_venue(
                venue, size, urgency, market_conditions
            )
            venue_scores[venue_id] = score
        
        # Sort by score
        sorted_venues = sorted(
            venue_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Select primary and backup venues
        primary = sorted_venues[0][0]
        backups = [v[0] for v in sorted_venues[1:3]]
        
        # Determine execution strategy
        strategy = self._select_execution_strategy(
            size, urgency, market_conditions
        )
        
        # Estimate costs and impact
        expected_cost = self._estimate_cost(primary, size, side)
        fill_time = self._estimate_fill_time(primary, size, urgency)
        impact = self._estimate_impact(primary, size, market_conditions)
        
        reasoning = self._generate_routing_reasoning(
            primary, strategy, venue_scores
        )
        
        return SmartRoutingDecision(
            primary_venue=primary,
            backup_venues=backups,
            execution_strategy=strategy,
            expected_cost_bps=expected_cost,
            expected_fill_time_ms=fill_time,
            market_impact_estimate=impact,
            routing_reasoning=reasoning
        )
    
    def _score_venue(
        self,
        venue: Venue,
        size: float,
        urgency: float,
        market_conditions: Dict
    ) -> float:
        """Score a venue for this order"""
        
        scores = []
        
        # Liquidity score (0-1)
        liquidity_score = venue.liquidity_score
        scores.append(liquidity_score * 0.3)
        
        # Fee score (lower fees = higher score)
        # Use taker fees as baseline (conservative)
        fee_score = 1 - (venue.taker_fee_bps / 1.0)  # Normalize
        scores.append(max(0, fee_score) * 0.25)
        
        # Latency score (lower latency = higher score, especially for urgent orders)
        latency_score = 1 - (venue.avg_latency_ms / 100)
        urgency_weight = urgency * 0.25
        scores.append(max(0, latency_score) * urgency_weight)
        
        # Size compatibility
        if venue.min_order_size <= size <= venue.max_order_size:
            size_score = 1.0
        elif size < venue.min_order_size:
            size_score = 0.5  # Too small
        else:
            size_score = 0.3  # Too large, might be split
        scores.append(size_score * 0.2)
        
        return sum(scores)
    
    def _select_execution_strategy(
        self,
        size: float,
        urgency: float,
        market_conditions: Dict
    ) -> ExecutionStrategy:
        """Select optimal execution strategy"""
        
        # Large orders = use TWAP or VWAP
        avg_volume = market_conditions.get('avg_daily_volume', size * 10)
        
        if size > avg_volume * 0.05:  # >5% of ADV
            if urgency > 0.7:
                return ExecutionStrategy.IMPLEMENTATION_SHORTFALL
            else:
                return ExecutionStrategy.VWAP
        
        # Medium orders = TWAP
        if size > avg_volume * 0.01:
            return ExecutionStrategy.TWAP
        
        # Small urgent orders = market
        if urgency > 0.8:
            return ExecutionStrategy.MARKET
        
        # Default = adaptive
        return ExecutionStrategy.ADAPTIVE
    
    def _estimate_cost(
        self,
        venue_id: str,
        size: float,
        side: str
    ) -> float:
        """Estimate execution cost in bps"""
        
        venue = self.venues.get(venue_id)
        if not venue:
            return 20.0  # Default 20bps
        
        # Base taker fee
        cost = venue.taker_fee_bps
        
        # Add spread estimate (conservative)
        cost += 5.0
        
        # Add market impact estimate
        cost += min(10, size / 1000)  # Simplified
        
        return cost
    
    def _estimate_fill_time(
        self,
        venue_id: str,
        size: float,
        urgency: float
    ) -> float:
        """Estimate fill time in milliseconds"""
        
        venue = self.venues.get(venue_id)
        base_latency = venue.avg_latency_ms if venue else 50
        
        # Urgency reduces fill time
        urgency_factor = 1 - (urgency * 0.5)
        
        return base_latency * urgency_factor
    
    def _estimate_impact(
        self,
        venue_id: str,
        size: float,
        market_conditions: Dict
    ) -> float:
        """Estimate market impact"""
        
        # Simplified square root impact model
        avg_volume = market_conditions.get('avg_daily_volume', size * 10)
        participation = size / avg_volume if avg_volume > 0 else 0.01
        
        impact_bps = 10 * (participation ** 0.5) * 100
        
        return impact_bps
    
    def _generate_routing_reasoning(
        self,
        primary: str,
        strategy: ExecutionStrategy,
        venue_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable routing reasoning"""
        
        reasoning = f"Primary venue: {primary} (score: {venue_scores[primary]:.2f}). "
        reasoning += f"Strategy: {strategy.value}. "
        
        # Add why primary was chosen
        venue = self.venues.get(primary)
        if venue:
            reasons = []
            if venue.liquidity_score > 0.8:
                reasons.append("high liquidity")
            if venue.taker_fee_bps < 0.2:
                reasons.append("low fees")
            if venue.avg_latency_ms < 15:
                reasons.append("low latency")
            
            if reasons:
                reasoning += f"Selected for: {', '.join(reasons)}."
        
        return reasoning


class ExecutionAlgorithmEngine:
    """
    Execution algorithms (TWAP, VWAP, etc.)
    """
    
    def __init__(self):
        self.active_orders: Dict[str, List[OrderSlice]] = {}
        self.execution_history: deque = deque(maxlen=1000)
        
    def create_twap_slices(
        self,
        parent_order_id: str,
        total_size: float,
        duration_minutes: int,
        num_slices: int,
        side: str,
        start_time: Optional[datetime] = None
    ) -> List[OrderSlice]:
        """Create TWAP order slices"""
        
        if start_time is None:
            start_time = datetime.utcnow()
        
        slice_size = total_size / num_slices
        interval = duration_minutes / num_slices
        
        slices = []
        for i in range(num_slices):
            slice_time = start_time + timedelta(minutes=interval * i)
            
            slice_order = OrderSlice(
                slice_id=f"{parent_order_id}_slice_{i}",
                size=slice_size,
                price=0.0,  # Market order
                venue='primary',  # Default
                scheduled_time=slice_time,
                execution_strategy=ExecutionStrategy.TWAP,
                urgency=0.3
            )
            slices.append(slice_order)
        
        self.active_orders[parent_order_id] = slices
        return slices
    
    def create_vwap_slices(
        self,
        parent_order_id: str,
        total_size: float,
        duration_minutes: int,
        side: str,
        volume_profile: Optional[Dict[int, float]] = None
    ) -> List[OrderSlice]:
        """Create VWAP order slices based on volume profile"""
        
        # Default volume profile (higher at open and close)
        if volume_profile is None:
            volume_profile = self._get_default_volume_profile(duration_minutes)
        
        # Normalize profile
        total_volume = sum(volume_profile.values())
        
        slices = []
        start_time = datetime.utcnow()
        
        for minute, volume_pct in volume_profile.items():
            slice_size = total_size * (volume_pct / total_volume)
            
            slice_order = OrderSlice(
                slice_id=f"{parent_order_id}_vwap_{minute}",
                size=slice_size,
                price=0.0,
                venue='primary',
                scheduled_time=start_time + timedelta(minutes=minute),
                execution_strategy=ExecutionStrategy.VWAP,
                urgency=0.4
            )
            slices.append(slice_order)
        
        self.active_orders[parent_order_id] = slices
        return slices
    
    def _get_default_volume_profile(self, duration: int) -> Dict[int, float]:
        """Get default intraday volume profile"""
        
        # U-shaped profile: higher at start and end
        profile = {}
        for i in range(duration):
            # Simple U-shape approximation
            if i < duration * 0.2:  # First 20%
                weight = 1.5
            elif i > duration * 0.8:  # Last 20%
                weight = 1.5
            else:
                weight = 0.8
            
            profile[i] = weight
        
        return profile
    
    def adaptive_slice_sizing(
        self,
        parent_order_id: str,
        realized_volume: float,
        expected_volume: float,
        remaining_size: float
    ) -> List[float]:
        """Adaptively adjust slice sizes based on market conditions"""
        
        # If realized volume > expected, speed up
        # If realized volume < expected, slow down
        
        volume_ratio = realized_volume / expected_volume if expected_volume > 0 else 1.0
        
        # Adjust urgency
        if volume_ratio > 1.2:  # More volume than expected
            urgency_adjustment = 1.3  # Speed up
        elif volume_ratio < 0.8:  # Less volume than expected
            urgency_adjustment = 0.7  # Slow down
        else:
            urgency_adjustment = 1.0
        
        # Calculate new slice sizes
        remaining_slices = len(self.active_orders.get(parent_order_id, []))
        if remaining_slices > 0:
            base_size = remaining_size / remaining_slices
            adjusted_sizes = [base_size * urgency_adjustment] * remaining_slices
            return adjusted_sizes
        
        return [remaining_size]
    
    def record_execution(
        self,
        slice_id: str,
        executed_price: float,
        executed_size: float,
        venue: str,
        slippage_bps: float
    ) -> None:
        """Record execution for performance tracking"""
        
        self.execution_history.append({
            'slice_id': slice_id,
            'price': executed_price,
            'size': executed_size,
            'venue': venue,
            'slippage_bps': slippage_bps,
            'timestamp': datetime.utcnow()
        })
    
    def get_execution_performance(self, parent_order_id: str) -> Dict[str, Any]:
        """Get execution performance metrics for a parent order"""
        
        slices = self.active_orders.get(parent_order_id, [])
        
        if not slices:
            return {'error': 'Order not found'}
        
        # Calculate metrics
        total_size = sum(s.size for s in slices)
        
        # Get executions for these slices
        slice_ids = {s.slice_id for s in slices}
        executions = [
            e for e in self.execution_history
            if e['slice_id'] in slice_ids
        ]
        
        if not executions:
            return {
                'parent_order_id': parent_order_id,
                'total_slices': len(slices),
                'executed_slices': 0,
                'fill_rate': 0.0
            }
        
        executed_size = sum(e['size'] for e in executions)
        avg_slippage = sum(e['slippage_bps'] for e in executions) / len(executions)
        
        return {
            'parent_order_id': parent_order_id,
            'total_slices': len(slices),
            'executed_slices': len(executions),
            'fill_rate': executed_size / total_size,
            'avg_slippage_bps': avg_slippage,
            'total_executed': executed_size,
            'venues_used': list(set(e['venue'] for e in executions))
        }


class EnhancedExecutionEngine:
    """
    Complete execution engine combining routing and algorithms.
    """
    
    def __init__(self):
        self.router = SmartOrderRouter()
        self.algorithms = ExecutionAlgorithmEngine()
        self.liquidity_monitor = LiquidityMonitor()
        
    def execute_order(
        self,
        symbol: str,
        size: float,
        side: str,
        urgency: float = 0.5,
        market_conditions: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute an order with intelligent routing and algorithms.
        
        Returns:
            Execution plan and performance estimates
        """
        
        market_conditions = market_conditions or {}
        
        # Get routing decision
        routing = self.router.route_order(
            symbol, size, side, urgency, market_conditions
        )
        
        # Determine if algorithmic execution needed
        avg_volume = market_conditions.get('avg_daily_volume', size * 10)
        
        if size > avg_volume * 0.05:  # Large order
            # Use execution algorithm
            if routing.execution_strategy == ExecutionStrategy.TWAP:
                slices = self.algorithms.create_twap_slices(
                    f"order_{symbol}_{datetime.utcnow().timestamp()}",
                    size, 30, 5, side
                )
            elif routing.execution_strategy == ExecutionStrategy.VWAP:
                slices = self.algorithms.create_vwap_slices(
                    f"order_{symbol}_{datetime.utcnow().timestamp()}",
                    size, 30, side
                )
            else:
                slices = []
        else:
            slices = []
        
        return {
            'routing_decision': routing,
            'execution_strategy': routing.execution_strategy.value,
            'algorithm_slices': [
                {
                    'id': s.slice_id,
                    'size': s.size,
                    'time': s.scheduled_time.isoformat()
                }
                for s in slices
            ],
            'expected_performance': {
                'cost_bps': routing.expected_cost_bps,
                'fill_time_ms': routing.expected_fill_time_ms,
                'market_impact_bps': routing.market_impact_estimate
            }
        }


class LiquidityMonitor:
    """
    Real-time liquidity monitoring across venues.
    """
    
    def __init__(self):
        self.liquidity_snapshots: Dict[str, Dict] = {}
        self.liquidity_history: Dict[str, deque] = {}
        
    def update_liquidity(
        self,
        symbol: str,
        venue: str,
        bid_depth: float,
        ask_depth: float,
        spread_bps: float
    ) -> None:
        """Update liquidity snapshot for a symbol/venue"""
        
        if symbol not in self.liquidity_snapshots:
            self.liquidity_snapshots[symbol] = {}
            self.liquidity_history[symbol] = deque(maxlen=100)
        
        snapshot = {
            'venue': venue,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'spread_bps': spread_bps,
            'total_depth': bid_depth + ask_depth,
            'timestamp': datetime.utcnow()
        }
        
        self.liquidity_snapshots[symbol][venue] = snapshot
        self.liquidity_history[symbol].append(snapshot)
    
    def get_best_liquidity(self, symbol: str) -> Tuple[str, float]:
        """Get venue with best liquidity for symbol"""
        
        venues = self.liquidity_snapshots.get(symbol, {})
        
        if not venues:
            return 'primary', 0.5
        
        # Score by total depth and spread
        best_venue = None
        best_score = 0
        
        for venue, snapshot in venues.items():
            depth_score = min(1.0, snapshot['total_depth'] / 10000)
            spread_score = max(0, 1 - snapshot['spread_bps'] / 50)
            
            score = depth_score * 0.6 + spread_score * 0.4
            
            if score > best_score:
                best_score = score
                best_venue = venue
        
        return best_venue or 'primary', best_score
