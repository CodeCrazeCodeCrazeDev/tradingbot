"""
Advanced Execution Algorithms Module
=====================================

Smart order execution with:
- Smart Order Router (SOR)
- Iceberg Orders & Stealth Execution
- Dark Pool Mining
- VWAP/TWAP Execution
- Execution Quality Monitoring
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
import asyncio
import random
import heapq
import numpy
import pandas

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    LIMIT_IOC = "limit_ioc"
    LIMIT_FOK = "limit_fok"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"  # Percentage of Volume
    IS = "is"  # Implementation Shortfall


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VenueType(Enum):
    """Trading venue types"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DARK_POOL = "dark_pool"
    ECN = "ecn"
    ATS = "ats"  # Alternative Trading System
    INTERNALIZE = "internalize"


@dataclass
class Venue:
    """Trading venue information"""
    name: str
    venue_type: VenueType
    fee_maker: float  # Maker fee (can be negative for rebate)
    fee_taker: float  # Taker fee
    latency_ms: float  # Average latency in milliseconds
    avg_spread: float  # Average spread
    avg_depth: float  # Average depth at best price
    fill_rate: float  # Historical fill rate
    adverse_selection: float  # Adverse selection risk (0-1)
    
    def score(self, order_size: float, is_aggressive: bool) -> float:
        """Calculate venue score for routing"""
        fee = self.fee_taker if is_aggressive else self.fee_maker
        
        score = (
            self.fill_rate * 0.30 +
            (1 - self.adverse_selection) * 0.25 +
            (1 - self.avg_spread * 100) * 0.20 +
            (1 - self.latency_ms / 100) * 0.15 +
            (1 - fee * 100) * 0.10
        )
        
        return score


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "day"
    venue: Optional[str] = None
    parent_order_id: Optional[str] = None
    
    # Execution state
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    avg_fill_price: float = 0
    fills: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """Execution quality report"""
    order_id: str
    symbol: str
    side: str
    total_quantity: float
    filled_quantity: float
    avg_fill_price: float
    arrival_price: float
    vwap_benchmark: float
    twap_benchmark: float
    
    # Quality metrics
    implementation_shortfall: float
    slippage_bps: float
    market_impact_bps: float
    timing_cost_bps: float
    
    # Execution details
    num_fills: int
    execution_time_seconds: float
    venues_used: List[str]
    fill_rate: float


