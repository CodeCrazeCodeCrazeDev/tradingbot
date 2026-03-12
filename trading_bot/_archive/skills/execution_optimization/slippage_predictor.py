"""
Skill #44: Slippage Predictor
=============================

Predicts expected slippage based on order size,
market conditions, and historical patterns.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SlippagePrediction:
    """Slippage prediction result."""
    expected_slippage: float
    slippage_std: float
    worst_case: float
    best_case: float
    confidence_interval: tuple
    trading_signal: str


class SlippagePredictor:
    """Predicts execution slippage."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.slippage_history: List[float] = []
        logger.info("SlippagePredictor initialized")
    
    def predict(
        self,
        order_size: float,
        avg_volume: float,
        spread: float,
        volatility: float
    ) -> SlippagePrediction:
        """Predict slippage for order."""
        # Participation rate
        participation = order_size / (avg_volume + 1e-10)
        
        # Base slippage from spread
        base = spread / 2
        
        # Impact slippage
        impact = 0.1 * np.sqrt(participation) * volatility
        
        # Total expected
        expected = base + impact
        
        # Standard deviation
        std = volatility * np.sqrt(participation)
        
        # Worst/best case
        worst = expected + 2 * std
        best = max(0, expected - std)
        
        # Confidence interval
        ci = (expected - 1.96 * std, expected + 1.96 * std)
        
        self.slippage_history.append(expected)
        
        signal = self._generate_signal(expected, worst, participation)
        
        return SlippagePrediction(
            expected_slippage=expected,
            slippage_std=std,
            worst_case=worst,
            best_case=best,
            confidence_interval=ci,
            trading_signal=signal
        )
    
    def _generate_signal(self, expected: float, worst: float, part: float) -> str:
        """Generate signal."""
        if expected > 0.005:
            return f"HIGH SLIPPAGE: Expected {expected:.4%}, worst {worst:.4%}"
        elif expected > 0.001:
            return f"MODERATE: Expected {expected:.4%}, {part:.1%} participation"
        return f"LOW SLIPPAGE: Expected {expected:.4%}"
