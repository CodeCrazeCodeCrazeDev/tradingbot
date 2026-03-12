"""
Fractal Momentum Divergence Module
Detects divergences using fractal analysis and multi-timeframe momentum.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging
try:
    from scipy import signal
except ImportError:
    scipy = None
from sklearn.preprocessing import StandardScaler
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class DivergenceSignal:
    """A detected divergence signal."""
    timestamp: datetime
    divergence_type: str  # regular, hidden, fractal
    timeframe: str
    indicator: str
    strength: float
    direction: str  # bullish, bearish
    confidence: float
    levels: Dict[str, float]
    metadata: Dict[str, Any]


class FractalMomentumDivergence:
    """
    Detects divergences using fractal analysis.
    
    Features:
    - Multi-timeframe divergence detection
    - Fractal pattern recognition
    - Momentum confirmation
    - Adaptive filtering
    - Signal strength calculation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the fractal divergence detector."""
        self.config = config or {}
        
        # Analysis parameters
        self.fractal_window = self.config.get('fractal_window', 5)
        self.momentum_window = self.config.get('momentum_window', 14)
        self.divergence_threshold = self.config.get('divergence_threshold', 0.5)
        self.min_pattern_bars = self.config.get('min_pattern_bars', 3)
        
        # Signal history
        self.signals: List[DivergenceSignal] = []
        
        # State tracking
        self.fractal_patterns: Dict[str, List[Tuple[datetime, float]]] = {}
        self.momentum_states: Dict[str, Dict[str, float]] = {}
    
    def analyze_divergence(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        Analyze price data for divergences.
        
        Args:
            data: OHLCV data
            timeframe: Current timeframe
            
        Returns:
            Dictionary with divergence analysis
        """
        try:
            # Calculate indicators
            rsi = self._calculate_rsi(data['close'])
            momentum = self._calculate_momentum(data)
            fractals = self._detect_fractals(data)
            
            # Find divergences
            regular_divs = self._find_regular_divergences(data, rsi, fractals)
            hidden_divs = self._find_hidden_divergences(data, rsi, fractals)
            fractal_divs = self._find_fractal_divergences(data, momentum, fractals)
            
            # Combine and filter signals
            signals = self._combine_signals(regular_divs + hidden_divs + fractal_divs,
                                         data, timeframe)
            
            # Update state
            self._update_state(signals, data, timeframe)
            
            return {
                'signals': signals,
                'fractals': fractals,
                'momentum': momentum,
                'rsi': rsi
            }
            
        except Exception as e:
            logger.error(f"Error analyzing divergence: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI indicator."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.momentum_window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.momentum_window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series()
    
    def _calculate_momentum(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate momentum indicators."""
        try:
            close = data['close']
            
            # Rate of change
            roc = close.pct_change(self.momentum_window)
            
            # Moving average convergence divergence
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Stochastic oscillator
            high_roll = data['high'].rolling(window=14).max()
            low_roll = data['low'].rolling(window=14).min()
            stoch = 100 * (close - low_roll) / (high_roll - low_roll)
            
            return {
                'roc': roc,
                'macd': macd,
                'macd_signal': signal,
                'stochastic': stoch
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return {}
    
    def _detect_fractals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect price fractals using window comparison."""
        fractals = []
        
        try:
            for i in range(2, len(data) - 2):
                # Bullish fractal
                if (data['low'].iloc[i-2:i+3].idxmin() == data.index[i] and
                    data['low'].iloc[i] == data['low'].iloc[i-2:i+3].min()):
                    fractals.append({
                        'type': 'bullish',
                        'timestamp': data.index[i],
                        'price': data['low'].iloc[i],
                        'index': i
                    })
                
                # Bearish fractal
                if (data['high'].iloc[i-2:i+3].idxmax() == data.index[i] and
                    data['high'].iloc[i] == data['high'].iloc[i-2:i+3].max()):
                    fractals.append({
                        'type': 'bearish',
                        'timestamp': data.index[i],
                        'price': data['high'].iloc[i],
                        'index': i
                    })
            
            return fractals
            
        except Exception as e:
            logger.error(f"Error detecting fractals: {e}")
            return []
    
    def _find_regular_divergences(self, data: pd.DataFrame,
                               rsi: pd.Series,
                               fractals: List[Dict[str, Any]]) -> List[DivergenceSignal]:
        """Find regular (classic) divergences."""
        signals = []
        
        try:
            for i in range(len(fractals) - 1):
                for j in range(i + 1, len(fractals)):
                    f1, f2 = fractals[i], fractals[j]
                    
                    # Skip if fractals are too close
                    if f2['index'] - f1['index'] < self.min_pattern_bars:
                        continue
                    
                    # Bullish divergence
                    if (f1['type'] == f2['type'] == 'bullish' and
                        f2['price'] < f1['price'] and
                        rsi.iloc[f2['index']] > rsi.iloc[f1['index']]):
                        
                        signal = DivergenceSignal(
                            timestamp=f2['timestamp'],
                            divergence_type='regular',
                            timeframe='',  # Set later
                            indicator='rsi',
                            strength=abs(f2['price'] - f1['price']) / f1['price'],
                            direction='bullish',
                            confidence=min(rsi.iloc[f2['index']] / 100, 0.95),
                            levels={
                                'price_1': f1['price'],
                                'price_2': f2['price'],
                                'rsi_1': float(rsi.iloc[f1['index']]),
                                'rsi_2': float(rsi.iloc[f2['index']])
                            },
                            metadata={
                                'fractal_1': f1,
                                'fractal_2': f2,
                                'bars_between': f2['index'] - f1['index']
                            }
                        )
                        signals.append(signal)
                    
                    # Bearish divergence
                    elif (f1['type'] == f2['type'] == 'bearish' and
                          f2['price'] > f1['price'] and
                          rsi.iloc[f2['index']] < rsi.iloc[f1['index']]):
                        
                        signal = DivergenceSignal(
                            timestamp=f2['timestamp'],
                            divergence_type='regular',
                            timeframe='',  # Set later
                            indicator='rsi',
                            strength=abs(f2['price'] - f1['price']) / f1['price'],
                            direction='bearish',
                            confidence=min((100 - rsi.iloc[f2['index']]) / 100, 0.95),
                            levels={
                                'price_1': f1['price'],
                                'price_2': f2['price'],
                                'rsi_1': float(rsi.iloc[f1['index']]),
                                'rsi_2': float(rsi.iloc[f2['index']])
                            },
                            metadata={
                                'fractal_1': f1,
                                'fractal_2': f2,
                                'bars_between': f2['index'] - f1['index']
                            }
                        )
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error finding regular divergences: {e}")
            return []
    
    def _find_hidden_divergences(self, data: pd.DataFrame,
                              rsi: pd.Series,
                              fractals: List[Dict[str, Any]]) -> List[DivergenceSignal]:
        """Find hidden divergences."""
        signals = []
        
        try:
            for i in range(len(fractals) - 1):
                for j in range(i + 1, len(fractals)):
                    f1, f2 = fractals[i], fractals[j]
                    
                    # Skip if fractals are too close
                    if f2['index'] - f1['index'] < self.min_pattern_bars:
                        continue
                    
                    # Bullish hidden divergence
                    if (f1['type'] == f2['type'] == 'bullish' and
                        f2['price'] > f1['price'] and
                        rsi.iloc[f2['index']] < rsi.iloc[f1['index']]):
                        
                        signal = DivergenceSignal(
                            timestamp=f2['timestamp'],
                            divergence_type='hidden',
                            timeframe='',  # Set later
                            indicator='rsi',
                            strength=abs(f2['price'] - f1['price']) / f1['price'],
                            direction='bullish',
                            confidence=min(rsi.iloc[f2['index']] / 100, 0.9),  # Lower confidence
                            levels={
                                'price_1': f1['price'],
                                'price_2': f2['price'],
                                'rsi_1': float(rsi.iloc[f1['index']]),
                                'rsi_2': float(rsi.iloc[f2['index']])
                            },
                            metadata={
                                'fractal_1': f1,
                                'fractal_2': f2,
                                'bars_between': f2['index'] - f1['index']
                            }
                        )
                        signals.append(signal)
                    
                    # Bearish hidden divergence
                    elif (f1['type'] == f2['type'] == 'bearish' and
                          f2['price'] < f1['price'] and
                          rsi.iloc[f2['index']] > rsi.iloc[f1['index']]):
                        
                        signal = DivergenceSignal(
                            timestamp=f2['timestamp'],
                            divergence_type='hidden',
                            timeframe='',  # Set later
                            indicator='rsi',
                            strength=abs(f2['price'] - f1['price']) / f1['price'],
                            direction='bearish',
                            confidence=min((100 - rsi.iloc[f2['index']]) / 100, 0.9),
                            levels={
                                'price_1': f1['price'],
                                'price_2': f2['price'],
                                'rsi_1': float(rsi.iloc[f1['index']]),
                                'rsi_2': float(rsi.iloc[f2['index']])
                            },
                            metadata={
                                'fractal_1': f1,
                                'fractal_2': f2,
                                'bars_between': f2['index'] - f1['index']
                            }
                        )
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error finding hidden divergences: {e}")
            return []
    
    def _find_fractal_divergences(self, data: pd.DataFrame,
                               momentum: Dict[str, pd.Series],
                               fractals: List[Dict[str, Any]]) -> List[DivergenceSignal]:
        """Find fractal momentum divergences."""
        signals = []
        
        try:
            # Get momentum indicators
            macd = momentum['macd']
            stoch = momentum['stochastic']
            
            for i in range(len(fractals) - 1):
                for j in range(i + 1, len(fractals)):
                    f1, f2 = fractals[i], fractals[j]
                    
                    # Skip if fractals are too close
                    if f2['index'] - f1['index'] < self.min_pattern_bars:
                        continue
                    
                    # Check fractal momentum divergence
                    if f1['type'] == f2['type']:
                        # Calculate fractal momentum
                        mom1 = macd.iloc[f1['index']] * stoch.iloc[f1['index']]
                        mom2 = macd.iloc[f2['index']] * stoch.iloc[f2['index']]
                        
                        # Bullish fractal divergence
                        if (f1['type'] == 'bullish' and
                            f2['price'] < f1['price'] and mom2 > mom1):
                            
                            signal = DivergenceSignal(
                                timestamp=f2['timestamp'],
                                divergence_type='fractal',
                                timeframe='',  # Set later
                                indicator='momentum',
                                strength=abs(mom2 - mom1) / abs(mom1),
                                direction='bullish',
                                confidence=min(abs(mom2) / (abs(mom1) + abs(mom2)), 0.95),
                                levels={
                                    'price_1': f1['price'],
                                    'price_2': f2['price'],
                                    'momentum_1': float(mom1),
                                    'momentum_2': float(mom2)
                                },
                                metadata={
                                    'fractal_1': f1,
                                    'fractal_2': f2,
                                    'bars_between': f2['index'] - f1['index'],
                                    'macd_1': float(macd.iloc[f1['index']]),
                                    'macd_2': float(macd.iloc[f2['index']]),
                                    'stoch_1': float(stoch.iloc[f1['index']]),
                                    'stoch_2': float(stoch.iloc[f2['index']])
                                }
                            )
                            signals.append(signal)
                        
                        # Bearish fractal divergence
                        elif (f1['type'] == 'bearish' and
                              f2['price'] > f1['price'] and mom2 < mom1):
                            
                            signal = DivergenceSignal(
                                timestamp=f2['timestamp'],
                                divergence_type='fractal',
                                timeframe='',  # Set later
                                indicator='momentum',
                                strength=abs(mom2 - mom1) / abs(mom1),
                                direction='bearish',
                                confidence=min(abs(mom2) / (abs(mom1) + abs(mom2)), 0.95),
                                levels={
                                    'price_1': f1['price'],
                                    'price_2': f2['price'],
                                    'momentum_1': float(mom1),
                                    'momentum_2': float(mom2)
                                },
                                metadata={
                                    'fractal_1': f1,
                                    'fractal_2': f2,
                                    'bars_between': f2['index'] - f1['index'],
                                    'macd_1': float(macd.iloc[f1['index']]),
                                    'macd_2': float(macd.iloc[f2['index']]),
                                    'stoch_1': float(stoch.iloc[f1['index']]),
                                    'stoch_2': float(stoch.iloc[f2['index']])
                                }
                            )
                            signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error finding fractal divergences: {e}")
            return []
    
    def _combine_signals(self, signals: List[DivergenceSignal],
                       data: pd.DataFrame,
                       timeframe: str) -> List[DivergenceSignal]:
        """Combine and filter divergence signals."""
        try:
            # Set timeframe for all signals
            for signal in signals:
                signal.timeframe = timeframe
            
            # Sort by strength and confidence
            signals.sort(key=lambda x: x.strength * x.confidence, reverse=True)
            
            # Filter weak signals
            strong_signals = [
                s for s in signals
                if s.strength * s.confidence > self.divergence_threshold
            ]
            
            # Store signals
            self.signals.extend(strong_signals)
            
            # Limit signal history
            if len(self.signals) > 1000:
                self.signals = self.signals[-1000:]
            
            return strong_signals
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return []
    
    def _update_state(self, signals: List[DivergenceSignal],
                    data: pd.DataFrame,
                    timeframe: str):
        """Update internal state tracking."""
        try:
            # Update fractal patterns
            if timeframe not in self.fractal_patterns:
                self.fractal_patterns[timeframe] = []
            
            for signal in signals:
                if signal.divergence_type == 'fractal':
                    self.fractal_patterns[timeframe].append((
                        signal.timestamp,
                        signal.levels['price_2']
                    ))
            
            # Limit pattern history
            if len(self.fractal_patterns[timeframe]) > 100:
                self.fractal_patterns[timeframe] = self.fractal_patterns[timeframe][-100:]
            
            # Update momentum states
            self.momentum_states[timeframe] = {
                'last_price': float(data['close'].iloc[-1]),
                'momentum_score': float(np.mean([s.strength * s.confidence 
                                               for s in signals]) if signals else 0)
            }
            
        except Exception as e:
            logger.error(f"Error updating state: {e}")
    
    def get_active_signals(self, current_time: datetime,
                         max_age_minutes: int = 60) -> List[DivergenceSignal]:
        """Get currently active signals."""
        active_signals = []
        
        for signal in self.signals:
            age_minutes = (current_time - signal.timestamp).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                active_signals.append(signal)
        
        return active_signals
