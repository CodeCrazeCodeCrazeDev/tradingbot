"""
Elite Trading Bot - WebSocket Client

This module provides WebSocket connectivity for real-time market data streaming
from various financial data providers and trading platforms.
"""

import asyncio
import json
import logging
import ssl
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
import uuid

try:
    import websockets
except ImportError:
    websockets = None
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from .auth_manager import AuthManager

logger = logging.getLogger(__name__)


class WebSocketState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SUBSCRIBING = "subscribing"
    SUBSCRIBED = "subscribed"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class WebsocketClient:
    """
    WebSocket client for real-time market data streaming.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Subscription management
    - Message handling with callbacks
    - Authentication support
    - Heartbeat monitoring
    - Connection state tracking
    """
    
    def __init__(self, 
                 url: str,
                 name: str,
                 auth_manager: Optional[AuthManager] = None,
                 ping_interval: int = 30,
                 reconnect_interval: int = 5,
                 max_reconnect_interval: int = 300,
                 ssl_verify: bool = True):
        """
        Initialize the WebSocket client.
        
        Args:
            url: WebSocket URL
            name: Client name for identification
            auth_manager: Optional authentication manager
            ping_interval: Ping interval in seconds
            reconnect_interval: Initial reconnect interval in seconds
            max_reconnect_interval: Maximum reconnect interval in seconds
            ssl_verify: Whether to verify SSL certificates
        """
        self.url = url
        self.name = name
        self.auth_manager = auth_manager
        self.ping_interval = ping_interval
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_interval = max_reconnect_interval
        self.ssl_verify = ssl_verify
        
        # Connection state
        self.state = WebSocketState.DISCONNECTED
        self.ws: Optional[WebSocketClientProtocol] = None
        self.last_message_time: Optional[float] = None
        self.reconnect_count = 0
        self.connection_id = str(uuid.uuid4())
        
        # Subscription management
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.pending_subscriptions: Set[str] = set()
        
        # Message handling
        self.message_handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.default_handlers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Tasks
        self.tasks: List[asyncio.Task] = []
        
        logger.info(f"WebsocketClient '{name}' initialized for {url}")
    
    async def connect(self) -> bool:
        """
        Connect to the WebSocket server.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.state in (WebSocketState.CONNECTED, WebSocketState.SUBSCRIBED):
            logger.debug(f"WebsocketClient '{self.name}' already connected")
            return True
        
        self.state = WebSocketState.CONNECTING
        logger.info(f"WebsocketClient '{self.name}' connecting to {self.url}")
        
        try:
            # Configure SSL context
            ssl_context = None
            if self.url.startswith("wss://"):
                ssl_context = ssl.create_default_context()
                if not self.ssl_verify:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to WebSocket server
            self.ws = await websockets.connect(
                self.url,
                ssl=ssl_context,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_interval + 10,
                close_timeout=5
            )
            
            self.state = WebSocketState.CONNECTED
            self.last_message_time = time.time()
            self.reconnect_count = 0
            self.connection_id = str(uuid.uuid4())
            
            logger.info(f"WebsocketClient '{self.name}' connected (id: {self.connection_id})")
            
            # Start message handling and heartbeat tasks
            self._start_tasks()
            
            # Resubscribe to previous subscriptions
            if self.subscriptions:
                await self._resubscribe()
            
            return True
            
        except Exception as e:
            self.state = WebSocketState.ERROR
            logger.error(f"WebsocketClient '{self.name}' connection failed: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        self.tasks = []
        
        # Close WebSocket connection
        if self.ws:
            try:
                await self.ws.close()
                logger.info(f"WebsocketClient '{self.name}' disconnected")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {str(e)}")
            
            self.ws = None
        
        self.state = WebSocketState.DISCONNECTED
    
    def _start_tasks(self):
        """Start message handling and heartbeat tasks."""
        # Cancel existing tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        self.tasks = []
        
        # Start new tasks
        self.tasks.append(asyncio.create_task(self._message_handler()))
        self.tasks.append(asyncio.create_task(self._heartbeat_monitor()))
        
        logger.debug(f"WebsocketClient '{self.name}' tasks started")
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages."""
        if not self.ws:
            return
        try:
        
            async for message in self.ws:
                self.last_message_time = time.time()
                
                try:
                    # Parse message
                    if isinstance(message, str):
                        data = json.loads(message)
                    elif isinstance(message, bytes):
                        data = json.loads(message.decode('utf-8'))
                    else:
                        logger.warning(f"Received unknown message type: {type(message)}")
                        continue
                    
                    # Process message
                    await self._process_message(data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse message as JSON: {message[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
        
        except ConnectionClosedError as e:
            logger.warning(f"WebsocketClient '{self.name}' connection closed: {str(e)}")
            await self._handle_disconnection()
        except Exception as e:
            logger.error(f"WebsocketClient '{self.name}' message handler error: {str(e)}")
            await self._handle_disconnection()
    
    async def _heartbeat_monitor(self):
        """Monitor connection health and handle reconnection."""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                
                # Check if connection is still alive
                if self.ws and self.last_message_time:
                    time_since_last = time.time() - self.last_message_time
                    
                    if time_since_last > self.ping_interval * 2:
                        logger.warning(f"WebsocketClient '{self.name}' heartbeat timeout ({time_since_last:.1f}s)")
                        await self._handle_disconnection()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {str(e)}")
    
    async def _handle_disconnection(self):
        """Handle WebSocket disconnection with reconnection logic."""
        if self.state == WebSocketState.RECONNECTING:
            return
        
        self.state = WebSocketState.RECONNECTING
        
        # Calculate reconnect delay with exponential backoff
        delay = min(
            self.reconnect_interval * (2 ** self.reconnect_count),
            self.max_reconnect_interval
        )
        
        self.reconnect_count += 1
        
        logger.info(f"WebsocketClient '{self.name}' reconnecting in {delay}s (attempt {self.reconnect_count})")
        
        # Close existing connection
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            
            self.ws = None
        
        # Wait before reconnecting
        await asyncio.sleep(delay)
        
        # Attempt to reconnect
        success = await self.connect()
        
        if not success:
            # Schedule another reconnection attempt
            asyncio.create_task(self._handle_disconnection())
    
    async def _process_message(self, data: Dict[str, Any]):
        """
        Process an incoming message.
        
        Args:
            data: Message data
        """
        # Check for subscription confirmations
        if self._is_subscription_confirmation(data):
            await self._handle_subscription_confirmation(data)
        
        # Determine message type
        message_type = self._get_message_type(data)
        
        # Call specific handlers for this message type
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in message handler: {str(e)}")
        
        # Call default handlers
        for handler in self.default_handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in default handler: {str(e)}")
    
    def _is_subscription_confirmation(self, data: Dict[str, Any]) -> bool:
        """
        Check if a message is a subscription confirmation.
        
        Args:
            data: Message data
            
        Returns:
            True if message is a subscription confirmation
        """
        # This is a generic implementation - specific clients should override this
        if 'type' in data and data['type'] in ('subscribed', 'subscription'):
            return True
        
        return False
    
    async def _handle_subscription_confirmation(self, data: Dict[str, Any]):
        """
        Handle subscription confirmation.
        
        Args:
            data: Confirmation message data
        """
        # This is a generic implementation - specific clients should override this
        channel = data.get('channel', '')
        
        if channel in self.pending_subscriptions:
            self.pending_subscriptions.remove(channel)
            logger.info(f"WebsocketClient '{self.name}' subscription confirmed for {channel}")
        
        if not self.pending_subscriptions and self.state == WebSocketState.SUBSCRIBING:
            self.state = WebSocketState.SUBSCRIBED
            logger.info(f"WebsocketClient '{self.name}' all subscriptions confirmed")
    
    def _get_message_type(self, data: Dict[str, Any]) -> str:
        """
        Determine the type of a message.
        
        Args:
            data: Message data
            
        Returns:
            Message type string
        """
        # This is a generic implementation - specific clients should override this
        if 'type' in data:
            return data['type']
        elif 'channel' in data:
            return data['channel']
        elif 'e' in data:  # Binance style
            return data['e']
        else:
            return 'unknown'
    
    async def subscribe(self, channel: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name
            params: Optional subscription parameters
            
        Returns:
            True if subscription request sent successfully
        """
        if not self.ws or self.state not in (WebSocketState.CONNECTED, WebSocketState.SUBSCRIBED):
            logger.warning(f"Cannot subscribe to {channel}: not connected")
            return False
        
        # Store subscription for reconnection
        self.subscriptions[channel] = params or {}
        
        # Add to pending subscriptions
        self.pending_subscriptions.add(channel)
        
        # Create subscription message
        subscription = {
            "type": "subscribe",
            "channel": channel
        }
        
        if params:
            subscription.update(params)
        
        # Send subscription request
        try:
            await self.ws.send(json.dumps(subscription))
            logger.info(f"WebsocketClient '{self.name}' subscribed to {channel}")
            
            if self.state == WebSocketState.CONNECTED:
                self.state = WebSocketState.SUBSCRIBING
            
            return True
            
        except Exception as e:
            logger.error(f"Subscription error for {channel}: {str(e)}")
            return False
    
    async def unsubscribe(self, channel: str) -> bool:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name
            
        Returns:
            True if unsubscription request sent successfully
        """
        if not self.ws or self.state not in (WebSocketState.CONNECTED, WebSocketState.SUBSCRIBED):
            logger.warning(f"Cannot unsubscribe from {channel}: not connected")
            return False
        
        # Remove from subscriptions
        if channel in self.subscriptions:
            del self.subscriptions[channel]
        
        # Remove from pending subscriptions
        if channel in self.pending_subscriptions:
            self.pending_subscriptions.remove(channel)
        
        # Create unsubscription message
        unsubscription = {
            "type": "unsubscribe",
            "channel": channel
        }
        
        try:
            # Send unsubscription request
            await self.ws.send(json.dumps(unsubscription))
            logger.info(f"WebsocketClient '{self.name}' unsubscribed from {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Unsubscription error for {channel}: {str(e)}")
            return False
    
    async def _resubscribe(self):
        """Resubscribe to all previous subscriptions after reconnection."""
        if not self.subscriptions:
            return
        
        logger.info(f"WebsocketClient '{self.name}' resubscribing to {len(self.subscriptions)} channels")
        
        self.state = WebSocketState.SUBSCRIBING
        self.pending_subscriptions = set(self.subscriptions.keys())
        
        for channel, params in self.subscriptions.items():
            await self.subscribe(channel, params)
    
    async def send(self, data: Union[Dict[str, Any], str]) -> bool:
        """
        Send a message to the WebSocket server.
        
        Args:
            data: Message data (dictionary or JSON string)
            
        Returns:
            True if message sent successfully
        """
        if not self.ws:
            logger.warning(f"Cannot send message: not connected")
            return False
        try:
        
            if isinstance(data, dict):
                await self.ws.send(json.dumps(data))
            else:
                await self.ws.send(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def add_message_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Add a handler for a specific message type.
        
        Args:
            message_type: Message type to handle
            handler: Handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Added handler for message type '{message_type}'")
    
    def add_default_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Add a default handler for all messages.
        
        Args:
            handler: Handler function
        """
        self.default_handlers.append(handler)
        logger.debug(f"Added default message handler")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.
        
        Returns:
            Connection information
        """
        info = {
            "name": self.name,
            "url": self.url,
            "state": self.state.value,
            "connection_id": self.connection_id,
            "reconnect_count": self.reconnect_count,
            "subscriptions": list(self.subscriptions.keys()),
            "pending_subscriptions": list(self.pending_subscriptions),
            "connected": self.ws is not None
        }
        
        if self.last_message_time:
            info["last_message_age"] = time.time() - self.last_message_time
        
        return info
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class BinanceWebsocketClient(WebsocketClient):
    """WebSocket client for Binance exchange."""
    
    def __init__(self, testnet: bool = False, **kwargs):
        """
        Initialize Binance WebSocket client.
        
        Args:
            testnet: Whether to use testnet
            **kwargs: Additional client parameters
        """
        url = "wss://stream.binance.com:9443/ws" if not testnet else "wss://testnet.binance.vision/ws"
        super().__init__(url=url, name="binance", **kwargs)
    
    async def subscribe_ticker(self, symbol: str) -> bool:
        """
        Subscribe to ticker updates for a symbol.
        
        Args:
            symbol: Symbol name (lowercase)
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe(f"{symbol}@ticker")
    
    async def subscribe_klines(self, symbol: str, interval: str) -> bool:
        """
        Subscribe to kline (candlestick) updates.
        
        Args:
            symbol: Symbol name (lowercase)
            interval: Kline interval (e.g., "1m", "5m", "1h")
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe(f"{symbol}@kline_{interval}")
    
    async def subscribe_depth(self, symbol: str, levels: int = 10) -> bool:
        """
        Subscribe to order book updates.
        
        Args:
            symbol: Symbol name (lowercase)
            levels: Order book depth (5, 10, or 20)
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe(f"{symbol}@depth{levels}")
    
    async def subscribe_trades(self, symbol: str) -> bool:
        """
        Subscribe to trade updates.
        
        Args:
            symbol: Symbol name (lowercase)
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe(f"{symbol}@trade")
    
    def _get_message_type(self, data: Dict[str, Any]) -> str:
        """Get Binance-specific message type."""
        if 'e' in data:
            return data['e']  # Event type
        elif 'stream' in data:
            return data['stream']  # Stream name
        else:
            return super()._get_message_type(data)


class CoinbaseWebsocketClient(WebsocketClient):
    """WebSocket client for Coinbase Pro exchange."""
    
    def __init__(self, **kwargs):
        """
        Initialize Coinbase WebSocket client.
        
        Args:
            **kwargs: Additional client parameters
        """
        super().__init__(url="wss://ws-feed.pro.coinbase.com", name="coinbase", **kwargs)
    
    async def subscribe(self, channel: str, product_ids: List[str]) -> bool:
        """
        Subscribe to a channel for specific products.
        
        Args:
            channel: Channel name
            product_ids: List of product IDs
            
        Returns:
            True if subscription successful
        """
        # Store subscription
        self.subscriptions[channel] = {"product_ids": product_ids}
        
        # Add to pending subscriptions
        self.pending_subscriptions.add(channel)
        
        # Create subscription message
        subscription = {
            "type": "subscribe",
            "channels": [
                {
                    "name": channel,
                    "product_ids": product_ids
                }
            ]
        }
        
        # Send subscription request
        return await self.send(subscription)
    
    async def subscribe_ticker(self, product_ids: List[str]) -> bool:
        """
        Subscribe to ticker updates.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe("ticker", product_ids)
    
    async def subscribe_level2(self, product_ids: List[str]) -> bool:
        """
        Subscribe to order book updates.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe("level2", product_ids)
    
    async def subscribe_matches(self, product_ids: List[str]) -> bool:
        """
        Subscribe to trade matches.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            True if subscription successful
        """
        return await self.subscribe("matches", product_ids)
    
    def _is_subscription_confirmation(self, data: Dict[str, Any]) -> bool:
        """Check if message is a Coinbase subscription confirmation."""
        return data.get('type') == 'subscriptions'
    
    def _get_message_type(self, data: Dict[str, Any]) -> str:
        """Get Coinbase-specific message type."""
        if 'type' in data:
            return data['type']
        else:
            return super()._get_message_type(data)
