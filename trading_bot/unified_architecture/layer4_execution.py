"""
Layer 4: Execution Layer
========================

The execution layer handles all order management, routing, and fill tracking.

Components:
- SmartRouter: Intelligent order routing
- OrderManager: Order lifecycle management
- FillTracker: Track and reconcile fills
- SlippageProtector: Protect against slippage
- ExecutionLayer: Master coordinator

Integrates:
- trading_bot/execution/smart_order_router.py
- trading_bot/execution/order_state_machine.py
- trading_bot/execution/fill_tracker.py
- trading_bot/execution/slippage_protection.py
- trading_bot/execution/atomic_execution.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionAlgorithm(Enum):
    """Execution algorithms"""
    MARKET = "market"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    SNIPER = "sniper"
    ADAPTIVE = "adaptive"


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
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Metadata
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET
    parent_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_complete(self) -> bool:
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, 
                               OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity


@dataclass
class Fill:
    """Order fill"""
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    fee: float = 0.0
    venue: str = "default"


@dataclass
class ExecutionResult:
    """Result of order execution"""
    success: bool
    order: Order
    fills: List[Fill] = field(default_factory=list)
    message: str = ""
    slippage_bps: float = 0.0
    execution_time_ms: float = 0.0


class SmartRouter:
    """
    Smart order routing
    
    Integrates trading_bot/execution/smart_order_router.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._router = None
        
        # Venue configuration
        self.venues = config.get('venues', ['default'])
        self.venue_weights: Dict[str, float] = {v: 1.0 for v in self.venues}
        
        try:
            # Try to import existing router
            from trading_bot.execution.smart_order_router import SmartOrderRouter
            self._router = SmartOrderRouter(config)
            logger.info("Smart router initialized")
        except Exception as e:
            logger.warning(f"Using fallback router: {e}")
    
    def route(self, order: Order) -> str:
        """Route order to best venue"""
        if self._router:
            try:
                return self._router.route(order)
            except Exception as e:
                logger.error(f"Routing error: {e}")
        
        # Fallback: return first venue
        return self.venues[0] if self.venues else "default"
    
    def split_order(self, order: Order, max_size: float) -> List[Order]:
        """Split large order into smaller chunks"""
        if order.quantity <= max_size:
            return [order]
        
        chunks = []
        remaining = order.quantity
        chunk_num = 0
        
        while remaining > 0:
            chunk_size = min(remaining, max_size)
            chunk_order = Order(
                order_id=f"{order.order_id}_chunk_{chunk_num}",
                client_order_id=f"{order.client_order_id}_chunk_{chunk_num}",
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=chunk_size,
                price=order.price,
                stop_price=order.stop_price,
                parent_order_id=order.order_id,
                algorithm=order.algorithm
            )
            chunks.append(chunk_order)
            remaining -= chunk_size
            chunk_num += 1
        
        return chunks
    
    def update_venue_performance(self, venue: str, fill_quality: float):
        """Update venue performance metrics"""
        current = self.venue_weights.get(venue, 1.0)
        self.venue_weights[venue] = 0.9 * current + 0.1 * fill_quality


