"""
APEX-FI Layer 5: Intelligent Execution & Microstructure Navigation
===================================================================

Citadel-inspired execution intelligence with RL-trained order router,
adversarial defense, transaction cost prediction, and co-located edge intelligence.

Mission: Turn portfolio targets into executed positions with zero information leakage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class VenueType(str, Enum):
    """Execution venue types."""
    LIT_EXCHANGE = "lit_exchange"
    DARK_POOL = "dark_pool"
    ATS = "ats"  # Alternative Trading System
    CROSSING_NETWORK = "crossing_network"


class ExecutionAlgorithm(str, Enum):
    """Execution algorithm types."""
    VWAP = "vwap"
    TWAP = "twap"
    POV = "pov"  # Percentage of Volume
    IMPLEMENTATION_SHORTFALL = "implementation_shortfall"
    ADAPTIVE = "adaptive"


@dataclass
class ExecutionPlan:
    """Execution plan for an order."""
    order_id: str
    symbol: str
    target_quantity: float
    side: str  # 'buy' or 'sell'
    algorithm: ExecutionAlgorithm
    venues: List[VenueType]
    time_horizon_seconds: int
    urgency: float  # 0-1, higher = more urgent
    max_participation_rate: float = 0.10
    predicted_cost_bps: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of order execution."""
    order_id: str
    executed_quantity: float
    average_price: float
    total_cost: float
    slippage_bps: float
    venues_used: List[VenueType]
    execution_time_seconds: float
    quality_score: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


class RLOrderRouter:
    """
    Reinforcement Learning-trained order router.
    
    Learns optimal routing across 50+ venues adapting to intraday microstructure patterns.
    """
    
    def __init__(self):
        self.venues: Dict[str, Dict[str, Any]] = {}
        self.routing_history: deque = deque(maxlen=10000)
        self.venue_performance: Dict[str, List[float]] = {}
        
        self._initialize_venues()
        
        logger.info("RL Order Router initialized")
    
    def _initialize_venues(self) -> None:
        """Initialize venue configurations."""
        # Major lit exchanges
        self.venues['NYSE'] = {
            'type': VenueType.LIT_EXCHANGE,
            'avg_spread_bps': 1.0,
            'avg_depth': 100000,
            'latency_ms': 0.5,
        }
        
        self.venues['NASDAQ'] = {
            'type': VenueType.LIT_EXCHANGE,
            'avg_spread_bps': 0.8,
            'avg_depth': 120000,
            'latency_ms': 0.4,
        }
        
        # Dark pools
        self.venues['SIGMA_X'] = {
            'type': VenueType.DARK_POOL,
            'avg_spread_bps': 0.5,
            'avg_depth': 50000,
            'latency_ms': 1.0,
        }
        
        self.venues['CROSSFINDER'] = {
            'type': VenueType.DARK_POOL,
            'avg_spread_bps': 0.6,
            'avg_depth': 40000,
            'latency_ms': 1.2,
        }
        
        logger.debug(f"Initialized {len(self.venues)} venues")
    
    def select_venues(
        self,
        symbol: str,
        quantity: float,
        urgency: float,
        time_of_day: str = "midday"
    ) -> List[str]:
        """
        Select optimal venues using RL policy.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            urgency: Urgency level (0-1)
            time_of_day: Time of day (opening, midday, close)
            
        Returns:
            List of venue IDs
        """
        # Simplified RL policy (in production: actual RL agent)
        selected_venues = []
        
        if urgency > 0.7:
            # High urgency: use lit exchanges
            selected_venues = ['NYSE', 'NASDAQ']
        elif urgency < 0.3:
            # Low urgency: try dark pools first
            selected_venues = ['SIGMA_X', 'CROSSFINDER', 'NYSE']
        else:
            # Medium urgency: balanced approach
            selected_venues = ['NASDAQ', 'SIGMA_X', 'NYSE']
        
        # Adjust based on time of day
        if time_of_day == "opening":
            # Prefer lit exchanges during opening
            selected_venues = ['NYSE', 'NASDAQ'] + selected_venues
        elif time_of_day == "close":
            # More aggressive during close
            selected_venues = ['NYSE', 'NASDAQ']
        
        # Remove duplicates while preserving order
        seen = set()
        unique_venues = []
        for venue in selected_venues:
            if venue not in seen and venue in self.venues:
                seen.add(venue)
                unique_venues.append(venue)
        
        return unique_venues[:3]  # Top 3 venues
    
    def route_order(
        self,
        plan: ExecutionPlan
    ) -> Dict[str, float]:
        """
        Route order across venues.
        
        Returns:
            Venue allocations (venue_id -> quantity)
        """
        # Select venues
        venues = self.select_venues(
            plan.symbol,
            plan.target_quantity,
            plan.urgency
        )
        
        # Allocate quantity across venues (simplified)
        allocations = {}
        remaining = plan.target_quantity
        
        for i, venue in enumerate(venues):
            if i == len(venues) - 1:
                # Last venue gets remainder
                allocations[venue] = remaining
            else:
                # Split proportionally
                allocation = remaining / (len(venues) - i)
                allocations[venue] = allocation
                remaining -= allocation
        
        logger.debug(f"Routed order across {len(allocations)} venues")
        return allocations
    
    def record_execution(
        self,
        venue: str,
        quality_score: float,
        slippage_bps: float
    ) -> None:
        """Record execution quality for learning."""
        if venue not in self.venue_performance:
            self.venue_performance[venue] = []
        
        self.venue_performance[venue].append(quality_score)
        
        # Keep only recent performance
        if len(self.venue_performance[venue]) > 1000:
            self.venue_performance[venue] = self.venue_performance[venue][-1000:]
        
        self.routing_history.append({
            'timestamp': datetime.now(),
            'venue': venue,
            'quality': quality_score,
            'slippage': slippage_bps,
        })


