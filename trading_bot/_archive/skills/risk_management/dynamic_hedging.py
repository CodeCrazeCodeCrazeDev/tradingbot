"""
Skill #48: Dynamic Hedging Engine
=================================

Dynamically adjusts hedges based on portfolio Greeks and market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class HedgeRecommendation:
    """Hedge recommendation."""
    instrument: str
    quantity: float
    direction: str
    urgency: str


@dataclass
class DynamicHedgingResult:
    """Dynamic hedging result."""
    current_exposure: Dict[str, float]
    hedge_recommendations: List[HedgeRecommendation]
    hedge_cost: float
    residual_risk: float
    trading_signal: str


class DynamicHedgingEngine:
    """Dynamically manages portfolio hedges."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.1)
        logger.info("DynamicHedgingEngine initialized")
    
    def analyze(
        self,
        portfolio_delta: float,
        portfolio_gamma: float,
        portfolio_vega: float,
        spot_price: float,
        volatility: float
    ) -> DynamicHedgingResult:
        """Analyze and recommend hedges."""
        exposure = {
            'delta': portfolio_delta,
            'gamma': portfolio_gamma,
            'vega': portfolio_vega
        }
        
        recommendations = []
        
        # Delta hedge
        if abs(portfolio_delta) > self.rebalance_threshold:
            recommendations.append(HedgeRecommendation(
                instrument='underlying',
                quantity=abs(portfolio_delta),
                direction='sell' if portfolio_delta > 0 else 'buy',
                urgency='high' if abs(portfolio_delta) > 0.5 else 'medium'
            ))
        
        # Gamma hedge
        if abs(portfolio_gamma) > self.rebalance_threshold:
            recommendations.append(HedgeRecommendation(
                instrument='options',
                quantity=abs(portfolio_gamma) * 100,
                direction='buy' if portfolio_gamma < 0 else 'sell',
                urgency='medium'
            ))
        
        # Vega hedge
        if abs(portfolio_vega) > self.rebalance_threshold * 1000:
            recommendations.append(HedgeRecommendation(
                instrument='variance_swap',
                quantity=abs(portfolio_vega),
                direction='buy' if portfolio_vega < 0 else 'sell',
                urgency='low'
            ))
        
        hedge_cost = sum(0.001 * r.quantity for r in recommendations)
        residual = np.sqrt(portfolio_delta**2 + portfolio_gamma**2 * spot_price**2 * 0.01)
        
        signal = self._generate_signal(recommendations, residual)
        
        return DynamicHedgingResult(
            current_exposure=exposure,
            hedge_recommendations=recommendations,
            hedge_cost=hedge_cost,
            residual_risk=residual,
            trading_signal=signal
        )
    
    def _generate_signal(self, recs: List[HedgeRecommendation], residual: float) -> str:
        """Generate signal."""
        if not recs:
            return "HEDGED: Portfolio within tolerance"
        urgent = [r for r in recs if r.urgency == 'high']
        if urgent:
            return f"URGENT HEDGE: {len(urgent)} high priority adjustments needed"
        return f"REBALANCE: {len(recs)} hedge adjustments recommended"
