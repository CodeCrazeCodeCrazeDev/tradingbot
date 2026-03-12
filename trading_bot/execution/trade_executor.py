"""
Trade Executor Module - Compatibility Wrapper
Provides unified interface for trade execution
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """Order data structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class TradeExecutor:
    """
    Trade execution engine
    Handles order placement and management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trade executor
        
        Args:
            config: Executor configuration
        """
        self.config = config or {}
        self.is_paper_trading = self.config.get('paper_trading', True)
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        
    def execute_trade(self, order: Order) -> Dict[str, Any]:
        """
        Execute a trade order
        
        Args:
            order: Order object to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Generate order ID if not provided
            if not order.order_id:
                self.order_counter += 1
                order.order_id = f"ORD_{self.order_counter:06d}"
            
            order.timestamp = datetime.now()
            
            if self.is_paper_trading:
                # Paper trading simulation
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                self.orders[order.order_id] = order
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'status': order.status.value,
                    'message': 'Order executed (paper trading)'
                }
            else:
                # Real trading (requires MT5 or broker integration)
                return self._execute_real_trade(order)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Order execution failed: {str(e)}'
            }
    
    def _execute_real_trade(self, order: Order) -> Dict[str, Any]:
        """Execute real trade via MT5"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                raise Exception("MT5 not initialized")
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": order.quantity,
                "type": mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if order.price:
                request["price"] = order.price
            if order.stop_loss:
                request["sl"] = order.stop_loss
            if order.take_profit:
                request["tp"] = order.take_profit
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.order_id = str(result.order)
                self.orders[order.order_id] = order
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'status': order.status.value,
                    'message': 'Order executed successfully'
                }
            else:
                raise Exception(f"Order failed: {result.comment}")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Real trade execution failed: {str(e)}'
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            order.status = OrderStatus.CANCELLED
            return {'success': True, 'message': 'Order cancelled'}
        return {'success': False, 'message': 'Order not found'}
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open orders"""
        return [o for o in self.orders.values() 
                if o.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]]

# Export for compatibility
__all__ = ['TradeExecutor', 'Order', 'OrderType', 'OrderSide', 'OrderStatus']
