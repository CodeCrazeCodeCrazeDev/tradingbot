"""
WebSocket Data Feeds
====================

Real-time WebSocket connections to crypto exchanges.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
import threading
from collections import deque

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection state"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class TickData:
    """Real-time tick data"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    exchange: str = ""
    trade_id: Optional[str] = None


@dataclass
class OrderBookUpdate:
    """Order book update"""
    symbol: str
    timestamp: datetime
    bids: List[tuple]  # [(price, size), ...]
    asks: List[tuple]  # [(price, size), ...]
    exchange: str = ""
    is_snapshot: bool = False


class WebSocketFeed(ABC):
    """Base class for WebSocket feeds"""
    
    def __init__(self, symbols: List[str], on_tick: Optional[Callable] = None):
        self.symbols = set(symbols)
        self.on_tick = on_tick
        self.state = ConnectionState.DISCONNECTED
        self._ws = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._message_count = 0
        self._last_message_time: Optional[datetime] = None
        self._callbacks: List[Callable] = []
        
    @abstractmethod
    async def connect(self):
        """Connect to WebSocket"""
        pass
        
    @abstractmethod
    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols"""
        pass
        
    @abstractmethod
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        pass
        
    def add_callback(self, callback: Callable):
        """Add tick callback"""
        self._callbacks.append(callback)
        
    def remove_callback(self, callback: Callable):
        """Remove tick callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            
    async def _notify_callbacks(self, tick: TickData):
        """Notify all callbacks"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Callback error: {e}")
                
    async def start(self):
        """Start the WebSocket feed"""
        self._running = True
        while self._running:
            try:
                await self.connect()
                await self.subscribe(list(self.symbols))
                await self._listen()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.state = ConnectionState.RECONNECTING
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay
                )
                
    async def stop(self):
        """Stop the WebSocket feed"""
        self._running = False
        if self._ws:
            await self._ws.close()
        self.state = ConnectionState.DISCONNECTED
        
    @abstractmethod
    async def _listen(self):
        """Listen for messages"""
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Get feed statistics"""
        return {
            'state': self.state.value,
            'symbols': list(self.symbols),
            'message_count': self._message_count,
            'last_message': self._last_message_time.isoformat() if self._last_message_time else None
        }


