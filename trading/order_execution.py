"""
Smart order execution system for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionAlgo(Enum):
    """Execution algorithms."""
    VWAP = "vwap"
    TWAP = "twap"
    ICEBERG = "iceberg"
    SMART = "smart"
    ADAPTIVE = "adaptive"


@dataclass
class Order:
    """Trading order details."""
    symbol: str
    side: str  # BUY or SELL
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    algo: Optional[ExecutionAlgo] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def remaining_quantity(self) -> float:
        """Calculate remaining quantity."""
        return self.quantity - self.filled_quantity
    
    @property
    def is_complete(self) -> bool:
        """Check if order is complete."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]


class SmartExecutionEngine:
    """
    Smart order execution engine.
    Implements various execution algorithms and adapts to market conditions.
    """
    
    def __init__(
        self,
        slippage_tolerance: float = 0.001,  # 0.1%
        min_execution_size: float = 0.01,
        max_retry_attempts: int = 3
    ):
        self.slippage_tolerance = slippage_tolerance
        self.min_execution_size = min_execution_size
        self.max_retry_attempts = max_retry_attempts
        
        # Active orders
        self.active_orders: Dict[str, Order] = {}
        
        # Order history
        self.order_history: List[Order] = []
        
        # Execution metrics
        self.metrics = {
            'fill_rate': 0.0,
            'avg_slippage': 0.0,
            'rejection_rate': 0.0,
            'avg_execution_time': 0.0
        }
        
        logger.info("✅ Smart Execution Engine initialized")
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        algo: Optional[ExecutionAlgo] = None
    ) -> Optional[Order]:
        """
        Submit new order for execution.
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: Order type
            price: Limit price if applicable
            stop_price: Stop price if applicable
            algo: Execution algorithm
        
        Returns:
            New order if successful
        """
        try:
            # Validate order
            if not self._validate_order(
                symbol, side, quantity, order_type, price
            ):
                return None
            
            # Create order
            order = Order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                algo=algo
            )
            
            # Add to active orders
            self.active_orders[str(id(order))] = order
            
            # Start execution
            self._execute_order(order)
            
            logger.info(f"✅ Submitted {side} order for {symbol}")
            logger.info(f"   Quantity: {quantity}")
            if price:
                logger.info(f"   Price: ${price:.4f}")
            if algo:
                logger.info(f"   Algorithm: {algo.value}")
            
            return order
            
        except Exception as e:
            logger.error(f"❌ Error submitting order: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel active order."""
        if order_id not in self.active_orders:
            logger.warning(f"⚠️ Order {order_id} not found")
            return False
        
        try:
            order = self.active_orders[order_id]
            
            # Can only cancel pending or active orders
            if order.status not in [OrderStatus.PENDING, OrderStatus.ACTIVE]:
                logger.warning(f"⚠️ Cannot cancel order in {order.status.value} state")
                return False
            
            # Cancel order
            order.status = OrderStatus.CANCELLED
            
            # Move to history
            self.order_history.append(order)
            del self.active_orders[order_id]
            
            logger.info(f"✅ Cancelled order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order: {str(e)}")
            return False
    
    def _validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: OrderType,
        price: Optional[float]
    ) -> bool:
        """Validate order parameters."""
        # Check symbol
        if not symbol:
            logger.error("❌ Invalid symbol")
            return False
        
        # Check side
        if side not in ['BUY', 'SELL']:
            logger.error("❌ Invalid side")
            return False
        
        # Check quantity
        if quantity < self.min_execution_size:
            logger.error("❌ Order size too small")
            return False
        
        # Check price for limit orders
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not price:
            logger.error("❌ Price required for limit orders")
            return False
        
        return True
    
    def _execute_order(self, order: Order):
        """Execute order using appropriate algorithm."""
        # Select execution algorithm
        if not order.algo:
            order.algo = self._select_execution_algo(order)
        
        if order.algo == ExecutionAlgo.VWAP:
            self._execute_vwap(order)
        elif order.algo == ExecutionAlgo.TWAP:
            self._execute_twap(order)
        elif order.algo == ExecutionAlgo.ICEBERG:
            self._execute_iceberg(order)
        elif order.algo == ExecutionAlgo.ADAPTIVE:
            self._execute_adaptive(order)
        else:
            self._execute_smart(order)
    
    def _select_execution_algo(self, order: Order) -> ExecutionAlgo:
        """Select best execution algorithm based on order and market."""
        # Large orders use VWAP
        if order.quantity > 1.0:
            return ExecutionAlgo.VWAP
        
        # High volatility uses adaptive
        volatility = self._get_market_volatility(order.symbol)
        if volatility > 0.02:
            return ExecutionAlgo.ADAPTIVE
        
        # Default to smart routing
        return ExecutionAlgo.SMART
    
    def _execute_vwap(self, order: Order):
        """Execute using VWAP algorithm - splits order over time weighted by volume."""
        logger.info(f"Executing {order.symbol} using VWAP")
        # For now, execute as market order with slippage estimate
        # In production, this would split the order over time periods
        self._execute_market_order(order, slippage_factor=0.0005)  # 0.05% slippage
    
    def _execute_twap(self, order: Order):
        """Execute using TWAP algorithm - splits order evenly over time."""
        logger.info(f"Executing {order.symbol} using TWAP")
        # For now, execute as market order with slippage estimate
        # In production, this would split the order into equal time slices
        self._execute_market_order(order, slippage_factor=0.0003)  # 0.03% slippage
    
    def _execute_iceberg(self, order: Order):
        """Execute using Iceberg algorithm - shows only small visible portion."""
        logger.info(f"Executing {order.symbol} using Iceberg")
        # For now, execute as market order
        # In production, this would show only a fraction of the order
        self._execute_market_order(order, slippage_factor=0.0002)  # 0.02% slippage
    
    def _execute_adaptive(self, order: Order):
        """Execute using Adaptive algorithm - adjusts based on market conditions."""
        logger.info(f"Executing {order.symbol} using Adaptive")
        # Adaptive execution adjusts aggressiveness based on market
        volatility = self._get_market_volatility(order.symbol)
        slippage_factor = 0.001 * (1 + volatility * 10)  # Higher slippage in volatile markets
        self._execute_market_order(order, slippage_factor=slippage_factor)
    
    def _execute_smart(self, order: Order):
        """Execute using Smart Routing - finds best execution venue."""
        logger.info(f"Executing {order.symbol} using Smart Routing")
        # Smart routing finds the best price across venues
        self._execute_market_order(order, slippage_factor=0.0001)  # 0.01% slippage
    
    def _execute_market_order(self, order: Order, slippage_factor: float = 0.0005):
        """
        Execute a market order with estimated slippage.
        This is the base execution method used by all algorithms.
        
        Args:
            order: The order to execute
            slippage_factor: Expected slippage as a fraction (0.001 = 0.1%)
        """
        try:
            # Calculate fill price with slippage
            if order.side == 'BUY':
                fill_price = order.price * (1 + slippage_factor)
            else:
                fill_price = order.price * (1 - slippage_factor)
            
            # Check slippage tolerance
            actual_slippage = abs(fill_price - order.price) / order.price
            if actual_slippage > self.slippage_tolerance:
                logger.warning(f"Slippage {actual_slippage:.4%} exceeds tolerance {self.slippage_tolerance:.4%}")
                order.status = OrderStatus.REJECTED
                return
            
            # Execute the order (in production, this would call the broker API)
            order.filled_quantity = order.quantity
            order.filled_price = fill_price
            order.status = OrderStatus.FILLED
            
            # Move to history
            if order.symbol in self.active_orders:
                del self.active_orders[order.symbol]
            self.order_history.append(order)
            
            # Bound history size
            if len(self.order_history) > 10000:
                self.order_history = self.order_history[-5000:]
            
            logger.info(f"Order filled: {order.symbol} {order.side} {order.quantity} @ {fill_price:.4f}")
            
        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            order.status = OrderStatus.REJECTED
    
    def _get_market_volatility(self, symbol: str) -> float:
        """Get market volatility."""
        # Implement actual volatility calculation
        return 0.01
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get current order status."""
        # Check active orders
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
        else:
            # Check history
            order = next(
                (o for o in self.order_history if str(id(o)) == order_id),
                None
            )
        
        if not order:
            return None
        
        return {
            'symbol': order.symbol,
            'side': order.side,
            'type': order.type.value,
            'quantity': order.quantity,
            'filled_quantity': order.filled_quantity,
            'remaining_quantity': order.remaining_quantity,
            'price': order.price,
            'filled_price': order.filled_price,
            'status': order.status.value,
            'algo': order.algo.value if order.algo else None,
            'timestamp': order.timestamp
        }
    
    def get_execution_metrics(self) -> Dict:
        """Get execution performance metrics."""
        if not self.order_history:
            return self.metrics
        
        # Calculate metrics
        total_orders = len(self.order_history)
        filled_orders = sum(
            1 for o in self.order_history
            if o.status == OrderStatus.FILLED
        )
        rejected_orders = sum(
            1 for o in self.order_history
            if o.status == OrderStatus.REJECTED
        )
        
        # Update metrics (with safe division)
        self.metrics = {
            'fill_rate': filled_orders / total_orders if total_orders > 0 else 0.0,
            'avg_slippage': np.mean([
                abs(o.filled_price - o.price) / o.price
                for o in self.order_history
                if o.status == OrderStatus.FILLED and o.price and o.price > 0
            ]) if filled_orders > 0 else 0.0,
            'rejection_rate': rejected_orders / total_orders if total_orders > 0 else 0.0,
            'avg_execution_time': np.mean([
                (datetime.now() - o.timestamp).total_seconds()  # Fixed: correct order
                for o in self.order_history
                if o.status == OrderStatus.FILLED and o.timestamp
            ]) if filled_orders > 0 else 0.0
        }
        
        return self.metrics


# Alias for compatibility
OrderExecutionManager = SmartExecutionEngine
