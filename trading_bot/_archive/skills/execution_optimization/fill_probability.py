"""
Skill #37: Fill Probability Predictor
=====================================

Predicts probability of order fill based on market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class FillProbabilityResult:
    """Fill probability prediction result."""
    fill_probability: float
    partial_fill_prob: float
    expected_fill_time: float
    price_improvement_prob: float
    trading_signal: str


class FillProbabilityPredictor:
    """Predicts order fill probability."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("FillProbabilityPredictor initialized")
    
    def predict(
        self,
        order_price: float,
        order_side: str,
        current_bid: float,
        current_ask: float,
        volatility: float,
        time_horizon: float = 60
    ) -> FillProbabilityResult:
        """Predict fill probability."""
        mid = (current_bid + current_ask) / 2
        spread = current_ask - current_bid
        
        # Distance from mid
        if order_side == 'buy':
            distance = (mid - order_price) / mid
        else:
            distance = (order_price - mid) / mid
        
        # Base probability from distance
        base_prob = np.exp(-distance / volatility) if volatility > 0 else 0.5
        
        # Adjust for time
        time_factor = 1 - np.exp(-time_horizon / 60)
        fill_prob = min(0.99, base_prob * time_factor)
        
        # Partial fill
        partial_prob = fill_prob * 0.8
        
        # Expected time
        expected_time = -np.log(1 - fill_prob + 0.01) * 60 / volatility if volatility > 0 else 60
        
        # Price improvement
        improvement_prob = 0.1 if distance > spread else 0.3
        
        signal = self._generate_signal(fill_prob, expected_time)
        
        return FillProbabilityResult(
            fill_probability=fill_prob,
            partial_fill_prob=partial_prob,
            expected_fill_time=expected_time,
            price_improvement_prob=improvement_prob,
            trading_signal=signal
        )
    
    def _generate_signal(self, prob: float, time: float) -> str:
        """Generate signal."""
        if prob > 0.8:
            return f"HIGH FILL PROB: {prob:.0%}, expected {time:.0f}s"
        elif prob > 0.5:
            return f"MODERATE: {prob:.0%} fill probability"
        return f"LOW FILL PROB: {prob:.0%}, consider adjusting price"
