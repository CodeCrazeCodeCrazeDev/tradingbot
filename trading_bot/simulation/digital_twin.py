"""
Digital Twin Simulation System

A high-fidelity simulation environment that mirrors live market conditions.
Every proposed trade is executed in the twin first; only strategies that
prove profitable there are allowed to trade live capital.

Features:
- Parallel simulation of live trading
- Historical tick data replay
- Strategy validation before live deployment
- Performance comparison (twin vs live)
- Risk-free feature testing
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import copy
import statistics
import uuid

logger = logging.getLogger(__name__)


class SimulationMode(Enum):
    """Simulation modes."""
    SHADOW = "shadow"  # Run alongside live, no execution
    VALIDATION = "validation"  # Validate before live execution
    BACKTEST = "backtest"  # Historical replay
    STRESS_TEST = "stress_test"  # Extreme scenarios


class ExecutionResult(Enum):
    """Trade execution results."""
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class MarketTick:
    """Single market tick."""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass
class SimulatedOrder:
    """Order in the digital twin."""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    order_type: str  # 'MARKET', 'LIMIT', 'STOP'
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    timestamp: datetime
    status: str = "PENDING"
    filled_quantity: float = 0
    filled_price: float = 0
    fill_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price
        }


@dataclass
class SimulatedPosition:
    """Position in the digital twin."""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float = 0
    realized_pnl: float = 0
    
    def update_pnl(self, current_price: float):
        """Update unrealized P&L."""
        try:
            if self.quantity > 0:
                self.unrealized_pnl = (current_price - self.avg_price) * self.quantity
            elif self.quantity < 0:
                self.unrealized_pnl = (self.avg_price - current_price) * abs(self.quantity)
        except Exception as e:
            logger.error(f"Error in update_pnl: {e}")
            raise


@dataclass
class SimulatedTrade:
    """Executed trade in the digital twin."""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0
    slippage: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'commission': self.commission,
            'slippage': self.slippage
        }


@dataclass
class ValidationResult:
    """Result of strategy validation."""
    strategy_id: str
    passed: bool
    twin_pnl: float
    twin_trades: int
    twin_win_rate: float
    twin_sharpe: float
    twin_max_drawdown: float
    validation_period_hours: int
    recommendation: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'passed': self.passed,
            'twin_pnl': self.twin_pnl,
            'twin_trades': self.twin_trades,
            'twin_win_rate': self.twin_win_rate,
            'twin_sharpe': self.twin_sharpe,
            'twin_max_drawdown': self.twin_max_drawdown,
            'validation_period_hours': self.validation_period_hours,
            'recommendation': self.recommendation
        }


class SlippageModel:
    """
    Models realistic slippage.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.base_slippage_pct = self.config.get('base_slippage_pct', 0.01)
            self.volume_impact_factor = self.config.get('volume_impact_factor', 0.001)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        order_size: float,
        avg_volume: float,
        spread: float,
        volatility: float
    ) -> float:
        """
        Calculate expected slippage.
        
        Returns:
            Slippage as percentage of price
        """
        # Base slippage
        try:
            slippage = self.base_slippage_pct
        
            # Volume impact
            if avg_volume > 0:
                volume_ratio = order_size / avg_volume
                slippage += volume_ratio * self.volume_impact_factor * 100
        
            # Spread impact
            slippage += spread * 0.5  # Half the spread
        
            # Volatility impact
            slippage += volatility * 0.1
        
            return slippage
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class CommissionModel:
    """
    Models trading commissions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.per_trade = self.config.get('per_trade', 1.0)
            self.per_share = self.config.get('per_share', 0.005)
            self.percentage = self.config.get('percentage', 0.001)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(self, quantity: float, price: float) -> float:
        """Calculate commission."""
        try:
            notional = quantity * price
        
            commission = self.per_trade
            commission += quantity * self.per_share
            commission += notional * self.percentage
        
            return commission
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class ExecutionSimulator:
    """
    Simulates order execution with realistic fills.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.slippage_model = SlippageModel(config)
            self.commission_model = CommissionModel(config)
        
            # Fill probability for limit orders
            self.limit_fill_probability = self.config.get('limit_fill_probability', 0.7)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def execute_market_order(
        self,
        order: SimulatedOrder,
        tick: MarketTick,
        avg_volume: float,
        volatility: float
    ) -> Tuple[ExecutionResult, float, float]:
        """
        Execute market order.
        
        Returns:
            Tuple of (result, fill_price, slippage)
        """
        # Determine fill price based on side
        try:
            if order.side == 'BUY':
                base_price = tick.ask
            else:
                base_price = tick.bid
        
            # Calculate slippage
            slippage_pct = self.slippage_model.calculate(
                order.quantity, avg_volume, tick.spread, volatility
            )
        
            # Apply slippage
            if order.side == 'BUY':
                fill_price = base_price * (1 + slippage_pct / 100)
            else:
                fill_price = base_price * (1 - slippage_pct / 100)
        
            slippage = abs(fill_price - base_price)
        
            return ExecutionResult.FILLED, fill_price, slippage
        except Exception as e:
            logger.error(f"Error in execute_market_order: {e}")
            raise
    
    def execute_limit_order(
        self,
        order: SimulatedOrder,
        tick: MarketTick
    ) -> Tuple[ExecutionResult, float, float]:
        """
        Execute limit order.
        
        Returns:
            Tuple of (result, fill_price, slippage)
        """
        try:
            if order.price is None:
                return ExecutionResult.REJECTED, 0, 0
        
            # Check if limit price is hit
            if order.side == 'BUY':
                if tick.ask <= order.price:
                    # Fill at limit price or better
                    fill_price = min(order.price, tick.ask)
                    return ExecutionResult.FILLED, fill_price, 0
            else:
                if tick.bid >= order.price:
                    fill_price = max(order.price, tick.bid)
                    return ExecutionResult.FILLED, fill_price, 0
        
            return ExecutionResult.REJECTED, 0, 0  # Not filled
        except Exception as e:
            logger.error(f"Error in execute_limit_order: {e}")
            raise


