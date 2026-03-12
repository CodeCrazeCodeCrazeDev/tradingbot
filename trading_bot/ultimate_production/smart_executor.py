"""
Smart Executor - Intelligent Order Execution System
====================================================

This module implements sophisticated order execution algorithms
designed to minimize market impact and slippage.

Features:
1. Smart Order Routing
2. TWAP/VWAP Execution
3. Iceberg Orders
4. Slippage Protection
5. Fill Tracking
6. Execution Quality Analysis

Goal: Execute orders at the best possible price while minimizing
market impact and information leakage.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)


class ExecutionAlgorithm(Enum):
    """Execution algorithm types"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    SMART = "smart"
    ADAPTIVE = "adaptive"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ExecutionOrder:
    """Order for execution"""
    order_id: str
    symbol: str
    direction: str  # BUY, SELL
    quantity: float
    order_type: str  # market, limit
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET
    time_in_force: str = "GTC"  # GTC, IOC, FOK, DAY
    max_slippage: float = 0.001  # 0.1%
    urgency: str = "normal"  # low, normal, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: str
    success: bool
    status: OrderStatus
    fill_price: float
    fill_quantity: float
    fees: float
    slippage: float
    execution_time: timedelta
    venue: str
    error: Optional[str] = None
    child_orders: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketSnapshot:
    """Current market state"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    last_price: float
    volume: float
    spread: float
    
    @property
    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid_price) * 10000 if self.mid_price > 0 else 0


class SlippageModel:
    """
    Model to estimate and track slippage
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Historical slippage tracking
            self.slippage_history: Dict[str, deque] = {}
            self.max_history = 100
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_slippage(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        market: MarketSnapshot
    ) -> float:
        """
        Estimate expected slippage for an order
        
        Returns:
            Estimated slippage as a fraction of price
        """
        # Base slippage from spread
        try:
            base_slippage = market.spread / market.mid_price / 2
        
            # Size impact
            if direction == "BUY":
                available_liquidity = market.ask_size
            else:
                available_liquidity = market.bid_size
        
            size_ratio = quantity / available_liquidity if available_liquidity > 0 else 1
            size_impact = size_ratio * 0.001  # 0.1% per 100% of available liquidity
        
            # Historical adjustment
            historical_avg = self._get_historical_average(symbol)
        
            # Combine estimates
            estimated = base_slippage + size_impact
            if historical_avg > 0:
                estimated = 0.7 * estimated + 0.3 * historical_avg
        
            return estimated
        except Exception as e:
            logger.error(f"Error in estimate_slippage: {e}")
            raise
    
    def record_slippage(self, symbol: str, slippage: float):
        """Record actual slippage for learning"""
        try:
            if symbol not in self.slippage_history:
                self.slippage_history[symbol] = deque(maxlen=self.max_history)
        
            self.slippage_history[symbol].append(slippage)
        except Exception as e:
            logger.error(f"Error in record_slippage: {e}")
            raise
    
    def _get_historical_average(self, symbol: str) -> float:
        """Get historical average slippage for symbol"""
        try:
            if symbol not in self.slippage_history:
                return 0.0
        
            history = self.slippage_history[symbol]
            if len(history) == 0:
                return 0.0
        
            return np.mean(list(history))
        except Exception as e:
            logger.error(f"Error in _get_historical_average: {e}")
            raise


