"""
Perfect Bot - Optimized Strategy
Improved win rate through multiple filters and advanced indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizedStrategy:
    """
    Multi-filter strategy designed for >50% win rate
    
    Features:
    - Trend filter (only trade with trend)
    - Volatility filter (avoid low volatility)
    - Multiple timeframe confirmation
    - Support/resistance levels
    - RSI overbought/oversold
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'sma_fast': 10,
            'sma_slow': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'atr_period': 14,
            'atr_multiplier': 1.5,
            'trend_strength_min': 0.02,  # 2% minimum trend
            'volatility_min': 0.005,  # 0.5% minimum volatility
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        df = data.copy()
        
        # Moving averages
        df['sma_fast'] = df['close'].rolling(self.config['sma_fast']).mean()
        df['sma_slow'] = df['close'].rolling(self.config['sma_slow']).mean()
        df['ema_fast'] = df['close'].ewm(span=self.config['sma_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config['sma_slow']).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self.config['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.config['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(self.config['atr_period']).mean()
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_middle'] = sma_20
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Volatility
        df['volatility'] = df['close'].pct_change().rolling(20).std()
        
        # Trend strength
        df['trend_strength'] = abs(df['sma_fast'] - df['sma_slow']) / df['close']
        
        # Support and Resistance
        df['support'] = df['low'].rolling(20).min()
        df['resistance'] = df['high'].rolling(20).max()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals with multiple filters
        
        Returns:
            Series with 1 (buy), -1 (sell), 0 (hold)
        """
        df = self.calculate_indicators(data)
        
        signals = pd.Series(0, index=df.index)
        
        # Filter 1: Trend Direction
        trend_up = df['sma_fast'] > df['sma_slow']
        trend_down = df['sma_fast'] < df['sma_slow']
        
        # Filter 2: Trend Strength (avoid weak trends)
        strong_trend = df['trend_strength'] > self.config['trend_strength_min']
        
        # Filter 3: Volatility (avoid low volatility)
        sufficient_volatility = df['volatility'] > self.config['volatility_min']
        
        # Filter 4: RSI (overbought/oversold)
        rsi_oversold = df['rsi'] < self.config['rsi_oversold']
        rsi_overbought = df['rsi'] > self.config['rsi_overbought']
        rsi_neutral = (df['rsi'] > 40) & (df['rsi'] < 60)
        
        # Filter 5: MACD confirmation
        macd_bullish = (df['macd'] > df['macd_signal']) & (df['macd_histogram'] > 0)
        macd_bearish = (df['macd'] < df['macd_signal']) & (df['macd_histogram'] < 0)
        
        # Filter 6: Price position (not at extremes)
        not_at_resistance = df['close'] < (df['resistance'] * 0.98)
        not_at_support = df['close'] > (df['support'] * 1.02)
        
        # BUY SIGNAL: All conditions must be true
        buy_signal = (
            trend_up &
            strong_trend &
            sufficient_volatility &
            (rsi_oversold | rsi_neutral) &
            macd_bullish &
            not_at_resistance
        )
        
        # SELL SIGNAL: All conditions must be true
        sell_signal = (
            trend_down &
            strong_trend &
            sufficient_volatility &
            (rsi_overbought | rsi_neutral) &
            macd_bearish &
            not_at_support
        )
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        return signals
    
    def calculate_dynamic_stops(self, data: pd.DataFrame, position: int) -> Tuple[float, float]:
        """
        Calculate dynamic stop loss and take profit based on ATR
        
        Args:
            data: DataFrame with indicators
            position: 1 for long, -1 for short
        
        Returns:
            (stop_loss_distance, take_profit_distance) as percentage
        """
        current_price = data['close'].iloc[-1]
        atr = data['atr'].iloc[-1]
        
        # Stop loss: 1.5x ATR
        stop_loss_distance = (atr * self.config['atr_multiplier']) / current_price
        
        # Take profit: 3x ATR (2:1 risk/reward)
        take_profit_distance = (atr * self.config['atr_multiplier'] * 2) / current_price
        
        return stop_loss_distance, take_profit_distance
    
    def get_position_size(self, account_balance: float, risk_per_trade: float = 0.02) -> float:
        """
        Calculate position size based on account balance and risk
        
        Args:
            account_balance: Current account balance
            risk_per_trade: Percentage of account to risk (default 2%)
        
        Returns:
            Position size in lots
        """
        risk_amount = account_balance * risk_per_trade
        # This is simplified - in real trading, consider leverage and margin
        return risk_amount / account_balance
    
    def backtest_strategy(self, data: pd.DataFrame, initial_capital: float = 10000) -> Dict:
        """
        Backtest the optimized strategy
        
        Returns:
            Dictionary with performance metrics
        """
        df = self.calculate_indicators(data)
        signals = self.generate_signals(data)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            signal = signals.iloc[i]
            
            # Calculate dynamic stops
            stop_loss_pct, take_profit_pct = self.calculate_dynamic_stops(df.iloc[:i+1], position)
            
            # Exit logic
            if position == 1:  # Long position
                # Stop loss
                if current_price <= entry_price * (1 - stop_loss_pct):
                    pnl = capital * ((current_price / entry_price) - 1)
                    capital += pnl
                    trades.append({'entry': entry_price, 'exit': current_price, 'pnl': pnl, 'type': 'long'})
                    position = 0
                # Take profit
                elif current_price >= entry_price * (1 + take_profit_pct):
                    pnl = capital * ((current_price / entry_price) - 1)
                    capital += pnl
                    trades.append({'entry': entry_price, 'exit': current_price, 'pnl': pnl, 'type': 'long'})
                    position = 0
            
            elif position == -1:  # Short position
                # Stop loss
                if current_price >= entry_price * (1 + stop_loss_pct):
                    pnl = capital * ((entry_price / current_price) - 1)
                    capital += pnl
                    trades.append({'entry': entry_price, 'exit': current_price, 'pnl': pnl, 'type': 'short'})
                    position = 0
                # Take profit
                elif current_price <= entry_price * (1 - take_profit_pct):
                    pnl = capital * ((entry_price / current_price) - 1)
                    capital += pnl
                    trades.append({'entry': entry_price, 'exit': current_price, 'pnl': pnl, 'type': 'short'})
                    position = 0
            
            # Entry logic
            if signal == 1 and position == 0:
                position = 1
                entry_price = current_price
            elif signal == -1 and position == 0:
                position = -1
                entry_price = current_price
            
            equity_curve.append(capital)
        
        # Calculate metrics
        if len(trades) == 0:
            return {'error': 'No trades executed'}
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        total_return = (capital / initial_capital - 1) * 100
        win_rate = len(winning_trades) / len(trades) * 100
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum([t['pnl'] for t in winning_trades]) / sum([t['pnl'] for t in losing_trades])) if losing_trades else float('inf')
        
        # Sharpe ratio
        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'total_return': total_return,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'final_capital': capital
        }


def test_optimized_strategy():
    """Test the optimized strategy"""
    print("="*70)
    print("OPTIMIZED STRATEGY TEST")
    print("="*70)
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    returns = np.random.randn(252) * 0.015  # 1.5% daily volatility
    prices = 100 * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(252) * 0.005),
        'high': prices * (1 + abs(np.random.randn(252)) * 0.01),
        'low': prices * (1 - abs(np.random.randn(252)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    # Test strategy
    strategy = OptimizedStrategy()
    results = strategy.backtest_strategy(data)
    
    print("\nBACKTEST RESULTS:")
    print(f"  Total Return:     {results['total_return']:.2f}%")
    print(f"  Total Trades:     {results['total_trades']}")
    print(f"  Win Rate:         {results['win_rate']:.1f}%")
    print(f"  Profit Factor:    {results['profit_factor']:.2f}")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:     {results['max_drawdown']:.2f}%")
    print(f"  Final Capital:    ${results['final_capital']:.2f}")
    
    if results['win_rate'] > 50:
        print("\n  SUCCESS: Win rate > 50%!")
    else:
        print(f"\n  Note: Win rate {results['win_rate']:.1f}% (target: >50%)")
        print("  Try adjusting strategy parameters")
    
    print("\n" + "="*70)
    print("OPTIMIZED STRATEGY READY!")
    print("="*70)


if __name__ == "__main__":
    test_optimized_strategy()
