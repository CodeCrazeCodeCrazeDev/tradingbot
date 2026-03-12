"""
Advanced Execution Algorithms Module
=====================================

Comprehensive execution algorithms:
- Smart Order Router (SOR) with multi-venue execution
- Iceberg Orders & Stealth Execution
- Dark Pool Liquidity Mining
- VWAP/TWAP Execution
- Order Flow Toxicity Detection (VPIN)
- Latency Arbitrage Defense
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import random
import math
import numpy
import pandas

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    LIMIT_IOC = "limit_ioc"
    LIMIT_FOK = "limit_fok"
    ICEBERG = "iceberg"
    PEG = "peg"
    MIDPOINT = "midpoint"


class VenueType(Enum):
    """Venue types"""
    PRIMARY_EXCHANGE = "primary_exchange"
    SECONDARY_EXCHANGE = "secondary_exchange"
    DARK_POOL = "dark_pool"
    ECN = "ecn"
    INTERNALIZER = "internalizer"


class ToxicityLevel(Enum):
    """Order flow toxicity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class Venue:
    """Trading venue"""
    name: str
    venue_type: VenueType
    spread: float  # Average spread in bps
    depth: float  # Average depth at best
    fill_rate: float  # Historical fill rate
    latency_ms: float  # Latency in milliseconds
    fee_maker: float  # Maker fee in bps
    fee_taker: float  # Taker fee in bps
    
    @property
    def score(self) -> float:
        """Calculate venue score"""
        return (
            (1 / (self.spread + 1)) * 0.30 +
            self.depth / 10000 * 0.25 +
            self.fill_rate * 0.20 +
            (1 / (self.latency_ms + 1)) * 0.15 +
            (1 / (self.fee_taker + 1)) * 0.10
        )


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    time_in_force: str = "day"
    venue: Optional[str] = None
    
    # Execution tracking
    filled_quantity: float = 0
    avg_fill_price: float = 0
    status: str = "pending"


@dataclass
class Fill:
    """Order fill"""
    order_id: str
    fill_id: str
    timestamp: datetime
    quantity: float
    price: float
    venue: str
    fee: float


@dataclass
class ExecutionQuality:
    """Execution quality metrics"""
    order_id: str
    arrival_price: float
    vwap: float
    twap: float
    avg_fill_price: float
    slippage_bps: float
    implementation_shortfall: float
    market_impact: float
    fill_rate: float
    execution_time_seconds: float


@dataclass
class VPINMetrics:
    """VPIN toxicity metrics"""
    timestamp: datetime
    vpin: float
    toxicity_level: ToxicityLevel
    buy_volume: float
    sell_volume: float
    total_volume: float
    recommendation: str


