"""
Skill #33: Implementation Shortfall Minimizer
=============================================

Minimizes the difference between decision price and
actual execution price.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ShortfallComponent:
    """Component of implementation shortfall."""
    delay_cost: float
    market_impact: float
    timing_cost: float
    opportunity_cost: float
    total: float


@dataclass
class ShortfallResult:
    """Implementation shortfall analysis result."""
    shortfall: ShortfallComponent
    optimal_speed: float
    recommended_duration: int
    trading_signal: str


class ImplementationShortfallMinimizer:
    """Minimizes implementation shortfall in execution."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("ImplementationShortfallMinimizer initialized")
    
    def analyze(
        self,
        decision_price: float,
        current_price: float,
        quantity: float,
        volatility: float,
        avg_volume: float
    ) -> ShortfallResult:
        """Analyze and minimize implementation shortfall."""
        # Calculate shortfall components
        delay = abs(current_price - decision_price) / decision_price
        impact = self._estimate_market_impact(quantity, avg_volume, volatility)
        timing = volatility * np.sqrt(1/252)  # Daily timing risk
        opportunity = delay * 0.5  # Opportunity cost
        
        shortfall = ShortfallComponent(
            delay_cost=delay,
            market_impact=impact,
            timing_cost=timing,
            opportunity_cost=opportunity,
            total=delay + impact + timing + opportunity
        )
        
        # Optimal execution speed
        optimal_speed = self._calculate_optimal_speed(volatility, impact)
        duration = int(60 / optimal_speed) if optimal_speed > 0 else 60
        
        signal = self._generate_signal(shortfall, optimal_speed)
        
        return ShortfallResult(
            shortfall=shortfall,
            optimal_speed=optimal_speed,
            recommended_duration=duration,
            trading_signal=signal
        )
    
    def _estimate_market_impact(self, qty: float, vol: float, volatility: float) -> float:
        """Estimate market impact."""
        participation = qty / (vol + 1e-10)
        return 0.1 * np.sqrt(participation) * volatility
    
    def _calculate_optimal_speed(self, volatility: float, impact: float) -> float:
        """Calculate optimal execution speed."""
        return np.sqrt(volatility / (impact + 1e-10))
    
    def _generate_signal(self, shortfall: ShortfallComponent, speed: float) -> str:
        """Generate trading signal."""
        if shortfall.total > 0.01:
            return f"HIGH SHORTFALL ({shortfall.total:.2%}): Execute at speed {speed:.2f}"
        return f"LOW SHORTFALL ({shortfall.total:.2%}): Normal execution"
