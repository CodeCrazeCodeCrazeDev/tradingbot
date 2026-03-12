import logging
logger = logging.getLogger(__name__)
"""Technical Analysis Components for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from loguru import logger
import numpy
import pandas


class PricePatternRecognition:
    """Advanced price pattern recognition system."""
    
    def __init__(self):
        try:
            self.patterns = {}
            logger.info("Initialized PricePatternRecognition")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, List]:
        """Detect candlestick patterns using TA-Lib."""
        try:
            patterns = {}
        
            # Bullish patterns
            # Detect hammer pattern
            patterns['hammer'] = self._detect_hammer(df)
        
            # Detect doji pattern
            patterns['doji'] = self._detect_doji(df)
        
            # Detect bullish engulfing
            patterns['engulfing_bullish'] = self._detect_bullish_engulfing(df)
        
            # Bearish patterns
            patterns['hanging_man'] = self._detect_hanging_man(df)
            patterns['shooting_star'] = self._detect_shooting_star(df)
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_candlestick_patterns: {e}")
            raise
    
    def _detect_hammer(self, df: pd.DataFrame) -> pd.Series:
        """Detect hammer candlestick pattern."""
        try:
            result = pd.Series(0, index=df.index)
        
            for i in range(len(df)):
                body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
                upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
            
                if (lower_shadow > body_size * 2 and
                    upper_shadow < body_size * 0.1 and
                    df['close'].iloc[i] > df['open'].iloc[i]):
                    result.iloc[i] = 100
        
            return result
        except Exception as e:
            logger.error(f"Error in _detect_hammer: {e}")
            raise
    
    def _detect_doji(self, df: pd.DataFrame) -> pd.Series:
        """Detect doji candlestick pattern."""
        try:
            result = pd.Series(0, index=df.index)
        
            for i in range(len(df)):
                body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
                total_size = df['high'].iloc[i] - df['low'].iloc[i]
            
                if total_size > 0 and body_size / total_size < 0.1:
                    result.iloc[i] = 100
        
            return result
        except Exception as e:
            logger.error(f"Error in _detect_doji: {e}")
            raise
    
    def _detect_bullish_engulfing(self, df: pd.DataFrame) -> pd.Series:
        """Detect bullish engulfing pattern."""
        try:
            result = pd.Series(0, index=df.index)
        
            for i in range(1, len(df)):
                prev_body_size = abs(df['close'].iloc[i-1] - df['open'].iloc[i-1])
                curr_body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            
                if (df['close'].iloc[i] > df['open'].iloc[i] and
                    df['open'].iloc[i] < df['close'].iloc[i-1] and
                    df['close'].iloc[i] > df['open'].iloc[i-1] and
                    curr_body_size > prev_body_size):
                    result.iloc[i] = 100
        
            return result
        except Exception as e:
            logger.error(f"Error in _detect_bullish_engulfing: {e}")
            raise
    
    def _detect_hanging_man(self, df: pd.DataFrame) -> pd.Series:
        """Detect hanging man pattern."""
        try:
            result = pd.Series(0, index=df.index)
        
            for i in range(len(df)):
                body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
                upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
            
                if (lower_shadow > body_size * 2 and
                    upper_shadow < body_size * 0.1 and
                    df['close'].iloc[i] < df['open'].iloc[i]):
                    result.iloc[i] = 100
        
            return result
        except Exception as e:
            logger.error(f"Error in _detect_hanging_man: {e}")
            raise
    
    def _detect_shooting_star(self, df: pd.DataFrame) -> pd.Series:
        """Detect shooting star pattern."""
        try:
            result = pd.Series(0, index=df.index)
        
            for i in range(len(df)):
                body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
                upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
            
                if (upper_shadow > body_size * 2 and
                    lower_shadow < body_size * 0.1 and
                    df['close'].iloc[i] < df['open'].iloc[i]):
                    result.iloc[i] = 100
        
            return result
        except Exception as e:
            logger.error(f"Error in _detect_shooting_star: {e}")
            raise
    
    def detect_chart_patterns(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """Detect chart patterns like triangles, flags, etc."""
        try:
            patterns = {}
        
            # Support and resistance levels
            highs = df['high'].rolling(window=window).max()
            lows = df['low'].rolling(window=window).min()
        
            patterns['support_levels'] = lows.dropna().unique()
            patterns['resistance_levels'] = highs.dropna().unique()
        
            return patterns
        except Exception as e:
            logger.error(f"Error in detect_chart_patterns: {e}")
            raise


class MomentumIndicators:
    """Momentum-based technical indicators."""
    
    def __init__(self):
        try:
            logger.info("Initialized MomentumIndicators")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            logger.error(f"Error in calculate_rsi: {e}")
            raise
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD."""
        try:
            exp1 = prices.ewm(span=12, adjust=False).mean()
            exp2 = prices.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            return {
                'macd': macd,
                'signal': signal,
                'histogram': histogram
            }
        except Exception as e:
            logger.error(f"Error in calculate_macd: {e}")
            raise
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, 
                           close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Stochastic oscillator."""
        try:
            lowest_low = low.rolling(window=14).min()
            highest_high = high.rolling(window=14).max()
            slowk = 100 * (close - lowest_low) / (highest_high - lowest_low)
            slowd = slowk.rolling(window=3).mean()
            return {
                'slowk': slowk,
                'slowd': slowd
            }
        except Exception as e:
            logger.error(f"Error in calculate_stochastic: {e}")
            raise


class VolatilityMeasures:
    """Volatility measurement and analysis."""
    
    def __init__(self):
        try:
            logger.info("Initialized VolatilityMeasures")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, 
                     close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        try:
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error in calculate_atr: {e}")
            raise
    
    def calculate_bollinger_bands(self, prices: pd.Series, 
                                period: int = 20, std: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        try:
            middle = prices.rolling(window=period).mean()
            stddev = prices.rolling(window=period).std()
            upper = middle + (stddev * std)
            lower = middle - (stddev * std)
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
        except Exception as e:
            logger.error(f"Error in calculate_bollinger_bands: {e}")
            raise
    
    def calculate_volatility_regime(self, prices: pd.Series, 
                                  window: int = 20) -> pd.Series:
        """Calculate volatility regime (high/low volatility periods)."""
        try:
            returns = prices.pct_change()
            volatility = returns.rolling(window=window).std()
        
            # Classify into regimes
            vol_median = volatility.median()
            regime = pd.Series(index=volatility.index, dtype=str)
            regime[volatility > vol_median * 1.5] = 'high'
            regime[volatility < vol_median * 0.5] = 'low'
            regime[(volatility >= vol_median * 0.5) & (volatility <= vol_median * 1.5)] = 'normal'
        
            return regime
        except Exception as e:
            logger.error(f"Error in calculate_volatility_regime: {e}")
            raise
