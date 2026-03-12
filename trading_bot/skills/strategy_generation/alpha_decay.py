"""
Skill #66: Alpha Decay Forecaster
=================================

Forecasts alpha decay and signal half-life.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlphaDecayResult:
    """Alpha decay forecast result."""
    half_life: float
    current_alpha: float
    forecasted_alpha: Dict[int, float]
    decay_model: str
    trading_signal: str


class AlphaDecayForecaster:
    """Forecasts alpha signal decay."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("AlphaDecayForecaster initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forecast(self, alpha_history: np.ndarray) -> AlphaDecayResult:
        """Forecast alpha decay."""
        try:
            if len(alpha_history) < 10:
                return self._create_empty_result()
        
            current = alpha_history[-1]
        
            # Fit exponential decay
            x = np.arange(len(alpha_history))
            log_alpha = np.log(np.abs(alpha_history) + 1e-10)
            slope, intercept = np.polyfit(x, log_alpha, 1)
        
            half_life = -np.log(2) / slope if slope < 0 else float('inf')
        
            # Forecast
            forecasted = {}
            for days in [1, 5, 10, 20]:
                forecasted[days] = current * np.exp(slope * days)
        
            model = "exponential" if slope < 0 else "stable"
        
            return AlphaDecayResult(
                half_life=half_life, current_alpha=current,
                forecasted_alpha=forecasted, decay_model=model,
                trading_signal=f"ALPHA: Half-life {half_life:.1f} days, current {current:.4f}"
            )
        except Exception as e:
            logger.error(f"Error in forecast: {e}")
            raise
    
    def _create_empty_result(self) -> AlphaDecayResult:
        return AlphaDecayResult(0, 0, {}, "unknown", "Insufficient data")
