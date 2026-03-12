"""
Skill #32: Adaptive TWAP/VWAP
=============================

Time-weighted and volume-weighted average price execution
with adaptive adjustments based on market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TWAPVWAPSlice:
    """Execution slice for TWAP/VWAP."""
    time: datetime
    target_quantity: float
    actual_quantity: float
    target_price: float
    volume_weight: float


@dataclass
class AdaptiveTWAPVWAPResult:
    """Adaptive TWAP/VWAP result."""
    slices: List[TWAPVWAPSlice]
    algorithm: str
    expected_avg_price: float
    volume_profile: np.ndarray
    adaptation_factor: float
    trading_signal: str


class AdaptiveTWAPVWAP:
    """Adaptive TWAP and VWAP execution algorithms."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_slice_size = self.config.get('min_slice_size', 100)
        logger.info("AdaptiveTWAPVWAP initialized")
    
    def create_schedule(
        self,
        quantity: float,
        duration_minutes: int,
        current_price: float,
        historical_volumes: Optional[np.ndarray] = None,
        algorithm: str = 'vwap'
    ) -> AdaptiveTWAPVWAPResult:
        """Create adaptive TWAP or VWAP schedule."""
        num_slices = max(1, duration_minutes // 5)
        now = datetime.now()
        
        if algorithm == 'vwap' and historical_volumes is not None:
            slices = self._create_vwap_schedule(quantity, num_slices, now, historical_volumes, current_price)
            volume_profile = historical_volumes[-num_slices:] if len(historical_volumes) >= num_slices else historical_volumes
        else:
            slices = self._create_twap_schedule(quantity, num_slices, now, current_price)
            volume_profile = np.ones(num_slices) / num_slices
        
        expected_price = np.mean([s.target_price for s in slices])
        adaptation = self._calculate_adaptation_factor(slices)
        signal = self._generate_signal(algorithm, len(slices), expected_price)
        
        return AdaptiveTWAPVWAPResult(
            slices=slices,
            algorithm=algorithm,
            expected_avg_price=expected_price,
            volume_profile=volume_profile,
            adaptation_factor=adaptation,
            trading_signal=signal
        )
    
    def _create_twap_schedule(
        self, quantity: float, num_slices: int, start: datetime, price: float
    ) -> List[TWAPVWAPSlice]:
        """Create TWAP schedule with equal time slices."""
        slice_qty = quantity / num_slices
        return [
            TWAPVWAPSlice(
                time=start + timedelta(minutes=5 * i),
                target_quantity=slice_qty,
                actual_quantity=0,
                target_price=price,
                volume_weight=1.0 / num_slices
            )
            for i in range(num_slices)
        ]
    
    def _create_vwap_schedule(
        self, quantity: float, num_slices: int, start: datetime,
        volumes: np.ndarray, price: float
    ) -> List[TWAPVWAPSlice]:
        """Create VWAP schedule weighted by volume."""
        if len(volumes) < num_slices:
            volumes = np.concatenate([volumes, np.ones(num_slices - len(volumes))])
        
        vol_profile = volumes[-num_slices:]
        weights = vol_profile / np.sum(vol_profile)
        
        return [
            TWAPVWAPSlice(
                time=start + timedelta(minutes=5 * i),
                target_quantity=quantity * weights[i],
                actual_quantity=0,
                target_price=price,
                volume_weight=weights[i]
            )
            for i in range(num_slices)
        ]
    
    def _calculate_adaptation_factor(self, slices: List[TWAPVWAPSlice]) -> float:
        """Calculate how much schedule adapts to conditions."""
        weights = [s.volume_weight for s in slices]
        return float(np.std(weights) / (np.mean(weights) + 1e-10))
    
    def _generate_signal(self, algo: str, num_slices: int, price: float) -> str:
        """Generate execution signal."""
        return f"{algo.upper()}: {num_slices} slices, target avg price {price:.4f}"
