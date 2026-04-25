"""
Liquidity Trap Detector
=======================

Detects situations where exit will be costly or impossible:
- Bid-ask spread expansion > 3x normal
- Order book depth < 20% of normal
- Market impact models showing > 1% slippage
- Cross-market liquidity drying up
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class LiquidityRisk:
    """Detected liquidity risk."""
    asset: str
    risk_level: float  # 0.0-1.0
    spread_expansion: float  # multiple of normal
    depth_reduction: float  # percentage
    estimated_slippage: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'risk_level': self.risk_level,
            'spread_expansion': self.spread_expansion,
            'depth_reduction': self.depth_reduction,
            'estimated_slippage': self.estimated_slippage,
            'timestamp': self.timestamp.isoformat(),
        }


class LiquidityTrapDetector:
    """
    Detects liquidity traps where position exit becomes problematic.
    
    Critical for risk management - entering is easy, exiting can be impossible
    in stressed market conditions.
    """
    
    def __init__(self, 
                 spread_threshold: float = 3.0,
                 depth_threshold: float = 0.2,
                 slippage_threshold: float = 0.01):
        """
        Initialize detector.
        
        Args:
            spread_threshold: Spread expansion factor (e.g., 3x normal)
            depth_threshold: Depth reduction percentage (e.g., 0.2 = 80% reduction)
            slippage_threshold: Slippage threshold (e.g., 0.01 = 1%)
        """
        self.spread_threshold = spread_threshold
        self.depth_threshold = depth_threshold
        self.slippage_threshold = slippage_threshold
        
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        
        logger.info("LiquidityTrapDetector initialized")
    
    def set_baseline(self, asset: str, normal_spread: float, 
                    normal_depth: float, normal_volume: float):
        """Set baseline liquidity metrics for an asset."""
        self.baseline_metrics[asset] = {
            'spread': normal_spread,
            'depth': normal_depth,
            'volume': normal_volume,
            'timestamp': datetime.now().timestamp(),
        }
    
    def detect(self, 
              asset: str,
              current_spread: float,
              current_depth: float,
              order_size: float = 10000) -> Optional[LiquidityRisk]:
        """
        Detect liquidity trap conditions.
        
        Args:
            asset: Asset symbol
            current_spread: Current bid-ask spread
            current_depth: Current order book depth
            order_size: Expected order size for slippage estimation
            
        Returns:
            LiquidityRisk if trap detected, None otherwise
        """
        if asset not in self.baseline_metrics:
            # Cannot detect without baseline
            return None
        
        baseline = self.baseline_metrics[asset]
        
        # Calculate metrics
        spread_expansion = current_spread / baseline['spread'] if baseline['spread'] > 0 else 1.0
        depth_reduction = (baseline['depth'] - current_depth) / baseline['depth'] if baseline['depth'] > 0 else 0.0
        
        # Estimate slippage using square-root law
        # Slippage ~ sqrt(order_size / daily_volume)
        if baseline.get('volume', 0) > 0:
            estimated_slippage = np.sqrt(order_size / baseline['volume']) * 0.5
        else:
            estimated_slippage = 0.0
        
        # Determine if liquidity trap
        is_trap = (
            spread_expansion > self.spread_threshold or
            depth_reduction > (1 - self.depth_threshold) or
            estimated_slippage > self.slippage_threshold
        )
        
        if not is_trap:
            return None
        
        # Calculate risk level
        risk_components = [
            min(1.0, spread_expansion / (self.spread_threshold * 2)),
            min(1.0, depth_reduction / 0.8),
            min(1.0, estimated_slippage / (self.slippage_threshold * 2)),
        ]
        risk_level = max(risk_components)
        
        return LiquidityRisk(
            asset=asset,
            risk_level=risk_level,
            spread_expansion=spread_expansion,
            depth_reduction=depth_reduction,
            estimated_slippage=estimated_slippage,
            timestamp=datetime.now(),
        )
    
    def check_exit_feasibility(self, asset: str, position_size: float) -> Dict[str, Any]:
        """
        Check if position exit is feasible without excessive costs.
        
        Returns:
            Dictionary with feasibility assessment
        """
        if asset not in self.baseline_metrics:
            return {'feasible': True, 'risk': 'unknown', 'max_exit_size': float('inf')}
        
        baseline = self.baseline_metrics[asset]
        
        # Estimate slippage for full position
        if baseline.get('volume', 0) > 0:
            slippage = np.sqrt(position_size / baseline['volume']) * 0.5
        else:
            slippage = 0.1  # Conservative estimate
        
        # Maximum feasible exit size (target < 0.5% slippage)
        max_exit = baseline['volume'] * (0.005 / 0.5) ** 2 if baseline.get('volume', 0) > 0 else position_size * 0.1
        
        feasible = slippage < 0.01  # Less than 1% slippage
        
        return {
            'feasible': feasible,
            'estimated_slippage': slippage,
            'max_exit_size': max_exit,
            'risk': 'high' if slippage > 0.02 else 'medium' if slippage > 0.01 else 'low',
        }
