"""
Order Manager - Centralized Order Lifecycle Management
======================================================

Manages the complete lifecycle of orders:
1. Order creation and validation
2. Order submission and tracking
3. Fill management and reconciliation
4. Order modification and cancellation
5. Position tracking
"""

import logging
import threading
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import uuid
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()
    TRAILING_STOP = auto()


class OrderSide(Enum):
    """Order side"""
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    """Order status"""
    PENDING = auto()        # Created but not submitted
    SUBMITTED = auto()      # Sent to broker
    ACCEPTED = auto()       # Accepted by broker
    PARTIALLY_FILLED = auto()  # Partially executed
    FILLED = auto()         # Fully executed
    CANCELLED = auto()      # Cancelled
    REJECTED = auto()       # Rejected by broker
    EXPIRED = auto()        # Expired
    ERROR = auto()          # Error state


class TimeInForce(Enum):
    """Time in force"""
    GTC = auto()    # Good till cancelled
    DAY = auto()    # Day order
    IOC = auto()    # Immediate or cancel
    FOK = auto()    # Fill or kill
    GTD = auto()    # Good till date


@dataclass
class Order:
    """Represents a trading order"""
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
    average_fill_price: float = 0.0
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    broker_order_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if order is active"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]
    
    @property
    def is_complete(self) -> bool:
        """Check if order is complete"""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.ERROR
        ]
    
    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity to fill"""
        return self.quantity - self.filled_quantity
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage"""
        return (self.filled_quantity / self.quantity * 100) if self.quantity > 0 else 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "order_id": self.order_id,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side.name,
            "order_type": self.order_type.name,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "time_in_force": self.time_in_force.name,
            "status": self.status.name,
            "filled_quantity": self.filled_quantity,
            "average_fill_price": self.average_fill_price,
            "commission": self.commission,
            "created_at": self.created_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "broker_order_id": self.broker_order_id,
            "strategy_id": self.strategy_id,
            "error_message": self.error_message
        }


@dataclass
class Fill:
    """Represents an order fill"""
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    broker_fill_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.name,
            "quantity": self.quantity,
            "price": self.price,
            "commission": self.commission,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Position:
    """Represents a position"""
    symbol: str
    quantity: float
    average_price: float
    side: OrderSide
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    market_value: float = 0.0
    cost_basis: float = 0.0
    opened_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "side": self.side.name,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "opened_at": self.opened_at.isoformat()
        }


