"""
Binance broker implementation for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import websockets
import asyncio
from .broker_interface import (
    BrokerInterface,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position
)

# Set up logger
logger = logging.getLogger(__name__)


class BinanceBroker(BrokerInterface):
    """
    Binance-specific broker implementation.
    Handles Binance API quirks and features.
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True
    ):
        # Set appropriate base URL
        base_url = (
            "https://testnet.binance.vision/api"
            if testnet else
            "https://api.binance.com/api"
        )
        
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            testnet=testnet
        )
        
        # WebSocket connection
        self.ws = None
        self.ws_connected = False
        self.ws_subscriptions = set()
        
        # Order book cache
        self.order_books = {}
        
        # Account listeners
        self.account_listeners = []
        
        logger.info("✅ Binance Broker initialized")
    
    async def connect(self):
        """Connect to Binance API and WebSocket."""
        await super().connect()
        
        try:
            # Connect WebSocket
            await self._ws_connect()
            
            # Subscribe to user data stream
            await self._start_user_stream()
            
            logger.info("✅ WebSocket connected")
            
        except Exception as e:
            logger.error(f"❌ WebSocket error: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from Binance."""
        # Close WebSocket
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.ws_connected = False
        
        # Close REST session
        await super().disconnect()
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Place order on Binance."""
        # Convert order type
        binance_type = self._convert_order_type(type)
        
        # Add Binance-specific parameters
        params = {
            'symbol': symbol,
            'side': side.value,
            'type': binance_type,
            'quantity': self._format_quantity(quantity),
            'newClientOrderId': self._generate_order_id(),
            'timeInForce': 'GTC'
        }
        
        if price:
            params['price'] = self._format_price(price)
        if stop_price:
            params['stopPrice'] = self._format_price(stop_price)
        
        # Place order
        order = await super().place_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
        
        return order
    
    async def get_exchange_info(self) -> Dict:
        """Get Binance exchange information."""
        try:
            endpoint = "/v1/exchangeInfo"
            method = "GET"
            
            return await self._send_request(method, endpoint)
            
        except Exception as e:
            logger.error(f"❌ Exchange info error: {str(e)}")
            return {}
    
    async def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information."""
        try:
            info = await self.get_exchange_info()
            
            for sym in info['symbols']:
                if sym['symbol'] == symbol:
                    return sym
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Symbol info error: {str(e)}")
            return {}
    
    async def get_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> Dict:
        """Get order book for symbol."""
        try:
            endpoint = "/v1/depth"
            method = "GET"
            
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            return await self._send_request(
                method,
                endpoint,
                params
            )
            
        except Exception as e:
            logger.error(f"❌ Order book error: {str(e)}")
            return {}
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 500
    ) -> List[Dict]:
        """Get recent trades for symbol."""
        try:
            endpoint = "/v1/trades"
            method = "GET"
            
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            return await self._send_request(
                method,
                endpoint,
                params
            )
            
        except Exception as e:
            logger.error(f"❌ Recent trades error: {str(e)}")
            return []
    
    async def _ws_connect(self):
        """Connect to Binance WebSocket."""
        ws_url = (
            "wss://testnet.binance.vision/ws"
            if self.testnet else
            "wss://stream.binance.com:9443/ws"
        )
        
        self.ws = await websockets.connect(ws_url)
        self.ws_connected = True
        
        # Start message handler
        asyncio.create_task(self._ws_message_handler())
    
    async def _start_user_stream(self):
        """Start user data stream."""
        try:
            # Get listen key
            endpoint = "/v1/userDataStream"
            method = "POST"
            
            response = await self._send_request(method, endpoint)
            listen_key = response['listenKey']
            
            # Subscribe to user stream
            await self._ws_subscribe([
                f"{listen_key}@userData"
            ])
            
            logger.info("✅ User data stream started")
            
        except Exception as e:
            logger.error(f"❌ User stream error: {str(e)}")
            raise
    
    async def _ws_subscribe(self, channels: List[str]):
        """Subscribe to WebSocket channels."""
        if not self.ws_connected:
            raise ValueError("WebSocket not connected")
        
        # Prepare subscription message
        message = {
            'method': 'SUBSCRIBE',
            'params': channels,
            'id': len(self.ws_subscriptions)
        }
        
        # Send subscription
        await self.ws.send(json.dumps(message))
        
        # Add to subscriptions
        self.ws_subscriptions.update(channels)
    
    async def _ws_message_handler(self):
        """Handle WebSocket messages."""
        while self.ws_connected:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Handle different message types
                if 'e' in data:  # Event type
                    event_type = data['e']
                    
                    if event_type == 'executionReport':
                        await self._handle_execution_report(data)
                    elif event_type == 'outboundAccountPosition':
                        await self._handle_account_update(data)
                    elif event_type == 'balanceUpdate':
                        await self._handle_balance_update(data)
                
            except websockets.ConnectionClosed:
                logger.warning("⚠️ WebSocket connection closed")
                self.ws_connected = False
                break
                
    async def _handle_execution_report(self, data: Dict):
        """Handle order execution reports."""
        order_id = data['c']  # Client order ID
        
        if order_id in self.orders:
            order = self.orders[order_id]
            
            # Update order status
            order.status = self._convert_order_status(data['X'])
            order.filled_quantity = float(data['l'])
            order.filled_price = float(data['L'])
            order.commission = float(data['n'])
            
            logger.info(f"📊 Order update: {order_id}")
            logger.info(f"   Status: {order.status.value}")
            logger.info(f"   Filled: {order.filled_quantity}")
    
    async def _handle_account_update(self, data: Dict):
        """Handle account position updates."""
        # Update positions
        for pos in data['B']:
            symbol = pos['a']
            free = float(pos['f'])
            locked = float(pos['l'])
            
            if symbol in self.positions:
                position = self.positions[symbol]
                position.quantity = free + locked
                position.timestamp = datetime.now()
        
        # Notify listeners
        for listener in self.account_listeners:
            await listener(self.positions)
    
    async def _handle_balance_update(self, data: Dict):
        """Handle balance updates."""
        # Implement balance update handling
        pass
    
    def _convert_order_type(self, type: OrderType) -> str:
        """Convert order type to Binance format."""
        mapping = {
            OrderType.MARKET: 'MARKET',
            OrderType.LIMIT: 'LIMIT',
            OrderType.STOP: 'STOP_LOSS',
            OrderType.STOP_LIMIT: 'STOP_LOSS_LIMIT'
        }
        return mapping[type]
    
    def _convert_order_status(self, status: str) -> OrderStatus:
        """Convert Binance order status."""
        mapping = {
            'NEW': OrderStatus.PENDING,
            'PARTIALLY_FILLED': OrderStatus.OPEN,
            'FILLED': OrderStatus.FILLED,
            'CANCELED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED,
            'EXPIRED': OrderStatus.EXPIRED
        }
        return mapping.get(status, OrderStatus.PENDING)
    
    def _format_quantity(self, quantity: float) -> str:
        """Format quantity according to Binance rules."""
        return f"{quantity:.8f}".rstrip('0').rstrip('.')
    
    def _format_price(self, price: float) -> str:
        """Format price according to Binance rules."""
        return f"{price:.8f}".rstrip('0').rstrip('.')
    
    def add_account_listener(self, listener: callable):
        """Add account update listener."""
        self.account_listeners.append(listener)
    
    def remove_account_listener(self, listener: callable):
        """Remove account update listener."""
        if listener in self.account_listeners:
            self.account_listeners.remove(listener)