class BinanceWebSocketFeed(WebSocketFeed):
    """Binance WebSocket feed"""
    
    WS_URL = "wss://stream.binance.com:9443/ws"
    
    async def connect(self):
        """Connect to Binance WebSocket"""
        try:
            import websockets
            
            self.state = ConnectionState.CONNECTING
            self._ws = await websockets.connect(self.WS_URL)
            self.state = ConnectionState.CONNECTED
            self._reconnect_delay = 1.0
            logger.info("Connected to Binance WebSocket")
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Binance connection failed: {e}")
            raise
            
    async def subscribe(self, symbols: List[str]):
        """Subscribe to Binance streams"""
        if not self._ws:
            return
            
        # Subscribe to trade streams
        streams = [f"{s.lower()}@trade" for s in symbols]
        
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": 1
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
        self.symbols.update(symbols)
        logger.info(f"Subscribed to {len(symbols)} Binance streams")
        
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from Binance streams"""
        if not self._ws:
            return
            
        streams = [f"{s.lower()}@trade" for s in symbols]
        
        unsubscribe_msg = {
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": 2
        }
        
        await self._ws.send(json.dumps(unsubscribe_msg))
        self.symbols -= set(symbols)
        
    async def _listen(self):
        """Listen for Binance messages"""
        async for message in self._ws:
            try:
                data = json.loads(message)
                
                # Skip subscription confirmations
                if 'result' in data:
                    continue
                    
                # Parse trade data
                if 'e' in data and data['e'] == 'trade':
                    tick = TickData(
                        symbol=data['s'],
                        timestamp=datetime.fromtimestamp(data['T'] / 1000),
                        price=float(data['p']),
                        volume=float(data['q']),
                        exchange='binance',
                        trade_id=str(data['t'])
                    )
                    
                    self._message_count += 1
                    self._last_message_time = datetime.now()
                    
                    await self._notify_callbacks(tick)
                    
            except Exception as e:
                logger.error(f"Error processing Binance message: {e}")


class CoinbaseWebSocketFeed(WebSocketFeed):
    """Coinbase WebSocket feed"""
    
    WS_URL = "wss://ws-feed.exchange.coinbase.com"
    
    async def connect(self):
        """Connect to Coinbase WebSocket"""
            
        try:
            self.state = ConnectionState.CONNECTING
            self._ws = await websockets.connect(self.WS_URL)
            self.state = ConnectionState.CONNECTED
            self._reconnect_delay = 1.0
            logger.info("Connected to Coinbase WebSocket")
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Coinbase connection failed: {e}")
            raise
            
    async def subscribe(self, symbols: List[str]):
        """Subscribe to Coinbase channels"""
        if not self._ws:
            return
            
        # Format symbols for Coinbase (e.g., BTC-USD)
        product_ids = []
        for s in symbols:
            if '-' not in s:
                # Convert BTCUSD to BTC-USD
                if s.endswith('USD'):
                    product_ids.append(f"{s[:-3]}-USD")
                elif s.endswith('USDT'):
                    product_ids.append(f"{s[:-4]}-USD")
                else:
                    product_ids.append(s)
            else:
                product_ids.append(s)
                
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": ["ticker", "matches"]
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
        self.symbols.update(symbols)
        logger.info(f"Subscribed to {len(product_ids)} Coinbase products")
        
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from Coinbase channels"""
        if not self._ws:
            return
            
        product_ids = [f"{s[:-3]}-USD" if s.endswith('USD') else s for s in symbols]
        
        unsubscribe_msg = {
            "type": "unsubscribe",
            "product_ids": product_ids,
            "channels": ["ticker", "matches"]
        }
        
        await self._ws.send(json.dumps(unsubscribe_msg))
        self.symbols -= set(symbols)
        
    async def _listen(self):
        """Listen for Coinbase messages"""
        async for message in self._ws:
            try:
                data = json.loads(message)
                
                # Skip subscription confirmations
                if data.get('type') in ['subscriptions', 'error']:
                    continue
                    
                # Parse ticker data
                if data.get('type') == 'ticker':
                    tick = TickData(
                        symbol=data['product_id'].replace('-', ''),
                        timestamp=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
                        price=float(data['price']),
                        volume=float(data.get('volume_24h', 0)),
                        bid=float(data.get('best_bid', 0)),
                        ask=float(data.get('best_ask', 0)),
                        exchange='coinbase'
                    )
                    
                    self._message_count += 1
                    self._last_message_time = datetime.now()
                    
                    await self._notify_callbacks(tick)
                    
                # Parse match (trade) data
                elif data.get('type') == 'match':
                    tick = TickData(
                        symbol=data['product_id'].replace('-', ''),
                        timestamp=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
                        price=float(data['price']),
                        volume=float(data['size']),
                        exchange='coinbase',
                        trade_id=str(data['trade_id'])
                    )
                    
                    self._message_count += 1
                    self._last_message_time = datetime.now()
                    
                    await self._notify_callbacks(tick)
                    
            except Exception as e:
                logger.error(f"Error processing Coinbase message: {e}")