class AdversarialDefense:
    """
    Adversarial execution defense.
    
    Detects and evades predatory HFT order flow patterns.
    Randomizes order sizing, timing, and venue selection.
    """
    
    def __init__(self):
        self.adverse_selection_threshold = 0.3
        self.randomization_enabled = True
        self.suspicious_patterns: deque = deque(maxlen=1000)
        
        logger.info("Adversarial Defense initialized")
    
    def detect_front_running(
        self,
        order_flow: List[Dict[str, Any]]
    ) -> bool:
        """
        Detect potential front-running patterns.
        
        Args:
            order_flow: Recent order flow data
            
        Returns:
            True if front-running detected
        """
        if len(order_flow) < 3:
            return False
        
        # Simplified detection: look for orders ahead of ours
        # In production: sophisticated pattern matching
        
        our_orders = [o for o in order_flow if o.get('is_ours', False)]
        other_orders = [o for o in order_flow if not o.get('is_ours', False)]
        
        if not our_orders or not other_orders:
            return False
        
        # Check if other orders consistently appear just before ours
        front_running_count = 0
        
        for our_order in our_orders:
            our_time = our_order.get('timestamp', 0)
            
            for other_order in other_orders:
                other_time = other_order.get('timestamp', 0)
                
                # Other order within 100ms before ours
                if 0 < (our_time - other_time) < 0.1:
                    front_running_count += 1
        
        # If >30% of our orders are preceded by others, suspicious
        if len(our_orders) > 0:
            ratio = front_running_count / len(our_orders)
            return ratio > self.adverse_selection_threshold
        
        return False
    
    def randomize_order_params(
        self,
        base_quantity: float,
        base_timing_ms: float
    ) -> Tuple[float, float]:
        """
        Randomize order parameters to prevent detection.
        
        Returns:
            (randomized_quantity, randomized_timing_ms)
        """
        if not self.randomization_enabled:
            return base_quantity, base_timing_ms
        
        # Randomize quantity ±10%
        quantity_noise = np.random.uniform(-0.1, 0.1)
        randomized_quantity = base_quantity * (1 + quantity_noise)
        
        # Randomize timing ±20%
        timing_noise = np.random.uniform(-0.2, 0.2)
        randomized_timing = base_timing_ms * (1 + timing_noise)
        
        return randomized_quantity, randomized_timing
    
    def should_pause_execution(
        self,
        adverse_selection_score: float
    ) -> bool:
        """
        Determine if execution should be paused due to adverse conditions.
        
        Args:
            adverse_selection_score: Score from 0-1 (higher = more adverse)
            
        Returns:
            True if should pause
        """
        return adverse_selection_score > self.adverse_selection_threshold


