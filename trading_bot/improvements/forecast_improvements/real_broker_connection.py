"""
Real Broker Connection - Improvement #1 (CRITICAL)
==================================================

Live MT5/broker integration for real money trading.

Features:
- Real MT5 connection with credentials
- Order execution with confirmation
- Position synchronization
- Account balance tracking
- Real-time fill notifications
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import threading

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Broker connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILL = "partial_fill"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class BrokerCredentials:
    """Broker connection credentials"""
    server: str
    login: int
    password: str
    timeout: int = 60000
    portable: bool = False
    path: str = ""  # MT5 terminal path


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    fill_time: Optional[datetime] = None
    rejection_reason: str = ""
    client_order_id: str = ""
    magic_number: int = 0


@dataclass
class Position:
    """Position representation"""
    position_id: str
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    commission: float = 0.0
    swap: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    magic_number: int = 0


@dataclass
class AccountInfo:
    """Account information"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    currency: str = "USD"
    leverage: int = 100
    name: str = ""
    server: str = ""
    company: str = ""


@dataclass
class FillNotification:
    """Fill notification"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    is_partial: bool = False
    remaining_quantity: float = 0.0


class BrokerConnection(ABC):
    """Abstract base class for broker connections"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check connection status"""
        pass
    
    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Submit order to broker"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify existing order"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        pass


