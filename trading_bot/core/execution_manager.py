"""
Execution Manager - Coordinates all execution components

This module serves as the central coordination point for all execution components,
managing order placement, execution algorithms, and trade management.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

# Import execution components
from trading_bot.execution.smart_router import SmartOrderRouter, VenueType, ExecutionQuality
from trading_bot.execution.smart_execution import SmartExecutionEngine
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor
from trading_bot.risk.risk_manager import RiskManager
from trading_bot.core.signal_counterintelligence import (
    CounterintelligenceMode,
    validate_intelligence_metadata,
)

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


class OrderType(Enum):
    """Order types supported by the execution manager"""
    MARKET = 'market'
    LIMIT = 'limit'
    STOP = 'stop'
    STOP_LIMIT = 'stop_limit'
    TRAILING_STOP = 'trailing_stop'
    TAKE_PROFIT = 'take_profit'


class OrderStatus(Enum):
    """Order status values"""
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    PARTIALLY_FILLED = 'partially_filled'
    FILLED = 'filled'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'
    EXPIRED = 'expired'


@dataclass
class Order:
    """Order information"""
    id: str
    symbol: str
    order_type: OrderType
    side: str  # 'buy' or 'sell'
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = 'GTC'  # GTC, IOC, FOK, etc.
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: Optional[float] = None
    venue_id: Optional[str] = None
    algorithm: Optional[str] = None
    parent_id: Optional[str] = None
    client_order_id: Optional[str] = None  # For idempotency
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Trade:
    """Executed trade information"""
    id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    venue_id: str
    commission: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Position:
    """Position information"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    open_time: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.open_time is None:
            self.open_time = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class ExecutionManager:
    """
    Coordinates all execution components and provides a unified interface
    for order placement, execution, and trade management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize execution components
        self.smart_router = SmartOrderRouter(self.config.get('smart_router', {}))
        self.execution_engine = SmartExecutionEngine(self.config.get('execution_engine', {}))
        self.risk_manager = RiskManager(self.config.get('risk_manager', {}))
        
        # Initialize algorithm executors
        self.algorithms = {
            'twap': TWAPExecutor(),
            'vwap': VWAPExecutor(),
            # Additional algorithms will be loaded dynamically
        }
        
        # Order and trade storage
        self.orders = {}  # order_id -> Order
        self.orders_by_client_id = {}  # client_order_id -> Order
        self.submitted_order_ids = set()  # For idempotency tracking
        self.trades = {}
        self.positions = {}
        
        # Order ID counter
        self._order_id_counter = 0
        self._trade_id_counter = 0
        
        # Error handling configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)  # seconds
        self.counterintelligence_mode = self._coerce_counterintelligence_mode(
            self.config.get("counterintelligence_mode", CounterintelligenceMode.HARD_GATE)
        )
        
        logger.info("Execution Manager initialized")
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID"""
        self._order_id_counter += 1
        return f"order_{int(time.time())}_{self._order_id_counter}"
    
    def _generate_trade_id(self) -> str:
        """Generate a unique trade ID"""
        self._trade_id_counter += 1
        return f"trade_{int(time.time())}_{self._trade_id_counter}"
    
    async def place_order(self, symbol: str, order_type: OrderType, side: str, 
                        quantity: float, price: Optional[float] = None,
                        stop_price: Optional[float] = None,
                        time_in_force: str = 'GTC',
                        algorithm: Optional[str] = None,
                        urgency: float = 0.5,
                        market_volatility: float = 0.3,
                        metadata: Optional[Dict[str, Any]] = None) -> Order:
        """
        Place a new order with idempotency support
        
        Args:
            symbol: Trading symbol
            order_type: Type of order
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force (GTC, IOC, FOK, etc.)
            algorithm: Execution algorithm to use
            urgency: Order urgency (0-1)
            market_volatility: Current market volatility (0-1)
            metadata: Additional order metadata (can include 'client_order_id')
            
        Returns:
            Order object (existing if duplicate detected)
        """
        # Extract or generate client order ID for idempotency
        metadata = metadata or {}
        client_order_id = metadata.get('client_order_id') or str(uuid.uuid4())
        
        # Check for duplicate order (idempotency)
        if client_order_id in self.orders_by_client_id:
            existing_order = self.orders_by_client_id[client_order_id]
            logger.warning(
                f"Duplicate order detected with client_order_id={client_order_id}, "
                f"returning existing order {existing_order.id}"
            )
            return existing_order
        
        # Generate internal order ID
        order_id = self._generate_order_id()
        
        # Create order object
        order = Order(
            id=order_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            status=OrderStatus.PENDING,
            client_order_id=client_order_id,
            metadata=metadata
        )
        
        # Store order with both IDs
        self.orders[order_id] = order
        self.orders_by_client_id[client_order_id] = order
        self.submitted_order_ids.add(client_order_id)

        intelligence_metadata = metadata.get("intelligence") or metadata.get("intelligence_metadata") or metadata
        gate_passed, gate_reasons = validate_intelligence_metadata(
            intelligence_metadata,
            self.counterintelligence_mode,
        )
        if not gate_passed:
            order.status = OrderStatus.REJECTED
            order.metadata["rejection_reason"] = "; ".join(gate_reasons)
            logger.warning(
                f"Order {order_id} rejected by signal counterintelligence: "
                f"{order.metadata['rejection_reason']}"
            )
            return order
        
        # Check risk limits
        risk_check = self.risk_manager.check_order_risk(order)
        if not risk_check['approved']:
            order.status = OrderStatus.REJECTED
            order.metadata['rejection_reason'] = risk_check['reason']
            logger.warning(f"Order {order_id} rejected by risk manager: {risk_check['reason']}")
            return order
        
        # Route order to optimal venue
        if order_type == OrderType.MARKET:
            routing_decision = self.smart_router.route_order(
                symbol=symbol,
                side=side.lower(),
                size=quantity,
                urgency=urgency,
                market_volatility=market_volatility
            )
            
            # Update order with routing information
            order.venue_id = routing_decision.venue_id
            order.algorithm = routing_decision.algorithm
            order.metadata['routing_decision'] = {
                'expected_cost_bps': routing_decision.expected_cost_bps,
                'expected_latency_ms': routing_decision.expected_latency_ms,
                'expected_fill_rate': routing_decision.expected_fill_rate,
                'reason': routing_decision.reason
            }
        
        # Execute order
        try:
            # Submit order to venue
            result = await self._submit_order(order)
            
            # Update order with result
            order.status = OrderStatus.SUBMITTED
            order.metadata['submission_time'] = datetime.now()
            order.metadata['submission_result'] = result
            
            logger.info(f"Order {order_id} submitted successfully")
            
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.metadata['rejection_reason'] = str(e)
            logger.error(f"Order {order_id} submission failed: {e}")
        
        return order

    def _coerce_counterintelligence_mode(self, value: Any) -> CounterintelligenceMode:
        if isinstance(value, CounterintelligenceMode):
            return value
        try:
            return CounterintelligenceMode(str(value))
        except ValueError:
            return CounterintelligenceMode.HARD_GATE
    
    async def _submit_order(self, order: Order) -> Dict[str, Any]:
        """
        Submit an order to the appropriate venue
        
        Args:
            order: Order to submit
            
        Returns:
            Submission result
        """
        # Determine execution method based on order type and algorithm
        if order.algorithm and order.algorithm in self.algorithms:
            # Use specified algorithm
            executor = self.algorithms[order.algorithm]
            result = await executor.execute(order)
        else:
            # Use smart execution engine
            result = await self.execution_engine.execute_order(order)
        
        return result
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            True if cancellation was successful
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot cancel unknown order: {order_id}")
            return False
        
        order = self.orders[order_id]
        
        # Check if order can be cancelled
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
            return False
        try:
        
            # Send cancellation request
            result = await self.execution_engine.cancel_order(order)
            
            # Update order status
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            order.metadata['cancellation_time'] = datetime.now()
            order.metadata['cancellation_result'] = result
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Order {order_id} cancellation failed: {e}")
            return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Optional[Order]:
        """
        Modify an existing order
        
        Args:
            order_id: ID of order to modify
            **kwargs: Order parameters to modify
            
        Returns:
            Modified order or None if modification failed
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot modify unknown order: {order_id}")
            return None
        
        order = self.orders[order_id]
        
        # Check if order can be modified
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            logger.warning(f"Cannot modify order {order_id} with status {order.status}")
            return None
        try:
        
            # Create modification request
            modifications = {}
            for key, value in kwargs.items():
                if hasattr(order, key):
                    modifications[key] = value
            
            # Send modification request
            result = await self.execution_engine.modify_order(order, modifications)
            
            # Update order
            for key, value in modifications.items():
                setattr(order, key, value)
            
            order.updated_at = datetime.now()
            order.metadata['modification_time'] = datetime.now()
            order.metadata['modification_result'] = result
            
            logger.info(f"Order {order_id} modified successfully")
            return order
            
        except Exception as e:
            logger.error(f"Order {order_id} modification failed: {e}")
            return None
    
    async def process_fill(self, order_id: str, fill_quantity: float, 
                         fill_price: float, timestamp: datetime = None,
                         venue_id: Optional[str] = None,
                         commission: float = 0.0) -> Trade:
        """
        Process a fill for an order
        
        Args:
            order_id: ID of the filled order
            fill_quantity: Quantity filled
            fill_price: Fill price
            timestamp: Fill timestamp
            venue_id: Venue where the fill occurred
            commission: Commission paid
            
        Returns:
            Trade object representing the fill
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot process fill for unknown order: {order_id}")
            raise ValueError(f"Unknown order ID: {order_id}")
        
        order = self.orders[order_id]
        
        # Check if order can be filled
        if order.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            logger.warning(f"Cannot fill order {order_id} with status {order.status}")
            raise ValueError(f"Cannot fill order with status {order.status}")
        
        # Generate trade ID
        trade_id = self._generate_trade_id()
        
        # Create trade object
        trade = Trade(
            id=trade_id,
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=fill_quantity,
            price=fill_price,
            timestamp=timestamp or datetime.now(),
            venue_id=venue_id or order.venue_id or "unknown",
            commission=commission
        )
        
        # Store trade
        self.trades[trade_id] = trade
        
        # Update order
        order.filled_quantity += fill_quantity
        
        # Calculate average fill price
        if order.average_fill_price is None:
            order.average_fill_price = fill_price
        else:
            total_quantity = order.filled_quantity
            previous_quantity = total_quantity - fill_quantity
            order.average_fill_price = (
                (order.average_fill_price * previous_quantity) + 
                (fill_price * fill_quantity)
            ) / total_quantity
        
        # Update order status
        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED
        
        order.updated_at = datetime.now()
        
        # Update position
        await self._update_position(trade)
        
        # Record execution quality
        if order.venue_id:
            fill_latency = (trade.timestamp - order.metadata.get('submission_time', trade.timestamp)).total_seconds() * 1000
            expected_latency = order.metadata.get('routing_decision', {}).get('expected_latency_ms', 0)
            
            # Determine execution quality
            if fill_latency <= expected_latency * 0.8:
                quality = ExecutionQuality.EXCELLENT
            elif fill_latency <= expected_latency * 1.2:
                quality = ExecutionQuality.GOOD
            elif fill_latency <= expected_latency * 2.0:
                quality = ExecutionQuality.AVERAGE
            elif fill_latency <= expected_latency * 3.0:
                quality = ExecutionQuality.POOR
            else:
                quality = ExecutionQuality.BAD
            
            # Record quality
            self.smart_router.record_execution_quality(order.venue_id, quality)
            
            # Update venue metrics
            self.smart_router.update_venue_metrics(
                venue_id=order.venue_id,
                latency_ms=fill_latency,
                fill_rate=fill_quantity / order.quantity
            )
        
        logger.info(f"Processed fill for order {order_id}: {fill_quantity} @ {fill_price}")
        return trade
    
    async def _update_position(self, trade: Trade) -> None:
        """
        Update position based on a trade
        
        Args:
            trade: Trade to process
        """
        symbol = trade.symbol
        
        # Get existing position or create new one
        if symbol in self.positions:
            position = self.positions[symbol]
        else:
            position = Position(
                symbol=symbol,
                quantity=0,
                entry_price=0,
                current_price=trade.price,
                unrealized_pnl=0
            )
            self.positions[symbol] = position
        
        # Calculate position changes
        old_quantity = position.quantity
        trade_quantity = trade.quantity if trade.side.lower() == 'buy' else -trade.quantity
        new_quantity = old_quantity + trade_quantity
        
        # Update position
        if new_quantity == 0:
            # Position closed
            realized_pnl = (trade.price - position.entry_price) * -old_quantity
            position.realized_pnl += realized_pnl
            position.quantity = 0
            position.entry_price = 0
            
        elif old_quantity == 0 or (old_quantity > 0 and trade_quantity > 0) or (old_quantity < 0 and trade_quantity < 0):
            # New position or adding to existing position
            position.entry_price = ((position.entry_price * abs(old_quantity)) + 
                                  (trade.price * abs(trade_quantity))) / abs(new_quantity)
            position.quantity = new_quantity
            
        elif abs(trade_quantity) <= abs(old_quantity) and ((old_quantity > 0 and trade_quantity < 0) or (old_quantity < 0 and trade_quantity > 0)):
            # Reducing position
            realized_pnl = (trade.price - position.entry_price) * trade_quantity
            position.realized_pnl += realized_pnl
            position.quantity = new_quantity
            
        else:
            # Flipping position
            realized_pnl = (trade.price - position.entry_price) * -old_quantity
            position.realized_pnl += realized_pnl
            position.quantity = new_quantity
            position.entry_price = trade.price
        
        # Update current price and unrealized P&L
        position.current_price = trade.price
        position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
    
    async def update_market_price(self, symbol: str, price: float) -> None:
        """
        Update market price for a symbol
        
        Args:
            symbol: Trading symbol
            price: Current market price
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = price
            position.unrealized_pnl = (price - position.entry_price) * position.quantity
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        return self.orders.get(order_id)
    
    def get_orders(self, symbol: Optional[str] = None, 
                 status: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get orders filtered by symbol and/or status
        
        Args:
            symbol: Filter by symbol
            status: Filter by status
            
        Returns:
            List of matching orders
        """
        result = list(self.orders.values())
        
        if symbol:
            result = [o for o in result if o.symbol == symbol]
        
        if status:
            result = [o for o in result if o.status == status]
        
        return result
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None if no position
        """
        return self.positions.get(symbol)
    
    def get_positions(self) -> List[Position]:
        """
        Get all positions
        
        Returns:
            List of all positions
        """
        return list(self.positions.values())
    
    def get_active_positions(self) -> List[Position]:
        """
        Get all active positions (non-zero quantity)
        
        Returns:
            List of active positions
        """
        return [p for p in self.positions.values() if p.quantity != 0]
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        win_rate: float = 0.5,
        reward_risk_ratio: float = 1.5,
        max_risk_percent: float = 0.02
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            win_rate: Historical win rate (0-1)
            reward_risk_ratio: Reward to risk ratio
            max_risk_percent: Maximum risk per trade as decimal
            
        Returns:
            Dictionary with position sizing details
        """
        # Get account equity from config or default
        account_equity = self.config.get('account_equity', 10000.0)
        
        # Calculate risk per share/unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            logger.warning("Risk per unit is zero, cannot calculate position size")
            return {
                'recommended_size': 0.0,
                'max_size': 0.0,
                'risk_amount': 0.0,
                'risk_percent': 0.0,
                'kelly_fraction': 0.0,
                'reason': 'Invalid stop loss (same as entry)'
            }
        
        # Calculate Kelly criterion
        if win_rate > 0 and reward_risk_ratio > 0:
            kelly = (win_rate * reward_risk_ratio - (1 - win_rate)) / reward_risk_ratio
            kelly = max(0, min(kelly, 0.25))  # Cap at 25%
        else:
            kelly = 0.0
        
        # Use fractional Kelly (half Kelly for safety)
        fractional_kelly = kelly * 0.5
        
        # Calculate risk amount
        risk_amount = account_equity * min(max_risk_percent, fractional_kelly if fractional_kelly > 0 else max_risk_percent)
        
        # Calculate position size
        position_size = risk_amount / risk_per_unit
        
        # Apply symbol-specific constraints (lot size, min/max)
        min_lot = self.config.get('min_lot_size', 0.01)
        max_lot = self.config.get('max_lot_size', 100.0)
        lot_step = self.config.get('lot_step', 0.01)
        
        # Round to lot step
        position_size = round(position_size / lot_step) * lot_step
        position_size = max(min_lot, min(position_size, max_lot))
        
        return {
            'recommended_size': position_size,
            'max_size': max_lot,
            'risk_amount': risk_amount,
            'risk_percent': risk_amount / account_equity,
            'kelly_fraction': kelly,
            'fractional_kelly': fractional_kelly,
            'stop_loss_distance': risk_per_unit,
            'account_equity': account_equity,
            'reason': f'Kelly: {kelly:.2%}, Risk: {max_risk_percent:.2%}'
        }
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio status.
        
        Returns:
            Dictionary with portfolio metrics
        """
        active_positions = self.get_active_positions()
        
        # Calculate totals
        total_unrealized_pnl = sum(p.unrealized_pnl for p in active_positions)
        total_realized_pnl = sum(p.realized_pnl for p in self.positions.values())
        
        # Get account info
        account_balance = self.config.get('account_balance', 10000.0)
        account_equity = account_balance + total_unrealized_pnl
        
        # Calculate drawdown
        peak_equity = self.config.get('peak_equity', account_equity)
        if account_equity > peak_equity:
            peak_equity = account_equity
            self.config['peak_equity'] = peak_equity
        
        current_drawdown = (peak_equity - account_equity) / peak_equity if peak_equity > 0 else 0.0
        
        # Calculate daily P&L (simplified - would need trade history)
        daily_pnl = total_unrealized_pnl + total_realized_pnl
        
        # Calculate margin usage (simplified)
        total_position_value = sum(abs(p.quantity * p.current_price) for p in active_positions)
        leverage = self.config.get('leverage', 100)
        margin_used = total_position_value / leverage if leverage > 0 else 0
        free_margin = account_equity - margin_used
        free_margin_ratio = free_margin / account_equity if account_equity > 0 else 1.0
        
        return {
            'account_balance': account_balance,
            'account_equity': account_equity,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'daily_pnl': daily_pnl,
            'current_drawdown': current_drawdown,
            'peak_equity': peak_equity,
            'positions': [{
                'symbol': p.symbol,
                'quantity': p.quantity,
                'entry_price': p.entry_price,
                'current_price': p.current_price,
                'unrealized_pnl': p.unrealized_pnl,
                'realized_pnl': p.realized_pnl
            } for p in active_positions],
            'position_count': len(active_positions),
            'margin_used': margin_used,
            'free_margin': free_margin,
            'free_margin_ratio': free_margin_ratio,
            'leverage': leverage
        }
    
    async def close_position(self, symbol: str, market_order: bool = True) -> Optional[Order]:
        """
        Close an existing position
        
        Args:
            symbol: Symbol to close
            market_order: Whether to use a market order
            
        Returns:
            Order object for the closing order or None if no position
        """
        position = self.get_position(symbol)
        if not position or position.quantity == 0:
            logger.warning(f"No position to close for {symbol}")
            return None
        
        # Determine order side
        side = 'sell' if position.quantity > 0 else 'buy'
        
        # Place closing order
        order_type = OrderType.MARKET if market_order else OrderType.LIMIT
        price = None if market_order else position.current_price
        
        order = await self.place_order(
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=abs(position.quantity),
            price=price,
            metadata={'purpose': 'position_close'}
        )
        
        return order
    
    async def close_all_positions(self, market_order: bool = True) -> Dict[str, Order]:
        """
        Close all open positions
        
        Args:
            market_order: Whether to use market orders
            
        Returns:
            Dictionary of symbol to closing order
        """
        active_positions = self.get_active_positions()
        result = {}
        
        for position in active_positions:
            order = await self.close_position(position.symbol, market_order)
            if order:
                result[position.symbol] = order
        
        return result


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create execution manager
    manager = ExecutionManager()
    
    # Example order placement
    async def test_execution():
        # Place a market order
        order = await manager.place_order(
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side="buy",
            quantity=1.0,
            urgency=0.7,
            market_volatility=0.3
        )
        
        logger.info(f"Placed order: {order.id}, Status: {order.status}")
        
        # Process a fill
        if order.status == OrderStatus.SUBMITTED:
            trade = await manager.process_fill(
                order_id=order.id,
                fill_quantity=1.0,
                fill_price=1.1050,
                commission=0.1
            )
            
            logger.info(f"Processed fill: {trade.id}, Price: {trade.price}")
            
            # Get position
            position = manager.get_position("EURUSD")
            logger.info(f"Position: {position.quantity} @ {position.entry_price}")
            
            # Update market price
            await manager.update_market_price("EURUSD", 1.1075)
            position = manager.get_position("EURUSD")
            logger.info(f"Updated position: {position.quantity} @ {position.entry_price}, Unrealized P&L: {position.unrealized_pnl}")
            
            # Close position
            close_order = await manager.close_position("EURUSD")
            logger.info(f"Close order: {close_order.id}, Status: {close_order.status}")
    
    # Run the test
    asyncio.run(test_execution())