class OrderManager:
    """
    Order lifecycle management
    
    Integrates trading_bot/execution/order_state_machine.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Order storage
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.max_history = 10000
        
        # Callbacks
        self.on_fill: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        
        try:
            # Import existing state machine
            from trading_bot.execution.order_state_machine import OrderStateMachine
            self._state_machine = OrderStateMachine()
            logger.info("Order manager initialized with state machine")
        except Exception as e:
            logger.warning(f"Using fallback order manager: {e}")
            self._state_machine = None
    
    def create_order(self, symbol: str, side: OrderSide, quantity: float,
                    order_type: OrderType = OrderType.MARKET,
                    price: Optional[float] = None,
                    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET,
                    **kwargs) -> Order:
        """Create a new order"""
        order_id = str(uuid.uuid4())
        client_order_id = kwargs.get('client_order_id', f"cli_{order_id[:8]}")
        
        order = Order(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            algorithm=algorithm,
            metadata=kwargs
        )
        
        self.orders[order_id] = order
        logger.info(f"Order created: {order_id} {side.value} {quantity} {symbol}")
        
        return order
    
    def update_status(self, order_id: str, status: OrderStatus,
                     filled_quantity: Optional[float] = None,
                     average_price: Optional[float] = None):
        """Update order status"""
        order = self.orders.get(order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return
        
        old_status = order.status
        order.status = status
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
        if average_price is not None:
            order.average_fill_price = average_price
        
        if status == OrderStatus.SUBMITTED:
            order.submitted_at = datetime.now()
        elif status == OrderStatus.FILLED:
            order.filled_at = datetime.now()
        
        # Callback
        if self.on_status_change:
            self.on_status_change(order, old_status, status)
        
        # Move to history if complete
        if order.is_complete:
            self.order_history.append(order)
            if len(self.order_history) > self.max_history:
                self.order_history.pop(0)
        
        logger.info(f"Order {order_id} status: {old_status.value} -> {status.value}")
    
    def record_fill(self, order_id: str, fill: Fill):
        """Record a fill for an order"""
        order = self.orders.get(order_id)
        if not order:
            logger.warning(f"Order not found for fill: {order_id}")
            return
        
        order.filled_quantity += fill.quantity
        
        # Update average price
        if order.average_fill_price == 0:
            order.average_fill_price = fill.price
        else:
            total_value = (order.average_fill_price * (order.filled_quantity - fill.quantity) +
                         fill.price * fill.quantity)
            order.average_fill_price = total_value / order.filled_quantity
        
        # Update status
        if order.filled_quantity >= order.quantity:
            self.update_status(order_id, OrderStatus.FILLED)
        elif order.filled_quantity > 0:
            self.update_status(order_id, OrderStatus.PARTIAL)
        
        # Callback
        if self.on_fill:
            self.on_fill(order, fill)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if order.is_complete:
            return False
        
        self.update_status(order_id, OrderStatus.CANCELLED)
        return True
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        open_orders = [o for o in self.orders.values() if not o.is_complete]
        if symbol:
            open_orders = [o for o in open_orders if o.symbol == symbol]
        return open_orders


class FillTracker:
    """
    Track and reconcile order fills
    
    Integrates trading_bot/execution/fill_tracker.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Fill storage
        self.fills: Dict[str, Fill] = {}
        self.fills_by_order: Dict[str, List[Fill]] = {}
        
        # Reconciliation
        self.unreconciled: List[Fill] = []
        
        try:
            # Import existing tracker
            from trading_bot.execution.fill_tracker import FillTracker as ExistingTracker
            self._tracker = ExistingTracker(config)
            logger.info("Fill tracker initialized")
        except Exception as e:
            logger.warning(f"Using fallback fill tracker: {e}")
            self._tracker = None
    
    def record_fill(self, fill: Fill):
        """Record a new fill"""
        self.fills[fill.fill_id] = fill
        
        if fill.order_id not in self.fills_by_order:
            self.fills_by_order[fill.order_id] = []
        self.fills_by_order[fill.order_id].append(fill)
        
        logger.info(f"Fill recorded: {fill.fill_id} - {fill.quantity} @ {fill.price}")
    
    def get_fills_for_order(self, order_id: str) -> List[Fill]:
        """Get all fills for an order"""
        return self.fills_by_order.get(order_id, [])
    
    def calculate_vwap(self, order_id: str) -> float:
        """Calculate VWAP for an order"""
        fills = self.get_fills_for_order(order_id)
        if not fills:
            return 0.0
        
        total_value = sum(f.price * f.quantity for f in fills)
        total_quantity = sum(f.quantity for f in fills)
        
        return total_value / total_quantity if total_quantity > 0 else 0.0
    
    def reconcile(self, expected_orders: List[Order]) -> Dict[str, Any]:
        """Reconcile fills with expected orders"""
        results = {
            'matched': [],
            'unmatched_fills': [],
            'missing_fills': []
        }
        
        for order in expected_orders:
            fills = self.get_fills_for_order(order.order_id)
            total_filled = sum(f.quantity for f in fills)
            
            if total_filled == order.quantity:
                results['matched'].append(order.order_id)
            elif total_filled < order.quantity:
                results['missing_fills'].append({
                    'order_id': order.order_id,
                    'expected': order.quantity,
                    'filled': total_filled
                })
        
        return results


