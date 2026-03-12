"""
Order Fill Confirmation System

Ensures orders are properly confirmed before proceeding.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status types"""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderConfirmationSystem:
    """
    Order fill confirmation with timeout and retry logic
    """
    
    def __init__(self, broker, config: Optional[Dict[str, Any]] = None):
        self.broker = broker
        self.config = config or {}
        
        # Configuration
        self.confirmation_timeout = self.config.get('confirmation_timeout', 30)  # seconds
        self.check_interval = self.config.get('check_interval', 0.5)  # seconds
        self.max_retries = self.config.get('max_retries', 3)
        self.partial_fill_timeout = self.config.get('partial_fill_timeout', 60)
        
        # Tracking
        self.pending_orders = {}
        self.confirmed_orders = {}
        self.failed_orders = {}
    
    async def place_order_with_confirmation(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place order and wait for confirmation
        
        Args:
            symbol: Trading symbol
            order_type: 'buy' or 'sell'
            volume: Order volume
            price: Limit price (None for market)
            sl: Stop loss
            tp: Take profit
            **kwargs: Additional parameters
        
        Returns:
            Confirmed order details
        
        Raises:
            OrderTimeoutError: If confirmation times out
            OrderRejectedError: If order is rejected
        """
        order_id = None
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # Place order
                logger.info(f"Placing order: {symbol} {order_type} {volume}")
                
                result = await self.broker.place_order(
                    symbol=symbol,
                    order_type=order_type,
                    volume=volume,
                    price=price,
                    sl=sl,
                    tp=tp,
                    **kwargs
                )
                
                order_id = result.get('order_id') or result.get('deal_id')
                
                if not order_id:
                    raise ValueError("No order ID returned from broker")
                
                # Track pending order
                self.pending_orders[order_id] = {
                    'symbol': symbol,
                    'type': order_type,
                    'volume': volume,
                    'placed_at': datetime.now(),
                    'status': OrderStatus.PENDING
                }
                
                # Wait for confirmation
                confirmed = await self._wait_for_confirmation(order_id, result)
                
                if confirmed:
                    return confirmed
                
                # If not confirmed, retry
                retry_count += 1
                logger.warning(f"Order {order_id} not confirmed, retry {retry_count}/{self.max_retries}")
                await asyncio.sleep(1)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Order placement failed (attempt {retry_count}): {e}")
                
                if retry_count >= self.max_retries:
                    raise
                
                await asyncio.sleep(1)
        
        raise OrderTimeoutError(f"Order failed after {self.max_retries} retries")
    
    async def _wait_for_confirmation(
        self,
        order_id: str,
        initial_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for order confirmation with timeout
        
        Args:
            order_id: Order ID to confirm
            initial_result: Initial order result
        
        Returns:
            Confirmed order details or None
        """
        start_time = datetime.now()
        timeout = timedelta(seconds=self.confirmation_timeout)
        
        # Check if already filled in initial result
        if initial_result.get('volume') and initial_result.get('price'):
            logger.info(f"Order {order_id} filled immediately")
            return self._mark_confirmed(order_id, initial_result)
        
        # Poll for confirmation
        while datetime.now() - start_time < timeout:
            try:
                # Get order status from broker
                status = await self._get_order_status(order_id)
                
                if status['status'] == OrderStatus.FILLED:
                    logger.info(f"Order {order_id} confirmed as FILLED")
                    return self._mark_confirmed(order_id, status)
                
                elif status['status'] == OrderStatus.PARTIALLY_FILLED:
                    logger.warning(f"Order {order_id} partially filled: {status.get('filled_volume')}/{status.get('volume')}")
                    
                    # Wait longer for partial fills
                    if datetime.now() - start_time > timedelta(seconds=self.partial_fill_timeout):
                        logger.warning(f"Partial fill timeout, accepting partial")
                        return self._mark_confirmed(order_id, status)
                
                elif status['status'] == OrderStatus.REJECTED:
                    logger.error(f"Order {order_id} rejected: {status.get('reason')}")
                    self._mark_failed(order_id, status)
                    raise OrderRejectedError(status.get('reason', 'Unknown'))
                
                elif status['status'] == OrderStatus.CANCELLED:
                    logger.warning(f"Order {order_id} cancelled")
                    self._mark_failed(order_id, status)
                    return None
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error checking order status: {e}")
                await asyncio.sleep(self.check_interval)
        
        # Timeout
        logger.error(f"Order {order_id} confirmation timeout after {self.confirmation_timeout}s")
        
        # Try to cancel timed out order
        try:
            await self.broker.cancel_order(order_id)
            logger.info(f"Cancelled timed out order {order_id}")
        except Exception as e:
            logger.error(f"Failed to cancel timed out order: {e}")
        
        self._mark_failed(order_id, {'reason': 'timeout'})
        raise OrderTimeoutError(f"Order {order_id} confirmation timeout")
    
    async def _get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status from broker
        
        Args:
            order_id: Order ID
        
        Returns:
            Order status details
        """
        # Try to get from positions first (for filled orders)
        positions = await self.broker.get_positions()
        for pos in positions:
            if pos.get('ticket') == order_id or pos.get('deal_id') == order_id:
                return {
                    'status': OrderStatus.FILLED,
                    'order_id': order_id,
                    'filled_volume': pos.get('volume'),
                    'fill_price': pos.get('price_open'),
                    'profit': pos.get('profit', 0)
                }
        
        # Check if order exists in pending orders
        if hasattr(self.broker, 'get_order_status'):
            return await self.broker.get_order_status(order_id)
        
        # Fallback: assume pending
        return {
            'status': OrderStatus.PENDING,
            'order_id': order_id
        }
    
    def _mark_confirmed(self, order_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Mark order as confirmed"""
        confirmed_order = {
            **details,
            'confirmed_at': datetime.now().isoformat(),
            'status': OrderStatus.FILLED
        }
        
        self.confirmed_orders[order_id] = confirmed_order
        
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
        
        return confirmed_order
    
    def _mark_failed(self, order_id: str, details: Dict[str, Any]):
        """Mark order as failed"""
        self.failed_orders[order_id] = {
            **details,
            'failed_at': datetime.now().isoformat()
        }
        
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
    
    def get_confirmation_stats(self) -> Dict[str, Any]:
        """Get confirmation statistics"""
        total = len(self.confirmed_orders) + len(self.failed_orders)
        
        return {
            'total_orders': total,
            'confirmed': len(self.confirmed_orders),
            'failed': len(self.failed_orders),
            'pending': len(self.pending_orders),
            'success_rate': len(self.confirmed_orders) / total if total > 0 else 0
        }


class OrderTimeoutError(Exception):
    """Order confirmation timeout"""
    pass


class OrderRejectedError(Exception):
    """Order rejected by broker"""
    pass


# Export
__all__ = [
    'OrderConfirmationSystem',
    'OrderStatus',
    'OrderTimeoutError',
    'OrderRejectedError'
]
