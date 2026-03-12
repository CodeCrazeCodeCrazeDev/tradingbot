"""
Week 2 Assignment: Build a Simple Backtesting Engine
Learn: Strategy testing, performance metrics, realistic simulation

Goal: Test strategies with realistic costs and slippage
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    direction: str  # 'long' or 'short'
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 10000
    commission_pct: float = 0.001  # 0.1% per trade
    slippage_pct: float = 0.0005   # 0.05% slippage
    position_size_pct: float = 0.95  # Use 95% of capital
    stop_loss_pct: float = 0.02    # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit


class SimpleBacktester:
    """Professional backtesting engine with realistic costs"""
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.equity_curve: pd.Series = None
        
    def run_backtest(self, 
                     data: pd.DataFrame, 
                     signals: pd.Series) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLC data
            signals: Series with 1 (buy), -1 (sell), 0 (hold)
        
        Returns:
            Dictionary with performance metrics
        """
        capital = self.config.initial_capital
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        entry_time = None
        
        equity = []
        equity_index = []
        
        for i in range(len(data)):
            current_price = data['close'].iloc[i]
            current_time = data.index[i]
            signal = signals.iloc[i]
            
            # Check for exit conditions first
            if position != 0:
                # Stop loss check
                if position == 1:  # Long position
                    if current_price <= entry_price * (1 - self.config.stop_loss_pct):
                        # Stop loss hit
                        exit_price = current_price * (1 - self.config.slippage_pct)
                        self._close_position(entry_time, current_time, entry_price, 
                                           exit_price, capital, position)
                        capital = equity[-1]
                        position = 0
                        continue
                    
                    # Take profit check
                    if current_price >= entry_price * (1 + self.config.take_profit_pct):
                        exit_price = current_price * (1 - self.config.slippage_pct)
                        self._close_position(entry_time, current_time, entry_price, 
                                           exit_price, capital, position)
                        capital = equity[-1]
                        position = 0
                        continue
                
                elif position == -1:  # Short position
                    if current_price >= entry_price * (1 + self.config.stop_loss_pct):
                        exit_price = current_price * (1 + self.config.slippage_pct)
                        self._close_position(entry_time, current_time, entry_price, 
                                           exit_price, capital, position)
                        capital = equity[-1]
                        position = 0
                        continue
                    
                    if current_price <= entry_price * (1 - self.config.take_profit_pct):
                        exit_price = current_price * (1 + self.config.slippage_pct)
                        self._close_position(entry_time, current_time, entry_price, 
                                           exit_price, capital, position)
                        capital = equity[-1]
                        position = 0
                        continue
            
            # Entry signals
            if signal == 1 and position == 0:  # Buy signal
                position = 1
                entry_price = current_price * (1 + self.config.slippage_pct)
                entry_time = current_time
                
            elif signal == -1 and position == 0:  # Sell signal
                position = -1
                entry_price = current_price * (1 - self.config.slippage_pct)
                entry_time = current_time
            
            # Update equity curve
            if position == 1:
                equity.append(capital * (current_price / entry_price))
            elif position == -1:
                equity.append(capital * (2 - current_price / entry_price))
            else:
                equity.append(capital)
            equity_index.append(current_time)
        
        # Close any open position at the end
        if position != 0:
            exit_price = data['close'].iloc[-1]
            self._close_position(entry_time, data.index[-1], entry_price, 
                               exit_price, capital, position)
        
        self.equity_curve = pd.Series(equity, index=equity_index)
        
        return self._calculate_metrics()
    
    def _close_position(self, entry_time, exit_time, entry_price, exit_price, 
                       capital, direction):
        """Close a position and record the trade"""
        
        # Calculate PnL
        if direction == 1:  # Long
            pnl_pct = (exit_price - entry_price) / entry_price
        else:  # Short
            pnl_pct = (entry_price - exit_price) / entry_price
        
        # Apply commission
        commission = capital * self.config.commission_pct * 2  # Entry + exit
        pnl = capital * pnl_pct - commission
        
        trade = Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            exit_price=exit_price,
            position_size=capital,
            direction='long' if direction == 1 else 'short',
            pnl=pnl,
            pnl_pct=pnl_pct,
            commission=commission,
            slippage=abs(entry_price - exit_price) * self.config.slippage_pct
        )
        
        self.trades.append(trade)
    
    def _calculate_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        if not self.trades:
            return {'error': 'No trades executed'}
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Returns
        total_return = (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0] - 1) * 100
        
        # Sharpe ratio
        returns = self.equity_curve.pct_change().dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative = self.equity_curve
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Profit factor
        total_profit = sum([t.pnl for t in winning_trades])
        total_loss = abs(sum([t.pnl for t in losing_trades]))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown,
            'final_capital': self.equity_curve.iloc[-1],
            'total_commission': sum([t.commission for t in self.trades]),
            'total_slippage': sum([t.slippage for t in self.trades])
        }
    
    def plot_results(self):
        """Plot backtest results"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Equity curve
        axes[0].plot(self.equity_curve.index, self.equity_curve.values)
        axes[0].set_title('Equity Curve')
        axes[0].set_ylabel('Capital ($)')
        axes[0].grid(True)
        
        # Drawdown
        cumulative = self.equity_curve
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        
        axes[1].fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        axes[1].set_title('Drawdown')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].grid(True)
        
        plt.tight_layout()
        plt.savefig('backtest_results.png')
        print("Results saved to backtest_results.png")


def example_strategy():
    """Example: Simple moving average crossover strategy"""
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    prices = pd.Series(100 + np.cumsum(np.random.randn(252) * 2), index=dates)
    
    data = pd.DataFrame({
        'close': prices,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'volume': np.random.randint(1000, 10000, 252)
    })
    
    # Calculate moving averages
    data['sma_fast'] = data['close'].rolling(10).mean()
    data['sma_slow'] = data['close'].rolling(30).mean()
    
    # Generate signals
    signals = pd.Series(0, index=data.index)
    signals[data['sma_fast'] > data['sma_slow']] = 1  # Buy
    signals[data['sma_fast'] < data['sma_slow']] = -1  # Sell
    
    # Run backtest
    config = BacktestConfig(
        initial_capital=10000,
        commission_pct=0.001,
        slippage_pct=0.0005,
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    
    backtester = SimpleBacktester(config)
    results = backtester.run_backtest(data, signals)
    
    # Print results
    print("="*70)
    print("BACKTEST RESULTS: Moving Average Crossover")
    print("="*70)
    print(f"\nTotal Return:     {results['total_return_pct']:.2f}%")
    print(f"Total Trades:     {results['total_trades']}")
    print(f"Win Rate:         {results['win_rate']:.1f}%")
    print(f"Profit Factor:    {results['profit_factor']:.2f}")
    print(f"Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:     {results['max_drawdown_pct']:.2f}%")
    print(f"Final Capital:    ${results['final_capital']:.2f}")
    print(f"Total Commission: ${results['total_commission']:.2f}")
    
    # Plot results
    backtester.plot_results()


if __name__ == "__main__":
    example_strategy()
    
    print("\n" + "="*70)
    print("EXERCISES:")
    print("="*70)
    print("""
1. Add position sizing based on Kelly Criterion
2. Implement trailing stop loss
3. Add partial profit taking (scale out)
4. Test multiple strategies and compare
5. Add Monte Carlo simulation for robustness testing
6. Implement walk-forward optimization

CHALLENGE: Build a strategy that achieves:
- Win rate > 50%
- Profit factor > 1.5
- Sharpe ratio > 1.0
- Max drawdown < 15%
    """)