class SmartOrderRouter:
    """
    Smart Order Router (SOR)
    
    Routes orders to optimal venues based on:
    - Liquidity availability
    - Fee structure
    - Historical fill quality
    - Latency
    - Adverse selection risk
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize venues
        self.venues: Dict[str, Venue] = {}
        self._initialize_default_venues()
        
        # Routing history
        self.routing_history: deque = deque(maxlen=10000)
        
        # Real-time liquidity
        self.venue_liquidity: Dict[str, Dict[str, float]] = {}
        
        # Venue selection weights
        self.selection_weights = {
            'spread': self.config.get('spread_weight', 0.30),
            'depth': self.config.get('depth_weight', 0.25),
            'fill_rate': self.config.get('fill_rate_weight', 0.20),
            'latency': self.config.get('latency_weight', 0.15),
            'fee': self.config.get('fee_weight', 0.10),
        }
    
    def _initialize_default_venues(self):
        """Initialize default venue configurations"""
        default_venues = [
            Venue("NYSE", VenueType.PRIMARY, -0.0002, 0.0003, 5, 0.0001, 10000, 0.95, 0.1),
            Venue("NASDAQ", VenueType.PRIMARY, -0.0002, 0.0003, 3, 0.0001, 8000, 0.94, 0.12),
            Venue("BATS", VenueType.SECONDARY, -0.0003, 0.0002, 2, 0.00015, 5000, 0.90, 0.15),
            Venue("IEX", VenueType.SECONDARY, 0.0001, 0.0001, 10, 0.0002, 3000, 0.85, 0.05),
            Venue("SIGMA_X", VenueType.DARK_POOL, 0.0001, 0.0001, 15, 0, 2000, 0.60, 0.08),
            Venue("CROSSFINDER", VenueType.DARK_POOL, 0.0001, 0.0001, 20, 0, 1500, 0.55, 0.10),
            Venue("LEVEL_ATS", VenueType.ATS, 0.00005, 0.00015, 8, 0.0001, 4000, 0.80, 0.12),
        ]
        
        for venue in default_venues:
            self.venues[venue.name] = venue
    
    def update_liquidity(self, venue_name: str, symbol: str, 
                        bid_depth: float, ask_depth: float, spread: float):
        """Update real-time liquidity for a venue"""
        if venue_name not in self.venue_liquidity:
            self.venue_liquidity[venue_name] = {}
        
        self.venue_liquidity[venue_name][symbol] = {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'spread': spread,
            'timestamp': datetime.now(),
        }
    
    def route_order(self, order: Order) -> List[Tuple[str, float]]:
        """
        Route order to optimal venues
        
        Args:
            order: Order to route
            
        Returns:
            List of (venue_name, quantity) tuples
        """
        is_aggressive = order.order_type in [OrderType.MARKET, OrderType.LIMIT_IOC]
        
        # Score venues
        venue_scores = []
        for venue_name, venue in self.venues.items():
            # Get real-time liquidity if available
            liquidity = self.venue_liquidity.get(venue_name, {}).get(order.symbol, {})
            
            # Calculate score
            base_score = venue.score(order.quantity, is_aggressive)
            
            # Adjust for real-time liquidity
            if liquidity:
                depth = liquidity.get('bid_depth' if order.side == 'buy' else 'ask_depth', venue.avg_depth)
                spread = liquidity.get('spread', venue.avg_spread)
                
                liquidity_score = min(depth / order.quantity, 1.0) * 0.3
                spread_score = (1 - spread * 1000) * 0.2
                
                base_score = base_score * 0.5 + liquidity_score + spread_score
            
            venue_scores.append((venue_name, base_score, venue))
        
        # Sort by score
        venue_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate order across venues
        allocations = self._allocate_across_venues(order, venue_scores)
        
        # Record routing decision
        self.routing_history.append({
            'timestamp': datetime.now(),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'quantity': order.quantity,
            'allocations': allocations,
        })
        
        return allocations
    
    def _allocate_across_venues(self, order: Order, 
                               venue_scores: List[Tuple[str, float, Venue]]) -> List[Tuple[str, float]]:
        """Allocate order quantity across venues"""
        remaining = order.quantity
        allocations = []
        
        for venue_name, score, venue in venue_scores:
            if remaining <= 0:
                break
            
            # Get available liquidity
            liquidity = self.venue_liquidity.get(venue_name, {}).get(order.symbol, {})
            available = liquidity.get('bid_depth' if order.side == 'buy' else 'ask_depth', venue.avg_depth)
            
            # Allocate based on score and liquidity
            allocation = min(remaining, available * 0.5)  # Don't take more than 50% of depth
            
            if allocation > 0:
                allocations.append((venue_name, allocation))
                remaining -= allocation
        
        # If remaining, send to primary venue
        if remaining > 0 and venue_scores:
            primary = venue_scores[0][0]
            # Find existing allocation or add new
            for i, (v, q) in enumerate(allocations):
                if v == primary:
                    allocations[i] = (v, q + remaining)
                    remaining = 0
                    break
            if remaining > 0:
                allocations.append((primary, remaining))
        
        return allocations
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self.routing_history:
            return {}
        
        venue_counts = {}
        venue_volumes = {}
        
        for record in self.routing_history:
            for venue, qty in record['allocations']:
                venue_counts[venue] = venue_counts.get(venue, 0) + 1
                venue_volumes[venue] = venue_volumes.get(venue, 0) + qty
        
        return {
            'total_orders': len(self.routing_history),
            'venue_order_counts': venue_counts,
            'venue_volumes': venue_volumes,
        }


class IcebergExecutor:
    """
    Iceberg Order Executor
    
    Hides true order size by showing only a portion at a time.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Display size settings
        self.min_display_pct = self.config.get('min_display_pct', 0.10)
        self.max_display_pct = self.config.get('max_display_pct', 0.20)
        
        # Replenish settings
        self.replenish_delay_min = self.config.get('replenish_delay_min', 0.5)
        self.replenish_delay_max = self.config.get('replenish_delay_max', 2.0)
        
        # Active icebergs
        self.active_icebergs: Dict[str, Dict[str, Any]] = {}
    
    def create_iceberg(self, order: Order, avg_volume_at_level: float) -> Dict[str, Any]:
        """
        Create iceberg order structure
        
        Args:
            order: Parent order
            avg_volume_at_level: Average volume at the price level
            
        Returns:
            Iceberg configuration
        """
        # Determine if iceberg is appropriate
        if order.quantity <= avg_volume_at_level * 2:
            # Order is small enough, no need for iceberg
            return {'use_iceberg': False, 'order': order}
        
        # Calculate display size
        display_pct = random.uniform(self.min_display_pct, self.max_display_pct)
        display_size = order.quantity * display_pct
        
        # Ensure display size is reasonable
        display_size = max(display_size, avg_volume_at_level * 0.5)
        display_size = min(display_size, avg_volume_at_level * 1.5)
        
        iceberg = {
            'use_iceberg': True,
            'parent_order': order,
            'total_quantity': order.quantity,
            'display_size': display_size,
            'hidden_size': order.quantity - display_size,
            'filled_quantity': 0,
            'current_display': display_size,
            'child_orders': [],
            'status': 'active',
        }
        
        self.active_icebergs[order.order_id] = iceberg
        
        return iceberg
    
    def get_next_slice(self, order_id: str) -> Optional[Order]:
        """Get next slice to display after fill"""
        if order_id not in self.active_icebergs:
            return None
        
        iceberg = self.active_icebergs[order_id]
        
        if iceberg['status'] != 'active':
            return None
        
        remaining = iceberg['total_quantity'] - iceberg['filled_quantity']
        
        if remaining <= 0:
            iceberg['status'] = 'completed'
            return None
        
        # Calculate next display size with randomization
        base_display = iceberg['display_size']
        variation = random.uniform(0.8, 1.2)
        next_display = min(base_display * variation, remaining)
        
        # Create child order
        parent = iceberg['parent_order']
        child = Order(
            order_id=f"{order_id}_slice_{len(iceberg['child_orders'])}",
            symbol=parent.symbol,
            side=parent.side,
            order_type=OrderType.LIMIT,
            quantity=next_display,
            price=parent.price,
            parent_order_id=order_id,
        )
        
        iceberg['child_orders'].append(child)
        iceberg['current_display'] = next_display
        
        return child
    
    def record_fill(self, order_id: str, filled_qty: float):
        """Record fill for iceberg"""
        # Check if it's a child order
        parent_id = order_id.split('_slice_')[0] if '_slice_' in order_id else order_id
        
        if parent_id in self.active_icebergs:
            self.active_icebergs[parent_id]['filled_quantity'] += filled_qty
    
    def get_replenish_delay(self) -> float:
        """Get randomized replenish delay"""
        return random.uniform(self.replenish_delay_min, self.replenish_delay_max)


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
        
        # Dark pool venues
        self.dark_pools = [
            'SIGMA_X', 'CROSSFINDER', 'LEVEL_ATS', 'LIQUIDNET', 
            'POSIT', 'INSTINET', 'ITG_POSIT'
        ]
        
        # Ping order settings
        self.ping_size = self.config.get('ping_size', 100)
        self.ping_timeout = self.config.get('ping_timeout', 1.0)
        
        # Discovered liquidity
        self.discovered_liquidity: Dict[str, Dict[str, float]] = {}
        
        # Fill history by pool
        self.pool_fill_history: Dict[str, deque] = {
            pool: deque(maxlen=1000) for pool in self.dark_pools
        }
    
    def probe_liquidity(self, symbol: str, side: str, 
                       mid_price: float) -> Dict[str, float]:
        """
        Probe dark pools for hidden liquidity
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            mid_price: Current mid price
            
        Returns:
            Dictionary of pool -> estimated liquidity
        """
        discovered = {}
        
        for pool in self.dark_pools:
            # Simulate ping (in production, would send actual orders)
            # Use historical fill rate as proxy
            history = list(self.pool_fill_history[pool])
            
            if history:
                recent_fills = [h for h in history 
                              if h['symbol'] == symbol and 
                              (datetime.now() - h['timestamp']).seconds < 3600]
                
                if recent_fills:
                    avg_size = np.mean([f['size'] for f in recent_fills])
                    fill_rate = len([f for f in recent_fills if f['filled']]) / len(recent_fills)
                    discovered[pool] = avg_size * fill_rate
                else:
                    discovered[pool] = 0
            else:
                # Default estimate based on pool characteristics
                discovered[pool] = self.ping_size * random.uniform(0.3, 0.7)
        
        self.discovered_liquidity[symbol] = discovered
        return discovered
    
    def get_optimal_routing(self, symbol: str, quantity: float,
                           side: str) -> List[Tuple[str, float]]:
        """
        Get optimal routing across dark pools
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            side: 'buy' or 'sell'
            
        Returns:
            List of (pool, quantity) allocations
        """
        # Get discovered liquidity
        liquidity = self.discovered_liquidity.get(symbol, {})
        
        if not liquidity:
            # Probe first
            liquidity = self.probe_liquidity(symbol, side, 0)
        
        # Sort pools by liquidity
        sorted_pools = sorted(liquidity.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate
        allocations = []
        remaining = quantity
        
        for pool, available in sorted_pools:
            if remaining <= 0:
                break
            
            # Take up to 50% of available
            allocation = min(remaining, available * 0.5)
            if allocation > 0:
                allocations.append((pool, allocation))
                remaining -= allocation
        
        return allocations
    
    def record_fill(self, pool: str, symbol: str, size: float, filled: bool):
        """Record fill result for learning"""
        self.pool_fill_history[pool].append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'size': size,
            'filled': filled,
        })
    
    def get_pool_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each dark pool"""
        stats = {}
        
        for pool in self.dark_pools:
            history = list(self.pool_fill_history[pool])
            
            if history:
                fills = [h for h in history if h['filled']]
                fill_rate = len(fills) / len(history)
                avg_size = np.mean([h['size'] for h in fills]) if fills else 0
                
                stats[pool] = {
                    'fill_rate': fill_rate,
                    'avg_fill_size': avg_size,
                    'total_attempts': len(history),
                    'total_fills': len(fills),
                }
            else:
                stats[pool] = {
                    'fill_rate': 0,
                    'avg_fill_size': 0,
                    'total_attempts': 0,
                    'total_fills': 0,
                }
        
        return stats


class VWAPExecutor:
    """
    VWAP (Volume-Weighted Average Price) Executor
    
    Executes order to match or beat VWAP benchmark.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Volume profile (hourly buckets)
        self.volume_profile: Dict[int, float] = {}
        self._initialize_default_profile()
        
        # Execution state
        self.active_executions: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_default_profile(self):
        """Initialize default intraday volume profile"""
        # U-shaped volume profile typical for US equities
        profile = {
            9: 0.12,   # 9:30-10:00 - High opening volume
            10: 0.10,  # 10:00-11:00
            11: 0.08,  # 11:00-12:00
            12: 0.06,  # 12:00-13:00 - Lunch lull
            13: 0.07,  # 13:00-14:00
            14: 0.09,  # 14:00-15:00
            15: 0.14,  # 15:00-16:00 - High closing volume
        }
        
        # Normalize
        total = sum(profile.values())
        self.volume_profile = {k: v / total for k, v in profile.items()}
    
    def create_schedule(self, order: Order, duration_minutes: int = 60,
                       start_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Create VWAP execution schedule
        
        Args:
            order: Order to execute
            duration_minutes: Execution duration
            start_time: Start time (default: now)
            
        Returns:
            List of scheduled slices
        """
        if start_time is None:
            start_time = datetime.now()
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Calculate slices based on volume profile
        slices = []
        current_time = start_time
        remaining = order.quantity
        
        while current_time < end_time and remaining > 0:
            hour = current_time.hour
            volume_weight = self.volume_profile.get(hour, 0.1)
            
            # Calculate slice size
            time_remaining = (end_time - current_time).total_seconds() / 60
            slice_duration = min(5, time_remaining)  # 5-minute slices
            
            slice_weight = volume_weight * (slice_duration / 60)
            slice_size = min(order.quantity * slice_weight, remaining)
            
            if slice_size > 0:
                slices.append({
                    'scheduled_time': current_time,
                    'quantity': slice_size,
                    'status': 'pending',
                })
            
            remaining -= slice_size
            current_time += timedelta(minutes=slice_duration)
        
        # Store execution
        self.active_executions[order.order_id] = {
            'order': order,
            'slices': slices,
            'start_time': start_time,
            'end_time': end_time,
            'filled_quantity': 0,
            'status': 'active',
        }
        
        return slices
    
    def get_next_slice(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get next slice to execute"""
        if order_id not in self.active_executions:
            return None
        
        execution = self.active_executions[order_id]
        
        for slice_info in execution['slices']:
            if slice_info['status'] == 'pending':
                if datetime.now() >= slice_info['scheduled_time']:
                    slice_info['status'] = 'executing'
                    return slice_info
        
        return None
    
    def calculate_vwap(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate VWAP from price/volume data"""
        if not prices or not volumes:
            return 0
        
        total_value = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)
        
        return total_value / total_volume if total_volume > 0 else prices[-1]


class TWAPExecutor:
    """
    TWAP (Time-Weighted Average Price) Executor
    
    Executes order evenly over time.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}
    
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
        start_time = datetime.now()
        slice_interval = duration_minutes / num_slices
        slice_size = order.quantity / num_slices
        
        slices = []
        for i in range(num_slices):
            scheduled_time = start_time + timedelta(minutes=i * slice_interval)
            
            # Add small randomization to avoid predictability
            jitter = random.uniform(-0.5, 0.5) * slice_interval * 0.1
            scheduled_time += timedelta(minutes=jitter)
            
            slices.append({
                'scheduled_time': scheduled_time,
                'quantity': slice_size,
                'status': 'pending',
                'slice_number': i,
            })
        
        self.active_executions[order.order_id] = {
            'order': order,
            'slices': slices,
            'start_time': start_time,
            'duration_minutes': duration_minutes,
            'filled_quantity': 0,
            'status': 'active',
        }
        
        return slices


class ExecutionQualityMonitor:
    """
    Monitors and analyzes execution quality
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Execution history
        self.executions: deque = deque(maxlen=10000)
        
        # Benchmark data
        self.benchmark_data: Dict[str, Dict[str, Any]] = {}
    
    def record_execution(self, order: Order, fills: List[Dict[str, Any]],
                        arrival_price: float, vwap: float, twap: float):
        """Record execution for analysis"""
        if not fills:
            return
        
        total_qty = sum(f['quantity'] for f in fills)
        avg_price = sum(f['price'] * f['quantity'] for f in fills) / total_qty
        
        # Calculate metrics
        if order.side == 'buy':
            is_cost = (avg_price - arrival_price) / arrival_price
            slippage = (avg_price - arrival_price) / arrival_price
        else:
            is_cost = (arrival_price - avg_price) / arrival_price
            slippage = (arrival_price - avg_price) / arrival_price
        
        execution_record = {
            'timestamp': datetime.now(),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': total_qty,
            'avg_price': avg_price,
            'arrival_price': arrival_price,
            'vwap': vwap,
            'twap': twap,
            'implementation_shortfall': is_cost,
            'slippage_bps': slippage * 10000,
            'num_fills': len(fills),
            'venues': list(set(f.get('venue', 'unknown') for f in fills)),
        }
        
        self.executions.append(execution_record)
    
    def generate_report(self, order_id: str = None) -> Optional[ExecutionReport]:
        """Generate execution quality report"""
        if order_id:
            executions = [e for e in self.executions if e['order_id'] == order_id]
        else:
            executions = list(self.executions)
        
        if not executions:
            return None
        
        # Aggregate if multiple
        exec_data = executions[-1] if order_id else executions[-1]
        
        return ExecutionReport(
            order_id=exec_data['order_id'],
            symbol=exec_data['symbol'],
            side=exec_data['side'],
            total_quantity=exec_data['quantity'],
            filled_quantity=exec_data['quantity'],
            avg_fill_price=exec_data['avg_price'],
            arrival_price=exec_data['arrival_price'],
            vwap_benchmark=exec_data['vwap'],
            twap_benchmark=exec_data['twap'],
            implementation_shortfall=exec_data['implementation_shortfall'],
            slippage_bps=exec_data['slippage_bps'],
            market_impact_bps=exec_data['slippage_bps'] * 0.6,  # Estimate
            timing_cost_bps=exec_data['slippage_bps'] * 0.4,  # Estimate
            num_fills=exec_data['num_fills'],
            execution_time_seconds=0,  # Would need timestamps
            venues_used=exec_data['venues'],
            fill_rate=1.0,
        )
    
    def get_aggregate_statistics(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Get aggregate execution statistics"""
        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent = [e for e in self.executions if e['timestamp'] > cutoff]
        
        if not recent:
            return {}
        
        return {
            'total_executions': len(recent),
            'avg_slippage_bps': np.mean([e['slippage_bps'] for e in recent]),
            'avg_implementation_shortfall': np.mean([e['implementation_shortfall'] for e in recent]),
            'median_slippage_bps': np.median([e['slippage_bps'] for e in recent]),
            'slippage_std': np.std([e['slippage_bps'] for e in recent]),
            'best_slippage': min(e['slippage_bps'] for e in recent),
            'worst_slippage': max(e['slippage_bps'] for e in recent),
            'venue_distribution': self._get_venue_distribution(recent),
        }
    
    def _get_venue_distribution(self, executions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of executions across venues"""
        distribution = {}
        for e in executions:
            for venue in e['venues']:
                distribution[venue] = distribution.get(venue, 0) + 1
        return distribution
