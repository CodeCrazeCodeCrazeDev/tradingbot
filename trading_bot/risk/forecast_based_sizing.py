"""
Forecast-Based Position Sizing

Uses TFT forecast uncertainty to dynamically adjust position sizes.
Wide prediction intervals → reduce size
Narrow intervals → increase size (up to Kelly limit)
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class ForecastSignal:
    """Forecast signal with uncertainty quantification"""
    median_prediction: float  # 50th percentile
    lower_bound: float  # 10th percentile
    upper_bound: float  # 90th percentile
    confidence: float  # 0-1 scale
    horizon: int  # Forecast horizon in hours
    
    @property
    def prediction_interval_width(self) -> float:
        """Width of 80% prediction interval"""
        return self.upper_bound - self.lower_bound
    
    @property
    def is_bullish(self) -> bool:
        """Is forecast bullish (median > 0)?"""
        return self.median_prediction > 0
    
    @property
    def is_bearish(self) -> bool:
        """Is forecast bearish (median < 0)?"""
        return self.median_prediction < 0


class ForecastBasedSizer:
    """
    Position sizer that uses forecast uncertainty
    
    Logic:
    - Wide prediction interval → high uncertainty → reduce size
    - Narrow interval → low uncertainty → increase size
    - High confidence favorable forecast → larger position
    - Low confidence → smaller position
    """
    
    def __init__(
        self,
        base_size: float = 0.10,
        max_size: float = 0.50,
        min_size: float = 0.01,
        narrow_threshold_pips: float = 20.0,
        wide_threshold_pips: float = 50.0,
        confidence_threshold: float = 0.6
    ):
        """
        Args:
            base_size: Base position size in lots
            max_size: Maximum position size in lots
            min_size: Minimum position size in lots
            narrow_threshold_pips: Threshold for narrow prediction interval
            wide_threshold_pips: Threshold for wide prediction interval
            confidence_threshold: Minimum confidence for trading
        """
        try:
            self.base_size = base_size
            self.max_size = max_size
            self.min_size = min_size
            self.narrow_threshold_pips = narrow_threshold_pips
            self.wide_threshold_pips = wide_threshold_pips
            self.confidence_threshold = confidence_threshold
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_position_size(
        self,
        forecast: ForecastSignal,
        kelly_limit: Optional[float] = None,
        current_equity: float = 10000.0,
        pip_value: float = 10.0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate optimal position size based on forecast
        
        Args:
            forecast: Forecast signal with uncertainty
            kelly_limit: Maximum size from Kelly criterion
            current_equity: Current account equity
            pip_value: Value of 1 pip for 1 lot
            
        Returns:
            Tuple of (position_size, sizing_details)
        """
        # Convert prediction interval to pips (assuming returns are in decimal)
        try:
            interval_pips = forecast.prediction_interval_width * 10000
        
            # Base multiplier from prediction interval
            if interval_pips < self.narrow_threshold_pips:
                # Narrow interval → high confidence → increase size
                interval_multiplier = 1.5
                interval_regime = "narrow"
            elif interval_pips > self.wide_threshold_pips:
                # Wide interval → low confidence → reduce size
                interval_multiplier = 0.5
                interval_regime = "wide"
            else:
                # Normal interval
                interval_multiplier = 1.0
                interval_regime = "normal"
        
            # Confidence multiplier
            if forecast.confidence > 0.8:
                confidence_multiplier = 1.3
            elif forecast.confidence > self.confidence_threshold:
                confidence_multiplier = 1.0
            else:
                confidence_multiplier = 0.5
        
            # Direction alignment (forecast should be favorable)
            direction_multiplier = 1.0
            if abs(forecast.median_prediction) < 0.0001:  # Very small prediction
                direction_multiplier = 0.3
        
            # Calculate size
            size = self.base_size * interval_multiplier * confidence_multiplier * direction_multiplier
        
            # Apply Kelly limit if provided
            if kelly_limit is not None:
                size = min(size, kelly_limit)
        
            # Apply min/max constraints
            size = np.clip(size, self.min_size, self.max_size)
        
            # Calculate risk metrics
            expected_move_pips = abs(forecast.median_prediction) * 10000
            risk_pips = interval_pips / 2  # Half of prediction interval
            risk_amount = size * risk_pips * pip_value
            risk_percent = (risk_amount / current_equity) * 100
        
            sizing_details = {
                'position_size': size,
                'interval_pips': interval_pips,
                'interval_regime': interval_regime,
                'interval_multiplier': interval_multiplier,
                'confidence': forecast.confidence,
                'confidence_multiplier': confidence_multiplier,
                'direction_multiplier': direction_multiplier,
                'expected_move_pips': expected_move_pips,
                'risk_pips': risk_pips,
                'risk_amount': risk_amount,
                'risk_percent': risk_percent,
                'kelly_limit': kelly_limit,
            }
        
            logger.info(
                f"Forecast-based sizing: {size:.2f} lots "
                f"(interval: {interval_pips:.1f} pips [{interval_regime}], "
                f"confidence: {forecast.confidence:.2f}, "
                f"risk: {risk_percent:.2f}%)"
            )
        
            return size, sizing_details
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def should_trade(self, forecast: ForecastSignal) -> Tuple[bool, str]:
        """
        Determine if we should trade based on forecast
        
        Returns:
            Tuple of (should_trade, reason)
        """
        # Check confidence
        try:
            if forecast.confidence < self.confidence_threshold:
                return False, f"Low confidence: {forecast.confidence:.2f} < {self.confidence_threshold}"
        
            # Check prediction magnitude
            if abs(forecast.median_prediction) < 0.0001:
                return False, "Prediction too small (< 0.01%)"
        
            # Check prediction interval width
            interval_pips = forecast.prediction_interval_width * 10000
            if interval_pips > self.wide_threshold_pips * 2:
                return False, f"Prediction interval too wide: {interval_pips:.1f} pips"
        
            # Check direction consistency (bounds should agree on direction)
            if forecast.lower_bound > 0 and forecast.upper_bound > 0:
                return True, "Bullish forecast with high certainty"
            elif forecast.lower_bound < 0 and forecast.upper_bound < 0:
                return True, "Bearish forecast with high certainty"
            elif abs(forecast.median_prediction) > interval_pips / 10000:
                return True, "Directional forecast with moderate certainty"
            else:
                return False, "Prediction interval spans both directions"
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise
    
    def adjust_for_volatility(
        self,
        base_size: float,
        current_volatility: float,
        normal_volatility: float = 0.01
    ) -> float:
        """
        Adjust position size for current volatility
        
        Args:
            base_size: Base position size
            current_volatility: Current market volatility
            normal_volatility: Normal/average volatility
            
        Returns:
            Adjusted position size
        """
        try:
            volatility_ratio = current_volatility / normal_volatility
        
            # Inverse relationship: higher volatility → smaller size
            volatility_adjustment = 1.0 / np.sqrt(volatility_ratio)
        
            adjusted_size = base_size * volatility_adjustment
        
            logger.debug(
                f"Volatility adjustment: {volatility_ratio:.2f}x normal → "
                f"size multiplier {volatility_adjustment:.2f}"
            )
        
            return np.clip(adjusted_size, self.min_size, self.max_size)
        except Exception as e:
            logger.error(f"Error in adjust_for_volatility: {e}")
            raise
    
    def calculate_stop_loss(
        self,
        forecast: ForecastSignal,
        atr: float,
        multiplier: float = 2.0
    ) -> float:
        """
        Calculate stop loss based on forecast and ATR
        
        Args:
            forecast: Forecast signal
            atr: Average True Range
            multiplier: ATR multiplier for stop
            
        Returns:
            Stop loss distance in pips
        """
        # Use prediction interval as basis
        try:
            interval_pips = forecast.prediction_interval_width * 10000
        
            # ATR-based stop
            atr_pips = atr * 10000
            atr_stop = atr_pips * multiplier
        
            # Use wider of the two
            stop_loss_pips = max(interval_pips, atr_stop)
        
            # Minimum stop loss
            min_stop = 10.0  # 10 pips minimum
            stop_loss_pips = max(stop_loss_pips, min_stop)
        
            logger.debug(
                f"Stop loss: {stop_loss_pips:.1f} pips "
                f"(interval: {interval_pips:.1f}, ATR: {atr_stop:.1f})"
            )
        
            return stop_loss_pips
        except Exception as e:
            logger.error(f"Error in calculate_stop_loss: {e}")
            raise
    
    def calculate_take_profit(
        self,
        forecast: ForecastSignal,
        stop_loss_pips: float,
        min_risk_reward: float = 2.0
    ) -> float:
        """
        Calculate take profit based on forecast
        
        Args:
            forecast: Forecast signal
            stop_loss_pips: Stop loss distance
            min_risk_reward: Minimum risk:reward ratio
            
        Returns:
            Take profit distance in pips
        """
        # Expected move from forecast
        try:
            expected_move_pips = abs(forecast.median_prediction) * 10000
        
            # Minimum take profit from risk:reward
            min_tp = stop_loss_pips * min_risk_reward
        
            # Use larger of expected move or minimum R:R
            take_profit_pips = max(expected_move_pips, min_tp)
        
            logger.debug(
                f"Take profit: {take_profit_pips:.1f} pips "
                f"(expected: {expected_move_pips:.1f}, min R:R: {min_tp:.1f})"
            )
        
            return take_profit_pips
        except Exception as e:
            logger.error(f"Error in calculate_take_profit: {e}")
            raise


