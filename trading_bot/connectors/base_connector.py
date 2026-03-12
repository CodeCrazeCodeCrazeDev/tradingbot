"""
Base Connector for Exchange Integration
Provides unified interface for all exchange connections
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import websockets
except ImportError:
    websockets = None
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from abc import ABC, abstractmethod
import json

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    exchange: str
    timestamp: datetime
    price: float
    bid: float
    ask: float
    volume: float
    open: float
    high: float
    low: float
    close: float
    vwap: Optional[float] = None
    metadata: Dict[str, Any] = None

@dataclass
class OrderBook:
    """Order book data structure"""
    symbol: str
    exchange: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]
    metadata: Dict[str, Any] = None

@dataclass
class Trade:
    """Trade data structure"""
    symbol: str
    exchange: str
    timestamp: datetime
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    trade_id: str
    metadata: Dict[str, Any] = None

@dataclass
class Ticker:
    """Ticker data structure"""
    symbol: str
    exchange: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume_24h: float
    change_24h: float
    metadata: Dict[str, Any] = None

class BaseConnector(ABC):
    """
    Base class for all exchange connectors
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.exchange_name = config.get('exchange', 'unknown')
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.testnet = config.get('testnet', False)
        
        # Connection management
        self.status = ConnectionStatus.DISCONNECTED
        self.session = None
        self.ws_connection = None
        
        # Callbacks
        self.callbacks = {
            'market_data': [],
            'order_book': [],
            'trade': [],
            'ticker': [],
            'error': []
        }
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            requests_per_second=config.get('rate_limit', 10)
        )
        
        # Reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = config.get('max_reconnect', 5)
        
    @abstractmethod
    async def connect(self):
        """Establish connection to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to exchange"""
        pass
    
    @abstractmethod
    async def subscribe_market_data(self, symbols: List[str]):
        """Subscribe to market data for symbols"""
        pass
    
    @abstractmethod
    async def subscribe_order_book(self, symbols: List[str], depth: int = 10):
        """Subscribe to order book updates"""
        pass
    
    @abstractmethod
    async def subscribe_trades(self, symbols: List[str]):
        """Subscribe to trade feed"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker for symbol"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Dict) -> Dict:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict:
        """Get account balance"""
        pass
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for event type"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    async def emit_event(self, event_type: str, data: Any):
        """Emit event to registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
    
    async def reconnect(self):
        """Reconnect to exchange"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {self.exchange_name}")
            self.status = ConnectionStatus.ERROR
            return False
        
        self.reconnect_attempts += 1
        self.status = ConnectionStatus.RECONNECTING
        
        logger.info(f"Reconnecting to {self.exchange_name} (attempt {self.reconnect_attempts})")
        
        # Exponential backoff
        await asyncio.sleep(2 ** self.reconnect_attempts)
        
        try:
            await self.connect()
            self.reconnect_attempts = 0
            return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            return await self.reconnect()
    
    async def heartbeat(self):
        """Send heartbeat to maintain connection"""
        while self.status == ConnectionStatus.CONNECTED:
            try:
                # Send ping or heartbeat message
                if self.ws_connection:
                    await self.ws_connection.ping()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await self.reconnect()
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange"""
        # Override in subclasses for exchange-specific formatting
        return symbol.replace('/', '')
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class RateLimiter:
    """
    Rate limiter for API calls
    """
    
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.request_times = []
        
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        current_time = asyncio.get_event_loop().time()
        
        # Remove old request times
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < 1.0
        ]
        
        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_second:
            sleep_time = 1.0 - (current_time - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                current_time = asyncio.get_event_loop().time()
        
        self.request_times.append(current_time)
        self.last_request_time = current_time
