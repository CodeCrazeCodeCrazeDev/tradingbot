"""
Real-Time Execution Engine
==========================

Real-time order execution with WebSocket-based order management.
No polling for order status - uses streaming updates.

Features:
1. Real-time order submission
2. WebSocket order status streaming
3. Real-time fill tracking
4. Slippage monitoring
5. Execution quality analysis
6. Smart order routing
7. Partial fill handling

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force"""
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    DAY = "day"  # Day order


@dataclass
class Order:
    """Order representation"""
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    fills: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity
    
    @property
    def fill_rate(self) -> float:
        return self.filled_quantity / self.quantity if self.quantity > 0 else 0
    
    @property
    def is_complete(self) -> bool:
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, 
                               OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force.value,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'remaining_quantity': self.remaining_quantity,
            'fill_rate': self.fill_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'fills': self.fills
        }


@dataclass
class Fill:
    """Order fill"""
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    commission_asset: str = "USDT"
    timestamp: datetime = field(default_factory=datetime.now)
    is_maker: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fill_id': self.fill_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'commission_asset': self.commission_asset,
            'timestamp': self.timestamp.isoformat(),
            'is_maker': self.is_maker
        }


@dataclass
class ExecutionReport:
    """Execution quality report"""
    order_id: str
    symbol: str
    side: OrderSide
    requested_quantity: float
    filled_quantity: float
    requested_price: float
    avg_fill_price: float
    slippage_bps: float
    execution_time_ms: float
    fill_rate: float
    num_fills: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'requested_quantity': self.requested_quantity,
            'filled_quantity': self.filled_quantity,
            'requested_price': self.requested_price,
            'avg_fill_price': self.avg_fill_price,
            'slippage_bps': self.slippage_bps,
            'execution_time_ms': self.execution_time_ms,
            'fill_rate': self.fill_rate,
            'num_fills': self.num_fills,
            'timestamp': self.timestamp.isoformat()
        }


class OrderRouter:
    """
    Smart order router for optimal execution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._venues: List[str] = config.get('venues', ['primary'])
        
    def route_order(self, order: Order, market_data: Dict[str, Any] = None) -> str:
        """Determine best venue for order"""
        # Simple routing - in production would analyze liquidity, fees, etc.
        return self._venues[0] if self._venues else 'primary'
    
    def split_order(self, order: Order, market_data: Dict[str, Any] = None) -> List[Order]:
        """Split large order into smaller chunks"""
        max_order_size = self.config.get('max_order_size', float('inf'))
        
        if order.quantity <= max_order_size:
            return [order]
        
        chunks = []
        remaining = order.quantity
        chunk_num = 0
        
        while remaining > 0:
            chunk_size = min(remaining, max_order_size)
            chunk_order = Order(
                order_id=f"{order.order_id}-{chunk_num}",
                client_order_id=f"{order.client_order_id}-{chunk_num}",
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=chunk_size,
                price=order.price,
                stop_price=order.stop_price,
                time_in_force=order.time_in_force,
                metadata={**order.metadata, 'parent_order_id': order.order_id}
            )
            chunks.append(chunk_order)
            remaining -= chunk_size
            chunk_num += 1
        
        return chunks


class SimulatedBroker:
    """
    Simulated broker for paper trading.
    Provides realistic execution simulation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._latency_ms = config.get('latency_ms', 50)
        self._slippage_bps = config.get('slippage_bps', 2)
        self._fill_rate = config.get('fill_rate', 0.98)
        self._order_counter = 0
        
    async def submit_order(self, order: Order, current_price: float) -> Order:
        """Submit order to simulated broker"""
        # Simulate network latency
        await asyncio.sleep(self._latency_ms / 1000)
        
        self._order_counter += 1
        order.order_id = f"SIM-{self._order_counter:08d}"
        order.status = OrderStatus.SUBMITTED
        order.updated_at = datetime.now()
        
        # Simulate execution
        if order.order_type == OrderType.MARKET:
            await self._execute_market_order(order, current_price)
        elif order.order_type == OrderType.LIMIT:
            await self._execute_limit_order(order, current_price)
        
        return order
    
    async def _execute_market_order(self, order: Order, current_price: float):
        """Execute market order with slippage"""
        import random
        
        # Apply slippage
        slippage = current_price * (self._slippage_bps / 10000)
        if order.side == OrderSide.BUY:
            fill_price = current_price + slippage * random.uniform(0, 1)
        else:
            fill_price = current_price - slippage * random.uniform(0, 1)
        
        # Simulate partial fills
        if random.random() < self._fill_rate:
            filled_qty = order.quantity
        else:
            filled_qty = order.quantity * random.uniform(0.8, 0.99)
        
        # Create fill
        fill = Fill(
            fill_id=f"FILL-{uuid.uuid4().hex[:8]}",
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=filled_qty,
            price=fill_price,
            commission=filled_qty * fill_price * 0.0004,  # 4 bps commission
            timestamp=datetime.now()
        )
        
        order.fills.append(fill.to_dict())
        order.filled_quantity = filled_qty
        order.avg_fill_price = fill_price
        order.status = OrderStatus.FILLED if filled_qty == order.quantity else OrderStatus.PARTIALLY_FILLED
        order.updated_at = datetime.now()
    
    async def _execute_limit_order(self, order: Order, current_price: float):
        """Execute limit order"""
        if order.price is None:
            order.status = OrderStatus.REJECTED
            return
        
        # Check if limit price is executable
        if order.side == OrderSide.BUY and current_price <= order.price:
            await self._execute_market_order(order, order.price)
        elif order.side == OrderSide.SELL and current_price >= order.price:
            await self._execute_market_order(order, order.price)
        # Otherwise order remains pending
    
    async def cancel_order(self, order: Order) -> Order:
        """Cancel order"""
        await asyncio.sleep(self._latency_ms / 1000)
        
        if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
        
        return order


