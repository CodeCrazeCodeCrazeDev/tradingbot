"""
AlphaAlgo Institutional - Layer 6: Execution & Microstructure
==============================================================

The Execution Layer is responsible for:
- Optimal order execution
- Market microstructure analysis
- Transaction cost analysis
- Slippage minimization
- Execution algorithm selection
- Fill quality monitoring

This layer operates as the EXECUTION INTELLIGENCE UNIT.

Key principles:
- Execution costs are real costs
- Market impact must be minimized
- Timing matters
- Liquidity is not guaranteed
- Adverse selection is real
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict
import uuid

from .core_types import (
    ExecutionPlan, TradeResult, CommitteeType, CommitteeVote,
    CommitteeDecision, MarketRegime, RiskLevel, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXECUTION TYPES
# =============================================================================

class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"  # Percentage of volume
    IS = "is"  # Implementation shortfall


class ExecutionAlgorithm(Enum):
    """Execution algorithms."""
    DIRECT = "direct"  # Direct market order
    TWAP = "twap"  # Time-weighted average price
    VWAP = "vwap"  # Volume-weighted average price
    POV = "pov"  # Percentage of volume
    IS = "is"  # Implementation shortfall minimization
    ICEBERG = "iceberg"  # Hidden size orders
    SNIPER = "sniper"  # Aggressive liquidity taking
    PASSIVE = "passive"  # Passive limit orders
    ADAPTIVE = "adaptive"  # Adaptive based on conditions


class ExecutionUrgency(Enum):
    """Execution urgency levels."""
    LOW = "low"  # Can wait for best price
    MEDIUM = "medium"  # Balance speed and price
    HIGH = "high"  # Need execution soon
    IMMEDIATE = "immediate"  # Execute now regardless of cost


class FillQuality(Enum):
    """Fill quality assessment."""
    EXCELLENT = "excellent"  # Better than expected
    GOOD = "good"  # Within expectations
    ACCEPTABLE = "acceptable"  # Slightly worse than expected
    POOR = "poor"  # Significantly worse
    FAILED = "failed"  # Execution failed


@dataclass
class OrderBookState:
    """Current order book state."""
    symbol: str
    timestamp: datetime
    best_bid: float
    best_ask: float
    bid_size: float
    ask_size: float
    bid_depth: List[Tuple[float, float]]  # (price, size) levels
    ask_depth: List[Tuple[float, float]]
    spread: float
    spread_bps: float
    imbalance: float  # Bid/ask imbalance


@dataclass
class ExecutionContext:
    """Context for execution decision."""
    symbol: str
    direction: str  # 'buy' or 'sell'
    quantity: float
    urgency: ExecutionUrgency
    max_participation_rate: float
    max_slippage_bps: float
    time_horizon_minutes: int
    order_book: Optional[OrderBookState] = None
    regime: MarketRegime = MarketRegime.NORMAL
    volatility: float = 0.0
    avg_daily_volume: float = 0.0


@dataclass
class ExecutionOrder:
    """An execution order."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    parent_id: Optional[str] = None
    symbol: str = ""
    direction: str = ""
    order_type: OrderType = OrderType.LIMIT
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.DIRECT
    quantity: float = 0.0
    filled_quantity: float = 0.0
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    status: str = "pending"
    avg_fill_price: float = 0.0
    slippage_bps: float = 0.0
    commission: float = 0.0


@dataclass
class ExecutionReport:
    """Execution quality report."""
    order_id: str
    symbol: str
    direction: str
    quantity: float
    avg_price: float
    arrival_price: float
    vwap: float
    implementation_shortfall: float
    slippage_bps: float
    market_impact_bps: float
    timing_cost_bps: float
    fill_rate: float
    fill_quality: FillQuality
    execution_time_seconds: float


# =============================================================================
# MARKET MICROSTRUCTURE ANALYZER
# =============================================================================

