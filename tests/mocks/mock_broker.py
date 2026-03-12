"""
Mock broker implementations for testing.
Simulates MT5 and other broker connections without requiring actual connections.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid
from typing import Set


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class MockOrder:
    """Represents a mock order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    fees: float = 0.0
    slippage: float = 0.0


@dataclass
class MockPosition:
    """Represents a mock position."""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MockMT5Broker:
    """
    Mock MT5 broker for testing.
    Simulates all MT5 broker operations without requiring actual connection.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        self.initialized = False
        
        # Account state
        self.balance = self.config.get('initial_balance', 10000.0)
        self.equity = self.balance
        self.margin = 0.0
        self.free_margin = self.balance
        self.leverage = self.config.get('leverage', 100)
        
        # Trading state
        self.positions: Dict[str, MockPosition] = {}
        self.orders: Dict[str, MockOrder] = {}
        self.order_history: List[MockOrder] = []
        self.trade_history: List[Dict] = []
        
        # Market prices (simulated)
        self.prices: Dict[str, Dict[str, float]] = {
            'EURUSD': {'bid': 1.0850, 'ask': 1.0852, 'last': 1.0851},
            'GBPUSD': {'bid': 1.2650, 'ask': 1.2653, 'last': 1.2651},
            'USDJPY': {'bid': 149.50, 'ask': 149.53, 'last': 149.51},
            'AUDUSD': {'bid': 0.6550, 'ask': 0.6553, 'last': 0.6551},
            'USDCAD': {'bid': 1.3650, 'ask': 1.3653, 'last': 1.3651},
        }
        
        # Simulation settings
        self.slippage_pips = self.config.get('slippage_pips', 0.5)
        self.commission_per_lot = self.config.get('commission_per_lot', 7.0)
        self.fill_probability = self.config.get('fill_probability', 0.98)
    
    async def connect(self) -> bool:
        """Simulate broker connection."""
        await asyncio.sleep(0.01)  # Simulate connection delay
        self.connected = True
        self.initialized = True
        return True
    
    async def disconnect(self) -> bool:
        """Simulate broker disconnection."""
        await asyncio.sleep(0.01)
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check if broker is connected."""
        return self.connected
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        self._check_connection()
        return {
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'free_margin': self.free_margin,
            'leverage': self.leverage,
            'currency': 'USD',
            'profit': self.equity - self.balance,
        }
    
    async def get_account_balance(self) -> float:
        """Get account balance."""
        self._check_connection()
        return self.balance
    
    async def get_account_equity(self) -> float:
        """Get account equity."""
        self._check_connection()
        self._update_equity()
        return self.equity
    
    async def get_positions(self) -> List[MockPosition]:
        """Get all open positions."""
        self._check_connection()
        self._update_positions()
        return list(self.positions.values())
    
    async def get_position(self, symbol: str) -> Optional[MockPosition]:
        """Get position for a specific symbol."""
        self._check_connection()
        self._update_positions()
        return self.positions.get(symbol)
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'market',
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> MockOrder:
        """Place an order."""
        self._check_connection()
        
        order_id = str(uuid.uuid4())[:8]
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        order_type_enum = OrderType(order_type.lower())
        
        order = MockOrder(
            order_id=order_id,
            symbol=symbol,
            side=order_side,
            order_type=order_type_enum,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        
        self.orders[order_id] = order
        
        # Simulate order execution for market orders
        if order_type_enum == OrderType.MARKET:
            await self._execute_order(order)
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        self._check_connection()
        
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                self.order_history.append(order)
                del self.orders[order_id]
                return True
        return False
    
    async def close_position(self, symbol: str, quantity: Optional[float] = None) -> bool:
        """Close a position."""
        self._check_connection()
        
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        close_quantity = quantity or position.quantity
        
        # Create closing order
        close_side = 'sell' if position.side == 'buy' else 'buy'
        await self.place_order(symbol, close_side, close_quantity, 'market')
        
        # Update or remove position
        if close_quantity >= position.quantity:
            del self.positions[symbol]
        else:
            position.quantity -= close_quantity
        
        return True
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        self._check_connection()
        
        return {
            'symbol': symbol,
            'digits': 5 if 'JPY' not in symbol else 3,
            'point': 0.00001 if 'JPY' not in symbol else 0.001,
            'trade_contract_size': 100000,
            'volume_min': 0.01,
            'volume_max': 100.0,
            'volume_step': 0.01,
            'spread': 2,
        }
    
    async def get_tick(self, symbol: str) -> Dict[str, float]:
        """Get current tick data."""
        self._check_connection()
        
        if symbol in self.prices:
            prices = self.prices[symbol]
            # Add small random variation
            variation = random.uniform(-0.0001, 0.0001)
            return {
                'bid': prices['bid'] + variation,
                'ask': prices['ask'] + variation,
                'last': prices['last'] + variation,
                'time': datetime.now().timestamp(),
            }
        return {'bid': 0, 'ask': 0, 'last': 0, 'time': 0}
    
    def set_price(self, symbol: str, bid: float, ask: float):
        """Set price for a symbol (for testing)."""
        self.prices[symbol] = {
            'bid': bid,
            'ask': ask,
            'last': (bid + ask) / 2,
        }
    
    async def _execute_order(self, order: MockOrder):
        """Execute an order (internal)."""
        # Simulate fill probability
        if random.random() > self.fill_probability:
            order.status = OrderStatus.REJECTED
            return
        
        # Get execution price
        prices = self.prices.get(order.symbol, {'bid': 1.0, 'ask': 1.0})
        if order.side == OrderSide.BUY:
            base_price = prices['ask']
            slippage = self.slippage_pips * 0.0001
        else:
            base_price = prices['bid']
            slippage = -self.slippage_pips * 0.0001
        
        execution_price = base_price + slippage
        
        # Calculate fees
        lots = order.quantity / 100000
        fees = lots * self.commission_per_lot
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = execution_price
        order.fees = fees
        order.slippage = slippage
        
        # Update position
        await self._update_position_from_order(order)
        
        # Update account
        self.balance -= fees
        self._update_equity()
        
        # Record trade
        self.trade_history.append({
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': execution_price,
            'fees': fees,
            'timestamp': datetime.now(),
        })
    
    async def _update_position_from_order(self, order: MockOrder):
        """Update position based on filled order."""
        symbol = order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if (order.side == OrderSide.BUY and position.side == 'buy') or \
               (order.side == OrderSide.SELL and position.side == 'sell'):
                # Adding to position
                total_cost = position.quantity * position.entry_price + order.quantity * order.filled_price
                position.quantity += order.quantity
                position.entry_price = total_cost / position.quantity
            else:
                # Reducing position
                if order.quantity >= position.quantity:
                    # Close position
                    pnl = self._calculate_pnl(position, order.filled_price)
                    self.balance += pnl
                    del self.positions[symbol]
                else:
                    # Partial close
                    position.quantity -= order.quantity
        else:
            # New position
            self.positions[symbol] = MockPosition(
                symbol=symbol,
                side=order.side.value,
                quantity=order.quantity,
                entry_price=order.filled_price,
                current_price=order.filled_price,
            )
    
    def _calculate_pnl(self, position: MockPosition, exit_price: float) -> float:
        """Calculate P&L for a position."""
        if position.side == 'buy':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
        return pnl
    
    def _update_positions(self):
        """Update all positions with current prices."""
        for symbol, position in self.positions.items():
            if symbol in self.prices:
                prices = self.prices[symbol]
                if position.side == 'buy':
                    position.current_price = prices['bid']
                else:
                    position.current_price = prices['ask']
                position.unrealized_pnl = self._calculate_pnl(position, position.current_price)
    
    def _update_equity(self):
        """Update account equity."""
        self._update_positions()
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        self.equity = self.balance + unrealized_pnl
        self.free_margin = self.equity - self.margin
    
    def _check_connection(self):
        """Check if broker is connected."""
        if not self.connected:
            raise ConnectionError("Broker not connected")


class MockBrokerConnection:
    """
    Simple mock broker connection for basic testing.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.connected = False
        self.balance = self.config.get('initial_balance', 10000.0)
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        return self.connected
    
    def get_balance(self) -> float:
        return self.balance
    
    def place_order(self, symbol: str, side: str, quantity: float) -> Dict:
        return {
            'order_id': str(uuid.uuid4())[:8],
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'status': 'filled',
        }
