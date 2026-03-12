"""
Binance Exchange Connector
Real-time data and trading for Binance
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
import json
import hmac
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .base_connector import (
    BaseConnector, ConnectionStatus, MarketData, 
    OrderBook, Trade, Ticker
)

logger = logging.getLogger(__name__)

class BinanceConnector(BaseConnector):
    """
    Binance exchange connector with WebSocket support
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Binance-specific endpoints
        if self.testnet:
            self.rest_url = "https://testnet.binance.vision/api/v3"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.rest_url = "https://api.binance.com/api/v3"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        # WebSocket streams
        self.subscribed_streams = []
        self.stream_buffer = {}
        
    async def connect(self):
        """Connect to Binance"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test connection
            async with self.session.get(f"{self.rest_url}/ping") as response:
                if response.status == 200:
                    logger.info("Connected to Binance REST API")
            
            # Connect WebSocket
            await self._connect_websocket()
            
            self.status = ConnectionStatus.CONNECTED
            
            # Start heartbeat
            asyncio.create_task(self.heartbeat())
            
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            self.status = ConnectionStatus.ERROR
            raise
    
    async def _connect_websocket(self):
        """Connect to Binance WebSocket"""
        try:
            self.ws_connection = await websockets.connect(self.ws_url)
            
            # Start message handler
            asyncio.create_task(self._handle_ws_messages())
            
            logger.info("Connected to Binance WebSocket")
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def _handle_ws_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws_connection:
                data = json.loads(message)
                await self._process_ws_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self.reconnect()
        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")
    
    async def _process_ws_message(self, data: Dict):
        """Process WebSocket message"""
        if 'e' in data:  # Event type
            event_type = data['e']
            
            if event_type == 'trade':
                await self._process_trade(data)
            elif event_type == 'depthUpdate':
                await self._process_order_book(data)
            elif event_type == '24hrTicker':
                await self._process_ticker(data)
            elif event_type == 'kline':
                await self._process_kline(data)
    
    async def disconnect(self):
        """Disconnect from Binance"""
        try:
            if self.ws_connection:
                await self.ws_connection.close()
            
            if self.session:
                await self.session.close()
            
            self.status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from Binance")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    async def subscribe_market_data(self, symbols: List[str]):
        """Subscribe to market data streams"""
        streams = []
        
        for symbol in symbols:
            normalized = self.normalize_symbol(symbol).lower()
            streams.append(f"{normalized}@kline_1m")
            streams.append(f"{normalized}@ticker")
        
        await self._subscribe_streams(streams)
    
    async def subscribe_order_book(self, symbols: List[str], depth: int = 10):
        """Subscribe to order book updates"""
        streams = []
        
        for symbol in symbols:
            normalized = self.normalize_symbol(symbol).lower()
            streams.append(f"{normalized}@depth{depth}")
        
        await self._subscribe_streams(streams)
    
    async def subscribe_trades(self, symbols: List[str]):
        """Subscribe to trade streams"""
        streams = []
        
        for symbol in symbols:
            normalized = self.normalize_symbol(symbol).lower()
            streams.append(f"{normalized}@trade")
        
        await self._subscribe_streams(streams)
    
    async def _subscribe_streams(self, streams: List[str]):
        """Subscribe to WebSocket streams"""
        if not self.ws_connection:
            await self._connect_websocket()
        
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": len(self.subscribed_streams)
        }
        
        await self.ws_connection.send(json.dumps(subscribe_message))
        self.subscribed_streams.extend(streams)
        
        logger.info(f"Subscribed to streams: {streams}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker"""
        normalized = self.normalize_symbol(symbol)
        
        async with self.session.get(
            f"{self.rest_url}/ticker/24hr",
            params={'symbol': normalized}
        ) as response:
            data = await response.json()
            
            return Ticker(
                symbol=symbol,
                exchange=self.exchange_name,
                timestamp=datetime.now(),
                bid=float(data.get('bidPrice', 0)),
                ask=float(data.get('askPrice', 0)),
                last=float(data.get('lastPrice', 0)),
                volume_24h=float(data.get('volume', 0)),
                change_24h=float(data.get('priceChangePercent', 0))
            )
    
    async def place_order(self, order: Dict) -> Dict:
        """Place an order on Binance"""
        # Prepare order parameters
        params = {
            'symbol': self.normalize_symbol(order['symbol']),
            'side': order['side'].upper(),
            'type': order.get('type', 'LIMIT').upper(),
            'timeInForce': order.get('time_in_force', 'GTC'),
            'quantity': order['quantity']
        }
        
        if params['type'] == 'LIMIT':
            params['price'] = order['price']
        
        # Add timestamp and signature
        params['timestamp'] = int(datetime.now().timestamp() * 1000)
        params['signature'] = self._generate_signature(params)
        
        # Send order
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with self.session.post(
            f"{self.rest_url}/order",
            headers=headers,
            params=params
        ) as response:
            result = await response.json()
            
            if response.status == 200:
                logger.info(f"Order placed: {result}")
                return result
            else:
                logger.error(f"Order failed: {result}")
                raise Exception(f"Order failed: {result}")
    
    async def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order"""
        params = {
            'orderId': order_id,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        if symbol:
            params['symbol'] = self.normalize_symbol(symbol)
        
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with self.session.delete(
            f"{self.rest_url}/order",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                logger.info(f"Order {order_id} cancelled")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}")
                return False
    
    async def get_order_status(self, order_id: str, symbol: str = None) -> Dict:
        """Get order status"""
        params = {
            'orderId': order_id,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        if symbol:
            params['symbol'] = self.normalize_symbol(symbol)
        
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with self.session.get(
            f"{self.rest_url}/order",
            headers=headers,
            params=params
        ) as response:
            return await response.json()
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        params = {
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with self.session.get(
            f"{self.rest_url}/account",
            headers=headers,
            params=params
        ) as response:
            data = await response.json()
            
            # Extract non-zero balances
            positions = []
            for balance in data.get('balances', []):
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                
                if free > 0 or locked > 0:
                    positions.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })
            
            return positions
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        params = {
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with self.session.get(
            f"{self.rest_url}/account",
            headers=headers,
            params=params
        ) as response:
            data = await response.json()
            
            return {
                'balances': data.get('balances', []),
                'total_btc': data.get('totalAssetOfBtc', 0)
            }
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate signature for authenticated requests"""
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _process_trade(self, data: Dict):
        """Process trade data from WebSocket"""
        trade = Trade(
            symbol=data['s'],
            exchange=self.exchange_name,
            timestamp=datetime.fromtimestamp(data['T'] / 1000),
            price=float(data['p']),
            size=float(data['q']),
            side='buy' if data['m'] else 'sell',
            trade_id=str(data['t'])
        )
        
        await self.emit_event('trade', trade)
    
    async def _process_order_book(self, data: Dict):
        """Process order book update"""
        order_book = OrderBook(
            symbol=data['s'],
            exchange=self.exchange_name,
            timestamp=datetime.fromtimestamp(data['E'] / 1000),
            bids=[(float(p), float(q)) for p, q in data.get('b', [])],
            asks=[(float(p), float(q)) for p, q in data.get('a', [])]
        )
        
        await self.emit_event('order_book', order_book)
    
    async def _process_ticker(self, data: Dict):
        """Process ticker update"""
        ticker = Ticker(
            symbol=data['s'],
            exchange=self.exchange_name,
            timestamp=datetime.fromtimestamp(data['E'] / 1000),
            bid=float(data.get('b', 0)),
            ask=float(data.get('a', 0)),
            last=float(data.get('c', 0)),
            volume_24h=float(data.get('v', 0)),
            change_24h=float(data.get('P', 0))
        )
        
        await self.emit_event('ticker', ticker)
    
    async def _process_kline(self, data: Dict):
        """Process kline/candlestick data"""
        kline = data['k']
        
        market_data = MarketData(
            symbol=data['s'],
            exchange=self.exchange_name,
            timestamp=datetime.fromtimestamp(kline['t'] / 1000),
            price=float(kline['c']),
            bid=0,  # Not available in kline
            ask=0,  # Not available in kline
            volume=float(kline['v']),
            open=float(kline['o']),
            high=float(kline['h']),
            low=float(kline['l']),
            close=float(kline['c'])
        )
        
        await self.emit_event('market_data', market_data)
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Binance format"""
        # Binance uses format like BTCUSDT (no separator)
        return symbol.replace('/', '').replace('-', '')
