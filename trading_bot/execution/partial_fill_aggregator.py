"""
Partial Fill Aggregator System
Implements HI-EXE-005: Partial fill aggregator with timeouts

Tracks incomplete fills and aggregates partial executions to maintain
accurate position tracking. Critical for proper order management.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class FillStatus(Enum):
    """Order fill status"""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FULLY_FILLED = "fully_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class PartialFill:
    """Individual fill event"""
    fill_id: str
    order_id: str
    timestamp: datetime
    quantity: float
    price: float
    commission: float = 0.0
    venue: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fill_id': self.fill_id,
            'order_id': self.order_id,
            'timestamp': self.timestamp.isoformat(),
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'venue': self.venue,
            'metadata': self.metadata
        }


@dataclass
class AggregatedFill:
    """Aggregated fill information"""
    order_id: str
    symbol: str
    side: str
    total_quantity: float
    filled_quantity: float
    remaining_quantity: float
    average_price: float
    total_commission: float
    status: FillStatus
    fills: List[PartialFill]
    created_at: datetime
    last_fill_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    def fill_percentage(self) -> float:
        """Get fill percentage"""
        if self.total_quantity == 0:
            return 0.0
        return (self.filled_quantity / self.total_quantity) * 100
    
    def is_complete(self) -> bool:
        """Check if fully filled"""
        return abs(self.filled_quantity - self.total_quantity) < 1e-8
    
    def is_timeout(self) -> bool:
        """Check if timed out"""
        if not self.timeout_at:
            return False
        return datetime.now() >= self.timeout_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'total_quantity': self.total_quantity,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'fill_percentage': self.fill_percentage(),
            'average_price': self.average_price,
            'total_commission': self.total_commission,
            'status': self.status.value,
            'fill_count': len(self.fills),
            'created_at': self.created_at.isoformat(),
            'last_fill_at': self.last_fill_at.isoformat() if self.last_fill_at else None
        }


class PartialFillAggregator:
    """
    Aggregates partial fills and tracks incomplete orders
    
    Features:
    - Partial fill tracking per order
    - Average price calculation
    - Timeout management
    - Fill notifications
    - Position reconciliation
    """
    
    def __init__(self,
                 default_timeout_seconds: int = 300,
                 auto_cancel_on_timeout: bool = True,
                 cleanup_interval_seconds: int = 60):
        """
        Initialize partial fill aggregator
        
        Args:
            default_timeout_seconds: Default timeout for incomplete fills
            auto_cancel_on_timeout: Cancel orders that timeout
            cleanup_interval_seconds: How often to clean up old orders
        """
        self.default_timeout = default_timeout_seconds
        self.auto_cancel_on_timeout = auto_cancel_on_timeout
        self.cleanup_interval = cleanup_interval_seconds
        
        # Order tracking
        self.orders: Dict[str, AggregatedFill] = {}
        self.completed_orders: Dict[str, AggregatedFill] = {}
        
        # Callbacks
        self.on_partial_fill: List[Callable] = []
        self.on_complete_fill: List[Callable] = []
        self.on_timeout: List[Callable] = []
        
        # Statistics
        self.stats = {
            'total_orders': 0,
            'partial_fills': 0,
            'complete_fills': 0,
            'timeouts': 0,
            'total_fill_events': 0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Cleanup thread
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"Partial Fill Aggregator initialized (timeout: {default_timeout_seconds}s)")
    
    def register_order(self,
                      order_id: str,
                      symbol: str,
                      side: str,
                      quantity: float,
                      timeout_seconds: Optional[int] = None) -> AggregatedFill:
        """
        Register new order for fill tracking
        
        Args:
            order_id: Unique order ID
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Total order quantity
            timeout_seconds: Custom timeout (uses default if None)
        
        Returns:
            AggregatedFill instance
        """
        with self.lock:
            if order_id in self.orders:
                logger.warning(f"Order {order_id} already registered")
                return self.orders[order_id]
            
            timeout = timeout_seconds or self.default_timeout
            
            order = AggregatedFill(
                order_id=order_id,
                symbol=symbol,
                side=side,
                total_quantity=quantity,
                filled_quantity=0.0,
                remaining_quantity=quantity,
                average_price=0.0,
                total_commission=0.0,
                status=FillStatus.PENDING,
                fills=[],
                created_at=datetime.now(),
                timeout_at=datetime.now() + timedelta(seconds=timeout)
            )
            
            self.orders[order_id] = order
            self.stats['total_orders'] += 1
            
            logger.info(f"Registered order {order_id}: {symbol} {side} {quantity} "
                       f"(timeout: {timeout}s)")
            
            return order
    
    def add_fill(self,
                order_id: str,
                fill_id: str,
                quantity: float,
                price: float,
                commission: float = 0.0,
                venue: Optional[str] = None,
                metadata: Optional[Dict] = None) -> AggregatedFill:
        """
        Add fill event to order
        
        Args:
            order_id: Order ID
            fill_id: Unique fill ID
            quantity: Filled quantity
            price: Fill price
            commission: Commission paid
            venue: Execution venue
            metadata: Additional metadata
        
        Returns:
            Updated AggregatedFill
        """
        with self.lock:
            if order_id not in self.orders:
                logger.error(f"Order {order_id} not found for fill {fill_id}")
                raise ValueError(f"Order {order_id} not registered")
            
            order = self.orders[order_id]
            
            # Create fill record
            fill = PartialFill(
                fill_id=fill_id,
                order_id=order_id,
                timestamp=datetime.now(),
                quantity=quantity,
                price=price,
                commission=commission,
                venue=venue,
                metadata=metadata or {}
            )
            
            # Update aggregated data
            old_filled = order.filled_quantity
            order.fills.append(fill)
            order.filled_quantity += quantity
            order.remaining_quantity = order.total_quantity - order.filled_quantity
            order.total_commission += commission
            order.last_fill_at = datetime.now()
            
            # Calculate average price (weighted)
            if order.filled_quantity > 0:
                total_value = sum(f.quantity * f.price for f in order.fills)
                order.average_price = total_value / order.filled_quantity
            
            # Update status
            if order.is_complete():
                order.status = FillStatus.FULLY_FILLED
                self._complete_order(order_id)
                self.stats['complete_fills'] += 1
                logger.info(f"Order {order_id} fully filled at avg price {order.average_price:.5f}")
            else:
                order.status = FillStatus.PARTIALLY_FILLED
                self.stats['partial_fills'] += 1
                logger.info(f"Order {order_id} partially filled: {order.filled_quantity}/{order.total_quantity} "
                           f"({order.fill_percentage():.1f}%)")
            
            self.stats['total_fill_events'] += 1
            
            # Trigger callbacks
            if order.status == FillStatus.FULLY_FILLED:
                self._trigger_complete_callbacks(order)
            else:
                self._trigger_partial_callbacks(order)
            
            return order
    
    def get_order(self, order_id: str) -> Optional[AggregatedFill]:
        """Get order by ID"""
        with self.lock:
            return self.orders.get(order_id) or self.completed_orders.get(order_id)
    
    def get_incomplete_orders(self) -> List[AggregatedFill]:
        """Get all incomplete orders"""
        with self.lock:
            return [
                order for order in self.orders.values()
                if order.status in [FillStatus.PENDING, FillStatus.PARTIALLY_FILLED]
            ]
    
    def get_timed_out_orders(self) -> List[AggregatedFill]:
        """Get orders that have timed out"""
        with self.lock:
            return [
                order for order in self.orders.values()
                if order.is_timeout() and order.status != FillStatus.FULLY_FILLED
            ]
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order
        
        Args:
            order_id: Order to cancel
        
        Returns:
            True if cancelled
        """
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return False
            
            order.status = FillStatus.CANCELLED
            self._complete_order(order_id)
            
            logger.info(f"Order {order_id} cancelled (filled: {order.filled_quantity}/{order.total_quantity})")
            return True
    
    def _complete_order(self, order_id: str):
        """Move order to completed"""
        with self.lock:
            if order_id in self.orders:
                order = self.orders.pop(order_id)
                self.completed_orders[order_id] = order
    
    def _cleanup_loop(self):
        """Background cleanup of timed out orders"""
        while self.running:
            try:
                time.sleep(self.cleanup_interval)
                self._check_timeouts()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def _check_timeouts(self):
        """Check for timed out orders"""
        with self.lock:
            timed_out = self.get_timed_out_orders()
            
            for order in timed_out:
                logger.warning(f"Order {order.order_id} timed out "
                             f"(filled: {order.filled_quantity}/{order.total_quantity})")
                
                order.status = FillStatus.EXPIRED
                self.stats['timeouts'] += 1
                
                # Trigger timeout callbacks
                self._trigger_timeout_callbacks(order)
                
                # Auto-cancel if enabled
                if self.auto_cancel_on_timeout:
                    self.cancel_order(order.order_id)
    
    def _trigger_partial_callbacks(self, order: AggregatedFill):
        """Trigger partial fill callbacks"""
        for callback in self.on_partial_fill:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Error in partial fill callback: {e}")
    
    def _trigger_complete_callbacks(self, order: AggregatedFill):
        """Trigger complete fill callbacks"""
        for callback in self.on_complete_fill:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Error in complete fill callback: {e}")
    
    def _trigger_timeout_callbacks(self, order: AggregatedFill):
        """Trigger timeout callbacks"""
        for callback in self.on_timeout:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Error in timeout callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register event callback"""
        if event_type == 'partial':
            self.on_partial_fill.append(callback)
        elif event_type == 'complete':
            self.on_complete_fill.append(callback)
        elif event_type == 'timeout':
            self.on_timeout.append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        with self.lock:
            return {
                **self.stats,
                'active_orders': len(self.orders),
                'completed_orders': len(self.completed_orders),
                'incomplete_orders': len(self.get_incomplete_orders())
            }
    
    def stop(self):
        """Stop background threads"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create aggregator
    aggregator = PartialFillAggregator(default_timeout_seconds=10)
    
    # Register callbacks
    def on_partial(order):
        logger.info(f"📊 Partial fill: {order.fill_percentage():.1f}% complete")
    
    def on_complete(order):
        logger.info(f"✅ Fully filled: {order.filled_quantity} @ avg {order.average_price:.2f}")
    
    aggregator.register_callback('partial', on_partial)
    aggregator.register_callback('complete', on_complete)
    
    # Register order
    order = aggregator.register_order(
        order_id="ORD-001",
        symbol="EURUSD",
        side="BUY",
        quantity=10.0,
        timeout_seconds=10
    )
    
    # Simulate partial fills
    aggregator.add_fill("ORD-001", "FILL-1", 3.0, 1.1000)
    time.sleep(1)
    aggregator.add_fill("ORD-001", "FILL-2", 4.0, 1.1005)
    time.sleep(1)
    aggregator.add_fill("ORD-001", "FILL-3", 3.0, 1.1010)
    
    # Print statistics
    stats = aggregator.get_statistics()
    logger.info(f"\nStatistics: {stats}")
    
    # Stop
    aggregator.stop()