class TransactionCostEngine:
    """
    Transaction cost intelligence engine.
    
    Predicts realized transaction costs pre-trade and measures post-trade.
    Delta continuously recalibrates the cost model.
    """
    
    def __init__(self):
        self.cost_model_params = {
            'spread_impact': 0.5,
            'depth_impact': 0.3,
            'volatility_impact': 0.2,
        }
        
        self.prediction_errors: deque = deque(maxlen=1000)
        
        logger.info("Transaction Cost Engine initialized")
    
    def predict_cost(
        self,
        symbol: str,
        quantity: float,
        bid_ask_spread_bps: float,
        market_depth: float,
        volatility: float,
        participation_rate: float
    ) -> float:
        """
        Predict transaction cost in basis points.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            bid_ask_spread_bps: Current bid-ask spread in bps
            market_depth: Available market depth
            volatility: Recent volatility
            participation_rate: Our participation rate in volume
            
        Returns:
            Predicted cost in basis points
        """
        # Base cost from spread
        spread_cost = bid_ask_spread_bps * self.cost_model_params['spread_impact']
        
        # Market impact from depth
        if market_depth > 0:
            depth_ratio = quantity / market_depth
            depth_cost = depth_ratio * 100 * self.cost_model_params['depth_impact']
        else:
            depth_cost = 10.0  # High cost if no depth
        
        # Volatility cost
        volatility_cost = volatility * 100 * self.cost_model_params['volatility_impact']
        
        # Participation rate impact (higher participation = higher cost)
        participation_cost = participation_rate * 50
        
        total_cost = spread_cost + depth_cost + volatility_cost + participation_cost
        
        return max(0.0, total_cost)
    
    def measure_realized_cost(
        self,
        execution_price: float,
        benchmark_price: float
    ) -> float:
        """
        Measure realized transaction cost.
        
        Args:
            execution_price: Actual execution price
            benchmark_price: Benchmark price (e.g., arrival price)
            
        Returns:
            Realized cost in basis points
        """
        if benchmark_price == 0:
            return 0.0
        
        cost_bps = abs((execution_price - benchmark_price) / benchmark_price) * 10000
        
        return cost_bps
    
    def update_model(
        self,
        predicted_cost_bps: float,
        realized_cost_bps: float
    ) -> None:
        """Update cost model based on prediction error."""
        error = abs(predicted_cost_bps - realized_cost_bps)
        self.prediction_errors.append(error)
        
        # Recalibrate model parameters (simplified)
        if len(self.prediction_errors) >= 100:
            avg_error = np.mean(list(self.prediction_errors)[-100:])
            
            # Adjust parameters if error is high
            if avg_error > 5.0:
                # Increase impact parameters
                for key in self.cost_model_params:
                    self.cost_model_params[key] *= 1.05
            elif avg_error < 2.0:
                # Decrease impact parameters
                for key in self.cost_model_params:
                    self.cost_model_params[key] *= 0.95
        
        logger.debug(f"Cost model updated - Error: {error:.2f} bps")
    
    def get_model_accuracy(self) -> float:
        """Get cost model prediction accuracy."""
        if not self.prediction_errors:
            return 0.0
        
        avg_error = np.mean(list(self.prediction_errors))
        # Convert error to accuracy score
        accuracy = max(0.0, 1.0 - (avg_error / 10.0))
        
        return accuracy


