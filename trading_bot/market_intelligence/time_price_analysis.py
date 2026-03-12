import logging
logger = logging.getLogger(__name__)
"""Time and Price Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
import pytz
import numpy
import pandas


class TimeAnalysisComponents:
    """Analyze time-based market patterns."""
    
    def __init__(self):
        try:
            self.time_patterns = {}
            logger.info("Initialized TimeAnalysisComponents")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_session_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze trading session patterns.
        
        Args:
            df: DataFrame with OHLC data and datetime index
            
        Returns:
            Dictionary with session analysis
        """
        # Ensure datetime index
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.warning("DataFrame index is not datetime, attempting conversion")
                df.index = pd.to_datetime(df.index)
        
            # Add time-based features
            df_copy = df.copy()
            df_copy['hour'] = df_copy.index.hour
            df_copy['day_of_week'] = df_copy.index.dayofweek
            df_copy['returns'] = df_copy['close'].pct_change()
        
            # Define trading sessions (UTC times)
            sessions = {
                'asian': {'start': 0, 'end': 8},      # 00:00 - 08:00 UTC
                'london': {'start': 8, 'end': 16},    # 08:00 - 16:00 UTC
                'new_york': {'start': 13, 'end': 21}, # 13:00 - 21:00 UTC
                'overlap': {'start': 13, 'end': 16}   # London-NY overlap
            }
        
            session_stats = {}
        
            for session_name, times in sessions.items():
                # Filter data for session hours
                if times['start'] < times['end']:
                    session_mask = (df_copy['hour'] >= times['start']) & (df_copy['hour'] < times['end'])
                else:  # Handle overnight sessions
                    session_mask = (df_copy['hour'] >= times['start']) | (df_copy['hour'] < times['end'])
            
                session_data = df_copy[session_mask]
            
                if len(session_data) > 0:
                    session_stats[session_name] = {
                        'avg_volatility': session_data['returns'].std(),
                        'avg_volume': session_data['volume'].mean() if 'volume' in session_data.columns else None,
                        'avg_range': (session_data['high'] - session_data['low']).mean(),
                        'bullish_sessions': (session_data['close'] > session_data['open']).sum(),
                        'bearish_sessions': (session_data['close'] < session_data['open']).sum(),
                        'total_sessions': len(session_data)
                    }
        
            return session_stats
        except Exception as e:
            logger.error(f"Error in analyze_session_patterns: {e}")
            raise
    
    def detect_time_cycles(self, df: pd.DataFrame, 
                          cycle_periods: List[int] = None) -> Dict:
        """Detect cyclical patterns in price data.
        
        Args:
            df: DataFrame with OHLC data
            cycle_periods: List of periods to analyze for cycles
            
        Returns:
            Dictionary with cycle analysis
        """
        try:
            if cycle_periods is None:
                cycle_periods = [5, 10, 20, 50, 100]  # Common cycle periods
        
            cycle_analysis = {}
            returns = df['close'].pct_change().dropna()
        
            for period in cycle_periods:
                if len(returns) >= period * 3:  # Need at least 3 cycles
                    # Calculate autocorrelation at the given period
                    autocorr = returns.autocorr(lag=period)
                
                    # Calculate cycle strength using FFT
                    fft_values = np.fft.fft(returns.values)
                    frequencies = np.fft.fftfreq(len(returns))
                
                    # Find dominant frequency near the expected cycle
                    expected_freq = 1.0 / period
                    freq_range = 0.1 / period  # ±10% tolerance
                
                    mask = (np.abs(frequencies - expected_freq) <= freq_range) | \
                           (np.abs(frequencies + expected_freq) <= freq_range)
                
                    if np.any(mask):
                        cycle_strength = np.mean(np.abs(fft_values[mask]))
                    else:
                        cycle_strength = 0
                
                    cycle_analysis[f'{period}_period'] = {
                        'autocorrelation': autocorr,
                        'cycle_strength': cycle_strength,
                        'significance': abs(autocorr) > 0.1  # Threshold for significance
                    }
        
            return cycle_analysis
        except Exception as e:
            logger.error(f"Error in detect_time_cycles: {e}")
            raise
    
    def analyze_day_of_week_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze day-of-week patterns.
        
        Args:
            df: DataFrame with OHLC data and datetime index
            
        Returns:
            Dictionary with day-of-week analysis
        """
        try:
            df_copy = df.copy()
            df_copy['day_of_week'] = df_copy.index.dayofweek
            df_copy['returns'] = df_copy['close'].pct_change()
        
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_stats = {}
        
            for day_num in range(7):
                day_data = df_copy[df_copy['day_of_week'] == day_num]
            
                if len(day_data) > 0:
                    day_stats[day_names[day_num]] = {
                        'avg_return': day_data['returns'].mean(),
                        'volatility': day_data['returns'].std(),
                        'avg_range': (day_data['high'] - day_data['low']).mean(),
                        'bullish_days': (day_data['close'] > day_data['open']).sum(),
                        'bearish_days': (day_data['close'] < day_data['open']).sum(),
                        'total_days': len(day_data)
                    }
        
            return day_stats
        except Exception as e:
            logger.error(f"Error in analyze_day_of_week_patterns: {e}")
            raise


class PriceAnalysis:
    """Advanced price analysis components."""
    
    def __init__(self):
        try:
            self.price_patterns = {}
            logger.info("Initialized PriceAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_price_levels(self, df: pd.DataFrame, 
                             method: str = 'pivot') -> Dict:
        """Calculate key price levels.
        
        Args:
            df: DataFrame with OHLC data
            method: Method for level calculation ('pivot', 'fibonacci', 'psychological')
            
        Returns:
            Dictionary with price levels
        """
        try:
            if method == 'pivot':
                return self._calculate_pivot_levels(df)
            elif method == 'fibonacci':
                return self._calculate_fibonacci_levels(df)
            elif method == 'psychological':
                return self._calculate_psychological_levels(df)
            else:
                raise ValueError(f"Unknown method: {method}")
        except Exception as e:
            logger.error(f"Error in calculate_price_levels: {e}")
            raise
    
    def _calculate_pivot_levels(self, df: pd.DataFrame) -> Dict:
        """Calculate pivot point levels."""
        # Use last complete period for calculation
        try:
            last_period = df.iloc[-1]
        
            high = last_period['high']
            low = last_period['low']
            close = last_period['close']
        
            # Standard pivot calculation
            pivot = (high + low + close) / 3
        
            # Support and resistance levels
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
        
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
        
            return {
                'pivot': pivot,
                'resistance_levels': {'R1': r1, 'R2': r2, 'R3': r3},
                'support_levels': {'S1': s1, 'S2': s2, 'S3': s3}
            }
        except Exception as e:
            logger.error(f"Error in _calculate_pivot_levels: {e}")
            raise
    
    def _calculate_fibonacci_levels(self, df: pd.DataFrame, 
                                  lookback: int = 100) -> Dict:
        """Calculate Fibonacci retracement levels."""
        try:
            recent_data = df.tail(lookback)
        
            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()
        
            fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
            fib_prices = {}
        
            price_range = swing_high - swing_low
        
            for level in fib_levels:
                fib_prices[f'fib_{level}'] = swing_low + (price_range * level)
        
            return {
                'swing_high': swing_high,
                'swing_low': swing_low,
                'fib_levels': fib_prices
            }
        except Exception as e:
            logger.error(f"Error in _calculate_fibonacci_levels: {e}")
            raise
    
    def _calculate_psychological_levels(self, df: pd.DataFrame) -> Dict:
        """Calculate psychological price levels."""
        try:
            current_price = df['close'].iloc[-1]
        
            # Round numbers (00, 50 levels)
            price_int = int(current_price)
        
            psychological_levels = []
        
            # Add round number levels around current price
            for i in range(-5, 6):
                level = price_int + i
                if level > 0:
                    psychological_levels.append(level)
                    psychological_levels.append(level + 0.5)  # Half levels
        
            # Filter levels within reasonable range of current price
            price_range = current_price * 0.1  # ±10% of current price
            relevant_levels = [
                level for level in psychological_levels
                if abs(level - current_price) <= price_range
            ]
        
            return {
                'current_price': current_price,
                'psychological_levels': sorted(relevant_levels)
            }
        except Exception as e:
            logger.error(f"Error in _calculate_psychological_levels: {e}")
            raise
    
    def analyze_price_action_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze price action patterns.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with price action analysis
        """
        try:
            patterns = {}
        
            # Calculate candle characteristics
            df_copy = df.copy()
            df_copy['body_size'] = abs(df_copy['close'] - df_copy['open'])
            df_copy['upper_shadow'] = df_copy['high'] - np.maximum(df_copy['open'], df_copy['close'])
            df_copy['lower_shadow'] = np.minimum(df_copy['open'], df_copy['close']) - df_copy['low']
            df_copy['total_range'] = df_copy['high'] - df_copy['low']
        
            # Avoid division by zero
            df_copy['body_ratio'] = np.where(
                df_copy['total_range'] > 0,
                df_copy['body_size'] / df_copy['total_range'],
                0
            )
        
            # Detect doji patterns
            doji_threshold = 0.1  # Body is less than 10% of total range
            patterns['doji_count'] = (df_copy['body_ratio'] < doji_threshold).sum()
        
            # Detect hammer/hanging man patterns
            hammer_threshold = 0.3
            long_lower_shadow = df_copy['lower_shadow'] > df_copy['body_size'] * 2
            short_upper_shadow = df_copy['upper_shadow'] < df_copy['body_size'] * 0.5
            patterns['hammer_count'] = (long_lower_shadow & short_upper_shadow).sum()
        
            # Detect shooting star patterns
            long_upper_shadow = df_copy['upper_shadow'] > df_copy['body_size'] * 2
            short_lower_shadow = df_copy['lower_shadow'] < df_copy['body_size'] * 0.5
            patterns['shooting_star_count'] = (long_upper_shadow & short_lower_shadow).sum()
        
            # Detect engulfing patterns
            bullish_engulfing = 0
            bearish_engulfing = 0
        
            for i in range(1, len(df_copy)):
                prev_candle = df_copy.iloc[i-1]
                curr_candle = df_copy.iloc[i]
            
                # Bullish engulfing
                if (prev_candle['close'] < prev_candle['open'] and  # Previous bearish
                    curr_candle['close'] > curr_candle['open'] and  # Current bullish
                    curr_candle['open'] < prev_candle['close'] and  # Opens below prev close
                    curr_candle['close'] > prev_candle['open']):    # Closes above prev open
                    bullish_engulfing += 1
            
                # Bearish engulfing
                if (prev_candle['close'] > prev_candle['open'] and  # Previous bullish
                    curr_candle['close'] < curr_candle['open'] and  # Current bearish
                    curr_candle['open'] > prev_candle['close'] and  # Opens above prev close
                    curr_candle['close'] < prev_candle['open']):    # Closes below prev open
                    bearish_engulfing += 1
        
            patterns['bullish_engulfing_count'] = bullish_engulfing
            patterns['bearish_engulfing_count'] = bearish_engulfing
        
            return patterns
        except Exception as e:
            logger.error(f"Error in analyze_price_action_patterns: {e}")
            raise


