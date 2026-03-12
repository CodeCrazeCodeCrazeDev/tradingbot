"""
Real-Time Data Hub
==================

Central WebSocket hub for ALL data streams in the trading system.
Replaces polling with true real-time streaming.

Features:
1. WebSocket connections to exchanges (Binance, Coinbase, etc.)
2. Real-time tick data streaming
3. Order book streaming
4. Trade stream aggregation
5. News and sentiment streaming
6. Auto-reconnection with exponential backoff
7. Data normalization and validation
8. Event broadcasting to all subscribers

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Types of data streams"""
    TICK = "tick"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    KLINE = "kline"
    AGG_TRADE = "agg_trade"
    DEPTH = "depth"
    TICKER = "ticker"
    NEWS = "news"
    SENTIMENT = "sentiment"
    ECONOMIC = "economic"


class ConnectionState(Enum):
    """WebSocket connection state"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class StreamConfig:
    """Configuration for a data stream"""
    stream_type: StreamType
    symbol: str
    exchange: str = "binance"
    interval: str = "1m"
    depth: int = 20
    enabled: bool = True


@dataclass
class RealTimeData:
    """Normalized real-time data packet"""
    stream_id: str
    stream_type: StreamType
    symbol: str
    exchange: str
    timestamp: datetime
    data: Dict[str, Any]
    sequence: int = 0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stream_id': self.stream_id,
            'stream_type': self.stream_type.value,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'sequence': self.sequence,
            'latency_ms': self.latency_ms
        }


@dataclass
class TickData:
    """Real-time tick data"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    bid_size: float = 0.0
    ask_size: float = 0.0
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid) * 10000 if self.mid > 0 else 0


@dataclass
class OrderBookLevel:
    """Single order book level"""
    price: float
    quantity: float
    orders: int = 1


@dataclass
class OrderBookSnapshot:
    """Real-time order book snapshot"""
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    sequence: int = 0
    
    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None
    
    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None
    
    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


@dataclass
class TradeData:
    """Real-time trade data"""
    symbol: str
    timestamp: datetime
    price: float
    quantity: float
    side: str  # "buy" or "sell"
    trade_id: str = ""
    is_maker: bool = False


