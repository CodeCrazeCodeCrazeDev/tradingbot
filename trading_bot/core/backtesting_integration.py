"""
Backtesting Integration Module
Integrates backtesting capabilities with the main trading system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from trading_bot.constants import (
    MIN_BACKTEST_DAYS,
    RECOMMENDED_BACKTEST_DAYS,
    MIN_TRADES_FOR_STATISTICS,
    MIN_WIN_RATE,
    MIN_PROFIT_FACTOR
)

logger = logging.getLogger(__name__)


class BacktestMode(Enum):
    """Backtest execution mode"""
    FAST = "fast"  # Skip detailed logging
    NORMAL = "normal"  # Standard execution
    DETAILED = "detailed"  # Full logging and analysis


@dataclass
class BacktestConfig:
    """Backtest configuration"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    symbols: List[str] = field(default_factory=lambda: ['BTCUSDT'])
    mode: BacktestMode = BacktestMode.NORMAL
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    max_positions: int = 10
    enable_shorting: bool = True
    risk_per_trade: float = 0.02
    
    def validate(self) -> None:
        """Validate configuration"""
        try:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        
            days = (self.end_date - self.start_date).days
            if days < MIN_BACKTEST_DAYS:
                logger.warning(
                    f"Backtest period ({days} days) is less than minimum "
                    f"recommended ({MIN_BACKTEST_DAYS} days)"
                )
        
            if self.initial_capital <= 0:
                raise ValueError("initial_capital must be positive")
        
            if not self.symbols:
                raise ValueError("symbols list cannot be empty")
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


@dataclass
class Trade:
    """Backtest trade record"""
    trade_id: str
    symbol: str
    direction: str  # 'long' or 'short'
    entry_time: datetime
    entry_price: float
    quantity: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    commission: float = 0.0
    slippage: float = 0.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResults:
    """Backtest results summary"""
    config: BacktestConfig
    trades: List[Trade]
    equity_curve: pd.DataFrame
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    avg_trade_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    avg_trade_duration_hours: float = 0.0
    total_commission: float = 0.0
    total_slippage: float = 0.0
    
    final_equity: float = 0.0
    return_percent: float = 0.0
    
    def calculate_metrics(self) -> None:
        """Calculate all performance metrics"""
        try:
            if not self.trades:
                return
        
            closed_trades = [t for t in self.trades if t.exit_time is not None]
            self.total_trades = len(closed_trades)
        
            if self.total_trades == 0:
                return
        
            # Win/Loss statistics
            winning = [t for t in closed_trades if t.pnl and t.pnl > 0]
            losing = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
            self.winning_trades = len(winning)
            self.losing_trades = len(losing)
            self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
            # P&L statistics
            self.total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
            self.gross_profit = sum(t.pnl for t in winning)
            self.gross_loss = abs(sum(t.pnl for t in losing))
            self.profit_factor = self.gross_profit / self.gross_loss if self.gross_loss > 0 else 0
        
            self.avg_trade_pnl = self.total_pnl / self.total_trades
            self.avg_win = self.gross_profit / self.winning_trades if self.winning_trades > 0 else 0
            self.avg_loss = self.gross_loss / self.losing_trades if self.losing_trades > 0 else 0
        
            self.largest_win = max((t.pnl for t in winning), default=0)
            self.largest_loss = min((t.pnl for t in losing), default=0)
        
            # Duration
            durations = [
                (t.exit_time - t.entry_time).total_seconds() / 3600
                for t in closed_trades if t.exit_time
            ]
            self.avg_trade_duration_hours = np.mean(durations) if durations else 0
        
            # Costs
            self.total_commission = sum(t.commission for t in closed_trades)
            self.total_slippage = sum(t.slippage for t in closed_trades)
        
            # Equity curve metrics
            if not self.equity_curve.empty:
                equity = self.equity_curve['equity'].values
                self.final_equity = equity[-1]
                self.return_percent = ((self.final_equity - self.config.initial_capital) / 
                                       self.config.initial_capital * 100)
            
                # Drawdown
                running_max = np.maximum.accumulate(equity)
                drawdown = (equity - running_max) / running_max * 100
                self.max_drawdown_percent = abs(drawdown.min())
                self.max_drawdown = (running_max.max() - equity[drawdown.argmin()])
            
                # Risk-adjusted returns
                returns = self.equity_curve['equity'].pct_change().dropna()
                if len(returns) > 1:
                    self.sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252) 
                                        if returns.std() > 0 else 0)
                
                    negative_returns = returns[returns < 0]
                    self.sortino_ratio = (returns.mean() / negative_returns.std() * np.sqrt(252)
                                         if len(negative_returns) > 0 and negative_returns.std() > 0 else 0)
                
                    self.calmar_ratio = (self.return_percent / self.max_drawdown_percent 
                                        if self.max_drawdown_percent > 0 else 0)
        except Exception as e:
            logger.error(f"Error in calculate_metrics: {e}")
            raise
    
    def is_profitable(self) -> bool:
        """Check if backtest is profitable"""
        return self.total_pnl > 0 and self.win_rate >= MIN_WIN_RATE and self.profit_factor >= MIN_PROFIT_FACTOR
    
    def get_summary(self) -> Dict[str, Any]:
        """Get results summary"""
        return {
            'period': f"{self.config.start_date.date()} to {self.config.end_date.date()}",
            'total_trades': self.total_trades,
            'win_rate': f"{self.win_rate:.2%}",
            'profit_factor': f"{self.profit_factor:.2f}",
            'total_pnl': f"${self.total_pnl:,.2f}",
            'return': f"{self.return_percent:.2f}%",
            'max_drawdown': f"{self.max_drawdown_percent:.2f}%",
            'sharpe_ratio': f"{self.sharpe_ratio:.2f}",
            'avg_trade': f"${self.avg_trade_pnl:.2f}",
            'final_equity': f"${self.final_equity:,.2f}"
        }