class RealTimeExecution:
    """
    Real-time order execution engine.
    
    Features:
    - Real-time order submission
    - WebSocket order status streaming
    - Execution quality tracking
    - Smart order routing
    - Fill aggregation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Components
        self._router = OrderRouter(config.get('router', {}))
        self._broker = SimulatedBroker(config.get('broker', {}))
        
        # Order tracking
        self._orders: Dict[str, Order] = {}
        self._pending_orders: Dict[str, Order] = {}
        self._completed_orders: deque = deque(maxlen=1000)
        
        # Execution reports
        self._execution_reports: deque = deque(maxlen=500)
        
        # Subscribers
        self._order_subscribers: List[Callable] = []
        self._fill_subscribers: List[Callable] = []
        
        # Current prices (updated from data hub)
        self._current_prices: Dict[str, float] = {}
        
        # Metrics
        self._metrics = {
            'orders_submitted': 0,
            'orders_filled': 0,
            'orders_cancelled': 0,
            'orders_rejected': 0,
            'total_volume': 0.0,
            'avg_slippage_bps': 0.0,
            'avg_execution_time_ms': 0.0
        }
        
        self._running = False
        
        logger.info("RealTimeExecution initialized")
    
    def update_price(self, symbol: str, price: float):
        """Update current price for a symbol"""
        self._current_prices[symbol] = price
    
    async def submit_order(self, 
                          symbol: str,
                          side: OrderSide,
                          quantity: float,
                          order_type: OrderType = OrderType.MARKET,
                          price: float = None,
                          stop_price: float = None,
                          time_in_force: TimeInForce = TimeInForce.GTC,
                          metadata: Dict[str, Any] = None) -> Order:
        """Submit a new order"""
        client_order_id = f"CLT-{uuid.uuid4().hex[:12]}"
        
        order = Order(
            order_id="",  # Will be assigned by broker
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            metadata=metadata or {}
        )
        
        # Store pending order
        self._pending_orders[client_order_id] = order
        
        # Get current price
        current_price = self._current_prices.get(symbol, price or 0)
        
        # Route and submit
        start_time = time.time()
        
        try:
            # Route order
            venue = self._router.route_order(order)
            order.metadata['venue'] = venue
            
            # Submit to broker
            order = await self._broker.submit_order(order, current_price)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tracking
            self._orders[order.order_id] = order
            del self._pending_orders[client_order_id]
            
            self._metrics['orders_submitted'] += 1
            
            # Generate execution report if filled
            if order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                await self._generate_execution_report(order, current_price, execution_time)
            
            # Notify subscribers
            await self._notify_order_update(order)
            
            logger.info(f"Order submitted: {order.order_id} {order.symbol} "
                       f"{order.side.value} {order.quantity} @ {order.avg_fill_price:.2f}")
            
            return order
            
        except Exception as e:
            logger.error(f"Order submission error: {e}")
            order.status = OrderStatus.REJECTED
            order.metadata['error'] = str(e)
            return order
    
    async def cancel_order(self, order_id: str) -> Optional[Order]:
        """Cancel an order"""
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return None
        
        if order.is_complete:
            logger.warning(f"Cannot cancel completed order: {order_id}")
            return order
        
        order = await self._broker.cancel_order(order)
        
        if order.status == OrderStatus.CANCELLED:
            self._metrics['orders_cancelled'] += 1
            self._completed_orders.append(order)
        
        await self._notify_order_update(order)
        
        return order
    
    async def _generate_execution_report(self, order: Order, 
                                         requested_price: float,
                                         execution_time_ms: float):
        """Generate execution quality report"""
        if order.avg_fill_price == 0 or requested_price == 0:
            slippage_bps = 0
        else:
            if order.side == OrderSide.BUY:
                slippage_bps = (order.avg_fill_price - requested_price) / requested_price * 10000
            else:
                slippage_bps = (requested_price - order.avg_fill_price) / requested_price * 10000
        
        report = ExecutionReport(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            requested_quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            requested_price=requested_price,
            avg_fill_price=order.avg_fill_price,
            slippage_bps=slippage_bps,
            execution_time_ms=execution_time_ms,
            fill_rate=order.fill_rate,
            num_fills=len(order.fills)
        )
        
        self._execution_reports.append(report)
        
        # Update metrics
        if order.status == OrderStatus.FILLED:
            self._metrics['orders_filled'] += 1
        
        self._metrics['total_volume'] += order.filled_quantity * order.avg_fill_price
        
        # Update running averages
        reports = list(self._execution_reports)
        if reports:
            self._metrics['avg_slippage_bps'] = sum(r.slippage_bps for r in reports) / len(reports)
            self._metrics['avg_execution_time_ms'] = sum(r.execution_time_ms for r in reports) / len(reports)
    
    async def _notify_order_update(self, order: Order):
        """Notify subscribers of order update"""
        for callback in self._order_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(order)
                else:
                    callback(order)
            except Exception as e:
                logger.error(f"Order subscriber error: {e}")
    
    async def _notify_fill(self, fill: Fill):
        """Notify subscribers of fill"""
        for callback in self._fill_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(fill)
                else:
                    callback(fill)
            except Exception as e:
                logger.error(f"Fill subscriber error: {e}")
    
    def subscribe_orders(self, callback: Callable):
        """Subscribe to order updates"""
        self._order_subscribers.append(callback)
    
    def subscribe_fills(self, callback: Callable):
        """Subscribe to fills"""
        self._fill_subscribers.append(callback)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get open orders"""
        orders = [o for o in self._orders.values() if not o.is_complete]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_execution_reports(self, limit: int = 100) -> List[ExecutionReport]:
        """Get recent execution reports"""
        return list(self._execution_reports)[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics"""
        return {
            **self._metrics,
            'open_orders': len([o for o in self._orders.values() if not o.is_complete]),
            'pending_orders': len(self._pending_orders),
            'completed_orders': len(self._completed_orders)
        }
    
    async def start(self):
        """Start execution engine"""
        self._running = True
        logger.info("RealTimeExecution started")
    
    async def stop(self):
        """Stop execution engine"""
        self._running = False
        
        # Cancel all open orders
        for order in list(self._orders.values()):
            if not order.is_complete:
                await self.cancel_order(order.order_id)
        
        logger.info("RealTimeExecution stopped")