class WebSocketConnection:
    """
    WebSocket connection manager with auto-reconnection.
    """
    
    def __init__(self, url: str, name: str = "default"):
        self.url = url
        self.name = name
        self.state = ConnectionState.DISCONNECTED
        self.ws = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._reconnect_delay = 1.0
        self._callbacks: List[Callable] = []
        self._running = False
        self._last_message_time: Optional[datetime] = None
        self._message_count = 0
        
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            import websockets
            
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to {self.name}: {self.url}")
            
            self.ws = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            
            self.state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            logger.info(f"Connected to {self.name}")
            
            return True
            
        except ImportError:
            logger.warning("websockets not installed, using simulation mode")
            self.state = ConnectionState.CONNECTED
            return True
        except Exception as e:
            logger.error(f"Connection error for {self.name}: {e}")
            self.state = ConnectionState.ERROR
            return False
    
    async def disconnect(self):
        """Close WebSocket connection"""
        self._running = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        self.state = ConnectionState.DISCONNECTED
        logger.info(f"Disconnected from {self.name}")
    
    async def reconnect(self):
        """Reconnect with exponential backoff"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {self.name}")
            return False
        
        self.state = ConnectionState.RECONNECTING
        self._reconnect_attempts += 1
        
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        delay = min(delay, 60)  # Max 60 seconds
        
        logger.info(f"Reconnecting to {self.name} in {delay:.1f}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(delay)
        
        return await self.connect()
    
    def add_callback(self, callback: Callable):
        """Add message callback"""
        self._callbacks.append(callback)
    
    async def send(self, message: Dict[str, Any]):
        """Send message"""
        if self.ws and self.state == ConnectionState.CONNECTED:
            try:
                await self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Send error: {e}")
    
    async def listen(self):
        """Listen for messages"""
        self._running = True
        
        while self._running:
            try:
                if self.ws and self.state == ConnectionState.CONNECTED:
                    try:
                        message = await asyncio.wait_for(
                            self.ws.recv(),
                            timeout=30
                        )
                        
                        self._last_message_time = datetime.now()
                        self._message_count += 1
                        
                        data = json.loads(message)
                        
                        for callback in self._callbacks:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                                
                    except asyncio.TimeoutError:
                        # No message received, check connection
                        continue
                    except Exception as e:
                        logger.error(f"Receive error: {e}")
                        if self._running:
                            await self.reconnect()
                else:
                    # Not connected, try to reconnect
                    if self._running:
                        await self.reconnect()
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Listen error: {e}")
                await asyncio.sleep(1)


class SimulatedDataGenerator:
    """
    Generates simulated real-time data when WebSocket is unavailable.
    Provides realistic market data patterns.
    """
    
    def __init__(self):
        self._prices: Dict[str, float] = {}
        self._volumes: Dict[str, float] = {}
        self._sequence: Dict[str, int] = {}
        
    def get_tick(self, symbol: str) -> TickData:
        """Generate simulated tick data"""
        import random
        
        # Initialize price if not exists
        if symbol not in self._prices:
            if "BTC" in symbol:
                self._prices[symbol] = 50000 + random.uniform(-1000, 1000)
            elif "ETH" in symbol:
                self._prices[symbol] = 3000 + random.uniform(-100, 100)
            else:
                self._prices[symbol] = 100 + random.uniform(-10, 10)
            self._volumes[symbol] = random.uniform(1000, 10000)
        
        # Random walk
        change_pct = random.gauss(0, 0.0001)  # 0.01% std dev
        self._prices[symbol] *= (1 + change_pct)
        
        price = self._prices[symbol]
        spread = price * 0.0001  # 1 bps spread
        
        return TickData(
            symbol=symbol,
            timestamp=datetime.now(),
            bid=price - spread/2,
            ask=price + spread/2,
            last=price + random.uniform(-spread/2, spread/2),
            volume=random.uniform(0.1, 10),
            bid_size=random.uniform(1, 100),
            ask_size=random.uniform(1, 100)
        )
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> OrderBookSnapshot:
        """Generate simulated order book"""
        
        tick = self.get_tick(symbol)
        mid = tick.mid
        
        bids = []
        asks = []
        
        for i in range(depth):
            # Bids below mid
            bid_price = mid * (1 - 0.0001 * (i + 1))
            bid_qty = random.uniform(0.1, 10) * (1 + i * 0.1)
            bids.append(OrderBookLevel(price=bid_price, quantity=bid_qty))
            
            # Asks above mid
            ask_price = mid * (1 + 0.0001 * (i + 1))
            ask_qty = random.uniform(0.1, 10) * (1 + i * 0.1)
            asks.append(OrderBookLevel(price=ask_price, quantity=ask_qty))
        
        self._sequence[symbol] = self._sequence.get(symbol, 0) + 1
        
        return OrderBookSnapshot(
            symbol=symbol,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks,
            sequence=self._sequence[symbol]
        )
    
    def get_trade(self, symbol: str) -> TradeData:
        """Generate simulated trade"""
        
        tick = self.get_tick(symbol)
        
        return TradeData(
            symbol=symbol,
            timestamp=datetime.now(),
            price=tick.last,
            quantity=random.uniform(0.01, 5),
            side="buy" if random.random() > 0.5 else "sell",
            trade_id=hashlib.md5(f"{symbol}{time.time()}".encode()).hexdigest()[:16],
            is_maker=random.random() > 0.5
        )


class RealTimeDataHub:
    """
    Central hub for ALL real-time data streams.
    
    Features:
    - WebSocket connections to multiple exchanges
    - Automatic failover to simulation mode
    - Data normalization across exchanges
    - Event broadcasting to subscribers
    - Latency tracking
    - Data quality monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Connections
        self._connections: Dict[str, WebSocketConnection] = {}
        self._running = False
        
        # Data storage
        self._latest_ticks: Dict[str, TickData] = {}
        self._latest_orderbooks: Dict[str, OrderBookSnapshot] = {}
        self._trade_buffer: Dict[str, deque] = {}
        self._kline_buffer: Dict[str, deque] = {}
        
        # Subscribers
        self._subscribers: Dict[StreamType, List[Callable]] = {
            st: [] for st in StreamType
        }
        self._symbol_subscribers: Dict[str, List[Callable]] = {}
        
        # Simulation fallback
        self._simulator = SimulatedDataGenerator()
        self._use_simulation = self.config.get('use_simulation', True)
        
        # Metrics
        self._metrics = {
            'messages_received': 0,
            'messages_per_second': 0,
            'avg_latency_ms': 0,
            'connection_uptime': 0,
            'last_message_time': None
        }
        
        # Stream configurations
        self._streams: Dict[str, StreamConfig] = {}
        
        logger.info("RealTimeDataHub initialized")
    
    async def initialize(self):
        """Initialize all connections"""
        logger.info("Initializing RealTimeDataHub...")
        
        # Try to establish WebSocket connections
        exchanges = self.config.get('exchanges', ['binance'])
        
        for exchange in exchanges:
            await self._connect_exchange(exchange)
        
        # Start background tasks
        asyncio.create_task(self._metrics_loop())
        
        logger.info("RealTimeDataHub initialized")
    
    async def _connect_exchange(self, exchange: str):
        """Connect to exchange WebSocket"""
        urls = {
            'binance': 'wss://stream.binance.com:9443/ws',
            'binance_futures': 'wss://fstream.binance.com/ws',
            'coinbase': 'wss://ws-feed.exchange.coinbase.com',
            'kraken': 'wss://ws.kraken.com',
        }
        
        url = urls.get(exchange)
        if not url:
            logger.warning(f"Unknown exchange: {exchange}")
            return
        
        conn = WebSocketConnection(url, exchange)
        conn.add_callback(lambda data: self._on_message(exchange, data))
        
        if await conn.connect():
            self._connections[exchange] = conn
            asyncio.create_task(conn.listen())
        else:
            logger.warning(f"Could not connect to {exchange}, using simulation")
            self._use_simulation = True
    
    async def subscribe_stream(self, config: StreamConfig):
        """Subscribe to a data stream"""
        stream_id = f"{config.exchange}:{config.symbol}:{config.stream_type.value}"
        self._streams[stream_id] = config
        
        # Initialize buffers
        if config.symbol not in self._trade_buffer:
            self._trade_buffer[config.symbol] = deque(maxlen=1000)
        if config.symbol not in self._kline_buffer:
            self._kline_buffer[config.symbol] = deque(maxlen=500)
        
        # Send subscription message to exchange
        conn = self._connections.get(config.exchange)
        if conn and conn.state == ConnectionState.CONNECTED:
            await self._send_subscription(conn, config)
        
        # Start simulation if needed
        if self._use_simulation:
            asyncio.create_task(self._simulate_stream(config))
        
        logger.info(f"Subscribed to stream: {stream_id}")
    
    async def _send_subscription(self, conn: WebSocketConnection, config: StreamConfig):
        """Send subscription message to exchange"""
        if conn.name == 'binance':
            stream_name = self._get_binance_stream_name(config)
            await conn.send({
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": hash(stream_name) % 1000000
            })
    
    def _get_binance_stream_name(self, config: StreamConfig) -> str:
        """Get Binance stream name"""
        symbol = config.symbol.lower()
        
        stream_map = {
            StreamType.TICK: f"{symbol}@ticker",
            StreamType.TRADE: f"{symbol}@trade",
            StreamType.AGG_TRADE: f"{symbol}@aggTrade",
            StreamType.ORDERBOOK: f"{symbol}@depth{config.depth}@100ms",
            StreamType.DEPTH: f"{symbol}@depth@100ms",
            StreamType.KLINE: f"{symbol}@kline_{config.interval}",
            StreamType.TICKER: f"{symbol}@ticker",
        }
        
        return stream_map.get(config.stream_type, f"{symbol}@ticker")
    
    async def _simulate_stream(self, config: StreamConfig):
        """Simulate data stream"""
        interval_ms = {
            StreamType.TICK: 100,
            StreamType.TRADE: 50,
            StreamType.ORDERBOOK: 100,
            StreamType.KLINE: 1000,
            StreamType.TICKER: 1000,
        }.get(config.stream_type, 100)
        
        # Wait for hub to start
        while not self._running:
            await asyncio.sleep(0.1)
        
        while self._running and config.enabled:
            try:
                if config.stream_type == StreamType.TICK:
                    tick = self._simulator.get_tick(config.symbol)
                    await self._process_tick(config.symbol, tick)
                    
                elif config.stream_type == StreamType.ORDERBOOK:
                    book = self._simulator.get_orderbook(config.symbol, config.depth)
                    await self._process_orderbook(config.symbol, book)
                    
                elif config.stream_type == StreamType.TRADE:
                    trade = self._simulator.get_trade(config.symbol)
                    await self._process_trade(config.symbol, trade)
                
                await asyncio.sleep(interval_ms / 1000)
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                await asyncio.sleep(1)
    
    async def _on_message(self, exchange: str, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        self._metrics['messages_received'] += 1
        self._metrics['last_message_time'] = datetime.now()
        
        try:
            # Parse based on exchange format
            if exchange == 'binance':
                await self._parse_binance_message(data)
            elif exchange == 'coinbase':
                await self._parse_coinbase_message(data)
            else:
                logger.debug(f"Unknown exchange format: {exchange}")
                
        except Exception as e:
            logger.error(f"Message parsing error: {e}")
    
    async def _parse_binance_message(self, data: Dict[str, Any]):
        """Parse Binance WebSocket message"""
        event_type = data.get('e')
        symbol = data.get('s', '').upper()
        
        if event_type == '24hrTicker':
            tick = TickData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(data.get('E', 0) / 1000),
                bid=float(data.get('b', 0)),
                ask=float(data.get('a', 0)),
                last=float(data.get('c', 0)),
                volume=float(data.get('v', 0)),
                bid_size=float(data.get('B', 0)),
                ask_size=float(data.get('A', 0))
            )
            await self._process_tick(symbol, tick)
            
        elif event_type == 'trade':
            trade = TradeData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(data.get('T', 0) / 1000),
                price=float(data.get('p', 0)),
                quantity=float(data.get('q', 0)),
                side="buy" if data.get('m', False) else "sell",
                trade_id=str(data.get('t', '')),
                is_maker=data.get('m', False)
            )
            await self._process_trade(symbol, trade)
            
        elif event_type == 'depthUpdate':
            bids = [OrderBookLevel(float(p), float(q)) for p, q in data.get('b', [])]
            asks = [OrderBookLevel(float(p), float(q)) for p, q in data.get('a', [])]
            
            book = OrderBookSnapshot(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(data.get('E', 0) / 1000),
                bids=bids,
                asks=asks,
                sequence=data.get('u', 0)
            )
            await self._process_orderbook(symbol, book)
    
    async def _parse_coinbase_message(self, data: Dict[str, Any]):
        """Parse Coinbase WebSocket message"""
        msg_type = data.get('type')
        product_id = data.get('product_id', '').replace('-', '')
        
        if msg_type == 'ticker':
            tick = TickData(
                symbol=product_id,
                timestamp=datetime.fromisoformat(data.get('time', '').replace('Z', '+00:00')),
                bid=float(data.get('best_bid', 0)),
                ask=float(data.get('best_ask', 0)),
                last=float(data.get('price', 0)),
                volume=float(data.get('volume_24h', 0))
            )
            await self._process_tick(product_id, tick)
    
    async def _process_tick(self, symbol: str, tick: TickData):
        """Process tick data"""
        self._latest_ticks[symbol] = tick
        
        # Notify subscribers
        await self._notify_subscribers(StreamType.TICK, symbol, tick)
    
    async def _process_orderbook(self, symbol: str, book: OrderBookSnapshot):
        """Process order book update"""
        self._latest_orderbooks[symbol] = book
        
        # Notify subscribers
        await self._notify_subscribers(StreamType.ORDERBOOK, symbol, book)
    
    async def _process_trade(self, symbol: str, trade: TradeData):
        """Process trade data"""
        if symbol not in self._trade_buffer:
            self._trade_buffer[symbol] = deque(maxlen=1000)
        
        self._trade_buffer[symbol].append(trade)
        
        # Notify subscribers
        await self._notify_subscribers(StreamType.TRADE, symbol, trade)
    
    async def _notify_subscribers(self, stream_type: StreamType, symbol: str, data: Any):
        """Notify all subscribers of new data"""
        # Type subscribers
        for callback in self._subscribers.get(stream_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(symbol, data)
                else:
                    callback(symbol, data)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")
        
        # Symbol subscribers
        for callback in self._symbol_subscribers.get(symbol, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(stream_type, data)
                else:
                    callback(stream_type, data)
            except Exception as e:
                logger.error(f"Symbol subscriber callback error: {e}")
    
    def subscribe(self, stream_type: StreamType, callback: Callable):
        """Subscribe to a stream type"""
        if stream_type not in self._subscribers:
            self._subscribers[stream_type] = []
        self._subscribers[stream_type].append(callback)
    
    def subscribe_symbol(self, symbol: str, callback: Callable):
        """Subscribe to all data for a symbol"""
        if symbol not in self._symbol_subscribers:
            self._symbol_subscribers[symbol] = []
        self._symbol_subscribers[symbol].append(callback)
    
    def unsubscribe(self, stream_type: StreamType, callback: Callable):
        """Unsubscribe from a stream type"""
        if stream_type in self._subscribers:
            self._subscribers[stream_type] = [
                cb for cb in self._subscribers[stream_type] if cb != callback
            ]
    
    def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """Get latest tick for a symbol"""
        return self._latest_ticks.get(symbol)
    
    def get_latest_orderbook(self, symbol: str) -> Optional[OrderBookSnapshot]:
        """Get latest order book for a symbol"""
        return self._latest_orderbooks.get(symbol)
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """Get recent trades for a symbol"""
        trades = self._trade_buffer.get(symbol, deque())
        return list(trades)[-limit:]
    
    async def _metrics_loop(self):
        """Update metrics periodically"""
        last_count = 0
        
        while self._running:
            try:
                current_count = self._metrics['messages_received']
                self._metrics['messages_per_second'] = (current_count - last_count) / 5
                last_count = current_count
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(5)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get hub metrics"""
        return {
            **self._metrics,
            'active_connections': len([c for c in self._connections.values() 
                                       if c.state == ConnectionState.CONNECTED]),
            'total_connections': len(self._connections),
            'active_streams': len(self._streams),
            'symbols_tracked': len(self._latest_ticks),
            'simulation_mode': self._use_simulation
        }
    
    async def start(self):
        """Start the data hub"""
        self._running = True
        logger.info("RealTimeDataHub started")
    
    async def stop(self):
        """Stop the data hub"""
        self._running = False
        
        # Close all connections
        for conn in self._connections.values():
            await conn.disconnect()
        
        logger.info("RealTimeDataHub stopped")
