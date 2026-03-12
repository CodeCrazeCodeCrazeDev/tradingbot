"""
from typing import Callable, List, Optional, Set
Binance Broker Adapter - Production-Ready Binance Integration

Complete implementation for Binance spot and futures trading:
- Real-time order execution
- Position management
- WebSocket streaming
- Rate limiting
- Error handling with retries
"""

import asyncio
import logging
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - install with: pip install aiohttp")

try:
    from trading_bot.brokers.broker_adapter import (
        BrokerAdapter, Position, OrderResponse, OrderStatus, OrderSide, OrderType
    )
except ImportError:
    
    class OrderStatus(Enum):
        PENDING = "pending"
        FILLED = "filled"
        PARTIALLY_FILLED = "partially_filled"
        CANCELLED = "cancelled"
        REJECTED = "rejected"
    
    class OrderSide(Enum):
        BUY = "buy"
        SELL = "sell"
    
    class OrderType(Enum):
        MARKET = "market"
        LIMIT = "limit"
        STOP = "stop"
        STOP_LIMIT = "stop_limit"
    
    @dataclass
    class Position:
        symbol: str
        side: str
        quantity: float
        entry_price: float
        current_price: float
        unrealized_pnl: float
        realized_pnl: float = 0.0
        timestamp: datetime = None
    
    @dataclass
    class OrderResponse:
        order_id: str
        status: OrderStatus
        filled_quantity: float
        average_fill_price: float
        commission: float
        timestamp: datetime
        metadata: Dict[str, Any]
        
        @property
        def success(self) -> bool:
            return self.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING]
    
    class BrokerAdapter:
        pass


class BinanceEndpoints:
    """Binance API endpoints"""
    # Spot
    SPOT_BASE = "https://api.binance.com"
    SPOT_TESTNET = "https://testnet.binance.vision"
    
    # Futures
    FUTURES_BASE = "https://fapi.binance.com"
    FUTURES_TESTNET = "https://testnet.binancefuture.com"
    
    # WebSocket
    SPOT_WS = "wss://stream.binance.com:9443/ws"
    FUTURES_WS = "wss://fstream.binance.com/ws"


