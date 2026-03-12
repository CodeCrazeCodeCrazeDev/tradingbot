"""
Advanced backtesting engine for AlphaAlgo 2.0
"""

import logging
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
from enum import Enum

# Set up logger
logger = logging.getLogger(__name__)


class BacktestMode(Enum):
    """Backtesting modes."""
    SIMPLE = "simple"  # Basic OHLCV
    DETAILED = "detailed"  # With order book
    REALISTIC = "realistic"  # With market impact


@dataclass
class BacktestTrade:
    """Backtesting trade details."""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    
    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()


@dataclass
class BacktestResult:
    """Backtesting results."""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: List[BacktestTrade]
    equity_curve: pd.Series
    metrics: Dict[str, float]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BacktestEngine:
    """
    Advanced backtesting engine.
    Supports multiple modes and realistic simulation.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        mode: BacktestMode = BacktestMode.REALISTIC,
        commission_rate: float = 0.001,  # 0.1%
        slippage_model: str = "fixed",
        risk_free_rate: float = 0.02     # 2% annual
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.mode = mode
        self.commission_rate = commission_rate
        self.slippage_model = slippage_model
        self.risk_free_rate = risk_free_rate
        
        # Trading state
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        # Market data
        self.data = {}
        self.current_time = None
        
        # Performance tracking
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'commission_paid': 0.0,
            'slippage_paid': 0.0
        }
        
        logger.info("✅ Backtest Engine initialized")
        logger.info(f"   Mode: {mode.value}")
        logger.info(f"   Initial capital: ${initial_capital:,.2f}")
    
    def load_data(
        self,
        data: Dict[str, pd.DataFrame],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """
        Load market data for backtesting.
        
        Args:
            data: Dictionary of DataFrames with market data
            start_time: Optional backtest start time
            end_time: Optional backtest end time
        """
        try:
            # Validate data
            for symbol, df in data.items():
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError(f"Missing required columns for {symbol}")
            
            self.data = data
            
            # Set time range
            times = pd.concat([df.index for df in data.values()])
            self.start_time = start_time or times.min()
            self.end_time = end_time or times.max()
            self.current_time = self.start_time
            
            logger.info("✅ Data loaded successfully")
            logger.info(f"   Symbols: {len(data)}")
            logger.info(f"   Date range: {self.start_time} to {self.end_time}")
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {str(e)}")
            raise
    
    def run(
        self,
        strategy: Callable,
        progress_callback: Optional[Callable] = None
    ) -> BacktestResult:
        """
        Run backtest simulation.
        
        Args:
            strategy: Trading strategy function
            progress_callback: Optional progress callback
        
        Returns:
            BacktestResult object
        """
        try:
            logger.info("🚀 Starting backtest simulation...")
            
            # Reset state
            self._reset_state()
            
            # Run simulation
            total_steps = len(pd.date_range(self.start_time, self.end_time, freq='1min'))
            current_step = 0
            
            for timestamp in pd.date_range(self.start_time, self.end_time, freq='1min'):
                self.current_time = timestamp
                
                # Update market data
                market_data = self._get_market_data(timestamp)
                
                # Run strategy
                signals = strategy(market_data, self.positions.copy())
                
                # Execute signals
                if signals:
                    self._execute_signals(signals, market_data)
                
                # Update positions
                self._update_positions(market_data)
                
                # Record equity
                self.equity_curve.append(self._calculate_equity())
                
                # Update progress
                current_step += 1
                if progress_callback:
                    progress_callback(current_step / total_steps)
            
            # Calculate final results
            results = self._calculate_results()
            
            logger.info("✅ Backtest completed successfully")
            logger.info(f"   Total return: {results.total_return:.2%}")
            logger.info(f"   Sharpe ratio: {results.sharpe_ratio:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in backtest: {str(e)}")
            raise
    
    def _reset_state(self):
        """Reset backtest state."""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'commission_paid': 0.0,
            'slippage_paid': 0.0
        }
    
    def _get_market_data(self, timestamp: datetime) -> Dict:
        """Get market data for timestamp."""
        market_data = {}
        
        for symbol, df in self.data.items():
            if timestamp in df.index:
                market_data[symbol] = {
                    'open': df.loc[timestamp, 'open'],
                    'high': df.loc[timestamp, 'high'],
                    'low': df.loc[timestamp, 'low'],
                    'close': df.loc[timestamp, 'close'],
                    'volume': df.loc[timestamp, 'volume']
                }
                
                # Add order book if available
                if self.mode in [BacktestMode.DETAILED, BacktestMode.REALISTIC]:
                    if 'bid' in df.columns and 'ask' in df.columns:
                        market_data[symbol]['bid'] = df.loc[timestamp, 'bid']
                        market_data[symbol]['ask'] = df.loc[timestamp, 'ask']
        
        return market_data
    
    def _execute_signals(
        self,
        signals: Dict[str, Dict],
        market_data: Dict
    ):
        """Execute trading signals."""
        for symbol, signal in signals.items():
            if symbol not in market_data:
                continue
            
            side = signal['side']
            quantity = signal['quantity']
            
            # Calculate execution price
            price = self._calculate_execution_price(
                symbol,
                side,
                quantity,
                market_data[symbol]
            )
            
            # Calculate transaction costs
            commission = abs(price * quantity * self.commission_rate)
            slippage = self._calculate_slippage(
                symbol,
                side,
                quantity,
                price,
                market_data[symbol]
            )
            
            # Update position
            if symbol not in self.positions:
                self.positions[symbol] = 0
            self.positions[symbol] += quantity if side == 'BUY' else -quantity
            
            # Record trade
            trade = BacktestTrade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=price,
                entry_time=self.current_time,
                fees=commission,
                slippage=slippage
            )
            self.trades.append(trade)
            
            # Update capital
            self.current_capital -= (price * quantity + commission + slippage)
            
            # Update metrics
            self.metrics['total_trades'] += 1
            self.metrics['commission_paid'] += commission
            self.metrics['slippage_paid'] += slippage
    
    def _calculate_execution_price(
        self,
        symbol: str,
        side: str,
        quantity: float,
        market_data: Dict
    ) -> float:
        """Calculate realistic execution price."""
        if self.mode == BacktestMode.SIMPLE:
            return market_data['close']
        
        elif self.mode == BacktestMode.DETAILED:
            # Use bid/ask prices
            return market_data['ask'] if side == 'BUY' else market_data['bid']
        
        else:  # REALISTIC
            # Include market impact
            base_price = market_data['ask'] if side == 'BUY' else market_data['bid']
            impact = self._calculate_market_impact(symbol, quantity, market_data)
            return base_price * (1 + impact if side == 'BUY' else 1 - impact)
    
    def _calculate_slippage(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        market_data: Dict
    ) -> float:
        """Calculate slippage cost."""
        if self.slippage_model == "fixed":
            return abs(price * quantity * 0.0001)  # 1 bp
        
        elif self.slippage_model == "volatility":
            volatility = (market_data['high'] - market_data['low']) / market_data['close']
            return abs(price * quantity * volatility * 0.1)
        
        else:  # proportional
            return abs(price * quantity * 0.0001 * (quantity / market_data['volume']))
    
    def _calculate_market_impact(
        self,
        symbol: str,
        quantity: float,
        market_data: Dict
    ) -> float:
        """Calculate price impact of trade."""
        # Simple square-root model
        daily_volume = market_data['volume']
        if daily_volume == 0:
            return 0
        
        participation = quantity / daily_volume
        return 0.1 * np.sqrt(participation)  # 10 bps per sqrt(participation rate)
    
    def _update_positions(self, market_data: Dict):
        """Update position values."""
        for symbol, position in list(self.positions.items()):
            if symbol not in market_data:
                continue
            
            # Check for position close
            if abs(position) < 1e-6:
                del self.positions[symbol]
                continue
            
            # Mark to market
            price = market_data[symbol]['close']
            
            # Update open trades
            for trade in self.trades:
                if (trade.symbol == symbol and
                    trade.exit_price is None and
                    position == 0):
                    trade.exit_price = price
                    trade.exit_time = self.current_time
                    trade.pnl = (
                        (price - trade.entry_price) * trade.quantity
                        if trade.side == 'BUY'
                        else (trade.entry_price - price) * trade.quantity
                    )
                    
                    # Update metrics
                    self.metrics['total_pnl'] += trade.pnl
                    if trade.pnl > 0:
                        self.metrics['winning_trades'] += 1
                    else:
                        self.metrics['losing_trades'] += 1
    
    def _calculate_equity(self) -> float:
        """Calculate current equity."""
        equity = self.current_capital
        
        # Add position values
        for symbol, position in self.positions.items():
            if symbol in self.data:
                price = self.data[symbol].loc[self.current_time, 'close']
                equity += position * price
        
        return equity
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate final backtest results."""
        equity_curve = pd.Series(self.equity_curve)
        returns = equity_curve.pct_change().dropna()
        
        # Calculate metrics
        total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1
        
        sharpe = np.sqrt(252) * (
            np.mean(returns) / np.std(returns)
        ) if len(returns) > 0 else 0
        
        max_dd = np.min(
            equity_curve / equity_curve.cummax() - 1
        ) if len(equity_curve) > 0 else 0
        
        win_rate = (
            self.metrics['winning_trades'] /
            self.metrics['total_trades']
        ) if self.metrics['total_trades'] > 0 else 0
        
        profit_factor = (
            sum(t.pnl for t in self.trades if t.pnl > 0) /
            abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        ) if any(t.pnl < 0 for t in self.trades) else float('inf')
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades=self.trades,
            equity_curve=equity_curve,
            metrics={
                'total_trades': self.metrics['total_trades'],
                'winning_trades': self.metrics['winning_trades'],
                'losing_trades': self.metrics['losing_trades'],
                'total_pnl': self.metrics['total_pnl'],
                'commission_paid': self.metrics['commission_paid'],
                'slippage_paid': self.metrics['slippage_paid'],
                'avg_trade_pnl': (
                    self.metrics['total_pnl'] / self.metrics['total_trades']
                    if self.metrics['total_trades'] > 0 else 0
                ),
                'max_drawdown_duration': self._calculate_max_dd_duration(equity_curve),
                'avg_trade_duration': self._calculate_avg_trade_duration()
            }
        )
    
    def _calculate_max_dd_duration(self, equity: pd.Series) -> int:
        """Calculate maximum drawdown duration in days."""
        if len(equity) < 2:
            return 0
        
        # Calculate drawdown series
        roll_max = equity.cummax()
        drawdown = equity / roll_max - 1
        
        # Find longest drawdown
        is_dd = drawdown < 0
        dd_starts = is_dd.ne(is_dd.shift()).cumsum()
        dd_grp = drawdown.groupby(dd_starts)
        
        max_dd_duration = 0
        for _, grp in dd_grp:
            if (grp < 0).any():
                duration = len(grp)
                max_dd_duration = max(max_dd_duration, duration)
        
        return max_dd_duration
    
    def _calculate_avg_trade_duration(self) -> float:
        """Calculate average trade duration in days."""
        durations = []
        
        for trade in self.trades:
            if trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 86400
                durations.append(duration)
        
        return np.mean(durations) if durations else 0
    
    def plot_results(self, filename: Optional[str] = None):
        """Plot backtest results."""
        try:
            import matplotlib.pyplot as plt
            
            # Create figure
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
            
            # Plot equity curve
            equity_curve = pd.Series(self.equity_curve)
            equity_curve.plot(ax=ax1, title='Equity Curve')
            ax1.set_ylabel('Portfolio Value ($)')
            ax1.grid(True)
            
            # Plot drawdown
            drawdown = equity_curve / equity_curve.cummax() - 1
            drawdown.plot(ax=ax2, title='Drawdown', color='red')
            ax2.set_ylabel('Drawdown (%)')
            ax2.grid(True)
            
            # Plot trade distribution
            pnls = [t.pnl for t in self.trades]
            ax3.hist(pnls, bins=50, title='Trade P/L Distribution')
            ax3.set_xlabel('P/L ($)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True)
            
            plt.tight_layout()
            
            if filename:
                plt.savefig(filename)
                logger.info(f"✅ Results plot saved to {filename}")
            else:
                plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib not available for plotting")
