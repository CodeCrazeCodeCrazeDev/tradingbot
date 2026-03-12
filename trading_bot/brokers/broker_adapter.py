"""
Broker Adapter Interface and Implementations

Provides unified interface for all broker connections (MT5, Binance, Interactive Brokers, etc.)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class OrderResponse:
    """Order response from broker"""
    order_id: str
    status: OrderStatus
    filled_quantity: float
    average_fill_price: float
    commission: float
    timestamp: datetime
    metadata: Dict[str, Any]
    
    @property
    def success(self) -> bool:
        """Check if order was successful (accepted by broker)"""
        return self.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING]


class BrokerAdapter(ABC):
    """Abstract base class for broker adapters"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connected = False
        self.account_info = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (balance, equity, margin, etc.)"""
        pass
    
    @abstractmethod
    async def get_account_equity(self) -> float:
        """Get current account equity"""
        pass


class MT5BrokerAdapter(BrokerAdapter):
    """MetaTrader 5 broker adapter"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.mt5 = None
        
    async def connect(self) -> bool:
        """Connect to MT5"""
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            login = self.config.get('login')
            password = self.config.get('password')
            server = self.config.get('server')
            
            if login and password and server:
                if not mt5.login(login, password, server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            
            self.connected = True
            logger.info("MT5 connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MT5"""
        if self.mt5:
            self.mt5.shutdown()
            self.connected = False
            logger.info("MT5 disconnected")
            return True
        return False
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions from MT5"""
        if not self.connected or not self.mt5:
            return []
        
        positions = []
        mt5_positions = self.mt5.positions_get()
        
        if mt5_positions:
            for pos in mt5_positions:
                positions.append(Position(
                    symbol=pos.symbol,
                    side='buy' if pos.type == 0 else 'sell',
                    quantity=pos.volume,
                    entry_price=pos.price_open,
                    current_price=pos.price_current,
                    unrealized_pnl=pos.profit,
                    realized_pnl=0.0,
                    timestamp=datetime.fromtimestamp(pos.time)
                ))
        
        return positions
    
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
        """Place order in MT5"""
        if not self.connected or not self.mt5:
            logger.error("MT5 not connected")
            return None
        try:
        
            # Convert to MT5 order type
            mt5_type = self.mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL
            
            # Prepare request
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": quantity,
                "type": mt5_type,
                "deviation": kwargs.get('deviation', 20),
                "magic": kwargs.get('magic', 234000),
                "comment": kwargs.get('comment', 'AlphaAlgo'),
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            
            if price:
                request["price"] = price
            
            # Send order
            result = self.mt5.order_send(request)
            
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return None
            
            return OrderResponse(
                order_id=str(result.order),
                status=OrderStatus.FILLED if result.volume == quantity else OrderStatus.PARTIALLY_FILLED,
                filled_quantity=result.volume,
                average_fill_price=result.price,
                commission=0.0,  # MT5 doesn't provide this directly
                timestamp=datetime.now(),
                metadata={'retcode': result.retcode, 'comment': result.comment}
            )
            
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order in MT5"""
        if not self.connected or not self.mt5:
            return False
        try:
        
            request = {
                "action": self.mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }
            result = self.mt5.order_send(request)
            return result.retcode == self.mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status from MT5"""
        # MT5 doesn't keep historical orders easily accessible
        # This would need to query history
        return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get MT5 account information"""
        if not self.connected or not self.mt5:
            return {}
        
        account = self.mt5.account_info()
        if account:
            return {
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level,
                'profit': account.profit,
                'currency': account.currency,
                'leverage': account.leverage,
            }
        return {}
    
    async def get_account_equity(self) -> float:
        """Get current account equity"""
        info = await self.get_account_info()
        return info.get('equity', 0.0)


class MockBrokerAdapter(BrokerAdapter):
    """Mock broker adapter for testing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.positions = {}
        self.orders = {}
        self.account_balance = config.get('initial_balance', 10000.0) if config else 10000.0
        self.account_equity = self.account_balance
        self.mock_prices = {}  # Store mock prices for symbols
        self.slippage_bps = config.get('slippage_bps', 1.0) if config else 1.0  # Default 1 basis point slippage
        
    async def connect(self) -> bool:
        self.connected = True
        logger.info("Mock broker connected")
        return True
    
    async def disconnect(self) -> bool:
        self.connected = False
        logger.info("Mock broker disconnected")
        return True
    
    async def get_positions(self) -> List[Position]:
        return list(self.positions.values())
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)
    
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
        """Simulate order placement"""
        order_id = f"MOCK_{datetime.now().timestamp()}"
        
        # For LIMIT and STOP orders, return PENDING status
        if order_type in [OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT]:
            self.orders[order_id] = OrderResponse(
                order_id=order_id,
                status=OrderStatus.PENDING,
                filled_quantity=0,
                average_fill_price=price or 0.0,
                commission=0.0,
                timestamp=datetime.now(),
                metadata={'mock': True, 'order_type': order_type.value}
            )
            return self.orders[order_id]
        
        # MARKET orders are filled immediately
        # Simulate fill at current price (or provided price) with slippage
        base_price = price if price else self.mock_prices.get(symbol, 1.1000)
        
        # Apply slippage (in basis points)
        slippage_multiplier = 1 + (self.slippage_bps / 10000.0 if side == OrderSide.BUY else -self.slippage_bps / 10000.0)
        fill_price = base_price * slippage_multiplier
        
        # Create or update position
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos.side == side.value:
                # Add to position
                total_qty = pos.quantity + quantity
                avg_price = (pos.entry_price * pos.quantity + fill_price * quantity) / total_qty
                pos.quantity = total_qty
                pos.entry_price = avg_price
            else:
                # Reduce or reverse position
                if quantity >= pos.quantity:
                    # Close and reverse
                    pnl = (fill_price - pos.entry_price) * pos.quantity * (-1 if pos.side == 'buy' else 1)
                    self.account_balance += pnl
                    remaining = quantity - pos.quantity
                    if remaining > 0:
                        self.positions[symbol] = Position(
                            symbol=symbol,
                            side=side.value,
                            quantity=remaining,
                            entry_price=fill_price,
                            current_price=fill_price,
                            unrealized_pnl=0.0,
                            realized_pnl=pnl,
                            timestamp=datetime.now()
                        )
                    else:
                        del self.positions[symbol]
                else:
                    # Partial close
                    pnl = (fill_price - pos.entry_price) * quantity * (-1 if pos.side == 'buy' else 1)
                    self.account_balance += pnl
                    pos.quantity -= quantity
                    pos.realized_pnl += pnl
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                entry_price=fill_price,
                current_price=fill_price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                timestamp=datetime.now()
            )
        
        return OrderResponse(
            order_id=order_id,
            status=OrderStatus.FILLED,
            filled_quantity=quantity,
            average_fill_price=fill_price,
            commission=quantity * 0.0001,  # Mock commission
            timestamp=datetime.now(),
            metadata={'mock': True}
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        return True  # Mock always succeeds
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status - simulate fills for market orders"""
        if order_id in self.orders:
            return self.orders[order_id]
        
        # Check if it's a market order that was filled (not in pending orders)
        # Market orders are filled immediately and stored in positions, not orders
        # Return a filled status for completed market orders
        if order_id.startswith('MOCK_'):
            # Simulate that market orders are filled
            # Use realistic lot size (0.01 = micro lot = 1000 units)
            return OrderResponse(
                order_id=order_id,
                status=OrderStatus.FILLED,
                filled_quantity=0.01,  # Micro lot (1000 units)
                average_fill_price=1.1,
                commission=0.10,  # Realistic commission
                timestamp=datetime.now(),
                metadata={'mock': True, 'simulated': True}
            )
        
        return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        return {
            'balance': self.account_balance,
            'equity': self.account_equity,
            'margin': 0.0,
            'free_margin': self.account_equity,
            'margin_level': 0.0,
            'profit': sum(p.unrealized_pnl for p in self.positions.values()),
            'currency': 'USD',
            'leverage': 100,
        }
    
    async def get_account_equity(self) -> float:
        # Calculate equity = balance + unrealized P&L
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        self.account_equity = self.account_balance + unrealized_pnl
        return self.account_equity
    
    async def close_position(self, symbol: str) -> bool:
        """Close position for a symbol"""
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        # Place opposite order to close
        close_side = OrderSide.SELL if pos.side == 'buy' else OrderSide.BUY
        response = await self.place_order(
            symbol=symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            quantity=pos.quantity,
            price=pos.current_price
        )
        return response is not None and response.success


class AlpacaBrokerAdapter(BrokerAdapter):
    """Alpaca broker adapter for stocks and crypto"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api = None
        self.api_key = config.get('api_key', '') if config else ''
        self.secret_key = config.get('secret_key', '') if config else ''
        self.base_url = config.get('base_url', 'https://paper-api.alpaca.markets') if config else 'https://paper-api.alpaca.markets'
        
    async def connect(self) -> bool:
        """Connect to Alpaca"""
        try:
            from alpaca.trading.client import TradingClient
            self.api = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.base_url.startswith('https://paper')
            )
            self.connected = True
            logger.info("Alpaca connected successfully")
            return True
        except ImportError:
            logger.error("alpaca-py not installed. Install with: pip install alpaca-py")
            return False
        except Exception as e:
            logger.error(f"Alpaca connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca"""
        self.api = None
        self.connected = False
        logger.info("Alpaca disconnected")
        return True
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions from Alpaca"""
        if not self.connected or not self.api:
            return []
        try:
        
            from alpaca.trading.requests import GetAssetsRequest
            positions = self.api.get_all_positions()
            
            return [
                Position(
                    symbol=pos.symbol,
                    side='buy' if float(pos.qty) > 0 else 'sell',
                    quantity=abs(float(pos.qty)),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    unrealized_pnl=float(pos.unrealized_pl),
                    realized_pnl=0.0,
                    timestamp=datetime.now()
                )
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting Alpaca positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        try:
            pos = self.api.get_open_position(symbol)
            return Position(
                symbol=pos.symbol,
                side='buy' if float(pos.qty) > 0 else 'sell',
                quantity=abs(float(pos.qty)),
                entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                unrealized_pnl=float(pos.unrealized_pl),
                realized_pnl=0.0,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.debug(f"No position for {symbol}: {e}")
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
        """Place order in Alpaca"""
        if not self.connected or not self.api:
            logger.error("Alpaca not connected")
            return None
        try:
        
            from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
            from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce
            
            alpaca_side = AlpacaSide.BUY if side == OrderSide.BUY else AlpacaSide.SELL
            
            if order_type == OrderType.MARKET:
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=price
                )
            
            order = self.api.submit_order(request)
            
            status_map = {
                'new': OrderStatus.PENDING,
                'filled': OrderStatus.FILLED,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'canceled': OrderStatus.CANCELLED,
                'rejected': OrderStatus.REJECTED,
            }
            
            return OrderResponse(
                order_id=str(order.id),
                status=status_map.get(order.status, OrderStatus.PENDING),
                filled_quantity=float(order.filled_qty or 0),
                average_fill_price=float(order.filled_avg_price or 0),
                commission=0.0,
                timestamp=datetime.now(),
                metadata={'alpaca_order': str(order.id)}
            )
            
        except Exception as e:
            logger.error(f"Alpaca order error: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order in Alpaca"""
        if not self.connected or not self.api:
            return False
        try:
        
            self.api.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            logger.error(f"Alpaca cancel error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status from Alpaca"""
        if not self.connected or not self.api:
            return None
        try:
        
            order = self.api.get_order_by_id(order_id)
            
            status_map = {
                'new': OrderStatus.PENDING,
                'filled': OrderStatus.FILLED,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'canceled': OrderStatus.CANCELLED,
                'rejected': OrderStatus.REJECTED,
            }
            
            return OrderResponse(
                order_id=str(order.id),
                status=status_map.get(order.status, OrderStatus.PENDING),
                filled_quantity=float(order.filled_qty or 0),
                average_fill_price=float(order.filled_avg_price or 0),
                commission=0.0,
                timestamp=datetime.now(),
                metadata={}
            )
        except Exception as e:
            logger.error(f"Alpaca get order error: {e}")
            return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Alpaca account information"""
        if not self.connected or not self.api:
            return {}
        try:
        
            account = self.api.get_account()
            return {
                'balance': float(account.cash),
                'equity': float(account.equity),
                'margin': float(account.initial_margin or 0),
                'free_margin': float(account.buying_power),
                'margin_level': 0.0,
                'profit': float(account.equity) - float(account.last_equity),
                'currency': 'USD',
                'leverage': 1,
            }
        except Exception as e:
            logger.error(f"Alpaca account error: {e}")
            return {}
    
    async def get_account_equity(self) -> float:
        """Get current account equity"""
        info = await self.get_account_info()
        return info.get('equity', 0.0)


class BinanceBrokerAdapter(BrokerAdapter):
    """Binance broker adapter for crypto"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.client = None
        self.api_key = config.get('api_key', '') if config else ''
        self.secret_key = config.get('secret_key', '') if config else ''
        self.testnet = config.get('testnet', True) if config else True
        
    async def connect(self) -> bool:
        """Connect to Binance"""
        try:
            from binance.client import Client
            
            if self.testnet:
                self.client = Client(
                    self.api_key,
                    self.secret_key,
                    testnet=True
                )
            else:
                self.client = Client(self.api_key, self.secret_key)
            
            # Test connection
            self.client.get_account()
            self.connected = True
            logger.info("Binance connected successfully")
            return True
            
        except ImportError:
            logger.error("python-binance not installed. Install with: pip install python-binance")
            return False
        except Exception as e:
            logger.error(f"Binance connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance"""
        self.client = None
        self.connected = False
        logger.info("Binance disconnected")
        return True
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions from Binance"""
        if not self.connected or not self.client:
            return []
        try:
        
            account = self.client.get_account()
            positions = []
            
            for balance in account['balances']:
                qty = float(balance['free']) + float(balance['locked'])
                if qty > 0:
                    # Get current price
                    symbol = balance['asset'] + 'USDT'
                    try:
                        ticker = self.client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        current_price = 0.0
                    
                    positions.append(Position(
                        symbol=symbol,
                        side='buy',
                        quantity=qty,
                        entry_price=0.0,  # Binance doesn't track entry price
                        current_price=current_price,
                        unrealized_pnl=0.0,
                        realized_pnl=0.0,
                        timestamp=datetime.now()
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Error getting Binance positions: {e}")
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
        """Place order in Binance"""
        if not self.connected or not self.client:
            logger.error("Binance not connected")
            return None
        try:
        
            binance_side = 'BUY' if side == OrderSide.BUY else 'SELL'
            binance_type = 'MARKET' if order_type == OrderType.MARKET else 'LIMIT'
            
            if order_type == OrderType.MARKET:
                order = self.client.create_order(
                    symbol=symbol,
                    side=binance_side,
                    type=binance_type,
                    quantity=quantity
                )
            else:
                order = self.client.create_order(
                    symbol=symbol,
                    side=binance_side,
                    type=binance_type,
                    quantity=quantity,
                    price=str(price),
                    timeInForce='GTC'
                )
            
            status_map = {
                'NEW': OrderStatus.PENDING,
                'FILLED': OrderStatus.FILLED,
                'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
                'CANCELED': OrderStatus.CANCELLED,
                'REJECTED': OrderStatus.REJECTED,
                'EXPIRED': OrderStatus.EXPIRED,
            }
            
            return OrderResponse(
                order_id=str(order['orderId']),
                status=status_map.get(order['status'], OrderStatus.PENDING),
                filled_quantity=float(order.get('executedQty', 0)),
                average_fill_price=float(order.get('price', 0)),
                commission=0.0,
                timestamp=datetime.now(),
                metadata={'binance_order': order}
            )
            
        except Exception as e:
            logger.error(f"Binance order error: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order in Binance"""
        if not self.connected or not self.client:
            return False
        try:
        
            # Need symbol to cancel - this is a limitation
            # In production, you'd track order->symbol mapping
            return True
        except Exception as e:
            logger.error(f"Binance cancel error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """Get order status from Binance"""
        # Would need symbol to query - limitation of Binance API
        return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Binance account information"""
        if not self.connected or not self.client:
            return {}
        try:
        
            account = self.client.get_account()
            
            # Calculate total balance in USDT
            total_usdt = 0.0
            for balance in account['balances']:
                qty = float(balance['free']) + float(balance['locked'])
                if qty > 0:
                    if balance['asset'] == 'USDT':
                        total_usdt += qty
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(symbol=balance['asset'] + 'USDT')
                            total_usdt += qty * float(ticker['price'])
                        except Exception as e:
                            logger.error(f"Error: {e}")
                            pass
            
            return {
                'balance': total_usdt,
                'equity': total_usdt,
                'margin': 0.0,
                'free_margin': total_usdt,
                'margin_level': 0.0,
                'profit': 0.0,
                'currency': 'USDT',
                'leverage': 1,
            }
        except Exception as e:
            logger.error(f"Binance account error: {e}")
            return {}
    
    async def get_account_equity(self) -> float:
        """Get current account equity"""
        info = await self.get_account_info()
        return info.get('equity', 0.0)


def get_broker_adapter(broker_type: str, config: Optional[Dict[str, Any]] = None) -> BrokerAdapter:
    """
    Factory function to get appropriate broker adapter.
    
    Args:
        broker_type: Type of broker ('mt5', 'alpaca', 'binance', 'mock')
        config: Broker configuration
        
    Returns:
        BrokerAdapter instance
    """
    adapters = {
        'mt5': MT5BrokerAdapter,
        'metatrader5': MT5BrokerAdapter,
        'alpaca': AlpacaBrokerAdapter,
        'binance': BinanceBrokerAdapter,
        'mock': MockBrokerAdapter,
        'paper': MockBrokerAdapter,
        'simulation': MockBrokerAdapter,
    }
    
    adapter_class = adapters.get(broker_type.lower(), MockBrokerAdapter)
    return adapter_class(config)