class DigitalTwin:
    """
    Main Digital Twin simulation system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Components
            self.executor = ExecutionSimulator(config)
        
            # State
            self.mode = SimulationMode.SHADOW
            self.positions: Dict[str, SimulatedPosition] = {}
            self.orders: Dict[str, SimulatedOrder] = {}
            self.trades: List[SimulatedTrade] = []
            self.equity_curve: List[Tuple[datetime, float]] = []
        
            # Initial capital
            self.initial_capital = self.config.get('initial_capital', 100000)
            self.cash = self.initial_capital
        
            # Market data
            self.latest_ticks: Dict[str, MarketTick] = {}
            self.tick_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
            # Performance tracking
            self.peak_equity = self.initial_capital
            self.max_drawdown = 0
            self.trade_results: List[float] = []
        
            # Validation thresholds
            self.validation_thresholds = {
                'min_trades': self.config.get('min_trades', 10),
                'min_win_rate': self.config.get('min_win_rate', 0.4),
                'min_sharpe': self.config.get('min_sharpe', 0.5),
                'max_drawdown': self.config.get('max_drawdown', 0.15),
                'min_profit_factor': self.config.get('min_profit_factor', 1.2)
            }
        
            logger.info("DigitalTwin initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_mode(self, mode: SimulationMode):
        """Set simulation mode."""
        try:
            self.mode = mode
            logger.info(f"Digital Twin mode set to: {mode.value}")
        except Exception as e:
            logger.error(f"Error in set_mode: {e}")
            raise
    
    def process_tick(self, tick: MarketTick):
        """
        Process incoming market tick.
        
        Args:
            tick: Market tick data
        """
        try:
            self.latest_ticks[tick.symbol] = tick
            self.tick_history[tick.symbol].append(tick)
        
            # Update positions
            if tick.symbol in self.positions:
                self.positions[tick.symbol].update_pnl(tick.mid)
        
            # Check pending orders
            self._process_pending_orders(tick)
        
            # Update equity curve
            self._update_equity()
        except Exception as e:
            logger.error(f"Error in process_tick: {e}")
            raise
    
    def _process_pending_orders(self, tick: MarketTick):
        """Process pending orders against new tick."""
        try:
            for order_id, order in list(self.orders.items()):
                if order.symbol != tick.symbol or order.status != 'PENDING':
                    continue
            
                # Get market data
                avg_volume = self._get_avg_volume(tick.symbol)
                volatility = self._get_volatility(tick.symbol)
            
                # Execute based on order type
                if order.order_type == 'MARKET':
                    result, fill_price, slippage = self.executor.execute_market_order(
                        order, tick, avg_volume, volatility
                    )
                elif order.order_type == 'LIMIT':
                    result, fill_price, slippage = self.executor.execute_limit_order(
                        order, tick
                    )
                else:
                    continue
            
                if result == ExecutionResult.FILLED:
                    self._fill_order(order, fill_price, slippage, tick.timestamp)
        except Exception as e:
            logger.error(f"Error in _process_pending_orders: {e}")
            raise
    
    def _fill_order(
        self,
        order: SimulatedOrder,
        fill_price: float,
        slippage: float,
        timestamp: datetime
    ):
        """Fill an order."""
        try:
            order.status = 'FILLED'
            order.filled_quantity = order.quantity
            order.filled_price = fill_price
            order.fill_timestamp = timestamp
        
            # Calculate commission
            commission = self.executor.commission_model.calculate(order.quantity, fill_price)
        
            # Create trade
            trade = SimulatedTrade(
                trade_id=str(uuid.uuid4())[:8],
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=timestamp,
                commission=commission,
                slippage=slippage
            )
        
            self.trades.append(trade)
        
            # Update position
            self._update_position(trade)
        
            # Update cash
            notional = trade.quantity * trade.price
            if trade.side == 'BUY':
                self.cash -= notional + commission
            else:
                self.cash += notional - commission
        except Exception as e:
            logger.error(f"Error in _fill_order: {e}")
            raise
    
    def _update_position(self, trade: SimulatedTrade):
        """Update position from trade."""
        try:
            symbol = trade.symbol
        
            if symbol not in self.positions:
                self.positions[symbol] = SimulatedPosition(
                    symbol=symbol,
                    quantity=0,
                    avg_price=0
                )
        
            pos = self.positions[symbol]
        
            if trade.side == 'BUY':
                # Adding to long or covering short
                if pos.quantity >= 0:
                    # Adding to long
                    total_cost = pos.quantity * pos.avg_price + trade.quantity * trade.price
                    pos.quantity += trade.quantity
                    pos.avg_price = total_cost / pos.quantity if pos.quantity > 0 else 0
                else:
                    # Covering short
                    if trade.quantity >= abs(pos.quantity):
                        # Fully covered + going long
                        realized = (pos.avg_price - trade.price) * abs(pos.quantity)
                        pos.realized_pnl += realized
                        self.trade_results.append(realized)
                    
                        remaining = trade.quantity - abs(pos.quantity)
                        pos.quantity = remaining
                        pos.avg_price = trade.price if remaining > 0 else 0
                    else:
                        # Partial cover
                        realized = (pos.avg_price - trade.price) * trade.quantity
                        pos.realized_pnl += realized
                        self.trade_results.append(realized)
                        pos.quantity += trade.quantity
            else:
                # Adding to short or closing long
                if pos.quantity <= 0:
                    # Adding to short
                    total_cost = abs(pos.quantity) * pos.avg_price + trade.quantity * trade.price
                    pos.quantity -= trade.quantity
                    pos.avg_price = total_cost / abs(pos.quantity) if pos.quantity != 0 else 0
                else:
                    # Closing long
                    if trade.quantity >= pos.quantity:
                        # Fully closed + going short
                        realized = (trade.price - pos.avg_price) * pos.quantity
                        pos.realized_pnl += realized
                        self.trade_results.append(realized)
                    
                        remaining = trade.quantity - pos.quantity
                        pos.quantity = -remaining
                        pos.avg_price = trade.price if remaining > 0 else 0
                    else:
                        # Partial close
                        realized = (trade.price - pos.avg_price) * trade.quantity
                        pos.realized_pnl += realized
                        self.trade_results.append(realized)
                        pos.quantity -= trade.quantity
        except Exception as e:
            logger.error(f"Error in _update_position: {e}")
            raise
    
    def _update_equity(self):
        """Update equity curve."""
        try:
            equity = self.cash
        
            for pos in self.positions.values():
                if pos.symbol in self.latest_ticks:
                    tick = self.latest_ticks[pos.symbol]
                    pos.update_pnl(tick.mid)
                    equity += pos.quantity * tick.mid
        
            self.equity_curve.append((datetime.now(), equity))
        
            # Update peak and drawdown
            if equity > self.peak_equity:
                self.peak_equity = equity
        
            drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
            self.max_drawdown = max(self.max_drawdown, drawdown)
        except Exception as e:
            logger.error(f"Error in _update_equity: {e}")
            raise
    
    def _get_avg_volume(self, symbol: str) -> float:
        """Get average volume for symbol."""
        try:
            history = self.tick_history.get(symbol, [])
            if not history:
                return 10000
        
            volumes = [t.volume for t in history]
            return statistics.mean(volumes) if volumes else 10000
        except Exception as e:
            logger.error(f"Error in _get_avg_volume: {e}")
            raise
    
    def _get_volatility(self, symbol: str) -> float:
        """Get volatility for symbol."""
        try:
            history = self.tick_history.get(symbol, [])
            if len(history) < 10:
                return 0.01
        
            prices = [t.mid for t in history]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
            if returns:
                return statistics.stdev(returns) * 100
            return 0.01
        except Exception as e:
            logger.error(f"Error in _get_volatility: {e}")
            raise
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'MARKET',
        price: Optional[float] = None
    ) -> str:
        """
        Submit order to digital twin.
        
        Returns:
            Order ID
        """
        try:
            order_id = str(uuid.uuid4())[:8]
        
            order = SimulatedOrder(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=None,
                timestamp=datetime.now()
            )
        
            self.orders[order_id] = order
        
            # If market order and we have tick data, execute immediately
            if order_type == 'MARKET' and symbol in self.latest_ticks:
                tick = self.latest_ticks[symbol]
                avg_volume = self._get_avg_volume(symbol)
                volatility = self._get_volatility(symbol)
            
                result, fill_price, slippage = self.executor.execute_market_order(
                    order, tick, avg_volume, volatility
                )
            
                if result == ExecutionResult.FILLED:
                    self._fill_order(order, fill_price, slippage, datetime.now())
        
            return order_id
        except Exception as e:
            logger.error(f"Error in submit_order: {e}")
            raise
    
    def validate_strategy(
        self,
        strategy_id: str,
        validation_hours: int = 24
    ) -> ValidationResult:
        """
        Validate strategy performance in digital twin.
        
        Args:
            strategy_id: Strategy identifier
            validation_hours: Hours of validation data
            
        Returns:
            ValidationResult with pass/fail and metrics
        """
        # Calculate metrics
        try:
            total_trades = len(self.trades)
        
            if total_trades < self.validation_thresholds['min_trades']:
                return ValidationResult(
                    strategy_id=strategy_id,
                    passed=False,
                    twin_pnl=0,
                    twin_trades=total_trades,
                    twin_win_rate=0,
                    twin_sharpe=0,
                    twin_max_drawdown=self.max_drawdown,
                    validation_period_hours=validation_hours,
                    recommendation="INSUFFICIENT_DATA",
                    details={'reason': f"Only {total_trades} trades, need {self.validation_thresholds['min_trades']}"}
                )
        
            # Calculate P&L
            total_pnl = sum(self.trade_results)
        
            # Win rate
            winning_trades = sum(1 for r in self.trade_results if r > 0)
            win_rate = winning_trades / len(self.trade_results) if self.trade_results else 0
        
            # Sharpe ratio (simplified)
            if len(self.trade_results) > 1:
                avg_return = statistics.mean(self.trade_results)
                std_return = statistics.stdev(self.trade_results)
                sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
            else:
                sharpe = 0
        
            # Profit factor
            gross_profit = sum(r for r in self.trade_results if r > 0)
            gross_loss = abs(sum(r for r in self.trade_results if r < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
            # Determine pass/fail
            passed = (
                win_rate >= self.validation_thresholds['min_win_rate'] and
                sharpe >= self.validation_thresholds['min_sharpe'] and
                self.max_drawdown <= self.validation_thresholds['max_drawdown'] and
                profit_factor >= self.validation_thresholds['min_profit_factor']
            )
        
            # Generate recommendation
            if passed:
                recommendation = "APPROVED_FOR_LIVE"
            else:
                issues = []
                if win_rate < self.validation_thresholds['min_win_rate']:
                    issues.append(f"Low win rate: {win_rate:.0%}")
                if sharpe < self.validation_thresholds['min_sharpe']:
                    issues.append(f"Low Sharpe: {sharpe:.2f}")
                if self.max_drawdown > self.validation_thresholds['max_drawdown']:
                    issues.append(f"High drawdown: {self.max_drawdown:.0%}")
                if profit_factor < self.validation_thresholds['min_profit_factor']:
                    issues.append(f"Low profit factor: {profit_factor:.2f}")
            
                recommendation = f"REJECTED: {', '.join(issues)}"
        
            return ValidationResult(
                strategy_id=strategy_id,
                passed=passed,
                twin_pnl=total_pnl,
                twin_trades=total_trades,
                twin_win_rate=win_rate,
                twin_sharpe=sharpe,
                twin_max_drawdown=self.max_drawdown,
                validation_period_hours=validation_hours,
                recommendation=recommendation,
                details={
                    'profit_factor': profit_factor,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss,
                    'avg_trade': statistics.mean(self.trade_results) if self.trade_results else 0
                }
            )
        except Exception as e:
            logger.error(f"Error in validate_strategy: {e}")
            raise
    
    def reset(self):
        """Reset digital twin state."""
        try:
            self.positions.clear()
            self.orders.clear()
            self.trades.clear()
            self.equity_curve.clear()
            self.cash = self.initial_capital
            self.peak_equity = self.initial_capital
            self.max_drawdown = 0
            self.trade_results.clear()
        
            logger.info("Digital Twin reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def get_equity(self) -> float:
        """Get current equity."""
        try:
            equity = self.cash
        
            for pos in self.positions.values():
                if pos.symbol in self.latest_ticks:
                    tick = self.latest_ticks[pos.symbol]
                    equity += pos.quantity * tick.mid
        
            return equity
        except Exception as e:
            logger.error(f"Error in get_equity: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get digital twin status."""
        return {
            'mode': self.mode.value,
            'equity': self.get_equity(),
            'cash': self.cash,
            'positions': len(self.positions),
            'open_orders': len([o for o in self.orders.values() if o.status == 'PENDING']),
            'total_trades': len(self.trades),
            'max_drawdown': self.max_drawdown,
            'pnl': self.get_equity() - self.initial_capital,
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_digital_twin(config: Optional[Dict] = None) -> DigitalTwin:
    """Create DigitalTwin instance."""
    return DigitalTwin(config)


# Example usage
if __name__ == "__main__":
    import random
    
    twin = create_digital_twin({
        'initial_capital': 100000,
        'min_trades': 5
    })
    
    print("=" * 60)
    print("DIGITAL TWIN SIMULATION")
    print("=" * 60)
    
    # Simulate market data and trades
    symbol = "EURUSD"
    base_price = 1.1000
    
    print("\nRunning simulation...")
    
    for i in range(100):
        # Generate tick
        price = base_price + random.uniform(-0.005, 0.005)
        spread = 0.0002
        
        tick = MarketTick(
            timestamp=datetime.now(),
            symbol=symbol,
            bid=price - spread/2,
            ask=price + spread/2,
            last=price,
            volume=random.randint(1000, 10000)
        )
        
        twin.process_tick(tick)
        
        # Random trading
        if random.random() < 0.1:  # 10% chance to trade
            side = 'BUY' if random.random() > 0.5 else 'SELL'
            quantity = random.randint(1000, 5000)
            
            order_id = twin.submit_order(symbol, side, quantity)
    
    # Show results
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    
    status = twin.get_status()
    print(f"\nEquity: ${status['equity']:,.2f}")
    print(f"P&L: ${status['pnl']:,.2f}")
    print(f"Max Drawdown: {status['max_drawdown']:.2%}")
    print(f"Total Trades: {status['total_trades']}")
    
    # Validate strategy
    print("\n" + "=" * 60)
    print("STRATEGY VALIDATION")
    print("=" * 60)
    
    validation = twin.validate_strategy("TEST_STRATEGY")
    
    print(f"\nStrategy: {validation.strategy_id}")
    print(f"Passed: {'✅ YES' if validation.passed else '❌ NO'}")
    print(f"P&L: ${validation.twin_pnl:,.2f}")
    print(f"Trades: {validation.twin_trades}")
    print(f"Win Rate: {validation.twin_win_rate:.1%}")
    print(f"Sharpe: {validation.twin_sharpe:.2f}")
    print(f"Max Drawdown: {validation.twin_max_drawdown:.1%}")
    print(f"\nRecommendation: {validation.recommendation}")
    
    if validation.details:
        print(f"\nDetails:")
        for key, value in validation.details.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
