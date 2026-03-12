"""
Technical Indicators for Trading Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for a DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added indicators
    """
    # Make a copy to avoid modifying the original
    try:
        df = df.copy()
    
        # Check if required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
    
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            # Add missing columns with NaN values
            for col in missing_columns:
                df[col] = np.nan
    
        # Calculate RSI
        df = calculate_rsi(df)
    
        # Calculate MACD
        df = calculate_macd(df)
    
        # Calculate Bollinger Bands
        df = calculate_bollinger_bands(df)
    
        # Calculate ATR
        df = calculate_atr(df)
    
        # Calculate additional indicators
        df = calculate_additional_indicators(df)
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_indicators: {e}")
        raise


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        df: DataFrame with close prices
        period: RSI period
        
    Returns:
        DataFrame with added RSI
    """
    # Calculate price changes
    try:
        delta = df['close'].diff()
    
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
    
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
    
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_rsi: {e}")
        raise


def calculate_macd(df: pd.DataFrame, fast_period: int = 12, 
                 slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculate Moving Average Convergence Divergence (MACD)
    
    Args:
        df: DataFrame with close prices
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal EMA period
        
    Returns:
        DataFrame with added MACD
    """
    # Calculate EMAs
    try:
        fast_ema = df['close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df['close'].ewm(span=slow_period, adjust=False).mean()
    
        # Calculate MACD line and signal line
        df['macd'] = fast_ema - slow_ema
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_macd: {e}")
        raise


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, 
                            std_dev: float = 2.0) -> pd.DataFrame:
    """
    Calculate Bollinger Bands
    
    Args:
        df: DataFrame with close prices
        period: SMA period
        std_dev: Standard deviation multiplier
        
    Returns:
        DataFrame with added Bollinger Bands
    """
    # Calculate SMA
    try:
        df['sma'] = df['close'].rolling(window=period).mean()
    
        # Calculate standard deviation
        rolling_std = df['close'].rolling(window=period).std()
    
        # Calculate upper and lower bands
        df['bb_upper'] = df['sma'] + (rolling_std * std_dev)
        df['bb_lower'] = df['sma'] - (rolling_std * std_dev)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma']
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_bollinger_bands: {e}")
        raise


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
        
    Returns:
        DataFrame with added ATR
    """
    # Calculate True Range
    try:
        df['tr1'] = abs(df['high'] - df['low'])
        df['tr2'] = abs(df['high'] - df['close'].shift())
        df['tr3'] = abs(df['low'] - df['close'].shift())
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
        # Calculate ATR
        df['atr'] = df['tr'].rolling(window=period).mean()
    
        # Drop temporary columns
        df = df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_atr: {e}")
        raise


def calculate_additional_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate additional technical indicators
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added indicators
    """
    # Stochastic Oscillator
    try:
        df = calculate_stochastic(df)
    
        # Moving Averages
        df = calculate_moving_averages(df)
    
        # ADX (Average Directional Index)
        df = calculate_adx(df)
    
        # OBV (On-Balance Volume)
        df = calculate_obv(df)
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_additional_indicators: {e}")
        raise


def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, 
                       d_period: int = 3) -> pd.DataFrame:
    """
    Calculate Stochastic Oscillator
    
    Args:
        df: DataFrame with OHLC data
        k_period: %K period
        d_period: %D period
        
    Returns:
        DataFrame with added Stochastic Oscillator
    """
    # Calculate %K
    try:
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        df['stoch_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
    
        # Calculate %D
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_stochastic: {e}")
        raise


def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate various Moving Averages
    
    Args:
        df: DataFrame with close prices
        
    Returns:
        DataFrame with added Moving Averages
    """
    # Simple Moving Averages
    try:
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
    
        # Exponential Moving Averages
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_moving_averages: {e}")
        raise


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average Directional Index (ADX)
    
    Args:
        df: DataFrame with OHLC data
        period: ADX period
        
    Returns:
        DataFrame with added ADX
    """
    # Calculate +DM and -DM
    try:
        df['up_move'] = df['high'].diff()
        df['down_move'] = df['low'].diff(-1).abs()
    
        df['plus_dm'] = np.where(
            (df['up_move'] > df['down_move']) & (df['up_move'] > 0),
            df['up_move'],
            0
        )
    
        df['minus_dm'] = np.where(
            (df['down_move'] > df['up_move']) & (df['down_move'] > 0),
            df['down_move'],
            0
        )
    
        # Calculate ATR
        if 'atr' not in df.columns:
            df = calculate_atr(df, period)
    
        # Calculate +DI and -DI
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])
    
        # Calculate DX and ADX
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=period).mean()
    
        # Drop temporary columns
        df = df.drop(['up_move', 'down_move', 'plus_dm', 'minus_dm', 'dx'], axis=1)
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_adx: {e}")
        raise