class BacktestEngine:
    """
    Backtesting Engine
    
    Runs strategy backtests with historical data.
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize backtest engine
        
        Args:
            config: Backtest configuration
        """
        try:
            config.validate()
            self.config = config
        
            self.equity = config.initial_capital
            self.positions: Dict[str, Trade] = {}
            self.closed_trades: List[Trade] = []
            self.equity_history: List[Dict[str, Any]] = []
        
            self.trade_counter = 0
        
            logger.info(f"BacktestEngine initialized: {config.start_date.date()} to {config.end_date.date()}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def run(
        self,
        strategy: Callable,
        data_provider: Callable
    ) -> BacktestResults:
        """
        Run backtest
        
        Args:
            strategy: Strategy function that generates signals
            data_provider: Function that provides historical data
            
        Returns:
            BacktestResults with performance metrics
        """
        try:
            logger.info("Starting backtest...")
        
            # Get historical data
            data = await data_provider(
                self.config.symbols,
                self.config.start_date,
                self.config.end_date
            )
        
            # Run backtest loop
            for timestamp, market_data in self._iterate_data(data):
                # Update open positions
                self._update_positions(timestamp, market_data)
            
                # Generate signals from strategy
                signals = await strategy(market_data, self.positions, self.equity)
            
                # Execute signals
                for signal in signals:
                    self._execute_signal(timestamp, signal, market_data)
            
                # Record equity
                self._record_equity(timestamp)
        
            # Close remaining positions
            self._close_all_positions(self.config.end_date, data)
        
            # Create results
            results = self._create_results()
        
            logger.info(f"Backtest complete: {results.total_trades} trades, "
                       f"{results.win_rate:.1%} win rate, "
                       f"${results.total_pnl:,.2f} P&L")
        
            return results
        except Exception as e:
            logger.error(f"Error in run: {e}")
            raise
    
    def _iterate_data(self, data: Dict[str, pd.DataFrame]):
        """Iterate through historical data"""
        # Combine all symbol data by timestamp
        try:
            all_timestamps = set()
            for df in data.values():
                all_timestamps.update(df.index)
        
            for timestamp in sorted(all_timestamps):
                market_data = {}
                for symbol, df in data.items():
                    if timestamp in df.index:
                        market_data[symbol] = df.loc[timestamp].to_dict()
            
                if market_data:
                    yield timestamp, market_data
        except Exception as e:
            logger.error(f"Error in _iterate_data: {e}")
            raise
    
    def _execute_signal(
        self,
        timestamp: datetime,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> None:
        """Execute trading signal"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
        
            # Check if we can open new position
            if len(self.positions) >= self.config.max_positions:
                return
        
            if symbol in self.positions:
                return  # Already have position
        
            # Calculate position size
            risk_amount = self.equity * self.config.risk_per_trade
            price = signal.get('price', market_data[symbol]['close'])
            stop_loss = signal.get('stop_loss', price * 0.98)
        
            risk_per_unit = abs(price - stop_loss)
            if risk_per_unit == 0:
                return
        
            quantity = risk_amount / risk_per_unit
        
            # Apply slippage
            if direction == 'long':
                entry_price = price * (1 + self.config.slippage)
            else:
                entry_price = price * (1 - self.config.slippage)
        
            # Calculate commission
            position_value = entry_price * quantity
            commission = position_value * self.config.commission
        
            # Create trade
            self.trade_counter += 1
            trade = Trade(
                trade_id=f"T{self.trade_counter:06d}",
                symbol=symbol,
                direction=direction,
                entry_time=timestamp,
                entry_price=entry_price,
                quantity=quantity,
                commission=commission,
                slippage=position_value * self.config.slippage,
                metadata=signal.get('metadata', {})
            )
        
            self.positions[symbol] = trade
            self.equity -= commission
        
            if self.config.mode == BacktestMode.DETAILED:
                logger.debug(f"Opened {direction} {symbol} @ {entry_price:.2f} x {quantity:.4f}")
        except Exception as e:
            logger.error(f"Error in _execute_signal: {e}")
            raise
    
    def _update_positions(self, timestamp: datetime, market_data: Dict[str, Any]) -> None:
        """Update open positions"""
        try:
            to_close = []
        
            for symbol, trade in self.positions.items():
                if symbol not in market_data:
                    continue
            
                current_price = market_data[symbol]['close']
            
                # Check stop loss / take profit
                if trade.direction == 'long':
                    pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    pnl = (trade.entry_price - current_price) * trade.quantity
            
                # Simple exit logic (can be enhanced)
                if pnl < -trade.entry_price * trade.quantity * 0.02:  # 2% stop loss
                    to_close.append((symbol, current_price, "stop_loss"))
                elif pnl > trade.entry_price * trade.quantity * 0.04:  # 4% take profit
                    to_close.append((symbol, current_price, "take_profit"))
        
            # Close positions
            for symbol, price, reason in to_close:
                self._close_position(symbol, timestamp, price, reason)
        except Exception as e:
            logger.error(f"Error in _update_positions: {e}")
            raise
    
    def _close_position(
        self,
        symbol: str,
        timestamp: datetime,
        price: float,
        reason: str = ""
    ) -> None:
        """Close position"""
        try:
            if symbol not in self.positions:
                return
        
            trade = self.positions[symbol]
        
            # Apply slippage
            if trade.direction == 'long':
                exit_price = price * (1 - self.config.slippage)
            else:
                exit_price = price * (1 + self.config.slippage)
        
            # Calculate P&L
            if trade.direction == 'long':
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:
                pnl = (trade.entry_price - exit_price) * trade.quantity
        
            # Commission
            position_value = exit_price * trade.quantity
            commission = position_value * self.config.commission
        
            pnl -= commission
            pnl -= trade.commission
        
            # Update trade
            trade.exit_time = timestamp
            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
            trade.commission += commission
            trade.reason = reason
        
            self.equity += (trade.entry_price * trade.quantity) + pnl
            self.closed_trades.append(trade)
            del self.positions[symbol]
        
            if self.config.mode == BacktestMode.DETAILED:
                logger.debug(f"Closed {symbol} @ {exit_price:.2f}, P&L: ${pnl:.2f} ({reason})")
        except Exception as e:
            logger.error(f"Error in _close_position: {e}")
            raise
    
    def _close_all_positions(self, timestamp: datetime, data: Dict[str, pd.DataFrame]) -> None:
        """Close all remaining positions"""
        try:
            for symbol in list(self.positions.keys()):
                if symbol in data and not data[symbol].empty:
                    price = data[symbol].iloc[-1]['close']
                    self._close_position(symbol, timestamp, price, "backtest_end")
        except Exception as e:
            logger.error(f"Error in _close_all_positions: {e}")
            raise
    
    def _record_equity(self, timestamp: datetime) -> None:
        """Record current equity"""
        try:
            self.equity_history.append({
                'timestamp': timestamp,
                'equity': self.equity,
                'positions': len(self.positions)
            })
        except Exception as e:
            logger.error(f"Error in _record_equity: {e}")
            raise
    
    def _create_results(self) -> BacktestResults:
        """Create backtest results"""
        try:
            equity_df = pd.DataFrame(self.equity_history)
            if not equity_df.empty:
                equity_df.set_index('timestamp', inplace=True)
        
            results = BacktestResults(
                config=self.config,
                trades=self.closed_trades,
                equity_curve=equity_df
            )
        
            results.calculate_metrics()
        
            return results
        except Exception as e:
            logger.error(f"Error in _create_results: {e}")
            raise


# Singleton instance
_backtest_engine: Optional[BacktestEngine] = None


def get_backtest_engine(config: Optional[BacktestConfig] = None) -> BacktestEngine:
    """Get or create backtest engine"""
    try:
        global _backtest_engine
    
        if _backtest_engine is None:
            if config is None:
                raise ValueError("config required for first initialization")
            _backtest_engine = BacktestEngine(config)
    
        return _backtest_engine
    except Exception as e:
        logger.error(f"Error in get_backtest_engine: {e}")
        raise


async def run_backtest(
    strategy: Callable,
    data_provider: Callable,
    config: BacktestConfig
) -> BacktestResults:
    """Convenience function to run backtest"""
    try:
        engine = BacktestEngine(config)
        return await engine.run(strategy, data_provider)
    except Exception as e:
        logger.error(f"Error in run_backtest: {e}")
        raise