class SlippageProtector:
    """
    Protect against excessive slippage
    
    Integrates trading_bot/execution/slippage_protection.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Slippage limits (basis points)
        self.max_slippage_bps = config.get('max_slippage_bps', 50)
        self.warning_slippage_bps = config.get('warning_slippage_bps', 20)
        
        # Tracking
        self.slippage_history: List[float] = []
        self.max_history = 1000
        
        try:
            # Import existing protector
            from trading_bot.execution.slippage_protection import SlippageProtection
            self._protector = SlippageProtection(config)
            logger.info("Slippage protector initialized")
        except Exception as e:
            logger.warning(f"Using fallback slippage protector: {e}")
            self._protector = None
    
    def check_slippage(self, expected_price: float, actual_price: float,
                      side: OrderSide) -> Dict[str, Any]:
        """Check slippage and return result"""
        if expected_price == 0:
            return {'allowed': True, 'slippage_bps': 0}
        
        # Calculate slippage
        if side == OrderSide.BUY:
            slippage = (actual_price - expected_price) / expected_price
        else:
            slippage = (expected_price - actual_price) / expected_price
        
        slippage_bps = slippage * 10000
        
        # Record
        self.slippage_history.append(slippage_bps)
        if len(self.slippage_history) > self.max_history:
            self.slippage_history.pop(0)
        
        # Check limits
        result = {
            'slippage_bps': slippage_bps,
            'allowed': slippage_bps <= self.max_slippage_bps,
            'warning': slippage_bps > self.warning_slippage_bps
        }
        
        if result['warning']:
            logger.warning(f"High slippage: {slippage_bps:.1f} bps")
        
        if not result['allowed']:
            logger.error(f"Slippage exceeded limit: {slippage_bps:.1f} bps > {self.max_slippage_bps} bps")
        
        return result
    
    def get_average_slippage(self) -> float:
        """Get average slippage"""
        if not self.slippage_history:
            return 0.0
        return sum(self.slippage_history) / len(self.slippage_history)
    
    def adjust_price_for_slippage(self, price: float, side: OrderSide,
                                  buffer_bps: float = 10) -> float:
        """Adjust price to account for expected slippage"""
        avg_slippage = self.get_average_slippage()
        total_adjustment = (avg_slippage + buffer_bps) / 10000
        
        if side == OrderSide.BUY:
            return price * (1 + total_adjustment)
        else:
            return price * (1 - total_adjustment)


class ExecutionLayer:
    """
    Master coordinator for Layer 4: Execution
    
    Orchestrates all execution components
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.router = SmartRouter(config.get('router', {}))
        self.order_manager = OrderManager(config.get('orders', {}))
        self.fill_tracker = FillTracker(config.get('fills', {}))
        self.slippage_protector = SlippageProtector(config.get('slippage', {}))
        
        # Broker interface
        self._broker = None
        self._init_broker()
        
        # Statistics
        self.stats = {
            'orders_submitted': 0,
            'orders_filled': 0,
            'orders_cancelled': 0,
            'total_slippage_bps': 0.0
        }
        
        logger.info("Execution Layer initialized")
    
    def _init_broker(self):
        """Initialize broker connection"""
        try:
            from trading_bot.brokers.broker_adapter import BrokerAdapter
            broker_type = self.config.get('broker_type', 'mock')
            self._broker = BrokerAdapter.create(broker_type, self.config.get('broker', {}))
            logger.info(f"Broker initialized: {broker_type}")
        except Exception as e:
            logger.warning(f"Broker initialization failed: {e}")
    
    async def execute(self, symbol: str, side: OrderSide, quantity: float,
                     order_type: OrderType = OrderType.MARKET,
                     price: Optional[float] = None,
                     algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET,
                     **kwargs) -> ExecutionResult:
        """
        Execute a trade
        
        Pipeline:
        1. Create order
        2. Route to venue
        3. Submit to broker
        4. Track fills
        5. Check slippage
        """
        start_time = datetime.now()
        
        # Step 1: Create order
        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            algorithm=algorithm,
            **kwargs
        )
        
        # Step 2: Route
        venue = self.router.route(order)
        order.metadata['venue'] = venue
        
        # Step 3: Submit to broker
        try:
            if self._broker:
                result = await self._broker.submit_order(order)
                self.order_manager.update_status(order.order_id, OrderStatus.SUBMITTED)
                self.stats['orders_submitted'] += 1
            else:
                # Simulate fill for testing
                result = self._simulate_fill(order)
        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            self.order_manager.update_status(order.order_id, OrderStatus.REJECTED)
            return ExecutionResult(
                success=False,
                order=order,
                message=str(e)
            )
        
        # Step 4: Wait for fills (simplified)
        fills = await self._wait_for_fills(order)
        
        # Step 5: Check slippage
        if fills and price:
            avg_fill_price = sum(f.price * f.quantity for f in fills) / sum(f.quantity for f in fills)
            slippage_result = self.slippage_protector.check_slippage(price, avg_fill_price, side)
            slippage_bps = slippage_result['slippage_bps']
            self.stats['total_slippage_bps'] += slippage_bps
        else:
            slippage_bps = 0.0
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update stats
        if order.status == OrderStatus.FILLED:
            self.stats['orders_filled'] += 1
        
        return ExecutionResult(
            success=order.status == OrderStatus.FILLED,
            order=order,
            fills=fills,
            message="Order executed successfully" if order.status == OrderStatus.FILLED else "Order pending",
            slippage_bps=slippage_bps,
            execution_time_ms=execution_time
        )
    
    def _simulate_fill(self, order: Order) -> Dict[str, Any]:
        """Simulate order fill for testing"""
        fill = Fill(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price or 1.0,
            timestamp=datetime.now()
        )
        
        self.fill_tracker.record_fill(fill)
        self.order_manager.record_fill(order.order_id, fill)
        
        return {'fill': fill}
    
    async def _wait_for_fills(self, order: Order, timeout: float = 30.0) -> List[Fill]:
        """Wait for order fills"""
        start = datetime.now()
        
        while (datetime.now() - start).total_seconds() < timeout:
            if order.is_complete:
                break
            await asyncio.sleep(0.1)
        
        return self.fill_tracker.get_fills_for_order(order.order_id)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if self._broker:
            try:
                await self._broker.cancel_order(order_id)
            except Exception as e:
                logger.error(f"Cancel failed: {e}")
                return False
        
        result = self.order_manager.cancel_order(order_id)
        if result:
            self.stats['orders_cancelled'] += 1
        return result
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        return self.order_manager.get_open_orders(symbol)
    
    def get_status(self) -> Dict[str, Any]:
        """Get execution layer status"""
        return {
            'stats': self.stats,
            'open_orders': len(self.order_manager.get_open_orders()),
            'average_slippage_bps': self.slippage_protector.get_average_slippage(),
            'broker_connected': self._broker is not None
        }
