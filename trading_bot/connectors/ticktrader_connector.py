"""
TickTrader / FXOpen Connector
Level 2 (Order Book) Data via TickTrader Web API
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import json
import logging
import os
import hmac
import hashlib
import base64
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class OrderBookSource(Enum):
    """Order book data source"""
    TICKTRADER = "ticktrader"
    FXOPEN = "fxopen"
    UNKNOWN = "unknown"


@dataclass
class OrderBookLevel:
    """Single level in order book"""
    price: float
    size: float


@dataclass
class OrderBook:
    """Order book snapshot"""
    symbol: str
    source: OrderBookSource
    timestamp: datetime
    bids: List['OrderBookLevel']
    asks: List['OrderBookLevel']


@dataclass
class TickTraderConfig:
    """TickTrader connection configuration"""
    login: str
    password: str
    server: str
    use_ssl: bool = True
    timeout: int = 30
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 10


class TickTraderConnector:
    """
    TickTrader / FXOpen connector for Level 2 market data
    
    Supports:
    - Real-time order book (Level 2) data
    - Market depth streaming
    - Trade execution
    - Account information
    """
    
    def __init__(self, config: Optional[TickTraderConfig] = None):
        """Initialize TickTrader connector"""
        # Load from environment if config not provided
        if config is None:
            config = TickTraderConfig(
                login=os.getenv('TICKTRADER_LOGIN', ''),
                password=os.getenv('TICKTRADER_PASSWORD', ''),
                server=os.getenv('TICKTRADER_SERVER', '')
            )
        
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # WebSocket connection
        self.ws_connection = None
        self.ws_connected = False
        
        # API endpoints
        protocol = "https" if self.config.use_ssl else "http"
        ws_protocol = "wss" if self.config.use_ssl else "ws"
        
        self.base_url = f"{protocol}://{self.config.server}/api/v2"
        self.ws_url = f"{ws_protocol}://{self.config.server}/api/v2/feed"
        
        # Authentication
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Subscriptions
        self.subscribed_symbols: List[str] = []
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'order_book': [],
            'tick': [],
            'trade': [],
            'connected': [],
            'disconnected': [],
            'error': []
        }
        
        # Reconnection
        self.reconnect_attempts = 0
        self._reconnect_task: Optional[asyncio.Task] = None
        
        logger.info(f"TickTraderConnector initialized for {self.config.server}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event_type: str, data: Any):
        """Emit event to handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    async def connect(self) -> bool:
        """Connect to TickTrader server"""
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info(f"Connecting to TickTrader at {self.config.server}...")
            
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Authenticate
            if not await self._authenticate():
                raise Exception("Authentication failed")
            
            # Connect WebSocket for streaming
            await self._connect_websocket()
            
            self.status = ConnectionStatus.CONNECTED
            self.reconnect_attempts = 0
            
            await self.emit_event('connected', {'server': self.config.server})
            logger.info("Successfully connected to TickTrader")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.status = ConnectionStatus.ERROR
            await self.emit_event('error', {'error': str(e)})
            return False
    
    async def disconnect(self):
        """Disconnect from TickTrader"""
        try:
            self.status = ConnectionStatus.DISCONNECTED
            
            # Close WebSocket
            if self.ws_connection:
                await self.ws_connection.close()
                self.ws_connection = None
                self.ws_connected = False
            
            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            await self.emit_event('disconnected', {})
            logger.info("Disconnected from TickTrader")
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    async def _authenticate(self) -> bool:
        """Authenticate with TickTrader API"""
        try:
            # TickTrader Web API uses basic auth or token-based auth
            auth_url = f"{self.base_url}/auth"
            
            auth_data = {
                'Login': self.config.login,
                'Password': self.config.password
            }
            
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('Token') or data.get('AccessToken')
                    logger.info("Authentication successful")
                    return True
                else:
                    # Try basic auth header approach
                    logger.warning(f"Token auth failed ({response.status}), using basic auth")
                    return True  # Will use basic auth in requests
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        else:
            # Use basic auth
            credentials = f"{self.config.login}:{self.config.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
        
        return headers
    
    async def _connect_websocket(self):
        """Connect to WebSocket for streaming data"""
        try:
            import websockets
            
            headers = self._get_auth_headers()
            
            self.ws_connection = await websockets.connect(
                self.ws_url,
                extra_headers=headers
            )
            self.ws_connected = True
            
            # Start message handler
            asyncio.create_task(self._handle_ws_messages())
            
            logger.info("WebSocket connected for streaming")
            
        except ImportError:
            logger.warning("websockets not installed, using polling mode")
            self.ws_connected = False
        except Exception as e:
            logger.warning(f"WebSocket connection failed: {e}, using polling mode")
            self.ws_connected = False
    
    async def _handle_ws_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws_connection:
                data = json.loads(message)
                await self._process_message(data)
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.ws_connected = False
            await self._schedule_reconnect()
    
    async def _process_message(self, data: Dict):
        """Process incoming message"""
        msg_type = data.get('Type') or data.get('type') or data.get('e')
        
        if msg_type in ['Level2', 'OrderBook', 'Depth', 'depth']:
            await self._process_order_book(data)
        elif msg_type in ['Tick', 'Quote', 'tick']:
            await self._process_tick(data)
        elif msg_type in ['Trade', 'trade']:
            await self._process_trade(data)
    
    async def _process_order_book(self, data: Dict):
        """Process order book update"""
        from trading_bot.data.level2_data_handler import OrderBook, OrderBookLevel, OrderBookSource
        
        symbol = data.get('Symbol') or data.get('symbol') or data.get('s')
        
        # Parse bids
        bids_data = data.get('Bids') or data.get('bids') or data.get('b') or []
        bids = []
        for bid in bids_data:
            if isinstance(bid, dict):
                bids.append(OrderBookLevel(
                    price=float(bid.get('Price') or bid.get('price') or bid.get('p', 0)),
                    size=float(bid.get('Volume') or bid.get('size') or bid.get('v', 0))
                ))
            elif isinstance(bid, (list, tuple)) and len(bid) >= 2:
                bids.append(OrderBookLevel(price=float(bid[0]), size=float(bid[1])))
        
        # Parse asks
        asks_data = data.get('Asks') or data.get('asks') or data.get('a') or []
        asks = []
        for ask in asks_data:
            if isinstance(ask, dict):
                asks.append(OrderBookLevel(
                    price=float(ask.get('Price') or ask.get('price') or ask.get('p', 0)),
                    size=float(ask.get('Volume') or ask.get('size') or ask.get('v', 0))
                ))
            elif isinstance(ask, (list, tuple)) and len(ask) >= 2:
                asks.append(OrderBookLevel(price=float(ask[0]), size=float(ask[1])))
        
        # Sort bids descending, asks ascending
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)
        
        order_book = OrderBook(
            symbol=symbol,
            source=OrderBookSource.TICKTRADER,
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )
        
        await self.emit_event('order_book', order_book)
    
    async def _process_tick(self, data: Dict):
        """Process tick/quote update"""
        tick = {
            'symbol': data.get('Symbol') or data.get('symbol'),
            'bid': float(data.get('Bid') or data.get('bid') or 0),
            'ask': float(data.get('Ask') or data.get('ask') or 0),
            'last': float(data.get('Last') or data.get('last') or 0),
            'timestamp': datetime.now()
        }
        await self.emit_event('tick', tick)
    
    async def _process_trade(self, data: Dict):
        """Process trade update"""
        trade = {
            'symbol': data.get('Symbol') or data.get('symbol'),
            'price': float(data.get('Price') or data.get('price') or 0),
            'size': float(data.get('Volume') or data.get('size') or 0),
            'side': data.get('Side') or data.get('side'),
            'timestamp': datetime.now()
        }
        await self.emit_event('trade', trade)
    
    async def subscribe_level2(self, symbols: List[str]):
        """Subscribe to Level 2 (order book) data"""
        try:
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    self.subscribed_symbols.append(symbol)
            
            if self.ws_connected and self.ws_connection:
                # Send subscription via WebSocket
                subscribe_msg = {
                    'Type': 'Subscribe',
                    'Symbols': symbols,
                    'Streams': ['Level2', 'Tick']
                }
                await self.ws_connection.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to Level 2 for: {symbols}")
            else:
                # Start polling mode
                asyncio.create_task(self._poll_level2(symbols))
                logger.info(f"Started polling Level 2 for: {symbols}")
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
    
    async def _poll_level2(self, symbols: List[str], interval: float = 1.0):
        """Poll Level 2 data (fallback when WebSocket unavailable)"""
        while self.status == ConnectionStatus.CONNECTED:
            try:
                for symbol in symbols:
                    order_book = await self.get_order_book(symbol)
                    if order_book:
                        await self.emit_event('order_book', order_book)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(interval * 2)
    
    async def get_order_book(self, symbol: str, depth: int = 20) -> Optional[Any]:
        """Get order book snapshot via REST API"""
            
        try:
            url = f"{self.base_url}/level2/{symbol}"
            params = {'depth': depth}
            
            async with self.session.get(
                url,
                headers=self._get_auth_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse response
                    bids = []
                    asks = []
                    
                    for bid in data.get('Bids', data.get('bids', [])):
                        if isinstance(bid, dict):
                            bids.append(OrderBookLevel(
                                price=float(bid.get('Price', bid.get('price', 0))),
                                size=float(bid.get('Volume', bid.get('size', 0)))
                            ))
                        elif isinstance(bid, (list, tuple)):
                            bids.append(OrderBookLevel(price=float(bid[0]), size=float(bid[1])))
                    
                    for ask in data.get('Asks', data.get('asks', [])):
                        if isinstance(ask, dict):
                            asks.append(OrderBookLevel(
                                price=float(ask.get('Price', ask.get('price', 0))),
                                size=float(ask.get('Volume', ask.get('size', 0)))
                            ))
                        elif isinstance(ask, (list, tuple)):
                            asks.append(OrderBookLevel(price=float(ask[0]), size=float(ask[1])))
                    
                    bids.sort(key=lambda x: x.price, reverse=True)
                    asks.sort(key=lambda x: x.price)
                    
                    return OrderBook(
                        symbol=symbol,
                        source=OrderBookSource.TICKTRADER,
                        timestamp=datetime.now(),
                        bids=bids,
                        asks=asks
                    )
                else:
                    logger.warning(f"Failed to get order book: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Get order book error: {e}")
            return None
    
    async def get_symbols(self) -> List[Dict]:
        """Get available symbols"""
        try:
            url = f"{self.base_url}/symbols"
            
            async with self.session.get(
                url,
                headers=self._get_auth_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
                
        except Exception as e:
            logger.error(f"Get symbols error: {e}")
            return []
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            url = f"{self.base_url}/account"
            
            async with self.session.get(
                url,
                headers=self._get_auth_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except Exception as e:
            logger.error(f"Get account info error: {e}")
            return None
    
    async def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.reconnect_attempts < self.config.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.status = ConnectionStatus.RECONNECTING
            
            delay = self.config.reconnect_delay * self.reconnect_attempts
            logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts})")
            
            await asyncio.sleep(delay)
            await self.connect()
            
            # Resubscribe
            if self.subscribed_symbols:
                await self.subscribe_level2(self.subscribed_symbols)
        else:
            logger.error("Max reconnection attempts reached")
            self.status = ConnectionStatus.ERROR


# Factory function
def create_ticktrader_connector(config: Optional[TickTraderConfig] = None) -> TickTraderConnector:
    """Create TickTrader connector instance"""
    return TickTraderConnector(config)


__all__ = [
    'TickTraderConnector',
    'TickTraderConfig',
    'ConnectionStatus',
    'create_ticktrader_connector'
]
