"""
Aggressive Trading Strategy
More trades, relaxed filters, higher frequency
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AggressiveStrategy:
    """
    Aggressive strategy for more frequent trading
    
    Key differences from conservative:
    - Lower trend strength requirement
    - Lower volatility threshold
    - More lenient RSI bounds
    - Accepts weaker MACD signals
    - Trades closer to support/resistance
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'sma_fast': 5,           # Faster (was 10)
            'sma_slow': 20,          # Faster (was 30)
            'rsi_period': 14,
            'rsi_oversold': 40,      # More lenient (was 30)
            'rsi_overbought': 60,    # More lenient (was 70)
            'atr_period': 14,
            'atr_multiplier': 1.0,   # Tighter stops (was 1.5)
            'trend_strength_min': 0.005,  # Much lower (was 0.02)
            'volatility_min': 0.002,      # Much lower (was 0.005)
            'min_confidence': 0.55,       # Lower ML threshold (was 0.60)
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        df = data.copy()
        
        # Moving averages (faster periods)
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
        
        # ATR
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
        
        # Support and Resistance (shorter period for more trades)
        df['support'] = df['low'].rolling(10).min()
        df['resistance'] = df['high'].rolling(10).max()
        
        # Momentum
        df['momentum'] = df['close'] / df['close'].shift(5) - 1
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate AGGRESSIVE trading signals
        
        Returns:
            Series with 1 (buy), -1 (sell), 0 (hold)
        """
        df = self.calculate_indicators(data)
        
        signals = pd.Series(0, index=df.index)
        
        # RELAXED FILTERS for more trades
        
        # Filter 1: Trend Direction (still important)
        trend_up = df['sma_fast'] > df['sma_slow']
        trend_down = df['sma_fast'] < df['sma_slow']
        
        # Filter 2: Trend Strength (MUCH MORE LENIENT)
        has_trend = df['trend_strength'] > self.config['trend_strength_min']
        
        # Filter 3: Volatility (MUCH MORE LENIENT)
        has_volatility = df['volatility'] > self.config['volatility_min']
        
        # Filter 4: RSI (MORE LENIENT BOUNDS)
        rsi_buy_zone = df['rsi'] < self.config['rsi_overbought']
        rsi_sell_zone = df['rsi'] > self.config['rsi_oversold']
        
        # Filter 5: MACD (Accept weaker signals)
        macd_bullish = df['macd_histogram'] > -0.0001  # Very lenient
        macd_bearish = df['macd_histogram'] < 0.0001   # Very lenient
        
        # Filter 6: Momentum
        positive_momentum = df['momentum'] > -0.01  # Accept slight negative
        negative_momentum = df['momentum'] < 0.01   # Accept slight positive
        
        # BUY SIGNAL: Relaxed conditions
        buy_signal = (
            trend_up &
            has_trend &
            has_volatility &
            rsi_buy_zone &
            macd_bullish &
            positive_momentum
        )
        
        # SELL SIGNAL: Relaxed conditions
        sell_signal = (
            trend_down &
            has_trend &
            has_volatility &
            rsi_sell_zone &
            macd_bearish &
            negative_momentum
        )
        
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        return signals
    
    def calculate_dynamic_stops(self, data: pd.DataFrame, position: int) -> Tuple[float, float]:
        """Calculate tighter stops for aggressive trading"""
        current_price = data['close'].iloc[-1]
        atr = data['atr'].iloc[-1]
        
        # Tighter stops (1.0x ATR instead of 1.5x)
        stop_loss_distance = (atr * self.config['atr_multiplier']) / current_price
        
        # Tighter take profit (1.5x ATR instead of 3x)
        take_profit_distance = (atr * self.config['atr_multiplier'] * 1.5) / current_price
        
        return stop_loss_distance, take_profit_distance
    
    def should_trade(self, strategy_signal: int, ml_prediction: int, ml_confidence: float) -> bool:
        """
        RELAXED TRADING DECISION
        
        Now accepts:
        - Strategy OR ML signal (not both required)
        - Lower ML confidence threshold (55% vs 60%)
        """
        # Accept if EITHER strategy OR ML agrees (not both required)
        signal_agreement = (strategy_signal != 0) or (ml_prediction == 1)
        
        # Lower confidence threshold
        confident_enough = ml_confidence > self.config['min_confidence']
        
        return signal_agreement and confident_enough


def test_aggressive_strategy():
    """Test aggressive strategy"""
    print("="*70)
    print("AGGRESSIVE STRATEGY TEST")
    print("="*70)
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    prices = 100 * (1 + np.random.randn(252) * 0.015).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(252) * 0.005),
        'high': prices * (1 + abs(np.random.randn(252)) * 0.01),
        'low': prices * (1 - abs(np.random.randn(252)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    # Test aggressive strategy
    strategy = AggressiveStrategy()
    signals = strategy.generate_signals(data)
    
    buy_signals = (signals == 1).sum()
    sell_signals = (signals == -1).sum()
    total_signals = buy_signals + sell_signals
    
    print(f"\nSignal Generation:")
    print(f"  Buy Signals:   {buy_signals}")
    print(f"  Sell Signals:  {sell_signals}")
    print(f"  Total Signals: {total_signals}")
    print(f"  Signal Rate:   {total_signals/len(data)*100:.1f}%")
    
    # Test trading decision logic
    print(f"\nTrading Decision Logic:")
    print(f"  Strategy OR ML (not both required)")
    print(f"  ML Confidence threshold: {strategy.config['min_confidence']*100:.0f}%")
    
    # Simulate some decisions
    test_cases = [
        (1, 1, 0.60, "Both agree, high confidence"),
        (1, 0, 0.60, "Strategy only, high confidence"),
        (0, 1, 0.60, "ML only, high confidence"),
        (1, 1, 0.50, "Both agree, low confidence"),
        (0, 0, 0.60, "Neither signal"),
    ]
    
    print(f"\n  Test Cases:")
    for strat_sig, ml_pred, ml_conf, desc in test_cases:
        should_trade = strategy.should_trade(strat_sig, ml_pred, ml_conf)
        result = "TRADE" if should_trade else "HOLD"
        print(f"    {desc:40s} -> {result}")
    
    print("\n" + "="*70)
    print("AGGRESSIVE STRATEGY READY!")
    print("="*70)
    
    if total_signals > 20:
        print(f"\nSUCCESS: Generated {total_signals} signals (much more aggressive!)")
    else:
        print(f"\nNote: {total_signals} signals generated")


if __name__ == "__main__":
    test_aggressive_strategy()
