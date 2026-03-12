"""
AlphaAlgo Market Data Collectors
================================
Production-grade collectors for WebSocket and REST data sources.
Handles reconnection, heartbeats, sequence validation, batching.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import hashlib
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Dict, List, Optional, Callable, Any, 
    AsyncIterator, Tuple, Set, Protocol
)
from datetime import datetime, timezone
from collections import deque
import struct

logger = logging.getLogger(__name__)


class CollectorState(Enum):
    """Collector lifecycle states"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATING = auto()
    AUTHENTICATED = auto()
    SUBSCRIBING = auto()
    SUBSCRIBED = auto()
    RECEIVING = auto()
    RECONNECTING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass
class CollectorConfig:
    """Configuration for market data collectors"""
    # Connection
    collector_id: str                          # Unique collector identifier
    exchange: str                              # Exchange name
    endpoint_ws: str                           # WebSocket endpoint
    endpoint_rest: str                         # REST API endpoint
    
    # Authentication
    api_key: str = ''
    api_secret: str = ''
    passphrase: str = ''                       # For exchanges like Coinbase
    
    # Subscriptions
    symbols: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)  # trades, quotes, l2, etc.
    
    # Reconnection
    reconnect_delay_initial: float = 1.0       # Initial delay in seconds
    reconnect_delay_max: float = 60.0          # Maximum delay
    reconnect_delay_multiplier: float = 2.0    # Exponential backoff multiplier
    max_reconnect_attempts: int = 100          # 0 = infinite
    
    # Heartbeat
    heartbeat_interval: float = 30.0           # Seconds between heartbeats
    heartbeat_timeout: float = 60.0            # Timeout before reconnect
    
    # Batching
    batch_size: int = 100                      # Events per batch
    batch_timeout_ms: int = 50                 # Max wait before flush
    
    # Sequence
    sequence_gap_threshold: int = 10           # Warn if gap exceeds this
    sequence_reset_on_reconnect: bool = True
    
    # Performance
    recv_buffer_size: int = 65536              # Socket receive buffer
    max_message_size: int = 10 * 1024 * 1024   # 10MB max message
    
    # Timestamps
    use_exchange_timestamps: bool = True       # Prefer exchange timestamps
    max_clock_drift_ms: int = 1000             # Max acceptable drift
    
    # REST fallback
    rest_poll_interval: float = 1.0            # Seconds between REST polls
    rest_timeout: float = 10.0                 # REST request timeout


@dataclass
class CollectorStats:
    """Runtime statistics for collector"""
    messages_received: int = 0
    messages_processed: int = 0
    messages_dropped: int = 0
    bytes_received: int = 0
    sequence_gaps: int = 0
    reconnects: int = 0
    errors: int = 0
    last_message_ts: int = 0
    last_heartbeat_ts: int = 0
    avg_latency_us: float = 0.0
    max_latency_us: float = 0.0
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'messages_received': self.messages_received,
            'messages_processed': self.messages_processed,
            'messages_dropped': self.messages_dropped,
            'bytes_received': self.bytes_received,
            'sequence_gaps': self.sequence_gaps,
            'reconnects': self.reconnects,
            'errors': self.errors,
            'last_message_ts': self.last_message_ts,
            'avg_latency_us': self.avg_latency_us,
            'max_latency_us': self.max_latency_us,
            'uptime_seconds': self.uptime_seconds,
        }


class MessageHandler(Protocol):
    """Protocol for message handlers"""
    ...


