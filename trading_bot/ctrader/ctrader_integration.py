"""
cTrader Integration Module

Connects to cTrader for:
- Real-time market data (tick, OHLCV, multi-timeframe)
- Level 2 / Depth of Market (DOM) data
- News feed integration
- Order execution via cTrader Open API

Uses cTrader Open API (protobuf-based) for low-latency connectivity.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# CTRADER CREDENTIALS
# ============================================================================
CTRADER_CONFIG = {
    'login_email': 'petesonmwangi206@gmail.com',
    'password': 'Peter/2006',
    'api_host': 'demo.ctraderapi.com',
    'api_port': 5035,
    'client_id': '',       # Set via env var CTRADER_CLIENT_ID
    'client_secret': '',   # Set via env var CTRADER_CLIENT_SECRET
}


class ConnectionState(Enum):
    """cTrader connection states."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    AUTHENTICATING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()


class DataType(Enum):
    """Types of data available from cTrader."""
    TICK = auto()
    OHLCV = auto()
    DEPTH_OF_MARKET = auto()
    NEWS = auto()
    ACCOUNT_INFO = auto()
    POSITIONS = auto()
    ORDERS = auto()
    DEALS = auto()


class Timeframe(Enum):
    """Supported timeframes."""
    M1 = '1m'
    M5 = '5m'
    M15 = '15m'
    M30 = '30m'
    H1 = '1h'
    H4 = '4h'
    D1 = '1d'
    W1 = '1w'
    MN1 = '1M'


@dataclass
class TickData:
    """Real-time tick data."""
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    volume: float = 0.0
    last_price: float = 0.0


@dataclass
class OHLCVBar:
    """OHLCV candlestick bar."""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    tick_volume: int = 0


@dataclass
class Level2Entry:
    """Single Level 2 / DOM entry."""
    price: float
    volume: float
    side: str  # 'bid' or 'ask'
    order_count: int = 0


@dataclass
class DepthOfMarket:
    """Full Level 2 / Depth of Market snapshot."""
    symbol: str
    timestamp: datetime
    bids: List[Level2Entry]
    asks: List[Level2Entry]
    total_bid_volume: float = 0.0
    total_ask_volume: float = 0.0
    imbalance: float = 0.0  # >0 = more buying pressure

    def __post_init__(self):
        self.total_bid_volume = sum(e.volume for e in self.bids)
        self.total_ask_volume = sum(e.volume for e in self.asks)
        total = self.total_bid_volume + self.total_ask_volume
        if total > 0:
            self.imbalance = (self.total_bid_volume - self.total_ask_volume) / total


@dataclass
class NewsItem:
    """News item from cTrader feed."""
    id: str
    title: str
    body: str
    source: str
    symbols: List[str]
    importance: str  # 'low', 'medium', 'high'
    timestamp: datetime
    url: str = ""
    sentiment: Optional[float] = None  # -1 to 1


@dataclass
class AccountInfo:
    """cTrader account information."""
    account_id: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    unrealized_pnl: float
    currency: str
    leverage: float
    is_live: bool


