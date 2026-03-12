"""
Skill #39: Smart Order Fragmenter
=================================

Intelligently splits large orders into smaller pieces
to minimize market impact.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderFragment:
    """Single order fragment."""
    size: float
    delay_ms: int
    venue: str
    order_type: str


@dataclass
class FragmentationResult:
    """Order fragmentation result."""
    fragments: List[OrderFragment]
    num_fragments: int
    avg_fragment_size: float
    expected_impact_reduction: float
    trading_signal: str


class SmartOrderFragmenter:
    """Intelligently fragments large orders."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_fragment = self.config.get('min_fragment', 100)
            logger.info("SmartOrderFragmenter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def fragment(
        self,
        total_quantity: float,
        avg_volume: float,
        volatility: float,
        venues: List[str] = None
    ) -> FragmentationResult:
        """Fragment order into smaller pieces."""
        try:
            venues = venues or ['primary']
        
            # Calculate optimal fragment size
            participation = total_quantity / (avg_volume + 1e-10)
            optimal_size = max(self.min_fragment, total_quantity / max(1, int(participation * 20)))
        
            num_fragments = max(1, int(total_quantity / optimal_size))
        
            fragments = []
            remaining = total_quantity
        
            for i in range(num_fragments):
                size = min(optimal_size, remaining)
                fragments.append(OrderFragment(
                    size=size,
                    delay_ms=100 * i,
                    venue=venues[i % len(venues)],
                    order_type='limit' if volatility < 0.02 else 'market'
                ))
                remaining -= size
        
            impact_reduction = 1 - np.sqrt(1 / num_fragments)
            signal = self._generate_signal(num_fragments, optimal_size, impact_reduction)
        
            return FragmentationResult(
                fragments=fragments,
                num_fragments=num_fragments,
                avg_fragment_size=optimal_size,
                expected_impact_reduction=impact_reduction,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in fragment: {e}")
            raise
    
    def _generate_signal(self, num: int, size: float, reduction: float) -> str:
        """Generate signal."""
        return f"FRAGMENTED: {num} pieces of ~{size:.0f}, {reduction:.0%} impact reduction"
