"""
Skill #65: Strategy Decay Detector
==================================

Detects when strategies are losing effectiveness.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class DecayResult:
    """Strategy decay detection result."""
    decay_detected: bool
    decay_rate: float
    performance_trend: float
    days_to_ineffective: float
    trading_signal: str


class StrategyDecayDetector:
    """Detects strategy performance decay."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("StrategyDecayDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect(self, performance_history: np.ndarray) -> DecayResult:
        """Detect strategy decay."""
        try:
            if len(performance_history) < 20:
                return self._create_empty_result()
        
            # Calculate trend
            x = np.arange(len(performance_history))
            slope, _ = np.polyfit(x, performance_history, 1)
        
            decay_detected = slope < -0.001
            decay_rate = abs(slope) if slope < 0 else 0
        
            # Days to ineffective
            current_perf = performance_history[-1]
            if decay_rate > 0 and current_perf > 0:
                days = current_perf / decay_rate
            else:
                days = float('inf')
        
            return DecayResult(
                decay_detected=decay_detected, decay_rate=decay_rate,
                performance_trend=slope, days_to_ineffective=days,
                trading_signal=f"{'DECAY DETECTED' if decay_detected else 'STABLE'}: Rate {decay_rate:.4f}/day"
            )
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise
    
    def _create_empty_result(self) -> DecayResult:
        return DecayResult(False, 0, 0, float('inf'), "Insufficient data")
