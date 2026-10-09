"""
Smart Order Router & Microstructure-Aware Execution
===================================================
HFT-lite execution performance with intelligent venue selection.

Features:
- Smart Order Router (best venue selection)
- Microstructure-aware execution
- LOB imbalance analysis
- VWAP/TWAP with volatility adjustment
- Adaptive limit/market hybrid orders
- Latency-tuned decision layer
- Toxic flow avoidance
- Liquidity sniping without price impact

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading
import heapq
import uuid

import numpy as np
import pandas as pd

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = auto()
    LIMIT = auto()
    LIMIT_IOC = auto()  # Immediate or Cancel
    LIMIT_FOK = auto()  # Fill or Kill
    ICEBERG = auto()
    TWAP = auto()
    VWAP = auto()
    ADAPTIVE = auto()
    SNIPER = auto()


class ExecutionUrgency(Enum):
    """Execution urgency levels"""
    LOW = auto()      # Can wait for best price
    MEDIUM = auto()   # Balance price and time
    HIGH = auto()     # Need execution soon
    CRITICAL = auto() # Immediate execution required


class VenueType(Enum):
    """Trading venue types"""
    PRIMARY = auto()
    DARK_POOL = auto()
    ECN = auto()
    MARKET_MAKER = auto()
    INTERNALIZED = auto()


@dataclass
class VenueInfo:
    """Information about a trading venue"""
    venue_id: str
    name: str
    venue_type: VenueType
    
    # Costs
    maker_fee: float = 0.0001  # 1 bp
    taker_fee: float = 0.0003  # 3 bp
    
    # Liquidity
    avg_spread: float = 0.0001
    avg_depth: float = 1000000  # USD
    fill_rate: float = 0.95
    
    # Latency
    latency_ms: float = 1.0
    
    # Current state
    current_spread: float = 0.0001
    current_depth: float = 1000000
    queue_position: int = 0
    
    # Performance tracking
    historical_fill_rate: float = 0.95
    avg_slippage: float = 0.0001


@dataclass
class OrderBookLevel:
    """Single level in order book"""
    price: float
    size: float
    order_count: int = 1
    venue_id: str = ""


@dataclass
class OrderBook:
    """Limit Order Book representation"""
    symbol: str
    timestamp: datetime
    
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)
    
    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0
    
    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else float('inf')
    
    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2
    
    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid_price) * 10000 if self.mid_price > 0 else 0
    
    def get_depth(self, side: str, levels: int = 5) -> float:
        """Get total depth for N levels"""
        book = self.bids if side == 'bid' else self.asks
        return sum(level.size for level in book[:levels])
    
    def get_imbalance(self, levels: int = 5) -> float:
        """Calculate order book imbalance (-1 to 1)"""
        bid_depth = self.get_depth('bid', levels)
        ask_depth = self.get_depth('ask', levels)
        total = bid_depth + ask_depth
        if total == 0:
            return 0
        return (bid_depth - ask_depth) / total


@dataclass
class ExecutionPlan:
    """Execution plan for an order"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    total_quantity: float
    
    # Execution details
    order_type: OrderType = OrderType.ADAPTIVE
    urgency: ExecutionUrgency = ExecutionUrgency.MEDIUM
    
    # Venue allocation
    venue_allocations: Dict[str, float] = field(default_factory=dict)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: int = 300  # 5 minutes default
    
    # Constraints
    max_participation_rate: float = 0.1  # 10% of volume
    price_limit: Optional[float] = None
    
    # Child orders
    child_orders: List[Dict] = field(default_factory=list)
    
    # Progress
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    total_cost: float = 0.0


@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: str
    success: bool
    
    # Fill details
    filled_quantity: float = 0.0
    avg_price: float = 0.0
    total_cost: float = 0.0
    
    # Performance
    slippage_bps: float = 0.0
    market_impact_bps: float = 0.0
    execution_time_ms: float = 0.0
    
    # Venue breakdown
    venue_fills: Dict[str, float] = field(default_factory=dict)
    
    # Errors
    error_message: str = ""