class MicrostructureAnalyzer:
    """Analyzes market microstructure."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.spread_history: Dict[str, List[float]] = defaultdict(list)
        self.volume_history: Dict[str, List[float]] = defaultdict(list)
    
    def analyze_order_book(self, order_book: OrderBookState) -> Dict[str, Any]:
        """
        Analyze order book state.
        
        Returns:
            Dict of microstructure metrics
        """
        # Spread analysis
        spread_bps = order_book.spread_bps
        
        # Depth analysis
        total_bid_depth = sum(size for _, size in order_book.bid_depth)
        total_ask_depth = sum(size for _, size in order_book.ask_depth)
        
        # Imbalance
        if total_bid_depth + total_ask_depth > 0:
            imbalance = (total_bid_depth - total_ask_depth) / (total_bid_depth + total_ask_depth)
        else:
            imbalance = 0.0
        
        # Depth-weighted mid price
        if order_book.bid_depth and order_book.ask_depth:
            bid_weighted = sum(p * s for p, s in order_book.bid_depth) / max(1, total_bid_depth)
            ask_weighted = sum(p * s for p, s in order_book.ask_depth) / max(1, total_ask_depth)
            weighted_mid = (bid_weighted + ask_weighted) / 2
        else:
            weighted_mid = (order_book.best_bid + order_book.best_ask) / 2
        
        # Liquidity score (0-1)
        liquidity_score = min(1.0, (total_bid_depth + total_ask_depth) / 1000000)
        
        return {
            'spread_bps': spread_bps,
            'total_bid_depth': total_bid_depth,
            'total_ask_depth': total_ask_depth,
            'imbalance': imbalance,
            'weighted_mid': weighted_mid,
            'liquidity_score': liquidity_score,
            'is_liquid': liquidity_score > 0.3 and spread_bps < 10
        }
    
    def estimate_market_impact(
        self,
        order_size: float,
        avg_daily_volume: float,
        volatility: float
    ) -> float:
        """
        Estimate market impact in basis points.
        
        Uses simplified Almgren-Chriss model.
        """
        if avg_daily_volume <= 0:
            return 100.0  # High impact for illiquid
        
        # Participation rate
        participation = order_size / avg_daily_volume
        
        # Temporary impact (linear in participation)
        temp_impact = 10 * participation  # 10 bps per 1% participation
        
        # Permanent impact (square root in participation)
        perm_impact = 5 * np.sqrt(participation)
        
        # Volatility adjustment
        vol_adjustment = volatility / 0.20  # Normalized to 20% vol
        
        total_impact = (temp_impact + perm_impact) * vol_adjustment
        
        return min(100, total_impact)  # Cap at 100 bps
    
    def detect_adverse_selection(
        self,
        fills: List[Tuple[float, float, datetime]],  # (price, size, time)
        mid_prices: List[Tuple[float, datetime]]
    ) -> float:
        """
        Detect adverse selection in fills.
        
        Returns:
            Adverse selection score (0-1, higher = more adverse)
        """
        if not fills or not mid_prices:
            return 0.0
        
        adverse_count = 0
        total_count = 0
        
        for fill_price, fill_size, fill_time in fills:
            # Find mid price at fill time
            relevant_mids = [m for m, t in mid_prices if t <= fill_time]
            if not relevant_mids:
                continue
            
            mid_at_fill = relevant_mids[-1]
            
            # Find mid price after fill (e.g., 1 minute later)
            future_mids = [m for m, t in mid_prices if t > fill_time]
            if not future_mids:
                continue
            
            mid_after = future_mids[0]
            
            # Check if price moved against us
            # For buys: adverse if mid went down after fill
            # For sells: adverse if mid went up after fill
            if fill_price > mid_at_fill:  # Likely a buy
                if mid_after < mid_at_fill:
                    adverse_count += 1
            else:  # Likely a sell
                if mid_after > mid_at_fill:
                    adverse_count += 1
            
            total_count += 1
        
        return adverse_count / max(1, total_count)


# =============================================================================
# EXECUTION ALGORITHM SELECTOR
# =============================================================================

class AlgorithmSelector:
    """Selects optimal execution algorithm."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def select_algorithm(self, context: ExecutionContext) -> ExecutionAlgorithm:
        """
        Select optimal execution algorithm based on context.
        
        Args:
            context: Execution context
            
        Returns:
            Selected execution algorithm
        """
        # Immediate urgency -> direct market order
        if context.urgency == ExecutionUrgency.IMMEDIATE:
            return ExecutionAlgorithm.DIRECT
        
        # Calculate participation rate
        if context.avg_daily_volume > 0:
            participation = context.quantity / context.avg_daily_volume
        else:
            participation = 1.0
        
        # Large orders (>5% ADV) -> TWAP or VWAP
        if participation > 0.05:
            if context.time_horizon_minutes >= 60:
                return ExecutionAlgorithm.VWAP
            else:
                return ExecutionAlgorithm.TWAP
        
        # Medium orders (1-5% ADV) -> POV or IS
        if participation > 0.01:
            if context.urgency == ExecutionUrgency.HIGH:
                return ExecutionAlgorithm.IS
            else:
                return ExecutionAlgorithm.POV
        
        # Small orders -> based on urgency and spread
        if context.order_book and context.order_book.spread_bps < 5:
            if context.urgency == ExecutionUrgency.LOW:
                return ExecutionAlgorithm.PASSIVE
            else:
                return ExecutionAlgorithm.DIRECT
        
        # Default to adaptive
        return ExecutionAlgorithm.ADAPTIVE
    
    def get_algorithm_parameters(
        self,
        algorithm: ExecutionAlgorithm,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Get parameters for selected algorithm."""
        params = {
            'algorithm': algorithm.value,
            'symbol': context.symbol,
            'direction': context.direction,
            'quantity': context.quantity
        }
        
        if algorithm == ExecutionAlgorithm.TWAP:
            params['duration_minutes'] = context.time_horizon_minutes
            params['slice_count'] = max(5, context.time_horizon_minutes // 5)
        
        elif algorithm == ExecutionAlgorithm.VWAP:
            params['duration_minutes'] = context.time_horizon_minutes
            params['volume_profile'] = 'historical'
        
        elif algorithm == ExecutionAlgorithm.POV:
            params['participation_rate'] = min(0.20, context.max_participation_rate)
            params['max_duration_minutes'] = context.time_horizon_minutes
        
        elif algorithm == ExecutionAlgorithm.IS:
            params['risk_aversion'] = 0.5
            params['urgency'] = context.urgency.value
        
        elif algorithm == ExecutionAlgorithm.ICEBERG:
            params['display_size'] = context.quantity * 0.1
            params['refresh_rate'] = 0.5
        
        elif algorithm == ExecutionAlgorithm.PASSIVE:
            params['limit_offset_bps'] = 2
            params['timeout_minutes'] = context.time_horizon_minutes
        
        return params


# =============================================================================
# TRANSACTION COST ANALYZER
# =============================================================================

class TransactionCostAnalyzer:
    """Analyzes transaction costs."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.execution_history: List[ExecutionReport] = []
    
    def estimate_costs(
        self,
        symbol: str,
        quantity: float,
        direction: str,
        order_book: Optional[OrderBookState],
        avg_daily_volume: float,
        volatility: float
    ) -> Dict[str, float]:
        """
        Estimate transaction costs.
        
        Returns:
            Dict of cost components in basis points
        """
        costs = {}
        
        # Spread cost (half spread for crossing)
        if order_book:
            costs['spread_cost_bps'] = order_book.spread_bps / 2
        else:
            costs['spread_cost_bps'] = 5.0  # Default assumption
        
        # Market impact
        if avg_daily_volume > 0:
            participation = quantity / avg_daily_volume
            costs['market_impact_bps'] = 10 * np.sqrt(participation) * (volatility / 0.20)
        else:
            costs['market_impact_bps'] = 20.0
        
        # Commission (assumed)
        costs['commission_bps'] = self.config.get('commission_bps', 1.0)
        
        # Timing risk (opportunity cost)
        costs['timing_risk_bps'] = volatility * 100 / np.sqrt(252)  # Daily vol in bps
        
        # Total
        costs['total_bps'] = sum(costs.values())
        
        return costs
    
    def analyze_execution(
        self,
        order: ExecutionOrder,
        arrival_price: float,
        vwap: float
    ) -> ExecutionReport:
        """
        Analyze execution quality.
        
        Args:
            order: Executed order
            arrival_price: Price at order arrival
            vwap: Volume-weighted average price during execution
            
        Returns:
            ExecutionReport
        """
        # Implementation shortfall
        if order.direction == 'buy':
            is_bps = (order.avg_fill_price - arrival_price) / arrival_price * 10000
        else:
            is_bps = (arrival_price - order.avg_fill_price) / arrival_price * 10000
        
        # Slippage vs VWAP
        if order.direction == 'buy':
            vwap_slippage = (order.avg_fill_price - vwap) / vwap * 10000
        else:
            vwap_slippage = (vwap - order.avg_fill_price) / vwap * 10000
        
        # Fill rate
        fill_rate = order.filled_quantity / order.quantity if order.quantity > 0 else 0
        
        # Execution time
        if order.filled_at and order.created_at:
            exec_time = (order.filled_at - order.created_at).total_seconds()
        else:
            exec_time = 0
        
        # Fill quality assessment
        if is_bps < 0:
            quality = FillQuality.EXCELLENT
        elif is_bps < 5:
            quality = FillQuality.GOOD
        elif is_bps < 15:
            quality = FillQuality.ACCEPTABLE
        elif fill_rate > 0:
            quality = FillQuality.POOR
        else:
            quality = FillQuality.FAILED
        
        report = ExecutionReport(
            order_id=order.id,
            symbol=order.symbol,
            direction=order.direction,
            quantity=order.quantity,
            avg_price=order.avg_fill_price,
            arrival_price=arrival_price,
            vwap=vwap,
            implementation_shortfall=is_bps,
            slippage_bps=order.slippage_bps,
            market_impact_bps=is_bps * 0.6,  # Estimate
            timing_cost_bps=is_bps * 0.4,  # Estimate
            fill_rate=fill_rate,
            fill_quality=quality,
            execution_time_seconds=exec_time
        )
        
        self.execution_history.append(report)
        return report
    
    def get_historical_costs(self, symbol: str = None) -> Dict[str, float]:
        """Get historical average costs."""
        relevant = self.execution_history
        if symbol:
            relevant = [r for r in relevant if r.symbol == symbol]
        
        if not relevant:
            return {'avg_is_bps': 0, 'avg_slippage_bps': 0, 'avg_fill_rate': 1.0}
        
        return {
            'avg_is_bps': np.mean([r.implementation_shortfall for r in relevant]),
            'avg_slippage_bps': np.mean([r.slippage_bps for r in relevant]),
            'avg_fill_rate': np.mean([r.fill_rate for r in relevant]),
            'sample_count': len(relevant)
        }


# =============================================================================
# EXECUTION INTELLIGENCE UNIT
# =============================================================================

class ExecutionIntelligenceUnit:
    """
    Internal committee responsible for execution.
    
    Responsibilities:
    - Optimal execution algorithm selection
    - Market microstructure analysis
    - Transaction cost analysis
    - Fill quality monitoring
    - Execution timing
    
    Key principles:
    - Execution costs are real costs
    - Market impact must be minimized
    - Timing matters
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.EXECUTION_INTELLIGENCE
        
        # Initialize components
        self.microstructure_analyzer = MicrostructureAnalyzer(self.config)
        self.algorithm_selector = AlgorithmSelector(self.config)
        self.tca = TransactionCostAnalyzer(self.config)
        
        # Order tracking
        self.pending_orders: Dict[str, ExecutionOrder] = {}
        self.completed_orders: List[ExecutionOrder] = []
        
        # Execution metrics
        self.total_orders = 0
        self.successful_orders = 0
        self.total_slippage_bps = 0.0
        
        logger.info("ExecutionIntelligenceUnit initialized")
    
    def create_execution_plan(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        urgency: ExecutionUrgency,
        order_book: Optional[OrderBookState] = None,
        regime: MarketRegime = MarketRegime.NORMAL,
        volatility: float = 0.0,
        avg_daily_volume: float = 0.0
    ) -> ExecutionPlan:
        """
        Create an execution plan.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            quantity: Order quantity
            urgency: Execution urgency
            order_book: Current order book state
            regime: Market regime
            volatility: Current volatility
            avg_daily_volume: Average daily volume
            
        Returns:
            ExecutionPlan
        """
        # Create context
        context = ExecutionContext(
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            urgency=urgency,
            max_participation_rate=0.10,
            max_slippage_bps=20.0,
            time_horizon_minutes=self._get_time_horizon(urgency),
            order_book=order_book,
            regime=regime,
            volatility=volatility,
            avg_daily_volume=avg_daily_volume
        )
        
        # Select algorithm
        algorithm = self.algorithm_selector.select_algorithm(context)
        params = self.algorithm_selector.get_algorithm_parameters(algorithm, context)
        
        # Estimate costs
        costs = self.tca.estimate_costs(
            symbol, quantity, direction, order_book, avg_daily_volume, volatility
        )
        
        # Analyze microstructure if order book available
        if order_book:
            micro = self.microstructure_analyzer.analyze_order_book(order_book)
            execution_price = order_book.best_ask if direction == 'buy' else order_book.best_bid
        else:
            micro = {}
            execution_price = 0.0
        
        # Create plan
        plan = ExecutionPlan(
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            algorithm=algorithm.value,
            urgency=urgency.value,
            expected_slippage=costs.get('total_bps', 0),
            max_participation_rate=context.max_participation_rate,
            time_horizon_minutes=context.time_horizon_minutes,
            limit_price=execution_price if execution_price > 0 else None,
            venue_preferences=['primary'],
            execution_constraints={'max_slippage_bps': context.max_slippage_bps}
        )
        
        return plan
    
    def _get_time_horizon(self, urgency: ExecutionUrgency) -> int:
        """Get time horizon in minutes based on urgency."""
        horizons = {
            ExecutionUrgency.IMMEDIATE: 1,
            ExecutionUrgency.HIGH: 15,
            ExecutionUrgency.MEDIUM: 60,
            ExecutionUrgency.LOW: 240
        }
        return horizons.get(urgency, 60)
    
    def submit_order(self, plan: ExecutionPlan) -> ExecutionOrder:
        """
        Submit an order based on execution plan.
        
        Returns:
            ExecutionOrder
        """
        order = ExecutionOrder(
            symbol=plan.symbol,
            direction=plan.direction,
            order_type=self._algorithm_to_order_type(plan.algorithm),
            algorithm=ExecutionAlgorithm(plan.algorithm),
            quantity=plan.quantity,
            limit_price=plan.limit_price,
            status="submitted"
        )
        
        self.pending_orders[order.id] = order
        self.total_orders += 1
        
        logger.info(f"Submitted order {order.id}: {plan.direction} {plan.quantity} {plan.symbol}")
        return order
    
    def _algorithm_to_order_type(self, algorithm: str) -> OrderType:
        """Convert algorithm to order type."""
        mapping = {
            'direct': OrderType.MARKET,
            'twap': OrderType.TWAP,
            'vwap': OrderType.VWAP,
            'pov': OrderType.POV,
            'is': OrderType.IS,
            'iceberg': OrderType.ICEBERG,
            'passive': OrderType.LIMIT,
            'adaptive': OrderType.LIMIT
        }
        return mapping.get(algorithm, OrderType.LIMIT)
    
    def update_order(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float,
        status: str
    ):
        """Update order status."""
        if order_id not in self.pending_orders:
            return
        
        order = self.pending_orders[order_id]
        order.filled_quantity = filled_quantity
        order.avg_fill_price = avg_fill_price
        order.status = status
        
        if status in ['filled', 'cancelled', 'rejected']:
            order.filled_at = datetime.utcnow()
            self.completed_orders.append(order)
            del self.pending_orders[order_id]
            
            if status == 'filled':
                self.successful_orders += 1
    
    def vote(self, execution_plan: ExecutionPlan) -> CommitteeVote:
        """
        Vote on an execution plan.
        
        Returns:
            CommitteeVote with execution assessment
        """
        issues = []
        
        # Check expected slippage
        if execution_plan.expected_slippage > 30:
            issues.append(f"High expected slippage: {execution_plan.expected_slippage:.1f} bps")
        
        # Check participation rate
        if execution_plan.max_participation_rate > 0.20:
            issues.append(f"High participation rate: {execution_plan.max_participation_rate:.1%}")
        
        # Check time horizon vs urgency
        if execution_plan.urgency == 'immediate' and execution_plan.time_horizon_minutes > 5:
            issues.append("Time horizon inconsistent with urgency")
        
        # Make decision
        if not issues:
            decision = CommitteeDecision.APPROVE
            confidence = 0.9
            rationale = f"Execution plan approved: {execution_plan.algorithm} for {execution_plan.quantity} {execution_plan.symbol}"
        elif len(issues) == 1:
            decision = CommitteeDecision.CONDITIONAL
            confidence = 0.7
            rationale = f"Conditional approval: {issues[0]}"
        else:
            decision = CommitteeDecision.REJECT
            confidence = 0.8
            rationale = f"Rejected: {', '.join(issues)}"
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            conditions=issues if decision == CommitteeDecision.CONDITIONAL else []
        )
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return {
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'success_rate': self.successful_orders / max(1, self.total_orders),
            'pending_orders': len(self.pending_orders),
            'avg_slippage_bps': self.total_slippage_bps / max(1, self.successful_orders),
            'historical_costs': self.tca.get_historical_costs()
        }


# =============================================================================
# EXECUTION LAYER
# =============================================================================

class ExecutionLayer:
    """
    Layer 6: Execution & Microstructure Layer
    
    Responsible for:
    - Optimal order execution
    - Market microstructure analysis
    - Transaction cost analysis
    - Fill quality monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.execution_unit = ExecutionIntelligenceUnit(self.config)
        
        # Layer state
        self.last_execution: Optional[datetime] = None
        self.execution_count = 0
        
        logger.info("ExecutionLayer initialized")
    
    def create_execution_plan(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        urgency: ExecutionUrgency = ExecutionUrgency.MEDIUM,
        order_book: Optional[OrderBookState] = None,
        regime: MarketRegime = MarketRegime.NORMAL,
        volatility: float = 0.0,
        avg_daily_volume: float = 0.0
    ) -> ExecutionPlan:
        """Create execution plan."""
        return self.execution_unit.create_execution_plan(
            symbol, direction, quantity, urgency,
            order_book, regime, volatility, avg_daily_volume
        )
    
    def submit_order(self, plan: ExecutionPlan) -> ExecutionOrder:
        """Submit order."""
        order = self.execution_unit.submit_order(plan)
        self.last_execution = datetime.utcnow()
        self.execution_count += 1
        return order
    
    def update_order(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float,
        status: str
    ):
        """Update order status."""
        self.execution_unit.update_order(order_id, filled_quantity, avg_fill_price, status)
    
    def analyze_execution(
        self,
        order: ExecutionOrder,
        arrival_price: float,
        vwap: float
    ) -> ExecutionReport:
        """Analyze execution quality."""
        return self.execution_unit.tca.analyze_execution(order, arrival_price, vwap)
    
    def estimate_costs(
        self,
        symbol: str,
        quantity: float,
        direction: str,
        order_book: Optional[OrderBookState] = None,
        avg_daily_volume: float = 0.0,
        volatility: float = 0.0
    ) -> Dict[str, float]:
        """Estimate transaction costs."""
        return self.execution_unit.tca.estimate_costs(
            symbol, quantity, direction, order_book, avg_daily_volume, volatility
        )
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get layer state."""
        return {
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count,
            'execution_metrics': self.execution_unit.get_execution_metrics()
        }