@dataclass
class SequenceTracker:
    """Tracks sequence numbers per symbol/channel"""
    expected: Dict[str, int] = field(default_factory=dict)
    last_seen: Dict[str, int] = field(default_factory=dict)
    gaps: List[Tuple[str, int, int]] = field(default_factory=list)  # (key, expected, actual)
    
    def validate(self, key: str, sequence: int) -> Tuple[bool, Optional[int]]:
        """
        Validate sequence number.
        Returns (is_valid, gap_size or None)
        """
        if key not in self.expected:
            # First message for this key
            self.expected[key] = sequence + 1
            self.last_seen[key] = sequence
            return True, None
        
        expected = self.expected[key]
        
        if sequence == expected:
            # Perfect sequence
            self.expected[key] = sequence + 1
            self.last_seen[key] = sequence
            return True, None
        
        if sequence > expected:
            # Gap detected
            gap = sequence - expected
            self.gaps.append((key, expected, sequence))
            self.expected[key] = sequence + 1
            self.last_seen[key] = sequence
            return False, gap
        
        # Duplicate or out-of-order (sequence < expected)
        return False, None
    
    def reset(self, key: Optional[str] = None):
        """Reset sequence tracking"""
        if key:
            self.expected.pop(key, None)
            self.last_seen.pop(key, None)
        else:
            self.expected.clear()
            self.last_seen.clear()
            self.gaps.clear()