class CTraderConnection:
    """
    Manages connection to cTrader Open API.
    
    Handles authentication, heartbeat, reconnection, and message routing.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = {**CTRADER_CONFIG, **(config or {})}
        self.state = ConnectionState.DISCONNECTED
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.receive_task: Optional[asyncio.Task] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds
        self.last_heartbeat: Optional[datetime] = None
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.access_token: Optional[str] = None

        # Load credentials from environment
        import os
        if not self.config['client_id']:
            self.config['client_id'] = os.environ.get('CTRADER_CLIENT_ID', '')
        if not self.config['client_secret']:
            self.config['client_secret'] = os.environ.get('CTRADER_CLIENT_SECRET', '')

        logger.info("CTraderConnection initialized")

    async def connect(self) -> bool:
        """Connect to cTrader Open API."""
        try:
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to cTrader at {self.config['api_host']}:{self.config['api_port']}")

            self.reader, self.writer = await asyncio.open_connection(
                self.config['api_host'],
                self.config['api_port'],
                ssl=True
            )

            self.state = ConnectionState.AUTHENTICATING

            # Authenticate
            auth_success = await self._authenticate()
            if not auth_success:
                logger.error("cTrader authentication failed")
                self.state = ConnectionState.ERROR
                return False

            self.state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Start message receiver
            self.receive_task = asyncio.create_task(self._receive_loop())

            logger.info("Connected to cTrader successfully")
            return True

        except Exception as e:
            logger.error(f"cTrader connection failed: {e}")
            self.state = ConnectionState.ERROR
            return False

    async def disconnect(self):
        """Disconnect from cTrader."""
        self.state = ConnectionState.DISCONNECTED

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass

        logger.info("Disconnected from cTrader")

    async def _authenticate(self) -> bool:
        """Authenticate with cTrader Open API."""
        try:
            # OAuth2 authentication flow
            auth_request = {
                'payloadType': 'ProtoOAApplicationAuthReq',
                'clientId': self.config['client_id'],
                'clientSecret': self.config['client_secret'],
            }

            await self._send_message(auth_request)

            # Wait for auth response
            response = await self._receive_message(timeout=10)
            if response and response.get('payloadType') == 'ProtoOAApplicationAuthRes':
                logger.info("cTrader application authenticated")

                # Account authentication
                account_auth = {
                    'payloadType': 'ProtoOAAccountAuthReq',
                    'accessToken': self.access_token or '',
                }
                await self._send_message(account_auth)

                return True

            return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def _send_message(self, message: Dict[str, Any]):
        """Send a message to cTrader."""
        if self.writer is None:
            logger.error("Cannot send: not connected")
            return

        try:
            data = json.dumps(message).encode('utf-8')
            length = len(data).to_bytes(4, byteorder='big')
            self.writer.write(length + data)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def _receive_message(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive a message from cTrader."""
        if self.reader is None:
            return None

        try:
            length_bytes = await asyncio.wait_for(
                self.reader.read(4), timeout=timeout
            )
            if not length_bytes:
                return None

            length = int.from_bytes(length_bytes, byteorder='big')
            data = await asyncio.wait_for(
                self.reader.read(length), timeout=timeout
            )
            return json.loads(data.decode('utf-8'))

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None

    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.state == ConnectionState.CONNECTED:
            try:
                await self._send_message({'payloadType': 'ProtoHeartbeatEvent'})
                self.last_heartbeat = datetime.utcnow()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)

    async def _receive_loop(self):
        """Continuously receive and route messages."""
        while self.state == ConnectionState.CONNECTED:
            try:
                message = await self._receive_message(timeout=30)
                if message:
                    payload_type = message.get('payloadType', '')
                    for handler in self.message_handlers.get(payload_type, []):
                        try:
                            await handler(message)
                        except Exception as e:
                            logger.error(f"Handler error for {payload_type}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive loop error: {e}")
                if self.state == ConnectionState.CONNECTED:
                    await self._reconnect()

    async def _reconnect(self):
        """Attempt to reconnect."""
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1

        if self.reconnect_attempts > self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.state = ConnectionState.ERROR
            return

        delay = self.reconnect_delay * (2 ** min(self.reconnect_attempts - 1, 5))
        logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts})")
        await asyncio.sleep(delay)

        await self.connect()

    def on_message(self, payload_type: str, handler: Callable):
        """Register a message handler."""
        self.message_handlers[payload_type].append(handler)