class RateLimiter:
    """Rate limiter for Binance API"""
    
    def __init__(self, requests_per_minute: int = 1200, orders_per_second: int = 10):
        self.requests_per_minute = requests_per_minute
        self.orders_per_second = orders_per_second
        self.request_times: List[float] = []
        self.order_times: List[float] = []
        self._lock = asyncio.Lock()
    
    async def wait_for_request(self):
        """Wait if rate limit would be exceeded"""
        async with self._lock:
            now = time.time()
            # Clean old requests
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            if len(self.request_times) >= self.requests_per_minute:
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            self.request_times.append(time.time())
    
    async def wait_for_order(self):
        """Wait if order rate limit would be exceeded"""
        async with self._lock:
            now = time.time()
            self.order_times = [t for t in self.order_times if now - t < 1]
            
            if len(self.order_times) >= self.orders_per_second:
                wait_time = 1 - (now - self.order_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.order_times.append(time.time())


class BinanceBrokerAdapter(BrokerAdapter):
    """
    Production-ready Binance broker adapter.
    
    Features:
    - Spot and Futures trading
    - Testnet support
    - WebSocket streaming
    - Rate limiting
    - Automatic reconnection
    - Order tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False
        
        # API credentials
        self.api_key = self.config.get('api_key', '')
        self.api_secret = self.config.get('api_secret', '')
        self.testnet = self.config.get('testnet', True)
        self.futures = self.config.get('futures', False)
        
        # Set endpoints
        if self.futures:
            self.base_url = BinanceEndpoints.FUTURES_TESTNET if self.testnet else BinanceEndpoints.FUTURES_BASE
            self.ws_url = BinanceEndpoints.FUTURES_WS
        else:
            self.base_url = BinanceEndpoints.SPOT_TESTNET if self.testnet else BinanceEndpoints.SPOT_BASE
            self.ws_url = BinanceEndpoints.SPOT_WS
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiter
        self.rate_limiter = RateLimiter()
        
        # WebSocket
        self.ws_connection = None
        self.ws_callbacks: Dict[str, Callable] = {}
        self.ws_running = False
        
        # Cache
        self._account_cache = None
        self._account_cache_time = None
        self._cache_ttl = 5
        
        # Order tracking
        self.pending_orders: Dict[str, OrderResponse] = {}
        
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not installed - Binance adapter unavailable")
    
    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign request with HMAC SHA256"""
        params['timestamp'] = int(time.time() * 1000)
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        return params
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False
    ) -> Optional[Dict]:
        """Make HTTP request to Binance API"""
        if not self.session:
            return None
        
        await self.rate_limiter.wait_for_request()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            try:
                params = self._sign_request(params)

                async with self.session.request(
                    method,
                    url,
                    params=params if method == 'GET' else None,
                    json=params if method == 'POST' else None,
                    headers=self._get_headers()
                ) as response:
                    data = await response.json()

                    if response.status != 200:
                        logger.error(f"Binance API error: {data}")
                        return None

                    return data

            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None

    async def connect(self) -> bool:
        """Connect to Binance"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not available")
            return False
        
        if not self.api_key or not self.api_secret:
            logger.error("Binance API credentials not provided")
            return False
        try:
        
            # Create session
            self.session = aiohttp.ClientSession()
            
            # Test connection
            if self.futures:
                account = await self._request('GET', '/fapi/v2/account', signed=True)
            else:
                account = await self._request('GET', '/api/v3/account', signed=True)
            
            if account is None:
                logger.error("Failed to connect to Binance")
                await self.session.close()
                return False
            
            self.connected = True
            mode = "TESTNET" if self.testnet else "LIVE"
            market = "FUTURES" if self.futures else "SPOT"
            logger.info(f"Binance connected ({mode} {market})")
            
            # Log account info
            if self.futures:
                balance = float(account.get('totalWalletBalance', 0))
                logger.info(f"  Wallet Balance: ${balance:,.2f}")
            else:
                balances = {b['asset']: float(b['free']) for b in account.get('balances', []) if float(b['free']) > 0}
                logger.info(f"  Balances: {balances}")
            
            return True
            
        except Exception as e:
            logger.error(f"Binance connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance"""
        self.connected = False
        self.ws_running = False
        
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Binance disconnected")
        return True
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not self.connected:
            return []
        try:
        
            if self.futures:
                # Futures positions
                data = await self._request('GET', '/fapi/v2/positionRisk', signed=True)
                if not data:
                    return []
                
                positions = []
                for pos in data:
                    qty = float(pos.get('positionAmt', 0))
                    if qty != 0:
                        entry_price = float(pos.get('entryPrice', 0))
                        mark_price = float(pos.get('markPrice', 0))
                        unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                        
                        positions.append(Position(
                            symbol=pos['symbol'],
                            side='buy' if qty > 0 else 'sell',
                            quantity=abs(qty),
                            entry_price=entry_price,
                            current_price=mark_price,
                            unrealized_pnl=unrealized_pnl,
                            realized_pnl=0.0,
                            timestamp=datetime.now()
                        ))
                
                return positions
            else:
                # Spot - return balances as positions
                account = await self._request('GET', '/api/v3/account', signed=True)
                if not account:
                    return []
                
                positions = []
                for balance in account.get('balances', []):
                    free = float(balance.get('free', 0))
                    locked = float(balance.get('locked', 0))
                    total = free + locked
                    
                    if total > 0 and balance['asset'] != 'USDT':
                        # Get current price
                        ticker = await self._request('GET', '/api/v3/ticker/price', {'symbol': f"{balance['asset']}USDT"})
                        price = float(ticker.get('price', 0)) if ticker else 0
                        
                        positions.append(Position(
                            symbol=f"{balance['asset']}USDT",
                            side='buy',
                            quantity=total,
                            entry_price=price,  # We don't have entry price for spot
                            current_price=price,
                            unrealized_pnl=0.0,
                            realized_pnl=0.0,
                            timestamp=datetime.now()
                        ))
                
                return positions
                
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        positions = await self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Optional[OrderResponse]:
        """Place an order"""
        if not self.connected:
            logger.error("Not connected to Binance")
            return None
        
        await self.rate_limiter.wait_for_order()
        
        try:
            # Build order params
            params = {
                'symbol': symbol,
                'side': 'BUY' if side == OrderSide.BUY else 'SELL',
                'quantity': quantity
            }
            
            # Order type
            if order_type == OrderType.MARKET:
                params['type'] = 'MARKET'
            elif order_type == OrderType.LIMIT:
                params['type'] = 'LIMIT'
                params['price'] = price
                params['timeInForce'] = kwargs.get('time_in_force', 'GTC')
            elif order_type == OrderType.STOP:
                params['type'] = 'STOP_MARKET' if self.futures else 'STOP_LOSS'
                params['stopPrice'] = stop_price
            elif order_type == OrderType.STOP_LIMIT:
                params['type'] = 'STOP' if self.futures else 'STOP_LOSS_LIMIT'
                params['price'] = price
                params['stopPrice'] = stop_price
                params['timeInForce'] = kwargs.get('time_in_force', 'GTC')
            
            # Add optional params
            if 'client_order_id' in kwargs:
                params['newClientOrderId'] = kwargs['client_order_id']
            
            # Submit order
            endpoint = '/fapi/v1/order' if self.futures else '/api/v3/order'
            result = await self._request('POST', endpoint, params, signed=True)
            
            if not result:
                return None
            
            # Parse response
            status_map = {
                'NEW': OrderStatus.PENDING,
                'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
                'FILLED': OrderStatus.FILLED,
                'CANCELED': OrderStatus.CANCELLED,
                'REJECTED': OrderStatus.REJECTED,
                'EXPIRED': OrderStatus.CANCELLED
            }
            
            status = status_map.get(result.get('status', 'NEW'), OrderStatus.PENDING)
            
            response = OrderResponse(
                order_id=str(result.get('orderId', '')),
                status=status,
                filled_quantity=float(result.get('executedQty', 0)),
                average_fill_price=float(result.get('avgPrice', 0)) if self.futures else float(result.get('price', 0)),
                commission=0.0,  # Calculated separately
                timestamp=datetime.now(),
                metadata={
                    'client_order_id': result.get('clientOrderId', ''),
                    'binance_status': result.get('status', ''),
                    'type': result.get('type', '')
                }
            )
            
            logger.info(f"Order placed: {response.order_id} - {symbol} {side.value} {quantity}")
            
            # Track pending orders
            if status == OrderStatus.PENDING:
                self.pending_orders[response.order_id] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order"""
        if not self.connected:
            return False
        try:
        
            params = {'orderId': int(order_id)}
            if symbol:
                params['symbol'] = symbol
            
            endpoint = '/fapi/v1/order' if self.futures else '/api/v3/order'
            result = await self._request('DELETE', endpoint, params, signed=True)
            
            if result and result.get('status') == 'CANCELED':
                logger.info(f"Order cancelled: {order_id}")
                self.pending_orders.pop(order_id, None)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str = None) -> Optional[OrderResponse]:
        """Get order status"""
        if not self.connected:
            return None
        try:
        
            params = {'orderId': int(order_id)}
            if symbol:
                params['symbol'] = symbol
            
            endpoint = '/fapi/v1/order' if self.futures else '/api/v3/order'
            result = await self._request('GET', endpoint, params, signed=True)
            
            if not result:
                return None
            
            status_map = {
                'NEW': OrderStatus.PENDING,
                'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
                'FILLED': OrderStatus.FILLED,
                'CANCELED': OrderStatus.CANCELLED,
                'REJECTED': OrderStatus.REJECTED,
                'EXPIRED': OrderStatus.CANCELLED
            }
            
            return OrderResponse(
                order_id=str(result.get('orderId', '')),
                status=status_map.get(result.get('status', 'NEW'), OrderStatus.PENDING),
                filled_quantity=float(result.get('executedQty', 0)),
                average_fill_price=float(result.get('avgPrice', 0)) if self.futures else float(result.get('price', 0)),
                commission=0.0,
                timestamp=datetime.now(),
                metadata={'binance_status': result.get('status', '')}
            )
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected:
            return {}
        
        # Check cache
        if self._account_cache and self._account_cache_time:
            try:
                age = (datetime.now() - self._account_cache_time).total_seconds()
                if age < self._cache_ttl:
                    return self._account_cache

                if self.futures:
                    account = await self._request('GET', '/fapi/v2/account', signed=True)
                    if not account:
                        return {}

                    info = {
                        'balance': float(account.get('totalWalletBalance', 0)),
                        'equity': float(account.get('totalMarginBalance', 0)),
                        'available_balance': float(account.get('availableBalance', 0)),
                        'margin': float(account.get('totalInitialMargin', 0)),
                        'unrealized_pnl': float(account.get('totalUnrealizedProfit', 0)),
                        'margin_ratio': float(account.get('totalMaintMargin', 0)) / float(account.get('totalMarginBalance', 1)) * 100,
                        'currency': 'USDT',
                        'can_trade': account.get('canTrade', False)
                    }
                else:
                    account = await self._request('GET', '/api/v3/account', signed=True)
                    if not account:
                        return {}

                    # Calculate total in USDT
                    total_usdt = 0
                    for balance in account.get('balances', []):
                        free = float(balance.get('free', 0))
                        locked = float(balance.get('locked', 0))
                        total = free + locked

                        if total > 0:
                            if balance['asset'] == 'USDT':
                                total_usdt += total
                            else:
                                # Get price
                                ticker = await self._request('GET', '/api/v3/ticker/price', {'symbol': f"{balance['asset']}USDT"})
                                if ticker:
                                    total_usdt += total * float(ticker.get('price', 0))

                    info = {
                        'balance': total_usdt,
                        'equity': total_usdt,
                        'available_balance': total_usdt,
                        'margin': 0,
                        'unrealized_pnl': 0,
                        'currency': 'USDT',
                        'can_trade': account.get('canTrade', False)
                    }

                self._account_cache = info
                self._account_cache_time = datetime.now()

                return info

            except Exception as e:
                logger.error(f"Failed to get account info: {e}")
                return {}

    async def get_account_equity(self) -> float:
        """Get current account equity"""
        info = await self.get_account_info()
        return info.get('equity', 0.0)
    
    async def close_position(self, symbol: str) -> bool:
        """Close position for a symbol"""
        if not self.connected:
            return False
        try:
        
            position = await self.get_position(symbol)
            if not position:
                return True  # No position to close
            
            # Place opposite order
            side = OrderSide.SELL if position.side == 'buy' else OrderSide.BUY
            
            response = await self.place_order(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                reduceOnly=True if self.futures else False
            )
            
            return response is not None and response.success
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    async def close_all_positions(self) -> bool:
        """Close all positions"""
        if not self.connected:
            return False
        try:
        
            positions = await self.get_positions()
            success = True
            
            for pos in positions:
                if not await self.close_position(pos.symbol):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return False
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get ticker for a symbol"""
        if not self.connected:
            return None
        try:
        
            endpoint = '/fapi/v1/ticker/24hr' if self.futures else '/api/v3/ticker/24hr'
            result = await self._request('GET', endpoint, {'symbol': symbol})
            
            if result:
                return {
                    'symbol': result.get('symbol'),
                    'price': float(result.get('lastPrice', 0)),
                    'bid': float(result.get('bidPrice', 0)),
                    'ask': float(result.get('askPrice', 0)),
                    'volume': float(result.get('volume', 0)),
                    'change_24h': float(result.get('priceChangePercent', 0))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            return None
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book"""
        if not self.connected:
            return None
        try:
        
            endpoint = '/fapi/v1/depth' if self.futures else '/api/v3/depth'
            result = await self._request('GET', endpoint, {'symbol': symbol, 'limit': limit})
            
            if result:
                return {
                    'bids': [[float(p), float(q)] for p, q in result.get('bids', [])],
                    'asks': [[float(p), float(q)] for p, q in result.get('asks', [])],
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get orderbook: {e}")
            return None
    
    # WebSocket methods
    async def start_websocket(self, streams: List[str], callback: Callable):
        """Start WebSocket connection"""
        if not AIOHTTP_AVAILABLE:
            return
        
        self.ws_running = True
        stream_url = f"{self.ws_url}/{'/'.join(streams)}"
        
        while self.ws_running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(stream_url) as ws:
                        self.ws_connection = ws
                        logger.info(f"WebSocket connected: {streams}")
                        
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await callback(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error(f"WebSocket error: {ws.exception()}")
                                break
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self.ws_running:
                    await asyncio.sleep(5)  # Reconnect delay
    
    async def stop_websocket(self):
        """Stop WebSocket connection"""
        self.ws_running = False
        if self.ws_connection:
            await self.ws_connection.close()


# Export
__all__ = [
    'BinanceBrokerAdapter',
    'BinanceEndpoints',
    'RateLimiter'
]