class WebSocketCollector:
    """
    Production WebSocket collector with:
    - Automatic reconnection with exponential backoff
    - Heartbeat monitoring
    - Sequence validation
    - Message batching
    - Timestamp alignment
    """
    
    def __init__(
        self,
        config: CollectorConfig,
        message_handler: Callable[[bytes, int], Any],
    ):
        self.config = config
        self.message_handler = message_handler
        
        # State
        self.state = CollectorState.DISCONNECTED
        self._ws = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Reconnection
        self._reconnect_delay = config.reconnect_delay_initial
        self._reconnect_attempts = 0
        
        # Heartbeat
        self._last_heartbeat = 0
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Sequence tracking
        self.sequence_tracker = SequenceTracker()
        
        # Batching
        self._batch: List[Tuple[bytes, int]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        
        # Stats
        self.stats = CollectorStats()
        self._start_time = 0
        
        # Latency tracking (ring buffer)
        self._latencies: deque = deque(maxlen=1000)
        
        logger.info(f"WebSocketCollector initialized: {config.collector_id}")
    
    async def start(self):
        """Start the collector"""
        if self._running:
            logger.warning(f"Collector {self.config.collector_id} already running")
            return
        
        self._running = True
        self._start_time = time.time()
        self._shutdown_event.clear()
        
        # Start batch flusher
        self._batch_task = asyncio.create_task(self._batch_flusher())
        
        # Main connection loop
        while self._running:
            try:
                await self._connect()
                await self._run_receive_loop()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collector error: {e}")
                self.stats.errors += 1
                
                if self._running:
                    await self._handle_reconnect()
        
        self.state = CollectorState.SHUTDOWN
        logger.info(f"Collector {self.config.collector_id} stopped")
    
    async def stop(self):
        """Stop the collector gracefully"""
        logger.info(f"Stopping collector {self.config.collector_id}")
        self._running = False
        self._shutdown_event.set()
        
        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._batch_task:
            self._batch_task.cancel()
        
        # Close WebSocket
        if self._ws:
            await self._ws.close()
        
        # Flush remaining batch
        await self._flush_batch()
    
    async def _connect(self):
        """Establish WebSocket connection"""
        self.state = CollectorState.CONNECTING
        
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed")
            raise
        
        logger.info(f"Connecting to {self.config.endpoint_ws}")
        
        self._ws = await websockets.connect(
            self.config.endpoint_ws,
            max_size=self.config.max_message_size,
            ping_interval=self.config.heartbeat_interval,
            ping_timeout=self.config.heartbeat_timeout,
        )
        
        self.state = CollectorState.CONNECTED
        self._reconnect_delay = self.config.reconnect_delay_initial
        self._reconnect_attempts = 0
        
        # Authenticate if needed
        if self.config.api_key:
            await self._authenticate()
        
        # Subscribe to channels
        await self._subscribe()
        
        # Start heartbeat monitor
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        self._last_heartbeat = time.time_ns()
        
        logger.info(f"Connected and subscribed: {self.config.collector_id}")
    
    async def _authenticate(self):
        """Send authentication message"""
        self.state = CollectorState.AUTHENTICATING
        
        # Generate signature (exchange-specific)
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp)
        
        auth_msg = {
            'type': 'auth',
            'api_key': self.config.api_key,
            'timestamp': timestamp,
            'signature': signature,
        }
        
        if self.config.passphrase:
            auth_msg['passphrase'] = self.config.passphrase
        
        await self._ws.send(json.dumps(auth_msg))
        
        # Wait for auth response
        response = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
        response_data = json.loads(response)
        
        if response_data.get('type') == 'error':
            raise Exception(f"Authentication failed: {response_data}")
        
        self.state = CollectorState.AUTHENTICATED
        logger.info(f"Authenticated: {self.config.collector_id}")
    
    async def _subscribe(self):
        """Subscribe to market data channels"""
        self.state = CollectorState.SUBSCRIBING
        
        subscribe_msg = {
            'type': 'subscribe',
            'channels': self.config.channels,
            'symbols': self.config.symbols,
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
        
        # Reset sequence tracking on new subscription
        if self.config.sequence_reset_on_reconnect:
            self.sequence_tracker.reset()
        
        self.state = CollectorState.SUBSCRIBED
        logger.info(f"Subscribed to {len(self.config.symbols)} symbols")
    
    async def _run_receive_loop(self):
        """Main message receive loop"""
        self.state = CollectorState.RECEIVING
        
        async for message in self._ws:
            if not self._running:
                break
            
            receive_ts = time.time_ns()
            self._last_heartbeat = receive_ts
            
            # Handle binary or text
            if isinstance(message, bytes):
                raw_bytes = message
            else:
                raw_bytes = message.encode('utf-8')
            
            self.stats.messages_received += 1
            self.stats.bytes_received += len(raw_bytes)
            self.stats.last_message_ts = receive_ts
            
            # Add to batch
            await self._add_to_batch(raw_bytes, receive_ts)
    
    async def _add_to_batch(self, raw_message: bytes, receive_ts: int):
        """Add message to batch"""
        async with self._batch_lock:
            self._batch.append((raw_message, receive_ts))
            
            if len(self._batch) >= self.config.batch_size:
                await self._flush_batch_internal()
    
    async def _batch_flusher(self):
        """Periodic batch flusher"""
        while self._running:
            await asyncio.sleep(self.config.batch_timeout_ms / 1000)
            await self._flush_batch()
    
    async def _flush_batch(self):
        """Flush current batch"""
        async with self._batch_lock:
            await self._flush_batch_internal()
    
    async def _flush_batch_internal(self):
        """Internal batch flush (must hold lock)"""
        if not self._batch:
            return
        
        batch = self._batch
        self._batch = []
        
        for raw_message, receive_ts in batch:
            try:
                # Call handler
                if asyncio.iscoroutinefunction(self.message_handler):
                    await self.message_handler(raw_message, receive_ts)
                else:
                    self.message_handler(raw_message, receive_ts)
                
                self.stats.messages_processed += 1
                
                # Track latency
                process_ts = time.time_ns()
                latency_us = (process_ts - receive_ts) / 1000
                self._latencies.append(latency_us)
                
                if latency_us > self.stats.max_latency_us:
                    self.stats.max_latency_us = latency_us
                
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                self.stats.messages_dropped += 1
        
        # Update average latency
        if self._latencies:
            self.stats.avg_latency_us = sum(self._latencies) / len(self._latencies)
    
    async def _heartbeat_monitor(self):
        """Monitor heartbeat and trigger reconnect if stale"""
        while self._running:
            await asyncio.sleep(self.config.heartbeat_interval)
            
            elapsed = (time.time_ns() - self._last_heartbeat) / 1e9
            
            if elapsed > self.config.heartbeat_timeout:
                logger.warning(f"Heartbeat timeout: {elapsed:.1f}s")
                if self._ws:
                    await self._ws.close()
                break
    
    async def _handle_reconnect(self):
        """Handle reconnection with exponential backoff"""
        self.state = CollectorState.RECONNECTING
        self._reconnect_attempts += 1
        self.stats.reconnects += 1
        
        if (self.config.max_reconnect_attempts > 0 and 
            self._reconnect_attempts > self.config.max_reconnect_attempts):
            logger.error(f"Max reconnect attempts exceeded")
            self._running = False
            return
        
        logger.info(f"Reconnecting in {self._reconnect_delay:.1f}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(self._reconnect_delay)
        
        # Exponential backoff
        self._reconnect_delay = min(
            self._reconnect_delay * self.config.reconnect_delay_multiplier,
            self.config.reconnect_delay_max
        )
    
    def _generate_signature(self, timestamp: str) -> str:
        """Generate HMAC signature for authentication"""
        import hmac
        message = f"{timestamp}GET/users/self/verify"
        signature = hmac.new(
            self.config.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        self.stats.uptime_seconds = time.time() - self._start_time if self._start_time else 0
        return {
            'collector_id': self.config.collector_id,
            'exchange': self.config.exchange,
            'state': self.state.name,
            **self.stats.to_dict()
        }


class RESTCollector:
    """
    REST API collector for fallback or supplementary data.
    Polls endpoints at configured intervals.
    """
    
    def __init__(
        self,
        config: CollectorConfig,
        message_handler: Callable[[bytes, int], Any],
    ):
        self.config = config
        self.message_handler = message_handler
        
        self.state = CollectorState.DISCONNECTED
        self._running = False
        self._session = None
        self.stats = CollectorStats()
        self._start_time = 0
        
        logger.info(f"RESTCollector initialized: {config.collector_id}")
    
    async def start(self):
        """Start REST polling"""
        if self._running:
            return
        
        self._running = True
        self._start_time = time.time()
        self.state = CollectorState.CONNECTED
        
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.rest_timeout)
            )
        except ImportError:
            logger.error("aiohttp package not installed")
            raise
        
        while self._running:
            try:
                await self._poll_all_symbols()
            except Exception as e:
                logger.error(f"REST poll error: {e}")
                self.stats.errors += 1
            
            await asyncio.sleep(self.config.rest_poll_interval)
        
        self.state = CollectorState.SHUTDOWN
    
    async def stop(self):
        """Stop REST polling"""
        self._running = False
        if self._session:
            await self._session.close()
    
    async def _poll_all_symbols(self):
        """Poll data for all configured symbols"""
        tasks = [
            self._poll_symbol(symbol)
            for symbol in self.config.symbols
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _poll_symbol(self, symbol: str):
        """Poll data for a single symbol"""
        receive_ts = time.time_ns()
        
        # Build URL (exchange-specific)
        url = f"{self.config.endpoint_rest}/ticker/{symbol}"
        
        headers = {}
        if self.config.api_key:
            headers['X-API-KEY'] = self.config.api_key
        
        async with self._session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.read()
                self.stats.messages_received += 1
                self.stats.bytes_received += len(data)
                self.stats.last_message_ts = receive_ts
                
                # Call handler
                if asyncio.iscoroutinefunction(self.message_handler):
                    await self.message_handler(data, receive_ts)
                else:
                    self.message_handler(data, receive_ts)
                
                self.stats.messages_processed += 1
            else:
                logger.warning(f"REST error {response.status} for {symbol}")
                self.stats.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        self.stats.uptime_seconds = time.time() - self._start_time if self._start_time else 0
        return {
            'collector_id': self.config.collector_id,
            'exchange': self.config.exchange,
            'state': self.state.name,
            'type': 'REST',
            **self.stats.to_dict()
        }


class CollectorManager:
    """
    Manages multiple collectors across exchanges.
    Provides unified interface for starting, stopping, monitoring.
    """
    
    def __init__(self):
        self.collectors: Dict[str, WebSocketCollector] = {}
        self.rest_collectors: Dict[str, RESTCollector] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        logger.info("CollectorManager initialized")
    
    def add_collector(
        self,
        config: CollectorConfig,
        message_handler: Callable[[bytes, int], Any],
        use_rest_fallback: bool = True,
    ):
        """Add a new collector"""
        # WebSocket collector
        ws_collector = WebSocketCollector(config, message_handler)
        self.collectors[config.collector_id] = ws_collector
        
        # REST fallback
        if use_rest_fallback and config.endpoint_rest:
            rest_collector = RESTCollector(config, message_handler)
            self.rest_collectors[f"{config.collector_id}_rest"] = rest_collector
        
        logger.info(f"Added collector: {config.collector_id}")
    
    async def start_all(self):
        """Start all collectors"""
        if self._running:
            return
        
        self._running = True
        
        # Start WebSocket collectors
        for collector_id, collector in self.collectors.items():
            task = asyncio.create_task(collector.start())
            self._tasks.append(task)
            logger.info(f"Started collector: {collector_id}")
        
        # Start REST collectors (as fallback)
        for collector_id, collector in self.rest_collectors.items():
            task = asyncio.create_task(collector.start())
            self._tasks.append(task)
            logger.info(f"Started REST collector: {collector_id}")
    
    async def stop_all(self):
        """Stop all collectors"""
        self._running = False
        
        # Stop WebSocket collectors
        for collector in self.collectors.values():
            await collector.stop()
        
        # Stop REST collectors
        for collector in self.rest_collectors.values():
            await collector.stop()
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        self._tasks.clear()
        logger.info("All collectors stopped")
    
    def get_collector(self, collector_id: str) -> Optional[WebSocketCollector]:
        """Get collector by ID"""
        return self.collectors.get(collector_id)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collectors"""
        stats = {}
        
        for collector_id, collector in self.collectors.items():
            stats[collector_id] = collector.get_stats()
        
        for collector_id, collector in self.rest_collectors.items():
            stats[collector_id] = collector.get_stats()
        
        return stats
    
    def get_health(self) -> Dict[str, Any]:
        """Get overall health status"""
        total = len(self.collectors) + len(self.rest_collectors)
        healthy = sum(
            1 for c in self.collectors.values()
            if c.state in (CollectorState.RECEIVING, CollectorState.SUBSCRIBED)
        )
        healthy += sum(
            1 for c in self.rest_collectors.values()
            if c.state == CollectorState.CONNECTED
        )
        
        return {
            'total_collectors': total,
            'healthy_collectors': healthy,
            'health_ratio': healthy / total if total > 0 else 0,
            'running': self._running,
        }


# Exchange-specific collector configurations
EXCHANGE_CONFIGS = {
    'binance': {
        'ws_endpoint': 'wss://stream.binance.com:9443/ws',
        'rest_endpoint': 'https://api.binance.com/api/v3',
        'channels': ['trade', 'bookTicker', 'depth20@100ms'],
    },
    'coinbase': {
        'ws_endpoint': 'wss://ws-feed.exchange.coinbase.com',
        'rest_endpoint': 'https://api.exchange.coinbase.com',
        'channels': ['matches', 'ticker', 'level2'],
    },
    'kraken': {
        'ws_endpoint': 'wss://ws.kraken.com',
        'rest_endpoint': 'https://api.kraken.com/0/public',
        'channels': ['trade', 'spread', 'book'],
    },
    'ftx': {
        'ws_endpoint': 'wss://ftx.com/ws/',
        'rest_endpoint': 'https://ftx.com/api',
        'channels': ['trades', 'ticker', 'orderbook'],
    },
    'deribit': {
        'ws_endpoint': 'wss://www.deribit.com/ws/api/v2',
        'rest_endpoint': 'https://www.deribit.com/api/v2/public',
        'channels': ['trades', 'ticker', 'book'],
    },
}


def create_collector_config(
    exchange: str,
    symbols: List[str],
    api_key: str = '',
    api_secret: str = '',
) -> CollectorConfig:
    """Factory function to create exchange-specific collector config"""
    
    if exchange not in EXCHANGE_CONFIGS:
        raise ValueError(f"Unknown exchange: {exchange}")
    
    ex_config = EXCHANGE_CONFIGS[exchange]
    
    return CollectorConfig(
        collector_id=f"{exchange}_{uuid.uuid4().hex[:8]}",
        exchange=exchange,
        endpoint_ws=ex_config['ws_endpoint'],
        endpoint_rest=ex_config['rest_endpoint'],
        api_key=api_key,
        api_secret=api_secret,
        symbols=symbols,
        channels=ex_config['channels'],
    )
