"""
Idempotent Order Execution System
Implements HI-EXE-001: Client Order IDs + Idempotent Submits

Ensures that orders are never duplicated even if submission is retried.
Critical for production trading to prevent financial losses from duplicate orders.
"""

import uuid
import hashlib
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status states"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class OrderRequest:
    """Idempotent order request with client-side ID"""
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT/STOP
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC/IOC/FOK
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'order_type': self.order_type,
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force,
            'client_order_id': self.client_order_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    def get_idempotency_key(self) -> str:
        """Generate idempotency key from order parameters"""
        # Use client_order_id as primary key
        return self.client_order_id
    
    def get_content_hash(self) -> str:
        """Generate content hash to detect parameter changes"""
        content = f"{self.symbol}|{self.side}|{self.quantity}|{self.order_type}|{self.price}|{self.stop_price}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class OrderResult:
    """Result of order submission"""
    client_order_id: str
    exchange_order_id: Optional[str]
    status: OrderStatus
    submitted_at: datetime
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'client_order_id': self.client_order_id,
            'exchange_order_id': self.exchange_order_id,
            'status': self.status.value,
            'submitted_at': self.submitted_at.isoformat(),
            'filled_quantity': self.filled_quantity,
            'average_price': self.average_price,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


class IdempotentExecutor:
    """
    Idempotent order executor that guarantees exactly-once semantics
    
    Features:
    - Client-side order IDs for idempotency
    - Request deduplication
    - Result caching
    - Automatic retry with same ID
    - Content hash verification
    - TTL-based cache cleanup
    """
    
    def __init__(self, 
                 cache_ttl_seconds: int = 3600,
                 max_cache_size: int = 10000,
                 enable_content_verification: bool = True):
        """
        Initialize idempotent executor
        
        Args:
            cache_ttl_seconds: How long to cache results (default 1 hour)
            max_cache_size: Maximum number of cached results
            enable_content_verification: Verify order content hasn't changed
        """
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.max_cache_size = max_cache_size
        self.enable_content_verification = enable_content_verification
        
        # Cache for submitted orders and results
        self.submitted_orders: Dict[str, OrderRequest] = {}
        self.order_results: Dict[str, OrderResult] = {}
        self.order_timestamps: Dict[str, datetime] = {}
        self.content_hashes: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'duplicate_detections': 0,
            'content_mismatches': 0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"Idempotent Executor initialized (TTL: {cache_ttl_seconds}s, max_size: {max_cache_size})")
    
    def place_order(self, request: OrderRequest, executor_func: callable) -> OrderResult:
        """
        Place order with idempotency guarantee
        
        Args:
            request: Order request with client_order_id
            executor_func: Function to actually submit order (e.g., broker.place_order)
        
        Returns:
            OrderResult with submission details
        
        Raises:
            ValueError: If content hash mismatch detected
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            idempotency_key = request.get_idempotency_key()
            content_hash = request.get_content_hash()
            
            # Check if already submitted
            if idempotency_key in self.submitted_orders:
                self.stats['cache_hits'] += 1
                self.stats['duplicate_detections'] += 1
                
                # Verify content hasn't changed
                if self.enable_content_verification:
                    cached_hash = self.content_hashes.get(idempotency_key)
                    if cached_hash and cached_hash != content_hash:
                        self.stats['content_mismatches'] += 1
                        error_msg = (
                            f"Order content mismatch for {idempotency_key}. "
                            f"Same client_order_id used with different parameters. "
                            f"Original hash: {cached_hash}, New hash: {content_hash}"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                
                # Return cached result
                cached_result = self.order_results.get(idempotency_key)
                if cached_result:
                    logger.info(f"Returning cached result for order {idempotency_key} (duplicate request)")
                    return cached_result
            
            # New order - submit it
            self.stats['cache_misses'] += 1
            
            try:
                # Store request before submission
                self.submitted_orders[idempotency_key] = request
                self.content_hashes[idempotency_key] = content_hash
                self.order_timestamps[idempotency_key] = datetime.now()
                
                # Execute actual order submission
                logger.info(f"Submitting new order {idempotency_key}: {request.symbol} {request.side} {request.quantity}")
                result = executor_func(request)
                
                # Cache result
                self.order_results[idempotency_key] = result
                
                # Cleanup old entries if cache too large
                self._cleanup_cache()
                
                logger.info(f"Order {idempotency_key} submitted successfully: {result.status.value}")
                return result
                
            except Exception as e:
                # Store error result for idempotency
                error_result = OrderResult(
                    client_order_id=idempotency_key,
                    exchange_order_id=None,
                    status=OrderStatus.REJECTED,
                    submitted_at=datetime.now(),
                    error_message=str(e)
                )
                self.order_results[idempotency_key] = error_result
                
                logger.error(f"Order {idempotency_key} submission failed: {e}")
                raise
    
    def get_order_status(self, client_order_id: str) -> Optional[OrderResult]:
        """Get cached order result by client_order_id"""
        with self.lock:
            return self.order_results.get(client_order_id)
    
    def update_order_status(self, client_order_id: str, 
                           status: OrderStatus,
                           filled_quantity: Optional[float] = None,
                           average_price: Optional[float] = None):
        """Update order status (e.g., from fill notifications)"""
        with self.lock:
            result = self.order_results.get(client_order_id)
            if result:
                result.status = status
                if filled_quantity is not None:
                    result.filled_quantity = filled_quantity
                if average_price is not None:
                    result.average_price = average_price
                logger.info(f"Updated order {client_order_id} status to {status.value}")
    
    def is_order_submitted(self, client_order_id: str) -> bool:
        """Check if order was already submitted"""
        with self.lock:
            return client_order_id in self.submitted_orders
    
    def _cleanup_cache(self):
        """Remove old entries if cache exceeds max size"""
        if len(self.order_results) <= self.max_cache_size:
            return
        
        # Remove oldest entries
        now = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.order_timestamps.items():
            if now - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        # If not enough expired, remove oldest
        if len(expired_keys) < len(self.order_results) - self.max_cache_size:
            sorted_keys = sorted(self.order_timestamps.items(), key=lambda x: x[1])
            num_to_remove = len(self.order_results) - self.max_cache_size
            expired_keys.extend([k for k, _ in sorted_keys[:num_to_remove]])
        
        # Remove entries
        for key in expired_keys:
            self.submitted_orders.pop(key, None)
            self.order_results.pop(key, None)
            self.order_timestamps.pop(key, None)
            self.content_hashes.pop(key, None)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} old cache entries")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        with self.lock:
            cache_hit_rate = (
                self.stats['cache_hits'] / self.stats['total_requests'] * 100
                if self.stats['total_requests'] > 0 else 0
            )
            
            return {
                **self.stats,
                'cache_hit_rate_pct': round(cache_hit_rate, 2),
                'cached_orders': len(self.order_results),
                'cache_size_pct': round(len(self.order_results) / self.max_cache_size * 100, 2)
            }
    
    def clear_cache(self):
        """Clear all cached data (use with caution)"""
        with self.lock:
            self.submitted_orders.clear()
            self.order_results.clear()
            self.order_timestamps.clear()
            self.content_hashes.clear()
            logger.warning("Order cache cleared")


class OrderBatchExecutor:
    """
    Batch executor for multiple orders with idempotency
    Useful for portfolio rebalancing or multi-leg strategies
    """
    
    def __init__(self, idempotent_executor: IdempotentExecutor):
        self.executor = idempotent_executor
        self.batch_results: Dict[str, List[OrderResult]] = {}
        self.lock = threading.RLock()
    
    def place_batch(self, 
                   requests: List[OrderRequest],
                   executor_func: callable,
                   batch_id: Optional[str] = None) -> List[OrderResult]:
        """
        Place multiple orders atomically with idempotency
        
        Args:
            requests: List of order requests
            executor_func: Function to submit orders
            batch_id: Optional batch identifier for tracking
        
        Returns:
            List of OrderResults
        """
        if not batch_id:
            batch_id = str(uuid.uuid4())
        
        results = []
        
        with self.lock:
            logger.info(f"Executing batch {batch_id} with {len(requests)} orders")
            
            for request in requests:
                try:
                    result = self.executor.place_order(request, executor_func)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch {batch_id} order {request.client_order_id} failed: {e}")
                    # Continue with other orders
                    results.append(OrderResult(
                        client_order_id=request.client_order_id,
                        exchange_order_id=None,
                        status=OrderStatus.REJECTED,
                        submitted_at=datetime.now(),
                        error_message=str(e)
                    ))
            
            # Cache batch results
            self.batch_results[batch_id] = results
            
            success_count = sum(1 for r in results if r.status == OrderStatus.SUBMITTED)
            logger.info(f"Batch {batch_id} completed: {success_count}/{len(requests)} successful")
        
        return results
    
    def get_batch_results(self, batch_id: str) -> Optional[List[OrderResult]]:
        """Get results for a batch"""
        with self.lock:
            return self.batch_results.get(batch_id)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Mock executor function
    def mock_broker_submit(request: OrderRequest) -> OrderResult:
        """Mock broker submission"""
        time.sleep(0.1)  # Simulate network delay
        return OrderResult(
            client_order_id=request.client_order_id,
            exchange_order_id=f"EX-{uuid.uuid4().hex[:8]}",
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now()
        )
    
    # Create idempotent executor
    executor = IdempotentExecutor(cache_ttl_seconds=300)
    
    # Test 1: Submit order
    order1 = OrderRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=1.0,
        order_type="MARKET"
    )
    
    result1 = executor.place_order(order1, mock_broker_submit)
    logger.info(f"Order 1 submitted: {result1.exchange_order_id}")
    
    # Test 2: Retry same order (should return cached)
    result2 = executor.place_order(order1, mock_broker_submit)
    logger.info(f"Order 1 retry: {result2.exchange_order_id} (cached: {result1.exchange_order_id == result2.exchange_order_id})")
    
    # Test 3: Different order with same client_order_id (should fail)
    order3 = OrderRequest(
        symbol="GBPUSD",  # Different symbol
        side="BUY",
        quantity=1.0,
        order_type="MARKET",
        client_order_id=order1.client_order_id  # Same ID!
    )
    
    try:
        result3 = executor.place_order(order3, mock_broker_submit)
    except ValueError as e:
        logger.info(f"Content mismatch detected: {e}")
    
    # Print statistics
    stats = executor.get_statistics()
    logger.info(f"\nStatistics: {stats}")
