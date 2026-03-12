"""
Alpaca Broker Adapter

Real implementation for Alpaca trading API:
- Paper and live trading support
- Real-time market data
- Position management
- Order execution
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import base classes
try:
    from trading_bot.brokers.broker_adapter import (
        BrokerAdapter, Position, OrderResponse, OrderStatus, OrderSide, OrderType
    )
except ImportError:
    pass
try:
    # Define locally if import fails
    from enum import Enum
    
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

# Alpaca SDK imports
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest, LimitOrderRequest, StopOrderRequest,
        GetOrdersRequest, ClosePositionRequest
    )
    from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce, OrderType as AlpacaOrderType
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("Alpaca SDK not available. Install with: pip install alpaca-py")


class AlpacaBrokerAdapter(BrokerAdapter):
    """
    Alpaca broker adapter for paper and live trading.
    
    Features:
    - Paper trading (free, no risk)
    - Live trading (real money)
    - Real-time quotes
    - Historical data
    - Position management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False
        
        # API credentials
        self.api_key = self.config.get('api_key', '')
        self.api_secret = self.config.get('api_secret', '')
        self.paper = self.config.get('paper', True)  # Default to paper trading
        
        # Clients
        self.trading_client = None
        self.data_client = None
        
        # Cache
        self._account_cache = None
        self._account_cache_time = None
        self._cache_ttl = 5  # seconds
        
        if not ALPACA_AVAILABLE:
            logger.error("Alpaca SDK not installed")
    
    async def connect(self) -> bool:
        """Connect to Alpaca"""
        if not ALPACA_AVAILABLE:
            logger.error("Alpaca SDK not available")
            return False
        
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca API credentials not provided")
            return False
        try:
        
            # Initialize trading client
            self.trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.api_secret,
                paper=self.paper
            )
            
            # Initialize data client
            self.data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret
            )
            
            # Test connection by getting account
            account = self.trading_client.get_account()
            
            self.connected = True
            mode = "PAPER" if self.paper else "LIVE"
            logger.info(f"Alpaca connected ({mode}): Account {account.account_number}")
            logger.info(f"  Equity: ${float(account.equity):,.2f}")
            logger.info(f"  Buying Power: ${float(account.buying_power):,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Alpaca connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca"""
        self.connected = False
        self.trading_client = None
        self.data_client = None
        logger.info("Alpaca disconnected")
        return True
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not self.connected or not self.trading_client:
            return []
        try:
        
            alpaca_positions = self.trading_client.get_all_positions()
            
            positions = []
            for pos in alpaca_positions:
                positions.append(Position(
                    symbol=pos.symbol,
                    side='buy' if pos.side == 'long' else 'sell',
                    quantity=float(pos.qty),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    unrealized_pnl=float(pos.unrealized_pl),
                    realized_pnl=0.0,
                    timestamp=datetime.now()
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        if not self.connected or not self.trading_client:
            return None
        try:
        
            pos = self.trading_client.get_open_position(symbol)
            
            return Position(
                symbol=pos.symbol,
                side='buy' if pos.side == 'long' else 'sell',
                quantity=float(pos.qty),
                entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                unrealized_pnl=float(pos.unrealized_pl),
                realized_pnl=0.0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            # Position doesn't exist
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
        if not self.connected or not self.trading_client:
            logger.error("Not connected to Alpaca")
            return None
        try:
        
            # Convert side
            alpaca_side = AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL
            
            # Get time in force
            tif = kwargs.get('time_in_force', TimeInForce.DAY)
            
            # Create order request based on type
            if order_type == OrderType.MARKET:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif
                )
            elif order_type == OrderType.LIMIT:
                if price is None:
                    logger.error("Limit order requires price")
                    return None
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    limit_price=price
                )
            elif order_type == OrderType.STOP:
                if stop_price is None:
                    logger.error("Stop order requires stop_price")
                    return None
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    stop_price=stop_price
                )
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return None
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            
            # Convert status
            status_map = {
                'new': OrderStatus.PENDING,
                'accepted': OrderStatus.PENDING,
                'pending_new': OrderStatus.PENDING,
                'filled': OrderStatus.FILLED,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'canceled': OrderStatus.CANCELLED,
                'rejected': OrderStatus.REJECTED,
                'expired': OrderStatus.CANCELLED
            }
            
            status = status_map.get(order.status.value, OrderStatus.PENDING)
            
            logger.info(f"Order placed: {order.id} - {symbol} {side.value} {quantity} @ {order_type.value}")
            
            return OrderResponse(
                order_id=str(order.id),
                status=status,
                filled_quantity=float(order.filled_qty) if order.filled_qty else 0,
                average_fill_price=float(order.filled_avg_price) if order.filled_avg_price else 0,
                commission=0.0,  # Alpaca is commission-free
                timestamp=datetime.now(),
                metadata={
                    'alpaca_status': order.status.value,
                    'client_order_id': order.client_order_id
                }
            )
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if not self.connected or not self.trading_client:
            return False
        try:
        
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status"""
        if not self.connected or not self.trading_client:
            return None
        try:
        
            order = self.trading_client.get_order_by_id(order_id)
            
            status_map = {
                'new': OrderStatus.PENDING,
                'accepted': OrderStatus.PENDING,
                'pending_new': OrderStatus.PENDING,
                'filled': OrderStatus.FILLED,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'canceled': OrderStatus.CANCELLED,
                'rejected': OrderStatus.REJECTED,
                'expired': OrderStatus.CANCELLED
            }
            
            status = status_map.get(order.status.value, OrderStatus.PENDING)
            
            return OrderResponse(
                order_id=str(order.id),
                status=status,
                filled_quantity=float(order.filled_qty) if order.filled_qty else 0,
                average_fill_price=float(order.filled_avg_price) if order.filled_avg_price else 0,
                commission=0.0,
                timestamp=datetime.now(),
                metadata={'alpaca_status': order.status.value}
            )
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.connected or not self.trading_client:
            return {}
        
        # Check cache
        if self._account_cache and self._account_cache_time:
            try:
                age = (datetime.now() - self._account_cache_time).total_seconds()
                if age < self._cache_ttl:
                    return self._account_cache

                account = self.trading_client.get_account()

                info = {
                    'account_number': account.account_number,
                    'balance': float(account.cash),
                    'equity': float(account.equity),
                    'buying_power': float(account.buying_power),
                    'margin': float(account.initial_margin) if account.initial_margin else 0,
                    'free_margin': float(account.buying_power),
                    'profit': float(account.equity) - float(account.last_equity),
                    'currency': 'USD',
                    'leverage': 1,  # Alpaca doesn't use leverage for stocks
                    'status': account.status.value,
                    'pattern_day_trader': account.pattern_day_trader,
                    'trading_blocked': account.trading_blocked,
                    'daytrade_count': account.daytrade_count
                }

                # Update cache
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
        if not self.connected or not self.trading_client:
            return False
        try:
        
            self.trading_client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    async def close_all_positions(self) -> bool:
        """Close all positions"""
        if not self.connected or not self.trading_client:
            return False
        try:
        
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info("All positions closed")
            return True
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            return False
    
    async def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote for a symbol"""
        if not self.connected or not self.data_client:
            return None
        try:
        
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    'symbol': symbol,
                    'bid': float(quote.bid_price),
                    'ask': float(quote.ask_price),
                    'bid_size': quote.bid_size,
                    'ask_size': quote.ask_size,
                    'timestamp': quote.timestamp
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get quote: {e}")
            return None
    
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = '1H',
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """Get historical bars"""
        if not self.connected or not self.data_client:
            return None
        try:
        
            # Convert timeframe
            tf_map = {
                '1m': TimeFrame.Minute,
                '5m': TimeFrame(5, 'Min'),
                '15m': TimeFrame(15, 'Min'),
                '1H': TimeFrame.Hour,
                '1D': TimeFrame.Day
            }
            
            tf = tf_map.get(timeframe, TimeFrame.Hour)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                limit=limit
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if symbol in bars:
                return [
                    {
                        'timestamp': bar.timestamp,
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': bar.volume
                    }
                    for bar in bars[symbol]
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get bars: {e}")
            return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Create adapter (paper trading)
        adapter = AlpacaBrokerAdapter({
            'api_key': 'YOUR_API_KEY',
            'api_secret': 'YOUR_API_SECRET',
            'paper': True
        })
        
        # Connect
        if await adapter.connect():
            # Get account info
            account = await adapter.get_account_info()
            logger.info(f"\nAccount: {account}")
            
            # Get positions
            positions = await adapter.get_positions()
            logger.info(f"\nPositions: {positions}")
            
            # Get quote
            quote = await adapter.get_quote('AAPL')
            logger.info(f"\nAAPL Quote: {quote}")
            
            # Disconnect
            await adapter.disconnect()
        else:
            logger.info("Connection failed - check API credentials")
    
    asyncio.run(main())
