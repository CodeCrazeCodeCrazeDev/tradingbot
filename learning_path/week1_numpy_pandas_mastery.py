"""
Week 1 Assignment: Numpy/Pandas Performance Mastery
Learn: Vectorization, rolling windows, time series operations

Goal: Process market data 100x faster than loops
"""

import numpy as np
import pandas as pd
import time
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')


class MarketDataProcessor:
    """High-performance market data processing using vectorization"""
    
    @staticmethod
    def slow_moving_average(prices: np.ndarray, window: int) -> np.ndarray:
        """SLOW: Loop-based moving average (DON'T USE THIS!)"""
        result = np.zeros(len(prices))
        for i in range(window - 1, len(prices)):
            result[i] = np.mean(prices[i - window + 1:i + 1])
        return result
    
    @staticmethod
    def fast_moving_average(prices: np.ndarray, window: int) -> np.ndarray:
        """FAST: Vectorized moving average using convolution"""
        return np.convolve(prices, np.ones(window)/window, mode='same')
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate percentage returns (vectorized)"""
        return prices.pct_change()
    
    @staticmethod
    def calculate_log_returns(prices: pd.Series) -> pd.Series:
        """Calculate log returns (better for statistical analysis)"""
        return np.log(prices / prices.shift(1))
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
        """Calculate rolling volatility (annualized)"""
        return returns.rolling(window=window).std() * np.sqrt(252)
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator (vectorized)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band
    
    @staticmethod
    def detect_support_resistance(prices: pd.Series, window: int = 20) -> Tuple[pd.Series, pd.Series]:
        """Detect support and resistance levels using rolling min/max"""
        support = prices.rolling(window=window).min()
        resistance = prices.rolling(window=window).max()
        return support, resistance
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()


def performance_comparison():
    """Compare loop vs vectorized performance"""
    
    # Generate sample data (1 year of daily prices)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(252) * 2)
    
    print("="*70)
    print("PERFORMANCE COMPARISON: Loops vs Vectorization")
    print("="*70)
    
    # Test 1: Moving Average
    print("\nTest 1: 20-period Moving Average on 252 data points")
    
    start = time.time()
    slow_ma = MarketDataProcessor.slow_moving_average(prices, 20)
    slow_time = time.time() - start
    
    start = time.time()
    fast_ma = MarketDataProcessor.fast_moving_average(prices, 20)
    fast_time = time.time() - start
    
    speedup = slow_time / fast_time
    print(f"  Loop-based:    {slow_time*1000:.4f} ms")
    print(f"  Vectorized:    {fast_time*1000:.4f} ms")
    print(f"  Speedup:       {speedup:.1f}x faster!")
    
    # Test 2: Multiple indicators
    print("\nTest 2: Calculate 5 indicators on 1000 data points")
    
    large_prices = pd.Series(100 + np.cumsum(np.random.randn(1000) * 2))
    
    start = time.time()
    returns = MarketDataProcessor.calculate_returns(large_prices)
    volatility = MarketDataProcessor.calculate_volatility(returns)
    rsi = MarketDataProcessor.calculate_rsi(large_prices)
    upper, middle, lower = MarketDataProcessor.calculate_bollinger_bands(large_prices)
    support, resistance = MarketDataProcessor.detect_support_resistance(large_prices)
    vectorized_time = time.time() - start
    
    print(f"  All indicators: {vectorized_time*1000:.4f} ms")
    print(f"  Per indicator:  {vectorized_time*1000/5:.4f} ms")


def trading_strategy_example():
    """Example: Build a simple mean reversion strategy"""
    
    print("\n" + "="*70)
    print("TRADING STRATEGY EXAMPLE: Bollinger Band Mean Reversion")
    print("="*70)
    
    # Generate sample price data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    prices = pd.Series(
        100 + np.cumsum(np.random.randn(252) * 2),
        index=dates,
        name='price'
    )
    
    # Calculate indicators
    upper, middle, lower = MarketDataProcessor.calculate_bollinger_bands(prices)
    rsi = MarketDataProcessor.calculate_rsi(prices)
    
    # Generate signals (vectorized!)
    buy_signal = (prices < lower) & (rsi < 30)
    sell_signal = (prices > upper) & (rsi > 70)
    
    # Calculate strategy returns
    position = pd.Series(0, index=prices.index)
    position[buy_signal] = 1   # Long
    position[sell_signal] = -1  # Short
    position = position.shift(1).fillna(0)  # Shift to avoid look-ahead bias
    
    returns = prices.pct_change()
    strategy_returns = position * returns
    
    # Performance metrics
    total_return = (1 + strategy_returns).cumprod().iloc[-1] - 1
    sharpe = MarketDataProcessor.calculate_sharpe_ratio(strategy_returns.dropna())
    max_dd = MarketDataProcessor.calculate_max_drawdown(prices)
    
    print(f"\nStrategy Performance:")
    print(f"  Total Return:    {total_return*100:.2f}%")
    print(f"  Sharpe Ratio:    {sharpe:.2f}")
    print(f"  Max Drawdown:    {max_dd*100:.2f}%")
    print(f"  Total Trades:    {buy_signal.sum() + sell_signal.sum()}")
    print(f"  Win Rate:        {(strategy_returns > 0).sum() / len(strategy_returns.dropna()) * 100:.1f}%")


def advanced_exercises():
    """Advanced exercises for mastery"""
    
    print("\n" + "="*70)
    print("ADVANCED EXERCISES")
    print("="*70)
    
    print("""
1. **Multi-Timeframe Analysis**
   - Resample daily data to weekly/monthly
   - Calculate indicators on multiple timeframes
   - Combine signals from different timeframes

2. **Portfolio Optimization**
   - Calculate correlation matrix for multiple assets
   - Implement Markowitz mean-variance optimization
   - Calculate efficient frontier

3. **Risk Management**
   - Implement Value at Risk (VaR) calculation
   - Calculate Conditional VaR (CVaR)
   - Position sizing using Kelly Criterion

4. **Advanced Indicators**
   - Implement MACD, Stochastic, ADX
   - Create custom composite indicators
   - Optimize indicator parameters

5. **Backtesting Framework**
   - Build vectorized backtesting engine
   - Include transaction costs and slippage
   - Calculate comprehensive performance metrics
    """)


if __name__ == "__main__":
    # Run performance comparison
    performance_comparison()
    
    # Run trading strategy example
    trading_strategy_example()
    
    # Show advanced exercises
    advanced_exercises()
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS:")
    print("="*70)
    print("""
1. ALWAYS use vectorized operations (100x faster)
2. Use pandas for time series (built-in resampling, rolling windows)
3. Avoid loops when possible (use .apply() as last resort)
4. Shift signals to avoid look-ahead bias
5. Calculate log returns for statistical analysis
6. Annualize volatility and returns for comparison
    """)