def example_usage():
    """Example usage of forecast-based sizing"""
    try:
        logging.basicConfig(level=logging.INFO)
    
        # Create sizer
        sizer = ForecastBasedSizer(
            base_size=0.10,
            max_size=0.50,
            narrow_threshold_pips=20.0,
            wide_threshold_pips=50.0
        )
    
        # Example 1: High confidence, narrow interval (bullish)
        forecast1 = ForecastSignal(
            median_prediction=0.0015,  # +0.15% (15 pips)
            lower_bound=0.0010,  # +0.10%
            upper_bound=0.0020,  # +0.20%
            confidence=0.85,
            horizon=24
        )
    
        should_trade, reason = sizer.should_trade(forecast1)
        logger.info(f"\nForecast 1: {reason}")
    
        if should_trade:
            size, details = sizer.calculate_position_size(forecast1, kelly_limit=0.30)
            logger.info(f"Position size: {size:.2f} lots")
            logger.info(f"Risk: {details['risk_percent']:.2f}%")
        
            stop_loss = sizer.calculate_stop_loss(forecast1, atr=0.0008)
            take_profit = sizer.calculate_take_profit(forecast1, stop_loss)
            logger.info(f"Stop loss: {stop_loss:.1f} pips")
            logger.info(f"Take profit: {take_profit:.1f} pips")
    
        # Example 2: Low confidence, wide interval
        forecast2 = ForecastSignal(
            median_prediction=0.0005,
            lower_bound=-0.0030,
            upper_bound=0.0040,
            confidence=0.45,
            horizon=24
        )
    
        should_trade, reason = sizer.should_trade(forecast2)
        logger.info(f"\nForecast 2: {reason}")
    
        if should_trade:
            size, details = sizer.calculate_position_size(forecast2)
            logger.info(f"Position size: {size:.2f} lots")
    
        # Example 3: High confidence, narrow interval (bearish)
        forecast3 = ForecastSignal(
            median_prediction=-0.0012,
            lower_bound=-0.0018,
            upper_bound=-0.0006,
            confidence=0.90,
            horizon=24
        )
    
        should_trade, reason = sizer.should_trade(forecast3)
        logger.info(f"\nForecast 3: {reason}")
    
        if should_trade:
            size, details = sizer.calculate_position_size(forecast3, kelly_limit=0.40)
            logger.info(f"Position size: {size:.2f} lots")
            logger.info(f"Risk: {details['risk_percent']:.2f}%")
    except Exception as e:
        logger.error(f"Error in example_usage: {e}")
        raise


if __name__ == "__main__":
    example_usage()