class SmartOrderRouter:
    """
    Smart Order Router (SOR)
    
    Features:
    - Multi-venue execution
    - Latency-aware routing
    - Liquidity discovery
    - Impact minimization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize venues
        self.venues = self._initialize_venues()
        
        # Routing weights
        self.spread_weight = self.config.get('spread_weight', 0.30)
        self.depth_weight = self.config.get('depth_weight', 0.25)
        self.fill_rate_weight = self.config.get('fill_rate_weight', 0.20)
        self.latency_weight = self.config.get('latency_weight', 0.15)
        self.fee_weight = self.config.get('fee_weight', 0.10)
        
        # Execution history
        self.execution_history: deque = deque(maxlen=1000)
    
    def _initialize_venues(self) -> Dict[str, Venue]:
        """Initialize trading venues"""
        return {
            'NYSE': Venue(
                name='NYSE',
                venue_type=VenueType.PRIMARY_EXCHANGE,
                spread=1.0,
                depth=5000,
                fill_rate=0.85,
                latency_ms=0.5,
                fee_maker=-0.2,  # Rebate
                fee_taker=0.3,
            ),
            'NASDAQ': Venue(
                name='NASDAQ',
                venue_type=VenueType.PRIMARY_EXCHANGE,
                spread=0.8,
                depth=4000,
                fill_rate=0.88,
                latency_ms=0.3,
                fee_maker=-0.25,
                fee_taker=0.3,
            ),
            'BATS': Venue(
                name='BATS',
                venue_type=VenueType.SECONDARY_EXCHANGE,
                spread=0.9,
                depth=3000,
                fill_rate=0.82,
                latency_ms=0.4,
                fee_maker=-0.3,
                fee_taker=0.25,
            ),
            'IEX': Venue(
                name='IEX',
                venue_type=VenueType.SECONDARY_EXCHANGE,
                spread=1.2,
                depth=2000,
                fill_rate=0.75,
                latency_ms=0.35,  # Speed bump
                fee_maker=0.0,
                fee_taker=0.09,
            ),
            'SIGMA_X': Venue(
                name='SIGMA_X',
                venue_type=VenueType.DARK_POOL,
                spread=0.0,  # Midpoint
                depth=10000,
                fill_rate=0.40,
                latency_ms=1.0,
                fee_maker=0.1,
                fee_taker=0.1,
            ),
            'CROSSFINDER': Venue(
                name='CROSSFINDER',
                venue_type=VenueType.DARK_POOL,
                spread=0.0,
                depth=8000,
                fill_rate=0.35,
                latency_ms=1.2,
                fee_maker=0.15,
                fee_taker=0.15,
            ),
        }
    
    def calculate_venue_scores(self, order: Order) -> Dict[str, float]:
        """Calculate scores for each venue"""
        scores = {}
        
        for name, venue in self.venues.items():
            # Base score
            score = venue.score
            
            # Adjust for order characteristics
            if order.quantity > venue.depth:
                # Large order penalty
                score *= 0.8
            
            if order.order_type == OrderType.MARKET:
                # Market orders prefer low latency
                score *= (1 / (venue.latency_ms + 0.1))
            
            scores[name] = score
        
        return scores
    
    def route_order(self, order: Order) -> List[Tuple[str, float]]:
        """
        Route order across venues
        
        Args:
            order: Order to route
            
        Returns:
            List of (venue, quantity) tuples
        """
        scores = self.calculate_venue_scores(order)
        
        # Normalize scores
        total_score = sum(scores.values())
        if total_score == 0:
            return [(list(self.venues.keys())[0], order.quantity)]
        
        normalized = {k: v / total_score for k, v in scores.items()}
        
        # Allocate quantity
        routing = []
        remaining = order.quantity
        
        # Sort by score descending
        sorted_venues = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        
        for venue_name, weight in sorted_venues:
            if remaining <= 0:
                break
            
            venue = self.venues[venue_name]
            
            # Allocate based on weight and depth
            allocation = min(
                remaining * weight * 2,  # Allow over-allocation to top venues
                venue.depth * 0.5,  # Don't exceed 50% of depth
                remaining,
            )
            
            if allocation > 0:
                routing.append((venue_name, allocation))
                remaining -= allocation
        
        # If remaining, add to best venue
        if remaining > 0 and routing:
            venue_name, qty = routing[0]
            routing[0] = (venue_name, qty + remaining)
        
        return routing
    
    def execute_order(self, order: Order) -> List[Fill]:
        """
        Execute order across venues
        
        Args:
            order: Order to execute
            
        Returns:
            List of fills
        """
        routing = self.route_order(order)
        fills = []
        
        for venue_name, quantity in routing:
            venue = self.venues[venue_name]
            
            # Simulate fill
            fill_rate = venue.fill_rate * random.uniform(0.9, 1.1)
            filled_qty = quantity * min(fill_rate, 1.0)
            
            if filled_qty > 0:
                # Calculate fill price with slippage
                slippage = venue.spread / 10000 * random.uniform(0.5, 1.5)
                if order.side == 'buy':
                    fill_price = order.price * (1 + slippage) if order.price else 0
                else:
                    fill_price = order.price * (1 - slippage) if order.price else 0
                
                fill = Fill(
                    order_id=order.order_id,
                    fill_id=f"{order.order_id}_{venue_name}_{len(fills)}",
                    timestamp=datetime.now(),
                    quantity=filled_qty,
                    price=fill_price,
                    venue=venue_name,
                    fee=filled_qty * fill_price * venue.fee_taker / 10000,
                )
                fills.append(fill)
        
        return fills


class IcebergExecutor:
    """
    Iceberg Order Executor
    
    Hides true order size by showing only a portion at a time
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Iceberg parameters
        self.display_pct_min = self.config.get('display_pct_min', 0.10)
        self.display_pct_max = self.config.get('display_pct_max', 0.20)
        self.replenish_delay_min = self.config.get('replenish_delay_min', 0.5)
        self.replenish_delay_max = self.config.get('replenish_delay_max', 2.0)
        
        # Active icebergs
        self.active_icebergs: Dict[str, Dict[str, Any]] = {}
    
    def create_iceberg(self, order: Order, avg_volume_at_level: float) -> Dict[str, Any]:
        """
        Create iceberg order
        
        Args:
            order: Full order
            avg_volume_at_level: Average volume at price level
            
        Returns:
            Iceberg configuration
        """
        # Determine display size
        display_pct = random.uniform(self.display_pct_min, self.display_pct_max)
        display_size = order.quantity * display_pct
        
        # Ensure display size is reasonable relative to market
        if display_size > avg_volume_at_level * 2:
            display_size = avg_volume_at_level * random.uniform(0.5, 1.0)
        
        iceberg = {
            'order_id': order.order_id,
            'total_quantity': order.quantity,
            'display_size': display_size,
            'hidden_size': order.quantity - display_size,
            'filled_quantity': 0,
            'remaining_quantity': order.quantity,
            'replenish_count': 0,
            'created_at': datetime.now(),
        }
        
        self.active_icebergs[order.order_id] = iceberg
        
        return iceberg
    
    def on_fill(self, order_id: str, filled_quantity: float) -> Optional[Dict[str, Any]]:
        """
        Handle fill and potentially replenish
        
        Args:
            order_id: Order ID
            filled_quantity: Quantity filled
            
        Returns:
            Replenishment info if needed
        """
        if order_id not in self.active_icebergs:
            return None
        
        iceberg = self.active_icebergs[order_id]
        
        iceberg['filled_quantity'] += filled_quantity
        iceberg['remaining_quantity'] -= filled_quantity
        
        # Check if need to replenish
        if iceberg['remaining_quantity'] > 0:
            # Random delay before replenishment
            delay = random.uniform(self.replenish_delay_min, self.replenish_delay_max)
            
            # New display size (randomize to avoid detection)
            new_display = min(
                iceberg['remaining_quantity'],
                iceberg['display_size'] * random.uniform(0.8, 1.2),
            )
            
            iceberg['replenish_count'] += 1
            
            return {
                'action': 'replenish',
                'delay_seconds': delay,
                'new_display_size': new_display,
                'remaining': iceberg['remaining_quantity'],
            }
        else:
            # Order complete
            del self.active_icebergs[order_id]
            return {
                'action': 'complete',
                'total_filled': iceberg['filled_quantity'],
                'replenish_count': iceberg['replenish_count'],
            }


