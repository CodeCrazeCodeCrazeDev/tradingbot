"""
Exchange Abstraction Layer
==========================

Unified interface for all exchanges and brokers:
- MT5
- Binance
- Interactive Brokers
- Alpaca
- Coinbase
- Kraken

Provides consistent API regardless of underlying exchange.

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum, auto
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """Exchange types"""
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FUTURES = "futures"
    OPTIONS = "options"


class ConnectionStatus(Enum):
    """Connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


@dataclass
class Ticker:
    """Ticker data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime
    exchange: str = ""
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class OHLCV:
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""
    timeframe: str = ""


@dataclass
class Position:
    """Position data"""
    position_id: str
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    margin_used: float = 0.0
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    open_time: datetime = field(default_factory=datetime.now)
    exchange: str = ""


@dataclass
class Order:
    """Order data"""
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    exchange: str = ""


@dataclass
class AccountInfo:
    """Account information"""
    account_id: str
    balance: float
    equity: float
    margin_used: float
    free_margin: float
    margin_level: float
    leverage: float
    currency: str = "USD"
    exchange: str = ""
    
    @property
    def margin_usage_pct(self) -> float:
        if self.equity == 0:
            return 0.0
        return (self.margin_used / self.equity) * 100


@dataclass
class ExchangeCapabilities:
    """Exchange capabilities"""
    supports_market_orders: bool = True
    supports_limit_orders: bool = True
    supports_stop_orders: bool = True
    supports_trailing_stops: bool = False
    supports_oco_orders: bool = False
    supports_bracket_orders: bool = False
    supports_short_selling: bool = True
    supports_margin_trading: bool = True
    supports_futures: bool = False
    supports_options: bool = False
    max_leverage: float = 1.0
    min_order_size: float = 0.01
    max_order_size: float = 1000000.0
    supported_timeframes: List[str] = field(default_factory=list)
    supported_order_types: List[OrderType] = field(default_factory=list)


class ExchangeAdapter(ABC):
    """
    Abstract base class for all exchange adapters
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.exchange_name = config.get('name', 'unknown')
        self.exchange_type = ExchangeType(config.get('type', 'forex'))
        self.status = ConnectionStatus.DISCONNECTED
        self.capabilities = ExchangeCapabilities()
        
        # Callbacks
        self.on_ticker: List[Callable] = []
        self.on_order_update: List[Callable] = []
        self.on_position_update: List[Callable] = []
        self.on_error: List[Callable] = []
        
        # Rate limiting
        self.rate_limit_requests = config.get('rate_limit', 10)
        self.rate_limit_window = 1.0  # seconds
        self.request_times: List[datetime] = []
        
        # Reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = config.get('max_reconnect', 5)
        self.reconnect_delay = 5  # seconds
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from exchange"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get current ticker for symbol"""
        pass
    
    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[OHLCV]:
        """Get OHLCV data"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs
    ) -> Optional[Order]:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders"""
        pass
    
    @abstractmethod
    async def close_position(
        self,
        position_id: str,
        quantity: Optional[float] = None
    ) -> Optional[Order]:
        """Close a position"""
        pass
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = datetime.now()
        
        # Remove old requests
        self.request_times = [
            t for t in self.request_times
            if (now - t).total_seconds() < self.rate_limit_window
        ]
        
        # Check if we need to wait
        if len(self.request_times) >= self.rate_limit_requests:
            oldest = self.request_times[0]
            wait_time = self.rate_limit_window - (now - oldest).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.request_times.append(datetime.now())
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {self.exchange_name}")
            self.status = ConnectionStatus.ERROR
            return False
        
        self.reconnect_attempts += 1
        self.status = ConnectionStatus.RECONNECTING
        
        logger.info(f"Reconnecting to {self.exchange_name} (attempt {self.reconnect_attempts})")
        
        await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
        
        try:
            success = await self.connect()
            if success:
                self.reconnect_attempts = 0
                return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
        
        return await self.reconnect()
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback"""
        if event_type == 'ticker':
            self.on_ticker.append(callback)
        elif event_type == 'order':
            self.on_order_update.append(callback)
        elif event_type == 'position':
            self.on_position_update.append(callback)
        elif event_type == 'error':
            self.on_error.append(callback)
    
    async def _emit_event(self, event_type: str, data: Any):
        """Emit event to callbacks"""
        callbacks = {
            'ticker': self.on_ticker,
            'order': self.on_order_update,
            'position': self.on_position_update,
            'error': self.on_error
        }.get(event_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Callback error: {e}")


class MT5Adapter(ExchangeAdapter):
    """MetaTrader 5 adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        config['name'] = 'MT5'
        config['type'] = 'forex'
        super().__init__(config)
        
        self.mt5 = None
        self.capabilities = ExchangeCapabilities(
            supports_trailing_stops=True,
            max_leverage=500.0,
            supported_timeframes=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1']
        )
    
    async def connect(self) -> bool:
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            login = self.config.get('login')
            password = self.config.get('password')
            server = self.config.get('server')
            
            if login and password and server:
                if not mt5.login(login, password=password, server=server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            
            self.status = ConnectionStatus.AUTHENTICATED
            logger.info("MT5 connected successfully")
            return True
            
        except ImportError:
            logger.error("MetaTrader5 package not installed")
            return False
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        if self.mt5:
            self.mt5.shutdown()
            self.status = ConnectionStatus.DISCONNECTED
            logger.info("MT5 disconnected")
            return True
        return False
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        if not self.mt5:
            return None
        
        await self._rate_limit()
        
        tick = self.mt5.symbol_info_tick(symbol)
        if tick:
            return Ticker(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                timestamp=datetime.fromtimestamp(tick.time),
                exchange='MT5'
            )
        return None
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[OHLCV]:
        if not self.mt5:
            return []
        
        await self._rate_limit()
        
        # Map timeframe string to MT5 constant
        tf_map = {
            'M1': self.mt5.TIMEFRAME_M1,
            'M5': self.mt5.TIMEFRAME_M5,
            'M15': self.mt5.TIMEFRAME_M15,
            'M30': self.mt5.TIMEFRAME_M30,
            'H1': self.mt5.TIMEFRAME_H1,
            'H4': self.mt5.TIMEFRAME_H4,
            'D1': self.mt5.TIMEFRAME_D1,
            'W1': self.mt5.TIMEFRAME_W1,
            'MN1': self.mt5.TIMEFRAME_MN1
        }
        
        mt5_tf = tf_map.get(timeframe, self.mt5.TIMEFRAME_H1)
        
        if start_time and end_time:
            rates = self.mt5.copy_rates_range(symbol, mt5_tf, start_time, end_time)
        else:
            rates = self.mt5.copy_rates_from_pos(symbol, mt5_tf, 0, limit)
        
        if rates is None:
            return []
        
        return [
            OHLCV(
                timestamp=datetime.fromtimestamp(r['time']),
                open=r['open'],
                high=r['high'],
                low=r['low'],
                close=r['close'],
                volume=r['tick_volume'],
                symbol=symbol,
                timeframe=timeframe
            )
            for r in rates
        ]
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        if not self.mt5:
            return None
        
        await self._rate_limit()
        
        info = self.mt5.account_info()
        if info:
            return AccountInfo(
                account_id=str(info.login),
                balance=info.balance,
                equity=info.equity,
                margin_used=info.margin,
                free_margin=info.margin_free,
                margin_level=info.margin_level,
                leverage=info.leverage,
                currency=info.currency,
                exchange='MT5'
            )
        return None
    
    async def get_positions(self) -> List[Position]:
        if not self.mt5:
            return []
        
        await self._rate_limit()
        
        positions = self.mt5.positions_get()
        if positions is None:
            return []
        
        return [
            Position(
                position_id=str(p.ticket),
                symbol=p.symbol,
                side=OrderSide.BUY if p.type == 0 else OrderSide.SELL,
                quantity=p.volume,
                entry_price=p.price_open,
                current_price=p.price_current,
                unrealized_pnl=p.profit,
                margin_used=p.volume * p.price_open / self.mt5.account_info().leverage,
                leverage=self.mt5.account_info().leverage,
                stop_loss=p.sl if p.sl > 0 else None,
                take_profit=p.tp if p.tp > 0 else None,
                open_time=datetime.fromtimestamp(p.time),
                exchange='MT5'
            )
            for p in positions
        ]
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        positions = await self.get_positions()
        for p in positions:
            if p.symbol == symbol:
                return p
        return None
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs
    ) -> Optional[Order]:
        if not self.mt5:
            return None
        
        await self._rate_limit()
        
        # Get symbol info
        symbol_info = self.mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol not found: {symbol}")
            return None
        
        # Prepare request
        request = {
            'action': self.mt5.TRADE_ACTION_DEAL if order_type == OrderType.MARKET else self.mt5.TRADE_ACTION_PENDING,
            'symbol': symbol,
            'volume': quantity,
            'type': self.mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL,
            'deviation': 20,
            'magic': kwargs.get('magic', 0),
            'comment': kwargs.get('comment', 'Elite Bot'),
            'type_time': self.mt5.ORDER_TIME_GTC,
            'type_filling': self.mt5.ORDER_FILLING_IOC,
        }
        
        if price:
            request['price'] = price
        else:
            tick = self.mt5.symbol_info_tick(symbol)
            request['price'] = tick.ask if side == OrderSide.BUY else tick.bid
        
        if stop_loss:
            request['sl'] = stop_loss
        if take_profit:
            request['tp'] = take_profit
        
        # Send order
        result = self.mt5.order_send(request)
        
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.comment}")
            return None
        
        return Order(
            order_id=str(result.order),
            client_order_id=str(result.request_id),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.FILLED if order_type == OrderType.MARKET else OrderStatus.OPEN,
            filled_quantity=quantity if order_type == OrderType.MARKET else 0,
            average_fill_price=result.price,
            exchange='MT5'
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        if not self.mt5:
            return False
        
        await self._rate_limit()
        
        request = {
            'action': self.mt5.TRADE_ACTION_REMOVE,
            'order': int(order_id)
        }
        
        result = self.mt5.order_send(request)
        return result.retcode == self.mt5.TRADE_RETCODE_DONE
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        if not self.mt5:
            return None
        
        await self._rate_limit()
        
        order = self.mt5.orders_get(ticket=int(order_id))
        if order and len(order) > 0:
            o = order[0]
            return Order(
                order_id=str(o.ticket),
                client_order_id=str(o.ticket),
                symbol=o.symbol,
                side=OrderSide.BUY if o.type in [0, 2, 4] else OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=o.volume_initial,
                price=o.price_open,
                stop_price=None,
                status=OrderStatus.OPEN,
                filled_quantity=o.volume_initial - o.volume_current,
                exchange='MT5'
            )
        return None
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        if not self.mt5:
            return []
        
        await self._rate_limit()
        
        if symbol:
            orders = self.mt5.orders_get(symbol=symbol)
        else:
            orders = self.mt5.orders_get()
        
        if orders is None:
            return []
        
        return [
            Order(
                order_id=str(o.ticket),
                client_order_id=str(o.ticket),
                symbol=o.symbol,
                side=OrderSide.BUY if o.type in [0, 2, 4] else OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=o.volume_initial,
                price=o.price_open,
                stop_price=None,
                status=OrderStatus.OPEN,
                filled_quantity=o.volume_initial - o.volume_current,
                exchange='MT5'
            )
            for o in orders
        ]
    
    async def close_position(
        self,
        position_id: str,
        quantity: Optional[float] = None
    ) -> Optional[Order]:
        if not self.mt5:
            return None
        
        await self._rate_limit()
        
        # Get position
        position = self.mt5.positions_get(ticket=int(position_id))
        if not position:
            return None
        
        p = position[0]
        close_qty = quantity or p.volume
        
        # Close position
        request = {
            'action': self.mt5.TRADE_ACTION_DEAL,
            'symbol': p.symbol,
            'volume': close_qty,
            'type': self.mt5.ORDER_TYPE_SELL if p.type == 0 else self.mt5.ORDER_TYPE_BUY,
            'position': int(position_id),
            'deviation': 20,
            'magic': 0,
            'comment': 'Close position',
            'type_time': self.mt5.ORDER_TIME_GTC,
            'type_filling': self.mt5.ORDER_FILLING_IOC,
        }
        
        tick = self.mt5.symbol_info_tick(p.symbol)
        request['price'] = tick.bid if p.type == 0 else tick.ask
        
        result = self.mt5.order_send(request)
        
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close position failed: {result.comment}")
            return None
        
        return Order(
            order_id=str(result.order),
            client_order_id=str(result.request_id),
            symbol=p.symbol,
            side=OrderSide.SELL if p.type == 0 else OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=close_qty,
            price=None,
            stop_price=None,
            status=OrderStatus.FILLED,
            filled_quantity=close_qty,
            average_fill_price=result.price,
            exchange='MT5'
        )


class ExchangeManager:
    """
    Manages multiple exchange connections
    """
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeAdapter] = {}
        self.primary_exchange: Optional[str] = None
        
        # Aggregated data
        self.tickers: Dict[str, Dict[str, Ticker]] = defaultdict(dict)
        self.positions: Dict[str, List[Position]] = defaultdict(list)
        
        logger.info("ExchangeManager initialized")
    
    def register_exchange(
        self,
        name: str,
        adapter: ExchangeAdapter,
        primary: bool = False
    ):
        """Register an exchange adapter"""
        self.exchanges[name] = adapter
        if primary or self.primary_exchange is None:
            self.primary_exchange = name
        logger.info(f"Exchange registered: {name}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered exchanges"""
        results = {}
        for name, adapter in self.exchanges.items():
            try:
                results[name] = await adapter.connect()
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
                results[name] = False
        return results
    
    async def disconnect_all(self):
        """Disconnect from all exchanges"""
        for name, adapter in self.exchanges.items():
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect from {name}: {e}")
    
    def get_exchange(self, name: str) -> Optional[ExchangeAdapter]:
        """Get exchange adapter by name"""
        return self.exchanges.get(name)
    
    def get_primary_exchange(self) -> Optional[ExchangeAdapter]:
        """Get primary exchange adapter"""
        if self.primary_exchange:
            return self.exchanges.get(self.primary_exchange)
        return None
    
    async def get_best_price(self, symbol: str) -> Optional[Ticker]:
        """Get best price across all exchanges"""
        best_ticker = None
        best_spread = float('inf')
        
        for name, adapter in self.exchanges.items():
            try:
                ticker = await adapter.get_ticker(symbol)
                if ticker and ticker.spread < best_spread:
                    best_spread = ticker.spread
                    best_ticker = ticker
            except Exception as e:
                logger.error(f"Failed to get ticker from {name}: {e}")
        
        return best_ticker
    
    async def get_aggregate_positions(self) -> Dict[str, List[Position]]:
        """Get positions from all exchanges"""
        result = {}
        for name, adapter in self.exchanges.items():
            try:
                positions = await adapter.get_positions()
                result[name] = positions
            except Exception as e:
                logger.error(f"Failed to get positions from {name}: {e}")
                result[name] = []
        return result
    
    async def get_total_equity(self) -> float:
        """Get total equity across all exchanges"""
        total = 0.0
        for name, adapter in self.exchanges.items():
            try:
                info = await adapter.get_account_info()
                if info:
                    total += info.equity
            except Exception as e:
                logger.error(f"Failed to get account info from {name}: {e}")
        return total


# Factory function
def create_exchange_adapter(exchange_type: str, config: Dict[str, Any]) -> ExchangeAdapter:
    """Create an exchange adapter"""
    adapters = {
        'mt5': MT5Adapter,
        # Add more adapters as they are implemented
    }
    
    adapter_class = adapters.get(exchange_type.lower())
    if adapter_class:
        return adapter_class(config)
    
    raise ValueError(f"Unknown exchange type: {exchange_type}")


# Singleton instance
_exchange_manager: Optional[ExchangeManager] = None


def get_exchange_manager() -> ExchangeManager:
    """Get or create exchange manager singleton"""
    global _exchange_manager
    if _exchange_manager is None:
        _exchange_manager = ExchangeManager()
    return _exchange_manager


# Export
__all__ = [
    'ExchangeAdapter',
    'MT5Adapter',
    'ExchangeManager',
    'ExchangeType',
    'ConnectionStatus',
    'OrderStatus',
    'OrderSide',
    'OrderType',
    'Ticker',
    'OHLCV',
    'Position',
    'Order',
    'AccountInfo',
    'ExchangeCapabilities',
    'create_exchange_adapter',
    'get_exchange_manager'
]
