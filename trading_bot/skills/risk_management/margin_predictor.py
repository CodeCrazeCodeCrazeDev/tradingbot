"""
Skill #59: Margin Call Predictor
================================

Predicts probability of margin calls based on portfolio risk.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarginCallResult:
    """Margin call prediction result."""
    margin_call_probability: float
    days_to_margin_call: float
    current_margin_usage: float
    buffer_remaining: float
    trading_signal: str


class MarginCallPredictor:
    """Predicts margin call probability."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("MarginCallPredictor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def predict(
        self,
        portfolio_value: float,
        margin_used: float,
        maintenance_margin: float,
        volatility: float
    ) -> MarginCallResult:
        """Predict margin call probability."""
        try:
            margin_usage = margin_used / (portfolio_value + 1e-10)
            buffer = portfolio_value - maintenance_margin
            buffer_pct = buffer / (portfolio_value + 1e-10)
        
            # Probability based on buffer and volatility
            z_score = buffer_pct / (volatility * np.sqrt(1/252) + 1e-10)
            prob = 1 - 0.5 * (1 + np.erf(z_score / np.sqrt(2)))
        
            # Days to margin call
            if volatility > 0:
                days = (buffer_pct / volatility) ** 2 * 252
            else:
                days = float('inf')
        
            signal = self._generate_signal(prob, days, margin_usage)
        
            return MarginCallResult(
                margin_call_probability=prob, days_to_margin_call=days,
                current_margin_usage=margin_usage, buffer_remaining=buffer_pct,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def _generate_signal(self, prob: float, days: float, usage: float) -> str:
        try:
            if prob > 0.2:
                return f"HIGH MARGIN RISK: {prob:.0%} probability, ~{days:.0f} days buffer"
            return f"MARGIN OK: {usage:.0%} used, {prob:.0%} call probability"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