class DarkPoolMiner:
    """
    Dark Pool Liquidity Mining
    
    Strategies:
    - Ping orders to detect hidden liquidity
    - Midpoint pegging
    - Multi-venue aggregation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Dark pool universe
        self.dark_pools = {
            'SIGMA_X': {'fill_rate': 0.40, 'adverse_selection': 0.15, 'fee': 0.10},
            'CROSSFINDER': {'fill_rate': 0.35, 'adverse_selection': 0.18, 'fee': 0.15},
            'LEVEL_ATS': {'fill_rate': 0.30, 'adverse_selection': 0.12, 'fee': 0.12},
            'INSTINET': {'fill_rate': 0.38, 'adverse_selection': 0.20, 'fee': 0.08},
            'LIQUIDNET': {'fill_rate': 0.25, 'adverse_selection': 0.10, 'fee': 0.20},
        }
        
        # Ping parameters
        self.ping_size = self.config.get('ping_size', 100)
        
        # Discovered liquidity
        self.discovered_liquidity: Dict[str, Dict[str, float]] = {}
    
    def ping_dark_pools(self, symbol: str, side: str, price: float) -> Dict[str, Any]:
        """
        Send ping orders to discover hidden liquidity
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            price: Reference price
            
        Returns:
            Discovered liquidity info
        """
        discoveries = {}
        
        for pool_name, pool_info in self.dark_pools.items():
            # Simulate ping response
            if random.random() < pool_info['fill_rate'] * 0.3:  # Ping fill rate lower
                # Discovered some liquidity
                discovered_size = self.ping_size * random.uniform(5, 50)
                discoveries[pool_name] = {
                    'size': discovered_size,
                    'price': price,  # Midpoint
                    'confidence': random.uniform(0.5, 0.9),
                }
        
        self.discovered_liquidity[symbol] = discoveries
        
        return {
            'symbol': symbol,
            'pools_pinged': len(self.dark_pools),
            'pools_with_liquidity': len(discoveries),
            'total_discovered': sum(d['size'] for d in discoveries.values()),
            'discoveries': discoveries,
        }
    
    def optimal_dark_routing(self, order: Order) -> List[Tuple[str, float]]:
        """
        Calculate optimal routing across dark pools
        
        Args:
            order: Order to route
            
        Returns:
            List of (pool, quantity) tuples
        """
        # Score each pool
        scores = {}
        
        for pool_name, pool_info in self.dark_pools.items():
            score = (
                pool_info['fill_rate'] * 0.4 +
                (1 - pool_info['adverse_selection']) * 0.3 +
                (1 - pool_info['fee'] / 0.3) * 0.2 +
                0.1  # Base score
            )
            
            # Boost if we discovered liquidity
            if order.symbol in self.discovered_liquidity:
                if pool_name in self.discovered_liquidity[order.symbol]:
                    score *= 1.5
            
            scores[pool_name] = score
        
        # Normalize and allocate
        total_score = sum(scores.values())
        routing = []
        
        for pool_name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            allocation = order.quantity * (score / total_score)
            routing.append((pool_name, allocation))
        
        return routing


class VWAPExecutor:
    """
    VWAP Execution Algorithm
    
    Executes order to match Volume-Weighted Average Price
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Volume profile (hourly buckets)
        self.volume_profile = self.config.get('volume_profile', {
            '09:30': 0.08, '10:00': 0.07, '10:30': 0.06, '11:00': 0.05,
            '11:30': 0.05, '12:00': 0.04, '12:30': 0.04, '13:00': 0.04,
            '13:30': 0.05, '14:00': 0.05, '14:30': 0.06, '15:00': 0.08,
            '15:30': 0.10, '16:00': 0.12,
        })
    
    def create_schedule(self, order: Order, duration_minutes: int = 60,
                       num_slices: int = 12) -> List[Dict[str, Any]]:
        """
        Create VWAP execution schedule
        
        Args:
            order: Order to execute
            duration_minutes: Execution duration
            num_slices: Number of slices
            
        Returns:
            List of scheduled slices
        """
        slice_duration = duration_minutes / num_slices
        start_time = datetime.now()
        
        # Get volume weights for time period
        weights = self._get_volume_weights(start_time, duration_minutes)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            weights = [1.0 / num_slices] * num_slices
        else:
            weights = [w / total_weight for w in weights]
        
        # Create slices
        schedule = []
        for i in range(num_slices):
            slice_time = start_time + timedelta(minutes=i * slice_duration)
            slice_qty = order.quantity * weights[i] if i < len(weights) else order.quantity / num_slices
            
            schedule.append({
                'slice_number': i + 1,
                'scheduled_time': slice_time,
                'quantity': slice_qty,
                'weight': weights[i] if i < len(weights) else 1.0 / num_slices,
                'status': 'pending',
            })
        
        return schedule
    
    def _get_volume_weights(self, start_time: datetime, duration_minutes: int) -> List[float]:
        """Get volume weights for time period"""
        weights = []
        current = start_time
        
        while current < start_time + timedelta(minutes=duration_minutes):
            hour_key = current.strftime('%H:%M')
            
            # Find closest hour in profile
            closest_hour = min(
                self.volume_profile.keys(),
                key=lambda h: abs(
                    datetime.strptime(h, '%H:%M').hour * 60 + datetime.strptime(h, '%H:%M').minute -
                    current.hour * 60 - current.minute
                )
            )
            
            weights.append(self.volume_profile.get(closest_hour, 0.05))
            current += timedelta(minutes=5)
        
        return weights


