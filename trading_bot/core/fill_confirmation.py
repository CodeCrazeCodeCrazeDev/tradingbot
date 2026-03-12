"""
Fill Confirmation System
Verifies order fills with broker to prevent position mismatches
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class FillStatus(Enum):
    """Order fill status"""
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ConfirmationResult(Enum):
    """Fill confirmation result"""
    CONFIRMED = "confirmed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class OrderFill:
    """Order fill information"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    filled_quantity: float
    average_price: float
    status: FillStatus
    timestamp: datetime
    broker_order_id: Optional[str] = None
    commission: float = 0.0
    slippage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfirmationReport:
    """Fill confirmation report"""
    order_id: str
    result: ConfirmationResult
    fill: Optional[OrderFill]
    attempts: int
    duration_seconds: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class FillConfirmationService:
    """
    Fill Confirmation Service
    
    Verifies order fills with broker to ensure position accuracy.
    Implements retry logic with exponential backoff.
    """
    
    def __init__(
        self,
        broker_adapter,
        max_attempts: int = 10,
        initial_delay: float = 0.5,
        max_delay: float = 30.0,
        timeout_seconds: float = 300.0
    ):
        """
        Initialize fill confirmation service
        
        Args:
            broker_adapter: Broker adapter with get_order_status method
            max_attempts: Maximum confirmation attempts
            initial_delay: Initial retry delay in seconds
            max_delay: Maximum retry delay in seconds
            timeout_seconds: Total timeout for confirmation
        """
        self.broker = broker_adapter
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.timeout_seconds = timeout_seconds
        
        # Tracking
        self.pending_orders: Dict[str, datetime] = {}
        self.confirmed_fills: Dict[str, OrderFill] = {}
        self.failed_orders: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'total_confirmations': 0,
            'successful_confirmations': 0,
            'failed_confirmations': 0,
            'timeouts': 0,
            'partial_fills': 0,
            'avg_confirmation_time': 0.0
        }
        
        self._lock = asyncio.Lock()
        
        logger.info(
            f"FillConfirmationService initialized: "
            f"max_attempts={max_attempts}, timeout={timeout_seconds}s"
        )
    
    async def confirm_fill(
        self,
        order_id: str,
        symbol: str,
        expected_quantity: float,
        side: str
    ) -> ConfirmationReport:
        """
        Confirm order fill with broker
        
        Args:
            order_id: Order ID to confirm
            symbol: Trading symbol
            expected_quantity: Expected fill quantity
            side: Order side (BUY/SELL)
            
        Returns:
            ConfirmationReport with fill details
        """
        start_time = datetime.now()
        attempts = 0
        delay = self.initial_delay
        
        async with self._lock:
            self.pending_orders[order_id] = start_time
            self.stats['total_confirmations'] += 1
        
        logger.info(f"Starting fill confirmation for order {order_id}")
        
        try:
            while attempts < self.max_attempts:
                attempts += 1
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Check timeout
                if elapsed > self.timeout_seconds:
                    logger.warning(
                        f"Fill confirmation timeout for order {order_id} "
                        f"after {elapsed:.1f}s"
                    )
                    async with self._lock:
                        self.stats['timeouts'] += 1
                        self.failed_orders[order_id] = "timeout"
                        del self.pending_orders[order_id]
                    
                    return ConfirmationReport(
                        order_id=order_id,
                        result=ConfirmationResult.TIMEOUT,
                        fill=None,
                        attempts=attempts,
                        duration_seconds=elapsed,
                        error_message=f"Timeout after {elapsed:.1f}s"
                    )
                
                # Query broker for order status
                try:
                    order_status = await self._get_order_status(order_id, symbol)
                    
                    if order_status:
                        fill = self._parse_order_status(
                            order_id, symbol, side, expected_quantity, order_status
                        )
                        
                        # Check if order is filled
                        if fill.status == FillStatus.FILLED:
                            logger.info(
                                f"Order {order_id} confirmed FILLED: "
                                f"{fill.filled_quantity} @ {fill.average_price}"
                            )
                            
                            async with self._lock:
                                self.confirmed_fills[order_id] = fill
                                self.stats['successful_confirmations'] += 1
                                if order_id in self.pending_orders:
                                    del self.pending_orders[order_id]
                            
                            return ConfirmationReport(
                                order_id=order_id,
                                result=ConfirmationResult.CONFIRMED,
                                fill=fill,
                                attempts=attempts,
                                duration_seconds=elapsed
                            )
                        
                        # Check if order is rejected/cancelled
                        elif fill.status in [FillStatus.REJECTED, FillStatus.CANCELLED]:
                            logger.warning(
                                f"Order {order_id} {fill.status.value}: "
                                f"{fill.metadata.get('reason', 'unknown')}"
                            )
                            
                            async with self._lock:
                                self.stats['failed_confirmations'] += 1
                                self.failed_orders[order_id] = fill.status.value
                                if order_id in self.pending_orders:
                                    del self.pending_orders[order_id]
                            
                            return ConfirmationReport(
                                order_id=order_id,
                                result=ConfirmationResult.REJECTED,
                                fill=fill,
                                attempts=attempts,
                                duration_seconds=elapsed,
                                error_message=f"Order {fill.status.value}"
                            )
                        
                        # Partially filled - continue monitoring
                        elif fill.status == FillStatus.PARTIALLY_FILLED:
                            logger.info(
                                f"Order {order_id} partially filled: "
                                f"{fill.filled_quantity}/{expected_quantity}"
                            )
                            async with self._lock:
                                self.stats['partial_fills'] += 1
                
                except Exception as e:
                    logger.error(f"Error checking order status: {e}")
                
                # Wait before next attempt with exponential backoff
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.max_delay)
            
            # Max attempts reached
            logger.error(
                f"Fill confirmation failed for order {order_id} "
                f"after {attempts} attempts"
            )
            
            async with self._lock:
                self.stats['failed_confirmations'] += 1
                self.failed_orders[order_id] = "max_attempts"
                if order_id in self.pending_orders:
                    del self.pending_orders[order_id]
            
            return ConfirmationReport(
                order_id=order_id,
                result=ConfirmationResult.FAILED,
                fill=None,
                attempts=attempts,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=f"Max attempts ({attempts}) reached"
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error in fill confirmation: {e}")
            
            async with self._lock:
                self.stats['failed_confirmations'] += 1
                if order_id in self.pending_orders:
                    del self.pending_orders[order_id]
            
            return ConfirmationReport(
                order_id=order_id,
                result=ConfirmationResult.FAILED,
                fill=None,
                attempts=attempts,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _get_order_status(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order status from broker"""
        try:
            if hasattr(self.broker, 'get_order_status'):
                return await self.broker.get_order_status(order_id, symbol)
            elif hasattr(self.broker, 'get_order'):
                return await self.broker.get_order(order_id)
            else:
                logger.warning("Broker adapter does not support order status queries")
                return None
        except Exception as e:
            logger.error(f"Error querying broker for order status: {e}")
            return None
    
    def _parse_order_status(
        self,
        order_id: str,
        symbol: str,
        side: str,
        expected_quantity: float,
        status_data: Dict[str, Any]
    ) -> OrderFill:
        """Parse broker order status response"""
        
        # Extract status
        status_str = status_data.get('status', 'unknown').lower()
        if 'fill' in status_str and 'partial' not in status_str:
            status = FillStatus.FILLED
        elif 'partial' in status_str:
            status = FillStatus.PARTIALLY_FILLED
        elif 'reject' in status_str:
            status = FillStatus.REJECTED
        elif 'cancel' in status_str:
            status = FillStatus.CANCELLED
        elif 'expire' in status_str:
            status = FillStatus.EXPIRED
        elif 'pending' in status_str or 'new' in status_str:
            status = FillStatus.PENDING
        else:
            status = FillStatus.UNKNOWN
        
        # Extract quantities
        filled_qty = float(status_data.get('filled_quantity', 0))
        avg_price = float(status_data.get('average_price', 0))
        
        # Extract additional info
        broker_order_id = status_data.get('broker_order_id') or status_data.get('id')
        commission = float(status_data.get('commission', 0))
        
        # Calculate slippage if we have expected price
        slippage = 0.0
        if 'expected_price' in status_data and avg_price > 0:
            expected_price = float(status_data['expected_price'])
            slippage = abs(avg_price - expected_price) / expected_price
        
        return OrderFill(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=expected_quantity,
            filled_quantity=filled_qty,
            average_price=avg_price,
            status=status,
            timestamp=datetime.now(),
            broker_order_id=broker_order_id,
            commission=commission,
            slippage=slippage,
            metadata=status_data
        )
    
    def get_fill(self, order_id: str) -> Optional[OrderFill]:
        """Get confirmed fill for order"""
        return self.confirmed_fills.get(order_id)
    
    def get_pending_orders(self) -> List[str]:
        """Get list of pending order IDs"""
        return list(self.pending_orders.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get confirmation statistics"""
        stats = self.stats.copy()
        
        # Calculate success rate
        total = stats['total_confirmations']
        if total > 0:
            stats['success_rate'] = stats['successful_confirmations'] / total
        else:
            stats['success_rate'] = 0.0
        
        stats['pending_count'] = len(self.pending_orders)
        
        return stats
    
    async def cleanup_old_orders(self, max_age_hours: int = 24):
        """Clean up old pending orders"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        async with self._lock:
            old_orders = [
                order_id for order_id, timestamp in self.pending_orders.items()
                if timestamp < cutoff
            ]
            
            for order_id in old_orders:
                logger.warning(f"Cleaning up stale pending order: {order_id}")
                del self.pending_orders[order_id]
                self.failed_orders[order_id] = "stale"
        
        return len(old_orders)


# Singleton instance
_fill_confirmation_service: Optional[FillConfirmationService] = None


def get_fill_confirmation_service(broker_adapter=None) -> FillConfirmationService:
    """Get or create fill confirmation service singleton"""
    global _fill_confirmation_service
    
    if _fill_confirmation_service is None:
        if broker_adapter is None:
            raise ValueError("broker_adapter required for first initialization")
        _fill_confirmation_service = FillConfirmationService(broker_adapter)
    
    return _fill_confirmation_service


async def confirm_order_fill(
    order_id: str,
    symbol: str,
    quantity: float,
    side: str,
    broker_adapter=None
) -> ConfirmationReport:
    """Convenience function to confirm order fill"""
    service = get_fill_confirmation_service(broker_adapter)
    return await service.confirm_fill(order_id, symbol, quantity, side)
