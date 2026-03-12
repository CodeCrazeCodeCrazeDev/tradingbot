"""
Skill #34: Participation Rate Controller
========================================

Controls execution to maintain target participation rate
in market volume.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParticipationResult:
    """Participation rate control result."""
    target_rate: float
    current_rate: float
    adjustment_needed: float
    next_slice_size: float
    trading_signal: str


class ParticipationRateController:
    """Controls participation rate in market volume."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_participation = self.config.get('max_participation', 0.2)
        self.executed = 0.0
        self.market_volume = 0.0
        logger.info("ParticipationRateController initialized")
    
    def control(
        self,
        target_rate: float,
        remaining_quantity: float,
        recent_volume: float,
        expected_volume: float
    ) -> ParticipationResult:
        """Control participation rate."""
        self.market_volume += recent_volume
        
        current_rate = self.executed / (self.market_volume + 1e-10)
        adjustment = target_rate - current_rate
        
        # Calculate next slice
        next_slice = min(
            remaining_quantity,
            expected_volume * target_rate,
            expected_volume * self.max_participation
        )
        
        signal = self._generate_signal(target_rate, current_rate, adjustment)
        
        return ParticipationResult(
            target_rate=target_rate,
            current_rate=current_rate,
            adjustment_needed=adjustment,
            next_slice_size=next_slice,
            trading_signal=signal
        )
    
    def record_execution(self, quantity: float):
        """Record executed quantity."""
        self.executed += quantity
    
    def _generate_signal(self, target: float, current: float, adj: float) -> str:
        """Generate control signal."""
        if adj > 0.05:
            return f"INCREASE: Current {current:.1%} below target {target:.1%}"
        elif adj < -0.05:
            return f"DECREASE: Current {current:.1%} above target {target:.1%}"
        return f"ON TARGET: {current:.1%} participation"
    
    def reset(self):
        """Reset controller."""
        self.executed = 0.0
        self.market_volume = 0.0