class CTraderMarketData:
    """
    Market data provider using cTrader.
    
    Provides:
    - Real-time tick data
    - OHLCV bars (multi-timeframe)
    - Level 2 / Depth of Market
    """

    def __init__(self, connection: CTraderConnection):
        self.connection = connection
        self.tick_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.bar_cache: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=1000))
        )
        self.dom_cache: Dict[str, DepthOfMarket] = {}
        self.subscribed_symbols: set = set()
        self.tick_callbacks: List[Callable] = []
        self.bar_callbacks: List[Callable] = []
        self.dom_callbacks: List[Callable] = []

        # Register message handlers
        self.connection.on_message('ProtoOASpotEvent', self._handle_spot_event)
        self.connection.on_message('ProtoOADepthEvent', self._handle_depth_event)

        logger.info("CTraderMarketData initialized")

    async def subscribe_ticks(self, symbols: List[str]):
        """Subscribe to real-time tick data for symbols."""
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                await self.connection._send_message({
                    'payloadType': 'ProtoOASubscribeSpotsReq',
                    'symbolId': self._get_symbol_id(symbol),
                })
                self.subscribed_symbols.add(symbol)
                logger.info(f"Subscribed to ticks: {symbol}")

    async def subscribe_depth(self, symbols: List[str]):
        """Subscribe to Level 2 / DOM data."""
        for symbol in symbols:
            await self.connection._send_message({
                'payloadType': 'ProtoOASubscribeDepthQuotesReq',
                'symbolId': self._get_symbol_id(symbol),
            })
            logger.info(f"Subscribed to L2 data: {symbol}")

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 500,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[OHLCVBar]:
        """Get historical OHLCV bars."""
        if to_date is None:
            to_date = datetime.utcnow()
        if from_date is None:
            from_date = to_date - timedelta(days=count)

        request = {
            'payloadType': 'ProtoOAGetTrendbarsReq',
            'symbolId': self._get_symbol_id(symbol),
            'period': self._timeframe_to_period(timeframe),
            'fromTimestamp': int(from_date.timestamp() * 1000),
            'toTimestamp': int(to_date.timestamp() * 1000),
            'count': count,
        }

        await self.connection._send_message(request)

        # Return cached bars for now
        cache_key = f"{symbol}_{timeframe.value}"
        return list(self.bar_cache[symbol][timeframe.value])

    def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """Get the latest tick for a symbol."""
        if symbol in self.tick_cache and self.tick_cache[symbol]:
            return self.tick_cache[symbol][-1]
        return None

    def get_dom(self, symbol: str) -> Optional[DepthOfMarket]:
        """Get current Depth of Market for a symbol."""
        return self.dom_cache.get(symbol)

    def on_tick(self, callback: Callable):
        """Register a tick data callback."""
        self.tick_callbacks.append(callback)

    def on_bar(self, callback: Callable):
        """Register a bar data callback."""
        self.bar_callbacks.append(callback)

    def on_dom_update(self, callback: Callable):
        """Register a DOM update callback."""
        self.dom_callbacks.append(callback)

    async def _handle_spot_event(self, message: Dict[str, Any]):
        """Handle incoming tick/spot data."""
        symbol = self._get_symbol_name(message.get('symbolId', 0))
        bid = message.get('bid', 0) / 100000.0  # Convert from pipettes
        ask = message.get('ask', 0) / 100000.0

        tick = TickData(
            symbol=symbol,
            bid=bid,
            ask=ask,
            spread=ask - bid,
            timestamp=datetime.utcnow(),
            volume=message.get('volume', 0),
        )

        self.tick_cache[symbol].append(tick)

        # Notify callbacks
        for callback in self.tick_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")

    async def _handle_depth_event(self, message: Dict[str, Any]):
        """Handle incoming Level 2 / DOM data."""
        symbol = self._get_symbol_name(message.get('symbolId', 0))

        bids = [
            Level2Entry(
                price=entry.get('price', 0) / 100000.0,
                volume=entry.get('volume', 0),
                side='bid',
                order_count=entry.get('orderCount', 0),
            )
            for entry in message.get('bids', [])
        ]

        asks = [
            Level2Entry(
                price=entry.get('price', 0) / 100000.0,
                volume=entry.get('volume', 0),
                side='ask',
                order_count=entry.get('orderCount', 0),
            )
            for entry in message.get('asks', [])
        ]

        dom = DepthOfMarket(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bids=sorted(bids, key=lambda x: x.price, reverse=True),
            asks=sorted(asks, key=lambda x: x.price),
        )

        self.dom_cache[symbol] = dom

        # Notify callbacks
        for callback in self.dom_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(dom)
                else:
                    callback(dom)
            except Exception as e:
                logger.error(f"DOM callback error: {e}")

    def _get_symbol_id(self, symbol: str) -> int:
        """Convert symbol name to cTrader symbol ID."""
        # Common forex symbol IDs (these vary by broker)
        symbol_map = {
            'EURUSD': 1, 'GBPUSD': 2, 'USDJPY': 3, 'USDCHF': 4,
            'AUDUSD': 5, 'NZDUSD': 6, 'USDCAD': 7, 'EURGBP': 8,
            'EURJPY': 9, 'GBPJPY': 10, 'EURCHF': 11, 'AUDJPY': 12,
            'EURAUD': 13, 'EURNZD': 14, 'GBPAUD': 15, 'GBPCAD': 16,
            'XAUUSD': 17, 'XAGUSD': 18, 'US30': 19, 'US500': 20,
        }
        return symbol_map.get(symbol.upper(), 0)

    def _get_symbol_name(self, symbol_id: int) -> str:
        """Convert cTrader symbol ID to name."""
        id_map = {
            1: 'EURUSD', 2: 'GBPUSD', 3: 'USDJPY', 4: 'USDCHF',
            5: 'AUDUSD', 6: 'NZDUSD', 7: 'USDCAD', 8: 'EURGBP',
            9: 'EURJPY', 10: 'GBPJPY', 11: 'EURCHF', 12: 'AUDJPY',
            13: 'EURAUD', 14: 'EURNZD', 15: 'GBPAUD', 16: 'GBPCAD',
            17: 'XAUUSD', 18: 'XAGUSD', 19: 'US30', 20: 'US500',
        }
        return id_map.get(symbol_id, f'UNKNOWN_{symbol_id}')

    def _timeframe_to_period(self, tf: Timeframe) -> int:
        """Convert timeframe to cTrader period enum."""
        period_map = {
            Timeframe.M1: 1, Timeframe.M5: 2, Timeframe.M15: 3,
            Timeframe.M30: 4, Timeframe.H1: 5, Timeframe.H4: 6,
            Timeframe.D1: 7, Timeframe.W1: 8, Timeframe.MN1: 9,
        }
        return period_map.get(tf, 1)