class TWAPExecutor:
    """
    TWAP Execution Algorithm
    
    Executes order evenly over time
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def create_schedule(self, order: Order, duration_minutes: int = 60,
                       num_slices: int = 12) -> List[Dict[str, Any]]:
        """
        Create TWAP execution schedule
        
        Args:
            order: Order to execute
            duration_minutes: Execution duration
            num_slices: Number of slices
            
        Returns:
            List of scheduled slices
        """
        slice_duration = duration_minutes / num_slices
        slice_qty = order.quantity / num_slices
        start_time = datetime.now()
        
        schedule = []
        for i in range(num_slices):
            slice_time = start_time + timedelta(minutes=i * slice_duration)
            
            # Add small randomization to avoid detection
            random_offset = random.uniform(-0.1, 0.1) * slice_qty
            adjusted_qty = slice_qty + random_offset
            
            schedule.append({
                'slice_number': i + 1,
                'scheduled_time': slice_time,
                'quantity': max(0, adjusted_qty),
                'weight': 1.0 / num_slices,
                'status': 'pending',
            })
        
        return schedule


class VPINCalculator:
    """
    Volume-Synchronized Probability of Informed Trading (VPIN)
    
    Detects toxic order flow
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # VPIN parameters
        self.bucket_size = self.config.get('bucket_size', 1000)  # Volume per bucket
        self.num_buckets = self.config.get('num_buckets', 50)
        
        # Trade history
        self.trades: deque = deque(maxlen=10000)
        
        # Buckets
        self.buckets: deque = deque(maxlen=self.num_buckets)
        self.current_bucket = {'buy_volume': 0, 'sell_volume': 0, 'total_volume': 0}
    
    def process_trade(self, price: float, size: float, side: str):
        """
        Process a trade
        
        Args:
            price: Trade price
            size: Trade size
            side: 'buy' or 'sell' (or use tick rule)
        """
        self.trades.append({
            'price': price,
            'size': size,
            'side': side,
            'timestamp': datetime.now(),
        })
        
        # Update current bucket
        if side == 'buy':
            self.current_bucket['buy_volume'] += size
        else:
            self.current_bucket['sell_volume'] += size
        self.current_bucket['total_volume'] += size
        
        # Check if bucket is full
        if self.current_bucket['total_volume'] >= self.bucket_size:
            self.buckets.append(self.current_bucket.copy())
            self.current_bucket = {'buy_volume': 0, 'sell_volume': 0, 'total_volume': 0}
    
    def calculate_vpin(self) -> VPINMetrics:
        """
        Calculate VPIN
        
        Returns:
            VPINMetrics
        """
        if len(self.buckets) < 10:
            return VPINMetrics(
                timestamp=datetime.now(),
                vpin=0.5,
                toxicity_level=ToxicityLevel.MODERATE,
                buy_volume=0,
                sell_volume=0,
                total_volume=0,
                recommendation="Insufficient data",
            )
        
        # Calculate order imbalance for each bucket
        imbalances = []
        total_buy = 0
        total_sell = 0
        
        for bucket in self.buckets:
            imbalance = abs(bucket['buy_volume'] - bucket['sell_volume'])
            imbalances.append(imbalance)
            total_buy += bucket['buy_volume']
            total_sell += bucket['sell_volume']
        
        total_volume = total_buy + total_sell
        
        # VPIN = sum of imbalances / total volume
        if total_volume > 0:
            vpin = sum(imbalances) / total_volume
        else:
            vpin = 0.5
        
        # Determine toxicity level
        if vpin > 0.7:
            toxicity = ToxicityLevel.EXTREME
            recommendation = "High toxicity - reduce liquidity provision, widen spreads"
        elif vpin > 0.5:
            toxicity = ToxicityLevel.HIGH
            recommendation = "Elevated toxicity - increase caution"
        elif vpin > 0.3:
            toxicity = ToxicityLevel.MODERATE
            recommendation = "Normal conditions"
        else:
            toxicity = ToxicityLevel.LOW
            recommendation = "Low toxicity - safe to provide liquidity"
        
        return VPINMetrics(
            timestamp=datetime.now(),
            vpin=vpin,
            toxicity_level=toxicity,
            buy_volume=total_buy,
            sell_volume=total_sell,
            total_volume=total_volume,
            recommendation=recommendation,
        )


