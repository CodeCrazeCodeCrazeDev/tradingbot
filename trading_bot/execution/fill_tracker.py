"""
Order Fill Confirmation and Tracking

Tracks order fills, confirms execution, and maintains accurate position state.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

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


class FillStatus(Enum):
    """Fill status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Fill:
    """Individual fill record"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    fill_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderFillRecord:
    """Complete order fill record"""
    order_id: str
    symbol: str
    side: str
    requested_quantity: float
    filled_quantity: float
    average_fill_price: float
    total_commission: float
    fills: List[Fill] = field(default_factory=list)
    status: FillStatus = FillStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def quantity(self) -> float:
        """Return filled quantity if confirmed, otherwise requested quantity"""
        if self.status == FillStatus.CONFIRMED:
            return self.filled_quantity
        return self.requested_quantity
    
    @property
    def slippage_bps(self) -> float:
        """Get slippage in basis points"""
        expected_price = self.metadata.get('expected_price')
        if expected_price and self.average_fill_price:
            return abs(self.average_fill_price - expected_price) / expected_price * 10000
        return 0.0


class FillTracker:
    """Track and confirm order fills"""
    
    def __init__(self, broker_adapter, config: Optional[Dict[str, Any]] = None):
        self.broker = broker_adapter
        self.config = config or {}
        
        # Fill records
        self.fill_records: Dict[str, OrderFillRecord] = {}
        self.pending_confirmations: Dict[str, OrderFillRecord] = {}
        self.pending_orders: Dict[str, OrderFillRecord] = {}  # Alias for pending_confirmations
        
        # Configuration
        self.confirmation_timeout = self.config.get('confirmation_timeout', 30)  # seconds
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)  # seconds
        
        # Statistics
        self.total_orders = 0
        self.total_fills = 0
        self.confirmed_fills = 0
        self.failed_fills = 0
        self.timeout_fills = 0
        self.confirmed_orders = {}  # Dict of confirmed order records
        
        # Slippage tracking
        self.slippage_history: List[Dict[str, Any]] = []
        self.max_slippage_history = self.config.get('max_slippage_history', 1000)
        
    async def track_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        expected_price: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OrderFillRecord:
        """
        Start tracking an order for fill confirmation
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Order quantity
            expected_price: Expected fill price
            metadata: Additional metadata
            
        Returns:
            OrderFillRecord
        """
        record = OrderFillRecord(
            order_id=order_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            filled_quantity=0.0,
            average_fill_price=0.0,
            total_commission=0.0,
            metadata=metadata or {}
        )
        
        if expected_price:
            record.metadata['expected_price'] = expected_price
        
        self.fill_records[order_id] = record
        self.pending_confirmations[order_id] = record
        self.pending_orders[order_id] = record  # Keep both references
        self.total_orders += 1
        
        # Start confirmation task
        asyncio.create_task(self._confirm_fill(order_id))
        
        return record
    
    async def _confirm_fill(self, order_id: str):
        """
        Confirm order fill with broker
        
        Retries until confirmed, failed, or timeout
        """
        start_time = datetime.now()
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Check if order still pending
                if order_id not in self.pending_confirmations:
                    return
                
                # Get order status from broker
                order_response = await self.broker.get_order_status(order_id)
                
                if order_response:
                    record = self.fill_records[order_id]
                    
                    # Update fill record
                    record.filled_quantity = order_response.filled_quantity
                    record.average_fill_price = order_response.average_fill_price
                    record.total_commission = order_response.commission
                    
                    # Create fill entry
                    fill = Fill(
                        order_id=order_id,
                        symbol=record.symbol,
                        side=record.side,
                        quantity=order_response.filled_quantity,
                        price=order_response.average_fill_price,
                        commission=order_response.commission,
                        timestamp=order_response.timestamp,
                        fill_id=order_response.order_id,
                        metadata=order_response.metadata
                    )
                    record.fills.append(fill)
                    
                    # Check if fully filled
                    if record.filled_quantity >= record.requested_quantity * 0.99:  # 99% filled
                        record.status = FillStatus.CONFIRMED
                        record.confirmed_at = datetime.now()
                        
                        # Remove from pending
                        if order_id in self.pending_confirmations:
                            del self.pending_confirmations[order_id]
                        if order_id in self.pending_orders:
                            del self.pending_orders[order_id]
                        
                        # Add to confirmed orders
                        self.confirmed_orders[order_id] = record
                        
                        # Update statistics
                        self.total_fills += 1
                        self.confirmed_fills += 1
                        
                        # Track slippage
                        self._track_slippage(record)
                        
                        logger.info(
                            f"Order {order_id} confirmed: {record.filled_quantity} @ "
                            f"{record.average_fill_price:.5f}, Commission: {record.total_commission:.2f}"
                        )
                        return
                
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > self.confirmation_timeout:
                    record = self.fill_records[order_id]
                    record.status = FillStatus.TIMEOUT
                    if order_id in self.pending_confirmations:
                        del self.pending_confirmations[order_id]
                    if order_id in self.pending_orders:
                        del self.pending_orders[order_id]
                    self.total_fills += 1
                    self.timeout_fills += 1
                    logger.warning(f"Order {order_id} confirmation timeout after {elapsed:.1f}s")
                    return
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay)
                retries += 1
                
            except Exception as e:
                logger.error(f"Error confirming fill for {order_id}: {e}")
                retries += 1
                await asyncio.sleep(self.retry_delay)
        
        # Max retries reached
        if order_id in self.pending_confirmations:
            record = self.fill_records[order_id]
            record.status = FillStatus.FAILED
            if order_id in self.pending_confirmations:
                del self.pending_confirmations[order_id]
            if order_id in self.pending_orders:
                del self.pending_orders[order_id]
            self.total_fills += 1
            self.failed_fills += 1
            logger.error(f"Order {order_id} confirmation failed after {retries} retries")
    
    def _track_slippage(self, record: OrderFillRecord):
        """Track slippage for filled order"""
        expected_price = record.metadata.get('expected_price')
        
        if expected_price and record.average_fill_price:
            # Calculate slippage in basis points
            slippage_bps = abs(record.average_fill_price - expected_price) / expected_price * 10000
            
            # Determine direction
            if record.side == 'buy':
                slippage_direction = 'positive' if record.average_fill_price < expected_price else 'negative'
            else:
                slippage_direction = 'positive' if record.average_fill_price > expected_price else 'negative'
            
            slippage_record = {
                'order_id': record.order_id,
                'symbol': record.symbol,
                'side': record.side,
                'expected_price': expected_price,
                'actual_price': record.average_fill_price,
                'slippage_bps': slippage_bps,
                'direction': slippage_direction,
                'quantity': record.filled_quantity,
                'timestamp': record.confirmed_at or datetime.now()
            }
            
            self.slippage_history.append(slippage_record)
            
            # Trim history if too large
            if len(self.slippage_history) > self.max_slippage_history:
                self.slippage_history = self.slippage_history[-self.max_slippage_history:]
            
            logger.info(
                f"Slippage tracked: {record.symbol} {record.side}, "
                f"Expected: {expected_price:.5f}, Actual: {record.average_fill_price:.5f}, "
                f"Slippage: {slippage_bps:.2f} bps ({slippage_direction})"
            )
    
    def get_fill_record(self, order_id: str) -> Optional[OrderFillRecord]:
        """Get fill record for order"""
        return self.fill_records.get(order_id)
    
    def get_slippage_stats(self, symbol: Optional[str] = None, lookback_hours: int = 24) -> Dict[str, Any]:
        """
        Get slippage statistics
        
        Args:
            symbol: Filter by symbol (None for all)
            lookback_hours: Hours to look back
            
        Returns:
            Dictionary with slippage statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        # Filter slippage records
        records = [
            r for r in self.slippage_history
            if r['timestamp'] >= cutoff_time and (symbol is None or r['symbol'] == symbol)
        ]
        
        if not records:
            return {
                'count': 0,
                'avg_slippage_bps': 0.0,
                'max_slippage_bps': 0.0,
                'min_slippage_bps': 0.0,
                'positive_slippage_pct': 0.0,
            }
        
        slippages = [r['slippage_bps'] for r in records]
        positive_count = sum(1 for r in records if r['direction'] == 'positive')
        
        return {
            'count': len(records),
            'avg_slippage_bps': sum(slippages) / len(slippages),
            'max_slippage_bps': max(slippages),
            'min_slippage_bps': min(slippages),
            'positive_slippage_pct': (positive_count / len(records)) * 100,
            'symbol': symbol or 'all',
            'lookback_hours': lookback_hours,
        }
    
    def get_confirmation_stats(self) -> Dict[str, Any]:
        """Get fill confirmation statistics"""
        total = self.total_fills
        
        return {
            'total_orders': self.total_orders,
            'total_fills': total,
            'confirmed_fills': self.confirmed_fills,
            'confirmed_orders': len(self.confirmed_orders),
            'failed_fills': self.failed_fills,
            'timeout_fills': self.timeout_fills,
            'pending_confirmations': len(self.pending_confirmations),
            'confirmation_rate': (self.confirmed_fills / total * 100) if total > 0 else 0.0,
        }
    
    async def wait_for_confirmation(
        self,
        order_id: str,
        timeout: Optional[float] = None
    ) -> Optional[OrderFillRecord]:
        """
        Wait for order fill confirmation
        
        Args:
            order_id: Order ID to wait for
            timeout: Timeout in seconds (None for default)
            
        Returns:
            OrderFillRecord if confirmed, None if timeout/failed
        """
        if timeout is None:
            timeout = self.confirmation_timeout
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            record = self.fill_records.get(order_id)
            
            if record and record.status == FillStatus.CONFIRMED:
                return record
            
            if record and record.status in [FillStatus.FAILED, FillStatus.TIMEOUT]:
                return None
            
            await asyncio.sleep(0.1)
        
        return None