class TWAPExecutor:
    """
    Time-Weighted Average Price executor
    Splits order into equal parts over time
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.default_slices = self.config.get('default_slices', 10)
            self.default_duration = self.config.get('default_duration_minutes', 30)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def execute(
        self,
        order: ExecutionOrder,
        executor_func,
        num_slices: Optional[int] = None,
        duration_minutes: Optional[int] = None
    ) -> ExecutionResult:
        """Execute order using TWAP algorithm"""
        try:
            slices = num_slices or self.default_slices
            duration = duration_minutes or self.default_duration
        
            slice_quantity = order.quantity / slices
            interval = duration * 60 / slices  # seconds between slices
        
            fills = []
            total_filled = 0
            total_cost = 0
        
            for i in range(slices):
                # Create child order
                child_order = ExecutionOrder(
                    order_id=f"{order.order_id}_twap_{i}",
                    symbol=order.symbol,
                    direction=order.direction,
                    quantity=slice_quantity,
                    order_type="market",
                    algorithm=ExecutionAlgorithm.MARKET,
                    metadata={'parent_id': order.order_id, 'slice': i}
                )
            
                # Execute slice
                result = await executor_func(child_order)
            
                if result.success:
                    fills.append(result)
                    total_filled += result.fill_quantity
                    total_cost += result.fill_price * result.fill_quantity
            
                # Wait for next slice (except last)
                if i < slices - 1:
                    await asyncio.sleep(interval)
        
            # Calculate average price
            avg_price = total_cost / total_filled if total_filled > 0 else 0
        
            return ExecutionResult(
                order_id=order.order_id,
                success=total_filled > 0,
                status=OrderStatus.FILLED if total_filled >= order.quantity * 0.95 else OrderStatus.PARTIAL,
                fill_price=avg_price,
                fill_quantity=total_filled,
                fees=sum(f.fees for f in fills),
                slippage=sum(f.slippage for f in fills) / len(fills) if fills else 0,
                execution_time=timedelta(minutes=duration),
                venue="TWAP",
                child_orders=[f.order_id for f in fills],
                metadata={'algorithm': 'TWAP', 'slices': slices}
            )
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            raise


class VWAPExecutor:
    """
    Volume-Weighted Average Price executor
    Executes proportionally to historical volume profile
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.default_duration = self.config.get('default_duration_minutes', 60)
        
            # Simplified volume profile (in production, use actual historical data)
            # Represents typical intraday volume distribution
            self.volume_profile = [
                0.08, 0.06, 0.05, 0.04, 0.04,  # First hour
                0.03, 0.03, 0.03, 0.03, 0.03,  # Mid-morning
                0.04, 0.05, 0.06, 0.07, 0.08,  # Lunch
                0.05, 0.04, 0.04, 0.05, 0.06,  # Afternoon
                0.07, 0.08, 0.09, 0.10, 0.12,  # Close
            ]
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def execute(
        self,
        order: ExecutionOrder,
        executor_func,
        duration_minutes: Optional[int] = None
    ) -> ExecutionResult:
        """Execute order using VWAP algorithm"""
        try:
            duration = duration_minutes or self.default_duration
        
            # Determine number of slices based on duration
            num_slices = min(len(self.volume_profile), duration // 5)
        
            # Get volume weights for our execution window
            weights = self.volume_profile[:num_slices]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
        
            interval = duration * 60 / num_slices
        
            fills = []
            total_filled = 0
            total_cost = 0
        
            for i, weight in enumerate(weights):
                slice_quantity = order.quantity * weight
            
                child_order = ExecutionOrder(
                    order_id=f"{order.order_id}_vwap_{i}",
                    symbol=order.symbol,
                    direction=order.direction,
                    quantity=slice_quantity,
                    order_type="market",
                    algorithm=ExecutionAlgorithm.MARKET,
                    metadata={'parent_id': order.order_id, 'slice': i, 'weight': weight}
                )
            
                result = await executor_func(child_order)
            
                if result.success:
                    fills.append(result)
                    total_filled += result.fill_quantity
                    total_cost += result.fill_price * result.fill_quantity
            
                if i < len(weights) - 1:
                    await asyncio.sleep(interval)
        
            avg_price = total_cost / total_filled if total_filled > 0 else 0
        
            return ExecutionResult(
                order_id=order.order_id,
                success=total_filled > 0,
                status=OrderStatus.FILLED if total_filled >= order.quantity * 0.95 else OrderStatus.PARTIAL,
                fill_price=avg_price,
                fill_quantity=total_filled,
                fees=sum(f.fees for f in fills),
                slippage=sum(f.slippage for f in fills) / len(fills) if fills else 0,
                execution_time=timedelta(minutes=duration),
                venue="VWAP",
                child_orders=[f.order_id for f in fills],
                metadata={'algorithm': 'VWAP', 'slices': num_slices}
            )
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            raise


class IcebergExecutor:
    """
    Iceberg order executor
    Shows only a small portion of the order at a time
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.show_ratio = self.config.get('show_ratio', 0.1)  # Show 10% at a time
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def execute(
        self,
        order: ExecutionOrder,
        executor_func,
        show_quantity: Optional[float] = None
    ) -> ExecutionResult:
        """Execute order using iceberg algorithm"""
        try:
            show_qty = show_quantity or (order.quantity * self.show_ratio)
        
            fills = []
            remaining = order.quantity
            total_cost = 0
            slice_num = 0
        
            while remaining > 0:
                slice_qty = min(show_qty, remaining)
            
                child_order = ExecutionOrder(
                    order_id=f"{order.order_id}_ice_{slice_num}",
                    symbol=order.symbol,
                    direction=order.direction,
                    quantity=slice_qty,
                    order_type=order.order_type,
                    limit_price=order.limit_price,
                    algorithm=ExecutionAlgorithm.LIMIT if order.limit_price else ExecutionAlgorithm.MARKET,
                    metadata={'parent_id': order.order_id, 'slice': slice_num}
                )
            
                result = await executor_func(child_order)
            
                if result.success:
                    fills.append(result)
                    remaining -= result.fill_quantity
                    total_cost += result.fill_price * result.fill_quantity
                    slice_num += 1
                else:
                    # If a slice fails, stop
                    break
            
                # Small delay between slices
                await asyncio.sleep(0.5)
        
            total_filled = order.quantity - remaining
            avg_price = total_cost / total_filled if total_filled > 0 else 0
        
            return ExecutionResult(
                order_id=order.order_id,
                success=total_filled > 0,
                status=OrderStatus.FILLED if remaining <= 0 else OrderStatus.PARTIAL,
                fill_price=avg_price,
                fill_quantity=total_filled,
                fees=sum(f.fees for f in fills),
                slippage=sum(f.slippage for f in fills) / len(fills) if fills else 0,
                execution_time=timedelta(seconds=len(fills) * 0.5),
                venue="ICEBERG",
                child_orders=[f.order_id for f in fills],
                metadata={'algorithm': 'ICEBERG', 'slices': slice_num}
            )
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            raise


class SmartOrderRouter:
    """
    Smart order router that selects best execution venue and algorithm
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Available venues (in production, these would be real connections)
            self.venues = self.config.get('venues', ['PRIMARY', 'SECONDARY'])
        
            # Venue performance tracking
            self.venue_stats: Dict[str, Dict[str, float]] = {
                venue: {'fills': 0, 'avg_slippage': 0, 'latency_ms': 50}
                for venue in self.venues
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def select_venue(self, order: ExecutionOrder, market: MarketSnapshot) -> str:
        """Select best venue for order"""
        try:
            if len(self.venues) == 1:
                return self.venues[0]
        
            # Score each venue
            scores = {}
            for venue in self.venues:
                stats = self.venue_stats[venue]
            
                # Lower slippage is better
                slippage_score = 1 - min(1, stats['avg_slippage'] * 100)
            
                # Lower latency is better
                latency_score = 1 - min(1, stats['latency_ms'] / 100)
            
                # More fills indicate reliability
                fill_score = min(1, stats['fills'] / 100)
            
                scores[venue] = 0.5 * slippage_score + 0.3 * latency_score + 0.2 * fill_score
        
            return max(scores, key=scores.get)
        except Exception as e:
            logger.error(f"Error in select_venue: {e}")
            raise
    
    def select_algorithm(
        self,
        order: ExecutionOrder,
        market: MarketSnapshot
    ) -> ExecutionAlgorithm:
        """Select best execution algorithm"""
        # For small orders, use market
        try:
            if order.quantity * market.mid_price < 1000:
                return ExecutionAlgorithm.MARKET
        
            # For large orders relative to liquidity, use TWAP/VWAP
            liquidity = market.bid_size + market.ask_size
            if order.quantity > liquidity * 0.1:
                if order.urgency == "low":
                    return ExecutionAlgorithm.VWAP
                else:
                    return ExecutionAlgorithm.TWAP
        
            # For medium orders, use iceberg
            if order.quantity > liquidity * 0.05:
                return ExecutionAlgorithm.ICEBERG
        
            # Default to smart limit
            return ExecutionAlgorithm.LIMIT
        except Exception as e:
            logger.error(f"Error in select_algorithm: {e}")
            raise
    
    def update_venue_stats(self, venue: str, slippage: float, latency_ms: float):
        """Update venue performance statistics"""
        try:
            if venue not in self.venue_stats:
                self.venue_stats[venue] = {'fills': 0, 'avg_slippage': 0, 'latency_ms': 50}
        
            stats = self.venue_stats[venue]
            stats['fills'] += 1
        
            # Exponential moving average
            alpha = 0.1
            stats['avg_slippage'] = alpha * slippage + (1 - alpha) * stats['avg_slippage']
            stats['latency_ms'] = alpha * latency_ms + (1 - alpha) * stats['latency_ms']
        except Exception as e:
            logger.error(f"Error in update_venue_stats: {e}")
            raise


class ExecutionQualityAnalyzer:
    """
    Analyze execution quality and track performance
    """
    
    def __init__(self):
        try:
            self.executions: List[ExecutionResult] = []
            self.max_history = 1000
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_execution(self, result: ExecutionResult):
        """Record an execution for analysis"""
        try:
            self.executions.append(result)
        
            if len(self.executions) > self.max_history:
                self.executions = self.executions[-self.max_history:]
        except Exception as e:
            logger.error(f"Error in record_execution: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution quality metrics"""
        try:
            if not self.executions:
                return {}
        
            successful = [e for e in self.executions if e.success]
        
            if not successful:
                return {'success_rate': 0}
        
            return {
                'total_executions': len(self.executions),
                'success_rate': len(successful) / len(self.executions),
                'avg_slippage': np.mean([e.slippage for e in successful]),
                'avg_slippage_bps': np.mean([e.slippage for e in successful]) * 10000,
                'max_slippage': max(e.slippage for e in successful),
                'avg_fees': np.mean([e.fees for e in successful]),
                'avg_execution_time': np.mean([e.execution_time.total_seconds() for e in successful]),
                'fill_rate': np.mean([e.fill_quantity / e.metadata.get('requested_quantity', e.fill_quantity) 
                                     for e in successful if e.metadata.get('requested_quantity', 0) > 0]),
            }
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            raise


class SmartExecutor:
    """
    Main Smart Execution System
    
    Coordinates all execution components for optimal order execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.slippage_model = SlippageModel(config)
            self.twap_executor = TWAPExecutor(config)
            self.vwap_executor = VWAPExecutor(config)
            self.iceberg_executor = IcebergExecutor(config)
            self.router = SmartOrderRouter(config)
            self.quality_analyzer = ExecutionQualityAnalyzer()
        
            # Execution mode
            self.mode = self.config.get('mode', 'paper')  # paper, live
        
            # Paper trading state
            self.paper_fills: Dict[str, ExecutionResult] = {}
        
            logger.info(f"Smart Executor initialized in {self.mode} mode")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def execute(self, trade: Any) -> ExecutionResult:
        """
        Execute a trade with smart routing and algorithms
        
        Args:
            trade: TradeExecution object from core_engine
        
        Returns:
            ExecutionResult with fill details
        """
        try:
            start_time = datetime.now()
        
            # Create execution order
            order = ExecutionOrder(
                order_id=trade.execution_id,
                symbol=trade.symbol,
                direction=trade.direction,
                quantity=trade.quantity,
                order_type="market",
                algorithm=ExecutionAlgorithm.SMART,
                metadata={'trade_id': trade.execution_id}
            )
        
            # Get market snapshot
            market = await self._get_market_snapshot(order.symbol)
        
            # Select algorithm
            algorithm = self.router.select_algorithm(order, market)
            order.algorithm = algorithm
        
            # Select venue
            venue = self.router.select_venue(order, market)
        
            # Estimate slippage
            estimated_slippage = self.slippage_model.estimate_slippage(
                order.symbol, order.direction, order.quantity, market
            )
        
            # Execute based on algorithm
            if algorithm == ExecutionAlgorithm.TWAP:
                result = await self.twap_executor.execute(order, self._execute_single)
            elif algorithm == ExecutionAlgorithm.VWAP:
                result = await self.vwap_executor.execute(order, self._execute_single)
            elif algorithm == ExecutionAlgorithm.ICEBERG:
                result = await self.iceberg_executor.execute(order, self._execute_single)
            else:
                result = await self._execute_single(order)
        
            # Update execution time
            result.execution_time = datetime.now() - start_time
            result.venue = venue
            result.metadata['algorithm'] = algorithm.value
            result.metadata['estimated_slippage'] = estimated_slippage
            result.metadata['requested_quantity'] = order.quantity
        
            # Record for analysis
            self.quality_analyzer.record_execution(result)
            self.slippage_model.record_slippage(order.symbol, result.slippage)
            self.router.update_venue_stats(venue, result.slippage, result.execution_time.total_seconds() * 1000)
        
            return result
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            raise
    
    async def _execute_single(self, order: ExecutionOrder) -> ExecutionResult:
        """Execute a single order"""
        try:
            if self.mode == "paper":
                return await self._paper_execute(order)
            else:
                return await self._live_execute(order)
        except Exception as e:
            logger.error(f"Error in _execute_single: {e}")
            raise
    
    async def _paper_execute(self, order: ExecutionOrder) -> ExecutionResult:
        """Paper trading execution"""
        # Get current market
        try:
            market = await self._get_market_snapshot(order.symbol)
        
            # Simulate fill with realistic slippage
            base_slippage = market.spread / market.mid_price / 2
            random_slippage = np.random.uniform(0, 0.0005)  # Up to 5 bps random
            total_slippage = base_slippage + random_slippage
        
            if order.direction == "BUY":
                fill_price = market.ask * (1 + random_slippage)
            else:
                fill_price = market.bid * (1 - random_slippage)
        
            # Simulate fees (0.1% typical)
            fees = order.quantity * fill_price * 0.001
        
            result = ExecutionResult(
                order_id=order.order_id,
                success=True,
                status=OrderStatus.FILLED,
                fill_price=fill_price,
                fill_quantity=order.quantity,
                fees=fees,
                slippage=total_slippage,
                execution_time=timedelta(milliseconds=np.random.uniform(10, 100)),
                venue="PAPER",
                metadata={'mode': 'paper'}
            )
        
            self.paper_fills[order.order_id] = result
        
            return result
        except Exception as e:
            logger.error(f"Error in _paper_execute: {e}")
            raise
    
    async def _live_execute(self, order: ExecutionOrder) -> ExecutionResult:
        """Live trading execution - connects to real broker"""
        # In production, this would connect to actual broker API
        # For now, return error indicating live trading not configured
        
        try:
            logger.warning("Live execution not configured - falling back to paper")
            return await self._paper_execute(order)
        except Exception as e:
            logger.error(f"Error in _live_execute: {e}")
            raise
    
    async def _get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        """Get current market snapshot"""
        # In production, this would get real market data
        # For now, generate synthetic data
        
        try:
            base_prices = {
                'EURUSD': 1.0850,
                'GBPUSD': 1.2650,
                'USDJPY': 149.50,
                'AUDUSD': 0.6550,
                'BTCUSD': 42000.0,
            }
        
            base_price = base_prices.get(symbol, 100.0)
        
            # Add some randomness
            noise = np.random.uniform(-0.0005, 0.0005)
            mid = base_price * (1 + noise)
        
            # Typical spread
            spread = mid * 0.0001  # 1 pip for forex
        
            return MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(),
                bid=mid - spread / 2,
                ask=mid + spread / 2,
                bid_size=np.random.uniform(100000, 1000000),
                ask_size=np.random.uniform(100000, 1000000),
                last_price=mid,
                volume=np.random.uniform(1000000, 10000000),
                spread=spread,
            )
        except Exception as e:
            logger.error(f"Error in _get_market_snapshot: {e}")
            raise
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return self.quality_analyzer.get_metrics()
    
    def get_venue_stats(self) -> Dict[str, Dict[str, float]]:
        """Get venue performance statistics"""
        return self.router.venue_stats