class LatencyArbitrageDefense:
    """
    Defense against latency arbitrage
    
    Strategies:
    - Predictive quote updates
    - Quote fading
    - Strategic quote placement
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Defense parameters
        self.staleness_threshold_ms = self.config.get('staleness_threshold_ms', 50)
        self.fade_rate = self.config.get('fade_rate', 0.1)  # bps per ms
        
        # Quote tracking
        self.last_quote_time: Optional[datetime] = None
        self.last_quote_price: float = 0
        
        # Market data
        self.recent_prices: deque = deque(maxlen=100)
    
    def update_market_data(self, price: float, timestamp: datetime = None):
        """Update market data"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.recent_prices.append({
            'price': price,
            'timestamp': timestamp,
        })
    
    def calculate_staleness_risk(self) -> Dict[str, Any]:
        """
        Calculate quote staleness risk
        
        Returns:
            Staleness risk assessment
        """
        if self.last_quote_time is None:
            return {'risk': 0, 'action': 'none'}
        
        # Time since last quote update
        time_since_update = (datetime.now() - self.last_quote_time).total_seconds() * 1000
        
        # Calculate recent volatility
        if len(self.recent_prices) >= 10:
            prices = [p['price'] for p in list(self.recent_prices)[-10:]]
            volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
        else:
            volatility = 0.001
        
        # Calculate order flow pressure
        if len(self.recent_prices) >= 5:
            recent = list(self.recent_prices)[-5:]
            price_change = (recent[-1]['price'] - recent[0]['price']) / recent[0]['price']
            flow_pressure = abs(price_change) * 10000  # In bps
        else:
            flow_pressure = 0
        
        # Staleness risk score
        risk = (
            time_since_update / self.staleness_threshold_ms * 0.4 +
            volatility * 1000 * 0.3 +
            flow_pressure / 10 * 0.3
        )
        
        # Determine action
        if risk > 1.0:
            action = 'cancel_and_requote'
        elif risk > 0.7:
            action = 'fade_quotes'
        elif risk > 0.4:
            action = 'monitor'
        else:
            action = 'none'
        
        return {
            'risk': risk,
            'time_since_update_ms': time_since_update,
            'volatility': volatility,
            'flow_pressure': flow_pressure,
            'action': action,
        }
    
    def get_faded_quote(self, original_bid: float, original_ask: float) -> Tuple[float, float]:
        """
        Get faded quotes based on staleness
        
        Args:
            original_bid: Original bid price
            original_ask: Original ask price
            
        Returns:
            Tuple of (faded_bid, faded_ask)
        """
        staleness = self.calculate_staleness_risk()
        
        if staleness['action'] == 'none':
            return original_bid, original_ask
        
        # Calculate fade amount
        fade_bps = staleness['risk'] * self.fade_rate * staleness['time_since_update_ms']
        fade_amount = (original_ask - original_bid) * fade_bps / 100
        
        # Widen spread symmetrically
        faded_bid = original_bid - fade_amount / 2
        faded_ask = original_ask + fade_amount / 2
        
        return faded_bid, faded_ask