def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate On-Balance Volume (OBV)
    
    Args:
        df: DataFrame with close prices and volume
        
    Returns:
        DataFrame with added OBV
    """
    # Calculate OBV
    try:
        df['price_change'] = df['close'].diff()
        df['obv_change'] = np.where(
            df['price_change'] > 0,
            df['volume'],
            np.where(
                df['price_change'] < 0,
                -df['volume'],
                0
            )
        )
        df['obv'] = df['obv_change'].cumsum()
    
        # Drop temporary columns
        df = df.drop(['price_change', 'obv_change'], axis=1)
    
        return df
    except Exception as e:
        logger.error(f"Error in calculate_obv: {e}")
        raise


class TechnicalIndicatorAnalyzer:
    """
    Technical Indicator Analysis class for compatibility.
    """
    
    def __init__(self):
        try:
            self.indicators = {}
            logger.info("✅ Technical Indicator Analyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        return calculate_indicators(df)
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI."""
        return calculate_rsi(df, period)
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD."""
        return calculate_macd(df, fast, slow, signal)
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        return calculate_bollinger_bands(df, period, std_dev)
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate ATR."""
        return calculate_atr(df, period)
    
    def get_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal from indicators.
        
        Returns:
            Dictionary with signal information
        """
        try:
            if df.empty or len(df) < 2:
                return {'signal': 'NEUTRAL', 'strength': 0.0, 'indicators': {}}
        
            latest = df.iloc[-1]
            signals = []
        
            # RSI signal
            if 'rsi' in df.columns and not pd.isna(latest['rsi']):
                if latest['rsi'] < 30:
                    signals.append(('BUY', 0.7))
                elif latest['rsi'] > 70:
                    signals.append(('SELL', 0.7))
        
            # MACD signal
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                    if latest['macd'] > latest['macd_signal']:
                        signals.append(('BUY', 0.6))
                    else:
                        signals.append(('SELL', 0.6))
        
            # Bollinger Bands signal
            if all(col in df.columns for col in ['close', 'bb_lower', 'bb_upper']):
                if not pd.isna(latest['bb_lower']) and not pd.isna(latest['bb_upper']):
                    if latest['close'] < latest['bb_lower']:
                        signals.append(('BUY', 0.5))
                    elif latest['close'] > latest['bb_upper']:
                        signals.append(('SELL', 0.5))
        
            # Aggregate signals
            if not signals:
                return {'signal': 'NEUTRAL', 'strength': 0.0, 'indicators': {}}
        
            buy_strength = sum(s[1] for s in signals if s[0] == 'BUY')
            sell_strength = sum(s[1] for s in signals if s[0] == 'SELL')
        
            if buy_strength > sell_strength:
                signal = 'BUY'
                strength = buy_strength / len(signals)
            elif sell_strength > buy_strength:
                signal = 'SELL'
                strength = sell_strength / len(signals)
            else:
                signal = 'NEUTRAL'
                strength = 0.0
        
            return {
                'signal': signal,
                'strength': strength,
                'indicators': {
                    'rsi': latest.get('rsi'),
                    'macd': latest.get('macd'),
                    'macd_signal': latest.get('macd_signal'),
                    'bb_upper': latest.get('bb_upper'),
                    'bb_lower': latest.get('bb_lower')
                }
            }
        except Exception as e:
            logger.error(f"Error in get_signal: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2022-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': np.random.normal(100, 1, 100),
        'high': np.random.normal(101, 1, 100),
        'low': np.random.normal(99, 1, 100),
        'close': np.random.normal(100, 1, 100),
        'volume': np.random.normal(1000, 100, 100)
    }, index=dates)
    
    # Calculate indicators
    df_with_indicators = calculate_indicators(df)
    
    # Print results
    print(df_with_indicators.tail())
