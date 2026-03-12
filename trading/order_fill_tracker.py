"""
Order fill confirmation and tracking system
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class FillStatus(Enum):
    """Order fill status."""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class OrderFill:
    """Order fill details."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    filled_quantity: float
    average_price: float
    fills: List[Dict]
    status: FillStatus
    timestamp: datetime
    slippage: float = 0.0
    commission: float = 0.0


class OrderFillTracker:
    """
    Tracks order fills and confirms execution.
    Monitors slippage and execution quality.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Tracking
        self.pending_orders: Dict[str, Dict] = {}
        self.filled_orders: Dict[str, OrderFill] = {}
        self.fill_history: List[OrderFill] = []
        
        # Slippage tracking
        self.slippage_history = []
        self.max_acceptable_slippage = self.config.get('max_slippage', 0.001)  # 0.1%
        
        # Confirmation timeout
        self.confirmation_timeout = self.config.get('confirmation_timeout', 30)  # seconds
        
        logger.info("✅ Order Fill Tracker initialized")
    
    def register_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        expected_price: float
    ):
        """Register new order for tracking."""
        self.pending_orders[order_id] = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'expected_price': expected_price,
            'filled_quantity': 0.0,
            'fills': [],
            'timestamp': datetime.now(),
            'status': FillStatus.PENDING
        }
        
        logger.info(f"📝 Registered order {order_id} for {symbol}")
    
    def update_fill(
        self,
        order_id: str,
        fill_quantity: float,
        fill_price: float,
        commission: float = 0.0
    ):
        """Update order with fill information."""
        if order_id not in self.pending_orders:
            logger.warning(f"⚠️ Unknown order ID: {order_id}")
            return
        
        order = self.pending_orders[order_id]
        
        # Add fill
        fill = {
            'quantity': fill_quantity,
            'price': fill_price,
            'commission': commission,
            'timestamp': datetime.now()
        }
        order['fills'].append(fill)
        
        # Update filled quantity
        order['filled_quantity'] += fill_quantity
        
        # Calculate average price
        total_value = sum(f['quantity'] * f['price'] for f in order['fills'])
        total_quantity = sum(f['quantity'] for f in order['fills'])
        average_price = total_value / total_quantity if total_quantity > 0 else 0
        
        # Calculate slippage
        expected_price = order['expected_price']
        slippage = abs(average_price - expected_price) / expected_price if expected_price > 0 else 0
        
        # Update status
        if order['filled_quantity'] >= order['quantity']:
            order['status'] = FillStatus.FILLED
        elif order['filled_quantity'] > 0:
            order['status'] = FillStatus.PARTIAL
        
        # Check slippage
        if slippage > self.max_acceptable_slippage:
            logger.warning(
                f"⚠️ High slippage on {order_id}: {slippage:.2%} "
                f"(expected: {expected_price:.4f}, got: {average_price:.4f})"
            )
        
        # Track slippage
        self.slippage_history.append({
            'order_id': order_id,
            'symbol': order['symbol'],
            'slippage': slippage,
            'timestamp': datetime.now()
        })
        
        logger.info(
            f"✅ Fill update for {order_id}: "
            f"{order['filled_quantity']}/{order['quantity']} @ {average_price:.4f}"
        )
        
        # If fully filled, move to completed
        if order['status'] == FillStatus.FILLED:
            self._complete_order(order_id, average_price, slippage, commission)
    
    def _complete_order(
        self,
        order_id: str,
        average_price: float,
        slippage: float,
        commission: float
    ):
        """Move order to completed fills."""
        if order_id not in self.pending_orders:
            return
        
        order = self.pending_orders[order_id]
        
        # Create fill record
        fill = OrderFill(
            order_id=order_id,
            symbol=order['symbol'],
            side=order['side'],
            quantity=order['quantity'],
            filled_quantity=order['filled_quantity'],
            average_price=average_price,
            fills=order['fills'],
            status=FillStatus.FILLED,
            timestamp=datetime.now(),
            slippage=slippage,
            commission=commission
        )
        
        # Store
        self.filled_orders[order_id] = fill
        self.fill_history.append(fill)
        
        # Remove from pending
        del self.pending_orders[order_id]
        
        logger.info(f"✅ Order {order_id} completed: {fill.filled_quantity} @ {average_price:.4f}")
    
    def cancel_order(self, order_id: str):
        """Cancel pending order."""
        if order_id not in self.pending_orders:
            logger.warning(f"⚠️ Cannot cancel unknown order: {order_id}")
            return
        
        order = self.pending_orders[order_id]
        order['status'] = FillStatus.CANCELLED
        
        # If partially filled, complete with partial fill
        if order['filled_quantity'] > 0:
            total_value = sum(f['quantity'] * f['price'] for f in order['fills'])
            total_quantity = sum(f['quantity'] for f in order['fills'])
            average_price = total_value / total_quantity
            
            slippage = abs(average_price - order['expected_price']) / order['expected_price']
            commission = sum(f['commission'] for f in order['fills'])
            
            self._complete_order(order_id, average_price, slippage, commission)
        else:
            # Remove from pending
            del self.pending_orders[order_id]
        
        logger.info(f"❌ Order {order_id} cancelled")
    
    async def wait_for_fill(
        self,
        order_id: str,
        timeout: Optional[int] = None
    ) -> Optional[OrderFill]:
        """
        Wait for order to be filled.
        
        Args:
            order_id: Order ID to wait for
            timeout: Timeout in seconds (default: config timeout)
        
        Returns:
            OrderFill if filled, None if timeout
        """
        if timeout is None:
            timeout = self.confirmation_timeout
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Check if filled
            if order_id in self.filled_orders:
                return self.filled_orders[order_id]
            
            # Check if cancelled or rejected
            if order_id in self.pending_orders:
                status = self.pending_orders[order_id]['status']
                if status in [FillStatus.CANCELLED, FillStatus.REJECTED]:
                    logger.warning(f"⚠️ Order {order_id} {status.value}")
                    return None
            
            # Wait a bit
            await asyncio.sleep(0.1)
        
        # Timeout
        logger.warning(f"⚠️ Order {order_id} fill confirmation timeout")
        return None
    
    def get_fill_status(self, order_id: str) -> Optional[Dict]:
        """Get current fill status of order."""
        if order_id in self.filled_orders:
            fill = self.filled_orders[order_id]
            return {
                'order_id': order_id,
                'status': 'filled',
                'filled_quantity': fill.filled_quantity,
                'average_price': fill.average_price,
                'slippage': fill.slippage,
                'commission': fill.commission
            }
        
        if order_id in self.pending_orders:
            order = self.pending_orders[order_id]
            return {
                'order_id': order_id,
                'status': order['status'].value,
                'filled_quantity': order['filled_quantity'],
                'total_quantity': order['quantity'],
                'fill_percentage': order['filled_quantity'] / order['quantity'] * 100
            }
        
        return None
    
    def get_slippage_stats(self, hours: int = 24) -> Dict:
        """Get slippage statistics."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_slippage = [
            s['slippage'] for s in self.slippage_history
            if s['timestamp'] > cutoff
        ]
        
        if not recent_slippage:
            return {
                'count': 0,
                'avg_slippage': 0.0,
                'max_slippage': 0.0,
                'min_slippage': 0.0
            }
        
        import numpy as np
        
        return {
            'count': len(recent_slippage),
            'avg_slippage': np.mean(recent_slippage),
            'max_slippage': np.max(recent_slippage),
            'min_slippage': np.min(recent_slippage),
            'std_slippage': np.std(recent_slippage)
        }
    
    def get_execution_quality(self) -> Dict:
        """Get execution quality metrics."""
        if not self.fill_history:
            return {
                'total_fills': 0,
                'avg_slippage': 0.0,
                'avg_commission': 0.0,
                'fill_rate': 0.0
            }
        
        import numpy as np
        
        total_orders = len(self.fill_history) + len(self.pending_orders)
        
        return {
            'total_fills': len(self.fill_history),
            'avg_slippage': np.mean([f.slippage for f in self.fill_history]),
            'avg_commission': np.mean([f.commission for f in self.fill_history]),
            'fill_rate': len(self.fill_history) / total_orders if total_orders > 0 else 0.0,
            'pending_orders': len(self.pending_orders)
        }
