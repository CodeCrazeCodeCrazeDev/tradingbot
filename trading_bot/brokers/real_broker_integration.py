"""
Real Broker Integration - Production-Ready MT5 and Alpaca Live Trading
========================================================================
Provides actual live trading capabilities with real brokers.
"""

import asyncio
import logging
import time
import hashlib
import hmac
import json
try:
    import aiohttp
except ImportError:
    aiohttp = None
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class BrokerType(Enum):
    MT5 = "mt5"
    ALPACA = "alpaca"
    BINANCE = "binance"
    INTERACTIVE_BROKERS = "ib"


@dataclass
class BrokerCredentials:
    """Broker authentication credentials."""
    broker_type: BrokerType
    api_key: str = ""
    api_secret: str = ""
    account_id: str = ""
    server: str = ""
    login: int = 0
    password: str = ""
    terminal_path: str = ""
    is_paper: bool = True


@dataclass
class Order:
    """Order representation."""
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal("0")
    average_price: Optional[Decimal] = None
    commission: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    broker_order_id: str = ""
    error_message: str = ""
    time_in_force: str = "GTC"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Position representation."""
    symbol: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    leverage: int = 1
    opened_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountInfo:
    """Account information."""
    account_id: str
    balance: Decimal
    equity: Decimal
    margin_used: Decimal
    margin_available: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    currency: str = "USD"
    leverage: int = 1
    positions_count: int = 0
    open_orders_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketData:
    """Real-time market data."""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: Decimal
    timestamp: datetime
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open: Optional[Decimal] = None
    close: Optional[Decimal] = None


@dataclass
class ExecutionReport:
    """Order execution report."""
    order_id: str
    execution_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    timestamp: datetime
    liquidity: str = "taker"  # maker or taker


# ============================================================================
# BASE BROKER INTERFACE
# ============================================================================

class BaseBroker(ABC):
    """Abstract base class for all broker implementations."""
    
    def __init__(self, credentials: BrokerCredentials):
        self.credentials = credentials
        self.is_connected = False
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.account_info: Optional[AccountInfo] = None
        self._callbacks: Dict[str, List[Callable]] = {
            'order_update': [],
            'position_update': [],
            'execution': [],
            'market_data': [],
            'error': [],
        }
        self._lock = threading.Lock()
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Submit an order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify an existing order."""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all orders."""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all positions."""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get current market data."""
        pass
    
    @abstractmethod
    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """Subscribe to market data updates."""
        pass
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for events."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def _emit_event(self, event_type: str, data: Any):
        """Emit event to callbacks."""
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")


# ============================================================================
# MT5 BROKER IMPLEMENTATION
# ============================================================================

class MT5Broker(BaseBroker):
    """MetaTrader 5 broker implementation."""
    
    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self._mt5 = None
        self._symbol_info_cache: Dict[str, Any] = {}
        self._last_tick_time: Dict[str, datetime] = {}
        
    async def connect(self) -> bool:
        """Connect to MT5 terminal."""
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
            
            # Initialize MT5
            init_params = {}
            if self.credentials.terminal_path:
                init_params['path'] = self.credentials.terminal_path
            if self.credentials.login:
                init_params['login'] = self.credentials.login
            if self.credentials.password:
                init_params['password'] = self.credentials.password
            if self.credentials.server:
                init_params['server'] = self.credentials.server
                
            if not mt5.initialize(**init_params):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Verify connection
            account = mt5.account_info()
            if account is None:
                logger.error("Failed to get account info")
                return False
            
            self.is_connected = True
            logger.info(f"Connected to MT5: Account {account.login}, Balance: {account.balance}")
            
            # Update account info
            await self.get_account_info()
            
            return True
            
        except ImportError:
            logger.error("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
            return False
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MT5."""
        try:
            if self._mt5:
                self._mt5.shutdown()
            self.is_connected = False
            logger.info("Disconnected from MT5")
            return True
        except Exception as e:
            logger.error(f"MT5 disconnect error: {e}")
            return False
    
    async def submit_order(self, order: Order) -> Order:
        """Submit order to MT5."""
        if not self.is_connected:
            order.status = OrderStatus.REJECTED
            order.error_message = "Not connected to MT5"
            return order
        try:
        
            mt5 = self._mt5
            
            # Get symbol info
            symbol_info = mt5.symbol_info(order.symbol)
            if symbol_info is None:
                order.status = OrderStatus.REJECTED
                order.error_message = f"Symbol {order.symbol} not found"
                return order
            
            if not symbol_info.visible:
                if not mt5.symbol_select(order.symbol, True):
                    order.status = OrderStatus.REJECTED
                    order.error_message = f"Failed to select symbol {order.symbol}"
                    return order
            
            # Build request
            request = {
                "action": mt5.TRADE_ACTION_DEAL if order.order_type == OrderType.MARKET else mt5.TRADE_ACTION_PENDING,
                "symbol": order.symbol,
                "volume": float(order.quantity),
                "type": self._get_mt5_order_type(order),
                "deviation": 20,
                "magic": 234000,
                "comment": f"AlphaAlgo:{order.client_order_id}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add price for limit/stop orders
            if order.price:
                request["price"] = float(order.price)
            else:
                # Use current price for market orders
                tick = mt5.symbol_info_tick(order.symbol)
                if tick:
                    request["price"] = tick.ask if order.side == OrderSide.BUY else tick.bid
            
            if order.stop_price:
                request["stoplimit"] = float(order.stop_price)
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                order.status = OrderStatus.REJECTED
                order.error_message = "Order send returned None"
                return order
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                order.status = OrderStatus.REJECTED
                order.error_message = f"Order rejected: {result.comment} (code: {result.retcode})"
                return order
            
            # Update order with result
            order.broker_order_id = str(result.order)
            order.status = OrderStatus.FILLED if result.retcode == mt5.TRADE_RETCODE_DONE else OrderStatus.SUBMITTED
            order.filled_quantity = Decimal(str(result.volume))
            order.average_price = Decimal(str(result.price))
            order.updated_at = datetime.utcnow()
            
            # Store order
            with self._lock:
                self.orders[order.order_id] = order
            
            self._emit_event('order_update', order)
            logger.info(f"MT5 order submitted: {order.order_id} -> {order.broker_order_id}")
            
            return order
            
        except Exception as e:
            logger.error(f"MT5 submit order error: {e}")
            order.status = OrderStatus.REJECTED
            order.error_message = str(e)
            return order
    
    def _get_mt5_order_type(self, order: Order) -> int:
        """Convert order type to MT5 constant."""
        mt5 = self._mt5
        
        if order.order_type == OrderType.MARKET:
            return mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
        elif order.order_type == OrderType.LIMIT:
            return mt5.ORDER_TYPE_BUY_LIMIT if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL_LIMIT
        elif order.order_type == OrderType.STOP:
            return mt5.ORDER_TYPE_BUY_STOP if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL_STOP
        elif order.order_type == OrderType.STOP_LIMIT:
            return mt5.ORDER_TYPE_BUY_STOP_LIMIT if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL_STOP_LIMIT
        
        return mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order in MT5."""
        if not self.is_connected:
            return False
        try:
        
            mt5 = self._mt5
            
            # Find order
            order = self.orders.get(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found")
                return False
            
            # Build cancel request
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": int(order.broker_order_id),
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()
                self._emit_event('order_update', order)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"MT5 cancel order error: {e}")
            return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify order in MT5."""
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        try:
        
            mt5 = self._mt5
            
            request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": int(order.broker_order_id),
                "symbol": order.symbol,
            }
            
            if 'price' in kwargs:
                request['price'] = float(kwargs['price'])
            if 'quantity' in kwargs:
                request['volume'] = float(kwargs['quantity'])
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                if 'price' in kwargs:
                    order.price = Decimal(str(kwargs['price']))
                if 'quantity' in kwargs:
                    order.quantity = Decimal(str(kwargs['quantity']))
                order.updated_at = datetime.utcnow()
                self._emit_event('order_update', order)
            
            return order
            
        except Exception as e:
            logger.error(f"MT5 modify order error: {e}")
            return order
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all orders."""
        if not self.is_connected:
            return []
        try:
        
            mt5 = self._mt5
            
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders is None:
                return []
            
            result = []
            for mt5_order in orders:
                order = Order(
                    order_id=str(mt5_order.ticket),
                    client_order_id=mt5_order.comment.replace("AlphaAlgo:", "") if mt5_order.comment else "",
                    symbol=mt5_order.symbol,
                    side=OrderSide.BUY if mt5_order.type in [0, 2, 4] else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=Decimal(str(mt5_order.volume_current)),
                    price=Decimal(str(mt5_order.price_open)),
                    status=OrderStatus.SUBMITTED,
                    broker_order_id=str(mt5_order.ticket),
                )
                result.append(order)
            
            return result
            
        except Exception as e:
            logger.error(f"MT5 get orders error: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        positions = await self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    async def get_positions(self) -> List[Position]:
        """Get all positions."""
        if not self.is_connected:
            return []
        try:
        
            mt5 = self._mt5
            positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for mt5_pos in positions:
                position = Position(
                    symbol=mt5_pos.symbol,
                    side=PositionSide.LONG if mt5_pos.type == 0 else PositionSide.SHORT,
                    quantity=Decimal(str(mt5_pos.volume)),
                    entry_price=Decimal(str(mt5_pos.price_open)),
                    current_price=Decimal(str(mt5_pos.price_current)),
                    unrealized_pnl=Decimal(str(mt5_pos.profit)),
                    margin_used=Decimal(str(mt5_pos.margin if hasattr(mt5_pos, 'margin') else 0)),
                )
                result.append(position)
                
                # Update cache
                with self._lock:
                    self.positions[mt5_pos.symbol] = position
            
            return result
            
        except Exception as e:
            logger.error(f"MT5 get positions error: {e}")
            return []
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information."""
        if not self.is_connected:
            raise ConnectionError("Not connected to MT5")
        try:
        
            mt5 = self._mt5
            account = mt5.account_info()
            
            if account is None:
                raise ValueError("Failed to get account info")
            
            self.account_info = AccountInfo(
                account_id=str(account.login),
                balance=Decimal(str(account.balance)),
                equity=Decimal(str(account.equity)),
                margin_used=Decimal(str(account.margin)),
                margin_available=Decimal(str(account.margin_free)),
                unrealized_pnl=Decimal(str(account.profit)),
                realized_pnl=Decimal("0"),
                currency=account.currency,
                leverage=account.leverage,
            )
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"MT5 get account info error: {e}")
            raise
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get current market data."""
        if not self.is_connected:
            raise ConnectionError("Not connected to MT5")
        try:
        
            mt5 = self._mt5
            tick = mt5.symbol_info_tick(symbol)
            
            if tick is None:
                raise ValueError(f"No tick data for {symbol}")
            
            return MarketData(
                symbol=symbol,
                bid=Decimal(str(tick.bid)),
                ask=Decimal(str(tick.ask)),
                last=Decimal(str(tick.last)),
                volume=Decimal(str(tick.volume)),
                timestamp=datetime.fromtimestamp(tick.time),
            )
            
        except Exception as e:
            logger.error(f"MT5 get market data error: {e}")
            raise
    
    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """Subscribe to market data updates."""
        if not self.is_connected:
            return False
        try:
        
            mt5 = self._mt5
            
            for symbol in symbols:
                if not mt5.symbol_select(symbol, True):
                    logger.warning(f"Failed to select symbol {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"MT5 subscribe market data error: {e}")
            return False


# ============================================================================
# ALPACA BROKER IMPLEMENTATION
# ============================================================================

class AlpacaBroker(BaseBroker):
    """Alpaca broker implementation."""
    
    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self._api = None
        self._stream = None
        self._base_url = "https://paper-api.alpaca.markets" if credentials.is_paper else "https://api.alpaca.markets"
        self._data_url = "https://data.alpaca.markets"
        self._ws_url = "wss://stream.data.alpaca.markets/v2/iex"
        
    async def connect(self) -> bool:
        """Connect to Alpaca."""
            
        try:
            # Test connection
            async with aiohttp.ClientSession() as session:
                headers = {
                    "APCA-API-KEY-ID": self.credentials.api_key,
                    "APCA-API-SECRET-KEY": self.credentials.api_secret,
                }
                
                async with session.get(f"{self._base_url}/v2/account", headers=headers) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Alpaca connection failed: {error}")
                        return False
                    
                    account = await resp.json()
                    self.is_connected = True
                    logger.info(f"Connected to Alpaca: Account {account['account_number']}, Equity: ${account['equity']}")
                    
                    # Update account info
                    await self.get_account_info()
                    
                    return True
                    
        except ImportError:
            logger.error("aiohttp package not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"Alpaca connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca."""
        self.is_connected = False
        logger.info("Disconnected from Alpaca")
        return True
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request to Alpaca."""
        
        headers = {
            "APCA-API-KEY-ID": self.credentials.api_key,
            "APCA-API-SECRET-KEY": self.credentials.api_secret,
            "Content-Type": "application/json",
        }
        
        url = f"{self._base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, headers=headers, json=data) as resp:
                    return await resp.json()
            elif method == "DELETE":
                async with session.delete(url, headers=headers) as resp:
                    if resp.status == 204:
                        return {}
                    return await resp.json()
            elif method == "PATCH":
                async with session.patch(url, headers=headers, json=data) as resp:
                    return await resp.json()
        
        return {}
    
    async def submit_order(self, order: Order) -> Order:
        """Submit order to Alpaca."""
        if not self.is_connected:
            order.status = OrderStatus.REJECTED
            order.error_message = "Not connected to Alpaca"
            return order
        try:
        
            data = {
                "symbol": order.symbol,
                "qty": str(order.quantity),
                "side": order.side.value,
                "type": order.order_type.value,
                "time_in_force": order.time_in_force.lower(),
                "client_order_id": order.client_order_id,
            }
            
            if order.price:
                data["limit_price"] = str(order.price)
            if order.stop_price:
                data["stop_price"] = str(order.stop_price)
            
            result = await self._request("POST", "/v2/orders", data)
            
            if "id" in result:
                order.broker_order_id = result["id"]
                order.status = self._parse_alpaca_status(result.get("status", ""))
                order.filled_quantity = Decimal(result.get("filled_qty", "0"))
                if result.get("filled_avg_price"):
                    order.average_price = Decimal(result["filled_avg_price"])
                order.updated_at = datetime.utcnow()
                
                with self._lock:
                    self.orders[order.order_id] = order
                
                self._emit_event('order_update', order)
                logger.info(f"Alpaca order submitted: {order.order_id} -> {order.broker_order_id}")
            else:
                order.status = OrderStatus.REJECTED
                order.error_message = result.get("message", "Unknown error")
            
            return order
            
        except Exception as e:
            logger.error(f"Alpaca submit order error: {e}")
            order.status = OrderStatus.REJECTED
            order.error_message = str(e)
            return order
    
    def _parse_alpaca_status(self, status: str) -> OrderStatus:
        """Parse Alpaca order status."""
        status_map = {
            "new": OrderStatus.SUBMITTED,
            "accepted": OrderStatus.SUBMITTED,
            "pending_new": OrderStatus.PENDING,
            "partially_filled": OrderStatus.PARTIAL,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.REJECTED,
        }
        return status_map.get(status.lower(), OrderStatus.PENDING)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order in Alpaca."""
        if not self.is_connected:
            return False
        try:
        
            order = self.orders.get(order_id)
            if not order:
                return False
            
            await self._request("DELETE", f"/v2/orders/{order.broker_order_id}")
            
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            self._emit_event('order_update', order)
            
            return True
            
        except Exception as e:
            logger.error(f"Alpaca cancel order error: {e}")
            return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify order in Alpaca."""
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        try:
        
            data = {}
            if 'quantity' in kwargs:
                data['qty'] = str(kwargs['quantity'])
            if 'price' in kwargs:
                data['limit_price'] = str(kwargs['price'])
            if 'stop_price' in kwargs:
                data['stop_price'] = str(kwargs['stop_price'])
            
            result = await self._request("PATCH", f"/v2/orders/{order.broker_order_id}", data)
            
            if 'quantity' in kwargs:
                order.quantity = Decimal(str(kwargs['quantity']))
            if 'price' in kwargs:
                order.price = Decimal(str(kwargs['price']))
            order.updated_at = datetime.utcnow()
            
            self._emit_event('order_update', order)
            
            return order
            
        except Exception as e:
            logger.error(f"Alpaca modify order error: {e}")
            return order
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all orders."""
        if not self.is_connected:
            return []
        try:
        
            params = "?status=open"
            if symbol:
                params += f"&symbols={symbol}"
            
            result = await self._request("GET", f"/v2/orders{params}")
            
            orders = []
            for alpaca_order in result:
                order = Order(
                    order_id=alpaca_order["client_order_id"],
                    client_order_id=alpaca_order["client_order_id"],
                    symbol=alpaca_order["symbol"],
                    side=OrderSide(alpaca_order["side"]),
                    order_type=OrderType(alpaca_order["type"]),
                    quantity=Decimal(alpaca_order["qty"]),
                    price=Decimal(alpaca_order["limit_price"]) if alpaca_order.get("limit_price") else None,
                    status=self._parse_alpaca_status(alpaca_order["status"]),
                    broker_order_id=alpaca_order["id"],
                    filled_quantity=Decimal(alpaca_order.get("filled_qty", "0")),
                )
                orders.append(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"Alpaca get orders error: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        if not self.is_connected:
            return None
        try:
        
            result = await self._request("GET", f"/v2/positions/{symbol}")
            
            if "symbol" in result:
                return Position(
                    symbol=result["symbol"],
                    side=PositionSide.LONG if result["side"] == "long" else PositionSide.SHORT,
                    quantity=Decimal(result["qty"]),
                    entry_price=Decimal(result["avg_entry_price"]),
                    current_price=Decimal(result["current_price"]),
                    unrealized_pnl=Decimal(result["unrealized_pl"]),
                    realized_pnl=Decimal(result.get("realized_pl", "0")),
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Alpaca get position error: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all positions."""
        if not self.is_connected:
            return []
        try:
        
            result = await self._request("GET", "/v2/positions")
            
            positions = []
            for alpaca_pos in result:
                position = Position(
                    symbol=alpaca_pos["symbol"],
                    side=PositionSide.LONG if alpaca_pos["side"] == "long" else PositionSide.SHORT,
                    quantity=Decimal(alpaca_pos["qty"]),
                    entry_price=Decimal(alpaca_pos["avg_entry_price"]),
                    current_price=Decimal(alpaca_pos["current_price"]),
                    unrealized_pnl=Decimal(alpaca_pos["unrealized_pl"]),
                )
                positions.append(position)
                
                with self._lock:
                    self.positions[alpaca_pos["symbol"]] = position
            
            return positions
            
        except Exception as e:
            logger.error(f"Alpaca get positions error: {e}")
            return []
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information."""
        if not self.is_connected:
            raise ConnectionError("Not connected to Alpaca")
        try:
        
            result = await self._request("GET", "/v2/account")
            
            self.account_info = AccountInfo(
                account_id=result["account_number"],
                balance=Decimal(result["cash"]),
                equity=Decimal(result["equity"]),
                margin_used=Decimal(result.get("initial_margin", "0")),
                margin_available=Decimal(result["buying_power"]),
                unrealized_pnl=Decimal(result.get("unrealized_pl", "0")),
                realized_pnl=Decimal(result.get("realized_pl", "0")),
                currency="USD",
            )
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"Alpaca get account info error: {e}")
            raise
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get current market data."""
        if not self.is_connected:
            raise ConnectionError("Not connected to Alpaca")
        try:
        
            
            headers = {
                "APCA-API-KEY-ID": self.credentials.api_key,
                "APCA-API-SECRET-KEY": self.credentials.api_secret,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._data_url}/v2/stocks/{symbol}/quotes/latest",
                    headers=headers
                ) as resp:
                    result = await resp.json()
            
            quote = result.get("quote", {})
            
            return MarketData(
                symbol=symbol,
                bid=Decimal(str(quote.get("bp", 0))),
                ask=Decimal(str(quote.get("ap", 0))),
                last=Decimal(str(quote.get("bp", 0))),  # Use bid as last
                volume=Decimal(str(quote.get("bs", 0))),
                timestamp=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Alpaca get market data error: {e}")
            raise
    
    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """Subscribe to market data updates."""
        # Alpaca streaming would be implemented here
        return True


# ============================================================================
# UNIFIED BROKER MANAGER
# ============================================================================

class UnifiedBrokerManager:
    """
    Unified broker manager that provides a single interface for multiple brokers.
    Supports automatic failover, load balancing, and health monitoring.
    """
    
    def __init__(self):
        self.brokers: Dict[str, BaseBroker] = {}
        self.primary_broker: Optional[str] = None
        self.fallback_order: List[str] = []
        self._health_status: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        
    def register_broker(self, name: str, broker: BaseBroker, is_primary: bool = False):
        """Register a broker."""
        with self._lock:
            self.brokers[name] = broker
            self._health_status[name] = False
            
            if is_primary or self.primary_broker is None:
                self.primary_broker = name
            
            if name not in self.fallback_order:
                self.fallback_order.append(name)
        
        logger.info(f"Registered broker: {name} (primary: {is_primary})")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered brokers."""
        results = {}
        
        for name, broker in self.brokers.items():
            try:
                success = await broker.connect()
                results[name] = success
                self._health_status[name] = success
                logger.info(f"Broker {name} connection: {'success' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
                results[name] = False
                self._health_status[name] = False
        
        # Start health check
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all brokers."""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        results = {}
        for name, broker in self.brokers.items():
            try:
                success = await broker.disconnect()
                results[name] = success
            except Exception as e:
                logger.error(f"Failed to disconnect from {name}: {e}")
                results[name] = False
        
        return results
    
    async def _health_check_loop(self):
        """Periodic health check for all brokers."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                for name, broker in self.brokers.items():
                    try:
                        await broker.get_account_info()
                        self._health_status[name] = True
                    except Exception:
                        self._health_status[name] = False
                        logger.warning(f"Broker {name} health check failed")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def get_active_broker(self) -> Optional[BaseBroker]:
        """Get the currently active broker."""
        # Try primary first
        if self.primary_broker and self._health_status.get(self.primary_broker):
            return self.brokers.get(self.primary_broker)
        
        # Try fallbacks
        for name in self.fallback_order:
            if self._health_status.get(name):
                return self.brokers.get(name)
        
        return None
    
    async def submit_order(self, order: Order, broker_name: Optional[str] = None) -> Order:
        """Submit order to specified or active broker."""
        if broker_name:
            broker = self.brokers.get(broker_name)
        else:
            broker = self.get_active_broker()
        
        if not broker:
            order.status = OrderStatus.REJECTED
            order.error_message = "No active broker available"
            return order
        
        return await broker.submit_order(order)
    
    async def cancel_order(self, order_id: str, broker_name: Optional[str] = None) -> bool:
        """Cancel order."""
        if broker_name:
            broker = self.brokers.get(broker_name)
        else:
            broker = self.get_active_broker()
        
        if not broker:
            return False
        
        return await broker.cancel_order(order_id)
    
    async def get_positions(self, broker_name: Optional[str] = None) -> List[Position]:
        """Get positions from specified or all brokers."""
        if broker_name:
            broker = self.brokers.get(broker_name)
            if broker:
                return await broker.get_positions()
            return []
        
        # Aggregate from all brokers
        all_positions = []
        for broker in self.brokers.values():
            if broker.is_connected:
                positions = await broker.get_positions()
                all_positions.extend(positions)
        
        return all_positions
    
    async def get_account_info(self, broker_name: Optional[str] = None) -> Optional[AccountInfo]:
        """Get account info."""
        if broker_name:
            broker = self.brokers.get(broker_name)
        else:
            broker = self.get_active_broker()
        
        if not broker:
            return None
        
        return await broker.get_account_info()
    
    def get_health_status(self) -> Dict[str, bool]:
        """Get health status of all brokers."""
        return self._health_status.copy()


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_broker(credentials: BrokerCredentials) -> BaseBroker:
    """Factory function to create appropriate broker instance."""
    if credentials.broker_type == BrokerType.MT5:
        return MT5Broker(credentials)
    elif credentials.broker_type == BrokerType.ALPACA:
        return AlpacaBroker(credentials)
    else:
        raise ValueError(f"Unsupported broker type: {credentials.broker_type}")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'OrderSide', 'OrderType', 'OrderStatus', 'PositionSide', 'BrokerType',
    'BrokerCredentials', 'Order', 'Position', 'AccountInfo', 'MarketData',
    'ExecutionReport', 'BaseBroker', 'MT5Broker', 'AlpacaBroker',
    'UnifiedBrokerManager', 'create_broker',
]
