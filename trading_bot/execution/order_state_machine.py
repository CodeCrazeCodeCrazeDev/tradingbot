"""
Order State Machine
===================

Formal order lifecycle management with state transitions,
event handling, and audit trail.

States:
- CREATED: Order created but not submitted
- PENDING: Submitted to broker, awaiting acknowledgment
- ACKNOWLEDGED: Broker acknowledged receipt
- PARTIALLY_FILLED: Some quantity filled
- FILLED: Fully filled
- CANCELLED: Cancelled by user or system
- REJECTED: Rejected by broker
- EXPIRED: Order expired
- FAILED: System failure

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum, auto
import uuid
import json
from collections import deque
import threading

logger = logging.getLogger(__name__)


class OrderState(Enum):
    """Order lifecycle states"""
    CREATED = "created"
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FAILED = "failed"


class OrderEvent(Enum):
    """Events that trigger state transitions"""
    SUBMIT = "submit"
    ACK = "acknowledge"
    PARTIAL_FILL = "partial_fill"
    FILL = "fill"
    CANCEL_REQUEST = "cancel_request"
    CANCEL_CONFIRM = "cancel_confirm"
    REJECT = "reject"
    EXPIRE = "expire"
    FAIL = "fail"
    AMEND = "amend"
    TIMEOUT = "timeout"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    OCO = "oco"
    BRACKET = "bracket"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class TimeInForce(Enum):
    """Time in force options"""
    GTC = "good_till_cancelled"
    DAY = "day"
    IOC = "immediate_or_cancel"
    FOK = "fill_or_kill"
    GTD = "good_till_date"


@dataclass
class OrderFill:
    """Individual fill record"""
    fill_id: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    venue: str = ""
    liquidity: str = ""  # "maker" or "taker"
    
    def to_dict(self) -> Dict:
        return {
            'fill_id': self.fill_id,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'timestamp': self.timestamp.isoformat(),
            'venue': self.venue,
            'liquidity': self.liquidity
        }


@dataclass
class StateTransition:
    """Record of a state transition"""
    from_state: OrderState
    to_state: OrderState
    event: OrderEvent
    timestamp: datetime
    reason: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'from_state': self.from_state.value,
            'to_state': self.to_state.value,
            'event': self.event.value,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'metadata': self.metadata
        }


@dataclass
class Order:
    """Order with full lifecycle tracking"""
    # Identity
    order_id: str
    client_order_id: str
    broker_order_id: Optional[str] = None
    
    # Order details
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: float = 0.0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    
    # State
    state: OrderState = OrderState.CREATED
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    average_fill_price: float = 0.0
    total_commission: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    
    # Expiration
    expire_time: Optional[datetime] = None
    
    # Tracking
    fills: List[OrderFill] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)
    
    # Metadata
    strategy_id: str = ""
    magic_number: int = 0
    comment: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    # Parent/child relationships
    parent_order_id: Optional[str] = None
    child_order_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.remaining_quantity = self.quantity
    
    def is_terminal(self) -> bool:
        """Check if order is in terminal state"""
        return self.state in [
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
            OrderState.FAILED
        ]
    
    def is_active(self) -> bool:
        """Check if order is active"""
        return self.state in [
            OrderState.PENDING,
            OrderState.ACKNOWLEDGED,
            OrderState.PARTIALLY_FILLED
        ]
    
    def get_fill_rate(self) -> float:
        """Get fill rate as percentage"""
        if self.quantity <= 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100
    
    def get_duration(self) -> Optional[timedelta]:
        """Get order duration"""
        if self.filled_at:
            return self.filled_at - self.created_at
        elif self.cancelled_at:
            return self.cancelled_at - self.created_at
        elif self.is_active():
            return datetime.now() - self.created_at
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'broker_order_id': self.broker_order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force.value,
            'state': self.state.value,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'average_fill_price': self.average_fill_price,
            'total_commission': self.total_commission,
            'created_at': self.created_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'fills': [f.to_dict() for f in self.fills],
            'transitions': [t.to_dict() for t in self.transitions],
            'strategy_id': self.strategy_id,
            'magic_number': self.magic_number,
            'comment': self.comment,
            'tags': self.tags,
            'metadata': self.metadata
        }


class OrderStateMachine:
    """
    Manages order state transitions with validation and callbacks
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        OrderState.CREATED: {
            OrderEvent.SUBMIT: OrderState.PENDING,
            OrderEvent.FAIL: OrderState.FAILED,
            OrderEvent.CANCEL_REQUEST: OrderState.CANCELLED
        },
        OrderState.PENDING: {
            OrderEvent.ACK: OrderState.ACKNOWLEDGED,
            OrderEvent.REJECT: OrderState.REJECTED,
            OrderEvent.FILL: OrderState.FILLED,
            OrderEvent.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
            OrderEvent.CANCEL_CONFIRM: OrderState.CANCELLED,
            OrderEvent.TIMEOUT: OrderState.FAILED,
            OrderEvent.FAIL: OrderState.FAILED
        },
        OrderState.ACKNOWLEDGED: {
            OrderEvent.FILL: OrderState.FILLED,
            OrderEvent.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
            OrderEvent.CANCEL_CONFIRM: OrderState.CANCELLED,
            OrderEvent.EXPIRE: OrderState.EXPIRED,
            OrderEvent.REJECT: OrderState.REJECTED,
            OrderEvent.FAIL: OrderState.FAILED
        },
        OrderState.PARTIALLY_FILLED: {
            OrderEvent.FILL: OrderState.FILLED,
            OrderEvent.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
            OrderEvent.CANCEL_CONFIRM: OrderState.CANCELLED,
            OrderEvent.EXPIRE: OrderState.EXPIRED,
            OrderEvent.FAIL: OrderState.FAILED
        }
    }
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.orders_by_broker_id: Dict[str, str] = {}
        self.orders_by_client_id: Dict[str, str] = {}
        
        # Callbacks
        self.on_state_change: List[Callable] = []
        self.on_fill: List[Callable] = []
        self.on_complete: List[Callable] = []
        self.on_error: List[Callable] = []
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'orders_created': 0,
            'orders_filled': 0,
            'orders_cancelled': 0,
            'orders_rejected': 0,
            'total_fills': 0,
            'total_commission': 0.0
        }
        
        logger.info("OrderStateMachine initialized")
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        expire_time: Optional[datetime] = None,
        strategy_id: str = "",
        magic_number: int = 0,
        comment: str = "",
        tags: List[str] = None,
        metadata: Dict = None,
        parent_order_id: Optional[str] = None
    ) -> Order:
        """Create a new order"""
        with self._lock:
            order_id = str(uuid.uuid4())
            client_order_id = f"CLT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order_id[:8]}"
            
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
                expire_time=expire_time,
                strategy_id=strategy_id,
                magic_number=magic_number,
                comment=comment,
                tags=tags or [],
                metadata=metadata or {},
                parent_order_id=parent_order_id
            )
            
            self.orders[order_id] = order
            self.orders_by_client_id[client_order_id] = order_id
            self.stats['orders_created'] += 1
            
            logger.info(f"Order created: {order_id} {symbol} {side.value} {quantity}")
            
            return order
    
    def transition(
        self,
        order_id: str,
        event: OrderEvent,
        reason: str = "",
        metadata: Dict = None,
        fill: Optional[OrderFill] = None,
        broker_order_id: Optional[str] = None
    ) -> bool:
        """
        Attempt to transition order to new state
        
        Returns True if transition was successful
        """
        with self._lock:
            order = self.orders.get(order_id)
            if not order:
                logger.error(f"Order not found: {order_id}")
                return False
            
            # Check if transition is valid
            valid_events = self.VALID_TRANSITIONS.get(order.state, {})
            if event not in valid_events:
                logger.warning(
                    f"Invalid transition: {order.state.value} + {event.value} "
                    f"for order {order_id}"
                )
                return False
            
            # Get new state
            new_state = valid_events[event]
            old_state = order.state
            
            # Record transition
            transition = StateTransition(
                from_state=old_state,
                to_state=new_state,
                event=event,
                timestamp=datetime.now(),
                reason=reason,
                metadata=metadata or {}
            )
            order.transitions.append(transition)
            
            # Update state
            order.state = new_state
            
            # Update timestamps
            if event == OrderEvent.SUBMIT:
                order.submitted_at = datetime.now()
            elif event == OrderEvent.ACK:
                order.acknowledged_at = datetime.now()
                if broker_order_id:
                    order.broker_order_id = broker_order_id
                    self.orders_by_broker_id[broker_order_id] = order_id
            elif event in [OrderEvent.FILL, OrderEvent.PARTIAL_FILL]:
                if fill:
                    self._process_fill(order, fill)
                if new_state == OrderState.FILLED:
                    order.filled_at = datetime.now()
                    self.stats['orders_filled'] += 1
            elif event == OrderEvent.CANCEL_CONFIRM:
                order.cancelled_at = datetime.now()
                self.stats['orders_cancelled'] += 1
            elif event == OrderEvent.REJECT:
                self.stats['orders_rejected'] += 1
            elif event == OrderEvent.EXPIRE:
                order.expired_at = datetime.now()
            
            logger.info(
                f"Order {order_id} transitioned: {old_state.value} -> {new_state.value} "
                f"({event.value})"
            )
            
            # Fire callbacks
            self._fire_callbacks(order, old_state, new_state, event, fill)
            
            return True
    
    def _process_fill(self, order: Order, fill: OrderFill):
        """Process a fill"""
        order.fills.append(fill)
        order.filled_quantity += fill.quantity
        order.remaining_quantity = order.quantity - order.filled_quantity
        order.total_commission += fill.commission
        
        # Calculate average fill price
        total_value = sum(f.quantity * f.price for f in order.fills)
        total_qty = sum(f.quantity for f in order.fills)
        if total_qty > 0:
            order.average_fill_price = total_value / total_qty
        
        self.stats['total_fills'] += 1
        self.stats['total_commission'] += fill.commission
    
    def _fire_callbacks(
        self,
        order: Order,
        old_state: OrderState,
        new_state: OrderState,
        event: OrderEvent,
        fill: Optional[OrderFill]
    ):
        """Fire registered callbacks"""
        # State change callbacks
        for callback in self.on_state_change:
            try:
                callback(order, old_state, new_state, event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Fill callbacks
        if fill:
            for callback in self.on_fill:
                try:
                    callback(order, fill)
                except Exception as e:
                    logger.error(f"Fill callback error: {e}")
        
        # Completion callbacks
        if order.is_terminal():
            for callback in self.on_complete:
                try:
                    callback(order)
                except Exception as e:
                    logger.error(f"Complete callback error: {e}")
        
        # Error callbacks
        if new_state in [OrderState.REJECTED, OrderState.FAILED]:
            for callback in self.on_error:
                try:
                    callback(order, event)
                except Exception as e:
                    logger.error(f"Error callback error: {e}")
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_order_by_broker_id(self, broker_order_id: str) -> Optional[Order]:
        """Get order by broker order ID"""
        order_id = self.orders_by_broker_id.get(broker_order_id)
        if order_id:
            return self.orders.get(order_id)
        return None
    
    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Get order by client order ID"""
        order_id = self.orders_by_client_id.get(client_order_id)
        if order_id:
            return self.orders.get(order_id)
        return None
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders"""
        return [o for o in self.orders.values() if o.is_active()]
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Get all orders for a symbol"""
        return [o for o in self.orders.values() if o.symbol == symbol]
    
    def get_orders_by_strategy(self, strategy_id: str) -> List[Order]:
        """Get all orders for a strategy"""
        return [o for o in self.orders.values() if o.strategy_id == strategy_id]
    
    def cancel_order(self, order_id: str, reason: str = "User requested") -> bool:
        """Request order cancellation"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if order.is_terminal():
            logger.warning(f"Cannot cancel terminal order: {order_id}")
            return False
        
        # For created orders, cancel immediately
        if order.state == OrderState.CREATED:
            return self.transition(order_id, OrderEvent.CANCEL_REQUEST, reason)
        
        # For active orders, this just marks intent - actual cancellation
        # happens when broker confirms
        logger.info(f"Cancel requested for order: {order_id}")
        return True
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all active orders, optionally filtered by symbol"""
        cancelled = 0
        for order in self.get_active_orders():
            if symbol is None or order.symbol == symbol:
                if self.cancel_order(order.order_id):
                    cancelled += 1
        return cancelled
    
    def check_expirations(self) -> List[str]:
        """Check and expire orders past their expiration time"""
        expired = []
        now = datetime.now()
        
        for order in self.get_active_orders():
            if order.expire_time and now > order.expire_time:
                if self.transition(order.order_id, OrderEvent.EXPIRE, "Order expired"):
                    expired.append(order.order_id)
        
        return expired
    
    def check_timeouts(self, timeout_seconds: int = 60) -> List[str]:
        """Check for orders stuck in pending state"""
        timed_out = []
        now = datetime.now()
        
        for order in self.orders.values():
            if order.state == OrderState.PENDING:
                if order.submitted_at:
                    elapsed = (now - order.submitted_at).total_seconds()
                    if elapsed > timeout_seconds:
                        if self.transition(
                            order.order_id,
                            OrderEvent.TIMEOUT,
                            f"Order timed out after {elapsed:.0f}s"
                        ):
                            timed_out.append(order.order_id)
        
        return timed_out
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        active = len(self.get_active_orders())
        total = len(self.orders)
        
        return {
            **self.stats,
            'active_orders': active,
            'total_orders': total,
            'fill_rate': self.stats['orders_filled'] / total * 100 if total > 0 else 0,
            'rejection_rate': self.stats['orders_rejected'] / total * 100 if total > 0 else 0
        }
    
    def register_callback(
        self,
        event_type: str,
        callback: Callable
    ):
        """Register a callback"""
        if event_type == 'state_change':
            self.on_state_change.append(callback)
        elif event_type == 'fill':
            self.on_fill.append(callback)
        elif event_type == 'complete':
            self.on_complete.append(callback)
        elif event_type == 'error':
            self.on_error.append(callback)
    
    def cleanup_old_orders(self, days: int = 7):
        """Remove old terminal orders"""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for order_id, order in self.orders.items():
            if order.is_terminal() and order.created_at < cutoff:
                to_remove.append(order_id)
        
        for order_id in to_remove:
            order = self.orders.pop(order_id)
            if order.broker_order_id:
                self.orders_by_broker_id.pop(order.broker_order_id, None)
            self.orders_by_client_id.pop(order.client_order_id, None)
        
        logger.info(f"Cleaned up {len(to_remove)} old orders")
        return len(to_remove)


class BracketOrderManager:
    """
    Manages bracket orders (entry + stop loss + take profit)
    """
    
    def __init__(self, state_machine: OrderStateMachine):
        self.state_machine = state_machine
        self.brackets: Dict[str, Dict[str, str]] = {}  # bracket_id -> {entry, sl, tp}
        
        # Register callback to manage child orders
        state_machine.register_callback('fill', self._on_fill)
        state_machine.register_callback('complete', self._on_complete)
    
    def create_bracket_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        entry_price: Optional[float],
        stop_loss: float,
        take_profit: float,
        order_type: OrderType = OrderType.MARKET,
        **kwargs
    ) -> Dict[str, Order]:
        """Create a bracket order (entry + SL + TP)"""
        bracket_id = str(uuid.uuid4())
        
        # Create entry order
        entry_order = self.state_machine.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=entry_price,
            metadata={'bracket_id': bracket_id, 'bracket_role': 'entry'},
            **kwargs
        )
        
        # Create stop loss order (opposite side)
        sl_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        sl_order = self.state_machine.create_order(
            symbol=symbol,
            side=sl_side,
            order_type=OrderType.STOP,
            quantity=quantity,
            stop_price=stop_loss,
            parent_order_id=entry_order.order_id,
            metadata={'bracket_id': bracket_id, 'bracket_role': 'stop_loss'},
            **kwargs
        )
        
        # Create take profit order (opposite side)
        tp_order = self.state_machine.create_order(
            symbol=symbol,
            side=sl_side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=take_profit,
            parent_order_id=entry_order.order_id,
            metadata={'bracket_id': bracket_id, 'bracket_role': 'take_profit'},
            **kwargs
        )
        
        # Link child orders
        entry_order.child_order_ids = [sl_order.order_id, tp_order.order_id]
        
        # Store bracket
        self.brackets[bracket_id] = {
            'entry': entry_order.order_id,
            'stop_loss': sl_order.order_id,
            'take_profit': tp_order.order_id
        }
        
        logger.info(f"Bracket order created: {bracket_id}")
        
        return {
            'entry': entry_order,
            'stop_loss': sl_order,
            'take_profit': tp_order,
            'bracket_id': bracket_id
        }
    
    def _on_fill(self, order: Order, fill: OrderFill):
        """Handle fill events for bracket orders"""
        bracket_id = order.metadata.get('bracket_id')
        if not bracket_id:
            return
        
        bracket = self.brackets.get(bracket_id)
        if not bracket:
            return
        
        role = order.metadata.get('bracket_role')
        
        if role == 'entry' and order.state == OrderState.FILLED:
            # Entry filled - activate SL and TP orders
            logger.info(f"Bracket entry filled, activating SL/TP: {bracket_id}")
            # In real implementation, submit SL and TP to broker
        
        elif role in ['stop_loss', 'take_profit'] and order.state == OrderState.FILLED:
            # SL or TP filled - cancel the other
            other_role = 'take_profit' if role == 'stop_loss' else 'stop_loss'
            other_order_id = bracket[other_role]
            self.state_machine.cancel_order(other_order_id, f"{role} filled, cancelling {other_role}")
    
    def _on_complete(self, order: Order):
        """Handle completion events for bracket orders"""
        bracket_id = order.metadata.get('bracket_id')
        if not bracket_id:
            return
        
        bracket = self.brackets.get(bracket_id)
        if not bracket:
            return
        
        # Check if all bracket orders are complete
        all_complete = all(
            self.state_machine.get_order(oid).is_terminal()
            for oid in bracket.values()
        )
        
        if all_complete:
            logger.info(f"Bracket order complete: {bracket_id}")
            # Could clean up bracket here


class OCOOrderManager:
    """
    Manages One-Cancels-Other orders
    """
    
    def __init__(self, state_machine: OrderStateMachine):
        self.state_machine = state_machine
        self.oco_groups: Dict[str, List[str]] = {}  # oco_id -> [order_ids]
        
        state_machine.register_callback('fill', self._on_fill)
    
    def create_oco_order(
        self,
        orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create an OCO order group"""
        oco_id = str(uuid.uuid4())
        created_orders = []
        
        for order_params in orders:
            order = self.state_machine.create_order(
                metadata={'oco_id': oco_id},
                **order_params
            )
            created_orders.append(order)
        
        self.oco_groups[oco_id] = [o.order_id for o in created_orders]
        
        logger.info(f"OCO order created: {oco_id} with {len(created_orders)} orders")
        
        return {
            'oco_id': oco_id,
            'orders': created_orders
        }
    
    def _on_fill(self, order: Order, fill: OrderFill):
        """Handle fill events for OCO orders"""
        oco_id = order.metadata.get('oco_id')
        if not oco_id:
            return
        
        group = self.oco_groups.get(oco_id)
        if not group:
            return
        
        # Cancel all other orders in the group
        for order_id in group:
            if order_id != order.order_id:
                self.state_machine.cancel_order(
                    order_id,
                    f"OCO triggered by {order.order_id}"
                )
        
        logger.info(f"OCO triggered: {oco_id}")


# Singleton instance
_state_machine_instance: Optional[OrderStateMachine] = None


def get_order_state_machine() -> OrderStateMachine:
    """Get or create the order state machine singleton"""
    global _state_machine_instance
    if _state_machine_instance is None:
        _state_machine_instance = OrderStateMachine()
    return _state_machine_instance


# Export
__all__ = [
    'OrderStateMachine',
    'Order',
    'OrderState',
    'OrderEvent',
    'OrderType',
    'OrderSide',
    'TimeInForce',
    'OrderFill',
    'StateTransition',
    'BracketOrderManager',
    'OCOOrderManager',
    'get_order_state_machine'
]
