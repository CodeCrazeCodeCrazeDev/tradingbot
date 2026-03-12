"""
MT5 Broker Adapter - Production-Ready MetaTrader 5 Integration

This module provides a complete, production-ready adapter for MetaTrader 5.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import MT5, make it optional
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 not available - install with: pip install MetaTrader5")


class OrderType(Enum):
    """Order types"""
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5


class MT5BrokerAdapter:
    """Production-ready MT5 broker adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        if not MT5_AVAILABLE:
            raise ImportError("MetaTrader5 package not installed")
        
        self.config = config
        self.login = config.get('login')
        self.password = config.get('password')
        self.server = config.get('server')
        self.timeout = config.get('timeout', 60000)  # 60 seconds
        
        self.connected = False
        self.last_error = None
        
        # Initialize MT5
        self._initialize()
    
    async def connect(self) -> bool:
        try:
            if not MT5_AVAILABLE:
                logger.error("MetaTrader5 package not installed")
                return False
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            if self.login and self.password and self.server:
                if not mt5.login(self.login, self.password, self.server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            self.connected = True
            logger.info("MT5 connected successfully")
            return True
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                logger.info("MT5 disconnected")
                return True
            return False
        except Exception as e:
            logger.error(f"MT5 disconnect error: {e}")
            return False

    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        positions = await self.get_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return pos
        return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order by order ID.
        
        Args:
            order_id: The order ticket number
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return False
        try:
            ticket = int(order_id)
            # Get the order first
            orders = mt5.orders_get(ticket=ticket)
            if not orders:
                logger.warning(f"Order {order_id} not found or already executed")
                return False
            
            order = orders[0]
            
            # Prepare cancellation request
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }
            
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Cancel order failed: {mt5.last_error()}")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Cancel failed: {result.comment} (code: {result.retcode})")
                return False
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an order by order ID.
        
        Args:
            order_id: The order ticket number
            
        Returns:
            Dict with order details or None if not found
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
        try:
            ticket = int(order_id)
            
            # Check pending orders first
            orders = mt5.orders_get(ticket=ticket)
            if orders:
                order = orders[0]
                return {
                    'order_id': order.ticket,
                    'symbol': order.symbol,
                    'type': self._order_type_to_string(order.type),
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'status': 'pending',
                    'time_setup': datetime.fromtimestamp(order.time_setup).isoformat(),
                    'comment': order.comment,
                    'magic': order.magic
                }
            
            # Check order history
            history = mt5.history_orders_get(ticket=ticket)
            if history:
                order = history[0]
                return {
                    'order_id': order.ticket,
                    'symbol': order.symbol,
                    'type': self._order_type_to_string(order.type),
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'status': self._order_state_to_string(order.state),
                    'time_setup': datetime.fromtimestamp(order.time_setup).isoformat(),
                    'time_done': datetime.fromtimestamp(order.time_done).isoformat() if order.time_done else None,
                    'comment': order.comment,
                    'magic': order.magic
                }
            
            # Check deals (executed orders)
            deals = mt5.history_deals_get(ticket=ticket)
            if deals:
                deal = deals[0]
                return {
                    'order_id': deal.order,
                    'deal_id': deal.ticket,
                    'symbol': deal.symbol,
                    'type': 'buy' if deal.type == 0 else 'sell',
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'status': 'executed',
                    'time': datetime.fromtimestamp(deal.time).isoformat(),
                    'comment': deal.comment,
                    'magic': deal.magic
                }
            
            logger.warning(f"Order {order_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {e}")
            return None
    
    def _order_type_to_string(self, order_type: int) -> str:
        """Convert MT5 order type to string"""
        type_map = {
            0: 'buy',
            1: 'sell',
            2: 'buy_limit',
            3: 'sell_limit',
            4: 'buy_stop',
            5: 'sell_stop',
            6: 'buy_stop_limit',
            7: 'sell_stop_limit'
        }
        return type_map.get(order_type, 'unknown')
    
    def _order_state_to_string(self, state: int) -> str:
        """Convert MT5 order state to string"""
        state_map = {
            0: 'started',
            1: 'placed',
            2: 'canceled',
            3: 'partial',
            4: 'filled',
            5: 'rejected',
            6: 'expired',
            7: 'request_add',
            8: 'request_modify',
            9: 'request_cancel'
        }
        return state_map.get(state, 'unknown')
    
    async def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """
        Modify stop loss and/or take profit of an existing position.
        
        Args:
            ticket: Position ticket number
            sl: New stop loss price (None to keep current)
            tp: New take profit price (None to keep current)
            
        Returns:
            True if modified successfully
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return False
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                logger.error(f"Position {ticket} not found")
                return False
            
            pos = positions[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl if sl is not None else pos.sl,
                "tp": tp if tp is not None else pos.tp,
            }
            
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Modify position failed: {mt5.last_error()}")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Modify failed: {result.comment} (code: {result.retcode})")
                return False
            
            logger.info(f"Position {ticket} modified: SL={sl}, TP={tp}")
            return True
            
        except Exception as e:
            logger.error(f"Error modifying position {ticket}: {e}")
            return False
    
    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders"""
        if not self.connected:
            logger.error("Not connected to MT5")
            return []
        try:
            orders = mt5.orders_get()
            if orders is None:
                error = mt5.last_error()
                if error[0] != 1:
                    logger.error(f"Failed to get orders: {error}")
                return []
            
            result = []
            for order in orders:
                result.append({
                    'order_id': order.ticket,
                    'symbol': order.symbol,
                    'type': self._order_type_to_string(order.type),
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'status': 'pending',
                    'time_setup': datetime.fromtimestamp(order.time_setup).isoformat(),
                    'comment': order.comment,
                    'magic': order.magic
                })
            return result
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    async def get_trade_history(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get trade history within date range.
        
        Args:
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: now)
            
        Returns:
            List of historical trades
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return []
        try:
            from datetime import timedelta
            
            if from_date is None:
                from_date = datetime.now() - timedelta(days=30)
            if to_date is None:
                to_date = datetime.now()
            
            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                error = mt5.last_error()
                if error[0] != 1:
                    logger.error(f"Failed to get history: {error}")
                return []
            
            result = []
            for deal in deals:
                if deal.entry != 0:  # Skip balance operations
                    result.append({
                        'deal_id': deal.ticket,
                        'order_id': deal.order,
                        'symbol': deal.symbol,
                        'type': 'buy' if deal.type == 0 else 'sell',
                        'entry': 'in' if deal.entry == 0 else 'out',
                        'volume': deal.volume,
                        'price': deal.price,
                        'profit': deal.profit,
                        'commission': deal.commission,
                        'swap': deal.swap,
                        'time': datetime.fromtimestamp(deal.time).isoformat(),
                        'comment': deal.comment,
                        'magic': deal.magic
                    })
            return result
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []

    async def get_account_equity(self) -> float:
        info = await self.get_account_info()
        return info.get('equity', 0.0)

    def _initialize(self):
        """Initialize MT5 terminal"""
        if not mt5.initialize():
            error = mt5.last_error()
            raise ConnectionError(f"MT5 initialization failed: {error}")
        
        logger.info("MT5 initialized successfully")
        
        # Login
        if self.login and self.password and self.server:
            if not mt5.login(self.login, self.password, self.server):
                error = mt5.last_error()
                raise AuthenticationError(f"MT5 login failed: {error}")
            
            logger.info(f"Logged in to MT5 account {self.login}")
            self.connected = True
        else:
            logger.warning("No login credentials provided, using current MT5 session")
            self.connected = True
    
    async def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "elite_bot",
        magic: int = 234000
    ) -> Dict[str, Any]:
        """
        Place order with full error handling
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            order_type: 'buy' or 'sell'
            volume: Order volume in lots
            price: Limit price (None for market orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            magic: Magic number for identification
        
        Returns:
            Dict with order result
        """
        if not self.connected:
            raise ConnectionError("Not connected to MT5")
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found")
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                raise ValueError(f"Failed to select symbol {symbol}")
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Failed to get tick for {symbol}")
        
        # Determine order type
        if order_type.lower() == 'buy':
            trade_type = mt5.ORDER_TYPE_BUY
            execution_price = price if price else tick.ask
        elif order_type.lower() == 'sell':
            trade_type = mt5.ORDER_TYPE_SELL
            execution_price = price if price else tick.bid
        else:
            raise ValueError(f"Invalid order type: {order_type}")
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": trade_type,
            "price": execution_price,
            "sl": sl if sl else 0.0,
            "tp": tp if tp else 0.0,
            "deviation": 20,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            raise OrderExecutionError(f"Order send failed: {error}")
        
        # Check result
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise OrderExecutionError(
                f"Order failed: {result.comment} (code: {result.retcode})"
            )
        
        logger.info(
            f"Order executed: {symbol} {order_type} {volume} @ {result.price}"
        )
        
        return {
            'order_id': result.order,
            'deal_id': result.deal,
            'symbol': symbol,
            'type': order_type,
            'volume': result.volume,
            'price': result.price,
            'sl': sl,
            'tp': tp,
            'comment': result.comment,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")
        
        positions = mt5.positions_get()
        
        if positions is None:
            # No positions or error
            error = mt5.last_error()
            if error[0] != 1:  # 1 = no error, just no positions
                logger.error(f"Failed to get positions: {error}")
            return []
        
        result = []
        for pos in positions:
            result.append({
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'buy' if pos.type == 0 else 'sell',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'sl': pos.sl,
                'tp': pos.tp,
                'time': datetime.fromtimestamp(pos.time).isoformat(),
                'magic': pos.magic,
                'comment': pos.comment
            })
        
        return result
    
    async def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close specific position"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")
        
        # Get position
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            raise PositionNotFoundError(f"Position {ticket} not found")
        
        pos = positions[0]
        
        # Get current price
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            raise ValueError(f"Failed to get tick for {pos.symbol}")
        
        # Determine close type (opposite of position)
        if pos.type == 0:  # Buy position
            close_type = mt5.ORDER_TYPE_SELL
            close_price = tick.bid
        else:  # Sell position
            close_type = mt5.ORDER_TYPE_BUY
            close_price = tick.ask
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": "close_position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            raise OrderExecutionError(f"Close failed: {error}")
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise OrderExecutionError(
                f"Close failed: {result.comment} (code: {result.retcode})"
            )
        
        logger.info(f"Position {ticket} closed at {result.price}")
        
        return {
            'ticket': ticket,
            'close_price': result.price,
            'profit': pos.profit,
            'timestamp': datetime.now().isoformat()
        }
    
    async def close_all_positions(self) -> List[Dict[str, Any]]:
        """Close all open positions"""
        positions = await self.get_positions()
        results = []
        
        for pos in positions:
            try:
                result = await self.close_position(pos['ticket'])
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to close position {pos['ticket']}: {e}")
                results.append({
                    'ticket': pos['ticket'],
                    'error': str(e)
                })
        
        return results
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")
        
        account = mt5.account_info()
        if account is None:
            error = mt5.last_error()
            raise ValueError(f"Failed to get account info: {error}")
        
        return {
            'login': account.login,
            'balance': account.balance,
            'equity': account.equity,
            'profit': account.profit,
            'margin': account.margin,
            'margin_free': account.margin_free,
            'margin_level': account.margin_level,
            'leverage': account.leverage,
            'currency': account.currency,
            'server': account.server,
            'company': account.company
        }
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")
        
        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Symbol {symbol} not found")
        
        return {
            'symbol': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'digits': info.digits,
            'point': info.point,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
            'trade_contract_size': info.trade_contract_size
        }
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.shutdown()


# Custom exceptions
class AuthenticationError(Exception):
    """Authentication failed"""
    pass


class OrderExecutionError(Exception):
    """Order execution failed"""
    pass


class PositionNotFoundError(Exception):
    """Position not found"""
    pass


# Export
__all__ = [
    'MT5BrokerAdapter',
    'OrderType',
    'AuthenticationError',
    'OrderExecutionError',
    'PositionNotFoundError',
    'MT5_AVAILABLE'
]
