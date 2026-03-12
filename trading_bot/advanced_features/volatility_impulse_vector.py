"""
Volatility Impulse Vector Module
Predicts explosive price moves using volatility analysis and momentum signals.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging
try:
    from scipy import stats
except ImportError:
    scipy = None
from sklearn.preprocessing import StandardScaler
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class VolatilitySignal:
    """A detected volatility impulse signal."""
    timestamp: datetime
    signal_type: str  # explosion, compression, reversal
    strength: float
    direction: str  # up, down, neutral
    timeframe: str
    confidence: float
    metrics: Dict[str, float]
    metadata: Dict[str, Any]


class VolatilityImpulseVector:
    """
    Predicts explosive price moves using volatility analysis.
    
    Features:
    - Volatility regime detection
    - Momentum surge identification
    - Compression breakout signals
    - Multi-timeframe volatility analysis
    - Price velocity calculations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the volatility impulse detector."""
        self.config = config or {}
        
        # Analysis parameters
        self.volatility_window = self.config.get('volatility_window', 20)
        self.momentum_window = self.config.get('momentum_window', 10)
        self.signal_threshold = self.config.get('signal_threshold', 2.0)
        self.min_compression_bars = self.config.get('min_compression_bars', 5)
        
        # Signal history
        self.signals: List[VolatilitySignal] = []
        
        # State tracking
        self.volatility_regimes: Dict[str, str] = {}  # timeframe -> regime
        self.compression_zones: Dict[str, List[Tuple[float, float]]] = {}  # timeframe -> zones
    
    def calculate_vector(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        Calculate the volatility impulse vector for price data.
        
        Args:
            data: OHLCV data
            timeframe: Current timeframe
            
        Returns:
            Dictionary with vector analysis
        """
        try:
            # Calculate base metrics
            returns = data['close'].pct_change()
            log_returns = np.log(data['close']).diff()
            volume_changes = data['volume'].pct_change()
            
            # Volatility metrics
            volatility = self._calculate_volatility_metrics(returns, log_returns)
            
            # Momentum metrics
            momentum = self._calculate_momentum_metrics(data, returns)
            
            # Volume metrics
            volume = self._calculate_volume_metrics(data['volume'], volume_changes)
            
            # Combine metrics
            vector = self._combine_metrics(volatility, momentum, volume)
            
            # Detect signals
            signals = self._detect_signals(vector, data, timeframe)
            
            # Update state
            self._update_state(vector, signals, timeframe)
            
            return {
                'vector': vector,
                'signals': signals,
                'volatility': volatility,
                'momentum': momentum,
                'volume': volume
            }
            
        except Exception as e:
            logger.error(f"Error calculating vector: {e}")
            return {}
    
    def _calculate_volatility_metrics(self, returns: pd.Series, 
                                   log_returns: pd.Series) -> Dict[str, float]:
        """Calculate volatility-based metrics."""
        try:
            # Standard volatility
            rolling_std = returns.rolling(self.volatility_window).std()
            
            # Parkinson volatility (uses high-low range)
            parkinson_vol = np.sqrt(1 / (4 * np.log(2)) * 
                                  log_returns.rolling(self.volatility_window).std() ** 2)
            
            # Volatility of volatility
            vol_of_vol = rolling_std.rolling(self.volatility_window).std()
            
            # Normalized metrics
            current_vol = rolling_std.iloc[-1]
            avg_vol = rolling_std.mean()
            vol_zscore = (current_vol - avg_vol) / rolling_std.std()
            
            return {
                'current_volatility': float(current_vol),
                'average_volatility': float(avg_vol),
                'volatility_zscore': float(vol_zscore),
                'parkinson_volatility': float(parkinson_vol.iloc[-1]),
                'volatility_of_volatility': float(vol_of_vol.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {e}")
            return {}
    
    def _calculate_momentum_metrics(self, data: pd.DataFrame, 
                                 returns: pd.Series) -> Dict[str, float]:
        """Calculate momentum-based metrics."""
        try:
            # RSI
            delta = returns
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Price velocity
            velocity = returns.rolling(self.momentum_window).sum()
            acceleration = velocity.diff()
            
            # Momentum indicators
            momentum = data['close'].diff(self.momentum_window)
            rate_of_change = data['close'].pct_change(self.momentum_window)
            
            return {
                'rsi': float(rsi.iloc[-1]),
                'velocity': float(velocity.iloc[-1]),
                'acceleration': float(acceleration.iloc[-1]),
                'momentum': float(momentum.iloc[-1]),
                'rate_of_change': float(rate_of_change.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum metrics: {e}")
            return {}
    
    def _calculate_volume_metrics(self, volume: pd.Series, 
                               volume_changes: pd.Series) -> Dict[str, float]:
        """Calculate volume-based metrics."""
        try:
            # Volume metrics
            rolling_vol = volume.rolling(self.volatility_window)
            vol_mean = rolling_vol.mean()
            vol_std = rolling_vol.std()
            
            # Volume momentum
            vol_momentum = volume_changes.rolling(self.momentum_window).sum()
            
            # Volume intensity
            intensity = (volume / vol_mean).iloc[-1]
            
            return {
                'volume_mean': float(vol_mean.iloc[-1]),
                'volume_std': float(vol_std.iloc[-1]),
                'volume_momentum': float(vol_momentum.iloc[-1]),
                'volume_intensity': float(intensity),
                'volume_zscore': float((volume.iloc[-1] - vol_mean.iloc[-1]) / vol_std.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {e}")
            return {}
    
    def _combine_metrics(self, volatility: Dict[str, float],
                       momentum: Dict[str, float],
                       volume: Dict[str, float]) -> Dict[str, float]:
        """Combine all metrics into a final vector."""
        try:
            # Volatility component
            vol_component = (
                volatility['volatility_zscore'] * 0.4 +
                volatility['volatility_of_volatility'] * 0.3 +
                abs(volatility['current_volatility'] - volatility['average_volatility']) * 0.3
            )
            
            # Momentum component
            mom_component = (
                momentum['velocity'] * 0.3 +
                momentum['acceleration'] * 0.3 +
                (momentum['rsi'] - 50) / 50 * 0.2 +
                momentum['rate_of_change'] * 0.2
            )
            
            # Volume component
            vol_component = (
                volume['volume_zscore'] * 0.4 +
                volume['volume_momentum'] * 0.3 +
                (volume['volume_intensity'] - 1) * 0.3
            )
            
            # Combine components
            vector_magnitude = np.sqrt(vol_component**2 + mom_component**2)
            vector_direction = np.sign(mom_component)
            
            return {
                'magnitude': float(vector_magnitude),
                'direction': float(vector_direction),
                'volatility_component': float(vol_component),
                'momentum_component': float(mom_component),
                'volume_component': float(vol_component)
            }
            
        except Exception as e:
            logger.error(f"Error combining metrics: {e}")
            return {}
    
    def _detect_signals(self, vector: Dict[str, float], data: pd.DataFrame,
                      timeframe: str) -> List[VolatilitySignal]:
        """Detect volatility impulse signals."""
        signals = []
        
        try:
            # Explosion signal
            if abs(vector['magnitude']) > self.signal_threshold:
                signal = VolatilitySignal(
                    timestamp=data.index[-1],
                    signal_type='explosion',
                    strength=abs(vector['magnitude']),
                    direction='up' if vector['direction'] > 0 else 'down',
                    timeframe=timeframe,
                    confidence=min(abs(vector['magnitude']) / self.signal_threshold, 1.0),
                    metrics={
                        'magnitude': vector['magnitude'],
                        'volatility_component': vector['volatility_component'],
                        'momentum_component': vector['momentum_component'],
                        'volume_component': vector['volume_component']
                    },
                    metadata={
                        'price': float(data['close'].iloc[-1]),
                        'volume': float(data['volume'].iloc[-1])
                    }
                )
                signals.append(signal)
                self.signals.append(signal)
            
            # Compression signal
            volatility = data['high'] - data['low']
            if len(volatility) >= self.min_compression_bars:
                recent_vol = volatility[-self.min_compression_bars:]
                if (recent_vol.std() < volatility.std() * 0.5 and
                    recent_vol.mean() < volatility.mean() * 0.7):
                    signal = VolatilitySignal(
                        timestamp=data.index[-1],
                        signal_type='compression',
                        strength=1.0 - (recent_vol.std() / volatility.std()),
                        direction='neutral',
                        timeframe=timeframe,
                        confidence=0.8,
                        metrics={
                            'compression_ratio': float(volatility.std() / recent_vol.std()),
                            'compression_duration': self.min_compression_bars
                        },
                        metadata={
                            'price_range': float(recent_vol.mean()),
                            'volume_average': float(data['volume'][-self.min_compression_bars:].mean())
                        }
                    )
                    signals.append(signal)
                    self.signals.append(signal)
            
            # Limit signal history
            if len(self.signals) > 1000:
                self.signals = self.signals[-1000:]
            
            return signals
            
        except Exception as e:
            logger.error(f"Error detecting signals: {e}")
            return []
    
    def _update_state(self, vector: Dict[str, float],
                    signals: List[VolatilitySignal],
                    timeframe: str):
        """Update internal state tracking."""
        try:
            # Update volatility regime
            if abs(vector['volatility_component']) > 1.5:
                self.volatility_regimes[timeframe] = 'high'
            elif abs(vector['volatility_component']) < 0.5:
                self.volatility_regimes[timeframe] = 'low'
            else:
                self.volatility_regimes[timeframe] = 'normal'
            
            # Update compression zones
            compression_signals = [s for s in signals if s.signal_type == 'compression']
            if compression_signals:
                if timeframe not in self.compression_zones:
                    self.compression_zones[timeframe] = []
                for signal in compression_signals:
                    self.compression_zones[timeframe].append((
                        signal.metadata['price_range'],
                        signal.strength
                    ))
            
            # Clean up old compression zones
            if timeframe in self.compression_zones:
                self.compression_zones[timeframe] = self.compression_zones[timeframe][-10:]
                
        except Exception as e:
            logger.error(f"Error updating state: {e}")
    
    def get_active_signals(self, current_time: datetime,
                         max_age_minutes: int = 60) -> List[VolatilitySignal]:
        """Get currently active signals."""
        active_signals = []
        
        for signal in self.signals:
            age_minutes = (current_time - signal.timestamp).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                active_signals.append(signal)
        
        return active_signals