class LOBAnalyzer:
    """Limit Order Book analysis for microstructure signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.imbalance_history = deque(maxlen=100)
        self.spread_history = deque(maxlen=100)
        
    def analyze(self, order_book: OrderBook) -> Dict[str, Any]:
        """Comprehensive LOB analysis"""
        
        analysis = {
            'timestamp': order_book.timestamp,
            'mid_price': order_book.mid_price,
            'spread_bps': order_book.spread_bps,
        }
        
        # Imbalance at multiple levels
        for levels in [1, 3, 5, 10]:
            analysis[f'imbalance_{levels}'] = order_book.get_imbalance(levels)
        
        # Depth analysis
        analysis['bid_depth_5'] = order_book.get_depth('bid', 5)
        analysis['ask_depth_5'] = order_book.get_depth('ask', 5)
        analysis['depth_ratio'] = (
            analysis['bid_depth_5'] / analysis['ask_depth_5']
            if analysis['ask_depth_5'] > 0 else 1
        )
        
        # Price pressure
        analysis['price_pressure'] = self._calculate_price_pressure(order_book)
        
        # Toxicity indicators
        analysis['is_toxic'] = self._detect_toxic_flow(order_book)
        
        # Update history
        self.imbalance_history.append(analysis['imbalance_5'])
        self.spread_history.append(order_book.spread_bps)
        
        # Historical analysis
        if len(self.imbalance_history) > 10:
            analysis['imbalance_trend'] = np.mean(list(self.imbalance_history)[-10:])
            analysis['spread_trend'] = np.mean(list(self.spread_history)[-10:])
        
        return analysis
    
    def _calculate_price_pressure(self, order_book: OrderBook) -> float:
        """Calculate price pressure from LOB"""
        
        if not order_book.bids or not order_book.asks:
            return 0
        
        # Weighted average price pressure
        bid_pressure = sum(
            level.size * (order_book.mid_price - level.price)
            for level in order_book.bids[:5]
        )
        ask_pressure = sum(
            level.size * (level.price - order_book.mid_price)
            for level in order_book.asks[:5]
        )
        
        total_pressure = bid_pressure + ask_pressure
        if total_pressure == 0:
            return 0
        
        return (bid_pressure - ask_pressure) / total_pressure
    
    def _detect_toxic_flow(self, order_book: OrderBook) -> bool:
        """Detect toxic order flow"""
        
        # Wide spread indicates potential toxicity
        if order_book.spread_bps > 10:
            return True
        
        # Extreme imbalance
        imbalance = order_book.get_imbalance(5)
        if abs(imbalance) > 0.8:
            return True
        
        # Thin book
        if order_book.get_depth('bid', 5) < 10000 or order_book.get_depth('ask', 5) < 10000:
            return True
        
        return False
    
    def predict_short_term_direction(self, order_book: OrderBook) -> Tuple[float, float]:
        """Predict short-term price direction from LOB"""
        
        # Imbalance-based prediction
        imbalance = order_book.get_imbalance(5)
        
        # Depth-weighted prediction
        bid_depth = order_book.get_depth('bid', 10)
        ask_depth = order_book.get_depth('ask', 10)
        depth_signal = (bid_depth - ask_depth) / (bid_depth + ask_depth + 1)
        
        # Combined signal
        direction = 0.6 * imbalance + 0.4 * depth_signal
        confidence = min(abs(direction), 1.0)
        
        return direction, confidence


class VenueSelector:
    """Intelligent venue selection"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.venues: Dict[str, VenueInfo] = {}
        self.venue_performance: Dict[str, List[float]] = {}
        
        # Initialize default venues
        self._initialize_default_venues()
        
    def _initialize_default_venues(self):
        """Initialize default trading venues"""
        
        default_venues = [
            VenueInfo(
                venue_id='primary',
                name='Primary Exchange',
                venue_type=VenueType.PRIMARY,
                maker_fee=0.0001,
                taker_fee=0.0003,
                avg_spread=0.0001,
                avg_depth=5000000,
                latency_ms=0.5
            ),
            VenueInfo(
                venue_id='dark_pool_1',
                name='Dark Pool Alpha',
                venue_type=VenueType.DARK_POOL,
                maker_fee=0.0,
                taker_fee=0.0001,
                avg_spread=0.0,
                avg_depth=2000000,
                fill_rate=0.3,
                latency_ms=2.0
            ),
            VenueInfo(
                venue_id='ecn_1',
                name='ECN Network',
                venue_type=VenueType.ECN,
                maker_fee=-0.0001,  # Rebate
                taker_fee=0.0003,
                avg_spread=0.00015,
                avg_depth=3000000,
                latency_ms=1.0
            ),
            VenueInfo(
                venue_id='mm_1',
                name='Market Maker',
                venue_type=VenueType.MARKET_MAKER,
                maker_fee=0.0,
                taker_fee=0.0002,
                avg_spread=0.0002,
                avg_depth=10000000,
                fill_rate=0.99,
                latency_ms=0.3
            )
        ]
        
        for venue in default_venues:
            self.venues[venue.venue_id] = venue
            self.venue_performance[venue.venue_id] = []
    
    def update_venue_state(
        self,
        venue_id: str,
        spread: float,
        depth: float,
        queue_position: int = 0
    ):
        """Update real-time venue state"""
        
        if venue_id in self.venues:
            self.venues[venue_id].current_spread = spread
            self.venues[venue_id].current_depth = depth
            self.venues[venue_id].queue_position = queue_position
    
    def select_best_venues(
        self,
        order_size: float,
        side: str,
        urgency: ExecutionUrgency,
        max_venues: int = 3
    ) -> List[Tuple[str, float]]:
        """Select best venues and allocate order"""
        
        venue_scores = []
        
        for venue_id, venue in self.venues.items():
            score = self._calculate_venue_score(venue, order_size, side, urgency)
            venue_scores.append((venue_id, score, venue))
        
        # Sort by score
        venue_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate to top venues
        allocations = []
        remaining = order_size
        
        for venue_id, score, venue in venue_scores[:max_venues]:
            if remaining <= 0:
                break
            
            # Allocate based on depth and score
            max_allocation = min(
                remaining,
                venue.current_depth * 0.1,  # Max 10% of depth
                order_size * 0.5  # Max 50% to single venue
            )
            
            if max_allocation > 0:
                allocations.append((venue_id, max_allocation))
                remaining -= max_allocation
        
        # Distribute remaining to primary
        if remaining > 0 and allocations:
            allocations[0] = (allocations[0][0], allocations[0][1] + remaining)
        
        return allocations
    
    def _calculate_venue_score(
        self,
        venue: VenueInfo,
        order_size: float,
        side: str,
        urgency: ExecutionUrgency
    ) -> float:
        """Calculate venue score for order"""
        
        # Base score from fill rate
        score = venue.fill_rate * 100
        
        # Cost adjustment
        expected_fee = venue.taker_fee if urgency == ExecutionUrgency.CRITICAL else venue.maker_fee
        score -= expected_fee * 10000  # Convert to bps impact
        
        # Spread adjustment
        score -= venue.current_spread * 5000
        
        # Depth adjustment
        depth_ratio = min(venue.current_depth / order_size, 10) / 10
        score += depth_ratio * 20
        
        # Latency adjustment (more important for high urgency)
        if urgency in [ExecutionUrgency.HIGH, ExecutionUrgency.CRITICAL]:
            score -= venue.latency_ms * 5
        
        # Dark pool bonus for large orders
        if venue.venue_type == VenueType.DARK_POOL and order_size > 100000:
            score += 10
        
        # Historical performance
        if venue.venue_id in self.venue_performance:
            perf = self.venue_performance[venue.venue_id]
            if perf:
                score += np.mean(perf[-20:]) * 10
        
        return score
    
    def record_fill(self, venue_id: str, slippage_bps: float):
        """Record fill performance for venue"""
        
        if venue_id in self.venue_performance:
            # Score: 1 for no slippage, decreasing with slippage
            score = max(0, 1 - slippage_bps / 10)
            self.venue_performance[venue_id].append(score)
            
            # Keep last 100 fills
            if len(self.venue_performance[venue_id]) > 100:
                self.venue_performance[venue_id].pop(0)