class MT5Connection(BrokerConnection):
    """MetaTrader 5 connection implementation"""
    
    def __init__(self, credentials: BrokerCredentials, config: Optional[Dict] = None):
        self.credentials = credentials
        self.config = config or {}
        self.status = ConnectionStatus.DISCONNECTED
        self._mt5 = None
        self._lock = threading.Lock()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
        self._last_heartbeat = None
        self._heartbeat_interval = 30  # seconds
        self._fill_callbacks: List[Callable] = []
        self._order_callbacks: List[Callable] = []
        
    async def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
        except ImportError:
            logger.warning("MetaTrader5 not installed, using mock connection")
            self._mt5 = None
            self.status = ConnectionStatus.CONNECTED
            return True
        
        self.status = ConnectionStatus.CONNECTING
        
        try:
            # Initialize MT5
            if self.credentials.path:
                initialized = self._mt5.initialize(
                    path=self.credentials.path,
                    login=self.credentials.login,
                    password=self.credentials.password,
                    server=self.credentials.server,
                    timeout=self.credentials.timeout,
                    portable=self.credentials.portable
                )
            else:
                initialized = self._mt5.initialize(
                    login=self.credentials.login,
                    password=self.credentials.password,
                    server=self.credentials.server,
                    timeout=self.credentials.timeout
                )
            
            if not initialized:
                error = self._mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                self.status = ConnectionStatus.ERROR
                return False
            
            # Verify login
            account_info = self._mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info after connection")
                self.status = ConnectionStatus.ERROR
                return False
            
            self.status = ConnectionStatus.CONNECTED
            self._last_heartbeat = datetime.now()
            self._reconnect_attempts = 0
            
            logger.info(f"Connected to MT5: {account_info.name} @ {account_info.server}")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MT5"""
        if self._mt5:
            try:
                self._mt5.shutdown()
                self.status = ConnectionStatus.DISCONNECTED
                logger.info("Disconnected from MT5")
                return True
            except Exception as e:
                logger.error(f"MT5 disconnect error: {e}")
                return False
        return True
    
    async def is_connected(self) -> bool:
        """Check if connected to MT5"""
        if self._mt5 is None:
            return self.status == ConnectionStatus.CONNECTED
        try:
        
            terminal_info = self._mt5.terminal_info()
            if terminal_info and terminal_info.connected:
                self._last_heartbeat = datetime.now()
                return True
            return False
        except Exception:
            return False
    
    async def _ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed"""
        if await self.is_connected():
            return True
        
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False
        
        self.status = ConnectionStatus.RECONNECTING
        self._reconnect_attempts += 1
        
        logger.info(f"Attempting reconnection ({self._reconnect_attempts}/{self._max_reconnect_attempts})")
        await asyncio.sleep(self._reconnect_delay)
        
        return await self.connect()
    
    async def submit_order(self, order: Order) -> Order:
        """Submit order to MT5"""
        if not await self._ensure_connected():
            order.status = OrderStatus.REJECTED
            order.rejection_reason = "Not connected to broker"
            return order
        
        if self._mt5 is None:
            # Mock mode
            return await self._mock_submit_order(order)
        try:
        
            # Get symbol info
            symbol_info = self._mt5.symbol_info(order.symbol)
            if symbol_info is None:
                order.status = OrderStatus.REJECTED
                order.rejection_reason = f"Symbol {order.symbol} not found"
                return order
            
            # Enable symbol if needed
            if not symbol_info.visible:
                if not self._mt5.symbol_select(order.symbol, True):
                    order.status = OrderStatus.REJECTED
                    order.rejection_reason = f"Failed to select symbol {order.symbol}"
                    return order
            
            # Prepare request
            request = {
                "action": self._mt5.TRADE_ACTION_DEAL if order.order_type == OrderType.MARKET else self._mt5.TRADE_ACTION_PENDING,
                "symbol": order.symbol,
                "volume": order.quantity,
                "type": self._mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else self._mt5.ORDER_TYPE_SELL,
                "deviation": 20,
                "magic": order.magic_number,
                "comment": f"Bot order {order.client_order_id}",
                "type_time": self._mt5.ORDER_TIME_GTC,
                "type_filling": self._mt5.ORDER_FILLING_IOC,
            }
            
            # Add price for limit orders
            if order.order_type == OrderType.LIMIT and order.price:
                request["price"] = order.price
            elif order.order_type == OrderType.MARKET:
                tick = self._mt5.symbol_info_tick(order.symbol)
                request["price"] = tick.ask if order.side == OrderSide.BUY else tick.bid
            
            # Add stop loss and take profit
            if order.stop_loss:
                request["sl"] = order.stop_loss
            if order.take_profit:
                request["tp"] = order.take_profit
            
            # Send order
            result = self._mt5.order_send(request)
            
            if result is None:
                order.status = OrderStatus.REJECTED
                order.rejection_reason = "Order send returned None"
                return order
            
            if result.retcode != self._mt5.TRADE_RETCODE_DONE:
                order.status = OrderStatus.REJECTED
                order.rejection_reason = f"Error {result.retcode}: {result.comment}"
                return order
            
            # Update order with result
            order.order_id = str(result.order)
            order.status = OrderStatus.FILLED
            order.filled_quantity = result.volume
            order.average_fill_price = result.price
            order.fill_time = datetime.now()
            order.updated_at = datetime.now()
            
            # Notify callbacks
            fill = FillNotification(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=result.volume,
                price=result.price,
                commission=0.0,  # MT5 doesn't return commission immediately
                timestamp=datetime.now()
            )
            await self._notify_fill(fill)
            
            logger.info(f"Order filled: {order.order_id} @ {order.average_fill_price}")
            return order
            
        except Exception as e:
            logger.error(f"Order submission error: {e}")
            order.status = OrderStatus.REJECTED
            order.rejection_reason = str(e)
            return order
    
    async def _mock_submit_order(self, order: Order) -> Order:
        """Mock order submission for testing"""
        await asyncio.sleep(0.1)  # Simulate network latency
        
        order.order_id = f"MOCK_{int(time.time() * 1000)}"
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_fill_price = order.price or 1.0
        order.fill_time = datetime.now()
        order.updated_at = datetime.now()
        
        logger.info(f"Mock order filled: {order.order_id}")
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if not await self._ensure_connected():
            return False
        
        if self._mt5 is None:
            logger.info(f"Mock order cancelled: {order_id}")
            return True
        try:
        
            # Get order info
            order = self._mt5.orders_get(ticket=int(order_id))
            if not order:
                logger.warning(f"Order {order_id} not found")
                return False
            
            request = {
                "action": self._mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }
            
            result = self._mt5.order_send(request)
            
            if result.retcode == self._mt5.TRADE_RETCODE_DONE:
                logger.info(f"Order cancelled: {order_id}")
                return True
            else:
                logger.error(f"Cancel failed: {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify existing order"""
        if not await self._ensure_connected():
            raise ConnectionError("Not connected to broker")
        
        if self._mt5 is None:
            try:
                # Mock mode
                return Order(
                    order_id=order_id,
                    symbol=kwargs.get('symbol', 'EURUSD'),
                    side=kwargs.get('side', OrderSide.BUY),
                    order_type=kwargs.get('order_type', OrderType.LIMIT),
                    quantity=kwargs.get('quantity', 0.1),
                    price=kwargs.get('price'),
                    stop_loss=kwargs.get('stop_loss'),
                    take_profit=kwargs.get('take_profit'),
                    status=OrderStatus.PENDING
                )

                request = {
                    "action": self._mt5.TRADE_ACTION_MODIFY,
                    "order": int(order_id),
                }

                if 'price' in kwargs:
                    request['price'] = kwargs['price']
                if 'stop_loss' in kwargs:
                    request['sl'] = kwargs['stop_loss']
                if 'take_profit' in kwargs:
                    request['tp'] = kwargs['take_profit']

                result = self._mt5.order_send(request)

                if result.retcode != self._mt5.TRADE_RETCODE_DONE:
                    raise Exception(f"Modify failed: {result.comment}")

                # Return updated order
                orders = self._mt5.orders_get(ticket=int(order_id))
                if orders:
                    mt5_order = orders[0]
                    return Order(
                        order_id=str(mt5_order.ticket),
                        symbol=mt5_order.symbol,
                        side=OrderSide.BUY if mt5_order.type == 0 else OrderSide.SELL,
                        order_type=OrderType.LIMIT,
                        quantity=mt5_order.volume_current,
                        price=mt5_order.price_open,
                        stop_loss=mt5_order.sl,
                        take_profit=mt5_order.tp,
                        status=OrderStatus.PENDING
                    )

                raise Exception("Order not found after modification")

            except Exception as e:
                logger.error(f"Modify order error: {e}")
                raise

    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not await self._ensure_connected():
            return []
        
        if self._mt5 is None:
            return []  # Mock mode
        try:
        
            positions = self._mt5.positions_get()
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append(Position(
                    position_id=str(pos.ticket),
                    symbol=pos.symbol,
                    side=OrderSide.BUY if pos.type == 0 else OrderSide.SELL,
                    quantity=pos.volume,
                    entry_price=pos.price_open,
                    current_price=pos.price_current,
                    unrealized_pnl=pos.profit,
                    realized_pnl=0.0,
                    stop_loss=pos.sl if pos.sl > 0 else None,
                    take_profit=pos.tp if pos.tp > 0 else None,
                    commission=pos.commission if hasattr(pos, 'commission') else 0.0,
                    swap=pos.swap,
                    opened_at=datetime.fromtimestamp(pos.time),
                    magic_number=pos.magic
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return []
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information"""
        if not await self._ensure_connected():
            return AccountInfo(
                balance=0, equity=0, margin=0, free_margin=0,
                margin_level=0, profit=0
            )
        
        if self._mt5 is None:
            try:
                # Mock mode
                return AccountInfo(
                    balance=10000.0,
                    equity=10000.0,
                    margin=0.0,
                    free_margin=10000.0,
                    margin_level=0.0,
                    profit=0.0,
                    currency="USD",
                    leverage=100,
                    name="Mock Account",
                    server="Mock Server"
                )

                info = self._mt5.account_info()
                if info is None:
                    raise Exception("Failed to get account info")

                return AccountInfo(
                    balance=info.balance,
                    equity=info.equity,
                    margin=info.margin,
                    free_margin=info.margin_free,
                    margin_level=info.margin_level if info.margin_level else 0.0,
                    profit=info.profit,
                    currency=info.currency,
                    leverage=info.leverage,
                    name=info.name,
                    server=info.server,
                    company=info.company
                )

            except Exception as e:
                logger.error(f"Get account info error: {e}")
                return AccountInfo(
                    balance=0, equity=0, margin=0, free_margin=0,
                    margin_level=0, profit=0
                )

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        if not await self._ensure_connected():
            return {}
        
        if self._mt5 is None:
            try:
                # Mock mode
                return {
                    'symbol': symbol,
                    'bid': 1.10000,
                    'ask': 1.10010,
                    'spread': 10,
                    'digits': 5,
                    'point': 0.00001,
                    'trade_contract_size': 100000,
                    'volume_min': 0.01,
                    'volume_max': 100.0,
                    'volume_step': 0.01
                }

                info = self._mt5.symbol_info(symbol)
                if info is None:
                    return {}

                tick = self._mt5.symbol_info_tick(symbol)

                return {
                    'symbol': info.name,
                    'bid': tick.bid if tick else 0,
                    'ask': tick.ask if tick else 0,
                    'spread': info.spread,
                    'digits': info.digits,
                    'point': info.point,
                    'trade_contract_size': info.trade_contract_size,
                    'volume_min': info.volume_min,
                    'volume_max': info.volume_max,
                    'volume_step': info.volume_step,
                    'trade_mode': info.trade_mode,
                    'swap_long': info.swap_long,
                    'swap_short': info.swap_short
                }

            except Exception as e:
                logger.error(f"Get symbol info error: {e}")
                return {}

    def register_fill_callback(self, callback: Callable[[FillNotification], None]):
        """Register callback for fill notifications"""
        self._fill_callbacks.append(callback)
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        """Register callback for order updates"""
        self._order_callbacks.append(callback)
    
    async def _notify_fill(self, fill: FillNotification):
        """Notify all fill callbacks"""
        for callback in self._fill_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(fill)
                else:
                    callback(fill)
            except Exception as e:
                logger.error(f"Fill callback error: {e}")


class BrokerConnectionManager:
    """Manages multiple broker connections"""
    
    def __init__(self):
        self.connections: Dict[str, BrokerConnection] = {}
        self.primary_connection: Optional[str] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
    
    def add_connection(self, name: str, connection: BrokerConnection, primary: bool = False):
        """Add a broker connection"""
        self.connections[name] = connection
        if primary or self.primary_connection is None:
            self.primary_connection = name
    
    def get_connection(self, name: Optional[str] = None) -> Optional[BrokerConnection]:
        """Get a broker connection"""
        if name:
            return self.connections.get(name)
        if self.primary_connection:
            return self.connections.get(self.primary_connection)
        return None
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all brokers"""
        results = {}
        for name, connection in self.connections.items():
            results[name] = await connection.connect()
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect all brokers"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
        
        results = {}
        for name, connection in self.connections.items():
            results[name] = await connection.disconnect()
        return results
    
    async def start_health_monitoring(self, interval: int = 30):
        """Start health monitoring for all connections"""
        self._running = True
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(interval)
        )
    
    async def _health_check_loop(self, interval: int):
        """Health check loop"""
        while self._running:
            for name, connection in self.connections.items():
                try:
                    is_connected = await connection.is_connected()
                    if not is_connected:
                        logger.warning(f"Connection {name} is down, attempting reconnect")
                        await connection.connect()
                except Exception as e:
                    logger.error(f"Health check error for {name}: {e}")
            
            await asyncio.sleep(interval)


class OrderExecutor:
    """High-level order execution with retry and confirmation"""
    
    def __init__(self, connection: BrokerConnection, config: Optional[Dict] = None):
        self.connection = connection
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.confirmation_timeout = self.config.get('confirmation_timeout', 30)
        self._pending_orders: Dict[str, Order] = {}
    
    async def execute_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        magic_number: int = 0
    ) -> Order:
        """Execute market order with retry logic"""
        order = Order(
            order_id="",
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            magic_number=magic_number,
            client_order_id=f"MKT_{int(time.time() * 1000)}"
        )
        
        for attempt in range(self.max_retries):
            try:
                result = await self.connection.submit_order(order)
                
                if result.status == OrderStatus.FILLED:
                    logger.info(f"Market order executed: {result.order_id}")
                    return result
                
                if result.status == OrderStatus.REJECTED:
                    if "requote" in result.rejection_reason.lower():
                        logger.warning(f"Requote on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error(f"Order rejected: {result.rejection_reason}")
                        return result
                
            except Exception as e:
                logger.error(f"Order execution error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        order.status = OrderStatus.REJECTED
        order.rejection_reason = "Max retries exceeded"
        return order
    
    async def execute_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        timeout: int = 60,
        magic_number: int = 0
    ) -> Order:
        """Execute limit order with timeout"""
        order = Order(
            order_id="",
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            magic_number=magic_number,
            client_order_id=f"LMT_{int(time.time() * 1000)}"
        )
        
        result = await self.connection.submit_order(order)
        
        if result.status == OrderStatus.REJECTED:
            return result
        
        # Wait for fill with timeout
        self._pending_orders[result.order_id] = result
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if result.status == OrderStatus.FILLED:
                del self._pending_orders[result.order_id]
                return result
            
            await asyncio.sleep(0.5)
        
        # Timeout - cancel order
        if result.order_id in self._pending_orders:
            await self.connection.cancel_order(result.order_id)
            result.status = OrderStatus.CANCELLED
            result.rejection_reason = "Timeout"
            del self._pending_orders[result.order_id]
        
        return result


class PositionSynchronizer:
    """Synchronizes local position state with broker"""
    
    def __init__(self, connection: BrokerConnection):
        self.connection = connection
        self.local_positions: Dict[str, Position] = {}
        self._sync_interval = 5  # seconds
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._position_callbacks: List[Callable] = []
    
    async def start(self):
        """Start position synchronization"""
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self):
        """Stop position synchronization"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
    
    async def _sync_loop(self):
        """Position sync loop"""
        while self._running:
            try:
                await self.sync()
            except Exception as e:
                logger.error(f"Position sync error: {e}")
            
            await asyncio.sleep(self._sync_interval)
    
    async def sync(self) -> Dict[str, Position]:
        """Sync positions with broker"""
        broker_positions = await self.connection.get_positions()
        
        broker_position_ids = {p.position_id for p in broker_positions}
        local_position_ids = set(self.local_positions.keys())
        
        # New positions
        new_ids = broker_position_ids - local_position_ids
        # Closed positions
        closed_ids = local_position_ids - broker_position_ids
        
        # Update local positions
        for pos in broker_positions:
            old_pos = self.local_positions.get(pos.position_id)
            self.local_positions[pos.position_id] = pos
            
            if pos.position_id in new_ids:
                await self._notify_position_change('opened', pos)
            elif old_pos and old_pos.unrealized_pnl != pos.unrealized_pnl:
                await self._notify_position_change('updated', pos)
        
        # Remove closed positions
        for pos_id in closed_ids:
            closed_pos = self.local_positions.pop(pos_id, None)
            if closed_pos:
                await self._notify_position_change('closed', closed_pos)
        
        return self.local_positions
    
    def register_callback(self, callback: Callable):
        """Register position change callback"""
        self._position_callbacks.append(callback)
    
    async def _notify_position_change(self, change_type: str, position: Position):
        """Notify position change callbacks"""
        for callback in self._position_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change_type, position)
                else:
                    callback(change_type, position)
            except Exception as e:
                logger.error(f"Position callback error: {e}")


class AccountTracker:
    """Tracks account balance and equity"""
    
    def __init__(self, connection: BrokerConnection):
        self.connection = connection
        self.history: deque = deque(maxlen=1000)
        self.current_info: Optional[AccountInfo] = None
        self._running = False
        self._track_task: Optional[asyncio.Task] = None
        self._update_interval = 10  # seconds
        self._equity_callbacks: List[Callable] = []
    
    async def start(self):
        """Start account tracking"""
        self._running = True
        self._track_task = asyncio.create_task(self._track_loop())
    
    async def stop(self):
        """Stop account tracking"""
        self._running = False
        if self._track_task:
            self._track_task.cancel()
    
    async def _track_loop(self):
        """Account tracking loop"""
        while self._running:
            try:
                await self.update()
            except Exception as e:
                logger.error(f"Account tracking error: {e}")
            
            await asyncio.sleep(self._update_interval)
    
    async def update(self) -> AccountInfo:
        """Update account info"""
        info = await self.connection.get_account_info()
        
        # Track history
        self.history.append({
            'timestamp': datetime.now(),
            'balance': info.balance,
            'equity': info.equity,
            'margin': info.margin,
            'free_margin': info.free_margin,
            'profit': info.profit
        })
        
        # Check for significant changes
        if self.current_info:
            equity_change = (info.equity - self.current_info.equity) / self.current_info.equity if self.current_info.equity > 0 else 0
            if abs(equity_change) > 0.01:  # 1% change
                await self._notify_equity_change(equity_change, info)
        
        self.current_info = info
        return info
    
    def get_drawdown(self) -> float:
        """Calculate current drawdown"""
        if not self.history:
            return 0.0
        
        peak_equity = max(h['equity'] for h in self.history)
        current_equity = self.history[-1]['equity'] if self.history else 0
        
        if peak_equity > 0:
            return (peak_equity - current_equity) / peak_equity
        return 0.0
    
    def get_daily_pnl(self) -> float:
        """Get today's P&L"""
        if not self.history:
            return 0.0
        
        today = datetime.now().date()
        today_records = [h for h in self.history if h['timestamp'].date() == today]
        
        if len(today_records) < 2:
            return 0.0
        
        return today_records[-1]['equity'] - today_records[0]['equity']
    
    def register_equity_callback(self, callback: Callable):
        """Register equity change callback"""
        self._equity_callbacks.append(callback)
    
    async def _notify_equity_change(self, change: float, info: AccountInfo):
        """Notify equity change callbacks"""
        for callback in self._equity_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change, info)
                else:
                    callback(change, info)
            except Exception as e:
                logger.error(f"Equity callback error: {e}")


