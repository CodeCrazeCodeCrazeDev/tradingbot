"""
Skill #40: Venue Selection Optimizer
====================================

Selects optimal execution venue based on liquidity,
costs, and fill probability.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class VenueScore:
    """Score for a single venue."""
    venue_name: str
    liquidity_score: float
    cost_score: float
    fill_score: float
    total_score: float


@dataclass
class VenueSelectionResult:
    """Venue selection result."""
    recommended_venue: str
    venue_scores: List[VenueScore]
    allocation: Dict[str, float]
    expected_savings: float
    trading_signal: str


class VenueSelectionOptimizer:
    """Optimizes venue selection for order execution."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.venues = self.config.get('venues', {
                'primary': {'fee': 0.001, 'rebate': 0.0005},
                'secondary': {'fee': 0.0008, 'rebate': 0.0003},
                'dark_pool': {'fee': 0.0005, 'rebate': 0}
            })
            logger.info("VenueSelectionOptimizer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def select(
        self,
        order_size: float,
        order_side: str,
        venue_liquidity: Dict[str, float]
    ) -> VenueSelectionResult:
        """Select optimal venue."""
        try:
            scores = []
        
            for venue, params in self.venues.items():
                liquidity = venue_liquidity.get(venue, 1000)
            
                liq_score = min(1, liquidity / order_size)
                cost_score = 1 - params['fee'] * 10
                fill_score = liq_score * 0.8
                total = 0.4 * liq_score + 0.3 * cost_score + 0.3 * fill_score
            
                scores.append(VenueScore(
                    venue_name=venue,
                    liquidity_score=liq_score,
                    cost_score=cost_score,
                    fill_score=fill_score,
                    total_score=total
                ))
        
            scores.sort(key=lambda x: x.total_score, reverse=True)
            best = scores[0].venue_name
        
            # Allocation
            total_score = sum(s.total_score for s in scores)
            allocation = {s.venue_name: s.total_score / total_score for s in scores}
        
            # Expected savings
            savings = (self.venues['primary']['fee'] - self.venues[best]['fee']) * order_size
        
            signal = self._generate_signal(best, scores[0].total_score, savings)
        
            return VenueSelectionResult(
                recommended_venue=best,
                venue_scores=scores,
                allocation=allocation,
                expected_savings=savings,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in select: {e}")
            raise
    
    def _generate_signal(self, venue: str, score: float, savings: float) -> str:
        """Generate signal."""
        return f"ROUTE TO {venue.upper()}: Score {score:.2f}, savings {savings:.4f}"
