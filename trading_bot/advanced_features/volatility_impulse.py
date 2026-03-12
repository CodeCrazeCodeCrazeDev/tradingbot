"""Volatility Impulse Vector (VII) Module - Advanced Volatility Analysis.

This module implements the revolutionary Volatility Impulse Vector indicator that combines
the rate of change of volatility, volume surge, and order book imbalance to detect
explosive move directions before they occur.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from scipy.signal import savgol_filter
from scipy.stats import zscore
from sklearn.preprocessing import MinMaxScaler
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class VolatilityImpulse:
    """Represents a volatility impulse detection result."""
    timestamp: pd.Timestamp
    impulse_magnitude: float
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float
    acceleration: float
    volume_surge: float
    order_imbalance: float
    predicted_move_size: float


@dataclass
class EnergyVector:
    """Represents market energy vector components."""
    price_energy: float
    volume_energy: float
    volatility_energy: float
    combined_magnitude: float
    direction_angle: float  # In radians
    release_probability: float


class VolatilityImpulseVector:
    """
    Main class implementing the Volatility Impulse Vector (VII) indicator.
    
    This revolutionary indicator detects not just high volatility, but whether
    volatility is accelerating and predicts the direction of energy release.
    """
    
    def __init__(self, 
                 atr_period: int = 14,
                 volume_surge_threshold: float = 2.0,
                 imbalance_threshold: float = 0.3,
                 smoothing_window: int = 5):
        """
        Initialize the Volatility Impulse Vector indicator.
        
        Args:
            atr_period: Period for ATR calculation
            volume_surge_threshold: Multiplier for volume surge detection
            imbalance_threshold: Threshold for order book imbalance
            smoothing_window: Window for smoothing calculations
        """
        try:
            self.atr_period = atr_period
            self.volume_surge_threshold = volume_surge_threshold
            self.imbalance_threshold = imbalance_threshold
            self.smoothing_window = smoothing_window
        
            # Storage for historical data
            self.volatility_history: List[float] = []
            self.volume_history: List[float] = []
            self.price_history: List[float] = []
            self.impulse_history: List[VolatilityImpulse] = []
        
            # Scalers for normalization
            self.volatility_scaler = MinMaxScaler()
            self.volume_scaler = MinMaxScaler()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_volatility_acceleration(self, 
                                        price_data: pd.DataFrame,
                                        high_col: str = 'high',
                                        low_col: str = 'low',
                                        close_col: str = 'close') -> np.ndarray:
        """
        Calculate the acceleration of volatility (derivative of ATR).
        
        Returns:
            Array of volatility acceleration values
        """
        # Calculate True Range
        try:
            tr1 = price_data[high_col] - price_data[low_col]
            tr2 = abs(price_data[high_col] - price_data[close_col].shift(1))
            tr3 = abs(price_data[low_col] - price_data[close_col].shift(1))
        
            true_range = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        
            # Calculate ATR
            atr = true_range.rolling(window=self.atr_period).mean()
        
            # Calculate ATR rate of change (volatility acceleration)
            atr_roc = atr.pct_change(periods=1)
        
            # Smooth the acceleration
            if len(atr_roc) >= self.smoothing_window:
                atr_acceleration = pd.Series(
                    savgol_filter(atr_roc.fillna(0), 
                                 window_length=min(self.smoothing_window, len(atr_roc)),
                                 polyorder=2)
                )
            else:
                atr_acceleration = atr_roc.fillna(0)
        
            return atr_acceleration.values
        except Exception as e:
            logger.error(f"Error in calculate_volatility_acceleration: {e}")
            raise
    
    def detect_volume_surge(self, 
                          volume_data: pd.Series,
                          lookback_period: int = 20) -> np.ndarray:
        """
        Detect volume surges relative to recent average.
        
        Returns:
            Array of volume surge ratios
        """
        # Calculate rolling average volume
        try:
            avg_volume = volume_data.rolling(window=lookback_period).mean()
        
            # Calculate surge ratio
            volume_surge_ratio = volume_data / avg_volume
        
            # Normalize surge detection
            surge_signals = np.where(
                volume_surge_ratio >= self.volume_surge_threshold, 
                volume_surge_ratio, 
                0
            )
        
            return surge_signals
        except Exception as e:
            logger.error(f"Error in detect_volume_surge: {e}")
            raise
    
    def calculate_order_book_imbalance(self, 
                                     bid_volume: pd.Series,
                                     ask_volume: pd.Series) -> np.ndarray:
        """
        Calculate order book imbalance.
        
        Returns:
            Array of imbalance values (-1 to 1, negative = bearish, positive = bullish)
        """
        try:
            total_volume = bid_volume + ask_volume
        
            # Avoid division by zero
            total_volume = total_volume.replace(0, np.nan)
        
            # Calculate imbalance
            imbalance = (bid_volume - ask_volume) / total_volume
        
            return imbalance.fillna(0).values
        except Exception as e:
            logger.error(f"Error in calculate_order_book_imbalance: {e}")
            raise
    
    def calculate_impulse_vector(self, 
                               market_data: pd.DataFrame,
                               volume_col: str = 'volume',
                               bid_volume_col: Optional[str] = None,
                               ask_volume_col: Optional[str] = None) -> List[VolatilityImpulse]:
        """
        Calculate the complete Volatility Impulse Vector.
        
        Returns:
            List of VolatilityImpulse objects
        """
        try:
            impulses = []
        
            # Calculate volatility acceleration
            vol_acceleration = self.calculate_volatility_acceleration(market_data)
        
            # Calculate volume surge
            volume_surge = self.detect_volume_surge(market_data[volume_col])
        
            # Calculate order book imbalance (if data available)
            if bid_volume_col and ask_volume_col and bid_volume_col in market_data.columns:
                order_imbalance = self.calculate_order_book_imbalance(
                    market_data[bid_volume_col], 
                    market_data[ask_volume_col]
                )
            else:
                # Estimate imbalance from price action
                order_imbalance = self._estimate_imbalance_from_price(market_data)
        
            # Combine components into impulse vector
            for i in range(len(market_data)):
                if i < max(self.atr_period, self.smoothing_window):
                    continue  # Skip initial periods with insufficient data
            
                # Get current values
                vol_accel = vol_acceleration[i] if i < len(vol_acceleration) else 0
                vol_surge = volume_surge[i] if i < len(volume_surge) else 0
                imbalance = order_imbalance[i] if i < len(order_imbalance) else 0
            
                # Calculate impulse magnitude
                impulse_magnitude = self._calculate_impulse_magnitude(
                    vol_accel, vol_surge, abs(imbalance)
                )
            
                # Determine direction
                direction = self._determine_impulse_direction(
                    vol_accel, imbalance, market_data.iloc[i]
                )
            
                # Calculate confidence
                confidence = self._calculate_impulse_confidence(
                    vol_accel, vol_surge, imbalance
                )
            
                # Predict move size
                predicted_move = self._predict_move_size(
                    impulse_magnitude, vol_accel, market_data.iloc[i]
                )
            
                impulse = VolatilityImpulse(
                    timestamp=market_data.index[i],
                    impulse_magnitude=impulse_magnitude,
                    direction=direction,
                    confidence=confidence,
                    acceleration=vol_accel,
                    volume_surge=vol_surge,
                    order_imbalance=imbalance,
                    predicted_move_size=predicted_move
                )
            
                impulses.append(impulse)
        
            self.impulse_history.extend(impulses)
            return impulses
        except Exception as e:
            logger.error(f"Error in calculate_impulse_vector: {e}")
            raise
    
    def _estimate_imbalance_from_price(self, market_data: pd.DataFrame) -> np.ndarray:
        """Estimate order imbalance from price action when order book data unavailable."""
        # Use price momentum and volume relationship
        try:
            price_momentum = market_data['close'].pct_change()
            volume_ratio = market_data['volume'] / market_data['volume'].rolling(10).mean()
        
            # Estimate imbalance based on price-volume relationship
            estimated_imbalance = price_momentum * np.log1p(volume_ratio)
        
            # Normalize to [-1, 1] range
            if len(estimated_imbalance) > 1:
                estimated_imbalance = zscore(estimated_imbalance.fillna(0))
                estimated_imbalance = np.tanh(estimated_imbalance)  # Bounded to [-1, 1]
            else:
                estimated_imbalance = estimated_imbalance.fillna(0).values
        
            # Handle both numpy array and pandas Series
            if hasattr(estimated_imbalance, 'values'):
                return estimated_imbalance.values
            return estimated_imbalance
        except Exception as e:
            logger.error(f"Error in _estimate_imbalance_from_price: {e}")
            raise
    
    def _calculate_impulse_magnitude(self, 
                                   vol_acceleration: float,
                                   volume_surge: float,
                                   imbalance_strength: float) -> float:
        """Calculate the magnitude of the volatility impulse."""
        # Weighted combination of components
        try:
            magnitude = (
                abs(vol_acceleration) * 0.4 +
                volume_surge * 0.35 +
                imbalance_strength * 0.25
            )
        
            return magnitude
        except Exception as e:
            logger.error(f"Error in _calculate_impulse_magnitude: {e}")
            raise
    
    def _determine_impulse_direction(self, 
                                   vol_acceleration: float,
                                   order_imbalance: float,
                                   current_bar: pd.Series) -> str:
        """Determine the direction of the impulse."""
        # Combine multiple directional signals
        try:
            price_direction = 1 if current_bar['close'] > current_bar['open'] else -1
            imbalance_direction = 1 if order_imbalance > 0 else -1
        
            # Weight the signals
            combined_signal = (
                price_direction * 0.4 +
                imbalance_direction * 0.6
            )
        
            if combined_signal > 0.2:
                return 'bullish'
            elif combined_signal < -0.2:
                return 'bearish'
            else:
                return 'neutral'
        except Exception as e:
            logger.error(f"Error in _determine_impulse_direction: {e}")
            raise
    
    def _calculate_impulse_confidence(self, 
                                    vol_acceleration: float,
                                    volume_surge: float,
                                    order_imbalance: float) -> float:
        """Calculate confidence score for the impulse."""
        # Higher values in all components increase confidence
        try:
            vol_confidence = min(abs(vol_acceleration) * 10, 1.0)
            volume_confidence = min(volume_surge / self.volume_surge_threshold, 1.0)
            imbalance_confidence = min(abs(order_imbalance) / self.imbalance_threshold, 1.0)
        
            # Combined confidence
            confidence = (vol_confidence + volume_confidence + imbalance_confidence) / 3.0
        
            return min(confidence, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_impulse_confidence: {e}")
            raise
    
    def _predict_move_size(self, 
                         impulse_magnitude: float,
                         vol_acceleration: float,
                         current_bar: pd.Series) -> float:
        """Predict the size of the expected move."""
        # Base prediction on current volatility and impulse strength
        try:
            current_range = current_bar['high'] - current_bar['low']
        
            # Scale prediction by impulse magnitude
            predicted_move = current_range * (1 + impulse_magnitude * 2)
        
            return predicted_move
        except Exception as e:
            logger.error(f"Error in _predict_move_size: {e}")
            raise


class VolatilityAccelerationDetector:
    """
    Specialized detector for volatility acceleration patterns.
    """
    
    def __init__(self, 
                 detection_window: int = 10,
                 acceleration_threshold: float = 0.5):
        """Initialize the Volatility Acceleration Detector."""
        try:
            self.detection_window = detection_window
            self.acceleration_threshold = acceleration_threshold
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_acceleration_breakout(self, 
                                   volatility_data: pd.Series) -> Dict:
        """
        Detect volatility acceleration breakouts.
        
        Returns:
            Dictionary with breakout analysis
        """
        try:
            if len(volatility_data) < self.detection_window * 2:
                return {'breakout_detected': False, 'confidence': 0.0}
        
            # Calculate acceleration
            acceleration = volatility_data.diff().rolling(self.detection_window).mean()
        
            # Detect significant acceleration
            recent_acceleration = acceleration.iloc[-1]
            historical_std = acceleration.std()
        
            # Normalize acceleration
            if historical_std > 0:
                acceleration_zscore = recent_acceleration / historical_std
            else:
                acceleration_zscore = 0
        
            # Detect breakout
            breakout_detected = abs(acceleration_zscore) > self.acceleration_threshold
            confidence = min(abs(acceleration_zscore) / self.acceleration_threshold, 1.0)
        
            return {
                'breakout_detected': breakout_detected,
                'confidence': confidence,
                'acceleration_zscore': acceleration_zscore,
                'direction': 'up' if acceleration_zscore > 0 else 'down'
            }
        except Exception as e:
            logger.error(f"Error in detect_acceleration_breakout: {e}")
            raise


class EnergyDirectionPredictor:
    """
    Predicts the direction of energy release using vector analysis.
    """
    
    def __init__(self, 
                 energy_components: int = 3,
                 prediction_horizon: int = 5):
        """Initialize the Energy Direction Predictor."""
        try:
            self.energy_components = energy_components
            self.prediction_horizon = prediction_horizon
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_energy_vectors(self, 
                               market_data: pd.DataFrame) -> List[EnergyVector]:
        """
        Calculate market energy vectors.
        
        Returns:
            List of EnergyVector objects
        """
        try:
            energy_vectors = []
        
            # Calculate price energy (momentum)
            price_energy = self._calculate_price_energy(market_data)
        
            # Calculate volume energy
            volume_energy = self._calculate_volume_energy(market_data)
        
            # Calculate volatility energy
            volatility_energy = self._calculate_volatility_energy(market_data)
        
            for i in range(len(market_data)):
                if i < 20:  # Need sufficient history
                    continue
            
                # Get current energy components
                p_energy = price_energy[i] if i < len(price_energy) else 0
                v_energy = volume_energy[i] if i < len(volume_energy) else 0
                vol_energy = volatility_energy[i] if i < len(volatility_energy) else 0
            
                # Calculate combined magnitude
                magnitude = np.sqrt(p_energy**2 + v_energy**2 + vol_energy**2)
            
                # Calculate direction angle
                direction_angle = np.arctan2(v_energy, p_energy)
            
                # Calculate release probability
                release_prob = self._calculate_release_probability(
                    p_energy, v_energy, vol_energy
                )
            
                energy_vector = EnergyVector(
                    price_energy=p_energy,
                    volume_energy=v_energy,
                    volatility_energy=vol_energy,
                    combined_magnitude=magnitude,
                    direction_angle=direction_angle,
                    release_probability=release_prob
                )
            
                energy_vectors.append(energy_vector)
        
            return energy_vectors
        except Exception as e:
            logger.error(f"Error in calculate_energy_vectors: {e}")
            raise
    
    def _calculate_price_energy(self, market_data: pd.DataFrame) -> np.ndarray:
        """Calculate price energy component."""
        # Use momentum and acceleration
        try:
            returns = market_data['close'].pct_change()
            momentum = returns.rolling(10).mean()
            acceleration = momentum.diff()
        
            price_energy = momentum + acceleration * 0.5
            return price_energy.fillna(0).values
        except Exception as e:
            logger.error(f"Error in _calculate_price_energy: {e}")
            raise
    
    def _calculate_volume_energy(self, market_data: pd.DataFrame) -> np.ndarray:
        """Calculate volume energy component."""
        # Use volume momentum and relative strength
        try:
            volume_momentum = market_data['volume'].pct_change()
            volume_strength = market_data['volume'] / market_data['volume'].rolling(20).mean()
        
            volume_energy = volume_momentum * np.log1p(volume_strength)
            return volume_energy.fillna(0).values
        except Exception as e:
            logger.error(f"Error in _calculate_volume_energy: {e}")
            raise
    
    def _calculate_volatility_energy(self, market_data: pd.DataFrame) -> np.ndarray:
        """Calculate volatility energy component."""
        # Use range expansion and contraction
        try:
            true_range = np.maximum(
                market_data['high'] - market_data['low'],
                np.maximum(
                    abs(market_data['high'] - market_data['close'].shift(1)),
                    abs(market_data['low'] - market_data['close'].shift(1))
                )
            )
        
            volatility_momentum = true_range.pct_change()
            volatility_energy = volatility_momentum.rolling(5).mean()
        
            return volatility_energy.fillna(0).values
        except Exception as e:
            logger.error(f"Error in _calculate_volatility_energy: {e}")
            raise
    
    def _calculate_release_probability(self, 
                                     price_energy: float,
                                     volume_energy: float,
                                     volatility_energy: float) -> float:
        """Calculate probability of energy release."""
        # Higher energy in all components increases release probability
        try:
            energy_sum = abs(price_energy) + abs(volume_energy) + abs(volatility_energy)
        
            # Use sigmoid function to bound probability
            release_prob = 1 / (1 + np.exp(-energy_sum * 5))
        
            return release_prob
        except Exception as e:
            logger.error(f"Error in _calculate_release_probability: {e}")
            raise
    
    def predict_energy_release(self, 
                             energy_vectors: List[EnergyVector],
                             current_price: float) -> Dict:
        """
        Predict when and where energy will be released.
        
        Returns:
            Dictionary with prediction results
        """
        try:
            if len(energy_vectors) < self.prediction_horizon:
                return {'prediction_available': False}
        
            recent_vectors = energy_vectors[-self.prediction_horizon:]
        
            # Analyze energy buildup trend
            magnitude_trend = np.polyfit(
                range(len(recent_vectors)),
                [v.combined_magnitude for v in recent_vectors],
                1
            )[0]
        
            # Average release probability
            avg_release_prob = np.mean([v.release_probability for v in recent_vectors])
        
            # Predict direction based on energy vector angles
            avg_direction = np.mean([v.direction_angle for v in recent_vectors])
        
            # Predict target price
            latest_magnitude = recent_vectors[-1].combined_magnitude
            predicted_move = latest_magnitude * current_price * 0.01  # 1% per unit magnitude
        
            if avg_direction > 0:
                target_price = current_price + predicted_move
                direction = 'bullish'
            else:
                target_price = current_price - predicted_move
                direction = 'bearish'
        
            return {
                'prediction_available': True,
                'direction': direction,
                'target_price': target_price,
                'release_probability': avg_release_prob,
                'magnitude_trend': magnitude_trend,
                'confidence': min(avg_release_prob * 2, 1.0)
            }
        except Exception as e:
            logger.error(f"Error in predict_energy_release: {e}")
            raise