class ToxicFlowDetector:
    """Detect and avoid toxic order flow"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.flow_history = deque(maxlen=1000)
        self.toxic_patterns = []
        
    def analyze_flow(
        self,
        trades: List[Dict],
        order_book: OrderBook
    ) -> Dict[str, Any]:
        """Analyze order flow for toxicity"""
        
        analysis = {
            'is_toxic': False,
            'toxicity_score': 0.0,
            'reasons': []
        }
        
        if not trades:
            return analysis
        
        # Calculate VPIN (Volume-synchronized Probability of Informed Trading)
        vpin = self._calculate_vpin(trades)
        analysis['vpin'] = vpin
        
        if vpin > 0.7:
            analysis['is_toxic'] = True
            analysis['reasons'].append(f'High VPIN: {vpin:.2f}')
        
        # Detect aggressive orders
        aggression = self._detect_aggression(trades)
        analysis['aggression'] = aggression
        
        if aggression > 0.8:
            analysis['is_toxic'] = True
            analysis['reasons'].append(f'High aggression: {aggression:.2f}')
        
        # Detect momentum ignition
        if self._detect_momentum_ignition(trades):
            analysis['is_toxic'] = True
            analysis['reasons'].append('Momentum ignition detected')
        
        # Detect spoofing
        if self._detect_spoofing(order_book):
            analysis['is_toxic'] = True
            analysis['reasons'].append('Potential spoofing detected')
        
        # Calculate overall toxicity score
        analysis['toxicity_score'] = (
            0.4 * vpin +
            0.3 * aggression +
            0.3 * (1 if analysis['is_toxic'] else 0)
        )
        
        return analysis
    
    def _calculate_vpin(self, trades: List[Dict]) -> float:
        """Calculate VPIN metric"""
        
        if len(trades) < 10:
            return 0.5
        
        # Classify trades as buy or sell
        buy_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'buy')
        sell_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return 0.5
        
        # VPIN = |Buy - Sell| / Total
        vpin = abs(buy_volume - sell_volume) / total_volume
        
        return vpin
    
    def _detect_aggression(self, trades: List[Dict]) -> float:
        """Detect aggressive trading"""
        
        if not trades:
            return 0.5
        
        # Count market orders vs limit orders
        market_orders = sum(1 for t in trades if t.get('order_type') == 'market')
        total_orders = len(trades)
        
        return market_orders / total_orders if total_orders > 0 else 0.5
    
    def _detect_momentum_ignition(self, trades: List[Dict]) -> bool:
        """Detect momentum ignition patterns"""
        
        if len(trades) < 20:
            return False
        
        # Look for sudden burst of same-direction trades
        recent_trades = trades[-20:]
        buy_count = sum(1 for t in recent_trades if t.get('side') == 'buy')
        sell_count = len(recent_trades) - buy_count
        
        # Extreme imbalance
        if buy_count > 18 or sell_count > 18:
            return True
        
        return False
    
    def _detect_spoofing(self, order_book: OrderBook) -> bool:
        """Detect potential spoofing"""
        
        if not order_book.bids or not order_book.asks:
            return False
        
        # Large orders far from mid price
        mid = order_book.mid_price
        
        for level in order_book.bids[3:10]:
            if level.size > order_book.bids[0].size * 5:
                distance = (mid - level.price) / mid
                if distance > 0.001:  # More than 10 bps away
                    return True
        
        for level in order_book.asks[3:10]:
            if level.size > order_book.asks[0].size * 5:
                distance = (level.price - mid) / mid
                if distance > 0.001:
                    return True
        
        return False
    
    def should_avoid_trading(self, toxicity_analysis: Dict) -> Tuple[bool, str]:
        """Determine if trading should be avoided"""
        
        if toxicity_analysis['toxicity_score'] > 0.7:
            return True, "High toxicity score"
        
        if toxicity_analysis.get('vpin', 0) > 0.8:
            return True, "Extreme VPIN"
        
        if 'Momentum ignition' in str(toxicity_analysis.get('reasons', [])):
            return True, "Momentum ignition"
        
        return False, ""


class AdaptiveExecutor:
    """Adaptive order execution with multiple algorithms"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lob_analyzer = LOBAnalyzer(config)
        self.venue_selector = VenueSelector(config)
        self.toxic_detector = ToxicFlowDetector(config)
        
    async def execute_twap(
        self,
        plan: ExecutionPlan,
        order_book: OrderBook,
        get_current_price: Callable
    ) -> ExecutionResult:
        """Time-Weighted Average Price execution"""
        
        result = ExecutionResult(order_id=plan.order_id, success=False)
        
        # Calculate slice size
        num_slices = max(1, plan.duration_seconds // 30)  # 30-second slices
        slice_size = plan.total_quantity / num_slices
        
        filled = 0
        total_cost = 0
        
        for i in range(num_slices):
            if filled >= plan.total_quantity:
                break
            
            # Get current price
            current_price = get_current_price()
            
            # Check price limit
            if plan.price_limit:
                if plan.side == 'buy' and current_price > plan.price_limit:
                    continue
                if plan.side == 'sell' and current_price < plan.price_limit:
                    continue
            
            # Execute slice
            slice_qty = min(slice_size, plan.total_quantity - filled)
            
            # Simulate fill
            fill_price = current_price * (1 + 0.0001 if plan.side == 'buy' else 1 - 0.0001)
            
            filled += slice_qty
            total_cost += slice_qty * fill_price
            
            # Wait for next slice
            if i < num_slices - 1:
                await asyncio.sleep(30)
        
        result.success = filled > 0
        result.filled_quantity = filled
        result.avg_price = total_cost / filled if filled > 0 else 0
        result.total_cost = total_cost
        
        return result
    
    async def execute_vwap(
        self,
        plan: ExecutionPlan,
        order_book: OrderBook,
        volume_profile: List[float],
        get_current_price: Callable
    ) -> ExecutionResult:
        """Volume-Weighted Average Price execution"""
        
        result = ExecutionResult(order_id=plan.order_id, success=False)
        
        # Normalize volume profile
        total_volume = sum(volume_profile) or 1
        volume_weights = [v / total_volume for v in volume_profile]
        
        filled = 0
        total_cost = 0
        
        for i, weight in enumerate(volume_weights):
            if filled >= plan.total_quantity:
                break
            
            # Calculate slice based on volume weight
            slice_size = plan.total_quantity * weight
            
            # Adjust for participation rate
            slice_size = min(slice_size, plan.max_participation_rate * volume_profile[i])
            
            # Get current price
            current_price = get_current_price()
            
            # Execute slice with volatility adjustment
            volatility = self._estimate_volatility(order_book)
            adjusted_slice = slice_size * (1 - volatility)  # Reduce in high vol
            
            # Simulate fill
            fill_price = current_price * (1 + 0.0001 if plan.side == 'buy' else 1 - 0.0001)
            
            filled += adjusted_slice
            total_cost += adjusted_slice * fill_price
            
            await asyncio.sleep(1)  # Simulate time passing
        
        result.success = filled > 0
        result.filled_quantity = filled
        result.avg_price = total_cost / filled if filled > 0 else 0
        result.total_cost = total_cost
        
        return result
    
    async def execute_adaptive(
        self,
        plan: ExecutionPlan,
        order_book: OrderBook,
        trades: List[Dict],
        get_current_price: Callable
    ) -> ExecutionResult:
        """Adaptive execution combining limit and market orders"""
        
        result = ExecutionResult(order_id=plan.order_id, success=False)
        
        # Analyze current conditions
        lob_analysis = self.lob_analyzer.analyze(order_book)
        toxic_analysis = self.toxic_detector.analyze_flow(trades, order_book)
        
        # Check if should avoid trading
        should_avoid, reason = self.toxic_detector.should_avoid_trading(toxic_analysis)
        if should_avoid:
            result.error_message = f"Avoiding trade: {reason}"
            return result
        
        # Select venues
        venue_allocations = self.venue_selector.select_best_venues(
            plan.total_quantity,
            plan.side,
            plan.urgency
        )
        
        filled = 0
        total_cost = 0
        
        for venue_id, allocation in venue_allocations:
            if filled >= plan.total_quantity:
                break
            
            # Determine order type based on conditions
            if plan.urgency == ExecutionUrgency.CRITICAL:
                order_type = OrderType.MARKET
            elif lob_analysis.get('is_toxic', False):
                order_type = OrderType.LIMIT  # Passive in toxic flow
            elif abs(lob_analysis.get('imbalance_5', 0)) > 0.5:
                # Use imbalance to our advantage
                if (plan.side == 'buy' and lob_analysis['imbalance_5'] < 0) or \
                   (plan.side == 'sell' and lob_analysis['imbalance_5'] > 0):
                    order_type = OrderType.LIMIT  # Favorable imbalance, be patient
                else:
                    order_type = OrderType.LIMIT_IOC  # Unfavorable, be quick
            else:
                order_type = OrderType.ADAPTIVE
            
            # Execute on venue
            current_price = get_current_price()
            
            # Calculate limit price
            if order_type in [OrderType.LIMIT, OrderType.LIMIT_IOC]:
                if plan.side == 'buy':
                    limit_price = order_book.best_bid + order_book.spread * 0.3
                else:
                    limit_price = order_book.best_ask - order_book.spread * 0.3
            else:
                limit_price = current_price
            
            # Simulate execution
            fill_qty = min(allocation, plan.total_quantity - filled)
            
            # Slippage based on order type
            if order_type == OrderType.MARKET:
                slippage = 0.0003
            elif order_type == OrderType.LIMIT_IOC:
                slippage = 0.0001
            else:
                slippage = 0.00005
            
            fill_price = limit_price * (1 + slippage if plan.side == 'buy' else 1 - slippage)
            
            filled += fill_qty
            total_cost += fill_qty * fill_price
            result.venue_fills[venue_id] = fill_qty
            
            # Record performance
            self.venue_selector.record_fill(venue_id, slippage * 10000)
        
        result.success = filled > 0
        result.filled_quantity = filled
        result.avg_price = total_cost / filled if filled > 0 else 0
        result.total_cost = total_cost
        result.slippage_bps = (result.avg_price / get_current_price() - 1) * 10000 if plan.side == 'buy' else (1 - result.avg_price / get_current_price()) * 10000
        
        return result
    
    async def execute_sniper(
        self,
        plan: ExecutionPlan,
        order_book: OrderBook,
        get_current_price: Callable
    ) -> ExecutionResult:
        """Snipe liquidity without moving price"""
        
        result = ExecutionResult(order_id=plan.order_id, success=False)
        
        # Wait for favorable conditions
        max_attempts = 100
        filled = 0
        total_cost = 0
        
        for attempt in range(max_attempts):
            if filled >= plan.total_quantity:
                break
            
            # Analyze LOB
            lob_analysis = self.lob_analyzer.analyze(order_book)
            
            # Look for favorable imbalance
            imbalance = lob_analysis.get('imbalance_5', 0)
            
            favorable = (
                (plan.side == 'buy' and imbalance < -0.3) or
                (plan.side == 'sell' and imbalance > 0.3)
            )
            
            if favorable:
                # Snipe available liquidity
                if plan.side == 'buy':
                    available = order_book.asks[0].size if order_book.asks else 0
                    price = order_book.best_ask
                else:
                    available = order_book.bids[0].size if order_book.bids else 0
                    price = order_book.best_bid
                
                # Take only what we need, don't move price
                take_size = min(
                    available * 0.3,  # Max 30% of top level
                    plan.total_quantity - filled
                )
                
                if take_size > 0:
                    filled += take_size
                    total_cost += take_size * price
            
            await asyncio.sleep(0.1)  # 100ms between attempts
        
        result.success = filled > 0
        result.filled_quantity = filled
        result.avg_price = total_cost / filled if filled > 0 else 0
        result.total_cost = total_cost
        
        return result
    
    async def execute_iceberg(
        self,
        plan: ExecutionPlan,
        order_book: OrderBook,
        visible_size: float,
        get_current_price: Callable
    ) -> ExecutionResult:
        """Iceberg order execution"""
        
        result = ExecutionResult(order_id=plan.order_id, success=False)
        
        filled = 0
        total_cost = 0
        
        while filled < plan.total_quantity:
            # Show only visible portion
            show_size = min(visible_size, plan.total_quantity - filled)
            
            # Place limit order
            if plan.side == 'buy':
                limit_price = order_book.best_bid
            else:
                limit_price = order_book.best_ask
            
            # Simulate partial fill
            fill_rate = np.random.uniform(0.3, 0.8)
            fill_qty = show_size * fill_rate
            
            filled += fill_qty
            total_cost += fill_qty * limit_price
            
            await asyncio.sleep(1)  # Wait before next slice
        
        result.success = filled > 0
        result.filled_quantity = filled
        result.avg_price = total_cost / filled if filled > 0 else 0
        result.total_cost = total_cost
        
        return result
    
    def _estimate_volatility(self, order_book: OrderBook) -> float:
        """Estimate current volatility from spread"""
        return min(order_book.spread_bps / 100, 0.1)


class LatencyOptimizer:
    """Latency-tuned decision layer"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.latency_cache: Dict[str, float] = {}
        self.decision_cache: Dict[str, Any] = {}
        self.cache_ttl_ms = self.config.get('cache_ttl_ms', 100)
        
    def get_cached_decision(self, key: str) -> Optional[Any]:
        """Get cached decision if still valid"""
        
        if key in self.decision_cache:
            cached = self.decision_cache[key]
            age_ms = (time.time() - cached['timestamp']) * 1000
            if age_ms < self.cache_ttl_ms:
                return cached['decision']
        
        return None
    
    def cache_decision(self, key: str, decision: Any):
        """Cache a decision"""
        self.decision_cache[key] = {
            'decision': decision,
            'timestamp': time.time()
        }
    
    def measure_latency(self, operation: str, start_time: float):
        """Record operation latency"""
        latency = (time.time() - start_time) * 1000
        
        if operation not in self.latency_cache:
            self.latency_cache[operation] = []
        
        self.latency_cache[operation].append(latency)
        
        # Keep last 100 measurements
        if len(self.latency_cache[operation]) > 100:
            self.latency_cache[operation].pop(0)
    
    def get_avg_latency(self, operation: str) -> float:
        """Get average latency for operation"""
        if operation in self.latency_cache and self.latency_cache[operation]:
            return np.mean(self.latency_cache[operation])
        return 0
    
    def optimize_path(self, venues: List[str]) -> List[str]:
        """Optimize venue order by latency"""
        
        venue_latencies = []
        for venue in venues:
            latency = self.get_avg_latency(f'venue_{venue}')
            venue_latencies.append((venue, latency))
        
        # Sort by latency
        venue_latencies.sort(key=lambda x: x[1])
        
        return [v[0] for v in venue_latencies]


class SmartOrderRouter:
    """
    Complete Smart Order Router with microstructure-aware execution.
    
    Features:
    - Best venue selection based on spread, liquidity, depth, volatility
    - Microstructure-aware execution avoiding toxic flow
    - LOB imbalance analysis
    - VWAP/TWAP with volatility adjustment
    - Adaptive limit/market hybrid orders
    - Latency-tuned decision layer
    - Liquidity sniping without price impact
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.lob_analyzer = LOBAnalyzer(config)
        self.venue_selector = VenueSelector(config)
        self.toxic_detector = ToxicFlowDetector(config)
        self.executor = AdaptiveExecutor(config)
        self.latency_optimizer = LatencyOptimizer(config)
        
        # State
        self.active_orders: Dict[str, ExecutionPlan] = {}
        self.completed_orders: List[ExecutionResult] = []
        
        logger.info("SmartOrderRouter initialized")
    
    async def route_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_book: OrderBook,
        trades: List[Dict] = None,
        urgency: ExecutionUrgency = ExecutionUrgency.MEDIUM,
        algorithm: OrderType = OrderType.ADAPTIVE,
        price_limit: Optional[float] = None,
        duration_seconds: int = 300
    ) -> ExecutionResult:
        """Route and execute order"""
        
        start_time = time.time()
        
        # Create execution plan
        plan = ExecutionPlan(
            order_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            order_type=algorithm,
            urgency=urgency,
            price_limit=price_limit,
            duration_seconds=duration_seconds
        )
        
        # Store active order
        self.active_orders[plan.order_id] = plan
        
        # Analyze conditions
        lob_analysis = self.lob_analyzer.analyze(order_book)
        toxic_analysis = self.toxic_detector.analyze_flow(trades or [], order_book)
        
        # Check if should avoid trading
        should_avoid, reason = self.toxic_detector.should_avoid_trading(toxic_analysis)
        if should_avoid and urgency != ExecutionUrgency.CRITICAL:
            result = ExecutionResult(
                order_id=plan.order_id,
                success=False,
                error_message=f"Trade avoided: {reason}"
            )
            return result
        
        # Select venues
        venue_allocations = self.venue_selector.select_best_venues(
            quantity, side, urgency
        )
        plan.venue_allocations = dict(venue_allocations)
        
        # Get price function
        def get_current_price():
            return order_book.mid_price
        
        # Execute based on algorithm
        if algorithm == OrderType.TWAP:
            result = await self.executor.execute_twap(plan, order_book, get_current_price)
        elif algorithm == OrderType.VWAP:
            # Generate simple volume profile
            volume_profile = [1.0] * 10  # Uniform for simplicity
            result = await self.executor.execute_vwap(plan, order_book, volume_profile, get_current_price)
        elif algorithm == OrderType.SNIPER:
            result = await self.executor.execute_sniper(plan, order_book, get_current_price)
        elif algorithm == OrderType.ICEBERG:
            visible_size = quantity * 0.1  # Show 10%
            result = await self.executor.execute_iceberg(plan, order_book, visible_size, get_current_price)
        else:
            result = await self.executor.execute_adaptive(plan, order_book, trades or [], get_current_price)
        
        # Record latency
        self.latency_optimizer.measure_latency('route_order', start_time)
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        # Move to completed
        del self.active_orders[plan.order_id]
        self.completed_orders.append(result)
        
        return result
    
    def get_execution_recommendation(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_book: OrderBook,
        trades: List[Dict] = None
    ) -> Dict[str, Any]:
        """Get execution recommendation without executing"""
        
        # Analyze conditions
        lob_analysis = self.lob_analyzer.analyze(order_book)
        toxic_analysis = self.toxic_detector.analyze_flow(trades or [], order_book)
        
        # Determine recommended algorithm
        if toxic_analysis['toxicity_score'] > 0.5:
            recommended_algo = OrderType.SNIPER
            reason = "High toxicity - use sniper to minimize impact"
        elif abs(lob_analysis.get('imbalance_5', 0)) > 0.6:
            if (side == 'buy' and lob_analysis['imbalance_5'] < 0) or \
               (side == 'sell' and lob_analysis['imbalance_5'] > 0):
                recommended_algo = OrderType.LIMIT
                reason = "Favorable imbalance - use passive limit orders"
            else:
                recommended_algo = OrderType.ADAPTIVE
                reason = "Unfavorable imbalance - use adaptive execution"
        elif quantity > 100000:
            recommended_algo = OrderType.ICEBERG
            reason = "Large order - use iceberg to hide size"
        else:
            recommended_algo = OrderType.ADAPTIVE
            reason = "Normal conditions - use adaptive execution"
        
        # Get venue recommendations
        venue_allocations = self.venue_selector.select_best_venues(
            quantity, side, ExecutionUrgency.MEDIUM
        )
        
        return {
            'recommended_algorithm': recommended_algo.name,
            'reason': reason,
            'venue_allocations': dict(venue_allocations),
            'lob_analysis': lob_analysis,
            'toxicity_score': toxic_analysis['toxicity_score'],
            'estimated_slippage_bps': self._estimate_slippage(quantity, order_book),
            'should_trade': not toxic_analysis['is_toxic']
        }
    
    def _estimate_slippage(self, quantity: float, order_book: OrderBook) -> float:
        """Estimate expected slippage"""
        
        # Simple model: slippage proportional to order size relative to depth
        depth = order_book.get_depth('bid', 10) + order_book.get_depth('ask', 10)
        if depth == 0:
            return 10  # High slippage if no depth
        
        impact = (quantity / depth) * 100  # bps
        spread_cost = order_book.spread_bps / 2
        
        return impact + spread_cost
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get execution performance statistics"""
        
        if not self.completed_orders:
            return {'total_orders': 0}
        
        slippages = [r.slippage_bps for r in self.completed_orders if r.success]
        latencies = [r.execution_time_ms for r in self.completed_orders]
        
        return {
            'total_orders': len(self.completed_orders),
            'success_rate': sum(1 for r in self.completed_orders if r.success) / len(self.completed_orders),
            'avg_slippage_bps': np.mean(slippages) if slippages else 0,
            'max_slippage_bps': max(slippages) if slippages else 0,
            'avg_latency_ms': np.mean(latencies) if latencies else 0,
            'total_volume': sum(r.filled_quantity for r in self.completed_orders)
        }


# Factory function
def create_router(config: Optional[Dict] = None) -> SmartOrderRouter:
    """Create and return a SmartOrderRouter instance"""
    return SmartOrderRouter(config)
