"""
Skill #41: Maker/Taker Decision Engine
======================================

Decides between passive (maker) and aggressive (taker)
order placement based on market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class MakerTakerResult:
    """Maker/taker decision result."""
    recommendation: str
    maker_score: float
    taker_score: float
    expected_cost_maker: float
    expected_cost_taker: float
    urgency_factor: float
    trading_signal: str


class MakerTakerDecisionEngine:
    """Decides between maker and taker orders."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.maker_rebate = self.config.get('maker_rebate', 0.0002)
        self.taker_fee = self.config.get('taker_fee', 0.0005)
        logger.info("MakerTakerDecisionEngine initialized")
    
    def decide(
        self,
        spread: float,
        volatility: float,
        urgency: float,
        queue_position: int = 0
    ) -> MakerTakerResult:
        """Decide maker vs taker."""
        # Maker score: better when spread wide, low urgency
        maker_score = spread * 100 - urgency + self.maker_rebate * 1000
        
        # Taker score: better when urgent, tight spread
        taker_score = urgency - spread * 50 - self.taker_fee * 1000
        
        # Costs
        maker_cost = -self.maker_rebate + spread * 0.5 * (1 - np.exp(-queue_position / 100))
        taker_cost = self.taker_fee + spread * 0.5
        
        recommendation = 'maker' if maker_score > taker_score else 'taker'
        
        signal = self._generate_signal(recommendation, maker_cost, taker_cost, urgency)
        
        return MakerTakerResult(
            recommendation=recommendation,
            maker_score=maker_score,
            taker_score=taker_score,
            expected_cost_maker=maker_cost,
            expected_cost_taker=taker_cost,
            urgency_factor=urgency,
            trading_signal=signal
        )
    
    def _generate_signal(self, rec: str, maker: float, taker: float, urgency: float) -> str:
        """Generate signal."""
        if rec == 'maker':
            return f"USE LIMIT ORDER: Cost {maker:.4%} vs {taker:.4%} market"
        return f"USE MARKET ORDER: Urgency {urgency:.0%}, cost {taker:.4%}"
