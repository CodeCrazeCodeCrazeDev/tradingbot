"""
Real-Time P&L Calculator
========================

Tick-by-tick P&L calculation with:
- Unrealized P&L tracking
- Realized P&L tracking
- Commission tracking
- Swap/rollover tracking
- Multi-currency support
- Performance attribution
- Risk metrics

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum, auto
from collections import defaultdict
import threading
import numpy as np
from typing import Set
import numpy

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


class PnLType(Enum):
    """P&L types"""
    UNREALIZED = "unrealized"
    REALIZED = "realized"
    COMMISSION = "commission"
    SWAP = "swap"
    TOTAL = "total"


@dataclass
class PositionPnL:
    """P&L for a single position"""
    position_id: str
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    
    # P&L components
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    
    # Pip values
    pips: float = 0.0
    pip_value: float = 10.0  # Default for standard lot
    
    # Timestamps
    entry_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    
    # Performance
    max_profit: float = 0.0
    max_loss: float = 0.0
    time_in_profit_seconds: float = 0.0
    time_in_loss_seconds: float = 0.0
    
    @property
    def total_pnl(self) -> float:
        return self.unrealized_pnl + self.realized_pnl - self.commission + self.swap
    
    @property
    def net_pnl(self) -> float:
        return self.unrealized_pnl - self.commission + self.swap
    
    @property
    def return_pct(self) -> float:
        position_value = self.quantity * self.entry_price
        if position_value == 0:
            return 0.0
        return (self.unrealized_pnl / position_value) * 100
    
    @property
    def duration(self) -> timedelta:
        return datetime.now() - self.entry_time
    
    def to_dict(self) -> Dict:
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'commission': self.commission,
            'swap': self.swap,
            'total_pnl': self.total_pnl,
            'pips': self.pips,
            'return_pct': self.return_pct,
            'duration_seconds': self.duration.total_seconds(),
            'max_profit': self.max_profit,
            'max_loss': self.max_loss
        }


@dataclass
class PortfolioPnL:
    """Aggregate P&L for entire portfolio"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Aggregate P&L
    total_unrealized: float = 0.0
    total_realized: float = 0.0
    total_commission: float = 0.0
    total_swap: float = 0.0
    
    # By symbol
    pnl_by_symbol: Dict[str, float] = field(default_factory=dict)
    
    # By strategy
    pnl_by_strategy: Dict[str, float] = field(default_factory=dict)
    
    # Performance metrics
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    
    # Risk metrics
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Position counts
    open_positions: int = 0
    winning_positions: int = 0
    losing_positions: int = 0
    
    @property
    def total_pnl(self) -> float:
        return self.total_unrealized + self.total_realized - self.total_commission + self.total_swap
    
    @property
    def win_rate(self) -> float:
        total = self.winning_positions + self.losing_positions
        if total == 0:
            return 0.0
        return (self.winning_positions / total) * 100
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_unrealized': self.total_unrealized,
            'total_realized': self.total_realized,
            'total_commission': self.total_commission,
            'total_swap': self.total_swap,
            'total_pnl': self.total_pnl,
            'pnl_by_symbol': self.pnl_by_symbol,
            'pnl_by_strategy': self.pnl_by_strategy,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'monthly_pnl': self.monthly_pnl,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'open_positions': self.open_positions,
            'win_rate': self.win_rate
        }


@dataclass
class PnLSnapshot:
    """Point-in-time P&L snapshot"""
    timestamp: datetime
    equity: float
    balance: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    free_margin: float


