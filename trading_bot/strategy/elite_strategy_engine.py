"""
Elite 5-Star Strategy Engine with Multi-Confirmation Layers
Implements institutional-grade entry/exit logic with multiple confirmations
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"


class SignalStrength(Enum):
    """Signal strength classification"""
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class EliteSignal:
    """Enhanced signal with multiple confirmation layers"""
    time: datetime
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    position_size: float
    strength: SignalStrength
    regime: MarketRegime
    confirmations: List[str]
    confidence: float  # 0-1
    risk_reward: float
    metadata: Dict


class EliteStrategyEngine:
    """
    5-Star Strategy Engine with:
    - Multi-timeframe analysis
    - Multiple confirmation layers
    - Regime detection
    - Dynamic position sizing
    - Smart stop-loss/take-profit
    """
    
    def __init__(self, symbol: str = "EURUSD", risk_per_trade: float = 0.01):
        try:
            self.symbol = symbol
            self.risk_per_trade = risk_per_trade
        
            # Confirmation thresholds
            self.min_confirmations = 3
            self.strong_signal_confirmations = 5
        
            # ATR periods for volatility
            self.atr_period = 14
        
            # Trend detection
            self.ema_fast = 20
            self.ema_slow = 50
            self.ema_trend = 200
        
            logger.info(f"Elite Strategy Engine initialized for {symbol}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, df: pd.DataFrame, account_balance: float = 10000) -> List[EliteSignal]:
        """
        Main analysis function with multi-confirmation logic
        
        Returns list of high-quality signals with multiple confirmations
        """
        try:
            if len(df) < 200:
                logger.warning("Insufficient data for analysis")
                return []
        
            # Calculate all indicators
            df = self._calculate_indicators(df)
        
            # Detect market regime
            regime = self._detect_regime(df)
        
            # Get confirmations for each direction
            buy_confirmations = self._get_buy_confirmations(df)
            sell_confirmations = self._get_sell_confirmations(df)
        
            signals = []
        
            # Generate BUY signal if enough confirmations
            if len(buy_confirmations) >= self.min_confirmations:
                signal = self._create_buy_signal(
                    df, buy_confirmations, regime, account_balance
                )
                if signal:
                    signals.append(signal)
        
            # Generate SELL signal if enough confirmations
            if len(sell_confirmations) >= self.min_confirmations:
                signal = self._create_sell_signal(
                    df, sell_confirmations, regime, account_balance
                )
                if signal:
                    signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        try:
            df = df.copy()
        
            # Moving Averages
            df['ema_20'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
            df['ema_200'] = df['close'].ewm(span=self.ema_trend, adjust=False).mean()
        
            # ATR for volatility
            df['atr'] = self._calculate_atr(df, self.atr_period)
        
            # RSI
            df['rsi'] = self._calculate_rsi(df['close'], 14)
        
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(df['close'])
        
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        
            # Volume analysis
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
            # Price momentum
            df['momentum'] = df['close'].pct_change(10)
        
            # Support/Resistance levels
            df['swing_high'] = df['high'].rolling(20, center=True).max()
            df['swing_low'] = df['low'].rolling(20, center=True).min()
        
            return df
        except Exception as e:
            logger.error(f"Error in _calculate_indicators: {e}")
            raise
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
        
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
        
            return true_range.rolling(period).mean()
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Error in _calculate_rsi: {e}")
            raise
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        try:
            ema_12 = prices.ewm(span=12, adjust=False).mean()
            ema_26 = prices.ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            return macd, signal, hist
        except Exception as e:
            logger.error(f"Error in _calculate_macd: {e}")
            raise
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            middle = prices.rolling(period).mean()
            std_dev = prices.rolling(period).std()
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            return upper, middle, lower
        except Exception as e:
            logger.error(f"Error in _calculate_bollinger_bands: {e}")
            raise
    
    def _detect_regime(self, df: pd.DataFrame) -> MarketRegime:
        """Detect current market regime"""
        try:
            last_row = df.iloc[-1]
        
            # Check trend
            if last_row['ema_20'] > last_row['ema_50'] > last_row['ema_200']:
                if last_row['atr'] > df['atr'].rolling(50).mean().iloc[-1] * 1.5:
                    return MarketRegime.VOLATILE
                return MarketRegime.TRENDING_UP
        
            elif last_row['ema_20'] < last_row['ema_50'] < last_row['ema_200']:
                if last_row['atr'] > df['atr'].rolling(50).mean().iloc[-1] * 1.5:
                    return MarketRegime.VOLATILE
                return MarketRegime.TRENDING_DOWN
        
            # Check for breakout
            if last_row['volume_ratio'] > 2.0 and abs(last_row['momentum']) > 0.02:
                return MarketRegime.BREAKOUT
        
            return MarketRegime.RANGING
        except Exception as e:
            logger.error(f"Error in _detect_regime: {e}")
            raise
    
    def _get_buy_confirmations(self, df: pd.DataFrame) -> List[str]:
        """Get all BUY confirmations"""
        try:
            confirmations = []
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
        
            # 1. Trend confirmation
            if last_row['ema_20'] > last_row['ema_50']:
                confirmations.append("EMA_BULLISH")
        
            # 2. Price above 200 EMA (long-term trend)
            if last_row['close'] > last_row['ema_200']:
                confirmations.append("ABOVE_200EMA")
        
            # 3. RSI oversold recovery
            if 30 < last_row['rsi'] < 50 and last_row['rsi'] > prev_row['rsi']:
                confirmations.append("RSI_RECOVERY")
        
            # 4. MACD bullish crossover
            if last_row['macd'] > last_row['macd_signal'] and prev_row['macd'] <= prev_row['macd_signal']:
                confirmations.append("MACD_CROSSOVER")
        
            # 5. MACD histogram increasing
            if last_row['macd_hist'] > prev_row['macd_hist'] and last_row['macd_hist'] > 0:
                confirmations.append("MACD_MOMENTUM")
        
            # 6. Price bouncing from lower Bollinger Band
            if prev_row['close'] <= prev_row['bb_lower'] and last_row['close'] > last_row['bb_lower']:
                confirmations.append("BB_BOUNCE")
        
            # 7. Volume confirmation
            if last_row['volume_ratio'] > 1.2:
                confirmations.append("VOLUME_SURGE")
        
            # 8. Bullish momentum
            if last_row['momentum'] > 0 and last_row['momentum'] > prev_row['momentum']:
                confirmations.append("MOMENTUM_POSITIVE")
        
            # 9. Price above swing low (support holding)
            if last_row['close'] > last_row['swing_low']:
                confirmations.append("SUPPORT_HOLDING")
        
            # 10. Bullish candle
            if last_row['close'] > last_row['open']:
                confirmations.append("BULLISH_CANDLE")
        
            return confirmations
        except Exception as e:
            logger.error(f"Error in _get_buy_confirmations: {e}")
            raise
    
    def _get_sell_confirmations(self, df: pd.DataFrame) -> List[str]:
        """Get all SELL confirmations"""
        try:
            confirmations = []
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
        
            # 1. Trend confirmation
            if last_row['ema_20'] < last_row['ema_50']:
                confirmations.append("EMA_BEARISH")
        
            # 2. Price below 200 EMA
            if last_row['close'] < last_row['ema_200']:
                confirmations.append("BELOW_200EMA")
        
            # 3. RSI overbought reversal
            if 50 < last_row['rsi'] < 70 and last_row['rsi'] < prev_row['rsi']:
                confirmations.append("RSI_REVERSAL")
        
            # 4. MACD bearish crossover
            if last_row['macd'] < last_row['macd_signal'] and prev_row['macd'] >= prev_row['macd_signal']:
                confirmations.append("MACD_CROSSOVER")
        
            # 5. MACD histogram decreasing
            if last_row['macd_hist'] < prev_row['macd_hist'] and last_row['macd_hist'] < 0:
                confirmations.append("MACD_MOMENTUM")
        
            # 6. Price rejecting upper Bollinger Band
            if prev_row['close'] >= prev_row['bb_upper'] and last_row['close'] < last_row['bb_upper']:
                confirmations.append("BB_REJECTION")
        
            # 7. Volume confirmation
            if last_row['volume_ratio'] > 1.2:
                confirmations.append("VOLUME_SURGE")
        
            # 8. Bearish momentum
            if last_row['momentum'] < 0 and last_row['momentum'] < prev_row['momentum']:
                confirmations.append("MOMENTUM_NEGATIVE")
        
            # 9. Price below swing high (resistance holding)
            if last_row['close'] < last_row['swing_high']:
                confirmations.append("RESISTANCE_HOLDING")
        
            # 10. Bearish candle
            if last_row['close'] < last_row['open']:
                confirmations.append("BEARISH_CANDLE")
        
            return confirmations
        except Exception as e:
            logger.error(f"Error in _get_sell_confirmations: {e}")
            raise
    
    def _create_buy_signal(self, df: pd.DataFrame, confirmations: List[str], 
                          regime: MarketRegime, account_balance: float) -> Optional[EliteSignal]:
        """Create BUY signal with smart stop-loss and take-profit"""
        try:
            last_row = df.iloc[-1]
        
            entry_price = last_row['close']
            atr = last_row['atr']
        
            # Dynamic stop-loss based on ATR
            stop_loss = entry_price - (2 * atr)
        
            # Multiple take-profit levels
            tp1 = entry_price + (1.5 * atr)  # 1.5:1 RR
            tp2 = entry_price + (2.5 * atr)  # 2.5:1 RR
            tp3 = entry_price + (4 * atr)    # 4:1 RR
        
            # Calculate position size based on risk
            risk_amount = account_balance * self.risk_per_trade
            stop_loss_distance = entry_price - stop_loss
            position_size = risk_amount / stop_loss_distance if stop_loss_distance > 0 else 0
        
            # Determine signal strength
            strength = self._determine_strength(len(confirmations))
        
            # Calculate confidence
            confidence = min(len(confirmations) / 10, 1.0)
        
            # Risk-reward ratio
            risk_reward = (tp2 - entry_price) / (entry_price - stop_loss) if stop_loss_distance > 0 else 0
        
            return EliteSignal(
                time=datetime.now(),
                symbol=self.symbol,
                direction='BUY',
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=tp1,
                take_profit_2=tp2,
                take_profit_3=tp3,
                position_size=position_size,
                strength=strength,
                regime=regime,
                confirmations=confirmations,
                confidence=confidence,
                risk_reward=risk_reward,
                metadata={
                    'atr': atr,
                    'rsi': last_row['rsi'],
                    'macd': last_row['macd'],
                    'volume_ratio': last_row['volume_ratio']
                }
            )
        except Exception as e:
            logger.error(f"Error in _create_buy_signal: {e}")
            raise
    
    def _create_sell_signal(self, df: pd.DataFrame, confirmations: List[str],
                           regime: MarketRegime, account_balance: float) -> Optional[EliteSignal]:
        """Create SELL signal with smart stop-loss and take-profit"""
        try:
            last_row = df.iloc[-1]
        
            entry_price = last_row['close']
            atr = last_row['atr']
        
            # Dynamic stop-loss based on ATR
            stop_loss = entry_price + (2 * atr)
        
            # Multiple take-profit levels
            tp1 = entry_price - (1.5 * atr)
            tp2 = entry_price - (2.5 * atr)
            tp3 = entry_price - (4 * atr)
        
            # Calculate position size
            risk_amount = account_balance * self.risk_per_trade
            stop_loss_distance = stop_loss - entry_price
            position_size = risk_amount / stop_loss_distance if stop_loss_distance > 0 else 0
        
            strength = self._determine_strength(len(confirmations))
            confidence = min(len(confirmations) / 10, 1.0)
            risk_reward = (entry_price - tp2) / (stop_loss - entry_price) if stop_loss_distance > 0 else 0
        
            return EliteSignal(
                time=datetime.now(),
                symbol=self.symbol,
                direction='SELL',
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=tp1,
                take_profit_2=tp2,
                take_profit_3=tp3,
                position_size=position_size,
                strength=strength,
                regime=regime,
                confirmations=confirmations,
                confidence=confidence,
                risk_reward=risk_reward,
                metadata={
                    'atr': atr,
                    'rsi': last_row['rsi'],
                    'macd': last_row['macd'],
                    'volume_ratio': last_row['volume_ratio']
                }
            )
        except Exception as e:
            logger.error(f"Error in _create_sell_signal: {e}")
            raise
    
    def _determine_strength(self, confirmation_count: int) -> SignalStrength:
        """Determine signal strength based on confirmation count"""
        try:
            if confirmation_count >= 7:
                return SignalStrength.VERY_STRONG
            elif confirmation_count >= 5:
                return SignalStrength.STRONG
            elif confirmation_count >= 3:
                return SignalStrength.MEDIUM
            else:
                return SignalStrength.WEAK
        except Exception as e:
            logger.error(f"Error in _determine_strength: {e}")
            raise


# Export
__all__ = ['EliteStrategyEngine', 'EliteSignal', 'MarketRegime', 'SignalStrength']