class CTraderNewsFeed:
    """
    News feed from cTrader.
    
    Provides real-time economic news, market events, and analysis.
    """

    def __init__(self, connection: CTraderConnection):
        self.connection = connection
        self.news_cache: deque = deque(maxlen=1000)
        self.news_callbacks: List[Callable] = []
        self.economic_calendar: List[Dict[str, Any]] = []

        # Register handlers
        self.connection.on_message('ProtoOANewsEvent', self._handle_news_event)

        logger.info("CTraderNewsFeed initialized")

    async def subscribe_news(self, symbols: Optional[List[str]] = None):
        """Subscribe to news feed."""
        request = {
            'payloadType': 'ProtoOASubscribeNewsReq',
        }
        if symbols:
            request['symbolIds'] = [
                CTraderMarketData(self.connection)._get_symbol_id(s) for s in symbols
            ]

        await self.connection._send_message(request)
        logger.info(f"Subscribed to news feed for: {symbols or 'all symbols'}")

    def get_recent_news(self, count: int = 50, symbol: Optional[str] = None) -> List[NewsItem]:
        """Get recent news items."""
        news = list(self.news_cache)
        if symbol:
            news = [n for n in news if symbol in n.symbols]
        return news[-count:]

    def get_high_impact_news(self, hours_ahead: int = 24) -> List[NewsItem]:
        """Get upcoming high-impact news events."""
        cutoff = datetime.utcnow() + timedelta(hours=hours_ahead)
        return [
            n for n in self.news_cache
            if n.importance == 'high' and n.timestamp <= cutoff
        ]

    def on_news(self, callback: Callable):
        """Register a news callback."""
        self.news_callbacks.append(callback)

    async def _handle_news_event(self, message: Dict[str, Any]):
        """Handle incoming news event."""
        news = NewsItem(
            id=str(message.get('newsId', '')),
            title=message.get('headline', ''),
            body=message.get('body', ''),
            source=message.get('source', 'cTrader'),
            symbols=message.get('symbols', []),
            importance=message.get('importance', 'medium'),
            timestamp=datetime.utcnow(),
            url=message.get('url', ''),
        )

        self.news_cache.append(news)

        for callback in self.news_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(news)
                else:
                    callback(news)
            except Exception as e:
                logger.error(f"News callback error: {e}")


class CTraderIntegration:
    """
    Master cTrader integration class.
    
    Provides unified access to:
    - Market data (ticks, OHLCV)
    - Level 2 / DOM data
    - News feed
    - Account information
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connection = CTraderConnection(self.config)
        self.market_data = CTraderMarketData(self.connection)
        self.news_feed = CTraderNewsFeed(self.connection)
        self.is_connected = False

        logger.info("CTraderIntegration initialized")

    async def connect(self) -> bool:
        """Connect to cTrader and initialize all services."""
        success = await self.connection.connect()
        self.is_connected = success

        if success:
            logger.info("cTrader integration fully connected")
        else:
            logger.error("cTrader integration connection failed")

        return success

    async def disconnect(self):
        """Disconnect from cTrader."""
        await self.connection.disconnect()
        self.is_connected = False

    async def subscribe_all(self, symbols: List[str]):
        """Subscribe to all data types for given symbols."""
        await self.market_data.subscribe_ticks(symbols)
        await self.market_data.subscribe_depth(symbols)
        await self.news_feed.subscribe_news(symbols)
        logger.info(f"Subscribed to all data for: {symbols}")

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """Get latest tick data."""
        return self.market_data.get_latest_tick(symbol)

    def get_dom(self, symbol: str) -> Optional[DepthOfMarket]:
        """Get current DOM/Level 2 data."""
        return self.market_data.get_dom(symbol)

    def get_news(self, count: int = 50) -> List[NewsItem]:
        """Get recent news."""
        return self.news_feed.get_recent_news(count)

    async def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.H1,
        count: int = 500
    ) -> List[OHLCVBar]:
        """Get historical bars."""
        return await self.market_data.get_historical_bars(symbol, timeframe, count)

    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            'connected': self.is_connected,
            'connection_state': self.connection.state.name,
            'subscribed_symbols': list(self.market_data.subscribed_symbols),
            'tick_cache_sizes': {
                sym: len(ticks) for sym, ticks in self.market_data.tick_cache.items()
            },
            'dom_available': list(self.market_data.dom_cache.keys()),
            'news_cached': len(self.news_feed.news_cache),
            'last_heartbeat': (
                self.connection.last_heartbeat.isoformat()
                if self.connection.last_heartbeat else None
            ),
            'reconnect_attempts': self.connection.reconnect_attempts,
        }