class RealTimePnLCalculator:
    """
    Real-time P&L calculation engine
    """
    
    # Pip values for common pairs (per standard lot)
    PIP_VALUES = {
        'EURUSD': 10.0, 'GBPUSD': 10.0, 'AUDUSD': 10.0, 'NZDUSD': 10.0,
        'USDJPY': 9.0, 'USDCHF': 10.0, 'USDCAD': 7.5,
        'EURGBP': 12.0, 'EURJPY': 9.0, 'GBPJPY': 9.0
    }
    
    # Pip sizes
    PIP_SIZES = {
        'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'AUDUSD': 0.0001, 'NZDUSD': 0.0001,
        'USDJPY': 0.01, 'USDCHF': 0.0001, 'USDCAD': 0.0001,
        'EURGBP': 0.0001, 'EURJPY': 0.01, 'GBPJPY': 0.01
    }
    
    def __init__(
        self,
        account_currency: str = "USD",
        update_interval_ms: int = 100
    ):
        self.account_currency = account_currency
        self.update_interval = update_interval_ms / 1000
        
        # Position tracking
        self.positions: Dict[str, PositionPnL] = {}
        
        # Price cache
        self.prices: Dict[str, float] = {}
        
        # P&L history
        self.pnl_history: List[PnLSnapshot] = []
        self.max_history_size = 10000
        
        # Daily tracking
        self.daily_start_equity: float = 0.0
        self.daily_realized: float = 0.0
        self.daily_trades: int = 0
        
        # Peak tracking for drawdown
        self.peak_equity: float = 0.0
        
        # Callbacks
        self.on_pnl_update: List[Callable] = []
        self.on_threshold_breach: List[Callable] = []
        
        # Thresholds
        self.profit_threshold: Optional[float] = None
        self.loss_threshold: Optional[float] = None
        self.drawdown_threshold: float = 0.20  # 20%
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._update_task = None
        
        logger.info("RealTimePnLCalculator initialized")
    
    def add_position(
        self,
        position_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        commission: float = 0.0,
        strategy_id: str = ""
    ) -> PositionPnL:
        """Add a new position to track"""
        with self._lock:
            pip_value = self.PIP_VALUES.get(symbol, 10.0)
            
            position = PositionPnL(
                position_id=position_id,
                symbol=symbol,
                side=side.lower(),
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,
                commission=commission,
                pip_value=pip_value * quantity
            )
            
            self.positions[position_id] = position
            
            logger.info(f"Position added: {position_id} {symbol} {side} {quantity}")
            
            return position
    
    def update_price(self, symbol: str, price: float):
        """Update price for a symbol"""
        with self._lock:
            self.prices[symbol] = price
            
            # Update all positions for this symbol
            for position in self.positions.values():
                if position.symbol == symbol:
                    self._update_position_pnl(position, price)
    
    def update_prices_batch(self, prices: Dict[str, float]):
        """Update multiple prices at once"""
        with self._lock:
            self.prices.update(prices)
            
            for position in self.positions.values():
                if position.symbol in prices:
                    self._update_position_pnl(position, prices[position.symbol])
    
    def _update_position_pnl(self, position: PositionPnL, current_price: float):
        """Update P&L for a single position"""
        old_pnl = position.unrealized_pnl
        
        position.current_price = current_price
        position.last_update = datetime.now()
        
        # Calculate pip difference
        pip_size = self.PIP_SIZES.get(position.symbol, 0.0001)
        
        if position.side == "long":
            price_diff = current_price - position.entry_price
        else:
            price_diff = position.entry_price - current_price
        
        position.pips = price_diff / pip_size
        position.unrealized_pnl = position.pips * position.pip_value
        
        # Track max profit/loss
        if position.unrealized_pnl > position.max_profit:
            position.max_profit = position.unrealized_pnl
        if position.unrealized_pnl < position.max_loss:
            position.max_loss = position.unrealized_pnl
        
        # Track time in profit/loss
        if position.unrealized_pnl > 0:
            position.time_in_profit_seconds += self.update_interval
        elif position.unrealized_pnl < 0:
            position.time_in_loss_seconds += self.update_interval
    
    def close_position(
        self,
        position_id: str,
        close_price: float,
        commission: float = 0.0
    ) -> Optional[PositionPnL]:
        """Close a position and realize P&L"""
        with self._lock:
            position = self.positions.get(position_id)
            if not position:
                logger.warning(f"Position not found: {position_id}")
                return None
            
            # Final P&L calculation
            self._update_position_pnl(position, close_price)
            
            # Move unrealized to realized
            position.realized_pnl = position.unrealized_pnl
            position.unrealized_pnl = 0.0
            position.commission += commission
            
            # Update daily tracking
            self.daily_realized += position.realized_pnl - position.commission
            self.daily_trades += 1
            
            # Remove from active positions
            del self.positions[position_id]
            
            logger.info(f"Position closed: {position_id} P&L: {position.realized_pnl:.2f}")
            
            return position
    
    def add_swap(self, position_id: str, swap_amount: float):
        """Add swap/rollover to position"""
        with self._lock:
            position = self.positions.get(position_id)
            if position:
                position.swap += swap_amount
    
    def get_position_pnl(self, position_id: str) -> Optional[PositionPnL]:
        """Get P&L for a specific position"""
        return self.positions.get(position_id)
    
    def get_portfolio_pnl(self) -> PortfolioPnL:
        """Get aggregate portfolio P&L"""
        with self._lock:
            portfolio = PortfolioPnL()
            
            pnl_by_symbol = defaultdict(float)
            
            for position in self.positions.values():
                portfolio.total_unrealized += position.unrealized_pnl
                portfolio.total_commission += position.commission
                portfolio.total_swap += position.swap
                
                pnl_by_symbol[position.symbol] += position.unrealized_pnl
                
                if position.unrealized_pnl > 0:
                    portfolio.winning_positions += 1
                elif position.unrealized_pnl < 0:
                    portfolio.losing_positions += 1
            
            portfolio.total_realized = self.daily_realized
            portfolio.pnl_by_symbol = dict(pnl_by_symbol)
            portfolio.open_positions = len(self.positions)
            portfolio.daily_pnl = portfolio.total_pnl
            
            # Calculate drawdown
            current_equity = self.daily_start_equity + portfolio.total_pnl
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
            if self.peak_equity > 0:
                portfolio.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
                portfolio.max_drawdown = max(portfolio.max_drawdown, portfolio.current_drawdown)
            
            return portfolio
    
    def get_pnl_by_symbol(self) -> Dict[str, Dict[str, float]]:
        """Get P&L breakdown by symbol"""
        with self._lock:
            result = defaultdict(lambda: {
                'unrealized': 0.0,
                'realized': 0.0,
                'commission': 0.0,
                'swap': 0.0,
                'positions': 0
            })
            
            for position in self.positions.values():
                result[position.symbol]['unrealized'] += position.unrealized_pnl
                result[position.symbol]['commission'] += position.commission
                result[position.symbol]['swap'] += position.swap
                result[position.symbol]['positions'] += 1
            
            return dict(result)
    
    def get_pnl_summary(self) -> Dict[str, Any]:
        """Get comprehensive P&L summary"""
        portfolio = self.get_portfolio_pnl()
        by_symbol = self.get_pnl_by_symbol()
        
        return {
            'portfolio': portfolio.to_dict(),
            'by_symbol': by_symbol,
            'positions': [p.to_dict() for p in self.positions.values()],
            'daily_trades': self.daily_trades,
            'peak_equity': self.peak_equity
        }
    
    def set_daily_start(self, equity: float):
        """Set starting equity for the day"""
        self.daily_start_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
        self.daily_realized = 0.0
        self.daily_trades = 0
    
    def set_thresholds(
        self,
        profit_threshold: Optional[float] = None,
        loss_threshold: Optional[float] = None,
        drawdown_threshold: Optional[float] = None
    ):
        """Set P&L thresholds for alerts"""
        if profit_threshold is not None:
            self.profit_threshold = profit_threshold
        if loss_threshold is not None:
            self.loss_threshold = loss_threshold
        if drawdown_threshold is not None:
            self.drawdown_threshold = drawdown_threshold
    
    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any thresholds are breached"""
        breaches = []
        portfolio = self.get_portfolio_pnl()
        
        if self.profit_threshold and portfolio.total_pnl >= self.profit_threshold:
            breaches.append({
                'type': 'profit_target',
                'threshold': self.profit_threshold,
                'current': portfolio.total_pnl
            })
        
        if self.loss_threshold and portfolio.total_pnl <= -self.loss_threshold:
            breaches.append({
                'type': 'loss_limit',
                'threshold': self.loss_threshold,
                'current': portfolio.total_pnl
            })
        
        if portfolio.current_drawdown >= self.drawdown_threshold:
            breaches.append({
                'type': 'drawdown_limit',
                'threshold': self.drawdown_threshold,
                'current': portfolio.current_drawdown
            })
        
        return breaches
    
    def take_snapshot(self, equity: float, balance: float, margin_used: float) -> PnLSnapshot:
        """Take a P&L snapshot"""
        portfolio = self.get_portfolio_pnl()
        
        snapshot = PnLSnapshot(
            timestamp=datetime.now(),
            equity=equity,
            balance=balance,
            unrealized_pnl=portfolio.total_unrealized,
            realized_pnl=portfolio.total_realized,
            margin_used=margin_used,
            free_margin=equity - margin_used
        )
        
        self.pnl_history.append(snapshot)
        
        # Trim history
        if len(self.pnl_history) > self.max_history_size:
            self.pnl_history = self.pnl_history[-self.max_history_size:]
        
        return snapshot
    
    def get_pnl_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PnLSnapshot]:
        """Get P&L history within time range"""
        history = self.pnl_history
        
        if start_time:
            history = [s for s in history if s.timestamp >= start_time]
        if end_time:
            history = [s for s in history if s.timestamp <= end_time]
        
        return history
    
    def calculate_statistics(self) -> Dict[str, float]:
        """Calculate P&L statistics"""
        if not self.pnl_history:
            return {}
        
        pnls = [s.unrealized_pnl + s.realized_pnl for s in self.pnl_history]
        
        if len(pnls) < 2:
            return {'mean': np.mean(pnls) if pnls else 0}
        
        returns = np.diff(pnls)
        
        return {
            'mean_pnl': np.mean(pnls),
            'std_pnl': np.std(pnls),
            'max_pnl': np.max(pnls),
            'min_pnl': np.min(pnls),
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'sharpe': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0,
            'skewness': float(np.mean(((returns - np.mean(returns)) / np.std(returns)) ** 3)) if np.std(returns) > 0 else 0,
            'kurtosis': float(np.mean(((returns - np.mean(returns)) / np.std(returns)) ** 4) - 3) if np.std(returns) > 0 else 0
        }
    
    async def start_realtime_updates(self):
        """Start real-time P&L updates"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Real-time P&L updates started")
    
    async def stop_realtime_updates(self):
        """Stop real-time P&L updates"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Real-time P&L updates stopped")
    
    async def _update_loop(self):
        """Background update loop"""
        while self._running:
            try:
                # Check thresholds
                breaches = self.check_thresholds()
                if breaches:
                    for callback in self.on_threshold_breach:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(breaches)
                            else:
                                callback(breaches)
                        except Exception as e:
                            logger.error(f"Threshold callback error: {e}")
                
                # Fire update callbacks
                portfolio = self.get_portfolio_pnl()
                for callback in self.on_pnl_update:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(portfolio)
                        else:
                            callback(portfolio)
                    except Exception as e:
                        logger.error(f"P&L update callback error: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"P&L update error: {e}")
                await asyncio.sleep(1)
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback"""
        if event_type == 'pnl_update':
            self.on_pnl_update.append(callback)
        elif event_type == 'threshold_breach':
            self.on_threshold_breach.append(callback)


# Singleton instance
_pnl_calculator: Optional[RealTimePnLCalculator] = None


def get_pnl_calculator() -> RealTimePnLCalculator:
    """Get or create P&L calculator singleton"""
    global _pnl_calculator
    if _pnl_calculator is None:
        _pnl_calculator = RealTimePnLCalculator()
    return _pnl_calculator


# Export
__all__ = [
    'RealTimePnLCalculator',
    'PositionPnL',
    'PortfolioPnL',
    'PnLSnapshot',
    'PnLType',
    'get_pnl_calculator'
]
