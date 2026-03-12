"""
Skill #64: Regime-Specific Strategy Selector
============================================

Selects optimal strategies based on market regime.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class RegimeSelectorResult:
    """Regime selection result."""
    current_regime: str
    selected_strategy: str
    regime_confidence: float
    strategy_weights: Dict[str, float]
    trading_signal: str


class RegimeSpecificStrategySelector:
    """Selects strategies based on market regime."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.strategies = {
            'trending': ['momentum', 'trend_following'],
            'mean_reverting': ['mean_reversion', 'pairs'],
            'volatile': ['volatility', 'options'],
            'quiet': ['carry', 'spread'],
        }
        logger.info("RegimeSpecificStrategySelector initialized")
    
    def select(self, returns: np.ndarray, volatility: float) -> RegimeSelectorResult:
        """Select strategy for current regime."""
        if len(returns) < 20:
            return self._create_empty_result()
        
        # Detect regime
        trend = np.mean(returns[-20:]) / (np.std(returns[-20:]) + 1e-10)
        
        if abs(trend) > 0.5:
            regime = 'trending'
        elif volatility > 0.02:
            regime = 'volatile'
        elif abs(trend) < 0.1:
            regime = 'mean_reverting'
        else:
            regime = 'quiet'
        
        strategies = self.strategies[regime]
        selected = strategies[0]
        confidence = min(0.9, 0.5 + abs(trend))
        
        weights = {s: 1.0 / len(strategies) for s in strategies}
        
        return RegimeSelectorResult(
            current_regime=regime, selected_strategy=selected,
            regime_confidence=confidence, strategy_weights=weights,
            trading_signal=f"REGIME: {regime}, use {selected} ({confidence:.0%} confidence)"
        )
    
    def _create_empty_result(self) -> RegimeSelectorResult:
        return RegimeSelectorResult("unknown", "", 0, {}, "Insufficient data")
