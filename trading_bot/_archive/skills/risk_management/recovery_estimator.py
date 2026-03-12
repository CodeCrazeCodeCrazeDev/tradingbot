"""
Skill #56: Recovery Time Estimator
==================================

Estimates time needed to recover from drawdowns.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Recovery estimation result."""
    estimated_days: float
    confidence_interval: tuple
    required_return: float
    historical_avg_recovery: float
    trading_signal: str


class RecoveryTimeEstimator:
    """Estimates recovery time from drawdowns."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("RecoveryTimeEstimator initialized")
    
    def estimate(self, current_drawdown: float, avg_daily_return: float, return_std: float) -> RecoveryResult:
        """Estimate recovery time."""
        if current_drawdown >= 0:
            return RecoveryResult(0, (0, 0), 0, 0, "No drawdown")
        
        required = -current_drawdown / (1 + current_drawdown)
        
        if avg_daily_return <= 0:
            days = float('inf')
            ci = (float('inf'), float('inf'))
        else:
            days = required / avg_daily_return
            std_days = return_std / avg_daily_return * np.sqrt(days) if avg_daily_return > 0 else 0
            ci = (max(0, days - 2 * std_days), days + 2 * std_days)
        
        signal = self._generate_signal(days, required)
        
        return RecoveryResult(
            estimated_days=days, confidence_interval=ci,
            required_return=required, historical_avg_recovery=days * 1.2,
            trading_signal=signal
        )
    
    def _generate_signal(self, days: float, required: float) -> str:
        if days > 100:
            return f"LONG RECOVERY: ~{days:.0f} days needed for {required:.1%} return"
        return f"RECOVERY: ~{days:.0f} days to recover {required:.1%}"
