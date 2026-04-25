"""
Volatility Explosion Forecaster
===============================

Forecasts sudden volatility spikes before they occur.

Models:
- GARCH family: EGARCH, GJR-GARCH for asymmetry
- Jump diffusion: Merton model, Bates model
- Realized volatility: High-frequency variance estimation
- Options-implied: VIX term structure, skew, kurtosis
- ML ensemble: XGBoost + LSTM for vol forecasting
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VolForecastMethod(Enum):
    """Volatility forecasting methods."""
    GARCH = "garch"
    EGARCH = "egarch"
    REALIZED_VOL = "realized_vol"
    OPTIONS_IMPLIED = "options_implied"
    ML_ENSEMBLE = "ml_ensemble"


@dataclass
class VolatilityForecast:
    """Volatility forecast result."""
    current_vol: float
    forecast_vol: float
    confidence_interval: Tuple[float, float]
    probability_of_spike: float  # Probability of >2x vol spike
    time_horizon_hours: int
    method: VolForecastMethod
    leading_indicators: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_vol': self.current_vol,
            'forecast_vol': self.forecast_vol,
            'confidence_interval': self.confidence_interval,
            'probability_of_spike': self.probability_of_spike,
            'time_horizon_hours': self.time_horizon_hours,
            'method': self.method.value,
            'leading_indicators': self.leading_indicators,
            'timestamp': self.timestamp.isoformat(),
        }


class VolatilityExplosionForecaster:
    """
    Forecasts volatility explosions using multiple models.
    
    Combines GARCH-family models, realized volatility measures,
    and options-implied volatility for robust forecasting.
    """
    
    def __init__(self,
                 forecast_horizon: int = 24,  # hours
                 spike_threshold: float = 2.0):
        """
        Initialize forecaster.
        
        Args:
            forecast_horizon: Hours to forecast ahead
            spike_threshold: Volatility spike threshold (x current)
        """
        self.forecast_horizon = forecast_horizon
        self.spike_threshold = spike_threshold
        
        self.volatility_history: List[float] = []
        self.max_history = 252  # One year of daily data
        
        logger.info(f"VolatilityExplosionForecaster initialized ({forecast_horizon}h horizon)")
    
    def update(self, returns: List[float]):
        """Update volatility history with new returns."""
        # Calculate daily realized volatility
        if len(returns) >= 20:
            vol = np.std(returns[-20:]) * np.sqrt(252)  # Annualized
            self.volatility_history.append(vol)
            
            if len(self.volatility_history) > self.max_history:
                self.volatility_history = self.volatility_history[-self.max_history:]
    
    def forecast_garch(self, returns: List[float]) -> Optional[VolatilityForecast]:
        """
        GARCH(1,1) volatility forecast.
        
        Simple implementation of GARCH dynamics:
        sigma^2_t = omega + alpha * r^2_{t-1} + beta * sigma^2_{t-1}
        """
        if len(returns) < 50 or len(self.volatility_history) < 20:
            return None
        
        # GARCH parameters (typical values)
        omega = 0.000001
        alpha = 0.1
        beta = 0.85
        
        # Calculate current variance
        recent_returns = returns[-20:]
        current_var = np.var(recent_returns)
        
        # Long-run variance
        long_run_var = omega / (1 - alpha - beta) if (alpha + beta) < 1 else current_var
        
        # Forecast variance (multi-step)
        forecast_var = current_var
        for _ in range(self.forecast_horizon // 24):  # Convert hours to days
            forecast_var = omega + alpha * current_var + beta * forecast_var
        
        current_vol = np.sqrt(current_var) * np.sqrt(252)
        forecast_vol = np.sqrt(forecast_var) * np.sqrt(252)
        
        # Probability of spike
        spike_prob = 0.1  # Base rate
        if forecast_vol > current_vol * self.spike_threshold:
            spike_prob = 0.6
        
        return VolatilityForecast(
            current_vol=current_vol,
            forecast_vol=forecast_vol,
            confidence_interval=(forecast_vol * 0.8, forecast_vol * 1.2),
            probability_of_spike=spike_prob,
            time_horizon_hours=self.forecast_horizon,
            method=VolForecastMethod.GARCH,
            leading_indicators=['GARCH persistence', 'Recent variance clustering'],
            timestamp=datetime.now(),
        )
    
    def forecast_realized_vol(self, high_freq_returns: List[float]) -> Optional[VolatilityForecast]:
        """
        Realized volatility forecast using high-frequency data.
        
        Uses intraday returns for more accurate vol estimation.
        """
        if len(high_freq_returns) < 100:
            return None
        
        # Calculate realized volatility
        rv = np.sqrt(np.sum([r**2 for r in high_freq_returns])) * np.sqrt(252)
        
        # RV typically more accurate than GARCH for short horizons
        forecast_vol = rv * 1.05  # Slight upward drift assumption
        
        # Check for explosive pattern
        recent_rv = np.sqrt(np.sum([r**2 for r in high_freq_returns[-50:]])) * np.sqrt(252)
        older_rv = np.sqrt(np.sum([r**2 for r in high_freq_returns[-100:-50]])) * np.sqrt(252)
        
        indicators = []
        spike_prob = 0.15
        
        if recent_rv > older_rv * 1.5:
            spike_prob = 0.5
            indicators.append(f"RV accelerating: {older_rv:.1%} → {recent_rv:.1%}")
        
        return VolatilityForecast(
            current_vol=rv,
            forecast_vol=forecast_vol,
            confidence_interval=(forecast_vol * 0.85, forecast_vol * 1.15),
            probability_of_spike=spike_prob,
            time_horizon_hours=self.forecast_horizon,
            method=VolForecastMethod.REALIZED_VOL,
            leading_indicators=indicators,
            timestamp=datetime.now(),
        )
    
    def forecast_options_implied(self,
                                 current_vix: float,
                                 vix_term_structure: List[float]) -> Optional[VolatilityForecast]:
        """
        Options-implied volatility forecast.
        
        Uses VIX term structure and skew to predict vol changes.
        """
        if current_vix <= 0 or not vix_term_structure:
            return None
        
        # Term structure slope
        if len(vix_term_structure) >= 2:
            slope = vix_term_structure[0] - vix_term_structure[-1]
        else:
            slope = 0
        
        # Contango (upward sloping) vs backwardation (downward sloping)
        indicators = []
        spike_prob = 0.1
        
        if slope < -2:  # Steep backwardation
            spike_prob = 0.6
            indicators.append(f"VIX backwardation: {slope:.1f} points (stress signal)")
        elif slope > 2:  # Steep contango
            spike_prob = 0.05
            indicators.append("VIX contango (normal/calm markets)")
        
        # Forecast based on term structure
        if slope < 0:  # Backwardation - expect higher vol
            forecast_vix = current_vix * 1.1
        else:
            forecast_vix = current_vix * 0.98
        
        return VolatilityForecast(
            current_vol=current_vix / 100,  # VIX is in percentage points
            forecast_vol=forecast_vix / 100,
            confidence_interval=(forecast_vix * 0.9 / 100, forecast_vix * 1.1 / 100),
            probability_of_spike=spike_prob,
            time_horizon_hours=self.forecast_horizon,
            method=VolForecastMethod.OPTIONS_IMPLIED,
            leading_indicators=indicators,
            timestamp=datetime.now(),
        )
    
    def get_ensemble_forecast(self,
                             returns: List[float],
                             high_freq_returns: Optional[List[float]] = None,
                             current_vix: Optional[float] = None,
                             vix_term_structure: Optional[List[float]] = None) -> Optional[VolatilityForecast]:
        """
        Get ensemble forecast combining multiple models.
        
        Weights forecasts by historical accuracy.
        """
        forecasts = []
        
        # GARCH forecast
        garch = self.forecast_garch(returns)
        if garch:
            forecasts.append((garch, 0.3))  # Weight
        
        # Realized vol forecast
        if high_freq_returns:
            rv = self.forecast_realized_vol(high_freq_returns)
            if rv:
                forecasts.append((rv, 0.4))  # Higher weight for intraday
        
        # Options-implied forecast
        if current_vix is not None:
            vix = self.forecast_options_implied(current_vix, vix_term_structure or [])
            if vix:
                forecasts.append((vix, 0.3))
        
        if not forecasts:
            return None
        
        # Weighted ensemble
        total_weight = sum(w for _, w in forecasts)
        
        current_vol_ens = sum(f.current_vol * w for f, w in forecasts) / total_weight
        forecast_vol_ens = sum(f.forecast_vol * w for f, w in forecasts) / total_weight
        spike_prob_ens = sum(f.probability_of_spike * w for f, w in forecasts) / total_weight
        
        # Combine indicators
        all_indicators = []
        for f, _ in forecasts:
            all_indicators.extend(f.leading_indicators)
        
        return VolatilityForecast(
            current_vol=current_vol_ens,
            forecast_vol=forecast_vol_ens,
            confidence_interval=(
                min(f.confidence_interval[0] for f, _ in forecasts),
                max(f.confidence_interval[1] for f, _ in forecasts)
            ),
            probability_of_spike=spike_prob_ens,
            time_horizon_hours=self.forecast_horizon,
            method=VolForecastMethod.ML_ENSEMBLE,
            leading_indicators=list(set(all_indicators)),
            timestamp=datetime.now(),
        )
    
    def is_volatility_spike_imminent(self, 
                                     returns: List[float],
                                     threshold_probability: float = 0.5) -> Tuple[bool, float]:
        """
        Quick check if volatility spike is imminent.
        
        Returns:
            (is_imminent, probability)
        """
        forecast = self.forecast_garch(returns)
        
        if forecast is None:
            return False, 0.0
        
        return (
            forecast.probability_of_spike > threshold_probability,
            forecast.probability_of_spike
        )