class MicrostructureNavigator:
    """
    Market microstructure navigation.
    
    Monitors order book dynamics, quote staleness, and optimal execution timing.
    """
    
    def __init__(self):
        self.order_book_snapshots: deque = deque(maxlen=1000)
        self.quote_staleness_threshold_ms = 100
        
        logger.info("Microstructure Navigator initialized")
    
    def analyze_order_book(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Analyze order book for execution insights.
        
        Args:
            bids: List of (price, size) tuples
            asks: List of (price, size) tuples
            
        Returns:
            Order book analysis
        """
        if not bids or not asks:
            return {'imbalance': 0.0, 'spread_bps': 0.0, 'depth': 0.0}
        
        # Calculate imbalance
        bid_volume = sum(size for _, size in bids)
        ask_volume = sum(size for _, size in asks)
        total_volume = bid_volume + ask_volume
        
        if total_volume > 0:
            imbalance = (bid_volume - ask_volume) / total_volume
        else:
            imbalance = 0.0
        
        # Calculate spread
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid_price = (best_bid + best_ask) / 2
        
        if mid_price > 0:
            spread_bps = ((best_ask - best_bid) / mid_price) * 10000
        else:
            spread_bps = 0.0
        
        # Calculate depth
        depth = bid_volume + ask_volume
        
        return {
            'imbalance': imbalance,
            'spread_bps': spread_bps,
            'depth': depth,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price,
        }
    
    def is_quote_stale(
        self,
        quote_timestamp: datetime,
        current_time: datetime
    ) -> bool:
        """Check if quote is stale."""
        age_ms = (current_time - quote_timestamp).total_seconds() * 1000
        return age_ms > self.quote_staleness_threshold_ms
    
    def get_optimal_execution_timing(
        self,
        time_of_day: datetime,
        volatility: float
    ) -> str:
        """
        Determine optimal execution timing.
        
        Returns:
            Timing recommendation: 'immediate', 'patient', 'wait'
        """
        hour = time_of_day.hour
        
        # Avoid opening and closing auctions if low urgency
        if hour == 9 or hour == 15:
            if volatility > 0.02:
                return 'wait'  # High volatility during auction
        
        # Midday typically has better liquidity
        if 11 <= hour <= 14:
            return 'patient'
        
        return 'immediate'


class ExecutionIntelligence:
    """
    Execution Intelligence - Master coordinator for Layer 5.
    
    Integrates RL order router, adversarial defense, transaction cost engine,
    and microstructure navigator.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.order_router = RLOrderRouter()
        self.adversarial_defense = AdversarialDefense()
        self.cost_engine = TransactionCostEngine()
        self.microstructure = MicrostructureNavigator()
        
        self.execution_history: List[ExecutionResult] = []
        
        logger.info("Execution Intelligence initialized - Layer 5 operational")
    
    def create_execution_plan(
        self,
        order_id: str,
        symbol: str,
        quantity: float,
        side: str,
        urgency: float = 0.5,
        time_horizon_seconds: int = 300
    ) -> ExecutionPlan:
        """
        Create execution plan for an order.
        
        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            quantity: Target quantity
            side: 'buy' or 'sell'
            urgency: Urgency level (0-1)
            time_horizon_seconds: Time horizon for execution
            
        Returns:
            Execution plan
        """
        # Select venues
        venues_list = self.order_router.select_venues(symbol, quantity, urgency)
        venues = [VenueType.LIT_EXCHANGE if 'NYSE' in v or 'NASDAQ' in v 
                 else VenueType.DARK_POOL for v in venues_list]
        
        # Predict transaction cost
        predicted_cost = self.cost_engine.predict_cost(
            symbol=symbol,
            quantity=quantity,
            bid_ask_spread_bps=1.0,  # Placeholder
            market_depth=100000,  # Placeholder
            volatility=0.01,  # Placeholder
            participation_rate=0.05
        )
        
        # Determine algorithm
        if urgency > 0.7:
            algorithm = ExecutionAlgorithm.IMPLEMENTATION_SHORTFALL
        elif urgency < 0.3:
            algorithm = ExecutionAlgorithm.VWAP
        else:
            algorithm = ExecutionAlgorithm.ADAPTIVE
        
        plan = ExecutionPlan(
            order_id=order_id,
            symbol=symbol,
            target_quantity=quantity,
            side=side,
            algorithm=algorithm,
            venues=venues,
            time_horizon_seconds=time_horizon_seconds,
            urgency=urgency,
            predicted_cost_bps=predicted_cost,
        )
        
        logger.info(f"Created execution plan: {order_id} - {algorithm.value}")
        return plan
    
    def execute_plan(
        self,
        plan: ExecutionPlan,
        market_data: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute the plan.
        
        Args:
            plan: Execution plan
            market_data: Optional market data
            
        Returns:
            Execution result
        """
        start_time = datetime.now()
        
        # Check for adverse conditions
        adverse_score = 0.2  # Placeholder
        if self.adversarial_defense.should_pause_execution(adverse_score):
            logger.warning("Execution paused due to adverse conditions")
        
        # Route order across venues
        venue_allocations = self.order_router.route_order(plan)
        
        # Simulate execution (in production: actual execution)
        executed_quantity = plan.target_quantity
        average_price = 100.0  # Placeholder
        benchmark_price = 100.0  # Placeholder
        
        # Measure cost
        realized_cost = self.cost_engine.measure_realized_cost(
            average_price,
            benchmark_price
        )
        
        # Update cost model
        self.cost_engine.update_model(plan.predicted_cost_bps, realized_cost)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Quality score (simplified)
        cost_accuracy = 1.0 - abs(plan.predicted_cost_bps - realized_cost) / max(plan.predicted_cost_bps, 1.0)
        quality_score = max(0.0, min(1.0, cost_accuracy))
        
        result = ExecutionResult(
            order_id=plan.order_id,
            executed_quantity=executed_quantity,
            average_price=average_price,
            total_cost=executed_quantity * average_price,
            slippage_bps=realized_cost,
            venues_used=plan.venues,
            execution_time_seconds=execution_time,
            quality_score=quality_score,
        )
        
        self.execution_history.append(result)
        
        # Record for RL learning
        for venue in venue_allocations:
            self.order_router.record_execution(venue, quality_score, realized_cost)
        
        logger.info(f"Executed order {plan.order_id} - Quality: {quality_score:.2f}")
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution intelligence statistics."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'average_quality': 0.0,
                'average_slippage_bps': 0.0,
                'cost_model_accuracy': self.cost_engine.get_model_accuracy(),
            }
        
        return {
            'total_executions': len(self.execution_history),
            'average_quality': np.mean([r.quality_score for r in self.execution_history]),
            'average_slippage_bps': np.mean([r.slippage_bps for r in self.execution_history]),
            'cost_model_accuracy': self.cost_engine.get_model_accuracy(),
            'venues_count': len(self.order_router.venues),
        }