class ExecutionQualityMonitor:
    """
    Monitors and analyzes execution quality
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Execution history
        self.executions: deque = deque(maxlen=1000)
    
    def record_execution(self, order: Order, fills: List[Fill],
                        arrival_price: float, vwap: float, twap: float) -> ExecutionQuality:
        """
        Record and analyze execution
        
        Args:
            order: Original order
            fills: List of fills
            arrival_price: Price at order arrival
            vwap: Market VWAP during execution
            twap: Market TWAP during execution
            
        Returns:
            ExecutionQuality metrics
        """
        if not fills:
            return ExecutionQuality(
                order_id=order.order_id,
                arrival_price=arrival_price,
                vwap=vwap,
                twap=twap,
                avg_fill_price=0,
                slippage_bps=0,
                implementation_shortfall=0,
                market_impact=0,
                fill_rate=0,
                execution_time_seconds=0,
            )
        
        # Calculate average fill price
        total_value = sum(f.quantity * f.price for f in fills)
        total_qty = sum(f.quantity for f in fills)
        avg_fill = total_value / total_qty if total_qty > 0 else 0
        
        # Slippage vs arrival
        if order.side == 'buy':
            slippage_bps = (avg_fill - arrival_price) / arrival_price * 10000
        else:
            slippage_bps = (arrival_price - avg_fill) / arrival_price * 10000
        
        # Implementation shortfall
        impl_shortfall = abs(avg_fill - arrival_price) / arrival_price
        
        # Market impact (vs VWAP)
        if order.side == 'buy':
            market_impact = (avg_fill - vwap) / vwap * 10000
        else:
            market_impact = (vwap - avg_fill) / vwap * 10000
        
        # Fill rate
        fill_rate = total_qty / order.quantity if order.quantity > 0 else 0
        
        # Execution time
        if fills:
            exec_time = (fills[-1].timestamp - fills[0].timestamp).total_seconds()
        else:
            exec_time = 0
        
        quality = ExecutionQuality(
            order_id=order.order_id,
            arrival_price=arrival_price,
            vwap=vwap,
            twap=twap,
            avg_fill_price=avg_fill,
            slippage_bps=slippage_bps,
            implementation_shortfall=impl_shortfall,
            market_impact=market_impact,
            fill_rate=fill_rate,
            execution_time_seconds=exec_time,
        )
        
        self.executions.append(quality)
        
        return quality
    
    def get_statistics(self) -> Dict[str, float]:
        """Get execution statistics"""
        if not self.executions:
            return {}
        
        executions = list(self.executions)
        
        return {
            'avg_slippage_bps': np.mean([e.slippage_bps for e in executions]),
            'avg_market_impact_bps': np.mean([e.market_impact for e in executions]),
            'avg_fill_rate': np.mean([e.fill_rate for e in executions]),
            'avg_execution_time': np.mean([e.execution_time_seconds for e in executions]),
            'total_executions': len(executions),
        }