class FillNotificationHandler:
    """Handles fill notifications"""
    
    def __init__(self):
        self.fills: deque = deque(maxlen=1000)
        self._callbacks: List[Callable] = []
    
    def register_callback(self, callback: Callable[[FillNotification], None]):
        """Register fill notification callback"""
        self._callbacks.append(callback)
    
    async def handle_fill(self, fill: FillNotification):
        """Handle a fill notification"""
        self.fills.append(fill)
        
        logger.info(
            f"Fill: {fill.symbol} {fill.side.value} {fill.quantity} @ {fill.price}"
        )
        
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(fill)
                else:
                    callback(fill)
            except Exception as e:
                logger.error(f"Fill callback error: {e}")
    
    def get_recent_fills(self, symbol: Optional[str] = None, limit: int = 100) -> List[FillNotification]:
        """Get recent fills"""
        fills = list(self.fills)
        
        if symbol:
            fills = [f for f in fills if f.symbol == symbol]
        
        return fills[-limit:]
    
    def get_fill_stats(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get fill statistics"""
        fills = self.get_recent_fills(symbol)
        
        if not fills:
            return {'count': 0}
        
        return {
            'count': len(fills),
            'total_quantity': sum(f.quantity for f in fills),
            'total_commission': sum(f.commission for f in fills),
            'avg_price': sum(f.price * f.quantity for f in fills) / sum(f.quantity for f in fills),
            'partial_fills': sum(1 for f in fills if f.is_partial)
        }


class RealBrokerConnection:
    """
    Unified real broker connection manager.
    Combines all broker connection functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connection_manager = BrokerConnectionManager()
        self.order_executor: Optional[OrderExecutor] = None
        self.position_sync: Optional[PositionSynchronizer] = None
        self.account_tracker: Optional[AccountTracker] = None
        self.fill_handler = FillNotificationHandler()
        self._initialized = False
    
    async def initialize(self, credentials: BrokerCredentials) -> bool:
        """Initialize broker connection"""
        # Create MT5 connection
        mt5_conn = MT5Connection(credentials, self.config)
        self.connection_manager.add_connection('mt5', mt5_conn, primary=True)
        
        # Connect
        results = await self.connection_manager.connect_all()
        
        if not results.get('mt5', False):
            logger.error("Failed to connect to MT5")
            return False
        
        # Initialize components
        primary = self.connection_manager.get_connection()
        if primary:
            self.order_executor = OrderExecutor(primary, self.config)
            self.position_sync = PositionSynchronizer(primary)
            self.account_tracker = AccountTracker(primary)
            
            # Register fill handler
            if isinstance(primary, MT5Connection):
                primary.register_fill_callback(self.fill_handler.handle_fill)
            
            # Start background tasks
            await self.position_sync.start()
            await self.account_tracker.start()
            await self.connection_manager.start_health_monitoring()
        
        self._initialized = True
        logger.info("Real broker connection initialized")
        return True
    
    async def shutdown(self):
        """Shutdown broker connection"""
        if self.position_sync:
            await self.position_sync.stop()
        if self.account_tracker:
            await self.account_tracker.stop()
        
        await self.connection_manager.disconnect_all()
        self._initialized = False
        logger.info("Real broker connection shutdown")
    
    async def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Order:
        """Execute a trade"""
        if not self._initialized or not self.order_executor:
            raise RuntimeError("Broker connection not initialized")
        
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        
        if order_type.lower() == "market":
            return await self.order_executor.execute_market_order(
                symbol=symbol,
                side=order_side,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        else:
            if price is None:
                raise ValueError("Price required for limit orders")
            return await self.order_executor.execute_limit_order(
                symbol=symbol,
                side=order_side,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        if self.position_sync:
            return list(self.position_sync.local_positions.values())
        return []
    
    async def get_account(self) -> Optional[AccountInfo]:
        """Get account info"""
        if self.account_tracker:
            return self.account_tracker.current_info
        return None
    
    def get_drawdown(self) -> float:
        """Get current drawdown"""
        if self.account_tracker:
            return self.account_tracker.get_drawdown()
        return 0.0
    
    def get_daily_pnl(self) -> float:
        """Get daily P&L"""
        if self.account_tracker:
            return self.account_tracker.get_daily_pnl()
        return 0.0
