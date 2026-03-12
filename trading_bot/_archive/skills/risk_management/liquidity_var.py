"""
Skill #51: Liquidity-Adjusted VaR
=================================

Adjusts VaR for liquidity risk and execution costs.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LiquidityVaRResult:
    """Liquidity-adjusted VaR result."""
    standard_var: float
    liquidity_var: float
    liquidity_adjustment: float
    liquidation_time: float
    trading_signal: str


class LiquidityAdjustedVaR:
    """Calculates liquidity-adjusted VaR."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        logger.info("LiquidityAdjustedVaR initialized")
    
    def calculate(
        self,
        returns: np.ndarray,
        position_size: float,
        avg_volume: float,
        spread: float,
        confidence: float = 0.99
    ) -> LiquidityVaRResult:
        """Calculate liquidity-adjusted VaR."""
        if len(returns) < 20:
            return self._create_empty_result()
        
        # Standard VaR
        std_var = np.percentile(returns, (1 - confidence) * 100) * position_size
        
        # Liquidation time
        liquidation_time = position_size / (avg_volume * 0.1)  # 10% participation
        
        # Liquidity cost
        spread_cost = spread * position_size
        impact_cost = 0.1 * np.sqrt(position_size / avg_volume) * position_size
        
        # Liquidity adjustment
        adjustment = spread_cost + impact_cost + np.std(returns) * np.sqrt(liquidation_time) * position_size
        
        liq_var = std_var - adjustment
        
        signal = self._generate_signal(std_var, liq_var, liquidation_time)
        
        return LiquidityVaRResult(
            standard_var=abs(std_var),
            liquidity_var=abs(liq_var),
            liquidity_adjustment=adjustment,
            liquidation_time=liquidation_time,
            trading_signal=signal
        )
    
    def _generate_signal(self, std: float, liq: float, time: float) -> str:
        """Generate signal."""
        adj_pct = (abs(liq) - abs(std)) / abs(std) * 100 if std != 0 else 0
        return f"L-VaR: {abs(liq):.2f} ({adj_pct:+.0f}% vs standard), liquidation {time:.1f} days"
    
    def _create_empty_result(self) -> LiquidityVaRResult:
        return LiquidityVaRResult(0, 0, 0, 0, "Insufficient data")