class OrderManager:
    """
    Centralized order management system.
    
    Features:
    - Order lifecycle management
    - Fill tracking and reconciliation
    - Position tracking
    - Order validation
    - Event callbacks
    """
    
    def __init__(
        self,
        broker_adapter=None,
        max_orders_per_symbol: int = 10,
        max_daily_orders: int = 100,
        order_timeout_seconds: float = 300,
        persist_orders: bool = True,
        orders_file: Optional[str] = None
    ):
        """
        Initialize order manager.
        
        Args:
            broker_adapter: Broker adapter for order execution
            max_orders_per_symbol: Maximum active orders per symbol
            max_daily_orders: Maximum orders per day
            order_timeout_seconds: Timeout for pending orders
            persist_orders: Whether to persist orders to file
            orders_file: File path for order persistence
        """
        self._lock = threading.RLock()
        self.broker = broker_adapter
        self.max_orders_per_symbol = max_orders_per_symbol
        self.max_daily_orders = max_daily_orders
        self.order_timeout = order_timeout_seconds
        self.persist_orders = persist_orders
        self.orders_file = Path(orders_file) if orders_file else Path("orders.json")
        
        # Order storage
        self._orders: Dict[str, Order] = {}
        self._orders_by_symbol: Dict[str, List[str]] = defaultdict(list)
        self._orders_by_status: Dict[OrderStatus, List[str]] = defaultdict(list)
        
        # Fill storage
        self._fills: Dict[str, Fill] = {}
        self._fills_by_order: Dict[str, List[str]] = defaultdict(list)
        
        # Position storage
        self._positions: Dict[str, Position] = {}
        
        # Daily tracking
        self._daily_order_count = 0
        self._last_reset_date: Optional[str] = None
        
        # Callbacks
        self._on_order_created: Optional[Callable] = None
        self._on_order_submitted: Optional[Callable] = None
        self._on_order_filled: Optional[Callable] = None
        self._on_order_cancelled: Optional[Callable] = None
        self._on_order_rejected: Optional[Callable] = None
        self._on_fill: Optional[Callable] = None
        self._on_position_update: Optional[Callable] = None
        
        # Load persisted orders
        self._load_orders()
        
        logger.info("OrderManager initialized")
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        strategy_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Order:
        """
        Create a new order.
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: Order type
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force
            strategy_id: Strategy identifier
            metadata: Additional metadata
            
        Returns:
            Created Order object
        """
        with self._lock:
            # Reset daily counter if new day
            self._check_daily_reset()
            
            # Validate order
            validation_error = self._validate_order(symbol, quantity, order_type, price)
            if validation_error:
                raise ValueError(validation_error)
            
            # Generate IDs
            order_id = str(uuid.uuid4())
            client_order_id = f"CLT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{order_id[:8]}"
            
            # Create order
            order = Order(
                order_id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
                strategy_id=strategy_id,
                metadata=metadata or {}
            )
            
            # Store order
            self._orders[order_id] = order
            self._orders_by_symbol[symbol].append(order_id)
            self._orders_by_status[OrderStatus.PENDING].append(order_id)
            
            logger.info(f"Order created: {order_id} - {side.name} {quantity} {symbol}")
            
            # Callback
            if self._on_order_created:
                try:
                    self._on_order_created(order)
                except Exception as e:
                    logger.error(f"Order created callback error: {e}")
            
            self._save_orders()
            return order
    
    def _validate_order(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType,
        price: Optional[float]
    ) -> Optional[str]:
        """Validate order parameters"""
        if not symbol:
            return "Symbol is required"
        
        if quantity <= 0:
            return "Quantity must be positive"
        
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price is None:
            return f"Price is required for {order_type.name} orders"
        
        # Check daily limit
        if self._daily_order_count >= self.max_daily_orders:
            return f"Daily order limit reached: {self.max_daily_orders}"
        
        # Check per-symbol limit
        active_orders = [
            oid for oid in self._orders_by_symbol.get(symbol, [])
            if self._orders.get(oid, Order("", "", "", OrderSide.BUY, OrderType.MARKET, 0)).is_active
        ]
        if len(active_orders) >= self.max_orders_per_symbol:
            return f"Max active orders for {symbol} reached: {self.max_orders_per_symbol}"
        
        return None
    
    async def submit_order(self, order_id: str) -> bool:
        """
        Submit an order to the broker.
        
        Args:
            order_id: Order ID to submit
            
        Returns:
            True if submitted successfully
        """
        with self._lock:
            pass
        try:
            order = self._orders.get(order_id)
            if not order:
                logger.error(f"Order not found: {order_id}")
                return False
            
            if order.status != OrderStatus.PENDING:
                logger.warning(f"Order {order_id} is not pending: {order.status.name}")
                return False
        
            # Submit to broker
            if self.broker:
                if hasattr(self.broker, 'submit_order'):
                    result = await self.broker.submit_order(order)
                elif hasattr(self.broker, 'place_order'):
                    result = await self.broker.place_order(
                        symbol=order.symbol,
                        side=order.side.name.lower(),
                        quantity=order.quantity,
                        order_type=order.order_type.name.lower(),
                        price=order.price
                    )
                else:
                    logger.error("Broker does not support order submission")
                    return False
                
                if result:
                    order.broker_order_id = result.get('order_id') if isinstance(result, dict) else str(result)
            
            with self._lock:
                order.status = OrderStatus.SUBMITTED
                order.submitted_at = datetime.utcnow()
                self._update_order_status_index(order_id, OrderStatus.PENDING, OrderStatus.SUBMITTED)
                self._daily_order_count += 1
            
            logger.info(f"Order submitted: {order_id}")
            
            if self._on_order_submitted:
                try:
                    self._on_order_submitted(order)
                except Exception as e:
                    logger.error(f"Order submitted callback error: {e}")
            
            self._save_orders()
            return True
            
        except Exception as e:
            logger.error(f"Error submitting order {order_id}: {e}")
            with self._lock:
                order.status = OrderStatus.ERROR
                order.error_message = str(e)
                self._update_order_status_index(order_id, OrderStatus.PENDING, OrderStatus.ERROR)
            return False
    
    def record_fill(
        self,
        order_id: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        broker_fill_id: Optional[str] = None
    ) -> Optional[Fill]:
        """
        Record a fill for an order.
        
        Args:
            order_id: Order ID
            quantity: Fill quantity
            price: Fill price
            commission: Commission
            broker_fill_id: Broker's fill ID
            
        Returns:
            Fill object if recorded
        """
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                logger.error(f"Order not found for fill: {order_id}")
                return None
            
            # Create fill
            fill_id = str(uuid.uuid4())
            fill = Fill(
                fill_id=fill_id,
                order_id=order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=quantity,
                price=price,
                commission=commission,
                timestamp=datetime.utcnow(),
                broker_fill_id=broker_fill_id
            )
            
            # Store fill
            self._fills[fill_id] = fill
            self._fills_by_order[order_id].append(fill_id)
            
            # Update order
            old_status = order.status
            order.filled_quantity += quantity
            order.commission += commission
            
            # Calculate average fill price
            total_value = (order.average_fill_price * (order.filled_quantity - quantity)) + (price * quantity)
            order.average_fill_price = total_value / order.filled_quantity if order.filled_quantity > 0 else 0
            
            # Update status
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.utcnow()
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
            
            self._update_order_status_index(order_id, old_status, order.status)
            
            logger.info(f"Fill recorded: {fill_id} - {quantity} @ {price} for order {order_id}")
            
            # Update position
            self._update_position(order.symbol, order.side, quantity, price)
            
            # Callbacks
            if self._on_fill:
                try:
                    self._on_fill(fill)
                except Exception as e:
                    logger.error(f"Fill callback error: {e}")
            
            if order.status == OrderStatus.FILLED and self._on_order_filled:
                try:
                    self._on_order_filled(order)
                except Exception as e:
                    logger.error(f"Order filled callback error: {e}")
            
            self._save_orders()
            return fill
    
    def cancel_order(self, order_id: str, reason: str = "User requested") -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancelled
        """
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                logger.error(f"Order not found: {order_id}")
                return False
            
            if not order.is_active:
                logger.warning(f"Order {order_id} is not active: {order.status.name}")
                return False
            
            old_status = order.status
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            order.metadata['cancel_reason'] = reason
            
            self._update_order_status_index(order_id, old_status, OrderStatus.CANCELLED)
            
            logger.info(f"Order cancelled: {order_id} - {reason}")
            
            if self._on_order_cancelled:
                try:
                    self._on_order_cancelled(order)
                except Exception as e:
                    logger.error(f"Order cancelled callback error: {e}")
            
            self._save_orders()
            return True
    
    def _update_position(self, symbol: str, side: OrderSide, quantity: float, price: float):
        """Update position based on fill"""
        with self._lock:
            if symbol not in self._positions:
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=0,
                    average_price=0,
                    side=side
                )
            
            position = self._positions[symbol]
            
            if side == OrderSide.BUY:
                # Buying increases position
                total_cost = (position.quantity * position.average_price) + (quantity * price)
                position.quantity += quantity
                position.average_price = total_cost / position.quantity if position.quantity > 0 else 0
                position.side = OrderSide.BUY
            else:
                # Selling decreases position
                position.quantity -= quantity
                if position.quantity < 0:
                    # Flipped to short
                    position.side = OrderSide.SELL
                    position.quantity = abs(position.quantity)
                    position.average_price = price
            
            position.cost_basis = position.quantity * position.average_price
            position.last_updated = datetime.utcnow()
            
            # Remove position if closed
            if position.quantity == 0:
                del self._positions[symbol]
            
            if self._on_position_update:
                try:
                    self._on_position_update(position if symbol in self._positions else None, symbol)
                except Exception as e:
                    logger.error(f"Position update callback error: {e}")
    
    def _update_order_status_index(self, order_id: str, old_status: OrderStatus, new_status: OrderStatus):
        """Update order status index"""
        if order_id in self._orders_by_status.get(old_status, []):
            self._orders_by_status[old_status].remove(order_id)
        self._orders_by_status[new_status].append(order_id)
    
    def _check_daily_reset(self):
        """Reset daily counter if new day"""
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        if self._last_reset_date != current_date:
            self._daily_order_count = 0
            self._last_reset_date = current_date
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Get all orders for a symbol"""
        order_ids = self._orders_by_symbol.get(symbol, [])
        return [self._orders[oid] for oid in order_ids if oid in self._orders]
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders"""
        return [o for o in self._orders.values() if o.is_active]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self._positions.values())
    
    def get_fills_for_order(self, order_id: str) -> List[Fill]:
        """Get all fills for an order"""
        fill_ids = self._fills_by_order.get(order_id, [])
        return [self._fills[fid] for fid in fill_ids if fid in self._fills]
    
    def get_stats(self) -> Dict:
        """Get order manager statistics"""
        return {
            "total_orders": len(self._orders),
            "active_orders": len([o for o in self._orders.values() if o.is_active]),
            "filled_orders": len(self._orders_by_status.get(OrderStatus.FILLED, [])),
            "cancelled_orders": len(self._orders_by_status.get(OrderStatus.CANCELLED, [])),
            "rejected_orders": len(self._orders_by_status.get(OrderStatus.REJECTED, [])),
            "total_fills": len(self._fills),
            "open_positions": len(self._positions),
            "daily_order_count": self._daily_order_count,
            "max_daily_orders": self.max_daily_orders
        }
    
    def _save_orders(self):
        """Save orders to file"""
        if not self.persist_orders:
            return
        try:
        
            data = {
                "orders": {oid: o.to_dict() for oid, o in self._orders.items()},
                "fills": {fid: f.to_dict() for fid, f in self._fills.items()},
                "positions": {s: p.to_dict() for s, p in self._positions.items()},
                "daily_order_count": self._daily_order_count,
                "last_reset_date": self._last_reset_date
            }
            
            self.orders_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.orders_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save orders: {e}")
    
    def _load_orders(self):
        """Load orders from file"""
        if not self.persist_orders or not self.orders_file.exists():
            return
        try:
        
            with open(self.orders_file, 'r') as f:
                data = json.load(f)
            
            self._daily_order_count = data.get("daily_order_count", 0)
            self._last_reset_date = data.get("last_reset_date")
            
            logger.info(f"Loaded {len(data.get('orders', {}))} orders from file")
            
        except Exception as e:
            logger.error(f"Failed to load orders: {e}")
    
    # Callback setters
    def on_order_created(self, callback: Callable):
        self._on_order_created = callback
    
    def on_order_submitted(self, callback: Callable):
        self._on_order_submitted = callback
    
    def on_order_filled(self, callback: Callable):
        self._on_order_filled = callback
    
    def on_order_cancelled(self, callback: Callable):
        self._on_order_cancelled = callback
    
    def on_fill(self, callback: Callable):
        self._on_fill = callback
    
    def on_position_update(self, callback: Callable):
        self._on_position_update = callback


# Global instance
_global_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    """Get global order manager instance"""
    global _global_order_manager
    if _global_order_manager is None:
        _global_order_manager = OrderManager()
    return _global_order_manager
