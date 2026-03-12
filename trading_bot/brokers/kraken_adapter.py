"""
Kraken Exchange Adapter
=======================

Production-ready adapter for Kraken cryptocurrency exchange.
Supports spot trading, margin trading, and futures.
"""

import asyncio
import hashlib
import hmac
import base64
import time
import logging
import urllib.parse
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import aiohttp
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - install with: pip install aiohttp")


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop-loss"
    TAKE_PROFIT = "take-profit"
    STOP_LOSS_LIMIT = "stop-loss-limit"
    TAKE_PROFIT_LIMIT = "take-profit-limit"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"


@dataclass
class KrakenPosition:
    """Kraken position"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    margin: float = 0.0
    leverage: float = 1.0


@dataclass
class KrakenOrder:
    """Kraken order"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    status: OrderStatus
    filled_quantity: float
    average_price: float
    fee: float
    timestamp: datetime


class KrakenAdapter:
    """
    Kraken Exchange Adapter
    
    Features:
    - Spot trading
    - Margin trading
    - Real-time market data
    - Order management
    - Position tracking
    """
    
    BASE_URL = "https://api.kraken.com"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.api_secret = self.config.get('api_secret', '')
        self.connected = False
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Symbol mapping (Kraken uses different naming)
        self.symbol_map = {
            'BTCUSD': 'XXBTZUSD',
            'ETHUSD': 'XETHZUSD',
            'BTCEUR': 'XXBTZEUR',
            'ETHEUR': 'XETHZEUR',
            'XRPUSD': 'XXRPZUSD',
            'LTCUSD': 'XLTCZUSD',
            'ADAUSD': 'ADAUSD',
            'DOTUSD': 'DOTUSD',
            'SOLUSD': 'SOLUSD',
        }
        
        # Reverse mapping
        self.reverse_symbol_map = {v: k for k, v in self.symbol_map.items()}
    
    def _get_kraken_symbol(self, symbol: str) -> str:
        """Convert standard symbol to Kraken format"""
        return self.symbol_map.get(symbol.upper(), symbol.upper())
    
    def _get_standard_symbol(self, kraken_symbol: str) -> str:
        """Convert Kraken symbol to standard format"""
        return self.reverse_symbol_map.get(kraken_symbol, kraken_symbol)
    
    def _generate_signature(self, urlpath: str, data: Dict) -> str:
        """Generate API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        mac = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        
        return base64.b64encode(mac.digest()).decode()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _public_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make public API request"""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp not available")
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/0/public/{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if data.get('error'):
                    raise Exception(f"Kraken API error: {data['error']}")
                
                return data.get('result', {})
        except Exception as e:
            logger.error(f"Public request failed: {e}")
            raise
    
    async def _private_request(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make private API request"""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp not available")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials required for private requests")
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/0/private/{endpoint}"
        urlpath = f"/0/private/{endpoint}"
        
        data = data or {}
        data['nonce'] = int(time.time() * 1000)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._generate_signature(urlpath, data)
        }
        
        try:
            async with session.post(url, data=data, headers=headers) as response:
                result = await response.json()
                
                if result.get('error'):
                    raise Exception(f"Kraken API error: {result['error']}")
                
                return result.get('result', {})
        except Exception as e:
            logger.error(f"Private request failed: {e}")
            raise
    
    async def connect(self) -> bool:
        """Connect to Kraken"""
        try:
            # Test connection with public endpoint
            server_time = await self._public_request('Time')
            
            if self.api_key and self.api_secret:
                # Test private endpoint
                balance = await self._private_request('Balance')
                logger.info(f"Kraken connected with {len(balance)} assets")
            else:
                logger.info("Kraken connected (public only)")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Kraken connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Kraken"""
        if self._session and not self._session.closed:
            await self._session.close()
        self.connected = False
        logger.info("Kraken disconnected")
        return True
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get ticker data for a symbol"""
        try:
            kraken_symbol = self._get_kraken_symbol(symbol)
            result = await self._public_request('Ticker', {'pair': kraken_symbol})
            
            if result:
                ticker_key = list(result.keys())[0]
                ticker = result[ticker_key]
                
                return {
                    'symbol': symbol,
                    'bid': float(ticker['b'][0]),
                    'ask': float(ticker['a'][0]),
                    'last': float(ticker['c'][0]),
                    'volume': float(ticker['v'][1]),  # 24h volume
                    'high': float(ticker['h'][1]),    # 24h high
                    'low': float(ticker['l'][1]),     # 24h low
                    'vwap': float(ticker['p'][1]),    # 24h VWAP
                    'trades': int(ticker['t'][1]),    # 24h trades
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            return None
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        """Get order book for a symbol"""
        try:
            kraken_symbol = self._get_kraken_symbol(symbol)
            result = await self._public_request('Depth', {
                'pair': kraken_symbol,
                'count': depth
            })
            
            if result:
                book_key = list(result.keys())[0]
                book = result[book_key]
                
                return {
                    'symbol': symbol,
                    'bids': [[float(b[0]), float(b[1])] for b in book['bids']],
                    'asks': [[float(a[0]), float(a[1])] for a in book['asks']],
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get order book: {e}")
            return None
    
    async def get_ohlcv(
        self,
        symbol: str,
        interval: int = 60,  # minutes
        since: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """Get OHLCV data"""
        try:
            kraken_symbol = self._get_kraken_symbol(symbol)
            params = {
                'pair': kraken_symbol,
                'interval': interval
            }
            
            if since:
                params['since'] = since
            
            result = await self._public_request('OHLC', params)
            
            if result:
                ohlc_key = list(result.keys())[0]
                if ohlc_key != 'last':
                    ohlc_data = result[ohlc_key]
                    
                    return [
                        {
                            'timestamp': datetime.fromtimestamp(candle[0]),
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'vwap': float(candle[5]),
                            'volume': float(candle[6]),
                            'count': int(candle[7])
                        }
                        for candle in ohlc_data
                    ]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get OHLCV: {e}")
            return None
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            result = await self._private_request('Balance')
            
            return {
                asset: float(balance)
                for asset, balance in result.items()
                if float(balance) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            balance = await self.get_balance()
            trade_balance = await self._private_request('TradeBalance')
            
            return {
                'balance': balance,
                'equity': float(trade_balance.get('e', 0)),
                'margin': float(trade_balance.get('m', 0)),
                'free_margin': float(trade_balance.get('mf', 0)),
                'unrealized_pnl': float(trade_balance.get('n', 0)),
                'cost_basis': float(trade_balance.get('c', 0)),
                'floating_valuation': float(trade_balance.get('v', 0)),
            }
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        leverage: Optional[int] = None,
        **kwargs
    ) -> Optional[KrakenOrder]:
        """Place an order"""
        try:
            kraken_symbol = self._get_kraken_symbol(symbol)
            
            data = {
                'pair': kraken_symbol,
                'type': side.value,
                'ordertype': order_type.value,
                'volume': str(quantity),
            }
            
            if price and order_type in [OrderType.LIMIT, OrderType.STOP_LOSS_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
                data['price'] = str(price)
            
            if stop_price and order_type in [OrderType.STOP_LOSS, OrderType.STOP_LOSS_LIMIT]:
                data['price'] = str(stop_price)
            
            if leverage:
                data['leverage'] = str(leverage)
            
            # Optional parameters
            if kwargs.get('validate_only'):
                data['validate'] = 'true'
            
            if kwargs.get('post_only'):
                data['oflags'] = 'post'
            
            result = await self._private_request('AddOrder', data)
            
            if result:
                order_ids = result.get('txid', [])
                if order_ids:
                    order_id = order_ids[0]
                    
                    logger.info(f"Order placed: {order_id} - {symbol} {side.value} {quantity}")
                    
                    return KrakenOrder(
                        order_id=order_id,
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        quantity=quantity,
                        price=price,
                        status=OrderStatus.PENDING,
                        filled_quantity=0,
                        average_price=0,
                        fee=0,
                        timestamp=datetime.now()
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            result = await self._private_request('CancelOrder', {'txid': order_id})
            
            if result.get('count', 0) > 0:
                logger.info(f"Order cancelled: {order_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return False
    
    async def cancel_all_orders(self) -> int:
        """Cancel all open orders"""
        try:
            result = await self._private_request('CancelAll')
            count = result.get('count', 0)
            logger.info(f"Cancelled {count} orders")
            return count
        except Exception as e:
            logger.error(f"Cancel all orders failed: {e}")
            return 0
    
    async def get_order_status(self, order_id: str) -> Optional[KrakenOrder]:
        """Get order status"""
        try:
            result = await self._private_request('QueryOrders', {'txid': order_id})
            
            if result and order_id in result:
                order = result[order_id]
                
                status_map = {
                    'pending': OrderStatus.PENDING,
                    'open': OrderStatus.OPEN,
                    'closed': OrderStatus.CLOSED,
                    'canceled': OrderStatus.CANCELED,
                    'expired': OrderStatus.EXPIRED
                }
                
                return KrakenOrder(
                    order_id=order_id,
                    symbol=self._get_standard_symbol(order['descr']['pair']),
                    side=OrderSide.BUY if order['descr']['type'] == 'buy' else OrderSide.SELL,
                    order_type=OrderType(order['descr']['ordertype']),
                    quantity=float(order['vol']),
                    price=float(order['descr']['price']) if order['descr']['price'] else None,
                    status=status_map.get(order['status'], OrderStatus.PENDING),
                    filled_quantity=float(order['vol_exec']),
                    average_price=float(order['price']) if order['price'] else 0,
                    fee=float(order['fee']),
                    timestamp=datetime.fromtimestamp(order['opentm'])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    async def get_open_orders(self) -> List[KrakenOrder]:
        """Get all open orders"""
        try:
            result = await self._private_request('OpenOrders')
            
            orders = []
            for order_id, order in result.get('open', {}).items():
                orders.append(KrakenOrder(
                    order_id=order_id,
                    symbol=self._get_standard_symbol(order['descr']['pair']),
                    side=OrderSide.BUY if order['descr']['type'] == 'buy' else OrderSide.SELL,
                    order_type=OrderType(order['descr']['ordertype']),
                    quantity=float(order['vol']),
                    price=float(order['descr']['price']) if order['descr']['price'] else None,
                    status=OrderStatus.OPEN,
                    filled_quantity=float(order['vol_exec']),
                    average_price=float(order['price']) if order['price'] else 0,
                    fee=float(order['fee']),
                    timestamp=datetime.fromtimestamp(order['opentm'])
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    async def get_positions(self) -> List[KrakenPosition]:
        """Get open positions (margin trading)"""
        try:
            result = await self._private_request('OpenPositions')
            
            positions = []
            for pos_id, pos in result.items():
                positions.append(KrakenPosition(
                    symbol=self._get_standard_symbol(pos['pair']),
                    side='buy' if pos['type'] == 'buy' else 'sell',
                    quantity=float(pos['vol']),
                    entry_price=float(pos['cost']) / float(pos['vol']),
                    current_price=float(pos['value']) / float(pos['vol']),
                    unrealized_pnl=float(pos['net']),
                    margin=float(pos['margin']),
                    leverage=float(pos.get('leverage', 1))
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_trade_history(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """Get trade history"""
        try:
            data = {'ofs': offset}
            
            if start:
                data['start'] = start
            if end:
                data['end'] = end
            
            result = await self._private_request('TradesHistory', data)
            
            trades = []
            for trade_id, trade in result.get('trades', {}).items():
                trades.append({
                    'trade_id': trade_id,
                    'order_id': trade['ordertxid'],
                    'symbol': self._get_standard_symbol(trade['pair']),
                    'side': trade['type'],
                    'price': float(trade['price']),
                    'quantity': float(trade['vol']),
                    'cost': float(trade['cost']),
                    'fee': float(trade['fee']),
                    'timestamp': datetime.fromtimestamp(trade['time'])
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []


# Export
__all__ = [
    'KrakenAdapter',
    'KrakenPosition',
    'KrakenOrder',
    'OrderSide',
    'OrderType',
    'OrderStatus'
]