class KrakenWebSocketFeed(WebSocketFeed):
    """Kraken WebSocket feed"""
    
    WS_URL = "wss://ws.kraken.com"
    
    async def connect(self):
        """Connect to Kraken WebSocket"""
            
        try:
            self.state = ConnectionState.CONNECTING
            self._ws = await websockets.connect(self.WS_URL)
            self.state = ConnectionState.CONNECTED
            self._reconnect_delay = 1.0
            logger.info("Connected to Kraken WebSocket")
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Kraken connection failed: {e}")
            raise
            
    async def subscribe(self, symbols: List[str]):
        """Subscribe to Kraken channels"""
        if not self._ws:
            return
            
        # Format symbols for Kraken (e.g., XBT/USD)
        pairs = []
        for s in symbols:
            if s.startswith('BTC'):
                pairs.append(f"XBT/{s[3:]}")
            elif '/' not in s:
                pairs.append(f"{s[:3]}/{s[3:]}")
            else:
                pairs.append(s)
                
        subscribe_msg = {
            "event": "subscribe",
            "pair": pairs,
            "subscription": {"name": "trade"}
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
        self.symbols.update(symbols)
        logger.info(f"Subscribed to {len(pairs)} Kraken pairs")
        
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from Kraken channels"""
        if not self._ws:
            return
            
        pairs = [f"{s[:3]}/{s[3:]}" if '/' not in s else s for s in symbols]
        
        unsubscribe_msg = {
            "event": "unsubscribe",
            "pair": pairs,
            "subscription": {"name": "trade"}
        }
        
        await self._ws.send(json.dumps(unsubscribe_msg))
        self.symbols -= set(symbols)
        
    async def _listen(self):
        """Listen for Kraken messages"""
        async for message in self._ws:
            try:
                data = json.loads(message)
                
                # Skip system messages
                if isinstance(data, dict):
                    continue
                    
                # Parse trade data (array format)
                if isinstance(data, list) and len(data) >= 4:
                    trades = data[1]
                    pair = data[3]
                    
                    for trade in trades:
                        price, volume, time_str, side, order_type, misc = trade
                        
                        tick = TickData(
                            symbol=pair.replace('/', '').replace('XBT', 'BTC'),
                            timestamp=datetime.fromtimestamp(float(time_str)),
                            price=float(price),
                            volume=float(volume),
                            exchange='kraken'
                        )
                        
                        self._message_count += 1
                        self._last_message_time = datetime.now()
                        
                        await self._notify_callbacks(tick)
                        
            except Exception as e:
                logger.error(f"Error processing Kraken message: {e}")


class WebSocketFeedManager:
    """
    Manages multiple WebSocket feeds with unified interface.
    
    Features:
    - Multi-exchange support
    - Automatic reconnection
    - Unified tick callback
    - Health monitoring
    """
    
    def __init__(self):
        self.feeds: Dict[str, WebSocketFeed] = {}
        self._callbacks: List[Callable] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
    def add_feed(self, name: str, feed: WebSocketFeed):
        """Add a WebSocket feed"""
        self.feeds[name] = feed
        feed.add_callback(self._on_tick)
        logger.info(f"Added feed: {name}")
        
    def remove_feed(self, name: str):
        """Remove a WebSocket feed"""
        if name in self.feeds:
            feed = self.feeds.pop(name)
            feed.remove_callback(self._on_tick)
            
    def add_callback(self, callback: Callable):
        """Add unified tick callback"""
        self._callbacks.append(callback)
        
    async def _on_tick(self, tick: TickData):
        """Handle tick from any feed"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
                
    async def start(self):
        """Start all feeds"""
        self._running = True
        
        for name, feed in self.feeds.items():
            task = asyncio.create_task(feed.start())
            self._tasks.append(task)
            logger.info(f"Started feed: {name}")
            
    async def stop(self):
        """Stop all feeds"""
        self._running = False
        
        for feed in self.feeds.values():
            await feed.stop()
            
        for task in self._tasks:
            task.cancel()
            
        self._tasks.clear()
        
    def get_status(self) -> Dict[str, Any]:
        """Get status of all feeds"""
        return {
            name: feed.get_stats()
            for name, feed in self.feeds.items()
        }


def create_websocket_feed(
    exchange: str,
    symbols: List[str],
    on_tick: Optional[Callable] = None
) -> WebSocketFeed:
    """
    Factory function to create WebSocket feed.
    
    Args:
        exchange: Exchange name (binance, coinbase, kraken)
        symbols: List of symbols to subscribe
        on_tick: Callback for tick data
        
    Returns:
        WebSocketFeed instance
    """
    exchange = exchange.lower()
    
    if exchange == 'binance':
        return BinanceWebSocketFeed(symbols, on_tick)
    elif exchange == 'coinbase':
        return CoinbaseWebSocketFeed(symbols, on_tick)
    elif exchange == 'kraken':
        return KrakenWebSocketFeed(symbols, on_tick)
    else:
        raise ValueError(f"Unknown exchange: {exchange}")


if __name__ == "__main__":
    async def on_tick(tick: TickData):
        print(f"[{tick.exchange}] {tick.symbol}: ${tick.price:.2f} @ {tick.timestamp}")
        
    async def main():
        manager = WebSocketFeedManager()
        
        # Add Binance feed
        binance = create_websocket_feed('binance', ['BTCUSDT', 'ETHUSDT'])
        manager.add_feed('binance', binance)
        
        manager.add_callback(on_tick)
        
        print("Starting WebSocket feeds...")
        print("Press Ctrl+C to stop")
        
        try:
            await manager.start()
            # Keep running
            while True:
                await asyncio.sleep(10)
                status = manager.get_status()
                for name, stats in status.items():
                    print(f"{name}: {stats['message_count']} messages, state={stats['state']}")
        except KeyboardInterrupt:
            print("\nStopping...")
            await manager.stop()
            
    asyncio.run(main())
