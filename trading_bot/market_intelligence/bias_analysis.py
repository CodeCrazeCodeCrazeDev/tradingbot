import logging
logger = logging.getLogger(__name__)
"""Bias Analysis Framework for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
from datetime import datetime, timedelta
import numpy
import pandas


class BiasDirection(Enum):
    """Market bias directions."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class BiasStrength(Enum):
    """Bias strength levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"


class MarketBiasDetector:
    """Detect and analyze market bias using multiple methodologies."""
    
    def __init__(self):
        try:
            self.bias_history = []
            self.bias_indicators = {}
            logger.info("Initialized MarketBiasDetection")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_directional_bias(self, df: pd.DataFrame, 
                               lookback_periods: List[int] = None) -> Dict:
        """Detect directional market bias using multiple timeframes.
        
        Args:
            df: DataFrame with OHLC data
            lookback_periods: List of periods to analyze for bias
            
        Returns:
            Dictionary with bias analysis
        """
        try:
            if lookback_periods is None:
                lookback_periods = [5, 10, 20, 50, 100]
        
            bias_signals = {}
        
            for period in lookback_periods:
                if len(df) >= period:
                    period_data = df.tail(period)
                
                    # Price momentum bias
                    price_change = (period_data['close'].iloc[-1] - period_data['close'].iloc[0]) / period_data['close'].iloc[0]
                
                    # Volume-weighted bias
                    if 'volume' in df.columns:
                        vwap = (period_data['close'] * period_data['volume']).sum() / period_data['volume'].sum()
                        vwap_bias = (period_data['close'].iloc[-1] - vwap) / vwap
                    else:
                        vwap_bias = 0
                
                    # Higher highs/lower lows bias
                    hh_ll_bias = self._calculate_hh_ll_bias(period_data)
                
                    # Moving average bias
                    ma_bias = self._calculate_ma_bias(period_data)
                
                    # Combine signals
                    combined_bias = (price_change * 0.3) + (vwap_bias * 0.2) + (hh_ll_bias * 0.3) + (ma_bias * 0.2)
                
                    # Determine direction and strength
                    direction = self._determine_bias_direction(combined_bias)
                    strength = self._determine_bias_strength(abs(combined_bias))
                
                    bias_signals[f'{period}_period'] = {
                        'direction': direction,
                        'strength': strength,
                        'score': combined_bias,
                        'price_momentum': price_change,
                        'vwap_bias': vwap_bias,
                        'structure_bias': hh_ll_bias,
                        'ma_bias': ma_bias
                    }
        
            # Calculate overall bias
            overall_bias = self._calculate_overall_bias(bias_signals)
        
            return {
                'overall_bias': overall_bias,
                'timeframe_analysis': bias_signals,
                'bias_confluence': self._calculate_bias_confluence(bias_signals),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in detect_directional_bias: {e}")
            raise
    
    def detect_session_bias(self, df: pd.DataFrame) -> Dict:
        """Detect bias based on trading session characteristics.
        
        Args:
            df: DataFrame with OHLC data and datetime index
            
        Returns:
            Dictionary with session bias analysis
        """
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
        
            df_copy = df.copy()
            df_copy['hour'] = df_copy.index.hour
            df_copy['returns'] = df_copy['close'].pct_change()
        
            # Define session hours (UTC)
            sessions = {
                'asian': (0, 8),
                'london': (8, 16), 
                'new_york': (13, 21),
                'overlap': (13, 16)
            }
        
            session_bias = {}
        
            for session_name, (start_hour, end_hour) in sessions.items():
                session_mask = (df_copy['hour'] >= start_hour) & (df_copy['hour'] < end_hour)
                session_data = df_copy[session_mask]
            
                if len(session_data) > 0:
                    # Calculate session bias metrics
                    avg_return = session_data['returns'].mean()
                    win_rate = (session_data['returns'] > 0).mean()
                    volatility = session_data['returns'].std()
                
                    # Determine session bias
                    if avg_return > 0.001 and win_rate > 0.55:
                        direction = BiasDirection.BULLISH
                    elif avg_return < -0.001 and win_rate < 0.45:
                        direction = BiasDirection.BEARISH
                    else:
                        direction = BiasDirection.NEUTRAL
                
                    session_bias[session_name] = {
                        'direction': direction,
                        'avg_return': avg_return,
                        'win_rate': win_rate,
                        'volatility': volatility,
                        'sample_size': len(session_data)
                    }
        
            return session_bias
        except Exception as e:
            logger.error(f"Error in detect_session_bias: {e}")
            raise
    
    def detect_liquidity_bias(self, df: pd.DataFrame) -> Dict:
        """Detect bias based on liquidity patterns.
        
        Args:
            df: DataFrame with OHLC and volume data
            
        Returns:
            Dictionary with liquidity bias analysis
        """
        try:
            if 'volume' not in df.columns:
                logger.warning("Volume data not available for liquidity bias analysis")
                return {}
        
            # Calculate volume metrics
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_ma']
            df_copy['returns'] = df_copy['close'].pct_change()
        
            # High volume periods
            high_volume_mask = df_copy['volume_ratio'] > 1.5
            high_vol_data = df_copy[high_volume_mask]
        
            # Low volume periods
            low_volume_mask = df_copy['volume_ratio'] < 0.7
            low_vol_data = df_copy[low_volume_mask]
        
            liquidity_bias = {}
        
            if len(high_vol_data) > 0:
                high_vol_return = high_vol_data['returns'].mean()
                high_vol_direction = BiasDirection.BULLISH if high_vol_return > 0 else BiasDirection.BEARISH
            
                liquidity_bias['high_volume'] = {
                    'direction': high_vol_direction,
                    'avg_return': high_vol_return,
                    'sample_size': len(high_vol_data)
                }
        
            if len(low_vol_data) > 0:
                low_vol_return = low_vol_data['returns'].mean()
                low_vol_direction = BiasDirection.BULLISH if low_vol_return > 0 else BiasDirection.BEARISH
            
                liquidity_bias['low_volume'] = {
                    'direction': low_vol_direction,
                    'avg_return': low_vol_return,
                    'sample_size': len(low_vol_data)
                }
        
            return liquidity_bias
        except Exception as e:
            logger.error(f"Error in detect_liquidity_bias: {e}")
            raise
    
    def _calculate_hh_ll_bias(self, df: pd.DataFrame) -> float:
        """Calculate higher highs/lower lows bias."""
        try:
            highs = df['high'].values
            lows = df['low'].values
        
            # Count higher highs and lower lows
            higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
            lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
        
            total_periods = len(highs) - 1
            if total_periods == 0:
                return 0
        
            hh_ratio = higher_highs / total_periods
            ll_ratio = lower_lows / total_periods
        
            return hh_ratio - ll_ratio
        except Exception as e:
            logger.error(f"Error in _calculate_hh_ll_bias: {e}")
            raise
    
    def _calculate_ma_bias(self, df: pd.DataFrame) -> float:
        """Calculate moving average bias."""
        try:
            close_prices = df['close']
        
            # Short and long moving averages
            ma_short = close_prices.rolling(5).mean()
            ma_long = close_prices.rolling(20).mean()
        
            if len(ma_short) == 0 or len(ma_long) == 0:
                return 0
        
            # Current MA relationship
            current_short = ma_short.iloc[-1]
            current_long = ma_long.iloc[-1]
        
            if pd.isna(current_short) or pd.isna(current_long):
                return 0
        
            return (current_short - current_long) / current_long
        except Exception as e:
            logger.error(f"Error in _calculate_ma_bias: {e}")
            raise
    
    def _determine_bias_direction(self, bias_score: float) -> BiasDirection:
        """Determine bias direction from score."""
        try:
            if bias_score > 0.005:
                return BiasDirection.BULLISH
            elif bias_score < -0.005:
                return BiasDirection.BEARISH
            else:
                return BiasDirection.NEUTRAL
        except Exception as e:
            logger.error(f"Error in _determine_bias_direction: {e}")
            raise
    
    def _determine_bias_strength(self, abs_bias_score: float) -> BiasStrength:
        """Determine bias strength from absolute score."""
        try:
            if abs_bias_score > 0.05:
                return BiasStrength.EXTREME
            elif abs_bias_score > 0.02:
                return BiasStrength.STRONG
            elif abs_bias_score > 0.01:
                return BiasStrength.MODERATE
            else:
                return BiasStrength.WEAK
        except Exception as e:
            logger.error(f"Error in _determine_bias_strength: {e}")
            raise
    
    def _calculate_overall_bias(self, bias_signals: Dict) -> Dict:
        """Calculate overall bias from multiple timeframes."""
        try:
            if not bias_signals:
                return {'direction': BiasDirection.NEUTRAL, 'strength': BiasStrength.WEAK, 'score': 0}
        
            # Weight longer timeframes more heavily
            weights = {
                '5_period': 0.1,
                '10_period': 0.15,
                '20_period': 0.25,
                '50_period': 0.3,
                '100_period': 0.2
            }
        
            weighted_score = 0
            total_weight = 0
        
            for period, signal in bias_signals.items():
                weight = weights.get(period, 0.1)
                weighted_score += signal['score'] * weight
                total_weight += weight
        
            if total_weight > 0:
                overall_score = weighted_score / total_weight
            else:
                overall_score = 0
        
            return {
                'direction': self._determine_bias_direction(overall_score),
                'strength': self._determine_bias_strength(abs(overall_score)),
                'score': overall_score
            }
        except Exception as e:
            logger.error(f"Error in _calculate_overall_bias: {e}")
            raise
    
    def _calculate_bias_confluence(self, bias_signals: Dict) -> Dict:
        """Calculate bias confluence across timeframes."""
        try:
            if not bias_signals:
                return {'bullish_confluence': 0, 'bearish_confluence': 0, 'neutral_confluence': 0}
        
            direction_counts = {
                BiasDirection.BULLISH: 0,
                BiasDirection.BEARISH: 0,
                BiasDirection.NEUTRAL: 0
            }
        
            for signal in bias_signals.values():
                direction_counts[signal['direction']] += 1
        
            total_signals = len(bias_signals)
        
            return {
                'bullish_confluence': direction_counts[BiasDirection.BULLISH] / total_signals,
                'bearish_confluence': direction_counts[BiasDirection.BEARISH] / total_signals,
                'neutral_confluence': direction_counts[BiasDirection.NEUTRAL] / total_signals
            }
        except Exception as e:
            logger.error(f"Error in _calculate_bias_confluence: {e}")
            raise


class BiasConfirmation:
    """Methods for confirming and validating market bias."""
    
    def __init__(self):
        try:
            self.confirmation_signals = {}
            logger.info("Initialized BiasConfirmationMethods")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def confirm_bias_with_price_action(self, df: pd.DataFrame, 
                                     expected_bias: BiasDirection) -> Dict:
        """Confirm bias using price action patterns.
        
        Args:
            df: DataFrame with OHLC data
            expected_bias: Expected bias direction to confirm
            
        Returns:
            Dictionary with confirmation analysis
        """
        try:
            confirmation_signals = []
        
            # Recent price action (last 10 periods)
            recent_data = df.tail(10)
        
            # Check for trend continuation patterns
            if expected_bias == BiasDirection.BULLISH:
                # Look for bullish patterns
                confirmation_signals.extend(self._check_bullish_patterns(recent_data))
            elif expected_bias == BiasDirection.BEARISH:
                # Look for bearish patterns
                confirmation_signals.extend(self._check_bearish_patterns(recent_data))
        
            # Calculate confirmation strength
            confirmation_score = len([s for s in confirmation_signals if s['confirms_bias']]) / max(len(confirmation_signals), 1)
        
            return {
                'confirmation_score': confirmation_score,
                'confirmation_signals': confirmation_signals,
                'is_confirmed': confirmation_score > 0.6
            }
        except Exception as e:
            logger.error(f"Error in confirm_bias_with_price_action: {e}")
            raise
    
    def confirm_bias_with_volume(self, df: pd.DataFrame, 
                               expected_bias: BiasDirection) -> Dict:
        """Confirm bias using volume analysis.
        
        Args:
            df: DataFrame with OHLC and volume data
            expected_bias: Expected bias direction to confirm
            
        Returns:
            Dictionary with volume confirmation
        """
        try:
            if 'volume' not in df.columns:
                return {'is_confirmed': False, 'reason': 'No volume data available'}
        
            recent_data = df.tail(20)
        
            # Calculate volume metrics
            recent_data = recent_data.copy()
            recent_data['returns'] = recent_data['close'].pct_change()
            recent_data['volume_ma'] = recent_data['volume'].rolling(10).mean()
            recent_data['volume_ratio'] = recent_data['volume'] / recent_data['volume_ma']
        
            # Volume confirmation logic
            if expected_bias == BiasDirection.BULLISH:
                # Check if bullish moves have higher volume
                bullish_moves = recent_data[recent_data['returns'] > 0]
                bearish_moves = recent_data[recent_data['returns'] < 0]
            
                if len(bullish_moves) > 0 and len(bearish_moves) > 0:
                    avg_bullish_volume = bullish_moves['volume_ratio'].mean()
                    avg_bearish_volume = bearish_moves['volume_ratio'].mean()
                
                    volume_confirmation = avg_bullish_volume > avg_bearish_volume
                else:
                    volume_confirmation = False
        
            elif expected_bias == BiasDirection.BEARISH:
                # Check if bearish moves have higher volume
                bullish_moves = recent_data[recent_data['returns'] > 0]
                bearish_moves = recent_data[recent_data['returns'] < 0]
            
                if len(bullish_moves) > 0 and len(bearish_moves) > 0:
                    avg_bullish_volume = bullish_moves['volume_ratio'].mean()
                    avg_bearish_volume = bearish_moves['volume_ratio'].mean()
                
                    volume_confirmation = avg_bearish_volume > avg_bullish_volume
                else:
                    volume_confirmation = False
        
            else:
                volume_confirmation = False
        
            return {
                'is_confirmed': volume_confirmation,
                'avg_bullish_volume': bullish_moves['volume_ratio'].mean() if len(bullish_moves) > 0 else 0,
                'avg_bearish_volume': bearish_moves['volume_ratio'].mean() if len(bearish_moves) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error in confirm_bias_with_volume: {e}")
            raise
    
    def confirm_bias_with_momentum(self, df: pd.DataFrame, 
                                 expected_bias: BiasDirection) -> Dict:
        """Confirm bias using momentum indicators.
        
        Args:
            df: DataFrame with OHLC data
            expected_bias: Expected bias direction to confirm
            
        Returns:
            Dictionary with momentum confirmation
        """
        # Calculate momentum indicators
        try:
            rsi = self._calculate_rsi(df['close'])
            macd_line, macd_signal = self._calculate_macd(df['close'])
        
            current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
            current_macd = macd_line.iloc[-1] - macd_signal.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0
        
            momentum_signals = []
        
            if expected_bias == BiasDirection.BULLISH:
                # RSI confirmation
                if current_rsi > 50 and current_rsi < 80:  # Bullish but not overbought
                    momentum_signals.append({'indicator': 'RSI', 'confirms': True, 'value': current_rsi})
                else:
                    momentum_signals.append({'indicator': 'RSI', 'confirms': False, 'value': current_rsi})
            
                # MACD confirmation
                if current_macd > 0:
                    momentum_signals.append({'indicator': 'MACD', 'confirms': True, 'value': current_macd})
                else:
                    momentum_signals.append({'indicator': 'MACD', 'confirms': False, 'value': current_macd})
        
            elif expected_bias == BiasDirection.BEARISH:
                # RSI confirmation
                if current_rsi < 50 and current_rsi > 20:  # Bearish but not oversold
                    momentum_signals.append({'indicator': 'RSI', 'confirms': True, 'value': current_rsi})
                else:
                    momentum_signals.append({'indicator': 'RSI', 'confirms': False, 'value': current_rsi})
            
                # MACD confirmation
                if current_macd < 0:
                    momentum_signals.append({'indicator': 'MACD', 'confirms': True, 'value': current_macd})
                else:
                    momentum_signals.append({'indicator': 'MACD', 'confirms': False, 'value': current_macd})
        
            # Calculate confirmation score
            confirming_signals = sum(1 for signal in momentum_signals if signal['confirms'])
            confirmation_score = confirming_signals / len(momentum_signals) if momentum_signals else 0
        
            return {
                'confirmation_score': confirmation_score,
                'is_confirmed': confirmation_score > 0.5,
                'momentum_signals': momentum_signals
            }
        except Exception as e:
            logger.error(f"Error in confirm_bias_with_momentum: {e}")
            raise
    
    def _check_bullish_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Check for bullish price action patterns."""
        try:
            patterns = []
        
            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i-1]
            
                # Higher highs and higher lows
                if current['high'] > previous['high'] and current['low'] > previous['low']:
                    patterns.append({
                        'pattern': 'higher_high_low',
                        'confirms_bias': True,
                        'timestamp': current.name
                    })
            
                # Bullish engulfing
                if (previous['close'] < previous['open'] and 
                    current['close'] > current['open'] and
                    current['open'] < previous['close'] and
                    current['close'] > previous['open']):
                    patterns.append({
                        'pattern': 'bullish_engulfing',
                        'confirms_bias': True,
                        'timestamp': current.name
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _check_bullish_patterns: {e}")
            raise
    
    def _check_bearish_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Check for bearish price action patterns."""
        try:
            patterns = []
        
            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i-1]
            
                # Lower highs and lower lows
                if current['high'] < previous['high'] and current['low'] < previous['low']:
                    patterns.append({
                        'pattern': 'lower_high_low',
                        'confirms_bias': True,
                        'timestamp': current.name
                    })
            
                # Bearish engulfing
                if (previous['close'] > previous['open'] and 
                    current['close'] < current['open'] and
                    current['open'] > previous['close'] and
                    current['close'] < previous['open']):
                    patterns.append({
                        'pattern': 'bearish_engulfing',
                        'confirms_bias': True,
                        'timestamp': current.name
                    })
        
            return patterns
        except Exception as e:
            logger.error(f"Error in _check_bearish_patterns: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
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
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD indicator."""
        try:
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9).mean()
            return macd_line, macd_signal
        except Exception as e:
            logger.error(f"Error in _calculate_macd: {e}")
            raise
