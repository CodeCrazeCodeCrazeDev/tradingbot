"""
Advanced Order Management System
=================================

Comprehensive order management:
- Partial fill handling
- Order timeout management
- Order amendment
- Order queue with priority
- Duplicate prevention
- Audit trail
- Failed order recovery
- Real-time notifications

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum, auto
from collections import defaultdict, deque
import threading
import heapq
import uuid

logger = logging.getLogger(__name__)


class OrderPriority(Enum):
    """Order priority levels"""
    CRITICAL = 0    # Emergency orders (stop loss, margin call)
    HIGH = 1        # Time-sensitive orders
    NORMAL = 2      # Regular orders
    LOW = 3         # Background orders
    BATCH = 4       # Batch processing orders


class NotificationType(Enum):
    """Notification types"""
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACKNOWLEDGED = "order_acknowledged"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIAL_FILL = "order_partial_fill"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_EXPIRED = "order_expired"
    ORDER_AMENDED = "order_amended"
    ORDER_TIMEOUT = "order_timeout"
    ORDER_RECOVERY = "order_recovery"


@dataclass
class PartialFill:
    """Partial fill record"""
    fill_id: str
    order_id: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    venue: str = ""
    liquidity: str = ""  # "maker" or "taker"


@dataclass
class OrderAuditEntry:
    """Order audit trail entry"""
    entry_id: str
    order_id: str
    timestamp: datetime
    action: str
    old_state: Optional[str]
    new_state: str
    details: Dict[str, Any] = field(default_factory=dict)
    user: str = "system"
    
    def to_dict(self) -> Dict:
        return {
            'entry_id': self.entry_id,
            'order_id': self.order_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'old_state': self.old_state,
            'new_state': self.new_state,
            'details': self.details,
            'user': self.user
        }


@dataclass
class OrderNotification:
    """Order notification"""
    notification_id: str
    order_id: str
    notification_type: NotificationType
    timestamp: datetime
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    delivered: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'notification_id': self.notification_id,
            'order_id': self.order_id,
            'type': self.notification_type.value,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'details': self.details,
            'delivered': self.delivered
        }


class PartialFillHandler:
    """
    Handles partial fills and aggregation
    """
    
    def __init__(self):
        self.fills: Dict[str, List[PartialFill]] = defaultdict(list)
        self.aggregated: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
        logger.info("PartialFillHandler initialized")
    
    def record_fill(self, fill: PartialFill):
        """Record a partial fill"""
        with self._lock:
            self.fills[fill.order_id].append(fill)
            self._update_aggregation(fill.order_id)
    
    def _update_aggregation(self, order_id: str):
        """Update aggregated fill data"""
        fills = self.fills.get(order_id, [])
        if not fills:
            return
        
        total_qty = sum(f.quantity for f in fills)
        total_value = sum(f.quantity * f.price for f in fills)
        total_commission = sum(f.commission for f in fills)
        
        avg_price = total_value / total_qty if total_qty > 0 else 0
        
        self.aggregated[order_id] = {
            'order_id': order_id,
            'total_quantity': total_qty,
            'average_price': avg_price,
            'total_value': total_value,
            'total_commission': total_commission,
            'fill_count': len(fills),
            'first_fill': fills[0].timestamp,
            'last_fill': fills[-1].timestamp,
            'venues': list(set(f.venue for f in fills if f.venue))
        }
    
    def get_fills(self, order_id: str) -> List[PartialFill]:
        """Get all fills for an order"""
        with self._lock:
            return list(self.fills.get(order_id, []))
    
    def get_aggregated(self, order_id: str) -> Optional[Dict]:
        """Get aggregated fill data"""
        with self._lock:
            return self.aggregated.get(order_id)
    
    def get_remaining_quantity(self, order_id: str, original_qty: float) -> float:
        """Get remaining unfilled quantity"""
        with self._lock:
            agg = self.aggregated.get(order_id)
            if agg:
                return original_qty - agg['total_quantity']
            return original_qty
    
    def is_fully_filled(self, order_id: str, original_qty: float, tolerance: float = 0.0001) -> bool:
        """Check if order is fully filled"""
        remaining = self.get_remaining_quantity(order_id, original_qty)
        return abs(remaining) < tolerance


class OrderTimeoutManager:
    """
    Manages order timeouts and automatic cancellation
    """
    
    def __init__(
        self,
        default_timeout_seconds: float = 60.0,
        check_interval_seconds: float = 1.0
    ):
        self.default_timeout = default_timeout_seconds
        self.check_interval = check_interval_seconds
        
        # Order timeouts: order_id -> (expiry_time, callback)
        self.timeouts: Dict[str, Tuple[datetime, Optional[Callable]]] = {}
        
        # Callbacks
        self.on_timeout: List[Callable] = []
        
        # Background task
        self._running = False
        self._task = None
        self._lock = threading.RLock()
        
        logger.info("OrderTimeoutManager initialized")
    
    def set_timeout(
        self,
        order_id: str,
        timeout_seconds: Optional[float] = None,
        callback: Optional[Callable] = None
    ):
        """Set timeout for an order"""
        with self._lock:
            timeout = timeout_seconds or self.default_timeout
            expiry = datetime.now() + timedelta(seconds=timeout)
            self.timeouts[order_id] = (expiry, callback)
    
    def cancel_timeout(self, order_id: str):
        """Cancel timeout for an order"""
        with self._lock:
            if order_id in self.timeouts:
                del self.timeouts[order_id]
    
    def extend_timeout(self, order_id: str, additional_seconds: float):
        """Extend timeout for an order"""
        with self._lock:
            if order_id in self.timeouts:
                expiry, callback = self.timeouts[order_id]
                new_expiry = expiry + timedelta(seconds=additional_seconds)
                self.timeouts[order_id] = (new_expiry, callback)
    
    async def start(self):
        """Start timeout monitoring"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Order timeout monitoring started")
    
    async def stop(self):
        """Stop timeout monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Order timeout monitoring stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                now = datetime.now()
                expired = []
                
                with self._lock:
                    for order_id, (expiry, callback) in list(self.timeouts.items()):
                        if now >= expiry:
                            expired.append((order_id, callback))
                            del self.timeouts[order_id]
                
                for order_id, callback in expired:
                    logger.warning(f"Order timeout: {order_id}")
                    
                    # Fire specific callback
                    if callback:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(order_id)
                            else:
                                callback(order_id)
                        except Exception as e:
                            logger.error(f"Timeout callback error: {e}")
                    
                    # Fire global callbacks
                    for cb in self.on_timeout:
                        try:
                            if asyncio.iscoroutinefunction(cb):
                                await cb(order_id)
                            else:
                                cb(order_id)
                        except Exception as e:
                            logger.error(f"Global timeout callback error: {e}")
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timeout monitor error: {e}")
                await asyncio.sleep(1)


class OrderQueueManager:
    """
    Priority queue for order submission
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        
        # Priority queue: (priority, timestamp, order_id, order_data)
        self.queue: List[Tuple[int, datetime, str, Dict]] = []
        
        # Active orders
        self.active: Set[str] = set()
        
        # Processed orders
        self.processed: deque = deque(maxlen=1000)
        
        # Callbacks
        self.on_order_ready: List[Callable] = []
        
        # Background task
        self._running = False
        self._task = None
        self._lock = threading.RLock()
        self._condition = asyncio.Condition()
        
        logger.info("OrderQueueManager initialized")
    
    async def enqueue(
        self,
        order_id: str,
        order_data: Dict,
        priority: OrderPriority = OrderPriority.NORMAL
    ):
        """Add order to queue"""
        async with self._condition:
            with self._lock:
                heapq.heappush(
                    self.queue,
                    (priority.value, datetime.now(), order_id, order_data)
                )
            self._condition.notify()
    
    async def dequeue(self) -> Optional[Tuple[str, Dict]]:
        """Get next order from queue"""
        async with self._condition:
            while True:
                with self._lock:
                    # Check if we can process more orders
                    if len(self.active) >= self.max_concurrent:
                        await self._condition.wait()
                        continue
                    
                    if not self.queue:
                        return None
                    
                    _, _, order_id, order_data = heapq.heappop(self.queue)
                    self.active.add(order_id)
                    return (order_id, order_data)
    
    def mark_complete(self, order_id: str):
        """Mark order as complete"""
        with self._lock:
            if order_id in self.active:
                self.active.remove(order_id)
                self.processed.append({
                    'order_id': order_id,
                    'completed_at': datetime.now()
                })
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return len(self.queue)
    
    def get_active_count(self) -> int:
        """Get count of active orders"""
        with self._lock:
            return len(self.active)
    
    async def start(self):
        """Start queue processing"""
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Order queue processing started")
    
    async def stop(self):
        """Stop queue processing"""
        self._running = False
        async with self._condition:
            self._condition.notify_all()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Order queue processing stopped")
    
    async def _process_loop(self):
        """Background processing loop"""
        while self._running:
            try:
                result = await self.dequeue()
                if result:
                    order_id, order_data = result
                    
                    for callback in self.on_order_ready:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(order_id, order_data)
                            else:
                                callback(order_id, order_data)
                        except Exception as e:
                            logger.error(f"Order ready callback error: {e}")
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)