class VolumePriceAnalysis:
    """Volume-Price analysis components."""
    
    def __init__(self):
        try:
            self.vp_patterns = {}
            logger.info("Initialized VolumePriceAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_vwap(self, df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calculate Volume Weighted Average Price.
        
        Args:
            df: DataFrame with OHLC and volume data
            period: Period for rolling VWAP (None for cumulative)
            
        Returns:
            Series with VWAP values
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for VWAP calculation")
                return pd.Series(index=df.index, dtype=float)
        
            typical_price = (df['high'] + df['low'] + df['close']) / 3
        
            if period is None:
                # Cumulative VWAP
                cumulative_volume = df['volume'].cumsum()
                cumulative_pv = (typical_price * df['volume']).cumsum()
                vwap = cumulative_pv / cumulative_volume
            else:
                # Rolling VWAP
                rolling_volume = df['volume'].rolling(window=period).sum()
                rolling_pv = (typical_price * df['volume']).rolling(window=period).sum()
                vwap = rolling_pv / rolling_volume
        
            return vwap
        except Exception as e:
            logger.error(f"Error in calculate_vwap: {e}")
            raise
    
    def analyze_volume_price_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze Volume Price Trend (VPT) indicator.
        
        Args:
            df: DataFrame with OHLC and volume data
            
        Returns:
            Dictionary with VPT analysis
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for VPT calculation")
                return {}
        
            # Calculate price change percentage
            price_change_pct = df['close'].pct_change()
        
            # Calculate VPT
            vpt = (price_change_pct * df['volume']).cumsum()
        
            # Analyze VPT trend
            vpt_ma = vpt.rolling(window=20).mean()
            vpt_trend = np.where(vpt > vpt_ma, 'bullish', 'bearish')
        
            # Detect divergences
            price_trend = df['close'].rolling(window=20).apply(
                lambda x: 'bullish' if x.iloc[-1] > x.iloc[0] else 'bearish'
            )
        
            divergence_signals = []
            for i in range(20, len(df)):
                if (price_trend.iloc[i] == 'bullish' and vpt_trend[i] == 'bearish'):
                    divergence_signals.append({
                        'timestamp': df.index[i],
                        'type': 'bearish_divergence',
                        'price': df['close'].iloc[i],
                        'vpt': vpt.iloc[i]
                    })
                elif (price_trend.iloc[i] == 'bearish' and vpt_trend[i] == 'bullish'):
                    divergence_signals.append({
                        'timestamp': df.index[i],
                        'type': 'bullish_divergence',
                        'price': df['close'].iloc[i],
                        'vpt': vpt.iloc[i]
                    })
        
            return {
                'vpt': vpt,
                'vpt_trend': vpt_trend,
                'divergence_signals': divergence_signals
            }
        except Exception as e:
            logger.error(f"Error in analyze_volume_price_trend: {e}")
            raise
    
    def calculate_on_balance_volume(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On Balance Volume (OBV).
        
        Args:
            df: DataFrame with OHLC and volume data
            
        Returns:
            Series with OBV values
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for OBV calculation")
                return pd.Series(index=df.index, dtype=float)
        
            price_change = df['close'].diff()
        
            obv_change = np.where(
                price_change > 0, df['volume'],
                np.where(price_change < 0, -df['volume'], 0)
            )
        
            obv = pd.Series(obv_change, index=df.index).cumsum()
        
            return obv
        except Exception as e:
            logger.error(f"Error in calculate_on_balance_volume: {e}")
            raise
    
    def detect_volume_climax(self, df: pd.DataFrame, 
                           volume_threshold: float = 2.0) -> List[Dict]:
        """Detect volume climax patterns.
        
        Args:
            df: DataFrame with OHLC and volume data
            volume_threshold: Volume threshold as multiple of average
            
        Returns:
            List of volume climax events
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for climax detection")
                return []
        
            # Calculate volume metrics
            volume_ma = df['volume'].rolling(window=20).mean()
            volume_ratio = df['volume'] / volume_ma
        
            # Calculate price change
            price_change = df['close'].pct_change()
        
            climax_events = []
        
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if i >= 20 and volume_ratio.iloc[i] > volume_threshold:
                
                    # Determine climax type
                    if price_change.iloc[i] > 0.02:  # Strong up move
                        climax_type = 'buying_climax'
                    elif price_change.iloc[i] < -0.02:  # Strong down move
                        climax_type = 'selling_climax'
                    else:
                        continue  # Skip if price change is not significant
                
                    climax_events.append({
                        'timestamp': timestamp,
                        'type': climax_type,
                        'volume': row['volume'],
                        'volume_ratio': volume_ratio.iloc[i],
                        'price_change': price_change.iloc[i],
                        'close': row['close']
                    })
        
            return climax_events
        except Exception as e:
            logger.error(f"Error in detect_volume_climax: {e}")
            raise