class DuplicateOrderPrevention:
    """
    Prevents duplicate order submission
    """
    
    def __init__(self, ttl_seconds: float = 60.0):
        self.ttl = ttl_seconds
        
        # Order hashes with expiry
        self.order_hashes: Dict[str, datetime] = {}
        
        # Idempotency keys
        self.idempotency_keys: Dict[str, str] = {}
        
        self._lock = threading.RLock()
        
        logger.info("DuplicateOrderPrevention initialized")
    
    def _generate_hash(self, order_data: Dict) -> str:
        """Generate hash for order data"""
        # Create deterministic hash from order parameters
        key_fields = ['symbol', 'side', 'quantity', 'price', 'order_type']
        hash_data = {k: order_data.get(k) for k in key_fields if k in order_data}
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]
    
    def check_duplicate(self, order_data: Dict, idempotency_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if order is a duplicate
        Returns: (is_duplicate, existing_order_id)
        """
        with self._lock:
            # Clean expired entries
            self._cleanup()
            
            # Check idempotency key first
            if idempotency_key:
                if idempotency_key in self.idempotency_keys:
                    return (True, self.idempotency_keys[idempotency_key])
            
            # Check order hash
            order_hash = self._generate_hash(order_data)
            if order_hash in self.order_hashes:
                return (True, None)
            
            return (False, None)
    
    def register_order(self, order_id: str, order_data: Dict, idempotency_key: Optional[str] = None):
        """Register an order to prevent duplicates"""
        with self._lock:
            order_hash = self._generate_hash(order_data)
            expiry = datetime.now() + timedelta(seconds=self.ttl)
            
            self.order_hashes[order_hash] = expiry
            
            if idempotency_key:
                self.idempotency_keys[idempotency_key] = order_id
    
    def _cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        expired = [h for h, exp in self.order_hashes.items() if exp < now]
        for h in expired:
            del self.order_hashes[h]


class OrderAuditTrail:
    """
    Complete order audit trail
    """
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        
        # Audit entries by order
        self.entries: Dict[str, List[OrderAuditEntry]] = defaultdict(list)
        
        # All entries (for global queries)
        self.all_entries: deque = deque(maxlen=max_entries)
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("OrderAuditTrail initialized")
    
    def _generate_id(self) -> str:
        """Generate unique entry ID"""
        with self._lock:
            entry_id = f"AUD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return entry_id
    
    def record(
        self,
        order_id: str,
        action: str,
        old_state: Optional[str],
        new_state: str,
        details: Optional[Dict] = None,
        user: str = "system"
    ) -> OrderAuditEntry:
        """Record an audit entry"""
        entry = OrderAuditEntry(
            entry_id=self._generate_id(),
            order_id=order_id,
            timestamp=datetime.now(),
            action=action,
            old_state=old_state,
            new_state=new_state,
            details=details or {},
            user=user
        )
        
        with self._lock:
            self.entries[order_id].append(entry)
            self.all_entries.append(entry)
        
        return entry
    
    def get_order_history(self, order_id: str) -> List[OrderAuditEntry]:
        """Get audit history for an order"""
        with self._lock:
            return list(self.entries.get(order_id, []))
    
    def get_recent_entries(self, limit: int = 100) -> List[OrderAuditEntry]:
        """Get recent audit entries"""
        with self._lock:
            return list(self.all_entries)[-limit:]
    
    def search(
        self,
        order_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[OrderAuditEntry]:
        """Search audit entries"""
        with self._lock:
            results = list(self.all_entries)
            
            if order_id:
                results = [e for e in results if e.order_id == order_id]
            if action:
                results = [e for e in results if e.action == action]
            if start_time:
                results = [e for e in results if e.timestamp >= start_time]
            if end_time:
                results = [e for e in results if e.timestamp <= end_time]
            
            return results
    
    def export(self, order_id: Optional[str] = None) -> List[Dict]:
        """Export audit entries as dictionaries"""
        if order_id:
            entries = self.get_order_history(order_id)
        else:
            with self._lock:
                entries = list(self.all_entries)
        
        return [e.to_dict() for e in entries]


class FailedOrderRecovery:
    """
    Handles failed order recovery with retry logic
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds
        
        # Failed orders: order_id -> (order_data, retry_count, next_retry_time)
        self.failed_orders: Dict[str, Tuple[Dict, int, datetime]] = {}
        
        # Recovery history
        self.recovery_history: deque = deque(maxlen=1000)
        
        # Callbacks
        self.on_retry: List[Callable] = []
        self.on_recovery_success: List[Callable] = []
        self.on_recovery_failed: List[Callable] = []
        
        # Background task
        self._running = False
        self._task = None
        self._lock = threading.RLock()
        
        logger.info("FailedOrderRecovery initialized")
    
    def record_failure(self, order_id: str, order_data: Dict, error: str):
        """Record a failed order for recovery"""
        with self._lock:
            if order_id in self.failed_orders:
                _, retry_count, _ = self.failed_orders[order_id]
                retry_count += 1
            else:
                retry_count = 0
            
            if retry_count >= self.max_retries:
                logger.error(f"Order {order_id} exceeded max retries")
                self._fire_recovery_failed(order_id, order_data, error)
                return
            
            # Calculate next retry time with exponential backoff
            delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
            next_retry = datetime.now() + timedelta(seconds=delay)
            
            self.failed_orders[order_id] = (order_data, retry_count, next_retry)
            
            logger.info(f"Order {order_id} scheduled for retry {retry_count + 1} at {next_retry}")
    
    def _fire_recovery_failed(self, order_id: str, order_data: Dict, error: str):
        """Fire recovery failed callbacks"""
        self.recovery_history.append({
            'order_id': order_id,
            'timestamp': datetime.now(),
            'success': False,
            'error': error
        })
        
        for callback in self.on_recovery_failed:
            try:
                callback(order_id, order_data, error)
            except Exception as e:
                logger.error(f"Recovery failed callback error: {e}")
    
    async def start(self, retry_func: Callable):
        """Start recovery monitoring"""
        self._running = True
        self._retry_func = retry_func
        self._task = asyncio.create_task(self._recovery_loop())
        logger.info("Failed order recovery started")
    
    async def stop(self):
        """Stop recovery monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Failed order recovery stopped")
    
    async def _recovery_loop(self):
        """Background recovery loop"""
        while self._running:
            try:
                now = datetime.now()
                ready_for_retry = []
                
                with self._lock:
                    for order_id, (order_data, retry_count, next_retry) in list(self.failed_orders.items()):
                        if now >= next_retry:
                            ready_for_retry.append((order_id, order_data, retry_count))
                
                for order_id, order_data, retry_count in ready_for_retry:
                    logger.info(f"Retrying order {order_id} (attempt {retry_count + 1})")
                    
                    # Fire retry callbacks
                    for callback in self.on_retry:
                        pass
                    try:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(order_id, order_data, retry_count)
                            else:
                                callback(order_id, order_data, retry_count)
                        except Exception as e:
                            logger.error(f"Retry callback error: {e}")
                    
                    # Attempt retry
                        if asyncio.iscoroutinefunction(self._retry_func):
                            success = await self._retry_func(order_id, order_data)
                        else:
                            success = self._retry_func(order_id, order_data)
                        
                        if success:
                            with self._lock:
                                if order_id in self.failed_orders:
                                    del self.failed_orders[order_id]
                            
                            self.recovery_history.append({
                                'order_id': order_id,
                                'timestamp': datetime.now(),
                                'success': True,
                                'attempts': retry_count + 1
                            })
                            
                            for callback in self.on_recovery_success:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(order_id, order_data)
                                    else:
                                        callback(order_id, order_data)
                                except Exception as e:
                                    logger.error(f"Recovery success callback error: {e}")
                        else:
                            self.record_failure(order_id, order_data, "Retry failed")
                            
                    except Exception as e:
                        logger.error(f"Retry error for {order_id}: {e}")
                        self.record_failure(order_id, order_data, str(e))
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
                await asyncio.sleep(5)


class OrderNotificationSystem:
    """
    Real-time order notifications
    """
    
    def __init__(self):
        # Notification handlers by type
        self.handlers: Dict[NotificationType, List[Callable]] = defaultdict(list)
        
        # Notification history
        self.history: deque = deque(maxlen=1000)
        
        # Pending notifications
        self.pending: List[OrderNotification] = []
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("OrderNotificationSystem initialized")
    
    def _generate_id(self) -> str:
        """Generate unique notification ID"""
        with self._lock:
            notif_id = f"NOT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return notif_id
    
    def register_handler(self, notification_type: NotificationType, handler: Callable):
        """Register a notification handler"""
        self.handlers[notification_type].append(handler)
    
    def register_global_handler(self, handler: Callable):
        """Register a handler for all notification types"""
        for ntype in NotificationType:
            self.handlers[ntype].append(handler)
    
    async def notify(
        self,
        order_id: str,
        notification_type: NotificationType,
        message: str,
        details: Optional[Dict] = None
    ) -> OrderNotification:
        """Send a notification"""
        notification = OrderNotification(
            notification_id=self._generate_id(),
            order_id=order_id,
            notification_type=notification_type,
            timestamp=datetime.now(),
            message=message,
            details=details or {}
        )
        
        # Fire handlers
        handlers = self.handlers.get(notification_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification)
                else:
                    handler(notification)
                notification.delivered = True
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
        
        # Store in history
        with self._lock:
            self.history.append(notification)
        
        return notification
    
    def get_history(
        self,
        order_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100
    ) -> List[OrderNotification]:
        """Get notification history"""
        with self._lock:
            results = list(self.history)
            
            if order_id:
                results = [n for n in results if n.order_id == order_id]
            if notification_type:
                results = [n for n in results if n.notification_type == notification_type]
            
            return results[-limit:]


class AdvancedOrderManager:
    """
    Complete advanced order management system
    """
    
    def __init__(self):
        # Components
        self.partial_fill_handler = PartialFillHandler()
        self.timeout_manager = OrderTimeoutManager()
        self.queue_manager = OrderQueueManager()
        self.duplicate_prevention = DuplicateOrderPrevention()
        self.audit_trail = OrderAuditTrail()
        self.recovery = FailedOrderRecovery()
        self.notifications = OrderNotificationSystem()
        
        # Order tracking
        self.orders: Dict[str, Dict] = {}
        
        logger.info("AdvancedOrderManager initialized")
    
    async def start(self, order_executor: Callable):
        """Start all background services"""
        await self.timeout_manager.start()
        await self.queue_manager.start()
        await self.recovery.start(order_executor)
        logger.info("AdvancedOrderManager started")
    
    async def stop(self):
        """Stop all background services"""
        await self.timeout_manager.stop()
        await self.queue_manager.stop()
        await self.recovery.stop()
        logger.info("AdvancedOrderManager stopped")
    
    async def submit_order(
        self,
        order_data: Dict,
        priority: OrderPriority = OrderPriority.NORMAL,
        timeout_seconds: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Submit an order with full management
        Returns: (success, order_id, error_message)
        """
        # Check for duplicates
        is_dup, existing_id = self.duplicate_prevention.check_duplicate(
            order_data, idempotency_key
        )
        if is_dup:
            return (False, existing_id or "", "Duplicate order detected")
        
        # Generate order ID
        order_id = str(uuid.uuid4())[:8]
        
        # Register to prevent duplicates
        self.duplicate_prevention.register_order(order_id, order_data, idempotency_key)
        
        # Record in audit trail
        self.audit_trail.record(
            order_id=order_id,
            action="submit",
            old_state=None,
            new_state="pending",
            details=order_data
        )
        
        # Set timeout
        if timeout_seconds:
            self.timeout_manager.set_timeout(order_id, timeout_seconds)
        
        # Add to queue
        await self.queue_manager.enqueue(order_id, order_data, priority)
        
        # Send notification
        await self.notifications.notify(
            order_id=order_id,
            notification_type=NotificationType.ORDER_SUBMITTED,
            message=f"Order {order_id} submitted",
            details=order_data
        )
        
        # Store order
        self.orders[order_id] = {
            'order_id': order_id,
            'data': order_data,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        return (True, order_id, None)
    
    async def record_fill(
        self,
        order_id: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        venue: str = ""
    ):
        """Record a fill for an order"""
        fill = PartialFill(
            fill_id=str(uuid.uuid4())[:8],
            order_id=order_id,
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now(),
            venue=venue
        )
        
        self.partial_fill_handler.record_fill(fill)
        
        # Update audit trail
        self.audit_trail.record(
            order_id=order_id,
            action="fill",
            old_state="pending",
            new_state="partially_filled",
            details={'quantity': quantity, 'price': price}
        )
        
        # Send notification
        await self.notifications.notify(
            order_id=order_id,
            notification_type=NotificationType.ORDER_PARTIAL_FILL,
            message=f"Order {order_id} partially filled: {quantity} @ {price}",
            details={'quantity': quantity, 'price': price}
        )
        
        # Cancel timeout if fully filled
        order = self.orders.get(order_id)
        if order:
            original_qty = order['data'].get('quantity', 0)
            if self.partial_fill_handler.is_fully_filled(order_id, original_qty):
                self.timeout_manager.cancel_timeout(order_id)
                self.queue_manager.mark_complete(order_id)
                
                await self.notifications.notify(
                    order_id=order_id,
                    notification_type=NotificationType.ORDER_FILLED,
                    message=f"Order {order_id} fully filled",
                    details=self.partial_fill_handler.get_aggregated(order_id)
                )
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get complete order status"""
        order = self.orders.get(order_id)
        if not order:
            return None
        
        return {
            **order,
            'fills': self.partial_fill_handler.get_aggregated(order_id),
            'audit_trail': [e.to_dict() for e in self.audit_trail.get_order_history(order_id)]
        }


# Singleton instance
_order_manager: Optional[AdvancedOrderManager] = None


def get_order_manager() -> AdvancedOrderManager:
    """Get or create order manager singleton"""
    global _order_manager
    if _order_manager is None:
        _order_manager = AdvancedOrderManager()
    return _order_manager


# Export
__all__ = [
    'AdvancedOrderManager',
    'PartialFillHandler',
    'OrderTimeoutManager',
    'OrderQueueManager',
    'DuplicateOrderPrevention',
    'OrderAuditTrail',
    'FailedOrderRecovery',
    'OrderNotificationSystem',
    'PartialFill',
    'OrderAuditEntry',
    'OrderNotification',
    'OrderPriority',
    'NotificationType',
    'get_order_manager'
]
